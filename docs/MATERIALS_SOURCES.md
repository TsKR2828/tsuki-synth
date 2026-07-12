# Material Constant Sourcing — data/materials.json

Authoritative store: `data/materials.json` (14 materials; `MaterialDB::getOrderedKeys()` in
`src/physics/MaterialDB.h` exposes 9 of them to the UI: steel, copper, bronze, aluminum, brass,
wood_spruce, wood_maple, glass, rubber). This document is descriptive only — **no values in
materials.json were changed while writing it.**

## How the damping triple is used (context, from src/physics/BeamModel.h:57-76)

```
alpha = material.damping.alpha          // mass/internal-friction term
beta  = material.damping.beta_air       // scales with freq^2
gamma = material.damping.gamma_radiation// scales with freq
decayDenom = alpha*2 + beta*freq*freq + gamma*freq
```

This is a Rayleigh-type damping split: `alpha` ~ material internal friction (roughly
frequency-independent), `beta_air*f^2` ~ viscous air-drag term (grows with frequency²,
consistent with the standard viscous boundary-layer/air-damping scaling used in Fletcher &
Rossing, *Principles of Vibration and Sound*, ch. 2), and `gamma_radiation*f` ~ acoustic
radiation loss (grows roughly linearly with frequency in the sub-critical-frequency regime for
small radiators, also ch. 2 territory). Knowing the intended physical role lets us judge
plausibility even where we cannot cite an exact number.

Status legend: **文獻** = literature-backed engineering/handbook value · **推導** = derived from
a formula/scaling law · **量測** = measured in this project · **待溯源** = untraceable to any
specific source; only order-of-magnitude / relative-ranking plausibility can be claimed.

---

## density / youngs_modulus / poisson_ratio

These three are classic solid-mechanics handbook constants (room temperature, along/near the
principal axis where the material is anisotropic). They are well within standard engineering
reference ranges (e.g. Callister *Materials Science and Engineering*; ASM Metals Handbook;
Forest Products Laboratory *Wood Handbook* for the wood species) and are marked **文獻** on that
basis, though no one paged through this codebase's history to confirm the exact reference used
when they were entered.

| material | density (kg/m³) | in-range? | E (Pa) | in-range? | ν | in-range? | status |
|---|---|---|---|---|---|---|---|
| steel | 7800 | yes (carbon steel ~7750-7870) | 200e9 | yes (190-210 GPa typical) | 0.29 | yes (0.27-0.30) | 文獻 |
| copper | 8900 | yes (8940-8960 pure Cu, close) | 120e9 | yes (110-130 GPa) | 0.34 | yes (0.33-0.36) | 文獻 |
| bronze | 8800 | yes (bronze alloys 8700-8900) | 110e9 | yes (95-120 GPa) | 0.34 | yes (0.32-0.35) | 文獻 |
| aluminum | 2700 | yes (2700 pure/6061) | 70e9 | yes (68-70 GPa) | 0.33 | yes (0.32-0.35) | 文獻 |
| brass | 8500 | yes (8400-8730 depending on Zn%) | 100e9 | yes (95-105 GPa) | 0.34 | yes (0.33-0.35) | 文獻 |
| wood_spruce | 450 | yes (Sitka/Engelmann spruce ~400-450) | 12e9 | yes (longitudinal E ~9-13 GPa) | 0.37 | plausible, wood ν is direction-dependent, treat as effective scalar | 文獻(近似等向簡化) |
| wood_maple | 650 | yes (hard maple ~630-700) | 12.5e9 | yes (~11-15 GPa longitudinal) | 0.38 | plausible, same caveat | 文獻(近似等向簡化) |
| rubber | 1100 | yes (natural/synthetic rubber ~1100-1200) | 5e6 | yes (natural/vulcanized rubber E ≈ 1-10 MPa; 5e6 Pa is the geometric mid of that decade) | 0.49 | yes (rubber is famously ~incompressible, 0.49-0.4999) | density/ν 文獻; **E 文獻 (Phase H fix, 2026-07-12) — corrected from 1.5e9 Pa (2-3 orders of magnitude too stiff for bulk rubber) per `reports/materials_physicalization_proposal.md` §5.1. Standard elastomer-engineering references (e.g. Hutchinson Aerospace & Industry damping definitions) give natural/vulcanized rubber E in the 1e6-1e7 Pa range; the exact pick within that decade does not change the predicted engine consequence (§5.2 of the proposal: any value in this range lands in the same `spectralTilt` floor-clamp regime in `CimbalomEngine.h`), so 5e6 is a representative pick, not a precision claim.** |
| glass | 2500 | yes (soda-lime glass ~2500) | 70e9 | yes (~70-72 GPa) | 0.22 | yes (0.20-0.23) | 文獻 |
| iron (cast) | 7200 | yes (grey cast iron ~7100-7300) | 170e9 | yes (cast iron 100-190 GPa depending on grade — wide range, 170 at the high end) | 0.26 | yes (0.21-0.30 for cast iron) | 文獻 |
| nylon | 1150 | yes (nylon 6/6 ~1140-1150) | 3e9 | yes (typical nylon 2-4 GPa) | 0.4 | yes (0.39-0.42) | 文獻 |
| bamboo | 700 | yes (700-800 typical) | 18e9 | yes (longitudinal, 10-20 GPa range reported) | 0.3 | plausible, no strong bamboo-specific ν reference checked | 文獻(近似) |
| wood_birch | 650 | yes (~650-670) | 15e9 | yes (birch longitudinal ~12-16 GPa) | 0.35 | plausible | 文獻 |
| wood_oak | 720 | yes (~700-750) | 12e9 | yes (oak longitudinal ~11-13 GPa) | 0.35 | plausible | 文獻 |

