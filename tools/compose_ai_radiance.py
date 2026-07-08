#!/usr/bin/env python3
"""Compose the deterministic multi-engine suite "AI Radiance / 光之驗算"."""

from __future__ import annotations

import collections
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCORE_DIR = ROOT / "scores" / "originals" / "ai_radiance"

NOTE_TO_PC = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}


def midi(note: str) -> int:
    if note[1:2] in {"#", "b"}:
        name, octave = note[:2], int(note[2:])
    else:
        name, octave = note[:1], int(note[1:])
    return (octave + 1) * 12 + NOTE_TO_PC[name]


def hz(note: str) -> float:
    return 440.0 * 2.0 ** ((midi(note) - 69) / 12.0)


def r(value: float, digits: int = 6) -> float:
    return round(value, digits)


def event(
    time: float,
    sounding_duration: float,
    engine: str,
    note: str,
    velocity: float,
    params: dict[str, Any],
    role: str,
    articulation: str,
    comment: str = "",
    glide: dict[str, Any] | None = None,
) -> dict[str, Any]:
    intended_release = time + sounding_duration
    result: dict[str, Any] = {
        "time": r(time),
        "duration": r(sounding_duration / 0.9, 8),
        "engine": engine,
        "note": note,
        "velocity": r(velocity, 3),
        "params": params,
        "performance": {
            "role": role,
            "midi_note": midi(note),
            "frequency_hz": r(hz(note), 3),
            "intended_release_time": r(intended_release),
            "articulation": articulation,
            "phrase_end": False,
            "breath_after_ms": 0.0,
        },
    }
    if comment:
        result["comment"] = comment
    if glide:
        result["glide"] = glide
    return result


def cimbalom(
    time: float,
    duration: float,
    note: str,
    velocity: float,
    role: str,
    *,
    material: str = "steel",
    diameter: float = 0.68,
    strike: float = 0.22,
    exciter: str = "wood_mallet",
    damping: float = 0.42,
    articulation: str = "hammered",
    comment: str = "",
) -> dict[str, Any]:
    return event(
        time,
        duration,
        "cimbalom",
        note,
        velocity,
        {
            "material": material,
            "diameter_mm": diameter,
            "strike_position": strike,
            "exciter": exciter,
            "damping_override": damping,
        },
        role,
        articulation,
        comment,
    )


