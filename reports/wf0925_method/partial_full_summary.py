#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF0925-V1 Part A (open-work:P2-partial-full): summarise the first
full-score (905-event) tools/partial_verify.py run on Fur Elise.

INFORMATIONAL ONLY. partial_verify.py itself reports status=informational /
gate_ready=false; nothing here upgrades that, and no new tolerance or
threshold is introduced -- every PASS/FAIL printed below is the verdict the
existing tools wrote (partial_verify.TOLERANCE_CENTS, the existing +/-5 c).
The only computation added here is re-running partial_verify's OWN
compute_pitch_via_partials() (imported, not re-implemented) on the 22 events
A13 asked to re-measure after B-2 -- those are no longer in the
weak-fundamental class, so the tool itself does not run that step for them.

Inputs:
  --stem-report     this run's stem_verify JSON (905 events, --keep-stems)
  --partial-report  this run's partial_verify JSON
  --d14-report      output/wf0914/D14/g2_full_report.json (09-14, same score)
  --pre-a14-stem    output/stem_verify_fur_elise_dry.json (08-30, before A14)
  --pre-a14-weak    output/wf0908/P1/partial_verify_weak_report.json (09-09,
                    the 22(+1) weak events' partial run, before A14 B-2)
"""
import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
import partial_verify as pv  # noqa: E402  (compute_pitch_via_partials, TOLERANCE_CENTS)


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def key(e):
    return (round(float(e["time"]), 5), e["note"])


def fmt(x, f="%+.3f"):
    return (f % x) if isinstance(x, (int, float)) and x is not None and math.isfinite(x) else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stem-report", required=True)
    ap.add_argument("--partial-report", required=True)
    ap.add_argument("--d14-report", required=True)
    ap.add_argument("--pre-a14-stem", required=True)
    ap.add_argument("--pre-a14-weak", required=True)
    ap.add_argument("--score", default=str(REPO / "scores/classical/fur_elise/fur_elise_complete.score.json"))
    args = ap.parse_args()

    stem = load(args.stem_report)
    part = load(args.partial_report)
    d14 = load(args.d14_report)
    pre = load(args.pre_a14_stem)
    pre_weak = load(args.pre_a14_weak)
    score = load(args.score)
    vel = {i: float(e["velocity"]) for i, e in enumerate(score["events"])}

    out = []
    P = out.append
    P("# WF0925-V1 Part A summary -- partial_verify full 905 (INFORMATIONAL, gate_ready=false)")
    P("# tolerance used by the tool (existing, unchanged): %s c ; provenance: %s"
      % (pv.TOLERANCE_CENTS, getattr(pv, "TOLERANCE_PROVENANCE", "?")))
    P("# partial report: status=%s gate_ready=%s amplitude_claim=%s cli=%s"
      % (part.get("status"), part.get("gate_ready"), part.get("amplitude_claim"), part.get("cli")))
    P("")

    # ---- 1. stem_verify: this run vs D14 (09-14) vs pre-A14 (08-30) ----
    sev = stem["stem_verify"]["events"]
    P("## 1. stem_verify (fundamental) summary")
    P("this run : %s" % stem["stem_verify"]["summary"])
    P("D14 09-14: %s" % d14["stem_verify"]["summary"])
    P("pre-A14 08-30: %s" % pre["stem_verify"]["summary"])
    d14ev = {e["index"]: e for e in d14["stem_verify"]["events"]}
    diff = [e["index"] for e in sev if d14ev.get(e["index"], {}).get("verdict") != e["verdict"]]
    P("per-event verdict differences vs D14 run: %d %s" % (len(diff), diff[:20]))
    cents_diff = [abs((e.get("pitch_cents") or 0) - (d14ev[e["index"]].get("pitch_cents") or 0))
                  for e in sev if e["index"] in d14ev]
    P("max |pitch_cents(this) - pitch_cents(D14)| over events: %s" % fmt(max(cents_diff), "%.6f"))
    sp = stem.get("superposition_proof") or {}
    P("superposition: n_stems_summed=%s established=%s residual_dbfs=%s"
      % (sp.get("n_stems_summed"), sp.get("established"),
         sp.get("residual_peak_dbfs", sp.get("residual_dbfs"))))
    P("")

    # ---- 2. partial level ----
    pev = part["events"]
    P("## 2. partial_verify summary (tool's own counters)")
    P(json.dumps(part["summary"], ensure_ascii=False))
    verd = Counter()
    by_n = defaultdict(Counter)
    reasons = Counter()
    fail_cents = []
    for e in pev:
        for p in e.get("partials") or []:
            verd[p["verdict"]] += 1
            by_n[p["n"]][p["verdict"]] += 1
            if p["verdict"] == "UNVERIFIED":
                r = p.get("reason") or ""
                # BAND_GATE_DBFS is tested BEFORE "pre-onset": the t=0 fallback
                # reason text itself says "no pre-onset region exists", so the
                # other order mislabelled those as pre-onset-floor refusals.
                if "band collision" in r:
                    reasons["own-event band collision"] += 1
                elif "BAND_GATE_DBFS" in r:
                    reasons["t=0 fallback absolute floor (BAND_GATE_DBFS)"] += 1
                elif "pre-onset" in r:
                    reasons["below own pre-onset floor + RISE_DB"] += 1
                elif "no usable frequency" in r:
                    reasons["dump-modes gave no frequency"] += 1
                elif "too short" in r:
                    reasons["segment too short"] += 1
                else:
                    reasons["measure_pitch_cents refusal: " + r[:60]] += 1
            if p["verdict"] == "FAIL":
                fail_cents.append(p["measured_cents"])
    tot = sum(verd.values())
    P("partial verdicts: PASS=%d FAIL=%d UNVERIFIED=%d (total partial slots %d)"
      % (verd["PASS"], verd["FAIL"], verd["UNVERIFIED"], tot))
    P("measured (PASS+FAIL) = %d ; of which FAIL = %d" % (verd["PASS"] + verd["FAIL"], verd["FAIL"]))
    for n in sorted(by_n):
        c = by_n[n]
        P("  n=%d: PASS=%d FAIL=%d UNVERIFIED=%d" % (n, c["PASS"], c["FAIL"], c["UNVERIFIED"]))
    P("UNVERIFIED reasons: %s" % dict(reasons))
    if fail_cents:
        fs = sorted(fail_cents, key=abs)
        P("FAIL |cents|: min %.3f  median %.3f  max %.3f ; sign + %d / - %d"
          % (abs(fs[0]), abs(fs[len(fs) // 2]), abs(fs[-1]),
             sum(1 for c in fail_cents if c > 0), sum(1 for c in fail_cents if c < 0)))
    ev_all_pass = sum(1 for e in pev if e.get("partials") and all(p["verdict"] == "PASS" for p in e["partials"]))
    ev_any_fail = sum(1 for e in pev if any(p["verdict"] == "FAIL" for p in e.get("partials") or []))
    P("events with every one of their partial slots PASS: %d ; events with >=1 FAIL partial: %d"
      % (ev_all_pass, ev_any_fail))
    # FAIL by note (which notes produce partial FAILs)
    fail_notes = Counter()
    for e in pev:
        nf = sum(1 for p in e.get("partials") or [] if p["verdict"] == "FAIL")
        if nf:
            fail_notes[e["note"]] += nf
    P("partial FAILs by note (top 15): %s" % fail_notes.most_common(15))
    fail_n_note = Counter()
    for e in pev:
        for p in e.get("partials") or []:
            if p["verdict"] == "FAIL":
                fail_n_note[(e["note"], p["n"])] += 1
    P("partial FAILs by (note, n) (top 20): %s" % fail_n_note.most_common(20))
    P("")

    # ---- 3. D16 weak set: this run's weak-fundamental-class events ----
    P("## 3. weak-fundamental class in THIS run (stem reason contains the marker) -> pitch_via_partials")
    weak = [e for e in pev if e.get("is_weak_fundamental_class")]
    grp = Counter((e["note"], vel[e["index"]]) for e in weak)
    P("count %d ; by (note, velocity): %s" % (len(weak), sorted(grp.items())))
    P("%-5s %-9s %-5s %-6s %-8s %9s %-10s %-26s  partials(n:verdict cents)" % (
        "idx", "time", "note", "vel", "pvp", "pvp_c", "B", "n_used"))
    for e in weak:
        ps = " ".join("%d:%s%s" % (p["n"], p["verdict"][0],
                                   ("%+.2f" % p["measured_cents"]) if "measured_cents" in p else "")
                      for p in e.get("partials") or [])
        P("%-5d %-9.4f %-5s %-6.3f %-8s %9s %-10s %-26s  %s" % (
            e["index"], e["time"], e["note"], vel[e["index"]], e.get("pitch_via_partials_verdict"),
            fmt(e.get("pitch_via_partials_cents")), fmt(e.get("pitch_via_partials_B"), "%.6f"),
            e.get("pitch_via_partials_n_used"), ps))
    amp_rows = []
    for e in weak:
        ps = e.get("partials") or []
        if len(ps) >= 2:
            amp_rows.append((e["index"], e["note"], vel[e["index"]],
                             ps[1].get("amplitude_db_rel_f1_predicted"),
                             ps[1].get("amplitude_db_rel_f1_measured")))
    P("n=2 level relative to n=1 (recorded only, amplitude_claim=none): predicted / measured dB")
    for r in amp_rows:
        P("  idx %d %s v%.3f : %s / %s" % (r[0], r[1], r[2], fmt(r[3], "%+.1f"), fmt(r[4], "%+.1f")))
    P("")

    # ---- 4. A13 '修完 B-2 後這 22 顆要重量' ----
    P("## 4. A13's 22 weak events (pre-A14 FAIL set) re-measured after B-2")
    pre_ev = {e["index"]: e for e in pre["stem_verify"]["events"]}
    old22 = sorted(i for i, e in pre_ev.items()
                   if e["verdict"] == "FAIL" and pv.WEAK_FUNDAMENTAL_REASON_MARKER in (e.get("reason") or ""))
    P("pre-A14 (08-30) weak-class FAIL indices: %d -> by note %s"
      % (len(old22), sorted(Counter(pre_ev[i]["note"] for i in old22).items())))
    pre_fail_all = [i for i, e in pre_ev.items() if e["verdict"] == "FAIL"]
    P("pre-A14 FAIL total %d (all weak-class: %s)" % (len(pre_fail_all), len(pre_fail_all) == len(old22)))
    pw = {key(e): e for e in pre_weak["events"]}
    pev_by_idx = {e["index"]: e for e in pev}
    sev_by_idx = {e["index"]: e for e in sev}
    agg_now = Counter()
    agg_then = Counter()
    pvp_now = Counter()
    P("%-5s %-9s %-5s %-6s | %-8s %8s | %-7s %9s | %-8s %9s %-18s | %-8s %9s" % (
        "idx", "time", "note", "vel", "stem_now", "f0_c", "pvp_pre", "pvp_pre_c",
        "pvp_now", "pvp_now_c", "n_used_now", "parts_now", "parts_pre"))
    for i in old22:
        e = pev_by_idx[i]
        s_now = sev_by_idx[i]
        parts = e.get("partials") or []
        dumped = [{"freq": p["expected_hz"]} for p in parts]
        res = pv.compute_pitch_via_partials(dumped, parts, e.get("expected_f0_hz"))
        pvp_now[res["verdict"]] += 1
        then = pw.get(key(e))
        for p in parts:
            agg_now[p["verdict"]] += 1
        if then:
            for p in then.get("partials") or []:
                agg_then[p["verdict"]] += 1
        pn = Counter(p["verdict"][0] for p in parts)
        pt = Counter(p["verdict"][0] for p in (then or {}).get("partials") or [])
        P("%-5d %-9.4f %-5s %-6.3f | %-8s %8s | %-7s %9s | %-8s %9s %-18s | P%dF%dU%d | P%dF%dU%d" % (
            i, e["time"], e["note"], vel[i], s_now["verdict"], fmt(s_now.get("pitch_cents")),
            (then or {}).get("pitch_via_partials_verdict"), fmt((then or {}).get("pitch_via_partials_cents")),
            res["verdict"], fmt(res["cents"]), res["n_used"],
            pn["P"], pn["F"], pn["U"], pt["P"], pt["F"], pt["U"]))
    P("stem verdict now for the 22: %s" % Counter(sev_by_idx[i]["verdict"] for i in old22))
    P("pitch_via_partials now (same function, run here because the tool skips non-weak-class events): %s"
      % dict(pvp_now))
    P("partial slots for the 22 -- now: %s ; pre-A14 (09-09 weak run): %s" % (dict(agg_now), dict(agg_then)))
    P("")

    # ---- 5. D16 16: were they PASS pre-A14? ----
    P("## 5. this run's FAIL set vs pre-A14")
    now_fail = [e["index"] for e in sev if e["verdict"] == "FAIL"]
    P("now FAIL %d: %s" % (len(now_fail), [(i, sev_by_idx[i]["note"], vel[i]) for i in now_fail]))
    P("their pre-A14 verdicts: %s" % Counter(pre_ev[i]["verdict"] for i in now_fail))
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
