#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""WF0925-N1 步驟 3：掃全 corpus 75 份 score（含 clean_batch2 商品用到的 50 份，全部都在 corpus 內），
列出基頻落在力脈衝零點附近的事件。

對每一份 score 跑 --cli 的 --dump-modes（layered score 由 CLI 自己展開，事件帶 layer_source），
只看走 HammerImpulse 半正弦力脈衝的弦類引擎：string / cimbalom / piano
（tongue_drum/water_gong/custom/fm 的模態不是弦的整數倍泛音，「第 1/第 2 partial」意義不同，不在本卡範圍）。

逐事件指標見 null_map_lib.event_metrics()。描述性分組（**描述用、非 GATE**）：
  near_null  = null_depth_db <= -10 dB（基頻落在零點凹口內：零點讓基頻比旁瓣包絡再低 10 dB 以上）
  weak_n1n2  = n1n2_dump_db  <  -10 dB（引擎 dump 的基頻叢比第 2 partial 叢低 10 dB 以上）
  stem_pred_dbfs = L1_db + 20log10(0.069 × master_volume) + 給愛麗絲 stem 校準 offset
                   ——只是「stem_verify 會不會判 near-silent」的參考值；offset 只用給愛麗絲鋼琴 stem 校準過，
                   其他引擎/參數沒有校準，表內另欄標明。-70 是 melody_verify.py 既有常數 BAND_GATE_DBFS。

輸出：
  reports/weak_fundamental_null_map/corpus_events_flagged.csv  near_null 或 weak_n1n2 的全部事件
  reports/weak_fundamental_null_map/corpus_file_summary.csv    每份 score 的計數
  reports/weak_fundamental_null_map/corpus_summary.json        彙總
