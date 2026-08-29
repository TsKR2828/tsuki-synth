#!/usr/bin/env python3
"""
Convert standard MIDI into TsukiSynth Score v1 JSON.

The converter preserves source note-on/note-off timing, then adds a small,
documented physical-articulation gap where consecutive notes would otherwise
touch exactly.  Rests and phrase breaths are emitted explicitly for AI and
non-auditory inspection while remaining harmless to the current C++ renderer.

Requires:
    pip install mido

Subcommands:
    four-seasons  Vivaldi-specific batch mode (unchanged since 2026-06-21).
                  Expects the Mutopia MIDI folders:
                  spring/spring-score.mid, spring/spring-score-1.mid, ...
    convert       Generic single/dual-track MIDI -> Score v1 (added
                  2026-08-28 for the Fur Elise relicense work; see
                  generic_piano_score_document() and
                  reports/decision_packets/CLASSICAL_RELICENSE_PLAN.md).
                  Example:
                    python tools/midi_to_tsukisynth.py convert in.mid \\
                      --output out.score.json --profile piano_two_hand \\
                      --engine piano --id my_id --title "My Title"
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from dataclasses import dataclass, replace as dataclass_replace
from pathlib import Path
from typing import Any, Iterable

try:
    import mido
except ImportError as exc:  # pragma: no cover - user-facing dependency guard
    raise SystemExit("mido is required: python -m pip install mido") from exc


MUTOPIA_LICENSE = "Creative Commons Attribution-ShareAlike 3.0"
MUTOPIA_LICENSE_URL = "https://creativecommons.org/licenses/by-sa/3.0/"
MUTOPIA_SOURCE_URLS = {
    "spring": "https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=301",
    "summer": "https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=336",
    "autumn": "https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=350",
    "winter": "https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=351",
}


@dataclass(frozen=True)
class TrackProfile:
    """Per-track physical/performance profile.

    Generalised 2026-08-28 (Fur Elise relicense work, see
    reports/decision_packets/CLASSICAL_RELICENSE_PLAN.md Sec.3): `engine`
    and `params` replace the old string-instrument-only
    diameter_mm/strike_position/damping fields so this dataclass can
    describe a bowed string course (Vivaldi) OR a struck piano/cimbalom
    course (Fur Elise, and any future single/dual-track piano MIDI)
    without a second parallel struct. `params` holds exactly the dict
    that goes into the score event's "params" object, in the same key
    order it always rendered in, so existing four-seasons output is
    byte-for-byte unchanged (verified by full corpus regeneration diff,
    see CLASSICAL_RELICENSE_PLAN.md execution notes)."""

    role: str
    label: str
    engine: str
    base_velocity: float
    params: dict[str, Any]


TRACK_PROFILES = {
    "solo": TrackProfile(
        role="solo_violin",
        label="Violino principale",
        engine="string",
        base_velocity=0.72,
        params={
            "material": "steel",
            "diameter_mm": 0.55,
            "strike_position": 0.18,
            "exciter": "bow",
            "damping_override": 0.34,
        },
    ),
    "violinone": TrackProfile(
        role="violin_1",
        label="Violino primo",
        engine="string",
        base_velocity=0.50,
        params={
            "material": "steel",
            "diameter_mm": 0.62,
            "strike_position": 0.22,
            "exciter": "bow",
            "damping_override": 0.40,
        },
    ),
    "violintwo": TrackProfile(
        role="violin_2",
        label="Violino secondo",
        engine="string",
        base_velocity=0.45,
        params={
            "material": "steel",
            "diameter_mm": 0.68,
            "strike_position": 0.24,
            "exciter": "bow",
            "damping_override": 0.44,
        },
    ),
    "viola": TrackProfile(
        role="viola",
        label="Alto viola",
        engine="string",
        base_velocity=0.42,
        params={
            "material": "steel",
            "diameter_mm": 0.90,
            "strike_position": 0.28,
            "exciter": "bow",
            "damping_override": 0.48,
        },
    ),
    "cello": TrackProfile(
        role="cello_continuo",
        label="Violoncello / continuo",
        engine="string",
        base_velocity=0.47,
        params={
            "material": "steel",
            "diameter_mm": 1.45,
            "strike_position": 0.32,
            "exciter": "bow",
            "damping_override": 0.52,
        },
    ),
}


# Generic single/dual-track piano profile set (2026-08-28, Fur Elise).
# Mutopia's LilyPond-exported piano MIDIs conventionally name the two
# staves' tracks "up:" (treble/right hand) and "down:" (bass/left hand) --
# confirmed by direct inspection of fur_Elise_WoO59.mid (see
# reports/gate_outputs/furelise_license_evidence.txt for the source
# fetch). params intentionally mirror the ONE existing verified "piano"
# engine example in this repo (scores/examples/physical_piano.score.json:
# material=steel, diameter_mm=1.0, no explicit strike_position/exciter)
# rather than inventing a per-note string-gauge table this project has no
# sourced data for -- ScoreRenderer.h's piano branch already overrides
# strike_position/exciter internally (wood_mallet+0.3 -> felt+0.125) when
# they are left at their string defaults, so omitting them here is not a
# loss of fidelity versus the existing example. base_velocity gives the
# melody (right hand) a touch more presence than the accompaniment (left
# hand), the same relative-dynamics idea already used for Vivaldi's
# solo-vs-continuo split -- the source MIDI itself has NO real dynamics
# (every note_on is velocity 62, a LilyPond/MIDI-export constant, verified
# by direct inspection), so per-hand balance is TsukiSynth interpretation
# data, exactly like the Vivaldi editorial_note already discloses for bow
# gaps and dynamics.
PIANO_HAND_PROFILES = {
    "up": TrackProfile(
        role="right_hand",
        label="Right hand (melody)",
        engine="piano",
        base_velocity=0.62,
        params={"material": "steel", "diameter_mm": 1.0},
    ),
    "down": TrackProfile(
        role="left_hand",
        label="Left hand (bass / accompaniment)",
        engine="piano",
        base_velocity=0.44,
        params={"material": "steel", "diameter_mm": 1.0},
    ),
}

PROFILE_SETS = {
    "piano_two_hand": PIANO_HAND_PROFILES,
}


FOUR_SEASONS: dict[str, list[dict[str, Any]]] = {
    "spring": [
        {
            "file": "spring-score.mid",
            "number": 1,
            "tempo_name": "Allegro",
            "key": "E major",
            "mood": "playful",
            "pace": "fast",
            "description": "鳥鳴、溪流與春雷；明亮而具清楚回聲式斷點。",
        },
        {
            "file": "spring-score-1.mid",
            "number": 2,
            "tempo_name": "Largo",
            "key": "C# minor",
            "mood": "calm",
            "pace": "slow",
            "description": "沉睡牧羊人；保留長線條與樂句尾端呼吸。",
        },
        {
            "file": "spring-score-2.mid",
            "number": 3,
            "tempo_name": "Danza pastorale. Allegro",
            "key": "E major",
            "mood": "playful",
            "pace": "dance",
            "description": "田園舞曲；複合拍律動與輕巧換弓。",
        },
    ],
    "summer": [
        {
            "file": "summer-score.mid",
            "number": 1,
            "tempo_name": "Allegro non molto",
            "key": "G minor",
            "mood": "tense",
            "pace": "moderate",
            "description": "暑氣、鳥鳴與風暴前兆；長停頓與突發段落並存。",
        },
        {
            "file": "summer-score-1.mid",
            "number": 2,
            "tempo_name": "Adagio e piano – Presto e forte",
            "key": "G minor",
            "mood": "ominous",
            "pace": "slow",
            "description": "疲倦與雷聲交錯；慢句之間保留明顯喘息。",
        },
        {
            "file": "summer-score-2.mid",
            "number": 3,
            "tempo_name": "Presto",
            "key": "G minor",
            "mood": "epic",
            "pace": "very_fast",
            "description": "猛烈夏季風暴；短音採緊密但可辨識的物理制音。",
        },
    ],
    "autumn": [
        {
            "file": "autumn-score.mid",
            "number": 1,
            "tempo_name": "Allegro",
            "key": "F major",
            "mood": "playful",
            "pace": "fast",
            "description": "豐收舞蹈與醉意；重拍清楚、句尾留氣。",
        },
        {
            "file": "autumn-score-1.mid",
            "number": 2,
            "tempo_name": "Adagio molto",
            "key": "D minor",
            "mood": "calm",
            "pace": "slow",
            "description": "醉後沉睡；延長共鳴並保留靜默空間。",
        },
        {
            "file": "autumn-score-2.mid",
            "number": 3,
            "tempo_name": "Allegro",
            "key": "F major",
            "mood": "epic",
            "pace": "fast",
            "description": "狩獵場景；追逐型短句與應答式休止。",
        },
    ],
    "winter": [
        {
            "file": "winter-score.mid",
            "number": 1,
            "tempo_name": "Allegro non molto",
            "key": "F minor",
            "mood": "tense",
            "pace": "very_fast",
            "description": "寒顫與跺腳；重複短音特別強調斷奏空隙。",
        },
        {
            "file": "winter-score-1.mid",
            "number": 2,
            "tempo_name": "Largo",
            "key": "E-flat major",
            "mood": "calm",
            "pace": "slow",
            "description": "室內暖意與窗外雨滴；旋律採長呼吸。",
        },
        {
            "file": "winter-score-2.mid",
            "number": 3,
            "tempo_name": "Allegro",
            "key": "F minor",
            "mood": "epic",
            "pace": "fast",
            "description": "冰上行走與北風；快速音群仍保留換弓邊界。",
        },
    ],
}


SEASON_META = {
    "spring": ("Spring / La primavera", "RV 269", 1),
    "summer": ("Summer / L'estate", "RV 315", 2),
    "autumn": ("Autumn / L'autunno", "RV 293", 3),
    "winter": ("Winter / L'inverno", "RV 297", 4),
}


@dataclass
class MidiNote:
    track: str
    start_tick: int
    end_tick: int
    note: int
    source_velocity: int
    start_sec: float = 0.0
    end_sec: float = 0.0
    sounding_end_sec: float = 0.0
    articulation: str = "legato"
    articulation_gap_ms: float = 0.0
    phrase_end: bool = False
    breath_after_ms: float = 0.0


class TickMap:
    def __init__(self, midi: mido.MidiFile):
        self.ticks_per_beat = midi.ticks_per_beat
        changes: list[tuple[int, int]] = [(0, 500_000)]
        absolute = 0
        for message in midi.tracks[0]:
            absolute += message.time
            if message.type == "set_tempo":
                changes.append((absolute, message.tempo))

        merged: dict[int, int] = {}
        for tick, tempo in changes:
            merged[tick] = tempo
        self.changes = sorted(merged.items())

        self.segments: list[tuple[int, float, int]] = []
        elapsed = 0.0
        previous_tick, previous_tempo = self.changes[0]
        self.segments.append((previous_tick, elapsed, previous_tempo))
        for tick, tempo in self.changes[1:]:
            elapsed += mido.tick2second(
                tick - previous_tick, self.ticks_per_beat, previous_tempo
            )
            self.segments.append((tick, elapsed, tempo))
            previous_tick, previous_tempo = tick, tempo

    def seconds(self, tick: int) -> float:
        segment = self.segments[0]
        for candidate in self.segments:
            if candidate[0] > tick:
                break
            segment = candidate
        base_tick, base_seconds, tempo = segment
        return base_seconds + mido.tick2second(
            tick - base_tick, self.ticks_per_beat, tempo
        )

    def tempo_at(self, tick: int) -> int:
        tempo = self.segments[0][2]
        for candidate_tick, _, candidate_tempo in self.segments:
            if candidate_tick > tick:
                break
            tempo = candidate_tempo
        return tempo

    def quarter_seconds_at(self, tick: int) -> float:
        return self.tempo_at(tick) / 1_000_000.0


def round_float(value: float, digits: int = 6) -> float:
    rounded = round(value, digits)
    return 0.0 if rounded == -0.0 else rounded


def midi_frequency(note: int) -> float:
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def note_name(note: int, key: str) -> str:
    spellings = {
        "E major": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
        "C# minor": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
        "G minor": ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
        "F major": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
        "D minor": ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
        "F minor": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
        "E-flat major": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    }
    names = spellings.get(
        key, ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    )
    return f"{names[note % 12]}{note // 12 - 1}"


def track_name(track: mido.MidiTrack, index: int) -> str:
    for message in track:
        if message.type == "track_name":
            # 2026-08-28: also strip a trailing colon. Mutopia's LilyPond
            # piano exports name staves "up:"/"down:" (confirmed by direct
            # inspection of fur_Elise_WoO59.mid); the Vivaldi track names
            # ("solo", "violinone", ...) never contain a colon, so this is
            # a no-op for every existing four-seasons caller (verified by
            # full 12-movement byte-for-byte regeneration diff, see
            # CLASSICAL_RELICENSE_PLAN.md execution notes).
            return message.name.strip().lower().rstrip(":")
    return f"track_{index}"


def extract_notes(midi: mido.MidiFile, valid_tracks: set[str]) -> list[MidiNote]:
    """Parses note-on/note-off pairs from every MIDI track whose
    (lower-cased, stripped) track_name is in `valid_tracks`. Generalised
    2026-08-28: previously read the module-global TRACK_PROFILES (Vivaldi
    only); callers now pass whichever track-name set applies to their
    profile set (e.g. set(TRACK_PROFILES) for four-seasons,
    set(PIANO_HAND_PROFILES) for a piano MIDI), with no change in
    behaviour for existing callers."""
    notes: list[MidiNote] = []
    for index, track in enumerate(midi.tracks[1:], start=1):
        name = track_name(track, index)
        if name not in valid_tracks:
            continue
        absolute = 0
        active: dict[tuple[int, int], collections.deque[tuple[int, int]]] = (
            collections.defaultdict(collections.deque)
        )
        for message in track:
            absolute += message.time
            if message.type == "note_on" and message.velocity > 0:
                active[(message.channel, message.note)].append(
                    (absolute, message.velocity)
                )
            elif message.type in {"note_off", "note_on"} and (
                message.type == "note_off" or message.velocity == 0
            ):
                queue = active[(message.channel, message.note)]
                if queue:
                    start_tick, velocity = queue.popleft()
                    notes.append(
                        MidiNote(
                            track=name,
                            start_tick=start_tick,
                            end_tick=max(absolute, start_tick + 1),
                            note=message.note,
                            source_velocity=velocity,
                        )
                    )
        dangling = sum(len(queue) for queue in active.values())
        if dangling:
            raise ValueError(f"{name}: {dangling} unmatched note-on events")
    return notes


def distinct_onsets(notes: Iterable[MidiNote]) -> list[int]:
    return sorted({note.start_tick for note in notes})


def next_value(values: list[int], current: int) -> int | None:
    for value in values:
        if value > current:
            return value
    return None


# Articulation-gap LABEL vocabulary per instrument family. The gap-length
# *physics* (how much of the notated duration is shaved off before the
# next onset) is identical across families -- only the semantic name of
# "what physically causes the gap" changes, so a piano transcription
# doesn't claim a "bow change" it never had. Generalised 2026-08-28;
# "bowed" is byte-for-byte the original (pre-generalisation) label set, so
# every existing four-seasons caller (which does not pass `style`) is
# unaffected.
ARTICULATION_STYLE_LABELS = {
    "bowed": {
        "short": "short_bow",
        "detached": "detached_bow",
        "long_change": "long_bow_change",
        "change": "bow_change",
    },
    "piano": {
        "short": "short_release",
        "detached": "detached_touch",
        "long_change": "long_pedal_release",
        "change": "finger_release",
    },
}


def articulation_gap_seconds(
    note: MidiNote,
    next_onset_tick: int | None,
    tick_map: TickMap,
    pace: str,
    same_pitch_at_next: bool,
    style: str = "bowed",
) -> tuple[float, str]:
    labels = ARTICULATION_STYLE_LABELS[style]
    source_duration = note.end_sec - note.start_sec
    if next_onset_tick is None:
        return min(0.055, source_duration * 0.08), "final_release"

    next_onset_sec = tick_map.seconds(next_onset_tick)
    if note.end_sec < next_onset_sec - 0.001:
        return 0.0, "notated_rest"
    if note.end_sec > next_onset_sec + 0.001:
        return 0.0, "overlap_sustain"

    beats = (note.end_tick - note.start_tick) / tick_map.ticks_per_beat
    if same_pitch_at_next and beats <= 0.5:
        cap = 0.042 if pace in {"fast", "very_fast"} else 0.055
        return min(cap, source_duration * 0.18), "staccato_rearticulation"
    if pace == "very_fast":
        return min(0.012, source_duration * 0.07), labels["short"]
    if pace in {"fast", "dance"}:
        return min(0.018, source_duration * 0.08), labels["detached"]
    if pace == "slow":
        return min(0.032, source_duration * 0.05), labels["long_change"]
    return min(0.022, source_duration * 0.07), labels["change"]


def add_timing_and_articulation(
    notes: list[MidiNote], tick_map: TickMap, pace: str, style: str = "bowed"
) -> None:
    by_track: dict[str, list[MidiNote]] = collections.defaultdict(list)
    for note in notes:
        note.start_sec = tick_map.seconds(note.start_tick)
        note.end_sec = tick_map.seconds(note.end_tick)
        by_track[note.track].append(note)

    for track_notes in by_track.values():
        track_notes.sort(key=lambda n: (n.start_tick, n.note, n.end_tick))
        onsets = distinct_onsets(track_notes)
        notes_at_onset: dict[int, set[int]] = collections.defaultdict(set)
        for note in track_notes:
            notes_at_onset[note.start_tick].add(note.note)

        for note in track_notes:
            next_onset_tick = next_value(onsets, note.start_tick)
            same_pitch = (
                next_onset_tick is not None
                and note.note in notes_at_onset[next_onset_tick]
            )
            gap, articulation = articulation_gap_seconds(
                note, next_onset_tick, tick_map, pace, same_pitch, style
            )
            source_duration = note.end_sec - note.start_sec
            gap = min(gap, max(0.0, source_duration - 0.006))
            note.sounding_end_sec = max(note.start_sec + 0.006, note.end_sec - gap)
            note.articulation = articulation
            note.articulation_gap_ms = gap * 1000.0

            if next_onset_tick is not None:
                next_onset_sec = tick_map.seconds(next_onset_tick)
                actual_silence = max(0.0, next_onset_sec - note.sounding_end_sec)
                quarter = tick_map.quarter_seconds_at(note.end_tick)
                phrase_threshold = max(
                    0.16 if pace != "slow" else 0.22, quarter * 0.45
                )
                note.phrase_end = actual_silence >= phrase_threshold
                note.breath_after_ms = actual_silence * 1000.0
            else:
                note.phrase_end = True
                note.breath_after_ms = 0.0


def merged_intervals(notes: list[MidiNote]) -> list[tuple[float, float]]:
    intervals = sorted(
        (note.start_sec, note.sounding_end_sec)
        for note in notes
        if note.sounding_end_sec > note.start_sec
    )
    merged: list[list[float]] = []
    for start, end in intervals:
        if not merged or start > merged[-1][1] + 0.001:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def make_rests(
    notes: list[MidiNote],
    piece_end: float,
    tick_map: TickMap,
    role_for: dict[str, str],
) -> list[dict[str, Any]]:
    """`role_for` maps track name -> performance.role string. Generalised
    2026-08-28: previously indexed the module-global TRACK_PROFILES
    directly; callers now pass whichever role mapping applies (see
    extract_notes() docstring for the same pattern)."""
    by_track: dict[str, list[MidiNote]] = collections.defaultdict(list)
    for note in notes:
        by_track[note.track].append(note)

    rests: list[dict[str, Any]] = []
    for track, track_notes in sorted(by_track.items()):
        intervals = merged_intervals(track_notes)
        cursor = 0.0
        for start, end in intervals:
            if start - cursor >= 0.035:
                rests.append(rest_record(track, cursor, start, tick_map, role_for[track]))
            cursor = max(cursor, end)
        if piece_end - cursor >= 0.035:
            rests.append(rest_record(track, cursor, piece_end, tick_map, role_for[track]))
    return rests


def rest_record(
    track: str, start: float, end: float, tick_map: TickMap, role: str
) -> dict[str, Any]:
    duration = end - start
    if start <= 0.001:
        kind = "entrance_rest"
    elif duration < 0.35:
        kind = "breath"
    elif duration < 2.0:
        kind = "rest"
    else:
        kind = "long_rest"
    quarter = tick_map.quarter_seconds_at(0)
    return {
        "track": track,
        "role": role,
        "time": round_float(start),
        "duration": round_float(duration),
        "approx_quarter_beats": round_float(duration / quarter, 3),
        "kind": kind,
    }


def make_phrases(
    notes: list[MidiNote],
    rests: list[dict[str, Any]],
    piece_end: float,
    role_for: dict[str, str],
) -> list[dict[str, Any]]:
    by_track: dict[str, list[MidiNote]] = collections.defaultdict(list)
    for note in notes:
        by_track[note.track].append(note)
    rests_by_track: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for rest in rests:
        if rest["kind"] in {"rest", "long_rest"}:
            rests_by_track[rest["track"]].append(rest)

    phrases: list[dict[str, Any]] = []
    for track, track_notes in sorted(by_track.items()):
        if not track_notes:
            continue
        boundaries = rests_by_track[track]
        phrase_start = min(note.start_sec for note in track_notes)
        phrase_number = 1
        for rest in boundaries:
            if rest["time"] <= phrase_start + 0.001:
                phrase_start = rest["time"] + rest["duration"]
                continue
            phrase_end = rest["time"]
            if phrase_end - phrase_start >= 0.08:
                phrases.append(
                    {
                        "track": track,
                        "role": role_for[track],
                        "number": phrase_number,
                        "start": round_float(phrase_start),
                        "end": round_float(phrase_end),
                        "breath_after_ms": round_float(
                            rest["duration"] * 1000.0, 3
                        ),
                    }
                )
                phrase_number += 1
            phrase_start = rest["time"] + rest["duration"]
        last_end = max(note.sounding_end_sec for note in track_notes)
        if last_end - phrase_start >= 0.08:
            phrases.append(
                {
                    "track": track,
                    "role": role_for[track],
                    "number": phrase_number,
                    "start": round_float(phrase_start),
                    "end": round_float(min(piece_end, last_end)),
                    "breath_after_ms": 0.0,
                }
            )
    return phrases


def velocity_for(note: MidiNote, profile: TrackProfile, tick_map: TickMap, pace: str) -> float:
    source_scale = note.source_velocity / 90.0 if note.source_velocity else 1.0
    velocity = profile.base_velocity * source_scale

    quarter_ticks = tick_map.ticks_per_beat
    if note.start_tick % quarter_ticks == 0:
        velocity += 0.035
    if note.articulation == "staccato_rearticulation":
        velocity += 0.025
    if note.phrase_end:
        velocity -= 0.025
    if pace == "slow":
        velocity -= 0.035
    elif pace == "very_fast":
        velocity += 0.025
    return max(0.12, min(0.92, velocity))


def time_signatures(midi: mido.MidiFile, tick_map: TickMap) -> list[dict[str, Any]]:
    absolute = 0
    result: list[dict[str, Any]] = []
    for message in midi.tracks[0]:
        absolute += message.time
        if message.type == "time_signature":
            result.append(
                {
                    "time": round_float(tick_map.seconds(absolute)),
                    "tick": absolute,
                    "numerator": message.numerator,
                    "denominator": message.denominator,
                }
            )
    return result


def tempo_map(tick_map: TickMap) -> list[dict[str, Any]]:
    result = []
    for tick, _, tempo in tick_map.segments:
        result.append(
            {
                "time": round_float(tick_map.seconds(tick)),
                "tick": tick,
                "quarter_bpm": round_float(mido.tempo2bpm(tempo), 3),
                "microseconds_per_quarter": tempo,
            }
        )
    return result


def event_record(
    note: MidiNote,
    profile: TrackProfile,
    tick_map: TickMap,
    pace: str,
    key: str,
) -> dict[str, Any]:
    intended_sounding_duration = note.sounding_end_sec - note.start_sec
    # ScoreRenderer calls noteOff at 90% of event.duration.
    renderer_duration = intended_sounding_duration / 0.9
    performance = {
        "track": note.track,
        "role": profile.role,
        "midi_note": note.note,
        "frequency_hz": round_float(midi_frequency(note.note), 3),
        "source_duration_sec": round_float(note.end_sec - note.start_sec),
        "intended_release_time": round_float(note.sounding_end_sec),
        "articulation": note.articulation,
        "articulation_gap_ms": round_float(note.articulation_gap_ms, 3),
        "phrase_end": note.phrase_end,
        "breath_after_ms": round_float(note.breath_after_ms, 3),
    }
    event: dict[str, Any] = {
        "time": round_float(note.start_sec),
        "duration": round_float(renderer_duration, 8),
        "engine": profile.engine,
        "note": note_name(note.note, key),
        "velocity": round_float(velocity_for(note, profile, tick_map, pace), 3),
        "params": dict(profile.params),
        "performance": performance,
    }
    if note.phrase_end and note.breath_after_ms >= 35.0:
        event["comment"] = (
            f"樂句尾；下一次進音前保留 {note.breath_after_ms:.1f} ms 呼吸。"
        )
    return event


def score_document(
    midi_path: Path,
    season: str,
    movement: dict[str, Any],
) -> dict[str, Any]:
    midi = mido.MidiFile(midi_path)
    tick_map = TickMap(midi)
    notes = extract_notes(midi, set(TRACK_PROFILES))
    add_timing_and_articulation(notes, tick_map, movement["pace"])

    piece_end = max(
        tick_map.seconds(max(note.end_tick for note in notes)),
        midi.length,
    )
    role_for = {name: profile.role for name, profile in TRACK_PROFILES.items()}
    rests = make_rests(notes, piece_end, tick_map, role_for)
    phrases = make_phrases(notes, rests, piece_end, role_for)

    season_title, rv, opus_number = SEASON_META[season]
    movement_number = movement["number"]
    score_id = f"vivaldi_four_seasons_{season}_m{movement_number}"
    events = [
        event_record(
            note,
            TRACK_PROFILES[note.track],
            tick_map,
            movement["pace"],
            movement["key"],
        )
        for note in sorted(
            notes,
            key=lambda n: (
                n.start_sec,
                list(TRACK_PROFILES).index(n.track),
                n.note,
                n.end_sec,
            ),
        )
    ]

    active_profiles = {
        name: {
            "role": profile.role,
            "label": profile.label,
            "engine": profile.engine,
            **profile.params,
            "base_velocity": profile.base_velocity,
        }
        for name, profile in TRACK_PROFILES.items()
        if any(note.track == name for note in notes)
    }

    first_tempo = tempo_map(tick_map)[0]["quarter_bpm"]
    is_slow = movement["pace"] == "slow"
    return {
        "$schema": "TsukiSynth Score v1",
        "meta": {
            "title": (
                f"Vivaldi — The Four Seasons: {season_title}, "
                f"Movement {movement_number} ({movement['tempo_name']})"
            ),
            "id": score_id,
            "author": "Antonio Vivaldi; physical-model transcription by Codex",
            "composer": "Antonio Vivaldi",
            "work": "Le quattro stagioni, Op. 8 Nos. 1–4",
            "catalogue": rv,
            "opus_number": f"Op. 8 No. {opus_number}",
            "movement_number": movement_number,
            "movement_name": movement["tempo_name"],
            "key": movement["key"],
            "description": movement["description"],
            "created": "2026-06-21",
            "tags": [
                "classical",
                "baroque",
                "vivaldi",
                "four-seasons",
                season,
                "physical-string",
                "explicit-rests",
                "phrase-breaths",
            ],
            "mood": movement["mood"],
            "use_case": "AI physical-model composition / accessible score rendering",
            "category": "classical_transcription",
            "worldview": "Vivaldi Four Seasons",
            "variation_of": None,
            "primary_type": "ambience",
            "sound_type": "oneshot",
            "family_id": f"vivaldi_four_seasons_{season}",
            "character": ["airy", "pulse"],
        },
        "source": {
            "score_source": "Mutopia Project performers' facsimile edition",
            "source_url": MUTOPIA_SOURCE_URLS[season],
            "source_midi_file": midi_path.name,
            "source_format": "LilyPond-generated Standard MIDI File",
            "license": MUTOPIA_LICENSE,
            "license_url": MUTOPIA_LICENSE_URL,
            "attribution": (
                "Mutopia Project score maintained by smailliw; source based on "
                "Performers' Facsimiles. Derived transcription shares alike."
            ),
            "editorial_note": (
                "Pitch, onset, note-off, rests, repeats, track roles, tempo and "
                "meter come from the source MIDI. Dynamics and physical bow-gap "
                "treatment are TsukiSynth interpretation data."
            ),
        },
        "global": {
            "bpm": first_tempo,
            "sample_rate": 48000,
            "master_volume": 0.68,
            "effects": {
                "reverb": {
                    "decay": 2.8 if is_slow else 2.1,
                    "wet": 0.28 if is_slow else 0.20,
                },
                "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                "distortion": {
                    "type": "overdrive",
                    "drive": 0,
                    "instability": 0,
                    "wet": 0,
                },
            },
        },
        "tempo_map": tempo_map(tick_map),
        "time_signatures": time_signatures(midi, tick_map),
        "track_profiles": active_profiles,
        "timing_policy": {
            "time_unit": "seconds",
            "source_timing": "MIDI note-on/note-off converted through tempo map",
            "renderer_note_off_ratio": 0.9,
            "duration_compensation": (
                "event.duration = intended sounding duration / 0.9 so the C++ "
                "renderer damper begins at the intended release time"
            ),
            "silence_representation": (
                "No fake rest notes. Silence is absence of events; rests[] and "
                "performance.breath_after_ms expose it explicitly."
            ),
            "articulation_policy": (
                "Notated rests are untouched. Contiguous notes receive a small "
                "bow-change gap; rapid repeated notes receive a larger detached gap."
            ),
        },
        "events": events,
        "rests": rests,
        "phrases": phrases,
        "export": {
            "filename": score_id,
            "export_filename": (
                f"Classical_Vivaldi_{season.title()}_Movement{movement_number}"
            ),
            "format": "wav",
            "bit_depth": 24,
            "normalize": True,
            "tail_silence_ms": 900 if is_slow else 600,
            "start_position": 0,
            "end_position": 1,
        },
    }


def generic_piano_score_document(
    midi_path: Path,
    *,
    score_id: str,
    title: str,
    engine: str = "piano",
    profile_set_name: str = "piano_two_hand",
    composer: str | None = None,
    work: str | None = None,
    key: str = "C major",
    mood: str = "neutral",
    pace: str = "moderate",
    description: str = "",
    tags: list[str] | None = None,
    family_id: str | None = None,
    created: str | None = None,
    variation_of: str | None = None,
    reverb_decay: float = 2.2,
    reverb_wet: float = 0.20,
    master_volume: float = 0.75,
    sample_rate: int = 48000,
    tail_silence_ms: int = 900,
    source_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generic single/dual-track MIDI -> TsukiSynth Score v1 converter.

    Added 2026-08-28 (reports/decision_packets/CLASSICAL_RELICENSE_PLAN.md
    Sec.3/Sec.4, Fur Elise being the first clean-source relicense target)
    to generalise the previously Vivaldi-only pipeline: reuses TickMap,
    extract_notes, add_timing_and_articulation, make_rests, make_phrases,
    velocity_for, time_signatures, tempo_map, event_record and
    validate_score/write_score exactly as `score_document()` (the
    four-seasons path) does, parameterised instead of hard-coded to
    Vivaldi's movement/season metadata. `score_document()` itself is
    UNCHANGED by this addition (see CLASSICAL_RELICENSE_PLAN.md execution
    notes: full 12-movement regeneration diffed byte-for-byte against a
    pre-refactor baseline).

    `style="piano"` is used for articulation labelling (see
    ARTICULATION_STYLE_LABELS) so a struck-piano transcription doesn't
    claim bowed-string articulation ("bow_change" etc.).
    """
    if engine not in {"piano", "cimbalom", "string"}:
        raise ValueError(f"unsupported engine for generic piano conversion: {engine}")
    profile_set = PROFILE_SETS[profile_set_name]
    # Only the engine field is overridden per the CLI --engine choice; the
    # params dict (material/diameter_mm) is schema-valid and physically
    # identical across string/cimbalom/piano (see PIANO_HAND_PROFILES
    # docstring), so no per-engine param table is needed.
    active_profile_set = {
        name: dataclass_replace(profile, engine=engine)
        for name, profile in profile_set.items()
    }

    midi = mido.MidiFile(midi_path)
    tick_map = TickMap(midi)
    notes = extract_notes(midi, set(active_profile_set))
    if not notes:
        raise ValueError(
            f"{midi_path}: no notes extracted -- track names did not match "
            f"profile set {profile_set_name!r} ({sorted(active_profile_set)}). "
            "Inspect the MIDI's track_name meta events."
        )
    add_timing_and_articulation(notes, tick_map, pace, style="piano")

    piece_end = max(
        tick_map.seconds(max(note.end_tick for note in notes)),
        midi.length,
    )
    role_for = {name: profile.role for name, profile in active_profile_set.items()}
    rests = make_rests(notes, piece_end, tick_map, role_for)
    phrases = make_phrases(notes, rests, piece_end, role_for)

    events = [
        event_record(note, active_profile_set[note.track], tick_map, pace, key)
        for note in sorted(
            notes,
            key=lambda n: (
                n.start_sec,
                list(active_profile_set).index(n.track),
                n.note,
                n.end_sec,
            ),
        )
    ]

    active_profiles = {
        name: {
            "role": profile.role,
            "label": profile.label,
            "engine": profile.engine,
            **profile.params,
            "base_velocity": profile.base_velocity,
        }
        for name, profile in active_profile_set.items()
        if any(note.track == name for note in notes)
    }

    first_tempo = tempo_map(tick_map)[0]["quarter_bpm"]
    author = (
        f"{composer}; physical-model transcription by TsukiSynth pipeline"
        if composer
        else "TsukiSynth classical transcription pipeline"
    )
    meta: dict[str, Any] = {
        "title": title,
        "id": score_id,
        "author": author,
        "key": key,
        "description": description,
        "mood": mood,
        "use_case": "AI physical-model composition / accessible score rendering",
        "category": "classical_transcription",
        "variation_of": variation_of,
        "primary_type": "ambience",
        "sound_type": "oneshot",
        "character": ["soft", "airy"],
    }
    if composer is not None:
        meta["composer"] = composer
    if work is not None:
        meta["work"] = work
    if tags is not None:
        meta["tags"] = tags
    if family_id is not None:
        meta["family_id"] = family_id
    if created is not None:
        meta["created"] = created

    score: dict[str, Any] = {
        "$schema": "TsukiSynth Score v1",
        "meta": meta,
        "global": {
            "bpm": first_tempo,
            "sample_rate": sample_rate,
            "master_volume": master_volume,
            "effects": {
                "reverb": {"decay": reverb_decay, "wet": reverb_wet},
                "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                "distortion": {
                    "type": "overdrive",
                    "drive": 0,
                    "instability": 0,
                    "wet": 0,
                },
            },
        },
        "tempo_map": tempo_map(tick_map),
        "time_signatures": time_signatures(midi, tick_map),
        "track_profiles": active_profiles,
        "timing_policy": {
            "time_unit": "seconds",
            "source_timing": "MIDI note-on/note-off converted through tempo map",
            "renderer_note_off_ratio": 0.9,
            "duration_compensation": (
                "event.duration = intended sounding duration / 0.9 so the C++ "
                "renderer damper begins at the intended release time"
            ),
            "silence_representation": (
                "No fake rest notes. Silence is absence of events; rests[] and "
                "performance.breath_after_ms expose it explicitly."
            ),
            "articulation_policy": (
                "Notated rests are untouched. Contiguous notes receive a small "
                "finger-release gap; rapid repeated notes receive a larger "
                "detached-touch gap (labels use ARTICULATION_STYLE_LABELS "
                "'piano' set -- no bowed-string vocabulary)."
            ),
        },
        "events": events,
        "rests": rests,
        "phrases": phrases,
        "export": {
            "filename": score_id,
            "format": "wav",
            "bit_depth": 24,
            "normalize": True,
            "tail_silence_ms": tail_silence_ms,
            "start_position": 0,
            "end_position": 1,
        },
    }
    if source_info is not None:
        score["source"] = source_info
    return score


