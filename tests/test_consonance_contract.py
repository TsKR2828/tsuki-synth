"""Regression tests for the event-specific consonance checker contract."""

import importlib.util
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_piece_consonance", ROOT / "tools" / "check_piece_consonance.py")
cc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cc)


class ConsonanceContractTests(unittest.TestCase):
    def test_note_parser_covers_tuner_range_and_rejects_invalid_values(self):
        cases = {
            "A0": 21,
            "C8": 108,
            "Cb4": 59,
            "B#3": 60,
            "60": 60,
            60: 60,
        }
        for note, expected in cases.items():
            with self.subTest(note=note):
                self.assertEqual(expected, cc.note_to_midi(note))
        for note in (True, -1, 128, "60.0", "H4", "C#", ""):
            with self.subTest(note=note):
                self.assertIsNone(cc.note_to_midi(note))

    def test_dump_spectrum_uses_every_string_body_gain_and_weak_floor(self):
        event = {
            "strings": [
                [
                    {"freq": 99.0, "amp": 2.0, "body_mag": 0.5},
                    {"freq": 198.0, "amp": 1.0, "body_mag": 1.0},
                ],
                [
                    {"freq": 101.0, "amp": 1.0, "body_mag": 1.0},
                    {"freq": 202.0, "amp": 0.0005, "body_mag": 1.0},
                ],
            ]
        }
        f0, spectrum = cc.spectrum_from_dump(event, velocity=0.4)
        self.assertAlmostEqual(math.sqrt(99.0 * 101.0), f0, places=12)
        self.assertEqual(3, len(spectrum))
        self.assertTrue(any(math.isclose(ratio, 99.0 / f0) for ratio, _ in spectrum))
        self.assertTrue(any(math.isclose(ratio, 101.0 / f0) for ratio, _ in spectrum))
        self.assertTrue(any(math.isclose(ratio, 198.0 / f0) for ratio, _ in spectrum))
        self.assertTrue(all(math.isclose(amp, 0.4) for _, amp in spectrum))

    def test_overlap_is_half_open(self):
        events = [
            {"time": 0.0, "duration": 1.0},
            {"time": 1.0, "duration": 1.0},
            {"time": 0.5, "duration": 0.25},
        ]
        pairs = cc.overlapping_pairs(events)
        self.assertEqual([(events[0], events[2])], pairs)

    def test_nearest_minimum_wraps_at_the_octave_boundary(self):
        nearest, distance = cc.nearest_min_distance(1198.0, [0.0, 700.0])
        self.assertEqual(0.0, nearest)
        self.assertEqual(2.0, distance)

    def test_outside_domain_pair_is_not_reported_as_pass(self):
        events = [
            {"idx": 0, "engine": "fm", "label": "fm", "time": 0.0,
             "duration": 1.0, "midi": 60, "role": "pad", "f0": 261.625565,
             "spectrum": [], "domain": "outside"},
            {"idx": 1, "engine": "piano", "label": "piano", "time": 0.0,
             "duration": 1.0, "midi": 67, "role": "tone", "f0": 391.995436,
             "spectrum": [(1.0, 1.0), (2.0, 0.5)], "domain": "physical-modal"},
        ]
        original = cc.load_events
        cc.load_events = lambda _score, _cli: events
        try:
            result = cc.check(Path("unused.score.json"), Path("unused-cli"))
        finally:
            cc.load_events = original
        self.assertEqual(1, len(result))
        self.assertEqual("UNVERIFIED-DOMAIN", result[0]["verdict"])

    def test_default_report_name_is_score_specific(self):
        path = cc.default_report_path(Path("pieces/my_piece.score.json"))
        self.assertEqual("my_piece_consonance_check.md", path.name)


if __name__ == "__main__":
    unittest.main()
