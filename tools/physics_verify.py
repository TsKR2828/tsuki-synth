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

Expected partials are read from each probe's --dump-modes event.  Stiff-string
events are additionally checked against an independent analytic oracle.  FM is
explicitly non-physical and receives an f0-only check.

Usage:
    python tools/physics_verify.py                 # default probe set
    python tools/physics_verify.py --notes 60 69   # MIDI notes to test
    python tools/physics_verify.py --engines tongue_drum water_gong
    python tools/physics_verify.py --cli <path-to-TsukiSynthCLI.exe>
    python tools/physics_verify.py --levels        # velocity/output-level report
    python tools/physics_verify.py --t60           # M5: modal decay T60 judgment
                                                    # (narrowband envelope log-slope
                                                    # vs --dump-modes theory, modal
                                                    # engines, ratio tol 0.80-1.25)
    python tools/physics_verify.py --amps          # M2-2d: first-5-partial rel-dB
                                                    # judgment vs --dump-modes theory
                                                    # (modal engines, MIDI 60, +/-3.0dB)
    python tools/physics_verify.py --full          # M1 breadth: note-range scan
                                                    # (>=6 notes/engine) + material
                                                    # scan (modal engines) + velocity
                                                    # x2 -> +6dB judgment (all engines)
                                                    # + amplitude + measured T60
                                                    # + eigenvalue anchors (F1) +
                                                    # residual energy (informational)
Independent anchors (2026-07-18 harness repair):
  F1 eigenvalue anchors — --dump-modes frequency RATIOS for tongue_drum
      (cantilever + free_free), water_gong (clamped) and water_gong_free
      (free-edge, Poisson-dependent, nu read from data/materials.json) are
      judged against literature/first-principles eigenvalue ratios that never
      touch the C++ tables. Runs in --full AND in the default probe mode.
  F2 ET f0 anchor — in frequency_mode="midi" probes the PRIMARY audio-f0
      expectation is midi_to_hz(midi) (equal temperament, ±5 cents per §6);
      the dump-derived value stays as a second implementation-conformance
      check.
  F3 velocity law bound — the model's own predicted velocity-doubling delta
      must satisfy |predicted - 20*log10(2)| <= 1.0 dB (§6 "+6.0 ± 1.0"),
      in addition to the render-vs-model conformance check.
  F5 residual energy — unpredicted spectral energy outside all predicted
      modal bands, reported in --full; INFORMATIONAL ONLY (threshold pending
      月月 approval).
Exit code 0 = all probes within tolerance.
"""

import argparse, json, math, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np

# T60 fit now uses one peak-relative time axis.  The historical 0.5-2.0 range
# hid large metrology/model regressions; the corrected synthetic and rendered
# probes support an explicit -20%/+25% implementation-consistency bound.
T60_RATIO_TOLERANCE = (0.80, 1.25)

# Spectral metrology contract.  One FFT peak may satisfy one expected mode only.
ANALYSIS_MAX_HZ = 20000.0
NYQUIST_GUARD = 0.98
PARTIAL_SEARCH_FRAC = 0.06
PARTIAL_MIN_SNR_DB = 20.0
PARTIAL_MIN_PROMINENCE_DB = 6.0
PARTIAL_MIN_GLOBAL_DB = -60.0
MODEL_REQUIRED_DB = -45.0
PARTIAL_MODEL_STRENGTH_SLACK_DB = 15.0
PARTIAL_MIN_REQUIRED = 1       # at least f0; every model-audible mode must pass
PARTIAL_MIN_COVERAGE = 1.0
MATERIAL_MIN_OBSERVED_CYCLES = 8.0

# Populated by scan_materials()/run_full() so the CLI can distinguish
# "all checked cases passed" from "everything is physically verified".
LAST_MATERIAL_UNVERIFIED = []
LAST_FULL_UNVERIFIED = []

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


# Fixed-free (cantilever) Euler-Bernoulli beam eigenvalues betaL — the model's
# DEFAULT tongue_drum boundary since the 2026-07-17 deep audit (BeamModel.h:
# "舌片與鼓身相連的一端近似固支、另一端自由").
# SOURCE (F1, 2026-07-18): analytic roots of cos(x)*cosh(x) = -1 (the
# fixed-free characteristic equation; e.g. Blevins, "Formulas for Natural
# Frequency and Mode Shape", Table 8-1 / any Euler-Bernoulli beam reference).
# Verified numerically in tests/test_physics_verify.py (scipy brentq root of
# cos*cosh+1 within 1e-5 of each entry). NOT copied from BeamModel.h -- the
# digits agree because both derive from the same published equation, which is
# exactly what makes this an independent anchor for the C++ table.
CANTILEVER_BETAL = [1.8751041, 4.6940911, 7.8547574, 10.9955407, 14.1371684]


def cantilever_ratios(n):
    b1 = CANTILEVER_BETAL[0]
    return [(b / b1) ** 2 for b in CANTILEVER_BETAL][:n]


def harmonic_ratios(n):
    return [float(k) for k in range(1, n + 1)]


# ── F1 (2026-07-18): independent eigenvalue anchors for beam/plate dumps ────
# WHY: the BEAM_BETAL / PLATE_OMEGA / PLATE_FREE_OMEGA tables above had become
# dead code (no consumer) -- every rendered-audio check took its expected
# frequencies from --dump-modes, so a corrupted C++ eigenvalue table would
# corrupt dump AND render identically and every gate would stay green
# ("dump 自我一致" instead of "獨立理論錨"). These checks compare the DUMPED
# modal-frequency RATIOS against literature/derived eigenvalue ratios that
# never touch the C++ code path.
#
# TOLERANCES (self-chosen per task spec "容差自訂要小", NOT §6 entries):
# - Beams + clamped plate: 0.10% -- same bound the stiff-string oracle already
#   enforces. Both sides are float32-rounded published constants; measured
#   agreement is ~1e-4 % (see validation), so 0.10% leaves margin for float
#   storage while still catching a single-digit table typo (>=0.05% shift).
# - Free-edge plate: 0.50% -- PlateModel.h linearly interpolates its
#   Poisson-root rows over nu (documented "<0.02% error" between rows), and
#   this anchor re-solves the exact characteristic equation at the actual
#   material nu, so 0.50% bounds interpolation error at any nu in [0.20,0.49]
#   while still catching the historical class of error (the (4,0) 21.83-vs-
#   21.527 transcription bug was a 1.4% shift).
EIGEN_RATIO_TOL_PCT = 0.10
EIGEN_FREE_RATIO_TOL_PCT = 0.50
EIGEN_MIDI = 60   # fixed probe note; eigenvalue RATIOS are pitch-independent
                  # (MIDI tuning scales every mode by one common factor)

# (m = nodal diameters, Omega at nu=0.33) bracketing centres for the free-edge
# root search below, straight from Leissa NASA SP-160 Table 2.5 (same primary
# source as PLATE_FREE_OMEGA above). The bracket [0.70, 1.40] x centre covers
# the entire nu=[0.20, 0.49] materials range (worst excursion: (2,0) moves
# 0.89x..1.08x across that range) without reaching the next same-m branch
# (nearest is >= 6x away in Omega).
FREE_PLATE_MODE_BRACKETS = [(2, 5.253), (0, 9.084), (3, 12.23), (1, 20.52),
                            (4, 21.527), (2, 35.25), (0, 38.55)]


def _free_plate_det(m, lam, nu):
    """Characteristic determinant of the completely-free Kirchhoff circular
    plate (radius normalised to 1), W(r) = A*J_m(lam*r) + B*I_m(lam*r):
        M_r(1) = 0:  w'' + nu*(w' - m^2 w) = 0
        V_r(1) = 0:  (lap w)' - (1-nu)*m^2*(w' - w) = 0   (Kelvin-Kirchhoff
                                                            effective shear)
    Both conditions reduced with the (modified) Bessel ODEs
    (J_m'' = -J_m'/z - (1 - m^2/z^2) J_m ; I_m'' = -I_m'/z + (1 + m^2/z^2) I_m)
    -- this is Leissa NASA SP-160 eq. 2.14's system, re-derived here in Python
    (scipy.special), fully independent of PlateModel.h's precomputed root
    rows. Validated in tests/test_physics_verify.py: at nu=0.33 the solved
    roots reproduce Leissa Table 2.5 within the table's own rounding (<0.2%).
    """
    from scipy.special import jv, iv
    J = jv(m, lam)
    Jp = (m / lam) * J - jv(m + 1, lam)
    I = iv(m, lam)
    Ip = (m / lam) * I + iv(m + 1, lam)
    MJ = (nu - 1.0) * lam * Jp + (-(lam * lam) + m * m * (1.0 - nu)) * J
    MI = (nu - 1.0) * lam * Ip + ((lam * lam) + m * m * (1.0 - nu)) * I
    VJ = -lam ** 3 * Jp - (1.0 - nu) * m * m * (lam * Jp - J)
    VI = lam ** 3 * Ip - (1.0 - nu) * m * m * (lam * Ip - I)
    return MJ * VI - MI * VJ


def free_plate_omegas(nu, count=None):
    """Solves Omega = lambda^2 of the first len(FREE_PLATE_MODE_BRACKETS)
    free-edge modes at the ACTUAL material Poisson ratio (read from
    data/materials.json by the caller -- the free-edge spectrum is
    nu-dependent, unlike the clamped case). Returns the list sorted ascending
    (branches can cross as nu changes, e.g. (1,1)/(4,0) near nu=0.45, and
    PlateModel.h exposes modes in actual frequency order). Returns None if
    any root cannot be bracketed -- callers must FAIL honestly, not guess."""
    from scipy.optimize import brentq
    omegas = []
    for m, centre in FREE_PLATE_MODE_BRACKETS:
        lo, hi = math.sqrt(centre * 0.70), math.sqrt(centre * 1.40)
        xs = np.linspace(lo, hi, 600)
        vals = [_free_plate_det(m, x, nu) for x in xs]
        roots = []
        for i in range(len(xs) - 1):
            if vals[i] == 0.0:
                roots.append(float(xs[i]))
            elif vals[i] * vals[i + 1] < 0.0:
                roots.append(brentq(lambda x: _free_plate_det(m, x, nu),
                                    xs[i], xs[i + 1], xtol=1e-12))
        if not roots:
            return None
        omegas.append(min((r * r for r in roots),
                          key=lambda o: abs(o - centre)))
    omegas.sort()
    return omegas[:count] if count else omegas


def material_poisson_ratio(material_key, materials_path=None):
    """Reads nu straight from data/materials.json (the same file the C++
    MaterialDB loads) -- per task spec, the free-edge anchor must be evaluated
    at the probe material's actual Poisson ratio, not assume nu=0.33."""
    if materials_path is None:
        materials_path = Path(__file__).resolve().parent.parent / "data" / "materials.json"
    data = json.loads(Path(materials_path).read_text(encoding="utf-8"))
    return float(data["materials"][material_key]["poisson_ratio"])


