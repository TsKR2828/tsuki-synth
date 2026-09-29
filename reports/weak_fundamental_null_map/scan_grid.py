#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""WF0925-N1 步驟 1：MIDI 21-108 × velocity 網格的弱基頻零點地圖（--dump-modes 實測 + 理論並列）。

網格：velocity 0.050, 0.075, ..., 1.000（每 0.025，共 39 列，grid_kind=regular）
      + 該設定在 75 份 corpus 裡實際出現過的全部 velocity 值（grid_kind=corpus）。
設定（configs）——每組都是 corpus 實際在用的 engine/exciter/參數組合：
  piano_felt      piano 引擎、steel Ø1.0 mm、預設（→ felt 氈槌、擊弦點 0.125，pianoHammerTauC()）
                  = 給愛麗絲鋼琴版 fur_elise_complete（+ physical_piano）
  cimbalom_wood   cimbalom 引擎、steel Ø1.0 mm、預設（→ wood_mallet 0.5 ms、擊弦點 0.3，tauCForNote()）
                  = 給愛麗絲揚琴版 fur_elise_complete_cimbalom
  cimbalom_felt   cimbalom、felt_mallet、steel Ø0.58、strike 0.295、damping_override 0.28
                  （Felt → 同一條 pianoHammerTauC()）= ai_radiance_m3 的 16 顆
  string_bow      string、bow（→ Cotton 6 ms，tauCForNote()）、steel Ø0.55、strike 0.18、
                  damping_override 0.34 = 韋瓦第四季最常見的一組
每個 MIDI 音一份 score（所有 velocity 當成不同時間的事件），用 --cli 的 --dump-modes 取模態。
輸出：reports/weak_fundamental_null_map/grid_<config>.csv（每格一列）與 grid_summary.json。

用法（repo 根目錄）：
  python reports/weak_fundamental_null_map/scan_grid.py \
      --cli output/wf0925/N1/cli.exe --workdir output/wf0925/N1/grid
