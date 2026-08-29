#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score_vs_midi_verify.py -- full-corpus MIDI<->score.json transcription GATE.

WHY (月月 2026-08-28): the render-audio gates in this repo (verify_score.py,
melody_verify.py, physics_verify.py) all judge the RENDERED WAV against the
score.json's own declarations. None of them ever look at the ORIGINAL SOURCE
MIDI a classical transcription was built from -- so a transcription bug
(wrong pitch, shifted onset, a dropped or duplicated note) that the
converter (tools/midi_to_tsukisynth.py) faithfully carries all the way
through to a physically-correct render would pass every existing gate while
being musically wrong. Until now that layer only had spot-checks (a handful
of notes eyeballed against the .ly / MIDI by a human or a one-off chat
session). This tool makes the whole-file MIDI<->score comparison a real,
scriptable, fail-closed GATE with a mutation-tested sentinel, closing that
verification-chain gap.

Independence (why this file does NOT import mido or tools/midi_to_tsukisynth.py):
    The transcriber (tools/midi_to_tsukisynth.py) uses `mido` to read the
    source MIDI. If this verifier also used mido, a bug in mido's own SMF
    parsing (or a shared misunderstanding of running status / tempo-map
    semantics between the transcriber author and mido) could make both
    sides "agree" on a wrong reading of the source file -- a common-mode
    failure that a verifier exists specifically to catch. This file
    therefore implements its own Standard MIDI File parser from the raw
    byte format (chunk headers, VLQ delta-times, running status, meta and
    channel events) using nothing but the Python standard library. It is
    the MIDI file's bytes -- not the transcriber's opinion of them -- that
    are treated as ground truth (per the task brief: "MIDI 為唯一真理源").

What is judged (fail-closed; UNVERIFIED/refused conditions are printed, not
silently passed) -- see verify() for the implementation of each:
  1. midi.parse             -- the file is a well-formed SMF this parser can
                                read (fails closed on SMPTE-division files or
                                unrecognised status bytes rather than guess).
  2. midi.note_pairing      -- every note-on paired with a note-off within
                                its own (track, channel, pitch) FIFO queue,
                                per MIDI 1.0 semantics (a note_on with
                                velocity 0 counts as a note-off). Any
                                dangling note-on is reported, not dropped.
  3. counts.total_events    -- len(score["events"]) == total paired notes
                                across every note-bearing MIDI track (not
                                just the tracks the converter happened to
                                read) -- catches a whole track silently
                                dropped or duplicated.
  4. match.bidirectional    -- source notes and score events are grouped
                                into buckets keyed by (track name, pitch)
                                and paired 1:1 in onset order within each
                                bucket (see match_bidirectional()). Any
                                bucket with a leftover source note (missing
                                from the score) or leftover score event (not
                                in the source) is reported by name/pitch/
                                time, not just as an aggregate count.
  5. Per matched pair:
       pitch     -- the pitch actually RENDERED by the score (decoded from
                    event["note"] the same way ScoreParser::noteNameToMidi
                    does -- see note_name_to_midi() -- NOT merely the
                    performance.midi_note provenance field, so a bug where
                    that field is right but the rendered note name is wrong
                    cannot slip through) must equal the source MIDI note
                    number EXACTLY (zero tolerance, per the task brief:
                    "轉譜層零容差"). performance.midi_note is separately
                    cross-checked against the same decoded pitch as a
                    self-consistency check (data-quality, not a MIDI
                    comparison).
       onset     -- event["time"] (seconds) vs the source note's start tick
                    converted through this file's own independently-built
                    tempo map, judged at ONSET_TOL_S (see its docstring for
                    the float-precision provenance of that number).
       duration  -- the score's actual sounding window
                    [time, performance.intended_release_time] must not
                    exceed the source MIDI note's sounding window
                    [start, end] by more than DURATION_EPS_S (float
                    round-trip slack only -- see its docstring; a
                    transcription is explicitly ALLOWED to shorten a note
                    for articulation, never to lengthen it past the source).
  6. duration.whole_piece   -- the overall span (last sounding instant
                                across every score event) must not extend
                                past the source MIDI's last note-off by more
                                than DURATION_EPS_S -- same one-sided "never
                                longer than source" semantics as the
                                per-pair duration check (5), applied globally
                                as a sanity net (a piece ending noticeably
                                SHORT of the source is already caught
                                per-note by counts/match above, since a
                                dropped tail note fails those checks
                                directly; ending LONG never has an innocent
                                explanation).

Deliberately NOT judged (interpretive fields; listed in the report, never
failed on): event["velocity"] (TsukiSynth performance-dynamics
interpretation, not sourced from the MIDI at all in this converter, see
midi_to_tsukisynth.PIANO_HAND_PROFILES's comment on the source having a flat
MIDI velocity 62 for every note), event["engine"] (an instrument-choice
variant -- piano vs cimbalom render the SAME notes), performance.articulation
/ articulation_gap_ms / phrase_end / breath_after_ms / comment (all derived
performance-interpretation data, not source facts).

