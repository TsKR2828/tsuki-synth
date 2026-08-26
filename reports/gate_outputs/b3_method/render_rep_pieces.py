#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 Rule 10 report -- six representative pieces: render + metrics.

Same six pieces as the B2 report Sec.4
(reports/b1_b2_bridge_damping_before_after.md): each is rendered with the
CURRENT TsukiSynthCLI into a work directory OUTSIDE the repo, then the
whole-piece RMS (dBFS), spectral centroid (Hz) and WAV SHA256 are recorded.

Metric definitions (self-contained so the after-run is bit-comparable):
  * Channels are mixed to mono by averaging (same convention as
    reports/phase_h_before_after/analyze.py::read_wav).
  * RMS dBFS = 20*log10(sqrt(mean(x^2))) over the ENTIRE file.
  * Spectral centroid = sum(f * |X(f)|) / sum(|X(f)|) over the magnitude
    of one rfft of the ENTIRE mono signal (no window). Whole-piece, not
    the phase_h 2-second window.
  * SHA256 over the raw WAV file bytes.

Usage (run from the repo root; workdir must NOT be inside the repo):
    python reports/gate_outputs/b3_method/render_rep_pieces.py ^
        --label before --workdir %TEMP%\\b3_render_before
    python reports/gate_outputs/b3_method/render_rep_pieces.py ^
        --label after --workdir %TEMP%\\b3_render_after

Output: reports/gate_outputs/b3_method/rep_pieces_<label>.csv
Columns: piece,score_path,wav,len_s,rms_dbfs,centroid_hz,sha256
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

# (short name, repo-relative score path); the produced wav is discovered in
# the per-piece output directory (the CLI's exported basename does not always
# match export.filename, e.g. Classical_Vivaldi_Summer_Movement2.wav).
PIECES = [
    ("vivaldi_summer_m2",
     "scores/classical/vivaldi_four_seasons/summer/vivaldi_four_seasons_summer_m2.score.json"),
    ("vivaldi_summer_m3",
     "scores/classical/vivaldi_four_seasons/summer/vivaldi_four_seasons_summer_m3.score.json"),
    ("moonlight_yangqin",
     "scores/examples/moonlight_sonata_movement1_yangqin.score.json"),
    ("akashic_opening_bell",
     "scores/library/akashic/akashic_opening_bell_001.score.json"),
    ("ai_radiance_m1",
     "scores/originals/ai_radiance/ai_radiance_m1.score.json"),
    ("vivaldi_autumn_m2",
     "scores/classical/vivaldi_four_seasons/autumn/vivaldi_four_seasons_autumn_m2.score.json"),
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
    out_csv = os.path.join(outdir, "rep_pieces_%s.csv" % args.label)

    rows = []
    for name, rel in PIECES:
        score = os.path.join(REPO, rel)
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
        row = [name, rel, wavname, "%.3f" % (len(x) / sr),
               "%.3f" % rms_dbfs(x),
               "%.2f" % spectral_centroid_whole(x, sr),
               sha256_of(wav)]
        rows.append(row)
        print("  len=%ss  RMS=%s dBFS  centroid=%s Hz  sha256=%s"
              % (row[3], row[4], row[5], row[6][:16]), flush=True)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["piece", "score_path", "wav", "len_s", "rms_dbfs",
                    "centroid_hz", "sha256"])
        w.writerows(rows)
    print("wrote", out_csv)


if __name__ == "__main__":
    sys.exit(main())
