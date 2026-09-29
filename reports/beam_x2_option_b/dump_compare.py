#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925b-BR: per-score --dump-modes comparison, base vs noX2 (descriptive, NOT a GATE).

For every corpus score that reaches BeamModel: run `--dump-modes` with both
CLIs and compare event by event.
  - beam events (engine beam/tongue_drum): mode-1 ("main mode" = partials[0],
    the lowest-frequency mode) T60 before/after, the ratio, and the mode-1
    amplitude change in dB (the per-note loudness-compensation scalar,
    ModalResonator::loudnessCompensationGain, reads the decay times, so the
    amplitudes move too; all modes of one event share that one scalar).
  - non-beam events in the same score: must dump byte-identical partials.
Writes dump_compare_by_score.csv next to this script.
"""
import argparse
import csv
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
from scan_beam_usage import corpus_files, beam_events  # noqa: E402

BEAM = {"beam", "tongue_drum"}


def dump(cli, p):
    r = subprocess.run([cli, "--dump-modes", str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout)["events"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli-base", required=True)
    ap.add_argument("--cli-nox2", required=True)
    a = ap.parse_args()
    rows = []
    for p in corpus_files():
        if not beam_events(p):
            continue
        eb, ex = dump(a.cli_base, p), dump(a.cli_nox2, p)
        assert len(eb) == len(ex)
        t_b, t_x, ratio, amp_db, freqs = [], [], [], [], []
        nonbeam = nonbeam_same = 0
        for b, x in zip(eb, ex):
            assert b["source_index"] == x["source_index"] and b["engine"] == x["engine"]
            if b["engine"] in BEAM:
                pb, px = b["partials"], x["partials"]
                assert [q["freq"] for q in pb] == [q["freq"] for q in px]
                tb, tx = float(pb[0]["decay"]), float(px[0]["decay"])
                t_b.append(tb)
                t_x.append(tx)
                ratio.append(tx / tb)
                freqs.append(float(pb[0]["freq"]))
                ab, axx = float(pb[0]["amp"]), float(px[0]["amp"])
                if ab > 0 and axx > 0:
                    amp_db.append(20 * math.log10(axx / ab))
            else:
                nonbeam += 1
                nonbeam_same += int(json.dumps(b, sort_keys=True) == json.dumps(x, sort_keys=True))
        rel = p.resolve().relative_to(REPO).as_posix()
        med = statistics.median
        rows.append({
            "score": rel, "beam_events": len(t_b),
            "f1_min_hz": "%.1f" % min(freqs), "f1_max_hz": "%.1f" % max(freqs),
            "t60_mode1_base_min_s": "%.4g" % min(t_b), "t60_mode1_base_med_s": "%.4g" % med(t_b),
            "t60_mode1_base_max_s": "%.4g" % max(t_b),
            "t60_mode1_nox2_min_s": "%.4g" % min(t_x), "t60_mode1_nox2_med_s": "%.4g" % med(t_x),
            "t60_mode1_nox2_max_s": "%.4g" % max(t_x),
            "ratio_min": "%.4f" % min(ratio), "ratio_med": "%.4f" % med(ratio),
            "ratio_max": "%.4f" % max(ratio),
            "amp1_change_db_min": "%+.3f" % min(amp_db), "amp1_change_db_med": "%+.3f" % med(amp_db),
            "amp1_change_db_max": "%+.3f" % max(amp_db),
            "nonbeam_events": nonbeam, "nonbeam_identical": nonbeam_same})
        r = rows[-1]
        print("%-70s n=%4d f1 %s-%s Hz  T60 med %s->%s s  ratio %s..%s  amp1 %s..%s dB  nonbeam %d/%d same"
              % (rel, len(t_b), r["f1_min_hz"], r["f1_max_hz"], r["t60_mode1_base_med_s"],
                 r["t60_mode1_nox2_med_s"], r["ratio_min"], r["ratio_max"],
                 r["amp1_change_db_min"], r["amp1_change_db_max"], nonbeam_same, nonbeam),
              flush=True)
    with open(HERE / "dump_compare_by_score.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("scores=%d  beam events=%d  non-beam events=%d (identical %d)"
          % (len(rows), sum(r["beam_events"] for r in rows),
             sum(r["nonbeam_events"] for r in rows), sum(r["nonbeam_identical"] for r in rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
