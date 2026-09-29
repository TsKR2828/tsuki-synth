"""WF0907-E9: --dump-modes for layered scores.

Drives the real, already-built TsukiSynthCLI.exe as a subprocess (same
pattern as tests/test_render_app_filename_safety.py -- there is no C++ test
target that reaches RenderApp.cpp's --dump-modes dispatch or
ScoreRenderer::dumpModesLayered() directly).

Per WF0907_README.md Sec.1 ("C++ lane 專用建置目錄 build-wf"), this test
looks for the CLI ONLY under build-wf/ -- never under build/ (that binary is
the Python lane's and must not be assumed to carry this card's C++ change).

What is checked (workcard Sec.3):
  (a) flattened event count == sum of each leaf's own (non-layered)
      --dump-modes dumped_event_count.
  (b) every flattened event's "time" == that leaf's own event time (read
      straight from the leaf .score.json) + the layer's offset_s, where
      offset_s is recomputed HERE, independently, from the same formulas
      ScoreRenderer::dumpModesLayered() documents mirroring from
      renderLayered() (subDuration/eventEndTime, trimBuffer's trim-length
      formula, region crop, crossfade-clamped cumulative placement). A
      silent drift between the two implementations fails this test.
  (c) a layer cycle (A -> B -> A) exits 1 (nested layers were never
      supported to begin with, so B.hasLayers() already fails closed here --
      see the fixture files' own description fields).

Also checks that layer.gain is reflected as a plain linear multiply on the
"amp" fields (mirroring AudioBuffer::applyGain in renderLayered(), not an
invented normalization).
"""

import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _find_cli():
    """TsukiSynthCLI under build-wf/ (WF0907_README Sec.1 X4 regulation).

    WF0925b-TF (decision packet O16): same deterministic ranking as
    tools/physics_verify.py / tools/verify_score.py find_cli() (WF0925-P1),
    never decided by file mtime (the old fallback, max(st_mtime), could
    silently pick a newer Debug build). Ranked by, in order: a "Release"
    directory in the path below build-wf/ (case-insensitive); name pattern
    order TsukiSynthCLI.exe, tsukisynth-cli*, TsukiSynthCLI; fewer path
    components, then the lower-cased relative path string."""
    build_wf = ROOT / "build-wf"
    if not build_wf.exists():
        return None
    patterns = ("TsukiSynthCLI.exe", "tsukisynth-cli*", "TsukiSynthCLI")
    ranked = []
    for pattern_idx, pattern in enumerate(patterns):
        for cand in build_wf.rglob(pattern):
            if not cand.is_file():
                continue
            rel = cand.relative_to(build_wf)
            in_release = any(part.lower() == "release" for part in rel.parts[:-1])
            ranked.append(((0 if in_release else 1, pattern_idx, len(rel.parts),
                            rel.as_posix().lower()), cand))
    return min(ranked, key=lambda item: item[0])[1] if ranked else None


def _run_dump(cli, score_path, timeout=120):
    proc = subprocess.run(
        [str(cli), "--dump-modes", str(score_path)],
        capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout)
    return proc


SR_DEFAULT = 48000.0
SOUND_SPEED_MPS = 343.0
REVERB_COMB_LATENCY_S = (1617.0 + 23.0) / 44100.0
REVERB_ALLPASS_LATENCY_S = (556.0 + 441.0 + 341.0 + 225.0 + 4.0 * 23.0) / 44100.0
FM_DEFAULT_RELEASE_MS = 500.0


def wall_delay_seconds(effects):
    distance_m = (effects.get("wall") or {}).get("distance_m", 0.0)
    return (2.0 * distance_m / SOUND_SPEED_MPS) if distance_m > 0.0 else 0.0


def effect_tail_seconds(effects):
    """Mirrors ScoreRenderer::effectTailSeconds() (src/score/ScoreRenderer.h)
    verbatim, reading the same score.json effects block dumpModesLayered()'s
    C++ counterpart reads via ScoreGlobal.effects."""
    tail = 0.0
    reverb = effects.get("reverb") or {}
    reverb_wet = reverb.get("wet", 0.0)
    reverb_decay = reverb.get("decay", 2.0)
    if reverb_wet > 0.001:
        tail += REVERB_COMB_LATENCY_S + reverb_decay + REVERB_ALLPASS_LATENCY_S

    delay = effects.get("delay") or {}
    delay_wet = delay.get("wet", 0.0)
    delay_time_ms = delay.get("time_ms", 0.0)
    delay_feedback = delay.get("feedback", 0.0)
    if delay_wet > 0.001 and delay_time_ms > 0.0:
        repeats = (math.ceil(math.log(0.001) / math.log(delay_feedback))
                   if delay_feedback > 0.0 else 1.0)
        tail += max(1.0, repeats) * delay_time_ms * 0.001 * 1.10
    return tail


