#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 Part B cross-check (descriptive, NOT a GATE, no threshold):
does the voice-lifetime formula used by voice_pool_occupancy.py match what
the engine code actually does?

Method: take real corpus events, render each ALONE through the CLI (dry:
reverb/delay wet zeroed via tools/stem_verify.derive_dry_score(); export
forced to unnormalised 32-bit float via stem_verify.unnormalized_export(),
tail_silence_ms at the schema cap 60000 so the buffer outlasts the voice).
The CLI's per-event loop is `for (i = start; i < end && voice.isActive();
++i)` (ScoreRenderer.h), so the LAST NON-ZERO SAMPLE of a dry single-event
render is where the voice went inactive -- the same isActive() criterion
the plugin uses before clearCurrentNote(). The CLI sends noteOff at
start + int(duration*sr*0.9) (ScoreRenderer.h noteOffSample), so the model
prediction here uses k = 0.9.

Prints predicted vs measured end time; the difference is reported as a
number only.

Usage:
  python reports/wf0925_method/voice_lifetime_probe.py --cli output/wf0925/V1/cli.exe \
      --dumps output/wf0925/V1/dumps --workdir output/wf0925/V1/lifetime_probe
"""
import argparse
import copy
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(HERE))
import verify_score as vs            # noqa: E402
import stem_verify as sv             # noqa: E402
import voice_pool_occupancy as vpo   # noqa: E402

# (score, event-selector) -- chosen to span every engine family and both
# "note-off before T60" and "T60 before note-off"; selectors are resolved
# against the score at run time (first matching event), nothing numeric is
# assumed about the result.
PROBES = [
    ("scores/classical/fur_elise/fur_elise_complete.score.json", {"note": "E5", "velocity": 0.278}),
    ("scores/classical/fur_elise/fur_elise_complete.score.json", {"note": "A2"}),
    ("scores/classical/fur_elise/fur_elise_complete.score.json", {"note": "A5", "velocity": 0.427}),
    ("scores/examples/moonlight_sonata_movement1_yangqin.score.json", {"index": 0}),
    ("scores/examples/moonlight_sonata_movement1_tongue_drum.score.json", {"index": 0}),
    ("scores/examples/water_gong_free.score.json", {"index": 0}),
    ("scores/classical/vivaldi_four_seasons/winter/vivaldi_four_seasons_winter_m1.score.json", {"longest": True}),
    ("scores/classical/vivaldi_four_seasons/summer/vivaldi_four_seasons_summer_m3.score.json", {"lowest": True}),
    ("scores/examples/moonlight_sonata_complete.score.json", {"index": 0}),
    ("scores/examples/moonlight_sonata_complete.score.json", {"longest": True}),
]


def pick(score, sel):
    evs = [(i, e) for i, e in enumerate(score["events"]) if float(e.get("velocity", 0)) > 0]
    if "index" in sel:
        return evs[sel["index"]]
    if sel.get("longest"):
        return max(evs, key=lambda ie: float(ie[1]["duration"]))
    if sel.get("lowest"):
        return min(evs, key=lambda ie: vs.note_to_midi(ie[1]["note"]) or 999)
    for i, e in evs:
        if all((abs(float(e.get(k)) - v) < 1e-9 if isinstance(v, float) else e.get(k) == v)
               for k, v in sel.items()):
            return i, e
    raise SystemExit("selector %r matched nothing" % (sel,))


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
    consts = vpo.read_code_constants()
    print("cli=%s sha256=%s" % (cli, vs.sha256_file(cli)))
    print("%-4s %-60s %-6s %-9s %7s %8s %9s %10s %10s %9s" % (
        "#", "score", "idx", "note", "dur_s", "T60max", "noteoff", "pred_end", "meas_end", "diff_s"))
    rows = []
    for k, (spath, sel) in enumerate(PROBES):
        src = json.loads((REPO / spath).read_text(encoding="utf-8"))
        idx, ev = pick(src, sel)
        # model record from the cached dump (same loader the occupancy script uses)
        events, sr, _ = vpo.load_events((REPO / spath).resolve(), args.dumps, consts)
        rec = next(e for e in events if e["id"] == str(idx))
        probe = copy.deepcopy(src)
        e1 = copy.deepcopy(ev)
        e1["time"] = 0.5
        probe["events"] = [e1]
        probe, _diff = sv.derive_dry_score(probe)
        probe["export"] = sv.unnormalized_export(probe.get("export"), bit_depth=32,
                                                 extra_tail_ms=60000.0)
        probe["export"]["filename"] = "probe_%02d" % k
        pdir = work / ("p%02d" % k)
        pdir.mkdir()
        ppath = pdir / "score.json"
        ppath.write_text(json.dumps(probe), encoding="utf-8")
        wav = vs.render_score(str(cli), str(ppath), str(pdir / "out"))
        sr_w, ch, arr = sv.read_wav_float(str(wav))
        x = np.max(np.abs(arr), axis=1) if arr.ndim == 2 else np.abs(arr)
        nz = np.nonzero(x > 0)[0]
        meas_end = (nz[-1] + 1) / sr_w if nz.size else None
        # model: note-on 0.5 s, CLI note-off at start + int(dur*sr*0.9)
        t_on = 0.5
        t_off = (int(round(t_on * sr_w)) + int(max(0.0, float(ev["duration"])) * sr_w * 0.9)) / sr_w
        v = vpo.Voice()
        v.ev, v.t_on, v.t_damp, v.fm_rel_t, v.fm_rel_level = rec, t_on, None, None, None
        v.key_down, v.sus_down = True, False
        v.end = vpo.compute_end(v)
        if t_off < v.end:
            vpo.stop_tail_off(v, t_off)
        pred_end = v.end
        diff = (meas_end - pred_end) if (meas_end is not None and math.isfinite(pred_end)) else None
        t60 = rec.get("t60_max")
        row = {"probe": k, "score": spath, "index": idx, "note": ev.get("note"),
               "engine": ev.get("engine"), "family": rec["family"],
               "duration_s": float(ev["duration"]), "t60_max_s": t60,
               "note_off_s": t_off, "pred_end_s": pred_end, "meas_end_s": meas_end,
               "diff_s": diff,
               "diff_pct_of_pred_lifetime": (100.0 * diff / (pred_end - t_on)) if diff is not None else None,
               "wav": str(wav)}
        rows.append(row)
        print("%-4d %-60s %-6d %-9s %7.3f %8s %9.4f %10.4f %10s %9s" % (
            k, spath[-60:], idx, ev.get("note"), float(ev["duration"]),
            ("%.3f" % t60) if t60 else "fm", t_off, pred_end,
            ("%.4f" % meas_end) if meas_end is not None else "-",
            ("%+.4f" % diff) if diff is not None else "-"))
    (work / "probe_results.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("wrote %s" % (work / "probe_results.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
