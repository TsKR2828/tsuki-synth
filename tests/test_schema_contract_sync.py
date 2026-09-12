"""WF0907-E8: schema <-> C++ ``--validate`` <-> converter cross-validation.

"What counts as a legal score" must have exactly one executable
definition: ``scores/schema/score.schema.json``. This module is the
single automated proof that the C++ ``--validate`` path (ScoreParser.h)
agrees with it -- not a hand-typed list of "known" boundary values, but a
program that WALKS the schema's own ``minimum``/``maximum``/
``exclusiveMinimum``/``enum``/``pattern``/``minLength``/``required``/
``type``/``oneOf`` keywords and turns every one of them into a mutation of
an otherwise-valid fixture. For every mutation, jsonschema's verdict and
``TsukiSynthCLI --validate``'s exit code must agree (both VALID or both
INVALID). Disagreement means the C++ parser is out of sync with the
schema it claims to implement.

Scope / deliberate limits (read before extending):
  - The walker descends through ``properties`` and single-schema
    ``items``/``additionalProperties`` nodes. It does NOT evaluate
    ``allOf``/``if``/``then`` conditionals (the per-engine
    ``params.propertyNames`` restriction) or array ``minItems``/
    ``maxItems`` -- those are structural/conditional shapes, not the
    scalar boundary values this card's audit (F-04/F-05,
    reports/gate_outputs/stem_verify_fur_elise_run.txt) flagged as
    drifted. The two manual "both events and layers" / "neither" cases
    below cover the one structural (``oneOf``) contract this suite does
    exercise directly.
  - ``events.*.params.<name>`` mutations are routed to a *representative*
    event whose engine actually owns that parameter (mirroring
    ScoreParser::parameterIsRelevant in src/score/ScoreParser.h), so a
    range/enum violation is not masked by an unrelated "parameter is
    not used by this engine" rejection.
  - Mutated *values* are never hand-typed from a separate "known bad
    values" list; they are derived mechanically from whatever the
    schema node itself declares (minimum-1, maximum+1, the
    exclusiveMinimum boundary itself, a sentinel outside an enum, a
    string that regex-fails a pattern, a fractional value for an
    ``integer``, a value of the wrong JSON type). Only the *sentinel
    constants* (e.g. the invalid-enum string) and the small pool of
    pattern-violating candidate strings are literals, because a
    schema keyword alone cannot name "a string outside this string
    enum" or "a string that fails this regex" without one.

Run standalone to (re)dump the constraint list used by the walker:
    python tests/test_schema_contract_sync.py --dump-constraints \
        output/wf0907/E8/constraints.json

CLI discovery: TSUKI_CLI env var first; else the single newest-by-mtime
TsukiSynthCLI(.exe) across BOTH build/ and build-wf/ (WF0907 C++ lane
build dir, see docs/workcards/WF0907_README.md Sec.1) -- not "build/ if
it has one at all, else build-wf/". Comparing mtimes across both
directories (rather than preferring one directory outright) matters
because the two are rebuilt independently by different lanes on the
same machine: build/ is intentionally the frozen 2026-08-31 binary the
Python/research lanes pin to (README Sec.1 -- never rebuilt), while
build-wf/ is what the C++ lane just rebuilt this run. Preferring
whichever directory happens to be listed/exist first would silently
test the *other* lane's stale binary instead of the one this change
was just built into. Tests that need the CLI are skipped (not failed)
when none is found, matching every other CLI-backed test in this
directory.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "scores" / "schema" / "score.schema.json"

# verify_score.py does `import loudness` as a sibling module -- tools/ must
# be on sys.path first (same convention as tests/test_stem_verify.py and
# tests/test_score_vs_midi_verify.py).
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "verify_score", ROOT / "tools" / "verify_score.py"
)
vs = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = vs
SPEC.loader.exec_module(vs)


def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# CLI discovery -- default build/, WF0907 C++ lane points this at build-wf/
# via TSUKI_CLI (README Sec.1: "C++ lane 的 Python GATE 一律加 --cli
# build-wf\...\TsukiSynthCLI.exe"); this test uses the env var form of the
# same override instead of a --cli flag because it runs under pytest.
#
# When TSUKI_CLI is unset, candidates are pooled from BOTH build/ and
# build-wf/ and the single newest-by-mtime file wins -- deliberately NOT
# "return build/'s newest if build/ has any at all, else look at
# build-wf/". build/ holds a binary the Python/research lanes pin to and
# the C++ lane must never rebuild (README Sec.1); build-wf/ is what this
# lane just rebuilt. A directory-preference order would keep resolving to
# build/'s (possibly much older, frozen) binary as long as it exists at
# all, even after this run rebuilt a fix into build-wf/ -- silently
# testing a stale CLI while looking green. Comparing mtimes across both
# directories means whichever lane rebuilt most recently is what a
# no-args `pytest tests -q` actually exercises.
# ---------------------------------------------------------------------------
def resolve_cli():
    env = os.environ.get("TSUKI_CLI")
    if env:
        p = Path(env)
        if p.is_file():
            return p
    cands = []
    for sub in ("build", "build-wf"):
        base = ROOT / sub
        if not base.exists():
            continue
        cands += [c for c in base.rglob("TsukiSynthCLI.exe") if c.is_file()]
        cands += [c for c in base.rglob("TsukiSynthCLI") if c.is_file()]
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)


def cli_validate_exit_code(cli, score_path, timeout=60):
    proc = subprocess.run(
        [str(cli), "--validate", str(score_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ---------------------------------------------------------------------------
# Extended base fixtures. NOT the on-disk scores/tests/melody_sentinel.
# score.json (never modified -- see WF0907_README.md "只碰你這張卡列出的
# 檔案"); these are separate in-memory documents built to give every schema
# leaf a real, navigable, already-valid location to mutate from. Every
# object/array container referenced by any walked schema path exists here;
# most *leaf values themselves* need not pre-exist (mutation is a plain
# dict/list assignment) except where a mutation needs to read the current
# value first (delete-a-required-key, or "make this integer fractional").
# ---------------------------------------------------------------------------

def _base_effects():
    return {
        "reverb": {"decay": 2.0, "wet": 0.1},
        "delay": {"time_ms": 100.0, "feedback": 0.2, "wet": 0.1},
        "wall": {"distance_m": 1.0, "material": "stone"},
        "distortion": {"type": "overdrive", "drive": 0.1, "instability": 0.0, "wet": 0.0},
        "eq": {"high_shelf_freq_hz": 2000.0, "high_shelf_gain_db": 0.0},
    }


def _base_meta():
    return {
        "title": "E8 contract fixture",
        "id": "e8_contract_fixture",
        "author": "wf0907_e8",
        "composer": "Test Composer",
        "work": "Test Work",
        "catalogue": "T.1",
        "opus_number": "1",
        "movement_number": 1,
        "movement_name": "Movement 1",
        "key": "C major",
        "description": "WF0907-E8 schema contract sync fixture",
        "created": "2026-09-08",
        "tags": ["test"],
        "mood": "calm",
        "use_case": "schema contract testing",
        "category": "test",
        "worldview": "test",
        "primary_type": "ui",
        "sound_type": "oneshot",
        "family_id": "e8_contract_fixture",
        "character": ["punch"],
        "loop_bpm": 100,
        "loop_bars": 4,
    }


def _base_export():
    return {
        "filename": "e8_contract_fixture",
        "export_filename": "e8_export",
        "format": "wav",
        "bit_depth": 24,
        "normalize": True,
        "tail_silence_ms": 200,
        "start_position": 0.0,
        "end_position": 1.0,
    }


def _base_source():
    return {
        "score_source": "test",
        "source_url": "https://example.com/x",
        "source_midi_file": "x.mid",
        "source_format": "smf1",
        "license": "CC0",
        "license_url": "https://example.com/license",
        "attribution": "a",
        "editorial_note": "n",
    }


def _base_events():
    return [
        {
            "event_id": "e0",
            "time": 0.0, "duration": 0.5, "engine": "cimbalom", "note": 60,
            "velocity": 0.7,
            "params": {
                "material": "steel", "strike_position": 0.3, "exciter": "wood_mallet",
                "damping_override": 50.0, "diameter_mm": 0.8, "num_strings": 3,
                "detuning_cents": 5.0, "tension_n": 100.0, "frequency_mode": "midi",
            },
            "glide": {"from_note": "C4", "duration_ms": 100.0, "curve": "linear"},
            "performance": {
                "track": "lead", "role": "lead", "midi_note": 60,
                "frequency_hz": 261.6, "source_duration_sec": 0.5,
                "intended_release_time": 0.45, "articulation": "legato",
                "articulation_gap_ms": 10.0, "phrase_end": False,
                "breath_after_ms": 0.0,
            },
            "comment": "base event",
        },
        {
            "time": 1.0, "duration": 0.5, "engine": "beam", "note": 64, "velocity": 0.6,
            "params": {
                "material": "steel", "strike_position": 0.3, "exciter": "wood_mallet",
                "damping_override": 50.0, "length_mm": 100.0, "width_mm": 25.0,
                "thickness_mm": 2.0, "beam_boundary": "cantilever", "frequency_mode": "midi",
            },
        },
        {
            "time": 2.0, "duration": 0.5, "engine": "plate", "note": 67, "velocity": 0.6,
            "params": {
                "material": "steel", "strike_position": 0.3, "exciter": "wood_mallet",
                "damping_override": 50.0, "radius_mm": 120.0, "thickness_mm": 2.0,
                "plate_free_edge": True, "frequency_mode": "midi",
            },
        },
        {
            "time": 3.0, "duration": 0.5, "engine": "fm", "note": 69, "velocity": 0.6,
            "params": {
                "fm_preset": 0, "fm_ratio": 2.0, "fm_index": 5.0,
                "fm_brightness": 0.5, "fm_feedback": 0.1, "fm_attack": 10.0,
                "fm_release": 500.0,
            },
        },
        {
            "time": 4.0, "duration": 0.5, "engine": "custom", "note": 71, "velocity": 0.6,
            "params": {
                "ratio_0": 1.0, "ratio_1": 2.0, "ratio_2": 3.0, "ratio_3": 4.0,
                "ratio_4": 5.0, "ratio_5": 6.0, "ratio_6": 7.0, "ratio_7": 8.0,
                "amp_0": 1.0, "amp_1": 0.5, "amp_2": 0.3, "amp_3": 0.2,
                "amp_4": 0.1, "amp_5": 0.1, "amp_6": 0.1, "amp_7": 0.1,
            },
        },
    ]


def make_events_base():
    return {
        "$schema": "TsukiSynth Score v1",
        "meta": _base_meta(),
        "global": {
            "bpm": 120, "sample_rate": 48000, "master_volume": 0.8,
            "random_seed": 42, "effects": _base_effects(),
        },
        "events": _base_events(),
        "export": _base_export(),
        "source": _base_source(),
        "tempo_map": [{"time": 0.0, "tick": 0, "quarter_bpm": 120.0,
                        "microseconds_per_quarter": 500000}],
        "time_signatures": [{"time": 0.0, "tick": 0, "numerator": 4, "denominator": 4}],
        "track_profiles": {
            "lead": {"role": "lead", "label": "Lead", "engine": "cimbalom",
                      "material": "steel", "diameter_mm": 0.8, "strike_position": 0.3,
                      "exciter": "wood_mallet", "damping_override": 50.0,
                      "base_velocity": 0.7},
        },
        "timing_policy": {
            "time_unit": "seconds", "renderer_note_off_ratio": 0.9,
            "duration_compensation": "n/a", "silence_representation": "n/a",
            "source_timing": "n/a", "articulation_policy": "n/a",
        },
        "rests": [{"track": "lead", "role": "lead", "time": 0.5, "duration": 0.5,
                    "approx_quarter_beats": 1.0, "kind": "rest"}],
        "phrases": [{"track": "lead", "role": "lead", "number": 1, "start": 0.0,
                      "end": 0.5, "breath_after_ms": 100.0}],
        "composition_thesis": "test",
        "crossfade_ms": 0,
    }


def make_layers_base():
    doc = make_events_base()
    del doc["events"]
    # melody_sentinel.score.json is the real, existing, 48kHz fixture this
    # layer references; --validate's full pipeline (ScoreRenderer::
    # validateLayeredScore) resolves "source" relative to the score file's
    # own directory and requires the resolved path to exist inside the
    # nearest "scores"-named ancestor directory, or (absent one) inside
    # that same directory -- see test_layers_base_cli_valid below for how
    # a plain tempdir satisfies this without needing to live under a real
    # scores/ tree.
    doc["layers"] = [{"source": "melody_sentinel.score.json",
                        "region": [0.0, 1.0], "gain": 1.0}]
    return doc


EVENTS_BASE = make_events_base()
LAYERS_BASE = make_layers_base()

# engine used at each representative index in EVENTS_BASE["events"]
_EVENT_ENGINES = ["cimbalom", "beam", "plate", "fm", "custom"]


def _param_relevant(engine, key):
    """Mirrors ScoreParser::parameterIsRelevant (src/score/ScoreParser.h)
    -- used only to pick WHICH representative event a params.<key>
    mutation is injected into, never to decide what value is invalid."""
    if key in ("material", "strike_position", "exciter", "damping_override"):
        return engine != "fm"
    if key.startswith("fm_"):
        return engine == "fm"
    if key.startswith("ratio_") or key.startswith("amp_"):
        return engine == "custom"
    if key in ("diameter_mm", "num_strings", "detuning_cents", "tension_n"):
        return engine in ("string", "cimbalom", "piano")
    if key in ("length_mm", "width_mm", "beam_boundary"):
        return engine in ("beam", "tongue_drum")
    if key == "frequency_mode":
        return engine in ("string", "cimbalom", "piano", "beam", "tongue_drum",
                           "plate", "water_gong")
    if key in ("radius_mm", "plate_free_edge"):
        return engine in ("plate", "water_gong")
    if key == "thickness_mm":
        return engine in ("beam", "tongue_drum", "plate", "water_gong")
    return False


def _engine_index_for_param(key):
    for idx, engine in enumerate(_EVENT_ENGINES):
        if _param_relevant(engine, key):
            return idx
    return None


# ---------------------------------------------------------------------------
# Schema -> concrete invalid-value mutations. See module docstring.
# ---------------------------------------------------------------------------

_PATTERN_CANDIDATES = ["@@@INVALID@@@", "../evil/path", "UPPER CASE 123", "  spaced  "]


def _pattern_violation(pattern):
    for candidate in _PATTERN_CANDIDATES:
        if re.search(pattern, candidate) is None:
            return candidate
    raise AssertionError(
        f"no candidate in _PATTERN_CANDIDATES violates pattern {pattern!r}; "
        "extend _PATTERN_CANDIDATES")


FRACTIONAL = object()  # marker: apply_mutation resolves this from the base's current value


def _resolve_scalar_mutations(node):
    """A schema leaf node -> [(reason, mutated_value_or_FRACTIONAL), ...]."""
    out = []
    if "minimum" in node:
        out.append(("minimum", node["minimum"] - 1))
    if "maximum" in node:
        out.append(("maximum", node["maximum"] + 1))
    if "exclusiveMinimum" in node:
        out.append(("exclusiveMinimum", node["exclusiveMinimum"]))
    if "enum" in node and node["enum"]:
        values = node["enum"]
        if all(isinstance(v, str) for v in values):
            out.append(("enum", "__WF0907_E8_INVALID_ENUM__"))
        else:
            out.append(("enum", -999999))
    if "pattern" in node:
        out.append(("pattern", _pattern_violation(node["pattern"])))
    if node.get("minLength", 0) and node["minLength"] > 0:
        out.append(("minLength", ""))
    t = node.get("type")
    if t == "integer":
        out.append(("type_wrong", "__WF0907_E8_WRONG_TYPE__"))
        out.append(("type_fractional", FRACTIONAL))
    elif t == "number":
        out.append(("type_wrong", "__WF0907_E8_WRONG_TYPE__"))
    elif t == "string":
        out.append(("type_wrong", 123456789))
    elif t == "boolean":
        out.append(("type_wrong", "__WF0907_E8_WRONG_TYPE__"))
    return out


def resolve_node_mutations(node):
    """A property schema (possibly ``oneOf``) -> [(reason, value), ...]."""
    if isinstance(node.get("oneOf"), list):
        out = []
        for branch in node["oneOf"]:
            for reason, value in _resolve_scalar_mutations(branch):
                # type_fractional reads the fixture's CURRENT value and
                # adds 0.5 to it; that is only meaningful when the base
                # fixture actually holds a value of the branch's own type
                # at this path (e.g. "note" holds an int, so its integer
                # branch could use it -- but this schema's oneOf fields are
                # each fixtured as ONE concrete type to exercise the OTHER
                # branch's pattern, so a mismatched-type branch's
                # type_fractional is not applicable here; the branch's
                # own minimum/maximum/enum/pattern mutations below don't
                # need the current value and still fully exercise it).
                if reason == "type_fractional":
                    continue
                out.append(("oneOf:" + reason, value))
        return out
    return _resolve_scalar_mutations(node)


_PARAMS_SKIP = ("events", 0, "params")


def walk_schema(schema):
    """Walk the schema, yielding (path, reason, value) mutation descriptors.
    ``path`` is a tuple of dict-key / list-index segments locating the
    field inside EVENTS_BASE or LAYERS_BASE (world picked by path[0])."""
    entries = []

    def recurse(node, path):
        if not isinstance(node, dict):
            return
        if path == _PARAMS_SKIP:
            return  # handled by walk_params_schema() with engine routing
        if (isinstance(node.get("oneOf"), list) and "properties" not in node
                and node.get("type") is None):
            for reason, value in resolve_node_mutations(node):
                entries.append((path, reason, value))
            return
        t = node.get("type")
        is_object = t == "object" or "properties" in node or isinstance(
            node.get("additionalProperties"), dict)
        if is_object:
            if isinstance(node.get("required"), list):
                entries.append((path, "required", node["required"]))
            for name, sub in node.get("properties", {}).items():
                recurse(sub, path + (name,))
            ap = node.get("additionalProperties")
            if isinstance(ap, dict):
                recurse(ap, path + ("lead",))  # the one track_profiles key in the base
            return
        if t == "array" or "items" in node:
            items = node.get("items")
            if isinstance(items, dict):
                recurse(items, path + (0,))
            return
        for reason, value in resolve_node_mutations(node):
            entries.append((path, reason, value))

    recurse(schema, ())
    return entries


def walk_params_schema(schema):
    entries = []
    params_props = (schema["properties"]["events"]["items"]["properties"]
                     ["params"]["properties"])
    for name, sub in params_props.items():
        idx = _engine_index_for_param(name)
        if idx is None:
            continue
        for reason, value in resolve_node_mutations(sub):
            entries.append((("events", idx, "params", name), reason, value))
    return entries


def build_mutation_matrix(schema):
    """Final flat list of (world, path, reason, value) mutations, expanding
    every ``required`` entry into one deletion mutation per required key."""
    raw = walk_schema(schema) + walk_params_schema(schema)
    matrix = []
    for path, reason, value in raw:
        if reason == "required":
            for key in value:
                final_path = path + (key,)
                world = "layers" if final_path[0] == "layers" else "events"
                matrix.append((world, final_path, "required_delete", None))
        else:
            world = "layers" if path and path[0] == "layers" else "events"
            matrix.append((world, path, reason, value))
    return matrix


def apply_mutation(world, path, reason, value):
    base = LAYERS_BASE if world == "layers" else EVENTS_BASE
    doc = copy.deepcopy(base)
    parent = doc
    for seg in path[:-1]:
        parent = parent[seg]
    last = path[-1]
    if reason == "required_delete":
        del parent[last]
        return doc
    if value is FRACTIONAL:
        parent[last] = float(parent[last]) + 0.5
        return doc
    parent[last] = value
    return doc


def mutation_label(world, path, reason):
    return f"{world}:" + ".".join(str(p) for p in path) + f" [{reason}]"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class BaseFixtureSanityTests(unittest.TestCase):
    """The two extended base fixtures must themselves be valid -- otherwise
    every mutation built on top of them is meaningless."""

    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema()
        cls.validator = Draft202012Validator(cls.schema)
        cls.cli = resolve_cli()

    def test_events_base_is_schema_valid(self):
        errors = list(self.validator.iter_errors(EVENTS_BASE))
        self.assertEqual([], [e.message for e in errors])

    def test_layers_base_is_schema_valid(self):
        errors = list(self.validator.iter_errors(LAYERS_BASE))
        self.assertEqual([], [e.message for e in errors])

    def test_events_base_cli_valid(self):
        if self.cli is None:
            self.skipTest("TsukiSynthCLI not found (set TSUKI_CLI or build build-wf/build)")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events_base.score.json"
            path.write_text(json.dumps(EVENTS_BASE), encoding="utf-8")
            code, out, err = cli_validate_exit_code(self.cli, path)
            self.assertEqual(0, code, msg=f"stdout={out!r} stderr={err!r}")

    def test_layers_base_cli_valid(self):
        """Written into a tempfile.TemporaryDirectory() *outside* the repo
        (never scores/tests/, which is a version-controlled directory
        shared by all three WF0907 lanes -- a killed process would leave a
        stray file behind for someone else to trip over) because the full
        --validate pipeline for a layered score additionally resolves the
        referenced layer file on disk (ScoreRenderer::validateLayeredScore),
        unlike the mutation matrix below where every mutation is already
        invalid at the ScoreParser::parse()/validateDocument() stage,
        before any file is touched. validateLayeredScore resolves
        layer.source relative to the score file's own directory and
        requires the resolved path to stay inside the nearest ancestor
        directory literally named "scores" -- or, absent one anywhere in
        the ancestry (true of a system tempdir), inside that same
        directory (see ScoreRenderer::layerAllowedRoot()). So a *copy* of
        the real melody_sentinel.score.json fixture the layer references
        is placed alongside the written file in that same tempdir, letting
        the whole tempdir stand in for the "scores" root instead of
        needing to be one."""
        if self.cli is None:
            self.skipTest("TsukiSynthCLI not found (set TSUKI_CLI or build build-wf/build)")
        sentinel_src = ROOT / "scores" / "tests" / "melody_sentinel.score.json"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            (tmp_dir / "melody_sentinel.score.json").write_text(
                sentinel_src.read_text(encoding="utf-8"), encoding="utf-8")
            path = tmp_dir / "layers_base.score.json"
            path.write_text(json.dumps(LAYERS_BASE), encoding="utf-8")
            code, out, err = cli_validate_exit_code(self.cli, path)
            self.assertEqual(0, code, msg=f"stdout={out!r} stderr={err!r}")


class MutationMatrixTests(unittest.TestCase):
    """The core cross-validation: schema-derived mutation -> jsonschema
    verdict must equal TsukiSynthCLI --validate verdict, for every mutation."""

    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema()
        cls.validator = Draft202012Validator(cls.schema)
        cls.cli = resolve_cli()
        cls.matrix = build_mutation_matrix(cls.schema)

    def test_matrix_is_nonempty(self):
        # sanity: the walker must actually find constraints, or this whole
        # suite silently proves nothing.
        self.assertGreater(len(self.matrix), 50, msg=(
            "schema walker found suspiciously few constraints; did the "
            "schema shape change out from under walk_schema()?"))

    def test_mutations_agree_with_cli(self):
        if self.cli is None:
            self.skipTest("TsukiSynthCLI not found (set TSUKI_CLI or build build-wf/build)")
        mismatches = []
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp) / "mutant.score.json"
            for i, (world, path, reason, value) in enumerate(self.matrix):
                doc = apply_mutation(world, path, reason, value)
                schema_errors = list(self.validator.iter_errors(doc))
                schema_valid = len(schema_errors) == 0
                tmp_path.write_text(json.dumps(doc), encoding="utf-8")
                code, out, err = cli_validate_exit_code(self.cli, tmp_path)
                cli_valid = (code == 0)
                if schema_valid != cli_valid:
                    mismatches.append(
                        f"{mutation_label(world, path, reason)}: "
                        f"jsonschema_valid={schema_valid} "
                        f"({len(schema_errors)} errors) "
                        f"cli_valid={cli_valid} (exit {code}) "
                        f"stdout={out.strip()!r} stderr={err.strip()!r}")
        self.assertEqual(
            [], mismatches,
            msg=f"{len(mismatches)}/{len(self.matrix)} mutations disagree:\n"
                + "\n".join(mismatches))

    def test_both_events_and_layers_present_is_invalid(self):
        if self.cli is None:
            self.skipTest("TsukiSynthCLI not found (set TSUKI_CLI or build build-wf/build)")
        doc = copy.deepcopy(EVENTS_BASE)
        doc["layers"] = copy.deepcopy(LAYERS_BASE["layers"])
        errors = list(self.validator.iter_errors(doc))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "both.score.json"
            path.write_text(json.dumps(doc), encoding="utf-8")
            code, out, err = cli_validate_exit_code(self.cli, path)
        self.assertGreater(len(errors), 0, "jsonschema should reject events+layers")
        self.assertNotEqual(0, code, msg=f"stdout={out!r} stderr={err!r}")

    def test_neither_events_nor_layers_present_is_invalid(self):
        if self.cli is None:
            self.skipTest("TsukiSynthCLI not found (set TSUKI_CLI or build build-wf/build)")
        doc = copy.deepcopy(EVENTS_BASE)
        del doc["events"]
        errors = list(self.validator.iter_errors(doc))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "neither.score.json"
            path.write_text(json.dumps(doc), encoding="utf-8")
            code, out, err = cli_validate_exit_code(self.cli, path)
        self.assertGreater(len(errors), 0, "jsonschema should reject neither events nor layers")
        self.assertNotEqual(0, code, msg=f"stdout={out!r} stderr={err!r}")


class CorpusValidityTests(unittest.TestCase):
    """R3: every corpus file must remain accepted by both the schema and
    the CLI -- none may be dropped from the corpus to make a GATE pass."""

    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema()
        cls.validator = Draft202012Validator(cls.schema)
        cls.cli = resolve_cli()
        cls.files = vs.find_all_scores(ROOT)

    def test_corpus_has_75_files(self):
        self.assertEqual(75, len(self.files), msg=(
            "corpus file count changed; WF0907_README.md Sec.3 and this "
            "card's GATE both assume 75 -- update the expectation only if "
            "the corpus genuinely grew/shrank on purpose, never to dodge a "
            "failure"))

    def test_corpus_is_schema_valid(self):
        failing = []
        for path in self.files:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
            errors = list(self.validator.iter_errors(doc))
            if errors:
                failing.append(f"{path}: {[e.message for e in errors]}")
        self.assertEqual([], failing)

    def test_corpus_is_cli_valid(self):
        if self.cli is None:
            self.skipTest("TsukiSynthCLI not found (set TSUKI_CLI or build build-wf/build)")
        failing = []
        for path in self.files:
            code, out, err = cli_validate_exit_code(self.cli, path, timeout=120)
            if code != 0:
                failing.append(f"{path}: exit {code} stdout={out.strip()!r} stderr={err.strip()!r}")
        self.assertEqual([], failing)


def _dump_constraints(out_path):
    schema = load_schema()
    matrix = build_mutation_matrix(schema)
    rows = []
    for world, path, reason, value in matrix:
        rows.append({
            "world": world,
            "path": [str(p) for p in path],
            "reason": reason,
            "mutated_value": "<FRACTIONAL:current+0.5>" if value is FRACTIONAL else value,
        })
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "total_mutations": len(rows),
        "mutations": rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} mutations to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--dump-constraints":
        _dump_constraints(sys.argv[2])
    else:
        unittest.main()
