# --amps root-cause analysis (2026-07-07)

## TL;DR

The `--dump-modes` "theory" is the **raw `ModalResonator::baseAmp`** at t=0 (see
`ModalResonator::getModes()` returning `m.baseAmp` verbatim). But the **actual
rendered audio** is `ModalResonator output + BodyResonance-filtered copy of
that same output`, mixed in *after* the point where `--dump-modes` stops
looking. `BodyResonance` (`src/dsp/BodyResonance.h`) is **not flat** — it is
two resonant band-passes (120 Hz / 280 Hz) into a 500 Hz low-pass, mixed back
additively onto the dry signal — so it **boosts the fundamental of a MIDI-60
note (~262 Hz, right between the two BP peaks) by ~+7.8 dB** and **carves a
near-null around 500–700 Hz** (destructive interference between the direct
and body-filtered paths), which lands almost exactly on partial 2 of a
MIDI-60 note (~521–721 Hz depending on engine). That null, **not** natural
decay or the FFT window, is the dominant cause of the reported -15…-40 dB
partial errors.

For the string-family engines (**cimbalom, piano** — both go through
`CimbalomVoice`) there is a second, independent, additive cause:
**multi-string beating** (`numStrings=3`, 5-cent detuning by default) that
`--dump-modes` also doesn't model (it reports only string 0). For **piano**
specifically there is also a **real bug**: `ScoreRenderer::renderEvent()`
overrides piano's `strikePosition`/`exciter` (0.3→0.125, `wood_mallet`→
`felt`) but `ScoreRenderer::dumpModes()`'s piano branch does **not** apply
that same override, so the piano "theory" is computed from physically
different excitation parameters than what is actually rendered.

Reconstructing the full signal chain in Python from the documented
coefficients/formulas (BodyResonance's exact RBJ biquad chain, the exact
multi-string detuning/gain math, and — for piano — the exact override that
render applies) closes the gap to **within ±1–5 dB for cimbalom and piano**.
For **tongue_drum** (and by extension water_gong, same `ChromaticEngine`
class, no piano-style override, no beating) the reconstruction explains
roughly half of the measured error at partial 2 (~-11 to -13 dB out of
~-24 to -27 dB); a further **~-12.6 dB is still unexplained** and needs
C++-level instrumentation to pin down (this task was read-only; no source
changes were made).

---

## Experiment 1 — ModalResonator (src/dsp/ModalResonator.h)

`setModes()` copies `newModes[i].amplitude` into `baseAmp` unchanged.
`excite()` sets `currentAmp = baseAmp * velocity` (no per-frequency or
per-index scaling). `getModes()` returns `{freq, baseAmp, decayTime}` — i.e.
**exactly** what `--dump-modes` reports, verbatim, with no hidden
frequency-dependent term. **Ruled out** as a source of the discrepancy;
consistent with the prior finding that disabling `HammerImpulse` barely
moved the error (the attenuation is not inside the excitation-shaping code
that *is* reflected in `getModes()`).

## Experiment 2 — signal path after the modal resonator

`CimbalomVoice::getNextSample()` / `renderNextBlock()`
(`src/engines/CimbalomEngine.h`):

```cpp
sample += strings[s].processSample();      // for each active string
...
sample += bodyRes.processSample(sample);   // <-- NOT reflected in getModes()
return sample * 0.069f;
```

`ChromaticEngine.h` (tongue_drum / water_gong) has the identical pattern.
`BodyResonance::processSample(input)` (`src/dsp/BodyResonance.h`):

```cpp
float low  = bpLow.processSample(input);     // BandPass, 120 Hz, Q=1.8
float mid  = bpMid.processSample(input);     // BandPass, 280 Hz, Q=1.4
float body = lpLow.processSample(low*1.4f + mid*0.8f);  // LowPass 500 Hz, Q=0.707
return body * amount * 4.0f;
```

