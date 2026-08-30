"""Sentinel tests for tools/stem_verify.py.

Style mirrors tests/test_score_vs_midi_verify.py: load the module by file
path (no package install needed, tools/ pushed onto sys.path first so the
module's own `import loudness` etc. resolve without PYTHONPATH).

Per repo rule ("沒有哨兵的驗證器等於沒有驗證"), each sentinel proves the tool
actually CATCHES an injected defect, not merely that it runs:

  S1 (test_s1_*)  -- perturbing one stem's samples before summing must break
                     the superposition proof with a nonzero, non-hidden
                     residual. Pure array-level test (compare_superposition
                     takes plain ndarrays, no rendering involved) -- this is
                     the "inject the perturbation at the compare layer"
                     option the task text explicitly allows.
  S2 (test_s2_*)  -- an event whose DECLARED time is moved far outside the
                     onset tolerance, verified against a REAL CLI render of
                     the note at its true time, must come back FAIL (not
                     PASS, not UNVERIFIED). Uses an actual TsukiSynthCLI
                     render (tools/verify_score.render_score) -- no
                     fabricated WAV bytes.
  S3 (test_s3_*)  -- a score with distortion enabled, and a score with a
                     non-empty 'layers' array, must both be refused by the
                     real CLI entry point (subprocess: `python
                     tools/stem_verify.py ...`) BEFORE any rendering is
                     attempted, with the reason recorded in the JSON report,
                     never a silently-produced green result.

A bonus (non-mandatory) test for the hand-rolled float32-WAV reader is
included too, since a bug there would quietly invalidate every
superposition number without ever showing up as an obvious crash.
"""

import importlib.util
import json
import os
import subprocess
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

SPEC = importlib.util.spec_from_file_location(
    "stem_verify", ROOT / "tools" / "stem_verify.py")
sv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sv)

SPEC_VS = importlib.util.spec_from_file_location(
    "verify_score", ROOT / "tools" / "verify_score.py")
vs = importlib.util.module_from_spec(SPEC_VS)
SPEC_VS.loader.exec_module(vs)

SENTINEL_FIXTURE = ROOT / "scores" / "tests" / "melody_sentinel.score.json"


# ============================================================================
# S1 -- superposition proof must break on a perturbed stem
# ============================================================================

