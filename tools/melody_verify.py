#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
melody_verify.py -- ear-free MELODY-POSITION verification for TsukiSynth.

WHY (docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md L1, 2026-08-20): the project's
terminal claim is "deaf people + AI can place a melody correctly by logic
alone". verify_score.py proves the NEGATIVE side of the time axis (declared
rests are silent) but nothing proved the POSITIVE side: that every scored
event actually SOUNDS at its declared time, at its declared pitch. Shifting
every note by 200 ms could pass every pre-existing gate. This tool closes
that gap, for any WAV whose provenance is a score.json -- CLI renders, host
harness renders (L2) and DAW exports (L3) all pass through this same judge.

Method (all deterministic, all documented):
  * Band bank: for each distinct in-score fundamental we build a +/-3% band
    (the repo's standard fundamental-isolation width, e.g. physics_verify.py
    F3) and compute a Hann/2048/hop-256 STFT band-energy track in dB.
  * ONSET (per event, "the note IS there"): the event's fundamental band
    must show a RISE (energy jumping >= RISE_DB above its local floor
    within <= RISE_SPAN frames) inside +/- ONSET_TOL_S of the declared
    time. The renderer places events sample-exactly
    (ScoreRenderer.h startSample = ev.time * sr), so the expectation is
    exact; the tolerance covers only the measurement (hop quantisation
    5.3 ms @ 48 kHz + exciter attack, tau_c is ms-scale).
  * PITCH (per event): amplitude centroid of the band over the early
    sustain (hard +/-3% band edges -- WF0909-C10B tried and REVERTED a
    raised-cosine edge taper meant to cut the estimator's own zero-offset
    bias below 1 cent; see measure_pitch_cents()'s docstring for why it
    was reverted rather than shipped), judged in cents against the
    --dump-modes course-centroid fundamental -- SAME 5.0-cent limit and
    same centroid convention the 2026-07-23 ratified tuner gate uses
    (verify_score.MODE_F0_TOL_CENTS). No new pitch tolerance is
    introduced. (measure_pitch_cents_legacy() below is now byte-identical
    in behaviour to measure_pitch_cents() -- kept as a separate name so
    the WF0909-C10B before/after numbers in
    reports/gate_outputs/wf0909_C10B_estimator.txt stay reproducible.)
  * EXTRA/MISPLACED ("no note is anywhere else"): every rise detected in
    ANY monitored band must coincide with SOME declared event's onset
    (strike transients are broadband, so any strike may light up any
    band). An unexplained rise fails -- this catches a note rendered at an
    undeclared moment (a shifted note shows up as missing at the declared
    time AND extra at the wrong time). The scan judges the time axis only;
    the pitch axis is judged per event.

Fail-closed refusals (UNVERIFIED, never silently PASS):
  * two events whose bands overlap AND whose onsets are closer than the
    match window -- the rise cannot be attributed (multi-pitch refusal,
    same philosophy as TODO C2);
  * delay effect active (echo rises are authored, not wrong melody; the
    extra-rise scan cannot distinguish them) -- extra-scan refused,
    per-event onset/pitch still judged;
  * FM events with a non-default fm_ratio (carrier pitch != note pitch is
    a creative choice this physical-position tool does not model).

Tolerance provenance (Rule 4 / R2 -- these may NEVER be widened to make a
run pass):
  ONSET_TOL_S = 0.010  proposed 2026-08-20 under the delegation ruling
                       (TODO.md C3-b): hop quantisation 256/48000 = 5.3 ms
                       + Hann window group spread; the sentinel selftest
                       prints the actual measurement-error distribution so
                       the margin is inspectable on every run.
  RISE_DB     = 15.0   a fresh strike fills its band from near-silence;
                       the slowest legal decay tail (T60 >= 0.3 s) falls
                       <= 2.7 dB over the 43 ms floor lookback, so a tail
                       can never self-trigger; 15 dB sits > 5x above that
                       drift while an actual onset jumps far more (the
                       sentinel run prints the observed margins).
  RISE_SPAN   = 5      frames (~27 ms): tau_c is ms-scale so a real attack
                       completes well inside this.
  FLOOR_LOOKBACK = 8   frames (~43 ms) of pre-onset minimum as local floor.
  BAND_GATE_DBFS = -70 band energy below this is treated as silence.

Usage:
  python tools/melody_verify.py <score.json>            # render + verify
  python tools/melody_verify.py <score.json> --wav F    # verify existing WAV
  python tools/melody_verify.py --selftest              # sentinel suite
  add --json OUT to write the machine-readable result.
