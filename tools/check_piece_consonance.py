#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/check_piece_consonance.py — M9-9d consonance compliance check.

Cross-checks every SIMULTANEOUS pair of modal notes in a score.json against
an event-specific Sethares (1993) roughness curve.  The spectra come from the
score's own C++ ``--dump-modes`` output, so material, geometry, strike point,
velocity-dependent hammer spectrum, beam/plate boundary, custom tuning and
multi-string detuning cannot be silently replaced by a MIDI-60 reference.

Method:
  1. Parse the score and run the real CLI ``--dump-modes`` once.  The dump's
     ``source_index`` and MIDI/frequency data are the identity contract; the
     optional ``performance.midi_note`` annotation is not required.
  2. Two events are "simultaneous" if their [time, time+duration) windows
     overlap (their sounding intervals as declared in the score -- this does
     NOT model resonance ringing past the declared duration; see the
     report's caveat section).
  3. For every simultaneous pair (i, j), i != j:
       - lower/higher is decided by the geometric centre of the dumped
         fundamental(s), not by an optional annotation;
       - each course's dumped modes are converted to frequency ratios around
         its own f0, retaining every active string (up to 8 modes/string);
       - the lower event stays at its actual absolute f0 while the higher
         event's *own* spectrum is swept through 0..1200 cents.  Thus the
         Sethares critical-band term retains the score's actual register.
       - cents_class = (1200*log2(f_high/f_low)) reduced into [0, 1200) by
         mod (octave-equivalence -- standard simplifying assumption for
         interval-class consonance judgments; documented, not hidden).
       - PASS if some local minimum in the matching table is within
         MIN_WINDOW_CENTS (10 cents, same constant tools/consonance.py uses
         for its own "recommended interval" definition) of cents_class.
         Otherwise VIOLATION (nearest minimum + distance reported). FM and
         authored Custom Harmonics are labelled UNVERIFIED-DOMAIN rather than
         being presented as physically verified.
  4. Writes a markdown report with every pair's verdict + a summary count.

Usage:
    python tools/check_piece_consonance.py <score.json> [--out PATH]

Without ``--out``, the report is written as
``reports/<score-basename>_consonance_check.md``; checking one score cannot
silently overwrite another score's report.
"""
import argparse, hashlib, json, math, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics_verify import find_cli
from consonance import sweep_curve, find_extrema, MIN_WINDOW_CENTS

PHYSICAL_MODAL_ENGINES = {
    "string", "cimbalom", "piano", "beam", "tongue_drum", "plate", "water_gong"
}
OUTSIDE_PHYSICAL_DOMAIN = {"fm", "custom"}
PARTIALS_PER_STRING = 8
RELATIVE_AMP_FLOOR = 1.0e-3  # -60 dB amplitude; below this the model is effectively weak


def note_to_midi(note):
    """Small display-only fallback; C++ dump MIDI remains authoritative."""
    if isinstance(note, int) and not isinstance(note, bool):
        return note if 0 <= note <= 127 else None
    text = str(note).strip()
    try:
        value = int(text)
        return value if str(value) == text and 0 <= value <= 127 else None
    except ValueError:
        pass
    if len(text) < 2 or text[0].upper() not in "ABCDEFG":
        return None
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[text[0].upper()]
    pos = 1
    if pos < len(text) and text[pos] in "#b":
        base += 1 if text[pos] == "#" else -1
        pos += 1
    try:
        midi = (int(text[pos:]) + 1) * 12 + base
    except ValueError:
        return None
    return midi if 0 <= midi <= 127 else None


def dumped_score_events(cli, score_path):
    result = subprocess.run([str(cli), "--dump-modes", str(score_path)],
                            capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown CLI error"
        raise RuntimeError(f"--dump-modes failed: {detail}")
    try:
        payload = json.loads(result.stdout)
        return {int(event["source_index"]): event for event in payload["events"]}
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid --dump-modes JSON: {exc}") from exc


def spectrum_from_dump(event_dump, velocity=1.0):
    """Return course-centre f0 and event-specific frequency-ratio spectrum."""
    strings = event_dump.get("strings") or []
    if not strings and event_dump.get("partials"):
        strings = [event_dump["partials"]]

    fundamentals, raw = [], []
    for string_modes in strings:
        valid = []
        for mode in string_modes[:PARTIALS_PER_STRING]:
            try:
                freq = float(mode["freq"])
                amp = abs(float(mode["amp"]) * float(mode.get("body_mag", 1.0)))
            except (KeyError, TypeError, ValueError):
                continue
            if math.isfinite(freq) and math.isfinite(amp) and freq > 0.0 and amp > 0.0:
                valid.append((freq, amp))
        if valid:
            fundamentals.append(valid[0][0])
            raw.extend(valid)
    if not fundamentals or not raw:
        return None, []

    # The geometric mean is the exact course centre for symmetric cent detuning.
    f0 = math.exp(sum(math.log(freq) for freq in fundamentals) / len(fundamentals))
    peak = max(amp for _, amp in raw)
    level = min(1.0, max(0.0, float(velocity)))
    spectrum = [
        (freq / f0, amp / peak * level)
        for freq, amp in raw if amp >= peak * RELATIVE_AMP_FLOOR
    ]
    return f0, spectrum


def event_timbre_label(event):
    engine = event["engine"]
    params = event.get("params", {})
    if engine in {"plate", "water_gong"}:
        return f"{engine}/{'free' if params.get('plate_free_edge', True) else 'clamped'}"
    if engine in {"beam", "tongue_drum"}:
        return f"{engine}/{params.get('beam_boundary', 'cantilever')}"
    return engine


def load_events(score_path, cli):
    data = json.loads(Path(score_path).read_text(encoding="utf-8"))
    dumped = dumped_score_events(cli, score_path)
    events = []
    for i, event in enumerate(data["events"]):
        perf = event.get("performance", {})
        mode_event = dumped.get(i)
        midi = mode_event.get("midi") if mode_event else note_to_midi(event.get("note"))
        engine = event["engine"]
        f0, spectrum = (spectrum_from_dump(mode_event, event["velocity"])
                        if mode_event else (None, []))
        if f0 is None and midi is not None:
            f0 = 440.0 * 2.0 ** ((midi - 69) / 12.0)
        domain = ("physical-modal" if engine in PHYSICAL_MODAL_ENGINES
                  else "outside" if engine in OUTSIDE_PHYSICAL_DOMAIN
                  else "unknown")
        events.append(dict(
            idx=i, engine=engine, label=event_timbre_label(event),
            time=event["time"], duration=event["duration"], midi=midi,
            role=perf.get("role", ""), f0=f0, spectrum=spectrum, domain=domain))
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


def nearest_min_distance(cents_class, minima_list):
    best_c, best_d = None, 1e9
    for m in minima_list:
        for cand in (m, m - 1200, m + 1200):   # wrap around 0/1200 boundary
            d = abs(cents_class - cand)
            if d < best_d:
                best_d, best_c = d, m
    return best_c, best_d


def check(score_path, cli):
    events = load_events(score_path, cli)
    pairs = overlapping_pairs(events)

    results = []
    for a, b in pairs:
        if a["f0"] is not None and b["f0"] is not None and a["f0"] <= b["f0"]:
            lo, hi = a, b
        else:
            lo, hi = b, a

        f_lo, f_hi = lo["f0"], hi["f0"]
        cents_class = ((1200.0 * math.log2(f_hi / f_lo)) % 1200.0
                       if f_lo and f_hi else None)
        table_desc = f"event-specific {lo['label']}->{hi['label']}"

        if lo["domain"] != "physical-modal" or hi["domain"] != "physical-modal":
            nearest_c, dist, verdict = None, None, "UNVERIFIED-DOMAIN"
        elif not lo["spectrum"] or not hi["spectrum"] or cents_class is None:
            nearest_c, dist, verdict = None, None, "UNVERIFIED-MODES"
        else:
            anchor = f_lo
            spec_lo = [(anchor * ratio, amp) for ratio, amp in lo["spectrum"]]
            spec_hi = [(anchor * ratio, amp) for ratio, amp in hi["spectrum"]]
            cents_axis, values = sweep_curve(spec_lo, spec_hi)
            minima, _ = find_extrema(cents_axis, values)
            nearest_c, dist = nearest_min_distance(
                cents_class, [c for c, _ in minima])
            # The epsilon only absorbs log2/mod representation error; the
            # registered window remains exactly MIN_WINDOW_CENTS.
            verdict = "PASS" if dist <= MIN_WINDOW_CENTS + 1e-6 else "VIOLATION"

        results.append(dict(
            lo_idx=lo["idx"], hi_idx=hi["idx"], lo_engine=lo["engine"], hi_engine=hi["engine"],
            lo_role=lo["role"], hi_role=hi["role"], lo_midi=lo["midi"], hi_midi=hi["midi"],
            cents_class=cents_class, table=table_desc, nearest=nearest_c, dist=dist, verdict=verdict))
    return results


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_report(results, score_path, out_path, cli_path=None):
    lines = []
    lines.append("# Consonance Compliance Check\n")
    lines.append(f"Score: `{score_path}`\n")
    lines.append(f"Score SHA256: `{sha256_file(score_path)}`\n")
    lines.append(f"Checker SHA256: `{sha256_file(__file__)}`\n")
    lines.append(f"Sethares implementation SHA256: "
                 f"`{sha256_file(Path(__file__).with_name('consonance.py'))}`\n")
    if cli_path is not None:
        lines.append(f"CLI: `{Path(cli_path).resolve()}`\n")
        lines.append(f"CLI SHA256: `{sha256_file(cli_path)}`\n")
    lines.append(
        "Method: every pair of events (across engines or within one engine) whose "
        "`[time, time+duration)` windows overlap is checked -- pitch-class interval "
        "(mod 1200 cents, octave-equivalence assumption) vs the nearest local minimum "
        "in an event-specific Sethares roughness curve built from this score's real "
        "C++ `--dump-modes` spectra (all active strings, material, geometry, boundary, "
        "strike and velocity-dependent hammer spectrum; tools/consonance.py formula, "
        f"ROADMAP_PHYSICS.md M9-9a). PASS = within {MIN_WINDOW_CENTS} cents of a "
        "local minimum. FM and Custom Harmonics are explicitly UNVERIFIED-DOMAIN. "
        "This checks the SCORE's declared "
        "sounding windows, not resonance ringing past note-off -- a note whose "
        "physical decay outlasts its declared `duration` may still overlap "
        "perceptually with the next note; that is a known scope limit, not "
        "silently assumed away.\n"
    )
    n_pass = sum(1 for r in results if r["verdict"] == "PASS")
    n_viol = sum(1 for r in results if r["verdict"] == "VIOLATION")
    n_unverified = sum(1 for r in results if r["verdict"].startswith("UNVERIFIED"))
    lines.append(f"**Summary: {len(results)} simultaneous pairs checked — "
                 f"{n_pass} PASS, {n_viol} VIOLATION, {n_unverified} UNVERIFIED.**\n")
    lines.append("| lo event | lo engine/role | hi event | hi engine/role | cents (mod 1200) | table | nearest min | dist | verdict |")
    lines.append("|---:|---|---:|---|---:|---|---:|---:|---|")
    for r in results:
        nearest_s = f"{r['nearest']:.0f}" if r["nearest"] is not None else "--"
        dist_s = f"{r['dist']:.1f}" if r["dist"] is not None else "--"
        cents_s = f"{r['cents_class']:.1f}" if r["cents_class"] is not None else "--"
        lo_midi = r["lo_midi"] if r["lo_midi"] is not None else "--"
        hi_midi = r["hi_midi"] if r["hi_midi"] is not None else "--"
        lines.append(f"| {r['lo_idx']} (MIDI {lo_midi}) | {r['lo_engine']}/{r['lo_role']} | "
                     f"{r['hi_idx']} (MIDI {hi_midi}) | {r['hi_engine']}/{r['hi_role']} | "
                     f"{cents_s} | {r['table']} | {nearest_s} | {dist_s} | {r['verdict']} |")
    lines.append("")
    if n_viol or n_unverified:
        lines.append("Violations/unvalidated pairs are NOT auto-fixed by this script "
                     "(no widening of the 10-cent window) -- fix the score or document "
                     "the exception explicitly, per ROADMAP_PHYSICS.md §1.\n")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


def default_report_path(score_path):
    name = Path(score_path).name
    if name.endswith(".score.json"):
        name = name[:-len(".score.json")]
    elif name.endswith(".json"):
        name = name[:-len(".json")]
    return (Path(__file__).resolve().parent.parent / "reports" /
            f"{name}_consonance_check.md")


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
    out_path = (Path(args.out) if args.out
                else default_report_path(score_path))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        results = check(score_path, cli)
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    write_report(results, score_path, out_path, cli)
    n_pass = sum(1 for r in results if r["verdict"] == "PASS")
    n_bad = len(results) - n_pass
    print(f"wrote {out_path}: {len(results)} pairs, {n_pass} PASS, {n_bad} not-PASS")
    return 0 if n_bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