def _synthetic_stems(sr=1000, n=2000, ch=2, seed=0):
    rng = np.random.default_rng(seed)
    stem_a = rng.normal(0, 0.05, size=(n, ch))
    stem_b = rng.normal(0, 0.05, size=(n // 2, ch))  # shorter -- exercises padding
    reference = stem_a.copy()
    reference[: stem_b.shape[0]] += stem_b
    return sr, stem_a, stem_b, reference


def test_s1_unperturbed_sum_is_bit_exact():
    """Control: the true sum of the stems against the reference it was
    constructed FROM must register as bit-exact with zero residual."""
    sr, stem_a, stem_b, reference = _synthetic_stems()
    result = sv.compare_superposition(reference, [stem_a, stem_b], sr)
    assert result["bit_exact"] is True
    assert result["max_abs_diff"] == 0.0
    assert result["residual_peak_dbfs"] is None
    assert result["first_diff_sample_index"] is None


def test_s1_amplitude_perturbation_breaks_superposition():
    """Multiplying one stem by 1.01 (spec's own example) before summing
    MUST be caught: bit_exact False, nonzero residual, and a located first
    differing sample -- not silently ignored or rounded away."""
    sr, stem_a, stem_b, reference = _synthetic_stems()
    perturbed_b = stem_b * 1.01
    result = sv.compare_superposition(reference, [stem_a, perturbed_b], sr)
    assert result["bit_exact"] is False
    assert result["max_abs_diff"] > 0.0
    assert result["residual_peak_dbfs"] is not None
    assert result["residual_peak_dbfs"] > -300.0  # a real, measurable number
    assert result["first_diff_sample_index"] is not None
    # the perturbation only touches stem_b's span -> first mismatch must be
    # inside that span, not e.g. spuriously at sample 0 or past the end
    assert 0 <= result["first_diff_sample_index"] < stem_b.shape[0]


def test_s1_sample_shift_perturbation_breaks_superposition():
    """Spec's other example: shifting one stem by a few samples before
    summing must also be caught."""
    sr, stem_a, stem_b, reference = _synthetic_stems()
    shifted_b = np.roll(stem_b, 3, axis=0)
    result = sv.compare_superposition(reference, [stem_a, shifted_b], sr)
    assert result["bit_exact"] is False
    assert result["max_abs_diff"] > 0.0
    assert result["residual_rms_dbfs"] is not None


def test_s1_pad_to_length_rejects_stem_longer_than_reference():
    with pytest.raises(ValueError):
        sv.pad_to_length(np.zeros((10, 2)), 5, 2)


# ============================================================================
# S2 -- a mis-declared onset must FAIL, via a real CLI render
# ============================================================================

def test_s2_mis_declared_time_is_fail_not_unverified_or_pass(tmp_path):
    cli = vs.find_cli()
    assert cli is not None, "TsukiSynthCLI must be built for this sentinel"

    base = json.loads(SENTINEL_FIXTURE.read_text(encoding="utf-8"))
    event = base["events"][0]  # cimbalom note 60 @ t=0.0, dur 0.5, fx-free fixture
    assert event["time"] == 0.0

    stem_score = sv.make_stem_score(base, event, "s2_true")
    out_dir = tmp_path / "true_render"
    score_path, wav_path = sv.render_one(cli, stem_score, out_dir)

    # control: unmutated declared time against its own real render -> PASS
    control_verdict = sv.judge_stem(score_path, wav_path)["verdict"]
    assert control_verdict == "PASS", (
        "sentinel fixture's own unmodified render must verify PASS before "
        "the mutation below means anything")

    # mutation: declare the SAME event 3.0s later than it actually sounds
    # (the isolated stem's own buffer -- eventEndTime + tail -- is far
    # shorter than that, so the analysis window around the mutated time is
    # genuine post-buffer silence: a clean FAIL, not an Rd/Re refusal from
    # some other note still ringing there).
    mutated_event = dict(event)
    mutated_event["time"] = event["time"] + 3.0
    mutated_score = sv.make_stem_score(base, mutated_event, "s2_mutated")
    mutated_path = tmp_path / "mutated_score.json"
    mutated_path.write_text(json.dumps(mutated_score), encoding="utf-8")

    result = sv.judge_stem(mutated_path, wav_path)  # SAME real wav, only the
                                                      # declared time changed
    assert result["verdict"] == "FAIL", (
        "expected FAIL for a %.1fs onset error (tolerance is 10ms), got %r: %r"
        % (3.0, result["verdict"], result.get("reason")))
    assert "onset" in result.get("reason", "").lower() or \
           "no onset" in result.get("reason", "").lower()


# ============================================================================
# S3 -- nonlinear-fx / layered scores must be refused, not silently rendered
# ============================================================================

def _write_distortion_enabled_score(tmp_path):
    base = json.loads(SENTINEL_FIXTURE.read_text(encoding="utf-8"))
    base["meta"]["id"] = "melody_sentinel_dist_sentinel"
    base["global"]["effects"]["distortion"]["drive"] = 0.5
    base["global"]["effects"]["distortion"]["wet"] = 0.5
    path = tmp_path / "dist_enabled.score.json"
    path.write_text(json.dumps(base), encoding="utf-8")
    return path


def _write_layered_score(tmp_path):
    base = json.loads(SENTINEL_FIXTURE.read_text(encoding="utf-8"))
    base["meta"]["id"] = "melody_sentinel_layered_sentinel"
    del base["events"]
    base["layers"] = [{"source": str(SENTINEL_FIXTURE), "gain": 1.0}]
    path = tmp_path / "layered.score.json"
    path.write_text(json.dumps(base), encoding="utf-8")
    return path


def _run_stem_verify_cli(score_path, report_path):
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "stem_verify.py"), str(score_path),
         "--json", str(report_path)],
        capture_output=True, text=True, timeout=120)


def test_s3_distortion_enabled_is_refused(tmp_path):
    score_path = _write_distortion_enabled_score(tmp_path)
    report_path = tmp_path / "dist_report.json"
    proc = _run_stem_verify_cli(score_path, report_path)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "refused"
    assert report["refusal_reasons"], "reason must be recorded in the report, not just stdout"
    assert any("distortion" in r.lower() for r in report["refusal_reasons"])
    # no stem/reference render output should exist -- refusal happens BEFORE
    # any rendering, per module docstring ("fail-closed, BEFORE any rendering")
    assert "stem_verify" not in report
    assert "superposition_proof" not in report


