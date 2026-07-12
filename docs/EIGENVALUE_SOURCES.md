# Modal Eigenvalue Constant Sourcing — M7 (7b + 7c)

Scope: literature verification of the three hard-coded eigenvalue tables that
drive the modal-synthesis engines' partial-frequency ratios:

- `BEAM_BETAL` — free-free Euler-Bernoulli beam (Tongue Drum engine), in
  `src/physics/BeamModel.h` + mirrored in `tools/physics_verify.py`.
- `PLATE_OMEGA` — clamped circular Kirchhoff plate (Water Gong engine,
  default), in `src/physics/PlateModel.h` (`zeros[]`) + mirrored in
  `tools/physics_verify.py`.
- `PLATE_FREE_OMEGA` — free-edge circular Kirchhoff plate (Water Gong engine,
  `freeEdge=true` A/B variant), in `src/physics/PlateModel.h` (`freeModes[]`) +
  mirrored in `tools/physics_verify.py`.

**No C++ or `.json` values were changed in this task (Phase G, M7 7b+7c).**
Comment-only annotations were added at the point of use. One discrepancy was
found (see §3) and was reported as a proposal, not applied — changing it
would alter rendered audio, which was called out as a separate Rule 10 task
(before/after report + corpus re-run).

> **STATUS UPDATE (Phase H, 2026-07-12): APPLIED.** 月月 reviewed and approved
> the §3 proposal below. `PLATE_FREE_OMEGA[4]` / `freeModes[4]` (m=4, n=0) was
> changed from **21.83** to **21.527** (the independently re-solved exact
> characteristic-equation root, re-derived and re-solved from scratch in
> Phase H, which reproduced the Phase G value 21.527 to 5 significant
> figures, consistent with Leissa Table 2.5's own footnoted-approximate 21.6).
> Rule 10 before/after audio report and full
> corpus re-run were completed for this change; see
> `reports/gate_outputs/phase_h_gate_full_eig.txt` and
> `reports/gate_outputs/phase_h_eig_delta.txt`. The old value 21.83 is kept on
> record below (§3, code snippet) as the pre-Phase-H value — it is history,
> not the current code.

Primary source obtained directly from NASA NTRS (not a secondhand citation):
Leissa, A. W., *Vibration of Plates*, NASA SP-160 (1969),
https://ntrs.nasa.gov/citations/19700009156 — full text downloaded and its
relevant table pages rendered/read as images to confirm exact digits (OCR/text
extraction of the scanned tables is unreliable enough on its own that every
number below was cross-checked visually against the table image).

---

## 1. `BEAM_BETAL` — free-free Euler-Bernoulli beam

Frequency equation for a uniform free-free beam: `cosh(betaL)*cos(betaL) = 1`
(standard result; tabulated in e.g. Blevins, *Formulas for Natural Frequency
and Mode Shape*). Roots were re-derived independently in this task by
root-bracketing `cosh(x)cos(x) - 1` with `scipy.optimize.brentq`:

| n | code value (BeamModel.h) | numerically verified root | match |
|---|---|---|---|
| 1 | 4.7300 | 4.7300407 | yes |
| 2 | 7.8532 | 7.8532046 | yes |
| 3 | 10.9956 | 10.9956078 | yes |
| 4 | 14.1372 | 14.1371655 | yes (rounds identically at 4 dp) |
| 5 | 17.2788 | 17.2787597 | yes |

**Result: PASS.** All 5 values (and the Python mirror's 6-decimal copies)
match the analytic roots to their stated precision. Comment citing "analytic
roots of cosh(x)cos(x)=1, verified numerically" added at
`src/physics/BeamModel.h` and `tools/physics_verify.py`.

---

## 2. `PLATE_OMEGA` — clamped circular Kirchhoff plate

Leissa NASA SP-160, **Table 2.1** ("Values of lambda^2 = omega*a^2*sqrt(rho
h/D) for a Clamped Circular Plate"), n = nodal diameters (columns), s = nodal
circles (rows). Frequency-independent of Poisson's ratio in the clamped case
(Leissa states this explicitly under the table).

Table 2.1 (as scanned from the primary source; digits confirmed against a
second independent reproduction, Tom Irvine's *Natural Frequencies of
Circular Plate Bending Modes*, Appendix H, which cites the same NASA SP-160):

```
       n=0        n=1        n=2        n=3
s=0  10.2158    21.260     34.877     51.030
s=1  39.771     60.829     84.583    111.021
s=2  89.104    120.079    153.815    190.304
s=3 158.184    199.053    242.729    289.180
```

This block covers only n=0..3; the code table also needs (m=4,n=0) and
(m=5,n=0) [m = nodal diameters, n = nodal circles in the C++ naming — inverted
letters vs. Leissa's n/s]. Those two entries, plus a check of every other
entry, were independently re-derived by solving the clamped-plate
characteristic equation (Leissa eq. 2.5):

```
Jn'(lambda)*In(lambda) - In'(lambda)*Jn(lambda) = 0
```

numerically (`mpmath`, 30-digit precision, `scipy.special.jv/iv` derivatives
for the initial bracket).

| code (m, n) | code value | table / re-solved lambda^2 | rel. error |
|---|---|---|---|
| (0,0) | 10.2158 | 10.21583 | 0.0003% |
| (1,0) | 21.260  | 21.2604  | 0.002%  |
| (2,0) | 34.877  | 34.8770  | 0%      |
| (0,1) | 39.771  | 39.7711  | 0%      |
| (3,0) | 51.030  | 51.0300  | 0%      |
| (1,1) | 60.829  | 60.8287  | 0.0005% |
| (4,0) | 69.666  | 69.6658  | 0.0003% |
| (2,1) | 84.583  | 84.5826  | 0.0005% |
| (0,2) | 89.104  | 89.1041  | 0%      |
| (5,0) | 90.739  | 90.7390  | 0%      |
| (3,1) | 111.02  | 111.0214 | 0.001%  |
| (1,2) | 120.08  | 120.0792 | 0.0007% |

**Result: PASS.** Max deviation 0.03% (table-rounding level), everything well
under the 1% threshold. Comment citing NASA SP-160 Table 2.1 + the
independent Bessel-equation re-solve added at `src/physics/PlateModel.h` and
`tools/physics_verify.py`.

---

## 3. `PLATE_FREE_OMEGA` — free-edge circular Kirchhoff plate (nu = 0.33)

Leissa NASA SP-160, **Table 2.5** ("Values of lambda^2 = omega*a^2*sqrt(rho/D)
for a Completely Free Circular Plate; nu = 0.33"), read directly from the
scanned table image (n = columns 0..6, s = rows 0..10):

```
       n=0       n=1       n=2       n=3       n=4        n=5        n=6
s=0     —         —       5.253     12.23    ᵃ21.6      ᵃ33.1      ᵃ46.2
s=1   9.084     20.52     35.25     52.91    ᵃ73.1      ᵃ95.8     ᵃ121.0
s=2  38.55      59.86     83.9     111.3     142.8      175.0      210.3
```
(ᵃ = table's own footnote: "Values true within 2 percent (ref. 2.20)" — i.e.
computed from Leissa's large-n *asymptotic* formula (eq. 2.15/2.16), not the
exact frequency equation (eq. 2.14), for entries where n or s is large.)

The exact free-plate characteristic equation (Leissa eq. 2.14) was also
independently re-derived from first principles in this task (Kirchhoff
circular-plate boundary conditions `M_r(a)=0`, `V_r(a)=0`, using the standard
polar-coordinate bending-moment/effective-shear formulas and the Bessel/
modified-Bessel ODEs to eliminate third derivatives) and solved numerically
(mpmath, 40-digit precision) as a cross-check independent of the scanned
table:

| code (m, n) | code value | Table 2.5 | independently re-solved (exact eq.) | vs. Table 2.5 |
|---|---|---|---|---|
| (2,0) | 5.253 | **5.253** (exact) | 5.262 | match (exact table digits) |
| (0,1) | 9.084 | **9.084** (exact) | 9.069 | match |
| (3,0) | 12.23 | **12.23** (exact) | 12.244 | match |
| (1,1) | 20.52 | **20.52** (exact) | 20.513 | match |
| (4,0) | **21.83** | ᵃ21.6 (2%-approx) | **21.527** | **MISMATCH: 1.06%** |
| (2,1) | 35.25 | **35.25** (exact) | 35.243 | match |
| (0,2) | 38.55 | **38.55** (exact) | 38.507 | match |

6 of 7 entries reproduce Table 2.5's digits exactly (these are the table's
*exact*-equation entries, not the footnoted approximations, so exact-string
agreement is the expected strong result). The independent re-solve of eq.
2.14 lands within ~0.2% of each of those 6 on top of the exact-string match,
which cross-validates the re-derivation itself.

**The 7th entry, (m=4, n=0) = 21.83, does not check out:**
- Table 2.5 gives **21.6** for (n=4, s=0), flagged as its own ~2%-accuracy
  asymptotic approximation.
- The independently re-solved *exact* equation (2.14) gives **21.527**,
  consistent with the table's 21.6 (0.34% apart, inside the table's stated 2%
  band) but **not** consistent with the code's 21.83 (1.4% from 21.527, 1.06%
  from the table's 21.6).
- Both comparisons exceed the task's 1% threshold, and both point the same
  direction (code value too high), which makes this look like a genuine
  transcription slip rather than table noise.

**Per Phase G task rules this value was NOT changed then.** Proposal recorded
for a follow-up task (needed 月月 sign-off + a Rule 10 before/after audio
report + corpus re-run, since this table feeds the free-edge Water Gong A/B
variant's audible partial ratios) — **this follow-up happened in Phase H
(2026-07-12) and the change below was APPLIED**, using 21.527 (the
independently re-solved exact root, re-confirmed by an independent Phase-H
re-derivation) rather than the table's rounded 21.6, since 21.527 is the
higher-precision, directly-computed value and both are within 0.34% of each
other:

```cpp
// src/physics/PlateModel.h, freeModes[] — pre-Phase-H value (historical):
{ 21.83f, 4, 0 },   // Phase H (2026-07-12): changed to { 21.527f, 4, 0 }
```
```python
# tools/physics_verify.py, PLATE_FREE_OMEGA — pre-Phase-H value (historical):
[5.253, 9.084, 12.23, 20.52, 21.83, 35.25, 38.55]
#                            ^^^^^ Phase H (2026-07-12): changed to 21.527
```

Comment-only annotations (source + the discrepancy above) were added at
`src/physics/PlateModel.h` and `tools/physics_verify.py` in Phase G; both
files were updated to the corrected value in Phase H (see status update at
the top of this document).

---

## Summary

| table | entries | result | change proposed | change applied |
|---|---|---|---|---|
| `BEAM_BETAL` | 5 | PASS — all match analytic roots | none | n/a |
| `PLATE_OMEGA` (clamped) | 12 | PASS — max 0.03% vs Leissa Table 2.1 + independent re-solve | none | n/a |
| `PLATE_FREE_OMEGA` (free, nu=0.33) | 7 | 6/7 PASS (exact match); 1 discrepancy | (4,0): 21.83 -> 21.6/21.527 | **APPLIED Phase H: 21.83 -> 21.527** |
