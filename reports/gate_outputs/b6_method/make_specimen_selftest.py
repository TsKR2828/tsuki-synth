#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B6 workcard §8 GATE item 7 artifact generator (Phase 3/4).

Builds the SYNTHETIC_TEST_ONLY self-consistency bundle (PASS case) and its
+10dB tampered counter-example (FAIL case) using the exact same logic as
tests/test_specimen_verify.py's Phase4SelfConsistencyTests, but writes the
bundle/dump files to a PERSISTENT directory (not a tempdir that gets
deleted) and invokes `python tools/specimen_verify.py <bundle> --dump-modes
<dump>` as an actual subprocess -- matching docs/workcards/B6.md §8 row 7's
exact command -- so its real stdout can be captured into
reports/gate_outputs/b6_specimen_selftest.txt.

This is NOT a test (that's tests/test_specimen_verify.py's
Phase4SelfConsistencyTests, already covered by pytest); it is purely
evidence generation for the GATE table, kept here (matching
render_b6_scores.py's precedent in this same directory) so a future audit
can regenerate this exact evidence without re-deriving the bundle shape.

Usage (run from repo root):
    python reports/gate_outputs/b6_method/make_specimen_selftest.py [out_dir]

out_dir defaults to reports/gate_outputs/b6_specimen_selftest_bundle/.
"""
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
CLI = REPO / "build" / "TsukiSynthCLI_artefacts" / "Release" / "TsukiSynthCLI.exe"
DEFAULT_OUT_DIR = REPO / "reports" / "gate_outputs" / "b6_specimen_selftest_bundle"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def real_dump(out_dir: Path):
    """Runs --dump-modes on a fixed A4/steel/velocity=0.5 cimbalom note and
    returns (dump_dict, dump_path). strike_position is 0.31, not the
    kCimbalomAttackEnergyRefA4 anchor's 0.3 -- at exactly 0.3,
    StringModel::calculateModes()'s sin(n*pi*0.3) mode-shape formula puts a
    genuine physical amplitude NULL at n=10/20/30 (0.3=3/10 is a
    low-denominator rational), and specimen_verify.py's predicted_by_index
    construction REFUSES the whole bundle if ANY partial in the dump's full
    "partials" array has amp==0 (checked unconditionally, before any claim
    is even read). This is a genuine, pre-existing model/harness
    interaction, not a B6 bug (docs/workcards/B6.md §3 explicitly forbids
    touching specimen_verify.py). 0.31 has no such low-denominator rational
    coincidence within the modelled partial range."""
    score = {
        "$schema": "TsukiSynth Score v1",
        "meta": {"title": "B6 Phase 4 self-consistency probe", "id": "b6_phase4_probe"},
        "global": {"bpm": 120, "sample_rate": 48000, "master_volume": 0.9},
        "events": [{
            "time": 0.0, "duration": 1.0, "engine": "cimbalom",
            "note": "A4", "velocity": 0.5,
            "params": {"material": "steel", "strike_position": 0.31},
        }],
        "export": {"filename": "b6_phase4_probe"},
    }
    score_path = out_dir / "b6_phase4_probe.score.json"
    score_path.write_text(json.dumps(score), encoding="utf-8")
    result = subprocess.run([str(CLI), "--dump-modes", str(score_path)],
                            capture_output=True, text=True, encoding="utf-8",
                            errors="replace")
    assert result.returncode == 0, f"--dump-modes failed:\n{result.stdout}\n{result.stderr}"
    dump_path = out_dir / "b6_phase4_probe.modes.json"
    dump_path.write_text(result.stdout, encoding="utf-8")
    dump = json.loads(result.stdout)
    assert len(dump["events"]) == 1
    return dump, dump_path


def level_db(real, imag):
    # Mirrors specimen_verify._complex_level_db() exactly.
    magnitude = math.hypot(real, imag)
    return 20.0 * math.log10(magnitude / 20.0e-6)


def make_bundle(out_dir: Path, specimen_verify, dump, dump_path, tamper_db, bundle_name):
    event = dump["events"][0]
    transfer = event["acoustic_transfer"]
    assert transfer, "fixture note must produce at least one acoustic_transfer point"
    partials = event["partials"]
    indices = sorted({point["model_partial_index"] for point in transfer})
    reference_index = indices[0]

    measured_modes = []
    for index in indices:
        p = partials[index]
        measured_modes.append({
            "model_partial_index": index,
            "frequency_hz": p["freq"], "frequency_u_hz": 0.01,
            "relative_magnitude_db": 0.0, "magnitude_u_db": 0.01,
            "t60_s": p["decay"], "t60_u_s": p["decay"] * 0.01,
            "coherence": 0.999,
            "phase_deg": 0.0, "phase_u_deg": 1.0,
            "frf_real_si_per_n": 1.0, "frf_imag_si_per_n": 0.0,
            "decay_fit_r2": 0.999,
        })

    acoustic_measurements = []
    for point_index, point in enumerate(transfer):
        real = point["pressure_per_force_real_pa_n"]
        imag = point["pressure_per_force_imag_pa_n"]
        if point_index == 0 and tamper_db:
            # docs/workcards/B6.md §7 item 4: bump ONE measured point,
            # keeping real/imag internally consistent with the level
            # specimen_verify.py itself recomputes and cross-checks.
            scale = 10.0 ** (tamper_db / 20.0)
            real *= scale
            imag *= scale
        level = level_db(real, imag)
        reference_force_rms_n = 1.0
        acoustic_measurements.append({
            "model_partial_index": point["model_partial_index"],
            "frequency_hz": partials[point["model_partial_index"]]["freq"],
            "radius_m": point["radius_m"], "azimuth_deg": point["azimuth_deg"],
            "elevation_deg": point["elevation_deg"],
            "pressure_per_force_real_pa_n": real,
            "pressure_per_force_imag_pa_n": imag,
            "transfer_level_db_re_20upa_per_n": level,
            "transfer_u_db": 0.0, "phase_u_deg": 0.0, "coherence": 0.999,
            "reference_force_rms_n": reference_force_rms_n,
            "spl_db_re_20upa": level + 20.0 * math.log10(reference_force_rms_n),
        })

    roles = sorted(specimen_verify.REQUIRED_ARTIFACT_ROLES
                   | specimen_verify.V2_REQUIRED_ARTIFACT_ROLES
                   | specimen_verify.V2_ACOUSTIC_ARTIFACT_ROLES)
    artifacts = []
    for role in roles:
        path = out_dir / f"{role}.csv"
        if not path.exists():
            path.write_text(
                f"SYNTHETIC_TEST_ONLY self-consistency evidence for {role} "
                "-- NOT a real specimen measurement, see "
                "tests/test_specimen_verify.py Phase4SelfConsistencyTests\n",
                encoding="utf-8")
        artifacts.append({"role": role, "path": path.name, "sha256": sha256(path)})

    bundle = {
        "$schema": specimen_verify.CONTRACT_V2,
        "specimen": {
            "id": "SYNTHETIC_TEST_ONLY-b6-phase4-selfcheck",
            "instrument_family": "cimbalom", "serial_or_lot": "SYNTHETIC_TEST_ONLY",
            "geometry": {"note": "SYNTHETIC_TEST_ONLY -- not a real specimen"},
            "material": {"note": "SYNTHETIC_TEST_ONLY -- not a real specimen"},
            "boundary_condition": "SYNTHETIC_TEST_ONLY",
        },
        "environment": {"temperature_c": 23.0, "relative_humidity_pct": 50.0, "pressure_kpa": 101.325},
        "acquisition": {
            "laboratory": "SYNTHETIC_TEST_ONLY -- not a real lab, see docs/workcards/B6.md §7 item 2",
            "operator": "b6-phase4-self-consistency-test",
            "captured_at_utc": "2026-08-28T00:00:00Z",
            "method": "impact_hammer_frf", "sample_rate_hz": 48000,
            "averages": 8, "frequency_resolution_hz": 0.25,
            "uncertainty_coverage_factor": 2.0,
            "excitation_point_xyz_m": [0.0, 0.0, 0.0],
            "excitation_direction_xyz": [0.0, 0.0, 1.0],
            "response_point_xyz_m": [1.05, 0.0, 0.0],
            "response_quantity": "pressure_pa",
        },
        "artifacts": artifacts,
        "model": {
            "event_source_index": event["source_index"],
            "mode_dump_path": dump_path.name,
            "mode_dump_sha256": sha256(dump_path),
            "uncertainty": {
                "frequency_relative_pct": 0.0, "relative_magnitude_db": 0.0,
                "t60_relative_pct": 0.0, "phase_deg": 0.0,
                "absolute_level_db": 0.0, "directivity_db": 0.0,
                "directivity_phase_deg": 0.0,
            },
        },
        "claim_scope": {
            "modal_frequencies": False, "relative_modal_magnitudes": False,
            "modal_t60": False, "complex_phase": False,
            "absolute_spl": True, "radiation_directivity": False,
        },
        "acceptance": {
            "min_mode_count": 1, "min_coherence": 0.9,
            "max_frequency_error_pct": 0.5, "max_relative_magnitude_error_db": 0.2,
            "max_t60_ratio": 1.02, "max_phase_error_deg": 5.0,
            "max_absolute_level_error_db": 0.01,
            "min_directivity_points": 2, "max_directivity_error_db": 0.1,
            "max_directivity_phase_error_deg": 1.0,
        },
        "relative_magnitude_reference_partial_index": reference_index,
        "measured_modes": measured_modes,
        "acoustic_measurements": acoustic_measurements,
    }
    bundle_path = out_dir / bundle_name
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return bundle_path


def main():
    out_dir = (Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT_DIR).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(REPO))
    from tools import specimen_verify  # noqa: E402  (needs REPO on sys.path first)

    dump, dump_path = real_dump(out_dir)
    pass_bundle = make_bundle(out_dir, specimen_verify, dump, dump_path, tamper_db=0.0,
                              bundle_name="measurement_selfconsistent.json")
    fail_bundle = make_bundle(out_dir, specimen_verify, dump, dump_path, tamper_db=10.0,
                              bundle_name="measurement_tampered_10db.json")

    print("=" * 78)
    print("B6 workcard §8 GATE item 7: specimen_verify.py self-consistency selftest")
    print("SYNTHETIC_TEST_ONLY -- self-consistency proof, NOT real specimen evidence")
    print("=" * 78)
    print()
    print(f"real dump: {dump_path}")
    print("real CLI note: A4, steel, strike_position=0.31, velocity=0.5, wood exciter")
    print(f"acoustic_transfer points in this dump: "
          f"{dump['events'][0]['acoustic_transfer']}")
    print()
    print("--- Case 1: self-consistent bundle (measured == predicted, verbatim copy) ---")
    print(f"$ python tools/specimen_verify.py {pass_bundle.relative_to(REPO)} "
          f"--dump-modes {dump_path.relative_to(REPO)}")
    r1 = subprocess.run([sys.executable, str(REPO / "tools" / "specimen_verify.py"),
                         str(pass_bundle), "--dump-modes", str(dump_path)],
                        capture_output=True, text=True, encoding="utf-8")
    print(r1.stdout)
    if r1.stderr:
        print("[stderr]", r1.stderr)
    print(f"exit code: {r1.returncode}")
    print()
    print("--- Case 2: tampered bundle (+10dB on partial 0's measured level) ---")
    print(f"$ python tools/specimen_verify.py {fail_bundle.relative_to(REPO)} "
          f"--dump-modes {dump_path.relative_to(REPO)}")
    r2 = subprocess.run([sys.executable, str(REPO / "tools" / "specimen_verify.py"),
                         str(fail_bundle), "--dump-modes", str(dump_path)],
                        capture_output=True, text=True, encoding="utf-8")
    print(r2.stdout)
    if r2.stderr:
        print("[stderr]", r2.stderr)
    print(f"exit code: {r2.returncode}")
    print()
    ok = ("RESULT: PASS" in r1.stdout) and ("RESULT: FAIL" in r2.stdout)
    print("=" * 78)
    print("OVERALL:", "PASS (self-consistent=PASS, tampered=FAIL, as expected)" if ok
          else "UNEXPECTED -- see cases above")
    print("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
