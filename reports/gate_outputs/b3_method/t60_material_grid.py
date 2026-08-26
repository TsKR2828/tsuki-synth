#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 Rule 10 report -- T60 material/note grid (before/after sampling).

Method: identical to the B2 report's Sec.1 measurement
(reports/b1_b2_bridge_damping_before_after.md) -- a one-event probe score
(cimbalom, velocity 0.5, default anchor-convention params: diameter 0.8 mm,
strike_position 0.3, wood_mallet, reverb/delay/distortion off, no macros)
is passed to `TsukiSynthCLI --dump-modes`, and the FUNDAMENTAL (first
partial) T60 of the CENTER STRING is read out. Center string = the string
of the default 3-string course whose fundamental is closest to the nominal
equal-tempered frequency of the MIDI note (freqMul = 1, matScale = dmpScale
= 1 under default macros), i.e. the same "central string" convention as
reports/gate_outputs/b2_attack_energy_remeasure.txt.

Grid: steel / aluminum / rubber  x  C2(36) / C4(60) / C6(84) / C8(108)
(the three materials the B3 workcard Sec.9 item 2 requires: low / mid /
high eta representatives).

Usage (run from the repo root):
    python reports/gate_outputs/b3_method/t60_material_grid.py --label before
    python reports/gate_outputs/b3_method/t60_material_grid.py --label after

Output: reports/gate_outputs/b3_method/t60_material_grid_<label>.csv
Columns: material,note_name,midi,nominal_hz,center_string_f0_hz,t60_s

Probe scores are written to a fresh temp directory (never into the repo).
The script is deliberately read-only with respect to src/data/tests.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_CLI = os.path.join(REPO, "build", "TsukiSynthCLI_artefacts", "Release",
                           "TsukiSynthCLI.exe")

MATERIALS = ["steel", "aluminum", "rubber"]
NOTES = [("C2", 36), ("C4", 60), ("C6", 84), ("C8", 108)]


def nominal_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def make_probe(midi, material):
    return {
        "$schema": "TsukiSynth Score v1",
        "meta": {
            "title": "B3 T60 grid probe",
            "id": "b3_t60_grid_probe",
            "author": "B3 workcard before/after sampling",
            "description": ("Single cimbalom note, velocity 0.5, anchor-"
                            "convention params; used only for --dump-modes, "
                            "never rendered as a deliverable."),
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
             "note": midi, "velocity": 0.5,
             "params": {"material": material, "diameter_mm": 0.8,
                        "strike_position": 0.3, "exciter": "wood_mallet"}},
        ],
        "export": {"filename": "b3_t60_grid_probe", "format": "wav",
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


def center_string_fundamental(dump, midi):
    """Return (f0_hz, t60_s) of the string whose fundamental is closest to
    the nominal ET frequency of `midi` (B2 center-string convention)."""
    ev = dump["events"][0]
    strings = ev.get("strings") or [ev["partials"]]
    target = nominal_hz(midi)
    best = min(strings, key=lambda s: abs(s[0]["freq"] - target))
    return best[0]["freq"], best[0]["decay"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True,
                    help="'before' or 'after' -- suffix of the output CSV")
    ap.add_argument("--cli", default=DEFAULT_CLI)
    args = ap.parse_args()

    outdir = os.path.dirname(os.path.abspath(__file__))
    out_csv = os.path.join(outdir, "t60_material_grid_%s.csv" % args.label)

    tmp = tempfile.mkdtemp(prefix="b3_t60_grid_")
    rows = []
    for material in MATERIALS:
        for name, midi in NOTES:
            probe = make_probe(midi, material)
            spath = os.path.join(tmp, "probe_%s_%d.score.json"
                                 % (material, midi))
            with open(spath, "w", encoding="utf-8") as f:
                json.dump(probe, f)
            dump = dump_modes(args.cli, spath)
            f0, t60 = center_string_fundamental(dump, midi)
            rows.append([material, name, midi,
                         "%.4f" % nominal_hz(midi), "%.4f" % f0,
                         "%.6g" % t60])
            print("%-9s %-3s midi=%3d  f0=%9.3f Hz  T60=%s s"
                  % (material, name, midi, f0, rows[-1][-1]))

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["material", "note_name", "midi", "nominal_hz",
                    "center_string_f0_hz", "t60_s"])
        w.writerows(rows)
    print("wrote", out_csv)


if __name__ == "__main__":
    sys.exit(main())
