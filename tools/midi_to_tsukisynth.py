#!/usr/bin/env python3
"""
Convert standard MIDI into TsukiSynth Score v1 JSON.

The converter preserves source note-on/note-off timing, then adds a small,
documented physical-articulation gap where consecutive notes would otherwise
touch exactly.  Rests and phrase breaths are emitted explicitly for AI and
non-auditory inspection while remaining harmless to the current C++ renderer.

Requires:
    pip install mido

Four Seasons batch mode expects the Mutopia MIDI folders:
    spring/spring-score.mid, spring/spring-score-1.mid, ...
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from dataclasses import dataclass
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
    role: str
    label: str
    base_velocity: float
    diameter_mm: float
    strike_position: float
    damping: float


TRACK_PROFILES = {
    "solo": TrackProfile(
        role="solo_violin",
        label="Violino principale",
        base_velocity=0.72,
        diameter_mm=0.55,
        strike_position=0.18,
        damping=0.34,
    ),
    "violinone": TrackProfile(
        role="violin_1",
        label="Violino primo",
        base_velocity=0.50,
        diameter_mm=0.62,
        strike_position=0.22,
        damping=0.40,
    ),
    "violintwo": TrackProfile(
        role="violin_2",
        label="Violino secondo",
        base_velocity=0.45,
        diameter_mm=0.68,
        strike_position=0.24,
        damping=0.44,
    ),
    "viola": TrackProfile(
        role="viola",
        label="Alto viola",
        base_velocity=0.42,
        diameter_mm=0.90,
        strike_position=0.28,
        damping=0.48,
    ),
    "cello": TrackProfile(
        role="cello_continuo",
        label="Violoncello / continuo",
        base_velocity=0.47,
        diameter_mm=1.45,
        strike_position=0.32,
        damping=0.52,
    ),
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
            return message.name.strip().lower()
    return f"track_{index}"


def extract_notes(midi: mido.MidiFile) -> list[MidiNote]:
    notes: list[MidiNote] = []
    for index, track in enumerate(midi.tracks[1:], start=1):
        name = track_name(track, index)
        if name not in TRACK_PROFILES:
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


def articulation_gap_seconds(
    note: MidiNote,
    next_onset_tick: int | None,
    tick_map: TickMap,
    pace: str,
    same_pitch_at_next: bool,
) -> tuple[float, str]:
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
        return min(0.012, source_duration * 0.07), "short_bow"
    if pace in {"fast", "dance"}:
        return min(0.018, source_duration * 0.08), "detached_bow"
    if pace == "slow":
        return min(0.032, source_duration * 0.05), "long_bow_change"
    return min(0.022, source_duration * 0.07), "bow_change"


def add_timing_and_articulation(
    notes: list[MidiNote], tick_map: TickMap, pace: str
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
                note, next_onset_tick, tick_map, pace, same_pitch
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
    notes: list[MidiNote], piece_end: float, tick_map: TickMap
) -> list[dict[str, Any]]:
    by_track: dict[str, list[MidiNote]] = collections.defaultdict(list)
    for note in notes:
        by_track[note.track].append(note)

    rests: list[dict[str, Any]] = []
    for track, track_notes in sorted(by_track.items()):
        intervals = merged_intervals(track_notes)
        cursor = 0.0
        for start, end in intervals:
            if start - cursor >= 0.035:
                rests.append(rest_record(track, cursor, start, tick_map))
            cursor = max(cursor, end)
        if piece_end - cursor >= 0.035:
            rests.append(rest_record(track, cursor, piece_end, tick_map))
    return rests


def rest_record(
    track: str, start: float, end: float, tick_map: TickMap
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
        "role": TRACK_PROFILES[track].role,
        "time": round_float(start),
        "duration": round_float(duration),
        "approx_quarter_beats": round_float(duration / quarter, 3),
        "kind": kind,
    }


def make_phrases(
    notes: list[MidiNote], rests: list[dict[str, Any]], piece_end: float
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
                        "role": TRACK_PROFILES[track].role,
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
                    "role": TRACK_PROFILES[track].role,
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
        "engine": "string",
        "note": note_name(note.note, key),
        "velocity": round_float(velocity_for(note, profile, tick_map, pace), 3),
        "params": {
            "material": "steel",
            "diameter_mm": profile.diameter_mm,
            "strike_position": profile.strike_position,
            "exciter": "bow",
            "damping_override": profile.damping,
        },
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
    notes = extract_notes(midi)
    add_timing_and_articulation(notes, tick_map, movement["pace"])

    piece_end = max(
        tick_map.seconds(max(note.end_tick for note in notes)),
        midi.length,
    )
    rests = make_rests(notes, piece_end, tick_map)
    phrases = make_phrases(notes, rests, piece_end)

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
            "engine": "string",
            "material": "steel",
            "diameter_mm": profile.diameter_mm,
            "strike_position": profile.strike_position,
            "exciter": "bow",
            "damping_override": profile.damping,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
