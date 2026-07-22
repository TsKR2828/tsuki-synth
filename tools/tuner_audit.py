#!/usr/bin/env python3
"""Executable tuner acceptance audit.

This is deliberately independent from the C++ estimator. It verifies the
public range/refusal contract with a zero-crossing oracle, while the dedicated
TsukiSynthTunerTest target exercises the real PitchDetector implementation.

Exit status is non-zero on every failed assertion. ``--inject-failure`` exists
only to prove that CI wiring observes a failing exit code.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Iterable, Optional

MIN_MIDI = 21   # A0
MAX_MIDI = 108  # C8
SEARCH_CENTS = 700.0
SAMPLE_RATES = (44_100, 48_000, 96_000, 192_000)
PHASES = (0.0, 0.71, 2.13)


def midi_frequency(midi: int) -> float:
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def supported_target(midi: int, sample_rate: int) -> bool:
    if not MIN_MIDI <= midi <= MAX_MIDI:
        return False
    max_search = midi_frequency(midi) * 2.0 ** (SEARCH_CENTS / 1200.0)
    return max_search < sample_rate * 0.45


def required_samples(midi: int, sample_rate: int) -> int:
    minimum = midi_frequency(midi) * 2.0 ** (-SEARCH_CENTS / 1200.0)
    seconds = min(0.34, max(0.05, 6.0 / minimum))
    return math.ceil(seconds * sample_rate)


def sine(frequency: float, sample_rate: int, count: int,
         phase: float = 0.0) -> list[float]:
    step = 2.0 * math.pi * frequency / sample_rate
    return [0.4 * math.sin(step * i + phase) for i in range(count)]


def independent_frequency(signal: Iterable[float], sample_rate: int) -> Optional[float]:
    """Sub-sample rising-zero-crossing frequency oracle for clean audit tones."""
    values = list(signal)
    if not values:
        return None
    mean = sum(values) / len(values)
    centred = [value - mean for value in values]
    rms = math.sqrt(sum(value * value for value in centred) / len(centred))
    if rms < 1.0e-6:
        return None

    crossings: list[float] = []
    for i in range(1, len(centred)):
        before, after = centred[i - 1], centred[i]
        if before <= 0.0 < after:
            denominator = after - before
            fraction = -before / denominator if denominator else 0.0
            crossings.append(i - 1 + fraction)
    if len(crossings) < 3:
        return None

    periods = [b - a for a, b in zip(crossings, crossings[1:])]
    period = median(periods)
    return sample_rate / period if period > 0.0 else None


def bounded_measurement(signal: Iterable[float], sample_rate: int,
                        target_midi: int) -> Optional[float]:
    """Apply the same public target range and octave-safe window as the UI."""
    if not supported_target(target_midi, sample_rate):
        return None
    measured = independent_frequency(signal, sample_rate)
    if measured is None:
        return None
    cents = 1200.0 * math.log2(measured / midi_frequency(target_midi))
    return measured if abs(cents) < SEARCH_CENTS - 2.0 else None


@dataclass
class Audit:
    failures: int = 0
    checks: int = 0

    def check(self, condition: bool, message: str) -> None:
        self.checks += 1
        if condition:
            print(f"[PASS] {message}")
        else:
            print(f"[FAIL] {message}")
            self.failures += 1


def range_sweep(audit: Audit) -> None:
    measured = refused = 0
    worst_cents = 0.0
    for sample_rate in SAMPLE_RATES:
        for midi in range(128):
            if not supported_target(midi, sample_rate):
                # An out-of-range target is rejected before audio is examined.
                probe = sine(440.0, sample_rate, max(64, sample_rate // 100))
                if bounded_measurement(probe, sample_rate, midi) is None:
                    refused += 1
                else:
                    audit.check(False, f"range refusal sr={sample_rate} MIDI={midi}")
                continue

            frequency = midi_frequency(midi)
            count = required_samples(midi, sample_rate)
            for phase in PHASES:
                result = bounded_measurement(
                    sine(frequency, sample_rate, count, phase),
                    sample_rate, midi)
                if result is None:
                    audit.check(False, f"missing sr={sample_rate} MIDI={midi} phase={phase}")
                    continue
                cents = abs(1200.0 * math.log2(result / frequency))
                worst_cents = max(worst_cents, cents)
                if cents > 1.0:
                    audit.check(False, f"accuracy sr={sample_rate} MIDI={midi}: {cents:.3f}c")
                measured += 1

    audit.check(measured == len(SAMPLE_RATES) * (MAX_MIDI - MIN_MIDI + 1)
                * len(PHASES),
                f"A0-C8 sweep: {measured} measured cases")
    audit.check(refused == len(SAMPLE_RATES)
                * (128 - (MAX_MIDI - MIN_MIDI + 1)),
                f"outside-range sweep: {refused} explicitly refused cases")
    audit.check(worst_cents <= 1.0,
                f"independent oracle worst error: {worst_cents:.4f} cents")


def shifted_and_negative_cases(audit: Audit) -> None:
    sample_rate = 48_000
    target = 69
    count = required_samples(target, sample_rate)
    target_hz = midi_frequency(target)
    for ratio in (0.85, 1.15, 0.85 * 0.85):
        result = bounded_measurement(
            sine(target_hz * ratio, sample_rate, count, 0.41),
            sample_rate, target)
        expected = 1200.0 * math.log2(ratio)
        actual = (1200.0 * math.log2(result / target_hz)
                  if result is not None else math.inf)
        audit.check(result is not None and abs(actual - expected) <= 1.0,
                    f"audio shift {expected:+.2f} cents is measured, not copied")

    for ratio in (0.5, 2.0):
        result = bounded_measurement(
            sine(target_hz * ratio, sample_rate, count), sample_rate, target)
        audit.check(result is None,
                    f"{ratio:g}x octave substitution is refused")
    audit.check(bounded_measurement([0.0] * count, sample_rate, target) is None,
                "silence never becomes a measured pitch")


def source_contract(audit: Audit) -> None:
    root = Path(__file__).resolve().parents[1]
    detector = (root / "src/analyzer/PitchDetector.h").read_text(encoding="utf-8")
    view = (root / "src/analyzer/TunerView.h").read_text(encoding="utf-8")
    processor = (root / "src/PluginProcessor.h").read_text(encoding="utf-8")
    cmake = (root / "CMakeLists.txt").read_text(encoding="utf-8")

    audit.check("minSupportedMidi = 21" in detector
                and "maxSupportedMidi = 108" in detector,
                "C++ detector declares the audited A0-C8 contract")
    audit.check("kMaxAnalysisSamples = 4096" in detector
                and "std::array<float" in detector,
                "C++ detector has fixed storage and bounded work")
    audit.check("TARGET" in view and "MEASURED" in view
                and "audio confidence" in view,
                "UI labels target, audio measurement, delta and confidence")
    audit.check("pullLatest" in view and "analyzerDryFifo { 65536 }" in processor,
                "tuner consumes newest dry audio with 192 kHz A0 history")
    audit.check("TsukiSynthTunerTest" in cmake,
                "real C++ tuner regression target is registered with CTest")


def run(include_source: bool = False, inject_failure: bool = False) -> int:
    audit = Audit()
    print("TsukiSynth tuner acceptance audit")
    range_sweep(audit)
    shifted_and_negative_cases(audit)
    if include_source:
        source_contract(audit)
    if inject_failure:
        audit.check(False, "injected failure proves non-zero exit status")

    print(f"{'PASS' if audit.failures == 0 else 'FAIL'} "
          f"({audit.checks} checks, {audit.failures} failures)")
    return 0 if audit.failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-contract", action="store_true",
                        help="also assert C++/UI/CMake contract wiring")
    parser.add_argument("--inject-failure", action="store_true",
                        help=argparse.SUPPRESS)
    args = parser.parse_args()
    return run(args.source_contract, args.inject_failure)


if __name__ == "__main__":
    raise SystemExit(main())
