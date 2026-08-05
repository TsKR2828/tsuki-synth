import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from tools import specimen_pipeline, specimen_verify


class SpecimenPipelineTests(unittest.TestCase):
    def write_csv(self, path, time_s, **columns):
        names = ["time_s", *columns]
        values = np.column_stack([time_s, *[columns[name] for name in columns]])
        np.savetxt(path, values, delimiter=",", header=",".join(names), comments="")

    def test_end_to_end_automated_bundle_is_valid_and_hashed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample_rate = 8000
            duration = 2.0
            time_s = np.arange(int(sample_rate * duration)) / sample_rate
            force_n = np.zeros_like(time_s)
            onset = int(0.05 * sample_rate)
            force_n[onset] = 1.0
            local_time = np.maximum(0.0, time_s - time_s[onset])
            decay = np.exp(-math.log(1000.0) * local_time / 1.0)
            response_si = np.where(
                time_s >= time_s[onset], decay * np.sin(2.0 * math.pi * 100.0 * local_time), 0.0)
            force_sensitivity = 0.01
            response_sensitivity = 0.02
            microphone_sensitivity = 0.05
            structural_paths = []
            for index in range(2):
                path = root / f"structural-{index}.csv"
                self.write_csv(
                    path, time_s, force_v=force_n * force_sensitivity,
                    response_v=response_si * response_sensitivity)
                structural_paths.append(path.name)
            acoustic_specs = []
            for azimuth, scale in ((0.0, 0.02), (90.0, 0.01)):
                for repetition in range(2):
                    path = root / f"acoustic-{int(azimuth)}-{repetition}.csv"
                    pressure_pa = response_si * scale
                    self.write_csv(
                        path, time_s, force_v=force_n * force_sensitivity,
                        microphone_v=pressure_pa * microphone_sensitivity)
                    acoustic_specs.append({
                        "path": path.name, "radius_m": 1.0,
                        "azimuth_deg": azimuth, "elevation_deg": 0.0,
                    })
            expected_pa = 20.0e-6 * 10.0 ** (94.0 / 20.0)
            calibrator_v = (math.sqrt(2.0) * expected_pa * microphone_sensitivity
                            * np.sin(2.0 * math.pi * 1000.0 * time_s))
            for label in ("before", "after"):
                self.write_csv(root / f"cal-{label}.csv", time_s,
                               microphone_v=calibrator_v)
            for name in ("force.txt", "response.txt", "acoustic.txt"):
                (root / name).write_text("traceable calibration evidence\n", encoding="utf-8")
            dump = {
                "contract": specimen_verify.MODE_DUMP_CONTRACT,
                "sample_rate_hz": sample_rate,
                "model_observables": [
                    "modal_frequency_hz", "relative_modal_amplitude", "modal_t60_s"
                ],
                "unsupported_observables": [
                    "complex_phase", "absolute_spl", "radiation_directivity"
                ],
                "events": [{
                    "source_index": 0, "engine": "beam",
                    "partials": [{"freq": 100.0, "amp": 1.0,
                                  "decay": 1.0, "body_mag": 1.0}],
                }],
            }
            (root / "modes.json").write_text(json.dumps(dump), encoding="utf-8")
            measurement = {
                "$schema": specimen_verify.CONTRACT_V2,
                "specimen": {
                    "id": "synthetic-pipeline-test", "instrument_family": "test",
                    "serial_or_lot": "not-a-real-specimen",
                    "geometry": {"length_m": 0.1},
                    "material": {"material_id": "synthetic"},
                    "boundary_condition": "synthetic-test-only",
                },
                "environment": {"temperature_c": 23.0,
                                "relative_humidity_pct": 50.0,
                                "pressure_kpa": 101.325},
                "acquisition": {
                    "laboratory": "unit-test", "operator": "automation",
                    "captured_at_utc": "2026-08-02T00:00:00Z",
                    "method": "impact_hammer_frf", "sample_rate_hz": sample_rate,
                    "averages": 2, "frequency_resolution_hz": 0.5,
                    "uncertainty_coverage_factor": 2.0,
                    "excitation_point_xyz_m": [0.0, 0.0, 0.0],
                    "excitation_direction_xyz": [0.0, 0.0, 1.0],
                    "response_point_xyz_m": [0.1, 0.0, 0.0],
                    "response_quantity": "acceleration_m_s2",
                },
                "artifacts": [],
                "model": {
                    "event_source_index": 0, "mode_dump_path": "generated",
                    "mode_dump_sha256": "0" * 64,
                    "uncertainty": {
                        "frequency_relative_pct": 0.0,
                        "relative_magnitude_db": 0.0, "t60_relative_pct": 0.0,
                        "phase_deg": 0.0, "absolute_level_db": 0.0,
                        "directivity_db": 0.0, "directivity_phase_deg": 0.0,
                    },
                },
                "claim_scope": {
                    "modal_frequencies": True, "relative_modal_magnitudes": True,
                    "modal_t60": True, "complex_phase": True,
                    "absolute_spl": True, "radiation_directivity": True,
                },
                "acceptance": {
                    "min_mode_count": 1, "min_coherence": 0.9,
                    "max_frequency_error_pct": 2.0,
                    "max_relative_magnitude_error_db": 3.0,
                    "max_t60_ratio": 1.25, "max_phase_error_deg": 15.0,
                    "max_absolute_level_error_db": 3.0,
                    "min_directivity_points": 2,
                    "max_directivity_error_db": 3.0,
                    "max_directivity_phase_error_deg": 20.0,
                },
                "relative_magnitude_reference_partial_index": 0,
                "measured_modes": [],
            }
            (root / "measurement-template.json").write_text(
                json.dumps(measurement), encoding="utf-8")
            recipe = {
                "$schema": specimen_pipeline.ACQUISITION_CONTRACT,
                "measurement_template": "measurement-template.json",
                "mode_dump": "modes.json",
                "channels": {
                    "force": {"column": "force_v",
                              "sensitivity_v_per_n": force_sensitivity},
                    "structural_response": {
                        "column": "response_v",
                        "sensitivity_v_per_si": response_sensitivity},
                    "microphone": {"column": "microphone_v"},
                },
                "structural_records": [{"path_glob": "structural-*.csv"}],
                "acoustic_records": [
                    {"path_glob": "acoustic-0-*.csv", "radius_m": 1.0,
                     "azimuth_deg": 0.0, "elevation_deg": 0.0},
                    {"path_glob": "acoustic-90-*.csv", "radius_m": 1.0,
                     "azimuth_deg": 90.0, "elevation_deg": 0.0},
                ],
                "calibrator": {
                    "before_path": "cal-before.csv", "after_path": "cal-after.csv",
                    "frequency_hz": 1000.0, "level_db_re_20upa": 94.0,
                },
                "evidence": [
                    {"role": "excitation_calibration", "path": "force.txt"},
                    {"role": "response_calibration", "path": "response.txt"},
                    {"role": "acoustic_calibration", "path": "acoustic.txt"},
                ],
                "analysis": {
                    "model_partial_indices": [0], "window": "boxcar",
                    "minimum_averages": 2,
                    "frequency_search_half_width_hz": 2.0,
                    "decay_bandwidth_hz": 20.0, "min_decay_fit_r2": 0.85,
                    "reference_force_rms_n": 1.0,
                },
            }
            recipe_path = root / "recipe.json"
            recipe_path.write_text(json.dumps(recipe), encoding="utf-8")
            output = root / "bundle"
            measurement_path = specimen_pipeline.build_bundle(recipe_path, output)
            bundle = json.loads(measurement_path.read_text(encoding="utf-8"))
            self.assertEqual(specimen_verify.CONTRACT_V2, bundle["$schema"])
            self.assertEqual(1, len(bundle["measured_modes"]))
            self.assertEqual(2, len(bundle["acoustic_measurements"]))
            resolved_recipe = json.loads(
                (output / "config" / "acquisition.json").read_text(encoding="utf-8"))
            self.assertEqual(2, len(resolved_recipe["structural_records"]))
            self.assertTrue(all("path" in item and "path_glob" not in item
                                for item in resolved_recipe["structural_records"]))
            self.assertAlmostEqual(0.05,
                                   json.loads((output / "analysis" / "microphone-calibration.json").read_text())["adopted_sensitivity_v_per_pa"],
                                   places=5)
            report = specimen_verify.verify_bundle(measurement_path)
            self.assertNotEqual("REFUSED", report["status"])
            self.assertEqual("UNVERIFIED", report["status"])
            saved_report = json.loads(
                (output / "verification-report.json").read_text(encoding="utf-8"))
            self.assertEqual("UNVERIFIED", saved_report["status"])

    def test_double_hit_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample_rate = 8000
            time_s = np.arange(sample_rate) / sample_rate
            force_v = np.zeros_like(time_s)
            force_v[400] = 1.0
            force_v[800] = 0.8
            path = root / "double-hit.csv"
            self.write_csv(path, time_s, force_v=force_v,
                           response_v=np.zeros_like(time_s))
            with self.assertRaises(specimen_pipeline.PipelineError):
                specimen_pipeline._record_arrays(
                    {"path": path.name}, root, sample_rate,
                    {"column": "force_v", "sensitivity_v_per_n": 1.0},
                    {"column": "response_v", "sensitivity_v_per_si": 1.0},
                    "impact_hammer_frf")

    def test_calibrator_drift_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample_rate = 8000
            time_s = np.arange(sample_rate) / sample_rate
            expected_pa = 20.0e-6 * 10.0 ** (94.0 / 20.0)
            for label, sensitivity in (("before", 0.05), ("after", 0.06)):
                voltage = (math.sqrt(2.0) * expected_pa * sensitivity
                           * np.sin(2.0 * math.pi * 1000.0 * time_s))
                self.write_csv(root / f"{label}.csv", time_s,
                               microphone_v=voltage)
            recipe = {"calibrator": {
                "before_path": "before.csv", "after_path": "after.csv",
                "frequency_hz": 1000.0, "level_db_re_20upa": 94.0,
                "max_drift_db": 0.5,
            }}
            with self.assertRaises(specimen_pipeline.PipelineError):
                specimen_pipeline._calibrator_sensitivity(
                    recipe, root, sample_rate, {"column": "microphone_v"})

    def test_recipe_schema_rejects_unknown_top_level_field(self):
        invalid = {
            "$schema": specimen_pipeline.ACQUISITION_CONTRACT,
            "measurement_template": "measurement.json", "mode_dump": "modes.json",
            "channels": {
                "force": {"sensitivity_v_per_n": 1.0},
                "structural_response": {"sensitivity_v_per_si": 1.0},
            },
            "structural_records": [{"path": "record.csv"}],
            "evidence": [
                {"role": "excitation_calibration", "path": "force.pdf"},
                {"role": "response_calibration", "path": "response.pdf"},
            ],
            "silently_ignore_this_typo": True,
        }
        with self.assertRaises(specimen_pipeline.PipelineError):
            specimen_pipeline._validate_recipe(invalid)


if __name__ == "__main__":
    unittest.main()
