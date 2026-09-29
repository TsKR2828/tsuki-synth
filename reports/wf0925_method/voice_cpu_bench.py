#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 Part B: rough CPU cost of one sounding voice, measured with the
CLI (NOT the plugin -- see caveats printed at the end). Descriptive only, no
threshold.

Method: for each engine family, build a dry score of N simultaneous notes
(distinct MIDI notes, all starting at t=0, params copied from one real corpus
event of that family), render it with the CLI N in {1, 16, 32, 64}, 3 times
each, take the minimum wall-clock per N, fit time = a + b*N. `b` is the
extra wall-clock seconds one more voice costs for this render; dividing by
the voice's own lifetime (from the same lifetime formula the occupancy
script uses) gives CPU-seconds per voice-second of audio, i.e. the fraction
of one CPU core one continuously-sounding voice needs in real time.

Usage:
  python reports/wf0925_method/voice_cpu_bench.py --cli output/wf0925/V1/cli.exe \
      --dumps output/wf0925/V1/dumps --workdir output/wf0925/V1/cpu_bench
"""
import argparse
import copy
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(HERE))
import verify_score as vs            # noqa: E402
import stem_verify as sv             # noqa: E402
import voice_pool_occupancy as vpo   # noqa: E402

BASES = [
    ("cimbalom (piano)", "scores/classical/fur_elise/fur_elise_complete.score.json", 0),
    ("cimbalom (string)", "scores/classical/vivaldi_four_seasons/winter/vivaldi_four_seasons_winter_m1.score.json", 0),
    ("chromatic (tongue_drum)", "scores/examples/moonlight_sonata_movement1_tongue_drum.score.json", 0),
    ("fm", "scores/examples/moonlight_sonata_complete.score.json", 0),
]
NS = [1, 16, 32, 64]
REPS = 3
DUR_S = 8.0


def midi_name(m):
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return "%s%d" % (names[m % 12], m // 12 - 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", required=True)
    ap.add_argument("--dumps", required=True)
    ap.add_argument("--workdir", required=True)
    args = ap.parse_args()
    cli = Path(args.cli).resolve()
    work = Path(args.workdir)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    print("cli=%s sha256=%s" % (cli, vs.sha256_file(cli)))
    print("machine: %s | %s | cpu_count=%s" % (platform.platform(), platform.processor(), os.cpu_count()))
    out = []
    for bi, (label, spath, idx) in enumerate(BASES):
        src = json.loads((REPO / spath).read_text(encoding="utf-8"))
        ev0 = [e for e in src["events"] if float(e.get("velocity", 0)) > 0][idx]
        times = {}
        for n in NS:
            notes = [36 + (i * 7) % 64 for i in range(n)]     # distinct, spread 36..99
            assert len(set(notes)) == n
            sc = copy.deepcopy(src)
            sc["events"] = []
            for m in notes:
                e = copy.deepcopy(ev0)
                e["time"] = 0.0
                e["duration"] = DUR_S
                e["note"] = midi_name(m)
                e.pop("performance", None)
                sc["events"].append(e)
            sc, _ = sv.derive_dry_score(sc)
            sc["export"] = sv.unnormalized_export(sc.get("export"), bit_depth=24)
            best = None
            for r in range(REPS):
                d = work / ("b%d_n%d_r%d" % (bi, n, r))
                d.mkdir()
                sc["export"]["filename"] = "bench"
                p = d / "score.json"
                p.write_text(json.dumps(sc), encoding="utf-8")
                t0 = time.perf_counter()
                rr = subprocess.run([str(cli), str(p), "--output", str(d / "out")],
                                    capture_output=True, text=True, encoding="utf-8",
                                    errors="replace")
                dt = time.perf_counter() - t0
                if rr.returncode != 0:
                    raise SystemExit("render failed: %s %s" % (rr.stdout, rr.stderr))
                best = dt if best is None else min(best, dt)
                shutil.rmtree(d / "out", ignore_errors=True)
            times[n] = best
        # lifetime of each voice in the largest render, same formula as the
        # occupancy script (CLI note-off point k=0.9, ScoreRenderer.h)
        dump_dir = work / "dumps"
        dump_dir.mkdir(exist_ok=True)
        rr = subprocess.run([str(cli), "--dump-modes", str(p)], capture_output=True,
                            text=True, encoding="utf-8", errors="replace")
        if rr.returncode != 0:
            raise SystemExit("dump failed: %s" % rr.stderr)
        vpo.dump_cache_path(dump_dir, p).write_text(rr.stdout, encoding="utf-8")
        consts = vpo.read_code_constants()
        evs, sr, _ = vpo.load_events(p.resolve(), dump_dir, consts)
        lifes = []
        for e in evs:
            v = vpo.Voice()
            v.ev, v.t_on, v.t_damp, v.fm_rel_t, v.fm_rel_level = e, 0.0, None, None, None
            v.key_down, v.sus_down = True, False
            v.end = vpo.compute_end(v)
            t_off = int(DUR_S * sr * 0.9) / sr
            if t_off < v.end:
                vpo.stop_tail_off(v, t_off)
            lifes.append(v.end)
        mean_life = float(np.mean(lifes))
        xs = np.array(NS, dtype=float)
        ys = np.array([times[n] for n in NS])
        b, a = np.polyfit(xs, ys, 1)
        out.append({"family": label, "base_score": spath, "base_event": idx,
                    "wall_s_by_n": times, "fit_a_s": a, "fit_b_s_per_voice": b,
                    "mean_voice_lifetime_s": mean_life,
                    "cpu_s_per_voice_s": b / mean_life if mean_life > 0 else None})
        print("%-24s wall(min of %d) %s | fit: %.4f s + %.5f s/voice | mean voice life %.3f s"
              " -> %.4f CPU-s per voice-s (= %.2f%% of one core per sounding voice)" % (
            label, REPS, " ".join("N=%d:%.3fs" % (n, times[n]) for n in NS), a, b, mean_life,
            b / mean_life, 100.0 * b / mean_life))
    (work / "cpu_bench.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("wrote %s" % (work / "cpu_bench.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
