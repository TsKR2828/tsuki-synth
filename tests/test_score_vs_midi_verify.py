"""Regression tests for tools/score_vs_midi_verify.py.

Style mirrors tests/test_verify_score_contract.py: load the module by file
path (no package install needed), exercise the pure logic directly with
small synthetic fixtures, and separately prove the real Fur Elise fixture
still verifies clean end-to-end.
"""

import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "score_vs_midi_verify", ROOT / "tools" / "score_vs_midi_verify.py")
svm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(svm)


# ---------------------------------------------------------------------------
# helpers to synthesise a minimal Standard MIDI File byte-for-byte, so the
# SMF-parser tests do not depend on any external fixture file.
# ---------------------------------------------------------------------------

def _vlq(value):
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(out)


def _track_chunk(events_bytes):
    return b"MTrk" + struct.pack(">I", len(events_bytes)) + events_bytes


def _note_on(delta, channel, note, vel):
    return _vlq(delta) + bytes([0x90 | channel, note, vel])


def _note_off(delta, channel, note, vel=0):
    return _vlq(delta) + bytes([0x80 | channel, note, vel])


def _track_name_meta(delta, name):
    b = name.encode("ascii")
    return _vlq(delta) + bytes([0xFF, 0x03, len(b)]) + b


def _tempo_meta(delta, us_per_quarter):
    t = us_per_quarter
    return (_vlq(delta) + bytes([0xFF, 0x51, 0x03])
            + bytes([(t >> 16) & 0xFF, (t >> 8) & 0xFF, t & 0xFF]))


def _end_of_track(delta=0):
    return _vlq(delta) + bytes([0xFF, 0x2F, 0x00])


def build_smf(tracks_events, ticks_per_quarter=480, fmt=1):
    header = (b"MThd" + struct.pack(">I", 6)
              + struct.pack(">HHH", fmt, len(tracks_events), ticks_per_quarter))
    out = header
    for events in tracks_events:
        out += _track_chunk(events)
    return out


def write_smf(path, tracks_events, ticks_per_quarter=480, fmt=1):
    Path(path).write_bytes(build_smf(tracks_events, ticks_per_quarter, fmt))


class SMFParserTests(unittest.TestCase):
    """Exercises the independent binary parser directly (no mido)."""

    def test_parses_simple_two_note_track(self):
        with tempfile.TemporaryDirectory(prefix="smf_test_") as d:
            p = Path(d) / "x.mid"
            control = _tempo_meta(0, 500_000) + _end_of_track()
            melody = (_track_name_meta(0, "up")
                      + _note_on(0, 0, 60, 90)
                      + _note_off(480, 0, 60)
                      + _note_on(0, 0, 62, 90)
                      + _note_off(480, 0, 62)
                      + _end_of_track())
            write_smf(p, [control, melody], ticks_per_quarter=480)
            tpq, tracks = svm.parse_smf(p)
            self.assertEqual(480, tpq)
            self.assertEqual(2, len(tracks))
            name, events = tracks[1]
            self.assertEqual("up", name)
            kinds = [e.kind for e in events if e.kind in ("note_on", "note_off")]
            self.assertEqual(["note_on", "note_off", "note_on", "note_off"], kinds)

    def test_running_status_is_decoded(self):
        # Two note-ons back to back sharing one status byte (running status).
        with tempfile.TemporaryDirectory(prefix="smf_test_") as d:
            p = Path(d) / "x.mid"
            track = (_note_on(0, 0, 60, 90)
                     + _vlq(10) + bytes([61, 90])   # running status note_on
                     + _note_off(10, 0, 60)
                     + _vlq(10) + bytes([61, 0])    # running status note_off (vel 0)
                     + _end_of_track())
            write_smf(p, [track], ticks_per_quarter=480)
            _tpq, tracks = svm.parse_smf(p)
            _name, events = tracks[0]
            ons = [e for e in events if e.kind == "note_on"]
            offs = [e for e in events if e.kind == "note_off"]
            self.assertEqual({60, 61}, {e.note for e in ons})
            self.assertEqual(2, len(offs))

    def test_velocity_zero_note_on_counts_as_note_off(self):
        with tempfile.TemporaryDirectory(prefix="smf_test_") as d:
            p = Path(d) / "x.mid"
            track = _note_on(0, 0, 64, 100) + _note_on(240, 0, 64, 0) + _end_of_track()
            write_smf(p, [track])
            _tpq, tracks = svm.parse_smf(p)
            notes, dangling = svm.extract_source_notes(tracks)
            self.assertEqual([], dangling)
            self.assertEqual(1, len(notes))
            self.assertEqual(240, notes[0].end_tick - notes[0].start_tick)

    def test_smpte_division_is_refused_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="smf_test_") as d:
            p = Path(d) / "x.mid"
            header = (b"MThd" + struct.pack(">I", 6)
                      + struct.pack(">Hhb", 1, 1, -25) + bytes([40]))
            # division high bit set (SMPTE) -- construct manually since
            # struct.pack(">H", ...) can't express negative frame rates.
            division = 0x8000 | ((256 - 25) << 8) | 40
            header = (b"MThd" + struct.pack(">I", 6)
                      + struct.pack(">HHH", 1, 1, division))
            p.write_bytes(header + _track_chunk(_end_of_track()))
            with self.assertRaises(svm.SMFError):
                svm.parse_smf(p)

    def test_dangling_note_on_is_reported_not_dropped(self):
        with tempfile.TemporaryDirectory(prefix="smf_test_") as d:
            p = Path(d) / "x.mid"
            track = _note_on(0, 0, 67, 90) + _end_of_track()
            write_smf(p, [track])
            _tpq, tracks = svm.parse_smf(p)
            notes, dangling = svm.extract_source_notes(tracks)
            self.assertEqual([], notes)
            self.assertEqual(1, len(dangling))
            self.assertEqual(67, dangling[0]["note"])

    def test_bad_chunk_id_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="smf_test_") as d:
            p = Path(d) / "x.mid"
            p.write_bytes(b"NOPE" + struct.pack(">I", 6) + b"\x00" * 6)
            with self.assertRaises(svm.SMFError):
                svm.parse_smf(p)


