# M1-1d Velocity Linearity Fix — Before / After Report

Date: 2026-07-05
Scope: modal engines (cimbalom, tongue_drum, water_gong, water_gong_free, piano).
FM Piano untouched (exempt per ROADMAP_PHYSICS.md §1g — FM index also scales with
velocity, not a pure amplitude law).

## Root cause

`BodyResonance::processSample()` (`src/dsp/BodyResonance.h`) drove its resonant
bandpass filters with the engine's raw sample (already ∝ velocity via
`ModalResonator::excite()`), but then **also** multiplied the filtered output by
a separate envelope follower (`envLevel`) that tracked `|input|` — itself ∝
velocity. Two multiplicative velocity-proportional factors compounded into a
`velocity²` term in the body-resonance contribution, which is summed into the
final output (`sample += bodyRes.processSample(sample)`). The resonator itself
(confirmed by isolated simulation from `--dump-modes` ground truth and by a
zeroed-`amount` rebuild) was already perfectly linear (+6.02 dB per ×2
velocity). Isolating `bodyRes.setAmount(0.0f)` in a debug rebuild reproduced
exactly +6.02 dB at every MIDI note tested (40/50/60/70/80), confirming
`BodyResonance` — used identically by `CimbalomEngine.h` and
`ChromaticEngine.h` — as the sole source of the superlinearity. `water_gong_free`
passed pre-fix only because it has fewer/weaker modes (7 vs. clamped
water_gong's 12), so its bodyRes contribution was proportionally small enough
to stay inside the ±1.0 dB window.

## Fix

`src/dsp/BodyResonance.h`: removed the `envLevel` envelope-follower and its
multiplication; the resonant bandpass filters alone (already linear and driven
sample-by-sample by the decaying, velocity-proportional input) are the
sufficient body-resonance model. Physical basis: a passive resonant body
(soundboard) is a linear system in the small-signal regime — output amplitude
∝ driving force (F = m·a).

`src/engines/CimbalomEngine.h` / `src/engines/ChromaticEngine.h`: re-anchored
the fixed per-engine output-gain constants (see below) since removing the v²
term changed each engine's absolute level at the equal-RMS calibration
reference (vel = 0.85, MIDI 60, per the 2026-06 calibration methodology in
DEVLOG.md).

## (a) Velocity judgment table — before / after

Harness: `python tools/physics_verify.py --full`, vel 0.378 → 0.756 (MIDI vel
48/127 → 96/127, exact ×2), MIDI 60, expect +6.0 ±1.0 dB RMS.

| engine | rms_lo (before) | rms_hi (before) | Δ (before) | verdict (before) | rms_lo (after) | rms_hi (after) | Δ (after) | verdict (after) |
|---|---|---|---|---|---|---|---|---|
| cimbalom | -35.7 | -26.3 | +9.5 dB | **FAIL** | -35.0 | -29.0 | **+6.0 dB** | **PASS** |
| tongue_drum | -34.4 | -26.7 | +7.7 dB | **FAIL** | -32.3 | -26.3 | **+6.0 dB** | **PASS** |
| water_gong | -35.5 | -27.6 | +7.9 dB | **FAIL** | -33.1 | -27.1 | **+6.0 dB** | **PASS** |
| water_gong_free | -38.1 | -32.1 | +6.0 dB | PASS | -38.1 | -32.1 | +6.0 dB | PASS (unchanged) |
| fm | -34.0 | -28.1 | +5.9 dB | EXEMPT | -34.0 | -28.1 | +5.9 dB | EXEMPT (untouched) |
| piano | -40.1 | -32.4 | +7.7 dB | **FAIL** | -39.4 | -33.3 | **+6.0 dB** | **PASS** |

Full gate: `reports/gate_outputs/full_BEFORE_velocity_fix.txt` → 1d FAIL,
`reports/gate_outputs/full_AFTER_velocity_fix.txt` → 1d PASS (1b/1c also PASS,
unaffected by this change).

Cross-engine equal-RMS re-anchoring (vel=0.85, MIDI 60, `--levels`):

| engine | rms dBFS (pre-fix, gain unchanged) | rms dBFS (post-fix, gain re-anchored) | gain constant before → after |
|---|---|---|---|
| cimbalom | -24.5 | -27.9 | `0.070f` → `0.069f` (peak-headroom limited, see note) |
| tongue_drum | -25.3 | -25.2 | `0.255f` → `0.196f` |
| water_gong / water_gong_free (shared) | -26.1 / -31.0 | -26.0 / -31.1 | `0.163f` → `0.151f` |
| piano (shares cimbalom's gain) | -30.9 | -32.3 | (same constant as cimbalom) |

Note on cimbalom/piano: they share one `CimbalomVoice` gain constant. An exact
RMS-only re-anchor for cimbalom would push its single-note peak to 0.0 dBFS at
vel=0.85 (and above `verify_score.py`'s registered `PEAK_LIMIT_DBFS = -0.3` at
vel=1.0) — a real clipping regression I will not introduce. The constant
(`0.069f`) instead restores cimbalom's original peak headroom (-2.0 dBFS @
vel=0.85, matching pre-fix exactly), which keeps piano's RMS within ~1.4 dB of
its pre-fix value. This is disclosed rather than silently accepted as an
".2 dB" pass — the peak-safety constraint took priority over exact RMS-match
for this one shared-gain pair.

## Independent second-pair verification (not the harness's 48/96 point)

To confirm the fix produces a genuinely linear curve rather than a fit to the
single 0.378→0.756 calibration point, a throwaway scratchpad script (not
committed to the repo) re-measured velocity doubling at three unrelated pairs
for all five modal engines:

| engine | vel 0.2→0.4 | vel 0.4→0.8 | vel 0.3→0.6 |
|---|---|---|---|
| cimbalom | +6.02 dB | +6.02 dB | +6.02 dB |
| tongue_drum | +6.02 dB | +6.02 dB | +6.02 dB |
| water_gong | +6.02 dB | +6.02 dB | +6.02 dB |
| water_gong_free | +6.03 dB | +6.02 dB | +6.02 dB |
| piano | +6.02 dB | +6.02 dB | +6.02 dB |

Every engine holds to +6.02 dB (theoretical ideal: 20·log10(2) = 6.0206 dB)
at every tested point on the curve, confirming the fix is a true linear law,
not a single-point coincidence.

## (b) Whole-score render comparison (3 example scores, before vs. after)

Rendered with the CLI before/after the fix (before-reference binaries were
built via a temporary `git stash` of the 3 changed files, rendered, then
restored — no unstaged change was lost). Scores use `"normalize": true`, so
final export peak is pinned to -0.45 dBFS (0.95 linear) in both cases by
design; RMS reflects the internal dynamic balance shift.

| score | engine(s) | rms before | rms after | Δrms | peak before | peak after | Δpeak |
|---|---|---|---|---|---|---|---|
| `physical_piano.score.json` | piano (cimbalom path) | -29.06 dBFS | -30.06 dBFS | -1.00 dB | -0.45 dBFS | -0.45 dBFS | 0.00 dB |
| `moonlight_sonata_movement1_tongue_drum.score.json` | tongue_drum (1142 events) | -22.22 dBFS | -18.41 dBFS | +3.81 dB | -0.45 dBFS | -0.45 dBFS | 0.00 dB |
| `water_gong_clamped.score.json` | water_gong (clamped) | -25.12 dBFS | -24.60 dBFS | +0.52 dB | -0.45 dBFS | -0.45 dBFS | 0.00 dB |

Peak is unchanged (both hit the `normalize` ceiling as intended). The
moonlight tongue_drum piece's +3.8 dB RMS shift is the piece with the most
overlapping/dense notes, where the old v²-in-velocity bug most strongly
suppressed the RMS of quieter passages relative to the loudest struck notes
(the bug amplified loud notes' body-resonance far more than soft ones); the
fix makes the piece's overall energy more consistent with the intended
amplitude-proportional-to-velocity law, which raises average RMS once peak
is renormalized to the same ceiling. This is expected and is not a leftover
defect — it is exactly the physical correction the fix targets.

Before-fix reference WAVs (for audition) are in the session scratchpad
(not committed): `before_wav/physical_piano.wav`,
`before_wav/moonlight_sonata_i_tongue_drum.wav`,
`before_wav/water_gong_clamped.wav`.

## (c) Timbre impact

Velocity no longer changes brightness, noise level, or partial count — only
overall loudness (as required: "velocity 只允許線性縮放激發力"). Timbral
brightness is now controlled solely by `hardness`/exciter-type parameters
(cutoff frequency, noise-burst duration) as before; those paths were already
velocity-independent and were not touched. The only audible difference vs.
before is that hitting harder no longer makes the instrument's body resonance
disproportionately louder/boomier relative to the string/plate tone — body
resonance now tracks the same linear velocity law as the rest of the voice.
