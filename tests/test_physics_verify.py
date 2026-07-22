"""Regression tests for the ear-free spectral/T60 metrology gates."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "physics_verify", ROOT / "tools" / "physics_verify.py")
pv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pv)


class PhysicsVerifyMetrologyTests(unittest.TestCase):
    def test_internal_adversarial_suite(self):
        results = pv.run_internal_selftests()
        failed = {name: detail for name, (ok, detail) in results.items() if not ok}
        self.assertEqual({}, failed)

    def test_overlapping_windows_cannot_reuse_one_peak(self):
        sr = 48000
        signal = pv._synthetic_modal_signal(sr, 0.7, [1025.0])
        measured = pv.measure_partials(sr, signal, [1000.0, 1050.0])
        found_bins = [m["bin"] for m in measured if m["status"] == "found"]
        self.assertEqual(len(found_bins), len(set(found_bins)))
        expected = [{"freq": f, "model_db": 0.0, "required": True}
                    for f in (1000.0, 1050.0)]
        ok, _, _ = pv.assess_partial_frequencies(expected, measured, 6.0)
        self.assertFalse(ok)  # a Hann sidelobe cannot stand in for mode two

    def test_out_of_band_is_explicit_and_fails_when_required(self):
        sr = 48000
        signal = pv._synthetic_modal_signal(sr, 0.7, [440.0])
        expected = [
            {"freq": 440.0, "model_db": 0.0, "required": True},
            {"freq": 30000.0, "model_db": 0.0, "required": True},
        ]
        measured = pv.measure_partials(sr, signal, [440.0, 30000.0])
        ok, _, coverage = pv.assess_partial_frequencies(expected, measured, 3.0)
        self.assertEqual("out_of_band", measured[1]["status"])
        self.assertFalse(ok)
        self.assertEqual(1, coverage["passed"])

    def test_stiff_string_oracle_is_not_integer_harmonics(self):
        score = {
            "events": [{
                "note": "60",
                "params": {"material": "steel", "diameter_mm": 0.8,
                           "tension_n": 0},
            }]
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "probe.score.json"
            path.write_text(json.dumps(score), encoding="utf-8")
            freqs = pv.stiff_string_oracle(path, count=6)
        f0 = freqs[0]
        self.assertGreater(freqs[5] / f0, 6.0)
        self.assertNotAlmostEqual(freqs[5], 6.0 * f0, places=3)

    def test_material_observability_requires_eight_cycles(self):
        minimum = pv.material_min_observable_t60(261.625565)
        self.assertAlmostEqual(8.0 / 261.625565, minimum, places=9)
        self.assertLess(0.028, minimum)   # rubber C4 is explicitly N/A


class EigenvalueAnchorTests(unittest.TestCase):
    """F1 (2026-07-18): literature eigenvalue anchors for beam/plate dumps."""

    def test_cantilever_betal_are_characteristic_equation_roots(self):
        # cos(x)*cosh(x) = -1 (fixed-free Euler-Bernoulli), solved
        # independently here — the table must be literature, not lore.
        import math
        from scipy.optimize import brentq
        for b in pv.CANTILEVER_BETAL:
            root = brentq(lambda x: math.cos(x) * math.cosh(x) + 1.0,
                          b - 0.01, b + 0.01)
            self.assertAlmostEqual(root, b, places=5)

    def test_free_free_betal_are_characteristic_equation_roots(self):
        # cos(x)*cosh(x) = +1 (free-free), flexible branch.
        import math
        from scipy.optimize import brentq
        for b in pv.BEAM_BETAL:
            root = brentq(lambda x: math.cos(x) * math.cosh(x) - 1.0,
                          b - 0.01, b + 0.01)
            self.assertAlmostEqual(root, b, places=5)

    def test_free_plate_solver_reproduces_leissa_nu033(self):
        # The Python characteristic-equation solver must land within Leissa
        # Table 2.5's own rounding (<=0.2%) of the published nu=0.33 values —
        # this pins the solver to the primary literature source.
        omegas = pv.free_plate_omegas(0.33)
        self.assertIsNotNone(omegas)
        self.assertEqual(len(pv.PLATE_FREE_OMEGA), len(omegas))
        for got, table in zip(omegas, pv.PLATE_FREE_OMEGA):
            self.assertLess(abs(got / table - 1.0), 0.002,
                            f"solved {got} vs table {table}")

    def test_free_plate_solver_is_poisson_sensitive(self):
        # The free-edge spectrum must move with nu (the clamped one doesn't);
        # a solver ignoring nu would silently break the bronze (nu=0.34) case.
        r33 = pv.free_plate_omegas(0.33)
        r49 = pv.free_plate_omegas(0.49)
        ratio33 = r33[1] / r33[0]
        ratio49 = r49[1] / r49[0]
        self.assertGreater(abs(ratio49 - ratio33) / ratio33, 0.05)

    def test_ratio_judgment_negative_cases(self):
        anchors = pv.cantilever_ratios(5)
        f1 = 261.626
        good = [f1 * r for r in anchors]
        ok, rows = pv.judge_frequency_ratios(good, anchors,
                                             pv.EIGEN_RATIO_TOL_PCT)
        self.assertTrue(ok)
        self.assertTrue(all(r["verdict"] == "PASS" for r in rows))
        # a 1% corruption of one table entry (the class of bug that motivated
        # F1) must fail at the 0.10% tolerance
        bad = list(good)
        bad[2] *= 1.01
        ok_bad, rows_bad = pv.judge_frequency_ratios(bad, anchors,
                                                     pv.EIGEN_RATIO_TOL_PCT)
        self.assertFalse(ok_bad)
        self.assertEqual("FAIL", rows_bad[2]["verdict"])
        # a truncated dump must not shrink the anchor's coverage
        ok_missing, rows_missing = pv.judge_frequency_ratios(
            good[:3], anchors, pv.EIGEN_RATIO_TOL_PCT)
        self.assertFalse(ok_missing)
        self.assertEqual("MISSING", rows_missing[4]["verdict"])
        # empty dump fails, never crashes
        ok_empty, _ = pv.judge_frequency_ratios([], anchors,
                                                pv.EIGEN_RATIO_TOL_PCT)
        self.assertFalse(ok_empty)


class EqualTemperamentAnchorTests(unittest.TestCase):
    """F2 (2026-07-18): ET is the primary absolute-pitch anchor."""

    def test_et_anchor_rejects_agreeing_but_detuned_pair(self):
        # dump and render agree with each other but both sit +20 cents off
        # 12-TET: the OLD dump-only judgment passes, the ET anchor must fail.
        sr = 48000
        f_et = 440.0
        f_shifted = f_et * 2.0 ** (20.0 / 1200.0)
        sig = pv._synthetic_modal_signal(sr, 0.7, [f_shifted])
        expected = [{"freq": f_shifted, "model_db": 0.0, "required": True}]
        meas = pv.measure_partials(sr, sig, [f_shifted])
        ok_dump_only, _, _ = pv.assess_partial_frequencies(expected, meas, 3.0)
        self.assertTrue(ok_dump_only)   # dump self-consistency alone is green
        ok_et, rows, _ = pv.assess_partial_frequencies(
            expected, meas, 3.0, f0_expected_et=f_et)
        self.assertFalse(ok_et)         # ...but the ET anchor catches it
        self.assertGreater(abs(rows[0]["et_cents"]), pv.F0_TOL_CENTS)

    def test_et_anchor_passes_on_pitch_and_keeps_conformance(self):
        sr = 48000
        sig = pv._synthetic_modal_signal(sr, 0.7, [440.0])
        expected = [{"freq": 440.0, "model_db": 0.0, "required": True}]
        meas = pv.measure_partials(sr, sig, [440.0])
        ok, rows, _ = pv.assess_partial_frequencies(
            expected, meas, 3.0, f0_expected_et=440.0)
        self.assertTrue(ok)
        self.assertLessEqual(abs(rows[0]["et_cents"]), pv.F0_TOL_CENTS)
        self.assertLessEqual(abs(rows[0]["impl_cents"]), pv.F0_TOL_CENTS)

    def test_et_anchor_rejects_render_off_both(self):
        # render off-pitch while dump stays honest: both checks must fail it
        sr = 48000
        sig = pv._synthetic_modal_signal(sr, 0.7, [440.0 * 2.0 ** (20.0 / 1200.0)])
        expected = [{"freq": 440.0, "model_db": 0.0, "required": True}]
        meas = pv.measure_partials(sr, sig, [440.0])
        ok, _, _ = pv.assess_partial_frequencies(
            expected, meas, 3.0, f0_expected_et=440.0)
        self.assertFalse(ok)


class VelocityLawTests(unittest.TestCase):
    """F3 (2026-07-18): |predicted_delta - 20*log10(2)| <= 1.0 dB bound."""

    def test_law_constant_value(self):
        self.assertAlmostEqual(6.0206, pv.VELOCITY_LAW_DB, places=4)

    def test_lawful_pair_passes(self):
        ok, detail = pv.assess_velocity_delta(pv.VELOCITY_LAW_DB,
                                              pv.VELOCITY_LAW_DB)
        self.assertTrue(ok)
        self.assertTrue(detail["match_ok"] and detail["law_ok"])

    def test_model_violating_law_fails_even_when_render_matches(self):
        # the exact degeneration F3 exists to close: model predicts +9,
        # render delivers +9 — self-consistent, but not physics.
        ok, detail = pv.assess_velocity_delta(9.0, 9.0)
        self.assertFalse(ok)
        self.assertTrue(detail["match_ok"])
        self.assertFalse(detail["law_ok"])

    def test_render_mismatch_fails(self):
        ok, detail = pv.assess_velocity_delta(4.0, pv.VELOCITY_LAW_DB)
        self.assertFalse(ok)
        self.assertFalse(detail["match_ok"])
        self.assertTrue(detail["law_ok"])

    def test_nan_prediction_fails(self):
        ok, _ = pv.assess_velocity_delta(6.0, float("nan"))
        self.assertFalse(ok)

    def test_selftest_velocity_law_negative(self):
        ok, detail = pv.selftest_velocity_law_negative()
        self.assertTrue(ok, detail)

    def test_selftest_velocity_law_negative_uniform_scale(self):
        ok, detail = pv.selftest_velocity_law_negative_uniform_scale()
        self.assertTrue(ok, detail)

    def test_fundamental_band_counterexample_isolates_violation(self):
        # F3 domain fix (2026-07-22): a fundamental-only +3 dB-over-law
        # violation, measured through measure_band_rms_db() (the SAME path
        # judge_velocity() uses), must FAIL -- even though a strong,
        # perfectly-lawful overtone 400x its power would pull a naive
        # wideband RMS delta back toward the lawful 6.0206 dB.
        sr = 48000
        f0, f1 = 440.0, 880.0
        lo_amps = [0.05, 1.0]
        lawful = 2.0
        unlawful = 2.0 * 10.0 ** (3.0 / 20.0)   # +3 dB over the law

        lo = pv._synthetic_modal_signal(sr, 0.7, [f0, f1], lo_amps)
        hi_bad = pv._synthetic_modal_signal(
            sr, 0.7, [f0, f1], [lo_amps[0] * unlawful, lo_amps[1] * lawful])

        band_lo = pv.measure_band_rms_db(sr, lo, f0)
        band_hi = pv.measure_band_rms_db(sr, hi_bad, f0)
        fund_delta = band_hi - band_lo
        ok, detail = pv.assess_velocity_delta(fund_delta, pv.VELOCITY_LAW_DB)
        self.assertFalse(ok)
        self.assertFalse(detail["match_ok"])

        broadband_delta = (pv.measure_levels(sr, hi_bad)[1]
                            - pv.measure_levels(sr, lo)[1])
        # the wideband number is much closer to the lawful value than the
        # fundamental-band number is -- proof the domain choice matters.
        self.assertLess(abs(broadband_delta - pv.VELOCITY_LAW_DB),
                         abs(fund_delta - pv.VELOCITY_LAW_DB))

    def test_fundamental_band_lawful_pair_passes(self):
        sr = 48000
        f0, f1 = 440.0, 880.0
        lawful = 2.0
        lo = pv._synthetic_modal_signal(sr, 0.7, [f0, f1], [0.05, 1.0])
        hi = pv._synthetic_modal_signal(sr, 0.7, [f0, f1],
                                        [0.05 * lawful, 1.0 * lawful])
        band_lo = pv.measure_band_rms_db(sr, lo, f0)
        band_hi = pv.measure_band_rms_db(sr, hi, f0)
        fund_delta = band_hi - band_lo
        ok, detail = pv.assess_velocity_delta(fund_delta, pv.VELOCITY_LAW_DB)
        self.assertTrue(ok, detail)


class AmplitudeCounterexampleTests(unittest.TestCase):
    """Task 4a (2026-07-18): wrong-amplitude counterexample."""

    def test_selftest_amps_wrong_amplitude(self):
        ok, detail = pv.selftest_amps_wrong_amplitude()
        self.assertTrue(ok, detail)

    def test_plus_6db_partial_fails_through_shared_judgment(self):
        sr = 48000
        freqs = [440.0, 880.0, 1320.0]
        expected = [{"freq": f, "model_db": db, "required": True}
                    for f, db in zip(freqs, [0.0, -6.0, -12.0])]
        amps = [1.0, 10.0 ** (-6.0 / 20.0), 10.0 ** (-12.0 / 20.0)]
        honest = pv._synthetic_modal_signal(sr, 0.7, freqs, amps)
        ok_pos, _ = pv.assess_partial_amplitudes(
            expected, pv.measure_partials(sr, honest, freqs))
        self.assertTrue(ok_pos)
        wrong = list(amps)
        wrong[1] *= 10.0 ** (6.0 / 20.0)   # +6 dB > ±3 dB tolerance
        bad = pv._synthetic_modal_signal(sr, 0.7, freqs, wrong)
        ok_neg, rows = pv.assess_partial_amplitudes(
            expected, pv.measure_partials(sr, bad, freqs))
        self.assertFalse(ok_neg)
        p2 = next(r for r in rows if r["n"] == 2)
        self.assertEqual("FAIL", p2["verdict"])
        self.assertGreater(abs(p2["err_db"]), pv.AMPS_DB_TOL)


class ResidualEnergyTests(unittest.TestCase):
    """F5 (2026-07-18, judgment conversion 2026-07-23): unpredicted-energy
    measurement, now judged against RESIDUAL_ENERGY_LIMIT_DB (月月
    approval 2026-07-23)."""

    def test_clean_signal_has_low_residual(self):
        sr = 48000
        freqs = [440.0, 880.0]
        clean = pv._synthetic_modal_signal(sr, 2.0, freqs)
        rdb = pv.measure_residual_energy(sr, clean, freqs, 1.8)
        self.assertIsNotNone(rdb)
        self.assertLess(rdb, -40.0)

    def test_unpredicted_partial_dominates_residual(self):
        sr = 48000
        freqs = [440.0, 880.0]
        clean = pv._synthetic_modal_signal(sr, 2.0, freqs)
        dirty = clean + 0.5 * pv._synthetic_modal_signal(sr, 2.0, [1500.0])
        rdb = pv.measure_residual_energy(sr, dirty, freqs, 1.8)
        # 0.5^2/(1+1+0.25) of the energy sits outside every predicted band:
        # expect roughly -9.5 dB re total
        self.assertGreater(rdb, -12.0)
        self.assertLess(rdb, -6.0)

    def test_unusable_segment_returns_none(self):
        import numpy as np
        self.assertIsNone(pv.measure_residual_energy(
            48000, np.zeros(64), [440.0], 1.8))

    def test_limit_constant_value(self):
        # Approved 月月 2026-07-23; see the constant's comment in
        # tools/physics_verify.py for the baseline data and margin. This test
        # pins the value so a future edit can't silently widen it.
        self.assertEqual(-60.0, pv.RESIDUAL_ENERGY_LIMIT_DB)

    def test_judge_passes_clean_signal_below_limit(self):
        sr = 48000
        freqs = [440.0, 880.0, 1320.0]
        clean = pv._synthetic_modal_signal(sr, 2.0, freqs)
        rdb = pv.measure_residual_energy(sr, clean, freqs, 1.8)
        self.assertLessEqual(rdb, pv.RESIDUAL_ENERGY_LIMIT_DB)
        self.assertTrue(pv.judge_residual_energy(rdb))

    def test_judge_fails_unmodeled_strong_peak_above_limit(self):
        sr = 48000
        freqs = [440.0, 880.0, 1320.0]
        clean = pv._synthetic_modal_signal(sr, 2.0, freqs)
        # A peak well outside every predicted ±3% band, strong enough to
        # land the residual comfortably above the -60.0 dB ceiling.
        dirty = clean + pv._synthetic_modal_signal(sr, 2.0, [3000.0], [0.5])
        rdb = pv.measure_residual_energy(sr, dirty, freqs, 1.8)
        self.assertGreater(rdb, pv.RESIDUAL_ENERGY_LIMIT_DB)
        self.assertFalse(pv.judge_residual_energy(rdb))

    def test_judge_treats_unmeasurable_none_as_fail(self):
        # An honest "cannot measure" must not be silently accepted as clean.
        self.assertFalse(pv.judge_residual_energy(None))

    def test_selftest_residual_energy_negative(self):
        ok, detail = pv.selftest_residual_energy_negative()
        self.assertTrue(ok, detail)


if __name__ == "__main__":
    unittest.main()