Usage:
    python tools/score_vs_midi_verify.py <midi> <score.json> [--json OUT]
    python tools/score_vs_midi_verify.py --selftest [--json OUT]
Exit codes: 0 = PASS (no FAIL among the checks), 1 = FAIL, 2 = usage/parse
error (BLOCKED -- could not even attempt the comparison).
"""

import argparse
import copy
import json
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# -- tolerances (all documented; R2/R4 -- never widen these to make a run
#    pass) --------------------------------------------------------------
ONSET_TOL_S = 0.001
# 1 ms, per the task brief ("onset 換算絕對秒後誤差 <= 1ms", i.e. "does the
# tempo map conversion land in the right place"). Both this verifier and the
# transcriber compute seconds = ticks * (tempo_us / 1e6) / ticks_per_beat
# using IEEE-754 double arithmetic; the only source of disagreement between
# two independent implementations of that one multiplication/division is
# double rounding noise (~1e-12 s) plus the score.json round-trip through
# midi_to_tsukisynth.round_float()'s 6-decimal rounding (<= 5e-7 s). 1 ms is
# therefore ~1900x looser than the actual noise floor -- it exists to give
# an honest, auditable margin, not because larger disagreement is expected
# or tolerated; any real onset bug (wrong tempo map, wrong tick arithmetic,
# a shifted note) produces errors of tens of milliseconds or more (see the
# --selftest 20 ms time-shift sentinel below), nowhere near this boundary.
DURATION_EPS_S = 0.0002
# 0.2 ms: NOT a relaxation of "duration must not exceed source" -- it is
# the float round-trip slack for a one-sided inequality check. The score's
# performance.intended_release_time has been through
# midi_to_tsukisynth.round_float() (6-decimal rounding, <= 5e-7 s per
# value) and is the difference of two already-rounded numbers (time and
# intended_release_time), so the representable error on the SOUNDING
# WINDOW LENGTH itself is bounded by ~1e-6 s, not the tolerance's 2e-4 s;
# the extra margin exists purely so an honest zero-slack transcription
# never fails on ULP noise, while a real "note rings past its source"
# defect (which this repo's articulation gaps deliberately measure in
# tens of milliseconds, see midi_to_tsukisynth.articulation_gap_seconds)
# is orders of magnitude larger than this margin.


# =========================================================================
# 1. Independent Standard MIDI File parser (no mido -- see module docstring
#    "Independence" section for why).
# =========================================================================

class SMFError(RuntimeError):
    pass


class SMFEvent:
    __slots__ = ("abs_tick", "kind", "channel", "note", "velocity", "meta_type", "data")

    def __init__(self, abs_tick, kind, channel=None, note=None, velocity=None,
                 meta_type=None, data=None):
        self.abs_tick = abs_tick
        self.kind = kind
        self.channel = channel
        self.note = note
        self.velocity = velocity
        self.meta_type = meta_type
        self.data = data


def _read_vlq(buf, pos):
    """MIDI variable-length quantity: 7 data bits per byte, MSB = continue."""
    value = 0
    while True:
        if pos >= len(buf):
            raise SMFError("truncated file: variable-length quantity runs "
                            "past the end of the track chunk")
        b = buf[pos]
        pos += 1
        value = (value << 7) | (b & 0x7F)
        if not (b & 0x80):
            return value, pos


def _read_chunk(data, pos):
    if pos + 8 > len(data):
        raise SMFError(f"truncated file: no room for a chunk header at byte {pos}")
    ctype = bytes(data[pos:pos + 4])
    length = struct.unpack(">I", data[pos + 4:pos + 8])[0]
    body_start = pos + 8
    body_end = body_start + length
    if body_end > len(data):
        raise SMFError(f"truncated file: {ctype!r} chunk declares length "
                        f"{length} but only {len(data) - body_start} byte(s) remain")
    return ctype, data[body_start:body_end], body_end


def parse_smf(path):
    """Parses a Standard MIDI File from raw bytes. Returns
    (ticks_per_quarter, tracks) where tracks is a list of
    (track_name_or_None, [SMFEvent, ...]); every event's abs_tick is
    already accumulated from that track's own delta-time stream. All
    tracks in a Standard MIDI File share one tick clock starting at
    tick 0 (MIDI 1.0 / SMF spec), so abs_tick values are directly
    comparable across tracks without any further adjustment.

    Fails closed (raises SMFError) rather than guess on: a missing/
    malformed MThd header, an SMPTE-timecode division (this piece's
    source files all use ticks-per-quarter-note; a verifier that silently
    misread an SMPTE file's tick meaning would be worse than one that
    refuses), a chunk that runs past the end of the file, or a status
    byte this implementation does not recognise as either a channel
    voice message, a meta event, or a sysex event.
    """
    data = Path(path).read_bytes()
    ctype, body, pos = _read_chunk(data, 0)
    if ctype != b"MThd":
        raise SMFError(f"not a Standard MIDI File: expected 'MThd', got {ctype!r}")
    if len(body) < 6:
        raise SMFError(f"MThd header too short: {len(body)} byte(s), need >= 6")
    fmt, ntracks, division = struct.unpack(">HHH", body[:6])
    if division & 0x8000:
        raise SMFError(
            "SMPTE-timecode tick division is not supported by this verifier "
            "(fail-closed refusal rather than a silent, possibly-wrong tick "
            "interpretation); every source file this tool has been run "
            "against uses ticks-per-quarter-note")
    ticks_per_quarter = division

    tracks = []
    for track_index in range(ntracks):
        ctype, body, pos = _read_chunk(data, pos)
        if ctype != b"MTrk":
            raise SMFError(f"expected an 'MTrk' chunk for track {track_index}, "
                            f"got {ctype!r}")
        events = []
        track_name = None
        abs_tick = 0
        running_status = None
        tpos = 0
        n = len(body)
        while tpos < n:
            delta, tpos = _read_vlq(body, tpos)
            abs_tick += delta
            if tpos >= n:
                raise SMFError(f"track {track_index}: truncated event at byte {tpos}")
            first = body[tpos]
            if first < 0x80:
                # Running status: this byte is actually the first DATA byte
                # of a repeat of the previous channel-voice status; do not
                # consume it as a status byte.
                if running_status is None:
                    raise SMFError(f"track {track_index}: running status "
                                    f"byte 0x{first:02X} used with none in "
                                    "effect (malformed file)")
                status = running_status
            else:
                status = first
                tpos += 1
                if status < 0xF0:
                    running_status = status

            if status == 0xFF:
                if tpos >= n:
                    raise SMFError(f"track {track_index}: truncated meta event")
                meta_type = body[tpos]
                tpos += 1
                length, tpos = _read_vlq(body, tpos)
                mdata = bytes(body[tpos:tpos + length])
                tpos += length
                if meta_type == 0x03 and track_name is None:  # track name (first only)
                    track_name = mdata.decode("ascii", errors="replace").strip()
                elif meta_type == 0x51 and length == 3:       # set tempo
                    tempo_us = (mdata[0] << 16) | (mdata[1] << 8) | mdata[2]
                    events.append(SMFEvent(abs_tick, "tempo", data=tempo_us))
            elif status in (0xF0, 0xF7):                      # sysex
                length, tpos = _read_vlq(body, tpos)
                tpos += length
            else:
                hi = status & 0xF0
                lo = status & 0x0F
                if hi in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    if tpos + 2 > n:
                        raise SMFError(f"track {track_index}: truncated "
                                        f"channel message at byte {tpos}")
                    d1, d2 = body[tpos], body[tpos + 1]
                    tpos += 2
                    if hi == 0x90:
                        kind = "note_on" if d2 > 0 else "note_off"
                        events.append(SMFEvent(abs_tick, kind, channel=lo,
                                                note=d1, velocity=d2))
                    elif hi == 0x80:
                        events.append(SMFEvent(abs_tick, "note_off", channel=lo,
                                                note=d1, velocity=d2))
                    # 0xA0 (poly aftertouch) / 0xB0 (control change) /
                    # 0xE0 (pitch bend) carry no note-identity information
                    # this tool needs; their 2 data bytes are consumed
                    # above (correct stream position) and discarded.
                elif hi in (0xC0, 0xD0):
                    if tpos + 1 > n:
                        raise SMFError(f"track {track_index}: truncated "
                                        f"channel message at byte {tpos}")
                    tpos += 1  # program change / channel pressure: 1 data byte
                else:
                    raise SMFError(
                        f"track {track_index}: unrecognised status byte "
                        f"0x{status:02X} at track-chunk offset {tpos} -- "
                        "refusing to guess its length")
        tracks.append((track_name, events))
    return ticks_per_quarter, tracks


def normalize_track_name(name, index):
    """Mirrors midi_to_tsukisynth.track_name()'s normalisation (lower-case,
    strip a trailing colon) purely so this independently-parsed track name
    is directly comparable to score event["performance"]["track"] values --
    this is matching a MIDI file's own declared string, not re-deriving any
    of the converter's musical logic."""
    if name:
        return name.strip().lower().rstrip(":")
    return f"track_{index}"


