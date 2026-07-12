#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/check_piece_consonance.py — M9-9d consonance compliance check.

Cross-checks every SIMULTANEOUS pair of notes in a score.json against the
recommended-interval tables from tools/consonance.py (Sethares 1993
dissonance-curve local minima, ROADMAP_PHYSICS.md M9-9a). Ear-free: every
verdict is "is this pitch-class interval within MIN_WINDOW_CENTS of a
registered local minimum in the matching table", a number lookup, not a
listening judgment.

Method:
  1. Parse the score's events; each event needs performance.midi_note (this
     script does not re-implement ScoreParser's note-name parser -- scores
     authored for this check must carry the explicit MIDI number).
  2. Two events are "simultaneous" if their [time, time+duration) windows
     overlap (their sounding intervals as declared in the score -- this does
     NOT model resonance ringing past the declared duration; see the
     report's caveat section).
  3. For every simultaneous pair (i, j), i != j:
       - f_i, f_j = 440 * 2**((midi-69)/12)  (12-TET, matches ScoreParser)
       - lower/higher decided by frequency
       - engine pair selects a table:
           same engine            -> that engine's SELF minima (tools/
                                      consonance.py sweep_curve(spec, spec))
           (cimbalom, tongue_drum) -> CROSS table, cimbalom=lower/fixed,
                                      tongue_drum=higher/transposed
                                      (ROADMAP_PHYSICS.md M9 pairing)
           (cimbalom, water_gong)  -> CROSS table, cimbalom=lower/fixed
           (tongue_drum, water_gong) -> CROSS table, tongue_drum=lower/fixed
         If the piece ever puts the "fixed" engine of a pair ABOVE the
         other one, that pair's direction was not computed by
         tools/consonance.py (the cross sweep only transposes UP from the
         fixed engine) -- flagged UNVALIDATED-DIRECTION, not silently passed.
       - cents_class = (1200*log2(f_high/f_low)) reduced into [0, 1200) by
         mod (octave-equivalence -- standard simplifying assumption for
         interval-class consonance judgments; documented, not hidden).
       - PASS if some local minimum in the matching table is within
         MIN_WINDOW_CENTS (10 cents, same constant tools/consonance.py uses
         for its own "recommended interval" definition) of cents_class.
         Otherwise VIOLATION (nearest minimum + distance reported).
  4. Writes a markdown report with every pair's verdict + a summary count.

Usage:
    python tools/check_piece_consonance.py <score.json> [--out PATH]
