"""Sentinel tests for tools/partial_verify.py (WF0908-P1).

Style mirrors tests/test_measurement_selfcal.py / tests/test_stem_verify.py:
load modules by file path (tools/ pushed onto sys.path first), build purely
SYNTHETIC known-answer signals (measurement_selfcal.synth_tone -- the same
synthesis this repo's own C10 self-cal sentinel uses, not a re-implementation)
and feed them through partial_verify's pure functions directly, with no
TsukiSynthCLI render anywhere in this file (no CLI dependency = these run
everywhere pytest runs).

Per repo rule ("沒有哨兵的驗證器等於沒有驗證"), each sentinel proves the tool
actually CATCHES an injected defect, not merely that it runs. Required by the
workcard (docs/workcards/WF0908_P1_partial_verify.md §3):
  (a) test_a_*  -- synthetic signal with all partials exactly on-model must
                   come back all PASS.
  (b) test_b_*  -- shifting only the n=3 partial's SYNTHESIZED frequency by
                   +8 cents (dumped/expected left unshifted) must FAIL only
                   n=3.
  (c) test_c_*  -- a partial with (near-)zero amplitude must come back
                   UNVERIFIED, never a guessed PASS.
  (d) test_d_*  -- boosting one partial's amplitude x10 must leave its
                   FREQUENCY verdict unchanged while the recorded amplitude
                   field honestly reflects the ~+20 dB change.
  (e) test_e_*  -- the report's gate_ready field must be False (this tool is
                   informational, never GATE evidence -- A13 選項 B+).
Plus bonus coverage for the pure-math helpers (B inference / least-squares
f0) and the C13 harmonic-aware pitch-via-partials path (a synthetic
weak-fundamental event: n=1 too quiet to measure, f0 correctly recovered
from n=2..N anyway).
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pv = _load("partial_verify", ROOT / "tools" / "partial_verify.py")
ms = _load("measurement_selfcal", ROOT / "tools" / "measurement_selfcal.py")
mv = pv.mv
vs = pv.vs

SR = 48000
T_ONSET = 0.1
DURATION_S = 1.6
T60 = 1.5
PEAK_DBFS = -6.0


def _build_dumped(freqs, amps, decay=T60, body_mag=1.0):
    return [{"freq": f, "amp": a, "decay": decay, "body_mag": body_mag}
            for f, a in zip(freqs, amps)]


def _harmonic_freqs(f0, n_max, B=1e-3):
    ns = np.arange(1, n_max + 1)
    return list(ns * f0 * np.sqrt(1.0 + B * ns ** 2))


# ============================================================================
# (a) all partials on-model -> all PASS
# ============================================================================

def test_a_exact_synthetic_signal_all_partials_pass():
    f0 = 440.0
    freqs = _harmonic_freqs(f0, 6)
    amps = [1.0 / n for n in range(1, 7)]
    dumped = _build_dumped(freqs, amps)
    sig = ms.synth_tone(freqs, amps, SR, T_ONSET, DURATION_S, T60, PEAK_DBFS)

    result = pv.judge_event_partials(sig, SR, dumped, T_ONSET, 6)

    assert len(result) == 6
    for r in result:
        assert r["verdict"] == "PASS", r
        assert abs(r["measured_cents"]) < 1.0, r


# ============================================================================
# (b) only n=3 shifted +8 cents in the SYNTHESIZED audio -> only n=3 FAILs
# ============================================================================

def test_b_single_partial_shifted_8_cents_only_that_partial_fails():
    f0 = 440.0
    freqs = _harmonic_freqs(f0, 6)
    amps = [1.0 / n for n in range(1, 7)]
    dumped = _build_dumped(freqs, amps)  # expected = UNSHIFTED

    shift = 2.0 ** (8.0 / 1200.0)
    freqs_synth = list(freqs)
    freqs_synth[2] *= shift  # n=3 (0-indexed 2)
    sig = ms.synth_tone(freqs_synth, amps, SR, T_ONSET, DURATION_S, T60, PEAK_DBFS)

    result = pv.judge_event_partials(sig, SR, dumped, T_ONSET, 6)

    for r in result:
        if r["n"] == 3:
            assert r["verdict"] == "FAIL", r
            assert abs(r["measured_cents"] - 8.0) < 1.0, r
        else:
            assert r["verdict"] == "PASS", r


# ============================================================================
# (c) a (near-)silent partial -> UNVERIFIED, never PASS
# ============================================================================

def test_c_silent_partial_is_unverified_not_pass():
    f0 = 440.0
    freqs = _harmonic_freqs(f0, 6)
    amps = [1.0 / n for n in range(1, 7)]
    amps[3] = 0.0  # n=4 carries no energy at all
    dumped = _build_dumped(freqs, amps)
    sig = ms.synth_tone(freqs, amps, SR, T_ONSET, DURATION_S, T60, PEAK_DBFS)

    result = pv.judge_event_partials(sig, SR, dumped, T_ONSET, 6)

    silent = [r for r in result if r["n"] == 4][0]
    assert silent["verdict"] == "UNVERIFIED", silent
    assert "measured_cents" not in silent
    # sanity: the surviving partials are unaffected
    for r in result:
        if r["n"] != 4:
            assert r["verdict"] == "PASS", r


# ============================================================================
# (d) amplitude x10 on one partial -> frequency verdict unchanged, amplitude
#     field honestly reflects it (~+20 dB), predicted amplitude untouched
# ============================================================================

def test_d_amplitude_boost_does_not_change_frequency_verdict():
    f0 = 440.0
    freqs = _harmonic_freqs(f0, 6)
    amps_base = [1.0 / n for n in range(1, 7)]
    dumped = _build_dumped(freqs, amps_base)

    sig_base = ms.synth_tone(freqs, amps_base, SR, T_ONSET, DURATION_S, T60, PEAK_DBFS)
    result_base = pv.judge_event_partials(sig_base, SR, dumped, T_ONSET, 6)

    amps_boost = list(amps_base)
    amps_boost[1] *= 10.0  # n=2, +20 dB
    sig_boost = ms.synth_tone(freqs, amps_boost, SR, T_ONSET, DURATION_S, T60, PEAK_DBFS)
    result_boost = pv.judge_event_partials(sig_boost, SR, dumped, T_ONSET, 6)

    r_base = [r for r in result_base if r["n"] == 2][0]
    r_boost = [r for r in result_boost if r["n"] == 2][0]

    # frequency verdict: unaffected by the amplitude change
    assert r_base["verdict"] == "PASS"
    assert r_boost["verdict"] == "PASS"
    assert abs(r_base["measured_cents"] - r_boost["measured_cents"]) < 0.5

    # predicted amplitude comes from --dump-modes (unchanged input) -> identical
    assert r_base["amplitude_db_rel_f1_predicted"] == r_boost["amplitude_db_rel_f1_predicted"]

    # measured amplitude honestly reflects the ~+20 dB change, only recorded
    delta = r_boost["amplitude_db_rel_f1_measured"] - r_base["amplitude_db_rel_f1_measured"]
    assert abs(delta - 20.0) < 2.0, delta
    assert r_base["amplitude_claim"] == "none"
    assert r_boost["amplitude_claim"] == "none"


# ============================================================================
# (e) gate_ready is always False (informational tool, never GATE evidence)
# ============================================================================

def test_e_gate_ready_is_always_false(tmp_path):
    # Exercises the REAL run() refusal path (no CLI needed): a stem_verify
    # report whose stems were not kept on disk must be refused, and the
    # gate_ready field -- set before any refusal branching runs -- must
    # still read False.
    fake_report = {
        "tool": "stem_verify.py",
        "superposition_proof": {"reference_wav": "some/path/reference.wav (deleted after run)"},
        "stem_verify": {"events": []},
    }
    p = tmp_path / "fake_stem_verify.json"
    p.write_text(json.dumps(fake_report), encoding="utf-8")

    report, code = pv.run(str(p), quiet=True)

    assert report["gate_ready"] is False
    assert report["status"] == "refused"
    assert code == 1


# ============================================================================
# bonus: pure-math helpers
# ============================================================================

def test_infer_B_and_least_squares_roundtrip():
    f0_true = 784.0
    B_true = 4.3e-3
    freqs = _harmonic_freqs(f0_true, 6, B=B_true)

    B_inferred = pv.infer_B_from_ratio(freqs[0], freqs[1])
    assert B_inferred is not None
    assert abs(B_inferred - B_true) / B_true < 1e-6

    pairs = [(n, freqs[n - 1]) for n in range(1, 7)]
    f0_ls = pv.least_squares_f0(pairs, B_inferred)
    assert f0_ls is not None
    assert abs(f0_ls - f0_true) / f0_true < 1e-6


def test_infer_B_handles_bad_input():
    assert pv.infer_B_from_ratio(None, 100.0) is None
    assert pv.infer_B_from_ratio(100.0, None) is None
    assert pv.infer_B_from_ratio(0.0, 100.0) is None
    assert pv.least_squares_f0([], 1e-3) is None
    assert pv.least_squares_f0([(1, 440.0)], None) is None


def test_is_weak_fundamental_class_matches_literal_marker_only():
    real_reason = ("no onset in near-silent fundamental band 760.5-830.4 Hz"
                    " (pre-onset floor -80.1 dBFS) within +/-58 ms of t=12.345s")
    assert pv.is_weak_fundamental_class(real_reason) is True
    assert pv.is_weak_fundamental_class("pitch off by +6.20 cents (limit 5.0)") is False
    assert pv.is_weak_fundamental_class(None) is False
    assert pv.is_weak_fundamental_class("") is False


# ============================================================================
# bonus: C13 end-to-end -- weak-fundamental event, f0 recovered from n>=2
# ============================================================================

def test_c13_pitch_via_partials_recovers_f0_when_fundamental_unmeasurable():
    f0 = 784.0  # G5-like: the A13 decision packet's own weak-fundamental case
    B = 4.3e-3
    freqs = _harmonic_freqs(f0, 6, B=B)
    # n=1 carries almost no energy (matches the real engine's own --dump-modes
    # for these notes, A13 §3.2: n=2 is the dominant partial); n=2.. are
    # normal falling-harmonic amplitudes.
    amps = [1e-5, 1.0, 0.5, 0.3, 0.2, 0.1]
    dumped = _build_dumped(freqs, amps)
    sig = ms.synth_tone(freqs, amps, SR, T_ONSET, DURATION_S, T60, PEAK_DBFS)

    partials_out = pv.judge_event_partials(sig, SR, dumped, T_ONSET, 6)
    n1 = [r for r in partials_out if r["n"] == 1][0]
    assert n1["verdict"] == "UNVERIFIED", n1  # too quiet to trust (gated)
    assert any(r["n"] == 2 and r["verdict"] == "PASS" for r in partials_out)

    pv_result = pv.compute_pitch_via_partials(dumped, partials_out, expected_f0=freqs[0])
    assert pv_result["verdict"] == "PASS", pv_result
    assert abs(pv_result["cents"]) < 2.0, pv_result
    assert 1 not in pv_result["n_used"]
    assert len(pv_result["n_used"]) >= 2


def test_is_weak_fundamental_class_marker_matches_melody_verify_source_string():
    """Guards against the marker constant silently drifting from
    melody_verify.py's own literal wording (a rename there would otherwise
    silently disable C13 for every event without any test noticing)."""
    import inspect
    src = inspect.getsource(mv)
    assert pv.WEAK_FUNDAMENTAL_REASON_MARKER in src