class TempoMap:
    """Independently-built tick->seconds conversion. Collects `set_tempo`
    meta events from EVERY track (not just track 0) -- a Standard MIDI File
    format-1 convention puts tempo on the first ("control") track, but nothing
    in the SMF spec forbids a tempo change elsewhere, and hard-coding "track
    0 only" would make this verifier trust the same assumption the
    transcriber makes rather than checking it independently."""

    def __init__(self, ticks_per_quarter, tracks):
        self.tpq = ticks_per_quarter
        changes = {0: 500_000}  # default: 120 BPM, per the MIDI spec
        for _name, events in tracks:
            for ev in events:
                if ev.kind == "tempo":
                    changes[ev.abs_tick] = ev.data
        self.changes = sorted(changes.items())
        self.segments = []
        elapsed = 0.0
        prev_tick, prev_tempo = self.changes[0]
        self.segments.append((prev_tick, elapsed, prev_tempo))
        for tick, tempo in self.changes[1:]:
            elapsed += (tick - prev_tick) * (prev_tempo / 1_000_000.0) / self.tpq
            self.segments.append((tick, elapsed, tempo))
            prev_tick, prev_tempo = tick, tempo

    def seconds(self, tick):
        seg = self.segments[0]
        for candidate in self.segments:
            if candidate[0] > tick:
                break
            seg = candidate
        base_tick, base_seconds, tempo = seg
        return base_seconds + (tick - base_tick) * (tempo / 1_000_000.0) / self.tpq