def test_s3_layered_score_is_refused(tmp_path):
    score_path = _write_layered_score(tmp_path)
    report_path = tmp_path / "layered_report.json"
    proc = _run_stem_verify_cli(score_path, report_path)

    assert proc.returncode == 1, proc.stdout + proc.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "refused"
    assert report["refusal_reasons"]
    assert any("layer" in r.lower() for r in report["refusal_reasons"])
    assert "stem_verify" not in report
    assert "superposition_proof" not in report


def test_s3_gate_check_pure_function_matches_cli_behaviour():
    """Direct unit-level check of gate_check() itself, isolating the logic
    from the subprocess/report plumbing tested above."""
    clean = json.loads(SENTINEL_FIXTURE.read_text(encoding="utf-8"))
    assert sv.gate_check(clean) == []

    dist = json.loads(json.dumps(clean))
    dist["global"]["effects"]["distortion"]["wet"] = 0.01
    reasons = sv.gate_check(dist)
    assert len(reasons) == 1 and "distortion" in reasons[0].lower()

    layered = json.loads(json.dumps(clean))
    del layered["events"]
    layered["layers"] = [{"source": "x.score.json"}]
    reasons = sv.gate_check(layered)
    assert len(reasons) == 1 and "layer" in reasons[0].lower()

    # reverb/delay/eq must NOT gate (all LTI per the decision packet)
    linear_fx = json.loads(json.dumps(clean))
    linear_fx["global"]["effects"]["reverb"] = {"decay": 2.0, "wet": 0.3}
    linear_fx["global"]["effects"]["delay"] = {"time_ms": 250, "feedback": 0.3, "wet": 0.2}
    assert sv.gate_check(linear_fx) == []


# ============================================================================
# bonus (not one of the 3 mandatory sentinels): the hand-rolled WAV reader
# must round-trip PCM16 and IEEE-float32 correctly, since every superposition
# number in the report depends on it reading raw bytes right.
# ============================================================================

def _write_minimal_wav(path, samples, sample_rate, audio_format, bits_per_sample):
    n_channels = samples.shape[1]
    if audio_format == 1 and bits_per_sample == 16:
        data = (samples * 32767.0).astype("<i2").tobytes()
    elif audio_format == 1 and bits_per_sample == 24:
        ints = np.clip(np.round(samples * 8388607.0), -8388608, 8388607).astype(np.int32)
        # little-endian 24-bit: 3 bytes per sample, no numpy dtype for this
        flat = ints.reshape(-1)
        b = np.empty((flat.size, 3), dtype=np.uint8)
        b[:, 0] = flat & 0xFF
        b[:, 1] = (flat >> 8) & 0xFF
        b[:, 2] = (flat >> 16) & 0xFF
        data = b.tobytes()
    elif audio_format == 3 and bits_per_sample == 32:
        data = samples.astype("<f4").tobytes()
    else:
        raise ValueError("unsupported test fixture format")
    block_align = n_channels * bits_per_sample // 8
    byte_rate = sample_rate * block_align
    fmt_chunk = struct.pack("<HHIIHH", audio_format, n_channels, sample_rate,
                             byte_rate, block_align, bits_per_sample)
    riff_body = (b"WAVE"
                 + b"fmt " + struct.pack("<I", len(fmt_chunk)) + fmt_chunk
                 + b"data" + struct.pack("<I", len(data)) + data)
    path.write_bytes(b"RIFF" + struct.pack("<I", len(riff_body)) + riff_body)


def test_bonus_read_wav_float_roundtrips_pcm16(tmp_path):
    samples = np.array([[0.5, -0.5], [0.25, -0.25], [0.0, 0.0]])
    p = tmp_path / "pcm16.wav"
    _write_minimal_wav(p, samples, 48000, audio_format=1, bits_per_sample=16)
    sr, ch, arr = sv.read_wav_float(p)
    assert sr == 48000 and ch == 2
    np.testing.assert_allclose(arr, samples, atol=1.0 / 32768.0)


