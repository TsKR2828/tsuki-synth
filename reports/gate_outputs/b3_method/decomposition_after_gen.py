#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 workcard Sec.6 step 15 -- per-mechanism decay-rate decomposition (AFTER).

For steel / aluminum / rubber at C2/C4/C6/C8 this prints and stores, term by
term, the three decay-rate channels of the post-B3 string damping law

    1/T60(f) = eta*f/2.2  +  (Qinv_air+Qinv_visc+Qinv_disl)*f/2.2  +  bridgeLoss

 - "eta"    : internal friction (Phase H traced loss factor)
 - "three"  : B3 Cuesta & Valette air-viscosity + viscoelastic + dislocation
              (each sub-term also reported separately)
 - "bridge" : B1 bridge/soundboard coupling (frequency independent)

The parameter chain mirrors the CLI noteOn path exactly (float64 mirror of
the float32 engine math): L = lengthFromMidiNote, r = 0.8mm/2 (anchor probe
convention), T = tensionForNote, soundboard = wood_spruce @ h = 9 mm.
Each row is CROSS-CHECKED against the actual binary: the same probe score as
t60_material_grid.py is run through `TsukiSynthCLI --dump-modes` and the
mirror's 1/(sum of terms) is compared with the binary's fundamental T60.

This is the data source for the B3 Rule 10 report's decomposition table
(workcard Sec.9 item 3) and the dislocation-vs-eta share table (item 4).

