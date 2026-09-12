#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A14 B-2 Rule-10 report -- render + f0/T60 fingerprint for the 5 corpus
scores A14 identifies as touching the Felt tau_c path
(docs/workcards/WF0908_P2_a14_tauc_rule10.md §3 step 6).

Adaptation of reports/gate_outputs/b4_method/render_affected_pieces.py
(same RMS/centroid/SHA256 metric definitions, same CLI invocation) plus a
--dump-modes based freq/decay fingerprint (sha256 over every partial's
freq+decay across every string and every event in the score, rounded to
6 decimals) to prove tau_c changes only the modal AMPLITUDE weighting, not
frequency or decay time -- same closed-chain argument as B4 report §2b/§3,
but computed directly over the real affected pieces rather than a
hand-picked event subset.

Usage (repo root; workdir must be OUTSIDE the repo):
    python reports/gate_outputs/wf0908_method/affected5_before_after.py ^
        --label before --workdir %TEMP%\\wf0908_p2_render_before
    python reports/gate_outputs/wf0908_method/affected5_before_after.py ^
        --label after --workdir %TEMP%\\wf0908_p2_render_after

Output:
    reports/gate_outputs/wf0908_method/affected5_render_<label>.csv
    reports/gate_outputs/wf0908_method/affected5_fingerprint_<label>.json
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import wave

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_CLI = os.path.join(REPO, "build", "TsukiSynthCLI_artefacts", "Release",
                           "TsukiSynthCLI.exe")

PIECES = [
    "scores/classical/fur_elise/fur_elise_complete.score.json",
    "scores/examples/physical_piano.score.json",
    "scores/library/akashic/akashic_action_001.score.json",
    "scores/library/ocean/ocean_action_001.score.json",
    "scores/originals/ai_radiance/ai_radiance_m3.score.json",
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


def dump_fingerprint(cli, score_path):
    """Runs --dump-modes and returns (freq_decay_sha256, amp_sha256,
    n_events, n_partials_total, felt_event_count_estimate)."""
    out = subprocess.run([cli, "--dump-modes", score_path],
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise RuntimeError("dump-modes failed for %s:\n%s\n%s"
                           % (score_path, out.stdout, out.stderr))
    dump = json.loads(out.stdout)
    fd_h = hashlib.sha256()
    amp_h = hashlib.sha256()
    n_events = 0
    n_partials = 0
    for ev in dump["events"]:
        n_events += 1
        for string in ev["strings"]:
            for p in string:
                fd_h.update(("%.6f|%.6f;" % (p["freq"], p["decay"])).encode("utf-8"))
                amp_h.update(("%.6f;" % p["amp"]).encode("utf-8"))
                n_partials += 1
    return fd_h.hexdigest(), amp_h.hexdigest(), n_events, n_partials


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--workdir", required=True,
                    help="render output dir; must be OUTSIDE the repo")
    ap.add_argument("--cli", default=DEFAULT_CLI)
    args = ap.parse_args()

    cli = os.path.abspath(args.cli)
    workdir = os.path.abspath(args.workdir)
    if (workdir + os.sep).startswith(REPO + os.sep):
        sys.exit("refusing to render inside the repo: " + workdir)
    os.makedirs(workdir, exist_ok=True)

    outdir = os.path.dirname(os.path.abspath(__file__))
    out_csv = os.path.join(outdir, "affected5_render_%s.csv" % args.label)
    out_fp = os.path.join(outdir, "affected5_fingerprint_%s.json" % args.label)

    rows = []
    fingerprints = {}
    for rel in PIECES:
        name = os.path.basename(rel).replace(".score.json", "")
        score = os.path.join(REPO, rel)
        piece_dir = os.path.join(workdir, name)
        os.makedirs(piece_dir, exist_ok=True)
        print("rendering", name, "...", flush=True)
        out = subprocess.run([cli, score, "--output", piece_dir],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        wavs = [f for f in os.listdir(piece_dir) if f.lower().endswith(".wav")]
        if out.returncode != 0 or len(wavs) != 1:
            raise RuntimeError("render failed for %s (rc=%d, wavs=%s):\n%s\n%s"
                               % (name, out.returncode, wavs, out.stdout, out.stderr))
        wavname = wavs[0]
        wav = os.path.join(piece_dir, wavname)
        sr, x = read_wav_mono(wav)
        row = [name, rel, wavname, "%.3f" % (len(x) / sr),
               "%.3f" % rms_dbfs(x), "%.2f" % spectral_centroid_whole(x, sr),
               sha256_of(wav)]
        rows.append(row)
        print("  len=%ss  RMS=%s dBFS  centroid=%s Hz  sha256=%s"
              % (row[3], row[4], row[5], row[6][:16]), flush=True)

        print("  dump-modes fingerprint ...", flush=True)
        fd_sha, amp_sha, n_ev, n_p = dump_fingerprint(cli, score)
        fingerprints[name] = {"score": rel, "freq_decay_sha256": fd_sha,
                              "amp_sha256": amp_sha, "n_events": n_ev,
                              "n_partials_total": n_p}
        print("  freq/decay sha256=%s  amp sha256=%s  events=%d partials=%d"
              % (fd_sha[:16], amp_sha[:16], n_ev, n_p), flush=True)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["piece", "score_path", "wav", "len_s", "rms_dbfs",
                    "centroid_hz", "sha256"])
        w.writerows(rows)
    print("wrote", out_csv)

    with open(out_fp, "w", encoding="utf-8") as f:
        json.dump(fingerprints, f, ensure_ascii=False, indent=2)
    print("wrote", out_fp)


if __name__ == "__main__":
    sys.exit(main())