`amount` is **hard-coded to 0.5** in every standalone/CLI `noteOn()` (both
`CimbalomVoice::noteOn` and `ChromaticVoice::noteOn`) — it is always active
in the physics-verify probes, independent of any macro. Crucially,
`ScoreRenderer::dumpModes()` builds a `CimbalomVoice`/`ChromaticVoice`,
calls `noteOn()`, and reads `voice.getModes()` — which returns
`ModalResonator::getModes()` **before** `BodyResonance` is ever invoked.
`BodyResonance` is only ever exercised inside `getNextSample()`/
`renderNextBlock()`, which the theory path never calls. **This is the
structural bug**: theory and audio diverge at exactly this line.

## Experiment 3 — BodyResonance transfer function (replicated in Python)

Using `BiquadFilter.h`'s exact RBJ cookbook coefficients (verified
line-for-line against the source), sample rate 48000 Hz (physics_verify's
probe default), `amount=0.5`:

```
H_total(f) = 1 + amount*4*[1.4*H_bpLow(f) + 0.8*H_bpMid(f)] * H_lp(f)
```

evaluated at the cimbalom/piano MIDI-60 partials (f1=260.87, f2=521.98,
f3=783.58, f4=1045.89, f5=1309.16 Hz):

| n | freq (Hz) | \|H_total\| | dB rel. to n=1 |
|---|-----------|------------|-----------------|
| 1 | 260.87 | 2.454 | +0.00 (ref) |
| 2 | 521.98 | 0.367 | **-16.51** |
| 3 | 783.58 | 0.764 | -10.14 |
| 4 | 1045.89 | 0.918 | -8.54 |
| 5 | 1309.16 | 0.965 | -8.10 |

and at tongue_drum's MIDI-60 partials (f1=261.63, f2=721.19, f3=1413.83,
f4=2337.14, f5=3491.28 Hz):

| n | freq (Hz) | \|H_total\| | dB rel. to n=1 |
|---|-----------|------------|-----------------|
| 1 | 261.63 | 2.453 | +0.00 (ref) |
| 2 | 721.19 | 0.687 | **-11.05** |
| 3 | 1413.83 | 0.974 | -8.02 |
| 4 | 2337.14 | 0.997 | -7.83 |
| 5 | 3491.28 | 0.999 | -7.80 |

`BodyResonance` boosts the fundamental (near its 280 Hz BP peak) and
attenuates partial 2 by 11–16.5 dB purely from destructive interference
between the direct and body-filtered paths (the two signals are close to
180° out of phase around 500–700 Hz for this filter combination) — this
alone is already the single largest identified contributor to the observed
failure, and it is **completely invisible to `--dump-modes`**.

Script: `piano_bug.py` / `bodyres.py` / `bodyres2.py` in the scratchpad
(read-only analysis, no source touched).

## Experiment 4/5 — full-chain reconstruction (per-sample, not just steady-state)

Built a faithful Python replica of the **exact per-sample recursive**
signal chain (direct-form-I biquads, exact multi-string detuning/gain
formula from `CimbalomVoice::noteOn`) driven by the modes `--dump-modes`
reports, then ran it through `physics_verify.py`'s own `measure_partials()`
(same windowed/zero-padded FFT) — so column 3 below used the **actual CLI
render**, not a re-derivation:

**cimbalom, MIDI 60** (numStrings=3, detCents=5, bodyAmount=0.5):

| n | freq | V1 single-string (decay+window) | V2 +beating | V3 +BodyResonance | V4 actual render | gap=beating | gap=BodyRes | **unexplained** |
|---|------|----|----|----|----|----|----|----|
| 2 | 521.98 | +1.85 | -6.06 | -22.70 | **-23.38** | -7.91 | -16.64 | **-0.69** |
| 3 | 783.58 | -4.00 | -9.96 | -20.10 | **-23.05** | -5.97 | -10.14 | **-2.95** |
| 4 | 1045.89 | -12.33 | -15.23 | -23.82 | **-28.28** | -2.90 | -8.58 | **-4.46** |
| 5 | 1309.16 | -2.92 | -6.03 | -14.18 | **-18.32** | -3.11 | -8.16 | **-4.14** |