Usage (repo root):  python reports/gate_outputs/b3_method/decomposition_after_gen.py
Output:             reports/gate_outputs/b3_method/decomposition_after.json
"""
import json
import math
import os
import subprocess
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CLI = os.path.join(REPO, "build", "TsukiSynthCLI_artefacts", "Release",
                   "TsukiSynthCLI.exe")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "decomposition_after.json")

# --- constants mirrored from the C++ sources (values, not re-derivations) ---
K_ETA_TO_DECAY = 2.2                 # MaterialDB::kEtaToDecayRate
LN1000 = 6.907755278982137           # StringModel::bridgeLossRate kLn1000
AIR_DENSITY = 1.225                  # StringModel::kAirDensity
AIR_KIN_VISC = 1.619e-5              # StringModel::kAirKinematicViscosity
DISL_QINV = 1.0 / 18000.0            # StringModel::kDislocationQInv
SOUNDBOARD_H = 0.009                 # CimbalomEngine kBridgeSoundboardThicknessM
DIAMETER = 0.8e-3                    # anchor probe convention (0.8 mm)
RADIUS = DIAMETER / 2.0

# materials.json values (density, youngs_modulus, eta)
MATERIALS = {
    "steel":    {"rho": 7800.0, "E": 200e9, "eta": 2.0e-4},
    "aluminum": {"rho": 2700.0, "E": 70e9,  "eta": 1.0e-4},
    "rubber":   {"rho": 1100.0, "E": 5e6,   "eta": 3.0e-1},
}
SPRUCE = {"rho": 450.0, "E": 12e9, "nu": 0.37}
NOTES = [("C2", 36), ("C4", 60), ("C6", 84), ("C8", 108)]


def nominal_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def length_from_midi(midi):
    return 0.35 * 2.0 ** (-(midi - 69) / 12.0)


def tension_for_note(midi, length, diameter, density):
    target = nominal_hz(midi)
    r = diameter / 2.0
    mu = density * math.pi * r * r
    v = 2.0 * length * target
    return mu * v * v


def q_inv_three(f, r, tension, rho, E):
    omega = 2.0 * math.pi * f
    M = (r / 2.0) * math.sqrt(omega / AIR_KIN_VISC)
    q_air = (AIR_DENSITY / rho) * (math.sqrt(2.0) / M + 1.0 / (2.0 * M * M))
    q_visc = 0.003 * E * rho * math.pi ** 2 * r ** 6 * omega ** 2 \
        / (4.0 * tension * tension)
    return q_air, q_visc, DISL_QINV


def bridge_loss(tension, length):
    E, nu, rho = SPRUCE["E"], SPRUCE["nu"], SPRUCE["rho"]
    h = SOUNDBOARD_H
    D = E * h ** 3 / (12.0 * (1.0 - nu * nu))
    rho_s = rho * h
    y_inf = 1.0 / (8.0 * math.sqrt(D * rho_s))
    return tension * y_inf / (LN1000 * length)


def make_probe(midi, material):
    # identical probe to t60_material_grid.py (anchor convention)
    return {
        "$schema": "TsukiSynth Score v1",
        "meta": {"title": "B3 decomposition probe", "id": "b3_decomp_probe",
                 "author": "B3 workcard step 15",
                 "description": "single note, --dump-modes only"},
        "global": {"bpm": 100, "sample_rate": 48000, "master_volume": 0.8,
                   "effects": {"reverb": {"decay": 0, "wet": 0},
                               "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                               "distortion": {"type": "overdrive", "drive": 0,
                                              "instability": 0, "wet": 0}}},
        "events": [{"time": 0.0, "duration": 1.0, "engine": "cimbalom",
                    "note": midi, "velocity": 0.5,
                    "params": {"material": material, "diameter_mm": 0.8,
                               "strike_position": 0.3,
                               "exciter": "wood_mallet"}}],
        "export": {"filename": "b3_decomp_probe", "format": "wav",
                   "bit_depth": 24, "normalize": False,
                   "tail_silence_ms": 200},
    }


def binary_fundamental(midi, material, tmp):
    spath = os.path.join(tmp, "probe_%s_%d.score.json" % (material, midi))
    with open(spath, "w", encoding="utf-8") as f:
        json.dump(make_probe(midi, material), f)
    out = subprocess.run([CLI, "--dump-modes", spath],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("--dump-modes failed:\n%s\n%s"
                           % (out.stdout, out.stderr))
    dump = json.loads(out.stdout)
    ev = dump["events"][0]
    strings = ev.get("strings") or [ev["partials"]]
    target = nominal_hz(midi)
    best = min(strings, key=lambda s: abs(s[0]["freq"] - target))
    return best[0]["freq"], best[0]["decay"]


def main():
    tmp = tempfile.mkdtemp(prefix="b3_decomp_")
    result = {
        "_meta": {
            "generated": "2026-08-24",
            "workcard": "docs/workcards/B3.md Sec.6 step 15",
            "law": "1/T60 = eta*f/2.2 + (Qinv_air+Qinv_visc+Qinv_disl)*f/2.2"
                   " + bridgeLoss",
            "chain": "L=lengthFromMidiNote, r=0.4mm (0.8mm anchor probe),"
                     " T=tensionForNote, soundboard wood_spruce h=9mm",
            "units": "rates in 1/s (contributions to 1/T60); shares"
                     " relative to the summed rate",
            "cross_check": "T60_mirror=1/(sum of rates) vs the binary's"
                           " --dump-modes fundamental decay (same probe as"
                           " t60_material_grid.py)",
        },
        "dislocation_vs_eta_share": {},
        "rows": [],
    }
    print("%-9s %-3s %10s | %10s %10s %10s %10s | %10s %10s | %9s %9s %7s"
          % ("material", "nt", "f0_hz", "rate_eta", "rate_air", "rate_visc",
             "rate_disl", "rate_3mech", "rate_bridge", "T60_mirr", "T60_bin",
             "mism%"))
    worst_mismatch = 0.0
    for mname, mat in MATERIALS.items():
        result["dislocation_vs_eta_share"][mname] = {
            "eta": mat["eta"],
            "disl_qinv_over_eta_percent": 100.0 * DISL_QINV / mat["eta"],
        }
        for note, midi in NOTES:
            L = length_from_midi(midi)
            T = tension_for_note(midi, L, DIAMETER, mat["rho"])
            f0_bin, t60_bin = binary_fundamental(midi, mname, tmp)
            f = f0_bin  # evaluate the mirror at the binary's tuned fundamental
            q_air, q_visc, q_disl = q_inv_three(f, RADIUS, T,
                                                mat["rho"], mat["E"])
            rate_eta = mat["eta"] * f / K_ETA_TO_DECAY
            rate_air = q_air * f / K_ETA_TO_DECAY
            rate_visc = q_visc * f / K_ETA_TO_DECAY
            rate_disl = q_disl * f / K_ETA_TO_DECAY
            rate_three = rate_air + rate_visc + rate_disl
            rate_bridge = bridge_loss(T, L)
            total = rate_eta + rate_three + rate_bridge
            t60_mirror = 1.0 / total
            mismatch = abs(t60_mirror / t60_bin - 1.0) * 100.0
            worst_mismatch = max(worst_mismatch, mismatch)
            row = {
                "material": mname, "note": note, "midi": midi,
                "f0_hz": round(f0_bin, 4),
                "string_length_m": round(L, 6),
                "string_tension_n": round(T, 4),
                "rate_eta": rate_eta,
                "rate_air": rate_air,
                "rate_visc": rate_visc,
                "rate_disl": rate_disl,
                "rate_three_mech": rate_three,
                "rate_bridge": rate_bridge,
                "rate_total": total,
                "share_eta": rate_eta / total,
                "share_three_mech": rate_three / total,
                "share_bridge": rate_bridge / total,
                "three_mech_internal_share": {
                    "air": rate_air / rate_three,
                    "visc": rate_visc / rate_three,
                    "disl": rate_disl / rate_three,
                },
                "t60_mirror_s": t60_mirror,
                "t60_binary_s": t60_bin,
                "mirror_vs_binary_mismatch_percent": mismatch,
            }
            result["rows"].append(row)
            print("%-9s %-3s %10.3f | %10.5f %10.5f %10.5f %10.5f |"
                  " %10.5f %10.5f | %9.4f %9.4f %6.3f%%"
                  % (mname, note, f, rate_eta, rate_air, rate_visc, rate_disl,
                     rate_three, rate_bridge, t60_mirror, t60_bin, mismatch))
    # Sec.4.2 qualitative distribution check (within the three mechanisms):
    # air dominates the low end, viscoelastic dominates the high end.
    steel_rows = [r for r in result["rows"] if r["material"] == "steel"]
    c2 = next(r for r in steel_rows if r["note"] == "C2")
    c8 = next(r for r in steel_rows if r["note"] == "C8")
    dist_ok = (c2["three_mech_internal_share"]["air"] >
               max(c2["three_mech_internal_share"]["visc"],
                   c2["three_mech_internal_share"]["disl"])) and \
              (c8["three_mech_internal_share"]["visc"] >
               max(c8["three_mech_internal_share"]["air"],
                   c8["three_mech_internal_share"]["disl"]))
    result["_meta"]["sec42_distribution_check"] = (
        "PASS: steel C2 air-dominated (%.1f%%), C8 viscoelastic-dominated"
        " (%.1f%%)" % (100 * c2["three_mech_internal_share"]["air"],
                       100 * c8["three_mech_internal_share"]["visc"])
        if dist_ok else "FAIL")
    result["_meta"]["worst_mirror_vs_binary_mismatch_percent"] = worst_mismatch
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print("\nSec 4.2 distribution check:",
          result["_meta"]["sec42_distribution_check"])
    print("worst mirror-vs-binary mismatch: %.4f%%" % worst_mismatch)
    print("wrote", OUT)
    return 0 if dist_ok else 1


if __name__ == "__main__":
    sys.exit(main())