class TempoMapTests(unittest.TestCase):
    def test_single_tempo_matches_hand_computation(self):
        # 480 ticks/quarter, 500000 us/quarter (120 BPM): 480 ticks = 0.5 s.
        tm = svm.TempoMap(480, [(None, [])])
        self.assertAlmostEqual(0.5, tm.seconds(480), places=9)
        self.assertAlmostEqual(1.0, tm.seconds(960), places=9)

    def test_tempo_change_mid_file_is_honoured(self):
        # Tempo doubles (BPM halves) at tick 480: first 480 ticks at
        # 500000 us/q (0.5s), next 480 ticks at 1000000 us/q (1.0s).
        events = [svm.SMFEvent(480, "tempo", data=1_000_000)]
        tm = svm.TempoMap(480, [(None, events)])
        self.assertAlmostEqual(0.5, tm.seconds(480), places=9)
        self.assertAlmostEqual(1.5, tm.seconds(960), places=9)

    def test_tempo_found_on_any_track_not_just_track_zero(self):
        events_on_track2 = [svm.SMFEvent(0, "tempo", data=1_000_000)]
        tm = svm.TempoMap(480, [(None, []), (None, events_on_track2)])
        self.assertAlmostEqual(1.0, tm.seconds(480), places=9)


class NoteNameToMidiTests(unittest.TestCase):
    def test_middle_c(self):
        self.assertEqual(60, svm.note_name_to_midi("C4"))

    def test_sharp_and_flat(self):
        self.assertEqual(61, svm.note_name_to_midi("C#4"))
        self.assertEqual(61, svm.note_name_to_midi("Db4"))

    def test_negative_octave(self):
        self.assertEqual(0, svm.note_name_to_midi("C-1"))

    def test_bare_integer_string(self):
        self.assertEqual(76, svm.note_name_to_midi("76"))

    def test_unparseable_returns_none(self):
        self.assertIsNone(svm.note_name_to_midi("not-a-note"))
        self.assertIsNone(svm.note_name_to_midi(None))
        self.assertIsNone(svm.note_name_to_midi(""))

    def test_out_of_range_midi_returns_none(self):
        self.assertIsNone(svm.note_name_to_midi("C11"))  # -> MIDI 132