class SourceNote:
    __slots__ = ("track", "channel", "note", "start_tick", "end_tick",
                 "start_sec", "end_sec")

    def __init__(self, track, channel, note, start_tick, end_tick):
        self.track = track
        self.channel = channel
        self.note = note
        self.start_tick = start_tick
        self.end_tick = end_tick
        self.start_sec = None
        self.end_sec = None


def extract_source_notes(tracks):
    """FIFO-pairs note-on/note-off within each (track, channel, pitch)
    queue, exactly matching MIDI 1.0's own semantics for overlapping
    same-pitch notes (a note-on with velocity 0 is a note-off). Returns
    (notes, dangling) where `dangling` lists any note-on left unpaired at
    the end of its track (a malformed-file condition, reported rather than
    silently dropped)."""
    notes = []
    dangling = []
    for track_index, (raw_name, events) in enumerate(tracks):
        name = normalize_track_name(raw_name, track_index)
        queues = {}
        for ev in events:
            if ev.kind == "note_on":
                queues.setdefault((ev.channel, ev.note), []).append(ev.abs_tick)
            elif ev.kind == "note_off":
                q = queues.get((ev.channel, ev.note))
                if q:
                    start_tick = q.pop(0)
                    end_tick = max(ev.abs_tick, start_tick + 1)
                    notes.append(SourceNote(name, ev.channel, ev.note, start_tick, end_tick))
                # a note-off with no queued note-on is not an error under
                # MIDI semantics (e.g. a stray all-notes-off); nothing to pair.
        for (channel, note), q in queues.items():
            for start_tick in q:
                dangling.append({"track": name, "channel": channel, "note": note,
                                  "start_tick": start_tick})
    return notes, dangling


# =========================================================================
# 2. Score-side note-name decoding (independent re-implementation of the
#    standard MIDI note-name mapping -- NOT imported from verify_score.py
#    or tools/midi_to_tsukisynth.py, so a bug shared with either of those
#    modules cannot slip through unseen).
# =========================================================================

_NOTE_BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_name_to_midi(name):
    """Decodes a note name exactly the way ScoreRenderer's
    ScoreParser::noteNameToMidi() does (letter A-G, optional # or b,
    signed octave number, octave 4 contains MIDI 60 = C4). Returns None
    if the string cannot be parsed at all -- callers must treat that as a
    hard failure, not a skip, since it means the pitch that would actually
    be rendered cannot even be determined."""
    if not isinstance(name, str) or not name:
        return None
    if name.lstrip("-").isdigit():
        midi = int(name)
        return midi if 0 <= midi <= 127 else None
    letter = name[0].upper()
    if letter not in _NOTE_BASE:
        return None
    i = 1
    base = _NOTE_BASE[letter]
    if i < len(name) and name[i] == "#":
        base += 1
        i += 1
    elif i < len(name) and name[i] in ("b", "B"):
        base -= 1
        i += 1
    octave_str = name[i:]
    if not octave_str or not (octave_str.lstrip("-").isdigit()):
        return None
    octave = int(octave_str)
    midi = (octave + 1) * 12 + base
    return midi if 0 <= midi <= 127 else None


# =========================================================================
# 3. Verification
# =========================================================================

class Check:
    def __init__(self, name, ok, message, detail=None):
        self.name = name
        self.ok = ok
        self.message = message
        self.detail = detail or {}

    def to_dict(self):
        return {"name": self.name, "ok": self.ok, "message": self.message,
                "detail": self.detail}


INTERPRETIVE_EVENT_FIELDS = ("velocity", "engine")
INTERPRETIVE_PERFORMANCE_FIELDS = (
    "articulation", "articulation_gap_ms", "phrase_end", "breath_after_ms",
)