def leaf_max_t60_by_source_index(leaf_dump):
    """{source_index: max modal decay across every string's every partial}
    -- exactly what ScoreRenderer::eventMaxT60() takes the max of (see
    ScoreRenderer.h eventMaxT60(): 'for modes in modeSets: for mode in
    modes: maxT60 = max(maxT60, mode.decayTime)')."""
    out = {}
    for ev in leaf_dump["events"]:
        best = 0.0
        for string_modes in ev.get("strings", []):
            for mode in string_modes:
                d = mode.get("decay", 0.0)
                if math.isfinite(d) and d > best:
                    best = d
        out[ev["source_index"]] = best
    return out


def event_end_time(raw_event, max_t60):
    start = max(0.0, raw_event.get("time", 0.0))
    duration = max(0.0, raw_event.get("duration", 1.0))
    end = start + duration
    if raw_event.get("engine") == "fm":
        release_ms = (raw_event.get("params") or {}).get(
            "fm_release", FM_DEFAULT_RELEASE_MS)
        note_off = start + duration * 0.9
        end = max(end, note_off + release_ms * 0.001)
    else:
        note_off = duration * 0.9
        active = max_t60 if max_t60 <= note_off else note_off + (max_t60 - note_off) * 0.05
        end = max(end, start + active)
    return end


def sub_total_samples_after_trim(raw_leaf, leaf_dump, sr):
    """subDuration -> ceil(*sr)+1 -> trimBuffer()'s length formula, all
    reproduced analytically (see docstring at top of file and the matching
    C++ doc comment on ScoreRenderer::dumpModesLayered())."""
    t60_by_index = leaf_max_t60_by_source_index(leaf_dump)
    sub_duration = 0.0
    for i, ev in enumerate(raw_leaf.get("events", [])):
        if ev.get("velocity", 0.8) <= 0.0:
            continue
        end = event_end_time(ev, t60_by_index.get(i, 0.0))
        sub_duration = max(sub_duration, end)

    effects = (raw_leaf.get("global") or {}).get("effects") or {}
    sub_duration += wall_delay_seconds(effects)
    sub_duration += effect_tail_seconds(effects)
    export = raw_leaf.get("export") or {}
    sub_duration += export.get("tail_silence_ms", 500.0) / 1000.0

    sub_total_samples = int(math.ceil(sub_duration * sr)) + 1

    ts = min(max(export.get("start_position", 0.0), 0.0), 1.0)
    te = min(max(export.get("end_position", 1.0), ts), 1.0)
    trim_start = int(ts * sub_total_samples)
    trim_end = int(te * sub_total_samples)
    trim_length = trim_end - trim_start
    assert trim_length > 0, "fixture trims to empty buffer -- test setup bug"
    return trim_length


def region_crop_len(region, sub_total_samples):
    rs = min(max((region or [0.0, 1.0])[0], 0.0), 1.0)
    re = min(max((region or [0.0, 1.0])[1], 0.0), 1.0)
    if re < rs:
        rs, re = re, rs
    region_start = min(max(int(rs * sub_total_samples), 0), sub_total_samples - 1)
    region_end = min(max(int(re * sub_total_samples), region_start + 1), sub_total_samples)
    return region_end - region_start


def compute_expected_placements(composite_json, composite_dir, cli, sr):
    """Returns [(leaf_path, raw_leaf_json, leaf_dump_json, gain, offset_s), ...]
    in layer order, independently recomputing offset_s the same way
    ScoreRenderer::dumpModesLayered() derives it from renderLayered()'s
    formulas (crossfade-clamped cumulative placement of each layer's
    region-cropped, trimmed, tail-extended length)."""
    num_samples = []
    raws = []
    dumps = []
    gains = []
    paths = []
    for layer in composite_json["layers"]:
        leaf_path = (composite_dir / layer["source"]).resolve()
        raw_leaf = json.loads(leaf_path.read_text(encoding="utf-8"))
        proc = _run_dump(cli, leaf_path)
        assert proc.returncode == 0, (
            f"leaf dump-modes failed for {leaf_path}: {proc.stderr}")
        leaf_dump = json.loads(proc.stdout)

        sub_total = sub_total_samples_after_trim(raw_leaf, leaf_dump, sr)
        num_samples.append(region_crop_len(layer.get("region"), sub_total))
        raws.append(raw_leaf)
        dumps.append(leaf_dump)
        gains.append(layer.get("gain", 1.0))
        paths.append(leaf_path)

    crossfade_samples = int(composite_json.get("crossfade_ms", 0) / 1000.0 * sr)
    min_len = min(num_samples)
    crossfade_samples = min(crossfade_samples, min_len - 1)
    crossfade_samples = max(crossfade_samples, 0)

    offsets = []
    write_pos = 0
    for i, n in enumerate(num_samples):
        offsets.append(write_pos / sr)
        if i + 1 < len(num_samples):
            write_pos += n - crossfade_samples

    return list(zip(paths, raws, dumps, gains, offsets))