Exit codes: 0 = no FAIL (UNVERIFIED count reported), 1 = FAIL, 2 = usage.
"""

import argparse
import importlib.util
import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("verify_score", ROOT / "verify_score.py")
vs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vs)

# -- constants (provenance in module docstring; R2: never widen) -------------
ONSET_TOL_S     = 0.010
BAND_REL_WIDTH  = 0.03      # +/-3%, repo-standard fundamental isolation
RISE_DB         = 15.0
RISE_SPAN       = 5
FLOOR_LOOKBACK  = 8
BAND_GATE_DBFS  = -70.0
PITCH_TOL_CENTS = vs.MODE_F0_TOL_CENTS   # 5.0, ratified 2026-07-23
# Pitch centroid segment: starts after the exciter transient, and must span
# AT LEAST one full beat period of a detuned course, or the centroid wobbles
# with the strings' phase alignment inside the window: the default cimbalom
# course spreads +/-5 cents, i.e. adjacent strings differ by ~0.289% of f0
# (~0.95 Hz at 330 Hz -> 1.05 s beat). A 0.4 s window measured the SAME
# render up to -7.7 c off (2026-08-20 host-probe run); 1.25 s covers >= 1
# beat period for f0 >= 275 Hz. Below that the coverage is partial -- an
# honest measurement limit, noted here rather than hidden.
PITCH_SEG_S     = (0.020, 1.250)
N_FFT, HOP      = 2048, 256
PAD_S           = 0.25      # prepended silence: gives t=0 events a floor
# Coarse STFT detection can flag a rise up to half a window EARLY (a frame
# whose tail overlaps the onset already gains energy; window-center
# convention). The coarse stage therefore only LOCATES candidates within
# +/-COARSE_TOL_S; the verdict uses the zero-phase refined estimate below.
COARSE_TOL_S    = 0.5 * N_FFT / 48000.0 + ONSET_TOL_S
# (Re, 2026-08-21 moonlight v3): the zero-phase 50%-crossing refiner's error
# scales with the band's envelope rise time (~1/bandwidth). Observed: 50-70
# Hz notes (band 3-4 Hz -> ~300 ms rise) measured 18-34 ms early -- ~10% of
# the rise time -- INCLUDING the piece's very first note over pure silence,
# so this is estimator resolution, not contamination. Requirement: error
# <= ONSET_TOL_S -> rise <= 100 ms -> bandwidth >= 10 Hz -> with the +/-3%
# band, f0 >= 10 / 0.06 = 167 Hz. Below that the ONSET claim is refused
# (fail-closed); the PITCH claim is still judged (its long centroid window
# does not depend on rise time).
ONSET_REFINE_MIN_F0 = 10.0 / (2.0 * BAND_REL_WIDTH)


class Spectrogram:
    """One shared |STFT| (Hann/N_FFT/HOP, frame time = window CENTER);
    every band track is a cheap slice of it. Computed once per WAV --
    per-band re-FFT made polyphonic corpus files quadratically slow."""

    def __init__(self, mono, sr):
        n = len(mono)
        if n < N_FFT:
            mono = np.pad(mono, (0, N_FFT - n))
            n = N_FFT
        frames = 1 + (n - N_FFT) // HOP
        idx = np.arange(N_FFT)[None, :] + (np.arange(frames) * HOP)[:, None]
        segs = mono[idx] * np.hanning(N_FFT)[None, :]
        self.mag2 = np.abs(np.fft.rfft(segs, axis=1)) ** 2
        self.freqs = np.fft.rfftfreq(N_FFT, 1.0 / sr)
        self.times = (np.arange(frames) * HOP + N_FFT / 2) / sr

    def band_db(self, f_lo, f_hi):
        sel = (self.freqs >= f_lo) & (self.freqs <= f_hi)
        if not sel.any():                    # band narrower than one bin:
            sel = np.zeros_like(self.freqs, bool)
            sel[int(np.argmin(np.abs(self.freqs - 0.5 * (f_lo + f_hi))))] = True
        e = np.sqrt(np.sum(self.mag2[:, sel], axis=1)) / (N_FFT / 2)
        return self.times, 20.0 * np.log10(np.maximum(e, 1e-12))


def detect_rises(times, db):
    """First frame of each group where energy jumps >= RISE_DB above the
    FLOOR_LOOKBACK-frame local floor within RISE_SPAN frames, gated at
    BAND_GATE_DBFS. The floor is the lookback MEDIAN, not the minimum: a
    detuned multi-string course (default 5-cent spread) produces brief deep
    beat nulls inside an ongoing note; a single-frame null would poison a
    min-floor and turn the beat recovery into a phantom onset (observed on
    the sentinel fixture, C4 course, 2026-08-20), while the median ignores
    dips narrower than half the lookback."""
    rises, in_group = [], False
    for k in range(1, len(db)):
        lo = max(0, k - FLOOR_LOOKBACK)
        floor = float(np.median(db[lo:k]))
        past = db[max(0, k - RISE_SPAN):k]
        jumped = (db[k] >= floor + RISE_DB and db[k] > BAND_GATE_DBFS
                  and (len(past) == 0 or db[k] - float(np.min(past)) >= RISE_DB * 0.6))
        if jumped and not in_group:
            rises.append(float(times[k]))
            in_group = True
        elif not jumped:
            in_group = False
    return rises


def band_of(f0):
    return (f0 * (1.0 - BAND_REL_WIDTH), f0 * (1.0 + BAND_REL_WIDTH))


def refined_onset(mono, sr, f_lo, f_hi, t_coarse):
    """Unbiased onset estimate: zero-phase FFT band mask -> analytic
    envelope -> 50% crossing. A zero-phase filter's step response is
    symmetric around the true transition, so the half-height crossing is an
    unbiased onset estimator (its pre-ringing advances exactly as much as
    its rise lags); residual bias is ~half the physical attack (tau_c,
    ms-scale), inside ONSET_TOL_S. Search is local to the coarse hit."""
    # Localised: a 2 s segment around the coarse hit (the band impulse
    # response is ~1/bandwidth ~ 60 ms, so 1 s of margin swamps edge
    # effects) -- a full-file FFT per event made long corpus files slow.
    seg_a = max(0, int((t_coarse - 1.0) * sr))
    seg_b = min(len(mono), int((t_coarse + 1.0) * sr))
    seg = mono[seg_a:seg_b]
    n = len(seg)
    if n < 256:
        return None
    spec = np.fft.fft(seg)
    fr = np.fft.fftfreq(n, 1.0 / sr)
    mask = np.zeros(n)
    mask[(fr >= f_lo) & (fr <= f_hi)] = 2.0       # analytic: positive freqs x2
    mask[0] = 0.0
    env = np.abs(np.fft.ifft(spec * mask))
    a = max(0, int((t_coarse - 0.040) * sr) - seg_a)
    b = min(n, int((t_coarse + 0.080) * sr) - seg_a)
    if b <= a:
        return None
    peak = float(np.max(env[a:b]))
    if peak <= 0:
        return None
    idx = np.nonzero(env[a:b] >= 0.5 * peak)[0]
    return (seg_a + a + int(idx[0])) / sr if len(idx) else None


def overlaps(a, b):
    return a[0] <= b[1] and b[0] <= a[1]


def measure_pitch_cents_legacy(mono, sr, f0, t_exp):
    """Band-limited amplitude-CENTROID pitch estimator -- kept VERBATIM,
    byte-for-byte the WF0907-C10 extraction of verify()'s original inline
    pitch block, under its own name so the WF0909-C10B before/after numbers
    in reports/c10b_estimator_before_after.md stay reproducible.

    WF0909-C10B tried to replace this with a raised-cosine-tapered variant
    (see measure_pitch_cents() below) to clear the self-cal sentinel's
    1-cent self-certification bar (this function's own error: max |error|
    = 1.1721 cents over the 1170-point development grid,
    reports/decision_packets/C10_selfcal_domain.zh-TW.md) -- that attempt
    was REVERTED (see measure_pitch_cents()'s docstring for the full
    numbers and why), so as of the WF0909-C10B fix round this function and
    measure_pitch_cents() are byte-identical in behaviour again. Both names
    are kept: this one for historical/comparison clarity, the other
    because it is the name every caller (verify(), stem_verify.py,
    partial_verify.py, measurement_selfcal.py) actually uses.

    Returns (cents, fail_reason): on success fail_reason is None; on
    failure cents is None and fail_reason is the same string verify() used
    to inline as r["reason"]."""
    s0 = int((t_exp + PITCH_SEG_S[0]) * sr)
    s1 = min(len(mono), int((t_exp + PITCH_SEG_S[1]) * sr))
    seg = mono[s0:s1]
    if len(seg) < 2048:
        return None, "segment too short for pitch"
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    fr = np.fft.rfftfreq(len(seg), 1.0 / sr)
    lo, hi = band_of(f0)
    m = (fr >= lo) & (fr <= hi)
    if not m.any() or float(np.sum(spec[m])) <= 0:
        return None, "no measurable band energy for pitch"
    f_meas = float(np.sum(fr[m] * spec[m]) / np.sum(spec[m]))
    cents = vs.cents_between(f_meas, f0)
    return cents, None


def measure_pitch_cents(mono, sr, f0, t_exp):
    """Pitch estimator: band-limited amplitude centroid of `mono` (sr Hz)
    over PITCH_SEG_S relative to onset time `t_exp` (already carrying
    whatever offset the caller's timeline uses -- verify() passes the
    +PAD_S analysis time), judged in cents against expected fundamental
    `f0`. This is the function verify(), stem_verify.py and
    partial_verify.py all call for the product GATE.

    AS OF THE WF0909-C10B FIX ROUND this is byte-identical to
    measure_pitch_cents_legacy() above (hard +/-3% rectangular band,
    band_of, no edge taper) -- the attempted replacement was tried,
    measured on BOTH the self-cal sentinel's accuracy axis and (this
    round's addition, WF0909-C10B fix round) its GAIN-FIDELITY axis, and
    REVERTED because every configuration found traded one for the other.
    Full story below, all numbers in
    reports/gate_outputs/wf0909_C10B_estimator.txt (step 1 = original
    round, step 2 = fix round).

    WHY THE ATTEMPT WAS MADE: the self-cal sentinel
    (tools/measurement_selfcal.py, 1170-point development grid) measures
    this hard-edge centroid's own error, AT ZERO true-vs-expected offset,
    at max |error| = 1.1721 cents -- above the 1-cent self-certification
    threshold the month-lead ruled the +/-5-cent product GATE needs before
    it can be trusted (C10 decision packet,
    reports/decision_packets/C10_selfcal_domain.zh-TW.md). Root cause
    (decision packet §0): summing energy over the WHOLE band with a HARD
    0/1 cutoff at its edges makes the result sensitive to exactly which
    bins the discrete FFT grid happens to place on which side of the
    boundary -- asymmetric Hann-window sidelobe leakage across that
    boundary then pulls the weighted mean off the true partial, worst
    where the band spans few bins (low f0, e.g. MIDI 37) or an inharmonic
    partial sits close to the edge (high f0, e.g. MIDI 100).

    FIVE CANDIDATES WERE TRIED AND ALL REJECTED, honestly recorded here
    rather than silently discarded (docs/workcards/WF0909_C10B_estimator
    .md §2.1 a/b/c for the first three; the fourth was the estimator this
    project briefly shipped before the fix-round audit caught it; the
    fifth was tried during the fix round itself):
      (a) 3-bin log-magnitude PARABOLIC interpolation around the single
          spectral peak (Smith & Serra 1987): passed both self-cal grids
          on ZERO-offset accuracy (dev max 0.2228 c, hold-out max 0.0832
          c) -- REJECTED on real rendered audio (melody_sentinel,
          --selftest): a course is 3 strings detuned +/-5 cents, i.e.
          separated by a FRACTION of one FFT bin at this window length, so
          within one partial beat cycle the peak bin locks onto whichever
          string's phase constructively dominates at that instant instead
          of the course's actual centre -- 4 of 5 sentinel notes went from
          PASS (<=1.6 c) to FAIL (up to -8.95 c, past the +/-5 c product
          GATE). The synthetic self-cal grid has no course/detuning model
          at all, so it could not have caught this.
      (b) two-frame PHASE-DIFFERENCE instantaneous frequency at the peak
          bin (phase-vocoder convention): passed both self-cal grids on
          zero-offset accuracy (dev max 0.3923 c) -- REJECTED for the
          IDENTICAL reason as (a): still a single-peak-bin method, same
          course failure on melody_sentinel (4/5 notes FAIL, up to
          -8.04 c).
      (c) zero-padding the SAME window before the SAME hard-edge centroid,
          swept 8x/16x/32x/64x -- REJECTED, does not converge below the
          1-cent line at all (max |error| 1.1796 / 1.1727 / 1.1693 /
          1.1710 c, asymptoting toward the un-padded 1.1721 c). Confirms
          the bias is real in-band sidelobe ENERGY, not a discrete-bin
          sampling artifact finer FFT sampling could interpolate away.
      (d) RAISED-COSINE EDGE TAPER (the estimator this project briefly
          shipped, PITCH_EDGE_TAPER_FRAC=0.75): a whole-band weighted mean
          -- same family as (c) -- but softening only the outer 75% of
          each band edge before summing, so course/detuning robustness is
          inherited (unlike (a)/(b)) while removing the hard 0/1 cutoff
          (c) never touched. On the zero-offset axis this WORKED: dev grid
          max |error| 0.2924 c, INDEPENDENT hold-out grid (off-lattice f0
          offsets, disjoint B/level/onset) 0.2465 c, melody_sentinel real
          audio improved 1.6007 c -> 0.4890 c with no PASS->FAIL
          regression. REJECTED by the fix-round audit on a SECOND axis the
          original round's hold-out grid never tested: gain fidelity when
          the TRUE frequency actually deviates from the EXPECTED one (the
          exact situation the +/-5-cent product GATE exists to catch).
          Both self-cal grids only ever centre the band on the SYNTHESIZED
          (already-shifted) frequency, so a taper that peaks its weight at
          the band's own centre necessarily also peaks at the true
          frequency in BOTH grids -- structurally blind to its own
          matched-filter behaviour. Measured with the sentinel's own
          measure_one(freq_offset_cents=...) (true frequency shifted away
          from the value passed as `f0`, mirroring real product use): at
          MIDI 37 (~69 Hz), harmonic, -6 dBFS, a true +12.0-cent deviation
          measured as only +4.806 c (gain 0.40, legacy's own +8.620 c on
          the SAME signal is gain 0.72) -- i.e. WITHOUT touching the
          +/-5-cent tolerance number, this taper shrank the EFFECTIVE
          tolerance at low f0 to roughly +/-12.5 cents worth of real
          mistuning before the GATE would catch it. A full taper-fraction
          sweep (0.75 down to 0.0 in 13 steps, same MIDI-36..100 sweep,
          offsets +-3/+-5/+-10/+-12 c, clean -6 dBFS signal) found the
          trade is CONTINUOUS and monotonic in the taper width -- no
          fraction gets the dev-grid error under 1.0 cent without a worst-
          case gain deficit at low MIDI staying above ~0.34 (34% of a real
          deviation silently absorbed); the fraction (~0.15-0.20) where
          dev-grid error first crosses 1.0 cent still carries a ~0.35-0.40
          gain deficit, no better than the shipped 0.75.
      (e) MEAN-SHIFT (self-referential) taper, tried during the fix round
          as a way to decouple (d)'s taper from the fixed hypothesis `f0`:
          start from the plain hard-cutoff centroid as a first estimate,
          then iterate the SAME raised-cosine taper re-centred on the
          CURRENT estimate (not on `f0`) until it converges (5 iterations
          is enough; 15 gives identical numbers). This measurably helps --
          at taper fraction 0.5 the worst-case gain deficit on the same
          offset sweep drops from (d)'s ~0.55-0.66 to ~0.31, with dev-grid
          max |error| = 0.7167 c (still < 1.0 c) -- but converges to a
          fixed point that is STILL worse than the legacy estimator's own
          gain fidelity at the same worst cell (MIDI 37, -12 c: mean-shift
          measures gain 0.687 vs legacy's own 0.885 on the identical
          signal) -- REJECTED for the same reason as (d), a smaller
          version of the identical defect, not a fix of it.
    CONCLUSION (fix round, WF0909-C10B): within the scope this card
    allows -- change only the frequency-estimation math inside this one
    function, leave band_of's +/-3% band selection untouched -- no
    variant of (c)/(d)/(e) achieves BOTH the self-cal sentinel's <=1-cent
    zero-offset bar AND gain fidelity at least as good as the legacy
    estimator's own (already imperfect, but not silently regressed)
    behaviour under a real deviation. Per this card's own §5 ("try three
    methods, if none reach <=1.0 including hold-out, stop and report the
    numbers"): five methods across two structurally different families
    were tried and none qualify -- this function REVERTS to the legacy
    hard-edge math (byte-identical to measure_pitch_cents_legacy() above)
    rather than ship a change that improves one number the sentinel
    checks while quietly weakening the number the product GATE actually
    depends on. The zero-offset bias this card set out to fix (1.1721 c
    > 1.0 c) remains UNFIXED; docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md §9
    and the C10 decision packet record this outcome and the still-open
    choice between the decision packet's original option A (narrow the
    claim domain, no code change) and a genuinely new option C (a method
    outside this family, not yet found).

    Band selection (band_of's +/-3% width itself), onset refinement
    (refined_onset), the Ra-Re refusal rules and course/detune handling
    were never touched by any of the five attempts above.

    Returns (cents, fail_reason): on success fail_reason is None; on
    failure cents is None and fail_reason is the same string verify() uses
    to inline as r["reason"]."""
    return measure_pitch_cents_legacy(mono, sr, f0, t_exp)


def expected_f0s(cli, score_path, events):
    """Per-event expected fundamental for a FLAT (non-layered) score.json --
    `events` is the score's own top-level "events" array, matched to
    --dump-modes output positionally by source_index. Modal engines:
    --dump-modes course centroid (physically true, incl. inharmonicity +
    detuning). FM with default ratio: equal temperament. f0s[i] None =>
    refusal reason in refusals[i].

    A layered score.json (top-level "layers", no "events") never reaches
    this function: verify() routes it to expected_f0s_layered() instead,
    on the flattened dump ScoreRenderer::dumpModesLayered() now produces
    (WF0907-E9 gave --dump-modes real layered support; before that, CLI
    --dump-modes on a layered file raised CliError("layer expansion is not
    implemented") and this function used to catch that string here as a
    whole-file refusal -- WF0907-E9b removed that branch since the CLI no
    longer raises it, and leaving it in would have been a stale claim about
    an upstream limitation that no longer exists)."""
    dumped = vs.dump_modes(cli, str(score_path)).get("events", [])
    by_src = {d.get("source_index"): d for d in dumped}
    f0s, partials, refusals, decays = [], [], [], []
    for i, ev in enumerate(events):
        f0 = None
        parts = []
        why = None
        eng = ev.get("engine")
        if ev.get("velocity", 0) <= 0:
            why = "zero velocity (renders nothing by contract)"
        elif eng == "fm":
            ratio = (ev.get("params") or {}).get("fm_ratio", 1.0)
            if abs(float(ratio) - 1.0) > 1e-9:
                why = "fm_ratio != 1: carrier pitch decoupled from note"
            else:
                f0 = vs.midi_to_hz(vs.note_to_midi(ev.get("note")))
                parts = [f0]
        else:
            d = by_src.get(i)
            f0 = vs.course_f0(d) if d else None
            if f0 is None:
                why = "no usable fundamental in --dump-modes output"
            else:
                # --dump-modes shape: "partials" = list of partial dicts for
                # string 0; "strings" = list of PER-STRING lists of partial
                # dicts (see ScoreRenderer::dumpModes). Union them all.
                seen = set()
                string_lists = d.get("strings") or [d.get("partials") or []]
                for plist in string_lists:
                    for p in (plist or []):
                        fq = p.get("freq") if isinstance(p, dict) else None
                        if fq and math.isfinite(fq) and fq > 0:
                            seen.add(float(fq))
                parts = sorted(seen) or [f0]
        f0s.append(f0)
        partials.append(parts)
        refusals.append(why)
        d = by_src.get(i)
        t60 = None
        if d is not None:
            plist = (d.get("partials") or [])
            if plist and isinstance(plist[0], dict):
                dv = plist[0].get("decay")
                if dv and math.isfinite(dv) and dv > 0:
                    t60 = float(dv)
        decays.append(t60)
    return f0s, partials, refusals, decays


def expected_f0s_layered(dumped_events):
    """WF0907-E9b: expected_f0s()'s counterpart for a LAYERED score.json.

    `dumped_events` is ScoreRenderer::dumpModesLayered()'s flattened
    "events" array (each leaf's own dumpModes() event objects, re-emitted
    with a layer-offset "time", "layer_source", and gain-scaled amplitude
    fields -- see RenderApp.cpp's --dump-modes branch and
    ScoreRenderer.h's dumpModesLayered()). There is no top-level score
    "events" array to match these against for a layered file
    (validateLayeredScore() requires "layers" instead), so the caller
    (verify()) builds its synthetic per-event list directly from this same
    `dumped_events`, in the same order -- the mapping here is POSITIONAL
    (index i <-> dumped_events[i]), not by "source_index" (that field is
    each LEAF's own local index and repeats across layers, so a
    source_index-keyed dict the way expected_f0s() uses one would silently
    collide entries from different layers).

    Known, honest degradation vs expected_f0s() (this is why WF0907-E9b's
    layered verification is INFORMATIONAL ONLY, never GATE-judged):
      * no velocity gate -- unneeded: dumpModes() already omits
        zero-velocity events ("not part of the render plan", see the C++
        comment in ScoreRenderer::dumpModes()), so every entry here already
        renders.
      * no FM fm_ratio!=1 special case -- expected_f0s() detects a
        decoupled FM carrier from the raw score event's own "params",
        which the flattened dump does not carry (only engine/note/midi +
        the dumped modal partials survive flattening). Every engine here,
        FM included, is judged uniformly off its own dumped
        partials/strings via vs.course_f0() -- the same measurement modal
        engines already use, applied to FM too rather than left unjudged.
      * is_course() (verify()'s extra-scan, see its definition) also reads
        each event's "params" (num_strings/detuning_cents) to tell a
        detuned multi-string course from a plain event -- absent here for
        the same reason as the FM ratio above, so it falls back to the
        default num_strings=3/detuning_cents=5.0 for every layered
        cimbalom/piano/string event, fail-open (over-widens refused
        beat-interference rises rather than under-widening). See the
        comment at is_course()'s definition for the full mechanism.
    """
    f0s, partials, refusals, decays = [], [], [], []
    for d in dumped_events:
        f0 = vs.course_f0(d)
        parts = []
        if f0 is None:
            refusals.append("no usable fundamental in --dump-modes output")
        else:
            refusals.append(None)
            seen = set()
            string_lists = d.get("strings") or [d.get("partials") or []]
            for plist in string_lists:
                for p in (plist or []):
                    fq = p.get("freq") if isinstance(p, dict) else None
                    if fq and math.isfinite(fq) and fq > 0:
                        seen.add(float(fq))
            parts = sorted(seen) or [f0]
        f0s.append(f0)
        partials.append(parts)
        t60 = None
        plist = (d.get("partials") or [])
        if plist and isinstance(plist[0], dict):
            dv = plist[0].get("decay")
            if dv and math.isfinite(dv) and dv > 0:
                t60 = float(dv)
        decays.append(t60)
    return f0s, partials, refusals, decays


def verify(score_path, wav_path=None, keep_json=None, quiet=False, cli=None):
    """cli=None (default, unchanged behaviour): TsukiSynthCLI is found by
    verify_score.find_cli(). cli=<path> (WF1003-S): that binary is used for
    the baseline render and every --dump-modes call, so a caller that runs
    an explicit --cli (stem_verify) needs no lookup override."""
    score_path = Path(score_path)
    score = json.loads(score_path.read_text(encoding="utf-8"))
    is_layered = "layers" in score
    events = score.get("events", [])
    if cli is None:
        cli = vs.find_cli()

    tmpdir = None
    if wav_path is None:
        tmpdir = tempfile.TemporaryDirectory(prefix="melody_verify_")
        wav_path = vs.render_score(cli, str(score_path), tmpdir.name)
    sr, mono, _ch = vs.read_wav_mono(wav_path)
    # Prepend digital silence so an event at t=0 still has a floor to rise
    # from (all internal analysis times carry the +PAD_S offset; every
    # reported/judged time has it removed again).
    mono = np.concatenate([np.zeros(int(PAD_S * sr)), mono])

    if is_layered:
        # WF0907-E9b: a layered score.json has no top-level "events" (its
        # "layers" list stands in for that -- see validateLayeredScore()),
        # so `events` above is []. Build a synthetic per-event list
        # directly from the flattened --dump-modes output instead, in the
        # SAME order as expected_f0s_layered()'s own positional read of it
        # (both walk `dumped` once, so index i in `events` below lines up
        # with dumped[i]). This is informational only, never GATE-judged --
        # see the docstring on expected_f0s_layered() for exactly what
        # cannot be reproduced from a flattened dump (FM ratio decoupling)
        # and what does not need to be (the velocity gate).
        dumped = vs.dump_modes(cli, str(score_path)).get("events", [])
        events = [{"time": d.get("time", 0.0), "note": d.get("note"),
                   "engine": d.get("engine"), "layer_source": d.get("layer_source")}
                  for d in dumped]
        f0s, partials, refusals, decays = expected_f0s_layered(dumped)
    else:
        f0s, partials, refusals, decays = expected_f0s(cli, score_path, events)

    # Reads the TOP-LEVEL score's own global.effects only. A layered
    # score.json's effects live per-leaf (each layer.source's own "global"),
    # not here -- a leaf's reverb/delay is invisible to this gate for a
    # layered file, so a layered run cannot claim the delay-echo/reverb-tail
    # refusals below the way a flat score's own run can. Another reason
    # WF0907-E9b's layered verification stays informational only.
    fx = (score.get("global") or {}).get("effects") or {}
    delay_wet = float(((fx.get("delay") or {}).get("wet")) or 0.0)
    rev = fx.get("reverb") or {}
    reverb_decay = (float(rev.get("decay") or 0.0)
                    if float(rev.get("wet") or 0.0) > 0 else 0.0)

    def effective_t60(i):
        """In-band energy decays at the SLOWER of the dry modal T60 and the
        reverb T60 (2026-08-20 moonlight v2 trial: predicting tails with the
        dry T60 alone left 567 re-strikes judged as measurable when a 5.8 s
        reverb was actually holding their bands up). None = unpredictable."""
        d = decays[i]
        if d is None:
            return None
        return max(d, reverb_decay)

    # -- collision refusal: overlapping bands + onsets inside match window --
    for i, ev in enumerate(events):
        if refusals[i] or f0s[i] is None:
            continue
        for j, ev2 in enumerate(events):
            if j <= i or refusals[j] or f0s[j] is None:
                continue
            if (overlaps(band_of(f0s[i]), band_of(f0s[j]))
                    and abs(float(ev["time"]) - float(ev2["time"]))
                        <= 2 * ONSET_TOL_S + 0.05):
                refusals[i] = refusals[j] = "band collision with concurrent event"

    # -- polyphony refusals (2026-08-20, from the moonlight corpus trial: --
    # -- 1043 spurious FAILs, three physically-predictable causes). All   --
    # -- three use only --dump-modes physics (partial freqs + T60), so    --
    # -- every refusal is a computed prediction, not a heuristic.         --
    #
    # (Ra) RE-STRIKE MASKING: the rise detector needs a RISE_DB jump above
    # the local floor, but an arpeggio re-strikes the same pitch while the
    # previous strike's tail still rings. Predict the tail: level drops
    # 60 dB * dt / T60; if the previous same-band event has decayed less
    # than RISE_DB + 6 dB (6 = margin for the new strike not being at the
    # old one's level) by this onset, the jump is physically unmeasurable
    # -> refuse the onset check rather than fail it.
    # (Rb) PARTIAL-INTO-BAND PITCH CONTAMINATION: the pitch centroid is
    # band-limited, but a CONCURRENT event's dumped partial landing inside
    # this event's fundamental band drags the centroid -> refuse PITCH only
    # (onset can still be judged: the transient is the event's own).
    onset_refused = [None] * len(events)
    pitch_refused = [None] * len(events)
    for i, ev in enumerate(events):
        if refusals[i] or f0s[i] is None:
            continue
        t_i = float(ev["time"])
        lo_i, hi_i = band_of(f0s[i])
        for j, ev2 in enumerate(events):
            if j == i or refusals[j] or f0s[j] is None:
                continue
            t_j = float(ev2["time"])
            j_parts_in_band = any(lo_i <= pf <= hi_i for pf in partials[j])
            # (Ra): j strikes BEFORE i and shares i's band
            if t_j < t_i and j_parts_in_band and onset_refused[i] is None:
                t60_j = effective_t60(j)
                if t60_j is None:
                    onset_refused[i] = ("prior same-band event ev%d has no "
                                        "predictable tail (no T60)" % j)
                else:
                    drop_db = 60.0 * (t_i - t_j) / t60_j
                    if drop_db < RISE_DB + 6.0:
                        onset_refused[i] = (
                            "re-strike over ev%d's ringing tail (predicted "
                            "only %.1f dB decayed, need >= %.1f)"
                            % (j, drop_db, RISE_DB + 6.0))
            # (Rb): j sounds DURING i's pitch segment and leaks into i's band
            if pitch_refused[i] is None and j_parts_in_band:
                seg_a, seg_b = t_i + PITCH_SEG_S[0], t_i + PITCH_SEG_S[1]
                et = effective_t60(j)
                j_end = t_j + (et if et is not None else PITCH_SEG_S[1])
                if t_j < seg_b and j_end > seg_a:
                    pitch_refused[i] = ("concurrent ev%d partial inside "
                                        "fundamental band" % j)

    # -- band tracks, computed once per distinct band -----------------------
    spectro = Spectrogram(mono, sr)
    tracks = {}

    def track(f0):
        key = round(f0, 3)
        if key not in tracks:
            lo, hi = band_of(f0)
            tracks[key] = spectro.band_db(lo, hi)
        return tracks[key]

    results = []
    onset_errs = []
    for i, ev in enumerate(events):
        r = {"index": i, "time": float(ev.get("time", 0.0)),
             "note": ev.get("note"), "engine": ev.get("engine")}
        if refusals[i]:
            r["verdict"] = "UNVERIFIED"
            r["reason"] = refusals[i]
            results.append(r)
            continue
        f0 = f0s[i]
        if onset_refused[i]:
            r["verdict"] = "UNVERIFIED"
            r["reason"] = onset_refused[i]
            results.append(r)
            continue
        skip_onset = None
        if f0 < ONSET_REFINE_MIN_F0:
            skip_onset = ("f0 %.1f Hz < %.0f Hz: band too narrow for +/-%.0f ms"
                          " onset refinement (Re)"
                          % (f0, ONSET_REFINE_MIN_F0, ONSET_TOL_S * 1e3))
        t_exp = float(ev["time"]) + PAD_S          # analysis timeline is padded
        times, db = track(f0)
        rises = detect_rises(times, db)
        # Stage 1 (coarse): does ANY candidate rise sit inside the coarse
        # window? (STFT can flag up to half a window early -- see COARSE_TOL_S.)
        near = [t for t in rises if abs(t - t_exp) <= COARSE_TOL_S + HOP / sr]
        r["expected_f0_hz"] = f0
        if skip_onset is None and not near:
            # (Rd, 2026-08-21 moonlight v3): "no rise" is only PROOF OF
            # ABSENCE when the band was near-silent beforehand -- a floor
            # already energised (dense texture + reverb) makes a RISE_DB
            # jump unmeasurable regardless of whether the note sounded.
            pre = [db[k] for k in range(len(times))
                   if t_exp - 0.043 <= times[k] < t_exp]
            floor = float(np.median(pre)) if pre else BAND_GATE_DBFS
            if floor > BAND_GATE_DBFS + 6.0:
                skip_onset = ("pre-onset band floor %.1f dBFS already energised"
                              " (> %.1f): rise unmeasurable (Rd)"
                              % (floor, BAND_GATE_DBFS + 6.0))
            else:
                r["verdict"] = "FAIL"
                r["reason"] = ("no onset in near-silent fundamental band %.1f-%.1f Hz"
                               " (pre-onset floor %.1f dBFS) within +/-%.0f ms of t=%.3fs"
                               % (band_of(f0)[0], band_of(f0)[1], floor,
                                  COARSE_TOL_S * 1e3, t_exp - PAD_S))
                results.append(r)
                continue
        if skip_onset is None:
            # Stage 2 (refined, the actual verdict): zero-phase envelope 50%
            # crossing, judged against ONSET_TOL_S.
            t_c = min(near, key=lambda t: abs(t - t_exp))
            lo_b, hi_b = band_of(f0)
            t_ref = refined_onset(mono, sr, lo_b, hi_b, t_c)
            if t_ref is None:
                r["verdict"] = "UNVERIFIED"
                r["reason"] = "onset refinement found no envelope in the search window"
                results.append(r)
                continue
            err = t_ref - t_exp
            if abs(err) > ONSET_TOL_S:
                r["verdict"] = "FAIL"
                r["reason"] = ("refined onset off by %+.2f ms (limit %.0f ms)"
                               % (err * 1e3, ONSET_TOL_S * 1e3))
                r["onset_err_ms"] = err * 1e3
                results.append(r)
                continue
            onset_errs.append(err)
            r["onset_err_ms"] = err * 1e3
        else:
            r["onset_refused"] = skip_onset

        # pitch: band-limited amplitude centroid over early sustain
        # (t_exp already carries the +PAD_S analysis offset)
        if pitch_refused[i]:
            r["verdict"] = "UNVERIFIED"
            note = (" (onset PASS, err %+.2f ms)" % r["onset_err_ms"]
                    if "onset_err_ms" in r else " (onset also refused)")
            r["reason"] = "pitch refused: " + pitch_refused[i] + note
            results.append(r)
            continue
        cents, pitch_fail = measure_pitch_cents(mono, sr, f0, t_exp)
        if pitch_fail:
            r["verdict"] = "UNVERIFIED"
            r["reason"] = pitch_fail
            results.append(r)
            continue
        r["pitch_cents"] = cents
        if abs(cents) > PITCH_TOL_CENTS:
            r["verdict"] = "FAIL"
            r["reason"] = "pitch off by %+.2f cents (limit %.1f)" % (cents, PITCH_TOL_CENTS)
        elif "onset_refused" in r:
            # pitch verified, onset refused (Rd/Re) -> the event as a whole
            # stays UNVERIFIED; the pitch number is kept as evidence.
            r["verdict"] = "UNVERIFIED"
            r["reason"] = r["onset_refused"] + "; pitch verified %+.2f c" % cents
        else:
            r["verdict"] = "PASS"
        results.append(r)

    # -- extra/misplaced scan -----------------------------------------------
    extra_fails = []
    extra_refused = []
    if delay_wet > 0:
        extra_state = "UNVERIFIED"
        extra_reason = "delay wet=%s: echoes are authored rises" % delay_wet
    else:
        extra_state, extra_reason = "PASS", ""
        for key, (times, db) in tracks.items():
            lo, hi = key * (1 - BAND_REL_WIDTH), key * (1 + BAND_REL_WIDTH)
            # A strike transient is BROADBAND (exciter noise burst): every
            # declared onset momentarily lights up every band (observed on
            # the sentinel fixture: each strike registered a rise in every
            # other note's band, 2026-08-20). A rise is therefore explained
            # by ANY declared event's onset -- the extra-scan judges the
            # TIME axis only ("energy appears at no undeclared moment");
            # the pitch axis is judged by the per-event checks above
            # (sentinel C proves a wrong-pitch declaration still fails).
            explainers = [float(ev["time"]) + PAD_S for i, ev in enumerate(events)
                          if not refusals[i]]
            # Coarse window here too: the scan's job is catching rises far
            # from ANY declared explanation; sub-COARSE_TOL_S placement
            # errors are already caught by the per-event refined check.
            # (Rc, 2026-08-20 moonlight trial): two same-band tails ringing
            # simultaneously BEAT against each other -- a slow, deep AM whose
            # recovery the median floor cannot suppress (beat periods are
            # seconds; the floor lookback is 43 ms). If >= 2 in-band events'
            # tails (t_j .. t_j + T60_j, unknown T60 treated as still
            # ringing) overlap a rise, the rise is attributable to tail
            # interference -> not judgable as an extra note (refuse, listed).
            # An event is a detuned multi-string course (cimbalom/piano
            # default: 3 strings, +/-5 cents) -> its OWN strings beat, with
            # deep AM nulls whose recovery registers as a rise (moonlight
            # v3: 5-cent spread at 69 Hz beats every ~5 s). One ringing
            # course therefore explains interference rises on its own.
            #
            # WF0907-E9b, known fail-open for a LAYERED score: the synthetic
            # `events` verify() builds for a layered run (see the is_layered
            # branch above) come from the flattened --dump-modes "events"
            # array, which carries only time/note/engine/layer_source --
            # never the raw score event's own "params" (num_strings,
            # detuning_cents). `ev.get("params")` is therefore ALWAYS None
            # for a layered event, so `prm` is always {} and this predicate
            # falls back to the DEFAULT num_strings=3/detuning_cents=5.0 for
            # every cimbalom/piano/string-engine layered event, whether or
            # not that leaf actually declared a multi-string detuned course.
            # Net effect: is_course() over-widens refused_rises (treats more
            # rises as course-beat interference than a flat-score run of the
            # same leaf would) -- fail-open, same direction as the other two
            # documented degradations in expected_f0s_layered()'s docstring.
            # Cannot be fixed without the leaf's own params reaching the
            # flattened dump (a --dump-modes / dumpModesLayered() change,
            # out of this card's scope); left honestly labeled here instead.
            def is_course(ev):
                if ev.get("engine") not in ("cimbalom", "piano", "string"):
                    return False
                prm = ev.get("params") or {}
                return (int(prm.get("num_strings", 3)) >= 2
                        and float(prm.get("detuning_cents", 5.0)) > 0)
            in_band_events = [(float(ev["time"]), effective_t60(i), is_course(ev))
                              for i, ev in enumerate(events)
                              if not refusals[i] and f0s[i] is not None
                              and any(lo <= pf <= hi for pf in partials[i])]
            refused_rises = 0
            for t in detect_rises(times, db):
                t_r = t - PAD_S
                if any(abs(t - te) <= COARSE_TOL_S + HOP / sr
                       for te in explainers):
                    continue
                ringing_evs = [(tj, t60j, crs) for (tj, t60j, crs) in in_band_events
                               if tj <= t_r and (t60j is None or t_r <= tj + t60j)]
                ringing = len(ringing_evs)
                if ringing >= 2 or any(crs for (_, _, crs) in ringing_evs):
                    refused_rises += 1
                    continue
                extra_fails.append({"band_hz": key, "rise_time": t_r})
            if refused_rises:
                extra_refused.append({"band_hz": key, "count": refused_rises})
        if extra_fails:
            extra_state = "FAIL"
            extra_reason = "; ".join(
                "unexplained onset at %.3fs in %.1f Hz band"
                % (x["rise_time"], x["band_hz"]) for x in extra_fails[:5])
        if extra_refused and extra_state == "PASS":
            extra_state = "PASS"   # refusals are listed, not failed
            extra_reason = ("%d rise(s) in %d band(s) refused as multi-tail "
                            "beat interference"
                            % (sum(x["count"] for x in extra_refused),
                               len(extra_refused)))

    n_pass = sum(1 for r in results if r["verdict"] == "PASS")
    n_fail = sum(1 for r in results if r["verdict"] == "FAIL") + (1 if extra_state == "FAIL" else 0)
    n_unv = sum(1 for r in results if r["verdict"] == "UNVERIFIED") + (1 if extra_state == "UNVERIFIED" else 0)

    max_abs_err = max((abs(e) for e in onset_errs), default=None)
    report = {"score": str(score_path), "wav": str(wav_path),
              "events": results,
              "extra_scan": {"verdict": extra_state, "reason": extra_reason,
                             "unexplained": extra_fails,
                             "beat_refused": extra_refused},
              "onset_err_ms": {"max_abs": (max_abs_err * 1e3) if max_abs_err is not None else None,
                               "tol": ONSET_TOL_S * 1e3},
              "summary": {"pass": n_pass, "fail": n_fail, "unverified": n_unv}}
    if is_layered:
        # WF0907-E9b: layered runs are informational only, never
        # GATE-judged (see the is_layered branch above and
        # expected_f0s_layered()'s docstring for why) -- main() reads this
        # to keep the exit code from acting like a real GATE for a layered
        # score.json, matching that claim instead of just stating it
        # (audit finding, WF0908-C10b fix round). Added ONLY for a layered
        # run, never for a flat one, so a flat score's report dict (and its
        # --json output) stays byte-identical to before this fix round --
        # required for WF0907-C10 §9.1's extract-before/after JSON-identity
        # proof (GATE 1), which this key must not disturb.
        report["informational"] = True
    if keep_json:
        Path(keep_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not quiet:
        if is_layered:
            print("  (informational only -- layered score.json, NOT "
                  "GATE-judged; see EARFREE_MELODY_GATE_DESIGN.zh-TW.md "
                  "WF0907-E9b / expected_f0s_layered() docstring)")
        for r in results:
            line = "  [%s] ev%d t=%.3f note=%s" % (r["verdict"], r["index"], r["time"], r["note"])
            if "onset_err_ms" in r:
                line += " onset_err=%+.2fms" % r["onset_err_ms"]
            if "pitch_cents" in r:
                line += " pitch=%+.2fc" % r["pitch_cents"]
            if r["verdict"] != "PASS":
                line += "  <- " + r.get("reason", "")
            print(line)
        print("  [extra-scan] " + extra_state + (("  <- " + extra_reason) if extra_reason else ""))
        print("  summary: %d PASS / %d FAIL / %d UNVERIFIED" % (n_pass, n_fail, n_unv))
    if tmpdir:
        tmpdir.cleanup()
    return report


# -- sentinel selftest -------------------------------------------------------
FIXTURE = ROOT.parent / "scores" / "tests" / "melody_sentinel.score.json"


def selftest():
    """Five judgments from ONE render (the fixture is monophonic, fx-free):
      A unmodified declarations        -> every event PASS, extra-scan PASS
      B ev2 declared 100 ms later      -> FAIL (missing at declared + extra)
      C ev3 declared a semitone up     -> FAIL (missing in that band)
      D ev1 removed from declarations  -> FAIL (extra: unexplained rise)
      E phantom event added            -> FAIL (missing)
    B-E mutate DECLARATIONS ONLY; the WAV stays A's render, so each verdict
    is attributable purely to the declared-vs-actual position mismatch."""
    cli = vs.find_cli()
    base = json.loads(FIXTURE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="melody_selftest_") as td:
        wav = vs.render_score(cli, str(FIXTURE), td)

        def run(mut, name):
            s = json.loads(json.dumps(base))
            mut(s)
            p = Path(td) / (name + ".score.json")
            p.write_text(json.dumps(s), encoding="utf-8")
            return verify(p, wav_path=wav, quiet=True)

        ok = True
        A = verify(FIXTURE, wav_path=wav, quiet=True)
        a_ok = (A["summary"]["fail"] == 0 and A["summary"]["unverified"] == 0
                and A["summary"]["pass"] == len(base["events"]))
        print("[%s] sentinel A: unmodified fixture verifies clean"
              " (max |onset err| = %.2f ms, tol %.0f ms)"
              % ("PASS" if a_ok else "FAIL",
                 A["onset_err_ms"]["max_abs"] if A["onset_err_ms"]["max_abs"] is not None else float("nan"),
                 A["onset_err_ms"]["tol"]))
        if not a_ok:
            for r in A["events"]:
                if r["verdict"] != "PASS":
                    print("    ev%d %s: %s" % (r["index"], r["verdict"], r.get("reason")))
            if A["extra_scan"]["verdict"] != "PASS":
                print("    extra-scan: " + A["extra_scan"]["reason"])
        ok &= a_ok

        def expect_fail(rep, name, desc):
            good = rep["summary"]["fail"] >= 1
            print("[%s] sentinel %s: %s -> %d FAIL as required"
                  % ("PASS" if good else "FAIL", name, desc, rep["summary"]["fail"]))
            return good

        B = run(lambda s: s["events"][2].__setitem__("time", s["events"][2]["time"] + 0.100), "B")
        ok &= expect_fail(B, "B", "+100 ms time shift is caught")
        C = run(lambda s: s["events"][3].__setitem__("note", s["events"][3]["note"] + 1), "C")
        ok &= expect_fail(C, "C", "+1 semitone transposition is caught")

        def drop1(s):
            s["events"].pop(1)
        D = run(drop1, "D")
        ok &= expect_fail(D, "D", "undeclared (extra) note is caught")

        def phantom(s):
            e = json.loads(json.dumps(s["events"][0]))
            e["time"] = 2.05
            # +2 semitones (D4): a pitch NO fixture note or partial occupies.
            # (+7 = G4 was tried first and correctly triggered the Ra
            # re-strike refusal instead of a FAIL -- the phantom must be in
            # a fresh band to be a *measurable* absence.)
            e["note"] = e["note"] + 2
            s["events"].append(e)
            s["events"].sort(key=lambda x: x["time"])
        E = run(phantom, "E")
        ok &= expect_fail(E, "E", "declared-but-absent (phantom) note is caught")

        print("SELFTEST " + ("PASS (5/5)" if ok else "FAIL"))
        return 0 if ok else 1


# -- deaf-accessible piano-roll HTML report ---------------------------------
# The final link of the "melody position is verifiable by LOGIC AND SIGHT"
# chain (EARFREE_MELODY_GATE_DESIGN section 4): expected note boxes overlaid
# on the actual spectrogram -- green = verified, red = failed, grey =
# refused. Reuses report_html.py's spectrogram/PNG machinery so the visual
# language matches the M4-approved report; deliberately a SEPARATE page so
# the signed-off M4 report itself stays untouched.

VERDICT_COLORS = {"PASS": "#2e7d32", "FAIL": "#c62828", "UNVERIFIED": "#757575"}


def write_html_report(report, score, wav_path, out_path):
    import importlib.util as _ilu
    _rspec = _ilu.spec_from_file_location("report_html", ROOT / "report_html.py")
    rh = _ilu.module_from_spec(_rspec)
    _rspec.loader.exec_module(rh)

    sr, mono, _ch = vs.read_wav_mono(wav_path)
    spec = rh.compute_spectrogram(sr, mono, freq_max=4000.0)
    uri = rh.png_data_uri(spec["width"], spec["height"], spec["rgb_bytes"])
    dur, fmax = spec["duration_s"], spec["freq_max_hz"]

    boxes = []
    for r in report["events"]:
        f0 = r.get("expected_f0_hz")
        if not f0 or f0 > fmax:
            continue
        lo, hi = band_of(f0)
        left = 100.0 * r["time"] / max(dur, 1e-9)
        width = 100.0 * 0.30 / max(dur, 1e-9)   # fixed 0.3 s display width
        top = 100.0 * (1.0 - hi / fmax)
        height = max(0.8, 100.0 * (hi - lo) / fmax)
        color = VERDICT_COLORS.get(r["verdict"], "#757575")
        tip = "ev%d %s %s" % (r["index"], r.get("note"), r["verdict"])
        if "onset_err_ms" in r:
            tip += " onset %+.2fms" % r["onset_err_ms"]
        if "pitch_cents" in r:
            tip += " pitch %+.2fc" % r["pitch_cents"]
        boxes.append(
            '<div class="nbox" title="%s" style="left:%.3f%%;top:%.3f%%;'
            'width:%.3f%%;height:%.3f%%;border-color:%s"></div>'
            % (rh.esc(tip), left, top, width, height, color))
    for x in report["extra_scan"].get("unexplained", []):
        f0 = x["band_hz"]
        if f0 > fmax:
            continue
        left = 100.0 * x["rise_time"] / max(dur, 1e-9)
        top = 100.0 * (1.0 - f0 / fmax)
        boxes.append(
            '<div class="xmark" title="%s" style="left:%.3f%%;top:%.3f%%"></div>'
            % ("unexplained rise %.3fs @ %.1f Hz" % (x["rise_time"], f0),
               left, top))

    rows = []
    for r in report["events"]:
        rows.append(
            "<tr><td>%d</td><td>%.3f</td><td>%s</td><td>%s</td>"
            "<td>%s</td><td>%s</td><td style='color:%s;font-weight:700'>%s</td>"
            "<td>%s</td></tr>"
            % (r["index"], r["time"], rh.esc(str(r.get("note"))),
               ("%.1f" % r["expected_f0_hz"]) if r.get("expected_f0_hz") else "-",
               ("%+.2f" % r["onset_err_ms"]) if "onset_err_ms" in r else "-",
               ("%+.2f" % r["pitch_cents"]) if "pitch_cents" in r else "-",
               VERDICT_COLORS.get(r["verdict"], "#757575"), r["verdict"],
               rh.esc(r.get("reason", ""))))
    su = report["summary"]
    ex = report["extra_scan"]
    title = ((score.get("meta") or {}).get("title")) or report["score"]
    html = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"/>
<title>%s - 旋律位置驗證 Melody-Position Report</title><style>
body{font-family:system-ui,sans-serif;margin:2em;background:#fafafa;color:#222}
.card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:1em 1.5em;margin-bottom:1.5em}
.wrap{position:relative;display:inline-block}
.wrap img{display:block;max-width:100%%}
.nbox{position:absolute;border:2px solid;border-radius:2px;box-shadow:0 0 0 1px rgba(255,255,255,.6)}
.xmark{position:absolute;width:10px;height:10px;margin:-5px;background:#c62828;transform:rotate(45deg);box-shadow:0 0 0 1px #fff}
table{border-collapse:collapse;width:100%%}td,th{border:1px solid #ddd;padding:4px 8px;font-size:.9em}
.plain{background:#eef6ff;border-radius:6px;padding:.5em .8em}
.badge{display:inline-block;padding:.2em .8em;border-radius:1em;color:#fff;font-weight:700;margin-right:.5em}
</style></head><body>
<h1>%s — 旋律位置驗證</h1>
<p class="plain">💬 白話：底圖是實際渲染出來的聲音（頻譜圖）。每個<b>方框</b>是樂譜宣告
「這個時間、這個音高應該有一個音」的位置——<span style="color:#2e7d32">綠框=驗證通過</span>、
<span style="color:#c62828">紅框=沒對上</span>、<span style="color:#757575">灰框=無法可靠判定（拒答）</span>。
<b>紅色菱形</b>=聲音出現在樂譜沒宣告的位置。全部綠框、沒有菱形，就代表旋律的位置
「照邏輯放對了」——不需要聽。</p>
<div class="card">
<span class="badge" style="background:#2e7d32">%d PASS</span>
<span class="badge" style="background:#c62828">%d FAIL</span>
<span class="badge" style="background:#757575">%d UNVERIFIED</span>
extra-scan: <b>%s</b> %s</div>
<div class="card"><div class="wrap"><img src="%s" width="%d" height="%d"/>%s</div>
<p>0 - %.1f s，0 - %.0f Hz（線性）。onset 容差 ±%.0f ms、pitch 容差 ±%.1f cents。</p></div>
<div class="card"><table><tr><th>#</th><th>t(s)</th><th>note</th><th>f0(Hz)</th>
<th>onset err(ms)</th><th>pitch(c)</th><th>verdict</th><th>reason</th></tr>%s</table></div>
<p class="hint">tools/melody_verify.py — EARFREE_MELODY_GATE_DESIGN.zh-TW.md L1/&#167;4</p>
</body></html>""" % (
        rh.esc(str(title)), rh.esc(str(title)),
        su["pass"], su["fail"], su["unverified"],
        ex["verdict"], rh.esc(ex.get("reason", "")),
        uri, spec["width"], spec["height"], "".join(boxes),
        dur, fmax, ONSET_TOL_S * 1e3, PITCH_TOL_CENTS, "".join(rows))
    Path(out_path).write_text(html, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("score", nargs="?")
    ap.add_argument("--wav")
    ap.add_argument("--json")
    ap.add_argument("--html")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.score:
        ap.print_help()
        sys.exit(2)
    rep = verify(a.score, wav_path=a.wav, keep_json=a.json)
    if a.html:
        score = json.loads(Path(a.score).read_text(encoding="utf-8"))
        wav = rep["wav"]
        if a.wav is None:
            # the tempdir render is gone; re-render for the report
            cli = vs.find_cli()
            import tempfile as _tf
            with _tf.TemporaryDirectory(prefix="melody_html_") as td:
                wav = vs.render_score(cli, a.score, td)
                write_html_report(rep, score, wav, a.html)
        else:
            write_html_report(rep, score, wav, a.html)
        print("  html report: %s" % a.html)
    # WF0907-E9b: a layered score.json's report is informational only (see
    # verify()'s "informational" field) -- its exit code must not act like
    # a real GATE's, matching the claim in expected_f0s_layered()'s
    # docstring instead of contradicting it (audit finding, WF0908-C10b fix
    # round).
    if rep.get("informational"):
        sys.exit(0)
    sys.exit(1 if rep["summary"]["fail"] else 0)


if __name__ == "__main__":
    main()
