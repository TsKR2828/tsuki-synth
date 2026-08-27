#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B4 Rule 10 report -- per-felt-event model f0/T60 invariance table.

B4 replaces ONLY the tau_c source of the Felt path. In CimbalomEngine.h,
tau_c feeds HammerImpulse::forceSpectrumMagnitude() (mode AMPLITUDE
weighting) and the fixed-v=0.5 loudness-compensation reference; mode
frequency and decayTime come from StringModel::* with no tau_c input.
So model f0 and model T60 of every felt event must be EXACTLY unchanged.

This script proves it per felt event of the affected scores without
needing the before binary, via an exciter-swap probe closed by the
non-Felt bit-invariance chain:

  For each affected (non-layered) score, dump modes twice with the SAME
  (current, B4-after) CLI:
    (o) the original score        -> felt events take pianoHammerTauC()
    (s) a temp copy whose felt events get params.exciter="cotton_mallet"
                                  -> the SAME events take the pre-B4
                                     tauCForNote() path (Cotton)
  and require, felt event by felt event, string by string, partial by
  partial: freq(o) == freq(s) AND decay(o) == decay(s) EXACTLY, while
  the amp columns DIFFER (sanity check that the swap really changed the
  excitation path).

Why (s) equals the true BEFORE values: (1) decay/freq never read tau_c
in either the HEAD or the working-tree code (only the amp weighting
does); (2) the non-Felt (Cotton/Wood/Metal) path is bit-identical
before/after B4 (nonfelt_invariance_{before,after}.txt: WAV and
--dump-modes SHA256 equal); (3) therefore before-felt freq/decay ==
before-cotton freq/decay == after-cotton freq/decay == after-felt
freq/decay -- the table's zero-difference claim is a closed chain of
code-level and bit-level evidence, not an assumption.

The layered ai_radiance_complete is excluded here: its only felt content
IS ai_radiance_m3's events (affected_scores_after.md), which are covered
by the m3 rows.

Piano-branch caveat handled: engine=piano events with the schema-default
exciter (wood_mallet) are remapped to felt by ScoreRenderer.h; setting
an explicit "cotton_mallet" is NOT remapped (the override only fires on
the exact string "wood_mallet"), so the swap lands on Cotton as intended.

Usage (from the repo root):
    python reports/gate_outputs/b4_method/t60_f0_felt_events.py --label after

Output: reports/gate_outputs/b4_method/t60_f0_felt_events_<label>.csv
Columns: piece,event_idx,engine,exciter,note,midi,velocity,
         center_f0_hz_felt,center_t60_s_felt,
         center_f0_hz_swap,center_t60_s_swap,
         all_freq_decay_equal,amps_differ,n_strings,n_partials
