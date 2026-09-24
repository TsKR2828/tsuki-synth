#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
measurement_selfcal.py -- self-calibration sentinel for the PITCH estimator
that melody_verify.py / stem_verify.py use as their product GATE.

WHY (WF0907-C10; TODO.md C10; 2026-08-30 decision): the product GATE judges
±5 cents. That number is this project's own ratified product threshold, not
an external (ISO/industry) standard, so it carries no external authority of
its own -- the only thing that gives it teeth is proof that the MEASURING
INSTRUMENT is accurate well inside it. This tool builds ONLY-synthetic,
known-answer signals (no TsukiSynthCLI render anywhere in this file) and
feeds them through `melody_verify.measure_pitch_cents` -- the EXACT function
`verify()` calls for the product GATE, not a re-implementation of it -- to
measure that estimator's own error against ground truth.

Requirement (month-lead ratified, R2: not adjustable by this tool):
    max_abs_error_cents over the grid below must be <= 1.0 cent.
Any region that misses it is NOT hidden or patched around: it is printed as
an honest limits table and the tool exits 1. Widening the 1-cent number, or
editing measure_pitch_cents to chase a pass, is out of scope for this file
(see WF0907_C10_selfcal.md ---3 "Forbidden").

Synthetic signal model
-----------------------
  output(t) = sum_n[ amp[n] * exp(-ln(1000) * max(0, t - t_onset) / T60)
                      * sin(2*pi*freq[n]*t) ]           for t >= t_onset
with amp[n] = 1/n (falling harmonic-series spectrum) and, per grid point,
ONE of two partial structures:
  * "harmonic"     freq[n] = n * f0_nominal
  * "inharm_1e-4"  freq[n] = n * f0_nominal * sqrt(1 + B*n^2), B = 1e-4
  * "inharm_1e-3"  freq[n] = n * f0_nominal * sqrt(1 + B*n^2), B = 1e-3
(B is a synthetic-test knob only -- this file makes NO claim that either
value describes any real instrument string; see ModalResonator.h L13 for
the exp(-ln(1000)*t/T60) decay convention this mirrors, and
src/physics/MaterialDB.h L82 for the same ln(1000)/pi provenance note.)
The n=1 partial's own frequency (freq[1], which already carries whatever
inharmonicity the variant applies) is the "true fundamental" judged against
-- exactly what verify_score.course_f0() reads off a real --dump-modes
partials[0] in production, so the comparison is apples-to-apples.

A single T60 is shared by every partial in a given signal (a simplifying
synthetic-test choice, disclosed rather than silently assumed: this file
tests the amplitude-centroid estimator's numerical precision on a decaying
multi-partial tone, not the physical realism of per-harmonic decay rates).

A −90 dBFS (RMS) white-noise bed is added under every signal, and the tone
itself is scaled so its own pre-noise peak sits at one of three levels
(−6 / −30 / −60 dBFS) -- so the grid also exercises the estimator far from
0 dBFS, where a real render's quieter notes live.

Grid: MIDI 36..100 (every semitone) x 3 partial-structure variants x 3
peak levels x sample rates in SR_LIST, all at one onset time (0.037 s --
non-zero, not an integer multiple of the STFT hop used elsewhere in this
tool suite) and one T60 (1.5 s, chosen so PITCH_SEG_S's window still sees
strong energy).

Sensitivity anti-false-green check (--3: prevents an estimator that just
echoes the expected value back from silently passing): on ONE representative
grid cell (A4 / harmonic / -6 dBFS / 48 kHz), the true synthesized frequency
is offset by +3.0 and then -3.0 cents from that cell's nominal f0, while the
EXPECTED f0 passed to the estimator is left at the unshifted nominal value.
A correct estimator must report the shift it was given, +-1.0 cent.

