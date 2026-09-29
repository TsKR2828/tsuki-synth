#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 Part A, DESCRIPTIVE diagnostic only (not a GATE, no threshold,
does not change or re-judge any verdict the tools wrote).

Question: partial_verify's 849 FAIL partials on Fur Elise are almost all
POSITIVE (measured sharper than expected). partial_verify documents that its
expected partial frequency is read off --dump-modes' STRING-0 mode list
(tools/partial_verify.py caveat "partial frequencies are read off
--dump-modes' string-0 mode list ... not the multi-string course centroid
tools/verify_score.py's course_f0() computes for the fundamental"). A piano
course has several detuned strings, and melody_verify.measure_pitch_cents()
is a band centroid of the SUM of those strings.

This script only puts two numbers side by side for every measured partial:
  measured_cents   -- what partial_verify wrote (vs the string-0 frequency)
  course_offset_c  -- cents between the amplitude-weighted mean of every
                      string's mode-n frequency (the same weighting rule
                      tools/verify_score.course_f0() applies to n=1) and the
                      string-0 mode-n frequency, read from the cached
                      --dump-modes of the full score (same CLI binary).
It prints descriptive statistics of measured_cents and of
(measured_cents - course_offset_c). Nothing is judged against anything.

Usage:
  python reports/wf0925_method/partial_offset_decomposition.py \
      --partial-report output/wf0925/V1/partial_full_report.json \
      --dump output/wf0925/V1/dumps/scores__classical__fur_elise__fur_elise_complete.score.json.dump.json
"""
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import partial_verify as pv  # noqa: E402  (TOLERANCE_CENTS only, to count the tool's own FAIL set)


def weighted_mean_freq(strings, k):
    fs, ws = [], []
    for s in strings:
        if len(s) <= k:
            continue
        f = s[k].get("freq")
        a = s[k].get("amp")
        if f is None or not math.isfinite(f) or f <= 0:
            continue
        fs.append(f)
        ws.append(a if (a is not None and math.isfinite(a) and a > 0) else None)
    if not fs:
        return None
    if any(w is None for w in ws):
        return float(np.mean(fs))
    return float(np.average(fs, weights=ws))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--partial-report", required=True)
    ap.add_argument("--dump", required=True)
    args = ap.parse_args()
    part = json.loads(Path(args.partial_report).read_text(encoding="utf-8"))
    dump = json.loads(Path(args.dump).read_text(encoding="utf-8"))
    dmap = {int(d["source_index"]): d for d in dump["events"]}

    rows = []
    mismatch = 0
    nstr = Counter()
    for e in part["events"]:
        d = dmap[e["index"]]
        strings = d.get("strings") or [d.get("partials") or []]
        nstr[len(strings)] += 1
        for p in e.get("partials") or []:
            if p.get("verdict") not in ("PASS", "FAIL"):
                continue
            k = p["n"] - 1
            f_s0 = strings[0][k]["freq"]
            if abs(f_s0 - p["expected_hz"]) > 1e-9 * max(1.0, f_s0):
                mismatch += 1
            fm = weighted_mean_freq(strings, k)
            off = 1200.0 * math.log2(fm / f_s0)
            rows.append((e["index"], e["note"], p["n"], p["verdict"], p["measured_cents"], off))

    print("# DESCRIPTIVE ONLY -- no verdict is changed; tolerance of the tool: %s c" % pv.TOLERANCE_CENTS)
    print("events by number of strings in the course (dump): %s" % dict(sorted(nstr.items())))
    print("partial slots compared (tool PASS+FAIL): %d ; string-0 freq != partial_verify expected_hz: %d"
          % (len(rows), mismatch))
    meas = np.array([r[4] for r in rows])
    off = np.array([r[5] for r in rows])
    resid = meas - off

    def stats(name, x):
        q = np.percentile(x, [0, 5, 25, 50, 75, 95, 100])
        print("%-34s n=%d mean %+.3f  sd %.3f  min %+.3f p5 %+.3f p25 %+.3f median %+.3f p75 %+.3f p95 %+.3f max %+.3f"
              % (name, x.size, x.mean(), x.std(), *q))
    stats("measured_cents (vs string 0)", meas)
    stats("course_offset_c (mean - string 0)", off)
    stats("measured - course_offset", resid)
    r = np.corrcoef(meas, off)[0, 1]
    print("Pearson r(measured_cents, course_offset_c) = %.4f" % r)
    fails = [x for x in rows if x[3] == "FAIL"]
    fm = np.array([x[4] for x in fails])
    fo = np.array([x[5] for x in fails])
    print("\n# the tool's own FAIL partials only (%d)" % len(fails))
    stats("measured_cents", fm)
    stats("course_offset_c", fo)
    stats("measured - course_offset", fm - fo)
    print("\n# by n (all measured partials): median measured / median course_offset / median residual")
    for n in sorted(set(x[2] for x in rows)):
        sel = [x for x in rows if x[2] == n]
        m = np.array([x[4] for x in sel]); o = np.array([x[5] for x in sel])
        print("  n=%d  count %4d  median measured %+.3f  median offset %+.3f  median residual %+.3f  "
              "max|residual| %.3f" % (n, len(sel), np.median(m), np.median(o), np.median(m - o),
                                        np.max(np.abs(m - o))))
    # Same existing +/-5 c number (the tool's own TOLERANCE_CENTS), applied to
    # the re-expressed value ONLY to show what the other convention would
    # look like -- descriptive, no verdict is written or changed anywhere.
    tol = pv.TOLERANCE_CENTS
    beyond = [x for x in rows if abs(x[4] - x[5]) > tol]
    print("\n# DESCRIPTIVE: if the expected value were the course mean instead of string 0, "
          "|measured - course_offset| > %s c for %d of %d measured partials "
          "(tool verdict now: FAIL %d / PASS %d)"
          % (tol, len(beyond), len(rows), sum(1 for x in beyond if x[3] == "FAIL"),
             sum(1 for x in beyond if x[3] == "PASS")))
    print("  by (note, n): %s" % Counter((x[1], x[2]) for x in beyond).most_common(20))
    print("\n# string detuning read from the dump (n=1 of every string, cents re string 0; amp) -- a few events")
    for i in sorted({rows[0][0], 9, 88, 500, 731} & set(dmap)):
        st = dmap[i].get("strings") or []
        f0 = st[0][0]["freq"]
        print("  idx %4d %-4s %s  amps %s" % (i, dmap[i].get("note"),
              " ".join("%+.2f" % (1200.0 * math.log2(s[0]["freq"] / f0)) for s in st),
              " ".join("%.3g" % s[0]["amp"] for s in st)))
    # largest residuals, listed for reading only
    print("\n# 15 largest |measured - course_offset| (listed only)")
    for x in sorted(rows, key=lambda x: -abs(x[4] - x[5]))[:15]:
        print("  idx %4d %-4s n=%d %-4s measured %+.3f offset %+.3f residual %+.3f"
              % (x[0], x[1], x[2], x[3], x[4], x[5], x[4] - x[5]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
