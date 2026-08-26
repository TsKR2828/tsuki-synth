#!/usr/bin/env python3
"""Cross-platform render reproducibility harness (TODO.md Verification gap:
"Establish cross-platform numerical reproducibility rules (bit identity where
possible, numeric/audio tolerance otherwise)").

The existing determinism check in `verify_score.py` renders the same score
twice *on one machine* and requires an identical SHA256.  That proves the
renderer has no hidden nondeterminism (uninitialised memory, time/RNG leakage,
container iteration order), but it says nothing about whether a Linux/clang or
macOS/AppleClang build produces the same audio as the Windows/MSVC build that
every documented GATE was run on.  Different compilers legitimately differ in
floating-point contraction (FMA), libm transcendental accuracy (`sin`, `exp`,
`pow`) and vectorisation, so bit identity is *not* guaranteed and may not even
be desirable to force.

This tool therefore separates two questions that must not be conflated:

  1. **Bit identity** - are the rendered WAVs byte-for-byte identical across
     platforms?  Reported as a hard yes/no.
  2. **Numeric agreement** - if not bit identical, *how far apart* are they, in
     units that map onto the physical claims the project actually makes
     (sample-domain error floor, spectral magnitude deviation, pitch deviation
     in cents)?

Usage
-----
On each platform (typically one CI matrix leg per OS)::

    python tools/crossplatform_verify.py --emit out/linux --label ubuntu-24.04

Then, on the collecting job, with every emitted directory available::

    python tools/crossplatform_verify.py --compare out/windows out/linux out/macos

The first `--compare` directory is the **reference**; every other directory is
compared against it.  Windows/MSVC is the reference by convention because that
is the environment all existing GATE evidence in `reports/gate_outputs/` was
produced on.

Verdict / exit code policy (ROADMAP_PHYSICS.md Rule 1 and Rule 2)
----------------------------------------------------------------
Rule 2 forbids an AI from inventing or widening a tolerance.  There is no
registered cross-platform tolerance in ROADMAP_PHYSICS.md section 6 yet, and
this tool must not invent one.  So:

  exit 0  BIT_IDENTICAL      - every platform matched byte-for-byte.  No
                               tolerance needed, nothing to decide.
  exit 3  UNREGISTERED       - differences measured, but no tolerance file
                               exists.  The measured numbers are printed so
                               they can be registered in section 6 by hand.
                               This is *not* a pass and *not* a failure; it is
                               "no verdict is possible yet".
  exit 1  OUT_OF_TOLERANCE   - a tolerance file exists and a metric exceeds it.
  exit 2  ERROR              - missing/corrupt input, header mismatch, a score
                               that failed to render, etc.  Fails closed.

A tolerance file (default `scores/crossplatform_tolerance.json`) looks like::

    {
      "_approved_by": "...", "_approved_date": "YYYY-MM-DD",
      "_basis": "why these numbers",
      "max_abs_delta_dbfs": -90.0,
      "delta_rms_re_signal_db": -80.0,
      "max_spectral_deviation_db": 0.5,
      "max_peak_pitch_deviation_cents": 0.5
    }

Every key is optional; a missing key means that metric is reported but not
judged.  The file is data, not code: this tool never writes it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent

# Fixed probe set.  Chosen to cover every engine family that has a physical
# claim, plus one deliberately out-of-domain FM score, while staying small
# enough to render on a 2-core hosted CI runner.  Do not silently shrink this
# list -- Rule 3 forbids narrowing a GATE's scope.
PROBE_SCORES = [
    "scores/examples/water_gong_clamped.score.json",   # PlateModel, clamped
    "scores/examples/water_gong_free.score.json",      # PlateModel, free edge
    "scores/examples/physical_piano.score.json",       # StringModel via cimbalom path
    "scores/examples/akashic_bell.score.json",         # BeamModel / tongue drum
    "scores/examples/fur_elise_opening.score.json",    # FM: out of physical domain
]

DEFAULT_TOLERANCE_FILE = REPO_ROOT / "scores" / "crossplatform_tolerance.json"

# Spectral comparison only judges bins that actually carry signal in the
# reference render.  Bins 80 dB below the reference peak are numerical dust and
# their relative deviation is meaningless.
SPECTRAL_FLOOR_DB = -80.0

EXIT_OK = 0
EXIT_OUT_OF_TOLERANCE = 1
EXIT_ERROR = 2
EXIT_UNREGISTERED = 3


# --------------------------------------------------------------------------
# I/O helpers
# --------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_wav(path: Path):
    """Decode a WAV to float64 in [-1, 1) without mixdown.

    Returns (sample_rate, samples[n, channels], sample_width_bytes).
    Scaling matches `verify_score.py::read_wav_all_channels` exactly so the
    two tools' dBFS numbers are directly comparable.
    """
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())
    if sw == 2:
        a = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        a = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        a = np.where(a & 0x800000, a - 0x1000000, a).astype(np.float64) / 8388608.0
    elif sw == 4:
        a = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"unsupported sample width {sw} bytes in {path}")
    a = a.reshape(-1, ch) if ch > 1 else a.reshape(-1, 1)
    return sr, a, sw


def find_cli(explicit: str | None):
    if explicit:
        p = Path(explicit)
        if not p.is_file():
            raise FileNotFoundError(f"--cli path does not exist: {p}")
        return p
    cands = []
    for pattern in ("TsukiSynthCLI.exe", "TsukiSynthCLI", "tsukisynth-cli*"):
        cands += [c for c in (REPO_ROOT / "build").rglob(pattern) if c.is_file()]
    if not cands:
        raise FileNotFoundError(
            "TsukiSynthCLI not found under build/. Build it first or pass --cli.")
    return max(cands, key=lambda p: p.stat().st_mtime)


def db(x: float) -> float:
    """Linear amplitude -> dB, with a hard -inf for exact zero.

    Returned as float('-inf') so that "no difference at all" is visually and
    numerically distinct from "a very small difference", instead of being
    flattened into an arbitrary floor value.
    """
    return float("-inf") if x <= 0.0 else 20.0 * float(np.log10(x))


# --------------------------------------------------------------------------
# Emit
# --------------------------------------------------------------------------

def emit(out_dir: Path, cli: Path, label: str) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "contract": "TsukiSynth CrossPlatform Emit v1",
        "label": label,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "cli_executable": cli.name,
        "cli_sha256": sha256_file(cli),
        "scores": {},
    }
    failures = 0
    for rel in PROBE_SCORES:
        score = REPO_ROOT / rel
        if not score.is_file():
            print(f"[ERROR] probe score missing: {rel}")
            failures += 1
            continue
        stem = Path(rel).stem.replace(".score", "")
        # The CLI refuses to overwrite an existing render, so always render
        # into a directory that is guaranteed empty.
        render_dir = out_dir / stem
        if render_dir.exists():
            shutil.rmtree(render_dir)
        render_dir.mkdir(parents=True)
        r = subprocess.run([str(cli), str(score), "--output", str(render_dir)],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1800)
        if r.returncode != 0:
            print(f"[ERROR] render failed (exit {r.returncode}) for {rel}")
            print(r.stdout)
            print(r.stderr)
            failures += 1
            continue
        wavs = sorted(render_dir.glob("*.wav"))
        if not wavs:
            print(f"[ERROR] no WAV produced for {rel}")
            failures += 1
            continue
        wav = wavs[-1]
        manifest_path = wav.with_name(wav.name + ".render.json")
        manifest = {}
        if manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"[ERROR] unreadable render manifest for {rel}: {e}")
                failures += 1
                continue
        sr, samples, sw = read_wav(wav)
        report["scores"][rel] = {
            "wav": str(wav.relative_to(out_dir)).replace("\\", "/"),
            "wav_sha256": sha256_file(wav),
            "sample_rate": sr,
            "channels": int(samples.shape[1]),
            "sample_width_bytes": sw,
            "frames": int(samples.shape[0]),
            # Provenance straight from render manifest v4 -- not re-derived, so
            # the compare step reports the same compiler string the renderer
            # itself recorded.
            "compiler": manifest.get("compiler"),
            "target": manifest.get("target"),
            "build_configuration": manifest.get("build_configuration"),
            "renderer_executable_sha256": manifest.get("renderer_executable_sha256"),
            "configured_source_commit": manifest.get("configured_source_commit"),
            "configured_source_dirty": manifest.get("configured_source_dirty"),
        }
        print(f"[OK] {rel} -> {wav.name}  sha256={report['scores'][rel]['wav_sha256'][:16]}...")
    (out_dir / "platform.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {out_dir / 'platform.json'} ({len(report['scores'])} score(s), "
          f"{failures} failure(s))")
    return EXIT_ERROR if failures else EXIT_OK


# --------------------------------------------------------------------------
# Compare
# --------------------------------------------------------------------------

def compare_signals(ref: np.ndarray, cand: np.ndarray, sr: int) -> dict:
    """Sample-domain and spectral agreement metrics between two renders.

    All dB values are absolute dBFS except `delta_rms_re_signal_db`, which is
    relative to the reference's own RMS so it survives a level change in the
    score without becoming meaningless.
    """
    diff = ref - cand
    max_abs = float(np.max(np.abs(diff)))
    ref_rms = float(np.sqrt(np.mean(ref ** 2)))
    diff_rms = float(np.sqrt(np.mean(diff ** 2)))
    nonzero = np.flatnonzero(np.any(diff != 0.0, axis=1))
    first_diff = int(nonzero[0]) if nonzero.size else -1

    out = {
        "max_abs_delta_dbfs": db(max_abs),
        "max_abs_delta_lsb_24bit": max_abs * 8388608.0,
        "delta_rms_dbfs": db(diff_rms),
        "delta_rms_re_signal_db": db(diff_rms / ref_rms) if ref_rms > 0 else float("-inf"),
        "first_differing_sample": first_diff,
        "first_differing_time_s": (first_diff / sr) if first_diff >= 0 else None,
        "differing_frame_fraction": float(nonzero.size) / float(ref.shape[0]),
    }

    # Spectral agreement on the channel mixdown.  A single whole-signal FFT is
    # deliberate: this asks "does the render land in the same place in the
    # frequency domain", which is the domain every physical claim is stated in.
    ref_m = ref.mean(axis=1)
    cand_m = cand.mean(axis=1)
    n = int(ref_m.size)
    if n >= 1024:
        win = np.hanning(n)
        R = np.abs(np.fft.rfft(ref_m * win))
        C = np.abs(np.fft.rfft(cand_m * win))
        peak = float(np.max(R))
        if peak > 0.0:
            floor = peak * (10.0 ** (SPECTRAL_FLOOR_DB / 20.0))
            mask = R >= floor
            if np.any(mask):
                dev = np.abs(20.0 * np.log10(np.maximum(C[mask], 1e-300) / R[mask]))
                out["max_spectral_deviation_db"] = float(np.max(dev))
                out["spectral_bins_compared"] = int(np.count_nonzero(mask))
            # Peak-bin pitch agreement, expressed in cents so it is directly
            # comparable to the +/-5 cent f0 tolerance in section 6.
            freqs = np.fft.rfftfreq(n, d=1.0 / sr)
            fr = float(freqs[int(np.argmax(R))])
            fc = float(freqs[int(np.argmax(C))])
            if fr > 0.0 and fc > 0.0:
                out["peak_bin_hz_reference"] = fr
                out["peak_bin_hz_candidate"] = fc
                out["peak_pitch_deviation_cents"] = float(1200.0 * np.log2(fc / fr))
    return out


JUDGED_METRICS = [
    # (metric key, tolerance key, comparison is "<= tolerance" on this value)
    ("max_abs_delta_dbfs", "max_abs_delta_dbfs"),
    ("delta_rms_re_signal_db", "delta_rms_re_signal_db"),
    ("max_spectral_deviation_db", "max_spectral_deviation_db"),
    ("peak_pitch_deviation_cents", "max_peak_pitch_deviation_cents"),
]


def judge(metrics: dict, tol: dict) -> list:
    """Returns a list of (metric, measured, limit, ok) for judged metrics only."""
    rows = []
    for mkey, tkey in JUDGED_METRICS:
        if tkey not in tol or mkey not in metrics:
            continue
        measured = metrics[mkey]
        limit = float(tol[tkey])
        # Pitch deviation is judged on magnitude; the dB metrics are error
        # floors where "more negative is better".
        value = abs(measured) if mkey.endswith("_cents") else measured
        rows.append((mkey, measured, limit, value <= limit))
    return rows


def load_platform(d: Path) -> dict:
    p = d / "platform.json"
    if not p.is_file():
        raise FileNotFoundError(f"{p} not found -- run --emit in that directory first")
    return json.loads(p.read_text(encoding="utf-8"))


def compare(dirs: list, tol_file: Path) -> int:
    if len(dirs) < 2:
        print("[ERROR] --compare needs at least two directories")
        return EXIT_ERROR

    reports = []
    for d in dirs:
        try:
            reports.append((d, load_platform(d)))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[ERROR] {e}")
            return EXIT_ERROR

    tol = None
    if tol_file.is_file():
        try:
            tol = json.loads(tol_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"[ERROR] tolerance file {tol_file} is not valid JSON: {e}")
            return EXIT_ERROR

    ref_dir, ref_rep = reports[0]
    print("=" * 74)
    print("TsukiSynth cross-platform render reproducibility")
    print("=" * 74)
    print(f"reference : {ref_rep.get('label')}  "
          f"({ref_rep['platform']['system']} {ref_rep['platform']['machine']})")
    for d, rep in reports[1:]:
        print(f"candidate : {rep.get('label')}  "
              f"({rep['platform']['system']} {rep['platform']['machine']})")
    print(f"tolerance : {tol_file if tol else 'NONE REGISTERED'}")
    print()

    all_bit_identical = True
    any_error = False
    any_out_of_tolerance = False

    for d, rep in reports[1:]:
        print("-" * 74)
        print(f"### {ref_rep.get('label')}  vs  {rep.get('label')}")
        ref_compiler = next(iter(ref_rep["scores"].values()), {}).get("compiler")
        cand_compiler = next(iter(rep["scores"].values()), {}).get("compiler")
        print(f"    compiler: {ref_compiler}  vs  {cand_compiler}")
        print("-" * 74)

        shared = [s for s in ref_rep["scores"] if s in rep["scores"]]
        missing = [s for s in ref_rep["scores"] if s not in rep["scores"]]
        if missing:
            # Fail closed: a score that only rendered on one platform is not a
            # pass, it is missing evidence (Rule 3: no silent scope narrowing).
            for s in missing:
                print(f"[ERROR] {s}: present in reference, absent in candidate")
            any_error = True

        for rel in shared:
            a = ref_rep["scores"][rel]
            b = rep["scores"][rel]
            if a["wav_sha256"] == b["wav_sha256"]:
                print(f"[BIT-IDENTICAL] {rel}")
                continue
            all_bit_identical = False

            for key in ("sample_rate", "channels", "sample_width_bytes", "frames"):
                if a[key] != b[key]:
                    print(f"[ERROR] {rel}: {key} differs "
                          f"({a[key]} vs {b[key]}) -- not a numeric-tolerance "
                          f"question, the renders are not comparable")
                    any_error = True
                    break
            else:
                sr_a, sam_a, _ = read_wav(ref_dir / a["wav"])
                sr_b, sam_b, _ = read_wav(d / b["wav"])
                m = compare_signals(sam_a, sam_b, sr_a)
                print(f"[DIFFERS] {rel}")
                print(f"    max |delta|            : {m['max_abs_delta_dbfs']:.2f} dBFS "
                      f"({m['max_abs_delta_lsb_24bit']:.3f} LSB at 24-bit)")
                print(f"    delta RMS              : {m['delta_rms_dbfs']:.2f} dBFS "
                      f"({m['delta_rms_re_signal_db']:.2f} dB re signal)")
                print(f"    first differing frame  : {m['first_differing_sample']} "
                      f"(t = {m['first_differing_time_s']:.6f} s)")
                print(f"    differing frames       : {m['differing_frame_fraction'] * 100:.4f} %")
                if "max_spectral_deviation_db" in m:
                    print(f"    max spectral deviation : {m['max_spectral_deviation_db']:.4f} dB "
                          f"over {m['spectral_bins_compared']} bin(s) above "
                          f"{SPECTRAL_FLOOR_DB:.0f} dB re peak")
                if "peak_pitch_deviation_cents" in m:
                    print(f"    peak-bin pitch         : {m['peak_pitch_deviation_cents']:+.4f} cents "
                          f"({m['peak_bin_hz_reference']:.3f} -> {m['peak_bin_hz_candidate']:.3f} Hz)")

                if tol is not None:
                    for mkey, measured, limit, ok in judge(m, tol):
                        verdict = "PASS" if ok else "FAIL"
                        print(f"      [{verdict}] {mkey}: {measured:.4f} "
                              f"(limit {limit:.4f})")
                        if not ok:
                            any_out_of_tolerance = True
        print()

    print("=" * 74)
    if any_error:
        print("RESULT: ERROR -- inputs incomplete or not comparable (fails closed)")
        return EXIT_ERROR
    if all_bit_identical:
        print("RESULT: BIT_IDENTICAL -- every platform matched byte-for-byte.")
        print("No cross-platform tolerance is needed.")
        return EXIT_OK
    if tol is None:
        print("RESULT: UNREGISTERED -- renders differ numerically across platforms.")
        print("The measured deviations above are printed for registration in")
        print("ROADMAP_PHYSICS.md section 6.  This tool must not invent a")
        print("tolerance (Rule 2), so no pass/fail verdict is issued.")
        print(f"To enable judgement, create {tol_file} with approved limits.")
        return EXIT_UNREGISTERED
    if any_out_of_tolerance:
        print("RESULT: OUT_OF_TOLERANCE -- a metric exceeded its registered limit.")
        return EXIT_OUT_OF_TOLERANCE
    print("RESULT: WITHIN REGISTERED TOLERANCE")
    return EXIT_OK


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------

def selftest() -> int:
    """Verify the comparator's arithmetic and that it cannot be fooled.

    Mirrors the counterexample discipline of `physics_verify.py --selftest`:
    every check that is supposed to catch something is proven to catch a
    deliberately constructed instance of it.
    """
    sr = 48000
    n = 48000
    t = np.arange(n) / sr
    base = (0.5 * np.sin(2 * np.pi * 440.0 * t)).reshape(-1, 1)
    base = np.repeat(base, 2, axis=1)
    failures = 0

    def check(name, cond, detail=""):
        nonlocal failures
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' -- ' + detail) if detail else ''}")
        if not cond:
            failures += 1

    print("crossplatform_verify self-test")
    print("-" * 60)

    # 1. Identical input must produce an exactly empty difference.
    m = compare_signals(base, base.copy(), sr)
    check("identical signals -> -inf max delta",
          m["max_abs_delta_dbfs"] == float("-inf"))
    check("identical signals -> no differing frame",
          m["first_differing_sample"] == -1 and m["differing_frame_fraction"] == 0.0)
    check("identical signals -> 0.000 dB spectral deviation",
          m.get("max_spectral_deviation_db", 1.0) < 1e-9,
          f"{m.get('max_spectral_deviation_db')}")

    # 2. A known-size offset must be reported at exactly that dBFS.
    eps = 10.0 ** (-100.0 / 20.0)          # -100 dBFS
    pert = base.copy()
    pert[1234, 0] += eps
    m = compare_signals(base, pert, sr)
    check("single -100 dBFS perturbation measured as -100.00 dBFS",
          abs(m["max_abs_delta_dbfs"] - (-100.0)) < 1e-6,
          f"{m['max_abs_delta_dbfs']:.6f}")
    check("perturbation located at the right frame",
          m["first_differing_sample"] == 1234,
          str(m["first_differing_sample"]))

    # 3. Counterexample: a gain error must show up in the spectral metric even
    #    though it barely moves the sample-domain floor for a quiet signal.
    m = compare_signals(base, base * (10.0 ** (0.5 / 20.0)), sr)
    check("+0.5 dB gain error detected as ~0.5 dB spectral deviation",
          abs(m.get("max_spectral_deviation_db", 0.0) - 0.5) < 0.02,
          f"{m.get('max_spectral_deviation_db'):.4f}")

    # 4. Counterexample: a pitch shift must be caught in cents.
    shifted = (0.5 * np.sin(2 * np.pi * 440.0 * (2.0 ** (50.0 / 1200.0)) * t)).reshape(-1, 1)
    shifted = np.repeat(shifted, 2, axis=1)
    m = compare_signals(base, shifted, sr)
    # Bin resolution at 1 s / 48 kHz is 1 Hz, i.e. ~3.9 cents at 440 Hz, so the
    # measured value is quantised; require it to land within one bin of +50.
    check("+50 cent shift reported within one FFT bin of +50 cents",
          abs(m.get("peak_pitch_deviation_cents", 0.0) - 50.0) < 4.0,
          f"{m.get('peak_pitch_deviation_cents'):.3f}")

    # 5. Counterexample: the judge must actually fail an out-of-limit metric.
    rows = judge({"max_abs_delta_dbfs": -60.0}, {"max_abs_delta_dbfs": -90.0})
    check("judge rejects -60 dBFS against a -90 dBFS limit",
          len(rows) == 1 and rows[0][3] is False)
    rows = judge({"max_abs_delta_dbfs": -120.0}, {"max_abs_delta_dbfs": -90.0})
    check("judge accepts -120 dBFS against a -90 dBFS limit",
          len(rows) == 1 and rows[0][3] is True)
    rows = judge({"peak_pitch_deviation_cents": -3.0},
                 {"max_peak_pitch_deviation_cents": 1.0})
    check("judge uses magnitude for a negative cent deviation",
          len(rows) == 1 and rows[0][3] is False)

    # 6. Counterexample: an unregistered metric must be reported, not silently
    #    treated as passing.
    rows = judge({"max_abs_delta_dbfs": -10.0}, {})
    check("empty tolerance file judges nothing (no silent PASS)", rows == [])

    print("-" * 60)
    print(f"RESULT: {'ALL SELF-TESTS PASSED' if failures == 0 else f'{failures} SELF-TEST FAILURE(S)'}")
    return EXIT_OK if failures == 0 else EXIT_OUT_OF_TOLERANCE


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Cross-platform render reproducibility harness.")
    ap.add_argument("--emit", metavar="OUTDIR",
                    help="render the probe scores locally into OUTDIR")
    ap.add_argument("--label", default=None,
                    help="human-readable name for this platform (default: auto)")
    ap.add_argument("--cli", default=None, help="path to TsukiSynthCLI")
    ap.add_argument("--compare", nargs="+", metavar="DIR",
                    help="compare emitted directories; the first is the reference")
    ap.add_argument("--tolerance", default=str(DEFAULT_TOLERANCE_FILE),
                    help="path to the approved tolerance file")
    ap.add_argument("--selftest", action="store_true",
                    help="verify the comparator against known counterexamples")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if args.emit:
        try:
            cli = find_cli(args.cli)
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
            return EXIT_ERROR
        label = args.label or f"{platform.system()}-{platform.machine()}"
        print(f"Rendering probe set with {cli}")
        return emit(Path(args.emit), cli, label)
    if args.compare:
        return compare([Path(d) for d in args.compare], Path(args.tolerance))
    ap.print_help()
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