def validate_score(score: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    events = score.get("events", [])
    if not events:
        errors.append("no events")
        return errors
    previous = -1.0
    for index, event in enumerate(events):
        time = event["time"]
        duration = event["duration"]
        if not math.isfinite(time) or time < 0:
            errors.append(f"event {index}: invalid time")
        if not math.isfinite(duration) or duration <= 0:
            errors.append(f"event {index}: invalid duration")
        if time < previous:
            errors.append(f"event {index}: events are not sorted")
        previous = time
        release = time + duration * 0.9
        intended = event["performance"]["intended_release_time"]
        if abs(release - intended) > 0.000_01:
            errors.append(f"event {index}: renderer release mismatch")
    for index, rest in enumerate(score.get("rests", [])):
        if rest["duration"] < 0.035:
            errors.append(f"rest {index}: below declared rest threshold")
    return errors


def write_score(score: dict[str, Any], output: Path) -> None:
    errors = validate_score(score)
    if errors:
        raise ValueError("; ".join(errors[:20]))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(score, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def generate_four_seasons(source_dir: Path, output_dir: Path) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for season, movements in FOUR_SEASONS.items():
        for movement in movements:
            midi_path = source_dir / season / movement["file"]
            if not midi_path.is_file():
                raise FileNotFoundError(midi_path)
            score = score_document(midi_path, season, movement)
            output = (
                output_dir
                / season
                / f"vivaldi_four_seasons_{season}_m{movement['number']}.score.json"
            )
            write_score(score, output)
            summary.append(
                {
                    "id": score["meta"]["id"],
                    "season": season,
                    "movement": movement["number"],
                    "tempo_name": movement["tempo_name"],
                    "bpm": score["global"]["bpm"],
                    "time_signatures": score["time_signatures"],
                    "events": len(score["events"]),
                    "rests": len(score["rests"]),
                    "phrases": len(score["phrases"]),
                    "duration_sec": round_float(
                        max(
                            event["performance"]["intended_release_time"]
                            for event in score["events"]
                        )
                    ),
                    "score_file": output.relative_to(output_dir).as_posix(),
                    "source_url": MUTOPIA_SOURCE_URLS[season],
                    "license": MUTOPIA_LICENSE,
                }
            )

    catalog = {
        "$schema": "TsukiSynth Classical Score Catalog v1",
        "title": "Antonio Vivaldi — The Four Seasons",
        "generated": "2026-06-21",
        "description": (
            "Twelve movement-level TsukiSynth physical-string transcriptions "
            "with explicit rests, phrase boundaries and breath intervals."
        ),
        "license": MUTOPIA_LICENSE,
        "license_url": MUTOPIA_LICENSE_URL,
        "movements": summary,
    }
    catalog_path = output_dir / "vivaldi_four_seasons.catalog.json"
    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    batch = subparsers.add_parser(
        "four-seasons", help="Generate all 12 Vivaldi Four Seasons movements"
    )
    batch.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Directory containing spring/, summer/, autumn/, winter/ MIDI folders",
    )
    batch.add_argument("--output-dir", type=Path, required=True)

    convert = subparsers.add_parser(
        "convert",
        help=(
            "Generic single/dual-track MIDI -> TsukiSynth Score v1 "
            "(e.g. a single-work piano transcription; see generic_piano_"
            "score_document())"
        ),
    )
    convert.add_argument("midi", type=Path, help="Source MIDI file")
    convert.add_argument("--output", type=Path, required=True, help="Output .score.json path")
    convert.add_argument("--profile", choices=sorted(PROFILE_SETS), default="piano_two_hand")
    convert.add_argument("--engine", choices=["piano", "cimbalom", "string"], default="piano")
    convert.add_argument("--id", dest="score_id", required=True)
    convert.add_argument("--title", required=True)
    convert.add_argument("--composer")
    convert.add_argument("--work")
    convert.add_argument("--key", default="C major")
    convert.add_argument(
        "--mood",
        default="neutral",
        choices=[
            "sacred", "mystical", "tense", "ominous", "playful", "calm",
            "epic", "melancholic", "neutral", "aggressive", "oppressive",
        ],
    )
    convert.add_argument("--pace", default="moderate")
    convert.add_argument("--description", default="")
    convert.add_argument("--tags", nargs="*", default=None)
    convert.add_argument("--family-id", dest="family_id")
    convert.add_argument("--created", default=None, help="ISO date, e.g. 2026-08-28")
    convert.add_argument("--variation-of", dest="variation_of", default=None)
    convert.add_argument("--reverb-decay", type=float, default=2.2)
    convert.add_argument("--reverb-wet", type=float, default=0.20)
    convert.add_argument("--master-volume", type=float, default=0.75)
    convert.add_argument("--sample-rate", type=int, default=48000)
    convert.add_argument("--tail-silence-ms", type=int, default=900)
    convert.add_argument("--source-url")
    convert.add_argument("--source-score-source")
    convert.add_argument("--source-format")
    convert.add_argument("--source-license")
    convert.add_argument("--source-license-url")
    convert.add_argument("--source-attribution")
    convert.add_argument("--source-editorial-note")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command == "four-seasons":
        summary = generate_four_seasons(args.source_dir, args.output_dir)
        total_events = sum(row["events"] for row in summary)
        total_rests = sum(row["rests"] for row in summary)
        print(
            f"Generated {len(summary)} movements: "
            f"{total_events} events, {total_rests} explicit rests"
        )
    elif args.command == "convert":
        source_fields = {
            "score_source": args.source_score_source,
            "source_url": args.source_url,
            "source_midi_file": args.midi.name,
            "source_format": args.source_format,
            "license": args.source_license,
            "license_url": args.source_license_url,
            "attribution": args.source_attribution,
            "editorial_note": args.source_editorial_note,
        }
        source_info = {k: v for k, v in source_fields.items() if v is not None}
        score = generic_piano_score_document(
            args.midi,
            score_id=args.score_id,
            title=args.title,
            engine=args.engine,
            profile_set_name=args.profile,
            composer=args.composer,
            work=args.work,
            key=args.key,
            mood=args.mood,
            pace=args.pace,
            description=args.description,
            tags=args.tags,
            family_id=args.family_id,
            created=args.created,
            variation_of=args.variation_of,
            reverb_decay=args.reverb_decay,
            reverb_wet=args.reverb_wet,
            master_volume=args.master_volume,
            sample_rate=args.sample_rate,
            tail_silence_ms=args.tail_silence_ms,
            source_info=source_info or None,
        )
        write_score(score, args.output)
        print(
            f"Generated {args.output}: {len(score['events'])} events, "
            f"{len(score['rests'])} explicit rests, {len(score['phrases'])} phrases"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
