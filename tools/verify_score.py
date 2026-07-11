#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_score.py -- whole-score, ear-free verification for TsukiSynth.

This is Milestone M3 of ROADMAP_PHYSICS.md: physics_verify.py only checks
single-note probes (engine x MIDI note). A composed score is much more than
that -- it is hundreds or thousands of overlapping events, explicit rests
that must not be swallowed by resonance, a rendered file that must not clip,
and a render pipeline that must be bit-for-bit reproducible. Nobody should
have to check those things by listening (see ROADMAP_PHYSICS.md Sec.0: "deaf
people + AI verify sound by physical theory, NOT by listening").

Checks performed (see ROADMAP_PHYSICS.md Sec.3 M3):
  2a. Schema sanity      -- required keys, events sorted by time, required
                            per-event fields, MIDI range, frequency_hz vs
                            equal temperament (+/-1 cent).
  2b. Mode scan          -- `--dump-modes` on the whole score (one CLI call,
                            not one per event -- see note below) checked for
                            empty mode sets, NaN/Inf, out-of-range
                            frequencies, non-finite/non-positive decay
                            constants, and f0-vs-equal-temperament deviation.
  2c. Rest verification  -- render the full score, merge every event's
                            sounding interval (+ decay tail) into a single
                            timeline, and measure RMS in every leftover gap.
                            This is the core new capability of M3: proof
                            that a rest is actually quiet in the rendered
                            audio, not just "no event happens to start here".
                            When a rest fails AND the score has nonzero
                            reverb/delay/distortion wet or drive, one extra
                            diagnostic render is made with those FX knobs
                            forced to 0 (decay time / delay time / filter
                            settings untouched) and the same window is
                            re-measured, so the failure message says whether
                            the overshoot survives FX bypass (dry model tail
                            -- release/modal decay) or disappears (FX tail
                            -- reverb/delay). Pass/fail is unaffected; this
                            is detail only, and never runs on a passing rest.
  2d. Peak / clipping    -- rendered peak <= -0.3 dBFS, no consecutive
                            clipped samples, output is not all zeros.
  2e. Determinism        -- render twice (to two different directories,
                            because the CLI refuses to overwrite an existing
                            file) and compare SHA256.

Implementation note on 2b (deviation from a literal per-event probe):
    The task brief for 2b describes building a single-note probe score per
    event, mirroring physics_verify.py. physics_verify.py does that because
    it needs to compare MEASURED AUDIO against per-engine theoretical
    partial-ratio predictions -- that requires an isolated, clean render.
    verify_score.py's 2b requirement (ROADMAP_PHYSICS.md Sec.3 M3, "全事件
    掃描: 無空模態集/無 NaN.../f0 偏差統計") is a sanity + f0 check on the
    model's own modal data, which `--dump-modes <score.json>` already
    reports for EVERY event in one shot (see src/cli/RenderApp.cpp and
    ScoreRenderer::dumpModes). Spawning one subprocess per event would cost
    minutes on scores with thousands of events (moonlight_sonata_complete
    has 6378) for no additional information -- the strike/material
    parameters that a probe would vary don't change the fundamental, only
    amplitude/decay, which are already reported per-event by the one whole-
    score call. This keeps M3 usable on every real asset in scores/, not
    just short examples.

Usage:
    python tools/verify_score.py <score.json>       # verify a single score
    python tools/verify_score.py --all                # verify every score
    python tools/verify_score.py --html <score.json>  # + write a single-file
                                                        # HTML visual report
                                                        # next to the score
                                                        # (ROADMAP_PHYSICS.md M4;
                                                        # see tools/report_html.py)
Exit code 0 = all checks passed. Exit code 1 = one or more checks failed.
"""

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

# ── tolerances (mirror physics_verify.py / ROADMAP_PHYSICS.md Sec.6) ───────
F0_TOL_CENTS = 1.0            # frequency_hz vs equal temperament (task 2a)
MODE_F0_TOL_CENTS = 12.0      # --dump-modes fundamental vs equal temperament
                              # (same as physics_verify.py F0_TOL_CENTS; the
                              # cimbalom multi-string model can shift the
                              # true fundamental a few cents from the tuned
                              # pitch, see PHYSICS_REPORT.md "5.002 cents")
FREQ_MIN_HZ = 0.0             # exclusive
FREQ_MAX_HZ = 20000.0         # inclusive
REST_RMS_LIMIT_DBFS = -50.0   # ROADMAP_PHYSICS.md Sec.6 "休止區 RMS"
REST_DECAY_ALLOWANCE_S = 0.5  # let the previous note's tail decay before
                              # judging a gap a "rest" (task 2c)
PEAK_LIMIT_DBFS = -0.3
CLIP_THRESHOLD = 0.999        # |sample| >= this counts as "clipped"
MAX_CONSECUTIVE_CLIPPED = 1   # no two clipped samples in a row allowed

MIDI_NOTE_MIN, MIDI_NOTE_MAX = 0, 127

# Engines dumpModes() actually reports partials for (see RenderApp.cpp /
# ScoreRenderer::dumpModes -- fm is synthesised, not modal, and is skipped).
MODAL_ENGINES = {"string", "cimbalom", "piano",
                  "beam", "tongue_drum", "plate", "water_gong",
                  "membrane", "custom"}

REQUIRED_TOP_KEYS = ("meta", "global", "export")
REQUIRED_EVENT_KEYS = ("time", "duration", "engine", "note", "velocity")


# ── note-name <-> MIDI (mirrors ScoreParser.h noteNameToMidi) ──────────────
_NOTE_BASE = {"A": 9, "B": 11, "C": 0, "D": 2, "E": 4, "F": 5, "G": 7}


def note_to_midi(note):
    """Best-effort re-implementation of ScoreParser::noteNameToMidi so this
    tool interprets `note` fields exactly like the C++ renderer does.
    Returns None if the note cannot be parsed at all (renderer would clamp
    to a default rather than fail, but a verifier should say so)."""
    if note is None:
        return None
    if isinstance(note, (int, float)):
        return int(round(note))
    s = str(note).strip()
    if not s:
        return None
    if s[0].isdigit():
        try:
            return int(round(float(s)))
        except ValueError:
            return None
    letter = s[0].upper()
    if letter not in _NOTE_BASE:
        return None
    base = _NOTE_BASE[letter]
    pos = 1
    if pos < len(s) and s[pos] == "#":
        base += 1
        pos += 1
    elif pos < len(s) and s[pos] == "b":
        base -= 1
        pos += 1
    octave_str = s[pos:]
    octave = 4
    if octave_str:
        try:
            octave = int(octave_str)
        except ValueError:
            return None
    return (octave + 1) * 12 + base


def midi_to_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def cents_between(f_measured, f_predicted):
    if f_measured is None or f_predicted is None or f_measured <= 0 or f_predicted <= 0:
        return None
    return 1200.0 * math.log2(f_measured / f_predicted)


# ── WAV reader (16 / 24 / 32-bit PCM -> mono float), same approach as
#    physics_verify.py ─────────────────────────────────────────────────────
def read_wav_mono(path):
    wf = wave.open(str(path), "rb")
    sr, ch, sw, n = (wf.getframerate(), wf.getnchannels(),
                     wf.getsampwidth(), wf.getnframes())
    raw = wf.readframes(n)
    wf.close()
    if sw == 2:
        a = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        a = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        a = np.where(a & 0x800000, a - 0x1000000, a).astype(np.float64) / 8388608.0
    elif sw == 4:
        a = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"unsupported sample width {sw}")
    if ch > 1:
        mono = a.reshape(-1, ch).mean(axis=1)
    else:
        mono = a
    return sr, mono, ch


def read_wav_all_channels(path):
    """Returns (sr, 2D float array [n_samples, n_channels]) without mixdown,
    used for the clip / all-zero checks so a clipped sample on only one
    channel is still caught."""
    wf = wave.open(str(path), "rb")
    sr, ch, sw, n = (wf.getframerate(), wf.getnchannels(),
                     wf.getsampwidth(), wf.getnframes())
    raw = wf.readframes(n)
    wf.close()
    if sw == 2:
        a = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        a = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        a = np.where(a & 0x800000, a - 0x1000000, a).astype(np.float64) / 8388608.0
    elif sw == 4:
        a = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"unsupported sample width {sw}")
    if ch > 1:
        a = a.reshape(-1, ch)
    else:
        a = a.reshape(-1, 1)
    return sr, a


def rms_dbfs(samples):
    if samples.size == 0:
        return -120.0
    rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
    return 20.0 * math.log10(rms) if rms > 1e-12 else -120.0


def peak_dbfs(samples):
    if samples.size == 0:
        return -120.0
    peak = float(np.max(np.abs(samples)))
    return 20.0 * math.log10(peak) if peak > 1e-12 else -120.0


# ── CLI discovery (same search as physics_verify.py) ────────────────────────
def find_cli():
    here = Path(__file__).resolve().parent.parent
    cands = list((here / "build").rglob("TsukiSynthCLI.exe"))
    cands += list((here / "build").rglob("tsukisynth-cli*"))
    cands += list((here / "build").rglob("TsukiSynthCLI"))
    cands = [c for c in cands if c.is_file()]
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)


class CliError(RuntimeError):
    pass


def run_cli(cli, args, timeout=600):
    try:
        return subprocess.run([str(cli), *[str(a) for a in args]],
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise CliError(
            f"TsukiSynthCLI did not finish within {timeout}s running "
            f"{' '.join(str(a) for a in args)}. The score may be unusually "
            "large, or the renderer may be stuck.") from e


def render_score(cli, score_path, out_dir):
    """Render `score_path` into `out_dir`. Returns the produced WAV path.
    Raises CliError with a human-readable message on failure. `out_dir`
    must not already contain the target output file -- the CLI refuses to
    overwrite an existing render and exits 1 ("SKIPPED (already exists)")."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    r = run_cli(cli, [score_path, "--output", out_dir])
    if r.returncode != 0:
        raise CliError(
            f"CLI render failed (exit {r.returncode}) for {score_path}:\n"
            f"{r.stdout}\n{r.stderr}")
    wav_files = sorted(out_dir.glob("*.wav")) + sorted(out_dir.glob("*.flac"))
    if not wav_files:
        raise CliError(
            f"CLI reported success but produced no output file for "
            f"{score_path}:\n{r.stdout}")
    # exactly one file expected per fresh output dir
    return wav_files[-1]


def score_has_nonzero_fx(score):
    """True if global.effects has any reverb/delay wet or distortion
    wet/drive > 0 -- i.e. there is something an FX-bypass render could
    plausibly change (task 2c diagnostic gate: only pay for the extra
    render when it could tell us something)."""
    fx = (score.get("global") or {}).get("effects") or {}
    rev = fx.get("reverb") or {}
    dly = fx.get("delay") or {}
    dist = fx.get("distortion") or {}
    for v in (rev.get("wet"), dly.get("wet"), dist.get("wet"), dist.get("drive")):
        if isinstance(v, (int, float)) and v > 0.0:
            return True
    return False


def make_fx_bypassed_copy(score):
    """Returns a deep-ish copy of `score` with reverb/delay wet and
    distortion wet/drive forced to 0, so a render of this copy isolates
    the DRY (post-model, pre-FX) tail. Only the FX wet/drive knobs are
    touched -- decay time, delay time_ms/feedback, distortion type stay
    as authored so this is a minimal "bypass", not a different score."""
    import copy
    bypassed = copy.deepcopy(score)
    fx = ((bypassed.get("global") or {}).get("effects")) or {}
    if "reverb" in fx and isinstance(fx["reverb"], dict):
        fx["reverb"]["wet"] = 0.0
    if "delay" in fx and isinstance(fx["delay"], dict):
        fx["delay"]["wet"] = 0.0
    if "distortion" in fx and isinstance(fx["distortion"], dict):
        fx["distortion"]["wet"] = 0.0
        fx["distortion"]["drive"] = 0.0
    return bypassed


def dump_modes(cli, score_path):
    """Runs --dump-modes once for the WHOLE score and returns the parsed
    JSON (see module docstring for why this replaces per-event probes)."""
    r = run_cli(cli, ["--dump-modes", score_path], timeout=1800)
    if r.returncode != 0:
        raise CliError(
            f"--dump-modes failed (exit {r.returncode}) for {score_path}:\n"
            f"{r.stdout}\n{r.stderr}")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise CliError(
            f"--dump-modes produced unparseable JSON for {score_path}: {e}\n"
            f"raw output:\n{r.stdout[:2000]}")


# ── a single check result ───────────────────────────────────────────────────
class Check:
    __slots__ = ("name", "ok", "message", "detail", "exempt_reason")

    def __init__(self, name, ok, message, detail=None, exempt_reason=None):
        self.name = name
        self.ok = ok
        self.message = message
        self.detail = detail or {}
        # Set (post-hoc, by apply_exemptions()) when a registered exemption
        # in scores/verify_exemptions.json matches this failing check. A
        # non-None exempt_reason means the check no longer counts toward the
        # file's overall pass/fail, but its original ok=False and message are
        # left intact so the raw failure is never silently hidden -- only
        # reclassified, and always with the reason printed alongside it.
        self.exempt_reason = exempt_reason

    def to_dict(self):
        return {"name": self.name, "ok": self.ok, "message": self.message,
                "detail": self.detail, "exempt_reason": self.exempt_reason}


# ── 2a. schema validation ───────────────────────────────────────────────────
def check_schema(score):
    checks = []

    missing_top = [k for k in REQUIRED_TOP_KEYS if k not in score]
    if missing_top:
        checks.append(Check(
            "schema.required_keys", False,
            "SCHEMA CHECK FAILED: score is missing required top-level "
            f"section(s): {', '.join(missing_top)} -- every score needs "
            "\"meta\", \"global\", and \"export\"."))
    else:
        checks.append(Check("schema.required_keys", True,
                             "All required top-level keys present (meta, global, export)."))

    events = score.get("events")
    if events is None:
        # layers-based scores legitimately have no events array; that is
        # covered by the schema (anyOf events/layers) and is not an error
        # here, but every per-event check below is then a no-op.
        checks.append(Check(
            "schema.events_present", True,
            "Score has no \"events\" array (uses \"layers\" instead); "
            "per-event schema checks are not applicable.",
            {"has_layers": bool(score.get("layers"))}))
        return checks, []

    # time sort
    times = [e.get("time") for e in events if isinstance(e, dict)]
    sort_violations = []
    for i in range(1, len(times)):
        if times[i - 1] is not None and times[i] is not None and times[i] < times[i - 1]:
            sort_violations.append((i - 1, times[i - 1], i, times[i]))
    if sort_violations:
        first = sort_violations[0]
        checks.append(Check(
            "schema.events_sorted", False,
            "SCHEMA CHECK FAILED: events are not sorted by \"time\" "
            f"(ascending). Event {first[0]} starts at {first[1]}s but "
            f"event {first[2]} right after it starts earlier, at "
            f"{first[3]}s. Found {len(sort_violations)} such violation(s) "
            "total.",
            {"violations": len(sort_violations), "first_index": first[0]}))
    else:
        checks.append(Check("schema.events_sorted", True,
                             f"All {len(times)} events are sorted by time (ascending)."))

    # per-event required fields + MIDI range + frequency_hz vs equal temperament
    bad_fields = []
    bad_midi = []
    bad_freq = []
    max_freq_cents_err = 0.0
    freq_checked = 0
    for i, ev in enumerate(events):
        if not isinstance(ev, dict):
            bad_fields.append((i, "event is not a JSON object"))
            continue
        missing = [k for k in REQUIRED_EVENT_KEYS if k not in ev]
        if missing:
            bad_fields.append((i, f"missing field(s): {', '.join(missing)}"))
            continue

        midi = note_to_midi(ev.get("note"))
        if midi is None:
            bad_midi.append((i, ev.get("note"), "could not be parsed as a note name or MIDI number"))
        elif not (MIDI_NOTE_MIN <= midi <= MIDI_NOTE_MAX):
            bad_midi.append((i, ev.get("note"), f"resolves to MIDI {midi}, outside 0-127"))

        perf = ev.get("performance") or {}
        freq_hz = perf.get("frequency_hz")
        if freq_hz is not None and midi is not None:
            expected = midi_to_hz(midi)
            err_cents = cents_between(freq_hz, expected)
            if err_cents is not None:
                freq_checked += 1
                max_freq_cents_err = max(max_freq_cents_err, abs(err_cents))
                if abs(err_cents) > F0_TOL_CENTS:
                    bad_freq.append((i, freq_hz, expected, err_cents))

    if bad_fields:
        i0, msg0 = bad_fields[0]
        checks.append(Check(
            "schema.event_required_fields", False,
            f"SCHEMA CHECK FAILED: event {i0} {msg0}. Every event needs "
            "time, duration, engine, note, and velocity. "
            f"({len(bad_fields)} event(s) affected total.)",
            {"count": len(bad_fields)}))
    else:
        checks.append(Check("schema.event_required_fields", True,
                             f"All {len(events)} events have the required fields "
                             "(time, duration, engine, note, velocity)."))

    if bad_midi:
        i0, note0, why0 = bad_midi[0]
        checks.append(Check(
            "schema.midi_range", False,
            f"SCHEMA CHECK FAILED: event {i0} has note \"{note0}\" which "
            f"{why0}. MIDI note numbers must be 0-127. "
            f"({len(bad_midi)} event(s) affected total.)",
            {"count": len(bad_midi)}))
    else:
        checks.append(Check("schema.midi_range", True,
                             "All event notes resolve to a valid MIDI number (0-127)."))

    if bad_freq:
        i0, f0, exp0, err0 = bad_freq[0]
        checks.append(Check(
            "schema.frequency_hz_equal_temperament", False,
            f"SCHEMA CHECK FAILED: event {i0}'s performance.frequency_hz "
            f"({f0:.3f} Hz) is {err0:+.2f} cents away from the equal-"
            f"temperament value for its MIDI note ({exp0:.3f} Hz). Limit "
            f"is +/-{F0_TOL_CENTS:.1f} cent. ({len(bad_freq)} event(s) "
            "affected total.)",
            {"count": len(bad_freq), "max_cents_checked": max_freq_cents_err}))
    else:
        msg = (f"All {freq_checked} performance.frequency_hz value(s) match equal "
               f"temperament (max deviation {max_freq_cents_err:.3f} cents, limit "
               f"+/-{F0_TOL_CENTS:.1f})."
               if freq_checked else
               "No performance.frequency_hz fields present to check (not required).")
        checks.append(Check("schema.frequency_hz_equal_temperament", True, msg))

    return checks, events


# ── 2b. mode scanning (whole-score --dump-modes, see module docstring) ─────
def check_modes(cli, score_path, events):
    """Returns (checks, dumped_events). `dumped_events` is the raw
    "events" array from --dump-modes's JSON (possibly []), returned
    alongside the Check objects so callers that need the underlying modal
    data (M4's HTML report: collision detection for the per-event f0
    chart) can reuse this one CLI call instead of running --dump-modes a
    second time -- see verify_one()."""
    checks = []
    try:
        dumped = dump_modes(cli, score_path)
    except CliError as e:
        checks.append(Check("modes.dump_modes_ran", False,
                             f"MODE SCAN FAILED: could not run --dump-modes: {e}"))
        return checks, []

    dumped_events = dumped.get("events", [])

    if not dumped_events:
        if not events:
            # layers-based score: check_schema() already returned an empty
            # events list for these, there is nothing per-event to dump.
            note = "This score has no \"events\" array (it uses \"layers\" instead)."
        elif not any(isinstance(ev, dict) and ev.get("engine") in MODAL_ENGINES
                     for ev in events):
            note = ("This score has no modal-engine events (e.g. it may be pure "
                     "FM, which ROADMAP_PHYSICS.md Sec.0 explicitly marks as "
                     "outside the physics-verification domain) -- nothing to "
                     "mode-scan.")
        else:
            note = "--dump-modes returned zero events even though modal events exist."
        checks.append(Check("modes.dump_modes_ran", True,
                             f"--dump-modes ran successfully. {note}",
                             {"modal_events": 0}))
        return checks, []

    checks.append(Check("modes.dump_modes_ran", True,
                         f"--dump-modes ran successfully for {len(dumped_events)} "
                         "modal event(s)."))

    empty_sets = []
    nan_inf = []
    bad_freq_range = []
    bad_decay = []
    f0_devs = []

    for i, ev in enumerate(dumped_events):
        partials = ev.get("partials", [])
        if not partials:
            empty_sets.append(i)
            continue

        midi = ev.get("midi")
        expected_f0 = midi_to_hz(midi) if isinstance(midi, (int, float)) else None

        for j, p in enumerate(partials):
            f = p.get("freq")
            a = p.get("amp")
            d = p.get("decay")

            for label, v in (("freq", f), ("amp", a), ("decay", d)):
                if v is None or not math.isfinite(v):
                    nan_inf.append((i, j, label, v))

            if f is not None and math.isfinite(f):
                if not (FREQ_MIN_HZ < f <= FREQ_MAX_HZ):
                    bad_freq_range.append((i, j, f))

            if d is not None and math.isfinite(d):
                if d <= 0.0:
                    bad_decay.append((i, j, d))

        if expected_f0 is not None and partials:
            f0 = partials[0].get("freq")
            if f0 is not None and math.isfinite(f0) and f0 > 0:
                c = cents_between(f0, expected_f0)
                if c is not None:
                    f0_devs.append((i, ev.get("engine"), ev.get("note"), c))

    if empty_sets:
        checks.append(Check(
            "modes.no_empty_sets", False,
            f"MODE SCAN FAILED: {len(empty_sets)} modal event(s) produced an "
            f"empty mode set (no partials at all) -- first at event index "
            f"{empty_sets[0]} of the dumped modal events. That note would "
            "render as silence.",
            {"count": len(empty_sets)}))
    else:
        checks.append(Check("modes.no_empty_sets", True,
                             f"No empty mode sets ({len(dumped_events)} modal events checked)."))

    total_partials = sum(len(ev.get("partials", [])) for ev in dumped_events)

    if nan_inf:
        i0, j0, label0, v0 = nan_inf[0]
        checks.append(Check(
            "modes.no_nan_inf", False,
            f"MODE SCAN FAILED: modal event {i0}, partial {j0} has a "
            f"non-finite {label0} value ({v0!r}). Found {len(nan_inf)} "
            f"non-finite value(s) across {total_partials} partials checked.",
            {"count": len(nan_inf), "total_partials": total_partials}))
    else:
        checks.append(Check("modes.no_nan_inf", True,
                             f"No NaN/Inf values ({total_partials} partials checked "
                             f"across {len(dumped_events)} events)."))

    if bad_freq_range:
        i0, j0, f0 = bad_freq_range[0]
        checks.append(Check(
            "modes.frequency_range", False,
            f"MODE SCAN FAILED: modal event {i0}, partial {j0} has "
            f"frequency {f0:.2f} Hz, outside the allowed range "
            f"(0, {FREQ_MAX_HZ:.0f}] Hz. {len(bad_freq_range)} partial(s) "
            "affected total.",
            {"count": len(bad_freq_range)}))
    else:
        checks.append(Check("modes.frequency_range", True,
                             f"All {total_partials} partial frequencies are within "
                             f"(0, {FREQ_MAX_HZ:.0f}] Hz."))

    if bad_decay:
        i0, j0, d0 = bad_decay[0]
        checks.append(Check(
            "modes.decay_positive_finite", False,
            f"MODE SCAN FAILED: modal event {i0}, partial {j0} has a "
            f"non-positive decay constant ({d0!r} s). Decay times must be "
            f"positive and finite. {len(bad_decay)} partial(s) affected total.",
            {"count": len(bad_decay)}))
    else:
        checks.append(Check("modes.decay_positive_finite", True,
                             f"All {total_partials} partial decay constants are "
                             "positive and finite."))

    if f0_devs:
        max_dev = max(abs(c) for *_, c in f0_devs)
        worst = max(f0_devs, key=lambda t: abs(t[3]))
        over = [t for t in f0_devs if abs(t[3]) > MODE_F0_TOL_CENTS]
        if over:
            i0, eng0, note0, c0 = over[0]
            checks.append(Check(
                "modes.f0_deviation", False,
                f"MODE SCAN FAILED: modal event {i0} ({eng0} note {note0}) "
                f"has a fundamental {c0:+.2f} cents away from its MIDI "
                f"pitch, exceeding the +/-{MODE_F0_TOL_CENTS:.1f}-cent "
                f"limit. Worst overall: {worst[3]:+.2f} cents "
                f"(event {worst[0]}, {worst[1]} note {worst[2]}). "
                f"{len(over)}/{len(f0_devs)} event(s) exceed the limit.",
                {"max_cents": max_dev, "over_limit": len(over), "checked": len(f0_devs)}))
        else:
            checks.append(Check(
                "modes.f0_deviation", True,
                f"Fundamental frequency deviation within +/-{MODE_F0_TOL_CENTS:.1f} "
                f"cents for all {len(f0_devs)} modal events (max observed: "
                f"{max_dev:.3f} cents).",
                {"max_cents": max_dev, "checked": len(f0_devs)}))
    else:
        checks.append(Check("modes.f0_deviation", True,
                             "No fundamentals available to check (no modal events with "
                             "a resolvable MIDI note)."))

    return checks, dumped_events


# ── 2c. rest verification ───────────────────────────────────────────────────
def merge_intervals(intervals):
    """[(start, end), ...] -> sorted, merged, non-overlapping list."""
    if not intervals:
        return []
    s = sorted(intervals)
    merged = [list(s[0])]
    for start, end in s[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(a, b) for a, b in merged]


def find_rest_intervals(events, decay_allowance=REST_DECAY_ALLOWANCE_S):
    """Builds the union of every event's [time, time+duration] span (across
    ALL tracks/engines -- scores are typically polyphonic, see
    ai_radiance_m1.score.json where 51/64 events overlap their neighbour),
    then returns the gaps between those spans, each shrunk by
    `decay_allowance` seconds from its start to let the previous note's
    resonance tail decay before judging the remainder a rest (task 2c /
    ROADMAP_PHYSICS.md Sec.6 "考慮前音殘響衰減")."""
    spans = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        t = ev.get("time")
        d = ev.get("duration")
        if t is None or d is None:
            continue
        spans.append((float(t), float(t) + max(float(d), 0.0)))

    sounding = merge_intervals(spans)
    rests = []
    for i in range(1, len(sounding)):
        gap_start = sounding[i - 1][1]
        gap_end = sounding[i][0]
        judged_start = gap_start + decay_allowance
        if judged_start < gap_end:
            rests.append((judged_start, gap_end, gap_start))
    return rests


def fx_bypass_rest_rms(cli, score, rests, sr_hint=None):
    """Re-renders `score` with all FX wet/drive knobs forced to 0 (see
    make_fx_bypassed_copy) into a throwaway temp dir, then measures RMS in
    the same rest windows already found in the FX-on render. Returns a dict
    {(judged_start, gap_end): dbfs} on success, or None if the bypass
    render itself failed (reported as an informational note, not a new
    failure -- the FX-on rest check already failed on its own merits).
    This is purely diagnostic (task 2c step 2): it never changes ok/fail,
    only adds detail so a human can tell reverb/delay tail from
    modal/release tail at a glance."""
    with tempfile.TemporaryDirectory(prefix="tsuki_verify_fxbypass_") as d:
        score_copy_path = Path(d) / "_fx_bypass_score.json"
        bypassed = make_fx_bypassed_copy(score)
        score_copy_path.write_text(json.dumps(bypassed, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
        try:
            wav_path = render_score(cli, score_copy_path, Path(d) / "render")
        except CliError:
            return None
        if wav_path.suffix.lower() != ".wav":
            return None
        try:
            sr, mono_audio, _ = read_wav_mono(wav_path)
        except Exception:
            return None

        result = {}
        for judged_start, gap_end, _raw_gap_start in rests:
            start_i = max(0, int(judged_start * sr))
            end_i = min(len(mono_audio), int(gap_end * sr))
            if end_i <= start_i:
                continue
            seg = mono_audio[start_i:end_i]
            result[(judged_start, gap_end)] = rms_dbfs(seg)
        return result


def check_rests(events, sr, mono_audio, cli=None, score=None):
    checks = []
    if not events:
        checks.append(Check("rests.checked", True,
                             "No events array to derive rest intervals from "
                             "(layers-based score); rest check skipped."))
        return checks

    rests = find_rest_intervals(events)
    if not rests:
        checks.append(Check("rests.checked", True,
                             "No rest interval is longer than the "
                             f"{REST_DECAY_ALLOWANCE_S:.1f}s decay allowance "
                             "-- nothing to check (score has no exploitable "
                             "gaps, or is continuously sounding)."))
        return checks

    duration_s = len(mono_audio) / sr if sr else 0.0
    failures = []
    worst_margin = None
    checked = 0
    # Per-interval pass/fail, kept regardless of the overall verdict (M4's
    # HTML report draws every rest span on the loudness curve, not just the
    # first failure -- see report_html.render_loudness_section()).
    all_intervals = []
    for judged_start, gap_end, raw_gap_start in rests:
        start_i = max(0, int(judged_start * sr))
        end_i = min(len(mono_audio), int(gap_end * sr))
        if end_i <= start_i:
            continue
        checked += 1
        seg = mono_audio[start_i:end_i]
        level = rms_dbfs(seg)
        margin = REST_RMS_LIMIT_DBFS - level  # positive = passing headroom
        interval_pass = level <= REST_RMS_LIMIT_DBFS
        all_intervals.append({"start": judged_start, "end": gap_end,
                               "level_dbfs": level, "pass": interval_pass})
        # report the window that was actually MEASURED (judged_start..gap_end,
        # i.e. after the decay-allowance skip) -- raw_gap_start is kept in the
        # detail dict for anyone who wants the full un-skipped gap context.
        if worst_margin is None or margin < worst_margin[0]:
            worst_margin = (margin, judged_start, gap_end, level, raw_gap_start)
        if not interval_pass:
            failures.append((judged_start, gap_end, level, raw_gap_start))

    if checked == 0:
        checks.append(Check("rests.checked", True,
                             "All candidate rest intervals fall outside the "
                             "rendered audio length; nothing to check."))
        return checks

    if failures:
        t0, t1, level0, raw0 = failures[0]
        detail = {"count": len(failures), "checked": checked,
                   "total_score_duration_s": duration_s,
                   "first_failure_raw_gap_start_s": raw0,
                   "intervals": all_intervals}
        fx_note = ""
        # Diagnostic-only FX-bypass re-render (ROADMAP_PHYSICS.md M3 step 2):
        # only spend the extra render when there is nonzero FX that could
        # plausibly explain the failing rest, and only because a rest check
        # already failed above -- this never runs on a passing score.
        if cli is not None and score is not None and score_has_nonzero_fx(score):
            fx_levels = fx_bypass_rest_rms(cli, score, [(f[0], f[1], f[3]) for f in failures])
            if fx_levels is None:
                fx_note = (" FX-bypass diagnostic render could not be produced "
                           "(render/decode failed) -- see detail for FX-on levels only.")
                detail["fx_bypass"] = "render_failed"
            else:
                bypass_detail = []
                for t0f, t1f, level_on, _raw in failures:
                    level_off = fx_levels.get((t0f, t1f))
                    bypass_detail.append({
                        "window_s": [t0f, t1f],
                        "fx_on_dbfs": level_on,
                        "fx_bypass_dbfs": level_off,
                    })
                detail["fx_bypass"] = bypass_detail
                off0 = fx_levels.get((t0, t1))
                if off0 is not None:
                    if off0 <= REST_RMS_LIMIT_DBFS:
                        fx_note = (
                            f" FX-bypass render of the same window measures "
                            f"{off0:.1f} dBFS (below the {REST_RMS_LIMIT_DBFS:.1f} "
                            "dBFS limit) -- the overshoot looks like a "
                            "reverb/delay tail, not the dry model's own decay.")
                    else:
                        fx_note = (
                            f" FX-bypass render of the same window STILL measures "
                            f"{off0:.1f} dBFS (still above the "
                            f"{REST_RMS_LIMIT_DBFS:.1f} dBFS limit) -- the tail "
                            "survives with FX removed, so this looks like the "
                            "dry model/instrument's own modal or release decay, "
                            "not a reverb/delay artifact.")
        checks.append(Check(
            "rests.rms_below_limit", False,
            f"REST CHECK FAILED: Rest at {t0:.2f}s-{t1:.2f}s has RMS "
            f"{level0:.1f} dBFS (limit: {REST_RMS_LIMIT_DBFS:.1f} dBFS) -- "
            "previous note may be ringing too long. "
            f"{len(failures)}/{checked} rest interval(s) exceed the limit."
            f"{fx_note}",
            detail))
    else:
        margin, t0, t1, level0, raw0 = worst_margin
        checks.append(Check(
            "rests.rms_below_limit", True,
            f"All {checked} rest interval(s) are below {REST_RMS_LIMIT_DBFS:.1f} "
            f"dBFS. Quietest margin: rest at {t0:.2f}s-{t1:.2f}s measured "
            f"{level0:.1f} dBFS ({margin:.1f} dB below the limit).",
            {"checked": checked, "worst_margin_db": margin, "intervals": all_intervals}))

    return checks


# ── 2d. peak / clipping check ────────────────────────────────────────────────
def check_peak_and_clipping(all_ch_audio):
    checks = []
    flat = all_ch_audio.reshape(-1)

    if flat.size == 0 or not np.any(flat != 0.0):
        checks.append(Check(
            "audio.not_all_zero", False,
            "PEAK CHECK FAILED: rendered audio is entirely silence (all "
            "samples are zero). The score produced no audible output at all."))
        return checks
    checks.append(Check("audio.not_all_zero", True,
                         "Rendered audio is not all zeros."))

    peak = float(np.max(np.abs(flat)))
    peak_db = 20.0 * math.log10(peak) if peak > 1e-12 else -120.0
    if peak_db > PEAK_LIMIT_DBFS:
        checks.append(Check(
            "audio.peak_below_limit", False,
            f"PEAK CHECK FAILED: rendered audio peaks at {peak_db:.2f} dBFS "
            f"(sample value {peak:.4f}), above the {PEAK_LIMIT_DBFS:.1f} "
            "dBFS limit -- the render is too loud and risks clipping on "
            "playback.",
            {"peak_dbfs": peak_db}))
    else:
        checks.append(Check("audio.peak_below_limit", True,
                             f"Peak level is {peak_db:.2f} dBFS "
                             f"(limit {PEAK_LIMIT_DBFS:.1f} dBFS)."))

    clipped = np.abs(all_ch_audio) >= CLIP_THRESHOLD
    consecutive_runs = []
    for ch in range(clipped.shape[1]):
        col = clipped[:, ch]
        if not col.any():
            continue
        # find run lengths of consecutive True
        diff = np.diff(col.astype(np.int8))
        run_starts = np.where(diff == 1)[0] + 1
        if col[0]:
            run_starts = np.concatenate(([0], run_starts))
        run_ends = np.where(diff == -1)[0] + 1
        if col[-1]:
            run_ends = np.concatenate((run_ends, [len(col)]))
        for s_i, e_i in zip(run_starts, run_ends):
            length = e_i - s_i
            if length > MAX_CONSECUTIVE_CLIPPED:
                consecutive_runs.append((ch, s_i, length))

    if consecutive_runs:
        ch0, s0, len0 = consecutive_runs[0]
        checks.append(Check(
            "audio.no_consecutive_clipping", False,
            f"PEAK CHECK FAILED: channel {ch0} has {len0} consecutive "
            f"samples at or above |{CLIP_THRESHOLD}| starting at sample "
            f"{s0} -- this is audible clipping/distortion. "
            f"{len(consecutive_runs)} such run(s) found.",
            {"count": len(consecutive_runs)}))
    else:
        total_clipped = int(clipped.sum())
        checks.append(Check("audio.no_consecutive_clipping", True,
                             "No consecutive clipped samples found "
                             f"(isolated single-sample peaks at threshold: {total_clipped})."))

    return checks


# ── 2e. determinism check ───────────────────────────────────────────────────
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_determinism(cli, score_path):
    checks = []
    with tempfile.TemporaryDirectory(prefix="tsuki_verify_det_a_") as d1, \
         tempfile.TemporaryDirectory(prefix="tsuki_verify_det_b_") as d2:
        try:
            wav1 = render_score(cli, score_path, d1)
            wav2 = render_score(cli, score_path, d2)
        except CliError as e:
            checks.append(Check(
                "determinism.rendered_twice", False,
                f"DETERMINISM CHECK FAILED: could not render the score twice "
                f"for comparison: {e}"))
            return checks

        h1 = sha256_file(wav1)
        h2 = sha256_file(wav2)
        if h1 != h2:
            checks.append(Check(
                "determinism.sha256_match", False,
                "DETERMINISM CHECK FAILED: rendering the same score twice "
                f"produced different audio (SHA256 {h1[:12]}... vs "
                f"{h2[:12]}...). The render pipeline is not reproducible -- "
                "something is using unseeded randomness or uninitialized "
                "memory.",
                {"sha256_a": h1, "sha256_b": h2}))
        else:
            checks.append(Check(
                "determinism.sha256_match", True,
                f"Two independent renders produced identical audio "
                f"(SHA256 {h1[:16]}...)."))
    return checks


# ── registered exemptions (M3 GATE: "--all: 全綠或有已記錄豁免") ───────────
# scores/verify_exemptions.json is an array of records:
#   {"file": "<basename of a .score.json>", "check": "<check-name prefix>",
#    "reason": "...", "approved": "<who/when>"}
# A record exempts every Check whose `name` STARTS WITH the record's "check"
# string, on the score whose filename (basename only) matches "file" exactly.
# This is deliberately narrow: e.g. "check": "rests.rms" matches the actual
# check name "rests.rms_below_limit" (a prefix match, since the GATE
# language speaks of "check families" like "rests.rms" rather than the exact
# internal Check.name), but does NOT match "rests.checked", and does not
# touch any other file. Any other failing check on the same file, or the
# same check family on a different file, still fails the run.
EXEMPTIONS_FILENAME = "verify_exemptions.json"


def find_exemptions_path():
    """scores/verify_exemptions.json, located relative to THIS file (not the
    process cwd), so `python tools/verify_score.py ...` works from any
    working directory."""
    return Path(__file__).resolve().parent.parent / "scores" / EXEMPTIONS_FILENAME


def load_exemptions(path=None):
    """Returns a list of exemption dicts (possibly empty). Never raises --
    a missing or malformed registry just means "no exemptions registered",
    reported to stderr so a typo doesn't silently disable an exemption."""
    path = Path(path) if path else find_exemptions_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"WARNING: could not load exemption registry {path}: {e}",
              file=sys.stderr)
        return []
    if not isinstance(data, list):
        print(f"WARNING: exemption registry {path} must be a JSON array; "
              "ignoring it (no exemptions registered).", file=sys.stderr)
        return []
    valid = []
    for i, rec in enumerate(data):
        if not (isinstance(rec, dict) and rec.get("file") and rec.get("check")
                and rec.get("reason")):
            print(f"WARNING: exemption registry {path} entry {i} is missing "
                  "required field(s) (file, check, reason); ignoring that "
                  "entry.", file=sys.stderr)
            continue
        valid.append(rec)
    return valid


def apply_exemptions(score_path, checks, exemptions):
    """Mutates `checks` in place: for every FAILING check that matches a
    registered exemption for this file (basename match + check-name-prefix
    match), sets its exempt_reason. Returns the list of (check, record)
    pairs that were exempted, for reporting. Passing checks are never
    touched -- an exemption can only ever change a fail into "exempt", never
    hide a check that already passed, and never turns a fail on an
    unregistered check/file into anything but a fail."""
    exempted = []
    basename = Path(score_path).name
    for c in checks:
        if c.ok:
            continue
        for rec in exemptions:
            if rec["file"] == basename and c.name.startswith(rec["check"]):
                c.exempt_reason = rec["reason"]
                exempted.append((c, rec))
                break
    return exempted


# ── main verification driver for a single score ────────────────────────────
def verify_one(cli, score_path, keep_render_dir=None, exemptions=None):
    """Returns (overall_ok: bool, checks: list[Check], measured: dict).
    `exemptions` (list of records from load_exemptions()) is applied to the
    finished check list before computing overall_ok -- see apply_exemptions()."""
    score_path = Path(score_path)
    all_checks = []
    measured = {}

    try:
        text = score_path.read_text(encoding="utf-8")
    except OSError as e:
        return False, [Check("file.readable", False,
                              f"Could not read file: {e}")], measured

    try:
        score = json.loads(text)
    except json.JSONDecodeError as e:
        return False, [Check("file.valid_json", False,
                              f"SCHEMA CHECK FAILED: file is not valid JSON: {e}")], measured
    all_checks.append(Check("file.valid_json", True, "File parses as valid JSON."))

    schema_checks, events = check_schema(score)
    all_checks.extend(schema_checks)

    mode_checks, dumped_events = check_modes(cli, score_path, events)
    all_checks.extend(mode_checks)

    # Stashed for tools/report_html.py (M4 --html mode): the parsed score,
    # its events, and the --dump-modes result are exactly what verify_one()
    # already computed above -- rather than have the HTML renderer re-read
    # and re-run --dump-modes itself (a second CLI subprocess call, and a
    # second source of truth that could drift from what was actually
    # judged), stash them here under underscore-prefixed keys so any caller
    # that wants them can use verify_one()'s own results directly. Ordinary
    # callers (print_report(), the --all summary) never read these keys.
    measured["_score"] = score
    measured["_events"] = events
    measured["_dumped_events"] = dumped_events

    # render once, reused for rest / peak-clip checks
    render_dir = Path(keep_render_dir) if keep_render_dir else None
    tmp_ctx = None
    if render_dir is None:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="tsuki_verify_render_")
        render_dir = Path(tmp_ctx.name)
    else:
        render_dir.mkdir(parents=True, exist_ok=True)

    render_failed = False
    try:
        try:
            wav_path = render_score(cli, score_path, render_dir)
        except CliError as e:
            all_checks.append(Check("render.ran", False,
                                     f"RENDER FAILED: {e}"))
            render_failed = True
        else:
            all_checks.append(Check("render.ran", True,
                                     f"Score rendered successfully to {wav_path.name}."))

            if wav_path.suffix.lower() != ".wav":
                # SHA256 determinism (below) is format-agnostic and still runs;
                # only the sample-level checks that need to decode audio are
                # skipped here (same WAV-only limitation as physics_verify.py).
                all_checks.append(Check(
                    "render.wav_readable", False,
                    f"RENDER CHECK FAILED: this score exports "
                    f"\"{wav_path.suffix.lstrip('.')}\" format, but this tool "
                    "can only analyze WAV audio directly (same limitation as "
                    "tools/physics_verify.py). Rest and peak/clipping checks "
                    "were skipped for this file -- re-export as WAV to verify "
                    "it, or convert the file separately and check it by hand."))
            else:
                sr, mono_audio, ch = read_wav_mono(wav_path)
                _, all_ch_audio = read_wav_all_channels(wav_path)
                measured["sample_rate"] = sr
                measured["channels"] = ch
                measured["duration_s"] = len(mono_audio) / sr if sr else 0.0
                measured["peak_dbfs"] = peak_dbfs(all_ch_audio.reshape(-1))
                measured["rms_dbfs"] = rms_dbfs(mono_audio)
                # Full arrays for report_html.py's spectrogram/f0/loudness
                # figures (same rendered WAV the checks above just used --
                # ROADMAP_PHYSICS.md M4 constraint: "All figures computed
                # from the SAME rendered WAV the checks used").
                measured["_mono_audio"] = mono_audio
                measured["_sample_rate"] = sr

                all_checks.extend(check_rests(events, sr, mono_audio, cli=cli, score=score))
                all_checks.extend(check_peak_and_clipping(all_ch_audio))
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()

    if render_failed:
        apply_exemptions(score_path, all_checks, exemptions or [])
        overall_ok = all(c.ok or c.exempt_reason for c in all_checks)
        return overall_ok, all_checks, measured

    all_checks.extend(check_determinism(cli, score_path))

    apply_exemptions(score_path, all_checks, exemptions or [])
    overall_ok = all(c.ok or c.exempt_reason for c in all_checks)
    return overall_ok, all_checks, measured


# ── reporting ────────────────────────────────────────────────────────────────
def print_report(score_path, ok, checks, measured, verbose=True):
    print(f"\n{'=' * 78}")
    print(f"SCORE: {score_path}")
    print(f"{'=' * 78}")
    if measured:
        dur = measured.get("duration_s")
        sr = measured.get("sample_rate")
        peak = measured.get("peak_dbfs")
        rms = measured.get("rms_dbfs")
        if dur is not None:
            print(f"  rendered: {dur:.2f}s @ {sr} Hz, "
                  f"peak {peak:.2f} dBFS, RMS {rms:.2f} dBFS")
    exempt_checks = [c for c in checks if c.exempt_reason]
    for c in checks:
        if c.exempt_reason:
            status = "EXEMPT"
        elif c.ok:
            status = "OK    "
        else:
            status = "FAIL  "
        if verbose or not c.ok or c.exempt_reason:
            print(f"  [{status}] {c.name}: {c.message}")
            if c.exempt_reason:
                print(f"           registered exemption: {c.exempt_reason}")
    if exempt_checks:
        print(f"  -> {'PASS' if ok else 'FAIL'} (with {len(exempt_checks)} "
              "registered exemption(s))")
    else:
        print(f"  -> {'PASS' if ok else 'FAIL'}")


def default_report_path(score_path):
    """<score_basename>.report.html next to the score (ROADMAP_PHYSICS.md M4
    "written next to the score"). Strips a trailing ".score.json" (the
    project's usual double extension) or plain ".json" before appending
    ".report.html", so "ai_radiance_m1.score.json" -> "ai_radiance_m1.report.html"."""
    name = score_path.name
    if name.endswith(".score.json"):
        base = name[: -len(".score.json")]
    elif name.endswith(".json"):
        base = name[: -len(".json")]
    else:
        base = name
    return score_path.with_name(base + ".report.html")


def find_all_scores(repo_root):
    """Task 2f directory list: examples/, vivaldi, ai_radiance, library/ (recursive)."""
    roots = [
        repo_root / "scores" / "examples",
        repo_root / "scores" / "classical" / "vivaldi_four_seasons",
        repo_root / "scores" / "originals" / "ai_radiance",
        repo_root / "scores" / "library",
    ]
    found = []
    for r in roots:
        if r.exists():
            found.extend(sorted(r.rglob("*.score.json")))
    return found


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    try:
        # line-buffered (not just UTF-8): --all can take many minutes over
        # scores/library + the Vivaldi movements, and the per-file progress
        # printed by verify_one()/print_report() should appear as it
        # happens rather than sit in a fully-buffered pipe until exit.
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

    ap = argparse.ArgumentParser(
        description="Whole-score verification for TsukiSynth (ROADMAP_PHYSICS.md M3). "
                     "Checks schema, modal data, rests, peak/clipping, and determinism "
                     "without relying on listening to the result.")
    ap.add_argument("score", nargs="?", help="path to a .score.json file")
    ap.add_argument("--all", action="store_true",
                     help="verify every .score.json under scores/examples, "
                          "scores/classical/vivaldi_four_seasons, "
                          "scores/originals/ai_radiance, and scores/library (recursive)")
    ap.add_argument("--html", metavar="SCORE",
                     help="generate a single-file, self-contained HTML visual "
                          "verification report for SCORE (ROADMAP_PHYSICS.md M4)")
    ap.add_argument("--html-out", metavar="PATH", default=None,
                     help="override the output path for --html (default: "
                          "<score_basename>.report.html next to the score)")
    ap.add_argument("--cli", default=None, help="path to TsukiSynthCLI executable")
    ap.add_argument("--quiet", action="store_true",
                     help="only print failing checks, not every passing one")
    args = ap.parse_args()

    cli = Path(args.cli) if args.cli else find_cli()
    if not cli or not cli.exists():
        print("ERROR: TsukiSynthCLI not found. Build it first "
              "(cmake --build build --target TsukiSynthCLI) or pass --cli.",
              file=sys.stderr)
        return 2
    print(f"CLI: {cli}")

    repo_root = Path(__file__).resolve().parent.parent
    exemptions = load_exemptions()
    if exemptions:
        print(f"Loaded {len(exemptions)} registered exemption(s) from "
              f"{find_exemptions_path()}.")

    if args.html:
        score_path = Path(args.html)
        if not score_path.exists():
            print(f"ERROR: score file not found: {score_path}", file=sys.stderr)
            return 2
        try:
            import report_html
        except ImportError as e:
            print(f"ERROR: could not import tools/report_html.py: {e}", file=sys.stderr)
            return 2

        ok, checks, measured = verify_one(cli, score_path, exemptions=exemptions)
        print_report(score_path, ok, checks, measured, verbose=not args.quiet)
        exempt_count = sum(1 for c in checks if c.exempt_reason)
        print(f"\nRESULT: {'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'}"
              + (f" (with {exempt_count} registered exemption(s))" if exempt_count else ""))

        html_text = report_html.generate_html_report(score_path, ok, checks, measured)
        out_path = Path(args.html_out) if args.html_out else default_report_path(score_path)
        out_path.write_text(html_text, encoding="utf-8")
        print(f"\nHTML report written to: {out_path}  ({len(html_text) / 1024.0:.1f} KB)")
        return 0 if ok else 1

    if args.all:
        score_files = find_all_scores(repo_root)
        if not score_files:
            print("ERROR: no .score.json files found under scores/examples, "
                  "scores/classical/vivaldi_four_seasons, "
                  "scores/originals/ai_radiance, scores/library.",
                  file=sys.stderr)
            return 2
        print(f"Found {len(score_files)} score file(s) to verify.\n")

        results = []
        for sp in score_files:
            try:
                ok, checks, measured = verify_one(cli, sp, exemptions=exemptions)
            except Exception as e:  # keep --all going even if one file explodes
                ok = False
                checks = [Check("internal.exception", False,
                                 f"INTERNAL ERROR while verifying this file: "
                                 f"{type(e).__name__}: {e}")]
                measured = {}
            print_report(sp.relative_to(repo_root), ok, checks, measured,
                         verbose=not args.quiet)
            results.append((sp, ok, checks))

        print(f"\n{'=' * 78}")
        print("SUMMARY")
        print(f"{'=' * 78}")
        n_pass = sum(1 for _, ok, _ in results if ok)
        n_fail = len(results) - n_pass
        total_exempt_checks = sum(1 for _, _, checks in results
                                   for c in checks if c.exempt_reason)
        for sp, ok, checks in results:
            failing = [c for c in checks if not c.ok and not c.exempt_reason]
            exempted = [c for c in checks if c.exempt_reason]
            status = "PASS" if ok else f"FAIL ({len(failing)} check(s))"
            if exempted:
                status += f" [{len(exempted)} exemption(s)]"
            print(f"  [{status:16s}] {sp.relative_to(repo_root)}"
                  + ("" if ok else f"  <- {failing[0].name}"))
        # Exempt counts are surfaced separately here and never folded into
        # n_pass above -- a registered exemption is not the same thing as a
        # check that actually passed (M3 GATE: "全綠或有已記錄豁免" requires
        # the exemption to stay visible, not disappear into the pass count).
        print(f"\n{n_pass}/{len(results)} score(s) passed all checks "
              f"({total_exempt_checks} check(s) covered by registered "
              f"exemption(s)), {n_fail} failed.")
        return 0 if n_fail == 0 else 1

    if not args.score:
        ap.print_help()
        return 2

    score_path = Path(args.score)
    if not score_path.exists():
        print(f"ERROR: score file not found: {score_path}", file=sys.stderr)
        return 2

    ok, checks, measured = verify_one(cli, score_path, exemptions=exemptions)
    print_report(score_path, ok, checks, measured, verbose=not args.quiet)
    exempt_count = sum(1 for c in checks if c.exempt_reason)
    if ok and exempt_count:
        print(f"\nRESULT: ALL CHECKS PASSED (with {exempt_count} registered "
              "exemption(s))")
    else:
        print(f"\nRESULT: {'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
