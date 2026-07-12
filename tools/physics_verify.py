#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
physics_verify.py — ear-free verification that TsukiSynth's RENDERED audio
matches the PHYSICS-MODEL predictions.

This closes "落差 D" of the 2026-06 project goal:
    deaf people + AI verify sound by physical theory, NOT by listening.

Pipeline (per probe = engine × MIDI note):
  1. write a probe .score.json  (single note, all FX off, normalize off)
  2. render it via TsukiSynthCLI  (deterministic since the NoiseGen seeding fix)
  3. FFT the sustain segment, peak-pick each partial (parabolic-interpolated)
  4. compare measured partials against the model-predicted partials
  5. report f0 cents error + per-partial % error, then PASS / FAIL

Why the predictions are exact & clean:
  * Chromatic uses tuneChromaticModesToMidi(); Cimbalom uses tensionForNote().
    Both pin the fundamental to the MIDI pitch:  f0 = 440 * 2**((midi-69)/12).
  * Modal partial RATIOS are material/size-independent (E, rho, L, d all cancel
    in f_n / f_1), so they are universal constants:
        tongue_drum (free-free Euler-Bernoulli beam): r_n = (betaL_n / betaL_1)**2
        water_gong  (Kirchhoff circular plate):        r_n = (j_n / j_1)**2
        cimbalom    (stiff string):  r_n ~= n, with an inharmonic stretch
                                     f_n = n*f1*sqrt(1+B n^2) (reported, not failed)
        fm piano (ratio 1):          harmonic, r_n = n

T60_RATIO_TOLERANCE = (0.5, 2.0)   # measured/model ratio must be within this range
                                    # (M5-5b, tightened from (0.2, 5.0) after the
                                    # 5a measurement rework -- judged, not informational)

Usage:
    python tools/physics_verify.py                 # default probe set
    python tools/physics_verify.py --notes 60 69   # MIDI notes to test
    python tools/physics_verify.py --engines tongue_drum water_gong
    python tools/physics_verify.py --cli <path-to-TsukiSynthCLI.exe>
    python tools/physics_verify.py --levels        # velocity/output-level report
    python tools/physics_verify.py --t60           # M5: modal decay T60 judgment
                                                    # (narrowband envelope log-slope
                                                    # vs --dump-modes theory, modal
                                                    # engines, ratio tol 0.5-2.0)
    python tools/physics_verify.py --amps          # M2-2d: first-5-partial rel-dB
                                                    # judgment vs --dump-modes theory
                                                    # (modal engines, MIDI 60, +/-3.0dB)
    python tools/physics_verify.py --full          # M1 breadth: note-range scan
                                                    # (>=6 notes/engine) + material
                                                    # scan (modal engines) + velocity
                                                    # x2 -> +6dB judgment (all engines)
                                                    # + M2-2d amplitude judgment
Exit code 0 = all probes within tolerance.
"""

import argparse, json, math, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np

# M5-5b (2026-07-12): tightened from the (0.2, 5.0) informational placeholder
# to the (0.5, 2.0) target registered in ROADMAP_PHYSICS.md §6, after the 5a
# measurement rework (narrowband +/-3% bandpass around the MEASURED f0 +
# beat-period-averaged envelope for multi-string courses) brought every modal
# engine's ratio to 1.00-1.28 at MIDI 60 and 72, reproducibly (see
# reports/gate_outputs/phase_g_gate_t60.txt). --t60 is now judged (exit-code
# affecting), matching --full/--amps.
T60_RATIO_TOLERANCE = (0.5, 2.0)   # measured/model ratio must be within this range

# ── physics constants (mirror the C++ models) ───────────────────────────────
# Free-free Euler-Bernoulli beam eigenvalues betaL  (BeamModel.h)
# SOURCE (M7 7b, 2026-07-12): analytic roots of cosh(x)*cos(x)=1, verified
# numerically (scipy brentq) to 7-8 sig figs: 4.7300407, 7.8532046, 10.9956078,
# 14.1371655, 17.2787597. Matches to stated precision -- see docs/EIGENVALUE_SOURCES.md.
BEAM_BETAL = [4.730041, 7.853205, 10.995608, 14.137165, 17.278760]
# True clamped circular Kirchhoff-plate frequency parameters Omega=lambda^2
# (Leissa) used by PlateModel.h. f is proportional to Omega (linear).
# SOURCE (M7 7b, 2026-07-12): Leissa NASA SP-160 Table 2.1 (clamped circular
# plate); all 8 entries verified digit-for-digit against the primary source and
# independently re-solved (Jn'*In - In'*Jn = 0, mpmath). Max deviation 0.03%.
# See docs/EIGENVALUE_SOURCES.md.
PLATE_OMEGA = [10.2158, 21.260, 34.877, 39.771, 51.030, 60.829, 69.666, 84.583]


def beam_ratios(n):
    b1 = BEAM_BETAL[0]
    return [(b / b1) ** 2 for b in BEAM_BETAL][:n]


def plate_ratios(n):
    o1 = PLATE_OMEGA[0]
    return [o / o1 for o in PLATE_OMEGA][:n]   # f proportional to Omega


# Free-edge circular plate Omega=lambda^2 (Leissa, nu=0.33 exactly) — for A/B.
# SOURCE (M7 7c, 2026-07-12): Leissa NASA SP-160 Table 2.5. 6/7 entries match
# Table 2.5 EXACTLY. CORRECTION APPLIED (Phase H, 2026-07-12, 月月 sign-off,
# Rule 10 before/after audio re-render done): index 4, (m=4,n=0), was 21.83,
# updated to 21.527 -- the independently re-solved exact free-plate
# characteristic-equation root (eq. 2.14, nu=0.33, mpmath 40-digit precision,
# reproduced twice independently in Phase G and Phase H), consistent with
# Table 2.5's own footnoted-approximate 21.6 (asymptotic formula, not exact).
# See src/physics/PlateModel.h and docs/EIGENVALUE_SOURCES.md for the full
# derivation and cross-validation against the table's other 6 exact entries.
# Old value 21.83 kept on record in docs/EIGENVALUE_SOURCES.md.
PLATE_FREE_OMEGA = [5.253, 9.084, 12.23, 20.52, 21.527, 35.25, 38.55]

def plate_free_ratios(n):
    o1 = PLATE_FREE_OMEGA[0]
    return [o / o1 for o in PLATE_FREE_OMEGA][:n]


def harmonic_ratios(n):
    return [float(k) for k in range(1, n + 1)]


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


# ── engine probe definitions ────────────────────────────────────────────────
# tol_pct: per-partial pass tolerance (%). inharmonic engines report (not fail)
# the upward stretch of high partials.
ENGINES = {
    "cimbalom": dict(
        engine="cimbalom", ratios=harmonic_ratios, npart=6, tol_pct=3.0,
        inharmonic=True,
        params={"material": "steel", "strike_position": 0.27, "diameter_mm": 0.8},
    ),
    "tongue_drum": dict(
        engine="tongue_drum", ratios=beam_ratios, npart=5, tol_pct=4.0,
        inharmonic=False,
        params={"material": "aluminum", "strike_position": 0.27,
                "thickness_mm": 3.0},
    ),
    "water_gong": dict(
        engine="water_gong", ratios=plate_ratios, npart=6, tol_pct=4.0,
        inharmonic=False,
        params={"material": "bronze", "strike_position": 0.30,
                "thickness_mm": 4.0, "plate_free_edge": False},
    ),
    "water_gong_free": dict(
        # npart=4: free plate has two close modes (~3.91 & 4.16, ~6% apart) that
        # the +/-6% measurement window cannot resolve; first 4 are well-separated.
        engine="water_gong", ratios=plate_free_ratios, npart=4, tol_pct=4.0,
        inharmonic=False,
        params={"material": "bronze", "strike_position": 0.30,
                "thickness_mm": 4.0, "plate_free_edge": True},
    ),
    "fm": dict(
        engine="fm", ratios=harmonic_ratios, npart=6, tol_pct=2.0,
        inharmonic=False,
        params={"fm_preset": 0},
    ),
    "piano": dict(
        engine="piano", ratios=harmonic_ratios, npart=6, tol_pct=3.0,
        inharmonic=True,
        params={"material": "steel"},
    ),
}

# M7-7a (2026-07-12): tightened from the (12.0 cent) placeholder to the 5.0
# cent target registered in ROADMAP_PHYSICS.md §6 ("人耳可辨閾約 5 cents，
# 標準不得低於耳朵"). Evidence: --full note-range scan (6 notes/engine, all
# 6 engines) + material scan (9 UI materials x 3 modal engines) at full
# precision (see reports/gate_outputs/phase_g_gate_full_f0.txt) measured a
# WORST-CASE |cents| of 0.880 (tongue_drum, wood_maple material) -- every
# other engine/material/note combination measured well under 0.1 cents. No
# per-engine exception was needed: measure_f0()'s power-weighted spectral
# centroid (see its docstring) already averages the multi-string course to
# its true acoustic center, so the cimbalom/piano detuned-course beating
# this task anticipated does NOT show up at the model's default
# detuningCents=5.0 -- a 2-point scaling experiment (detuning_cents=5/20/40,
# cimbalom & piano, MIDI 60) confirmed the centroid shift DOES scale with
# detuning (~0.003 / 0.044 / 0.199 cents) but stays two orders of magnitude
# under the 5-cent limit at the shipped default. A single global constant is
# therefore correct here; a per-engine override dict was not warranted by
# the data. (verify_score.py's MODE_F0_TOL_CENTS is a DIFFERENT measurement
# -- the raw --dump-modes string-0 value, not an audio centroid -- and was
# NOT tightened; see the comment on that constant for why.)
F0_TOL_CENTS = 5.0  # fundamental pitch tolerance (audio-measured, power-weighted centroid)


# ── M1-1a: per-engine valid MIDI range ──────────────────────────────────────
# Source: ROADMAP_PHYSICS.md §3 M1 task 1a — the plugin's documented "sweet
# spot" playable range per engine (Cim C2-C7 / Chr C3-C6 / FM C1-C7 / Piano
# A0-C8). This is a playability/design range, not a hard DSP limit; §1g of
# the roadmap requires recording (not hiding) any out-of-range failure here.
ENGINE_RANGES = {
    "cimbalom":        (36, 96),    # C2-C7
    "tongue_drum":     (48, 84),    # C3-C6
    "water_gong":      (48, 84),    # C3-C6
    "water_gong_free": (48, 84),    # C3-C6 (same physical instrument as water_gong)
    "fm":              (24, 96),    # C1-C7
    "piano":           (21, 108),   # A0-C8
}


def scan_notes(lo, hi, n=6):
    """M1-1b: n evenly-spaced MIDI notes spanning [lo, hi] inclusive (both
    endpoints always included). Rounded to the nearest integer MIDI note and
    de-duplicated (keeps order) so a narrow range doesn't emit repeats."""
    if n <= 1 or hi <= lo:
        return [lo]
    step = (hi - lo) / float(n - 1)
    notes = [int(round(lo + step * i)) for i in range(n)]
    out = []
    for m in notes:
        if not out or out[-1] != m:
            out.append(m)
    return out