def judge_frequency_ratios(dump_freqs, anchor_ratios, tol_pct):
    """Pure ratio judgment (unit-testable without a CLI): dumped mode
    frequency ratios f_n/f_1 vs literature eigenvalue ratios. Missing modes
    fail -- a truncated dump must not shrink the anchor's coverage."""
    rows = []
    if not dump_freqs or dump_freqs[0] <= 0.0:
        return False, rows
    ok = True
    f1 = float(dump_freqs[0])
    for i, want in enumerate(anchor_ratios, 1):
        if i - 1 >= len(dump_freqs):
            rows.append(dict(n=i, anchor=want, dump=None, err_pct=None,
                             verdict="MISSING"))
            ok = False
            continue
        got = float(dump_freqs[i - 1]) / f1
        err_pct = (got / want - 1.0) * 100.0
        this_ok = abs(err_pct) <= tol_pct
        ok = ok and this_ok
        rows.append(dict(n=i, anchor=want, dump=got, err_pct=err_pct,
                         verdict="PASS" if this_ok else "FAIL"))
    return ok, rows


def eigenvalue_anchor_cases(engines=None):
    """The four boundary cases F1 anchors. npart choices: beams use the 5
    tabulated betaL entries (modes 6+ are the documented asymptotic formula,
    not a table that can silently rot); clamped plate uses all 8
    literature-verified PLATE_OMEGA entries; free-edge uses all 7 table rows."""
    cases = [
        dict(name="tongue_drum cantilever (default)", eng="tongue_drum",
             override=None, kind="beam_cant",
             ratios=cantilever_ratios(5), tol=EIGEN_RATIO_TOL_PCT),
        dict(name="tongue_drum free_free (explicit)", eng="tongue_drum",
             override={"beam_boundary": "free_free"}, kind="beam_ff",
             ratios=beam_ratios(5), tol=EIGEN_RATIO_TOL_PCT),
        dict(name="water_gong clamped", eng="water_gong",
             override=None, kind="plate_cl",
             ratios=plate_ratios(8), tol=EIGEN_RATIO_TOL_PCT),
        dict(name="water_gong_free free-edge (nu-dependent)",
             eng="water_gong_free", override=None, kind="plate_fr",
             ratios=None, tol=EIGEN_FREE_RATIO_TOL_PCT),  # ratios need nu
    ]
    if engines is not None:
        cases = [c for c in cases if c["eng"] in engines]
    return cases


def scan_eigenvalue_anchors(cli, outdir, engines=None):
    """F1 gate: --dump-modes frequency ratios vs independent eigenvalue
    anchors (exit-code-affecting). Dump-only -- no audio is rendered, so a
    corrupted C++ eigenvalue table is caught here even though dump and render
    would agree with each other."""
    cases = eigenvalue_anchor_cases(engines)
    if not cases:
        print("\n(eigenvalue anchor scan skipped: none of the requested "
              "--engines are tongue_drum/water_gong/water_gong_free)")
        return True
    print("\n" + "-" * 70)
    print(f"Eigenvalue-ratio anchors (MIDI {EIGEN_MIDI}, --dump-modes ratios vs "
          "literature beam/plate eigenvalues; independent of the C++ tables):")
    overall_ok = True
    for case in cases:
        sf, _ = build_probe_score(case["eng"], EIGEN_MIDI, outdir,
                                  params_override=case["override"],
                                  tag="_eig_" + case["kind"])
        event = dump_modes_event(cli, sf)
        anchor = case["ratios"]
        nu_note = ""
        if anchor is None:   # free-edge: solve at the probe material's nu
            spec_params = dict(ENGINES[case["eng"]]["params"])
            if case["override"]:
                spec_params.update(case["override"])
            nu = material_poisson_ratio(spec_params.get("material", "steel"))
            omegas = free_plate_omegas(nu)
            if omegas:
                anchor = [o / omegas[0] for o in omegas]
                nu_note = (f" [nu={nu:.2f} from data/materials.json, "
                           "roots re-solved from the free-plate "
                           "characteristic equation]")
        print(f"\n# {case['name']}{nu_note}")
        if not event or not event.get("partials"):
            print("   -> FAIL (--dump-modes returned no modal event)")
            overall_ok = False
            continue
        if anchor is None:
            print("   -> FAIL (free-plate characteristic-equation root "
                  "search failed; cannot construct the anchor)")
            overall_ok = False
            continue
        freqs = [float(p["freq"]) for p in event["partials"]]
        case_ok, rows = judge_frequency_ratios(freqs, anchor, case["tol"])
        print(f"   {'n':>2} {'anchor_ratio':>12} {'dump_ratio':>11} "
              f"{'err%':>8}  verdict   (tol +/-{case['tol']:.2f}%)")
        for row in rows:
            dump_s = f"{row['dump']:11.6f}" if row["dump"] is not None else f"{'--':>11}"
            err_s = f"{row['err_pct']:+8.4f}" if row["err_pct"] is not None else f"{'--':>8}"
            print(f"   {row['n']:>2} {row['anchor']:>12.6f} {dump_s} "
                  f"{err_s}  {row['verdict']}")
        if not case_ok:
            print("   -> FAIL. Do NOT widen the anchor tolerance -- a dumped "
                  "ratio off the literature eigenvalue means the C++ "
                  "beam/plate table (or its consumer) changed; record the "
                  "numbers per ROADMAP_PHYSICS.md §1g.")
        print(f"   -> {'PASS' if case_ok else 'FAIL'}")
        overall_ok = overall_ok and case_ok
    return overall_ok


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


