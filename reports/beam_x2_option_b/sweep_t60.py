#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925b-BR: tongue_drum (BeamModel) modal T60, base vs noX2, via --dump-modes.

Descriptive only (NOT a GATE; no thresholds). Writes:
  t60_sweep.csv   one row per (material, MIDI, mode) with both CLIs' decay/amp
  t60_formula_check.txt  max relative deviation of each CLI's dump from the
                  closed-form law in src/physics/BeamModel.h:50-58 evaluated
                  in float64 with data/materials.json values:
                    base : 1/T60 = 2*eta*f/2.2 + beta_air*f^2 + gamma_rad*f
                    noX2 : 1/T60 =   eta*f/2.2 + beta_air*f^2 + gamma_rad*f
Probe: one score per material, MIDI 21..108 one event each (1 s apart,
duration 0.5 s, velocity 0.5), engine tongue_drum, frequency_mode default
(= "midi", tuned), geometry = the shipped Moonlight tongue-drum main group
(2.6 mm / 24 mm / 100 mm / strike 0.44, exciter wood_mallet).  After MIDI
tuning the modal frequencies are f0 x the fixed cantilever ratios, so the
T60 of every mode depends only on (frequency, material) -- the geometry only
affects amplitudes and which modes survive the 20 kHz / Nyquist filter.

Usage: python sweep_t60.py --cli-base <abs exe> --cli-nox2 <abs exe> --probe-dir <outside repo>
"""
import argparse
import csv
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MIDI = list(range(21, 109))
K_ETA = 2.2  # MaterialDB::kEtaToDecayRate (src/physics/MaterialDB.h:83)


def materials():
    d = json.load(open(REPO / "data" / "materials.json", encoding="utf-8"))
    return d["materials"]


def probe_score(material):
    events = []
    for i, m in enumerate(MIDI):
        events.append({"time": float(i), "duration": 0.5, "engine": "tongue_drum",
                       "note": m, "velocity": 0.5,
                       "params": {"material": material, "thickness_mm": 2.6,
                                  "length_mm": 100, "width_mm": 24,
                                  "strike_position": 0.44, "exciter": "wood_mallet"}})
    return {"$schema": "TsukiSynth Score v1",
            "meta": {"title": "BR probe " + material, "id": "br_probe_" + material,
                     "author": "WF0925b-BR", "description": "BeamModel x2 probe"},
            "global": {"bpm": 60, "sample_rate": 48000, "master_volume": 1.0,
                       "effects": {"reverb": {"decay": 1.0, "wet": 0},
                                   "delay": {"time_ms": 0, "feedback": 0, "wet": 0}}},
            "events": events,
            "export": {"filename": "br_probe_" + material, "format": "wav",
                       "bit_depth": 24, "normalize": False, "tail_silence_ms": 0}}


def dump(cli, score_path):
    r = subprocess.run([cli, "--dump-modes", str(score_path)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout)["events"]


def t60_formula(f, dm, x2):
    den = (2.0 if x2 else 1.0) * dm["eta"] * f / K_ETA \
        + dm["beam_plate_beta_air"] * f * f + dm["beam_plate_gamma_radiation"] * f
    return 1.0 / den if den > 0 else 5.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli-base", required=True)
    ap.add_argument("--cli-nox2", required=True)
    ap.add_argument("--probe-dir", required=True)
    a = ap.parse_args()
    pdir = Path(a.probe_dir)
    if str(pdir.resolve()).lower().startswith(str(REPO).lower()):
        sys.exit("probe dir must be outside the repo")
    pdir.mkdir(parents=True, exist_ok=True)
    mats = materials()
    rows = []
    worst = {"base": 0.0, "nox2": 0.0}
    worst_cross = {"base_vs_x1": 0.0}
    for name, mat in mats.items():
        sp = pdir / ("br_probe_%s.score.json" % name)
        sp.write_text(json.dumps(probe_score(name), indent=1), encoding="utf-8")
        eb, ex = dump(a.cli_base, sp), dump(a.cli_nox2, sp)
        assert len(eb) == len(ex) == len(MIDI)
        dm = mat["damping"]
        for ib, ix in zip(eb, ex):
            assert ib["midi"] == ix["midi"]
            pb, px = ib["partials"], ix["partials"]
            assert len(pb) == len(px), (name, ib["midi"])
            for n, (b, x) in enumerate(zip(pb, px), start=1):
                f = float(b["freq"])
                assert abs(f - float(x["freq"])) < 1e-6, "frequency changed?"
                tb, tx = float(b["decay"]), float(x["decay"])
                fb, fx = t60_formula(f, dm, True), t60_formula(f, dm, False)
                worst["base"] = max(worst["base"], abs(tb / fb - 1))
                worst["nox2"] = max(worst["nox2"], abs(tx / fx - 1))
                worst_cross["base_vs_x1"] = max(worst_cross["base_vs_x1"], abs(tb / fx - 1))
                ab, ax = float(b["amp"]), float(x["amp"])
                rows.append({"material": name, "midi": ib["midi"], "mode": n,
                             "freq_hz": "%.3f" % f, "t60_base_s": "%.6g" % tb,
                             "t60_nox2_s": "%.6g" % tx, "t60_ratio": "%.5f" % (tx / tb),
                             "alpha_base_per_s": "%.6g" % (6.907755 / tb),
                             "alpha_nox2_per_s": "%.6g" % (6.907755 / tx),
                             "x2_share_of_base_rate": "%.4f" % (
                                 (dm["eta"] * f / K_ETA) / (1.0 / fb)),
                             "amp_base": "%.6g" % ab, "amp_nox2": "%.6g" % ax,
                             "amp_change_db": ("%+.3f" % (20 * math.log10(ax / ab)))
                             if ab > 0 and ax > 0 else ""})
        print("material %-12s done (%d events)" % (name, len(eb)), flush=True)
    with open(HERE / "t60_sweep.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    msg = ("rows=%d  materials=%d  MIDI %d..%d\n"
           "max |dump/formula - 1|  base vs x2-law : %.3e\n"
           "max |dump/formula - 1|  noX2 vs x1-law : %.3e\n"
           "max |base dump / x1-law - 1| (should be large, i.e. base really has x2): %.3e\n"
           % (len(rows), len(mats), MIDI[0], MIDI[-1], worst["base"], worst["nox2"],
              worst_cross["base_vs_x1"]))
    (HERE / "t60_formula_check.txt").write_text(msg, encoding="utf-8")
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
