#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""WF0925-N1：選項 D（score 層微調受影響音符的力度）的「要調多少」數字表——只算、不改任何 score。

對商品 fur_elise_complete 裡落在零點凹口（null_depth <= -10 dB，描述用、非 GATE）的每一組 (音高, 力度)：
  1. 用 HammerImpulse.h 鏡像 + dump 的真實基頻，在 velocity 0.120–0.920（tools/midi_to_tsukisynth.py
     velocity_for() 的輸出範圍，見 ScoreRenderer.h dumpModes() 註解的引述）以 0.001 步進，
     找出往下、往上最近一個「凹口深度 > -10 dB」的力度；
  2. 把這些候選力度真的丟進 --cli 的 --dump-modes，量 n1/n2 與基頻起音位準 L1，
     再用給愛麗絲 stem 校準 offset 換算成 stem 基頻頻帶峰值參考值（-70 dBFS 是
     melody_verify.py 既有常數 BAND_GATE_DBFS）。
  3. 20log10(v_new/v_old) = 單純因為力度線性縮放造成的整體響度變化（ModalResonator::excite()
     currentAmp = baseAmp × velocity）；τc 改變造成的頻譜形狀變化另外反映在 n1/n2 欄。
輸出：reports/weak_fundamental_null_map/option_d_velocity_candidates.csv
**選項 D 會改渲染結果＝R10，本表只是讓月月看數字，不是施工。**
"""
import argparse
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import null_map_lib as L  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", default=L.DEFAULT_CLI)
    ap.add_argument("--workdir", default=os.path.join(L.REPO, "output", "wf0925", "N1", "optd"))
    args = ap.parse_args()
    cli = os.path.abspath(args.cli)
    os.makedirs(args.workdir, exist_ok=True)
    with open(os.path.join(HERE, "fur_elise_validation.json"), encoding="utf-8") as f:
        off = json.load(f)["stem_offset_db"]["mean"]
    score = json.load(open(os.path.join(L.REPO, "scores/classical/fur_elise/fur_elise_complete.score.json"),
                           encoding="utf-8"))
    master = float(score["global"]["master_volume"])
    params = {"material": "steel", "diameter_mm": 1.0}

    groups = []
    with open(os.path.join(HERE, "fur_elise_note_velocity.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if float(r["null_depth_db"]) <= -10.0:
                groups.append(r)

    def l1_to_stem(l1):
        return l1 + 20 * math.log10(L.CIMBALOM_OUTPUT_GAIN * master) + off

    cand = []   # (group, which, v)
    for g in groups:
        midi = int(g["midi"])
        v0 = float(g["velocity"])
        # f1 from the note's real (tuned) centre-string fundamental: equal-tempered (frequency_mode midi)
        f1 = L.midi_hz(midi)
        down = up = None
        for k in range(int(round(v0 * 1000)) - 1, 119, -1):
            v = k / 1000.0
            if L.null_info(2 * f1 * L.piano_hammer_tauc(midi, v))[1] > -10.0:
                down = v
                break
        for k in range(int(round(v0 * 1000)) + 1, 921):
            v = k / 1000.0
            if L.null_info(2 * f1 * L.piano_hammer_tauc(midi, v))[1] > -10.0:
                up = v
                break
        cand.append((g, "original", v0))
        if down is not None:
            cand.append((g, "down", down))
        if up is not None:
            cand.append((g, "up", up))

    # dump-verify every candidate (one score per note)
    by_note = {}
    for g, which, v in cand:
        by_note.setdefault(int(g["midi"]), []).append((g, which, v))
    rows = []
    for midi, items in sorted(by_note.items()):
        sp = os.path.join(args.workdir, "optd_midi%03d.score.json" % midi)
        evs = [{"time": 0.5 * i, "duration": 0.2, "engine": "piano", "note": L.midi_to_name(midi),
                "velocity": v, "params": dict(params)} for i, (_, _, v) in enumerate(items)]
        d = {"$schema": "TsukiSynth Score v1",
             "meta": {"title": "optd", "id": "optd", "author": "wf0925-N1", "description": "option D probe"},
             "global": {"bpm": 120, "sample_rate": 48000, "master_volume": 1.0,
                        "effects": {"reverb": {"decay": 1.0, "wet": 0.0},
                                    "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                                    "distortion": {"type": "overdrive", "drive": 0, "instability": 0, "wet": 0}}},
             "events": evs,
             "export": {"filename": "optd", "format": "wav", "bit_depth": 24, "normalize": False,
                        "tail_silence_ms": 500}}
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        dump = L.run_dump(cli, sp)
        dev = {e["source_index"]: e for e in dump["events"]}
        for i, (g, which, v) in enumerate(items):
            m = L.event_metrics(dev[i], v, "piano", params)
            v0 = float(g["velocity"])
            rows.append({
                "note": g["note"], "midi": midi, "count_in_score": int(g["count"]),
                "verdict_0914": "FAIL %s / PASS %s" % (g["fail_0914"], g["pass_0914"]),
                "which": which, "velocity": v, "delta_velocity": v - v0,
                "level_change_db_from_velocity": 20 * math.log10(v / v0),
                "x1": m["x1"], "null_depth_db": m["null_depth_db"],
                "n1n2_dump_db": m["n1n2_dump_db"], "L1_db": m["L1_db"],
                "stem_band_pred_dbfs": l1_to_stem(m["L1_db"]),
            })
    cols = list(rows[0].keys())
    with open(os.path.join(HERE, "option_d_velocity_candidates.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([L.fmt(r[c], 3) if isinstance(r[c], float) else L.fmt(r[c]) for c in cols])
    for r in rows:
        print("%-4s x%-2d %-8s v=%.3f (dv=%+.3f, %+.2f dB)  x1=%.3f depth=%6.1f dB  n1/n2=%6.1f dB  stem_pred=%6.1f dBFS  [%s]"
              % (r["note"], r["count_in_score"], r["which"], r["velocity"], r["delta_velocity"],
                 r["level_change_db_from_velocity"], r["x1"], r["null_depth_db"], r["n1n2_dump_db"],
                 r["stem_band_pred_dbfs"], r["verdict_0914"]))


if __name__ == "__main__":
    sys.exit(main())