# ── engine probe definitions ────────────────────────────────────────────────
# tol_pct is applied to every assessed partial, including stiff strings.  The
# old inharmonic branch merely printed stretch and could not fail; stiff-string
# expectations now come from --dump-modes and are cross-checked by an
# independent Python oracle below.
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
        # Modes 4/5 deliberately exercise the one-to-one assignment: their
        # +/-6% search windows overlap, but two distinct peaks are required.
        engine="water_gong", ratios=plate_free_ratios, npart=5, tol_pct=4.0,
        inharmonic=False,
        params={"material": "bronze", "strike_position": 0.30,
                "thickness_mm": 4.0, "plate_free_edge": True},
    ),
    "fm": dict(
        engine="fm", ratios=harmonic_ratios, npart=1, tol_pct=2.0,
        inharmonic=False,
        non_physical=True,
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


# ── spectral peak measurement (one-to-one, prominence-qualified) ────────────
def _db_ratio(num, den, floor=-240.0):
    return 20.0 * math.log10(num / den) if num > 0.0 and den > 0.0 else floor


def analysis_frequency_limit(sr):
    return min(ANALYSIS_MAX_HZ, sr * 0.5 * NYQUIST_GUARD)


def material_min_observable_t60(frequency_hz):
    return max(0.020, MATERIAL_MIN_OBSERVED_CYCLES / float(frequency_hz))


def measure_partials(sr, x, predicted_freqs, analysis_t60=None):
    """Assign independently visible FFT peaks to expected modes one-to-one.

    The previous implementation selected the maximum bin independently inside
    every +/-6% window.  Overlapping windows could therefore reuse one peak,
    and an empty window still returned its largest noise/leakage bin.  Results
    are dictionaries with an explicit status: found, missing, or out_of_band.
    """
    try:
        from scipy.signal import find_peaks, peak_prominences
    except Exception as exc:
        raise RuntimeError("scipy is required for prominence-qualified peak detection") from exc

    limit = analysis_frequency_limit(sr)
    out = [dict(status="out_of_band", expected=float(fp))
           if not (0.0 < float(fp) <= limit) else None
           for fp in predicted_freqs]

    # Fast-decay materials need a proportionally early/short window.  A fixed
    # 500 ms Hann window centres its energy after a 28 ms-T60 rubber mode has
    # vanished into quantisation, turning transient leakage into "amplitude".
    if analysis_t60 and analysis_t60 > 0.0:
        start_s = min(0.005, analysis_t60 * 0.05)
        window_s = _clamp(analysis_t60 * 0.5, 0.020, 0.50)
    else:
        start_s, window_s = 0.005, 0.50
    start = int(start_s * sr)
    seg = x[start:start + int(window_s * sr)]
    if len(seg) < min(int(0.1 * sr), int(window_s * sr)):
        seg = x[start:]
    valid_indices = [i for i, item in enumerate(out) if item is None]
    if len(seg) < 64:
        for i in valid_indices:
            out[i] = dict(status="missing", expected=float(predicted_freqs[i]), reason="short_window")
        return out

    seg = np.asarray(seg, dtype=np.float64) * np.hanning(len(seg))
    nfft = 1 << int(math.ceil(math.log2(len(seg) * 4)))
    spectrum = np.abs(np.fft.rfft(seg, nfft))
    bin_hz = sr / nfft
    max_bin = min(len(spectrum) - 2, int(limit / bin_hz))
    usable = spectrum[1:max_bin + 1]
    if usable.size < 3 or float(np.max(usable)) <= 1e-15:
        for i in valid_indices:
            out[i] = dict(status="missing", expected=float(predicted_freqs[i]), reason="silent")
        return out

    peak_bins, _ = find_peaks(spectrum[1:max_bin + 1])
    peak_bins = peak_bins + 1
    if peak_bins.size:
        prominences = peak_prominences(spectrum, peak_bins)[0]
    else:
        prominences = np.asarray([], dtype=np.float64)

    noise = max(float(np.median(usable)), 1e-15)
    global_peak = max(float(np.max(usable)), 1e-15)
    candidates = []
    for k, prom in zip(peak_bins.tolist(), prominences.tolist()):
        mag = float(spectrum[k])
        snr_db = _db_ratio(mag, noise)
        base = max(mag - float(prom), noise)
        prominence_db = _db_ratio(mag, base)
        global_db = _db_ratio(mag, global_peak)
        if (snr_db < PARTIAL_MIN_SNR_DB
                or prominence_db < PARTIAL_MIN_PROMINENCE_DB
                or global_db < PARTIAL_MIN_GLOBAL_DB):
            continue
        a, b, c = spectrum[k - 1], spectrum[k], spectrum[k + 1]
        d = a - 2.0 * b + c
        delta = 0.5 * (a - c) / d if abs(d) > 1e-15 else 0.0
        delta = float(_clamp(delta, -0.5, 0.5))
        candidates.append(dict(bin=k, freq=(k + delta) * bin_hz,
                               mag=mag, snr_db=snr_db,
                               prominence_db=prominence_db,
                               global_db=global_db))

    # Globally greedy nearest-frequency assignment.  A candidate bin and an
    # expected mode are each consumed at most once, so overlapping windows can
    # never claim the same physical peak twice.
    pairs = []
    for expected_i in valid_indices:
        fp = float(predicted_freqs[expected_i])
        for candidate_i, candidate in enumerate(candidates):
            rel_err = abs(candidate["freq"] / fp - 1.0)
            if rel_err <= PARTIAL_SEARCH_FRAC:
                pairs.append((rel_err, -candidate["prominence_db"],
                              expected_i, candidate_i))
    assigned_expected = set()
    assigned_candidates = set()
    for _, _, expected_i, candidate_i in sorted(pairs):
        if expected_i in assigned_expected or candidate_i in assigned_candidates:
            continue
        assigned_expected.add(expected_i)
        assigned_candidates.add(candidate_i)
        candidate = dict(candidates[candidate_i])
        candidate.update(status="found", expected=float(predicted_freqs[expected_i]))
        out[expected_i] = candidate

    for i in valid_indices:
        if out[i] is None:
            out[i] = dict(status="missing", expected=float(predicted_freqs[i]),
                          reason="no_qualified_unique_peak")
    return out


def assess_partial_frequencies(expected_modes, measured, tol_pct,
                               f0_measured=None, f0_expected_et=None):
    """Return (ok, rows, coverage) for model-required audible modes.

    Requiredness is determined by the *model* amplitude, never by whether the
    render happened to be weak.  Missing, weak, out-of-band, or frequency-wrong
    required modes fail.  Model-predicted modes below MODEL_REQUIRED_DB are
    reported as explicit non-required coverage, not silently counted as pass.

    f0_expected_et (F2, 2026-07-18): the equal-temperament anchor
    midi_to_hz(midi). Every probe this harness writes renders in
    frequency_mode="midi" (ScoreParser default; build_probe_score never
    overrides it), whose design contract pins the fundamental to 12-TET.
    When supplied, it is the PRIMARY absolute-pitch judgment (±F0_TOL_CENTS,
    the §6-registered ±5 cents -- unchanged); the dump-derived expectation is
    retained as a SECOND, implementation-conformance check. Without the ET
    anchor, a C++ tuning bug that shifted dump and render identically would
    keep the f0 gate green (dump self-consistency, not absolute pitch)."""
    rows = []
    required_total = sum(1 for mode in expected_modes if mode.get("required", True))
    found_required = 0
    ok = required_total >= min(PARTIAL_MIN_REQUIRED, len(expected_modes))
    fund_mag = 0.0
    if measured and measured[0].get("status") == "found":
        fund_mag = measured[0]["mag"]

    for i, (mode, result) in enumerate(zip(expected_modes, measured), 1):
        required = bool(mode.get("required", True))
        row = dict(n=i, expected=mode["freq"], model_db=mode.get("model_db"),
                   raw_model_db=mode.get("raw_model_db"),
                   isolated_model_db=mode.get("isolated_model_db"),
                   required=required, status=result.get("status", "missing"))
        if not required:
            row["verdict"] = "MODEL-WEAK (not required)"
            rows.append(row)
            continue
        if result.get("status") != "found":
            row["verdict"] = result.get("status", "missing").upper()
            ok = False
            rows.append(row)
            continue
        freq = f0_measured if i == 1 and f0_measured else result["freq"]
        rel_db = _db_ratio(result["mag"], fund_mag) if fund_mag > 0 else -240.0
        err_pct = (freq / mode["freq"] - 1.0) * 100.0
        if i == 1:
            # implementation-conformance: audio vs the model's own dump
            impl_cents = cents(freq, mode["freq"])
            freq_ok = abs(impl_cents) <= F0_TOL_CENTS
            et_cents = None
            if f0_expected_et and f0_expected_et > 0.0:
                # F2 PRIMARY anchor: audio vs equal temperament (see docstring)
                et_cents = cents(freq, f0_expected_et)
                freq_ok = freq_ok and abs(et_cents) <= F0_TOL_CENTS
            err_cents = et_cents if et_cents is not None else impl_cents
            row["impl_cents"] = impl_cents
            row["et_cents"] = et_cents
        else:
            err_cents = None
            freq_ok = abs(err_pct) <= tol_pct
        model_floor = max(PARTIAL_MIN_GLOBAL_DB,
                          float(mode.get("model_db", MODEL_REQUIRED_DB))
                          - PARTIAL_MODEL_STRENGTH_SLACK_DB)
        strength_ok = i == 1 or rel_db >= model_floor
        this_ok = freq_ok and strength_ok
        ok = ok and this_ok
        found_required += int(this_ok)
        row.update(freq=freq, rel_db=rel_db, err_pct=err_pct,
                   err_cents=err_cents, snr_db=result.get("snr_db"),
                   prominence_db=result.get("prominence_db"),
                   verdict="PASS" if this_ok else "FAIL")
        rows.append(row)

    coverage = found_required / required_total if required_total else 0.0
    if coverage < PARTIAL_MIN_COVERAGE:
        ok = False
    return ok, rows, dict(required=required_total, passed=found_required,
                          ratio=coverage, total=len(expected_modes))


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
        "$schema": "TsukiSynth Score v1",
        "meta": {"title": fn, "id": fn},
        "global": {"bpm": 120, "sample_rate": sr, "master_volume": 1.0,
                   "effects": {"reverb": {"decay": 2, "wet": 0},
                               "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                               "distortion": {"type": "overdrive", "drive": 0,
                                              "instability": 0, "wet": 0}}},
        "events": [{"time": 0.0, "duration": dur, "engine": spec["engine"],
                    "note": str(midi), "velocity": vel,
                    "params": params}],
        # Metrology probes use 24-bit PCM. At piano MIDI108 the physically
        # hammer-filtered modal signal can sit below one 16-bit LSB even though
        # it is still required relative to the fundamental; judging a quantised-
        # away partial as a model failure is a measurement bug, not an honest
        # negative test.
        "export": {"filename": fn, "format": "wav", "bit_depth": 24,
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
            wav, sf = render_probe(cli, eng, midi, outdir)
            sr, x = read_wav_mono(wav)
            if spec.get("non_physical"):
                # FM has no modal dump or independent physical partial oracle.
                # Keep it in range/level tests, but state and test only pitch.
                event = None
                expected = [dict(freq=f0, model_db=0.0, required=True)]
                oracle_ok, oracle_note = True, "FM non-modal: f0-only"
                model_t60 = None
            else:
                event, expected, oracle_ok, oracle_note = expected_modes_from_dump(
                    cli, sf, eng, sr)
                model_t60 = (expected[0]["decay"] if expected else None)

            print(f"\n# {eng:11s} MIDI {midi}  "
                  f"(expectation={'f0-only/non-physical' if spec.get('non_physical') else '--dump-modes'})")
            if oracle_note:
                print(f"   oracle: {oracle_note} [{'OK' if oracle_ok else 'FAIL'}]")
            if not expected:
                print("   -> FAIL (--dump-modes supplied no assessable modes)")
                overall_ok = False
                continue
            pred = [mode["freq"] for mode in expected]
            meas = measure_partials(sr, x, pred, analysis_t60=model_t60)
            f0_meas = measure_f0(x, sr, pred[0], model_t60=model_t60)
            # F2: f0_expected_et = midi_to_hz(midi) is the primary absolute-
            # pitch anchor for these frequency_mode="midi" probes (§6 ±5
            # cents); the dump expectation stays as conformance check #2.
            probe_ok, rows, coverage = assess_partial_frequencies(
                expected, meas, spec["tol_pct"], f0_measured=f0_meas,
                f0_expected_et=f0)
            probe_ok = probe_ok and oracle_ok
            if f0_meas:
                print(f"   f0 ET anchor: expected {f0:.3f} Hz (12-TET MIDI "
                      f"{midi}), measured {f0_meas:.3f} Hz "
                      f"({cents(f0_meas, f0):+.3f} cents, tol +/-"
                      f"{F0_TOL_CENTS:.1f}); dump-conformance "
                      f"{cents(f0_meas, pred[0]):+.3f} cents")

            print(f"   {'n':>2} {'expected':>11} {'measured':>11} {'err%':>7} "
                  f"{'rel_dB':>7} {'prom':>6}  verdict")
            for row in rows:
                measured_s = f"{row['freq']:11.3f}" if row.get("freq") is not None else f"{'--':>11}"
                err_s = f"{row['err_pct']:+7.2f}" if row.get("err_pct") is not None else f"{'--':>7}"
                rel_s = f"{row['rel_db']:+7.1f}" if row.get("rel_db") is not None else f"{'--':>7}"
                prom_s = (f"{row['prominence_db']:6.1f}" if row.get("prominence_db") is not None
                          else f"{'--':>6}")
                model_note = (f" model={row['model_db']:+.1f}dB"
                              if row.get("model_db") is not None else "")
                if row.get("raw_model_db") is not None:
                    model_note += f" raw={row['raw_model_db']:+.1f}dB"
                if row.get("isolated_model_db") is not None:
                    model_note += f" isolated={row['isolated_model_db']:+.1f}dB"
                print(f"   {row['n']:>2} {row['expected']:>11.3f} {measured_s} "
                      f"{err_s} {rel_s} {prom_s}  {row['verdict']}{model_note}")
            print(f"   coverage: {coverage['passed']}/{coverage['required']} required "
                  f"({coverage['ratio'] * 100.0:.0f}%), {coverage['total']} model modes listed")
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
    """Material *implementation sensitivity* gate, not material validation.

    MIDI tuning intentionally pins f0, so comparing every material to the same
    MIDI pitch was a tautology and is no longer advertised as physical material
    validation.  This gate instead checks that (a) each material's dumped modal
    frequencies are present in audio, (b) model-required relative amplitudes
    match the render, and (c) material T60 is finite and materially changes
    across the sweep.  --full separately measures default-material T60 from
    audio.  Real-world material validation still requires measured specimens.
    """
    scan_engines = [e for e in MATERIAL_SCAN_ENGINES if engines is None or e in engines]
    materials = load_material_keys(materials_path)
    print("\n" + "-" * 70)
    print(f"Material implementation-sensitivity scan (NOT real-material validation; "
          f"MIDI {MATERIAL_SCAN_MIDI}, {len(materials)} materials x "
          f"{len(scan_engines)} modal engines):")
    global LAST_MATERIAL_UNVERIFIED
    LAST_MATERIAL_UNVERIFIED = []
    overall_ok = True
    midi = MATERIAL_SCAN_MIDI
    for eng in scan_engines:
        spec = ENGINES[eng]
        decay_values = []
        for mat in materials:
            wav, sf = render_probe(cli, eng, midi, outdir,
                                   params_override={"material": mat},
                                   tag=f"_mat_{mat}")
            sr, x = read_wav_mono(wav)
            event, expected, oracle_ok, oracle_note = expected_modes_from_dump(
                cli, sf, eng, sr)
            if not expected:
                print(f"   {eng:11} material={mat:12} no dumped modes -> FAIL")
                overall_ok = False
                continue
            decay = expected[0].get("decay", 0.0)
            decay_ok = math.isfinite(decay) and decay > 0.0
            if decay_ok:
                decay_values.append(decay)
            # A frequency-domain modal judgment needs enough cycles before a
            # T60 decay.  Eight cycles is the explicit resolution contract;
            # below it, attack bandwidth and mode frequency are not separable
            # by this FFT gate.  Report N/A rather than PASS or a fake failure.
            min_observable_t60 = material_min_observable_t60(expected[0]["freq"])
            if decay_ok and oracle_ok and decay < min_observable_t60:
                case = f"{eng}/{mat}"
                LAST_MATERIAL_UNVERIFIED.append(
                    dict(engine=eng, material=mat, model_t60=decay,
                         min_t60=min_observable_t60,
                         reason=f"<{MATERIAL_MIN_OBSERVED_CYCLES:.0f} observable cycles"))
                print(f"   {eng:11} material={mat:12} T60(model)={decay:8.3f}s "
                      f"-> N/A / UNVERIFIED (needs >= {min_observable_t60:.3f}s "
                      f"for {MATERIAL_MIN_OBSERVED_CYCLES:.0f} cycles at "
                      f"{expected[0]['freq']:.1f}Hz)")
                continue
            measured = measure_partials(sr, x, [m["freq"] for m in expected],
                                        analysis_t60=decay)
            f0_meas = measure_f0(x, sr, expected[0]["freq"], model_t60=decay)
            # F2: material-scan probes are frequency_mode="midi" too -- f0 is
            # pinned to 12-TET regardless of material, so the ET anchor is the
            # correct primary expectation here as well.
            freq_ok, rows, coverage = assess_partial_frequencies(
                expected, measured, spec["tol_pct"], f0_measured=f0_meas,
                f0_expected_et=midi_to_hz(midi))
            amp_ok = True
            amp_assessed = 0
            for row in rows[1:]:
                if not row["required"]:
                    continue
                amp_assessed += 1
                if row.get("rel_db") is None or row.get("model_db") is None:
                    amp_ok = False
                elif abs(row["rel_db"] - row["model_db"]) > AMPS_DB_TOL:
                    amp_ok = False
            # A physical modal material probe must expose at least one overtone.
            amp_ok = amp_ok and amp_assessed >= 1
            probe_ok = freq_ok and amp_ok and decay_ok and oracle_ok
            print(f"   {eng:11} material={mat:12} T60(model)={decay:8.3f}s "
                  f"freq={coverage['passed']}/{coverage['required']} "
                  f"amp={amp_assessed} {'PASS' if probe_ok else 'FAIL'}"
                  f"{(' [' + oracle_note + ']') if oracle_note else ''}")
            if not probe_ok:
                print(f"      -> {eng}/{mat}: dump/audio frequency, relative amplitude, "
                      "or finite model-T60 contract failed")
            overall_ok = overall_ok and probe_ok
        if len(decay_values) != len(materials):
            sensitivity_ok = False
            spread = float("nan")
        else:
            spread = max(decay_values) / min(decay_values)
            sensitivity_ok = spread >= 1.10
        print(f"   {eng:11} material T60 sensitivity spread={spread:.2f}x "
              f"-> {'PASS' if sensitivity_ok else 'FAIL'} (no-op threshold 1.10x)")
        overall_ok = overall_ok and sensitivity_ok
    print("   Scope note: this is an implementation/no-op gate. It does not prove "
          "that JSON material constants match a measured specimen.")
    if LAST_MATERIAL_UNVERIFIED:
        print(f"   UNVERIFIED/N/A: {len(LAST_MATERIAL_UNVERIFIED)} case(s): "
              + ", ".join(f"{c['engine']}/{c['material']}" for c in LAST_MATERIAL_UNVERIFIED))
    return overall_ok


# ── M1-1d: velocity-response implementation judgment ────────────────────────
# Velocity still multiplies modal force linearly, but the physical hammer
# contact time also changes with velocity and therefore changes spectrum/RMS.
# Judge rendered delta against the dump-derived hammer/modal prediction; +6 dB
# remains a reported nominal reference, not a hard assumption.
VELOCITY_LO = 48 / 127.0
VELOCITY_HI = 96 / 127.0
VELOCITY_DB_TARGET = 6.0    # physical law: amplitude ~ force -> +6 dB per doubling
VELOCITY_DB_TOL = 1.0       # +/-1.0 dB judgment window (ROADMAP_PHYSICS.md §6)
VELOCITY_EXEMPT_ENGINES = {"fm"}   # FM index also rises with velocity -> not a pure amplitude law
# F3 (2026-07-18): the physical-law bound itself. SOURCE (derivation):
# amplitude is proportional to excitation force, force proportional to
# velocity (linear law -- ModalResonator::excite()'s currentAmp =
# baseAmp * velocity, documented in src/score/ScoreParser.h §M6-6a); the
# probe doubles velocity (48/127 -> 96/127), so the level delta must be
# 20*log10(2) = +6.0206 dB. §6 registers this as "+6.0 ± 1.0 dB" -- the
# same ±1.0 dB window is applied around the exact 20*log10(2) value here.
#
# MEASUREMENT DOMAIN (2026-07-22, F3 domain fix -- see measure_band_rms_db()'s
# doc comment for the full physics): this law is per-mode, not broadband.
# judge_velocity() below therefore measures BOTH measured_delta and
# predicted_delta in the FUNDAMENTAL'S OWN +/-3% band (FUND_BAND_HALF_WIDTH),
# and prints the wideband RMS delta separately as INFORMATIONAL ONLY -- it is
# real (Hertz hammer contact-time tau_c ~ v^-1/5 reshapes the spectrum, higher
# partials brighten at higher velocity) but is a different mechanism than the
# amplitude~force law and must not be judged against it.
#
# HONEST RECORD, WIDEBAND (2026-07-18, MIDI 60, measured at introduction of
# this bound, superseded as the JUDGED metric by the domain fix above --
# kept as the informational-broadband record; Rule 2: numbers recorded,
# tolerance NOT widened, NO exemption added):
#   cimbalom        predicted +6.2621 dB (law dev +0.24) PASS
#   tongue_drum     predicted +7.0086 dB (law dev +0.99) PASS (0.01 margin)
#   water_gong      predicted +6.2905 dB (law dev +0.27) PASS
#   water_gong_free predicted +6.3739 dB (law dev +0.35) PASS
#   piano           predicted +7.4373 dB (law dev +1.42) FAIL (wideband --
#                   see FUNDAMENTAL-BAND RECORD below, the domain now judged)
# The excess over 6.0206 tracks the deep-audit's velocity-dependent hammer
# contact time (higher velocity -> shorter contact -> brighter spectrum ->
# extra RMS on top of the pure amplitude law); piano (felt hammer,
# strike-position override) shows the largest brightening. This is real
# physics in the WIDEBAND signal, not a broken velocity->amplitude multiply --
# see the fundamental-band record below, which is now the judged metric.
#
# HONEST RECORD, FUNDAMENTAL-BAND (2026-07-22/23, MIDI 60, directed
# verification after the domain fix -- 月月 authorized this measurement-
# domain repair 2026-07-22; §6 wording update is DocsSync's, not done here.
# predicted/measured are both f0-band per judge_velocity(); "law dev" is
# predicted vs the 6.0206 dB law; render (measured) tracked predicted within
# ~0.001-0.002 dB on every engine below, well inside tolerance):
#   cimbalom        predicted +6.0587 dB (law dev +0.04) PASS
#   tongue_drum     predicted +6.0574 dB (law dev +0.04) PASS
#   water_gong      predicted +6.0586 dB (law dev +0.04) PASS
#   water_gong_free predicted +6.0588 dB (law dev +0.04) PASS
#   piano           predicted +6.6702 dB (law dev +0.65) PASS
# All five now PASS -- piano's wideband-only violation (+1.42 dev, FAIL) is
# gone once measured on the fundamental's own band, confirming the main-loop
# diagnosis: the deep-audit's Hertz hammer contact-time brightening
# concentrates on partials above the fundamental (piano's wideband record
# above, +7.4373 dB, is the SAME render, still elevated -- that is the real,
# expected contact-time effect, now correctly kept informational instead of
# failing the amplitude~force law it never actually violated). No FAILs to
# report at this MIDI/velocity pair; if a future run turns one up, record it
# honestly here per Rule 2 -- do not widen the tolerance or add an exemption.
VELOCITY_LAW_DB = 20.0 * math.log10(2.0)   # 6.020599913279624


def assess_velocity_delta(measured_delta, predicted_delta):
    """Pure velocity judgment (unit-testable, shared by judge_velocity() and
    --selftest 4b). Two independent conditions, both required:
      match_ok: |measured - predicted| <= VELOCITY_DB_TOL
                (render conforms to the model's own prediction)
      law_ok  : |predicted - VELOCITY_LAW_DB| <= VELOCITY_DB_TOL
                (F3: the model's OWN predicted delta must satisfy the
                amplitude-proportional-to-force law. Without this, a modal
                engine whose velocity law was miscoded to, say, +9 dB per
                doubling would predict +9, render +9, and pass -- the
                judgment would have degenerated to dump self-consistency.)
    Returns (ok, {"match_ok": bool, "law_ok": bool})."""
    if not (math.isfinite(measured_delta) and math.isfinite(predicted_delta)):
        return False, dict(match_ok=False, law_ok=False)
    match_ok = abs(measured_delta - predicted_delta) <= VELOCITY_DB_TOL
    law_ok = abs(predicted_delta - VELOCITY_LAW_DB) <= VELOCITY_DB_TOL
    return match_ok and law_ok, dict(match_ok=match_ok, law_ok=law_ok)


def judge_velocity(cli, engines, notes, outdir):
    # F3 domain fix (2026-07-22): judge on the FUNDAMENTAL'S OWN +/-3% band
    # (measure_band_rms_db(), same Butterworth family as measure_t60()) --
    # the amplitude~force law is per-mode, not broadband; see the doc
    # comments on measure_band_rms_db() and VELOCITY_LAW_DB above. The old
    # wideband RMS delta (measure_levels()) is still printed, but now purely
    # INFORMATIONAL -- it also carries the Hertz hammer contact-time's
    # spectral brightening (HammerImpulse.h), which is real physics but a
    # different mechanism than the law being judged here, so it must not
    # drive the verdict.
    print("\n" + "-" * 70)
    print(f"Velocity-response judgment (vel {VELOCITY_LO:.3f} -> {VELOCITY_HI:.3f}; "
          f"JUDGED in the fundamental's own +/-{FUND_BAND_HALF_WIDTH * 100:.0f}% "
          f"band -- render delta vs dump-derived model AND model delta vs the "
          f"{VELOCITY_LAW_DB:.4f} dB physical law, tol +/-{VELOCITY_DB_TOL:.1f} dB. "
          f"Wideband RMS delta is printed below as INFORMATIONAL ONLY):")
    print(f"   {'engine':11} {'MIDI':>4} {'f0_lo':>8} {'f0_hi':>8} "
          f"{'f0_delta':>9} {'model_dB':>9}  verdict")
    overall_ok = True
    for eng in engines:
        exempt = eng in VELOCITY_EXEMPT_ENGINES
        for midi in notes:
            lo, lo_score = render_probe(cli, eng, midi, outdir, vel=VELOCITY_LO)
            hi, hi_score = render_probe(cli, eng, midi, outdir, vel=VELOCITY_HI)
            sr_lo, x_lo = read_wav_mono(lo)
            sr_hi, x_hi = read_wav_mono(hi)
            _, broadband_lo = measure_levels(sr_lo, x_lo)
            _, broadband_hi = measure_levels(sr_hi, x_hi)
            broadband_delta = broadband_hi - broadband_lo

            lo_event = None if exempt else dump_modes_event(cli, lo_score)
            hi_event = None if exempt else dump_modes_event(cli, hi_score)
            pred_f0 = None
            if lo_event and lo_event.get("partials"):
                pred_f0 = lo_event["partials"][0]["freq"]
            if not pred_f0:
                pred_f0 = midi_to_hz(midi)
            # measured f0 (not the nominal MIDI pitch) centers the band, same
            # convention as measure_t60()'s f0_meas argument.
            f0_center = measure_f0(x_hi, sr_hi, pred_f0) or pred_f0
            band_lo = measure_band_rms_db(sr_lo, x_lo, f0_center)
            band_hi = measure_band_rms_db(sr_hi, x_hi, f0_center)
            fund_delta = (band_hi - band_lo
                          if band_lo is not None and band_hi is not None
                          else float("nan"))

            if exempt:
                verdict = "EXEMPT (FM index also scales with velocity)"
                predicted_delta = float("nan")
            else:
                if not lo_event or not hi_event:
                    predicted_delta = float("nan")
                else:
                    lo_strings = lo_event.get("strings") or [lo_event["partials"]]
                    hi_strings = hi_event.get("strings") or [hi_event["partials"]]
                    lo_theory = synth_theory_signal(lo_strings, 48000, 2.0) * VELOCITY_LO
                    hi_theory = synth_theory_signal(hi_strings, 48000, 2.0) * VELOCITY_HI
                    theory_lo_band = measure_band_rms_db(48000, lo_theory, f0_center)
                    theory_hi_band = measure_band_rms_db(48000, hi_theory, f0_center)
                    predicted_delta = (theory_hi_band - theory_lo_band
                                       if theory_lo_band is not None
                                       and theory_hi_band is not None
                                       else float("nan"))
                ok, vdetail = assess_velocity_delta(fund_delta, predicted_delta)
                verdict = "PASS" if ok else "FAIL"
                if not ok:
                    if not vdetail["law_ok"] and math.isfinite(predicted_delta):
                        print(f"      model's own predicted f0-band delta="
                              f"{predicted_delta:+.2f} dB violates the "
                              f"amplitude~force law {VELOCITY_LAW_DB:+.4f} "
                              f"+/-{VELOCITY_DB_TOL:.1f} dB (F3 physical-law "
                              f"bound) -> FAIL.")
                    if not vdetail["match_ok"] and math.isfinite(predicted_delta):
                        print(f"      measured f0-band delta={fund_delta:+.2f} dB, "
                              f"expected {predicted_delta:+.2f} "
                              f"+/-{VELOCITY_DB_TOL:.1f} dB -> FAIL.")
                    print(f"      Do NOT widen tolerance; record and investigate "
                          f"the engine's velocity->amplitude law per ROADMAP_PHYSICS.md §1g.")
                overall_ok = overall_ok and ok
            predicted_s = f"{predicted_delta:+9.1f}" if math.isfinite(predicted_delta) else f"{'--':>9}"
            fund_lo_s = f"{band_lo:8.1f}" if band_lo is not None else f"{'--':>8}"
            fund_hi_s = f"{band_hi:8.1f}" if band_hi is not None else f"{'--':>8}"
            fund_delta_s = f"{fund_delta:+9.1f}" if math.isfinite(fund_delta) else f"{'--':>9}"
            print(f"   {eng:11} {midi:>4} {fund_lo_s} {fund_hi_s} "
                  f"{fund_delta_s} {predicted_s}  {verdict}")
            print(f"      broadband RMS delta = {broadband_delta:+.2f} dB "
                  f"(informational -- includes Hertz contact-time spectral-"
                  f"brightening, physically real, see HammerImpulse.h)")
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
AMPS_WEAK_DB = MODEL_REQUIRED_DB  # requiredness comes from model, never render weakness
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


def _score_probe_parameters(score_path):
    score = json.loads(Path(score_path).read_text(encoding="utf-8"))
    event = score["events"][0]
    return event, event.get("params") or {}


def stiff_string_oracle(score_path, count=40):
    """Independent StringModel frequency oracle for cimbalom/piano probes.

    This mirrors the published stiff-string equation, not --dump-modes.  It is
    used only to cross-check that the dump source itself has not drifted.  The
    rendered-audio gate then uses the dump frequencies, including actual
    per-event tuning and truncation, rather than assuming integer harmonics.
    """
    event, params = _score_probe_parameters(score_path)
    midi = int(event["note"])
    material_key = params.get("material", "steel")
    materials_path = Path(__file__).resolve().parent.parent / "data" / "materials.json"
    materials = json.loads(materials_path.read_text(encoding="utf-8"))["materials"]
    material = materials[material_key]
    diameter = float(params.get("diameter_mm", 0.8)) * 0.001
    length = 0.35 * 2.0 ** (-(midi - 69) / 12.0)
    radius = diameter * 0.5
    mu = float(material["density"]) * math.pi * radius * radius
    target = midi_to_hz(midi)
    tension_override = params.get("tension_n", 0.0)
    tension = float(tension_override) if tension_override not in (None, 0, 0.0) else (
        mu * (2.0 * length * target) ** 2)
    young = float(material["youngs_modulus"])
    bcoef = (math.pi ** 3 * young * diameter ** 4
             / (64.0 * tension * length * length))
    raw_f1 = (1.0 / (2.0 * length)) * math.sqrt(tension / mu)
    tuned_f1 = raw_f1 * math.sqrt(1.0 + bcoef)
    tune_scale = target / tuned_f1
    out = []
    for n in range(1, count + 1):
        raw = n * raw_f1 * math.sqrt(1.0 + bcoef * n * n)
        if raw > ANALYSIS_MAX_HZ:
            break
        out.append(raw * tune_scale)
    return out


def expected_modes_from_dump(cli, score_path, engine, sr, duration=AMPS_PROBE_DUR,
                             max_modes=None):
    """Return model modes with explicit amplitude-required coverage.

    Frequencies come from the exact per-event dump, never fixed harmonic
    integers.  The model amplitude threshold is derived from a theory-only
    synthesis of dump amplitudes/decays; a weak *render* cannot exempt itself.
    """
    event = dump_modes_event(cli, score_path)
    if not event or not event.get("partials"):
        return None, [], False, "--dump-modes returned no modal event"
    spec = ENGINES[engine]
    strings = event.get("strings") or [event["partials"]]
    wanted = spec["npart"] if max_modes is None else min(spec["npart"], max_modes)
    partials = event["partials"][:wanted]
    expected_freqs = []
    for mode_i, partial in enumerate(partials):
        voices = [voice[mode_i] for voice in strings if len(voice) > mode_i]
        weights = [(float(v.get("amp", 0.0)) * float(v.get("body_mag", 1.0))) ** 2
                   for v in voices]
        weight_sum = sum(weights)
        expected_freqs.append(
            sum(float(v["freq"]) * w for v, w in zip(voices, weights)) / weight_sum
            if weight_sum > 0.0 else float(partial["freq"]))
    synth = synth_theory_signal(strings, sr, duration)
    analysis_t60 = float(partials[0].get("decay", 0.0)) if partials else None
    theory_meas = measure_partials(sr, synth, expected_freqs,
                                   analysis_t60=analysis_t60)
    fund_mag = (theory_meas[0].get("mag", 0.0)
                if theory_meas and theory_meas[0].get("status") == "found" else 0.0)
    raw_strengths = []
    for mode_i in range(len(partials)):
        voices = [voice[mode_i] for voice in strings if len(voice) > mode_i]
        raw_strengths.append(math.sqrt(sum(
            (float(v.get("amp", 0.0)) * float(v.get("body_mag", 1.0))) ** 2
            for v in voices)))
    raw_fund = raw_strengths[0] if raw_strengths else 0.0
    # Requiredness uses a non-circular per-mode theory measurement: synthesize
    # each dumped mode in isolation through the same time window.  This keeps
    # real decay in the criterion (e.g. a raw-strong 150 ms mode can be
    # spectrally below -45 dB in a 500 ms window) without allowing the rendered
    # audio, combined-spectrum leakage, or a missing detector result to exempt
    # the mode.
    isolated_strengths = []
    for mode_i, freq in enumerate(expected_freqs):
        isolated_strings = [[voice[mode_i]] for voice in strings
                            if len(voice) > mode_i]
        isolated = synth_theory_signal(isolated_strings, sr, duration)
        isolated_result = measure_partials(
            sr, isolated, [freq], analysis_t60=analysis_t60)[0]
        isolated_strengths.append(isolated_result.get("mag", 0.0)
                                  if isolated_result.get("status") == "found" else 0.0)
    isolated_fund = isolated_strengths[0] if isolated_strengths else 0.0
    modes = []
    for mode_i, (partial, result) in enumerate(zip(partials, theory_meas)):
        model_db = (_db_ratio(result["mag"], fund_mag)
                    if result.get("status") == "found" and fund_mag > 0 else -240.0)
        raw_model_db = (_db_ratio(raw_strengths[mode_i], raw_fund)
                        if raw_fund > 0.0 else -240.0)
        isolated_model_db = (_db_ratio(isolated_strengths[mode_i], isolated_fund)
                             if isolated_fund > 0.0 else -240.0)
        required = isolated_model_db >= MODEL_REQUIRED_DB
        modes.append(dict(freq=expected_freqs[len(modes)], model_db=model_db,
                          raw_model_db=raw_model_db,
                          isolated_model_db=isolated_model_db,
                          required=required,
                          decay=float(partial.get("decay", 0.0))))

    oracle_ok = True
    oracle_notes = []
    if engine in ("cimbalom", "piano"):
        oracle = stiff_string_oracle(score_path, count=len(partials))
        if len(oracle) != len(partials):
            oracle_ok = False
            oracle_notes.append(
                f"stiff-string oracle count {len(oracle)} != dump {len(partials)}")
        elif oracle:
            # Compare ratios on one dumped string.  Absolute frequencies carry
            # the deliberately detuned course offset (and high-mode string
            # truncation can move the multi-string centroid); ratios cancel
            # that rendering detail and isolate the independent stiff-string B
            # equation this oracle is meant to test.
            dumped = [float(p["freq"]) for p in partials]
            max_err = max(abs((got / dumped[0]) / (want / oracle[0]) - 1.0) * 100.0
                          for got, want in zip(dumped, oracle))
            stiff_ok = max_err <= 0.10
            oracle_ok = oracle_ok and stiff_ok
            oracle_notes.append(f"stiff-string oracle max error {max_err:.4f}%")
    return event, modes, oracle_ok, "; ".join(oracle_notes)


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
    event, expected, oracle_ok, oracle_note = expected_modes_from_dump(
        cli, sf, engine, AMPS_PROBE_SR, AMPS_PROBE_DUR, max_modes=AMPS_NPART)
    if not event or not expected:
        return False, []
    pred_freqs = [mode["freq"] for mode in expected]
    sr, x = read_wav_mono(wav)
    model_t60 = expected[0]["decay"]
    meas = measure_partials(sr, x, pred_freqs, analysis_t60=model_t60)
    f0_meas = measure_f0(x, sr, pred_freqs[0], model_t60=model_t60)
    return assess_partial_amplitudes(expected, meas, f0_meas=f0_meas,
                                     oracle_ok=oracle_ok,
                                     oracle_note=oracle_note)


def assess_partial_amplitudes(expected, meas, f0_meas=None,
                              oracle_ok=True, oracle_note=""):
    """Pure per-partial amplitude judgment, factored out of judge_amps()
    (2026-07-18, task 4a) so the --selftest wrong-amplitude counterexample
    exercises the IDENTICAL code path the real M2-2d gate uses. Logic is
    byte-for-byte the former judge_amps() loop; tolerances unchanged
    (AMPS_DB_TOL = ±3.0 dB, §6)."""
    rows = []
    fund_mag = (meas[0].get("mag", 0.0)
                if meas and meas[0].get("status") == "found" else 0.0)
    probe_ok = oracle_ok
    required_overtones = 0
    passed_overtones = 0
    for i, (mode, result) in enumerate(zip(expected, meas), 1):
        pred_db = mode["model_db"]
        required = mode["required"]
        if result.get("status") != "found":
            verdict = (result.get("status", "missing").upper() if required
                       else "MODEL-WEAK (not required)")
            rows.append(dict(n=i, freq=mode["freq"], pred_db=pred_db,
                              meas_db=None, err_db=None, verdict=verdict))
            if required:
                probe_ok = False
                if i > 1:
                    required_overtones += 1
            continue
        fmeas, mag = result["freq"], result["mag"]
        if i == 1 and f0_meas:
            fmeas = f0_meas
        meas_db = _db_ratio(mag, fund_mag) if fund_mag > 0 else -240.0
        if i == 1:
            rows.append(dict(n=i, freq=fmeas, pred_db=0.0, meas_db=0.0,
                              err_db=0.0, verdict="ref (0 dB)"))
            continue
        if not required:
            rows.append(dict(n=i, freq=fmeas, pred_db=pred_db, meas_db=meas_db,
                              err_db=None, verdict="MODEL-WEAK (not required)"))
            continue
        required_overtones += 1
        err_db = meas_db - pred_db
        # A model-required overtone cannot excuse itself by rendering weak.
        ok = abs(err_db) <= AMPS_DB_TOL and meas_db >= AMPS_WEAK_DB
        probe_ok = probe_ok and ok
        passed_overtones += int(ok)
        rows.append(dict(n=i, freq=fmeas, pred_db=pred_db, meas_db=meas_db,
                          err_db=err_db, verdict="PASS" if ok else "FAIL"))
    if required_overtones < 1 or passed_overtones != required_overtones:
        probe_ok = False
    if oracle_note and not oracle_ok:
        rows.append(dict(n=0, freq=0.0, pred_db=0.0, meas_db=None,
                         err_db=None, verdict="ORACLE FAIL: " + oracle_note))
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
    """Runs the complete implementation gate: multi-note range scan (1b)
    for every engine, material-sensitivity scan (1c) for modal engines, and the
    velocity-linearity judgment (1d) for every engine. Also runs the M2-2d
    partial-amplitude judgment and measured modal T60 for every physical modal
    engine, so --full covers pitch/partials/amplitude/decay rather than leaving
    the decay gate opt-in.
    Exit-code-affecting; every sub-check must pass for --full to report
    success.

    skip_amps=True restricts --full to its M1 scope (1b+1c+1d), for CI while
    M2-2d remediation is still in progress. This is NOT a tolerance change and
    NOT a silent gate-shrink: the M2 GATE (--amps) is unaffected and still
    FAILs honestly, CI runs a separate always-visible non-blocking --amps step,
    and M2 stays "In progress" in ROADMAP_PHYSICS.md until 2d passes for real.
    Scope decision approved by 月月 2026-07-09 (delegated via Fable) — see
    TODO.md CI-coupling entry."""
    global LAST_FULL_UNVERIFIED
    LAST_FULL_UNVERIFIED = []
    print("=" * 70)
    print("--full: implementation gate (eigenvalue anchors + range + material "
          "sensitivity + velocity)"
          + (" [--skip-amps: M1 scope only, M2-2d amplitude judgment NOT run]"
             if skip_amps else " + M2 amplitude judgment")
          + " + measured T60 + residual energy (informational)")
    print("=" * 70)

    # F1: dump-only eigenvalue anchors first (cheap, no audio) — they catch a
    # corrupted C++ beam/plate table BEFORE the render-vs-dump checks, which
    # by construction cannot see that class of error.
    eig_ok = scan_eigenvalue_anchors(cli, outdir, engines=engines)

    range_ok = scan_engine_ranges(cli, engines, outdir, n=6)

    material_engines = [e for e in engines if e in MATERIAL_SCAN_ENGINES]
    material_ok = True
    if material_engines:
        material_ok = scan_materials(cli, outdir, engines=material_engines)
        LAST_FULL_UNVERIFIED.extend(LAST_MATERIAL_UNVERIFIED)
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

    t60_engines = [e for e in engines if e in AMPS_SCAN_ENGINES]
    t60_ok = True
    if t60_engines:
        # Two fixed notes keep this auditable and match the standalone --t60
        # default.  T60's adaptive probe may extend to 30 s when needed.
        t60_ok = report_t60(cli, t60_engines, [60, 72], outdir)
    else:
        print("\n(T60 judgment skipped: no physical modal engines requested)")

    # F5: informational only — printed, never ANDed into the gate result.
    report_residual_energy(cli, engines, outdir)

    print("\n" + "=" * 70)
    print("--full summary:")
    print(f"   F1 eigenvalue anchors: {'PASS' if eig_ok else 'FAIL'}")
    print(f"   1b note-range scan   : {'PASS' if range_ok else 'FAIL'}")
    material_summary = "FAIL" if not material_ok else "CHECKED CASES PASS"
    if LAST_FULL_UNVERIFIED:
        material_summary += f"; {len(LAST_FULL_UNVERIFIED)} UNVERIFIED/N/A"
    print(f"   1c material sensitivity: {material_summary}")
    print(f"   1d velocity judgment : {'PASS' if velocity_ok else 'FAIL'}")
    print(f"   2d amplitude judgment: "
          f"{'SKIPPED (--skip-amps)' if skip_amps else ('PASS' if amps_ok else 'FAIL')}")
    print(f"   5b measured T60       : {'PASS' if t60_ok else 'FAIL'}")
    print("   F5 residual energy   : informational only (threshold pending "
          "approval; see lines above)")
    if LAST_FULL_UNVERIFIED:
        print("   Unverified ranges      : "
              + ", ".join(f"{c['engine']}/{c['material']} "
                          f"(T60 {c['model_t60']:.3f}s < {c['min_t60']:.3f}s)"
                          for c in LAST_FULL_UNVERIFIED))

    return (eig_ok and range_ok and material_ok and velocity_ok
            and amps_ok and t60_ok)


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
# T60_RATIO_TOLERANCE) still independently re-derives T60 from the
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
    peak_time_s = peak_idx / sr
    t = np.arange(n) / sr
    logenv = 20.0 * np.log10(np.maximum(seg, 1e-12) / peak_val)

    start_t = T60_ATTACK_SKIP_S
    # t=0 above is the envelope peak, while noteoff_time_s is absolute from
    # the beginning of the WAV.  Convert note-off to this peak-relative axis.
    # The old code mixed the two axes and included accelerated post-note-off
    # release in the fit, under-reporting long T60 values by roughly 7-15%.
    noteoff_relative_s = noteoff_time_s - peak_time_s
    end_candidates = [max(start_t, noteoff_relative_s - T60_NOTEOFF_MARGIN_S)]
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


# ── F3 domain fix (2026-07-22): fundamental-band RMS for the velocity law ──
# PHYSICS: "amplitude proportional to velocity/force" is a PER-MODE law --
# ModalResonator::excite() multiplies velocity linearly into EACH mode's own
# amplitude. It says nothing about broadband RMS, which also carries the
# Hertz hammer/mallet contact time's velocity dependence (HammerImpulse.h:
# tau_c ~ v^-1/5, +/-20% clamp). A shorter contact time at higher velocity
# reshapes the SPECTRUM (raises high-partial gain -> brighter tone), which is
# real physics but a SEPARATE mechanism from the amplitude~force law. Folding
# both mechanisms into one wideband RMS number conflates them: round-2's F3
# gate measured piano's wideband delta at +7.4373 dB and flagged the
# amplitude law as violated, when the excess above +6.0206 dB was actually
# the (real, expected) contact-time spectral brightening, not a broken
# velocity->amplitude multiply.
# FIX: judge the law on the FUNDAMENTAL'S OWN narrow band only. The
# fundamental is the cleanest single-mode observation window for this
# specific law: at the fundamental, omega0*tau_c sits far from the transfer
# function's spectral zeros/nulls that a shortened tau_c would sweep past
# (those effects concentrate at higher partials -- see HammerImpulse.h), so
# |H(omega0)| moves only slightly (main-loop estimate: ~+0.4 dB for felt
# tau_c 2ms->1.74ms at 261.6 Hz) as tau_c changes with velocity. That leaves
# the fundamental-band RMS delta dominated by the amplitude~force multiply
# ModalResonator::excite() actually implements -- the correct place to judge
# it. Reuses measure_t60()'s own +/-3% zero-phase 4th-order Butterworth band
# (T60_BAND_HALF_WIDTH) -- same physical justification (narrow enough to
# isolate one partial, wide enough to admit a detuned/beating string course)
# and the same measurement family already vetted by that gate.
FUND_BAND_HALF_WIDTH = T60_BAND_HALF_WIDTH


def measure_band_rms_db(sr, x, f0_center, half_width=FUND_BAND_HALF_WIDTH,
                         window_s=1.5):
    """RMS level (dBFS) of `x` after isolating a narrow +/-half_width band
    around f0_center with the SAME zero-phase 4th-order Butterworth bandpass
    method measure_t60() uses (see FUND_BAND_HALF_WIDTH doc above) -- this is
    the fundamental-band measurement the F3 velocity-law judgment (
    judge_velocity()) uses instead of wideband measure_levels(). `window_s`
    mirrors measure_levels()'s own 1.5 s analysis window so the two measures
    stay comparable at a glance in the informational broadband printout.
    Returns None if scipy is unavailable or the band can't be built (bad
    f0_center/sr) -- callers must treat that as "unmeasurable", not zero."""
    try:
        from scipy.signal import butter, sosfiltfilt
    except Exception:
        return None
    if not (f0_center and math.isfinite(f0_center) and f0_center > 0):
        return None
    nyq = sr / 2.0
    lo = f0_center * (1.0 - half_width) / nyq
    hi = f0_center * (1.0 + half_width) / nyq
    if not (0.0 < lo < hi < 1.0):
        return None
    seg = x[:int(window_s * sr)] if len(x) > int(window_s * sr) else x
    if len(seg) == 0:
        return None
    band = sosfiltfilt(butter(4, [lo, hi], btype="band", output="sos"), seg)
    rms = float(np.sqrt(np.mean(band * band)))
    return 20.0 * math.log10(rms) if rms > 1e-9 else -120.0


def _synthetic_modal_signal(sr, duration, freqs, amps=None):
    t = np.arange(int(sr * duration), dtype=np.float64) / sr
    amps = amps or [1.0] * len(freqs)
    x = np.zeros_like(t)
    for freq, amp in zip(freqs, amps):
        x += amp * np.sin(2.0 * np.pi * freq * t)
    return x


def selftest_measure_t60_relative_axis():
    """Known T60 with delayed onset and accelerated post-note-off release.

    The delayed onset makes absolute WAV time differ materially from the
    peak-relative fit axis.  Including post-note-off release (the old bug)
    produces a clearly wrong slope; the corrected path recovers 2.0 s.
    """
    sr = 48000
    f0 = 440.0
    known_t60 = 2.0
    onset = 0.60
    noteoff = 3.20
    total = 5.0
    t = np.arange(int(sr * total), dtype=np.float64) / sr
    x = np.zeros_like(t)
    active = t >= onset
    elapsed = t[active] - onset
    env = np.exp(-MODAL_DECAY_LN1000 * elapsed / known_t60)
    release_elapsed = np.maximum(t[active] - noteoff, 0.0)
    env *= np.exp(-MODAL_DECAY_LN1000 * release_elapsed / 0.15)
    x[active] = env * np.sin(2.0 * np.pi * f0 * elapsed)
    measured, span = measure_t60(sr, x, f0, 0.0, noteoff)
    ratio = measured / known_t60 if measured else None
    ok = measured is not None and span is not None and span >= T60_MIN_SPAN_DB
    ok = ok and 0.95 <= ratio <= 1.05
    return ok, measured, span


def selftest_partial_negative_injections():
    """Adversarial regressions for the historical false-green paths."""
    sr = 48000
    expected_freqs = [440.0, 880.0, 1320.0, 1760.0, 2200.0]
    expected = [dict(freq=f, model_db=0.0, required=True) for f in expected_freqs]

    positive = _synthetic_modal_signal(sr, 0.7, expected_freqs)
    positive_ok, _, _ = assess_partial_frequencies(
        expected, measure_partials(sr, positive, expected_freqs), 1.0)

    shifted = _synthetic_modal_signal(
        sr, 0.7, [440.0] + [f * 1.5 for f in expected_freqs[1:]])
    shifted_ok, _, _ = assess_partial_frequencies(
        expected, measure_partials(sr, shifted, expected_freqs), 3.0)

    missing = _synthetic_modal_signal(sr, 0.7, expected_freqs[:2])
    missing_ok, _, _ = assess_partial_frequencies(
        expected, measure_partials(sr, missing, expected_freqs), 3.0)

    super_nyquist_expected = [dict(freq=440.0, model_db=0.0, required=True),
                              dict(freq=30000.0, model_db=0.0, required=True)]
    nyquist_ok, _, _ = assess_partial_frequencies(
        super_nyquist_expected,
        measure_partials(sr, positive, [440.0, 30000.0]), 3.0)

    overlap_expected = [dict(freq=1000.0, model_db=0.0, required=True),
                        dict(freq=1050.0, model_db=0.0, required=True)]
    one_peak = _synthetic_modal_signal(sr, 0.7, [1025.0])
    overlap_ok, _, _ = assess_partial_frequencies(
        overlap_expected, measure_partials(sr, one_peak, [1000.0, 1050.0]), 6.0)

    results = {
        "positive_control": positive_ok,
        "50pct_shift_rejected": not shifted_ok,
        "missing_p3_p5_rejected": not missing_ok,
        "super_nyquist_rejected": not nyquist_ok,
        "overlap_peak_reuse_rejected": not overlap_ok,
    }
    return all(results.values()), results


def selftest_amps_wrong_amplitude():
    """4a (2026-07-18): wrong-amplitude counterexample. A synthetic 'render'
    whose partial 3 is deliberately +6 dB hot (well outside the ±3 dB
    AMPS_DB_TOL) must FAIL the amplitude judgment, through the SAME
    assess_partial_amplitudes() path the real M2-2d gate uses; the honest
    signal is the positive control and must PASS."""
    sr = 48000
    freqs = [440.0, 880.0, 1320.0, 1760.0, 2200.0]
    model_db = [0.0, -6.0, -12.0, -18.0, -24.0]
    expected = [dict(freq=f, model_db=db, required=True)
                for f, db in zip(freqs, model_db)]
    honest_amps = [10.0 ** (db / 20.0) for db in model_db]
    honest = _synthetic_modal_signal(sr, 0.7, freqs, honest_amps)
    ok_pos, _ = assess_partial_amplitudes(
        expected, measure_partials(sr, honest, freqs))
    wrong_amps = list(honest_amps)
    wrong_amps[2] *= 10.0 ** (6.0 / 20.0)   # partial 3: +6 dB off
    wrong = _synthetic_modal_signal(sr, 0.7, freqs, wrong_amps)
    ok_neg, rows_neg = assess_partial_amplitudes(
        expected, measure_partials(sr, wrong, freqs))
    p3 = next((r for r in rows_neg if r["n"] == 3), None)
    p3_flagged = p3 is not None and p3["verdict"] == "FAIL"
    ok = ok_pos and (not ok_neg) and p3_flagged
    detail = (f"honest={'PASS' if ok_pos else 'FAIL'}, +6dB-p3 "
              f"{'rejected' if not ok_neg else 'ACCEPTED (bug)'}"
              + (f", p3 err={p3['err_db']:+.2f} dB" if p3 and p3.get("err_db")
                 is not None else ""))
    return ok, detail


def selftest_velocity_law_negative():
    """4b (2026-07-22, F3 domain fix): FUNDAMENTAL-BAND velocity counter-
    example. The amplitude~force law is per-mode (see measure_band_rms_db()'s
    doc comment), so a counterexample must inject the violation into the
    fundamental's OWN band and be caught by the SAME +/-3% Butterworth
    measurement (measure_band_rms_db()) the real F3 gate (judge_velocity())
    uses -- not just anywhere in the spectrum.

    Two widely separated partials are synthesized: a weak fundamental
    (440 Hz, amp 0.05) and a MUCH stronger overtone (880 Hz, amp 1.0, 400x
    the power) -- a naive wideband RMS delta would be dominated by the
    overtone and could mask a fundamental-only violation entirely (this is
    the exact scenario the domain fix exists to catch: round-2's F3 read a
    wideband number that mixed two different physical mechanisms). Between
    lo/hi velocity, the overtone scales by the LAWFUL 2.0x (+6.0206 dB) but
    the fundamental scales by 2.0 * 10**(3/20) (+9.0206 dB, +3 dB over the
    law). Asserts (a) the render disagrees with a law-abiding model, (b) the
    model itself predicting the unlawful delta still fails the law bound,
    (c) an all-lawful control passes, and (d) the fundamental-band domain is
    actually what catches it -- the SAME bad pair's wideband delta must land
    far closer to the lawful 6.0206 dB than the fundamental-band delta does."""
    sr = 48000
    f0, f1 = 440.0, 880.0
    lo_amps = [0.05, 1.0]
    lawful_factor = 2.0                              # exactly VELOCITY_LAW_DB
    unlawful_factor = 2.0 * 10.0 ** (3.0 / 20.0)      # +3 dB over the law

    lo = _synthetic_modal_signal(sr, 0.7, [f0, f1], lo_amps)
    hi_bad = _synthetic_modal_signal(
        sr, 0.7, [f0, f1],
        [lo_amps[0] * unlawful_factor, lo_amps[1] * lawful_factor])
    hi_good = _synthetic_modal_signal(
        sr, 0.7, [f0, f1], [a * lawful_factor for a in lo_amps])

    band_lo = measure_band_rms_db(sr, lo, f0)
    band_hi_bad = measure_band_rms_db(sr, hi_bad, f0)
    band_hi_good = measure_band_rms_db(sr, hi_good, f0)
    delta_bad = band_hi_bad - band_lo    # ~= +9.02 dB, fundamental-band only
    delta_good = band_hi_good - band_lo  # ~= +6.02 dB, lawful control

    bad_render_ok, _ = assess_velocity_delta(delta_bad, VELOCITY_LAW_DB)
    bad_model_ok, bad_model_detail = assess_velocity_delta(delta_bad, delta_bad)
    good_ok, _ = assess_velocity_delta(delta_good, VELOCITY_LAW_DB)

    broadband_delta_bad = measure_levels(sr, hi_bad)[1] - measure_levels(sr, lo)[1]
    domain_matters = (abs(delta_bad - VELOCITY_LAW_DB)
                       > abs(broadband_delta_bad - VELOCITY_LAW_DB) + 1.0)

    ok = ((not bad_render_ok) and (not bad_model_ok)
          and (not bad_model_detail["law_ok"]) and good_ok and domain_matters)
    return ok, (f"f0-band delta {delta_bad:+.2f} dB rejected both ways "
                f"(wideband would have read {broadband_delta_bad:+.2f} dB, "
                f"masking the violation)")


def selftest_velocity_law_negative_uniform_scale():
    """4b legacy regression (2026-07-18 original, kept per 月月's 2026-07-22
    instruction to retain both if adjustable): the SAME violation factor is
    applied uniformly to the whole signal (not fundamental-only), so wideband
    and fundamental-band measurements agree -- this is a domain-independent
    sanity check that assess_velocity_delta() still rejects a uniformly
    mis-scaled +9 dB doubling, now measured through measure_band_rms_db()
    (the fundamental-band path judge_velocity() actually uses) instead of the
    old measure_levels() wideband path."""
    sr = 48000
    f0 = 440.0
    base = _synthetic_modal_signal(sr, 0.7, [f0, 880.0], [1.0, 0.5]) * 0.05
    bad_hi = base * (10.0 ** (9.0 / 20.0))
    band_lo = measure_band_rms_db(sr, base, f0)
    band_hi = measure_band_rms_db(sr, bad_hi, f0)
    delta = band_hi - band_lo   # ~= +9.0 dB, measured through measure_band_rms_db()
    bad_render_ok, _ = assess_velocity_delta(delta, VELOCITY_LAW_DB)
    bad_model_ok, bad_model_detail = assess_velocity_delta(delta, delta)
    good_ok, _ = assess_velocity_delta(VELOCITY_LAW_DB, VELOCITY_LAW_DB)
    ok = ((not bad_render_ok) and (not bad_model_ok)
          and (not bad_model_detail["law_ok"]) and good_ok)
    return ok, f"uniform-scale f0-band delta {delta:+.2f} dB rejected both ways"


def run_internal_selftests():
    f0_ok, f0_cents = selftest_measure_f0_short_window()
    t60_ok, t60_measured, t60_span = selftest_measure_t60_relative_axis()
    partial_ok, partial_results = selftest_partial_negative_injections()
    amps_ok, amps_detail = selftest_amps_wrong_amplitude()
    vel_ok, vel_detail = selftest_velocity_law_negative()
    vel_uniform_ok, vel_uniform_detail = selftest_velocity_law_negative_uniform_scale()
    return {
        "short_t60_f0": (f0_ok, f"{f0_cents:+.3f} cents" if f0_cents is not None else "none"),
        "relative_axis_t60": (t60_ok,
                               f"{t60_measured:.4f}s span={t60_span:.1f}dB"
                               if t60_measured is not None and t60_span is not None else "none"),
        **{name: (ok, "") for name, ok in partial_results.items()},
        "partial_negative_suite": (partial_ok, ""),
        "amps_wrong_amplitude_rejected": (amps_ok, amps_detail),
        "velocity_law_violation_rejected": (vel_ok, vel_detail),
        "velocity_law_violation_rejected_uniform": (vel_uniform_ok, vel_uniform_detail),
    }


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


# ── F5 (2026-07-18): residual spectral energy — INFORMATIONAL ONLY ──────────
# Blind-spot being instrumented: every existing gate asks "are the PREDICTED
# modes present and right?" — none asks "is there ENERGY the model did NOT
# predict?" (e.g. an accidentally-enabled extra oscillator, aliasing, or FX
# leakage would pass all mode-presence checks). This measures, during the
# sounding period, the spectral energy OUTSIDE all predicted modal bands
# (each ±3%, matching T60_BAND_HALF_WIDTH's convention) and OUTSIDE the
# documented exciter-noise window, in dB relative to total energy.
# NO EXIT-CODE EFFECT: a pass/fail threshold needs 月月's approval first
# (§6 Rule 2 — thresholds are registered, not invented mid-fix).
#
# Documented exciter-noise window (time-domain exclusion): both engines add a
# white-noise burst through an ExpDecay envelope at note-on. Envelope T60s,
# read off the source (not measured from audio):
#   CimbalomEngine.h  setupExciter(): durations[] = {4,3,2,1} ms scaled by
#     durScale = jlimit(0.5, 3.0, ...)  -> worst case 4 ms * 3.0 = 12 ms
#   ChromaticEngine.h setupExciter(): durations[] = {5,3,2,1} ms, no scale
# ExpDecay (src/dsp/Envelope.h) decays -60 dB per T60, so by
# 2.5 * 12 ms = 30 ms the noise is <= -150 dB — negligible in this measure.
EXCITER_NOISE_SKIP_S = 0.030
RESIDUAL_BAND_HALF_WIDTH = 0.03   # ±3% per predicted mode, per task spec


def measure_residual_energy(sr, x, mode_freqs, noteoff_time_s):
    """Returns residual energy in dB relative to total energy (both measured
    over the sounding period [EXCITER_NOISE_SKIP_S, note-off] with a Hann
    window, bins up to the analysis limit), or None if the segment is
    unusable. Residual = total minus every bin inside ±3% of ANY predicted
    mode frequency (all strings' modes, straight from --dump-modes)."""
    i0 = int(EXCITER_NOISE_SKIP_S * sr)
    i1 = min(len(x), int(noteoff_time_s * sr))
    seg = x[i0:i1]
    if len(seg) < 256:
        return None
    seg = np.asarray(seg, dtype=np.float64) * np.hanning(len(seg))
    nfft = 1 << int(math.ceil(math.log2(len(seg))))
    spec = np.abs(np.fft.rfft(seg, nfft)) ** 2
    binhz = sr / nfft
    limit = analysis_frequency_limit(sr)
    kmax = min(len(spec) - 1, int(limit / binhz))
    power = spec[1:kmax + 1]
    total = float(power.sum())
    if total <= 0.0:
        return None
    freqs = np.arange(1, kmax + 1) * binhz
    inband = np.zeros(len(power), dtype=bool)
    for f in mode_freqs:
        f = float(f)
        if not (0.0 < f <= limit * (1.0 + RESIDUAL_BAND_HALF_WIDTH)):
            continue
        inband |= ((freqs >= f * (1.0 - RESIDUAL_BAND_HALF_WIDTH))
                   & (freqs <= f * (1.0 + RESIDUAL_BAND_HALF_WIDTH)))
    residual = float(power[~inband].sum())
    return 10.0 * math.log10(max(residual, 1e-300) / total)


def report_residual_energy(cli, engines, outdir, midi=60):
    """F5 driver: one probe per modal engine. INFORMATIONAL, never affects
    the exit code — see the block comment above."""
    scan_engines = [e for e in AMPS_SCAN_ENGINES if engines is None or e in engines]
    if not scan_engines:
        return
    print("\n" + "-" * 70)
    print(f"Residual spectral energy outside predicted modal bands "
          f"(MIDI {midi}, bands ±{RESIDUAL_BAND_HALF_WIDTH * 100:.0f}% per "
          f"dumped mode, first {EXCITER_NOISE_SKIP_S * 1000:.0f} ms exciter-"
          f"noise window excluded):")
    for eng in scan_engines:
        try:
            wav, sf = render_probe(cli, eng, midi, outdir, tag="_resid")
            sr, x = read_wav_mono(wav)
            event = dump_modes_event(cli, sf)
        except RuntimeError as exc:
            print(f"   {eng:11} residual: NOT MEASURED ({exc}) "
                  f"[informational, threshold pending approval]")
            continue
        if not event or not event.get("partials"):
            print(f"   {eng:11} residual: NOT MEASURED (--dump-modes gave no "
                  f"modes) [informational, threshold pending approval]")
            continue
        strings = event.get("strings") or [event["partials"]]
        mode_freqs = sorted({float(m["freq"]) for voice in strings for m in voice})
        noteoff = 2.0 * T60_NOTEOFF_RATIO   # render_probe default dur=2.0
        rdb = measure_residual_energy(sr, x, mode_freqs, noteoff)
        if rdb is None:
            print(f"   {eng:11} residual: NOT MEASURED (unusable segment) "
                  f"[informational, threshold pending approval]")
        else:
            print(f"   {eng:11} residual: {rdb:+7.1f} dB re total "
                  f"({len(mode_freqs)} predicted modes) "
                  f"[informational, threshold pending approval]")
    print("   (No PASS/FAIL: this quantifies UNPREDICTED energy; a judgment "
          "threshold awaits 月月's approval per §6 Rule 2.)")


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
                         "ratio tol 0.80-1.25")
    ap.add_argument("--amps", action="store_true",
                    help="M2-2d: judge first-5-partial relative amplitude (dB "
                         "re fundamental) vs --dump-modes theory, all modal "
                         "engines (FM excluded) at MIDI 60; tol +/-3.0 dB "
                         "(ROADMAP_PHYSICS.md §6)")
    ap.add_argument("--full", action="store_true",
                    help="complete implementation gate: note-range, material "
                         "sensitivity, velocity, modal amplitude, and measured "
                         "T60; exit 0 only if every sub-check passes")
    ap.add_argument("--skip-amps", action="store_true",
                    help="with --full: restrict to M1 scope (1b+1c+1d), omit the "
                         "M2-2d amplitude judgment. For CI while M2 remediation "
                         "is in progress (月月-approved 2026-07-09); the M2 GATE "
                         "`--amps` is unaffected. No effect without --full.")
    ap.add_argument("--selftest", action="store_true",
                    help="synthetic metrology suite: short-decay f0, known T60 "
                         "on the peak-relative time axis, adversarial "
                         "partial injections (50%% shift, missing p3-p5, "
                         "super-Nyquist, overlapping-window peak reuse), a "
                         "+6dB wrong-amplitude partial (4a), and a "
                         "fundamental-band velocity delta violating the "
                         "+6.02dB law plus a uniform-scale legacy variant (4b)")
    args = ap.parse_args()

    if args.selftest:
        results = run_internal_selftests()
        all_ok = True
        for name, (ok, detail) in results.items():
            print(f"{name}: {'PASS' if ok else 'FAIL'}"
                  f"{(' (' + detail + ')') if detail else ''}")
            all_ok = all_ok and ok
        return 0 if all_ok else 1

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
        probes_ok = run(cli, args.engines, args.notes, od)
        # F1: the default probe run also carries the eigenvalue anchors for
        # any requested beam/plate engine (dump-only, no extra renders), so
        # the independent-anchor property holds outside --full too.
        return scan_eigenvalue_anchors(cli, od, engines=args.engines) and probes_ok

    if args.keep:
        outdir = Path(__file__).resolve().parent.parent / "build" / "physics_verify"
        outdir.mkdir(parents=True, exist_ok=True)
        ok = do(outdir)
    else:
        with tempfile.TemporaryDirectory() as td:
            ok = do(Path(td))

    print("\n" + "=" * 70)
    if args.full and ok and LAST_FULL_UNVERIFIED:
        print("RESULT: NO CHECKED FAILURES; UNVERIFIED/N/A RANGES REPORTED")
    elif args.full or args.amps or args.t60:
        print("RESULT:", "ALL WITHIN TOLERANCE" if ok else "SOME CHECKS FAILED")
    else:
        print("RESULT:", "ALL WITHIN TOLERANCE" if ok else "SOME PROBES OUT OF TOLERANCE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
