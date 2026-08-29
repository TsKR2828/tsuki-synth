#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B6 bit-identity harness -- render 8 corpus scores (4 that touch the
string/cimbalom/piano path B6's diagnostic code reads, 4 that don't --
tongue_drum/water_gong/custom/fm) and record per-WAV SHA256 for a
bit-exact before/after comparison across B6 Phase 1's --dump-modes-only
changes (docs/workcards/B6.md SS9).

Adaptation of reports/gate_outputs/b5_method/render_wood_scores.py: same
CLI invocation, same repo-external-workdir safety check, same
SHA256-over-raw-WAV-bytes definition. B6 does not touch render()/
renderEvent()/ModalResonator::excite()/processSample(), so every WAV
must be byte-identical before vs after.

Piece list (SS1 of the B6 task instructions):
  cimbalom/piano path (4):
    scores/examples/moonlight_sonata_movement1_yangqin.score.json      (cimbalom)
    scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json (cimbalom+tongue_drum)
    scores/examples/physical_piano.score.json                          (piano)
    scores/examples/restraint_metal_click.score.json                   (string+plate)
  tongue_drum/water_gong/custom/fm path (4):
    scores/examples/moonlight_sonata_movement1_tongue_drum.score.json  (tongue_drum)
    scores/examples/water_gong_free.score.json                         (water_gong)
    scores/originals/ai_radiance/ai_radiance_m1.score.json             (custom)
    scores/examples/fur_elise_opening.score.json                       (fm)

Usage (run from repo root; workdir must NOT be inside the repo):
    python reports/gate_outputs/b6_method/render_b6_scores.py \
        --label before --workdir %TEMP%\\b6_render_before
    python reports/gate_outputs/b6_method/render_b6_scores.py \
        --label after --workdir %TEMP%\\b6_render_after

Output:
    reports/gate_outputs/b6_method/render_<label>.csv
    reports/gate_outputs/b6_method/sha256_<label>.txt
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

PIECES = [
    "scores/examples/moonlight_sonata_movement1_yangqin.score.json",
    "scores/examples/moonlight_sonata_movement1_yangqin_tongue_mix.score.json",
    "scores/examples/physical_piano.score.json",
    "scores/examples/restraint_metal_click.score.json",
    "scores/examples/moonlight_sonata_movement1_tongue_drum.score.json",
    "scores/examples/water_gong_free.score.json",
    "scores/originals/ai_radiance/ai_radiance_m1.score.json",
    "scores/examples/fur_elise_opening.score.json",
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
               "%.3f" % rms_dbfs(x), digest]
        rows.append(row)
        sha_lines.append("%s  %s/%s" % (digest, name, wavname))
        print("  len=%ss  RMS=%s dBFS  sha256=%s"
              % (row[3], row[4], row[5][:16]), flush=True)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["piece", "score_path", "wav", "len_s", "rms_dbfs", "sha256"])
        w.writerows(rows)
    print("wrote", out_csv)

    with open(out_sha, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sha_lines) + "\n")
    print("wrote", out_sha)


if __name__ == "__main__":
    sys.exit(main())