LAYERED_CORPUS = [
    ROOT / "scores" / "tests" / "test_layer.score.json",
    ROOT / "scores" / "examples" / "layered_transition.score.json",
    ROOT / "scores" / "originals" / "ai_radiance" / "ai_radiance_complete.score.json",
]


class DumpModesLayeredTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cli = _find_cli()
        if cls.cli is None:
            raise unittest.SkipTest(
                "TsukiSynthCLI not built under build-wf/ -- run "
                "cmake --build build-wf --config Release --target TsukiSynthCLI "
                "first (WF0907_README.md Sec.1 X4 regulation)")

    def _dump_composite(self, score_path):
        proc = _run_dump(self.cli, score_path, timeout=300)
        self.assertEqual(0, proc.returncode,
                          f"{score_path}: --dump-modes exit {proc.returncode}: {proc.stderr}")
        return json.loads(proc.stdout)

    def test_cycle_fixture_exits_1(self):
        cycle_a = ROOT / "scores" / "tests" / "wf0907_e9_cycle_a.score.json"
        proc = _run_dump(self.cli, cycle_a)
        self.assertEqual(1, proc.returncode)
        self.assertIn("Nested layer scores are not supported", proc.stderr)

    def test_all_corpus_files_flatten_and_place_events_correctly(self):
        for score_path in LAYERED_CORPUS:
            with self.subTest(score=score_path.name):
                self._check_one(score_path)

    def _check_one(self, score_path):
        composite_dump = self._dump_composite(score_path)
        self.assertTrue(composite_dump.get("layered"))

        composite_json = json.loads(score_path.read_text(encoding="utf-8"))
        sr = float((composite_json.get("global") or {}).get(
            "sample_rate", SR_DEFAULT))

        placements = compute_expected_placements(
            composite_json, score_path.parent, self.cli, sr)

        # (a) flattened event count == sum of each leaf's own dumped count.
        expected_total = sum(d["dumped_event_count"] for _, _, d, _, _ in placements)
        self.assertEqual(expected_total, composite_dump["dumped_event_count"])
        self.assertEqual(expected_total, len(composite_dump["events"]))
        self.assertEqual(sum(layer["event_count"] for layer in composite_dump["layers"]),
                          expected_total)

        # Reported per-layer offset_s/gain must match our independent
        # recomputation, and (b) every event's flattened "time" must equal
        # that leaf's own event time + the layer's offset_s.
        events_by_layer_source = {}
        for ev in composite_dump["events"]:
            events_by_layer_source.setdefault(ev["layer_source"], []).append(ev)

        for (leaf_path, raw_leaf, leaf_dump, gain, expected_offset), layer_meta in zip(
                placements, composite_dump["layers"]):
            self.assertAlmostEqual(expected_offset, layer_meta["offset_s"], places=9)
            self.assertEqual(gain, layer_meta["gain"])

            leaf_source = layer_meta["source"]
            flat_events = events_by_layer_source.get(leaf_source, [])
            self.assertEqual(len(flat_events), leaf_dump["dumped_event_count"])

            leaf_events_by_idx = {e["source_index"]: e for e in leaf_dump["events"]}
            for flat_ev in flat_events:
                self.assertEqual(1, flat_ev["layer_depth"])
                src_idx = flat_ev["source_index"]
                leaf_time = raw_leaf["events"][src_idx].get("time", 0.0)
                self.assertAlmostEqual(
                    leaf_time + expected_offset, flat_ev["time"], places=9,
                    msg=f"{score_path.name} layer={leaf_source} source_index={src_idx}")

                # Gain must be a plain linear multiply on "amp", mirroring
                # AudioBuffer::applyGain -- not a fabricated normalization.
                leaf_ev = leaf_events_by_idx[src_idx]
                for flat_partial, leaf_partial in zip(
                        flat_ev["partials"], leaf_ev["partials"]):
                    self.assertTrue(math.isclose(
                        flat_partial["amp"], leaf_partial["amp"] * gain,
                        rel_tol=1e-9, abs_tol=1e-12))


if __name__ == "__main__":
    unittest.main()