"""
import argparse
import collections
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import null_map_lib as L  # noqa: E402

STRING_ENGINES = ("string", "cimbalom", "piano")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", default=L.DEFAULT_CLI)
    ap.add_argument("--stem-offset-db", type=float, default=None,
                    help="default: read stem_offset_db.mean from fur_elise_validation.json")
    args = ap.parse_args()
    cli = os.path.abspath(args.cli)
    off = args.stem_offset_db
    if off is None:
        with open(os.path.join(HERE, "fur_elise_validation.json"), encoding="utf-8") as f:
            off = json.load(f)["stem_offset_db"]["mean"]

    products = L.product_scores()
    files = L.corpus_files()
    flagged = []
    file_rows = []
    totals = collections.Counter()
    for fp in files:
        rel = os.path.relpath(str(fp), L.REPO).replace("\\", "/")
        with open(fp, encoding="utf-8") as f:
            score = json.load(f)
        master = float((score.get("global") or {}).get("master_volume", 1.0))
        dump = L.run_dump(cli, str(fp))
        layered = bool(dump.get("layered"))
        leaf_cache = {}
        n_string = n_near = n_weak = n_either = n_lowprec = 0
        n_pred_below = 0
        for ev in dump.get("events", []):
            eng = ev.get("engine")
            if eng not in STRING_ENGINES:
                continue
            if layered:
                leaf = ev.get("layer_source")
                if leaf not in leaf_cache:
                    with open(os.path.join(os.path.dirname(str(fp)), leaf), encoding="utf-8") as f:
                        leaf_cache[leaf] = json.load(f)
                sev = leaf_cache[leaf]["events"][ev["source_index"]]
                t = float(ev.get("time", sev.get("time", 0.0)))
            else:
                sev = score["events"][ev["source_index"]]
                t = float(sev.get("time", 0.0))
            # note 可以是音名字串或 MIDI 整數（dump 會把整數印成字串），兩種都比對
            assert sev.get("engine") == eng and str(sev.get("note")) == str(ev.get("note")), (rel, ev["source_index"])
            v = float(sev["velocity"])
            m = L.event_metrics(ev, v, eng, sev.get("params"))
            if "error" in m:
                continue
            n_string += 1
            near = m["null_depth_db"] <= -10.0
            weak = m["n1n2_dump_db"] is not None and m["n1n2_dump_db"] < -10.0
            pred = (m["L1_db"] + 20 * math.log10(L.CIMBALOM_OUTPUT_GAIN * master) + off
                    if m["L1_db"] is not None else None)
            n_near += near
            n_weak += weak
            n_either += (near or weak)
            n_lowprec += m["low_precision"]
            if pred is not None and pred < -70.0:
                n_pred_below += 1
            if near or weak:
                flagged.append({
                    "file": rel, "product_id": products.get(rel, ""),
                    "layer_source": ev.get("layer_source", ""),
                    "source_index": ev["source_index"], "time_s": t,
                    "engine": eng, "exciter": m["exciter"], "hardness": m["hardness"],
                    "note": ev["note"], "midi": m["midi"], "velocity": v,
                    "tau_ms": m["tau_ms"], "x1": m["x1"], "null_order": m["null_order"],
                    "null_depth_db": m["null_depth_db"],
                    "n1n2_dump_db": m["n1n2_dump_db"], "n1n2_theory_db": m["n1n2_theory_db"],
                    "n1_vs_max_db": m["n1_vs_max_db"], "L1_db": m["L1_db"],
                    "master_volume": master, "stem_pred_dbfs": pred,
                    "stem_pred_calibrated_for_this_config": (eng == "piano"),
                    "near_null": near, "weak_n1n2": weak, "low_precision": m["low_precision"],
                })
        file_rows.append({"file": rel, "product_id": products.get(rel, ""), "layered": layered,
                          "string_family_events": n_string, "near_null": n_near,
                          "weak_n1n2": n_weak, "either": n_either,
                          "stem_pred_below_-70": n_pred_below, "low_precision": n_lowprec})
        for k in ("string_family_events", "near_null", "weak_n1n2", "either"):
            totals[k] += file_rows[-1][k]
        print("%-80s %-26s strings=%5d near=%4d weak=%4d either=%4d"
              % (rel, products.get(rel, "")[:26], n_string, n_near, n_weak, n_either), flush=True)

    fcols = list(flagged[0].keys()) if flagged else []
    with open(os.path.join(HERE, "corpus_events_flagged.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fcols)
        for r in flagged:
            w.writerow([L.fmt(r.get(c), 3) if isinstance(r.get(c), float) else L.fmt(r.get(c)) for c in fcols])
    rcols = list(file_rows[0].keys())
    with open(os.path.join(HERE, "corpus_file_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(rcols)
        for r in file_rows:
            w.writerow([L.fmt(r.get(c)) for c in rcols])

    prod_flag = [r for r in flagged if r["product_id"]]
    groups = collections.OrderedDict()
    for r in sorted(flagged, key=lambda r: (r["file"], r["engine"], r["midi"], r["velocity"])):
        k = (r["file"], r["product_id"], r["engine"], r["hardness"], r["note"], r["velocity"])
        g = groups.setdefault(k, {"count": 0, "times": [], "x1": r["x1"], "null_order": r["null_order"],
                                  "null_depth_db": r["null_depth_db"], "n1n2_dump_db": r["n1n2_dump_db"],
                                  "L1_db": r["L1_db"], "stem_pred_dbfs": r["stem_pred_dbfs"],
                                  "near_null": r["near_null"], "weak_n1n2": r["weak_n1n2"]})
        g["count"] += 1
        g["times"].append(round(r["time_s"], 3))
    gcols = ["file", "product_id", "engine", "hardness", "note", "velocity", "count", "x1", "null_order",
             "null_depth_db", "n1n2_dump_db", "L1_db", "stem_pred_dbfs", "near_null", "weak_n1n2", "times_s"]
    with open(os.path.join(HERE, "corpus_flagged_by_note_velocity.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(gcols)
        for k, g in groups.items():
            w.writerow(list(k) + [g["count"], L.fmt(g["x1"]), L.fmt(g["null_order"]),
                                  L.fmt(g["null_depth_db"], 1),
                                  L.fmt(g["n1n2_dump_db"], 1), L.fmt(g["L1_db"], 1),
                                  L.fmt(g["stem_pred_dbfs"], 1), L.fmt(g["near_null"]),
                                  L.fmt(g["weak_n1n2"]), " ".join("%.3f" % t for t in g["times"])])

    summary = {
        "cli": cli, "stem_offset_db_used": off, "files_scanned": len(files),
        "products_in_catalog": len(products),
        "products_found_in_corpus": sum(1 for r in file_rows if r["product_id"]),
        "totals": dict(totals),
        "flagged_events": len(flagged),
        "flagged_in_products": len(prod_flag),
        "flagged_products": collections.Counter(r["product_id"] for r in prod_flag),
        "flagged_by_file": {r["file"]: r["either"] for r in file_rows if r["either"]},
        "flagged_by_engine_hardness": collections.Counter("%s/%s" % (r["engine"], r["hardness"]) for r in flagged),
        "files_with_string_family": sum(1 for r in file_rows if r["string_family_events"]),
    }
    with open(os.path.join(HERE, "corpus_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, default=str)
    print("\n==== corpus scan ====")
    print(json.dumps(summary, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