"""
import argparse, json, math, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics_verify import find_cli, midi_to_hz
from consonance import get_spectrum, sweep_curve, find_extrema, MIN_WINDOW_CENTS, nearest_name

# (lower_engine, higher_engine) -> which table to use. Matches the direction
# tools/consonance.py's report §3 computed (fixed engine listed first).
CROSS_PAIRS = {
    frozenset(["cimbalom", "tongue_drum"]): ("cimbalom", "tongue_drum"),
    frozenset(["cimbalom", "water_gong"]): ("cimbalom", "water_gong"),
    frozenset(["tongue_drum", "water_gong"]): ("tongue_drum", "water_gong"),
}


def load_events(score_path):
    data = json.loads(Path(score_path).read_text(encoding="utf-8"))
    events = []
    for i, e in enumerate(data["events"]):
        perf = e.get("performance", {})
        midi = perf.get("midi_note")
        if midi is None:
            raise RuntimeError(f"event {i} has no performance.midi_note "
                                "-- this checker requires an explicit MIDI "
                                "number per event (see module docstring).")
        events.append(dict(idx=i, engine=e["engine"], time=e["time"],
                            duration=e["duration"], midi=midi,
                            role=perf.get("role", "")))
    return events


def overlapping_pairs(events):
    pairs = []
    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            a, b = events[i], events[j]
            a_end = a["time"] + a["duration"]
            b_end = b["time"] + b["duration"]
            if a["time"] < b_end and b["time"] < a_end:
                pairs.append((a, b))
    return pairs


def build_tables(cli, outdir, engines_needed):
    spectra = {e: get_spectrum(cli, e, outdir) for e in engines_needed}
    self_minima = {}
    for e in engines_needed:
        _, _, minima, _ = (lambda ca, v: (ca, v) + find_extrema(ca, v))(*sweep_curve(spectra[e], spectra[e]))
        self_minima[e] = [c for c, _ in minima]
    cross_minima = {}
    for pair, (lo, hi) in CROSS_PAIRS.items():
        if lo in spectra and hi in spectra:
            cents_axis, vals = sweep_curve(spectra[lo], spectra[hi])
            minima, _ = find_extrema(cents_axis, vals)
            cross_minima[(lo, hi)] = [c for c, _ in minima]
    return self_minima, cross_minima


def nearest_min_distance(cents_class, minima_list):
    best_c, best_d = None, 1e9
    for m in minima_list:
        for cand in (m, m - 1200, m + 1200):   # wrap around 0/1200 boundary
            d = abs(cents_class - cand)
            if d < best_d:
                best_d, best_c = d, m
    return best_c, best_d


def check(score_path, cli, outdir):
    events = load_events(score_path)
    engines_needed = sorted(set(e["engine"] for e in events))
    self_minima, cross_minima = build_tables(cli, outdir, engines_needed)
    pairs = overlapping_pairs(events)

    results = []
    for a, b in pairs:
        fa, fb = midi_to_hz(a["midi"]), midi_to_hz(b["midi"])
        if fa <= fb:
            lo, hi = a, b
            f_lo, f_hi = fa, fb
        else:
            lo, hi = b, a
            f_lo, f_hi = fb, fa
        cents_raw = 1200.0 * math.log2(f_hi / f_lo) if f_hi != f_lo else 0.0
        cents_class = cents_raw % 1200.0
        if lo["engine"] == hi["engine"]:
            minima_list = self_minima[lo["engine"]]
            table_desc = f"{lo['engine']} self"
            direction_ok = True
        else:
            key = frozenset([lo["engine"], hi["engine"]])
            if key not in CROSS_PAIRS:
                minima_list, table_desc, direction_ok = [], "NO TABLE DEFINED", False
            else:
                want_lo, want_hi = CROSS_PAIRS[key]
                if lo["engine"] == want_lo:
                    minima_list = cross_minima[(want_lo, want_hi)]
                    table_desc = f"{want_lo}->{want_hi} cross"
                    direction_ok = True
                else:
                    minima_list, table_desc = [], f"{want_lo}->{want_hi} cross (REVERSED)"
                    direction_ok = False
        if direction_ok:
            nearest_c, dist = nearest_min_distance(cents_class, minima_list)
            # +1e-6 is floating-point epsilon (a 12-TET semitone stack of
            # log2/mod arithmetic can land at e.g. 700.0000000000003 cents
            # instead of exactly 700.0) -- NOT a widening of the 10-cent
            # window itself (ROADMAP_PHYSICS.md §1 Rule 2 forbids that); the
            # window is still exactly MIN_WINDOW_CENTS.
            verdict = "PASS" if dist <= MIN_WINDOW_CENTS + 1e-6 else "VIOLATION"
        else:
            nearest_c, dist, verdict = None, None, "UNVALIDATED-DIRECTION"
        results.append(dict(
            lo_idx=lo["idx"], hi_idx=hi["idx"], lo_engine=lo["engine"], hi_engine=hi["engine"],
            lo_role=lo["role"], hi_role=hi["role"], lo_midi=lo["midi"], hi_midi=hi["midi"],
            cents_class=cents_class, table=table_desc, nearest=nearest_c, dist=dist, verdict=verdict))
    return results


def write_report(results, score_path, out_path):
    lines = []
    lines.append("# Consonance Compliance Check\n")
    lines.append(f"Score: `{score_path}`\n")
    lines.append(
        "Method: every pair of events (across engines or within one engine) whose "
        "`[time, time+duration)` windows overlap is checked -- pitch-class interval "
        "(mod 1200 cents, octave-equivalence assumption) vs the nearest local minimum "
        "in the matching Sethares dissonance-curve table (tools/consonance.py, "
        f"ROADMAP_PHYSICS.md M9-9a). PASS = within {MIN_WINDOW_CENTS} cents of a "
        "registered minimum (same window tools/consonance.py itself uses for its "
        "'recommended interval' definition). This checks the SCORE's declared "
        "sounding windows, not resonance ringing past note-off -- a note whose "
        "physical decay outlasts its declared `duration` may still overlap "
        "perceptually with the next note; that is a known scope limit, not "
        "silently assumed away.\n"
    )
    n_pass = sum(1 for r in results if r["verdict"] == "PASS")
    n_viol = sum(1 for r in results if r["verdict"] == "VIOLATION")
    n_unval = sum(1 for r in results if r["verdict"] == "UNVALIDATED-DIRECTION")
    lines.append(f"**Summary: {len(results)} simultaneous pairs checked — "
                 f"{n_pass} PASS, {n_viol} VIOLATION, {n_unval} UNVALIDATED-DIRECTION.**\n")
    lines.append("| lo event | lo engine/role | hi event | hi engine/role | cents (mod 1200) | table | nearest min | dist | verdict |")
    lines.append("|---:|---|---:|---|---:|---|---:|---:|---|")
    for r in results:
        nearest_s = f"{r['nearest']:.0f}" if r["nearest"] is not None else "--"
        dist_s = f"{r['dist']:.1f}" if r["dist"] is not None else "--"
        lines.append(f"| {r['lo_idx']} (MIDI {r['lo_midi']}) | {r['lo_engine']}/{r['lo_role']} | "
                     f"{r['hi_idx']} (MIDI {r['hi_midi']}) | {r['hi_engine']}/{r['hi_role']} | "
                     f"{r['cents_class']:.1f} | {r['table']} | {nearest_s} | {dist_s} | {r['verdict']} |")
    lines.append("")
    if n_viol or n_unval:
        lines.append("Violations/unvalidated pairs are NOT auto-fixed by this script "
                     "(no widening of the 10-cent window) -- fix the score or document "
                     "the exception explicitly, per ROADMAP_PHYSICS.md §1.\n")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("score")
    ap.add_argument("--out", default=None)
    ap.add_argument("--cli", default=None)
    args = ap.parse_args()

    cli = Path(args.cli) if args.cli else find_cli()
    if not cli:
        print("ERROR: TsukiSynthCLI not found.", file=sys.stderr)
        return 1

    score_path = Path(args.score)
    out_path = Path(args.out) if args.out else (
        Path(__file__).resolve().parent.parent / "reports" /
        "rules_v2_demo_consonance_check.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        results = check(score_path, cli, Path(td))

    write_report(results, score_path, out_path)
    n_pass = sum(1 for r in results if r["verdict"] == "PASS")
    n_bad = len(results) - n_pass
    print(f"wrote {out_path}: {len(results)} pairs, {n_pass} PASS, {n_bad} not-PASS")
    return 0 if n_bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
