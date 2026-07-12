# Materials Physicalization — Sourced Proposal (Research Only, No Value Changes)

Status: **research/derivation only**. Nothing in `data/materials.json` or any `src/` file was
changed while writing this. This is the input document for the 月月/Opus keep-or-revert review
gate before any Rule 10 (before/after + full corpus re-render) work begins.

Scope: (1) the damping triple (`alpha`/`beta_air`/`gamma_radiation`), all 14 materials; (2) the
one flagged Young's-modulus value (`rubber`). `beta_air`/`gamma_radiation` themselves are **not**
re-derived — no per-material literature source exists for them (see §4), so they are proposed to
stay exactly as-is.

---

## 1. The damping-model mapping (load-bearing derivation)

### 1.1 What the code actually does

Confirmed by reading `src/dsp/ModalResonator.h:66-70` (`excite()`):

```cpp
if (m.decayTime > 0.0f)
    m.decayCoeff = std::exp (-6.9078f / (m.decayTime * (float) sampleRate));
```

`decayCoeff` is applied once per sample to the mode's amplitude. After `decayTime` seconds the
amplitude has been multiplied by `exp(-6.9078) = 0.001`, i.e. **-60 dB**. So the `decayTime` field
that the physics models hand to `ModalResonator` is, by construction, a literal **T60** (time for
that mode's *amplitude* — not energy — to fall 60 dB), not a generic "decay constant."

Each physics model computes `decayTime = 1 / decayDenom` per mode, with `decayDenom` built from
the material's damping triple and that mode's frequency `f`:

| model | file:line | `decayDenom` formula |
|---|---|---|
| StringModel (Cimbalom) | `StringModel.h:82` | `alpha + beta*f² + gamma*f` |
| PlateModel (Water Gong) | `PlateModel.h:139` | `alpha + beta*f² + gamma*f` |
| BeamModel (Tongue Drum) | `BeamModel.h:88` | `alpha*2 + beta*f² + gamma*f` |

So **T60(f) = 1 / (alpha_term + beta_air·f² + gamma_radiation·f)**, where `alpha_term = alpha`
for String/Plate and `alpha_term = 2·alpha` for Beam. The `*2` in `BeamModel.h` is an existing,
already-documented, intentional per-engine weighting (`BeamModel.h:87`: "梁比弦衰減快,damping
加權" — "beam decays faster than string, damping-weighted") — **not** something this task changes
or needs to fix, but it does mean the single `alpha` number in `materials.json` produces a
**2x shorter** T60 contribution in the Beam engine than in String/Plate for the identical value.
Any eta→alpha mapping inherits that asymmetry; it is reported per-model below rather than
"corrected," which would be an out-of-scope model-structure change (Rule 2/frozen tolerances).

This is a **Rayleigh-type split**: `alpha` ~ frequency-independent internal friction, `beta·f²` ~
viscous air drag (grows with f²), `gamma·f` ~ acoustic radiation loss (grows ~linearly with f),
consistent with Fletcher & Rossing, *Principles of Vibration and Sound*, ch. 2. This qualitative
model was already validated in `docs/MATERIALS_SOURCES.md` and is unchanged here.

### 1.2 The literature side: loss factor eta -> Q -> T60

Standard relation (cited per task instruction, re-derived here step-by-step so it's checkable):

- Loss factor `eta` (dimensionless, material internal friction) relates to modal quality factor by
  **Q = 1/eta**.
- For a linear damped oscillator/mode with quality factor Q at frequency f, the **energy** decay
  time constant is `tau_E = Q / (2*pi*f)` (definition of Q as `2*pi * energy-stored /
  energy-lost-per-cycle`).
- **Amplitude** (not energy) decays as `exp(-t / tau_amp)` with `tau_amp = 2*tau_E` (energy ~
  amplitude²), so `tau_amp = Q / (pi*f)`.
- T60 is defined here as amplitude falling to 0.1% (`-60 dB` = `20*log10(0.001)`), i.e.
  `exp(-T60/tau_amp) = 0.001` => `T60 = tau_amp * ln(1000) = tau_amp * 6.9078`.
- Substituting: **T60 = 6.9078 * Q / (pi*f) = (6.9078/pi) * Q/f ≈ 2.1996 * Q/f ≈ 2.2 * Q/f**.
- With `Q = 1/eta`: **T60 ≈ 2.2 / (f * eta)** — matches the task's stated standard relation
  exactly, and matches the engine's own `-6.9078`/`-60dB` convention (`ModalResonator.h:68`), so
  this T60 is the *same* T60 the engine already computes — no unit-convention mismatch.

### 1.3 Mapping eta to alpha

Treating `alpha_term` (`alpha` for String/Plate, `2*alpha` for Beam) as the model's stand-in for
the *internal-friction-only* contribution to `decayDenom` (i.e. evaluating the eta-based formula
with `beta`, `gamma` set to 0):

```
1 / alpha_term = 2.2 / (f * eta)   =>   alpha_term = eta * f / 2.2
```

**Critical caveat (must be flagged, not silently absorbed):** this makes the physically-correct
`alpha_term` a function of frequency `f`, but the engine's `alpha` is a single frequency-independent
scalar per material, shared across every note and every engine. A single number can only match
`eta*f/2.2` exactly at one frequency. Below that anchor frequency the fixed alpha *over-damps*
relative to what constant-eta physics predicts; above it, *under-damps*. This is an unavoidable
consequence of the existing frozen model shape (Rule 2: model structure is out of scope this
phase), not a new bug introduced by this proposal — but Opus/月月 should know the single-alpha
value is exact at exactly one note and only approximately right elsewhere.

**Anchor choice**: this proposal anchors at **MIDI 60 (middle C, f0 = 261.6256 Hz)**, i.e. the
same note item 5 uses for the impact table, so "alpha is literature-exact at this note" and "here
is what that implies at that note" are the same statement:

```
alpha_proposed = eta * 261.6256 / 2.2 = eta * 118.921     (String/Plate convention)
```

For Beam, the *same* `alpha` value (one number per material, shared across engines) yields
`alpha_term = 2*alpha`, i.e. Beam's alpha-only contribution is literature-exact at f = 523.25 Hz
(MIDI 72, one octave above the anchor) instead of MIDI 60 — a direct, documented consequence of
the existing `*2` weighting, not a new choice made here.

Which term is which, confirmed from the code (§1.1): `alpha` = internal friction (this section);
`beta_air` = air-drag term, `gamma_radiation` = radiation term (§4, kept as-is, no per-material
source available).

---

## 2. Literature eta values used (per material)

Sources: Fletcher & Rossing, *Principles of Vibration and Sound* / *The Physics of Musical
Instruments*, ch. 2 (loss-factor scaling, metal/wood/rubber qualitative ranges); Ashby, *Materials
Selection in Mechanical Design* (loss-coefficient vs. modulus chart — cast iron's damping capacity
is commonly tabulated at roughly one to two orders of magnitude above wrought steel/aluminum);
Lazan, *Damping of Materials and Members in Structural Mechanics* (specific damping capacity data
underlying the metals "order of magnitude above steel" claim for cast iron); Wegst, "Wood for
Sound," *American Journal of Botany* 93(10):1439-1448 (2006) — confirmed by direct web search in
this task: soundboard woods (spruce) are specifically chosen for **low** loss factor `tan δ`
relative to other tonewoods/hardwoods, "wood having higher Young's modulus (E) per specific
gravity and lower internal friction being suitable for soundboards" — this is the literature
support for the spruce-ordering fix in §5. Engineering elastomer/isolator loss-factor references
(patent/handbook literature retrieved this task, e.g. Hutchinson Aerospace & Industry damping
definitions sheet) confirm rubber/elastomer loss factors are enormously higher than any other
material class and strongly frequency/temperature dependent — no single number is defensible to
better than an order of magnitude, flagged accordingly.

No specific published numeric table could be pulled full-text in this session (ResearchGate/journal
paywalls returned 403 on direct fetch); the values below are the standard order-of-magnitude
ranges reproduced across this literature (and match the ranges given in the task brief itself),
not digitized from one single table. Every value is marked **推導(order-of-magnitude, 文獻方向)**
— defensible as "right order of magnitude, right qualitative family" but not a "read this exact
number off page N" citation. That is a strictly better sourcing state than the current **全部待溯源**
(ALL untraceable) status, but it is not "測量級" precision — flagged per material below.

| material | eta (chosen) | literature range used | confidence |
|---|---|---|---|
| aluminum | 1.0e-4 | ~1e-4 (metals, low end) | 推導(文獻量級) |
| steel | 2.0e-4 | ~1-6e-4 (carbon steel) | 推導(文獻量級) |
| bronze | 1.0e-3 | ~1-2e-3 (low end — bell-bronze reputation for long ring, keeps existing bronze<brass ordering that MATERIALS_SOURCES.md found "not contradicted") | 推導(文獻量級，排序判斷) |
| brass | 1.5e-3 | ~1-2e-3 (mid) | 推導(文獻量級) |
| copper | 2.0e-3 | ~1-2e-3 (high end — copper's known "dead"/high-internal-friction reputation vs. bronze/brass, consistent with MATERIALS_SOURCES.md's existing qualitative note) | 推導(文獻量級，排序判斷) |
| glass | 1.5e-3 | ~1-2e-3 (ordinary soda-lime glass, NOT fused-silica/quartz — see flag below) | 推導(文獻量級) |
| iron (cast) | 1.0e-2 | ~1-2 orders of magnitude above steel (Ashby/Lazan damping-capacity charts) | 推導(文獻方向明確，量級估計) |
| wood_spruce | 7.0e-3 | ~6-8e-3, LOW among woods (Wegst 2006) | 推導(文獻方向明確 — 這是修正 spruce 排序異常的關鍵值) |
| wood_maple | 1.2e-2 | ~1-2e-2 (hardwoods) | 推導(文獻量級，同組內部排序信心低) |
| wood_birch | 1.4e-2 | ~1-2e-2 | 推導(文獻量級，同組內部排序信心低) |
| wood_oak | 1.6e-2 | ~1-2e-2 | 推導(文獻量級，同組內部排序信心低) |
| bamboo | 1.0e-2 | ~1-2e-2 (grouped with hardwoods per task brief; no bamboo-specific number found) | 推導(文獻量級，信心較低) |
| nylon | 3.5e-2 | ~2-5e-2 | 推導(文獻量級) |
| rubber | 3.0e-1 | ~0.1-1 (huge, strongly f/T-dependent — single number is an order-of-magnitude placeholder only) | 推導(方向極確定,量級單一數字信心低) |

Not present in `data/materials.json` (no proposal needed): silver, stone/granite — mentioned in
the task brief as literature reference points, but the 14-material database has no such entries.

### 2.1 Confidence caveat for the wood group

Only the **spruce-vs-other-woods** split is well-supported by a named source (Wegst 2006,
confirmed this task). The *relative* ordering among maple/birch/oak/bamboo (all placed in the
task's own "~1-2e-2" bracket) is **not** independently sourced here — differentiating
1.2e-2/1.4e-2/1.6e-2/1.0e-2 among them is a placeholder spread within one literature bracket, not
four separately-cited numbers. If 月月/Opus wants that internal ordering defensible, it needs a
follow-up literature pass (e.g. a luthier-oriented wood damping table); as proposed here, treat
those four as "same order of magnitude, spruce clearly lower" and nothing more precise.

---

## 3. Converted alpha values (String/Plate convention, anchor = MIDI 60, f0 = 261.6256 Hz)

`alpha_proposed = eta * 261.6256 / 2.2 = eta * 118.921`

| material | alpha (old, 待溯源) | alpha (proposed) | change |
|---|---|---|---|
| aluminum | 0.30 | **0.0119** | ÷25 |
| steel | 0.50 | **0.0238** | ÷21 |
| bronze | 0.80 | **0.1189** | ÷6.7 |
| brass | 1.00 | **0.1784** | ÷5.6 |
| copper | 1.20 | **0.2378** | ÷5.0 |
| glass | 0.15 | **0.1784** | x1.2 |
| iron (cast) | 1.50 | **1.1892** | ÷1.3 |
| wood_spruce | 8.00 | **0.8324** | ÷9.6 |
| wood_maple | 6.50 | **1.4271** | ÷4.6 |
| wood_birch | 7.00 | **1.6649** | ÷4.2 |
| wood_oak | 7.50 | **1.9027** | ÷3.9 |
| bamboo | 5.00 | **1.1892** | ÷4.2 |
| nylon | 25.00 | **4.1622** | ÷6.0 |
| rubber | 2.50 | **35.676** | x14.3 |

`beta_air` / `gamma_radiation` unchanged in all rows (§4).

**Reordering effects worth flagging explicitly:**
- **Spruce fix confirmed**: new alpha ordering among woods is spruce (0.83) < bamboo/iron-adjacent
  region < maple (1.43) < birch (1.66) < oak (1.90) — spruce is now clearly the *lowest*-damped
  wood, matching its soundboard reputation. This directly resolves the anomaly
  `docs/MATERIALS_SOURCES.md` flagged (§92-102 of that file).
- **New anomaly this proposal introduces (needs 月月/Opus sign-off)**: glass's alpha barely moves
  (0.15 -> 0.178) while steel/aluminum drop by 20-25x. Glass is no longer the lowest-alpha
  material in the set (aluminum and steel now are) — a real reordering, driven by the fact that
  *ordinary* soda-lime glass (bottle/window glass — the physically appropriate reading of a
  generic "glass" preset) has a measured internal loss factor around 1-2e-3, i.e. genuinely
  higher than clean metals' 1-6e-4, even though ultra-pure fused silica/quartz resonators (used in
  high-Q lab oscillators) can be 2-3 orders of magnitude lower. The "glass rings a long time"
  perception (singing wine glasses) is a real phenomenon but owes as much to shape/weak
  radiative coupling as to bulk material loss — it does not require glass to have the lowest bulk
  eta of all solids. Flagging this as counter-intuitive but literature-consistent, not a mistake.

---

## 4. beta_air / gamma_radiation — no change proposed

Per task instruction: no per-material literature source for these two constants was found (none
was found for the previous documentation pass either — see `docs/MATERIALS_SOURCES.md` §"damping
triple"). Inventing per-material air-drag/radiation coefficients would violate Rule 4 ("a value
you cannot source stays at its old value"). **Proposal: keep all 14 materials' `beta_air` and
`gamma_radiation` exactly as currently stored, status stays 待溯源 (model-level constants — the
functional form, f² and f scaling, is textbook-standard; the per-material magnitudes are not
sourced and are not touched by this proposal).**

---

## 5. Rubber Young's modulus — proposed fix + traced consequence

### 5.1 Proposed value

`rubber.youngs_modulus`: **1.5e9 Pa -> propose ~5e6 Pa** (within the standard ~1e6-1e7 Pa range
for vulcanized/natural rubber Young's modulus reported across elastomer engineering references).
Because of the clipping behavior found below (§5.2), the *exact* pick within 1e6-1e7 does not
change the predicted engine consequence — any value in that decade lands in the same clipped
regime — so 5e6 (geometric-mid) is offered as a representative pick rather than a precision claim.
1.5e9 Pa is 2-3 orders of magnitude too stiff for bulk rubber (it's in vulcanized-ebonite/hard
rubber-composite or numerical-stability-compromise territory, not soft natural rubber).

### 5.2 Traced consequence in this engine (only path: CimbalomEngine)

Confirmed by grep: `youngsModulus` is read outside `PlateModel`/`BeamModel`/`StringModel`
internals in exactly one place — `src/engines/CimbalomEngine.h` (`startNote`, lines ~127-128 and
~276-277, both instances of the same formula):

```cpp
float logE = std::log10 (mat->youngsModulus);
float spectralTilt = juce::jlimit (0.1f, 1.0f, (logE - 7.5f) / 4.0f);
```

- Old: `logE = log10(1.5e9) = 9.176` -> `spectralTilt = (9.176-7.5)/4 = 0.419` (not clipped).
- New (any E in 1e6-1e7): `logE` in `[6.0, 7.0]` -> `(logE-7.5)/4` in `[-0.375, -0.125]` ->
  **clipped to the floor, spectralTilt = 0.1**, for *every* value in the proposed range (the
  clip boundary is at `logE = 7.9`, i.e. `E ≈ 7.94e7` — anything physically plausible for soft
  rubber sits below it). This is why the exact pick within 1e6-1e7 doesn't matter for the audible
  outcome: it's a floor-clamped regime either way.

Two audible knock-on effects, both confirmed by reading the surrounding code:

1. **Partial rolloff** (`CimbalomEngine.h:136`): `m.amplitude *= pow(spectralTilt, (partialN-1)*0.2)`.
   Lower `spectralTilt` (0.1 vs 0.419) makes higher partials die off in amplitude *faster* — a
   rubber-string Cimbalom note gets noticeably **darker** (fewer audible overtones) after the fix.
2. **Exciter (hammer-noise) brightness and duration** (`CimbalomEngine.h:204`,
   `setupExciter`/`CimbalomEngine.h:481-508`): `materialBright = clip(spectralTilt*2, 0.15, 2.0)`
   drops from `0.838 -> 0.2` (both inside the clip range, so this is a real, non-clipped ~4.2x
   drop). `materialBright` directly multiplies the exciter lowpass cutoff
   (`cutoff = cutoffs[idx] * (...) * materialBright`), so the attack noise burst gets **~4.2x
   darker**, and its envelope duration (`durScale = clip(1.5/(materialBright+0.5), 0.5, 3.0)`)
   goes from `1.12x -> 2.14x`, i.e. the noise burst also gets **~90% longer**. Net: a rubber-string
   Cimbalom note's attack transient becomes both darker and longer after the E fix.

**Not** an audible path: MIDI tuning. `sp.tension` comes from `StringModel::tensionForNote()`,
which depends on density/length/target-frequency only — not E — so pitch is unaffected. The
non-harmonicity coefficient `B = pi³·E·d⁴/(64·T·L²)` (`StringModel.h:62`) does scale with E, but
numerically (computed here for a representative MIDI 60 rubber string, L≈0.589 m,
d=0.8 mm, T≈52.5 N via `tensionForNote`): `B_old ≈ 1.64e-5`, `B_new ≈ 5.46e-8` — even at the 40th
partial (`n=40`, the model's max mode count) the resulting sharpening factor
`sqrt(1+B·n²)` goes from **1.3% (old)** to **0.004% (new)**, both effectively inaudible. So the
non-harmonicity channel is real but negligible; **spectralTilt/materialBright is the entire
audible story** for this fix.

Also **not** an audible path: `BeamModel`/`PlateModel`. Both retune every mode uniformly to the
target MIDI pitch via `tuneChromaticModesToMidi()` (`ChromaticEngine.h:38-60`,
`scale = target / modes.front().frequency` applied to *all* modes identically). Since `E` only
enters those two models as one overall multiplicative `stiffness` scalar applied equally to every
mode before that rescale (`BeamModel.h:48-49`, `PlateModel.h:49-52`), the rescale exactly cancels
E's effect on both the fundamental and every relative mode ratio (mode ratios in Beam/Plate come
from fixed material-independent eigenvalue tables, `betaL[]` / `zeros[]`/`freeModes[]`). **E has
zero audible effect in the Beam/Plate engines** for any material, confirmed by code, not assumed.

---

## 6. Predicted T60 impact table (pure model math, no rendering)

Evaluated at **MIDI 60** (f0 = 261.6256 Hz), using each material's *old* `beta_air`/`gamma_radiation`
(unchanged, §4) combined with old vs. proposed `alpha` (§3). Two columns per state because the two
engine conventions genuinely differ (§1.1):

- **T60 (String/Plate)**: `1 / (alpha + beta·f² + gamma·f)`
- **T60 (Beam)**: `1 / (2·alpha + beta·f² + gamma·f)`

| material | T60 old (S/P) | T60 new (S/P) | T60 old (Beam) | T60 new (Beam) | risk flag |
|---|---|---|---|---|---|
| aluminum | 3.23 s | **46.97 s** | 1.64 s | **30.14 s** | **>8s (both conventions) — 46x/18x longer** |
| steel | 1.95 s | **26.86 s** | 0.99 s | **16.39 s** | **>8s (both conventions) — 14x/17x longer** |
| bronze | 1.23 s | **7.49 s** | 0.62 s | 3.96 s | S/P borderline (near 8s ceiling, not over) |
| brass | 0.99 s | 5.16 s | 0.50 s | 2.69 s | none (5x longer, still under 8s) |
| copper | 0.82 s | 3.93 s | 0.41 s | 2.03 s | none |
| glass | 6.41 s | 5.42 s | 3.27 s | 2.76 s | none (slight *decrease*, still under 8s) |
| iron (cast) | 0.66 s | 0.83 s | 0.33 s | 0.42 s | none, small change |
| wood_spruce | 0.12 s | 1.16 s | 0.06 s | 0.59 s | none, but 9.6x longer — audible |
| wood_maple | 0.15 s | 0.69 s | 0.08 s | 0.35 s | none |
| wood_birch | 0.14 s | 0.59 s | 0.07 s | 0.30 s | none |
| wood_oak | 0.13 s | 0.52 s | 0.07 s | 0.26 s | none |
| bamboo | 0.20 s | 0.83 s | 0.10 s | 0.42 s | none |
| nylon | 0.04 s | 0.24 s | 0.02 s | 0.12 s | new value **<0.3s (Beam)**, borderline staccato |
| rubber | 0.39 s | **0.028 s** | 0.20 s | **0.014 s** | **<0.3s (both conventions) — collapses to a near-instant thud, 14x shorter** |

### Flags requiring explicit 月月/Opus review before Rule 10 execution

1. **Steel and aluminum blow past the >8s threshold by a wide margin (17-47s)** at a mid-register
   note. This is the single largest consequence of the whole proposal: their literature loss
   factors (1-6e-4 for steel, ~1e-4 for aluminum) are *much* lower than the loss factor the
   current tuned alpha values imply (back-solving: `eta_implied_old = alpha_old*2.2/f0`, e.g. for
   steel `0.5*2.2/261.6 ≈ 4.2e-3`, roughly 7-20x the literature value). This is directionally
   correct — real steel/aluminum resonators (tuning forks, bells) genuinely can ring for many
   seconds to tens of seconds — but it is a dramatic departure from the currently-tuned "musical"
   decay and a real **rest-check risk**: any existing score that relies on a steel/aluminum note
   decaying within a couple of seconds before the next event may now audibly bleed into
   subsequent material for 15-45+ seconds. This is the value 月月/Opus most needs to sign off on
   explicitly, possibly per-material rather than as a blanket switch.
2. **Rubber collapses to a near-click (14-28 ms)**, an order of magnitude *below* the old value,
   not above it. Combined with the spectralTilt/materialBright darkening (§5.2), a rubber Cimbalom
   note post-fix would sound like a muffled, almost pitchless thud rather than a sustained tone —
   likely a bigger perceptual change than any single metal fix. Worth an explicit listen-through
   decision, not just a numeric sign-off.
3. **Bronze sits right at the 8s boundary** (7.49s, String/Plate convention) — a small
   input-uncertainty shift (e.g. eta 1.0e-3 -> 1.3e-3, still inside the "1-2e-3" literature
   bracket) would push it over. Treat as "effectively flagged," not "safely under."
4. **The frequency-anchor caveat (§1.3) means all of the above numbers are exact only at MIDI 60.**
   Lower notes will show even larger T60 increases for the low-eta metals (T60 ∝ 1/f for the
   alpha-only part, so an octave down roughly doubles the already-large new T60); higher notes
   will show smaller increases. The corpus re-render mandated by Rule 10, if this proposal is
   accepted, needs to sample across the actual pitch range used in scores, not just MIDI 60, to
   catch the full extent of the rest-check risk.
5. Note on `T60_RATIO_TOLERANCE = (0.5, 2.0)` in `tools/physics_verify.py`: confirmed by reading
   the script that this is a **measured-audio vs. model-declared** ratio check (does the rendered
   waveform's decay match what the model itself claims it computed), not an absolute allowed T60
   range — so it is not mechanically broken by these magnitude changes as long as the rendering
   path correctly applies whatever new `decayTime` the model computes. The real risk from items
   1-3 above is compositional/perceptual (rest-check bleed, changed timbre), not this specific
   test gate.

---

## 7. Summary lists (per task deliverable spec)

**Materials with sourced proposed changes** (§3, all 14 `alpha` values; §5, `rubber.youngs_modulus`):
aluminum, steel, bronze, brass, copper, glass, iron, wood_spruce, wood_maple, wood_birch,
wood_oak, bamboo, nylon, rubber (alpha, all 14) + rubber (youngs_modulus, 1 value).

**Kept at old value (no change proposed, still 待溯源)**: `beta_air` and `gamma_radiation` for
all 14 materials (§4) — no per-material literature source exists; density/youngs_modulus/
poisson_ratio for the other 13 materials (already 文獻-backed per `docs/MATERIALS_SOURCES.md`,
untouched by this task).

**Rubber fix**: `youngs_modulus` 1.5e9 -> ~5e6 Pa (§5.1); traced consequence is spectralTilt
clipping to its floor (0.419 -> 0.1) in `CimbalomEngine.h`, producing a ~4.2x darker/longer
exciter transient and faster partial rolloff (§5.2); negligible non-harmonicity effect (1.3% ->
0.004% sharpening at partial 40, confirmed by calculation).

**Spruce fix**: `alpha` 8.0 -> 0.832 (using eta=7e-3, literature-low among woods per Wegst 2006),
now correctly the lowest-damped wood in the set, resolving the ordering anomaly
`docs/MATERIALS_SOURCES.md` flagged (§92-102 of that file).

**Predicted T60 impact**: see §6 table and the five numbered flags — steel/aluminum are the
dominant risk (>8s, both engine conventions, by a wide margin), rubber is the dominant *opposite*
risk (<0.3s, both conventions), bronze sits at the boundary.

No files were modified in `data/`, `src/`, or anywhere else as part of this task; this document is
the only artifact produced.
