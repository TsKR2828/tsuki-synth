#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""WF0925-N1 步驟 2：用給愛麗絲全曲 905 顆的 stem_verify 判定，驗證零點地圖。

資料：
  (a) output/wf0914/D14/g2_full_report.json —— D14 全量 stem_verify（A14 B-2 之後，677/16/212）
  (b) output/stem_verify_fur_elise_dry.json —— 08-30 stem_verify（A14 B-2 之前，671/22/212）
  (c) --cli 的 --dump-modes（本卡複製的 build\ CLI）對 fur_elise_complete.score.json 的全部事件
  (d) 本腳本自己重新渲染的 stem：對「每一種出現過的 (音高, 力度) 組合」各取第一顆，
      再加上 D14 的 16 顆 FAIL 全部、A5@0.462 全部（邊緣格）；
      渲染與判定直接呼叫 tools/stem_verify.py 的 derive_dry_score()/make_stem_score()/
      unnormalized_export()/render_one()/judge_stem()（不修改、不重寫判定邏輯），
      只把 verify_score.find_cli 指到 --cli；另外用 tools/melody_verify.py 的
      Spectrogram/band_of 量出 stem 的「基頻頻帶峰值 dBFS」。
      stem_verify 判 FAIL「no onset in near-silent fundamental band」的條件之一是這個頻帶
      沒有超過 melody_verify.py 既有常數 BAND_GATE_DBFS（-70 dBFS）——本卡沒有新增或修改任何門檻。

輸出：
  reports/weak_fundamental_null_map/fur_elise_events.csv        905 顆逐顆（dump 指標 + 兩次 verdict）
  reports/weak_fundamental_null_map/fur_elise_note_velocity.csv  依 (音高, 力度) 彙總
  reports/weak_fundamental_null_map/fur_elise_stems.csv          重新渲染的 stem：band 峰值、verdict
  reports/weak_fundamental_null_map/fur_elise_validation.json    彙總數字
