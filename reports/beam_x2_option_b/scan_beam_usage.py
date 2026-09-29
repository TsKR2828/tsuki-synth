#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925b-BR: which scores reach BeamModel (engine "beam" / "tongue_drum").

Descriptive only (NOT a GATE). Read-only over scores/ and the product catalog.

- corpus = the same 4 roots as tools/verify_score.py find_all_scores()
  (scores/examples, scores/classical, scores/originals/ai_radiance,
  scores/library; rglob "*.score.json") -> 75 files at the 2026-09-25 index.
- a score "reaches BeamModel" if it has an event with engine beam/tongue_drum
  (ScoreRenderer.h maps both to ChromaticSubEngine::TongueDrum), directly or
  through a "layers" source (resolved relative to the score's directory,
  recursively).
- also lists every other *.score.json under scores/ that reaches BeamModel
  (tests/, originals/rules_v2_demo ...) so the out-of-corpus scope is visible.
- products: exports/products/clean_batch2/catalog.csv "score" column
  (gitignored folder; skipped with a note if absent).

Outputs (next to this script):
  beam_usage_corpus.csv     one row per corpus score (75 rows)
  beam_usage_all_scores.csv one row per score under scores/ that reaches BeamModel
  beam_usage_products.csv   one row per clean_batch2 product (50 rows)
"""
import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BEAM_ENGINES = {"beam", "tongue_drum"}

NOTE_BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_to_midi(note):
    if isinstance(note, (int, float)):
        return int(note)
    s = str(note).strip()
    if s.lstrip("-").isdigit():
        return int(s)
    letter = s[0].upper()
    rest = s[1:]
    acc = 0
    while rest and rest[0] in "#b":
        acc += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    octave = int(rest)
    return 12 * (octave + 1) + NOTE_BASE[letter] + acc


def corpus_files():
    roots = [REPO / "scores" / "examples", REPO / "scores" / "classical",
             REPO / "scores" / "originals" / "ai_radiance", REPO / "scores" / "library"]
    out = []
    for r in roots:
        if r.exists():
            out.extend(sorted(r.rglob("*.score.json")))
    return out


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def beam_events(path, seen=None):
    """Return list of (event dict, via) for every beam event reachable."""
    seen = set() if seen is None else seen
    path = Path(path).resolve()
    if path in seen:
        return []
    seen.add(path)
    d = load(path)
    out = []
    for ev in d.get("events", []) or []:
        if ev.get("engine") in BEAM_ENGINES:
            out.append((ev, "direct"))
    for layer in d.get("layers", []) or []:
        src = layer.get("source")
        if not src:
            continue
        sub = (path.parent / src).resolve()
        if sub.exists():
            for ev, via in beam_events(sub, seen):
                out.append((ev, "layer:" + sub.name if via == "direct" else via))
    return out


def summarize(evs):
    if not evs:
        return {"beam_events": 0, "via": "", "materials": "", "exciters": "",
                "midi_min": "", "midi_max": "", "dur_min_s": "", "dur_max_s": "",
                "thickness_mm": "", "freq_mode": ""}
    mats = Counter((e.get("params") or {}).get("material", "?") for e, _ in evs)
    exc = Counter((e.get("params") or {}).get("exciter", "(default)") for e, _ in evs)
    th = Counter(str((e.get("params") or {}).get("thickness_mm", "(default)")) for e, _ in evs)
    fm = Counter(str((e.get("params") or {}).get("frequency_mode", e.get("frequency_mode", "(default)")))
                 for e, _ in evs)
    via = Counter(v for _, v in evs)
    midis = [note_to_midi(e.get("note")) for e, _ in evs]
    durs = [float(e.get("duration", 0.0)) for e, _ in evs]
    fmt = lambda c: ";".join("%s×%d" % (k, n) for k, n in sorted(c.items()))
    return {"beam_events": len(evs), "via": fmt(via), "materials": fmt(mats),
            "exciters": fmt(exc), "midi_min": min(midis), "midi_max": max(midis),
            "dur_min_s": "%.3f" % min(durs), "dur_max_s": "%.3f" % max(durs),
            "thickness_mm": fmt(th), "freq_mode": fmt(fm)}


def rel(p):
    return Path(p).resolve().relative_to(REPO).as_posix()


def main():
    cols = ["score", "beam_events", "via", "materials", "exciters", "midi_min", "midi_max",
            "dur_min_s", "dur_max_s", "thickness_mm", "freq_mode"]
    corpus = corpus_files()
    rows = []
    for p in corpus:
        r = {"score": rel(p)}
        r.update(summarize(beam_events(p)))
        rows.append(r)
    with open(HERE / "beam_usage_corpus.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    n_beam = sum(1 for r in rows if r["beam_events"])
    print("corpus files: %d ; reaching BeamModel: %d ; beam events total: %d"
          % (len(rows), n_beam, sum(r["beam_events"] or 0 for r in rows)))
    for r in rows:
        if r["beam_events"]:
            print("  %-70s %5d  %s | %s | MIDI %s-%s | dur %s-%s s"
                  % (r["score"], r["beam_events"], r["via"], r["materials"],
                     r["midi_min"], r["midi_max"], r["dur_min_s"], r["dur_max_s"]))

    corpus_set = {Path(p).resolve() for p in corpus}
    all_rows = []
    for p in sorted((REPO / "scores").rglob("*.score.json")):
        try:
            evs = beam_events(p)
        except Exception as e:  # malformed test fixtures etc.
            print("  (skip %s: %s)" % (rel(p), e))
            continue
        if evs:
            r = {"score": rel(p), "in_corpus": Path(p).resolve() in corpus_set}
            r.update(summarize(evs))
            all_rows.append(r)
    with open(HERE / "beam_usage_all_scores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["score", "in_corpus"] + cols[1:])
        w.writeheader()
        w.writerows(all_rows)
    print("all scores under scores/ reaching BeamModel: %d (in corpus %d, outside %d)"
          % (len(all_rows), sum(1 for r in all_rows if r["in_corpus"]),
             sum(1 for r in all_rows if not r["in_corpus"])))
    for r in all_rows:
        if not r["in_corpus"]:
            print("  outside corpus: %s (%d events)" % (r["score"], r["beam_events"]))

    cat = REPO / "exports" / "products" / "clean_batch2" / "catalog.csv"
    if not cat.exists():
        print("product catalog not found (exports/ is gitignored) -- skipped")
        return 0
    prow = []
    with open(cat, encoding="utf-8-sig") as f:
        for c in csv.DictReader(f):
            sp = REPO / c["score"].replace("\\", "/")
            evs = beam_events(sp) if sp.exists() else []
            r = {"id": c["id"], "kind": c["kind"], "group": c["group"],
                 "score": c["score"].replace("\\", "/"), "score_exists": sp.exists(),
                 "in_corpus": sp.resolve() in corpus_set if sp.exists() else False}
            r.update(summarize(evs))
            prow.append(r)
    with open(HERE / "beam_usage_products.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "kind", "group", "score", "score_exists",
                                          "in_corpus"] + cols[1:])
        w.writeheader()
        w.writerows(prow)
    print("products: %d ; score missing: %d ; not in corpus: %d ; reaching BeamModel: %d"
          % (len(prow), sum(1 for r in prow if not r["score_exists"]),
             sum(1 for r in prow if not r["in_corpus"]),
             sum(1 for r in prow if r["beam_events"])))
    for r in prow:
        if r["beam_events"]:
            print("  product %-40s %s  %d beam events (%s)"
                  % (r["id"], r["score"], r["beam_events"], r["via"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
