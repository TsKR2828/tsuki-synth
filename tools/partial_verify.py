#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
partial_verify.py -- partial (overtone) FREQUENCY internal-consistency check,
plus harmonic-aware pitch-via-partials for weak-fundamental events (WF0908-P1).

WHY / SCOPE (A13 decision packet, reports/decision_packets/
A13_partial_gate_domain.zh-TW.md, 選項 B+; design doc
docs/EARFREE_MELODY_GATE_DESIGN.zh-TW.md §8.6):

  * TsukiSynth's rigid-string partial model (f_n = n*f1*sqrt(1+B*n^2)) matches
    the physics literature's own model-vs-measurement agreement (Fletcher
    1964 JASA 36(1): RMS 0.99 cents / max 1.82 cents on a solid high string,
    A13 §2.2-A2) -- so "does the rendered audio's partial frequency match
    what the ENGINE ITSELF predicted via --dump-modes" is a claim that can be
    judged, reusing the EXISTING product tolerance (melody_verify.
    PITCH_TOL_CENTS = 5.0 cents, ratified 2026-07-23). No new tolerance is
    introduced (R2).
  * This is explicitly NOT "the engine matches a real piano" -- A13 §3.3
    found the engine's inharmonicity coefficient B is 2.4-5.4x a reference
    Hamilton upright piano's B at A4/G5/F#6/G6/D7 (string-geometry modeling
    choice, not this tool's concern; see --b-report below).
  * Partial AMPLITUDE has no sourced, non-arbitrary external tolerance (A13
    §4 選項 C: even 2024/2025 physics-informed neural piano models only give
    qualitative amplitude statements, never a defensible dB threshold) --
    amplitude is RECORDED ONLY, never judged. Every amplitude field in this
    tool's output carries "amplitude_claim": "none".
  * THIS TOOL'S OWN STATUS IS INFORMATIONAL, NOT GATE EVIDENCE
    (report["gate_ready"] is always False): the pitch measurer this file
    reuses (melody_verify.measure_pitch_cents) has a self-calibration
    sentinel (C10, tools/measurement_selfcal.py) whose "informational vs
    GATE" ruling is itself still pending 月月裁決. This tool must not be
    read as a stronger claim than its own prerequisite.

