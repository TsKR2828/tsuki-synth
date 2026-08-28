#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B5 baseline -- render every corpus score that touches a "wood_" field
(material or exciter), record per-WAV SHA256 for bit-exact before/after
comparison across the B5 damping-gap work.

Adaptation of reports/gate_outputs/b4_method/render_affected_pieces.py:
same CLI invocation ("<cli> <score> --output <piece_dir>"), same
"repo-external workdir" safety check, same SHA256-over-raw-WAV-bytes
definition. This script additionally records RMS dBFS and spectral
centroid (same definitions as B3/B4) purely as human-readable sanity
context; the authoritative before/after comparator is the SHA256 column.

Piece list: hard-coded PIECES below. It is the full output of

    grep -rl "wood_" scores/ --include="*.score.json"

run against HEAD=53e6c76 (fix/deep-physics-audit-20260716) on
2026-08-28. NOTE: none of these files actually use material
"wood_spruce" -- see README.md in this directory for the discrepancy
against the original task wording (grep found "wood_" as a substring
match against the *exciter* field "wood_mallet", not just the
*material* field; wood_spruce does not appear in any scores/*.score.json
at this commit).

Usage (run from the repo root; workdir must NOT be inside the repo):
    python reports/gate_outputs/b5_method/render_wood_scores.py ^
        --label before --workdir %TEMP%\\b5_render_before
    python reports/gate_outputs/b5_method/render_wood_scores.py ^
        --label after --workdir %TEMP%\\b5_render_after

Output:
    reports/gate_outputs/b5_method/render_<label>.csv
    reports/gate_outputs/b5_method/sha256_<label>.txt
      (one line per WAV: "<sha256>  <piece>/<wavname>")
"""
import argparse
import csv
import hashlib
import os
import subprocess
import sys
import wave

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_CLI = os.path.join(REPO, "build", "TsukiSynthCLI_artefacts", "Release",
                           "TsukiSynthCLI.exe")

# Full result of: grep -rl "wood_" scores/ --include="*.score.json"
# (13 files, captured against HEAD=53e6c76 on 2026-08-28)
PIECES = [
    "scores/examples/moonlight_sonata_movement1_yangqin.score.json",
    "scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json",
    "scores/library/akashic/akashic_notify_001.score.json",
    "scores/library/forest/forest_action_001.score.json",
    "scores/library/forest/forest_notify_001.score.json",
    "scores/library/forest/forest_transition_001.score.json",
    "scores/library/forest/forest_ui_001.score.json",
    "scores/library/rabbit/rabbit_notify_001.score.json",
    "scores/library/rabbit/rabbit_ui_001.score.json",
    "scores/originals/ai_radiance/ai_radiance_m1.score.json",
    "scores/originals/rules_v2_demo/rules_v2_demo_001.score.json",
    "scores/tests/melody_sentinel.score.json",
    "scores/tests/test_glide.score.json",
]


def read_wav_mono(path):
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        sw = w.getsampwidth()
        ch = w.getnchannels()
        raw = w.readframes(n)
    if sw == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        as_int = (b[:, 0].astype(np.int32)
                  | (b[:, 1].astype(np.int32) << 8)
                  | (b[:, 2].astype(np.int32) << 16))
        as_int[as_int >= (1 << 23)] -= (1 << 24)
        data = as_int.astype(np.float64) / (1 << 23)
    elif sw == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / (2 ** 31)
    else:
        raise ValueError("unsupported sampwidth %d" % sw)
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    return sr, data


def rms_dbfs(x):
    r = np.sqrt(np.mean(x ** 2)) if len(x) else 0.0
    return 20 * np.log10(max(r, 1e-12))


def spectral_centroid_whole(x, sr):
    spec = np.abs(np.fft.rfft(x))
    freqs = np.fft.rfftfreq(len(x), d=1.0 / sr)
    s = spec.sum()
    return float((freqs * spec).sum() / s) if s > 0 else 0.0


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--workdir", required=True,
                    help="render output dir; must be OUTSIDE the repo")
    ap.add_argument("--cli", default=DEFAULT_CLI)
    args = ap.parse_args()

    workdir = os.path.abspath(args.workdir)
    if (workdir + os.sep).startswith(REPO + os.sep):
        sys.exit("refusing to render inside the repo: " + workdir)
    os.makedirs(workdir, exist_ok=True)

    outdir = os.path.dirname(os.path.abspath(__file__))
    out_csv = os.path.join(outdir, "render_%s.csv" % args.label)
    out_sha = os.path.join(outdir, "sha256_%s.txt" % args.label)
    rows = []
    sha_lines = []
    for rel in PIECES:
        name = os.path.basename(rel).replace(".score.json", "")
        score = os.path.join(REPO, rel)
        if not os.path.exists(score):
            raise RuntimeError("missing score file: %s" % score)
        piece_dir = os.path.join(workdir, name)
        os.makedirs(piece_dir, exist_ok=True)
        print("rendering", name, "...", flush=True)
        out = subprocess.run([args.cli, score, "--output", piece_dir],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        wavs = [f for f in os.listdir(piece_dir) if f.lower().endswith(".wav")]
        if out.returncode != 0 or len(wavs) != 1:
            raise RuntimeError("render failed for %s (rc=%d, wavs=%s):\n%s\n%s"
                               % (name, out.returncode, wavs,
                                  out.stdout, out.stderr))
        wavname = wavs[0]
        wav = os.path.join(piece_dir, wavname)
        sr, x = read_wav_mono(wav)
        digest = sha256_of(wav)
        row = [name, rel, wavname, "%.3f" % (len(x) / sr),
               "%.3f" % rms_dbfs(x),
               "%.2f" % spectral_centroid_whole(x, sr),
               digest]
        rows.append(row)
        sha_lines.append("%s  %s/%s" % (digest, name, wavname))
        print("  len=%ss  RMS=%s dBFS  centroid=%s Hz  sha256=%s"
              % (row[3], row[4], row[5], row[6][:16]), flush=True)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["piece", "score_path", "wav", "len_s", "rms_dbfs",
                    "centroid_hz", "sha256"])
        w.writerows(rows)
    print("wrote", out_csv)

    with open(out_sha, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sha_lines) + "\n")
    print("wrote", out_sha)


if __name__ == "__main__":
    sys.exit(main())
