"""Contract tests for tools/scene_reverb.py against
docs/SCENE_REVERB_DESIGN.zh-TW.md Sec.6 (all ten numbered items).

scene_reverb.py is documented entirely as a CLI/JSON-in-JSON-out contract
(Sec.2-Sec.5 of the design map) -- no internal function/constant names are
specified anywhere in the design map. To avoid pinning the test suite to
implementation details the design map never promised (and therefore
failing for the wrong reason if the real implementation picks different
internal names), every behavioural assertion here drives the tool the same
way a human or another script would: as a subprocess, reading only stdout,
stderr, exit code and the score JSON files it writes. This mirrors the
task brief's explicit instruction to invoke CLI-level tests via
subprocess with cwd=repo root.

The module is still imported once via importlib (same pattern as
tests/test_verify_score_contract.py) purely as a fast, clear failure signal
if tools/scene_reverb.py is missing or fails to import/parse -- no
attributes of it are asserted on beyond `main` existing, which is the
established convention across every other tools/*.py in this repo
(check_piece_consonance.py, verify_score.py, specimen_pipeline.py, ...).

One genuine ambiguity in the design map: the exact JSON shape of the
"JSON 片段" that plain (non ``--report``) mode prints to stdout is never
pinned down -- only that it represents ``global.effects.reverb.{decay,
wet}``. Rather than guess a single shape and risk failing the suite for a
reason unrelated to physics/contract correctness, `_extract_decay_wet()`
below accepts either a flat ``{"decay":..., "wet":...}`` object or a
``{"reverb": {"decay":..., "wet":...}}`` wrapper.
"""

import copy
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "scene_reverb.py"

SPEC = importlib.util.spec_from_file_location("scene_reverb", SCRIPT)
scene_reverb = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scene_reverb)