def tongue(
    time: float,
    duration: float,
    note: str,
    velocity: float,
    role: str,
    *,
    material: str = "steel",
    thickness: float = 2.5,
    length: float = 72.0,
    width: float = 24.0,
    strike: float = 0.42,
    exciter: str = "finger",
    articulation: str = "soft_tap",
    comment: str = "",
    glide: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return event(
        time,
        duration,
        "tongue_drum",
        note,
        velocity,
        {
            "material": material,
            "thickness_mm": thickness,
            "length_mm": length,
            "width_mm": width,
            "strike_position": strike,
            "exciter": exciter,
        },
        role,
        articulation,
        comment,
        glide,
    )


def gong(
    time: float,
    duration: float,
    note: str,
    velocity: float,
    role: str,
    *,
    material: str = "bronze",
    thickness: float = 3.5,
    radius: float = 180.0,
    strike: float = 0.34,
    exciter: str = "felt_mallet",
    free_edge: bool = True,
    articulation: str = "resonant_strike",
    comment: str = "",
    glide: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return event(
        time,
        duration,
        "water_gong",
        note,
        velocity,
        {
            "material": material,
            "thickness_mm": thickness,
            "radius_mm": radius,
            "strike_position": strike,
            "exciter": exciter,
            "plate_free_edge": free_edge,
        },
        role,
        articulation,
        comment,
        glide,
    )


def custom(
    time: float,
    duration: float,
    note: str,
    velocity: float,
    role: str,
    *,
    material: str = "glass",
    strike: float = 0.31,
    exciter: str = "metal_tip",
    articulation: str = "spectral_flash",
    comment: str = "",
) -> dict[str, Any]:
    return event(
        time,
        duration,
        "custom",
        note,
        velocity,
        {
            "material": material,
            "strike_position": strike,
            "exciter": exciter,
        },
        role,
        articulation,
        comment,
    )


def fm(
    time: float,
    duration: float,
    note: str,
    velocity: float,
    role: str,
    *,
    preset: int,
    ratio: float,
    index: float,
    brightness: float,
    feedback: float,
    attack: float,
    release: float,
    articulation: str = "spectral_tone",
    comment: str = "",
    glide: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return event(
        time,
        duration,
        "fm",
        note,
        velocity,
        {
            "fm_preset": preset,
            "fm_ratio": ratio,
            "fm_index": index,
            "fm_brightness": brightness,
            "fm_feedback": feedback,
            "fm_attack": attack,
            "fm_release": release,
        },
        role,
        articulation,
        comment,
        glide,
    )


def add_accessibility_timing(
    events: list[dict[str, Any]], piece_end: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_role: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for item in events:
        by_role[item["performance"]["role"]].append(item)

    rests: list[dict[str, Any]] = []
    phrases: list[dict[str, Any]] = []
    for role, role_events in sorted(by_role.items()):
        groups: dict[float, list[dict[str, Any]]] = collections.defaultdict(list)
        for item in role_events:
            groups[item["time"]].append(item)
        onsets = sorted(groups)
        phrase_start = onsets[0]
        phrase_number = 1

        if phrase_start >= 0.05:
            rests.append(
                {
                    "track": role,
                    "role": role,
                    "time": 0.0,
                    "duration": r(phrase_start),
                    "kind": "entrance_rest",
                }
            )

        for index, onset in enumerate(onsets):
            group = groups[onset]
            group_end = max(
                item["performance"]["intended_release_time"] for item in group
            )
            next_onset = onsets[index + 1] if index + 1 < len(onsets) else piece_end
            silence = max(0.0, next_onset - group_end)
            for item in group:
                item["performance"]["breath_after_ms"] = r(silence * 1000.0, 3)
                item["performance"]["phrase_end"] = silence >= 0.24

            if silence >= 0.04:
                kind = "breath" if silence < 0.32 else "rest" if silence < 2.0 else "long_rest"
                rests.append(
                    {
                        "track": role,
                        "role": role,
                        "time": r(group_end),
                        "duration": r(silence),
                        "kind": kind,
                    }
                )
            if silence >= 0.24:
                phrases.append(
                    {
                        "track": role,
                        "role": role,
                        "number": phrase_number,
                        "start": r(phrase_start),
                        "end": r(group_end),
                        "breath_after_ms": r(silence * 1000.0, 3),
                    }
                )
                phrase_number += 1
                phrase_start = next_onset

        last_end = max(
            item["performance"]["intended_release_time"] for item in role_events
        )
        if not phrases or phrases[-1]["end"] < last_end - 0.01:
            phrases.append(
                {
                    "track": role,
                    "role": role,
                    "number": phrase_number,
                    "start": r(phrase_start),
                    "end": r(last_end),
                    "breath_after_ms": 0.0,
                }
            )
    return rests, phrases


def score(
    *,
    number: int,
    title: str,
    subtitle: str,
    bpm: float,
    meter: str,
    key: str,
    duration: float,
    events: list[dict[str, Any]],
    effects: dict[str, Any],
    thesis: str,
) -> dict[str, Any]:
    events.sort(
        key=lambda item: (
            item["time"],
            item["performance"]["role"],
            item["performance"]["midi_note"],
        )
    )
    rests, phrases = add_accessibility_timing(events, duration)
    return {
        "$schema": "TsukiSynth Score v1",
        "meta": {
            "title": f"AI Radiance / 光之驗算 — {number}. {title}",
            "id": f"ai_radiance_m{number}",
            "author": "Codex",
            "composer": "Codex",
            "work": "AI Radiance / 光之驗算",
            "movement_number": number,
            "movement_name": title,
            "key": key,
            "description": subtitle,
            "created": "2026-06-22",
            "tags": [
                "ai-original",
                "physical-model",
                "cimbalom",
                "tongue-drum",
                "water-gong",
                "multi-engine",
                "accessible-score",
            ],
            "mood": "mystical",
            "use_case": "AI original concert work / physical synthesis demonstration",
            "category": "original_composition",
            "worldview": "AI Radiance",
            "variation_of": None,
            "primary_type": "magic",
            "sound_type": "oneshot",
            "family_id": "ai_radiance",
            "character": ["airy", "metallic", "pulse"],
        },
        "composition_thesis": thesis,
        "global": {
            "bpm": bpm,
            "sample_rate": 48000,
            "master_volume": 0.52,
            "effects": effects,
        },
        "tempo_map": [{"time": 0.0, "quarter_bpm": bpm}],
        "time_signatures": [
            {
                "time": 0.0,
                "numerator": int(meter.split("/")[0]),
                "denominator": int(meter.split("/")[1]),
            }
        ],
        "timing_policy": {
            "time_unit": "seconds",
            "renderer_note_off_ratio": 0.9,
            "duration_compensation": "event.duration = intended sounding duration / 0.9",
            "silence_representation": "rests[] plus absence of events",
        },
        "events": events,
        "rests": rests,
        "phrases": phrases,
        "export": {
            "filename": f"ai_radiance_m{number}",
            "export_filename": f"Original_AI_Radiance_Movement{number}",
            "format": "wav",
            "bit_depth": 24,
            "normalize": True,
            "tail_silence_ms": 1200,
        },
    }


def movement_one() -> dict[str, Any]:
    beat = 60.0 / 72.0
    events: list[dict[str, Any]] = []
    pattern = ["E4", "B4", "F#5", "G#4", "C#5", "B4", "E5", "F#4"]
    for step in range(32):
        t = step * beat * 0.5
        note = pattern[step % len(pattern)]
        events.append(
            cimbalom(
                t,
                beat * 0.38,
                note,
                0.48 + 0.06 * (step % 4 == 0),
                "yangqin_lattice",
                diameter=0.52 + 0.04 * (step % 3),
                strike=0.16 + 0.035 * (step % 4),
                damping=0.46 + 0.08 * (step % 2),
                exciter="wood_mallet" if step % 4 else "metal_mallet",
                articulation="alternating_hammer",
            )
        )
        if step % 2 == 1:
            echo_note = ["E5", "F#5", "B5", "G#5"][step % 4]
            events.append(
                tongue(
                    t + beat * 0.17,
                    beat * 0.7,
                    echo_note,
                    0.28 + 0.025 * (step % 3),
                    "ethereal_echo",
                    material="steel" if step < 16 else "glass",
                    thickness=2.2 + 0.25 * (step % 3),
                    length=76 - 4 * (step % 4),
                    width=22 + 2 * (step % 2),
                    strike=0.38 + 0.04 * (step % 3),
                    exciter="finger",
                )
            )

    for t, note, radius in [
        (0.0, "E2", 260),
        (8 * beat, "B1", 315),
        (16 * beat, "C#2", 290),
        (24 * beat, "E2", 340),
    ]:
        events.append(
            gong(
                t,
                5.8,
                note,
                0.22,
                "bronze_horizon",
                material="bronze",
                thickness=5.2,
                radius=radius,
                strike=0.49,
                exciter="cotton_mallet",
                comment="自由邊界圓板作為低頻時間地平線。",
            )
        )

    for t, chord in [
        (4 * beat, ["E5", "G#5", "B5"]),
        (12 * beat, ["F#5", "B5", "C#6"]),
        (20 * beat, ["G#5", "B5", "E6"]),
        (28 * beat, ["E5", "B5", "F#6"]),
    ]:
        for note in chord:
            events.append(
                custom(
                    t,
                    3.4,
                    note,
                    0.16,
                    "glass_constellation",
                    material="glass",
                    strike=0.27,
                    exciter="metal_tip",
                )
            )

    return score(
        number=1,
        title="露珠格點 / Dew Lattice",
        subtitle="揚琴的離散攻擊穿過空靈鼓長尾；每四拍由自由邊界青銅板重新定義空間。",
        bpm=72,
        meter="4/4",
        key="E Lydian / E major field",
        duration=27.0,
        events=events,
        effects={
            "reverb": {"decay": 5.2, "wet": 0.42},
            "delay": {"time_ms": 416.667, "feedback": 0.18, "wet": 0.09},
            "wall": {"distance_m": 9.0, "material": "glass"},
            "distortion": {
                "type": "overdrive",
                "drive": 0.0,
                "instability": 0.0,
                "wet": 0.0,
            },
        },
        thesis="相同十二平均律基頻交給弦、梁與圓板後，各自展開不同非諧波模態；和聲由物理體的衰減交疊形成。",
    )


def movement_two() -> dict[str, Any]:
    beat = 60.0 / 112.0
    events: list[dict[str, Any]] = []
    low_cycle = ["G1", "D2", "F2", "C2", "Eb2", "D2"]
    for bar in range(12):
        t = bar * beat * 3
        low = low_cycle[bar % len(low_cycle)]
        events.append(
            gong(
                t,
                beat * 2.5,
                low,
                0.40 + 0.025 * (bar % 3),
                "storm_plate",
                material="copper" if bar % 2 else "bronze",
                thickness=2.0 + 0.35 * (bar % 4),
                radius=190 + 22 * (bar % 5),
                strike=0.12 + 0.06 * (bar % 4),
                exciter="metal_mallet" if bar % 3 == 0 else "felt_mallet",
                glide={
                    "from_note": ["D1", "Bb1", "G1"][bar % 3],
                    "duration_ms": 240 + 35 * (bar % 4),
                    "curve": "exponential",
                },
                comment="圓板起始頻率沿指數曲線收斂至目標音高。",
            )
        )

        burst = ["G4", "Bb4", "D5", "F5", "Eb5", "C5"]
        for hit in range(6):
            tt = t + hit * beat * 0.42
            events.append(
                cimbalom(
                    tt,
                    beat * 0.24,
                    burst[(hit + bar) % len(burst)],
                    0.55 + 0.05 * ((hit + bar) % 3),
                    "charged_yangqin",
                    material="steel",
                    diameter=0.46 + 0.08 * (hit % 4),
                    strike=0.08 + 0.055 * (hit % 5),
                    exciter="metal_hammer",
                    damping=0.72 + 0.18 * (hit % 2),
                    articulation="electric_hammer_burst",
                )
            )

        if bar % 2 == 0:
            for offset, note in [(0.18, "D6"), (0.71, "G5"), (1.13, "Bb5")]:
                events.append(
                    custom(
                        t + offset * beat,
                        beat * 1.3,
                        note,
                        0.20,
                        "inharmonic_lightning",
                        material="aluminum" if bar < 6 else "glass",
                        strike=0.16,
                        exciter="metal_tip",
                    )
                )

    for bar in [1, 4, 7, 10]:
        t = bar * beat * 3 + beat
        events.append(
            fm(
                t,
                beat * 1.8,
                ["G3", "Bb3", "D4", "F4"][bar % 4],
                0.30,
                "fm_warning_beacon",
                preset=3,
                ratio=7.0 + (bar % 3),
                index=7.5 + bar * 0.2,
                brightness=0.78,
                feedback=0.16,
                attack=3,
                release=900,
                articulation="bell_beacon",
            )
        )

    return score(
        number=2,
        title="方程風暴 / Storm of Equations",
        subtitle="水鑼滑頻構成壓力場，金屬揚琴以非對稱六連擊放電，自訂泛音與 FM 鐘作為閃電。",
        bpm=112,
        meter="3/4",
        key="G minor / chromatic pressure field",
        duration=20.5,
        events=events,
        effects={
            "reverb": {"decay": 6.4, "wet": 0.46},
            "delay": {"time_ms": 267.857, "feedback": 0.31, "wet": 0.14},
            "wall": {"distance_m": 14.0, "material": "stone"},
            "distortion": {
                "type": "wavefold",
                "drive": 0.18,
                "instability": 0.12,
                "wet": 0.16,
            },
        },
        thesis="以滑頻圓板的模態收斂對抗高阻尼弦的脈衝；密度衝突取代傳統主旋律。",
    )


def movement_three() -> dict[str, Any]:
    beat = 60.0 / 64.0
    events: list[dict[str, Any]] = []
    chords = [
        ["F3", "A3", "C4", "E4"],
        ["G3", "Bb3", "D4", "F4"],
        ["A3", "C4", "E4", "G4"],
        ["C3", "G3", "Bb3", "E4"],
        ["D3", "F3", "A3", "C4"],
        ["Bb2", "F3", "A3", "D4"],
        ["G2", "D3", "F3", "C4"],
        ["C3", "G3", "C4", "E4"],
    ]
    melody = [
        "A4",
        "C5",
        "E5",
        "D5",
        "C5",
        "A4",
        "G4",
        "C5",
        "F5",
        "E5",
        "C5",
        "A4",
        "D5",
        "C5",
        "G4",
        "F4",
    ]
    for bar, chord in enumerate(chords):
        t = bar * beat * 3
        for note_index, note in enumerate(chord):
            events.append(
                fm(
                    t + note_index * 0.018,
                    beat * 2.65,
                    note,
                    0.23 + note_index * 0.025,
                    "fm_memory_body",
                    preset=1,
                    ratio=1.0,
                    index=2.5 + 0.45 * (bar % 3),
                    brightness=0.32 + 0.04 * (bar % 2),
                    feedback=0.025,
                    attack=18,
                    release=1500,
                    articulation="slow_epiano_chord",
                )
            )

        for pulse in range(2):
            idx = bar * 2 + pulse
            mt = t + pulse * beat * 1.5 + beat * 0.22
            events.append(
                cimbalom(
                    mt,
                    beat * 0.92,
                    melody[idx],
                    0.42 + 0.04 * (idx % 4 == 0),
                    "remembering_yangqin",
                    material="steel",
                    diameter=0.58,
                    strike=0.27 + 0.025 * (idx % 3),
                    exciter="felt_mallet",
                    damping=0.28,
                    articulation="soft_memory_strike",
                )
            )
            events.append(
                tongue(
                    mt + beat * 0.36,
                    beat * 1.15,
                    ["F5", "C6", "A5", "E6"][idx % 4],
                    0.18,
                    "bamboo_afterimage",
                    material="bamboo",
                    thickness=1.8,
                    length=62 - 3 * (idx % 4),
                    width=16,
                    strike=0.50,
                    exciter="finger_tap",
                )
            )

    for t, note in [(0, "F2"), (6 * beat, "C2"), (12 * beat, "D2"), (18 * beat, "C2")]:
        events.append(
            gong(
                t,
                5.0,
                note,
                0.14,
                "distant_memory_plate",
                material="glass",
                thickness=6.0,
                radius=320,
                strike=0.52,
                exciter="cotton_mallet",
            )
        )

    return score(
        number=3,
        title="記憶果園 / Memory Orchard",
        subtitle="FM 電鋼琴提供精確諧波身體，柔槌揚琴說出旋律，竹空靈鼓只留下記憶的倒影。",
        bpm=64,
        meter="3/4",
        key="F major with Lydian extensions",
        duration=24.0,
        events=events,
        effects={
            "reverb": {"decay": 4.6, "wet": 0.38},
            "delay": {"time_ms": 468.75, "feedback": 0.20, "wet": 0.11},
            "wall": {"distance_m": 7.5, "material": "wood"},
            "distortion": {
                "type": "overdrive",
                "drive": 0.0,
                "instability": 0.0,
                "wet": 0.0,
            },
        },
        thesis="可驗證的整數 FM 頻譜擔任穩定記憶；物理弦與竹梁則以非諧波衰減讓記憶逐步失真。",
    )


def movement_four() -> dict[str, Any]:
    beat = 60.0 / 84.0
    events: list[dict[str, Any]] = []
    crystal = ["F5", "C6", "Ab5", "Eb6", "G5", "Db6", "C6", "F6"]
    for step in range(32):
        t = step * beat * 0.5
        events.append(
            tongue(
                t,
                beat * (0.34 if step % 4 else 0.62),
                crystal[step % len(crystal)],
                0.30 + 0.045 * (step % 5 == 0),
                "glass_clock",
                material="glass",
                thickness=1.3 + 0.18 * (step % 4),
                length=48 - 2.5 * (step % 5),
                width=13 + (step % 3),
                strike=0.18 + 0.055 * (step % 5),
                exciter="metal_tip" if step % 4 == 0 else "finger_tap",
                articulation="crystal_tick",
            )
        )
        if step % 4 in {1, 3}:
            events.append(
                cimbalom(
                    t + beat * 0.11,
                    beat * 0.28,
                    ["F4", "C5", "Eb5", "Ab4"][step % 4],
                    0.48,
                    "frozen_yangqin",
                    material="steel",
                    diameter=0.44,
                    strike=0.07 + 0.03 * (step % 3),
                    exciter="metal_hammer",
                    damping=1.15,
                    articulation="ice_fragment",
                )
            )

    for bar, (note, from_note) in enumerate(
        [("F2", "C1"), ("Db2", "Ab1"), ("Eb2", "Bb1"), ("C2", "F1")]
    ):
        t = bar * beat * 8
        events.append(
            gong(
                t,
                6.2,
                note,
                0.26,
                "ice_shelf",
                material="glass" if bar % 2 == 0 else "bronze",
                thickness=7.5 - bar * 0.7,
                radius=360 - bar * 25,
                strike=0.46,
                exciter="felt_mallet",
                glide={
                    "from_note": from_note,
                    "duration_ms": 1200 + bar * 180,
                    "curve": "exponential",
                },
            )
        )
        for note2 in [["F3", "Ab3", "C4"], ["Db3", "F3", "Ab3"], ["Eb3", "G3", "Bb3"], ["C3", "E3", "G3"]][bar]:
            events.append(
                fm(
                    t + beat * 0.06,
                    beat * 6.8,
                    note2,
                    0.16,
                    "aurora_pad",
                    preset=5,
                    ratio=1.5 + 0.25 * bar,
                    index=1.4 + 0.3 * bar,
                    brightness=0.16,
                    feedback=0.08,
                    attack=780,
                    release=3800,
                    articulation="slow_aurora",
                )
            )

    final_t = beat * 16
    for i, note in enumerate(["F3", "C4", "G4", "A4", "E5", "B5"]):
        events.append(
            custom(
                final_t + i * 0.021,
                7.0,
                note,
                0.13 + i * 0.012,
                "radiant_finale",
                material="glass" if i % 2 == 0 else "bronze",
                strike=0.32,
                exciter="metal_tip",
                comment="非整數高次模態將終止和弦展開成光譜。",
            )
        )

    return score(
        number=4,
        title="零度星冠 / Crown at Absolute Zero",
        subtitle="玻璃空靈鼓成為時鐘，鋼揚琴碎成冰晶；水鑼與 FM pad 在終點融合成無調性星冠。",
        bpm=84,
        meter="4/4",
        key="F minor dissolving toward spectral C",
        duration=27.0,
        events=events,
        effects={
            "reverb": {"decay": 9.0, "wet": 0.58},
            "delay": {"time_ms": 357.143, "feedback": 0.29, "wet": 0.15},
            "wall": {"distance_m": 18.0, "material": "metal"},
            "distortion": {
                "type": "bitcrush",
                "drive": 0.08,
                "instability": 0.04,
                "wet": 0.06,
            },
        },
        thesis="用高阻尼弦製造離散時間，用低阻尼玻璃與圓板保存連續時間；終止式是衰減常數的統一，而非傳統主和弦。",
    )


def validate(document: dict[str, Any]) -> None:
    events = document["events"]
    assert events
    assert events == sorted(
        events,
        key=lambda item: (
            item["time"],
            item["performance"]["role"],
            item["performance"]["midi_note"],
        ),
    )
    for item in events:
        assert 0 <= item["velocity"] <= 1
        assert item["duration"] > 0
        assert 0 <= item["performance"]["midi_note"] <= 127
        calculated = item["time"] + item["duration"] * 0.9
        intended = item["performance"]["intended_release_time"]
        assert abs(calculated - intended) <= 0.000_002


def engine_summary(documents: list[dict[str, Any]]) -> dict[str, Any]:
    engines: collections.Counter[str] = collections.Counter()
    materials: collections.Counter[str] = collections.Counter()
    notes: list[int] = []
    for document in documents:
        for item in document["events"]:
            engines[item["engine"]] += 1
            material = item["params"].get("material")
            if material:
                materials[material] += 1
            notes.append(item["performance"]["midi_note"])
    return {
        "movements": len(documents),
        "events": sum(len(document["events"]) for document in documents),
        "rests": sum(len(document["rests"]) for document in documents),
        "phrases": sum(len(document["phrases"]) for document in documents),
        "engines": dict(engines),
        "materials": dict(materials),
        "midi_range": [min(notes), max(notes)],
        "frequency_range_hz": [r(440 * 2 ** ((min(notes) - 69) / 12), 3), r(440 * 2 ** ((max(notes) - 69) / 12), 3)],
    }


def main() -> None:
    SCORE_DIR.mkdir(parents=True, exist_ok=True)
    documents = [movement_one(), movement_two(), movement_three(), movement_four()]
    for document in documents:
        validate(document)
        number = document["meta"]["movement_number"]
        target = SCORE_DIR / f"ai_radiance_m{number}.score.json"
        target.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    master = {
        "$schema": "TsukiSynth Score v1",
        "meta": {
            "title": "AI Radiance / 光之驗算 — Complete Suite",
            "id": "ai_radiance_complete",
            "author": "Codex",
            "composer": "Codex",
            "work": "AI Radiance / 光之驗算",
            "description": "四個物理命題構成的原創多引擎協奏曲。",
            "created": "2026-06-22",
            "tags": ["ai-original", "multi-engine", "physical-model", "complete-suite"],
            "mood": "mystical",
            "use_case": "AI original concert work",
            "category": "original_composition",
            "worldview": "AI Radiance",
            "variation_of": None,
            "primary_type": "magic",
            "sound_type": "oneshot",
            "family_id": "ai_radiance",
            "character": ["airy", "metallic", "pulse"],
        },
        "global": {
            "bpm": 72,
            "sample_rate": 48000,
            "master_volume": 0.82,
            "effects": {
                "reverb": {"decay": 3.0, "wet": 0.12},
                "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                "distortion": {
                    "type": "overdrive",
                    "drive": 0,
                    "instability": 0,
                    "wet": 0,
                },
            },
        },
        "layers": [
            {"source": f"ai_radiance_m{number}.score.json", "region": [0.0, 1.0], "gain": 1.0}
            for number in range(1, 5)
        ],
        "crossfade_ms": 1400,
        "export": {
            "filename": "ai_radiance_complete",
            "export_filename": "Original_AI_Radiance_Complete",
            "format": "wav",
            "bit_depth": 24,
            "normalize": True,
            "tail_silence_ms": 1800,
        },
    }
    (SCORE_DIR / "ai_radiance_complete.score.json").write_text(
        json.dumps(master, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    catalog = {
        "$schema": "TsukiSynth Original Composition Catalog v1",
        "title": "AI Radiance / 光之驗算",
        "composer": "Codex",
        "created": "2026-06-22",
        "summary": engine_summary(documents),
        "movements": [
            {
                "number": document["meta"]["movement_number"],
                "title": document["meta"]["movement_name"],
                "events": len(document["events"]),
                "rests": len(document["rests"]),
                "phrases": len(document["phrases"]),
                "thesis": document["composition_thesis"],
                "score_file": f"ai_radiance_m{document['meta']['movement_number']}.score.json",
                "wav_file": f"exports/wav/ai_radiance/Original_AI_Radiance_Movement{document['meta']['movement_number']}.wav",
            }
            for document in documents
        ],
        "complete_score": "ai_radiance_complete.score.json",
        "complete_wav": "exports/wav/ai_radiance/Original_AI_Radiance_Complete.wav",
    }
    (SCORE_DIR / "ai_radiance.catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(catalog["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
