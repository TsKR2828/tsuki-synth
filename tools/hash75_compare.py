#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hash75_compare.py -- per-score WAV-hash comparison between two verify_score
--all runs (the "75 首逐首雜湊比對" integration-card step).

Why this exists
---------------
Since WF1002b every integration card has to show, score by score, whether the
rendered audio changed versus the previous integration card (ROADMAP_PHYSICS.md
rule R10: any render-output change must be shown before/after and reported).
`tools/verify_score.py --all` already renders every score twice and prints,
per score, the determinism check line

    [OK    ] determinism.sha256_match: Two independent renders produced
             identical audio (SHA256 830d2089427a9c32...).

That 16-hex prefix is the SHA256 of the rendered WAV. This tool lifts it out of
two such logs and prints one SAME / DIFF row per score. It reads only what
verify_score.py printed; it renders nothing and re-implements no check.

Inputs
------
  LOG        a `verify_score.py --all` log file (text; UTF-8 or UTF-16 with
             BOM are both handled). Blocks are delimited by the
             `SCORE: <path>` header lines verify_score.py prints.
  REFERENCE  either another verify_score log (same format), OR a table that
             this tool printed on an earlier run (rows of
             `<score> <reference-hash12> <this-run-hash12> SAME|DIFF`; the
             "this run" column of that table is used as the reference, so the
             output of the last integration card can be fed straight back in).
             The format is auto-detected; --reference-format forces one.

Hashes are compared on the longest prefix both sides carry (16 hex from a
log, 12 hex from a table), and printed as their first 12 hex characters (the
width the integration tables always used); a log vs a table therefore still
compares, on 12. Scores are matched by path with backslash/slash differences
ignored.

Output
------
  header, reference/this-run counts, a one-line summary
  (`identical N, different N, only in reference N, only in this run N,
  unusable hash N`), then the per-score table:

    <score path> <reference hash12> <this-run hash12> SAME|DIFF|NEW|GONE|BAD

  SAME  hashes equal
  DIFF  hashes differ (render output changed -> R10: stop and report)
  NEW   score only in this run (no reference to compare)
  GONE  score only in the reference (missing from this run)
  BAD   no usable hash in this run's block: determinism line absent, or the
        determinism check itself FAILED (two renders disagreed), or the score
        block appears more than once in the log

A final `RESULT: PASS` / `RESULT: FAIL` line closes the output. Exit status:
  0  every score SAME, nothing missing/extra/unusable
  1  any DIFF / NEW / GONE / BAD, or either side parsed to zero scores
  2  usage error or unreadable input file

Usage
-----
  python tools/hash75_compare.py THIS_LOG REFERENCE
  python tools/hash75_compare.py THIS_LOG REFERENCE --expect 75
  python tools/hash75_compare.py THIS_LOG REFERENCE --out reports/gate_outputs/x.txt
  python tools/hash75_compare.py --help

