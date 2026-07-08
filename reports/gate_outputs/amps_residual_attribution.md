# --amps residual attribution (2026-07-09)

## TL;DR

**Single mechanism, fully closes every remaining `--amps` residual.**
`tools/physics_verify.py`'s `synth_theory_signal()` decays each mode as
`amp0 * exp(-t/decay)`, treating the `decay` field (`ModalResonator::Mode::
decayTime`) as a classic 1/e time-constant τ. But `ModalResonator::excite()`
— the model's own, already-documented math — defines `decayTime` as a **T60**
(time to -60 dB): `decayCoeff = exp(-6.9078f/(decayTime*sampleRate))` per
sample, i.e. the true closed form is `amp0 * exp(-ln(1000)*t/decayTime)`,
**6.9078× faster** than what the theory-side script computes. Substituting
the correct exponent closes every previously-failing partial to **within
±0.22 dB** (from as bad as **-33.7 dB**), reproduced across every diagnostic
render variant tested (BodyResonance bypassed, exciter noise disabled,
string count forced to 1). This is a **THEORY GAP** in the Python verifier,
not a C++ bug — the C++ decay recursion is internally consistent with its
own documented formula in every variant checked.

- `is_theory_gap`: **true**
- `is_cpp_bug`: **false**
- No `src/` file was modified; this report and its supporting renders are
  read-only diagnostics per the task's Phase-D2 read-only constraint.
- No §6 tolerance was touched (`AMPS_DB_TOL` stays ±3.0 dB).

---

## 1. The mechanism, in the model's own words

`src/dsp/ModalResonator.h`, `excite()`:

```cpp
// decay coefficient: reach -60dB (~0.001) after decayTime seconds
if (m.decayTime > 0.0f)
    m.decayCoeff = std::exp (-6.9078f / (m.decayTime * (float) sampleRate));
```

`processSample()` multiplies `currentAmp *= decayCoeff` once per sample, so
after `n = decayTime*sr` samples (`t = decayTime`), `currentAmp` has fallen
by `exp(-6.9078) ≈ 0.001` (-60 dB) — **by construction and by explicit
comment**, `decayTime` is a T60, and the closed-form envelope the C++ code
actually produces is:

```
amp(t) = amp0 * exp(-6.907755 * t / decayTime)        (ln(1000) = 6.907755..., matches the 6.9078f literal)
```

`tools/physics_verify.py`, `synth_theory_signal()` (the THEORY-only
windowed-synthesis predictor `judge_amps()` compares the render against):

```python
decay = m["decay"] if m["decay"] > 1e-9 else 1.0e9
x += amp * np.exp(-t / decay) * np.sin(2.0 * np.pi * m["freq"] * t)
```

