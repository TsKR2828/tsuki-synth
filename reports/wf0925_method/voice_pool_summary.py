#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 Part B: compact, human-readable evidence from the two
voice_pool_occupancy.py JSON outputs (score T60 / plugin-reachable T60).
Descriptive only; no threshold is applied anywhere -- rows are simply
listed when the unlimited-pool demand is larger than the pool size the
plugin source itself declares (read by voice_pool_occupancy.py).

Usage:
  python reports/wf0925_method/voice_pool_summary.py \
      --score-json output/wf0925/V1/voice_pool_scoreT60.json \
      --reachable-json output/wf0925/V1/voice_pool_reachableT60.json
"""
import argparse
import json
import math
from collections import Counter
from pathlib import Path


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--score-json", required=True)
    ap.add_argument("--reachable-json", required=True)
    args = ap.parse_args()
    variants = [("scoreT60", load(args.score_json)), ("reachableT60", load(args.reachable_json))]
    out = []
    P = out.append
    P("# WF0925-V1 Part B compact summary (analysis only; no GATE; no threshold)")
    P("# code constants: %s" % json.dumps({k: v for k, v in variants[0][1]["constants"].items()
                                          if k != "sources"}))
    P("# T60 variants: scoreT60 = --dump-modes of the corpus as authored; reachableT60 = same corpus with"
      " damping_override/tension_n removed (no plugin control for them), i.e. what a plugin instance"
      " with Macro knobs at centre produces")
    P("# scenarios: A note-off at time+duration | B time+0.9*duration | C sustain pedal held (hypothetical)")
    P("")
    for vname, d in variants:
        res = d["results"]
        P("=" * 100)
        P("## variant %s" % vname)
        # counts
        for view in ("family", "track"):
            for sc in ("A", "B", "C"):
                rows = [r for r in res if r["view"] == view and r["scenario"] == sc]
                over = sorted({r["score"] for r in rows if r["demand_max"] > r["pool_size"]})
                prod_over = sorted({r["score"] for r in rows if r["product"] and r["demand_max"] > r["pool_size"]})
                steals = sum(r["n_steals"] for r in rows)
                held = sum(r["steals_victim_key_down"] for r in rows)
                e_on = sum(r["early_damp_same_note_on"] for r in rows)
                e_off = sum(r["early_damp_foreign_note_off"] for r in rows)
                e_sc = sorted({r["score"].split("/")[-1] for r in rows
                               if r["early_damp_same_note_on"] or r["early_damp_foreign_note_off"]})
                P("view=%-6s scen=%s : scores with demand>pool %2d/75 (products %d/50) ; total steals %6d ;"
                  " victim key still down %5d ; key-held voices damped early by same-note rules: by a"
                  " same-note note-on %d, by another event's note-off %d (in %d scores)"
                  % (view, sc, len(over), len(prod_over), steals, held, e_on, e_off, len(e_sc)))
        P("")
        P("### max demand per score (view=family), columns A/B/C = demand_max (steals)")
        tab = {}
        for r in res:
            if r["view"] != "family":
                continue
            tab.setdefault((r["score"], r["group"]), {})[r["scenario"]] = r
        P("%-80s %-9s %-4s %9s %13s %13s %13s" % ("score", "pool", "prod", "T60max_s", "A", "B", "C"))
        for (s, g), v in sorted(tab.items()):
            a, b, c = v["A"], v["B"], v["C"]
            if max(a["demand_max"], b["demand_max"], c["demand_max"]) < 8 and not a["product"]:
                continue
            P("%-80s %-9s %-4s %9.2f %13s %13s %13s" % (
                s[-80:], g, "P" if a["product"] else "", a["t60_max_over_events"],
                "%d (%d)" % (a["demand_max"], a["n_steals"]), "%d (%d)" % (b["demand_max"], b["n_steals"]),
                "%d (%d)" % (c["demand_max"], c["n_steals"])))
        P("(scores omitted above: non-product rows whose demand never reaches 8 in any scenario)")
        P("")
        P("### same-note early damping (independent of pool size), scenario A, both views")
        for r in res:
            if r["scenario"] == "A" and (r["early_damp_same_note_on"] or r["early_damp_foreign_note_off"]):
                P("- %s | %s | %s : same-note note-on %d ; other event's note-off %d (of %d events)%s"
                  % (r["score"], r["view"], r["group"], r["early_damp_same_note_on"],
                     r["early_damp_foreign_note_off"], r["n_events"], "  [product]" if r["product"] else ""))
                if r["product"]:
                    for x in r["early_damp_examples"]:
                        P("    id %s %s on %.4f own note-off %.4f damped at %s (%s)"
                          % (x["id"], x["note"], x["t_on"], x["own_note_off"], x["damped_at"], x["cause"]))
        P("")
        P("### every (score, view, group, scenario) with demand > pool")
        for r in res:
            if r["demand_max"] <= r["pool_size"]:
                continue
            P("- %s | %s | %s | %s : demand %d (pool %d) first at t=%.3f s ; %.2f s total above pool in %d windows;"
              " steals %d (rules %s) ; victim key still down %d ; remaining-energy bins (descriptive) %s"
              % (r["score"], r["view"], r["group"], r["scenario"], r["demand_max"], r["pool_size"],
                 r["demand_max_t"], r["seconds_demand_above_pool"], r["n_intervals_above_pool"],
                 r["n_steals"], r["steal_rules"], r["steals_victim_key_down"],
                 r["steal_remaining_db_bins_descriptive"]))
            for st in r["loudest_victims"][:(5 if r["scenario"] != "C" else 2)]:
                P("    loudest victim: t=%.3f s steals %s (id %s, on %.3f s, age %.3f s, key_down=%s, rule %s)"
                  " remaining %.1f dB rel. own start ; incoming %s (id %s)" % (
                      st["t"], st["victim_note"], st["victim"], st["victim_t_on"], st["victim_age_s"],
                      st["victim_key_down"], st["rule"], st["victim_remaining_db"],
                      st["incoming_note"], st["incoming"]))
        P("")
        P("### full steal list (variant scoreT60 only): scenario A, view=family, non-FM rows (others: loudest victims above;"
          " complete lists in the JSON)")
        for r in res:
            if vname != "scoreT60" or r["scenario"] != "A" or r["view"] != "family" or r["family"] == "fm" or not r["steals"]:
                continue
            P("#### %s | %s (%d steals)" % (r["score"], r["group"], r["n_steals"]))
            for st in r["steals"]:
                P("  t=%9.3f incoming %-5s(id %s) -> steals %-5s(id %s, on %.3f, age %.3f s, key_down=%s,"
                  " %s, would have rung %.3f s more, remaining %s dB)" % (
                      st["t"], st["incoming_note"], st["incoming"], st["victim_note"], st["victim"],
                      st["victim_t_on"], st["victim_age_s"], st["victim_key_down"], st["rule"],
                      st["victim_cut_s"] if st["victim_cut_s"] is not None else float("inf"),
                      ("%.1f" % st["victim_remaining_db"]) if st["victim_remaining_db"] is not None else "n/a"))
        P("")
    print("\n".join(out))


if __name__ == "__main__":
    main()
