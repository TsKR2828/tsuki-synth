"""Regression tests for whole-score verification routing contracts."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "verify_score", ROOT / "tools" / "verify_score.py")
vs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vs)


class VerifyScoreRoutingTests(unittest.TestCase):
    def test_layered_top_level_mode_scan_is_explicit_na(self):
        original = vs.check_modes
        vs.check_modes = lambda *_args, **_kwargs: self.fail(
            "layered root must not be passed to CLI --dump-modes")
        try:
            checks, dumped = vs.check_top_level_modes(
                Path("unused-cli"), Path("composite.score.json"),
                {"layers": [{"source": "leaf.score.json"}]}, [])
        finally:
            vs.check_modes = original
        self.assertEqual([], dumped)
        self.assertEqual(1, len(checks))
        self.assertTrue(checks[0].ok)
        self.assertEqual("modes.top_level_not_applicable", checks[0].name)
        self.assertEqual("N/A", checks[0].detail["status"])

    def test_event_score_still_delegates_to_real_mode_check(self):
        sentinel = [vs.Check("sentinel", True, "delegated")]
        original = vs.check_modes
        vs.check_modes = lambda cli, path, events: (sentinel, ["dump"])
        try:
            checks, dumped = vs.check_top_level_modes(
                Path("cli"), Path("event.score.json"),
                {"events": [{}]}, [{}])
        finally:
            vs.check_modes = original
        self.assertIs(sentinel, checks)
        self.assertEqual(["dump"], dumped)


class RestRmsPerChannelTests(unittest.TestCase):
    """Contract: rest RMS is judged per channel (loudest channel wins), NOT
    on a (L+R)/2 mono mixdown -- decorrelated stereo content cancels in the
    mixdown and would be under-measured (2026-07-18 measurement-method fix;
    REST_RMS_LIMIT_DBFS itself is unchanged at -50 dBFS)."""

    SR = 1000  # small synthetic rate keeps the arrays tiny; nothing decodes it

    def _events_with_one_rest(self):
        # Sounding 0..1s and 10..11s. The gap 1..10s becomes a rest judged
        # from 1s + REST_DECAY_ALLOWANCE_S to 10s.
        return [{"time": 0.0, "duration": 1.0},
                {"time": 10.0, "duration": 1.0}]

    def _stereo_rest_noise(self, per_channel_rms, anti_correlated):
        """11s stereo array, silent except the judged rest window, which is
        filled with noise of exactly `per_channel_rms` RMS per channel.
        anti_correlated=True puts x on L and -x on R, so the (L+R)/2
        mixdown is EXACTLY zero while each channel is loud."""
        n = int(11.0 * self.SR)
        audio = np.zeros((n, 2))
        start = int((1.0 + vs.REST_DECAY_ALLOWANCE_S) * self.SR)
        end = int(10.0 * self.SR)
        rng = np.random.default_rng(20260718)
        x = rng.standard_normal(end - start)
        x *= per_channel_rms / np.sqrt(np.mean(x ** 2))
        audio[start:end, 0] = x
        audio[start:end, 1] = -x if anti_correlated else x
        return audio

    def _rest_check(self, checks):
        found = [c for c in checks if c.name == "rests.rms_below_limit"]
        self.assertEqual(1, len(found))
        return found[0]

    def test_anti_correlated_rest_noise_fails_despite_silent_mixdown(self):
        # -40 dBFS per channel: 10 dB ABOVE the -50 dBFS limit, yet the
        # mono mixdown is bit-exactly silent. The old mixdown method passed
        # this; the per-channel method must fail it.
        events = self._events_with_one_rest()
        audio = self._stereo_rest_noise(10.0 ** (-40.0 / 20.0), True)
        self.assertEqual(0.0, float(np.max(np.abs(audio.mean(axis=1)))),
                         "test premise: mixdown must be exactly silent")
        check = self._rest_check(vs.check_rests(events, self.SR, audio))
        self.assertFalse(check.ok)

    def test_quiet_rest_passes_on_every_channel(self):
        # -80 dBFS per channel on both channels: well below the limit.
        events = self._events_with_one_rest()
        audio = self._stereo_rest_noise(10.0 ** (-80.0 / 20.0), False)
        check = self._rest_check(vs.check_rests(events, self.SR, audio))
        self.assertTrue(check.ok)

    def test_max_channel_rms_reports_loudest_channel_not_mixdown(self):
        rng = np.random.default_rng(7)
        x = rng.standard_normal(4096)
        x *= 0.01 / np.sqrt(np.mean(x ** 2))  # exactly -40 dBFS per channel
        stereo = np.stack([x, -x], axis=1)
        self.assertAlmostEqual(-40.0, vs.max_channel_rms_dbfs(stereo), places=6)
        # the mixdown of the same material measures as digital silence
        self.assertEqual(-120.0, vs.rms_dbfs(stereo.mean(axis=1)))
        # 1D input is accepted as a single channel
        self.assertAlmostEqual(-40.0, vs.max_channel_rms_dbfs(x), places=6)


class RenderManifestContractTests(unittest.TestCase):
    """Contract: manifest v2 must carry wav_sha256 matching the bytes of the
    output file on disk; v1 (legacy binaries) stays accepted without a hash;
    anything else fails."""

    WAV_BYTES = b"RIFF-not-actually-decoded-by-the-manifest-check"

    def _base_manifest(self, contract, event_count=2):
        return {
            "contract": contract,
            "score": "../scores/examples/example.score.json",
            "output": "out.wav",
            "sample_rate": 48000,
            "random_seed": 1,
            "input_event_count": event_count,
            "input_layer_count": 0,
            "normalize": True,
            "pre_normalize_peak": 0.25,
            "applied_gain": 3.8,
            "samples_at_or_above_full_scale": 0,
        }

    def _run(self, manifest_dict, wav_bytes=WAV_BYTES, event_count=2):
        with tempfile.TemporaryDirectory(prefix="tsuki_manifest_test_") as d:
            wav_path = Path(d) / "out.wav"
            wav_path.write_bytes(wav_bytes)
            manifest_path = Path(d) / "out.wav.render.json"
            manifest_path.write_text(json.dumps(manifest_dict), encoding="utf-8")
            events = [{}] * event_count
            return vs.check_render_manifest(manifest_path, wav_path, events)

    def _sha(self, data=WAV_BYTES):
        import hashlib
        return hashlib.sha256(data).hexdigest()

    def test_v2_with_matching_hash_passes(self):
        manifest = self._base_manifest(vs.MANIFEST_CONTRACT_V2)
        manifest["wav_sha256"] = self._sha()
        check, measured = self._run(manifest)
        self.assertTrue(check.ok, check.message)
        self.assertEqual(self._sha(), check.detail["actual_wav_sha256"])
        self.assertEqual(vs.MANIFEST_CONTRACT_V2, check.detail["manifest_contract"])
        self.assertEqual(0.25, measured["pre_normalize_peak"])
        self.assertEqual(3.8, measured["normalization_gain"])
        self.assertEqual(0, measured["pre_normalize_full_scale_samples"])

    def test_v2_hash_comparison_is_case_insensitive(self):
        # juce::String::toHexString and hashlib both emit lowercase today,
        # but the contract is the hash value, not its letter case.
        manifest = self._base_manifest(vs.MANIFEST_CONTRACT_V2)
        manifest["wav_sha256"] = self._sha().upper()
        check, _ = self._run(manifest)
        self.assertTrue(check.ok, check.message)

    def test_v2_with_wrong_hash_fails(self):
        manifest = self._base_manifest(vs.MANIFEST_CONTRACT_V2)
        manifest["wav_sha256"] = "0" * 64
        check, _ = self._run(manifest)
        self.assertFalse(check.ok)
        self.assertIn("wav_sha256", check.message)

    def test_v2_detects_wav_bytes_changed_after_manifest_written(self):
        manifest = self._base_manifest(vs.MANIFEST_CONTRACT_V2)
        manifest["wav_sha256"] = self._sha(b"the bytes the renderer wrote")
        check, _ = self._run(manifest, wav_bytes=b"tampered afterwards")
        self.assertFalse(check.ok)
        self.assertIn("wav_sha256", check.message)

    def test_v2_missing_wav_sha256_fails(self):
        manifest = self._base_manifest(vs.MANIFEST_CONTRACT_V2)
        check, _ = self._run(manifest)
        self.assertFalse(check.ok)

    def test_v1_legacy_still_accepted_without_hash(self):
        manifest = self._base_manifest(vs.MANIFEST_CONTRACT_V1)
        check, measured = self._run(manifest)
        self.assertTrue(check.ok, check.message)
        self.assertIn("v1 legacy", check.message)
        self.assertIsNone(check.detail["actual_wav_sha256"])
        self.assertEqual(0.25, measured["pre_normalize_peak"])

    def test_unknown_contract_fails(self):
        manifest = self._base_manifest("TsukiSynth Render Manifest v99")
        manifest["wav_sha256"] = self._sha()
        check, _ = self._run(manifest)
        self.assertFalse(check.ok)
        self.assertIn("unrecognised contract", check.message)

    def test_v2_event_count_mismatch_fails_even_with_valid_hash(self):
        manifest = self._base_manifest(vs.MANIFEST_CONTRACT_V2, event_count=2)
        manifest["wav_sha256"] = self._sha()
        check, _ = self._run(manifest, event_count=3)
        self.assertFalse(check.ok)
        self.assertIn("input_event_count", check.message)

    def test_missing_manifest_file_fails(self):
        with tempfile.TemporaryDirectory(prefix="tsuki_manifest_test_") as d:
            wav_path = Path(d) / "out.wav"
            wav_path.write_bytes(self.WAV_BYTES)
            manifest_path = Path(d) / "out.wav.render.json"  # never written
            check, _ = vs.check_render_manifest(manifest_path, wav_path, [])
        self.assertFalse(check.ok)


if __name__ == "__main__":
    unittest.main()
