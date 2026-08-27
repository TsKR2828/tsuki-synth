#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B4 Rule 10 report -- bit-invariance sentinels for UNAFFECTED pieces.

The 68 unaffected corpus scores (affected_scores_after.md) must render
bit-for-bit identically before/after B4. Direct before-hashes for full
pieces exist in reports/gate_outputs/b3_method/rep_pieces_after.csv: that
CSV was sampled on the B3-after working tree (HEAD f67050b, clean), which
IS the B4-before state, and all six of its pieces are B4-unaffected
(none is in the affected-5 list). So re-rendering them NOW (B4 landed)
and comparing SHA256 against that CSV is a direct whole-piece
bit-invariance check across real corpus content:

  vivaldi_summer_m2 / vivaldi_summer_m3 / vivaldi_autumn_m2
      string engine, non-felt exciter (Wood path)
  moonlight_yangqin   cimbalom, wood_mallet (Wood path)
  akashic_opening_bell  pure Chromatic (tongue_drum/water_gong) null sentinel
  ai_radiance_m1      cimbalom wood path + chromatic mix

Same CLI invocation as render_affected_pieces.py / b3_method's
render_rep_pieces.py ([cli, score, --output dir]).

Usage (from the repo root; workdir must be OUTSIDE the repo):
    python reports/gate_outputs/b4_method/unaffected_sentinels_check.py \
        --workdir <outside-repo-dir>

Output: reports/gate_outputs/b4_method/unaffected_sentinels_after.txt
"""
import argparse
import csv
import hashlib
import os
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_CLI = os.path.join(REPO, "build", "TsukiSynthCLI_artefacts", "Release",
                           "TsukiSynthCLI.exe")
REF_CSV = os.path.join(REPO, "reports", "gate_outputs", "b3_method",
                       "rep_pieces_after.csv")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--cli", default=DEFAULT_CLI)
    args = ap.parse_args()

    workdir = os.path.abspath(args.workdir)
    if (workdir + os.sep).startswith(REPO + os.sep):
        sys.exit("refusing to render inside the repo: " + workdir)
    os.makedirs(workdir, exist_ok=True)

    with open(REF_CSV, "r", encoding="utf-8") as f:
        ref_rows = list(csv.DictReader(f))

    out_lines = []
    out_lines.append("B4 unaffected-piece bit-invariance sentinels")
    out_lines.append("reference (B4-before) hashes: reports/gate_outputs/"
                     "b3_method/rep_pieces_after.csv (B3-after tree = HEAD "
                     "f67050b clean = B4-before state)")
    out_lines.append("render: current working tree (B4 landed), same CLI "
                     "invocation as the reference run")
    out_lines.append("")
    all_ok = True
    for row in ref_rows:
        name = row["piece"]
        score = os.path.join(REPO, row["score_path"])
        piece_dir = os.path.join(workdir, name)
        os.makedirs(piece_dir, exist_ok=True)
        print("rendering", name, "...", flush=True)
        out = subprocess.run([args.cli, score, "--output", piece_dir],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        wavs = [f for f in os.listdir(piece_dir) if f.lower().endswith(".wav")]
        if out.returncode != 0 or len(wavs) != 1:
            raise RuntimeError("render failed for %s (rc=%d, wavs=%s)"
                               % (name, out.returncode, wavs))
        got = sha256_of(os.path.join(piece_dir, wavs[0]))
        ok = (got == row["sha256"]) and (wavs[0] == row["wav"])
        all_ok = all_ok and ok
        verdict = "IDENTICAL" if ok else "MISMATCH"
        out_lines.append("%-22s before=%s" % (name, row["sha256"]))
        out_lines.append("%-22s after =%s -> %s"
                         % ("", got, verdict))
        print("  %s (%s)" % (verdict, got[:16]), flush=True)

    out_lines.append("")
    out_lines.append("overall: %s"
                     % ("ALL 6 SENTINELS BIT-IDENTICAL" if all_ok
                        else "MISMATCH FOUND -- B4 leaked outside the Felt "
                             "path, STOP and investigate"))
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "unaffected_sentinels_after.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    print("wrote", out_path)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
