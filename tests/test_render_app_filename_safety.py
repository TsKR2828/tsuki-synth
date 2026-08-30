"""Regression sentinel for F-07 (workcard D): src/cli/RenderApp.cpp's
isSafeOutputName() output-filename gate.

Before this fix, isSafeOutputName() only rejected an empty name, a path
separator, "..", or an absolute path. Windows-reserved characters
(``: * ? " < > |``), control characters, a trailing '.'/space, and Windows
reserved device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9) all slipped
through the gate and only surfaced later as an opaque "FAILED to render"
once the renderer itself gave up.

There is no C++ test target that compiles RenderApp.cpp (it is a
juce_add_console_app with its own main() -- see CMakeLists.txt), so per the
workcard's file-scope constraint (CMakeLists.txt is out of scope) this drives
the real, already-built TsukiSynthCLI.exe as a subprocess instead of adding a
new C++ test target. This is the same "no test target reaches this code, so
drive the built CLI directly" pattern already used by
RealDumpModesRadiationSentinelTests in tests/test_specimen_verify.py.

Each malformed-name case here fails on the pre-fix binary (the CLI accepts
the name, then fails deep inside the renderer with no specific reason) and
passes on the fixed binary (rejected up front, with a reason naming the
violated rule, and no output written).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# verify_score.py itself imports loudness etc. by bare module name -- push
# tools/ onto sys.path first so that resolves (same pattern as
# tests/test_stem_verify.py).
sys.path.insert(0, str(ROOT / "tools"))
import verify_score


def _make_score(export_filename):
    """A minimal, fast-to-render 1-event score whose only purpose is to
    exercise the CLI's output-filename gate. Not a musical/physics fixture --
    do not reuse this for anything that cares about the rendered audio."""
    return {
        "$schema": "TsukiSynth Score v1",
        "meta": {
            "title": "F-07 filename gate sentinel",
            "id": "renderapp_filename_gate_sentinel",
            "author": "workcard-D sentinel",
            "description": "Drives TsukiSynthCLI's output-filename gate only.",
        },
        "global": {
            "bpm": 100,
            "sample_rate": 48000,
            "master_volume": 0.8,
            "effects": {
                "reverb": {"decay": 0, "wet": 0},
                "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                "distortion": {"type": "overdrive", "drive": 0, "instability": 0, "wet": 0},
            },
        },
        "events": [
            {
                "time": 0.0, "duration": 0.2, "engine": "cimbalom", "note": 60,
                "velocity": 0.7,
                "params": {"material": "steel", "diameter_mm": 0.8,
                           "strike_position": 0.3, "exciter": "wood_mallet"},
            }
        ],
        "export": {
            "filename": export_filename, "format": "wav", "bit_depth": 16,
            "normalize": True, "tail_silence_ms": 50,
        },
    }


class RenderAppFilenameSafetyTests(unittest.TestCase):
    """Drives the real CLI (not a reimplementation of isSafeOutputName) so
    these cases actually exercise src/cli/RenderApp.cpp."""

    @classmethod
    def setUpClass(cls):
        cls.cli = verify_score.find_cli()
        if cls.cli is None:
            raise unittest.SkipTest(
                "TsukiSynthCLI not built -- run cmake --build build "
                "--target TsukiSynthCLI first (X4 regulation)")

    def _render(self, export_filename, workdir):
        score_path = Path(workdir) / "sentinel.score.json"
        score_path.write_text(json.dumps(_make_score(export_filename)),
                               encoding="utf-8")
        out_dir = Path(workdir) / "out"
        proc = subprocess.run(
            [str(self.cli), str(score_path), "--output", str(out_dir)],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60)
        return proc, out_dir

    def _assert_rejected(self, export_filename, reason_fragment):
        with tempfile.TemporaryDirectory() as workdir:
            proc, out_dir = self._render(export_filename, workdir)
            self.assertNotEqual(
                proc.returncode, 0,
                f"CLI should refuse to render {export_filename!r}, "
                f"stdout={proc.stdout!r} stderr={proc.stderr!r}")
            self.assertIn(
                "REJECTED unsafe filename", proc.stdout,
                f"expected an up-front rejection message for "
                f"{export_filename!r}, got stdout={proc.stdout!r}")
            self.assertIn(
                reason_fragment.lower(), proc.stdout.lower(),
                f"rejection message for {export_filename!r} should name the "
                f"specific rule ({reason_fragment!r}), got "
                f"stdout={proc.stdout!r}")
            # No audio (or manifest) should have been written for a name
            # that was rejected before rendering ever started.
            if out_dir.is_dir():
                leftovers = [p.name for p in out_dir.iterdir()]
                self.assertEqual(
                    leftovers, [],
                    f"a rejected filename must not produce any output, "
                    f"found {leftovers}")

    def test_windows_reserved_character_is_rejected(self):
        # The exact name from the F-07 audit finding.
        self._assert_rejected("carrier:hidden", "reserved character")

    def test_control_character_is_rejected(self):
        self._assert_rejected("carrier\x01hidden", "control character")

    def test_trailing_dot_is_rejected(self):
        self._assert_rejected("carrier.", "trailing")

    @unittest.skip(
        "unreachable through export.filename: ScoreParser::readString() "
        "(src/score/ScoreParser.h:1153) calls .trim() on every string field "
        "at parse time, so a trailing space never survives to reach "
        "isSafeOutputName() through this entry point. The fallback path "
        "(scoreFile.getFileNameWithoutExtension(), used when export.filename "
        "is absent) *could* carry a trailing space, but constructing such a "
        "file on Windows requires an NT '\\\\?\\' path to bypass Win32's own "
        "trailing-space stripping -- out of scope for this sentinel. The "
        "isSafeOutputName() rejection branch for a trailing space still "
        "exists in the fix (see src/cli/RenderApp.cpp) as defense-in-depth "
        "for any future caller that skips ScoreParser's trim.")
    def test_trailing_space_is_rejected(self):
        self._assert_rejected("carrier ", "trailing")

    def test_reserved_device_name_is_rejected(self):
        self._assert_rejected("CON", "reserved device name")

    def test_reserved_device_name_is_rejected_case_insensitively(self):
        self._assert_rejected("com1", "reserved device name")

    def test_legal_filename_still_renders(self):
        with tempfile.TemporaryDirectory() as workdir:
            proc, out_dir = self._render("carrier_safe_name", workdir)
            self.assertNotIn(
                "REJECTED unsafe filename", proc.stdout,
                f"a legal filename must not be rejected, "
                f"stdout={proc.stdout!r}")
            self.assertEqual(
                proc.returncode, 0,
                f"expected a successful render for a legal filename, "
                f"stdout={proc.stdout!r} stderr={proc.stderr!r}")
            wav = out_dir / "carrier_safe_name.wav"
            self.assertTrue(
                wav.is_file(),
                f"expected {wav} to exist after a successful render, "
                f"out_dir contains: {list(out_dir.iterdir()) if out_dir.is_dir() else '(missing)'}")


if __name__ == "__main__":
    unittest.main()