class MatchBidirectionalTests(unittest.TestCase):
    """Exercises the 1:1 bucket-matching logic directly with synthetic
    notes/events, independent of any real MIDI or score file."""

    def _src(self, track, note, start_tick, end_tick):
        n = svm.SourceNote(track, 0, note, start_tick, end_tick)
        n.start_sec = start_tick / 1000.0
        n.end_sec = end_tick / 1000.0
        return n

    def _ev(self, track, note_name, time, release):
        return {"time": time, "note": note_name,
                "performance": {"track": track, "intended_release_time": release}}

    def test_clean_1to1_match(self):
        src = [self._src("up", 60, 0, 480), self._src("up", 62, 480, 960)]
        events = [self._ev("up", "C4", 0.0, 0.44), self._ev("up", "D4", 0.48, 0.9)]
        matched, missing, extra, unparseable = svm.match_bidirectional(src, events)
        self.assertEqual(2, len(matched))
        self.assertEqual([], missing)
        self.assertEqual([], extra)
        self.assertEqual([], unparseable)

    def test_chord_same_instant_different_pitches_all_matched(self):
        # Three simultaneous notes (a chord) -- must not be confused with
        # each other despite identical onset tick.
        src = [self._src("up", 60, 0, 480), self._src("up", 64, 0, 480),
               self._src("up", 67, 0, 480)]
        events = [self._ev("up", "C4", 0.0, 0.4), self._ev("up", "E4", 0.0, 0.4),
                  self._ev("up", "G4", 0.0, 0.4)]
        matched, missing, extra, unparseable = svm.match_bidirectional(src, events)
        self.assertEqual(3, len(matched))
        self.assertEqual([], missing)
        self.assertEqual([], extra)

    def test_missing_note_is_reported(self):
        src = [self._src("up", 60, 0, 480), self._src("up", 62, 480, 960)]
        events = [self._ev("up", "C4", 0.0, 0.44)]  # D4 missing
        matched, missing, extra, unparseable = svm.match_bidirectional(src, events)
        self.assertEqual(1, len(matched))
        self.assertEqual(1, len(missing))
        self.assertEqual(62, missing[0].note)
        self.assertEqual([], extra)

    def test_extra_note_is_reported(self):
        src = [self._src("up", 60, 0, 480)]
        events = [self._ev("up", "C4", 0.0, 0.44), self._ev("up", "D4", 0.48, 0.9)]
        matched, missing, extra, unparseable = svm.match_bidirectional(src, events)
        self.assertEqual(1, len(matched))
        self.assertEqual([], missing)
        self.assertEqual(1, len(extra))

    def test_unparseable_note_name_is_isolated_not_crashing(self):
        src = [self._src("up", 60, 0, 480)]
        events = [self._ev("up", "???", 0.0, 0.44)]
        matched, missing, extra, unparseable = svm.match_bidirectional(src, events)
        self.assertEqual(0, len(matched))
        self.assertEqual(1, len(unparseable))
        self.assertEqual(1, len(missing))  # the source note has nobody to match


class EndToEndFurEliseTests(unittest.TestCase):
    """Real-fixture proof: both shipped Fur Elise score variants verify
    clean against the actual Mutopia source MIDI (905 notes each)."""

    MIDI = ROOT / "scores" / "classical" / "fur_elise" / "source" / "fur_Elise_WoO59.mid"

    def _assert_clean(self, score_path):
        if not self.MIDI.is_file() or not score_path.is_file():
            self.skipTest(f"fixture not present: {self.MIDI} / {score_path}")
        report = svm.verify(self.MIDI, score_path, quiet=True)
        failing = [c for c in report["checks"] if not c["ok"]]
        self.assertEqual([], failing, msg=[c["message"] for c in failing])
        self.assertEqual(905, report["summary"]["score_events"])
        self.assertEqual(905, report["summary"]["source_notes"])
        self.assertEqual(905, report["summary"]["matched"])

    def test_piano_variant_verifies_clean(self):
        self._assert_clean(ROOT / "scores" / "classical" / "fur_elise"
                            / "fur_elise_complete.score.json")

    def test_cimbalom_variant_verifies_clean(self):
        self._assert_clean(ROOT / "scores" / "classical" / "fur_elise"
                            / "fur_elise_complete_cimbalom.score.json")


class SelftestSentinelTests(unittest.TestCase):
    """Runs the module's own --selftest mutation suite as a pytest case too
    (in addition to it being runnable standalone), so a regression here is
    caught by the normal test run, not only by manually invoking --selftest."""

    def test_selftest_suite_passes(self):
        if not svm.GOOD_MIDI.is_file() or not svm.GOOD_SCORE.is_file():
            self.skipTest(f"fixture not present: {svm.GOOD_MIDI} / {svm.GOOD_SCORE}")
        self.assertEqual(0, svm.selftest())


if __name__ == "__main__":
    unittest.main()