**Resolved (Phase H, 2026-07-12)**: `rubber.youngs_modulus` was two-to-three orders of magnitude
too stiff for real rubber and has been corrected from `1.5e9` to `5e6` Pa per 月月's sign-off on
`reports/materials_physicalization_proposal.md` §5.1. Traced audible consequence (only path,
`CimbalomEngine.h`): `spectralTilt` moves from `0.419` (unclamped) to its floor of `0.1` (clamped
for the entire 1e6-1e7 Pa plausible range), making a rubber-string Cimbalom note's partial rolloff
faster and its hammer-noise exciter transient ~4.2x darker and ~90% longer (§5.2 of the proposal).
Non-harmonicity effect from the same E change is negligible (1.3% -> 0.004% sharpening at partial
40). No effect on `BeamModel`/`PlateModel` (E only enters as a uniform pre-rescale stiffness
scalar there, cancelled by `tuneChromaticModesToMidi()`).

---

## damping.alpha / beta_air / gamma_radiation

**Update (Phase H, 2026-07-12)**: `alpha` for all 14 materials has been re-derived from published
loss-factor (`eta`) values via a load-bearing derivation and corrected — see
`reports/materials_physicalization_proposal.md` §1-§3 for the full step-by-step derivation, which
is reproduced in summary here. `beta_air` / `gamma_radiation` are **unchanged** (no per-material
literature source exists for either — proposal §4) and remain 待溯源.

**Derivation summary** (full version: proposal §1.2-§1.3). The engine's `decayTime` field is a
literal T60 (`ModalResonator.h:66-70`, `-6.9078`/`-60dB` convention). Standard loss-factor physics
gives `T60 ≈ 2.2 * Q / f` with `Q = 1/eta`, i.e. `T60 ≈ 2.2 / (f * eta)`. Mapping this onto the
engine's `decayDenom = alpha_term + beta*f² + gamma*f` (evaluating the alpha-only contribution)
gives `alpha_term = eta * f / 2.2`. Anchored at MIDI 60 (f0 = 261.6256 Hz, matching the proposal's
impact-table note): **`alpha_proposed = eta * 261.6256 / 2.2 = eta * 118.921`** (String/Plate
convention; Beam's existing `alpha*2` weighting, `BeamModel.h:87`, unchanged and out of scope,
means the same alpha is literature-exact at 523.25 Hz / MIDI 72 for Beam instead of MIDI 60 — a
documented consequence of the existing per-engine weighting, not a new choice).

