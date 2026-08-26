#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 Rule 10 report -- damping_override MIDI-60 anchor T60 (before/after).

Finds every *.score.json under scores/ that uses `damping_override`
(in `track_profiles` entries or per-event `params`), extracts the unique
mode-relevant parameter combos, and measures each combo's T60 at the
MIDI 60 anchor via `TsukiSynthCLI --dump-modes` -- the same center-string
fundamental readout as reports/gate_outputs/b2_attack_energy_remeasure.txt
and this directory's t60_material_grid.py.

Why MIDI 60: `damping_override`'s number semantics are anchored at MIDI 60
(see src/physics/MaterialDB.h around line 58 and StringModel.h's
decayTimeForFrequency doc). B2 preserved this anchor's T60; B3 will not
(the new Cuesta air+visc+dislocation terms add on top), so this file is
the honest "before" record of what changes.

Probe construction: engine + the mode-relevant params copied verbatim from
the source occurrence (material, diameter_mm, tension_n, num_strings,
detuning_cents, damping_override; strike_position/exciter forced to the
anchor convention 0.3/wood_mallet since they do not enter the decay law),
note = 60, velocity = 0.5, effects off, no macros. Probe scores go to a
temp directory, never into the repo.

Usage (run from the repo root):
    python reports/gate_outputs/b3_method/damping_override_anchor.py --label before
    python reports/gate_outputs/b3_method/damping_override_anchor.py --label after

Outputs (in this directory):
    damping_override_anchor_<label>.csv  -- one row per unique combo
    damping_override_files_<label>.md    -- file list + per-file combo map
"""
import argparse
import csv
import glob
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_CLI = os.path.join(REPO, "build", "TsukiSynthCLI_artefacts", "Release",
                           "TsukiSynthCLI.exe")

MODE_PARAM_KEYS = ["material", "diameter_mm", "tension_n", "num_strings",
                   "detuning_cents", "damping_override"]

NOMINAL_C4 = 440.0 * 2.0 ** ((60 - 69) / 12.0)


def combo_from(engine, params):
    combo = {"engine": engine}
    for k in MODE_PARAM_KEYS:
        if k in params:
            combo[k] = params[k]
    return combo


def combo_key(combo):
    return json.dumps(combo, sort_keys=True)


def collect():
    """Return (files_with_override, {combo_key: combo}, {file: [combo_key...]})."""
    files = sorted(glob.glob(os.path.join(REPO, "scores", "**", "*.score.json"),
                             recursive=True))
    hit_files = []
    combos = {}
    file_map = {}
    for f in files:
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        keys_here = []
        for tp in (d.get("track_profiles") or {}).values():
            if "damping_override" in tp:
                c = combo_from(tp.get("engine"), tp)
                keys_here.append(combo_key(c))
                combos[combo_key(c)] = c
        for ev in d.get("events") or []:
            p = ev.get("params") or {}
            if "damping_override" in p:
                c = combo_from(ev.get("engine"), p)
                keys_here.append(combo_key(c))
                combos[combo_key(c)] = c
        if keys_here:
            rel = os.path.relpath(f, REPO).replace("\\", "/")
            hit_files.append(rel)
            file_map[rel] = sorted(set(keys_here))
    return hit_files, combos, file_map


def make_probe(combo):
    params = {k: combo[k] for k in MODE_PARAM_KEYS if k in combo}
    params["strike_position"] = 0.3
    params["exciter"] = "wood_mallet"
    return {
        "$schema": "TsukiSynth Score v1",
        "meta": {"title": "B3 damping_override anchor probe",
                 "id": "b3_override_anchor_probe",
                 "author": "B3 workcard before/after sampling",
                 "description": "MIDI 60, velocity 0.5; --dump-modes only."},
        "global": {"bpm": 100, "sample_rate": 48000, "master_volume": 0.8,
                   "effects": {"reverb": {"decay": 0, "wet": 0},
                               "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                               "distortion": {"type": "overdrive", "drive": 0,
                                              "instability": 0, "wet": 0}}},
        "events": [dict(time=0.0, duration=1.0, engine=combo["engine"],
                        note=60, velocity=0.5, params=params)],
        "export": {"filename": "b3_override_anchor_probe", "format": "wav",
                   "bit_depth": 24, "normalize": False,
                   "tail_silence_ms": 200},
    }


def measure(cli, combo, tmp, idx):
    spath = os.path.join(tmp, "anchor_probe_%02d.score.json" % idx)
    with open(spath, "w", encoding="utf-8") as f:
        json.dump(make_probe(combo), f)
    out = subprocess.run([cli, "--dump-modes", spath],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("--dump-modes failed for combo %s:\n%s\n%s"
                           % (combo, out.stdout, out.stderr))
    dump = json.loads(out.stdout)
    ev = dump["events"][0]
    strings = ev.get("strings") or [ev["partials"]]
    best = min(strings, key=lambda s: abs(s[0]["freq"] - NOMINAL_C4))
    return best[0]["freq"], best[0]["decay"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--cli", default=DEFAULT_CLI)
    args = ap.parse_args()

    outdir = os.path.dirname(os.path.abspath(__file__))
    hit_files, combos, file_map = collect()
    print("%d score files use damping_override" % len(hit_files))

    tmp = tempfile.mkdtemp(prefix="b3_override_anchor_")
    results = {}
    for i, (key, combo) in enumerate(sorted(combos.items())):
        f0, t60 = measure(args.cli, combo, tmp, i)
        results[key] = (f0, t60)
        print("combo %02d %-60s f0=%9.3f  T60=%.6g s"
              % (i, key[:60], f0, t60))

    csv_path = os.path.join(outdir,
                            "damping_override_anchor_%s.csv" % args.label)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["engine", "material", "diameter_mm", "tension_n",
                    "num_strings", "detuning_cents", "damping_override",
                    "anchor_f0_hz", "anchor_t60_s"])
        for key in sorted(results):
            c = json.loads(key)
            f0, t60 = results[key]
            w.writerow([c.get("engine"), c.get("material"),
                        c.get("diameter_mm", ""), c.get("tension_n", ""),
                        c.get("num_strings", ""), c.get("detuning_cents", ""),
                        c.get("damping_override"),
                        "%.4f" % f0, "%.6g" % t60])
    print("wrote", csv_path)

    md_path = os.path.join(outdir,
                           "damping_override_files_%s.md" % args.label)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# damping_override score inventory (%s)\n\n" % args.label)
        f.write("%d score files under scores/ use `damping_override` "
                "(track_profiles and/or event params).\n"
                "Anchor T60 measured at MIDI 60 per unique combo -- see "
                "damping_override_anchor_%s.csv.\n\n" % (len(hit_files),
                                                         args.label))
        f.write("| # | score file | combos (engine/material/diam/override -> T60@60 s) |\n")
        f.write("|---|---|---|\n")
        for n, rel in enumerate(hit_files, 1):
            cells = []
            for key in file_map[rel]:
                c = json.loads(key)
                f0, t60 = results[key]
                cells.append("%s/%s/d=%s/ov=%s -> %.4g s"
                             % (c.get("engine"), c.get("material"),
                                c.get("diameter_mm", "-"),
                                c.get("damping_override"), t60))
            f.write("| %d | `%s` | %s |\n" % (n, rel, "<br>".join(cells)))
    print("wrote", md_path)


if __name__ == "__main__":
    sys.exit(main())