Onset timing (informational only -- no ratified tolerance number attaches
to a synthetic sentinel's onset, so this never affects exit code): measured
with melody_verify.refined_onset(), the same function verify() calls.

Hold-out grid (--holdout, WF0909-C10B §2.2 -- overfitting guard)
------------------------------------------------------------------
The grid above (`run_grid`) is the DEVELOPMENT grid: it sat on the table
while the WF0909-C10B estimator was being chosen (its numbers are quoted in
measure_pitch_cents()'s own docstring), so an estimator that merely
memorises this grid's specific f0/level/inharmonicity lattice would still
pass it without being a real fix. `--holdout` builds a SECOND, disjoint
grid that was never inspected while choosing PITCH_EDGE_TAPER_FRAC (the
sweep in melody_verify.py only ever looked at run_grid()'s numbers):
  * f0 = the SAME MIDI 36..100 nominal frequencies, but each shifted by
    EITHER +37 or -23 cents (both values arbitrary and off-lattice: not a
    quarter-tone, not a bin centre, not related to any constant elsewhere
    in this project) -- so no grid point coincides with a development-grid
    frequency or an exact semitone.
  * inharmonicity B in {3e-4, 2e-3} -- both DIFFERENT from the development
    grid's {1e-4, 1e-3} (and no "harmonic" B=0 variant, unlike run_grid).
  * peak level -12 / -45 dBFS -- both DIFFERENT from the development
    grid's {-6, -30, -60}.
  * onset time HOLDOUT_T_ONSET_S (below) -- a value that is not an integer
    multiple of the STFT hop used elsewhere in this tool suite (256/48000
    s), same provenance rule the development grid's T_ONSET_S follows.
Grid size: 65 MIDI notes x 2 offsets x 2 B values x 2 levels x 2 sample
rates = 1040 points. Same pass/fail rule as the development grid
(max_abs_error_cents <= MAX_ABS_ERROR_CENTS_LIMIT, 0 refusals) -- the 1.0
cent number is not relaxed for hold-out (R2).

Gain-fidelity scan (WF0909-C10B FIX ROUND addition; runs automatically as
part of BOTH the plain and --holdout CLI invocations below -- no separate
flag, see gain_fidelity_scan())
------------------------------------------------------------------
Both grids above center their band on the SYNTHESIZED (already-shifted)
frequency: `measure_one`/`measure_one_holdout` always pass `f0_true` (the
actual, possibly-offset, frequency the tone was built at) as the value
`measure_pitch_cents` is told to expect. That is the RIGHT test for "does
the estimator recover a fixed known tone accurately", but it is NOT the
situation the product's +/-5-cent GATE is actually built to catch, which
is "the caller expects f0_expected, the render actually sounds at
f0_expected+delta -- does the estimator report delta". A fix-round audit
of the WF0909-C10B raised-cosine estimator (see melody_verify.
measure_pitch_cents()'s docstring, candidate (d)) found an estimator that
passes BOTH grids above by a wide margin can still have severely
compressed GAIN on this second axis -- a taper that peaks its weight at
the band's own centre necessarily also peaks at the true frequency in
both grids above, so neither grid could have caught it.

`gain_fidelity_scan()` (run automatically inside the plain and --holdout
invocations below -- no separate CLI flag) exercises
this second axis directly: `measure_one(..., freq_offset_cents=off)` synthesizes the tone
at f0_true*2^(off/1200) while the EXPECTED value passed to
measure_pitch_cents stays at the unshifted f0_true (same convention the
original single-point sensitivity_check() already used at one A4 cell --
this generalises it across the MIDI range and the +/-5..12-cent band
where the product GATE's own pass/fail boundary actually lives). For each
(midi, variant, level, offset) cell it reports GAIN = measured_cents /
offset_cents, i.e. 1.0 = perfect fidelity, 0.0 = the estimator ignores
the true deviation entirely (the "always agrees with expected" mutant
test_mutant_estimator_caught_by_sensitivity_check already guards against
in miniature).

WF0909-C10B FIX ROUND left this scan INFORMATIONAL, because the only
estimator that had ever shipped (the hard-edge centroid) could not clear
any bar on this axis (gain as low as ~0.72 at MIDI 37 / +12 c on a clean
signal, and it loses 18.8 of a 40-cent deviation at MIDI 36), and R2
forbids inventing a tolerance number nobody has ratified.

WF0909-C10C (month-lead's card ---1.1) CHANGES THAT: this axis is now a
pass/fail GATE condition of this tool, judged
    |measured_cents - TRUE offset_cents| <= MAX_ABS_ERROR_CENTS_LIMIT
over offsets 0 / +-3 / +-5 / +-12 / +-25 / +-40 cents, with refusals
counting as failures. No new number was invented: the limit is the SAME
1.0-cent self-certification bar the month-lead ratified on 2026-08-30 and
the two grids already use, now applied to the axis the WF0909-C10B audit
proved those grids are structurally blind to. The
`gain` field (measured/offset) is kept for
test_gain_fidelity_no_regression_vs_legacy in
tests/test_measurement_selfcal.py, which additionally forbids ANY future
estimator from being worse on this axis than the legacy centroid was.

Course-semantics check (WF0909-C10C ---1.3; also exit-code affecting, see
course_semantics_check())
------------------------------------------------------------------
The grids and the gain scan all synthesize ONE partial per band. This
project's default cimbalom/piano presets do not: a note is a 3-string
COURSE detuned -5/0/+5 cents, and the ratified claim about the pitch
estimator is that it reports the course's CENTRE, not its loudest string.
That distinction is what killed WF0909-C10B's candidates (a) and (b) --
both passed every synthetic grid and then failed 4 of 5 real sentinel
notes. `course_semantics_check()` puts it in the synthetic tool where it
belongs, at both an equal-amplitude and a 0.5/1/0.5 amplitude course,
judged against the same 1.0-cent bar.

Release/damping-segment corpus (WF0914-D15; also exit-code affecting, folded
into run_grid()/run_holdout_grid() as the "release" segment -- see
RELEASE_FACTORS / RELEASE_TIME_S / synth_tone_release() below)
------------------------------------------------------------------
WF0909-C10C's real-audio rejection (module reference:
reports/decision_packets/C10_selfcal_domain.zh-TW.md S6.3 /
docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md S9.6) found the structural reason
a matched-model estimator can sweep every grid above and still be wrong on
real renders: every signal this file synthesized before D15 was a SINGLE
exponential decay for the whole analysis window, but a real note that gets
damped (key released, sustain pedal lifted, or voice-stolen) mid-window is
NOT -- ModalResonator::damp(factor) (src/dsp/ModalResonator.h L107-117)
shortens the CURRENT decayTime by `factor` without resetting amplitude, so
the true envelope is continuous in amplitude but discontinuous in decay
RATE at the release instant. The synthetic corpus was therefore blind to
exactly the failure geometry that mattered (WF0909-C10C's diagnosed
piano notes: duration 0.215-0.231 s inside a 1.23 s analysis window).

D15 closes that gap by adding a SECOND segment type, "release", alongside
the original ("sustain", unchanged) to both run_grid() and
run_holdout_grid(): `synth_tone_release()` builds the same falling-
harmonic-series partial stack as synth_tone(), decaying at T60_S until
RELEASE_TIME_S after onset, then continuing from whatever amplitude it has
already reached at a SHORTENED T60 = T60_S * release_factor -- the same
two-stage law ModalResonator.damp() implements, not a re-derived one. The
true fundamental (freqs[0]) is unaffected by the envelope change, so
ground truth is exactly as known as the sustain corpus's.

`release_factor` is drawn from RELEASE_FACTORS, the ACTUAL values this
project's engines call ModalResonator::damp()/StringModel damp() with (grep
result, not invented -- R4): 0.002 (voice-stealing quick fade,
src/engines/CimbalomEngine.h L355 and src/engines/ChromaticEngine.h L279,
same value independently in two engines), 0.05 (CimbalomEngine's regular
noteOff()/sustain-pedal-release path, src/engines/CimbalomEngine.h L867
inside applyDamp()), and 0.08 (ChromaticEngine's regular noteOff() path,
src/engines/ChromaticEngine.h L273/289/410). Each release cell in the grid
cycles through these three factors in turn so the corpus spans the engines'
actual damping-RANGE rather than picking one number. RELEASE_TIME_S (0.20 s
post-onset) is an engineering test-timing choice, not a literature
constant (labelled as such per WF0914_README S2 point 3): it sits inside
melody_verify.PITCH_SEG_S's analysis window ((0.020, 1.250) s relative to
onset) and is the same order of magnitude as the short real note durations
WF0909-C10C actually measured getting damped mid-window.

`release_sensitivity_check()` is the release corpus's own anti-false-green
positive control (module docstring "Sensitivity anti-false-green check"
section, same idea, same +-3.0/-3.0-cent injection and 1.0-cent tolerance,
applied to a release-segment signal instead of a plain sustain one): it
proves the estimator is measuring the release corpus's TRUE frequency, not
just echoing back the expected value, before any worst-case number computed
over that corpus is trusted.

R2/R3 unchanged by this section: no threshold, band, exit-code rule, or
grid point is REMOVED; MAX_ABS_ERROR_CENTS_LIMIT and SENSITIVITY_TOL_CENTS
are reused, not widened or re-derived.
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import melody_verify as mv  # noqa: E402  (same estimator the product GATE uses)

# -- ratified thresholds (R2: NOT adjustable here) ---------------------------
MAX_ABS_ERROR_CENTS_LIMIT = 1.0
SENSITIVITY_OFFSET_CENTS = 3.0
SENSITIVITY_TOL_CENTS = 1.0

# -- synthetic-corpus knobs (test-only; provenance in module docstring) ------
MIDI_LO, MIDI_HI = 36, 100
VARIANTS = ("harmonic", "inharm_1e-4", "inharm_1e-3")
LEVELS_DBFS = (-6.0, -30.0, -60.0)
SR_LIST = (48000, 44100)
T_ONSET_S = 0.037
T60_S = 1.5
DURATION_S = 1.6           # >= T_ONSET_S + PITCH_SEG_S[1] + margin
NOISE_FLOOR_DBFS_RMS = -90.0
N_PARTIALS_MAX = 12
NOISE_SEED = 20260907       # fixed: reproducible grid, not a tuned value

F0_BANDS = [("<167Hz", 0.0, 167.0),
            ("167-500Hz", 167.0, 500.0),
            ("500-2000Hz", 500.0, 2000.0),
            (">2000Hz", 2000.0, float("inf"))]

# -- hold-out grid knobs (WF0909-C10B §2.2; provenance in module docstring
# "Hold-out grid" section above -- deliberately disjoint from the
# development-grid knobs, never inspected while choosing the estimator) ----
HOLDOUT_OFFSETS_CENTS = (37.0, -23.0)
HOLDOUT_B_LIST = (3e-4, 2e-3)
HOLDOUT_LEVELS_DBFS = (-12.0, -45.0)
# WF0909-C10B fix round: the original value here (0.0533 s) was
# 9.99375 x the 256/48000 s STFT hop -- only 0.4 samples away from an
# INTEGER hop multiple, so it did not actually deliver the "non-hop-
# aligned onset" §2.2 asks for. 0.0507 s = 9.50625 x hop -- fractional
# part 0.506, the point in [0,1) FARTHEST from any integer hop boundary --
# and is still disjoint from the development grid's T_ONSET_S (0.037 s,
# 6.9375 x hop).
HOLDOUT_T_ONSET_S = 0.0507

# -- release/damping-segment corpus knobs (WF0914-D15; provenance in module
# docstring "Release/damping-segment corpus" section above) ------------------
# Actual values engines call ModalResonator::damp()/StringModel.damp() with
# (grep'd from src/, not invented -- R4):
#   0.002 -- voice-stealing quick fade-out, src/engines/CimbalomEngine.h:355
#            `strings[s].damp (0.002f);` and src/engines/ChromaticEngine.h:279
#            `resonator.damp (0.002f);` (same value, two independent engines)
#   0.05  -- CimbalomEngine's regular noteOff()/sustain-pedal-release damper,
#            src/engines/CimbalomEngine.h:867 (applyDamp(): `strings[s].damp
#            (0.05f);`)
#   0.08  -- ChromaticEngine's regular noteOff()/sustain-pedal-release damper,
#            src/engines/ChromaticEngine.h:273 / :289 / :410
#            (`resonator.damp (0.08f);`)
RELEASE_FACTORS = (0.002, 0.05, 0.08)
# Engineering test-timing choice (R4-labelled, not a literature constant):
# lands inside melody_verify.PITCH_SEG_S's analysis window ((0.020, 1.250) s
# relative to onset) and matches the order of magnitude of the short real
# note durations (0.215-0.231 s) WF0909-C10C measured getting damped
# mid-window (reports/decision_packets/C10_selfcal_domain.zh-TW.md S6.3;
# docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md S9.6).
RELEASE_TIME_S = 0.20


def midi_to_hz(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def build_partials(f0_nominal, variant, sr):
    """Returns (freqs, amps, f0_true). freqs/amps cover n=1..N, N capped so
    the top partial stays comfortably under Nyquist (0.45*sr)."""
    n_max = max(1, min(N_PARTIALS_MAX, int(0.45 * sr / f0_nominal)))
    ns = np.arange(1, n_max + 1)
    if variant == "harmonic":
        freqs = ns * f0_nominal
    else:
        b = {"inharm_1e-4": 1e-4, "inharm_1e-3": 1e-3}[variant]
        freqs = ns * f0_nominal * np.sqrt(1.0 + b * ns ** 2)
    amps = 1.0 / ns
    return freqs, amps, float(freqs[0])


def synth_tone(freqs, amps, sr, t_onset, duration_s, t60, peak_dbfs,
               noise_floor_dbfs=NOISE_FLOOR_DBFS_RMS, seed=NOISE_SEED):
    """Sum of decaying partials (0 before t_onset) + a fixed-RMS white-noise
    bed, tone peak-normalised to peak_dbfs BEFORE the noise is added."""
    n = int(round(duration_s * sr))
    t = np.arange(n) / sr
    active = t >= t_onset
    tt = np.where(active, t - t_onset, 0.0)
    env = np.exp(-math.log(1000.0) * tt / t60) * active
    sig = np.zeros(n)
    for f, a in zip(freqs, amps):
        sig += a * env * np.sin(2.0 * np.pi * f * t)
    peak = float(np.max(np.abs(sig)))
    target_peak = 10.0 ** (peak_dbfs / 20.0)
    if peak > 0:
        sig *= target_peak / peak
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    noise_rms = float(np.sqrt(np.mean(noise ** 2)))
    target_rms = 10.0 ** (noise_floor_dbfs / 20.0)
    if noise_rms > 0:
        noise *= target_rms / noise_rms
    return sig + noise


def synth_tone_release(freqs, amps, sr, t_onset, duration_s, t60_sustain,
                        release_time_s, release_factor, peak_dbfs,
                        noise_floor_dbfs=NOISE_FLOOR_DBFS_RMS, seed=NOISE_SEED):
    """WF0914-D15: two-stage-decay counterpart of synth_tone() (module
    docstring "Release/damping-segment corpus" section). Identical to
    synth_tone() for t < t_onset + release_time_s (T60 = t60_sustain); at
    and after that instant the envelope continues from whatever amplitude
    it already reached but decays at T60 = t60_sustain * release_factor --
    amplitude-continuous, decay-rate-discontinuous, mirroring
    ModalResonator::damp() (src/dsp/ModalResonator.h L107-117) exactly:
    that function also only rewrites decayCoeff going forward from the
    CURRENT amplitude, never resets it."""
    n = int(round(duration_s * sr))
    t = np.arange(n) / sr
    active = t >= t_onset
    tt = np.where(active, t - t_onset, 0.0)
    # stage 1 (0..release_time_s): identical formula to synth_tone().
    # stage 2 (>= release_time_s): continues from the stage-1 amplitude at
    # release_time_s, then decays at the shortened T60 for the elapsed time
    # since the release instant -- same log-domain construction as
    # synth_tone()'s single-stage exp(), just composed in two pieces.
    env = np.exp(-math.log(1000.0) * np.minimum(tt, release_time_s) / t60_sustain)
    t60_release = t60_sustain * release_factor
    tail = np.where(tt > release_time_s, tt - release_time_s, 0.0)
    env = env * np.exp(-math.log(1000.0) * tail / t60_release) * active
    sig = np.zeros(n)
    for f, a in zip(freqs, amps):
        sig += a * env * np.sin(2.0 * np.pi * f * t)
    peak = float(np.max(np.abs(sig)))
    target_peak = 10.0 ** (peak_dbfs / 20.0)
    if peak > 0:
        sig *= target_peak / peak
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    noise_rms = float(np.sqrt(np.mean(noise ** 2)))
    target_rms = 10.0 ** (noise_floor_dbfs / 20.0)
    if noise_rms > 0:
        noise *= target_rms / noise_rms
    return sig + noise


def measure_one(midi, variant, level_dbfs, sr, t_onset=T_ONSET_S, t60=T60_S,
                 duration_s=DURATION_S, freq_offset_cents=0.0, seed=NOISE_SEED):
    """Synthesizes one grid cell and returns
    (error_cents, fail_reason, onset_err_ms, f0_nominal, f0_true).
    freq_offset_cents shifts the SYNTHESIZED frequency away from f0_true
    while the value passed to measure_pitch_cents (the "expected" side)
    stays at the unshifted f0_true -- used only by the sensitivity check."""
    f0_nominal = midi_to_hz(midi)
    freqs, amps, f0_true = build_partials(f0_nominal, variant, sr)
    if freq_offset_cents:
        shift = 2.0 ** (freq_offset_cents / 1200.0)
        freqs = freqs * shift
    sig = synth_tone(freqs, amps, sr, t_onset, duration_s, t60, level_dbfs,
                      seed=seed)
    cents, fail = mv.measure_pitch_cents(sig, sr, f0_true, t_onset)
    onset_err_ms = None
    if fail is None:
        lo, hi = mv.band_of(f0_true)
        t_ref = mv.refined_onset(sig, sr, lo, hi, t_onset)
        if t_ref is not None:
            onset_err_ms = (t_ref - t_onset) * 1e3
    return cents, fail, onset_err_ms, f0_nominal, f0_true


def measure_one_release(midi, variant, level_dbfs, sr, release_factor,
                         t_onset=T_ONSET_S, t60=T60_S,
                         release_time_s=RELEASE_TIME_S,
                         duration_s=DURATION_S, freq_offset_cents=0.0,
                         seed=NOISE_SEED):
    """Release-segment counterpart of measure_one(): same grid cell
    (midi/variant/level/sr), same ground-truth f0_true, but synthesized with
    synth_tone_release() instead of synth_tone() (module docstring
    "Release/damping-segment corpus" section). Same return shape as
    measure_one() so callers/summarize() need no special-casing."""
    f0_nominal = midi_to_hz(midi)
    freqs, amps, f0_true = build_partials(f0_nominal, variant, sr)
    if freq_offset_cents:
        shift = 2.0 ** (freq_offset_cents / 1200.0)
        freqs = freqs * shift
    sig = synth_tone_release(freqs, amps, sr, t_onset, duration_s, t60,
                              release_time_s, release_factor, level_dbfs,
                              seed=seed)
    cents, fail = mv.measure_pitch_cents(sig, sr, f0_true, t_onset)
    onset_err_ms = None
    if fail is None:
        lo, hi = mv.band_of(f0_true)
        t_ref = mv.refined_onset(sig, sr, lo, hi, t_onset)
        if t_ref is not None:
            onset_err_ms = (t_ref - t_onset) * 1e3
    return cents, fail, onset_err_ms, f0_nominal, f0_true


def build_holdout_partials(midi, offset_cents, b, sr):
    """Hold-out counterpart of build_partials(): nominal MIDI frequency
    shifted by offset_cents (off-lattice, module docstring "Hold-out grid"
    section) then given stiffness-inharmonic partials f_n = n*f0*sqrt(1 +
    B*n^2) -- same formula as build_partials's inharmonic branch. No
    "harmonic" (B=0) hold-out variant, matching HOLDOUT_B_LIST. Returns
    (freqs, amps, f0_true)."""
    f0_nominal = midi_to_hz(midi) * (2.0 ** (offset_cents / 1200.0))
    n_max = max(1, min(N_PARTIALS_MAX, int(0.45 * sr / f0_nominal)))
    ns = np.arange(1, n_max + 1)
    freqs = ns * f0_nominal * np.sqrt(1.0 + b * ns ** 2)
    amps = 1.0 / ns
    return freqs, amps, float(freqs[0])


def measure_one_holdout(midi, offset_cents, b, level_dbfs, sr,
                         t_onset=HOLDOUT_T_ONSET_S, t60=T60_S,
                         duration_s=DURATION_S, seed=NOISE_SEED):
    """Hold-out counterpart of measure_one() -- same shape of return value
    (error_cents, fail_reason, onset_err_ms, f0_nominal, f0_true) so it can
    reuse summarize()."""
    f0_nominal = midi_to_hz(midi) * (2.0 ** (offset_cents / 1200.0))
    freqs, amps, f0_true = build_holdout_partials(midi, offset_cents, b, sr)
    sig = synth_tone(freqs, amps, sr, t_onset, duration_s, t60, level_dbfs,
                      seed=seed)
    cents, fail = mv.measure_pitch_cents(sig, sr, f0_true, t_onset)
    onset_err_ms = None
    if fail is None:
        lo, hi = mv.band_of(f0_true)
        t_ref = mv.refined_onset(sig, sr, lo, hi, t_onset)
        if t_ref is not None:
            onset_err_ms = (t_ref - t_onset) * 1e3
    return cents, fail, onset_err_ms, f0_nominal, f0_true


def measure_one_holdout_release(midi, offset_cents, b, level_dbfs, sr,
                                 release_factor,
                                 t_onset=HOLDOUT_T_ONSET_S, t60=T60_S,
                                 release_time_s=RELEASE_TIME_S,
                                 duration_s=DURATION_S, seed=NOISE_SEED):
    """Release-segment counterpart of measure_one_holdout() (WF0914-D15):
    same hold-out cell (midi/offset/B/level/sr), same ground-truth f0_true,
    synthesized with synth_tone_release() instead of synth_tone(). Same
    return shape so it plugs into summarize() unchanged."""
    f0_nominal = midi_to_hz(midi) * (2.0 ** (offset_cents / 1200.0))
    freqs, amps, f0_true = build_holdout_partials(midi, offset_cents, b, sr)
    sig = synth_tone_release(freqs, amps, sr, t_onset, duration_s, t60,
                              release_time_s, release_factor, level_dbfs,
                              seed=seed)
    cents, fail = mv.measure_pitch_cents(sig, sr, f0_true, t_onset)
    onset_err_ms = None
    if fail is None:
        lo, hi = mv.band_of(f0_true)
        t_ref = mv.refined_onset(sig, sr, lo, hi, t_onset)
        if t_ref is not None:
            onset_err_ms = (t_ref - t_onset) * 1e3
    return cents, fail, onset_err_ms, f0_nominal, f0_true


def run_holdout_grid():
    """Builds the WF0909-C10B hold-out grid (module docstring "Hold-out
    grid" section): 65 MIDI notes x 2 off-lattice cent offsets x 2
    inharmonicity B values x 2 peak levels x 2 sample rates = 1040 points,
    every knob disjoint from the development grid's (run_grid), TAGGED
    segment="sustain" -- PLUS (WF0914-D15) an equal-size "release" segment
    built from the identical (midi, offset, b, level, sr) cells via
    measure_one_holdout_release(), cycling through RELEASE_FACTORS, giving
    2080 points total. Same pass/fail rule as the development grid
    (max_abs_error_cents <= MAX_ABS_ERROR_CENTS_LIMIT, 0 refusals) -- the 1.0
    cent number is not relaxed for hold-out or for the release segment (R2)."""
    rows = []
    release_idx = 0
    for sr in SR_LIST:
        for midi in range(MIDI_LO, MIDI_HI + 1):
            for offset in HOLDOUT_OFFSETS_CENTS:
                for b in HOLDOUT_B_LIST:
                    for level in HOLDOUT_LEVELS_DBFS:
                        cents, fail, onset_err_ms, f0_nom, f0_true = measure_one_holdout(
                            midi, offset, b, level, sr)
                        rows.append({
                            "sr": sr, "midi": midi, "offset_cents": offset,
                            "b": b, "level_dbfs": level, "f0_nominal": f0_nom,
                            "f0_true": f0_true, "error_cents": cents,
                            "fail_reason": fail, "onset_err_ms": onset_err_ms,
                            "segment": "sustain", "release_factor": None,
                        })
                        rfactor = RELEASE_FACTORS[release_idx % len(RELEASE_FACTORS)]
                        release_idx += 1
                        rcents, rfail, ronset, rf0nom, rf0true = measure_one_holdout_release(
                            midi, offset, b, level, sr, rfactor)
                        rows.append({
                            "sr": sr, "midi": midi, "offset_cents": offset,
                            "b": b, "level_dbfs": level, "f0_nominal": rf0nom,
                            "f0_true": rf0true, "error_cents": rcents,
                            "fail_reason": rfail, "onset_err_ms": ronset,
                            "segment": "release", "release_factor": rfactor,
                        })
    return rows


# -- gain-fidelity scan knobs (WF0909-C10B FIX ROUND; module docstring
# "Gain-fidelity scan" section above) -- deliberately spans the +/-5-cent
# product GATE's own decision boundary, not just the +/-3-cent point the
# original sensitivity_check() used. ----------------------------------------
GAIN_SCAN_MIDIS = (37, 45, 60, 69, 80, 90, 100)
GAIN_SCAN_VARIANTS = ("harmonic", "inharm_1e-3")
GAIN_SCAN_LEVELS_DBFS = (-6.0, -30.0)
# WF0909-C10C ---1.1 (month-lead-ratified 1-cent bar applied to THIS axis):
# 0 / +-3 / +-5 / +-12 / +-25 / +-40 cents. 0 is included so the scan also
# covers "no deviation at all"; +-40 c is 78% of the way to the +/-3% band
# edge at any f0, i.e. the widest real mistuning band_of can still contain.
GAIN_SCAN_OFFSETS_CENTS = (0.0, -40.0, -25.0, -12.0, -5.0, -3.0,
                            3.0, 5.0, 12.0, 25.0, 40.0)


def gain_fidelity_scan(estimator=None, sr=48000):
    """WF0909-C10B fix round: measures GAIN = measured_cents / offset_cents
    (module docstring "Gain-fidelity scan") over GAIN_SCAN_MIDIS x
    GAIN_SCAN_VARIANTS x GAIN_SCAN_LEVELS_DBFS x GAIN_SCAN_OFFSETS_CENTS
    (308 points) at a fixed sample rate (gain fidelity is a per-bin-
    alignment/windowing property, not a resampling one -- SR_LIST's two
    rates are already exercised by run_grid/run_holdout_grid). `estimator`
    lets a caller (the mutant test, or a before/after comparison) swap in
    a different pitch function; defaults to the live
    melody_verify.measure_pitch_cents.

    WF0909-C10C (month-lead ruling recorded in the card's ---1.1): this scan
    is NO LONGER informational -- `error_cents` = measured - TRUE offset is
    judged against the SAME already-ratified MAX_ABS_ERROR_CENTS_LIMIT
    (1.0 cent) the two grids use, and main() exits 1 if any cell misses or
    refuses. That is not a new tolerance (R2): it is the 2026-08-30
    self-certification bar applied to the second axis the WF0909-C10B audit
    showed the grids were structurally blind to. Returns a list of row
    dicts; `gain` (= measured/offset) is kept for the legacy-comparison
    test and is None at offset 0."""
    fn = estimator if estimator is not None else mv.measure_pitch_cents
    rows = []
    for midi in GAIN_SCAN_MIDIS:
        for variant in GAIN_SCAN_VARIANTS:
            for level in GAIN_SCAN_LEVELS_DBFS:
                for offset in GAIN_SCAN_OFFSETS_CENTS:
                    f0_nominal = midi_to_hz(midi)
                    freqs, amps, f0_true = build_partials(f0_nominal, variant, sr)
                    shift = 2.0 ** (offset / 1200.0)
                    sig = synth_tone(freqs * shift, amps, sr, T_ONSET_S,
                                      DURATION_S, T60_S, level)
                    cents, fail = fn(sig, sr, f0_true, T_ONSET_S)
                    gain = (cents / offset) if (fail is None and offset != 0) else None
                    err = (cents - offset) if fail is None else None
                    rows.append({
                        "midi": midi, "variant": variant, "level_dbfs": level,
                        "offset_cents": offset, "measured_cents": cents,
                        "fail_reason": fail, "gain": gain, "error_cents": err,
                    })
    return rows


# -- course-semantics knobs (WF0909-C10C ---1.3) -----------------------------
# A "course" in this project's default cimbalom/piano presets is 3 strings
# detuned -5/0/+5 cents (see melody_verify.PITCH_SEG_S's own note). The
# ratified claim the pitch estimator makes about a course is that it reports
# the course's CENTRE, not its loudest string -- so both an equal-amplitude
# course and a 0.5/1/0.5 one must measure the centre.
COURSE_DETUNE_CENTS = (-5.0, 0.0, 5.0)
COURSE_AMP_SETS = (("equal", (1.0, 1.0, 1.0)),
                    ("unequal", (0.5, 1.0, 0.5)))
COURSE_SCAN_MIDIS = (36, 44, 48, 55, 60, 69, 80, 90, 100)


def course_semantics_check(estimator=None, sr=48000, level_dbfs=-6.0):
    """WF0909-C10C ---1.3: synthesize a 3-string course (COURSE_DETUNE_CENTS)
    around each COURSE_SCAN_MIDIS note, at both amplitude sets, and require
    the estimator to report the course CENTRE within
    MAX_ABS_ERROR_CENTS_LIMIT. No decay/inharmonicity variation here -- this
    check is about the course-centroid SEMANTIC, which is what the
    single-peak candidates (a)/(b) of WF0909-C10B broke on real audio while
    passing every synthetic grid. Returns a list of row dicts."""
    fn = estimator if estimator is not None else mv.measure_pitch_cents
    rows = []
    for label, amp_set in COURSE_AMP_SETS:
        for midi in COURSE_SCAN_MIDIS:
            f0 = midi_to_hz(midi)
            freqs = np.array([f0 * 2.0 ** (c / 1200.0) for c in COURSE_DETUNE_CENTS])
            amps = np.array(amp_set, dtype=float)
            sig = synth_tone(freqs, amps, sr, T_ONSET_S, DURATION_S, T60_S,
                              level_dbfs)
            cents, fail = fn(sig, sr, f0, T_ONSET_S)
            rows.append({"amp_set": label, "midi": midi, "f0_centre": f0,
                          "measured_cents": cents, "fail_reason": fail})
    return rows


def band_label(f0):
    for label, lo, hi in F0_BANDS:
        if lo <= f0 < hi:
            return label
    return F0_BANDS[-1][0]


def run_grid():
    """Development grid (module docstring "Grid" section): the original
    1170-point single-exponential-decay ("sustain") corpus, TAGGED
    segment="sustain" -- PLUS (WF0914-D15) an equal-size "release" segment
    built from the identical (midi, variant, level, sr) cells via
    measure_one_release(), cycling through RELEASE_FACTORS so the corpus
    spans the engines' actual damping-factor range (module docstring
    "Release/damping-segment corpus" section), giving 2340 points total."""
    rows = []
    release_idx = 0
    for sr in SR_LIST:
        for midi in range(MIDI_LO, MIDI_HI + 1):
            for variant in VARIANTS:
                for level in LEVELS_DBFS:
                    cents, fail, onset_err_ms, f0_nom, f0_true = measure_one(
                        midi, variant, level, sr)
                    rows.append({
                        "sr": sr, "midi": midi, "variant": variant,
                        "level_dbfs": level, "f0_nominal": f0_nom,
                        "f0_true": f0_true, "error_cents": cents,
                        "fail_reason": fail, "onset_err_ms": onset_err_ms,
                        "segment": "sustain", "release_factor": None,
                    })
                    rfactor = RELEASE_FACTORS[release_idx % len(RELEASE_FACTORS)]
                    release_idx += 1
                    rcents, rfail, ronset, rf0nom, rf0true = measure_one_release(
                        midi, variant, level, sr, rfactor)
                    rows.append({
                        "sr": sr, "midi": midi, "variant": variant,
                        "level_dbfs": level, "f0_nominal": rf0nom,
                        "f0_true": rf0true, "error_cents": rcents,
                        "fail_reason": rfail, "onset_err_ms": ronset,
                        "segment": "release", "release_factor": rfactor,
                    })
    return rows


def sensitivity_check(midi=69, variant="harmonic", level_dbfs=-6.0, sr=48000):
    """Returns list of (offset_cents, measured_cents, ok)."""
    out = []
    for offset in (SENSITIVITY_OFFSET_CENTS, -SENSITIVITY_OFFSET_CENTS):
        cents, fail, _onset, _nom, _true = measure_one(
            midi, variant, level_dbfs, sr, freq_offset_cents=offset)
        ok = (fail is None and cents is not None
              and abs(cents - offset) <= SENSITIVITY_TOL_CENTS)
        out.append((offset, cents, fail, ok))
    return out


def release_sensitivity_check(midi=69, variant="harmonic", level_dbfs=-6.0,
                               sr=48000, release_factor=RELEASE_FACTORS[1]):
    """WF0914-D15 positive control (module docstring "Release/damping-
    segment corpus" section): same idea as sensitivity_check() -- the TRUE
    synthesized frequency is offset by +/-3.0 cents while the EXPECTED value
    passed to the estimator stays unshifted -- but built on a RELEASE-
    segment signal (synth_tone_release()) instead of a plain sustain one.
    Proves the estimator is measuring the release corpus's true frequency,
    not echoing back the expected value, before any worst-case number
    computed over the release segment is trusted. Default release_factor
    is 0.05 (CimbalomEngine's regular damper, RELEASE_FACTORS[1]) -- the
    same tolerance/offset numbers as sensitivity_check() (R2: no new
    number). Returns list of (offset_cents, measured_cents, fail, ok)."""
    out = []
    for offset in (SENSITIVITY_OFFSET_CENTS, -SENSITIVITY_OFFSET_CENTS):
        cents, fail, _onset, _nom, _true = measure_one_release(
            midi, variant, level_dbfs, sr, release_factor,
            freq_offset_cents=offset)
        ok = (fail is None and cents is not None
              and abs(cents - offset) <= SENSITIVITY_TOL_CENTS)
        out.append((offset, cents, fail, ok))
    return out


def summarize(rows):
    errs = [r["error_cents"] for r in rows if r["fail_reason"] is None
            and r["error_cents"] is not None]
    fails = [r for r in rows if r["fail_reason"] is not None]
    max_abs = max((abs(e) for e in errs), default=None)

    by_band = {}
    for r in rows:
        if r["fail_reason"] is not None or r["error_cents"] is None:
            continue
        lbl = band_label(r["f0_true"])
        by_band.setdefault(lbl, []).append(abs(r["error_cents"]))

    by_level = {}
    for r in rows:
        if r["fail_reason"] is not None or r["error_cents"] is None:
            continue
        by_level.setdefault(r["level_dbfs"], []).append(abs(r["error_cents"]))

    # WF0914-D15: split by "segment" (sustain / release) when the rows carry
    # that tag (run_grid()/run_holdout_grid()); absent on rows from older
    # call sites (e.g. a caller building its own row list), so default to
    # "sustain" rather than KeyError.
    by_segment = {}
    n_fail_by_segment = {}
    for r in rows:
        seg = r.get("segment", "sustain")
        if r["fail_reason"] is not None:
            n_fail_by_segment[seg] = n_fail_by_segment.get(seg, 0) + 1
            continue
        if r["error_cents"] is None:
            continue
        by_segment.setdefault(seg, []).append(abs(r["error_cents"]))

    onset_errs = [r["onset_err_ms"] for r in rows if r["onset_err_ms"] is not None]
    return {
        "max_abs_error_cents": max_abs,
        "n_points": len(rows),
        "n_fail_reason": len(fails),
        "fails": fails,
        "by_band": {k: max(v) for k, v in by_band.items()},
        "by_level": {k: max(v) for k, v in by_level.items()},
        "by_segment": {k: max(v) for k, v in by_segment.items()},
        "n_fail_by_segment": n_fail_by_segment,
        "onset_max_abs_ms": max((abs(e) for e in onset_errs), default=None),
        "onset_n": len(onset_errs),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--holdout", action="store_true",
                     help="run the WF0909-C10B hold-out grid (module "
                          "docstring 'Hold-out grid' section) INSTEAD OF "
                          "the development grid -- disjoint f0 offsets/B/"
                          "level/onset, never inspected while choosing the "
                          "estimator, to catch development-grid overfitting.")
    a = ap.parse_args()

    if a.holdout:
        print("measurement_selfcal --holdout: synthesizing hold-out grid "
              "(MIDI %d..%d x %d offsets x %d B values x %d levels x sr %s)"
              % (MIDI_LO, MIDI_HI, len(HOLDOUT_OFFSETS_CENTS),
                 len(HOLDOUT_B_LIST), len(HOLDOUT_LEVELS_DBFS),
                 ",".join(str(s) for s in SR_LIST)))
        rows = run_holdout_grid()
        summ = summarize(rows)
        print("  grid points: %d  (fail_reason on %d)"
              % (summ["n_points"], summ["n_fail_reason"]))
        for r in summ["fails"][:20]:
            print("    [ERR] sr=%d midi=%d offset=%+.1fc B=%s level=%s: %s"
                  % (r["sr"], r["midi"], r["offset_cents"], r["b"],
                     r["level_dbfs"], r["fail_reason"]))
    else:
        print("measurement_selfcal: synthesizing grid "
              "(MIDI %d..%d x %d variants x %d levels x sr %s)"
              % (MIDI_LO, MIDI_HI, len(VARIANTS), len(LEVELS_DBFS),
                 ",".join(str(s) for s in SR_LIST)))
        rows = run_grid()
        summ = summarize(rows)
        print("  grid points: %d  (fail_reason on %d)"
              % (summ["n_points"], summ["n_fail_reason"]))
        for r in summ["fails"][:20]:
            print("    [ERR] sr=%d midi=%d variant=%s level=%s: %s"
                  % (r["sr"], r["midi"], r["variant"], r["level_dbfs"], r["fail_reason"]))

    print("  by f0 band (max |error_cents|):")
    for label, _lo, _hi in F0_BANDS:
        v = summ["by_band"].get(label)
        print("    %-12s %s" % (label, ("%.4f c" % v) if v is not None else "(no points)"))

    print("  by level (max |error_cents|):")
    for level in (HOLDOUT_LEVELS_DBFS if a.holdout else LEVELS_DBFS):
        v = summ["by_level"].get(level)
        print("    %+6.1f dBFS  %s" % (level, ("%.4f c" % v) if v is not None else "(no points)"))

    print("  by segment (WF0914-D15, max |error_cents|, fail_reason count):")
    for seg in ("sustain", "release"):
        v = summ["by_segment"].get(seg)
        nf = summ["n_fail_by_segment"].get(seg, 0)
        print("    %-8s %s  (fail_reason on %d)"
              % (seg, ("%.4f c" % v) if v is not None else "(no points)", nf))

    print("  max_abs_error_cents = %s  (limit %.1f)"
          % (("%.4f" % summ["max_abs_error_cents"])
             if summ["max_abs_error_cents"] is not None else "N/A",
             MAX_ABS_ERROR_CENTS_LIMIT))

    grid_ok = (summ["n_fail_reason"] == 0
               and summ["max_abs_error_cents"] is not None
               and summ["max_abs_error_cents"] <= MAX_ABS_ERROR_CENTS_LIMIT)

    print("  sensitivity anti-false-green (grid cell MIDI69/harmonic/-6dBFS/48kHz):")
    sens = sensitivity_check()
    sens_ok = True
    for offset, cents, fail, ok in sens:
        sens_ok &= ok
        if fail is not None:
            print("    offset %+.1fc -> FAIL: %s" % (offset, fail))
        else:
            print("    offset %+.1fc -> measured %+.4fc  [%s]"
                  % (offset, cents, "OK" if ok else "FAIL"))

    print("  release-segment sensitivity anti-false-green (WF0914-D15; grid "
          "cell MIDI69/harmonic/-6dBFS/48kHz, release_factor=%g -- module "
          "docstring 'Release/damping-segment corpus'):"
          % RELEASE_FACTORS[1])
    rel_sens = release_sensitivity_check()
    rel_sens_ok = True
    for offset, cents, fail, ok in rel_sens:
        rel_sens_ok &= ok
        if fail is not None:
            print("    offset %+.1fc -> FAIL: %s" % (offset, fail))
        else:
            print("    offset %+.1fc -> measured %+.4fc  [%s]"
                  % (offset, cents, "OK" if ok else "FAIL"))

    print("  onset error (informational, no exit-code effect): "
          "max |err| = %s ms over %d points"
          % (("%.4f" % summ["onset_max_abs_ms"])
             if summ["onset_max_abs_ms"] is not None else "N/A",
             summ["onset_n"]))

    print("  gain-fidelity scan (WF0909-C10C ---1.1: PASS/FAIL, exit-code "
          "affecting -- module docstring 'Gain-fidelity scan'): "
          "|measured - TRUE offset| over %d cells (MIDI %s x offsets %s), "
          "limit %.1f c:"
          % (len(GAIN_SCAN_MIDIS) * len(GAIN_SCAN_VARIANTS)
             * len(GAIN_SCAN_LEVELS_DBFS) * len(GAIN_SCAN_OFFSETS_CENTS),
             ",".join(str(m) for m in GAIN_SCAN_MIDIS),
             ",".join("%+g" % o for o in GAIN_SCAN_OFFSETS_CENTS),
             MAX_ABS_ERROR_CENTS_LIMIT))
    gain_rows = gain_fidelity_scan(sr=48000)
    n_gain_refuse = sum(1 for r in gain_rows if r["fail_reason"] is not None)
    gain_errs = [r for r in gain_rows if r["error_cents"] is not None]
    gain_max = max((abs(r["error_cents"]) for r in gain_errs), default=None)
    if gain_errs:
        worst_err_row = max(gain_errs, key=lambda r: abs(r["error_cents"]))
        print("    worst |measured - true| = %.4f c (midi=%d %s %+gdBFS "
              "offset=%+gc measured=%+.4fc)"
              % (abs(worst_err_row["error_cents"]), worst_err_row["midi"],
                 worst_err_row["variant"], worst_err_row["level_dbfs"],
                 worst_err_row["offset_cents"], worst_err_row["measured_cents"]))
    gains = [r for r in gain_rows if r["gain"] is not None]
    if gains:
        worst_deficit_row = max(gains, key=lambda r: abs(1.0 - r["gain"]))
        print("    worst gain (informational) = %.4f (midi=%d %s %+gdBFS "
              "offset=%+gc measured=%+.4fc)"
              % (worst_deficit_row["gain"], worst_deficit_row["midi"],
                 worst_deficit_row["variant"], worst_deficit_row["level_dbfs"],
                 worst_deficit_row["offset_cents"], worst_deficit_row["measured_cents"]))
    for r in gain_rows:
        if r["fail_reason"] is not None:
            print("    [ERR] midi=%d %s %+gdBFS offset=%+gc REFUSED: %s"
                  % (r["midi"], r["variant"], r["level_dbfs"],
                     r["offset_cents"], r["fail_reason"]))
        elif abs(r["error_cents"]) > MAX_ABS_ERROR_CENTS_LIMIT:
            print("    [ERR] midi=%d %s %+gdBFS offset=%+gc measured=%+.4fc "
                  "-> |err| %.4f c > %.1f"
                  % (r["midi"], r["variant"], r["level_dbfs"],
                     r["offset_cents"], r["measured_cents"],
                     abs(r["error_cents"]), MAX_ABS_ERROR_CENTS_LIMIT))
    gain_ok = (n_gain_refuse == 0 and gain_max is not None
               and gain_max <= MAX_ABS_ERROR_CENTS_LIMIT)

    print("  course-semantics check (WF0909-C10C ---1.3: PASS/FAIL, "
          "exit-code affecting): 3 strings at %s cents, amplitude sets %s, "
          "must report the CENTRE within %.1f c:"
          % ("/".join("%+g" % c for c in COURSE_DETUNE_CENTS),
             "/".join(lbl for lbl, _ in COURSE_AMP_SETS),
             MAX_ABS_ERROR_CENTS_LIMIT))
    course_rows = course_semantics_check()
    course_ok = True
    course_max = None
    for r in course_rows:
        if r["fail_reason"] is not None:
            course_ok = False
            print("    [ERR] %s midi=%d REFUSED: %s"
                  % (r["amp_set"], r["midi"], r["fail_reason"]))
            continue
        e = abs(r["measured_cents"])
        course_max = e if course_max is None else max(course_max, e)
        if e > MAX_ABS_ERROR_CENTS_LIMIT:
            course_ok = False
            print("    [ERR] %s midi=%d measured %+.4f c from the course "
                  "centre (> %.1f)"
                  % (r["amp_set"], r["midi"], r["measured_cents"],
                     MAX_ABS_ERROR_CENTS_LIMIT))
    print("    max |offset from course centre| = %s c over %d cells"
          % (("%.4f" % course_max) if course_max is not None else "N/A",
             len(course_rows)))

    passed = grid_ok and sens_ok and gain_ok and course_ok and rel_sens_ok
    print("RESULT (%s grid): %s"
          % ("hold-out" if a.holdout else "development", "PASS" if passed else "FAIL"))
    if not passed:
        print("  (R2: no tolerance in this file may be widened to reach PASS --"
              " a miss here is reported, not patched around.)")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