def test_bonus_read_wav_float_roundtrips_ieee_float32(tmp_path):
    samples = np.array([[0.7, -0.3], [0.1, -0.9], [1.0, -1.0]], dtype=np.float32)
    p = tmp_path / "float32.wav"
    _write_minimal_wav(p, samples, 48000, audio_format=3, bits_per_sample=32)
    sr, ch, arr = sv.read_wav_float(p)
    assert sr == 48000 and ch == 2
    # float32 -> float64 widen must be EXACT (no PCM-style quantisation)
    np.testing.assert_array_equal(arr, samples.astype(np.float64))


def test_bonus_read_wav_float_roundtrips_pcm24(tmp_path):
    """PCM24 is now load-bearing for EVERY real run (unnormalized_export()
    always renders stems at bit_depth=24, see run()), not just an
    incidental format -- was previously untested in isolation."""
    samples = np.array([[0.6, -0.6], [0.123456, -0.123456], [0.0, 0.0]])
    p = tmp_path / "pcm24.wav"
    _write_minimal_wav(p, samples, 48000, audio_format=1, bits_per_sample=24)
    sr, ch, arr = sv.read_wav_float(p)
    assert sr == 48000 and ch == 2
    np.testing.assert_allclose(arr, samples, atol=1.0 / 8388608.0)


# ============================================================================
# Regression sentinels for the polyphonic-verification audit (2026-08).
# Each of these proves a SPECIFIC finding is actually fixed, not merely that
# the tool still runs -- see the audit findings this session addressed:
#   BLOCKER  -- judge render was peak-normalized, producing a demonstrated
#               false PASS on a near-silent event.
#   MAJOR#2  -- superposition residual was dominated by reverb-tail
#               truncation, not float rounding.
#   MAJOR#3  -- judge and superposition-raw data came from two different
#               renders (now the same file).
#   MAJOR#4  -- no sentinel exercised run()'s real stem-list assembly; a
#               dropped-stem mutation slipped past every existing test.
#   MAJOR#5  -- no acceptance threshold existed for the superposition proof.
#   MAJOR#6  -- --limit made the proof a tautological self-comparison that
#               still printed as a passing headline.
#   MINOR#1  -- exit code ignored FAIL counts and the superposition result.
# ============================================================================

SENTINEL_SCORE = json.loads(SENTINEL_FIXTURE.read_text(encoding="utf-8"))


def test_completeness_check_accepts_consistent_counts():
    used = [(0, {}), (1, {}), (2, {})]
    missing = [1]
    # 2 of 3 events actually made it into the stem list -- consistent
    assert sv.check_superposition_completeness(used, missing, 2, 2) is None


def test_completeness_check_catches_stem_list_undercount():
    """Reproduces the exact mutation class the audit demonstrated: the list
    actually built for the sum is shorter than the (correct) missing_from_sum
    bookkeeping says it should be -- e.g. a stray '[...][1:]' at the call
    site. Must be refused, not silently accepted."""
    used = [(0, {}), (1, {}), (2, {})]
    missing = []  # bookkeeping says all 3 were available
    err = sv.check_superposition_completeness(used, missing, 2, 2)
    assert err is not None and "2" in err and "3" in err


def test_completeness_check_catches_compare_superposition_disagreement():
    """The list passed in matches expectations, but compare_superposition()
    itself reports a different count than it was given -- must also be
    refused (defense in depth: this is the check that would catch a bug
    INSIDE compare_superposition, independent of how the caller built the
    list)."""
    used = [(0, {}), (1, {})]
    missing = []
    err = sv.check_superposition_completeness(used, missing, 2, 1)
    assert err is not None


def test_superposition_tail_margin_ms_sourced_reverb_formula():
    """superposition_tail_margin_ms() must add exactly 2x the authored
    reverb decay (see its docstring for the -180dBFS derivation), and must
    be zero when reverb/delay are both off."""
    off = {"reverb": {"decay": 2.4, "wet": 0.0}, "delay": {"time_ms": 0, "feedback": 0, "wet": 0}}
    assert sv.superposition_tail_margin_ms(off) == 0.0

    on = {"reverb": {"decay": 2.4, "wet": 0.22}, "delay": {"time_ms": 0, "feedback": 0, "wet": 0}}
    assert sv.superposition_tail_margin_ms(on) == pytest.approx(2.0 * 2.4 * 1000.0)


def test_clamped_tail_silence_ms_respects_schema_cap():
    applied, requested, clamped = sv.clamped_tail_silence_ms(700, 100000.0)
    assert requested == pytest.approx(100700.0)
    assert applied == 60000  # scores/schema/score.schema.json tail_silence_ms max
    assert clamped is True

    applied, requested, clamped = sv.clamped_tail_silence_ms(700, 4800.0)
    assert applied == 5500 and clamped is False


