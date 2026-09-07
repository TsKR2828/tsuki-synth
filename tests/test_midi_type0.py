"""Regression tests for tools/midi_to_tsukisynth.py extract_notes() (F-06).

F-06: extract_notes() used to hard-skip track index 0
(`enumerate(midi.tracks[1:], start=1)`), assuming it was always a
conductor/meta track. Standard MIDI File Format 0 keeps every note in the
single track 0, so that assumption silently produced zero notes for
Format-0 files. This module proves:

  1. A Format-0 fixture (one track, containing both a track_name and real
     note_on/note_off pairs) now yields the notes -- this is exactly the
     `midi_type=0 / track_count=1 / extracted_note_count=0` reproduction
     from the audit, and fails against the pre-fix code (fixed skip of
     track index 0 means the loop body never runs for a 1-track file).
  2. A Format-1 fixture whose track 0 is meta-only (track_name + tempo,
     no note_on at all) and whose track 1 carries the notes still yields
     exactly the same notes as before the fix, and the track_name()
     fallback index for track 1+ is unchanged.

Style mirrors the rest of tests/: load the module by file path (no
package install needed), no conftest.py / shared fixtures (there are
none anywhere in this repo).
"""

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

import mido

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "midi_to_tsukisynth", ROOT / "tools" / "midi_to_tsukisynth.py"
)
mts = importlib.util.module_from_spec(SPEC)
# midi_to_tsukisynth.py declares module-level @dataclass classes; the
# dataclass machinery resolves forward-referenced annotation types via
# sys.modules[cls.__module__], so the module must be registered there
# before exec_module runs the class bodies (module_from_spec alone does
# not register it -- no other test file here loads this particular
# module, so this key is not shared).
sys.modules[SPEC.name] = mts
SPEC.loader.exec_module(mts)


def _notes_as_tuples(notes):
    """(note, start_tick, end_tick, source_velocity) -- deliberately not
    just a count, per the card's acceptance requirement to check onset,
    pitch, and note-on/note-off pairing."""
    return sorted(
        (n.note, n.start_tick, n.end_tick, n.source_velocity) for n in notes
    )