# ── WAV reader (16 / 24 / 32-bit PCM → mono float) ──────────────────────────
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
        a = a.reshape(-1, ch).mean(axis=1)
    return sr, a


# ── spectral peak measurement (parabolic-interpolated) ──────────────────────
def measure_partials(sr, x, predicted_freqs):
    start = int(0.02 * sr)
    seg = x[start:start + int(0.50 * sr)]   # onset window: fast-decaying high modes still present
    if len(seg) < int(0.1 * sr):
        seg = x[start:]
    if len(seg) < 64:
        return [None] * len(predicted_freqs)
    seg = seg * np.hanning(len(seg))
    N = 1 << int(math.ceil(math.log2(len(seg) * 4)))   # zero-pad ×4
    spec = np.abs(np.fft.rfft(seg, N))
    binhz = sr / N
    out = []
    for fp in predicted_freqs:
        lo, hi = fp * 0.94, fp * 1.06
        klo, khi = int(lo / binhz), int(hi / binhz) + 1
        klo, khi = max(klo, 1), min(khi, len(spec) - 1)
        if khi <= klo:
            out.append(None); continue
        k = klo + int(np.argmax(spec[klo:khi]))
        a, b, c = spec[k - 1], spec[k], spec[k + 1]
        d = a - 2 * b + c
        delta = 0.5 * (a - c) / d if abs(d) > 1e-12 else 0.0
        out.append(((k + delta) * binhz, float(spec[k])))
    return out


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ── FIX2/FIX3 (Phase I, 2026-07-13): adaptive f0-analysis window ────────────
# FIX2 root cause (reports/phase_h_before_after.md §4): measure_f0()'s OLD
# fixed 0.05-1.55s window skips the entire note for ultra-short decays (rubber
# T60 = 14-28ms after materials physicalization) -- by 50ms the signal is 2+
# T60 periods gone, so the window contains nothing but noise floor.
# FIX3 root cause (same report, §6): the SAME fixed 1.55s window, at extreme
# high notes with the NEW long steel T60, keeps slow-decaying high partials
# alive for the whole window; their Hann-window sidelobes leak into the
# narrow (+/-6%) fundamental search band and bias the power-weighted centroid
# (piano MIDI108: +5.2..+7.33 cents).
# Both are the same underlying bug: a window length that isn't derived from
# anything about the note being measured. Two independent derivations bound
# it now (the tighter one wins):
# FIX2 attack-skip: src/physics/HammerImpulse.h documents the model's own
# excitation contact-time constants (kTauCCotton=6.0ms is the LONGEST of the
# four hammer/mallet presets -- Felt/Wood/Metal are all shorter). That 6.0ms
# is the physically real "attack transient" duration in this model (broadband
# excitation noise before the struck body settles into pure modal ringing),
# not something that should scale with the STRUCK MATERIAL's decay time (T60)
# -- those are two unrelated physical quantities (excitation-side vs
# resonator-side). Dividing by 10 (not 4) keeps the skip a small fraction
# even of an ultra-short note, since for the shortest T60s in this corpus
# (rubber, 14-28ms) even the hammer's own 6ms contact time is already a large
# fraction of the note's total life.
F0_WINDOW_START_CAP_S = 0.006    # FIX2: HammerImpulse's longest documented
                                  # mallet contact time (kTauCCotton)
F0_WINDOW_START_T60_DIV = 10.0
F0_WINDOW_LEN_MIN_S = 0.030     # FIX2: 30ms floor -- shortest window that still
                                 # gives a usable FFT bin count at any sample rate
F0_WINDOW_LEN_MAX_S = 1.5       # unchanged ceiling (== old fixed window's span)
# FIX2 window length: this codebase's "decay"/model_t60 is ALREADY a -60dB
# (T60) point, not a 1/e time constant tau (see MODAL_DECAY_LN1000 above:
# amp(t) = amp0*exp(-ln(1000)*t/decayTime)) -- confirmed empirically: rendered
# ultra-short (rubber) notes are bit-exact zero in the WAV by ~1.4*model_T60
# (past the quantization floor). A naive "4x" multiplier (the rule-of-thumb
# for settling a 1/e tau) was tried first and measured WORSE (tongue_drum/
# rubber: -13.8 cents) because it pushes the Hann window's peak-weight region
# (the window's temporal center) well past the point the signal has already
# died to silence, so the FFT ends up dominated by edge/leakage artifacts
# instead of the live signal. 2x keeps the window's center close to where the
# note is transitioning from "mostly alive" to "silent" (the Hann taper's
# reduced weight near the far edge naturally de-emphasizes the dead tail
# instead of centering on it) -- measured -0.2 to +0.6 cents across all 3
# modal engines' rubber probes (see validation notes), vs 1x's 0.5-3.8 cents
# (fewer usable cycles) and 4x's -4.5 to -13.8 cents (Hann-center-in-silence
# bias).
F0_WINDOW_T60_MULT = 2.0
F0_ZEROPAD_MIN_N = 1 << 18      # FIX2: zero-pad floor. A 30ms window at 48kHz
                                 # is only ~1440 samples (2^11 zero-pad) -- far
                                 # too coarse a bin grid for a centroid over a
                                 # +/-6% band to land within a few cents; 2^18
                                 # gives ~0.18 Hz bins at 48kHz regardless of
                                 # how short the physical window is.
# FIX3: cycles-based cap so a long model_T60 can't force an arbitrarily long
# window at high f0. Derivation: a Hann window's main lobe is 4/T Hz wide
# (null-to-null); measure_f0's own search band is +/-6% of f0 (12% total,
# see klo/khi below). Requiring the main lobe to fit within HALF that band
# (a 2x safety margin, so a neighbouring partial's lobe/sidelobes have room
# to fall off before reaching band centre) gives 4/T <= 0.06*f0_pred, i.e.
# T <= (4/0.06)/f0_pred = 66.7/f0_pred seconds -- a fixed number of CYCLES of
# f0_pred, independent of amplitude/T60/material. This is derived purely from
# the window's own known spectral shape and the harness's own existing search
# -band width, not fitted to any specific note's pass/fail.
F0_LEAKAGE_SAFETY = 2.0
F0_WINDOW_CYCLES_NUM = 4.0 / (0.06 * F0_LEAKAGE_SAFETY)   # ~33.3 cycles of f0_pred