def test_blocker_near_silent_event_no_longer_false_passes(tmp_path):
    """Reproduces the audit's own PoC exactly: a single cimbalom note at
    velocity=0.001 (raw level ~-76dBFS, below melody_verify's own
    BAND_GATE_DBFS=-70) previously came back PASS because the judge render
    was peak-normalized to -0.45dBFS. It must now FAIL (the tool must judge
    the note at its TRUE, unboosted level)."""
    base = json.loads(SENTINEL_FIXTURE.read_text(encoding="utf-8"))
    base["meta"]["id"] = "blocker_regression_check"
    base["events"] = [dict(base["events"][0])]
    base["events"][0]["velocity"] = 0.001

    score_path = tmp_path / "near_silent.score.json"
    score_path.write_text(json.dumps(base), encoding="utf-8")

    report, code = sv.run(str(score_path), out_dir=str(tmp_path / "out"), quiet=True)
    assert report["status"] == "ok"
    verdict = report["stem_verify"]["events"][0]["verdict"]
    assert verdict == "FAIL", (
        "expected FAIL for a near-silent (-76dBFS raw) note judged at its "
        "TRUE level; got %r -- if this is PASS again, the judge render is "
        "being boosted (normalized) again" % verdict)
    assert code == 1  # n_fail=1 must also fail the exit code (MINOR#1)


def test_e2e_run_on_real_fixture_stem_count_matches_and_established(tmp_path):
    """Runs the REAL run() orchestration (real CLI renders) end to end on
    the small fx-free sentinel fixture: n_stems_summed must equal the
    voiced event count (MAJOR#4/#7), and since there is no reverb/delay to
    truncate or to introduce IIR path-order divergence, the superposition
    proof must be ESTABLISHED against its own quantization budget
    (MAJOR#5) -- not merely 'not bit-exact' with no verdict attached."""
    score_path = tmp_path / "sentinel.score.json"
    score_path.write_text(json.dumps(SENTINEL_SCORE), encoding="utf-8")

    report, code = sv.run(str(score_path), out_dir=str(tmp_path / "out"), quiet=True)
    assert report["status"] == "ok"
    assert report["event_count_used"] == 5
    sp = report["superposition_proof"]
    assert sp["n_stems_summed"] == 5
    assert sp.get("vacuous_self_comparison") is not True
    assert sp["established"] is True, sp
    assert report["stem_verify"]["summary"]["fail"] == 0
    assert report["exit_issues"] == []
    assert code == 0


def test_e2e_dropped_stem_is_caught_not_silently_summed(tmp_path, monkeypatch):
    """End-to-end mutant twin for MAJOR#4/#7: monkeypatch
    compare_superposition so it reports a DIFFERENT n_stems_summed than it
    was actually given (simulating a bug where the real sum silently drops
    or gains a stem without the bookkeeping noticing -- the exact class of
    bug a controlled '[...][1:]' mutation was shown to produce). run() must
    refuse the whole report (status='error', non-zero exit) rather than
    print a passing or merely 'not established' result built from the
    wrong stem set."""
    score_path = tmp_path / "sentinel.score.json"
    score_path.write_text(json.dumps(SENTINEL_SCORE), encoding="utf-8")

    real_compare = sv.compare_superposition

    def lying_compare(reference_arr, stem_arrays, sample_rate, quant_bit_depth=24):
        result = real_compare(reference_arr, stem_arrays, sample_rate, quant_bit_depth)
        result["n_stems_summed"] = len(stem_arrays) - 1  # lie: claim one fewer
        return result

    monkeypatch.setattr(sv, "compare_superposition", lying_compare)

    report, code = sv.run(str(score_path), out_dir=str(tmp_path / "out"), quiet=True)
    assert report["status"] == "error"
    assert "consistency check failed" in report["error"]
    assert code == 1


