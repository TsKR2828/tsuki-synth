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
    sustain, judged in cents against the --dump-modes course-centroid
    fundamental -- SAME 5.0-cent limit and same centroid convention the
    2026-07-23 ratified tuner gate uses (verify_score.MODE_F0_TOL_CENTS).
    No new pitch tolerance is introduced.
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


def expected_f0s(cli, score_path, events):
    """Per-event expected fundamental. Modal engines: --dump-modes course
    centroid (physically true, incl. inharmonicity + detuning). FM with
    default ratio: equal temperament. f0s[i] None => refusal reason in
    refusals[i]."""
    try:
        dumped = vs.dump_modes(cli, str(score_path)).get("events", [])
    except vs.CliError as e:
        if "layer expansion is not implemented" in str(e):
            # Layered scores have no --dump-modes (upstream CLI limitation,
            # 2026-08-21 corpus sweep) -> the whole file is a refusal, not a
            # crash: no expected-f0 ground truth exists to judge against.
            print("  [UNVERIFIED] whole file: layered score has no --dump-modes"
                  " ground truth (CLI: layer expansion not implemented)")
            sys.exit(3)
        raise
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


def verify(score_path, wav_path=None, keep_json=None, quiet=False):
    score_path = Path(score_path)
    score = json.loads(score_path.read_text(encoding="utf-8"))
    events = score.get("events", [])
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

    f0s, partials, refusals, decays = expected_f0s(cli, score_path, events)

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
        s0 = int((t_exp + PITCH_SEG_S[0]) * sr)
        s1 = min(len(mono), int((t_exp + PITCH_SEG_S[1]) * sr))
        seg = mono[s0:s1]
        if len(seg) < 2048:
            r["verdict"] = "UNVERIFIED"
            r["reason"] = "segment too short for pitch"
            results.append(r)
            continue
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        fr = np.fft.rfftfreq(len(seg), 1.0 / sr)
        lo, hi = band_of(f0)
        m = (fr >= lo) & (fr <= hi)
        if not m.any() or float(np.sum(spec[m])) <= 0:
            r["verdict"] = "UNVERIFIED"
            r["reason"] = "no measurable band energy for pitch"
            results.append(r)
            continue
        f_meas = float(np.sum(fr[m] * spec[m]) / np.sum(spec[m]))
        cents = vs.cents_between(f_meas, f0)
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
    if keep_json:
        Path(keep_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not quiet:
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
    sys.exit(1 if rep["summary"]["fail"] else 0)


if __name__ == "__main__":
    main()