"""
import argparse
import copy
import csv
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_CLI = os.path.join(REPO, "build", "TsukiSynthCLI_artefacts", "Release",
                           "TsukiSynthCLI.exe")

FELT_EXCITERS = {"felt", "felt_mallet", "finger", "finger_tap", "rubber_mallet"}
STRING_PATH_ENGINES = {"string", "cimbalom", "piano"}


def effective_felt(engine, exciter):
    if engine not in STRING_PATH_ENGINES:
        return False
    if engine == "piano" and exciter == "wood_mallet":
        exciter = "felt"
    return exciter in FELT_EXCITERS


def nominal_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def dump_modes(cli, score_path):
    out = subprocess.run([cli, "--dump-modes", score_path],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("--dump-modes failed for %s:\n%s\n%s"
                           % (score_path, out.stdout, out.stderr))
    return json.loads(out.stdout)


def center_string(strings, midi):
    target = nominal_hz(midi)
    return min(strings, key=lambda s: abs(s[0]["freq"] - target))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--cli", default=DEFAULT_CLI)
    args = ap.parse_args()

    outdir = os.path.dirname(os.path.abspath(__file__))
    listing = os.path.join(outdir, "affected_scores_%s.json" % args.label)
    with open(listing, "r", encoding="utf-8") as f:
        affected = json.load(f)["affected"]

    rows = []
    all_equal = True
    any_swap_ineffective = False
    for entry in affected:
        if entry.get("via_layers"):
            print("skip (layered; felt content covered by its source rows):",
                  entry["score"])
            continue
        rel = entry["score"]
        name = os.path.basename(rel).replace(".score.json", "")
        spath = os.path.join(REPO, rel)
        with open(spath, "r", encoding="utf-8") as f:
            doc = json.load(f)

        felt_idx = []
        for i, ev in enumerate(doc.get("events") or []):
            engine = ev.get("engine", "")
            exciter = (ev.get("params") or {}).get("exciter", "wood_mallet")
            if effective_felt(engine, exciter):
                felt_idx.append(i)

        swapped = copy.deepcopy(doc)
        for i in felt_idx:
            params = swapped["events"][i].setdefault("params", {})
            params["exciter"] = "cotton_mallet"

        with tempfile.TemporaryDirectory(prefix="b4_t60f0_") as td:
            spath_sw = os.path.join(td, name + "_cottonswap.score.json")
            with open(spath_sw, "w", encoding="utf-8") as f:
                json.dump(swapped, f)
            dump_o = dump_modes(args.cli, spath)
            dump_s = dump_modes(args.cli, spath_sw)

        ev_o = {e["source_index"]: e for e in dump_o["events"]}
        ev_s = {e["source_index"]: e for e in dump_s["events"]}

        for i in felt_idx:
            o, s = ev_o[i], ev_s[i]
            so = o.get("strings") or [o["partials"]]
            ss = s.get("strings") or [s["partials"]]
            eq = (len(so) == len(ss))
            amps_differ = False
            npart = 0
            if eq:
                for stro, strs in zip(so, ss):
                    if len(stro) != len(strs):
                        eq = False
                        break
                    npart = max(npart, len(stro))
                    for po, ps in zip(stro, strs):
                        if po["freq"] != ps["freq"] or po["decay"] != ps["decay"]:
                            eq = False
                            break
                        if po["amp"] != ps["amp"]:
                            amps_differ = True
                    if not eq:
                        break
            all_equal = all_equal and eq
            if not amps_differ:
                any_swap_ineffective = True
            co = center_string(so, o["midi"])
            cs = center_string(ss, s["midi"])
            src_ev = doc["events"][i]
            rows.append([
                name, i, src_ev.get("engine"),
                (src_ev.get("params") or {}).get("exciter", "(default)"),
                src_ev.get("note"), o["midi"], src_ev.get("velocity"),
                "%.6f" % co[0]["freq"], "%.6f" % co[0]["decay"],
                "%.6f" % cs[0]["freq"], "%.6f" % cs[0]["decay"],
                "EQUAL" if eq else "DIFFER",
                "yes" if amps_differ else "NO (swap ineffective?)",
                len(so), npart,
            ])
            print("%-18s ev%-3d %-8s midi=%3d f0=%10.4f T60=%9.4f s  "
                  "freq/decay felt-vs-cotton: %s  amps differ: %s"
                  % (name, i, src_ev.get("engine"), o["midi"],
                     co[0]["freq"], co[0]["decay"],
                     "EQUAL" if eq else "DIFFER",
                     "yes" if amps_differ else "NO"), flush=True)

    out_csv = os.path.join(outdir, "t60_f0_felt_events_%s.csv" % args.label)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["piece", "event_idx", "engine", "exciter", "note", "midi",
                    "velocity", "center_f0_hz_felt", "center_t60_s_felt",
                    "center_f0_hz_swap", "center_t60_s_swap",
                    "all_freq_decay_equal", "amps_differ",
                    "n_strings", "n_partials"])
        w.writerows(rows)
    print("wrote", out_csv)
    print("ALL freq/decay EXACTLY EQUAL: %s; every swap changed amps: %s"
          % (all_equal, not any_swap_ineffective))
    return 0 if (all_equal and not any_swap_ineffective) else 1


if __name__ == "__main__":
    sys.exit(main())
