#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B4 bit-invariance reference -- Wood / Cotton / Metal exciter probes.

B4 only changes the tau_c source for ExciterType::Felt on the
Cimbalom/piano string path; Wood, Cotton and Metal renders must stay
BIT-IDENTICAL (docs/workcards/B4.md Sec.6 step 7 / Sec.8 step 7). This
script freezes the reference: for each of the three non-Felt hammers it

  1. renders a one-event probe score (cimbalom, A4 = MIDI 69, velocity
     0.5, anchor-convention params: diameter 0.8 mm, strike 0.3, effects
     off, normalize off) and records the WAV SHA256;
  2. runs `--dump-modes` on the same probe and records EVERY partial amp
     of the center string (raw "amp" strings, 5 decimal places as the
     CLI prints them) plus the SHA256 of the full --dump-modes stdout.

After B4 lands, re-run with --label after: every SHA256 and every amp
line must be byte-for-byte identical to the before file (plain `fd`/
`diff` of the two txt files; the only allowed difference is the label
line itself).

The probe scores are regenerated deterministically (json.dump of the
same dict), so before/after runs feed the CLI identical input files.

Usage (run from the repo root):
    python reports/gate_outputs/b4_method/nonfelt_invariance.py --label before
    python reports/gate_outputs/b4_method/nonfelt_invariance.py --label after

Output: reports/gate_outputs/b4_method/nonfelt_invariance_<label>.txt
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_CLI = os.path.join(REPO, "build", "TsukiSynthCLI_artefacts", "Release",
                           "TsukiSynthCLI.exe")

# exciter string -> ExciterType (cimbalomExciterFromString): the three
# non-Felt hammers B4 must leave untouched.
EXCITERS = [("wood_mallet", "Wood"),
            ("cotton_mallet", "Cotton"),
            ("metal_mallet", "Metal")]
MIDI = 69  # A4


def make_probe(exciter):
    return {
        "$schema": "TsukiSynth Score v1",
        "meta": {
            "title": "B4 non-felt invariance probe",
            "id": "b4_nonfelt_probe",
            "author": "B4 workcard before/after sampling",
            "description": ("Single cimbalom A4, velocity 0.5, anchor-"
                            "convention params, non-Felt exciter; used for "
                            "the B4 bit-invariance check."),
        },
        "global": {
            "bpm": 100, "sample_rate": 48000, "master_volume": 0.8,
            "effects": {
                "reverb": {"decay": 0, "wet": 0},
                "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                "distortion": {"type": "overdrive", "drive": 0,
                               "instability": 0, "wet": 0},
            },
        },
        "events": [
            {"time": 0.0, "duration": 1.0, "engine": "cimbalom",
             "note": MIDI, "velocity": 0.5,
             "params": {"material": "steel", "diameter_mm": 0.8,
                        "strike_position": 0.3, "exciter": exciter}},
        ],
        "export": {"filename": "b4_nonfelt_probe", "format": "wav",
                   "bit_depth": 24, "normalize": False,
                   "tail_silence_ms": 200},
    }


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def nominal_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="'before' or 'after'")
    ap.add_argument("--cli", default=DEFAULT_CLI)
    args = ap.parse_args()

    outdir = os.path.dirname(os.path.abspath(__file__))
    out_txt = os.path.join(outdir, "nonfelt_invariance_%s.txt" % args.label)

    tmp = tempfile.mkdtemp(prefix="b4_nonfelt_")
    lines = []
    lines.append("B4 non-Felt bit-invariance reference (label=%s)" % args.label)
    lines.append("probe: cimbalom A4 (MIDI 69), velocity 0.5, steel, "
                 "diameter 0.8 mm, strike 0.3, effects off, normalize off")
    lines.append("after B4 every line below this header must be identical "
                 "to the before file.")
    lines.append("")

    for exciter, type_name in EXCITERS:
        probe = make_probe(exciter)
        spath = os.path.join(tmp, "probe_%s.score.json" % exciter)
        with open(spath, "w", encoding="utf-8") as f:
            json.dump(probe, f)

        # 1) render -> WAV SHA256
        piece_dir = os.path.join(tmp, "render_%s" % exciter)
        os.makedirs(piece_dir, exist_ok=True)
        out = subprocess.run([args.cli, spath, "--output", piece_dir],
                             capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        wavs = [f for f in os.listdir(piece_dir) if f.lower().endswith(".wav")]
        if out.returncode != 0 or len(wavs) != 1:
            raise RuntimeError("render failed for %s (rc=%d, wavs=%s):\n%s\n%s"
                               % (exciter, out.returncode, wavs,
                                  out.stdout, out.stderr))
        wav_sha = sha256_of(os.path.join(piece_dir, wavs[0]))

        # 2) --dump-modes -> stdout SHA256 + center-string amps
        dm = subprocess.run([args.cli, "--dump-modes", spath],
                            capture_output=True, text=True)
        if dm.returncode != 0:
            raise RuntimeError("--dump-modes failed for %s:\n%s\n%s"
                               % (exciter, dm.stdout, dm.stderr))
        dump_sha = hashlib.sha256(dm.stdout.encode("utf-8")).hexdigest()
        dump = json.loads(dm.stdout)
        ev = dump["events"][0]
        strings = ev.get("strings") or [ev["partials"]]
        target = nominal_hz(MIDI)
        center = min(strings, key=lambda s: abs(s[0]["freq"] - target))

        lines.append("== exciter=%s (ExciterType::%s) ==" % (exciter, type_name))
        lines.append("wav_sha256        = %s" % wav_sha)
        lines.append("dump_modes_sha256 = %s" % dump_sha)
        lines.append("center_string_f0  = %.4f Hz (%d partials)"
                     % (center[0]["freq"], len(center)))
        lines.append("center_string_amps = "
                     + " ".join("%.5f" % p["amp"] for p in center))
        lines.append("")
        print("%-13s wav=%s dump=%s" % (exciter, wav_sha[:16], dump_sha[:16]),
              flush=True)

    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote", out_txt)


if __name__ == "__main__":
    sys.exit(main())