def score_event_window(ev):
    """(rendered_midi_pitch_or_None, start_sec, end_sec, note_field,
    performance_dict). end_sec prefers performance.intended_release_time
    (the renderer's actual note-off instant per
    midi_to_tsukisynth.event_record()'s duration-compensation comment);
    falls back to time+duration (flagged in the caller) if that field is
    absent, e.g. for a hand-authored score.json this tool is pointed at
    outside the classical-transcription pipeline."""
    perf = ev.get("performance") or {}
    pitch = note_name_to_midi(ev.get("note"))
    start = float(ev.get("time", 0.0))
    if "intended_release_time" in perf:
        end = float(perf["intended_release_time"])
        end_is_fallback = False
    else:
        end = start + float(ev.get("duration", 0.0))
        end_is_fallback = True
    return pitch, start, end, ev.get("note"), perf, end_is_fallback


def match_bidirectional(source_notes, score_events):
    """Groups both sides into (track, pitch) buckets and pairs them 1:1 in
    onset order within each bucket -- this IS the "1:1 bidirectional
    match, chord/same-tick alignment" requirement: two notes struck at the
    literally identical instant are still disambiguated correctly because
    they occupy DIFFERENT pitch buckets (a chord's simultaneous notes never
    share a pitch by definition; genuine same-pitch same-instant doubling
    is vanishingly rare and would be handled deterministically by onset-
    order FIFO within the shared bucket, same policy as MIDI's own overlapping-
    note semantics in extract_source_notes()). Returns
    (matched_pairs, missing_source, extra_score) where `missing_source` is
    source notes with no score event in their bucket and `extra_score` is
    score events with no source note in their bucket."""
    src_buckets = {}
    for n in source_notes:
        src_buckets.setdefault((n.track, n.note), []).append(n)
    for lst in src_buckets.values():
        lst.sort(key=lambda n: n.start_tick)

    score_buckets = {}
    unparseable = []
    for i, ev in enumerate(score_events):
        pitch, start, end, note_field, perf, end_is_fallback = score_event_window(ev)
        track = normalize_track_name(perf.get("track"), i) if perf.get("track") else None
        if pitch is None:
            unparseable.append((i, ev))
            continue
        score_buckets.setdefault((track, pitch), []).append(
            (i, ev, start, end, end_is_fallback))
    for lst in score_buckets.values():
        lst.sort(key=lambda t: t[2])

    matched = []
    missing_source = []
    extra_score = []
    all_keys = set(src_buckets) | set(score_buckets)
    for key in all_keys:
        src_list = src_buckets.get(key, [])
        sc_list = score_buckets.get(key, [])
        common = min(len(src_list), len(sc_list))
        for j in range(common):
            matched.append((src_list[j], sc_list[j]))
        missing_source.extend(src_list[common:])
        extra_score.extend(sc_list[common:])

    return matched, missing_source, extra_score, unparseable