class ExtractNotesType0Test(unittest.TestCase):
    """Format 0: a single track holding track_name + tempo + notes."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write(self, midi_file, name):
        path = Path(self.tmpdir.name) / name
        midi_file.save(str(path))
        return path

    def test_type0_single_track_notes_are_extracted(self):
        midi_file = mido.MidiFile(type=0, ticks_per_beat=480)
        track = mido.MidiTrack()
        midi_file.tracks.append(track)
        track.append(mido.MetaMessage("track_name", name="up", time=0))
        track.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
        # channel 0: note 60 held for 240 ticks
        track.append(mido.Message("note_on", channel=0, note=60, velocity=80, time=0))
        # channel 1: note 60 (same pitch, different channel) held for 480
        # ticks -- interleaved on/off order deliberately exercises the
        # (channel, note) keyed pairing, not just note-number FIFO.
        track.append(mido.Message("note_on", channel=1, note=60, velocity=90, time=0))
        track.append(mido.Message("note_off", channel=1, note=60, velocity=0, time=120))
        track.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=120))
        track.append(mido.MetaMessage("end_of_track", time=0))
        path = self._write(midi_file, "type0.mid")

        loaded = mido.MidiFile(str(path))
        self.assertEqual(loaded.type, 0)
        self.assertEqual(len(loaded.tracks), 1)

        notes = mts.extract_notes(loaded, {"up", "down"})

        # Pre-fix code (enumerate(midi.tracks[1:], start=1)) iterates zero
        # tracks for a 1-track file and returns [] here -- this assertion
        # is the F-06 reproduction (midi_type=0 / extracted_note_count=0)
        # and fails on the unfixed code.
        self.assertEqual(len(notes), 2)

        # channel-aware pairing: channel 1's note-on (vel 90) must pair
        # with channel 1's note-off at abs tick 120, and channel 0's
        # note-on (vel 80) must pair with channel 0's note-off at abs
        # tick 240 -- a channel-blind FIFO-by-note-number would instead
        # produce (60, 0, 120, 80) / (60, 0, 240, 90).
        self.assertEqual(
            _notes_as_tuples(notes),
            [(60, 0, 120, 90), (60, 0, 240, 80)],
        )
        self.assertTrue(all(n.track == "up" for n in notes))

    def test_type0_track_name_not_in_valid_tracks_yields_no_notes(self):
        # extract_notes() keeps a STRICT name gate by default
        # (single_track_fallback=None): a Format-0 file whose sole track's
        # name isn't in valid_tracks still yields zero notes. The opt-in
        # fallback that admits it is exercised in
        # ExtractNotesSingleTrackFallbackTest below; this test pins the
        # strict default so callers that never pass the parameter (e.g.
        # the four-seasons path) cannot silently change behaviour.
        midi_file = mido.MidiFile(type=0, ticks_per_beat=480)
        track = mido.MidiTrack()
        midi_file.tracks.append(track)
        track.append(mido.MetaMessage("track_name", name="unrelated", time=0))
        track.append(mido.Message("note_on", channel=0, note=60, velocity=80, time=0))
        track.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=240))
        path = self._write(midi_file, "type0_unmatched_name.mid")

        loaded = mido.MidiFile(str(path))
        notes = mts.extract_notes(loaded, {"up", "down"})
        self.assertEqual(notes, [])


class ExtractNotesType1CompatibilityTest(unittest.TestCase):
    """Format 1: track 0 is meta-only, track 1+ carries the notes --
    result must be byte-for-byte (note-for-note) identical to the
    pre-fix behaviour."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write(self, midi_file, name):
        path = Path(self.tmpdir.name) / name
        midi_file.save(str(path))
        return path

    def test_meta_only_track0_is_still_skipped_and_track1_unaffected(self):
        midi_file = mido.MidiFile(type=1, ticks_per_beat=480)

        conductor = mido.MidiTrack()
        conductor.append(mido.MetaMessage("track_name", name="control track", time=0))
        conductor.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
        conductor.append(mido.MetaMessage("end_of_track", time=0))
        midi_file.tracks.append(conductor)

        melody = mido.MidiTrack()
        melody.append(mido.MetaMessage("track_name", name="up", time=0))
        melody.append(mido.Message("note_on", channel=0, note=64, velocity=70, time=0))
        melody.append(mido.Message("note_off", channel=0, note=64, velocity=0, time=240))
        melody.append(mido.Message("note_on", channel=0, note=67, velocity=75, time=0))
        melody.append(mido.Message("note_off", channel=0, note=67, velocity=0, time=240))
        melody.append(mido.MetaMessage("end_of_track", time=0))
        midi_file.tracks.append(melody)

        accompaniment = mido.MidiTrack()
        accompaniment.append(mido.MetaMessage("track_name", name="down", time=0))
        accompaniment.append(mido.Message("note_on", channel=0, note=48, velocity=50, time=0))
        accompaniment.append(mido.Message("note_off", channel=0, note=48, velocity=0, time=480))
        accompaniment.append(mido.MetaMessage("end_of_track", time=0))
        midi_file.tracks.append(accompaniment)

        path = self._write(midi_file, "type1.mid")
        loaded = mido.MidiFile(str(path))
        self.assertEqual(loaded.type, 1)
        self.assertEqual(len(loaded.tracks), 3)

        notes = mts.extract_notes(loaded, {"up", "down"})

        # conductor track (index 0, meta-only, no note_on) must not
        # contribute anything and must not appear via a stray fallback
        # name, exactly as the old fixed skip-index-0 behaviour ensured.
        self.assertEqual(
            _notes_as_tuples([n for n in notes if n.track == "up"]),
            [(64, 0, 240, 70), (67, 240, 480, 75)],
        )
        self.assertEqual(
            _notes_as_tuples([n for n in notes if n.track == "down"]),
            [(48, 0, 480, 50)],
        )
        self.assertEqual(len(notes), 3)

    def test_track_name_fallback_index_unshifted_for_track1_plus(self):
        # track_name()'s f"track_{index}" fallback for track 1+ must stay
        # exactly what it was under enumerate(midi.tracks[1:], start=1):
        # the melody track here has NO track_name meta at all, so it must
        # fall back to "track_1" (not "track_2"), matching pre-fix index
        # numbering.
        midi_file = mido.MidiFile(type=1, ticks_per_beat=480)

        conductor = mido.MidiTrack()
        conductor.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
        conductor.append(mido.MetaMessage("end_of_track", time=0))
        midi_file.tracks.append(conductor)

        unnamed_melody = mido.MidiTrack()
        unnamed_melody.append(mido.Message("note_on", channel=0, note=60, velocity=64, time=0))
        unnamed_melody.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=240))
        unnamed_melody.append(mido.MetaMessage("end_of_track", time=0))
        midi_file.tracks.append(unnamed_melody)

        path = self._write(midi_file, "type1_unnamed.mid")
        loaded = mido.MidiFile(str(path))

        notes = mts.extract_notes(loaded, {"track_1"})
        self.assertEqual(_notes_as_tuples(notes), [(60, 0, 240, 64)])
        self.assertEqual({n.track for n in notes}, {"track_1"})