def test_limited_run_superposition_is_not_applicable_not_bit_exact(tmp_path):
    """MAJOR#6: --limit rebuilds the reference from the SAME truncated
    subset as the stems, so any agreement is a tautology. A limited run
    must report the superposition result as N/A, never as a meaningful
    ESTABLISHED/BIT-EXACT headline."""
    score_path = tmp_path / "sentinel.score.json"
    score_path.write_text(json.dumps(SENTINEL_SCORE), encoding="utf-8")

    report, code = sv.run(str(score_path), out_dir=str(tmp_path / "out"),
                           limit=1, quiet=True)
    assert report["status"] == "ok"
    sp = report["superposition_proof"]
    assert sp["vacuous_self_comparison"] is True
    assert sp["established"] is None
    # a truncated debug run must not silently exit as if fully verified
    assert report["limited_run"] is True


def test_cli_exit_code_is_nonzero_when_events_fail(tmp_path):
    """MINOR#1: the CLI's exit code must reflect real FAIL verdicts, not
    just render/refusal errors (previously exit 0 even with FAILs present).
    Exercised at the actual subprocess/argparse/--json boundary (S3's style),
    independent of the direct sv.run() call in the blocker test above --
    reuses the same guaranteed-FAIL construction (a near-silent note, raw
    level below melody_verify's onset floor) since run() always renders
    exactly what a score declares, so a mismatched-declared-time FAIL (like
    S2's) cannot be produced through the real CLI without hand-editing the
    rendered WAV out from under it."""
    base = json.loads(SENTINEL_FIXTURE.read_text(encoding="utf-8"))
    base["meta"]["id"] = "exit_code_fail_check"
    base["events"] = [dict(base["events"][0])]
    base["events"][0]["velocity"] = 0.001
    score_path = tmp_path / "will_fail.score.json"
    score_path.write_text(json.dumps(base), encoding="utf-8")
    report_path = tmp_path / "report.json"

    proc = _run_stem_verify_cli(score_path, report_path)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "ok"
    assert report["stem_verify"]["summary"]["fail"] == 1
    assert any("n_fail" in x for x in report["exit_issues"])


# ============================================================================
# F-01 regression: a caller-supplied --out-dir's pre-existing stems/
# subdirectory must never be treated as this run's own to rmtree.
#   Repro (from the defect report): create <out_dir>/stems/unrelated-user-
#   file.txt, then run(..., limit=1, keep_stems=False) with that same
#   out_dir -- before the fix, this exits 0/status=ok but silently deletes
#   the unrelated file. All of these guard checks fire BEFORE find_cli() is
#   ever consulted (see run()'s ordering), so they are monkeypatched to a
#   deterministic "no CLI" stand-in and do NOT depend on TsukiSynthCLI being
#   built under build/.
# ============================================================================

def test_f01_preexisting_nonempty_stems_dir_is_refused_before_render(tmp_path, monkeypatch):
    """The exact repro: an unrelated file already sitting in <out_dir>/stems
    must survive, and the run must fail closed (status error, non-zero
    exit) -- BEFORE any render is attempted."""
    monkeypatch.setattr(sv.vs, "find_cli", lambda *a, **kw: None)

    out_dir = tmp_path / "out"
    stems_dir = out_dir / "stems"
    stems_dir.mkdir(parents=True)
    sentinel = stems_dir / "unrelated-user-file.txt"
    sentinel.write_text("do not delete me", encoding="utf-8")

    score_path = tmp_path / "score.score.json"
    score_path.write_text(json.dumps(SENTINEL_SCORE), encoding="utf-8")

    report, code = sv.run(str(score_path), out_dir=str(out_dir), limit=1, quiet=True)

    assert code == 1
    assert report["status"] == "error"
    assert str(stems_dir) in report["error"]
    assert "force-clean" in report["error"].lower()
    assert sentinel.exists(), "unrelated file must survive a fail-closed refusal"
    assert sentinel.read_text(encoding="utf-8") == "do not delete me"
    # the refusal must happen before any render/report data is produced
    assert "stem_verify" not in report
    assert "superposition_proof" not in report