This is `amp(t) = amp0 * exp(-t/decayTime)` — **missing the 6.907755
multiplier**. Both sides read the exact same `decayTime` number (straight
out of `--dump-modes`'s `"decay"` field, which is `ModalResonator::
getModes()`'s `m.decayTime` verbatim, unchanged since Experiment 1 of the
prior root-cause report) — the two formulas just disagree on what that
number *means*. The theory's envelope decays ~6.9× too slowly.

Because different partials generally have different `decayTime` values
(higher partials usually damp faster), this 6.9× rate error does **not**
cancel when partial *n* is expressed in dB relative to the fundamental (the
gate's own normalization): the fundamental and partial *n* pick up
different amounts of "extra" phantom energy from the too-slow theoretical
decay by the time the 20–520 ms measurement window is evaluated, and the
size of that mismatch scales with how different partial *n*'s `decayTime`
is from partial 1's.

---

## 2. Per-engine per-partial attribution table

`corrected-law` = same `synth_theory_signal()` pipeline, only the exponent
changed to `exp(-ln(1000)*t/decayTime)`; everything else (body_mag folded
in, full multi-string `strings` array, `measure_partials()` FFT pipeline)
identical to the current gate code. All numbers below are **directly
reproducible** by re-running `judge_amps()`'s own code path with that
one-line exponent substitution — no rendered audio was used to *derive* the
correction, only to *check* it (no-circularity rule respected: the fix
comes from `ModalResonator.h`'s own formula, not from fitting to audio).

| Engine | n | freq (Hz) | decayTime (s) | Gate-reported err (buggy theory) | err with corrected decay law | Stage attributed | Evidence |
|---|---|---|---|---|---|---|---|
| tongue_drum | 2 | 721.19 | 0.462 (vs p1=1.218) | **-12.60 dB** (FAIL) | **-0.06 dB** | decay-law exponent | closes to noise floor |
| tongue_drum | 3 | 1413.83 | 0.154 | -33.70 dB (below -45dB floor pre-fix; not gate-judged) | -0.19 dB | decay-law exponent | closes to noise floor |
| tongue_drum | 4/5 | 2337/3491 | 0.060/0.028 | already excluded, "weak <-45dB, not assessed" | not gate-relevant | n/a | see §4 caveat |
| cimbalom | 2 | 521.98 | 1.840 (vs p1=1.948) | -0.82 dB (PASS, informational) | -0.22 dB | decay-law exponent | small delta because decayTime p1≈p2 here |
| cimbalom | 3 | 783.58 | 1.695 | **-3.01 dB** (FAIL) | **-0.07 dB** | decay-law exponent | closes to noise floor |
| cimbalom | 4 | 1045.89 | 1.531 | **-4.52 dB** (FAIL) | **-0.07 dB** | decay-law exponent | closes to noise floor |
| cimbalom | 5 | 1309.16 | 1.364 | **-4.19 dB** (FAIL) | **-0.07 dB** | decay-law exponent | closes to noise floor |
| water_gong | 2 | 544.47 | 1.044 (vs p1=1.188) | -1.42 dB | -0.15 dB | decay-law exponent | closes to noise floor |
| water_gong | 3 | 893.20 | 0.833 | **-3.86 dB** (FAIL) | **-0.05 dB** | decay-law exponent | closes to noise floor |
| water_gong | 4 | 1018.53 | 0.760 | **-5.00 dB** (FAIL) | **-0.05 dB** | decay-law exponent | closes to noise floor |
| water_gong | 5 | 1306.87 | 0.612 | **-7.96 dB** (FAIL) | **-0.05 dB** | decay-law exponent | closes to noise floor |

The gate-reported numbers in column 4 match the CONTEXT-supplied residuals
essentially exactly (cimbalom p3/p4/p5 -3.0/-4.5/-4.2, water_gong p3/p4/p5
-3.9/-5.0/-8.0, tongue_drum p2 -12.60), confirming this reproduction is
measuring the same thing the gate measures.

---

## 3. Differential-rendering isolation (ruling out the other three candidate stages)

Ran the standard probe (MIDI 60, vel 0.85, dur 2 s, FX zero — mirrors
`render_probe()`) in normal / `--body-amount 0` / `--no-exciter-noise` /
`--num-strings 1` variants (and combinations), each measured through the
unmodified `measure_partials()` pipeline, each with its own matching
`--dump-modes` theory pulled through the *same* flags (RenderApp.cpp's
`extractDiagnosticOverrides()` applies identically to `--dump-modes` and to
a real render, so the "theory" side sees the same body_mag / string-count
state as the "actual" side in every variant — see
`src/cli/RenderApp.cpp:165`, `src/score/ScoreRenderer.h:88-92`).

**tongue_drum, partial 2 (721.19 Hz), buggy-theory error / corrected-law error:**

| Variant | buggy-theory err | corrected-law err |
|---|---|---|
| normal | -12.60 dB | -0.06 dB |
| `--body-amount 0` | -12.54 dB | 0.00 dB |
| `--no-exciter-noise` | -12.60 dB | -0.06 dB |
| `--body-amount 0 --no-exciter-noise` | -12.54 dB | 0.00 dB |

Bypassing BodyResonance entirely moves the error by <0.1 dB; disabling the
exciter noise burst moves it by **0.00 dB (bit-identical)**. Neither stage
is a contributor — `body_mag` was already correctly folded into the theory
by the prior fix, and the exciter noise transient (a broadband burst that
decays within a few ms per `Envelope::ExpDecay`, confirmed dead long before
the 20 ms measurement window starts) never touches a modal partial's
amplitude. In every variant, only the decay-law correction closes the gap.

**cimbalom, all 4 judged partials, buggy-theory error / corrected-law error:**

| Variant | n=2 | n=3 | n=4 | n=5 |
|---|---|---|---|---|
| normal (buggy / corrected) | -0.82 / -0.22 | -3.01 / -0.07 | -4.52 / -0.07 | -4.19 / -0.07 |
| `--body-amount 0` (buggy / corrected) | -0.58 / +0.01 | -2.94 / +0.01 | -4.44 / 0.00 | -4.12 / +0.01 |
| `--num-strings 1` (buggy / corrected) | -0.46 / -0.09 | -0.95 / -0.03 | -1.70 / -0.03 | -2.63 / -0.03 |
| `--num-strings 1 --body-amount 0` (buggy / corrected) | -0.36 / 0.00 | -0.92 / 0.00 | -1.67 / 0.00 | -2.59 / 0.00 |

Removing BodyResonance (`--body-amount 0`) barely changes the buggy-theory
error (already modeled correctly via `body_mag`). Removing multi-string
beating (`--num-strings 1`) *does* shrink the buggy-theory error somewhat
(the un-fixed decay-law error scales with how much of the modal energy the
partial carries, and single-string vs. 3-string changes the per-partial
`amp`/decayTime slightly) — but a clear residual survives even with beating
removed (-0.36 to -2.63 dB), and that residual, too, is fully closed
(≤0.09 dB) purely by the decay-law exponent fix. Beating is a real,
already-correctly-modeled physical effect (confirmed in the prior
root-cause report); it is not the source of the *remaining* gate failures.

**water_gong** (same `ChromaticEngine`/`BodyResonance` path as tongue_drum):
`--body-amount 0` moves p3/p4/p5's buggy-theory error by <0.1 dB
(-3.86→-3.81, -5.00→-4.94, -7.96→-7.91) and `--no-exciter-noise` moves it by
**0.00 dB** (bit-identical) — same pattern as tongue_drum. Corrected-law
error is ≤0.15 dB in both variants.

**Conclusion of the isolation experiment:** BodyResonance, exciter noise,
and string-count/beating were each independently toggled off; in no case
did any of them meaningfully change the residual. The decay-law exponent
fix is the only intervention tested that closes the gap, and it does so
**in every variant, independent of the other three stages** — i.e. it is
necessary and sufficient.

---

## 4. Caveat: tongue_drum partials 4/5 (not gate-relevant)

Partials 4/5 of tongue_drum sit at -106…-108 dB actual level, already below
`AMPS_WEAK_DB = -45.0` and excluded from judgment by `judge_amps()`'s own
"weak, not assessed" rule both before and after this fix. With the
corrected decay law, the *theory* side for partials 4/5 (and to a lesser
extent partial 3, whose buggy-theory error of -33.70 dB was likewise
already outside the ±3 dB window and not gate-judged) swings to large
*positive* deltas (+6 to +47 dB) because the theory-predicted level falls
to a physically-implausible near-zero value (`exp(-6.9*0.27/0.028)` for a
28 ms T60 partial evaluated near the window's ~270 ms effective center is
astronomically small) while the FFT's spectral-leakage/zero-padding noise
floor puts a lower bound on what `measure_partials()` can report for either
signal. This is a **numerical-floor artifact of comparing two
already-negligible quantities**, not a new discrepancy needing
explanation — both `judge_amps()` before and after this fix correctly
exclude these partials from the pass/fail verdict via the existing
`AMPS_WEAK_DB` gate, so no change to that logic is implied.

---

## 5. Why this is a THEORY gap, not a C++ bug

- The C++ decay recursion (`ModalResonator::excite()`/`processSample()`) is
  **self-consistent and documented**: its own comment states the intended
  semantics ("reach -60dB ... after decayTime seconds"), and every
  differential render in §3 confirms the actual rendered audio matches that
  documented formula to within measurement noise (≤0.22 dB, often
  ≤0.07 dB) — there is no version of the render, with any combination of
  body/exciter/string-count toggles, where the C++ output disagrees with
  its own `decayCoeff` formula.
- The defect is entirely inside `tools/physics_verify.py`'s
  `synth_theory_signal()` (a verification-harness script, not part of the
  render contract in `src/`): it re-derives an envelope from the
  `--dump-modes` JSON's `decay` field but uses the wrong scale constant
  (implicitly assuming decay-time semantics of τ = 1/e time, rather than
  reading the value as the T60 that `ModalResonator.h` defines and
  documents it to be).
- No `src/` file needed to change to close the gap (task's read-only
  constraint honored) — this is a pure prediction-side fix, matching the
  DELIVERABLE's "THEORY extension (documented linear stage the prediction
  must include)" category exactly: the linear stage in question is
  `ModalResonator`'s own T60-scaled exponential decay, which the predictor
  must use verbatim instead of a bare `exp(-t/decay)`.

## 6. Recommended fix (not applied — read-only phase)

In `tools/physics_verify.py`, `synth_theory_signal()`:

```python
LN1000 = 6.907755278982137   # ln(1000): ModalResonator::excite()'s hard-coded
                              # -6.9078f constant, i.e. decay is defined by the
                              # model itself as T60 (time to -60dB), not tau.
...
x += amp * np.exp(-LN1000 * t / decay) * np.sin(2.0 * np.pi * m["freq"] * t)
```

This is a one-line, single-constant correction that aligns the diagnostic
predictor with math `ModalResonator.h` already implements and documents; it
does not touch `AMPS_DB_TOL` (§6, stays ±3.0 dB) and does not change any
`src/` render code, so no before/after audio report is required (§1 rule
10 — rendered audio is byte-identical; only the Python-side "theory" number
changes). Expected effect on the gate: cimbalom p3/p4/p5, water_gong
p3/p4/p5, and tongue_drum p2 all move from FAIL to PASS (errors of
≤0.22 dB, comfortably inside ±3.0 dB); no partial that currently PASSes is
expected to newly FAIL (cimbalom/piano p2 error shrinks further, from
-0.82 dB to -0.22 dB).

---

## Tooling used (read-only; no `src/` file modified)

- `tools/physics_verify.py`'s own `find_cli()`, `dump_modes_event()`,
  `measure_partials()`, `read_wav_mono()`, `synth_theory_signal()` reused
  verbatim (imported, not re-implemented) for every measurement in this
  report.
- CLI diagnostic flags exercised: `--body-amount 0`, `--no-exciter-noise`,
  `--num-strings 1` (and combinations), on top of `TsukiSynthCLI.exe`
  rebuilt 2026-07-09 00:17 (post-dates the flags' addition to
  `src/cli/RenderApp.cpp`/`src/dsp/DiagnosticOverrides.h`, confirmed via
  `--help` listing the three flags).
- Scratch scripts (temp scratchpad dir, not part of the repo):
  `decay_law_test.py`, `diff_render.py`, `dump_test.py`.