"""
import argparse
import collections
import csv
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import null_map_lib as L  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

CONFIGS = collections.OrderedDict([
    ("piano_felt", {
        "engine": "piano",
        "params": {"material": "steel", "diameter_mm": 1.0},
        "label": "piano 引擎（給愛麗絲鋼琴版）",
        "match": lambda eng, p: eng == "piano",
    }),
    ("cimbalom_wood", {
        "engine": "cimbalom",
        "params": {"material": "steel", "diameter_mm": 1.0},
        "label": "cimbalom 預設 wood_mallet（給愛麗絲揚琴版）",
        "match": lambda eng, p: eng == "cimbalom" and L.cimbalom_exciter_hardness(
            (p or {}).get("exciter", "wood_mallet")) == 2,
    }),
    ("cimbalom_felt", {
        "engine": "cimbalom",
        "params": {"material": "steel", "diameter_mm": 0.58, "strike_position": 0.295,
                   "exciter": "felt_mallet", "damping_override": 0.28},
        "label": "cimbalom felt_mallet（ai_radiance_m3）",
        "match": lambda eng, p: eng in ("cimbalom", "string") and L.cimbalom_exciter_hardness(
            (p or {}).get("exciter", "wood_mallet")) == 1,
    }),
    ("string_bow", {
        "engine": "string",
        "params": {"material": "steel", "diameter_mm": 0.55, "strike_position": 0.18,
                   "exciter": "bow", "damping_override": 0.34},
        "label": "string bow（韋瓦第四季）",
        "match": lambda eng, p: eng in ("string", "cimbalom") and L.cimbalom_exciter_hardness(
            (p or {}).get("exciter", "wood_mallet")) == 0,
    }),
])

REGULAR_V = [round(0.05 + 0.025 * i, 3) for i in range(39)]   # 0.050 .. 1.000
MIDI_RANGE = list(range(21, 109))

COLUMNS = ["config", "midi", "note", "velocity", "grid_kind",
           "exciter", "hardness", "strike", "tau_ms", "f1_hz", "f2_hz", "x1", "x2",
           "H1_db", "H2_db", "null_order", "null_depth_db",
           "n1n2_dump_db", "n1n2_theory_db", "n1n2_s0_db", "n1_vs_max_db", "L1_db",
           "n1_course", "n2_course", "low_precision", "n_strings"]


def corpus_velocities(match):
    vs = set()
    for f in L.corpus_files():
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        for e in d.get("events", []):
            if match(e.get("engine"), e.get("params")):
                v = float(e.get("velocity", 0.0))
                if v > 0:
                    vs.add(v)
    return sorted(vs)


def write_score(path, engine, params, midi, velocities):
    evs = []
    for i, v in enumerate(velocities):
        evs.append({"time": round(0.5 * i, 3), "duration": 0.2, "engine": engine,
                    "note": L.midi_to_name(midi), "velocity": v, "params": dict(params)})
    d = {"$schema": "TsukiSynth Score v1",
         "meta": {"title": "n1grid", "id": "n1grid", "author": "wf0925-N1",
                  "description": "WF0925-N1 null-map grid probe (dump-modes only)"},
         "global": {"bpm": 120, "sample_rate": 48000, "master_volume": 1.0,
                    "effects": {"reverb": {"decay": 1.0, "wet": 0.0},
                                "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                                "distortion": {"type": "overdrive", "drive": 0,
                                               "instability": 0, "wet": 0}}},
         "events": evs,
         "export": {"filename": "n1grid", "format": "wav", "bit_depth": 24,
                    "normalize": False, "tail_silence_ms": 500}}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", default=L.DEFAULT_CLI)
    ap.add_argument("--workdir", default=os.path.join(L.REPO, "output", "wf0925", "N1", "grid"))
    ap.add_argument("--configs", default=",".join(CONFIGS.keys()))
    args = ap.parse_args()
    cli = os.path.abspath(args.cli)
    os.makedirs(args.workdir, exist_ok=True)

    summary = {"cli": cli, "regular_velocities": REGULAR_V, "midi_range": [21, 108], "configs": {}}
    for name in args.configs.split(","):
        cfg = CONFIGS[name]
        cvs = corpus_velocities(cfg["match"])
        extra = [v for v in cvs if all(abs(v - r) > 1e-9 for r in REGULAR_V)]
        vels = [(v, "regular") for v in REGULAR_V] + [(v, "corpus") for v in extra]
        # corpus 值剛好落在規則網格上的，也標記出來（grid_kind 仍是 regular）
        on_grid = [v for v in cvs if any(abs(v - r) <= 1e-9 for r in REGULAR_V)]
        rows = []
        diffs = []          # theory - dump (dB), well-resolved cells only
        diffs_all = []
        for midi in MIDI_RANGE:
            sp = os.path.join(args.workdir, "%s_midi%03d.score.json" % (name, midi))
            write_score(sp, cfg["engine"], cfg["params"], midi, [v for v, _ in vels])
            dump = L.run_dump(cli, sp)
            evs = {e["source_index"]: e for e in dump["events"]}
            if len(evs) != len(vels):
                raise RuntimeError("%s midi %d: dumped %d events, expected %d"
                                   % (name, midi, len(evs), len(vels)))
            for i, (v, kind) in enumerate(vels):
                m = L.event_metrics(evs[i], v, cfg["engine"], cfg["params"])
                row = {"config": name, "midi": midi, "note": L.midi_to_name(midi),
                       "velocity": v, "grid_kind": kind}
                row.update(m)
                rows.append(row)
                a, b = m.get("n1n2_theory_db"), m.get("n1n2_dump_db")
                if a is not None and b is not None:
                    diffs_all.append(a - b)
                    if not m.get("low_precision"):
                        diffs.append(a - b)
            print("[%s] MIDI %3d  %d cells" % (name, midi, len(vels)), flush=True)

        out_csv = os.path.join(HERE, "grid_%s.csv" % name)
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(COLUMNS)
            for r in rows:
                w.writerow([L.fmt(r.get(c), 4) if isinstance(r.get(c), float) else L.fmt(r.get(c))
                            for c in COLUMNS])
        reg = [r for r in rows if r["grid_kind"] == "regular" and r.get("n1n2_dump_db") is not None]
        n_f1 = sum(1 for r in reg if r["n1n2_dump_db"] < -10.0)
        n_f2 = sum(1 for r in reg if r["null_depth_db"] <= -10.0)
        n_any = sum(1 for r in reg if r["n1n2_dump_db"] < -10.0 or r["null_depth_db"] <= -10.0)

        def stats(xs):
            if not xs:
                return None
            xs = sorted(xs)
            return {"n": len(xs), "min": xs[0], "max": xs[-1],
                    "mean": sum(xs) / len(xs), "abs_max": max(abs(xs[0]), abs(xs[-1])),
                    "p99_abs": sorted(abs(x) for x in xs)[int(0.99 * (len(xs) - 1))]}

        summary["configs"][name] = {
            "label": cfg["label"], "engine": cfg["engine"], "params": cfg["params"],
            "corpus_velocities_extra": extra, "corpus_velocities_on_regular_grid": on_grid,
            "cells_total": len(rows), "cells_regular": len(reg),
            "regular_cells_n1n2_lt_-10dB": n_f1,
            "regular_cells_null_depth_le_-10dB": n_f2,
            "regular_cells_either": n_any,
            "theory_minus_dump_db_well_resolved": stats(diffs),
            "theory_minus_dump_db_all": stats(diffs_all),
            "csv": os.path.relpath(out_csv, L.REPO).replace("\\", "/"),
        }
        s = summary["configs"][name]
        print("== %s: %d cells (%d regular); n1/n2<-10dB: %d; null_depth<=-10dB: %d; either: %d"
              % (name, len(rows), len(reg), n_f1, n_f2, n_any))
        print("   theory-dump (well-resolved): %s" % json.dumps(s["theory_minus_dump_db_well_resolved"]))
        print("   theory-dump (all cells)    : %s" % json.dumps(s["theory_minus_dump_db_all"]))

    with open(os.path.join(HERE, "grid_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print("wrote grid_summary.json")


if __name__ == "__main__":
    sys.exit(main())