def test_f01_force_clean_removes_preexisting_stems_dir(tmp_path, monkeypatch):
    """--force-clean is the explicit opt-in to reclaim a non-empty
    caller-supplied stems/ directory. The clearing happens inside the guard
    itself (before find_cli()), so this is independently verifiable without
    TsukiSynthCLI being built."""
    monkeypatch.setattr(sv.vs, "find_cli", lambda *a, **kw: None)

    out_dir = tmp_path / "out"
    stems_dir = out_dir / "stems"
    stems_dir.mkdir(parents=True)
    sentinel = stems_dir / "unrelated-user-file.txt"
    sentinel.write_text("stale data", encoding="utf-8")

    score_path = tmp_path / "score.score.json"
    score_path.write_text(json.dumps(SENTINEL_SCORE), encoding="utf-8")

    report, code = sv.run(str(score_path), out_dir=str(out_dir),
                           force_clean=True, quiet=True)

    assert not sentinel.exists(), "--force-clean must actually clear the old directory"
    # whatever happens next (no CLI, in this monkeypatched environment) must
    # be a DIFFERENT failure than the F-01 non-empty refusal -- proves
    # force-clean actually bypassed the fail-closed guard rather than the
    # run failing for some unrelated reason before reaching it.
    assert report["status"] == "error"
    assert "TsukiSynthCLI executable not found" in report["error"]
    assert "non-empty stems directory" not in report["error"]
    assert code == 1


def test_f01_preexisting_empty_stems_dir_is_used_not_blocked(tmp_path, monkeypatch):
    """An existing but EMPTY stems/ directory is not a defect -- it must be
    usable directly, never refused."""
    monkeypatch.setattr(sv.vs, "find_cli", lambda *a, **kw: None)

    out_dir = tmp_path / "out"
    stems_dir = out_dir / "stems"
    stems_dir.mkdir(parents=True)  # empty: no files inside

    score_path = tmp_path / "score.score.json"
    score_path.write_text(json.dumps(SENTINEL_SCORE), encoding="utf-8")

    report, code = sv.run(str(score_path), out_dir=str(out_dir), quiet=True)

    # must reach the (monkeypatched) CLI-not-found stage, NOT the F-01
    # non-empty refusal -- proves the empty directory was not blocked.
    assert report["status"] == "error"
    assert "TsukiSynthCLI executable not found" in report["error"]
    assert "non-empty" not in report["error"]


def test_f01_own_temp_success_and_failure_paths_unaffected(tmp_path, monkeypatch):
    """own_temp (out_dir=None) never pre-exists a stems/ directory, so it
    must never hit the new fail-closed guard, and its existing cleanup
    behaviour (full removal of stems/reference/out_root on completion) must
    be unchanged by this fix -- exercised on both the sentinel fixture's
    normal PASSing run (success path) and its near-silent-note FAIL
    construction (failure path, MINOR#1's own regression), in both cases
    with out_dir left at its default of None."""
    fake_temp_root = tmp_path / "own_temp_root"
    fake_temp_root.mkdir()
    monkeypatch.setattr(sv.tempfile, "mkdtemp", lambda *a, **kw: str(fake_temp_root))

    # -- success path: sentinel fixture verifies clean, own_temp fully
    #    cleaned up, no F-01 refusal ever triggered ------------------------
    score_path = tmp_path / "sentinel.score.json"
    score_path.write_text(json.dumps(SENTINEL_SCORE), encoding="utf-8")

    report, code = sv.run(str(score_path), quiet=True)  # out_dir=None
    assert report["status"] == "ok"
    assert code == 0
    assert report["exit_issues"] == []
    assert "non-empty stems directory" not in report.get("error", "")
    assert not fake_temp_root.exists(), (
        "own_temp cleanup must still remove its own out_root on success, "
        "exactly as before this fix")

    # -- failure path: a guaranteed-FAIL note, same own_temp flow -- must
    #    still complete (not be refused by the new guard) and report the
    #    real FAIL, with the same own_temp cleanup behaviour -------------
    fake_temp_root.mkdir()
    base = json.loads(SENTINEL_FIXTURE.read_text(encoding="utf-8"))
    base["meta"]["id"] = "f01_own_temp_failure_path_check"
    base["events"] = [dict(base["events"][0])]
    base["events"][0]["velocity"] = 0.001
    fail_score_path = tmp_path / "will_fail.score.json"
    fail_score_path.write_text(json.dumps(base), encoding="utf-8")

    report, code = sv.run(str(fail_score_path), quiet=True)  # out_dir=None
    assert report["status"] == "ok"
    assert code == 1
    assert report["stem_verify"]["summary"]["fail"] == 1
    assert "non-empty stems directory" not in report.get("error", "")
    assert not fake_temp_root.exists(), (
        "own_temp cleanup must still remove its own out_root on a "
        "completed-but-FAILed run, exactly as before this fix")