if __name__ == "__main__":
    unittest.main()


class ExtractNotesSingleTrackFallbackTest(unittest.TestCase):
    """F-06 second half: the NAME gate. Dropping the index gate alone still
    left an ordinary single-track MIDI (no track_name, or any name that is
    not `up`/`down`) yielding zero notes. `single_track_fallback` admits
    exactly one note-bearing track under a caller-chosen profile name, and
    only when nothing else matched."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write(self, midi_file, name):
        path = Path(self.tmpdir.name) / name
        midi_file.save(str(path))
        return path

    def _type0(self, name, track_title=None):
        midi_file = mido.MidiFile(type=0, ticks_per_beat=480)
        track = mido.MidiTrack()
        midi_file.tracks.append(track)
        if track_title is not None:
            track.append(mido.MetaMessage("track_name", name=track_title, time=0))
        track.append(mido.Message("note_on", channel=0, note=60, velocity=80, time=0))
        track.append(mido.Message("note_off", channel=0, note=60, velocity=0, time=240))
        track.append(mido.Message("note_on", channel=0, note=48, velocity=70, time=0))
        track.append(mido.Message("note_off", channel=0, note=48, velocity=0, time=240))
        track.append(mido.MetaMessage("end_of_track", time=0))
        return mido.MidiFile(str(self._write(midi_file, name)))

    def test_type0_with_no_track_name_at_all_is_admitted(self):
        """The audit's real complaint: a plain Format-0 export carries no
        track_name meta at all, so track_name() returns the `track_0`
        fallback and the name gate dropped the whole file."""
        loaded = self._type0("type0_nameless.mid", track_title=None)

        strict = mts.extract_notes(loaded, {"up", "down"})
        self.assertEqual(strict, [], "strict default must still reject it")

        admitted = mts.extract_notes(loaded, {"up", "down"},
                                     single_track_fallback="up")
        self.assertEqual(len(admitted), 2)
        self.assertEqual(_notes_as_tuples(admitted),
                         [(48, 240, 480, 70), (60, 0, 240, 80)])
        self.assertTrue(all(n.track == "up" for n in admitted))

    def test_type0_with_unmatched_name_is_admitted(self):
        loaded = self._type0("type0_piano.mid", track_title="Piano")
        admitted = mts.extract_notes(loaded, {"up", "down"},
                                     single_track_fallback="down")
        self.assertEqual(len(admitted), 2)
        self.assertTrue(all(n.track == "down" for n in admitted),
                        "the caller's chosen profile name must be applied")

    def test_matching_name_wins_over_the_fallback(self):
        loaded = self._type0("type0_named_up.mid", track_title="up")
        admitted = mts.extract_notes(loaded, {"up", "down"},
                                     single_track_fallback="down")
        self.assertTrue(all(n.track == "up" for n in admitted),
                        "a real name match must not be overridden")

    def test_fallback_never_fires_for_multi_track_files(self):
        """Two note-bearing tracks with unmatched names stay rejected: the
        fallback must not guess which one to keep."""
        midi_file = mido.MidiFile(type=1, ticks_per_beat=480)
        meta = mido.MidiTrack()
        midi_file.tracks.append(meta)
        meta.append(mido.MetaMessage("track_name", name="control track", time=0))
        for title in ("Piano RH", "Piano LH"):
            track = mido.MidiTrack()
            midi_file.tracks.append(track)
            track.append(mido.MetaMessage("track_name", name=title, time=0))
            track.append(mido.Message("note_on", channel=0, note=60,
                                      velocity=80, time=0))
            track.append(mido.Message("note_off", channel=0, note=60,
                                      velocity=0, time=240))
        loaded = mido.MidiFile(str(self._write(midi_file,
                                               "type1_two_unmatched.mid")))

        self.assertEqual(
            mts.extract_notes(loaded, {"up", "down"}, single_track_fallback="up"),
            [])

    def test_meta_only_tracks_do_not_count_toward_the_single_track_rule(self):
        """A Format-1 file with one meta track + one unmatched music track is
        still 'a single note-bearing track' and must be admitted."""
        midi_file = mido.MidiFile(type=1, ticks_per_beat=480)
        meta = mido.MidiTrack()
        midi_file.tracks.append(meta)
        meta.append(mido.MetaMessage("track_name", name="control track", time=0))
        meta.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
        music = mido.MidiTrack()
        midi_file.tracks.append(music)
        music.append(mido.MetaMessage("track_name", name="Grand Piano", time=0))
        music.append(mido.Message("note_on", channel=0, note=64,
                                  velocity=75, time=0))
        music.append(mido.Message("note_off", channel=0, note=64,
                                  velocity=0, time=240))
        loaded = mido.MidiFile(str(self._write(midi_file,
                                               "type1_one_music.mid")))

        admitted = mts.extract_notes(loaded, {"up", "down"},
                                     single_track_fallback="up")
        self.assertEqual(len(admitted), 1)
        self.assertEqual(admitted[0].track, "up")

    def test_fallback_is_announced_on_stderr(self):
        """A one-track piano MIDI usually holds BOTH hands, so the whole piece
        inheriting one profile's role and base velocity must never be
        silent."""
        loaded = self._type0("type0_warn.mid", track_title=None)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            mts.extract_notes(loaded, {"up", "down"}, single_track_fallback="up")
        message = stderr.getvalue()
        self.assertIn("[WARN]", message)
        self.assertIn("both hands", message)

    def test_generic_document_admits_a_single_track_midi_end_to_end(self):
        path = Path(self.tmpdir.name) / "type0_doc.mid"
        self._type0("type0_doc.mid", track_title=None)

        score = mts.generic_piano_score_document(
            path, score_id="type0_fallback_probe", title="Type 0 probe")

        self.assertEqual(len(score["events"]), 2)
        self.assertTrue(
            all(e["performance"]["role"] == "right_hand"
                for e in score["events"]),
            "default single_track_profile is 'up' (right hand)")

    def test_generic_document_can_keep_the_strict_gate(self):
        path = Path(self.tmpdir.name) / "type0_strict.mid"
        self._type0("type0_strict.mid", track_title=None)

        with self.assertRaises(ValueError) as caught:
            mts.generic_piano_score_document(
                path, score_id="type0_strict_probe", title="Type 0 strict",
                single_track_profile=None)
        self.assertIn("no notes extracted", str(caught.exception))

    def test_generic_document_rejects_a_profile_name_not_in_the_set(self):
        path = Path(self.tmpdir.name) / "type0_badprofile.mid"
        self._type0("type0_badprofile.mid", track_title=None)

        with self.assertRaises(ValueError) as caught:
            mts.generic_piano_score_document(
                path, score_id="type0_bad_probe", title="Type 0 bad",
                single_track_profile="middle_hand")
        self.assertIn("not in profile set", str(caught.exception))