# ── robust fundamental via power-weighted spectral centroid ─────────────────
# Over a long window the centroid of the fundamental band averages the cimbalom's
# multi-string detuned cluster to its true center, while staying correct for a
# clean inharmonic single peak (water gong / tongue drum). NSDF/autocorrelation
# is NOT used: inharmonic modal spectra have no true period, so it mislocates f0.
def measure_f0(x, sr, f0_pred, model_t60=None):
    """model_t60: the MODEL's own predicted fundamental T60 (seconds), read
    via --dump-modes / model_fundamental_decay() by the caller BEFORE this
    call -- non-circular: it only sizes the OBSERVATION window (see FIX1's
    docstring on the same principle for the T60 probe). None falls back to
    the historical fixed 1.5s/50ms-skip window (used only if a caller can't
    supply a model prediction)."""
    if model_t60 and model_t60 > 0:
        start = min(F0_WINDOW_START_CAP_S, model_t60 / F0_WINDOW_START_T60_DIV)
        length_t60 = _clamp(F0_WINDOW_T60_MULT * model_t60,
                             F0_WINDOW_LEN_MIN_S, F0_WINDOW_LEN_MAX_S)
        # FIX3 leakage cap only applies when we actually HAVE a model T60 --
        # it exists specifically to bound how long a materials-physicalized
        # modal engine's window can get at high f0 (see docstring above). A
        # caller with no model prediction (e.g. `fm`, entirely outside the
        # materials/modal-decay path per module docstring) gets the
        # historical fixed window untouched, below.
        if f0_pred and f0_pred > 0:
            length_leak = _clamp(F0_WINDOW_CYCLES_NUM / f0_pred,
                                  F0_WINDOW_LEN_MIN_S, F0_WINDOW_LEN_MAX_S)
            length = min(length_t60, length_leak)   # tighter bound wins (FIX2 vs FIX3)
        else:
            length = length_t60
    else:
        start = 0.05
        length = 1.5   # historical fixed window, byte-for-byte, incl. no FIX3 cap

    i0, i1 = int(start * sr), int((start + length) * sr)
    seg = x[i0:i1]
    # Fallback only if the rendered file itself ended before the (intentionally
    # short, for fast-decaying materials) window did -- NOT just because the
    # window is short by design. Grabbing a later/longer slice in that case
    # would defeat FIX2 (it would run straight past an ultra-short T60 note
    # into pure noise floor).
    if len(seg) < 32 and i0 < len(x):
        seg = x[i0:]
    if len(seg) < 32:
        return None
    seg = seg * np.hanning(len(seg))
    N = max(F0_ZEROPAD_MIN_N, 1 << int(math.ceil(math.log2(len(seg)))))
    spec = np.abs(np.fft.rfft(seg, N))
    binhz = sr / N
    klo = max(1, int(f0_pred * 0.94 / binhz))
    khi = min(len(spec) - 1, int(f0_pred * 1.06 / binhz) + 1)
    if khi <= klo:
        return None
    power = spec[klo:khi] ** 2
    if power.sum() <= 0.0:
        return None
    freqs = np.arange(klo, khi) * binhz
    return float((freqs * power).sum() / power.sum())


# ── FIX2 validation: synthetic self-check (no CLI/audio involved) ──────────
def selftest_measure_f0_short_window():
    """FIX2 self-check (task requirement): a pure decaying sinusoid at a
    KNOWN frequency, T60=20ms (matching the rubber regime that exposed the
    old fixed-window bug), run through the IDENTICAL measure_f0() code path.
    Returns (ok, recovered_cents)."""
    sr = 48000
    f_known = 440.0
    t60 = 0.020
    n = int(0.5 * sr)
    t = np.arange(n) / sr
    decay_rate = MODAL_DECAY_LN1000 / t60
    x = np.exp(-decay_rate * t) * np.sin(2.0 * np.pi * f_known * t)
    f0_meas = measure_f0(x, sr, f_known, model_t60=t60)
    if f0_meas is None:
        return False, None
    c = cents(f0_meas, f_known)
    return abs(c) <= 3.0, c


# ── probe render via CLI ────────────────────────────────────────────────────
def build_probe_score(eng, midi, outdir, sr=48000, vel=0.85, dur=2.0,
                       params_override=None, tag=""):
    """Writes a probe .score.json and returns (path, fn) WITHOUT rendering any
    audio. Split out of render_probe() (Phase I, 2026-07-13) so a caller that
    only needs --dump-modes' model predictions (e.g. the FIX1 T60 pre-flight
    below) doesn't have to pay for a full CLI render first -- --dump-modes
    only ever reads the score file, never the rendered wav."""
    spec = ENGINES[eng]
    # params_override (M1-1c, material scan): merged on top of the engine's
    # default params so callers only need to specify the one field (material)
    # they're varying; everything else stays the harness's standard probe.
    params = dict(spec["params"])
    if params_override:
        params.update(params_override)
    fn = f"probe_{eng}_{midi}_{int(round(vel * 100))}_{int(round(dur * 10))}{tag}"
    score = {
        "meta": {"title": fn, "id": fn},
        "global": {"bpm": 120, "sample_rate": sr, "master_volume": 1.0,
                   "effects": {"reverb": {"decay": 2, "wet": 0},
                               "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                               "distortion": {"type": "overdrive", "drive": 0,
                                              "instability": 0, "wet": 0}}},
        "events": [{"time": 0.0, "duration": dur, "engine": spec["engine"],
                    "note": str(midi), "velocity": vel,
                    "params": params}],
        "export": {"filename": fn, "format": "wav", "bit_depth": 16,
                   "normalize": False, "tail_silence_ms": 200},
    }
    sf = outdir / (fn + ".score.json")
    sf.write_text(json.dumps(score), encoding="utf-8")
    return sf, fn


def render_probe(cli, eng, midi, outdir, sr=48000, vel=0.85, dur=2.0,
                  params_override=None, tag=""):
    sf, fn = build_probe_score(eng, midi, outdir, sr, vel, dur, params_override, tag)
    r = subprocess.run([str(cli), str(sf), "--output", str(outdir)],
                       capture_output=True, text=True)
    wav = outdir / (fn + ".wav")
    if r.returncode != 0 or not wav.exists():
        raise RuntimeError(f"render failed for {fn}: {r.stdout}\n{r.stderr}")
    return wav, sf


def find_cli():
    here = Path(__file__).resolve().parent.parent
    cands = list((here / "build").rglob("TsukiSynthCLI.exe"))
    cands += list((here / "build").rglob("tsukisynth-cli*"))
    cands += list((here / "build").rglob("TsukiSynthCLI"))
    cands = [c for c in cands if c.is_file()]
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)


# ── main ────────────────────────────────────────────────────────────────────
def cents(measured, predicted):
    return 1200.0 * math.log2(measured / predicted)


def run(cli, engines, notes, outdir):
    overall_ok = True
    for eng in engines:
        spec = ENGINES[eng]
        for midi in notes:
            f0 = midi_to_hz(midi)
            ratios = spec["ratios"](spec["npart"])
            pred = [f0 * r for r in ratios]
            wav, sf = render_probe(cli, eng, midi, outdir)
            sr, x = read_wav_mono(wav)
            meas = measure_partials(sr, x, pred)
            model_t60 = model_fundamental_decay(cli, sf)   # FIX2/3: sizes measure_f0's window

            print(f"\n# {eng:11s} MIDI {midi}  (f0_expected = {f0:8.3f} Hz)"
                  f"{'  [inharmonic: high-partial stretch is expected]' if spec.get('inharmonic') else ''}")
            print(f"   {'n':>2} {'predicted':>11} {'measured':>11} {'err%':>7} {'rel_dB':>6}  note")
            fund_mag = meas[0][1] if meas[0] else 0.0
            f0_meas = measure_f0(x, sr, f0, model_t60=model_t60)
            probe_ok = True
            for i, (r, fp, m) in enumerate(zip(ratios, pred, meas), 1):
                if m is None:
                    print(f"   {i:>2} {fp:>11.3f} {'--':>11} {'--':>7} {'--':>6}  NOT FOUND")
                    if i == 1:
                        probe_ok = False
                    continue
                fmeas, mag = m
                rel_db = 20.0 * math.log10(mag / fund_mag) if (fund_mag > 0 and mag > 0) else -120.0
                if i == 1 and f0_meas:
                    fmeas = f0_meas    # centroid: robust to multi-string beating
                errp = (fmeas / fp - 1.0) * 100.0
                if i == 1:
                    c = cents(fmeas, fp)
                    ok = abs(c) <= F0_TOL_CENTS
                    tag = f"f0 {c:+.1f} cents [{'OK' if ok else 'FAIL'}]"
                    probe_ok = probe_ok and ok
                elif rel_db < -45.0:
                    tag = "weak (< -45 dB) - not assessed"
                elif spec.get("inharmonic"):
                    tag = f"stretch {errp:+.2f}%"
                else:
                    ok = abs(errp) <= spec["tol_pct"]
                    tag = f"[{'OK' if ok else 'FAIL'}]"
                    probe_ok = probe_ok and ok
                print(f"   {i:>2} {fp:>11.3f} {fmeas:>11.3f} {errp:>+7.2f} {rel_db:>+6.0f}  {tag}")
            print(f"   -> {'PASS' if probe_ok else 'FAIL'}")
            overall_ok = overall_ok and probe_ok
    return overall_ok