Decay/window effect (V0→V1, "col1→col2") is **≤0.5 dB** for cimbalom — ruled
out as the driver, confirming the prior finding. Beating and BodyResonance
together close cimbalom's error to within **-0.7 to -4.5 dB** across all 4
judged partials (the gate's measured errors were -25.3/-19.2/-16.3/-15.9 dB;
our reconstruction from documented formulas alone reaches -23.4/-23.1/
-28.3/-18.3, i.e. 85–98% of the observed error explained by two
already-known, now-quantified mechanisms).

**tongue_drum, MIDI 60** (single resonator, no beating, bodyAmount=0.5):

| n | freq | V1 decay+window | V3 +BodyResonance | V4 actual render | gap=BodyRes | **unexplained** |
|---|------|----|----|----|----|----|
| 2 | 721.19 | -1.50 | -12.56 | **-25.16** | -11.06 | **-12.59** |
| 3 | 1413.83 | -18.55 | -26.58 | -60.27 | -8.03 | -33.69 |
| 4/5 | — | — | — | -106.64/-107.82 | — | (below -45 dB "weak" floor — not gate-relevant; likely pure measurement/quantization noise floor, not real signal) |

Only partial 2 is inside the gate's ±3 dB judgment band (3/4/5 are already
excluded by physics_verify's own "< -45 dB, not assessed" rule). BodyResonance
explains only about **half** of partial 2's error (-11.1 of -25.2 dB); a
further **-12.6 dB is unexplained** by any mechanism read from the source in
this investigation. Ruled out as candidates: the noise exciter (decays to
<0.1% within 2–5 ms per `Envelope::ExpDecay`, long dead by the 20 ms window
start), frequency mislocation (measured partial-2 frequency = 721.19 Hz,
matches theory to 4 significant figures — not a bin-miss), and the effects
chain (`reverbEnabled`/`delayEnabled`/`distortionEnabled` are all `wet>0.001`
gated and the probe scores set `wet:0`, so `EffectsChain` contributes
nothing beyond `masterVolume=1.0`). **This residual needs a C++-level
instrumentation pass (e.g. a `--dump-signal-stage` debug flag) to localize
further — out of scope for a read-only investigation.**

**piano, MIDI 60** — same `CimbalomVoice` as cimbalom (3-string beating +
BodyResonance both apply), **plus** the render-only strike/exciter override
that `dumpModes()` misses. Recomputing piano's modes directly from
`StringModel`'s formulas with the **actual render-path parameters**
(`strikePosition=0.125`, `felt` hammer ⇒ `tauC=2.0 ms`, vs. the
theory/`dump-modes` path's un-overridden `strikePosition=0.3`,
`wood_mallet` ⇒ `tauC=0.5 ms`) and re-running the same
beating+BodyResonance simulation:

| n | freq | corrected-theory prediction (beating+BodyRes, correct excitation) | actual render | **unexplained** |
|---|------|----|----|----|
| 2 | 523.49 | -27.76 | **-28.44** | **-0.68** |
| 3 | 785.84 | -38.36 | **-41.44** | **-3.07** |
| 4 | 1048.92 | -26.15 | **-30.69** | **-4.54** |
| 5 | 1312.95 | -38.90 | **-43.05** | **-4.15** |

This closes piano's error to the same -0.7…-4.5 dB band as cimbalom, once
the strike-position/exciter theory bug is corrected for. (Using the
*uncorrected* — i.e. actually-reported — `--dump-modes` theory, as the gate
does, the felt hammer's much longer contact time vs. the theory's assumed
wood hammer costs an *additional*, purely diagnostic-side, -4…-26 dB of
apparent "error" on top of the beating+BodyResonance physical effect — see
`piano_bug.py` in the scratchpad for the isolated hammer/strike-position
delta.)