**Caveat inherited from the derivation, not new here**: the physically-correct `alpha_term` is a
function of frequency `f`, but the engine's `alpha` is one frequency-independent scalar shared
across every note. A single number can only match `eta*f/2.2` exactly at the MIDI 60 anchor —
below that note the fixed alpha over-damps relative to constant-eta physics; above it, it
under-damps. This is an unavoidable consequence of the existing frozen model shape (Rule 2), not a
bug introduced by this fix.

Literature eta sources (full citations: proposal §2): Fletcher & Rossing, *Principles of Vibration
and Sound* / *The Physics of Musical Instruments*, ch. 2 (loss-factor scaling, metal/wood/rubber
qualitative ranges); Ashby, *Materials Selection in Mechanical Design* (loss-coefficient vs.
modulus chart, cast iron ~1-2 orders of magnitude above steel/aluminum); Lazan, *Damping of
Materials and Members in Structural Mechanics* (specific damping capacity data underlying the cast
iron claim); Wegst, "Wood for Sound," *American Journal of Botany* 93(10):1439-1448 (2006) (spruce
specifically chosen for **low** loss factor among tonewoods — the source for the spruce-ordering
fix below); engineering elastomer/isolator loss-factor handbook references (e.g. Hutchinson
Aerospace & Industry damping definitions) for rubber's order-of-magnitude-only estimate. No single
digitized numeric table could be pulled full-text this task (paywalled); every eta value below is
marked **推導(量級,文獻方向)** — right order of magnitude and qualitative family, not a
page-citable exact number. This is a strictly better sourcing state than the prior blanket
待溯源, but short of 測量級 precision.

| material | eta (chosen) | alpha (old, 待溯源) | alpha (new) | change | status |
|---|---|---|---|---|---|
| glass | 1.5e-3 | 0.15 | **0.1784** | x1.2 | 推導(文獻量級, ordinary soda-lime glass eta ~1-2e-3; note this makes glass no longer the lowest-alpha material — see reordering flag below) |
| aluminum | 1.0e-4 | 0.3 | **0.0119** | ÷25 | 推導(文獻量級, metals low end ~1e-4) |
| steel | 2.0e-4 | 0.5 | **0.0238** | ÷21 | 推導(文獻量級, carbon steel ~1-6e-4) |
| bronze | 1.0e-3 | 0.8 | **0.1189** | ÷6.7 | 推導(文獻量級，排序判斷 — keeps existing bronze<brass ordering, "not contradicted" per prior pass) |
| brass | 1.5e-3 | 1.0 | **0.1784** | ÷5.6 | 推導(文獻量級, mid-range ~1-2e-3) |
| copper | 2.0e-3 | 1.2 | **0.2378** | ÷5.0 | 推導(文獻量級，排序判斷 — high end, consistent with copper's known "dead"/high-internal-friction reputation) |
| iron (cast) | 1.0e-2 | 1.5 | **1.1892** | ÷1.3 | 推導(文獻方向明確 — Ashby/Lazan damping-capacity charts, cast iron 1-2 orders of magnitude above steel) |
| rubber | 3.0e-1 | 2.5 | **35.676** | x14.3 | 推導(方向極確定,量級單一數字信心低 — eta ~0.1-1, huge and strongly f/T-dependent, single number is order-of-magnitude placeholder only) |
| bamboo | 1.0e-2 | 5.0 | **1.1892** | ÷4.2 | 推導(文獻量級，信心較低 — grouped with hardwoods per task brief, no bamboo-specific number found) |
| wood_maple | 1.2e-2 | 6.5 | **1.4271** | ÷4.6 | 推導(文獻量級，同組內部排序信心低) |
| wood_birch | 1.4e-2 | 7.0 | **1.6649** | ÷4.2 | 推導(文獻量級，同組內部排序信心低) |
| wood_oak | 1.6e-2 | 7.5 | **1.9027** | ÷3.9 | 推導(文獻量級，同組內部排序信心低) |
| wood_spruce | 7.0e-3 | 8.0 | **0.8324** | ÷9.6 | 推導(文獻方向明確 — Wegst 2006, spruce is LOW among woods; **resolves the ordering anomaly flagged below**) |
| nylon | 3.5e-2 | 25.0 | **4.1622** | ÷6.0 | 推導(文獻量級, ~2-5e-2) |

**Wood-group confidence caveat**: only the spruce-vs-other-woods split is well-supported by a named
source (Wegst 2006). The *relative* ordering among maple/birch/oak/bamboo (all in the same
"~1-2e-2" literature bracket) is not independently sourced — treat those four as "same order of
magnitude, spruce clearly lower," not four separately-cited numbers (proposal §2.1).

**Resolved (Phase H, 2026-07-12)**: `wood_spruce.alpha` was the highest of all four wood entries,
which ran counter to spruce's known low-damping/high-Q reputation as the classic soundboard
tonewood — flagged in the prior documentation pass. Corrected `8.0 -> 0.8324` using eta = 7e-3
(literature-low among woods per Wegst 2006). New alpha ordering among woods: spruce (0.83) <
bamboo/iron-adjacent region < maple (1.43) < birch (1.66) < oak (1.90) — spruce is now correctly
the lowest-damped wood in the set.

**New reordering flag (needs 月月/Opus review before Rule 10 corpus re-render, proposal §3
"Reordering effects")**: glass's alpha barely moves (0.15 -> 0.178) while steel/aluminum drop
20-25x, so glass is no longer the lowest-alpha material — aluminum and steel now are. This is
literature-consistent (ordinary soda-lime glass eta ~1-2e-3 is genuinely higher than clean metals'
1-6e-4, even though fused-silica/quartz lab resonators can be orders of magnitude lower), not a
mistake, but is counter-intuitive relative to glass's "long ring" reputation (which owes as much
to shape/weak radiative coupling as to bulk material loss).