--expect N additionally fails if this run does not contain exactly N scores
(75 is the current corpus size; the tool does not hard-code it).
--out FILE also writes the report to FILE (UTF-8); stdout is printed either way.
"""

import argparse
import re
import sys
from pathlib import Path

HASH_WIDTH = 12  # printed width (integration-table width); compare uses full parsed prefix

_SCORE_HDR = re.compile(r"^SCORE:\s+(\S.*?)\s*$")
_DET_OK = re.compile(
    r"determinism\.sha256_match:.*?\(SHA256\s+([0-9a-fA-F]{12,64})\.\.\.\)")
_DET_ANY = re.compile(r"determinism\.sha256_match:")
# table row printed by this tool / the old WF1002b hash75.py:
#   "  scores\x\y.score.json <ref12> <this12> SAME"
_TABLE_ROW = re.compile(
    r"^\s+(\S+\.score\.json)\s+([0-9a-fA-F]{12})\s+([0-9a-fA-F]{12})\s+"
    r"(?:SAME|DIFF)\s*$")

BAD = "BAD"  # sentinel stored in place of a hash


def _norm_key(path):
    return path.replace("\\", "/")


def read_text(path):
    """Read a text file; honour UTF-8/UTF-16 BOMs (PowerShell redirects)."""
    raw = Path(path).read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig", errors="replace")


def parse_log(text):
    """verify_score --all log -> (ordered {key: (display, hash12|BAD)}, dups).

    A block with no determinism line, a FAILED determinism line (the failure
    message has no `(SHA256 xxxx...)` parenthesis), or a repeated SCORE header
    yields BAD for that score.
    """
    scores = {}
    dups = []
    cur = None
    for line in text.splitlines():
        m = _SCORE_HDR.match(line)
        if m:
            disp = m.group(1)
            cur = _norm_key(disp)
            if cur in scores:
                dups.append(disp)
                scores[cur] = (disp, BAD)
                cur = None  # ignore the repeated block's lines
            else:
                scores[cur] = (disp, BAD)  # BAD until a hash is seen
            continue
        if cur is None:
            continue
        if _DET_ANY.search(line):
            m = _DET_OK.search(line)
            if m and "[OK" in line:
                scores[cur] = (scores[cur][0], m.group(1).lower())
            else:
                scores[cur] = (scores[cur][0], BAD)
    return scores, dups


def parse_table(text):
    """Previously printed table -> {key: (display, hash12)} using the
    'this run' column as the reference hash."""
    scores = {}
    for line in text.splitlines():
        m = _TABLE_ROW.match(line)
        if m:
            scores[_norm_key(m.group(1))] = (m.group(1), m.group(3).lower())
    return scores


def load_reference(text, fmt):
    if fmt == "auto":
        fmt = "table" if parse_table(text) else "log"
    if fmt == "table":
        return parse_table(text), [], "table"
    scores, dups = parse_log(text)
    return scores, dups, "log"


def _same(a, b):
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def _show(h):
    return h if h == "-" else h[:HASH_WIDTH]


def compare(this, ref):
    """-> list of (display, ref_hash|'-', this_hash|'-', status)."""
    rows = []
    for key, (disp, h) in this.items():
        if key in ref:
            rh = ref[key][1]
            if h == BAD:
                rows.append((disp, _show(rh), "-", "BAD"))
            elif rh == BAD:
                rows.append((disp, "-", _show(h), "BAD"))
            else:
                rows.append((disp, _show(rh), _show(h),
                             "SAME" if _same(rh, h) else "DIFF"))
        else:
            rows.append((disp, "-", "-" if h == BAD else _show(h),
                         "BAD" if h == BAD else "NEW"))
    for key, (disp, rh) in ref.items():
        if key not in this:
            rows.append((disp, "-" if rh == BAD else _show(rh), "-", "GONE"))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="hash75_compare.py",
        description="Per-score WAV SHA256 comparison between a "
                    "`verify_score.py --all` log and a reference "
                    "(another log, or a table printed by this tool). "
                    "Exit 1 on any DIFF / missing / unusable score.")
    ap.add_argument("this_log",
                    help="verify_score.py --all log of the run under test")
    ap.add_argument("reference",
                    help="reference: a verify_score --all log, or a table "
                         "printed by this tool on an earlier run")
    ap.add_argument("--reference-format", choices=("auto", "log", "table"),
                    default="auto",
                    help="how to read REFERENCE (default: auto-detect)")
    ap.add_argument("--expect", type=int, default=None, metavar="N",
                    help="also fail unless this run holds exactly N scores")
    ap.add_argument("--out", default=None, metavar="FILE",
                    help="also write the report to FILE (UTF-8)")
    args = ap.parse_args(argv)

    try:
        this_text = read_text(args.this_log)
        ref_text = read_text(args.reference)
    except OSError as e:
        print(f"hash75_compare: cannot read input: {e}", file=sys.stderr)
        return 2

    this, this_dups = parse_log(this_text)
    ref, ref_dups, ref_fmt = load_reference(ref_text, args.reference_format)
    rows = compare(this, ref)

    n = {s: sum(1 for r in rows if r[3] == s)
         for s in ("SAME", "DIFF", "NEW", "GONE", "BAD")}
    problems = []
    if not this:
        problems.append("this run parsed to zero scores")
    if not ref:
        problems.append("reference parsed to zero scores")
    if this_dups:
        problems.append(f"{len(this_dups)} score(s) repeated in this run: "
                        + ", ".join(this_dups))
    if ref_dups:
        problems.append(f"{len(ref_dups)} score(s) repeated in reference: "
                        + ", ".join(ref_dups))
    if args.expect is not None and len(this) != args.expect:
        problems.append(f"expected {args.expect} scores in this run, "
                        f"found {len(this)}")
    ok = (not problems and n["DIFF"] == n["NEW"] == n["GONE"] == n["BAD"] == 0
          and n["SAME"] > 0)

    out = []
    out.append("# hash75_compare: per-score WAV SHA256 "
               f"(first {HASH_WIDTH} hex)  "
               f"$ python tools/hash75_compare.py {args.this_log} "
               f"{args.reference}")
    out.append(f"reference: {args.reference} ({ref_fmt}) -> {len(ref)} scores")
    out.append(f"this run : {args.this_log} -> {len(this)} scores")
    out.append(f"identical {n['SAME']}, different {n['DIFF']}, "
               f"only in reference {n['GONE']}, only in this run {n['NEW']}, "
               f"unusable hash {n['BAD']}")
    for p in problems:
        out.append(f"PROBLEM: {p}")
    out.append("")
    out.append("per-score (score, reference hash, this run hash, status):")
    for disp, rh, th, st in rows:
        out.append(f"  {disp} {rh} {th} {st}")
    out.append("")
    out.append("RESULT: " + ("PASS" if ok else "FAIL"))
    text = "\n".join(out)

    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