# ============================================================================
# P2 (2026-08-31): the F-01 guard above only checked containment on the
# --force-clean and cleanup paths. An existing but EMPTY stems/ (or
# reference/) that links outside out_root sailed straight through, and every
# rendered WAV landed outside the caller's --out-dir. Both subdirectories are
# now validated up front, whatever their contents.
# ============================================================================

def _link_directory(link_path, target):
    """Directory symlink, or a Windows junction when symlinks need privileges
    the test process does not have. Path.resolve() follows both identically."""
    try:
        os.symlink(target, link_path, target_is_directory=True)
        return
    except (OSError, NotImplementedError, AttributeError):
        pass
    if os.name == "nt":
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link_path), str(target)],
            capture_output=True, text=True)
        if completed.returncode == 0:
            return
    pytest.skip("this platform will not let the test process create a directory link")


@pytest.mark.parametrize("subdir_name", ["stems", "reference"])
def test_p2_empty_subdir_linked_outside_out_dir_is_refused(
        tmp_path, monkeypatch, subdir_name):
    """An EMPTY stems/ or reference/ that resolves outside --out-dir must be
    refused before anything renders -- otherwise the WAVs are written into the
    link target, outside the directory the caller nominated.

    The link target is deliberately left EMPTY. That is the actual escape:
    with a NON-empty target the pre-fix code happened to fail closed for an
    unrelated reason (the older "existing, non-empty stems" guard saw the
    target's contents through the link). With an empty target the pre-fix code
    sailed past every guard and reached the CLI lookup, i.e. a real CLI would
    have rendered outside --out-dir. Verified against a pre-fix copy."""
    monkeypatch.setattr(sv.vs, "find_cli", lambda *a, **kw: None)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    outside = tmp_path / "elsewhere"
    outside.mkdir()  # empty on purpose -- see docstring

    _link_directory(out_dir / subdir_name, outside)

    score_path = tmp_path / "score.score.json"
    score_path.write_text(json.dumps(SENTINEL_SCORE), encoding="utf-8")

    report, code = sv.run(str(score_path), out_dir=str(out_dir), limit=1,
                          quiet=True)

    assert code == 1
    assert report["status"] == "error"
    assert "not inside" in report["error"]
    assert subdir_name in report["error"]
    # Refused before the (monkeypatched) CLI lookup and before any render.
    # This is the assertion that discriminates: the pre-fix code reported
    # "TsukiSynthCLI executable not found" here instead.
    assert "TsukiSynthCLI executable not found" not in report["error"]
    assert "stem_verify" not in report
    assert list(outside.iterdir()) == [], "wrote outside --out-dir"


@pytest.mark.parametrize("subdir_name", ["stems", "reference"])
def test_p2_subdir_that_is_a_plain_file_is_refused(
        tmp_path, monkeypatch, subdir_name):
    """A plain file where stems/ or reference/ belongs must fail closed with a
    clear error instead of raising NotADirectoryError out of run()."""
    monkeypatch.setattr(sv.vs, "find_cli", lambda *a, **kw: None)

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / subdir_name).write_text("not a directory", encoding="utf-8")

    score_path = tmp_path / "score.score.json"
    score_path.write_text(json.dumps(SENTINEL_SCORE), encoding="utf-8")

    report, code = sv.run(str(score_path), out_dir=str(out_dir), limit=1,
                          quiet=True)

    assert code == 1
    assert report["status"] == "error"
    assert "not a directory" in report["error"]
    assert (out_dir / subdir_name).read_text(encoding="utf-8") == "not a directory"


def test_p2_ordinary_subdirs_inside_out_dir_still_pass_the_gate(
        tmp_path, monkeypatch):
    """The containment gate must not block the normal case: real, empty
    stems/ and reference/ directories genuinely inside --out-dir."""
    monkeypatch.setattr(sv.vs, "find_cli", lambda *a, **kw: None)

    out_dir = tmp_path / "out"
    (out_dir / "stems").mkdir(parents=True)
    (out_dir / "reference").mkdir(parents=True)

    score_path = tmp_path / "score.score.json"
    score_path.write_text(json.dumps(SENTINEL_SCORE), encoding="utf-8")

    report, code = sv.run(str(score_path), out_dir=str(out_dir), quiet=True)

    # reaches the monkeypatched CLI-not-found stage => the gate let it through
    assert "TsukiSynthCLI executable not found" in report["error"]