def run_cli(*args):
    """Invoke tools/scene_reverb.py exactly as a user would, from repo
    root, with the same interpreter running the tests."""
    return subprocess.run(
        [sys.executable, "tools/scene_reverb.py", *args],
        cwd=str(ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace")


def write_json(dir_path, name, data):
    p = Path(dir_path) / name
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p


def extract_decay_wet(payload):
    """Accept either a flat {"decay","wet"} object or a
    {"reverb": {"decay","wet"}} wrapper -- see module docstring."""
    if isinstance(payload, dict) and "decay" in payload and "wet" in payload:
        return float(payload["decay"]), float(payload["wet"])
    if isinstance(payload, dict) and "reverb" in payload:
        r = payload["reverb"]
        return float(r["decay"]), float(r["wet"])
    raise AssertionError(
        f"could not find decay/wet in CLI JSON output: {payload!r}")


def assert_same_key_order(test, a, b, path="$"):
    """Recursively assert two decoded JSON values have identical key
    ORDER at every level (Sec.5: "其餘 JSON 內容與鍵序不動"), independent
    of leaf value equality. Regular dict preserves JSON source key order
    in CPython 3.7+, so list(d.keys()) is sufficient -- no need for
    object_pairs_hook gymnastics."""
    test.assertIs(type(a), type(b), f"type differs at {path}")
    if isinstance(a, dict):
        test.assertEqual(list(a.keys()), list(b.keys()),
                          f"key order differs at {path}")
        for k in a:
            assert_same_key_order(test, a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        test.assertEqual(len(a), len(b), f"array length differs at {path}")
        for i, (x, y) in enumerate(zip(a, b)):
            assert_same_key_order(test, x, y, f"{path}[{i}]")


# ---------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------

# Sec.3.2 anchor 1 & 3: 10x8x3m shoebox, all concrete (alpha=0.02 <= 0.2
# -> Sabine). V=240, S=268, sum(S*alpha)=5.36 -> Sabine T60=7.209s.
ANCHOR_CONCRETE_ROOM = {
    "space": {
        "dimensions_m": [10.0, 8.0, 3.0],
        "material": "concrete",
    }
}

# Sec.3.2 anchor 3: same room, explicit listener_distance_m=3.0 (also the
# documented default) -> wet_raw=0.9881, clamped to the --wet-max default
# of 0.6.
ANCHOR_CONCRETE_ROOM_R3 = {
    "space": {
        "dimensions_m": [10.0, 8.0, 3.0],
        "material": "concrete",
        "listener_distance_m": 3.0,
    }
}

# Sec.3.2 anchor 2: same shoebox, all acoustic_tile (alpha=0.70 > 0.2 ->
# Eyring). -S*ln(1-0.70)=322.6647 -> Eyring T60=0.11975s (Sabine would
# give 0.20597s, report-only comparison, not the applied value).
ANCHOR_TILE_ROOM = {
    "space": {
        "dimensions_m": [10.0, 8.0, 3.0],
        "material": "acoustic_tile",
    }
}

# alpha=0.2 exactly (boundary, inclusive side -> Sabine). 10x10x8.25
# shoebox: S=2*(100+82.5+82.5)=530, V=825.
# wood_panel(0.10)*430 + carpet_heavy(0.63)*100 = 43+63 = 106,
# 106/530=0.2 exactly. Areas sum to exactly S=530 (no tolerance needed).
# Sabine T60 = 0.161*825/106 = 1.2530660377358491s exactly (rational
# arithmetic; carpet_heavy=0.63 per the corrected Sec.3.1 table --
# 2026-08-05 fix, see docs/SCENE_REVERB_DESIGN.zh-TW.md Sec.3.1).
BOUNDARY_ALPHA_EXACTLY_0_2 = {
    "space": {
        "dimensions_m": [10.0, 10.0, 8.25],
        "surfaces": [
            {"material": "wood_panel", "area_m2": 430.0},
            {"material": "carpet_heavy", "area_m2": 100.0},
        ],
    }
}

# alpha=0.201 (just above the boundary -> Eyring). Same shoebox, areas
# shifted by 1 m^2 each way, still summing to exactly S=530.
# sum(S*alpha) = 429*0.10 + 101*0.63 = 42.9+63.63 = 106.53,
# alpha=106.53/530=0.201 exactly.
# Verified with math.log: Eyring T60 = 1.1168428540754878s (vs. a Sabine
# value of ~1.2468, far outside tolerance -- the two formulas are well
# separated here so matching one over the other unambiguously proves
# which branch the implementation took).
BOUNDARY_ALPHA_JUST_ABOVE_0_2 = {
    "space": {
        "dimensions_m": [10.0, 10.0, 8.25],
        "surfaces": [
            {"material": "wood_panel", "area_m2": 429.0},
            {"material": "carpet_heavy", "area_m2": 101.0},
        ],
    }
}

# Deliberately huge, hard-surfaced room: Sabine T60 = 0.161*125000/300 =
# 67.08s, far past the schema's [0,30] decay ceiling -> must clamp to
# exactly 30 with a report warning, not fail closed (clamping is
# documented as a bounding behaviour, not a rejection).
OVERSIZE_HARD_ROOM = {
    "space": {
        "dimensions_m": [50.0, 50.0, 50.0],
        "material": "concrete",
    }
}

# 10x8x3 shoebox again (S=268) but surfaces only sum to 250 m^2: an 18
# m^2 / 6.7% shortfall, well past the +/-1% fail-closed tolerance.
SURFACES_AREA_MISMATCH = {
    "space": {
        "dimensions_m": [10.0, 8.0, 3.0],
        "surfaces": [
            {"material": "concrete", "area_m2": 200.0},
            {"material": "carpet_heavy", "area_m2": 50.0},
        ],
    }
}

KNOWN_PRESET_NAMES = {
    "outdoor_open", "forest", "room_small", "room_medium", "corridor",
    "hall_large", "cathedral", "cave", "bathroom", "underwater",
}

KNOWN_MATERIAL_NAMES = {
    "concrete", "brick", "glass", "plaster", "wood_panel", "wood_floor",
    "rock_rough", "carpet_heavy", "curtain_heavy", "acoustic_tile",
    "audience_seated", "grass_ground", "water_surface", "snow_fresh",
}

SAMPLE_SCORE = {
    "$schema": "TsukiSynth Score v1",
    "meta": {
        "title": "Scene Reverb Apply Fixture",
        "id": "scene_reverb_apply_fixture_001",
        "description": "Synthetic fixture for --apply round-trip tests.",
        "tags": ["fixture", "reverb"],
    },
    "global": {
        "bpm": 90,
        "sample_rate": 48000,
        "master_volume": 0.8,
        "effects": {
            "reverb": {"decay": 1.23, "wet": 0.11},
            "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
        },
    },
    "events": [
        {
            "time": 0.0,
            "duration": 1.0,
            "engine": "beam",
            "note": "C4",
            "velocity": 0.8,
            "params": {"material": "steel"},
        },
    ],
    "export": {"filename": "scene_reverb_apply_fixture", "format": "wav",
               "normalize": True},
}


class ModuleSmokeTest(unittest.TestCase):
    """Established house-style guard (see test_verify_score_contract.py):
    fail fast and clearly if the module can't even be imported, before any
    of the slower subprocess-driven contract tests run."""

    def test_module_has_a_main_entry_point(self):
        self.assertTrue(hasattr(scene_reverb, "main"))
        self.assertTrue(callable(scene_reverb.main))


class AnchorValueTests(unittest.TestCase):
    """Sec.6 item 1: the three Sec.3.2 known-value anchors, used verbatim
    with the stated tolerances."""

    def _decay_wet(self, scene):
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", scene)
            result = run_cli("--scene", str(scene_path))
            self.assertEqual(0, result.returncode, result.stderr)
            return extract_decay_wet(json.loads(result.stdout))

    def test_sabine_anchor_all_concrete_room(self):
        decay, _wet = self._decay_wet(ANCHOR_CONCRETE_ROOM)
        self.assertAlmostEqual(7.209, decay, delta=0.01)

    def test_eyring_switch_anchor_all_acoustic_tile_room(self):
        decay, _wet = self._decay_wet(ANCHOR_TILE_ROOM)
        self.assertAlmostEqual(0.1198, decay, delta=0.001)

    def test_wet_clamp_anchor_concrete_room_at_listener_distance_3m(self):
        # R=5.469, r_c=0.330m -> wet_raw=0.9881 -> min(0.9881, 0.6)=0.6:
        # the applied wet must hit the documented --wet-max default
        # exactly, not the raw physical value.
        _decay, wet = self._decay_wet(ANCHOR_CONCRETE_ROOM_R3)
        self.assertAlmostEqual(0.6, wet, delta=1e-4)

    def test_report_mode_names_both_formulas_on_eyring_switch(self):
        # Bonus coverage of Sec.3's "report 兩者皆印，標明採用哪個與理由"
        # transparency requirement, exercised on the same anchor that
        # forces the Sabine->Eyring switch. Not one of the ten numbered
        # Sec.6 items by itself, but it rides on item 1's anchor scene, so
        # it is kept alongside the other anchor tests. Deliberately loose
        # (substring, case-insensitive) since the design map fixes the
        # anchor NUMBERS but not the report's prose/markdown layout.
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", ANCHOR_TILE_ROOM)
            result = run_cli("--scene", str(scene_path), "--report")
        self.assertEqual(0, result.returncode, result.stderr)
        report = result.stdout.lower()
        self.assertIn("sabine", report)
        self.assertIn("eyring", report)


class AlphaBoundaryTests(unittest.TestCase):
    """Sec.6 item 2: alpha<=0.2 uses Sabine, alpha>0.2 uses Eyring, one
    example on each side of the boundary. The two formulas are verified
    (via math.log at test-authoring time) to diverge by ~0.1s here, far
    outside either tolerance, so matching one value unambiguously proves
    which branch fired -- no need for the CLI to expose which formula it
    picked."""

    def _decay(self, scene):
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", scene)
            result = run_cli("--scene", str(scene_path))
            self.assertEqual(0, result.returncode, result.stderr)
            decay, _wet = extract_decay_wet(json.loads(result.stdout))
            return decay

    def test_alpha_exactly_0_2_uses_sabine(self):
        decay = self._decay(BOUNDARY_ALPHA_EXACTLY_0_2)
        self.assertAlmostEqual(1.253066, decay, delta=0.001)

    def test_alpha_just_above_0_2_uses_eyring(self):
        decay = self._decay(BOUNDARY_ALPHA_JUST_ABOVE_0_2)
        self.assertAlmostEqual(1.116843, decay, delta=0.005)


class UnknownMaterialTests(unittest.TestCase):
    """Sec.6 item 3: unknown material name -> non-zero exit, message
    lists the legal material table (never silently defaults an alpha)."""

    def test_unknown_material_fails_closed_and_lists_legal_materials(self):
        scene = {"space": {"dimensions_m": [5.0, 5.0, 3.0],
                            "material": "styrofoam"}}
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", scene)
            result = run_cli("--scene", str(scene_path))
        self.assertNotEqual(0, result.returncode)
        combined = result.stdout + result.stderr
        self.assertIn("styrofoam", combined)
        # at least a couple of the real, legal material names must be
        # listed so the user (or the calling script) can self-correct
        # without consulting the source.
        self.assertIn("concrete", combined)
        self.assertIn("acoustic_tile", combined)

    def test_unknown_material_in_per_surface_entry_also_fails_closed(self):
        scene = {"space": {
            "dimensions_m": [10.0, 8.0, 3.0],
            "surfaces": [{"material": "unobtainium", "area_m2": 268.0}],
        }}
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", scene)
            result = run_cli("--scene", str(scene_path))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unobtainium", result.stdout + result.stderr)


class InputModeValidationTests(unittest.TestCase):
    """Sec.6 item 4: preset/space are mutually exclusive; both given, both
    missing, or any unknown key (top-level or nested) must fail closed."""

    def _fails(self, scene):
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", scene)
            result = run_cli("--scene", str(scene_path))
        self.assertNotEqual(0, result.returncode,
                             f"expected failure for {scene!r}, got "
                             f"stdout={result.stdout!r}")

    def test_preset_and_space_both_given_fails(self):
        self._fails({
            "preset": "cave",
            "space": {"dimensions_m": [5.0, 5.0, 3.0], "material": "concrete"},
        })

    def test_neither_preset_nor_space_given_fails(self):
        self._fails({})

    def test_unknown_top_level_key_fails(self):
        self._fails({"preset": "cave", "mystery_key": 1})

    def test_unknown_key_nested_inside_space_fails(self):
        self._fails({"space": {
            "dimensions_m": [5.0, 5.0, 3.0],
            "material": "concrete",
            "extra_nested_key": True,
        }})

    def test_unknown_preset_name_fails(self):
        self._fails({"preset": "definitely_not_a_real_preset"})


class SurfaceAreaMismatchTests(unittest.TestCase):
    """Sec.6 item 5: surfaces area sum must equal the shoebox total
    surface area within +/-1%, else fail closed (no silent residual
    padding)."""

    def test_surfaces_area_more_than_1_percent_short_fails(self):
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", SURFACES_AREA_MISMATCH)
            result = run_cli("--scene", str(scene_path))
        self.assertNotEqual(0, result.returncode)

    def test_surfaces_area_within_1_percent_passes(self):
        # 268 m^2 shoebox, surfaces summing to 266.5 (0.56% short, inside
        # tolerance) -- the positive control for the above negative test.
        scene = {"space": {
            "dimensions_m": [10.0, 8.0, 3.0],
            "surfaces": [
                {"material": "concrete", "area_m2": 216.5},
                {"material": "carpet_heavy", "area_m2": 50.0},
            ],
        }}
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", scene)
            result = run_cli("--scene", str(scene_path))
        self.assertEqual(0, result.returncode, result.stderr)


class DecayClampTests(unittest.TestCase):
    """Sec.6 item 6: a scene whose raw T60 exceeds the schema's 30s
    ceiling must clamp to exactly 30 (not reject) and surface a warning."""

    def test_oversize_hard_room_clamps_to_30_with_warning(self):
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", OVERSIZE_HARD_ROOM)
            result = run_cli("--scene", str(scene_path))
        self.assertEqual(0, result.returncode, result.stderr)
        decay, _wet = extract_decay_wet(json.loads(result.stdout))
        self.assertEqual(30.0, decay)
        combined = (result.stdout + result.stderr).lower()
        warned = any(marker in combined for marker in
                     ("clamp", "warn", "夾限", "警告", "capped", "exceed"))
        self.assertTrue(
            warned,
            f"expected a clamp warning in stdout/stderr, got: {combined!r}")


def _extract_trailing_float(line):
    """Pull the trailing numeric value off a `--report` line such as
    '- 房間常數 R = S·ᾱ/(1-ᾱ) = 5.4694' or
    '- 臨界距離 r_c = √(R/(16π)) = 0.3299 m' (optional trailing ' m' /
    ' s' unit). Used instead of exact-string matching so this stays
    robust to the report's prose wording while still pinning the number."""
    m = re.search(r"([0-9]+\.[0-9]+)\s*[a-zA-Z]?\s*$", line.strip())
    if m is None:
        raise AssertionError(f"no trailing float found in report line: {line!r}")
    return float(m.group(1))


class WetDerivationChainTests(unittest.TestCase):
    """2026-08-05 Opus finding (Lens C / blocker): the room constant R,
    critical distance r_c and wet_raw were entirely unverified -- the only
    wet assertion (test_wet_clamp_anchor_concrete_room_at_listener_
    distance_3m in AnchorValueTests) sits on a scene that SATURATES
    (wet_raw > wet_max), so any r_c/R computation wrong enough to still
    saturate reproduces the same clamped 0.6 output. These tests pin the
    unsaturated regime (where the raw formula value survives to the
    output unclamped) and the R/r_c intermediates themselves, closing
    that gap. Confirmed by mutation during the fix: corrupting
    room_constant's formula (*0.05 instead of the real ratio) and
    critical_distance's directivity constant (4*pi instead of 16*pi) made
    both new tests fail while the pre-existing saturated-anchor test kept
    passing."""

    def test_oversize_hard_room_wet_is_unsaturated_and_matches_hand_calc(self):
        # 50x50x50 concrete, default listener_distance_m=3.0: S=15000,
        # V=125000, alpha_bar=0.02 -> R=S*alpha_bar/(1-alpha_bar)=
        # 15000*0.02/0.98=306.122449, r_c=sqrt(R/(16*pi))=2.467816m,
        # wet_raw=9/(9+r_c^2)=0.596419... -- well below the 0.6 wet_max
        # default, so wet_applied==wet_raw and the CLAMPED output value
        # itself is the unsaturated raw physical number (rounded to 4dp).
        # decay still clamps to 30 (Sec.6 item 6, unaffected by this test).
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", OVERSIZE_HARD_ROOM)
            result = run_cli("--scene", str(scene_path))
        self.assertEqual(0, result.returncode, result.stderr)
        decay, wet = extract_decay_wet(json.loads(result.stdout))
        self.assertEqual(30.0, decay)
        self.assertAlmostEqual(0.5964, wet, delta=0.0005)
        # sanity: this must NOT be the saturated wet_max value -- otherwise
        # this test would be just as blind as the pre-existing anchor.
        self.assertLess(wet, 0.6)

    def test_concrete_room_r3_report_prints_room_constant_and_critical_distance(self):
        # Sec.3.2 anchor 3, the intermediates behind the final wet=0.6:
        # R=5.469, r_c=0.330m (design map §3.2). Grepped directly out of
        # the --report text so a wrong R/r_c formula is caught even though
        # the final wet is saturated (clamped to 0.6) and therefore blind
        # to r_c on its own.
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", ANCHOR_CONCRETE_ROOM_R3)
            result = run_cli("--scene", str(scene_path), "--report")
        self.assertEqual(0, result.returncode, result.stderr)

        r_line = next(
            (ln for ln in result.stdout.splitlines() if "房間常數 R" in ln), None)
        rc_line = next(
            (ln for ln in result.stdout.splitlines() if "臨界距離 r_c" in ln), None)
        self.assertIsNotNone(r_line, result.stdout)
        self.assertIsNotNone(rc_line, result.stdout)

        room_constant = _extract_trailing_float(r_line)
        critical_distance = _extract_trailing_float(rc_line)
        self.assertAlmostEqual(5.469, room_constant, delta=0.001)
        self.assertAlmostEqual(0.330, critical_distance, delta=0.001)


class ApplyTests(unittest.TestCase):
    """Sec.6 item 7: --apply must refuse output==input, and otherwise
    must change ONLY global.effects.reverb.{decay,wet}, preserving all
    other content and key order (Sec.5: "其餘 JSON 內容與鍵序不動"; also
    the repo-wide "output another file, never overwrite the original"
    culture)."""

    def test_apply_rejects_output_path_equal_to_input_path(self):
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            score_path = write_json(d, "in.score.json", SAMPLE_SCORE)
            scene_path = write_json(d, "scene.json", ANCHOR_CONCRETE_ROOM)
            result = run_cli(
                "--scene", str(scene_path),
                "--apply", str(score_path),
                "--output", str(score_path))
            self.assertNotEqual(0, result.returncode)
            # must not have touched the original file in the process of
            # refusing.
            self.assertEqual(
                SAMPLE_SCORE,
                json.loads(score_path.read_text(encoding="utf-8")))

    def test_apply_rejects_output_path_differing_only_by_case_from_input(self):
        # 2026-08-05 Opus finding: os.path.abspath() alone normalizes
        # separators/'..' but does NOT case-fold, so an --output whose
        # basename differs from --apply's input only by letter case slips
        # past a naive string-equality guard and silently overwrites the
        # original on case-insensitive filesystems (Windows, default
        # macOS) -- exactly the "output 不得等於 input" guarantee Sec.5
        # exists to enforce. Reproduced as a hash-before/after check so
        # this fails loudly if the guard regresses to string comparison.
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            score_path = write_json(d, "in.score.json", SAMPLE_SCORE)
            scene_path = write_json(d, "scene.json", ANCHOR_CONCRETE_ROOM)
            aliased_output = Path(d) / "IN.SCORE.JSON"  # same file, different case
            before = score_path.read_bytes()

            result = run_cli(
                "--scene", str(scene_path),
                "--apply", str(score_path),
                "--output", str(aliased_output))

            self.assertNotEqual(
                0, result.returncode,
                "case-aliased --output must be rejected exactly like an "
                "identical path, not silently accepted")
            after = score_path.read_bytes()
            self.assertEqual(
                before, after,
                "input file bytes changed -- case-aliased --output "
                "overwrote the original input")

    def test_apply_changes_only_reverb_decay_and_wet_rest_is_deep_equal(self):
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            score_path = write_json(d, "in.score.json", SAMPLE_SCORE)
            scene_path = write_json(d, "scene.json", ANCHOR_CONCRETE_ROOM)
            output_path = Path(d) / "out.score.json"
            result = run_cli(
                "--scene", str(scene_path),
                "--apply", str(score_path),
                "--output", str(output_path))
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(output_path.exists())

            output_doc = json.loads(output_path.read_text(encoding="utf-8"))
            new_reverb = output_doc["global"]["effects"]["reverb"]

            # sanity: apply actually changed the values away from the
            # fixture's deliberately-distinctive originals, so this test
            # cannot pass vacuously.
            self.assertNotAlmostEqual(
                SAMPLE_SCORE["global"]["effects"]["reverb"]["decay"],
                new_reverb["decay"], delta=0.01)
            self.assertAlmostEqual(7.209, new_reverb["decay"], delta=0.01)

            patched_input = copy.deepcopy(SAMPLE_SCORE)
            patched_input["global"]["effects"]["reverb"]["decay"] = \
                new_reverb["decay"]
            patched_input["global"]["effects"]["reverb"]["wet"] = \
                new_reverb["wet"]
            self.assertEqual(patched_input, output_doc)

            assert_same_key_order(self, SAMPLE_SCORE, output_doc)

    def test_apply_without_output_flag_fails(self):
        # --apply MUST be paired with --output (Sec.5); there is no
        # --in-place option.
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            score_path = write_json(d, "in.score.json", SAMPLE_SCORE)
            scene_path = write_json(d, "scene.json", ANCHOR_CONCRETE_ROOM)
            result = run_cli(
                "--scene", str(scene_path), "--apply", str(score_path))
        self.assertNotEqual(0, result.returncode)


class DeterminismTests(unittest.TestCase):
    """Sec.6 item 8: identical input, run twice, byte-identical stdout
    (no timestamps, no randomness)."""

    def test_plain_mode_same_input_twice_is_byte_identical(self):
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", ANCHOR_TILE_ROOM)
            r1 = run_cli("--scene", str(scene_path))
            r2 = run_cli("--scene", str(scene_path))
        self.assertEqual(0, r1.returncode, r1.stderr)
        self.assertEqual(r1.stdout, r2.stdout)

    def test_report_mode_same_input_twice_is_byte_identical(self):
        with tempfile.TemporaryDirectory(prefix="tsuki_scene_reverb_") as d:
            scene_path = write_json(d, "scene.json", ANCHOR_CONCRETE_ROOM_R3)
            r1 = run_cli("--scene", str(scene_path), "--report")
            r2 = run_cli("--scene", str(scene_path), "--report")
        self.assertEqual(0, r1.returncode, r1.stderr)
        self.assertEqual(r1.stdout, r2.stdout)


class ListPresetsTests(unittest.TestCase):
    """Sec.6 item 9: every preset in the Sec.4 table scanned for
    decay in [0,30] and wet in [0,1] (schema-legal ranges)."""

    def test_full_preset_table_scan_is_within_schema_bounds(self):
        result = run_cli("--list-presets")
        self.assertEqual(0, result.returncode, result.stderr)
        presets = json.loads(result.stdout)
        self.assertEqual(KNOWN_PRESET_NAMES, set(presets.keys()))
        for name, values in presets.items():
            decay, wet = extract_decay_wet(values)
            self.assertGreaterEqual(decay, 0.0, name)
            self.assertLessEqual(decay, 30.0, name)
            self.assertGreaterEqual(wet, 0.0, name)
            self.assertLessEqual(wet, 1.0, name)

    def test_spot_check_two_documented_preset_values(self):
        # Sec.4 table, verbatim: cave 6.0/0.40, outdoor_open 0.10/0.05.
        result = run_cli("--list-presets")
        self.assertEqual(0, result.returncode, result.stderr)
        presets = json.loads(result.stdout)
        cave_decay, cave_wet = extract_decay_wet(presets["cave"])
        self.assertAlmostEqual(6.0, cave_decay, delta=1e-6)
        self.assertAlmostEqual(0.40, cave_wet, delta=1e-6)

        outdoor_decay, outdoor_wet = extract_decay_wet(presets["outdoor_open"])
        self.assertAlmostEqual(0.10, outdoor_decay, delta=1e-6)
        self.assertAlmostEqual(0.05, outdoor_wet, delta=1e-6)


class ListMaterialsTests(unittest.TestCase):
    """Sec.6 item 10: every material in the Sec.3.1 table scanned for
    alpha in the open interval (0,1)."""

    def test_full_material_table_scan_alpha_in_open_unit_interval(self):
        result = run_cli("--list-materials")
        self.assertEqual(0, result.returncode, result.stderr)
        materials = json.loads(result.stdout)
        self.assertEqual(KNOWN_MATERIAL_NAMES, set(materials.keys()))
        for name, alpha in materials.items():
            self.assertGreater(float(alpha), 0.0, name)
            self.assertLess(float(alpha), 1.0, name)

    def test_spot_check_two_documented_material_alphas(self):
        # Sec.3.1 table, verbatim: concrete 0.02, audience_seated 0.80.
        result = run_cli("--list-materials")
        self.assertEqual(0, result.returncode, result.stderr)
        materials = json.loads(result.stdout)
        self.assertAlmostEqual(0.02, float(materials["concrete"]), delta=1e-6)
        self.assertAlmostEqual(
            0.80, float(materials["audience_seated"]), delta=1e-6)


if __name__ == "__main__":
    unittest.main()