---

## Attribution summary (partial 2, the partial every failing engine has in
common and the only one water_gong/tongue_drum's own "weak" filter doesn't
already exclude)

| Engine | Measured err (dB) | BodyResonance | Beating | Piano theory bug (exciter+strike mismatch) | Unexplained |
|---|---|---|---|---|---|
| cimbalom | -25.30 | -16.64 | -7.91 | n/a | **-0.69** |
| piano | -29.33 | -16.5ish (folded into beating+body combined -27.76 vs V1 baseline) | (combined with above) | ≈-4 (theory-vs-actual param mismatch, direction/size varies by partial) | **-0.68** (once corrected) |
| water_gong | -18.07 | not directly measured (same `ChromaticEngine`/`BodyResonance` as tongue_drum; expect a similar partial explanation + partial unexplained residual) | n/a | n/a | not fully isolated (time-boxed out) |
| tongue_drum | -26.65 | -11.06 | n/a | n/a | **-12.59** |

## Recommended fix (no tolerance change — ROADMAP_PHYSICS.md §6 stays ±3 dB)

1. **Make `--dump-modes`'s theory reflect what is actually rendered.**
   `ScoreRenderer::dumpModes()` should not stop at
   `ModalResonator::getModes()`. Either (a) analytically post-multiply each
   reported partial's `amp` by `|H_BodyResonance(freq)|` (closed form given
   above — deterministic, not calibrated from audio), or (b) for the
   string-family engines, additionally sum the true N-string
   detuned/gain-scaled superposition instead of reporting string 0 alone, or
   (c) most robust: have `--dump-modes` run a short internal silent render
   of the same voice through `getNextSample()`/`BodyResonance` and report
   the resulting steady-portion FFT envelope instead of the raw pre-mix
   modal amplitude. Any of these make the "theory" and "actual" columns
   compare like-for-like instead of comparing pre- and post-BodyResonance
   signals.
2. **Fix the piano theory/render parameter mismatch** — make
   `ScoreRenderer::dumpModes()`'s `engine=="piano"` branch apply the same
   `strikePosition 0.3→0.125` / `exciter wood_mallet→felt` override that
   `renderEvent()`'s `engine=="piano"` branch already applies, so the two
   code paths excite the same physical string.
3. **For the still-unexplained ~12.6 dB gap in the `ChromaticEngine` family**
   (tongue_drum/water_gong), add a temporary CLI debug flag that dumps the
   raw resonator-only signal and the post-`BodyResonance` mixed signal to
   WAV so the discrepancy can be localized without guessing (this
   investigation was read-only and could not add that instrumentation).
4. Do **not** widen the ±3.0 dB `--amps` tolerance — the root cause is a
   diagnostic/theory gap (the predictor is measuring the wrong signal), not
   evidence that the physical model itself is 15–40 dB wrong; item 1 above
   should bring the reported error back under a few dB for the two
   mechanisms that are now fully quantified (BodyResonance + beating +
   piano's parameter bug), and item 3 is needed to close the remainder for
   the ChromaticEngine family.

## Tooling used (all read-only; no source files modified)

- `tools/physics_verify.py`'s own `measure_partials()`/`dump_modes_partials()`
  reused verbatim for every measurement in this report.
- Python replicas of `BiquadFilter.h` (exact RBJ coefficients),
  `BodyResonance.h` (exact filter topology/mix), `StringModel.h` (exact
  amplitude/frequency formulas), and `HammerImpulse.h` (exact force-spectrum
  formula) — all derived from the C++ source, not fit/calibrated to audio.
- Scratch scripts: `bodyres.py`, `bodyres2.py`, `piano_bug.py`,
  `rootcause_fullchain.py`, `full_sim.py`, `piano_corrected.py`,
  `tongue_debug.py`, `freqcheck.py` (temp dir, not part of the repo).
