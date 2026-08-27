#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B4 Rule 10 report -- scan the 73-piece corpus for B4-affected scores.

A score is AFFECTED by B4 (hammer-felt nonlinear contact solver) iff at
least one of its events goes down the CimbalomVoice string path with an
EFFECTIVE ExciterType::Felt hammer, i.e. exactly the events whose tau_c
source changes:

  * event engine in {"string", "cimbalom", "piano"}   (renderCimbalom path)
  * AND effective exciter maps to ExciterType::Felt via
    src/score/ScoreRenderer.h::cimbalomExciterFromString():
        felt, felt_mallet, finger, finger_tap, rubber_mallet -> Felt
    with the piano-branch override applied FIRST
    (ScoreRenderer.h renderEvent() piano branch: exciter=="wood_mallet"
    -> "felt"; so engine=piano with the default exciter is Felt).

Chromatic engines (beam/tongue_drum/plate/water_gong/custom) use
chromaticExciterHardness(), NOT cimbalomExciterFromString(), and B4 does
not touch ChromaticEngine -- they are never affected regardless of their
exciter string.

Layered scores (root has "layers" instead of "events") are affected iff
any referenced sub-score is affected (sources resolved relative to the
layered score's own directory, same as the renderer).

track_profiles are metadata only (the renderer never applies them --
ScoreParser.h only validates them), so the scan reads event-level
engine/params.exciter with the ScoreEvent defaults
(exciter default = "wood_mallet", ScoreParser.h ScoreEvent struct).

Corpus enumeration: identical to tools/verify_score.py::find_all_scores()
(scores/examples, scores/classical/vivaldi_four_seasons,
scores/originals/ai_radiance, scores/library -- recursive *.score.json).

Usage (run from the repo root):
    python reports/gate_outputs/b4_method/scan_affected_scores.py --label before
    python reports/gate_outputs/b4_method/scan_affected_scores.py --label after

Output:
  reports/gate_outputs/b4_method/affected_scores_<label>.md   (human table)
  reports/gate_outputs/b4_method/affected_scores_<label>.json (machine list,
      consumed by render_affected_pieces.py)
"""
import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

# exciter strings -> ExciterType::Felt, mirror of cimbalomExciterFromString()
FELT_EXCITERS = {"felt", "felt_mallet", "finger", "finger_tap", "rubber_mallet"}
STRING_PATH_ENGINES = {"string", "cimbalom", "piano"}


def find_all_scores():
    roots = [
        REPO / "scores" / "examples",
        REPO / "scores" / "classical" / "vivaldi_four_seasons",
        REPO / "scores" / "originals" / "ai_radiance",
        REPO / "scores" / "library",
    ]
    found = []
    for r in roots:
        if r.exists():
            found.extend(sorted(r.rglob("*.score.json")))
    return found


def effective_felt(engine, exciter):
    """True iff this event's tau_c comes from the Felt path B4 changes."""
    if engine not in STRING_PATH_ENGINES:
        return False
    if engine == "piano" and exciter == "wood_mallet":
        exciter = "felt"          # renderEvent() piano-branch override
    return exciter in FELT_EXCITERS


def scan_events(doc):
    """Return (n_events_on_string_path, n_felt_events, felt_breakdown dict)."""
    n_path = 0
    n_felt = 0
    breakdown = {}
    for ev in doc.get("events") or []:
        engine = ev.get("engine", "")
        exciter = (ev.get("params") or {}).get("exciter", "wood_mallet")
        if engine in STRING_PATH_ENGINES:
            n_path += 1
        if effective_felt(engine, exciter):
            n_felt += 1
            key = "%s/%s" % (engine, exciter)
            breakdown[key] = breakdown.get(key, 0) + 1
    return n_path, n_felt, breakdown


def scan_score(path, cache):
    """Return dict {affected, n_felt, breakdown, via} for one score file."""
    path = path.resolve()
    if path in cache:
        return cache[path]
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    result = {"affected": False, "n_felt": 0, "breakdown": {}, "via": []}
    if doc.get("events") is not None:
        _, n_felt, breakdown = scan_events(doc)
        result["affected"] = n_felt > 0
        result["n_felt"] = n_felt
        result["breakdown"] = breakdown
    for layer in doc.get("layers") or []:
        src = layer.get("source")
        if not src:
            continue
        sub_path = (path.parent / src).resolve()
        sub = scan_score(sub_path, cache)
        if sub["affected"]:
            result["affected"] = True
            result["n_felt"] += sub["n_felt"]
            for k, v in sub["breakdown"].items():
                result["breakdown"][k] = result["breakdown"].get(k, 0) + v
            result["via"].append(os.path.relpath(sub_path, REPO).replace(os.sep, "/"))
    cache[path] = result
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="'before' or 'after'")
    args = ap.parse_args()

    outdir = Path(__file__).resolve().parent
    corpus = find_all_scores()
    cache = {}
    rows = []
    for p in corpus:
        rel = os.path.relpath(p, REPO).replace(os.sep, "/")
        r = scan_score(p, cache)
        rows.append((rel, r))

    affected = [(rel, r) for rel, r in rows if r["affected"]]
    unaffected = [(rel, r) for rel, r in rows if not r["affected"]]

    # machine-readable list
    with open(outdir / ("affected_scores_%s.json" % args.label), "w",
              encoding="utf-8") as f:
        json.dump({
            "corpus_total": len(rows),
            "affected_total": len(affected),
            "affected": [
                {"score": rel, "felt_events": r["n_felt"],
                 "breakdown": r["breakdown"], "via_layers": r["via"]}
                for rel, r in affected
            ],
            "unaffected": [rel for rel, _ in unaffected],
        }, f, indent=2)

    # human-readable md
    md = []
    md.append("# B4 受影響 score 清單（label=%s）" % args.label)
    md.append("")
    md.append("> 產出腳本：`reports/gate_outputs/b4_method/scan_affected_scores.py`")
    md.append("> 判定條件：event engine ∈ {string, cimbalom, piano} 且有效 exciter 經")
    md.append("> `cimbalomExciterFromString()` 映為 `ExciterType::Felt`")
    md.append("> （felt / felt_mallet / finger / finger_tap / rubber_mallet；")
    md.append("> piano 引擎先套 renderEvent() 的 wood_mallet→felt 覆寫）。")
    md.append("> Chromatic 引擎（beam/tongue_drum/plate/water_gong/custom）一律不受影響")
    md.append("> （B4 不碰 ChromaticEngine，且其 exciter 走 chromaticExciterHardness()）。")
    md.append("> layers 型 score：任一 source 子譜受影響即受影響。")
    md.append("> track_profiles 只是 metadata（renderer 不套用），掃描以 event 層為準。")
    md.append("")
    md.append("Corpus 總數：**%d** 首（tools/verify_score.py --all 同一組枚舉）" % len(rows))
    md.append("受影響：**%d** 首；不受影響：**%d** 首" % (len(affected), len(unaffected)))
    md.append("")
    md.append("## 受影響清單")
    md.append("")
    md.append("| # | score | Felt 事件數 | engine/exciter 明細 | 經由 layers |")
    md.append("|---|---|---|---|---|")
    for i, (rel, r) in enumerate(affected, 1):
        bd = "; ".join("%s ×%d" % (k, v) for k, v in sorted(r["breakdown"].items()))
        via = "<br>".join(r["via"]) if r["via"] else "—"
        md.append("| %d | `%s` | %d | %s | %s |" % (i, rel, r["n_felt"], bd, via))
    md.append("")
    md.append("## 不受影響清單（B4 後這些曲目渲染必須逐位元不變）")
    md.append("")
    for rel, _ in unaffected:
        md.append("- `%s`" % rel)
    md.append("")
    with open(outdir / ("affected_scores_%s.md" % args.label), "w",
              encoding="utf-8") as f:
        f.write("\n".join(md))

    print("corpus=%d affected=%d unaffected=%d"
          % (len(rows), len(affected), len(unaffected)))
    for rel, r in affected:
        print("  AFFECTED %-70s felt_events=%d %s"
              % (rel, r["n_felt"],
                 ("via " + ",".join(r["via"])) if r["via"] else ""))


if __name__ == "__main__":
    sys.exit(main())