"""
import argparse
import collections
import concurrent.futures
import csv
import json
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import null_map_lib as L  # noqa: E402

SCORE = "scores/classical/fur_elise/fur_elise_complete.score.json"
D14 = "output/wf0914/D14/g2_full_report.json"
PRE = "output/stem_verify_fur_elise_dry.json"


def load(p):
    with open(os.path.join(L.REPO, p), encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", default=L.DEFAULT_CLI)
    ap.add_argument("--workdir", default=os.path.join(L.REPO, "output", "wf0925", "N1", "fe_stems"))
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--no-stems", action="store_true")
    args = ap.parse_args()
    cli = os.path.abspath(args.cli)

    score = load(SCORE)
    events = score["events"]
    master = float(score["global"]["master_volume"])
    d14 = load(D14)["stem_verify"]["events"]
    pre = load(PRE)["stem_verify"]["events"]
    assert len(d14) == len(events) == len(pre) == 905
    for i, (a, b, e) in enumerate(zip(d14, pre, events)):
        assert a["index"] == i and b["index"] == i and a["note"] == e["note"] == b["note"], i
        assert abs(a["time"] - float(e["time"])) < 1e-3, i

    dump = L.run_dump(cli, os.path.join(L.REPO, SCORE))
    dev = {e["source_index"]: e for e in dump["events"]}
    rows = []
    for i, e in enumerate(events):
        m = L.event_metrics(dev[i], float(e["velocity"]), e["engine"], e.get("params"))
        mo = L.event_metrics(dev[i], float(e["velocity"]), e["engine"], e.get("params"),
                             variant="b4_before_a14")
        rows.append({
            "index": i, "time": float(e["time"]), "note": e["note"], "midi": m["midi"],
            "velocity": float(e["velocity"]),
            "verdict_0914_postA14": d14[i]["verdict"],
            "verdict_0830_preA14": pre[i]["verdict"],
            "reason_0914": (d14[i].get("reason") or "")[:80],
            "tau_ms": m["tau_ms"], "x1": m["x1"], "null_order": m["null_order"],
            "null_depth_db": m["null_depth_db"], "H1_db": m["H1_db"],
            "n1n2_dump_db": m["n1n2_dump_db"], "n1n2_theory_db": m["n1n2_theory_db"],
            "n1n2_s0_db": m["n1n2_s0_db"], "n1_vs_max_db": m["n1_vs_max_db"],
            "L1_db": m["L1_db"],
            "x1_b4_before_a14": mo["x1"], "null_depth_db_b4_before_a14": mo["null_depth_db"],
            "n1n2_theory_db_b4_before_a14": mo["n1n2_theory_db"],
            "f1_hz": m["f1_hz"],
        })

    # ---- stems (actual stem_verify judge, re-run with --cli) ----
    stem_rows = []
    if not args.no_stems:
        sys.path.insert(0, os.path.join(L.REPO, "tools"))
        import numpy as np
        import verify_score as vs
        import melody_verify as mv
        import stem_verify as sv
        from pathlib import Path
        vs.find_cli = lambda: Path(cli)
        mv.vs.find_cli = lambda: Path(cli)
        sv.vs.find_cli = lambda: Path(cli)

        dry = sv.derive_dry_score(score)
        if isinstance(dry, tuple):
            dry = dry[0]
        pick = []
        seen = set()
        for r in rows:
            key = (r["note"], r["velocity"])
            if key not in seen:
                seen.add(key)
                pick.append(r["index"])
        for r in rows:
            if r["verdict_0914_postA14"] == "FAIL" or (r["note"] == "A5" and abs(r["velocity"] - 0.462) < 1e-9):
                if r["index"] not in pick:
                    pick.append(r["index"])
        os.makedirs(args.workdir, exist_ok=True)

        def one(i):
            ev = events[i]
            ex = sv.unnormalized_export(dry.get("export"), bit_depth=24)
            st = sv.make_stem_score(dry, ev, "e%d" % i, export_override=ex)
            sub = Path(args.workdir) / ("e%d" % i)
            # CLI 不覆寫既有輸出/manifest（"SKIPPED (output or manifest already exists)"），
            # 重跑前先清掉本卡自己的暫存子資料夾（只在 --workdir 底下，預設 output/wf0925/N1/fe_stems/）
            if sub.exists():
                shutil.rmtree(sub)
            sp, wav = sv.render_one(Path(cli), st, sub)
            res = sv.judge_stem(sp, wav)
            sr, mono, _ = vs.read_wav_mono(wav)
            mono = np.concatenate([np.zeros(int(mv.PAD_S * sr)), mono])
            spec = mv.Spectrogram(mono, sr)
            f0 = res.get("expected_f0_hz") or rows[i]["f1_hz"]
            lo, hi = mv.band_of(f0)
            t, db = spec.band_db(lo, hi)
            t_exp = float(ev["time"]) + mv.PAD_S
            w = (t >= t_exp - 0.1) & (t <= t_exp + 0.3)
            pk = float(np.max(db[w]))
            try:
                os.remove(wav)
            except OSError:
                pass
            return i, res, pk

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
            for i, res, pk in ex.map(one, pick):
                r = rows[i]
                pred = r["L1_db"] + 20 * math.log10(L.CIMBALOM_OUTPUT_GAIN * master)
                stem_rows.append({
                    "index": i, "time": r["time"], "note": r["note"], "velocity": r["velocity"],
                    "verdict_rerun": res["verdict"], "verdict_0914_postA14": r["verdict_0914_postA14"],
                    "band_peak_dbfs": pk, "L1_plus_gain_master_db": pred,
                    "offset_db": pk - pred, "reason_rerun": (res.get("reason") or "")[:80]})
                print("stem ev%-4d %-4s v=%.3f rerun=%-10s d14=%-10s band_peak=%.1f dBFS"
                      % (i, r["note"], r["velocity"], res["verdict"],
                         r["verdict_0914_postA14"], pk), flush=True)
        stem_rows.sort(key=lambda r: r["index"])

    # ---- aggregate per (note, velocity) ----
    agg = collections.OrderedDict()
    for r in sorted(rows, key=lambda r: (r["midi"], r["velocity"])):
        key = (r["note"], r["velocity"])
        a = agg.setdefault(key, {"note": r["note"], "midi": r["midi"], "velocity": r["velocity"],
                                 "count": 0, "fail_0914": 0, "pass_0914": 0, "unv_0914": 0,
                                 "fail_0830": 0, "x1": r["x1"], "null_order": r["null_order"],
                                 "null_depth_db": r["null_depth_db"],
                                 "n1n2_dump_db": r["n1n2_dump_db"], "n1n2_s0_db": r["n1n2_s0_db"],
                                 "n1_vs_max_db": r["n1_vs_max_db"], "L1_db": r["L1_db"],
                                 "x1_b4_before_a14": r["x1_b4_before_a14"],
                                 "null_depth_db_b4_before_a14": r["null_depth_db_b4_before_a14"]})
        a["count"] += 1
        v = r["verdict_0914_postA14"]
        a["fail_0914"] += v == "FAIL"
        a["pass_0914"] += v == "PASS"
        a["unv_0914"] += v == "UNVERIFIED"
        a["fail_0830"] += r["verdict_0830_preA14"] == "FAIL"
    stem_by_key = {}
    for s in stem_rows:
        stem_by_key.setdefault((s["note"], s["velocity"]), []).append(s["band_peak_dbfs"])
    for k, a in agg.items():
        pk = stem_by_key.get(k)
        a["stem_band_peak_dbfs"] = (min(pk) if pk else None)

    # ---- summary numbers ----
    fails = [r for r in rows if r["verdict_0914_postA14"] == "FAIL"]
    judged = [r for r in rows if r["verdict_0914_postA14"] in ("PASS", "FAIL")]
    passes = [r for r in judged if r["verdict_0914_postA14"] == "PASS"]

    def cnt(rs, pred):
        return sum(1 for r in rs if pred(r))
    near = lambda r: r["null_depth_db"] <= -10.0            # 描述用、非 GATE
    weak = lambda r: r["n1n2_dump_db"] is not None and r["n1n2_dump_db"] < -10.0  # 描述用、非 GATE
    summary = {
        "cli": cli, "master_volume": master,
        "d14_counts": collections.Counter(r["verdict_0914_postA14"] for r in rows),
        "pre_a14_counts": collections.Counter(r["verdict_0830_preA14"] for r in rows),
        "fail16_all_null_depth_le_-10": cnt(fails, near),
        "fail16_n1n2_lt_-10": cnt(fails, weak),
        "fail16_x1_range": [min(r["x1"] for r in fails), max(r["x1"] for r in fails)],
        "fail16_null_orders": collections.Counter(r["null_order"] for r in fails),
        "fail16_null_depth_range": [min(r["null_depth_db"] for r in fails), max(r["null_depth_db"] for r in fails)],
        "pass_judged": len(passes),
        "pass_null_depth_le_-10": cnt(passes, near),
        "pass_n1n2_lt_-10": cnt(passes, weak),
        "pass_null_depth_le_-10_groups": collections.Counter(
            "%s@%.3f" % (r["note"], r["velocity"]) for r in passes if near(r)),
        "pass_n1n2_lt_-10_groups": collections.Counter(
            "%s@%.3f" % (r["note"], r["velocity"]) for r in passes if weak(r)),
        "unverified_null_depth_le_-10": cnt([r for r in rows if r["verdict_0914_postA14"] == "UNVERIFIED"], near),
        "old22_pre_a14": [
            {"index": r["index"], "note": r["note"], "velocity": r["velocity"],
             "x1_b4_before_a14": r["x1_b4_before_a14"],
             "null_depth_db_b4_before_a14": r["null_depth_db_b4_before_a14"],
             "x1_now": r["x1"], "null_depth_db_now": r["null_depth_db"]}
            for r in rows if r["verdict_0830_preA14"] == "FAIL"],
    }
    if stem_rows:
        offs = [s["offset_db"] for s in stem_rows]
        agree = sum(1 for s in stem_rows if s["verdict_rerun"] == s["verdict_0914_postA14"])
        # stem 實測 band 峰值 vs 既有 -70 dBFS 門檻（melody_verify.BAND_GATE_DBFS），只看有判 onset 的（f0>=167Hz）
        onset_judged = [s for s in stem_rows if s["verdict_rerun"] in ("PASS", "FAIL")]
        summary.update({
            "stems_rendered": len(stem_rows),
            "stems_verdict_agree_with_d14": agree,
            "stem_offset_db": {"n": len(offs), "min": min(offs), "max": max(offs),
                               "mean": sum(offs) / len(offs)},
            "stems_fail_band_peak_max": max((s["band_peak_dbfs"] for s in onset_judged
                                             if s["verdict_rerun"] == "FAIL"), default=None),
            "stems_pass_band_peak_min": min((s["band_peak_dbfs"] for s in onset_judged
                                             if s["verdict_rerun"] == "PASS"), default=None),
        })
        mean_off = summary["stem_offset_db"]["mean"]
        # 用 dump 預測全部 905 顆的 stem 基頻頻帶峰值（描述用；-70 是既有常數，不是本卡新門檻）
        for r in rows:
            r["band_peak_pred_dbfs"] = (r["L1_db"] + 20 * math.log10(L.CIMBALOM_OUTPUT_GAIN * master)
                                        + mean_off)
        conf = collections.Counter()
        for r in judged:
            conf[(r["verdict_0914_postA14"], "pred_below_-70" if r["band_peak_pred_dbfs"] < -70 else "pred_above_-70")] += 1
        summary["dump_prediction_confusion"] = {"%s|%s" % k: v for k, v in conf.items()}
        summary["dump_prediction_margin_pass_min"] = min(r["band_peak_pred_dbfs"] for r in passes)
        summary["dump_prediction_margin_fail_max"] = max(r["band_peak_pred_dbfs"] for r in fails)

    cols = list(rows[0].keys())
    with open(os.path.join(HERE, "fur_elise_events.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([L.fmt(r.get(c), 4) if isinstance(r.get(c), float) else L.fmt(r.get(c)) for c in cols])
    acols = list(next(iter(agg.values())).keys())
    with open(os.path.join(HERE, "fur_elise_note_velocity.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(acols)
        for a in agg.values():
            w.writerow([L.fmt(a.get(c), 3) if isinstance(a.get(c), float) else L.fmt(a.get(c)) for c in acols])
    if stem_rows:
        scols = list(stem_rows[0].keys())
        with open(os.path.join(HERE, "fur_elise_stems.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(scols)
            for s in stem_rows:
                w.writerow([L.fmt(s.get(c), 3) if isinstance(s.get(c), float) else L.fmt(s.get(c)) for c in scols])
    with open(os.path.join(HERE, "fur_elise_validation.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, default=str)

    # ---- human-readable printout ----
    print("\n==== fur_elise_complete validation ====")
    print("D14 (post-A14) verdicts:", dict(summary["d14_counts"]))
    print("08-30 (pre-A14) verdicts:", dict(summary["pre_a14_counts"]))
    print("16 FAIL: null_depth<=-10dB: %d/16 ; n1/n2(course)<-10dB: %d/16"
          % (summary["fail16_all_null_depth_le_-10"], summary["fail16_n1n2_lt_-10"]))
    print("16 FAIL: x1 range %.3f..%.3f ; null orders %s ; null depth %.1f..%.1f dB"
          % (tuple(summary["fail16_x1_range"]) + (dict(summary["fail16_null_orders"]),)
             + tuple(summary["fail16_null_depth_range"])))
    print("judged PASS: %d ; of which null_depth<=-10dB: %d %s"
          % (summary["pass_judged"], summary["pass_null_depth_le_-10"],
             dict(summary["pass_null_depth_le_-10_groups"])))
    print("judged PASS with n1/n2<-10dB: %d %s" % (summary["pass_n1n2_lt_-10"],
                                                   dict(summary["pass_n1n2_lt_-10_groups"])))
    print("UNVERIFIED with null_depth<=-10dB: %d" % summary["unverified_null_depth_le_-10"])
    print("old 22 (08-30 FAIL) under B4 tau_c: x1 / depth ->")
    for o in summary["old22_pre_a14"]:
        print("   ev%-4d %-4s v=%.3f  x1_B4=%.3f depth_B4=%.1f dB | x1_now=%.3f depth_now=%.1f dB"
              % (o["index"], o["note"], o["velocity"], o["x1_b4_before_a14"],
                 o["null_depth_db_b4_before_a14"], o["x1_now"], o["null_depth_db_now"]))
    if stem_rows:
        print("stems rendered: %d ; rerun verdict == D14 verdict: %d/%d"
              % (summary["stems_rendered"], summary["stems_verdict_agree_with_d14"], len(stem_rows)))
        print("stem offset (band_peak - (L1 + 20log10(0.069*master))): %s" % json.dumps(summary["stem_offset_db"]))
        print("stems: FAIL band peak max = %.1f dBFS ; PASS band peak min = %.1f dBFS  (gate -70, melody_verify.BAND_GATE_DBFS)"
              % (summary["stems_fail_band_peak_max"], summary["stems_pass_band_peak_min"]))
        print("dump-predicted band peak vs D14 verdict (judged events):", summary["dump_prediction_confusion"])
        print("  min predicted among PASS = %.1f dBFS ; max predicted among FAIL = %.1f dBFS"
              % (summary["dump_prediction_margin_pass_min"], summary["dump_prediction_margin_fail_max"]))


if __name__ == "__main__":
    sys.exit(main())