def verify(midi_path, score_path, keep_json=None, quiet=False):
    checks = []
    midi_path = Path(midi_path)
    score_path = Path(score_path)

    try:
        ticks_per_quarter, tracks = parse_smf(midi_path)
    except SMFError as e:
        checks.append(Check("midi.parse", False,
                             f"INDEPENDENT SMF PARSE FAILED: {midi_path}: {e}"))
        return finalize(checks, midi_path, score_path, keep_json, quiet)
    checks.append(Check("midi.parse", True,
                         f"Parsed {midi_path.name} with this tool's own SMF "
                         f"parser (no mido): {len(tracks)} track chunk(s), "
                         f"{ticks_per_quarter} ticks/quarter-note."))

    try:
        score = json.loads(score_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        checks.append(Check("score.parse", False,
                             f"SCORE JSON PARSE FAILED: {score_path}: {e}"))
        return finalize(checks, midi_path, score_path, keep_json, quiet)
    events = score.get("events")
    if events is None:
        checks.append(Check("score.parse", False,
                             f"SCORE HAS NO \"events\" ARRAY (uses \"layers\"?) "
                             "-- this tool verifies a leaf event-score against "
                             "a source MIDI, not a composite."))
        return finalize(checks, midi_path, score_path, keep_json, quiet)
    checks.append(Check("score.parse", True,
                         f"Parsed {score_path.name}: {len(events)} event(s)."))

    source_notes, dangling = extract_source_notes(tracks)
    if dangling:
        checks.append(Check(
            "midi.note_pairing", False,
            f"MIDI PARSE FAILED: {len(dangling)} note-on event(s) in the "
            f"source MIDI have no matching note-off -- ground truth cannot "
            f"be established. First: {dangling[0]}",
            {"count": len(dangling), "examples": dangling[:10]}))
        return finalize(checks, midi_path, score_path, keep_json, quiet)
    checks.append(Check("midi.note_pairing", True,
                         f"All note-on events paired cleanly with a note-off "
                         f"across {len(tracks)} track(s): {len(source_notes)} "
                         "source note(s)."))

    tempo_map = TempoMap(ticks_per_quarter, tracks)
    for n in source_notes:
        n.start_sec = tempo_map.seconds(n.start_tick)
        n.end_sec = tempo_map.seconds(n.end_tick)

    # -- 3. total event count -----------------------------------------------
    if len(events) != len(source_notes):
        checks.append(Check(
            "counts.total_events", False,
            f"EVENT COUNT MISMATCH: score has {len(events)} event(s), "
            f"source MIDI has {len(source_notes)} note(s) (across every "
            "note-bearing track, independently parsed).",
            {"score_events": len(events), "source_notes": len(source_notes)}))
    else:
        checks.append(Check(
            "counts.total_events", True,
            f"Score event count matches source MIDI note count exactly: "
            f"{len(events)}.",
            {"score_events": len(events), "source_notes": len(source_notes)}))

    # -- 4. bidirectional 1:1 match ------------------------------------------
    matched, missing_source, extra_score, unparseable = match_bidirectional(
        source_notes, events)

    if unparseable:
        i0, ev0 = unparseable[0]
        checks.append(Check(
            "score.pitch_parseable", False,
            f"UNPARSEABLE PITCH: score event {i0} has note={ev0.get('note')!r}, "
            "which does not decode to a MIDI note number -- the rendered "
            f"pitch is unknown. {len(unparseable)} event(s) affected.",
            {"count": len(unparseable), "indices": [i for i, _ in unparseable[:20]]}))
    else:
        checks.append(Check("score.pitch_parseable", True,
                             f"All {len(events)} event note names decode to a "
                             "MIDI pitch."))

    if missing_source or extra_score:
        detail = {
            "missing_from_score": [
                {"track": n.track, "midi_note": n.note,
                 "start_sec": round(n.start_sec, 6)}
                for n in missing_source[:20]],
            "extra_in_score": [
                {"index": i, "track": (ev.get("performance") or {}).get("track"),
                 "note": ev.get("note"), "time": ev.get("time")}
                for i, ev, *_ in extra_score[:20]],
            "missing_count": len(missing_source),
            "extra_count": len(extra_score),
        }
        checks.append(Check(
            "match.bidirectional", False,
            f"1:1 MATCH FAILED: {len(missing_source)} source MIDI note(s) "
            f"have no corresponding score event (in their (track,pitch) "
            f"bucket, onset-ordered), and {len(extra_score)} score event(s) "
            "have no corresponding source note. See detail for specifics.",
            detail))
    else:
        checks.append(Check(
            "match.bidirectional", True,
            f"All {len(matched)} note(s) matched 1:1 between source MIDI "
            "and score, grouped by (track, pitch) and paired in onset order "
            "-- including every chord's simultaneous notes, each in its "
            "own pitch bucket."))

    # -- 5. per-matched-pair pitch / onset / duration ------------------------
    pitch_fail = []
    onset_fail = []
    duration_fail = []
    self_consistency_fail = []
    max_onset_err = 0.0
    for src, (idx, ev, start, end, end_is_fallback) in matched:
        # pitch: guaranteed equal by construction of the bucket key
        # (src.note == the decoded score pitch) -- but performance.midi_note
        # is a SEPARATE field the renderer does not consult; check it is not
        # silently lying about the same event.
        perf = ev.get("performance") or {}
        declared = perf.get("midi_note")
        rendered_pitch = note_name_to_midi(ev.get("note"))
        if declared is not None and declared != rendered_pitch:
            self_consistency_fail.append({
                "index": idx, "note_field": ev.get("note"),
                "rendered_midi": rendered_pitch, "performance_midi_note": declared})
        if rendered_pitch != src.note:
            # cannot actually happen given the bucket key, kept as a hard
            # assertion-style guard so a future refactor of match_bidirectional
            # cannot silently break the zero-tolerance pitch guarantee.
            pitch_fail.append({"index": idx, "source_midi": src.note,
                                "rendered_midi": rendered_pitch})

        onset_err = start - src.start_sec
        max_onset_err = max(max_onset_err, abs(onset_err))
        if abs(onset_err) > ONSET_TOL_S:
            onset_fail.append({
                "index": idx, "track": src.track, "note": ev.get("note"),
                "score_time_s": start, "source_time_s": src.start_sec,
                "onset_err_ms": onset_err * 1000.0})

        source_dur = src.end_sec - src.start_sec
        score_dur = end - start
        if score_dur > source_dur + DURATION_EPS_S:
            duration_fail.append({
                "index": idx, "track": src.track, "note": ev.get("note"),
                "score_sounding_s": score_dur, "source_sounding_s": source_dur,
                "excess_ms": (score_dur - source_dur) * 1000.0,
                "end_field_is_fallback_time_plus_duration": end_is_fallback})

    if pitch_fail:
        checks.append(Check(
            "pitch.exact_match", False,
            f"PITCH MISMATCH: {len(pitch_fail)} matched event(s) render a "
            "different MIDI pitch than their bucket-matched source note "
            f"(internal invariant violation). First: {pitch_fail[0]}",
            {"count": len(pitch_fail), "examples": pitch_fail[:10]}))
    else:
        checks.append(Check("pitch.exact_match", True,
                             f"All {len(matched)} matched event(s) render "
                             "exactly the source MIDI note number (zero-"
                             "tolerance integer equality)."))

    if self_consistency_fail:
        checks.append(Check(
            "score.performance_midi_note_consistent", False,
            f"SELF-CONSISTENCY FAILED: {len(self_consistency_fail)} score "
            "event(s) have a performance.midi_note that disagrees with the "
            "pitch actually decoded from their own note field (a data-"
            "quality bug independent of the source MIDI comparison). "
            f"First: {self_consistency_fail[0]}",
            {"count": len(self_consistency_fail), "examples": self_consistency_fail[:10]}))
    else:
        checks.append(Check(
            "score.performance_midi_note_consistent", True,
            "performance.midi_note agrees with the rendered note-name pitch "
            "on every matched event."))

    if onset_fail:
        checks.append(Check(
            "onset.within_tolerance", False,
            f"ONSET MISMATCH: {len(onset_fail)} matched event(s) exceed the "
            f"+/-{ONSET_TOL_S * 1000:.1f} ms tempo-map tolerance. Worst: "
            f"{max(onset_fail, key=lambda d: abs(d['onset_err_ms']))}",
            {"count": len(onset_fail), "examples": onset_fail[:10],
             "tol_ms": ONSET_TOL_S * 1000.0}))
    else:
        checks.append(Check(
            "onset.within_tolerance", True,
            f"All {len(matched)} matched event(s) land within "
            f"+/-{ONSET_TOL_S * 1000:.1f} ms of the tempo-map-converted "
            f"source onset (max observed: {max_onset_err * 1000:.4f} ms)."))

    if duration_fail:
        checks.append(Check(
            "duration.not_exceeding_source", False,
            f"DURATION EXCEEDS SOURCE: {len(duration_fail)} matched event(s) "
            "sound longer than their source MIDI note "
            f"(> {DURATION_EPS_S * 1000:.2f} ms float-rounding slack). "
            f"First: {duration_fail[0]}",
            {"count": len(duration_fail), "examples": duration_fail[:10]}))
    else:
        checks.append(Check(
            "duration.not_exceeding_source", True,
            f"All {len(matched)} matched event(s) sound no longer than "
            "their source MIDI note (articulation may shorten; never "
            "lengthen)."))

    # -- 6. whole-piece duration consistency ---------------------------------
    if source_notes and events:
        source_end = max(n.end_sec for n in source_notes)
        score_end_candidates = []
        for ev in events:
            _p, start, end, _n, _perf, _fb = score_event_window(ev)
            score_end_candidates.append(end)
        score_end = max(score_end_candidates)
        diff = score_end - source_end   # positive = score runs PAST the source
        if diff > DURATION_EPS_S:
            checks.append(Check(
                "duration.whole_piece", False,
                f"WHOLE-PIECE DURATION EXCEEDS SOURCE: score's last "
                f"sounding instant is {score_end:.6f}s, source MIDI's last "
                f"note-off is {source_end:.6f}s ({diff * 1000:+.3f} ms "
                f"past it, limit {DURATION_EPS_S * 1000:.2f} ms slack).",
                {"score_end_s": score_end, "source_end_s": source_end,
                 "diff_ms": diff * 1000.0}))
        else:
            checks.append(Check(
                "duration.whole_piece", True,
                f"Score's overall length ({score_end:.6f}s) does not extend "
                f"past the source MIDI's last note-off ({source_end:.6f}s); "
                f"{-diff * 1000:.3f} ms short of it (articulation may "
                "legitimately shorten the final note's release, same as "
                "any other note -- see duration.not_exceeding_source)."))

    report = finalize(checks, midi_path, score_path, keep_json, quiet,
                       matched=len(matched), source_notes=len(source_notes),
                       score_events=len(events))
    return report


def finalize(checks, midi_path, score_path, keep_json, quiet, **extra):
    n_fail = sum(1 for c in checks if not c.ok)
    n_pass = sum(1 for c in checks if c.ok)
    report = {
        "midi": str(midi_path) if midi_path else None,
        "score": str(score_path) if score_path else None,
        "checks": [c.to_dict() for c in checks],
        "interpretive_fields_not_judged": {
            "event": list(INTERPRETIVE_EVENT_FIELDS),
            "performance": list(INTERPRETIVE_PERFORMANCE_FIELDS),
            "note": ("velocity is TsukiSynth performance-dynamics "
                     "interpretation (not a 1:1 copy of MIDI velocity by "
                     "design); engine selects the instrument model "
                     "(piano/cimbalom/string all render the SAME notes); "
                     "articulation fields describe HOW a note is shaped, "
                     "not WHICH note/when it starts."),
        },
        "summary": {"pass": n_pass, "fail": n_fail, **extra},
    }
    if keep_json:
        Path(keep_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not quiet:
        for c in checks:
            print(f"  [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.message}")
        print(f"  summary: {n_pass} PASS / {n_fail} FAIL"
              + (f" ({extra['matched']}/{extra['source_notes']} notes matched, "
                 f"{extra['score_events']} score events)" if "matched" in extra else ""))
    return report


# =========================================================================
# 4. Sentinel selftest -- known-good pair + four required mutations, each
#    demonstrated to FAIL, plus the unmodified pair demonstrated to PASS.
# =========================================================================

GOOD_MIDI = ROOT / "scores" / "classical" / "fur_elise" / "source" / "fur_Elise_WoO59.mid"
GOOD_SCORE = ROOT / "scores" / "classical" / "fur_elise" / "fur_elise_complete.score.json"


def _run_on_mutated_score(mutate_fn, tmpdir, name):
    score = json.loads(GOOD_SCORE.read_text(encoding="utf-8"))
    mutate_fn(score)
    p = Path(tmpdir) / (name + ".score.json")
    p.write_text(json.dumps(score, ensure_ascii=False), encoding="utf-8")
    return verify(GOOD_MIDI, p, quiet=True)


def selftest():
    if not GOOD_MIDI.is_file() or not GOOD_SCORE.is_file():
        print(f"[BLOCKED] sentinel fixture missing: {GOOD_MIDI} / {GOOD_SCORE}")
        return 2

    ok = True
    with tempfile.TemporaryDirectory(prefix="score_vs_midi_selftest_") as td:
        # A: unmodified pair must PASS cleanly.
        A = verify(GOOD_MIDI, GOOD_SCORE, quiet=True)
        a_ok = A["summary"]["fail"] == 0
        print(f"[{'PASS' if a_ok else 'FAIL'}] sentinel A: unmodified Fur Elise "
              f"(piano) score verifies clean against its source MIDI "
              f"({A['summary'].get('matched')} notes matched)")
        if not a_ok:
            for c in A["checks"]:
                if not c["ok"]:
                    print(f"    {c['name']}: {c['message']}")
        ok &= a_ok

        def expect_fail(rep, name, desc):
            good = rep["summary"]["fail"] >= 1
            failing = [c["name"] for c in rep["checks"] if not c["ok"]]
            print(f"[{'PASS' if good else 'FAIL'}] sentinel {name}: {desc} "
                  f"-> {rep['summary']['fail']} FAIL as required "
                  f"({', '.join(failing) if failing else 'none'})")
            return good

        # B: transpose one event by +2 semitones (pitch and its provenance
        # field both changed, so this isolates "wrong pitch was declared",
        # not merely a self-consistency bug).
        def mut_transpose(score):
            ev = score["events"][10]
            midi = note_name_to_midi(ev["note"]) + 2
            # re-derive a spelling the same way the source note names look
            # (sharp-based); exact spelling doesn't matter, only the
            # resulting MIDI number does.
            names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            ev["note"] = f"{names[midi % 12]}{midi // 12 - 1}"
            if "performance" in ev and "midi_note" in ev["performance"]:
                ev["performance"]["midi_note"] = midi
        B = _run_on_mutated_score(mut_transpose, td, "B")
        ok &= expect_fail(B, "B", "+2 semitone transposition of one event is caught")

        # C: shift one event's onset by +20 ms (well past the 1 ms tempo-
        # map tolerance, well short of colliding with a neighbour).
        def mut_timeshift(score):
            score["events"][10]["time"] = round(score["events"][10]["time"] + 0.020, 6)
        C = _run_on_mutated_score(mut_timeshift, td, "C")
        ok &= expect_fail(C, "C", "+20 ms onset shift of one event is caught")

        # D: delete one event.
        def mut_delete(score):
            score["events"].pop(15)
        D = _run_on_mutated_score(mut_delete, td, "D")
        ok &= expect_fail(D, "D", "deleting one score event is caught")

        # E: duplicate one event at a time no other event occupies (an
        # "extra" / phantom note the source MIDI does not have).
        def mut_extra(score):
            e = json.loads(json.dumps(score["events"][10]))
            e["time"] = round(e["time"] + 37.5, 6)  # well past the piece's end
            if "performance" in e:
                e["performance"]["intended_release_time"] = round(
                    e["performance"].get("intended_release_time", e["time"]) + 37.5, 6)
            score["events"].append(e)
            score["events"].sort(key=lambda x: x["time"])
        E = _run_on_mutated_score(mut_extra, td, "E")
        ok &= expect_fail(E, "E", "one extra (undeclared) note is caught")

    print("SELFTEST " + ("PASS (5/5)" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("midi", nargs="?", help="Source Standard MIDI File (.mid)")
    ap.add_argument("score", nargs="?", help="TsukiSynth score.json to verify")
    ap.add_argument("--json", help="Write the machine-readable report here")
    ap.add_argument("--selftest", action="store_true",
                     help="Run the mutation-tested sentinel suite and exit")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.midi or not a.score:
        ap.print_help()
        sys.exit(2)
    report = verify(a.midi, a.score, keep_json=a.json)
    sys.exit(1 if report["summary"]["fail"] else 0)


if __name__ == "__main__":
    main()