# ── M1-1b: multi-note range scan ────────────────────────────────────────────
def scan_engine_ranges(cli, engines, outdir, n=6):
    # Reuses run()'s exact f0+partial judgment (same tolerances, same printed
    # format) so a wide-range scan can never diverge from the 2-note default.
    print("\n" + "-" * 70)
    print(f"Note-range scan ({n} notes per engine, spanning each engine's "
          "declared valid range):")
    overall_ok = True
    for eng in engines:
        lo, hi = ENGINE_RANGES[eng]
        notes = scan_notes(lo, hi, n)
        print(f"\n### {eng}: valid range MIDI {lo}-{hi} -> probing {notes}")
        ok = run(cli, [eng], notes, outdir)
        if not ok:
            print(f"### {eng}: OUT OF TOLERANCE somewhere in {notes}. "
                  f"Do NOT widen tolerance — shrink the declared valid range "
                  f"(ENGINE_RANGES['{eng}']) or fix the model, per "
                  f"ROADMAP_PHYSICS.md §1g/§1.2.")
        overall_ok = overall_ok and ok
    return overall_ok


# ── M1-1c: material scan ────────────────────────────────────────────────────
# The 3 modal engines whose modal ratios are checked per-material. FM has no
# material param; piano/cimbalom share StringModel so cimbalom stands in for
# the string family here (roadmap 1c names "cimbalom / tongue_drum / water_gong").
MATERIAL_SCAN_ENGINES = ["cimbalom", "tongue_drum", "water_gong"]
MATERIAL_SCAN_MIDI = 60   # C4 — fixed probe note for the material sweep (1c)

# ROADMAP_PHYSICS.md §3 M1-1c: "UI 暴露的 9 種材質" (the 9 materials the UI
# exposes) — NOT all of data/materials.json (14 entries: the extra 5 —
# iron/nylon/bamboo/wood_birch/wood_oak — are in the physics DB and reachable
# from a hand-written score.json, but are not plugin AudioParameterChoice
# options). Source of truth: MaterialDB::getOrderedKeys() in
# src/physics/MaterialDB.h, duplicated here (Python can't include the C++
# header) — keep these two lists in sync if that array ever changes.
UI_MATERIAL_KEYS = ["steel", "copper", "bronze", "aluminum", "brass",
                     "wood_spruce", "wood_maple", "glass", "rubber"]


def load_material_keys(materials_path=None):
    """Returns the 9 UI-exposed material keys (§3 M1-1c), after validating
    each one actually exists in data/materials.json (catches drift between
    MaterialDB::getOrderedKeys() and the JSON data file)."""
    if materials_path is None:
        materials_path = Path(__file__).resolve().parent.parent / "data" / "materials.json"
    data = json.loads(Path(materials_path).read_text(encoding="utf-8"))
    available = data["materials"]
    missing = [k for k in UI_MATERIAL_KEYS if k not in available]
    if missing:
        raise RuntimeError(
            f"UI_MATERIAL_KEYS references materials missing from "
            f"{materials_path}: {missing}. MaterialDB::getOrderedKeys() and "
            f"materials.json have drifted apart — fix one or the other.")
    return list(UI_MATERIAL_KEYS)


def scan_materials(cli, outdir, engines=None, materials_path=None):
    # engines: restrict to this subset of MATERIAL_SCAN_ENGINES (honors --engines
    # filtering, same as scan_engine_ranges/judge_velocity); default = all 3.
    scan_engines = [e for e in MATERIAL_SCAN_ENGINES if engines is None or e in engines]
    materials = load_material_keys(materials_path)
    print("\n" + "-" * 70)
    print(f"Material scan (MIDI {MATERIAL_SCAN_MIDI}, f0 + partials, "
          f"{len(materials)} materials x {len(scan_engines)} modal engines):")
    overall_ok = True
    midi = MATERIAL_SCAN_MIDI
    f0 = midi_to_hz(midi)
    for eng in scan_engines:
        spec = ENGINES[eng]
        ratios = spec["ratios"](spec["npart"])
        pred = [f0 * r for r in ratios]
        for mat in materials:
            wav, sf = render_probe(cli, eng, midi, outdir,
                                   params_override={"material": mat},
                                   tag=f"_mat_{mat}")
            sr, x = read_wav_mono(wav)
            meas = measure_partials(sr, x, pred)
            model_t60 = model_fundamental_decay(cli, sf)   # FIX2: rubber's ~20ms T60
            f0_meas = measure_f0(x, sr, f0, model_t60=model_t60)

            probe_ok = True
            m0 = meas[0]
            fmeas0 = f0_meas if f0_meas else (m0[0] if m0 else None)
            if fmeas0 is None:
                print(f"   {eng:11} material={mat:12} f0 NOT FOUND  expected={f0:.3f} Hz -> FAIL")
                probe_ok = False
            else:
                c = cents(fmeas0, f0)
                ok = abs(c) <= F0_TOL_CENTS
                probe_ok = probe_ok and ok
                status = "OK" if ok else "FAIL"
                print(f"   {eng:11} material={mat:12} f0 measured={fmeas0:9.3f} Hz "
                      f"expected={f0:9.3f} Hz  {c:+6.1f} cents (tol {F0_TOL_CENTS}) [{status}]")

            fund_mag = m0[1] if m0 else 0.0
            for i, (fp, m) in enumerate(zip(pred, meas), 1):
                if i == 1 or m is None:
                    continue
                fmeas, mag = m
                rel_db = 20.0 * math.log10(mag / fund_mag) if (fund_mag > 0 and mag > 0) else -120.0
                if rel_db < -45.0:
                    continue   # weak partial - not assessed (same rule as run())
                errp = (fmeas / fp - 1.0) * 100.0
                if spec.get("inharmonic"):
                    continue   # inharmonic stretch is reported, not judged (same rule as run())
                ok = abs(errp) <= spec["tol_pct"]
                if not ok:
                    print(f"      partial {i}: measured={fmeas:.3f} Hz expected={fp:.3f} Hz "
                          f"err={errp:+.2f}% (tol +/-{spec['tol_pct']}%) -> FAIL")
                probe_ok = probe_ok and ok

            if not probe_ok:
                print(f"      -> {eng}/{mat} FAILED. Do NOT widen tolerance — "
                      f"record this material as unsupported for {eng} or fix the model, "
                      f"per ROADMAP_PHYSICS.md §1g.")
            overall_ok = overall_ok and probe_ok
    return overall_ok


# ── M1-1d: velocity linearity judgment ──────────────────────────────────────
# velocity x2 -> +6.0 +/- 1.0 dB RMS is the amplitude-proportional-to-force
# physical law (registered in ROADMAP_PHYSICS.md §6: "velocity x2 電平").
# 48/96 (MIDI-velocity-style units, out of 127) give an exact x2 ratio.
VELOCITY_LO = 48 / 127.0
VELOCITY_HI = 96 / 127.0
VELOCITY_DB_TARGET = 6.0    # physical law: amplitude ~ force -> +6 dB per doubling
VELOCITY_DB_TOL = 1.0       # +/-1.0 dB judgment window (ROADMAP_PHYSICS.md §6)
VELOCITY_EXEMPT_ENGINES = {"fm"}   # FM index also rises with velocity -> not a pure amplitude law


def judge_velocity(cli, engines, notes, outdir):
    # Converts the --levels display (report_levels) into a PASS/FAIL/EXEMPT
    # judgment per ROADMAP_PHYSICS.md M1-1d, without touching --levels itself.
    print("\n" + "-" * 70)
    print(f"Velocity linearity judgment (vel {VELOCITY_LO:.3f} -> {VELOCITY_HI:.3f}, "
          f"expect +{VELOCITY_DB_TARGET:.1f} +/-{VELOCITY_DB_TOL:.1f} dB RMS):")
    print(f"   {'engine':11} {'MIDI':>4} {'rms_lo':>8} {'rms_hi':>8} {'delta_dB':>9}  verdict")
    overall_ok = True
    for eng in engines:
        exempt = eng in VELOCITY_EXEMPT_ENGINES
        for midi in notes:
            lo, _ = render_probe(cli, eng, midi, outdir, vel=VELOCITY_LO)
            hi, _ = render_probe(cli, eng, midi, outdir, vel=VELOCITY_HI)
            _, rlo = measure_levels(*read_wav_mono(lo))
            _, rhi = measure_levels(*read_wav_mono(hi))
            delta = rhi - rlo
            if exempt:
                verdict = "EXEMPT (FM index also scales with velocity)"
            else:
                ok = abs(delta - VELOCITY_DB_TARGET) <= VELOCITY_DB_TOL
                verdict = "PASS" if ok else "FAIL"
                if not ok:
                    print(f"      measured delta={delta:+.2f} dB, expected "
                          f"{VELOCITY_DB_TARGET:+.1f} +/-{VELOCITY_DB_TOL:.1f} dB "
                          f"-> FAIL. Do NOT widen tolerance; record and investigate "
                          f"the engine's velocity->amplitude law per ROADMAP_PHYSICS.md §1g.")
                overall_ok = overall_ok and ok
            print(f"   {eng:11} {midi:>4} {rlo:>8.1f} {rhi:>8.1f} {delta:>+9.1f}  {verdict}")
    return overall_ok


