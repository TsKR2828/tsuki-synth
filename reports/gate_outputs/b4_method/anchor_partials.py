#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B4 Rule 10 report -- C2/C4/C7 anchor-note partial table (Felt piano path).

For each anchor note of the hammer K/alpha table (C2=36, C4=60, C7=96 --
docs/HAMMER_CONTACT_SOURCES.md Sec.2.1) and each of two velocities
(48/127 and 96/127, as required by docs/workcards/B4.md Sec.9), a
one-event probe score with engine "piano" and NO param overrides is fed
to `TsukiSynthCLI --dump-modes`. The piano branch of ScoreRenderer.h
remaps the default exciter wood_mallet -> felt and strike 0.3 -> 0.125,
so this is exactly the Felt-exciter piano path whose tau_c source B4
replaces.

Read-out: the CENTER STRING (the string of the default 3-string course
whose fundamental is closest to the nominal ET frequency of the MIDI
note -- the same convention as b3_method/t60_material_grid.py and the
B2 report), first 5 partials, amplitude in dB re the fundamental
(20*log10(amp_i / amp_1); partial 1 is 0 dB by definition -- kept in the
CSV as a self-check column).

Usage (run from the repo root):
    python reports/gate_outputs/b4_method/anchor_partials.py --label before
    python reports/gate_outputs/b4_method/anchor_partials.py --label after

Output: reports/gate_outputs/b4_method/anchor_partials_<label>.csv
Columns: note_name,midi,vel_midi,vel_float,center_string_f0_hz,
         p1_db,p2_db,p3_db,p4_db,p5_db,
         p1_amp,p2_amp,p3_amp,p4_amp,p5_amp
(pN_amp = raw relative_modal_amplitude straight from --dump-modes, kept
so the after-run can also be compared without the dB re-derivation.)

Probe scores are written to a temp directory, never into the repo.
"""
import argparse
import csv
import json
import math
import os
import subprocess
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_CLI = os.path.join(REPO, "build", "TsukiSynthCLI_artefacts", "Release",
                           "TsukiSynthCLI.exe")

ANCHORS = [("C2", 36), ("C4", 60), ("C7", 96)]
VELOCITIES = [48, 96]  # MIDI velocity; score velocity = v/127


def nominal_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def make_probe(midi, vel_float):
    return {
        "$schema": "TsukiSynth Score v1",
        "meta": {
            "title": "B4 anchor partial probe",
            "id": "b4_anchor_partial_probe",
            "author": "B4 workcard before/after sampling",
            "description": ("Single piano note, no param overrides (piano "
                            "branch remaps wood_mallet->felt, strike "
                            "0.3->0.125); used only for --dump-modes."),
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
            {"time": 0.0, "duration": 1.0, "engine": "piano",
             "note": midi, "velocity": vel_float},
        ],
        "export": {"filename": "b4_anchor_partial_probe", "format": "wav",
                   "bit_depth": 24, "normalize": False,
                   "tail_silence_ms": 200},
    }


def dump_modes(cli, score_path):
    out = subprocess.run([cli, "--dump-modes", score_path],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("--dump-modes failed for %s:\n%s\n%s"
                           % (score_path, out.stdout, out.stderr))
    return json.loads(out.stdout)


def center_string(dump, midi):
    ev = dump["events"][0]
    strings = ev.get("strings") or [ev["partials"]]
    target = nominal_hz(midi)
    return min(strings, key=lambda s: abs(s[0]["freq"] - target))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="'before' or 'after'")
    ap.add_argument("--cli", default=DEFAULT_CLI)
    args = ap.parse_args()

    outdir = os.path.dirname(os.path.abspath(__file__))
    out_csv = os.path.join(outdir, "anchor_partials_%s.csv" % args.label)

    tmp = tempfile.mkdtemp(prefix="b4_anchor_")
    rows = []
    for name, midi in ANCHORS:
        for vel_midi in VELOCITIES:
            vel_float = vel_midi / 127.0
            probe = make_probe(midi, vel_float)
            spath = os.path.join(tmp, "probe_%d_v%d.score.json"
                                 % (midi, vel_midi))
            with open(spath, "w", encoding="utf-8") as f:
                json.dump(probe, f)
            dump = dump_modes(args.cli, spath)
            partials = center_string(dump, midi)[:5]
            if len(partials) < 5:
                raise RuntimeError("only %d partials for midi %d"
                                   % (len(partials), midi))
            a1 = partials[0]["amp"]
            dbs = [20.0 * math.log10(p["amp"] / a1) for p in partials]
            rows.append([name, midi, vel_midi, "%.10f" % vel_float,
                         "%.4f" % partials[0]["freq"]]
                        + ["%.4f" % d for d in dbs]
                        + ["%.6g" % p["amp"] for p in partials])
            print("%-3s midi=%3d vel=%3d/127  f0=%9.3f Hz  "
                  "p1..p5 dB re fund: %s"
                  % (name, midi, vel_midi, partials[0]["freq"],
                     "  ".join("%+.2f" % d for d in dbs)), flush=True)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["note_name", "midi", "vel_midi", "vel_float",
                    "center_string_f0_hz",
                    "p1_db", "p2_db", "p3_db", "p4_db", "p5_db",
                    "p1_amp", "p2_amp", "p3_amp", "p4_amp", "p5_amp"])
        w.writerows(rows)
    print("wrote", out_csv)


if __name__ == "__main__":
    sys.exit(main())
