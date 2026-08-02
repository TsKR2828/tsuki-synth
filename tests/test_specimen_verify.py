import copy
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

from tools import specimen_verify


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


if __name__ == "__main__":
    unittest.main()