# ── M2-2d: partial-amplitude judgment ───────────────────────────────────────
# ROADMAP_PHYSICS.md §6: "Partial 振幅誤差 | 無（未驗證） | ±3.0 dB（M2）" — the
# theoretical prediction is built ENTIRELY from the model's own --dump-modes
# output (freq/amp/decay per mode, per active string/voice, plus each mode's
# body_mag = the exact |dry+BodyResonance(dry)| transfer magnitude read from
# the model's own live BiquadFilter/BodyResonance state — see
# BodyResonance::magnitudeAt() / BiquadFilter::responseAt() in
# src/dsp/BodyResonance.h / src/dsp/BiquadFilter.h). NONE of this is a
# re-derivation calibrated from rendered audio (that would be circular per
# ROADMAP_PHYSICS.md M2 "不算完成": "振幅預測值是反過來從渲染結果抄的") — it is
# a windowed-synthesis of the model's own documented linear signal chain
# (modal decay + multi-string beating + the body-resonance filter's transfer
# function), run through the IDENTICAL measurement pipeline
# (measure_partials()) used on the real CLI-rendered WAV. See
# reports/gate_outputs/amps_rootcause_analysis.md for the root-cause
# investigation this closes: --dump-modes used to report the raw pre-mix
# ModalResonator amplitude (string 0 only, no BodyResonance), which is not
# what getNextSample() actually renders.
AMPS_SCAN_ENGINES = ["cimbalom", "tongue_drum", "water_gong", "water_gong_free", "piano"]
AMPS_NPART = 5              # "first 5 partials" per ROADMAP_PHYSICS.md M2-2d
AMPS_DB_TOL = 3.0           # ±3.0 dB, registered in §6 — AI must NOT change this
AMPS_WEAK_DB = -45.0        # same "not assessed" floor as run()/scan_materials()
AMPS_PROBE_SR = 48000       # must match render_probe()'s default sr= (judge_amps
AMPS_PROBE_DUR = 2.0        # and dur=) so the theory synthesis and the real render
                             # are windowed/measured over an identical duration.


def dump_modes_partials(cli, score_path):
    """Runs --dump-modes on a single-event probe score and returns that
    event's partials list (each {"freq", "amp", "decay", "body_mag"},
    ascending frequency, string 0 only -- see ScoreRenderer::dumpModes).
    Mirrors model_fundamental_decay()'s subprocess pattern; returns None on
    any failure so callers can report NOT FOUND instead of crashing the whole
    scan. Kept for any external/legacy caller; judge_amps() below uses
    dump_modes_event() to also get the multi-string "strings" array."""
    event = dump_modes_event(cli, score_path)
    return event["partials"] if event else None