WHAT THIS TOOL DOES
  1. Reads a tools/stem_verify.py JSON report (must have been produced with
     an explicit --out-dir AND --keep-stems, so the per-event stem WAV/score
     files this tool needs are still on disk -- see run()'s refusal message
     if they are not).
  2. For each event stem_verify already isolated (single note, no polyphony
     -- so none of melody_verify's cross-event Ra/Rb/Rc refusals apply
     here), re-runs --dump-modes on THAT event's own derived single-event
     score.json (already written by stem_verify to
     <out_dir>/stems/ev_NNNN/score.json) to get the model's own predicted
     partial ladder (frequency/amplitude/decay/body_mag, string 0 -- the
     same convention tools/physics_verify.py's dump_modes_partials() uses).
  3. Measures the first N partials' FREQUENCY in the stem's own WAV by
     calling melody_verify.measure_pitch_cents() -- the EXACT function the
     product GATE uses for the fundamental -- once per partial, substituting
     that partial's --dump-modes frequency for "the expected f0". This is
     the "reuse the same estimator" requirement from the workcard: no new
     pitch/frequency estimator is written.
  4. Records (never judges) each partial's amplitude, in dB relative to
     partial n=1, both PREDICTED (from --dump-modes' amp*body_mag) and
     MEASURED (from the same band-limited spectral segment the frequency
     measurement already looked at).
  5. Gates a partial's frequency verdict to UNVERIFIED, not a guessed PASS/
     FAIL, whenever:
       (a) --dump-modes gave no usable frequency for that partial;
       (b) this event's own partial bands (±3%, melody_verify.band_of())
           collide with EACH OTHER (own-event self-collision -- concurrent-
           event Rb-style contamination cannot occur here since every stem
           is a single isolated note, but adjacent high-n partials can still
           crowd together once inharmonicity spreads them);
       (c) the partial's sustain-window level does not clear its OWN
           pre-onset silence (every stem is a single isolated note, so
           time < the event's own time is silence by construction) by at
           least melody_verify.RISE_DB (15 dB, that EXISTING onset-rise
           margin reused verbatim, not a new tolerance) -- an SNR-relative
           test, so it does not depend on a take's own absolute loudness.
  6. C13 (harmonic-aware f0 for weak-fundamental events): for any event
     whose stem_verify reason contains the literal marker string
     "near-silent fundamental band" (melody_verify.py's own wording for
     exactly the 22 weak-fundamental-class events identified in
     reports/gate_outputs/stem_verify_fur_elise_run.txt "發現 2" / A13 §3.2-
     §3.3), infers this event's OWN inharmonicity coefficient B directly
     from --dump-modes' own n=1/n=2 partial ratio (no external B), then
     least-squares-fits f0 against every partial THIS TOOL successfully
     measured (>=2 required). The result lands in a SEPARATE
     `pitch_via_partials_cents` / `pitch_via_partials_verdict` pair; the
     event's original stem_verify `verdict`/`reason` are copied through
     completely unmodified (never merged, per the workcard's explicit ban).

--b-report (A13 選項 B+'s second deliverable, "另外寫一份不當 GATE 的文獻對照
報告"): builds a small piano probe score (A4/G5/F#6/G6/D7, same params as
the fur_elise corpus: engine=piano, material=steel, diameter_mm=1.0),
--dump-modes's it, infers this repo's own B per note the same n=1/n=2-ratio
way, and lists the ratio against A13 §3.3's Fletcher-Hamilton reference B
per note. This sets NO pass/fail condition -- it is numbers only, exactly as
A13 §4 selected.

R6: this file only calls the existing CLI (--dump-modes) and reads existing
WAV/JSON files -- it does not touch src/.
"""

import argparse
import datetime
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent


def _load_module(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vs = _load_module("verify_score", ROOT / "verify_score.py")
mv = _load_module("melody_verify", ROOT / "melody_verify.py")

# -- reused, NOT new (R2) ------------------------------------------------
TOLERANCE_CENTS = mv.PITCH_TOL_CENTS          # 5.0, == vs.MODE_F0_TOL_CENTS
TOLERANCE_PROVENANCE = (
    "reuses melody_verify.PITCH_TOL_CENTS (== verify_score."
    "MODE_F0_TOL_CENTS, month-lead ratified 2026-07-23); no new tolerance "
    "is introduced by this tool (R2). External support for this not being "
    "an over-loose number for PARTIAL frequency specifically: Fletcher "
    "1964 JASA 36(1) model-vs-measurement agreement on a solid high string "
    "is RMS 0.99 cents / max 1.82 cents (A13 decision packet §2.2-A2) -- "
    "far tighter than the 5-cent gate this tool judges against.")
WEAK_FUNDAMENTAL_REASON_MARKER = "near-silent fundamental band"

# A13 §3.3: Hamilton upright piano (Fletcher 1964 Table I/III/IV), B derived
# from the paper's own solid-string formula B = 3.95e10 * d^2/(l^4 * f0^2)
# (this repo's R1 research lane verified that formula reproduces Table III's
# own measured key-31 B to within 5%). Copied here VERBATIM from the
# decision packet -- not re-derived, not a new constant (R4): only used by
# --b-report, which sets no pass/fail condition (A13 §4 選項 B+).
REFERENCE_B_HAMILTON = {
    "A4":  {"midi": 49, "B_ref": 5.53e-4},
    "G5":  {"midi": 59, "B_ref": 1.77e-3},
    "F#6": {"midi": 70, "B_ref": 3.07e-3},
    "G6":  {"midi": 71, "B_ref": 3.34e-3},
    "D7":  {"midi": 78, "B_ref": 7.20e-3},
}
B_REPORT_SOURCE_NOTE = (
    "reference B values copied verbatim from reports/decision_packets/"
    "A13_partial_gate_domain.zh-TW.md §3.3 (Fletcher 1964 JASA 36(1), "
    "Hamilton upright piano, Table I/III/IV). This report sets NO pass/"
    "fail condition -- A13 §4 選項 B+: the engine's string geometry is "
    "known to disagree with this reference (2.4-5.4x), fixing it would "
    "change every corpus render's bit-identical output (Rule 10), so this "
    "is reported, not gated.")


def rel_to_repo(path):
    p = Path(path).resolve()
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(p)


# ============================================================================
# pure math: B inference (from the model's OWN n=1/n=2 ratio -- no external
# B is ever used to judge anything; see module docstring point 6)
# ============================================================================

def infer_B_from_ratio(freq1, freq2):
    """f_n = n*f0*sqrt(1+B*n^2) => r = f2/f1 = 2*sqrt((1+4B)/(1+B)).
    Solving for B: r^2*(1+B) = 4*(1+4B) => B = (4 - r^2) / (r^2 - 16).
    Returns None if freq1/freq2 are unusable or the algebra degenerates
    (r^2 == 16, i.e. r == 4, a coincidence not expected for any real B)."""
    if freq1 is None or freq2 is None or freq1 <= 0 or freq2 <= 0:
        return None
    if not (math.isfinite(freq1) and math.isfinite(freq2)):
        return None
    r = freq2 / freq1
    denom = r * r - 16.0
    if abs(denom) < 1e-9:
        return None
    return (4.0 - r * r) / denom


def least_squares_f0(n_freq_pairs, B):
    """Linear least-squares fit of f_n = f0 * n*sqrt(1+B*n^2) given
    [(n, measured_freq), ...] and a fixed B. Single free parameter (f0), so
    the closed form is f0 = sum(f_n * k_n) / sum(k_n^2), k_n = n*sqrt(1+B*n^2).

    NOTE on what this `f0` IS: it is the formula's "ideal" (n=1-independent)
    parameter, per the canonical rigid-string form (Fletcher 1964 / Rigaud
    2013, A13 §2.2-A1/A3) -- NOT the same number as the partial n=1's own
    ACTUAL frequency, which is f0*sqrt(1+B) (already sharpened by B at n=1
    too). Everywhere else in this codebase (verify_score.course_f0(), the
    raw --dump-modes "partials"[0].freq) "the fundamental" means that
    ACTUAL n=1 frequency -- callers comparing this function's return value
    against one of those must first multiply by sqrt(1+B) (see
    compute_pitch_via_partials() below, which does exactly that).
    Returns None if fewer than 1 usable point or the normal equation
    degenerates (den <= 0, cannot happen for a real n/B but guarded)."""
    if B is None or not math.isfinite(B):
        return None
    num = 0.0
    den = 0.0
    for n, f in n_freq_pairs:
        if f is None or not math.isfinite(f):
            continue
        k = n * math.sqrt(max(0.0, 1.0 + B * n * n))
        num += f * k
        den += k * k
    if den <= 0.0:
        return None
    return num / den


def is_weak_fundamental_class(reason):
    """True iff `reason` (a stem_verify per-event 'reason' string) matches
    melody_verify.py's own literal wording for the 22 weak-fundamental
    events identified in reports/gate_outputs/stem_verify_fur_elise_run.txt
    ("no onset in near-silent fundamental band ..."). Substring match only
    -- never inferred/guessed from anything else (same discipline
    stem_verify.extract_rule_ids() uses for its own rule-id tokens)."""
    return bool(reason) and WEAK_FUNDAMENTAL_REASON_MARKER in reason


# ============================================================================
# per-partial measurement (reuses melody_verify.measure_pitch_cents for
# FREQUENCY -- point 3 of the module docstring; the "is this partial loud
# enough to trust" gate reuses melody_verify's existing RISE_DB margin
# (15.0 dB, not a new tolerance) as a LEVEL comparison between this
# partial's own pre-onset silence (every stem is a single isolated note,
# so time < t_exp is guaranteed silent by construction -- a cleaner,
# longer noise-floor reference than melody_verify's own 43ms FLOOR_LOOKBACK)
# and its sustain-window level.
#
# Two earlier, WRONG attempts at this gate, kept here so nobody re-tries
# them:
#  1. An absolute -70 dBFS floor (mv.BAND_GATE_DBFS) computed from this
#     tool's own long-single-FFT band-energy sum -- WRONG SCALE: that
#     constant is calibrated for mv.Spectrogram's fixed N_FFT=2048/HOP=256
#     per-frame convention, not a single ~1.2s-long FFT's per-bin
#     magnitude; silently gated out ~90% of partials that were fine.
#  2. mv.BAND_GATE_DBFS applied on mv.Spectrogram's OWN correct per-frame
#     scale, but still as an ABSOLUTE floor -- scale-correct this time, but
#     WRONG SEMANTICS for an isolated single partial: melody_verify uses
#     -70 dBFS as a floor for a note's COMBINED energy across many
#     partials; one ISOLATED partial of a quiet, unnormalised 24-bit
#     render sits far below that on ABSOLUTE level even when it is
#     perfectly measurable relative to this take's own noise floor. Real-
#     corpus sanity run: 0/22 of the weak-fundamental notes this card
#     exists to serve (A13 §3.2, reports/gate_outputs/
#     stem_verify_fur_elise_run.txt "發現 2") produced even the ONE known-
#     dominant partial as "verified" under that rule.
#  3. mv.detect_rises() (RISE_DB timing-rise near t_exp) -- also wrong: the
#     note's own broadband strike transient lights up EVERY band near
#     onset regardless of whether that specific partial carries any real
#     sustained energy there (melody_verify.py's own module docstring:
#     "A strike transient is BROADBAND ... every declared onset
#     momentarily lights up every band") -- a synthetic sentinel with a
#     partial forced to exactly zero amplitude still "passed" that gate.
#
# This version keeps RISE_DB's SAME margin (still melody_verify's own
# constant, not invented here) but applies it as a LEVEL DIFFERENCE
# (sustain-window level vs this partial's own true pre-onset silence)
# rather than a TIMED rise -- immune to the transient-click contamination
# of #3 (the pre-onset reference window, by construction, contains no
# transient at all) and correctly SNR-RELATIVE rather than pinned to an
# absolute full-scale number that does not track a take's own loudness
# (fixes #1/#2).
# ============================================================================

def partial_amplitude_dbfs(times, db, t_exp):
    """MAX of melody_verify.Spectrogram.band_db()'s own per-frame dB track
    over mv.PITCH_SEG_S's window relative to t_exp (the same window
    measure_pitch_cents() judges) -- "how loud did this partial actually
    get". Used both as the recorded (relative to partial n=1),
    never-judged amplitude field, AND as one side of the frequency-trust
    gate below. None only when the window has no frames at all."""
    seg_a, seg_b = t_exp + mv.PITCH_SEG_S[0], t_exp + mv.PITCH_SEG_S[1]
    idx = (times >= seg_a) & (times <= seg_b)
    if not idx.any():
        return None
    return float(np.max(db[idx]))


def partial_pre_onset_floor_dbfs(times, t_exp, db):
    """MEDIAN band level strictly before t_exp -- this event's own true
    silence reference (every stem_verify.py stem is a single isolated
    event; ScoreRenderer places it at startSample=t_exp*sr with nothing
    else in the score, so everything before that sample is silence by
    construction, not merely "quiet"). None if there is no pre-onset
    region at all (t_exp <= 0, or too little audio before it for even one
    STFT frame)."""
    idx = times < t_exp
    if not idx.any():
        return None
    return float(np.median(db[idx]))


def partial_trusted(times, db, t_exp):
    """True iff this partial's sustain-window level clears its OWN
    pre-onset floor by at least mv.RISE_DB (15.0 dB, melody_verify's
    existing onset-rise margin, reused verbatim -- not a new tolerance).
    Falls back to mv.BAND_GATE_DBFS (also existing, reused verbatim) as an
    absolute floor ONLY when there is no pre-onset region to compare
    against at all (t_exp <= 0 -- the very first event in a score). Returns
    (trusted: bool|None, sustain_dbfs, pre_floor_dbfs); trusted is None
    when sustain_dbfs itself could not be measured (segment too short)."""
    sustain = partial_amplitude_dbfs(times, db, t_exp)
    if sustain is None:
        return None, None, None
    floor = partial_pre_onset_floor_dbfs(times, t_exp, db)
    if floor is None:
        return (sustain > mv.BAND_GATE_DBFS), sustain, None
    return ((sustain - floor) >= mv.RISE_DB), sustain, floor


def partial_predicted_relative_energy(p):
    """--dump-modes mode amplitude * body_mag (the same product
    tools/physics_verify.py's synth_theory_signal() sums as each partial's
    contribution) -- an arbitrary-but-internally-consistent unit, only ever
    used as a RATIO against partial n=1's own value (never an absolute
    claim). None if the mode dict carries no usable amp."""
    if not isinstance(p, dict):
        return None
    amp = p.get("amp")
    if amp is None or not math.isfinite(amp):
        return None
    body_mag = p.get("body_mag")
    if body_mag is None or not math.isfinite(body_mag):
        body_mag = 1.0
    return float(amp) * float(body_mag)


def judge_event_partials(mono, sr, dumped_partials, t_exp, n_partials):
    """Returns a list of per-partial result dicts (n=1..min(n_partials,
    len(dumped_partials))), each:
      {"n", "expected_hz", "amplitude_claim": "none",
       "amplitude_db_rel_f1_predicted", "amplitude_db_rel_f1_measured",
       "verdict": PASS|FAIL|UNVERIFIED, "reason" (if not PASS),
       "measured_cents" (if a frequency measurement was actually made)}
    Pure function of (mono, sr, dumped_partials, t_exp, n_partials) -- no
    file I/O, so it is directly sentinel-testable against synthetic signals
    (measurement_selfcal.py-style)."""
    n_use = min(n_partials, len(dumped_partials))
    freqs = []
    for k in range(n_use):
        f = (dumped_partials[k] or {}).get("freq")
        freqs.append(f if (f is not None and math.isfinite(f) and f > 0) else None)

    collided = set()
    for i in range(n_use):
        if freqs[i] is None:
            continue
        for j in range(i + 1, n_use):
            if freqs[j] is None:
                continue
            if mv.overlaps(mv.band_of(freqs[i]), mv.band_of(freqs[j])):
                collided.add(i)
                collided.add(j)

    spectro = mv.Spectrogram(mono, sr)
    pred1 = partial_predicted_relative_energy(dumped_partials[0]) if dumped_partials else None
    energy1_dbfs = None
    out = []
    for k in range(n_use):
        n = k + 1
        entry = {"n": n, "expected_hz": freqs[k], "amplitude_claim": "none",
                 "amplitude_db_rel_f1_predicted": None,
                 "amplitude_db_rel_f1_measured": None}
        if freqs[k] is None:
            entry["verdict"] = "UNVERIFIED"
            entry["reason"] = "dump-modes gave no usable frequency for this partial"
            out.append(entry)
            continue

        pred_e = partial_predicted_relative_energy(dumped_partials[k])
        if pred1 and pred1 > 0 and pred_e is not None and pred_e > 0:
            entry["amplitude_db_rel_f1_predicted"] = 20.0 * math.log10(pred_e / pred1)

        times, db = spectro.band_db(*mv.band_of(freqs[k]))
        trusted, dbfs, floor_dbfs = partial_trusted(times, db, t_exp)
        if k == 0 and dbfs is not None:
            energy1_dbfs = dbfs
        if dbfs is not None and energy1_dbfs is not None:
            entry["amplitude_db_rel_f1_measured"] = dbfs - energy1_dbfs

        if k in collided:
            entry["verdict"] = "UNVERIFIED"
            entry["reason"] = ("own-event partial band collision: this "
                                "partial's +/-3% band overlaps another "
                                "measured partial's band (melody_verify."
                                "band_of/overlaps, reused) -- frequency not "
                                "judged")
            out.append(entry)
            continue

        if trusted is None:
            entry["verdict"] = "UNVERIFIED"
            entry["reason"] = "segment too short to measure this partial's band level"
            out.append(entry)
            continue
        if not trusted:
            if floor_dbfs is not None:
                entry["reason"] = (
                    "partial sustain level %.1f dBFS is only %.1f dB above "
                    "its own pre-onset (silent, by construction) floor %.1f "
                    "dBFS -- below the required %.1f dB (melody_verify."
                    "RISE_DB, reused verbatim) -- too quiet to trust a "
                    "frequency reading here"
                    % (dbfs, dbfs - floor_dbfs, floor_dbfs, mv.RISE_DB))
            else:
                entry["reason"] = (
                    "partial level %.1f dBFS at/below %.1f dBFS "
                    "(melody_verify.BAND_GATE_DBFS, reused verbatim -- no "
                    "pre-onset region exists for this event to compare "
                    "against, t=%.3fs) -- too quiet to trust a frequency "
                    "reading here" % (dbfs, mv.BAND_GATE_DBFS, t_exp))
            entry["verdict"] = "UNVERIFIED"
            out.append(entry)
            continue

        cents, fail = mv.measure_pitch_cents(mono, sr, freqs[k], t_exp)
        if fail:
            entry["verdict"] = "UNVERIFIED"
            entry["reason"] = fail
        else:
            entry["measured_cents"] = cents
            if abs(cents) <= TOLERANCE_CENTS:
                entry["verdict"] = "PASS"
            else:
                entry["verdict"] = "FAIL"
                entry["reason"] = ("partial pitch off by %+.2f cents "
                                    "(limit %.1f)" % (cents, TOLERANCE_CENTS))
        out.append(entry)
    return out


# ============================================================================
# C13: harmonic-aware pitch-via-partials for weak-fundamental-class events
# ============================================================================

def compute_pitch_via_partials(dumped_partials, partials_out, expected_f0):
    """Returns {"cents", "verdict", "reason", "B", "n_used"}. `verdict` is
    PASS/FAIL only when a least-squares f0 was actually computed against
    >=2 successfully-measured partials (PASS or FAIL entries in
    `partials_out` -- i.e. anything with a real `measured_cents`, UNVERIFIED
    entries excluded); otherwise UNVERIFIED with a reason. This result is
    NEVER merged into any event's own `verdict` field -- callers keep it
    entirely separate (workcard: "verdict 欄位原值不動")."""
    f1 = dumped_partials[0].get("freq") if dumped_partials else None
    f2 = dumped_partials[1].get("freq") if len(dumped_partials) > 1 else None
    B = infer_B_from_ratio(f1, f2)
    if B is None:
        return {"cents": None, "verdict": "UNVERIFIED",
                "reason": "could not infer B from --dump-modes n=1/n=2 partials",
                "B": None, "n_used": []}

    pairs = []
    for e in partials_out:
        if e.get("verdict") in ("PASS", "FAIL") and "measured_cents" in e and e.get("expected_hz"):
            meas_f = e["expected_hz"] * (2.0 ** (e["measured_cents"] / 1200.0))
            pairs.append((e["n"], meas_f))

    if len(pairs) < 2:
        return {"cents": None, "verdict": "UNVERIFIED",
                "reason": ("insufficient measured partials for harmonic-aware "
                            "f0 (need >=2, got %d)" % len(pairs)),
                "B": B, "n_used": [p[0] for p in pairs]}

    f0_ideal_ls = least_squares_f0(pairs, B)
    if f0_ideal_ls is None or expected_f0 is None:
        return {"cents": None, "verdict": "UNVERIFIED",
                "reason": "least-squares f0 solve failed",
                "B": B, "n_used": [p[0] for p in pairs]}
    # Convert the fit's "ideal" parameter to the ACTUAL n=1 partial
    # frequency (f1 = f0_ideal*sqrt(1+B)) so it is comparable to
    # `expected_f0` (verify_score.course_f0() / --dump-modes partials[0].freq
    # convention -- see least_squares_f0()'s docstring for why the two
    # differ by exactly this factor).
    f1_from_partials = f0_ideal_ls * math.sqrt(max(0.0, 1.0 + B))

    cents = vs.cents_between(f1_from_partials, expected_f0)
    if cents is None:
        return {"cents": None, "verdict": "UNVERIFIED",
                "reason": "cents_between() could not compare the solved f0 "
                          "against the expected fundamental",
                "B": B, "n_used": [p[0] for p in pairs], "f0_hz": f1_from_partials}
    verdict = "PASS" if abs(cents) <= TOLERANCE_CENTS else "FAIL"
    return {"cents": cents, "verdict": verdict, "reason": None, "B": B,
            "n_used": [p[0] for p in pairs], "f0_hz": f1_from_partials}


# ============================================================================
# orchestration
# ============================================================================

def run(stem_report_path, n_partials=6, json_out=None, html_out=None, quiet=False):
    stem_report_path = Path(stem_report_path)
    stem_report = json.loads(stem_report_path.read_text(encoding="utf-8"))

    report = {
        "tool": "partial_verify.py",
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "source_stem_verify_report": {
            "path": rel_to_repo(stem_report_path),
            "sha256": vs.sha256_file(stem_report_path),
        },
        "requested_partials": n_partials,
        "tolerance_cents": TOLERANCE_CENTS,
        "tolerance_provenance": TOLERANCE_PROVENANCE,
        "amplitude_claim": "none",
        "status": "informational",
        "gate_ready": False,
        "gate_ready_reason": ("C10 (measurement self-calibration, tools/"
                               "measurement_selfcal.py) is itself still "
                               "pending 月月裁決 on informational-vs-GATE "
                               "status; this tool cannot outrank its own "
                               "prerequisite -- A13 decision packet 選項 B+."),
    }

    cli = vs.find_cli()
    if cli is None:
        report["status"] = "error"
        report["error"] = "TsukiSynthCLI executable not found under build/"
        if not quiet:
            print("[ERROR] " + report["error"])
        return report, 1
    report["cli"] = {"path": rel_to_repo(cli), "sha256": vs.sha256_file(cli)}

    sp = stem_report.get("superposition_proof") or {}
    ref_wav = sp.get("reference_wav")
    if not ref_wav or str(ref_wav).endswith("(deleted after run)"):
        report["status"] = "refused"
        report["refusal_reason"] = (
            "the stem_verify report's stems were not kept on disk -- "
            "re-run tools/stem_verify.py with an explicit --out-dir AND "
            "--keep-stems so this tool can read the per-event stem WAV/"
            "score files it needs")
        if not quiet:
            print("[REFUSED] " + report["refusal_reason"])
        return report, 1

    stems_dir = Path(ref_wav).resolve().parent.parent / "stems"
    if not stems_dir.is_dir():
        report["status"] = "refused"
        report["refusal_reason"] = "expected stems directory not found at %s" % stems_dir
        if not quiet:
            print("[REFUSED] " + report["refusal_reason"])
        return report, 1

    events_in = ((stem_report.get("stem_verify") or {}).get("events")) or []
    out_events = []
    n_verified_total = 0
    n_refused_total = 0
    max_abs_cents = None
    pv_counts = {"eligible": 0, "measured": 0, "pass": 0, "fail": 0, "unverified": 0}

    for se in events_in:
        idx = se.get("index")
        entry = {"index": idx, "time": se.get("time"), "note": se.get("note"),
                  "engine": se.get("engine"), "stem_verdict": se.get("verdict"),
                  "stem_reason": se.get("reason")}
        stem_dir = stems_dir / ("ev_%04d" % idx) if idx is not None else None
        score_path = stem_dir / "score.json" if stem_dir else None
        wavs = sorted(stem_dir.glob("*.wav")) if stem_dir and stem_dir.is_dir() else []

        if idx is None or score_path is None or not score_path.is_file() or not wavs:
            entry["stem_available"] = False
            entry["unavailable_reason"] = (
                "no stem score/wav found at %s (upstream stem render may "
                "have failed -- see the stem_verify report's render_errors)"
                % stem_dir)
            out_events.append(entry)
            continue
        entry["stem_available"] = True

        try:
            dumped = vs.dump_modes(cli, str(score_path)).get("events", [])
        except vs.CliError as e:
            entry["stem_available"] = False
            entry["unavailable_reason"] = "--dump-modes failed: %s" % e
            out_events.append(entry)
            continue
        if not dumped:
            entry["stem_available"] = False
            entry["unavailable_reason"] = ("--dump-modes returned no events "
                                            "for this single-event stem score")
            out_events.append(entry)
            continue
        dumped_event = dumped[0]
        entry["derived_score_sha256"] = vs.sha256_file(score_path)

        partials_list = dumped_event.get("partials") or (
            (dumped_event.get("strings") or [[]])[0] or [])
        f0_expected = vs.course_f0(dumped_event)
        entry["expected_f0_hz"] = f0_expected
        if not partials_list:
            entry["unavailable_reason"] = "--dump-modes gave no partials for this event"
            out_events.append(entry)
            continue

        wav_path = wavs[-1]
        sr, mono, _ch = vs.read_wav_mono(str(wav_path))
        t_exp = float(se.get("time", 0.0))

        partials_out = judge_event_partials(mono, sr, partials_list, t_exp, n_partials)
        entry["partials"] = partials_out

        n_pass = sum(1 for p in partials_out if p.get("verdict") == "PASS")
        n_fail = sum(1 for p in partials_out if p.get("verdict") == "FAIL")
        n_unv = sum(1 for p in partials_out if p.get("verdict") == "UNVERIFIED")
        entry["partials_verified"] = n_pass + n_fail
        entry["partials_refused"] = n_unv
        n_verified_total += n_pass + n_fail
        n_refused_total += n_unv

        cents_list = [p["measured_cents"] for p in partials_out
                      if p.get("verdict") in ("PASS", "FAIL") and "measured_cents" in p]
        if cents_list:
            local_max = max(abs(c) for c in cents_list)
            max_abs_cents = local_max if max_abs_cents is None else max(max_abs_cents, local_max)

        weak = is_weak_fundamental_class(se.get("reason"))
        entry["is_weak_fundamental_class"] = weak
        if weak:
            pv_counts["eligible"] += 1
            pv = compute_pitch_via_partials(partials_list[:n_partials], partials_out, f0_expected)
            entry["pitch_via_partials_cents"] = pv["cents"]
            entry["pitch_via_partials_verdict"] = pv["verdict"]
            entry["pitch_via_partials_reason"] = pv["reason"]
            entry["pitch_via_partials_B"] = pv["B"]
            entry["pitch_via_partials_n_used"] = pv["n_used"]
            if pv["verdict"] == "UNVERIFIED":
                pv_counts["unverified"] += 1
            else:
                pv_counts["measured"] += 1
                pv_counts["pass" if pv["verdict"] == "PASS" else "fail"] += 1

        out_events.append(entry)

    report["events"] = out_events
    report["summary"] = {
        "events_total": len(events_in),
        "events_stem_available": sum(1 for e in out_events if e.get("stem_available")),
        "events_stem_missing": sum(1 for e in out_events if not e.get("stem_available")),
        "partials_verified_total": n_verified_total,
        "partials_refused_total": n_refused_total,
        "max_abs_partial_cents": max_abs_cents,
        "pitch_via_partials": pv_counts,
    }
    report["caveats"] = [
        "status=informational, gate_ready=false: this report is NOT GATE "
        "evidence (A13 decision packet 選項 B+; C10 self-cal still pending "
        "月月裁決).",
        "amplitude fields (amplitude_db_rel_f1_measured/_predicted) are "
        "recorded only, never judged (amplitude_claim=none) -- A13 §4 選項 "
        "C found no sourced, non-arbitrary external amplitude tolerance.",
        "pitch_via_partials_* is a SEPARATE claim from stem_verify's own "
        "'verdict'/'reason' fields, which this tool copies through "
        "completely unmodified.",
        "partial frequencies are read off --dump-modes' string-0 mode "
        "list (course-detuning convention shared with tools/"
        "physics_verify.py's dump_modes_partials()), not the multi-string "
        "course centroid tools/verify_score.py's course_f0() computes for "
        "the fundamental -- see module docstring point 2.",
    ]

    if not quiet:
        print("[partial_verify] %s" % stem_report_path)
        print("  events=%d  stem_available=%d  stem_missing=%d"
              % (report["summary"]["events_total"],
                 report["summary"]["events_stem_available"],
                 report["summary"]["events_stem_missing"]))
        print("  partials verified=%d refused=%d  max|cents|=%s"
              % (n_verified_total, n_refused_total,
                 ("%.4f" % max_abs_cents) if max_abs_cents is not None else "N/A"))
        print("  pitch_via_partials: eligible=%d measured=%d (pass=%d fail=%d) unverified=%d"
              % (pv_counts["eligible"], pv_counts["measured"], pv_counts["pass"],
                 pv_counts["fail"], pv_counts["unverified"]))

    if json_out:
        Path(json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                    encoding="utf-8")
    if html_out:
        write_html_report(report, html_out)
    return report, 0


def write_html_report(report, html_out):
    """Minimal, self-contained HTML table -- informational status stated at
    the top verbatim, never implied otherwise. Not the piano-roll overlay
    design doc §4 describes (out of this card's scope); just a legible
    rendering of this tool's own JSON."""
    rows = []
    for ev in report.get("events", []):
        if not ev.get("stem_available"):
            rows.append("<tr><td>%s</td><td colspan=6>stem unavailable: %s</td></tr>"
                         % (ev.get("index"), ev.get("unavailable_reason", "")))
            continue
        for p in ev.get("partials", []):
            rows.append(
                "<tr><td>%s</td><td>%s</td><td>%s</td><td>n=%s</td>"
                "<td>%s</td><td>%s</td><td>%s</td></tr>"
                % (ev.get("index"), ev.get("note"), ev.get("engine"), p.get("n"),
                   ("%.3f" % p["expected_hz"]) if p.get("expected_hz") else "-",
                   ("%+.3f" % p["measured_cents"]) if "measured_cents" in p else "-",
                   p.get("verdict")))
    html = (
        "<title>partial_verify report</title>"
        "<p><b>status: %s -- gate_ready: %s</b><br>%s</p>"
        "<table border=1 cellspacing=0 cellpadding=4>"
        "<tr><th>event</th><th>note</th><th>engine</th><th>partial</th>"
        "<th>expected Hz</th><th>measured cents</th><th>verdict</th></tr>"
        "%s</table>"
        % (report.get("status"), report.get("gate_ready"),
           report.get("gate_ready_reason", ""), "".join(rows)))
    Path(html_out).write_text(html, encoding="utf-8")


# ============================================================================
# --b-report (A13 選項 B+'s second deliverable -- NOT a GATE)
# ============================================================================

def build_b_probe_score(sr=48000):
    """Piano-engine probe score for A4/G5/F#6/G6/D7 (same params the
    fur_elise corpus itself uses for every note: material=steel,
    diameter_mm=1.0, see scores/classical/fur_elise/
    fur_elise_complete.score.json's own events) -- reproduces A13 §3.1's
    method. Follows tools/physics_verify.py's build_probe_score() minimal,
    known-schema-valid template."""
    notes = list(REFERENCE_B_HAMILTON.keys())
    events = []
    t = 0.0
    for note in notes:
        events.append({"time": t, "duration": 2.0, "engine": "piano",
                        "note": note, "velocity": 0.45,
                        "params": {"material": "steel", "diameter_mm": 1.0}})
        t += 3.0
    return {
        "$schema": "TsukiSynth Score v1",
        "meta": {"title": "wf0908_p1_b_report_probe", "id": "wf0908_p1_b_report_probe"},
        "global": {"bpm": 120, "sample_rate": sr, "master_volume": 1.0,
                   "effects": {"reverb": {"decay": 2, "wet": 0},
                               "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                               "distortion": {"type": "overdrive", "drive": 0,
                                              "instability": 0, "wet": 0}}},
        "events": events,
        "export": {"filename": "wf0908_p1_b_report_probe", "format": "wav"},
    }, notes


def run_b_report(out_path):
    import tempfile
    cli = vs.find_cli()
    if cli is None:
        raise RuntimeError("TsukiSynthCLI executable not found under build/")
    score, notes = build_b_probe_score()
    with tempfile.TemporaryDirectory(prefix="partial_verify_breport_") as td:
        score_path = Path(td) / "wf0908_p1_b_report_probe.score.json"
        score_path.write_text(json.dumps(score), encoding="utf-8")
        dumped = vs.dump_modes(cli, str(score_path)).get("events", [])

    lines = [
        "partial_verify.py --b-report -- A13 選項 B+ 第二項交付：B 對照真鋼琴",
        "只列數字，不設通過條件（%s" % B_REPORT_SOURCE_NOTE + ")",
        "cli: %s (sha256 %s)" % (rel_to_repo(cli), vs.sha256_file(cli)),
        "",
    ]
    if len(dumped) != len(notes):
        lines.append("[WARN] --dump-modes returned %d events, expected %d (%s)"
                      % (len(dumped), len(notes), notes))
    for note, d in zip(notes, dumped):
        partials = d.get("partials") or []
        f1 = partials[0].get("freq") if len(partials) > 0 else None
        f2 = partials[1].get("freq") if len(partials) > 1 else None
        B = infer_B_from_ratio(f1, f2)
        ref = REFERENCE_B_HAMILTON.get(note)
        ref_B = ref["B_ref"] if ref else None
        ratio = (B / ref_B) if (B is not None and ref_B) else None
        lines.append(
            "%-4s  engine B=%s  Hamilton-ref B=%s  ratio=%s"
            % (note,
               ("%.4e" % B) if B is not None else "N/A",
               ("%.4e" % ref_B) if ref_B is not None else "N/A",
               ("%.3fx" % ratio) if ratio is not None else "N/A"))
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


# ============================================================================
# CLI
# ============================================================================

def build_arg_parser():
    ap = argparse.ArgumentParser(
        description="Partial-frequency internal-consistency check "
                    "(informational; A13 decision packet 選項 B+) plus "
                    "harmonic-aware pitch-via-partials for weak-fundamental "
                    "events (C13).")
    ap.add_argument("stem_report", nargs="?", default=None,
                     help="tools/stem_verify.py JSON report (run with an "
                          "explicit --out-dir and --keep-stems)")
    ap.add_argument("--partials", type=int, default=6, dest="n_partials",
                     help="how many partials (n=1..N) to measure per event (default 6)")
    ap.add_argument("--json", default=None, help="write the full report as JSON to this path")
    ap.add_argument("--html", default=None, help="write a minimal HTML rendering to this path")
    ap.add_argument("--b-report", default=None, dest="b_report",
                     help="also (or, if stem_report is omitted, ONLY) write "
                          "the A13 選項 B+ engine-vs-Hamilton B ratio report "
                          "to this path -- sets no pass/fail condition")
    return ap


def main():
    ap = build_arg_parser()
    args = ap.parse_args()

    if args.stem_report is None and not args.b_report:
        ap.error("either a stem_verify report path or --b-report is required")

    code = 0
    if args.b_report:
        try:
            run_b_report(args.b_report)
            print("[partial_verify] --b-report written to %s" % args.b_report)
        except Exception as e:  # noqa: BLE001
            print("[ERROR] --b-report failed: %s: %s" % (type(e).__name__, e), file=sys.stderr)
            code = 1

    if args.stem_report is not None:
        try:
            _report, run_code = run(args.stem_report, n_partials=args.n_partials,
                                      json_out=args.json, html_out=args.html)
            code = code or run_code
        except Exception as e:  # noqa: BLE001
            print("[ERROR] %s: %s" % (type(e).__name__, e), file=sys.stderr)
            code = 1

    return code


if __name__ == "__main__":
    sys.exit(main())