---

## Summary — sourcing status (updated Phase H, 2026-07-12)

**Changed this phase** (all sourced to `reports/materials_physicalization_proposal.md`, applied
2026-07-12 per 月月's sign-off):

- All 14 materials' `damping.alpha` — re-derived from literature loss-factor (`eta`) values via
  `alpha = eta * f0 / 2.2` anchored at MIDI 60, status now **推導(量級,文獻方向)** (see table
  above for per-material eta source and confidence).
- `rubber.youngs_modulus`: `1.5e9 -> 5e6` Pa, status now **文獻** (corrected from a value 2-3
  orders of magnitude too stiff for bulk rubber).

**Still 待溯源 (unchanged, no per-material source exists)**: `beta_air` and `gamma_radiation` for
all 14 materials — the functional form (f² / f scaling) is textbook-standard, but no per-material
magnitude source was found (proposal §4); `density` / `poisson_ratio` and the other 13 materials'
`youngs_modulus` — already 文獻-backed per the table above, untouched by this phase.

**Open flags carried forward from this phase** (see full detail in the damping-table section
above and `reports/materials_physicalization_proposal.md` §6):

1. Steel and aluminum's new literature-derived alpha values imply T60 at MIDI 60 rising from
   ~1-2s to 17-47s (both String/Plate and Beam engine conventions) — a real, large, intentional
   consequence of the eta correction, flagged for 月月/Opus review of rest-check/compositional
   impact before the Rule 10 corpus re-render, not a bug.
2. Rubber's T60 at MIDI 60 collapses from ~0.2-0.4s to ~0.014-0.028s (near-instant thud),
   combined with the `youngs_modulus` fix's spectralTilt/materialBright darkening in
   `CimbalomEngine.h` — likely the single largest perceptual change of this phase, worth an
   explicit listen-through.
3. Bronze sits close to the 8s String/Plate boundary (7.49s) — small input-uncertainty shifts in
   its eta estimate could push it over; treat as effectively flagged.
4. All T60 figures above are exact only at the MIDI 60 anchor frequency (proposal §1.3); lower
   notes show larger increases for the low-eta metals, higher notes smaller ones.