def dump_modes_event(cli, score_path):
    """Runs --dump-modes and returns the full first-event dict: "partials"
    (string 0's modes, kept for back-compat) plus "strings" (every active
    string's/voice's modes, each already detuned/gain-scaled exactly as the
    C++ model's noteOn() computed them -- see CimbalomVoice::
    getAllStringModes() / ChromaticVoice::getModes()). Every mode also carries
    "body_mag". Returns None on any failure."""
    r = subprocess.run([str(cli), "--dump-modes", str(score_path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        events = json.loads(r.stdout)["events"]
        return events[0] if events else None
    except Exception:
        return None



# ln(1000) = 6.907755278982137. ModalResonator::excite() (src/dsp/
# ModalResonator.h) defines and hard-codes the --dump-modes "decay" field
# (Mode::decayTime) as a T60 -- time to fall to -60dB (~0.001x), not a 1/e
# time constant tau: `decayCoeff = exp(-6.9078f / (decayTime * sampleRate))`
# applied once per sample (see also the shortened-decay branch a few lines
# below it, same -6.9078f literal). The model's own closed-form envelope is
# therefore amp(t) = amp0 * exp(-ln(1000) * t / decayTime), not
# amp0 * exp(-t / decayTime). This constant is read verbatim off the C++
# source's own literal/comment, never fitted to rendered audio (no-circularity
# rule, ROADMAP_PHYSICS.md Sec.1).
MODAL_DECAY_LN1000 = 6.907755278982137


def synth_theory_signal(strings, sr, duration):
    """THEORY-ONLY windowed synthesis (no rendered-audio input, per the
    no-circularity rule above): sums every active string's/voice's modal
    partials as decaying sinusoids
        x(t) = sum_s sum_i  amp_i,s * body_mag_i,s * exp(-ln(1000)*t/decay_i,s)
                             * sin(2*pi*freq_i,s*t)
    The exp(-ln(1000)*t/decay) envelope matches ModalResonator::excite()'s own
    T60 definition of `decay` verbatim (see MODAL_DECAY_LN1000 above) --
    `decay` is time-to-(-60dB), not a 1/e time constant.
    `body_mag` folds in the model's own BodyResonance transfer magnitude at
    that mode's frequency (steady-state/quasi-static approximation -- valid
    because the body filter's own settling time, a few ms for its Q=1.4-1.8
    resonances, is short next to the decay times of every partial this gate
    judges; see BodyResonance::totalResponse()'s doc-comment). Summing
    multiple strings' slightly-detuned copies reproduces the real multi-string
    beating pattern using the model's own per-string frequency/gain math
    (CimbalomVoice::noteOn), not a Python re-derivation of the detuning
    formula. All modes (not just the first AMPS_NPART) are included since
    higher partials still land inside neighbouring partials' +/-6% search
    windows used by measure_partials()."""
    n = int(round(duration * sr))
    t = np.arange(n) / sr
    x = np.zeros(n)
    for voice_modes in strings:
        for m in voice_modes:
            amp = m["amp"] * m.get("body_mag", 1.0)
            decay = m["decay"] if m["decay"] > 1e-9 else 1.0e9
            x += amp * np.exp(-MODAL_DECAY_LN1000 * t / decay) * np.sin(2.0 * np.pi * m["freq"] * t)
    return x


def judge_amps(cli, engine, midi_note, outdir):
    """M2-2d: renders one probe, compares the first AMPS_NPART partials'
    measured relative amplitude (dB re fundamental) against a THEORY-ONLY
    windowed-synthesis prediction (see synth_theory_signal()) built from
    --dump-modes' full multi-string mode list + body_mag, run through the
    same measure_partials() pipeline used on the real render. Partial 1 (the
    fundamental) is the 0 dB reference for both sides by construction and is
    not itself judged; partials 2..AMPS_NPART are judged within
    +/-AMPS_DB_TOL dB. Returns (probe_ok, rows) where rows is a list of
    per-partial dicts for the caller to print/tally."""
    # tag="_amps": run_full() shares one outdir across scan_engine_ranges()
    # and scan_amps(), and both probe MIDI 60 with the harness's default
    # vel/dur -- without a distinguishing tag their probe filenames collide
    # (CLI refuses to overwrite an existing render), so scan_amps' probe
    # needs its own filename even though it renders identical parameters.
    wav, sf = render_probe(cli, engine, midi_note, outdir, tag="_amps",
                            sr=AMPS_PROBE_SR, dur=AMPS_PROBE_DUR)
    event = dump_modes_event(cli, sf)
    rows = []
    if not event or not event.get("partials"):
        return False, rows
    partials = event["partials"][:AMPS_NPART]
    pred_freqs = [p["freq"] for p in partials]

    # Theory-only prediction: windowed-synthesis of the FULL multi-string
    # mode list (not just the first AMPS_NPART partials of string 0 -- see
    # synth_theory_signal()'s docstring), measured with the identical
    # measure_partials() pipeline used on the real render below. Zero
    # rendered-audio input anywhere in this block.
    strings = event.get("strings") or [event["partials"]]
    synth = synth_theory_signal(strings, AMPS_PROBE_SR, AMPS_PROBE_DUR)
    synth_meas = measure_partials(AMPS_PROBE_SR, synth, pred_freqs)
    synth_fund_mag = synth_meas[0][1] if synth_meas[0] else 0.0

    sr, x = read_wav_mono(wav)
    meas = measure_partials(sr, x, pred_freqs)
    fund_mag = meas[0][1] if meas[0] else 0.0
    model_t60 = event["partials"][0]["decay"] if event["partials"] else None  # FIX2/3: reuse the
                                                                                # already-fetched --dump-modes event
    f0_meas = measure_f0(x, sr, pred_freqs[0], model_t60=model_t60)

    probe_ok = True
    for i, (p, m) in enumerate(zip(partials, meas), 1):
        sm = synth_meas[i - 1]
        pred_db = (20.0 * math.log10(sm[1] / synth_fund_mag)
                   if (synth_fund_mag > 0 and sm and sm[1] > 0) else -120.0)
        if m is None:
            rows.append(dict(n=i, freq=p["freq"], pred_db=pred_db,
                              meas_db=None, err_db=None, verdict="NOT FOUND"))
            if i == 1:
                probe_ok = False   # fundamental must be found (same as run())
            continue
        fmeas, mag = m
        if i == 1 and f0_meas:
            fmeas = f0_meas   # centroid: robust to multi-string beating (same as run())
        meas_db = 20.0 * math.log10(mag / fund_mag) if (fund_mag > 0 and mag > 0) else -120.0
        if i == 1:
            rows.append(dict(n=i, freq=fmeas, pred_db=0.0, meas_db=0.0,
                              err_db=0.0, verdict="ref (0 dB)"))
            continue
        if meas_db < AMPS_WEAK_DB:
            rows.append(dict(n=i, freq=fmeas, pred_db=pred_db, meas_db=meas_db,
                              err_db=None, verdict="weak (< -45 dB) - not assessed"))
            continue
        err_db = meas_db - pred_db
        ok = abs(err_db) <= AMPS_DB_TOL
        probe_ok = probe_ok and ok
        rows.append(dict(n=i, freq=fmeas, pred_db=pred_db, meas_db=meas_db,
                          err_db=err_db, verdict="PASS" if ok else "FAIL"))
    return probe_ok, rows


def scan_amps(cli, outdir, engines=None, midi_note=60):
    """M2-2d: runs judge_amps() for every modal engine (FM excluded -- non-
    physical synthesis, per module docstring / ROADMAP_PHYSICS.md §0) at
    MIDI 60 (middle C), printing the same per-partial table style as run()."""
    scan_engines = [e for e in AMPS_SCAN_ENGINES if engines is None or e in engines]
    print("\n" + "-" * 70)
    print(f"Partial-amplitude judgment (MIDI {midi_note}, first {AMPS_NPART} partials, "
          f"rel-dB vs --dump-modes theory, tol +/-{AMPS_DB_TOL} dB):")
    overall_ok = True
    for eng in scan_engines:
        probe_ok, rows = judge_amps(cli, eng, midi_note, outdir)
        f0 = midi_to_hz(midi_note)
        print(f"\n# {eng:11s} MIDI {midi_note}  (f0_expected = {f0:8.3f} Hz)")
        print(f"   {'n':>2} {'freq':>11} {'pred_dB':>8} {'meas_dB':>8} {'err_dB':>7}  verdict")
        if not rows:
            print("   -- NOT FOUND (--dump-modes returned no partials) -> FAIL")
            probe_ok = False
        for r in rows:
            meas_s = f"{r['meas_db']:>+8.2f}" if r['meas_db'] is not None else f"{'--':>8}"
            err_s = f"{r['err_db']:>+7.2f}" if r['err_db'] is not None else f"{'--':>7}"
            print(f"   {r['n']:>2} {r['freq']:>11.3f} {r['pred_db']:>+8.2f} {meas_s} {err_s}  {r['verdict']}")
        if not probe_ok:
            print(f"   -> {eng} FAILED. Do NOT widen the +/-{AMPS_DB_TOL} dB tolerance "
                  f"(ROADMAP_PHYSICS.md §6) — investigate the impulse-excitation model "
                  f"or record the discrepancy per §1g.")
        print(f"   -> {'PASS' if probe_ok else 'FAIL'}")
        overall_ok = overall_ok and probe_ok
    return overall_ok


# ── M1-1e: --full mode ──────────────────────────────────────────────────────
def run_full(cli, engines, outdir, skip_amps=False):
    """Runs the complete M1 verification breadth: multi-note range scan (1b)
    for every engine, material scan (1c) for the 3 modal engines, and the
    velocity-linearity judgment (1d) for every engine. Also runs the M2-2d
    partial-amplitude judgment for every modal engine, so --full covers M1+M2.
    Exit-code-affecting; every sub-check must pass for --full to report
    success.

    skip_amps=True restricts --full to its M1 scope (1b+1c+1d), for CI while
    M2-2d remediation is still in progress. This is NOT a tolerance change and
    NOT a silent gate-shrink: the M2 GATE (--amps) is unaffected and still
    FAILs honestly, CI runs a separate always-visible non-blocking --amps step,
    and M2 stays "In progress" in ROADMAP_PHYSICS.md until 2d passes for real.
    Scope decision approved by 月月 2026-07-09 (delegated via Fable) — see
    TODO.md CI-coupling entry."""
    print("=" * 70)
    print("--full: M1 verification breadth (range scan + material scan + velocity)"
          + (" [--skip-amps: M1 scope only, M2-2d amplitude judgment NOT run]"
             if skip_amps else " + M2 amplitude judgment"))
    print("=" * 70)

    range_ok = scan_engine_ranges(cli, engines, outdir, n=6)

    material_engines = [e for e in engines if e in MATERIAL_SCAN_ENGINES]
    material_ok = True
    if material_engines:
        material_ok = scan_materials(cli, outdir, engines=material_engines)
    else:
        print("\n(material scan skipped: none of the requested --engines are "
              f"in {MATERIAL_SCAN_ENGINES})")

    # Velocity judgment uses one representative note per engine (MIDI 60, or
    # the engine's declared range midpoint if 60 falls outside it) — the
    # physical law being checked (amplitude ~ velocity) is note-independent.
    vel_notes = []
    for eng in engines:
        lo, hi = ENGINE_RANGES[eng]
        vel_notes.append(60 if lo <= 60 <= hi else (lo + hi) // 2)
    # judge_velocity takes one shared note list; since engines may need
    # different representative notes, run it once per engine with its own note.
    velocity_ok = True
    for eng, midi in zip(engines, vel_notes):
        velocity_ok = judge_velocity(cli, [eng], [midi], outdir) and velocity_ok

    amps_engines = [] if skip_amps else [e for e in engines if e in AMPS_SCAN_ENGINES]
    amps_ok = True
    if amps_engines:
        amps_ok = scan_amps(cli, outdir, engines=amps_engines)
    elif skip_amps:
        print("\n(amplitude judgment SKIPPED by --skip-amps: M1-scope run; the M2 "
              "GATE `--amps` is unaffected and must still pass separately)")
    else:
        print("\n(amplitude judgment skipped: none of the requested --engines are "
              f"in {AMPS_SCAN_ENGINES})")

    print("\n" + "=" * 70)
    print("--full summary:")
    print(f"   1b note-range scan   : {'PASS' if range_ok else 'FAIL'}")
    print(f"   1c material scan     : {'PASS' if material_ok else 'FAIL'}")
    print(f"   1d velocity judgment : {'PASS' if velocity_ok else 'FAIL'}")
    print(f"   2d amplitude judgment: "
          f"{'SKIPPED (--skip-amps)' if skip_amps else ('PASS' if amps_ok else 'FAIL')}")

    return range_ok and material_ok and velocity_ok and amps_ok


def measure_levels(sr, x):
    seg = x[:int(1.5 * sr)] if len(x) > int(1.5 * sr) else x
    if len(seg) == 0:
        return (-120.0, -120.0)
    to_db = lambda v: 20.0 * math.log10(v) if v > 1e-9 else -120.0
    peak = float(np.max(np.abs(seg)))
    rms = float(np.sqrt(np.mean(seg * seg)))
    return (to_db(peak), to_db(rms))


def report_levels(cli, engines, notes, outdir):
    # Quantifies the ad-hoc per-engine output gains (cimbalom x0.15 /
    # chromatic x0.2 / fm x1.0) ear-free, and checks the physical law
    # amplitude is proportional to velocity (doubling velocity ~ +6 dB RMS).
    print("Per-engine output level @ matched note (vel 0.85):")
    print(f"   {'engine':11} {'MIDI':>4} {'peak dBFS':>10} {'rms dBFS':>9} "
          f"{'velx2->dB':>10}")
    for eng in engines:
        for midi in notes:
            lo, _ = render_probe(cli, eng, midi, outdir, vel=0.425)
            hi, _ = render_probe(cli, eng, midi, outdir, vel=0.85)
            _, rlo = measure_levels(*read_wav_mono(lo))
            phi, rhi = measure_levels(*read_wav_mono(hi))
            print(f"   {eng:11} {midi:>4} {phi:>10.1f} {rhi:>9.1f} "
                  f"{rhi - rlo:>+9.1f}")
    print("\n(+6 dB = amplitude scales linearly with velocity = physical;")
    print(" FM expected >+6 dB because higher velocity also raises FM index.)")
    return True


def model_fundamental_decay(cli, score_path):
    # Ground-truth decay from the C++ model itself (--dump-modes), avoiding any
    # Python re-derivation drift (the model's decayTime uses the natural,
    # pre-MIDI-tuning frequency, which a formula on the tuned f0 would get wrong).
    r = subprocess.run([str(cli), "--dump-modes", str(score_path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)["events"][0]["partials"][0]["decay"]
    except Exception:
        return None


# ── M5-5a: T60 measurement rework ───────────────────────────────────────────
T60_NOTEOFF_RATIO = 0.9       # mirrors ScoreRenderer's own
                              # `start + duration*sr*0.9` note-off formula
                              # (renderCimbalom/renderChromatic, both engines) —
                              # read off the C++ source, not re-derived.
T60_NOTEOFF_MARGIN_S = 0.3    # stay this far before note-off's accelerated
                              # damping (CimbalomVoice::noteOff -> applyDamp())
T60_ATTACK_SKIP_S = 0.1       # 5a: "skip first 100 ms" (attack transient)
T60_FLOOR_MARGIN_DB = 10.0    # 5a: stop at noise-floor + 10 dB
T60_BAND_HALF_WIDTH = 0.03    # 5a: narrow +/-3% band around the MEASURED f0
                              # (not the nominal MIDI f0 -- avoids band-edge
                              # attenuation from any small tuning offset)

# ── FIX1 (Phase I, 2026-07-13): adaptive T60 probe duration ─────────────────
# Root cause (reports/phase_h_before_after.md §3): materials physicalization
# pushed steel's model T60 to 26.85s at MIDI60, but the probe was a hard-coded
# 5.0s -- note-off happened before even 1/5 of a real decay period elapsed,
# and (for cimbalom/piano) the beat-averaging box-car saw so little decay
# inside that short window that the beat ripple itself dominated the fitted
# slope (measured 7.61s, a fake number 28% of the true model T60).
# Fix: read the MODEL's own predicted T60 via --dump-modes BEFORE rendering
# the timed probe (model_t60_preflight() below), then size the render/fit
# window off THAT prediction. This is sizing an instrument (the probe
# duration) to the known scale of the phenomenon being measured -- standard
# metrology (an oscilloscope's timebase is set from the signal's own period),
# not circularity: the JUDGMENT (measured slope vs model T60,
# T60_RATIO_TOLERANCE, unchanged) still independently re-derives T60 from the
# rendered audio and compares it to the model -- the model's prediction is
# never fed into the pass/fail arithmetic, only into how long to look.
T60_PROBE_DUR_MIN = 5.0        # unchanged floor (M5-5a's original constant)
T60_PROBE_DUR_MAX = 30.0       # task-specified cap
T60_PROBE_DUR_SCALE = 0.5      # probe = half the model's own predicted T60
T60_MIN_SPAN_DB = 8.0          # task-specified: fit needs >= 8 dB of clean decay
T60_BEAT_PERIODS_MIN = 3.0     # (carried forward from Phase G) the fit window
                                # must contain >= 3 full beat periods for the
                                # box-car average (step 3 below) to flatten the
                                # ripple rather than let one period's phase
                                # alias into the fitted slope.


def model_t60_preflight(cli, eng, midi, outdir, params_override=None):
    """FIX1: writes a throwaway probe score (score-only, no audio render --
    see build_probe_score()) and reads the model's predicted fundamental T60
    via --dump-modes. decayTime is a material/frequency-derived model
    constant; it does not depend on the note's requested duration, so a cheap
    short-duration throwaway score is enough to learn it before deciding how
    long the REAL timed probe needs to be. Also returns the beat frequency
    (0.0 for single-voice engines) for the T60_BEAT_PERIODS_MIN check."""
    sf, _ = build_probe_score(eng, midi, outdir, dur=0.05,
                               params_override=params_override, tag="_t60pf")
    model_t60 = model_fundamental_decay(cli, sf)
    event = dump_modes_event(cli, sf)
    beat_freq = fundamental_beat_freq_hz(event) if event else 0.0
    return model_t60, beat_freq


def adaptive_t60_probe_dur(model_t60, beat_freq_hz=0.0):
    """FIX1: duration = clamp(0.5 * model_T60, 5s, 30s), further raised (still
    capped at 30s) if needed so the fit window can contain
    T60_BEAT_PERIODS_MIN full beat periods (only relevant for cimbalom/piano's
    detuned multi-string course)."""
    if model_t60 and model_t60 > 0:
        dur = _clamp(T60_PROBE_DUR_SCALE * model_t60,
                     T60_PROBE_DUR_MIN, T60_PROBE_DUR_MAX)
    else:
        dur = T60_PROBE_DUR_MIN
    if beat_freq_hz and beat_freq_hz > 1e-6:
        # fit window (after attack-skip, before note-off margin) must span
        # >= T60_BEAT_PERIODS_MIN beat periods; solve for the note "duration"
        # that gives that much room before the T60_NOTEOFF_RATIO note-off.
        needed_fit_span = T60_BEAT_PERIODS_MIN / beat_freq_hz
        needed_dur = (T60_ATTACK_SKIP_S + needed_fit_span + T60_NOTEOFF_MARGIN_S) / T60_NOTEOFF_RATIO
        dur = max(dur, min(needed_dur, T60_PROBE_DUR_MAX))
    return dur


def fundamental_beat_freq_hz(event):
    """5a multi-string-beating handling: returns the beat frequency (Hz) of
    the struck course's fundamental, i.e. the spread between the slowest and
    fastest detuned string, taken from the model's OWN --dump-modes "strings"
    list (CimbalomVoice::getAllStringModes() -- non-circular, ground truth,
    same source model_fundamental_decay() already trusts). 0.0 for engines
    that render a single voice (ChromaticVoice: tongue_drum/water_gong/
    water_gong_free) -- no beating, no averaging needed. Cimbalom AND piano
    both go through renderCimbalom() with the same default numStrings=3 /
    detuningCents=5 course, so both need this."""
    strings = event.get("strings") or []
    fund = [voice[0]["freq"] for voice in strings if voice]
    if len(fund) < 2:
        return 0.0
    return max(fund) - min(fund)


def measure_t60(sr, x, f0_meas, beat_freq_hz, noteoff_time_s):
    """5a rework. Method:
      1. Isolate the fundamental with a NARROW +/-3% zero-phase 4th-order
         Butterworth bandpass (sosfiltfilt) around the MEASURED f0 (centroid
         from measure_f0(), not the nominal MIDI pitch) -- wide enough to pass
         the whole detuned string course, narrow enough to reject every other
         partial.
      2. Analytic-magnitude (Hilbert) envelope of that narrowband signal.
      3. Multi-string beating: if beat_freq_hz > 0 (cimbalom/piano course),
         box-car average the envelope over a window >= one full beat period
         (period = 1/beat_freq_hz, +5% margin for discretization) BEFORE
         fitting, per the task spec -- this turns the beating envelope's
         ripple into its slowly-varying mean without touching the underlying
         exponential decay-rate. Single-voice engines (beat_freq_hz == 0) skip
         this step untouched.
      4. Fit ln-envelope (in dB) vs time with a LINEAR regression (least
         squares, np.polyfit) over the window that:
           - starts T60_ATTACK_SKIP_S (100 ms) after the envelope peak (skips
             the attack transient),
           - ends at the EARLIEST of: (a) T60_NOTEOFF_MARGIN_S before the
             note-off instant (CimbalomVoice::noteOff()/ChromaticVoice's own
             note-off both trigger accelerated release damping -- must not be
             included in a free-decay slope fit), (b) the -60 dB point
             (relative to the peak), (c) noise-floor + 10 dB (noise floor
             measured from the tail of the ACTUAL rendered buffer, i.e. past
             the event's own note-off + release, where the CLI has already
             hard-truncated the buffer to silence -- see ScoreRenderer::render()
             totalDuration/tailSilenceMs).
      5. T60 = 60 dB / |slope in dB/s| (extrapolated from whatever window was
         actually fittable -- same convention as the model's own T60 field).
    Returns (t60_or_None, span_db_or_None). span_db is the dB of decay
    actually captured inside the fit window (FIX1: the achievable-span guard
    -- report_t60() asserts this is >= T60_MIN_SPAN_DB, extending the probe
    toward the 30s cap and retrying if not). Both None if there isn't a
    usable window (e.g. probe too short, envelope never establishes a
    fittable decay, or engine is silent)."""
    try:
        from scipy.signal import butter, sosfiltfilt, hilbert
    except Exception:
        return None, None
    nyq = sr / 2.0
    lo = f0_meas * (1.0 - T60_BAND_HALF_WIDTH) / nyq
    hi = f0_meas * (1.0 + T60_BAND_HALF_WIDTH) / nyq
    if not (0.0 < lo < hi < 1.0):
        return None, None
    band = sosfiltfilt(butter(4, [lo, hi], btype="band", output="sos"), x)
    env = np.abs(hilbert(band))

    if beat_freq_hz and beat_freq_hz > 1e-6:
        period_samples = sr / beat_freq_hz
        win = max(1, int(math.ceil(period_samples * 1.05)))   # >= 1 full period
        kernel = np.ones(win) / win
        env = np.convolve(env, kernel, mode="same")

    peak_idx = int(np.argmax(env))
    peak_val = float(env[peak_idx])
    if peak_val <= 1e-12:
        return None, None

    # Noise floor: tail of the ACTUAL rendered buffer (past note-off+release,
    # into the CLI's hard-truncated/tail-silence region), referenced to the
    # same narrowband envelope peak used for the fit.
    noise_tail = x[-int(0.1 * sr):] if len(x) > int(0.1 * sr) else x
    noise_rms = float(np.sqrt(np.mean(noise_tail * noise_tail))) if len(noise_tail) else 0.0
    floor_db = (20.0 * math.log10(max(noise_rms, 1e-12) / peak_val)) + T60_FLOOR_MARGIN_DB

    seg = env[peak_idx:]
    n = len(seg)
    t = np.arange(n) / sr
    logenv = 20.0 * np.log10(np.maximum(seg, 1e-12) / peak_val)

    start_t = T60_ATTACK_SKIP_S
    end_candidates = [max(start_t, noteoff_time_s - T60_NOTEOFF_MARGIN_S)]
    below60 = np.nonzero(logenv <= -60.0)[0]
    if below60.size:
        end_candidates.append(float(t[below60[0]]))
    if floor_db < 0.0:   # only meaningful if the floor is actually below the peak
        below_floor = np.nonzero(logenv <= floor_db)[0]
        if below_floor.size:
            end_candidates.append(float(t[below_floor[0]]))
    end_t = min(end_candidates)

    mask = (t >= start_t) & (t <= end_t)
    if mask.sum() < 20 or (end_t - start_t) < 0.05:
        return None, None
    idx = np.nonzero(mask)[0]
    span_db = float(logenv[idx[0]] - logenv[idx[-1]])   # dB of decay actually captured
    slope = np.polyfit(t[mask], logenv[mask], 1)[0]   # dB/s (negative)
    t60 = (-60.0 / slope) if slope < -1e-3 else None
    return t60, span_db


def _probe_and_measure_t60(cli, eng, midi, outdir, f0, probe_dur, tag=""):
    """One render + T60 measurement attempt at a given probe duration.
    Returns (pred_t60, meas_t60, span_db, beat_freq)."""
    wav, sf = render_probe(cli, eng, midi, outdir, dur=probe_dur, tag=tag)
    sr, x = read_wav_mono(wav)
    pred = model_fundamental_decay(cli, sf)
    event = dump_modes_event(cli, sf)
    beat_freq = fundamental_beat_freq_hz(event) if event else 0.0
    model_t60_for_f0 = pred   # same model prediction FIX2/3 wants for measure_f0's window
    f0_meas_center = measure_f0(x, sr, f0, model_t60=model_t60_for_f0) or f0
    noteoff_time = probe_dur * T60_NOTEOFF_RATIO
    meas, span_db = measure_t60(sr, x, f0_meas_center, beat_freq, noteoff_time)
    return pred, meas, span_db, beat_freq


def report_t60(cli, engines, notes, outdir):
    print("Modal decay T60 - measured (audio) vs model ground truth (--dump-modes):")
    print(f"   {'engine':11} {'MIDI':>4} {'model':>8} {'meas':>8} {'ratio':>6}")
    all_ok = True
    for eng in engines:
        if eng == "fm":
            continue   # FM decay is ADSR, not modal damping
        for midi in notes:
            f0 = midi_to_hz(midi)
            # FIX1: pre-flight the model's own T60 (and beat frequency)
            # BEFORE rendering the timed probe, so probe length derives from
            # the model's own prediction rather than a fixed constant.
            model_t60_pf, beat_freq_pf = model_t60_preflight(cli, eng, midi, outdir)
            probe_dur = adaptive_t60_probe_dur(model_t60_pf, beat_freq_pf)

            pred, meas, span_db, beat_freq = _probe_and_measure_t60(
                cli, eng, midi, outdir, f0, probe_dur)

            # FIX1 achievable-span guard: fitting needs a clean >= 8 dB span.
            # If the first attempt didn't get one (e.g. the pre-flight
            # estimate came in short, or note-off truncated the window),
            # extend straight to the 30s cap and retry once.
            if (span_db is None or span_db < T60_MIN_SPAN_DB) and probe_dur < T60_PROBE_DUR_MAX:
                probe_dur = T60_PROBE_DUR_MAX
                pred, meas, span_db, beat_freq = _probe_and_measure_t60(
                    cli, eng, midi, outdir, f0, probe_dur, tag="_ext")

            ps = f"{pred:7.2f}s" if pred else "   --  "
            ms = f"{meas:7.2f}s" if meas else "   --  "
            if pred and meas:
                ratio = meas / pred
                rs = f"{ratio:5.2f}"
                lo, hi = T60_RATIO_TOLERANCE
                if ratio < lo or ratio > hi:
                    rs += " << FAIL"
                    all_ok = False
            else:
                rs = "  --  "
                all_ok = False
            span_note = f"  (span {span_db:.1f}dB" if span_db is not None else "  (span --"
            span_note += f", probe {probe_dur:.1f}s)"
            print(f"   {eng:11} {midi:>4} {ps:>8} {ms:>8} {rs:>6}"
                  f"{'  (beat ' + format(beat_freq, '.2f') + ' Hz)' if beat_freq > 1e-6 else ''}"
                  f"{span_note}")
    print("\n(model = fundamental decayTime straight from the C++ model;")
    print(" measured = narrowband (+/-3% of measured f0) Hilbert-envelope")
    print(" log-slope fit, beat-period-averaged for multi-string courses;")
    print(" see measure_t60()'s docstring for the exact method, "
          "ROADMAP_PHYSICS.md M5-5a.)")
    return all_ok


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Verify rendered audio vs physics model.")
    ap.add_argument("--cli", default=None, help="path to TsukiSynthCLI executable")
    ap.add_argument("--engines", nargs="+", default=list(ENGINES.keys()),
                    choices=list(ENGINES.keys()))
    ap.add_argument("--notes", nargs="+", type=int, default=[60, 69],
                    help="MIDI notes (default C4 A4)")
    ap.add_argument("--keep", action="store_true", help="keep temp renders")
    ap.add_argument("--levels", action="store_true",
                    help="report per-engine output levels instead of partials")
    ap.add_argument("--t60", action="store_true",
                    help="M5: judge modal decay T60 (measured/model ratio) vs "
                         "the damping model, all modal engines (FM excluded); "
                         "tol 0.5-2.0 (ROADMAP_PHYSICS.md §6, M5-5b)")
    ap.add_argument("--amps", action="store_true",
                    help="M2-2d: judge first-5-partial relative amplitude (dB "
                         "re fundamental) vs --dump-modes theory, all modal "
                         "engines (FM excluded) at MIDI 60; tol +/-3.0 dB "
                         "(ROADMAP_PHYSICS.md §6)")
    ap.add_argument("--full", action="store_true",
                    help="M1 verification breadth: note-range scan (all engines) "
                         "+ material scan (modal engines) + velocity judgment "
                         "(all engines) + M2-2d amplitude judgment (modal "
                         "engines); exit 0 only if every sub-check passes")
    ap.add_argument("--skip-amps", action="store_true",
                    help="with --full: restrict to M1 scope (1b+1c+1d), omit the "
                         "M2-2d amplitude judgment. For CI while M2 remediation "
                         "is in progress (月月-approved 2026-07-09); the M2 GATE "
                         "`--amps` is unaffected. No effect without --full.")
    ap.add_argument("--selftest", action="store_true",
                    help="FIX2 (Phase I) synthetic self-check: a known-frequency "
                         "decaying sinusoid (T60=20ms) through measure_f0()'s "
                         "code path, no CLI/audio render needed; checks f0 "
                         "recovered within +/-3 cents")
    args = ap.parse_args()

    if args.selftest:
        ok, c = selftest_measure_f0_short_window()
        cstr = f"{c:+.3f}" if c is not None else "--"
        print(f"selftest_measure_f0_short_window: recovered {cstr} cents "
              f"(tol +/-3.0) -> {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    cli = Path(args.cli) if args.cli else find_cli()
    if not cli or not cli.exists():
        print("ERROR: TsukiSynthCLI not found. Build it first "
              "(cmake --build build --target TsukiSynthCLI) or pass --cli.",
              file=sys.stderr)
        return 2
    print(f"CLI: {cli}")

    if not args.full:
        print("=" * 70)
        print("TsukiSynth physics verification — measured spectrum vs theory")
        print("=" * 70)

    def do(od):
        if args.full:
            return run_full(cli, args.engines, od, skip_amps=args.skip_amps)
        if args.levels:
            return report_levels(cli, args.engines, args.notes, od)
        if args.t60:
            return report_t60(cli, args.engines, args.notes, od)
        if args.amps:
            return scan_amps(cli, od, engines=args.engines)
        return run(cli, args.engines, args.notes, od)

    if args.keep:
        outdir = Path(__file__).resolve().parent.parent / "build" / "physics_verify"
        outdir.mkdir(parents=True, exist_ok=True)
        ok = do(outdir)
    else:
        with tempfile.TemporaryDirectory() as td:
            ok = do(Path(td))

    print("\n" + "=" * 70)
    if args.full or args.amps or args.t60:
        print("RESULT:", "ALL WITHIN TOLERANCE" if ok else "SOME CHECKS FAILED")
    else:
        print("RESULT:", "ALL WITHIN TOLERANCE" if ok else "SOME PROBES OUT OF TOLERANCE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
