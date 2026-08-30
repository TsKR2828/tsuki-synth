"""Regression tests for F-02: crossplatform_verify.emit() must not delete a
caller-owned, non-empty render directory unless --force-clean was asked for.

These do not need a built TsukiSynthCLI. The gate under test (containment
check + empty/non-empty check) runs before the render subprocess is ever
launched, so we hand emit() `sys.executable` as a stand-in "cli": invoking
`python <score.json> --output <dir>` fails immediately (Python cannot run a
JSON file as a script) with a clean non-zero exit, never an OS-level
"not a valid executable" error, and never touches the guard we are testing.
"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "crossplatform_verify", ROOT / "tools" / "crossplatform_verify.py")
cv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cv)

# Real probe score shipped in the repo; used so `score.is_file()` passes and
# we reach the render_dir guard we actually want to exercise.
PROBE_REL = "scores/examples/water_gong_clamped.score.json"
PROBE_STEM = "water_gong_clamped"

FAKE_CLI = Path(sys.executable)


def _link_directory(link_path, target):
    """Create a directory symlink (or a Windows junction) at `link_path`
    pointing at `target`, or raise SkipTest when the platform refuses.

    os.symlink needs Developer Mode or admin on Windows; `mklink /J`
    junctions do not, and Path.resolve() follows them identically, so the
    junction is a faithful stand-in for the escape being tested."""
    try:
        os.symlink(target, link_path, target_is_directory=True)
        return
    except (OSError, NotImplementedError, AttributeError):
        pass
    if os.name == "nt":
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link_path), str(target)],
            capture_output=True, text=True)
        if completed.returncode == 0:
            return
    raise unittest.SkipTest(
        "this platform will not let the test process create a directory link")


class EmitSafetyTests(unittest.TestCase):
    def setUp(self):
        # Shrink the fixed probe set to just one entry for every test in this
        # file, so emit() doesn't also try (and fail-early on) the other four
        # real probe scores via our fake "cli". Restored in tearDown.
        self._orig_probe_scores = cv.PROBE_SCORES
        cv.PROBE_SCORES = [PROBE_REL]

    def tearDown(self):
        cv.PROBE_SCORES = self._orig_probe_scores

    def test_non_empty_render_dir_is_refused_without_force_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            render_dir = out_dir / PROBE_STEM
            render_dir.mkdir(parents=True)
            sentinel = render_dir / "unrelated_user_file.txt"
            sentinel.write_text("do not delete me", encoding="utf-8")

            rc = cv.emit(out_dir, FAKE_CLI, "test-label", force_clean=False)

            self.assertTrue(sentinel.is_file(),
                             "sentinel file was deleted despite no --force-clean")
            self.assertEqual(sentinel.read_text(encoding="utf-8"),
                              "do not delete me")
            self.assertEqual(cv.EXIT_ERROR, rc)

    def test_non_empty_render_dir_is_cleaned_with_force_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            render_dir = out_dir / PROBE_STEM
            render_dir.mkdir(parents=True)
            sentinel = render_dir / "unrelated_user_file.txt"
            sentinel.write_text("do not delete me", encoding="utf-8")

            cv.emit(out_dir, FAKE_CLI, "test-label", force_clean=True)

            self.assertFalse(sentinel.exists(),
                              "--force-clean did not clear the pre-existing directory")

    def test_missing_render_dir_is_unaffected_by_the_new_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            render_dir = out_dir / PROBE_STEM
            self.assertFalse(render_dir.exists())

            cv.emit(out_dir, FAKE_CLI, "test-label", force_clean=False)

            # The guard must not have refused a render_dir that never existed;
            # it should have been created and handed to the (fake) renderer.
            self.assertTrue(render_dir.is_dir(),
                             "render_dir was not created on the normal, "
                             "no-pre-existing-directory path")


if __name__ == "__main__":
    unittest.main()

    def test_render_dir_linked_to_out_root_is_refused_even_with_force_clean(self):
        """P1 (2026-08-31): the containment check used to accept
        `resolved == out_dir`, so a <out>/<stem> link pointing back at <out>
        itself passed -- and --force-clean then rmtree'd the WHOLE --emit
        root (every other stem's render plus platform.json) while still
        reporting success. render_dir is always out_dir/stem, so equality is
        never legitimate; it must be refused."""
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "emit"
            out_dir.mkdir()
            # Contents of the emit root that must survive.
            sibling = out_dir / "some_other_render"
            sibling.mkdir()
            (sibling / "render.wav").write_text("previous render",
                                                encoding="utf-8")
            (out_dir / "platform.json").write_text("{}", encoding="utf-8")

            _link_directory(out_dir / PROBE_STEM, out_dir)

            rc = cv.emit(out_dir, FAKE_CLI, "test-label", force_clean=True)

            self.assertTrue((sibling / "render.wav").is_file(),
                            "a self-referential link wiped the whole --emit root")
            self.assertEqual((sibling / "render.wav").read_text(encoding="utf-8"),
                             "previous render")
            self.assertTrue((out_dir / "platform.json").is_file())
            self.assertEqual(cv.EXIT_ERROR, rc)

    def test_render_dir_escaping_out_root_is_refused_with_force_clean(self):
        """The ordinary escape: <out>/<stem> links somewhere else entirely."""
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "emit"
            out_dir.mkdir()
            outside = Path(tmp) / "precious"
            outside.mkdir()
            (outside / "thesis.txt").write_text("years of work", encoding="utf-8")

            _link_directory(out_dir / PROBE_STEM, outside)

            rc = cv.emit(out_dir, FAKE_CLI, "test-label", force_clean=True)

            self.assertTrue((outside / "thesis.txt").is_file(),
                            "data outside --emit was deleted")
            self.assertEqual(cv.EXIT_ERROR, rc)

    def test_render_dir_that_is_a_plain_file_fails_cleanly(self):
        """A file sitting where the render directory belongs must be reported
        as that score's failure, not raise NotADirectoryError out of emit()."""
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            blocker = out_dir / PROBE_STEM
            blocker.write_text("not a directory", encoding="utf-8")

            for force_clean in (False, True):
                with self.subTest(force_clean=force_clean):
                    rc = cv.emit(out_dir, FAKE_CLI, "test-label",
                                 force_clean=force_clean)
                    self.assertEqual(cv.EXIT_ERROR, rc)
                    self.assertTrue(blocker.is_file())
                    self.assertEqual(blocker.read_text(encoding="utf-8"),
                                     "not a directory")
