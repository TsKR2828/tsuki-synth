#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scene_reverb.py -- scene description -> global.effects.reverb.{decay, wet}.

Design contract: docs/SCENE_REVERB_DESIGN.zh-TW.md (do not redesign here --
that file is the source of truth; this module implements it literally).

Honesty split (docs/SCENE_REVERB_DESIGN.zh-TW.md Sec.0, mirrors
ROADMAP_PHYSICS.md Sec.0's domain table):
  - "space" mode  = physical derivation layer. Every number has a formula
    and a stated basis (Sabine/Eyring reverberation time; absorption
    coefficients from published tables or, for three outdoor surfaces,
    documented literature estimates -- stated per entry in MATERIALS
    below). The report prints every intermediate quantity so nothing is
    a black box.
  - "preset" mode = documented creative layer. NOT a physical claim -- an
    art-directed starting table (mirrors the spectralTilt precedent, round-4
    decision (3) in ROADMAP_PHYSICS.md): explicitly labeled as such in every
    report this module prints.

`reverb.decay` is consumed by SimpleReverb::setDecayTime() as an authored
T60 in seconds (src/score/ScoreRenderer.h, effectTailSeconds comment), so
the Sabine/Eyring T60 computed here needs no unit conversion at the engine
boundary.

This tool sits upstream of score authoring. It does not touch src/, does
not change any GATE or tolerance in ROADMAP_PHYSICS.md Sec.6, and --apply
never overwrites the file it reads (see docs/SCENE_REVERB_DESIGN.zh-TW.md
Sec.5 and memory feedback_no_overwrite_originals).

Usage:
    python tools/scene_reverb.py --scene scene.json
    python tools/scene_reverb.py --scene scene.json --report
    python tools/scene_reverb.py --list-presets
    python tools/scene_reverb.py --list-materials
    python tools/scene_reverb.py --scene s.json --apply in.score.json --output out.score.json

Exit code 0 = success. Exit code 1 = any fail-closed validation error.
"""

import argparse
import json
import math
import os
import sys

# ── schema-level clamp range (mirrors scores/schema/score.schema.json) ─────
DECAY_MIN, DECAY_MAX = 0.0, 30.0
WET_MIN, WET_MAX_SCHEMA = 0.0, 1.0
DEFAULT_WET_MAX = 0.6  # documented creative ceiling, see design map Sec.3
DEFAULT_LISTENER_DISTANCE_M = 3.0
SABINE_EYRING_SWITCH_ALPHA = 0.2  # design map Sec.3: Sabine valid for ᾱ<=0.2
ROUND_DIGITS = 4  # design map Sec.5: "decay/wet 輸出至多 4 位小數"

# ── Sec.3.1 material table: mid-frequency (500 Hz-1 kHz) absorption
# coefficients. Design map Sec.3.1 requires every entry to land within
# +/-0.02 of a citeable published mid-band value; the citation basis
# differs by material class, so it is stated per-entry below rather than
# claimed as one blanket source (design map Sec.0 honesty layering: a
# number without a locatable published row must not carry a book citation
# it does not have):
#   - Indoor room-surface materials (concrete, brick, glass, plaster,
#     wood_panel, wood_floor, carpet_heavy, curtain_heavy, acoustic_tile,
#     audience_seated) are Kuttruff (*Room Acoustics*) / Everest & Pohlmann
#     (*Master Handbook of Acoustics*) room-absorption-table rows; the
#     specific row and its mid-band (500 Hz/1 kHz) figures are named below.
#   - Outdoor/ground materials (rock_rough, grass_ground, water_surface,
#     snow_fresh) are largely NOT room-acoustics-book rows -- Kuttruff and
#     Everest & Pohlmann are indoor-room-focused and do not tabulate
#     outdoor ground surfaces such as bare rock or grass. snow_fresh IS a
#     citeable Everest & Pohlmann outdoor-surface row (see its comment
#     below). rock_rough, grass_ground and water_surface have no single
#     authoritative published row; they are reasoned engineering estimates
#     from outdoor-sound-propagation ground-impedance literature (broad
#     hard/porous ground classification, not a specific numbered table),
#     labeled as estimates rather than book citations for exactly that
#     reason.
# Order below matches the design map's table reading order (row-major
# across its two-column layout), kept for --list-materials output.
MATERIALS = {
    # Bare poured/troweled concrete, unpainted -- among the least absorptive
    # common building materials at mid-band (Kuttruff Table 6.1-style
    # "concrete, unpainted" row; Everest & Pohlmann absorption table).
    "concrete": 0.02,
    # Heavy pile carpet over felt/foam-rubber underlay -- soft absorptive
    # floor covering (Kuttruff / Everest & Pohlmann "carpet, heavy, on 40 oz
    # hairfelt or foam rubber" row: 500 Hz 0.57 / 1 kHz 0.69, mid-band mean
    # 0.63). Distinct from the much less absorptive "carpet, heavy, ON
    # CONCRETE" (unpadded) row, which this material name is not describing.
    "carpet_heavy": 0.63,
    # Unglazed brick, exposed -- hard, only lightly absorptive at mid-band
    # (Kuttruff / Everest & Pohlmann "brick, unglazed" row, mid-band ~0.03).
    "brick": 0.03,
    # Heavy velour drapery, draped to half area -- Kuttruff / Everest &
    # Pohlmann "draperies, heavy velour, draped to half area" row: 500 Hz
    # 0.55 / 1 kHz 0.72, mid-band mean 0.635.
    "curtain_heavy": 0.635,
    # Heavy plate glass -- Kuttruff / Everest & Pohlmann "glass, heavy
    # plate" row (500 Hz ~0.04 / 1 kHz ~0.03, mid-band mean ~0.035; stored
    # value 0.04 is the design map Sec.3.1 table anchor, within its +/-0.02
    # promise); noticeably less absorptive than the thin "ordinary window
    # glass" row, which this material name is not describing.
    "glass": 0.04,
    # Acoustic ceiling tile -- purpose-built absorber, high mid-band alpha
    # (Kuttruff / Everest & Pohlmann "acoustic tile, suspended" row).
    "acoustic_tile": 0.70,
    # Plaster, smooth finish, on lath -- Kuttruff / Everest & Pohlmann
    # "plaster, smooth finish" row, mid-band ~0.05.
    "plaster": 0.05,
    # Seated audience, upholstered/occupied -- one of the largest and most
    # variable absorbers in room-acoustics practice; mid-band value per
    # published "audience, seated" rows (Kuttruff; Everest & Pohlmann).
    "audience_seated": 0.80,
    # Wood panel over air space -- Kuttruff / Everest & Pohlmann "wood
    # panel/plywood, thin, over air space" row family; mid-band absorption
    # for these rows spans roughly 0.09-0.17 across published sources, 0.10
    # taken as a representative value near the low end of that range
    # (thin panel on a shallow air gap, close-mounted).
    "wood_panel": 0.10,
    # Grass over soil, outdoor ground plane -- NOT a Kuttruff/Everest &
    # Pohlmann room-acoustics row (see module-header note above); reasoned
    # estimate from outdoor-sound-propagation ground-absorption literature,
    # representative mid-band value for a porous/absorptive ground cover.
    "grass_ground": 0.55,
    # Bare wood floor, no covering -- Kuttruff / Everest & Pohlmann "wood
    # floor, on joists/sleepers" row, mid-band ~0.07.
    "wood_floor": 0.07,
    # Calm open water surface -- NOT a Kuttruff/Everest & Pohlmann row;
    # near-total reflection, mid-band alpha estimated close to the
    # concrete/brick end of the published hard-surface range.
    "water_surface": 0.01,
    # Rough natural rock / bare stone outdoor surface -- NOT a
    # Kuttruff/Everest & Pohlmann row (see module-header note above);
    # reasoned estimate from outdoor-sound-propagation ground-impedance
    # literature, representative mid-band value for a hard, irregular
    # outdoor surface.
    "rock_rough": 0.04,
    # Fresh, uncompacted snow -- highly absorptive porous surface. Everest &
    # Pohlmann "snow, fresh fallen, 4 in" outdoor-surface row: 500 Hz 0.90 /
    # 1 kHz 0.95, mid-band mean 0.925.
    "snow_fresh": 0.925,
}

# ── Sec.4 preset table: documented creative layer, NOT a physical claim.
# Order matches the design map's table reading order.
PRESETS = {
    "outdoor_open": {"decay": 0.10, "wet": 0.05},
    "hall_large":   {"decay": 1.8,  "wet": 0.30},
    "forest":       {"decay": 0.30, "wet": 0.10},
    "cathedral":    {"decay": 4.5,  "wet": 0.35},
    "room_small":   {"decay": 0.40, "wet": 0.15},
    "cave":         {"decay": 6.0,  "wet": 0.40},
    "room_medium":  {"decay": 0.60, "wet": 0.20},
    "bathroom":     {"decay": 1.0,  "wet": 0.30},
    "corridor":     {"decay": 1.2,  "wet": 0.25},
    "underwater":   {"decay": 0.25, "wet": 0.50},
}

SPACE_TOP_KEYS = {"dimensions_m", "surfaces", "material", "listener_distance_m"}
SURFACE_KEYS = {"material", "area_m2"}
SCENE_TOP_KEYS = {"preset", "space"}
SURFACE_AREA_TOLERANCE = 0.01  # design map Sec.2: shoebox area sum +/-1%


class SceneError(Exception):
    """Fail-closed validation error for scene JSON (never silently guessed)."""


def _legal_materials_str():
    return ", ".join(sorted(MATERIALS))


def _legal_presets_str():
    return ", ".join(sorted(PRESETS))


def round4(x):
    return round(x, ROUND_DIGITS)


def clamp(value, lo, hi, label, warnings):
    """Clamp value into [lo, hi], appending a human-readable warning if the
    clamp actually changed anything (design map Sec.3: "夾限...超界要在
    report 標警告")."""
    if value < lo:
        warnings.append(f"{label} {value} 低於下限 {lo}，已夾限為 {lo}")
        return lo
    if value > hi:
        warnings.append(f"{label} {value} 超出上限 {hi}，已夾限為 {hi}")
        return hi
    return value


# ── Sec.2 scene JSON parsing / fail-closed validation ───────────────────────

def _require_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SceneError(f"{label} 必須是數字，收到：{value!r}")
    return float(value)


def _require_positive_number(value, label):
    n = _require_number(value, label)
    if not (n > 0):
        raise SceneError(f"{label} 必須是正數，收到：{n}")
    return n


def parse_scene(scene):
    """Validate the top-level scene dict and return ('preset', name) or
    ('space', normalized_space_dict). Raises SceneError on any violation."""
    if not isinstance(scene, dict):
        raise SceneError("scene JSON 頂層必須是物件（object）")

    unknown = set(scene.keys()) - SCENE_TOP_KEYS
    if unknown:
        raise SceneError(
            f"未知頂層鍵：{sorted(unknown)}；合法頂層鍵僅有 'preset' 或 'space'（二擇一）")

    has_preset = "preset" in scene
    has_space = "space" in scene
    if has_preset == has_space:  # both present, or both absent
        raise SceneError(
            "scene JSON 必須恰好提供 'preset' 或 'space' 其中一項（互斥），"
            "不可同時提供，也不可同時缺席")

    if has_preset:
        name = scene["preset"]
        if not isinstance(name, str):
            raise SceneError(f"'preset' 必須是字串，收到：{name!r}")
        if name not in PRESETS:
            raise SceneError(f"未知 preset '{name}'；合法 preset 清單：{_legal_presets_str()}")
        return "preset", name

    space = scene["space"]
    if not isinstance(space, dict):
        raise SceneError("'space' 必須是物件（object）")

    unknown = set(space.keys()) - SPACE_TOP_KEYS
    if unknown:
        raise SceneError(
            f"'space' 內有未知鍵：{sorted(unknown)}；合法鍵：{sorted(SPACE_TOP_KEYS)}")

    if "dimensions_m" not in space:
        raise SceneError("'space' 缺少必要鍵 'dimensions_m'")
    dims = space["dimensions_m"]
    if not (isinstance(dims, list) and len(dims) == 3):
        raise SceneError("'dimensions_m' 必須是長度為 3 的陣列 [length, width, height]")
    length = _require_positive_number(dims[0], "dimensions_m[0]（長）")
    width = _require_positive_number(dims[1], "dimensions_m[1]（寬）")
    height = _require_positive_number(dims[2], "dimensions_m[2]（高）")

    listener_distance = DEFAULT_LISTENER_DISTANCE_M
    if "listener_distance_m" in space:
        listener_distance = _require_positive_number(
            space["listener_distance_m"], "listener_distance_m")

    has_surfaces = "surfaces" in space
    has_material = "material" in space
    if has_surfaces == has_material:
        raise SceneError(
            "'space' 必須恰好提供 'surfaces' 或 'material' 其中一項（互斥），"
            "不可同時提供，也不可同時缺席")

    volume = length * width * height
    total_surface = 2.0 * (length * width + length * height + width * height)

    if has_material:
        material = space["material"]
        if not isinstance(material, str):
            raise SceneError(f"'material' 必須是字串，收到：{material!r}")
        if material not in MATERIALS:
            raise SceneError(f"未知材質 '{material}'；合法材質清單：{_legal_materials_str()}")
        surfaces = [{"material": material, "area_m2": total_surface}]
    else:
        raw_surfaces = space["surfaces"]
        if not (isinstance(raw_surfaces, list) and len(raw_surfaces) > 0):
            raise SceneError("'surfaces' 必須是非空陣列")
        surfaces = []
        for i, entry in enumerate(raw_surfaces):
            if not isinstance(entry, dict):
                raise SceneError(f"surfaces[{i}] 必須是物件（object）")
            unknown = set(entry.keys()) - SURFACE_KEYS
            if unknown:
                raise SceneError(
                    f"surfaces[{i}] 內有未知鍵：{sorted(unknown)}；合法鍵：{sorted(SURFACE_KEYS)}")
            if "material" not in entry or "area_m2" not in entry:
                raise SceneError(f"surfaces[{i}] 必須同時包含 'material' 與 'area_m2'")
            material = entry["material"]
            if not isinstance(material, str):
                raise SceneError(f"surfaces[{i}].material 必須是字串，收到：{material!r}")
            if material not in MATERIALS:
                raise SceneError(
                    f"surfaces[{i}] 使用未知材質 '{material}'；合法材質清單：{_legal_materials_str()}")
            area = _require_positive_number(entry["area_m2"], f"surfaces[{i}].area_m2")
            surfaces.append({"material": material, "area_m2": area})

        area_sum = sum(s["area_m2"] for s in surfaces)
        deviation = abs(area_sum - total_surface) / total_surface
        if deviation > SURFACE_AREA_TOLERANCE:
            raise SceneError(
                "surfaces 面積總和與 shoebox 總表面積偏離超過 "
                f"{SURFACE_AREA_TOLERANCE * 100:.0f}%：surfaces 總和="
                f"{area_sum:.4f} m^2，shoebox 總表面積={total_surface:.4f} m^2，"
                f"偏離={deviation * 100:.2f}%")

    return "space", {
        "length_m": length,
        "width_m": width,
        "height_m": height,
        "listener_distance_m": listener_distance,
        "surfaces": surfaces,
        "volume_m3": volume,
        "total_surface_m2": total_surface,
    }


# ── Sec.3 Sabine/Eyring physics ─────────────────────────────────────────────

def compute_physical(space, wet_max=DEFAULT_WET_MAX):
    """Full Sabine/Eyring + wet derivation for a normalized 'space' dict
    (as returned by parse_scene). Returns a result dict with every
    intermediate quantity so the report can print all of them (design map
    Sec.3: "每步都要在 report 印出")."""
    warnings = []

    volume = space["volume_m3"]
    total_surface = space["total_surface_m2"]
    surfaces = space["surfaces"]

    sum_s_alpha = 0.0
    for s in surfaces:
        alpha = MATERIALS[s["material"]]
        sum_s_alpha += s["area_m2"] * alpha
    alpha_bar = sum_s_alpha / total_surface

    if alpha_bar >= 1.0:
        # Cannot occur with the published table (max alpha 0.80 < 1), but
        # guarded fail-closed rather than silently producing Eyring's
        # divergent -ln(1 - alpha_bar) for alpha_bar -> 1.
        raise SceneError(
            f"平均吸音係數 ᾱ={alpha_bar} 已達 1.0，Eyring 公式在此發散，無法推導；"
            "請檢查 surfaces 材質組合")

    sabine_t60 = 0.161 * volume / sum_s_alpha
    eyring_t60 = 0.161 * volume / (-total_surface * math.log(1.0 - alpha_bar))

    use_eyring = alpha_bar > SABINE_EYRING_SWITCH_ALPHA
    adopted_t60 = eyring_t60 if use_eyring else sabine_t60
    adopted_model = "Eyring" if use_eyring else "Sabine"
    switch_reason = (
        f"ᾱ={alpha_bar:.4f} > {SABINE_EYRING_SWITCH_ALPHA}，Sabine 在高吸音下系統性高估，自動改用 Eyring"
        if use_eyring else
        f"ᾱ={alpha_bar:.4f} <= {SABINE_EYRING_SWITCH_ALPHA}，Sabine 公式適用範圍內"
    )

    decay_clamped = clamp(adopted_t60, DECAY_MIN, DECAY_MAX, "decay", warnings)

    # wet derivation (design map Sec.3): room constant R, critical distance
    # r_c (Q=1), direct/reverberant energy ratio wet_raw, then a documented
    # creative ceiling wet_max.
    room_constant = total_surface * alpha_bar / (1.0 - alpha_bar)
    critical_distance = math.sqrt(room_constant / (16.0 * math.pi))
    r = space["listener_distance_m"]
    wet_raw = (r * r) / (r * r + critical_distance * critical_distance)
    wet_applied = min(wet_raw, wet_max)
    if wet_raw > wet_max:
        warnings.append(
            f"wet_raw={wet_raw:.4f} 觸及 wet_max={wet_max}（documented creative 上限），"
            f"已限制為 {wet_max}")
    wet_clamped = clamp(wet_applied, WET_MIN, WET_MAX_SCHEMA, "wet", warnings)

    return {
        "mode": "space",
        "volume_m3": volume,
        "total_surface_m2": total_surface,
        "surfaces": surfaces,
        "sum_s_alpha": sum_s_alpha,
        "alpha_bar": alpha_bar,
        "sabine_t60_s": sabine_t60,
        "eyring_t60_s": eyring_t60,
        "adopted_model": adopted_model,
        "switch_reason": switch_reason,
        "room_constant": room_constant,
        "critical_distance_m": critical_distance,
        "listener_distance_m": r,
        "wet_raw": wet_raw,
        "wet_max": wet_max,
        "wet_applied_pre_clamp": wet_applied,
        "decay": round4(decay_clamped),
        "wet": round4(wet_clamped),
        "warnings": warnings,
    }


def compute_preset(name):
    """Sec.4 documented creative layer: table lookup, no physical claim."""
    warnings = []
    preset = PRESETS[name]
    decay_clamped = clamp(preset["decay"], DECAY_MIN, DECAY_MAX, "decay", warnings)
    wet_clamped = clamp(preset["wet"], WET_MIN, WET_MAX_SCHEMA, "wet", warnings)
    return {
        "mode": "preset",
        "preset": name,
        "decay": round4(decay_clamped),
        "wet": round4(wet_clamped),
        "warnings": warnings,
    }


# ── report rendering (markdown; used for both --report stdout and the
# default stderr human-readable report -- markdown reads fine as plain
# text, and keeping one renderer avoids two report formats drifting apart) ──

def render_report(result):
    lines = []
    if result["mode"] == "preset":
        lines.append("# scene_reverb report -- preset 模式")
        lines.append("")
        lines.append(
            "**注意：本結果為 documented creative 層（美術預設表），非物理推導。**"
            "（見 docs/SCENE_REVERB_DESIGN.zh-TW.md Sec.0/4）")
        lines.append("")
        lines.append(f"- preset：`{result['preset']}`")
        lines.append(f"- decay（T60，秒）：{result['decay']}")
        lines.append(f"- wet：{result['wet']}")
    else:
        lines.append("# scene_reverb report -- space 模式（Sabine/Eyring 物理推導）")
        lines.append("")
        lines.append(f"- V（體積）= {result['volume_m3']:.4f} m^3")
        lines.append(f"- S（總表面積）= {result['total_surface_m2']:.4f} m^2")
        lines.append("")
        lines.append("## 表面材質明細")
        lines.append("")
        lines.append("| 材質 | 面積 (m^2) | α (mid) | S·α |")
        lines.append("|---|---|---|---|")
        for s in result["surfaces"]:
            alpha = MATERIALS[s["material"]]
            lines.append(
                f"| {s['material']} | {s['area_m2']:.4f} | {alpha} | {s['area_m2'] * alpha:.4f} |")
        lines.append("")
        lines.append(f"- Σ(Sᵢ·αᵢ) = {result['sum_s_alpha']:.4f}")
        lines.append(f"- ᾱ = Σ(Sᵢ·αᵢ) / S = {result['alpha_bar']:.4f}")
        lines.append("")
        lines.append("## T60（Sabine / Eyring 對照）")
        lines.append("")
        lines.append(f"- Sabine T60 = 0.161·V / Σ(Sᵢ·αᵢ) = {result['sabine_t60_s']:.4f} s")
        lines.append(
            f"- Eyring T60 = 0.161·V / (-S·ln(1-ᾱ)) = {result['eyring_t60_s']:.4f} s")
        lines.append(f"- 採用：**{result['adopted_model']}**（{result['switch_reason']}）")
        lines.append("")
        lines.append("## wet 推導")
        lines.append("")
        lines.append(f"- 房間常數 R = S·ᾱ/(1-ᾱ) = {result['room_constant']:.4f}")
        lines.append(
            f"- 臨界距離 r_c = √(R/(16π)) = {result['critical_distance_m']:.4f} m")
        lines.append(f"- listener_distance_m = {result['listener_distance_m']:.4f}")
        lines.append(f"- wet_raw = r²/(r²+r_c²) = {result['wet_raw']:.4f}")
        lines.append(
            f"- wet_max（documented creative 上限）= {result['wet_max']}")
        lines.append(f"- wet（套用 wet_max 後）= {result['wet_applied_pre_clamp']:.4f}")
        lines.append("")
        lines.append("## 最終輸出")
        lines.append("")
        lines.append(f"- decay = {result['decay']}")
        lines.append(f"- wet = {result['wet']}")

    if result["warnings"]:
        lines.append("")
        lines.append("## 警告")
        lines.append("")
        for w in result["warnings"]:
            lines.append(f"- {w}")

    return "\n".join(lines) + "\n"


def render_json_fragment(result):
    return json.dumps({"reverb": {"decay": result["decay"], "wet": result["wet"]}},
                       ensure_ascii=False)


def render_presets_table():
    """--list-presets stdout payload. Sec.5 only says the table must be
    printable via --list-presets, without pinning a format; JSON is used
    here (rather than the markdown used by render_report) so the output
    stays machine-parseable, matching the plain --scene mode's JSON
    fragment convention. {preset_name: {"decay":..., "wet":...}}."""
    return json.dumps(
        {name: {"decay": PRESETS[name]["decay"], "wet": PRESETS[name]["wet"]}
         for name in sorted(PRESETS)},
        ensure_ascii=False, indent=2) + "\n"


def render_materials_table():
    """--list-materials stdout payload, same JSON rationale as
    render_presets_table() above. {material_name: alpha}."""
    return json.dumps(
        {name: MATERIALS[name] for name in sorted(MATERIALS)},
        ensure_ascii=False, indent=2) + "\n"


# ── --apply: modify only global.effects.reverb.{decay,wet} in-place ────────

def _same_file_path(a, b):
    """True if `a` and `b` refer to the same file on disk. Sec.5's
    "output 不得等於 input" guard must not be bypassable by path aliasing
    (different string, same file): different case on a case-insensitive
    filesystem, a './' or '..' detour, a symlink, or a hardlink.
    os.path.abspath() alone only normalizes separators and '..' -- it does
    NOT case-fold and does NOT resolve symlinks/hardlinks, so two paths
    that abspath() disagree on can still be the identical file. realpath()
    resolves symlinks; normcase() folds case on case-insensitive platforms
    (Windows, default macOS) and is a no-op on case-sensitive ones (Linux),
    so this stays correct everywhere. os.path.samefile() is also checked
    when both paths currently exist -- it additionally catches hardlinks,
    which share no path text at all and would defeat the realpath+normcase
    check by itself."""
    a_norm = os.path.normcase(os.path.realpath(a))
    b_norm = os.path.normcase(os.path.realpath(b))
    if a_norm == b_norm:
        return True
    if os.path.exists(a) and os.path.exists(b):
        try:
            return os.path.samefile(a, b)
        except OSError:
            return False
    return False


def apply_to_score(input_path, output_path, result):
    if _same_file_path(input_path, output_path):
        raise SceneError(
            "--output 不得等於 --apply 的輸入路徑（不覆寫原檔；"
            "見 docs/SCENE_REVERB_DESIGN.zh-TW.md Sec.5 / memory feedback_no_overwrite_originals）")

    if not os.path.isfile(input_path):
        raise SceneError(f"--apply 指定的檔案不存在：{input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        try:
            score = json.load(f)
        except json.JSONDecodeError as e:
            raise SceneError(f"--apply 指定的檔案不是合法 JSON：{input_path}（{e}）")

    if not isinstance(score, dict) or "global" not in score or not isinstance(score["global"], dict):
        raise SceneError(f"--apply 指定的檔案缺少必要的 'global' 物件，無法安全套用：{input_path}")

    effects = score["global"].setdefault("effects", {})
    if not isinstance(effects, dict):
        raise SceneError(f"'global.effects' 不是物件，無法安全套用：{input_path}")
    reverb = effects.setdefault("reverb", {})
    if not isinstance(reverb, dict):
        raise SceneError(f"'global.effects.reverb' 不是物件，無法安全套用：{input_path}")

    reverb["decay"] = result["decay"]
    reverb["wet"] = result["wet"]

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(score, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ── CLI ─────────────────────────────────────────────────────────────────────

def build_arg_parser():
    ap = argparse.ArgumentParser(
        description="Scene description -> global.effects.reverb.{decay, wet} "
                     "(docs/SCENE_REVERB_DESIGN.zh-TW.md).")
    ap.add_argument("--scene", metavar="PATH", help="path to a scene JSON file")
    ap.add_argument("--report", action="store_true",
                     help="print the full Sabine/Eyring derivation report "
                          "(markdown) to stdout instead of the compact JSON fragment")
    ap.add_argument("--list-presets", action="store_true",
                     help="print the Sec.4 preset table and exit")
    ap.add_argument("--list-materials", action="store_true",
                     help="print the Sec.3.1 material absorption table and exit")
    ap.add_argument("--apply", metavar="IN_SCORE",
                     help="score JSON file to read and update global.effects.reverb in "
                          "(requires --output; --output must differ from this path)")
    ap.add_argument("--output", metavar="OUT_SCORE",
                     help="output path for --apply (must differ from --apply's input path)")
    ap.add_argument("--wet-max", type=float, default=DEFAULT_WET_MAX,
                     help=f"documented creative ceiling for physically-derived wet "
                          f"(default {DEFAULT_WET_MAX}); ignored in preset mode")
    return ap


def main(argv=None):
    # UTF-8 output regardless of host codepage (mirrors verify_score.py's
    # sys.stdout.reconfigure): reports use non-ASCII math notation (ᾱ, Σ, ·)
    # and Chinese error text, which a cp1252/cp950 console would reject.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = build_arg_parser()
    args = ap.parse_args(argv)

    list_flags = args.list_presets or args.list_materials
    if list_flags and args.scene:
        ap.error("--list-presets/--list-materials 不可與 --scene 併用")
    if args.list_presets and args.list_materials:
        ap.error("--list-presets 與 --list-materials 不可併用")
    if list_flags and (args.apply or args.output or args.report):
        ap.error("--list-presets/--list-materials 不可與 --apply/--output/--report 併用")
    if not list_flags and not args.scene:
        ap.error("必須指定 --scene，或 --list-presets，或 --list-materials 其中一項")
    if bool(args.apply) != bool(args.output):
        ap.error("--apply 必須搭配 --output 一起使用")

    if args.list_presets:
        sys.stdout.write(render_presets_table())
        return 0
    if args.list_materials:
        sys.stdout.write(render_materials_table())
        return 0

    try:
        with open(args.scene, "r", encoding="utf-8") as f:
            try:
                scene = json.load(f)
            except json.JSONDecodeError as e:
                raise SceneError(f"--scene 指定的檔案不是合法 JSON：{args.scene}（{e}）")

        mode, data = parse_scene(scene)
        if mode == "preset":
            result = compute_preset(data)
        else:
            result = compute_physical(data, wet_max=args.wet_max)

        if args.apply:
            apply_to_score(args.apply, args.output, result)

        if args.report:
            sys.stdout.write(render_report(result))
        else:
            sys.stdout.write(render_json_fragment(result) + "\n")
            sys.stderr.write(render_report(result))
    except FileNotFoundError as e:
        sys.stderr.write(f"Error: 找不到檔案：{e.filename}\n")
        return 1
    except SceneError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
