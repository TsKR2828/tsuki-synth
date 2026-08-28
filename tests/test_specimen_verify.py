import copy
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

from tools import specimen_verify
from tools import verify_score


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SpecimenVerificationTests(unittest.TestCase):
    def make_fixture(self, directory):
        root = Path(directory)
        artifacts = []
        for role in sorted(specimen_verify.REQUIRED_ARTIFACT_ROLES):
            path = root / f"{role}.csv"
            path.write_text(f"calibrated evidence for {role}\n", encoding="utf-8")
            artifacts.append({"role": role, "path": path.name, "sha256": sha256(path)})

        dump = {
            "contract": specimen_verify.MODE_DUMP_CONTRACT,
            "sample_rate_hz": 96000,
            "model_observables": [
                "modal_frequency_hz", "relative_modal_amplitude", "modal_t60_s"
            ],
            "unsupported_observables": [
                "complex_phase", "absolute_spl", "radiation_directivity"
            ],
            "input_event_count": 1,
            "events": [{
                "source_index": 0,
                "engine": "beam",
                "partials": [
                    {"freq": 100.0, "amp": 1.0, "decay": 2.0, "body_mag": 1.0},
                    {"freq": 250.0, "amp": 0.5, "decay": 1.0, "body_mag": 1.0},
                ],
            }],
            "dumped_event_count": 1,
        }
        dump_path = root / "modes.json"
        dump_path.write_text(json.dumps(dump), encoding="utf-8")

        bundle = {
            "$schema": specimen_verify.CONTRACT,
            "specimen": {
                "id": "beam-A-001", "instrument_family": "cantilever_tongue",
                "serial_or_lot": "lot-7", "geometry": {"length_m": 0.1},
                "material": {"young_modulus_pa": 2.0e11},
                "boundary_condition": "clamped-free",
            },
            "environment": {
                "temperature_c": 23.0, "relative_humidity_pct": 50.0,
                "pressure_kpa": 101.325,
            },
            "acquisition": {
                "laboratory": "test-lab", "operator": "operator-1",
                "captured_at_utc": "2026-08-02T00:00:00Z",
                "method": "impact_hammer_frf", "sample_rate_hz": 96000,
                "averages": 8, "frequency_resolution_hz": 0.25,
                "uncertainty_coverage_factor": 2.0,
                "excitation_point_xyz_m": [0.09, 0.0, 0.0],
                "excitation_direction_xyz": [0.0, 0.0, 1.0],
                "response_point_xyz_m": [0.08, 0.0, 0.0],
                "response_quantity": "acceleration_m_s2",
            },
            "artifacts": artifacts,
            "model": {
                "event_source_index": 0, "mode_dump_sha256": sha256(dump_path),
                "uncertainty": {
                    "frequency_relative_pct": 0.0, "relative_magnitude_db": 0.0,
                    "t60_relative_pct": 0.0, "phase_deg": 0.0,
                },
            },
            "claim_scope": {
                "modal_frequencies": True, "relative_modal_magnitudes": True,
                "modal_t60": True, "complex_phase": False,
                "absolute_spl": False, "radiation_directivity": False,
            },
            "acceptance": {
                "min_mode_count": 2, "min_coherence": 0.9,
                "max_frequency_error_pct": 0.5,
                "max_relative_magnitude_error_db": 0.2,
                "max_t60_ratio": 1.02, "max_phase_error_deg": 5.0,
            },
            "relative_magnitude_reference_partial_index": 0,
            "measured_modes": [
                {
                    "model_partial_index": 0, "frequency_hz": 100.0,
                    "frequency_u_hz": 0.01, "relative_magnitude_db": 0.0,
                    "magnitude_u_db": 0.01, "t60_s": 2.0, "t60_u_s": 0.005,
                    "coherence": 0.999,
                },
                {
                    "model_partial_index": 1, "frequency_hz": 250.0,
                    "frequency_u_hz": 0.01,
                    "relative_magnitude_db": 20.0 * math.log10(0.5),
                    "magnitude_u_db": 0.01, "t60_s": 1.0, "t60_u_s": 0.005,
                    "coherence": 0.998,
                },
            ],
        }
        bundle_path = root / "measurement.json"
        bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
        return bundle, bundle_path, dump_path

    def test_exact_supported_observables_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            _, bundle_path, dump_path = self.make_fixture(directory)
            report = specimen_verify.verify_bundle(bundle_path, dump_path)
            self.assertEqual("PASS", report["status"])
            self.assertEqual(0, report["exit_code"])

    def test_frequency_counterexample_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, bundle_path, dump_path = self.make_fixture(directory)
            bundle["measured_modes"][1]["frequency_hz"] = 260.0
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            report = specimen_verify.verify_bundle(bundle_path, dump_path)
            self.assertEqual("FAIL", report["status"])

    def test_low_coherence_fails_data_quality(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, bundle_path, dump_path = self.make_fixture(directory)
            bundle["measured_modes"][0]["coherence"] = 0.5
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            report = specimen_verify.verify_bundle(bundle_path, dump_path)
            self.assertEqual("FAIL", report["status"])

    def test_requested_missing_phase_is_unverified_not_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, bundle_path, dump_path = self.make_fixture(directory)
            bundle["claim_scope"]["complex_phase"] = True
            for mode in bundle["measured_modes"]:
                mode["phase_deg"] = 0.0
                mode["phase_u_deg"] = 1.0
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            report = specimen_verify.verify_bundle(bundle_path, dump_path)
            self.assertEqual("UNVERIFIED", report["status"])
            self.assertEqual(3, report["exit_code"])

    def test_tampered_raw_artifact_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, bundle_path, dump_path = self.make_fixture(directory)
            raw = next(item for item in bundle["artifacts"]
                       if item["role"] == "raw_response")
            (Path(directory) / raw["path"]).write_text("tampered\n", encoding="utf-8")
            report = specimen_verify.verify_bundle(bundle_path, dump_path)
            self.assertEqual("REFUSED", report["status"])

    def test_nan_is_refused_even_though_python_json_accepts_it(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, bundle_path, dump_path = self.make_fixture(directory)
            bundle["measured_modes"][0]["frequency_hz"] = float("nan")
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            report = specimen_verify.verify_bundle(bundle_path, dump_path)
            self.assertEqual("REFUSED", report["status"])

    def make_v2_fixture(self, directory):
        bundle, bundle_path, dump_path = self.make_fixture(directory)
        root = Path(directory)
        bundle["$schema"] = specimen_verify.CONTRACT_V2
        bundle["model"]["mode_dump_path"] = dump_path.name
        bundle["model"]["uncertainty"].update({
            "absolute_level_db": 0.0, "directivity_db": 0.0,
            "directivity_phase_deg": 0.0,
        })
        bundle["acceptance"].update({
            "max_absolute_level_error_db": 0.1,
            "min_directivity_points": 2,
            "max_directivity_error_db": 0.1,
            "max_directivity_phase_error_deg": 1.0,
        })
        bundle["claim_scope"].update({
            "complex_phase": True, "absolute_spl": True,
            "radiation_directivity": True,
        })
        for mode in bundle["measured_modes"]:
            mode.update({
                "phase_deg": -30.0, "phase_u_deg": 0.0,
                "frf_real_si_per_n": 1.0, "frf_imag_si_per_n": 0.0,
                "decay_fit_r2": 0.999,
            })
        acoustic = []
        transfer = []
        for partial_index, magnitude in ((0, 0.02), (1, 0.01)):
            for azimuth, scale, phase_deg in ((0.0, 1.0, 20.0), (90.0, 0.5, -10.0)):
                value = magnitude * scale * complex(
                    math.cos(math.radians(phase_deg)),
                    math.sin(math.radians(phase_deg)))
                level = 20.0 * math.log10(abs(value) / 20.0e-6)
                acoustic.append({
                    "model_partial_index": partial_index,
                    "frequency_hz": 100.0 if partial_index == 0 else 250.0,
                    "radius_m": 1.0, "azimuth_deg": azimuth,
                    "elevation_deg": 0.0,
                    "pressure_per_force_real_pa_n": value.real,
                    "pressure_per_force_imag_pa_n": value.imag,
                    "transfer_level_db_re_20upa_per_n": level,
                    "transfer_u_db": 0.0, "phase_u_deg": 0.0,
                    "coherence": 0.999, "reference_force_rms_n": 2.0,
                    "spl_db_re_20upa": level + 20.0 * math.log10(2.0),
                })
                transfer.append({
                    "model_partial_index": partial_index,
                    "radius_m": 1.0, "azimuth_deg": azimuth,
                    "elevation_deg": 0.0,
                    "pressure_per_force_real_pa_n": value.real,
                    "pressure_per_force_imag_pa_n": value.imag,
                })
        bundle["acoustic_measurements"] = acoustic
        dump = json.loads(dump_path.read_text(encoding="utf-8"))
        dump["model_observables"].extend([
            "complex_phase", "absolute_pressure_per_force",
            "radiation_directivity",
        ])
        dump["unsupported_observables"] = []
        for partial in dump["events"][0]["partials"]:
            partial["phase_deg"] = -30.0
        dump["events"][0]["acoustic_transfer"] = transfer
        dump_path.write_text(json.dumps(dump), encoding="utf-8")
        bundle["model"]["mode_dump_sha256"] = sha256(dump_path)
        for role in (
                "analysis_config", "derived_frf", "raw_acoustic_response",
                "acoustic_calibration", "derived_acoustic_transfer"):
            path = root / f"{role}.csv"
            path.write_text(f"evidence for {role}\n", encoding="utf-8")
            bundle["artifacts"].append({
                "role": role, "path": path.name, "sha256": sha256(path)})
        bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
        return bundle, bundle_path, dump_path

    def test_v2_complex_phase_absolute_level_and_directivity_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            _, bundle_path, _ = self.make_v2_fixture(directory)
            report = specimen_verify.verify_bundle(bundle_path)
            self.assertEqual("PASS", report["status"])
            self.assertEqual("TsukiSynth Specimen Verification Report v2",
                             report["contract"])

    def test_v2_inconsistent_spl_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, bundle_path, _ = self.make_v2_fixture(directory)
            bundle["acoustic_measurements"][0]["spl_db_re_20upa"] += 1.0
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            report = specimen_verify.verify_bundle(bundle_path)
            self.assertEqual("REFUSED", report["status"])

    def test_v2_missing_model_direction_is_unverified(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, bundle_path, dump_path = self.make_v2_fixture(directory)
            dump = json.loads(dump_path.read_text(encoding="utf-8"))
            dump["events"][0]["acoustic_transfer"].pop()
            dump_path.write_text(json.dumps(dump), encoding="utf-8")
            bundle["model"]["mode_dump_sha256"] = sha256(dump_path)
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            report = specimen_verify.verify_bundle(bundle_path)
            self.assertEqual("UNVERIFIED", report["status"])

    def test_v2_directivity_counterexample_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle, bundle_path, _ = self.make_v2_fixture(directory)
            point = bundle["acoustic_measurements"][1]
            scale = 10.0 ** (6.0 / 20.0)
            point["pressure_per_force_real_pa_n"] *= scale
            point["pressure_per_force_imag_pa_n"] *= scale
            point["transfer_level_db_re_20upa_per_n"] += 6.0
            point["spl_db_re_20upa"] += 6.0
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            report = specimen_verify.verify_bundle(bundle_path)
            self.assertEqual("FAIL", report["status"])


ROOT = Path(__file__).resolve().parents[1]


class RealDumpModesRadiationSentinelTests(unittest.TestCase):
    """docs/workcards/B6.md §7 regression sentinel: reads a REAL C++
    --dump-modes output (not a hand-built fixture) and asserts that B6's
    Phase 1 informational field ("radiated_power_relative") shows up where
    expected, and that the three fields B6 explicitly must NOT add
    ("radiation_directivity", "complex_phase", "absolute_pressure_per_force")
    never appear in model_observables. This guards against someone later
    "helpfully" adding those alongside acoustic_transfer data, thinking
    "the data's all there anyway" (docs/workcards/B6.md §11 second bullet).

    Unlike every other test in this file, this one drives the real CLI
    binary via subprocess (see tools/verify_score.py's dump_modes()) instead
    of hand-crafting a Mode Dump v2 JSON fixture -- per B6.md §7's explicit
    instruction to use "真實 dump" rather than another hand-built one for
    this particular sentinel.
    """

    @classmethod
    def setUpClass(cls):
        cls.cli = verify_score.find_cli()
        if cls.cli is None:
            raise unittest.SkipTest (
                "TsukiSynthCLI not built -- run cmake --build build "
                "--target TsukiSynthCLI first (X4 regulation)")

    def _dump(self, score_rel_path):
        score_path = ROOT / score_rel_path
        self.assertTrue (score_path.exists(), f"missing score fixture: {score_path}")
        return verify_score.dump_modes (self.cli, str (score_path))

    def test_piano_path_gets_radiated_power_relative_not_forbidden_fields(self):
        # physical_piano.score.json: 4 events, engine="piano" -- the B6
        # string/cimbalom/piano path this diagnostic field is scoped to.
        dump = self._dump ("scores/examples/physical_piano.score.json")
        observables = dump["model_observables"]
        self.assertIn ("radiated_power_relative", observables,
                        "Phase 1 informational field must be present in "
                        "model_observables for a real dump")
        for forbidden in ("radiation_directivity", "complex_phase",
                          "absolute_pressure_per_force"):
            self.assertNotIn (forbidden, observables,
                              f"B6 Phase 1 must never add {forbidden!r} to "
                              "model_observables -- that needs a real phase/"
                              "directivity model B6 does not build (see "
                              "docs/workcards/B6.md §11)")
        # unsupported_observables must still list all three -- B6 does not
        # close any of these UNVERIFIED claims (only Phase 4's
        # absolute_pressure_per_force could partly do so, and Phase 4 is not
        # in scope here).
        unsupported = dump["unsupported_observables"]
        for still_unsupported in ("radiation_directivity", "complex_phase",
                                  "absolute_spl"):
            self.assertIn (still_unsupported, unsupported)
        self.assertTrue (any ("radiated_power_relative" in p
                              for event in dump["events"]
                              for p in event["partials"]),
                         "at least one piano partial should carry the "
                         "per-partial radiated_power_relative diagnostic value")
        # Every acoustic_transfer array in this dump (Phase 1 does not add
        # this field, only Phase 4 would) must be absent entirely -- B6
        # Phase 1 does not add acoustic_transfer.
        for event in dump["events"]:
            self.assertNotIn ("acoustic_transfer", event,
                              "B6 Phase 1 must not add acoustic_transfer "
                              "(that is Phase 4, gated on Phase 2's "
                              "calibration decision)")

    def test_fm_engine_produces_no_dump_events_at_all(self):
        # fur_elise_opening.score.json: engine="fm" only. dumpModes() skips
        # fm events entirely (pre-existing "fm = non-modal synthesis"
        # behaviour in ScoreRenderer.h, not something B6 introduced) --
        # confirm B6 did not accidentally change that: an all-fm score must
        # still dump 0 events, not crash and not gain any B6 fields.
        dump = self._dump ("scores/examples/fur_elise_opening.score.json")
        self.assertEqual (len (dump["events"]), 0,
                          "fm-only score must still dump 0 events (fm is "
                          "non-modal synthesis, skipped before B6's "
                          "radiation branch is ever reached)")
        self.assertIn ("radiated_power_relative", dump["model_observables"],
                       "the top-level model_observables string is added "
                       "unconditionally (B6.md §5: \"固定加入\"), even for a "
                       "score that ends up with zero dumped events")

    def test_water_gong_path_never_gets_radiated_power_relative_per_partial(self):
        # water_gong_free.score.json: engine="water_gong" -- a REAL modal
        # engine that DOES appear in dumpModes() output (unlike fm), but is
        # explicitly out of B6's string/cimbalom/piano scope (docs/workcards/
        # B6.md §3/§11: beam/tongue_drum/plate/water_gong/custom never get
        # the per-partial radiated_power_relative value, only string/
        # cimbalom/piano do).
        dump = self._dump ("scores/examples/water_gong_free.score.json")
        self.assertGreater (len (dump["events"]), 0, "fixture should have events")
        for event in dump["events"]:
            self.assertEqual (event["engine"], "water_gong")
            for p in event["partials"]:
                self.assertNotIn ("radiated_power_relative", p,
                                  "water_gong engine partials must never "
                                  "carry radiated_power_relative (out of "
                                  "B6 scope, docs/workcards/B6.md §3)")
            self.assertNotIn ("acoustic_transfer", event,
                              "B6 Phase 1 must not add acoustic_transfer "
                              "for any engine (that is Phase 4)")


if __name__ == "__main__":
    unittest.main()
