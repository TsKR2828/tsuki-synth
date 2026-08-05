#!/usr/bin/env python3
"""Build a self-contained Specimen Measurement v2 bundle from synchronized CSVs.

This program automates the non-human portion of specimen metrology: calibration
math, H1/coherence, complex phase, modal peak/T60 extraction, pressure/force,
SPL at a declared RMS force, directivity points, uncertainty estimates, hashes
and bundle assembly.  It intentionally cannot create the physical specimen,
mount sensors or make an uncalibrated recording traceable.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from scipy import signal
from jsonschema import Draft202012Validator


ACQUISITION_CONTRACT = "TsukiSynth Specimen Acquisition v1"
MEASUREMENT_CONTRACT = "TsukiSynth Specimen Measurement v2"
MODE_DUMP_CONTRACT = "TsukiSynth Mode Dump v2"
P_REF_PA = 20.0e-6
RECIPE_SCHEMA_PATH = (Path(__file__).resolve().parent.parent / "specimens" / "schema"
                      / "specimen_acquisition.schema.json")
EVIDENCE_ROLES = {
    "excitation_calibration", "response_calibration", "acoustic_calibration",
}


class PipelineError(RuntimeError):
    """Refuse to produce a bundle when its evidence or math is invalid."""


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_recipe(recipe: Any) -> None:
    schema = _load_json(RECIPE_SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(recipe),
        key=lambda error: tuple(str(part) for part in error.absolute_path))
    if errors:
        rendered = []
        for error in errors:
            path = ".".join(str(part) for part in error.absolute_path) or "$"
            rendered.append(f"{path}: {error.message}")
        raise PipelineError("acquisition recipe schema failed: " + "; ".join(rendered))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _finite_positive(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PipelineError(f"{name} must be a number")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise PipelineError(f"{name} must be finite and positive")
    return result


def _resolve(base: Path, text: str, label: str) -> Path:
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = base / candidate
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise PipelineError(f"{label} not found: {candidate}")
    return candidate


def _expand_record_specs(items: list[dict[str, Any]], base: Path,
                         label: str) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for item_index, item in enumerate(items):
        has_path = "path" in item
        has_glob = "path_glob" in item
        if has_path == has_glob:
            raise PipelineError(
                f"{label}[{item_index}] must contain exactly one of path or path_glob")
        if has_path:
            paths = [_resolve(base, item["path"], label)]
        else:
            pattern = item["path_glob"]
            if Path(pattern).is_absolute():
                raise PipelineError(f"{label}[{item_index}].path_glob must be relative")
            paths = sorted(path.resolve() for path in base.glob(pattern) if path.is_file())
            if not paths:
                raise PipelineError(f"{label} glob matched no files: {pattern}")
        for path in paths:
            if path in seen:
                raise PipelineError(f"duplicate {label} path: {path}")
            seen.add(path)
            record = copy.deepcopy(item)
            record.pop("path_glob", None)
            record["path"] = str(path)
            expanded.append(record)
    return expanded


def _read_columns(path: Path, columns: list[str]) -> dict[str, np.ndarray]:
    try:
        data = np.genfromtxt(path, delimiter=",", names=True, dtype=np.float64,
                             encoding="utf-8-sig")
    except Exception as exc:
        raise PipelineError(f"cannot read CSV {path}: {exc}") from exc
    if data.dtype.names is None:
        raise PipelineError(f"CSV has no header: {path}")
    if data.ndim == 0:
        data = np.asarray([data], dtype=data.dtype)
    if len(data) < 16:
        raise PipelineError(f"CSV needs at least 16 samples: {path}")
    result: dict[str, np.ndarray] = {}
    for name in columns:
        if name not in data.dtype.names:
            raise PipelineError(f"CSV {path} has no column {name!r}")
        values = np.asarray(data[name], dtype=np.float64)
        if not np.all(np.isfinite(values)):
            raise PipelineError(f"CSV {path} column {name!r} contains NaN/Inf")
        result[name] = values
    return result


def _check_time(time_s: np.ndarray, sample_rate_hz: float, path: Path) -> None:
    differences = np.diff(time_s)
    expected = 1.0 / sample_rate_hz
    if np.any(differences <= 0.0):
        raise PipelineError(f"time_s is not strictly increasing: {path}")
    relative = abs(float(np.median(differences)) - expected) / expected
    jitter = float(np.max(np.abs(differences - expected))) / expected
    if relative > 1.0e-4 or jitter > 1.0e-2:
        raise PipelineError(
            f"time base disagrees with sample_rate_hz or has excessive jitter: {path}")


def _window(name: str, count: int) -> np.ndarray:
    aliases = {"rectangular": "boxcar", "rect": "boxcar"}
    try:
        return signal.get_window(aliases.get(name, name), count, fftbins=True)
    except ValueError as exc:
        raise PipelineError(f"unsupported FFT window {name!r}") from exc


def _expanded_sem(values: np.ndarray, coverage: float, floor: float) -> float:
    values = np.asarray(values, dtype=np.float64)
    statistical = 0.0 if len(values) < 2 else coverage * float(np.std(values, ddof=1)) / math.sqrt(len(values))
    return math.hypot(statistical, floor)


def _circular_expanded_sem_deg(phases_deg: np.ndarray, coverage: float,
                               floor_deg: float) -> float:
    radians = np.radians(np.asarray(phases_deg, dtype=np.float64))
    resultant = abs(np.mean(np.exp(1j * radians)))
    resultant = min(1.0, max(1.0e-15, float(resultant)))
    circular_std_deg = math.degrees(math.sqrt(max(0.0, -2.0 * math.log(resultant))))
    statistical = coverage * circular_std_deg / math.sqrt(max(1, len(radians)))
    return math.hypot(statistical, floor_deg)


def _record_arrays(record: dict[str, Any], base: Path, sample_rate_hz: float,
                   force_cfg: dict[str, Any], response_cfg: dict[str, Any],
                   method: str) -> dict[str, Any]:
    path = _resolve(base, record["path"], "record")
    time_column = record.get("time_column", "time_s")
    force_column = record.get("force_column", force_cfg.get("column", "force_v"))
    response_column = record.get("response_column", response_cfg["column"])
    columns = _read_columns(path, [time_column, force_column, response_column])
    _check_time(columns[time_column], sample_rate_hz, path)
    force_v = columns[force_column]
    response_v = columns[response_column]
    for values, cfg, label in ((force_v, force_cfg, "force"),
                               (response_v, response_cfg, "response")):
        full_scale = cfg.get("full_scale_v")
        if full_scale is not None and np.max(np.abs(values)) >= 0.99 * _finite_positive(full_scale, f"{label}.full_scale_v"):
            raise PipelineError(f"{label} channel overload: {path}")
    force = (float(force_cfg.get("polarity", 1.0)) * force_v
             / _finite_positive(force_cfg["sensitivity_v_per_n"],
                                "force.sensitivity_v_per_n"))
    response = (float(response_cfg.get("polarity", 1.0)) * response_v
                / _finite_positive(response_cfg["sensitivity_v_per_si"],
                                   "response.sensitivity_v_per_si"))
    if method == "impact_hammer_frf":
        absolute_force = np.abs(force - np.mean(force))
        peak = float(np.max(absolute_force))
        if peak <= 0.0:
            raise PipelineError(f"zero force record: {path}")
        peaks, _ = signal.find_peaks(
            absolute_force, height=0.25 * peak,
            distance=max(1, int(round(0.002 * sample_rate_hz))))
        if len(peaks) != 1:
            raise PipelineError(f"impact record has {len(peaks)} significant hits: {path}")
    return {"path": path, "time": columns[time_column], "force": force,
            "response": response}


def _aggregate_frf(records: list[dict[str, Any]], sample_rate_hz: float,
                   window_name: str, relative_delay_s: float) -> dict[str, Any]:
    if len(records) < 2:
        raise PipelineError("H1/coherence requires at least two independent records")
    lengths = {len(item["force"]) for item in records}
    lengths.update(len(item["response"]) for item in records)
    if len(lengths) != 1:
        raise PipelineError("all records in an average group must have equal length")
    count = lengths.pop()
    taper = _window(window_name, count)
    x_spectra = []
    y_spectra = []
    for item in records:
        force = signal.detrend(item["force"], type="constant") * taper
        response = signal.detrend(item["response"], type="constant") * taper
        x_spectra.append(np.fft.rfft(force))
        y_spectra.append(np.fft.rfft(response))
    x = np.asarray(x_spectra)
    y = np.asarray(y_spectra)
    frequencies = np.fft.rfftfreq(count, 1.0 / sample_rate_hz)
    correction = np.exp(1j * 2.0 * np.pi * frequencies * relative_delay_s)
    y = y * correction[np.newaxis, :]
    g_yx = np.mean(y * np.conj(x), axis=0)
    g_xx = np.mean(np.abs(x) ** 2, axis=0)
    g_yy = np.mean(np.abs(y) ** 2, axis=0)
    epsilon = np.finfo(np.float64).tiny
    h1 = g_yx / np.maximum(g_xx, epsilon)
    coherence = np.abs(g_yx) ** 2 / np.maximum(g_xx * g_yy, epsilon)
    coherence = np.clip(coherence.real, 0.0, 1.0)
    individual = np.divide(y, x, out=np.zeros_like(y),
                           where=np.abs(x) > math.sqrt(epsilon))
    return {"frequencies": frequencies, "h1": h1,
            "coherence": coherence, "individual": individual}


def _target_bin(frequencies: np.ndarray, magnitude: np.ndarray, target_hz: float,
                half_width_hz: float) -> int:
    candidates = np.flatnonzero(
        (frequencies >= target_hz - half_width_hz)
        & (frequencies <= target_hz + half_width_hz))
    if len(candidates) == 0:
        raise PipelineError(f"no FFT bin near target {target_hz:g} Hz")
    return int(candidates[np.argmax(magnitude[candidates])])


def _decay_t60(response: np.ndarray, force: np.ndarray, sample_rate_hz: float,
               frequency_hz: float, bandwidth_hz: float,
               fit_upper_db: float, fit_lower_db: float) -> tuple[float, float]:
    nyquist = sample_rate_hz / 2.0
    low = max(1.0, frequency_hz - bandwidth_hz / 2.0)
    high = min(nyquist * 0.98, frequency_hz + bandwidth_hz / 2.0)
    if not low < high:
        raise PipelineError(f"invalid decay band around {frequency_hz:g} Hz")
    sos = signal.butter(4, [low, high], btype="bandpass", fs=sample_rate_hz,
                        output="sos")
    try:
        filtered = signal.sosfiltfilt(sos, signal.detrend(response, type="constant"))
    except ValueError as exc:
        raise PipelineError(f"record is too short for T60 filter at {frequency_hz:g} Hz") from exc
    envelope = np.abs(signal.hilbert(filtered))
    smooth_count = max(1, int(round(sample_rate_hz * 0.002)))
    if smooth_count > 1:
        envelope = np.convolve(envelope, np.ones(smooth_count) / smooth_count,
                              mode="same")
    force_peak = int(np.argmax(np.abs(force - np.mean(force))))
    peak_index = force_peak + int(np.argmax(envelope[force_peak:]))
    tail = envelope[peak_index:]
    if len(tail) < 32 or float(tail[0]) <= 0.0:
        raise PipelineError(f"no usable decay after {frequency_hz:g} Hz excitation")
    decay_db = 20.0 * np.log10(np.maximum(tail / float(tail[0]), 1.0e-15))
    upper_hits = np.flatnonzero(decay_db <= fit_upper_db)
    if len(upper_hits) == 0:
        raise PipelineError(f"decay never reaches {fit_upper_db:g} dB at {frequency_hz:g} Hz")
    begin = int(upper_hits[0])
    lower_hits = np.flatnonzero(decay_db[begin:] <= fit_lower_db)
    if len(lower_hits) == 0:
        raise PipelineError(f"decay never reaches {fit_lower_db:g} dB at {frequency_hz:g} Hz")
    end = begin + int(lower_hits[0]) + 1
    if end - begin < 16:
        raise PipelineError(f"too few decay-fit samples at {frequency_hz:g} Hz")
    times = np.arange(begin, end, dtype=np.float64) / sample_rate_hz
    values = decay_db[begin:end]
    slope, intercept = np.polyfit(times, values, 1)
    if slope >= 0.0:
        raise PipelineError(f"non-decaying modal fit at {frequency_hz:g} Hz")
    fitted = slope * times + intercept
    residual = float(np.sum((values - fitted) ** 2))
    total = float(np.sum((values - np.mean(values)) ** 2))
    r2 = 1.0 - residual / total if total > 0.0 else 0.0
    return -60.0 / float(slope), r2


def _calibrator_sensitivity(recipe: dict[str, Any], base: Path,
                            sample_rate_hz: float,
                            microphone_cfg: dict[str, Any]) -> tuple[float, dict[str, Any], list[tuple[str, Path]]]:
    calibrator = recipe.get("calibrator")
    if not isinstance(calibrator, dict):
        raise PipelineError("calibrated acoustic processing requires calibrator before/after records")
    level_db = float(calibrator.get("level_db_re_20upa", 94.0))
    tone_hz = _finite_positive(calibrator.get("frequency_hz", 1000.0),
                               "calibrator.frequency_hz")
    column = calibrator.get("microphone_column", microphone_cfg["column"])
    time_column = calibrator.get("time_column", "time_s")
    expected_pa = P_REF_PA * 10.0 ** (level_db / 20.0)
    sensitivities = []
    peaks = []
    evidence = []
    for label, role in (("before_path", "raw_calibrator_before"),
                        ("after_path", "raw_calibrator_after")):
        path = _resolve(base, calibrator[label], label)
        columns = _read_columns(path, [time_column, column])
        _check_time(columns[time_column], sample_rate_hz, path)
        full_scale = microphone_cfg.get("full_scale_v")
        if (full_scale is not None
                and np.max(np.abs(columns[column]))
                >= 0.99 * _finite_positive(full_scale, "microphone.full_scale_v")):
            raise PipelineError(f"microphone channel overload during calibration: {path}")
        voltage = signal.detrend(columns[column], type="constant")
        trim = len(voltage) // 10
        voltage = voltage[trim:len(voltage) - trim] if trim else voltage
        rms_v = float(np.sqrt(np.mean(voltage ** 2)))
        if rms_v <= 0.0:
            raise PipelineError(f"zero calibrator voltage: {path}")
        spectrum = np.abs(np.fft.rfft(voltage * _window("hann", len(voltage))))
        frequencies = np.fft.rfftfreq(len(voltage), 1.0 / sample_rate_hz)
        peak_hz = float(frequencies[int(np.argmax(spectrum[1:]) + 1)])
        if abs(peak_hz - tone_hz) > max(2.0, tone_hz * 0.01):
            raise PipelineError(f"calibrator tone is {peak_hz:g} Hz, expected {tone_hz:g} Hz")
        sensitivities.append(rms_v / expected_pa)
        peaks.append(peak_hz)
        evidence.append((role, path))
    drift_db = abs(20.0 * math.log10(sensitivities[1] / sensitivities[0]))
    limit_db = float(calibrator.get("max_drift_db", 0.5))
    if drift_db > limit_db:
        raise PipelineError(f"microphone calibration drift {drift_db:.3f} dB exceeds {limit_db:.3f} dB")
    sensitivity = math.sqrt(sensitivities[0] * sensitivities[1])
    result = {
        "reference_level_db_re_20upa": level_db,
        "reference_frequency_hz": tone_hz,
        "expected_pressure_rms_pa": expected_pa,
        "before_sensitivity_v_per_pa": sensitivities[0],
        "after_sensitivity_v_per_pa": sensitivities[1],
        "adopted_sensitivity_v_per_pa": sensitivity,
        "sensitivity_drift_db": drift_db,
        "maximum_drift_db": limit_db,
        "detected_tone_hz": peaks,
    }
    return sensitivity, result, evidence


def _artifact(role: str, relative: Path, root: Path) -> dict[str, str]:
    return {"role": role, "path": relative.as_posix(),
            "sha256": _sha256(root / relative)}


def _copy_inputs(items: list[tuple[str, Path]], root: Path, subdir: str,
                 artifacts: list[dict[str, str]]) -> dict[Path, Path]:
    copied: dict[Path, Path] = {}
    copied_hashes: dict[Path, str] = {}
    for role, source in items:
        resolved = source.resolve()
        if resolved not in copied:
            safe_name = f"{len(copied):04d}_{source.name}"
            relative = Path(subdir) / safe_name
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, root / relative)
            copied[resolved] = relative
            copied_hashes[resolved] = _sha256(root / relative)
        artifacts.append({
            "role": role, "path": copied[resolved].as_posix(),
            "sha256": copied_hashes[resolved],
        })
    return copied


def build_bundle(recipe_path: Path, output_directory: Path) -> Path:
    recipe_path = recipe_path.resolve()
    recipe = _load_json(recipe_path)
    _validate_recipe(recipe)
    base = recipe_path.parent
    template_path = _resolve(base, recipe["measurement_template"], "measurement_template")
    dump_path = _resolve(base, recipe["mode_dump"], "mode_dump")
    measurement = _load_json(template_path)
    dump = _load_json(dump_path)
    if measurement.get("$schema") != MEASUREMENT_CONTRACT:
        raise PipelineError(f"measurement template must use {MEASUREMENT_CONTRACT!r}")
    if dump.get("contract") != MODE_DUMP_CONTRACT:
        raise PipelineError(f"mode dump must use {MODE_DUMP_CONTRACT!r}")
    source_index = measurement["model"]["event_source_index"]
    events = [event for event in dump.get("events", [])
              if event.get("source_index") == source_index]
    if len(events) != 1 or not events[0].get("partials"):
        raise PipelineError("mode dump needs exactly one selected event with partials")
    predicted = events[0]["partials"]

    acquisition = measurement["acquisition"]
    sample_rate_hz = _finite_positive(acquisition["sample_rate_hz"],
                                      "acquisition.sample_rate_hz")
    coverage = _finite_positive(acquisition["uncertainty_coverage_factor"],
                                "uncertainty_coverage_factor")
    method = acquisition["method"]
    channels = recipe["channels"]
    force_cfg = channels["force"]
    structural_cfg = channels["structural_response"]
    analysis = recipe.get("analysis", {})
    window_name = analysis.get(
        "window", "boxcar" if method == "impact_hammer_frf" else "hann")
    partial_indices = analysis.get("model_partial_indices",
                                   list(range(len(predicted))))
    if not partial_indices or len(set(partial_indices)) != len(partial_indices):
        raise PipelineError("analysis.model_partial_indices must be non-empty and unique")
    if any(not isinstance(index, int) or index < 0 or index >= len(predicted)
           for index in partial_indices):
        raise PipelineError("analysis.model_partial_indices contains an absent partial")
    reference_index = measurement["relative_magnitude_reference_partial_index"]
    if reference_index not in partial_indices:
        raise PipelineError("relative magnitude reference partial is not selected")

    structural_specs = _expand_record_specs(
        recipe.get("structural_records", []), base, "structural_records")
    minimum_averages = int(analysis.get("minimum_averages", 8))
    if minimum_averages < 2:
        raise PipelineError("analysis.minimum_averages must be at least 2")
    if len(structural_specs) < minimum_averages:
        raise PipelineError(
            f"need at least {minimum_averages} structural_records; got {len(structural_specs)}")
    structural_records = [
        _record_arrays(item, base, sample_rate_hz, force_cfg, structural_cfg, method)
        for item in structural_specs
    ]
    force_delay = float(force_cfg.get("delay_s", 0.0))
    structural_delay = float(structural_cfg.get("delay_s", 0.0))
    structural_frf = _aggregate_frf(
        structural_records, sample_rate_hz, window_name,
        structural_delay - force_delay)
    frequency_resolution = float(structural_frf["frequencies"][1]
                                 - structural_frf["frequencies"][0])
    acquisition["frequency_resolution_hz"] = frequency_resolution
    acquisition["averages"] = len(structural_records)
    floors = analysis.get("uncertainty_floor", {})
    search_default = max(2.0 * frequency_resolution,
                         float(analysis.get("frequency_search_half_width_hz", 5.0)))
    fit_upper = float(analysis.get("decay_fit_upper_db", -5.0))
    fit_lower = float(analysis.get("decay_fit_lower_db", -35.0))
    if not fit_lower < fit_upper < 0.0:
        raise PipelineError("decay fit limits must satisfy lower < upper < 0 dB")
    minimum_r2 = float(analysis.get("min_decay_fit_r2", 0.90))

    extracted: dict[int, dict[str, Any]] = {}
    for partial_index in partial_indices:
        target = _finite_positive(predicted[partial_index]["freq"],
                                  f"partial {partial_index} frequency")
        half_width = max(search_default, target * float(analysis.get("relative_search_half_width", 0.01)))
        bin_index = _target_bin(structural_frf["frequencies"],
                                np.abs(structural_frf["h1"]), target, half_width)
        measured_frequency = float(structural_frf["frequencies"][bin_index])
        individual_bins = [
            _target_bin(structural_frf["frequencies"], np.abs(trial), target, half_width)
            for trial in structural_frf["individual"]
        ]
        individual_frequencies = structural_frf["frequencies"][individual_bins]
        complex_value = complex(structural_frf["h1"][bin_index])
        individual_values = structural_frf["individual"][:, bin_index]
        levels_db = 20.0 * np.log10(np.maximum(np.abs(individual_values), 1.0e-300))
        phases_deg = np.degrees(np.angle(individual_values))
        bandwidth = float(analysis.get("decay_bandwidth_hz",
                                       max(20.0, measured_frequency * 0.10)))
        decays = []
        fit_scores = []
        if method == "impact_hammer_frf":
            decay_inputs = [(record["response"], record["force"])
                            for record in structural_records]
        else:
            decay_inputs = []
            record_length = len(structural_records[0]["force"])
            for individual_h in structural_frf["individual"]:
                impulse_response = np.fft.irfft(individual_h, n=record_length)
                unit_impulse = np.zeros(record_length, dtype=np.float64)
                unit_impulse[0] = 1.0
                decay_inputs.append((impulse_response, unit_impulse))
        for decay_response, decay_force in decay_inputs:
            t60, r2 = _decay_t60(
                decay_response, decay_force, sample_rate_hz,
                measured_frequency, bandwidth, fit_upper, fit_lower)
            if r2 < minimum_r2:
                raise PipelineError(
                    f"partial {partial_index} decay fit R^2 {r2:.4f} < {minimum_r2:.4f}")
            decays.append(t60)
            fit_scores.append(r2)
        extracted[partial_index] = {
            "frequency_hz": measured_frequency,
            "frequency_u_hz": _expanded_sem(
                individual_frequencies, coverage,
                float(floors.get("frequency_hz", frequency_resolution / 2.0))),
            "absolute_level_db": 20.0 * math.log10(abs(complex_value)),
            "magnitude_u_db": _expanded_sem(
                levels_db, coverage, float(floors.get("magnitude_db", 0.0))),
            "t60_s": float(np.mean(decays)),
            "t60_u_s": _expanded_sem(
                np.asarray(decays), coverage, float(floors.get("t60_s", 0.0))),
            "coherence": float(structural_frf["coherence"][bin_index]),
            "phase_deg": float(math.degrees(math.atan2(complex_value.imag, complex_value.real))),
            "phase_u_deg": _circular_expanded_sem_deg(
                phases_deg, coverage, float(floors.get("phase_deg", 0.0))),
            "frf_real_si_per_n": complex_value.real,
            "frf_imag_si_per_n": complex_value.imag,
            "decay_fit_r2": float(min(fit_scores)),
        }
    reference_level = extracted[reference_index]["absolute_level_db"]
    measured_modes = []
    for partial_index in partial_indices:
        item = dict(extracted[partial_index])
        item["model_partial_index"] = partial_index
        item["relative_magnitude_db"] = item.pop("absolute_level_db") - reference_level
        measured_modes.append(item)
    measurement["measured_modes"] = measured_modes

    acoustic_specs = _expand_record_specs(
        recipe.get("acoustic_records", []), base, "acoustic_records")
    acoustic_records: list[dict[str, Any]] = []
    calibration_result = None
    calibrator_evidence: list[tuple[str, Path]] = []
    acoustic_groups: dict[tuple[float, float, float], list[dict[str, Any]]] = {}
    if acoustic_specs:
        microphone_cfg = dict(channels["microphone"])
        sensitivity, calibration_result, calibrator_evidence = _calibrator_sensitivity(
            recipe, base, sample_rate_hz, microphone_cfg)
        microphone_cfg["sensitivity_v_per_si"] = sensitivity
        microphone_delay = float(microphone_cfg.get("delay_s", 0.0))
        for spec in acoustic_specs:
            radius = _finite_positive(spec["radius_m"], "acoustic radius_m")
            azimuth = float(spec["azimuth_deg"])
            elevation = float(spec["elevation_deg"])
            if not (-180.0 <= azimuth <= 360.0 and -90.0 <= elevation <= 90.0):
                raise PipelineError("acoustic coordinate is outside the schema range")
            record = _record_arrays(
                spec, base, sample_rate_hz, force_cfg, microphone_cfg, method)
            record["coordinate"] = (radius, azimuth, elevation)
            acoustic_records.append(record)
            acoustic_groups.setdefault(record["coordinate"], []).append(record)
        short_groups = [coordinate for coordinate, records in acoustic_groups.items()
                        if len(records) < minimum_averages]
        if short_groups:
            raise PipelineError(
                f"each acoustic coordinate needs {minimum_averages} records; "
                f"insufficient at {short_groups}")
        reference_force = _finite_positive(
            analysis.get("reference_force_rms_n", 1.0), "reference_force_rms_n")
        acoustic_measurements = []
        for coordinate, records in sorted(acoustic_groups.items()):
            result = _aggregate_frf(
                records, sample_rate_hz, window_name, microphone_delay - force_delay)
            acoustic_resolution = float(result["frequencies"][1]
                                        - result["frequencies"][0])
            if abs(acoustic_resolution - frequency_resolution) > 1.0e-12:
                raise PipelineError(
                    "structural and acoustic records must use the same FFT length/resolution")
            for partial_index in partial_indices:
                frequency_hz = extracted[partial_index]["frequency_hz"]
                bin_index = int(np.argmin(np.abs(result["frequencies"] - frequency_hz)))
                complex_value = complex(result["h1"][bin_index])
                if abs(complex_value) <= 0.0:
                    raise PipelineError("zero pressure/force transfer cannot form SPL")
                individual_values = result["individual"][:, bin_index]
                levels_db = 20.0 * np.log10(np.maximum(np.abs(individual_values), 1.0e-300))
                phases_deg = np.degrees(np.angle(individual_values))
                transfer_level = 20.0 * math.log10(abs(complex_value) / P_REF_PA)
                acoustic_measurements.append({
                    "model_partial_index": partial_index,
                    "frequency_hz": float(result["frequencies"][bin_index]),
                    "radius_m": coordinate[0], "azimuth_deg": coordinate[1],
                    "elevation_deg": coordinate[2],
                    "pressure_per_force_real_pa_n": complex_value.real,
                    "pressure_per_force_imag_pa_n": complex_value.imag,
                    "transfer_level_db_re_20upa_per_n": transfer_level,
                    "transfer_u_db": _expanded_sem(
                        levels_db, coverage,
                        float(floors.get("acoustic_level_db", 0.0))),
                    "phase_u_deg": _circular_expanded_sem_deg(
                        phases_deg, coverage,
                        float(floors.get("acoustic_phase_deg", 0.0))),
                    "coherence": float(result["coherence"][bin_index]),
                    "reference_force_rms_n": reference_force,
                    "spl_db_re_20upa": transfer_level
                        + 20.0 * math.log10(reference_force),
                })
        measurement["acoustic_measurements"] = acoustic_measurements
    elif (measurement["claim_scope"]["absolute_spl"]
          or measurement["claim_scope"]["radiation_directivity"]):
        raise PipelineError("acoustic claims are enabled but acoustic_records is empty")

    output_directory = output_directory.resolve()
    if output_directory.exists():
        raise PipelineError(f"output directory already exists: {output_directory}")
    output_directory.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(
        prefix=f".{output_directory.name}-", dir=output_directory.parent))
    try:
        artifacts: list[dict[str, str]] = []
        raw_items: list[tuple[str, Path]] = []
        for record in structural_records:
            raw_items.extend((("raw_excitation", record["path"]),
                              ("raw_response", record["path"])))
        for record in acoustic_records:
            raw_items.extend((("raw_excitation", record["path"]),
                              ("raw_acoustic_response", record["path"])))
        raw_items.extend(calibrator_evidence)
        raw_map = _copy_inputs(raw_items, temporary, "raw", artifacts)

        evidence_items = []
        for item in recipe.get("evidence", []):
            role = item.get("role")
            if role not in EVIDENCE_ROLES:
                raise PipelineError(f"unsupported evidence role: {role!r}")
            evidence_items.append((role, _resolve(base, item["path"], role)))
        evidence_roles = {item[0] for item in evidence_items}
        required_evidence = {"excitation_calibration", "response_calibration"}
        if acoustic_records:
            required_evidence.add("acoustic_calibration")
        missing_evidence = sorted(required_evidence - evidence_roles)
        if missing_evidence:
            raise PipelineError("missing calibration evidence: " + ", ".join(missing_evidence))
        evidence_map = _copy_inputs(evidence_items, temporary, "calibration", artifacts)

        model_relative = Path("model") / "modes.json"
        (temporary / model_relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dump_path, temporary / model_relative)
        measurement["model"]["mode_dump_path"] = model_relative.as_posix()
        measurement["model"]["mode_dump_sha256"] = _sha256(temporary / model_relative)

        config_dir = temporary / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        source_config_relative = Path("config") / "acquisition-source.json"
        shutil.copy2(recipe_path, temporary / source_config_relative)
        artifacts.append(_artifact("analysis_config", source_config_relative, temporary))
        template_relative = Path("config") / "measurement-template.json"
        shutil.copy2(template_path, temporary / template_relative)
        artifacts.append(_artifact("analysis_config", template_relative, temporary))
        resolved_recipe = json.loads(json.dumps(recipe))
        resolved_recipe["measurement_template"] = "measurement-template.json"
        resolved_recipe["mode_dump"] = "../" + model_relative.as_posix()
        resolved_recipe["structural_records"] = copy.deepcopy(structural_specs)
        for source_item, resolved_item in zip(
                structural_specs, resolved_recipe["structural_records"]):
            source = _resolve(base, source_item["path"], "structural record").resolve()
            resolved_item["path"] = "../" + raw_map[source].as_posix()
        resolved_recipe["acoustic_records"] = copy.deepcopy(acoustic_specs)
        for source_item, resolved_item in zip(
                acoustic_specs, resolved_recipe["acoustic_records"]):
            source = _resolve(base, source_item["path"], "acoustic record").resolve()
            resolved_item["path"] = "../" + raw_map[source].as_posix()
        if calibrator_evidence:
            for label in ("before_path", "after_path"):
                source = _resolve(base, recipe["calibrator"][label], label).resolve()
                resolved_recipe["calibrator"][label] = "../" + raw_map[source].as_posix()
        for source_item, resolved_item in zip(
                recipe.get("evidence", []), resolved_recipe.get("evidence", [])):
            source = _resolve(base, source_item["path"], source_item["role"]).resolve()
            resolved_item["path"] = "../" + evidence_map[source].as_posix()
        resolved_config_relative = Path("config") / "acquisition.json"
        (temporary / resolved_config_relative).write_text(
            json.dumps(resolved_recipe, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        artifacts.append(_artifact("analysis_config", resolved_config_relative, temporary))

        analysis_dir = temporary / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        frf_relative = Path("analysis") / "structural-h1-frf.csv"
        with (temporary / frf_relative).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("frequency_hz", "real_si_per_n", "imag_si_per_n",
                             "magnitude_si_per_n", "phase_deg", "coherence"))
            for frequency, value, coherence in zip(
                    structural_frf["frequencies"], structural_frf["h1"],
                    structural_frf["coherence"]):
                writer.writerow((float(frequency), float(value.real), float(value.imag),
                                 float(abs(value)),
                                 float(math.degrees(math.atan2(value.imag, value.real))),
                                 float(coherence)))
        artifacts.append(_artifact("derived_frf", frf_relative, temporary))

        if acoustic_records:
            acoustic_relative = Path("analysis") / "acoustic-transfer.csv"
            with (temporary / acoustic_relative).open("w", newline="", encoding="utf-8") as handle:
                fieldnames = list(measurement["acoustic_measurements"][0])
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(measurement["acoustic_measurements"])
            artifacts.append(_artifact(
                "derived_acoustic_transfer", acoustic_relative, temporary))
            calibration_relative = Path("analysis") / "microphone-calibration.json"
            (temporary / calibration_relative).write_text(
                json.dumps(calibration_result, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8")
            artifacts.append(_artifact("derived_calibration", calibration_relative, temporary))

        uncertainty = {
            "coverage_factor": coverage,
            "method": "expanded standard error of repeated complex FRFs, RSS with declared floors",
            "frequency_resolution_hz": frequency_resolution,
            "record_counts": {
                "structural": len(structural_records),
                "acoustic_by_coordinate": {
                    f"r={key[0]},az={key[1]},el={key[2]}": len(value)
                    for key, value in sorted(acoustic_groups.items())
                },
            },
            "declared_uncertainty_floor": floors,
            "microphone_calibration": calibration_result,
            "notes": [
                "Statistical automation does not include unentered fixture, geometry or material uncertainty.",
                "Model uncertainty remains independently declared in measurement.model.uncertainty."
            ],
        }
        uncertainty_relative = Path("analysis") / "uncertainty-budget.json"
        (temporary / uncertainty_relative).write_text(
            json.dumps(uncertainty, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        artifacts.append(_artifact("uncertainty_analysis", uncertainty_relative, temporary))
        measurement["artifacts"] = artifacts

        measurement_path = temporary / "measurement.json"
        measurement_path.write_text(
            json.dumps(measurement, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8")

        # Validate the assembled result with the same production verifier before
        # publishing the directory.  UNVERIFIED is allowed because current model
        # dumps may intentionally lack phase/acoustic predictions; REFUSED is not.
        from tools import specimen_verify
        report = specimen_verify.verify_bundle(measurement_path)
        if report["status"] == "REFUSED":
            raise PipelineError(f"assembled bundle was refused: {report['summary']}")
        (temporary / "verification-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8")
        os.replace(temporary, output_directory)
        return output_directory / "measurement.json"
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a calibrated, hashed Specimen Measurement v2 bundle")
    parser.add_argument("recipe", help="Specimen Acquisition v1 recipe JSON")
    parser.add_argument("--out", required=True,
                        help="new output directory (must not already exist)")
    args = parser.parse_args()
    try:
        measurement = build_bundle(Path(args.recipe), Path(args.out))
    except (PipelineError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"REFUSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(f"BUNDLE: {measurement}")
    report_path = measurement.parent / "verification-report.json"
    report = _load_json(report_path)
    print(f"MODEL RESULT: {report['status']}")
    print(f"REPORT: {report_path}")
    print(f"REVERIFY: {sys.executable} tools/specimen_verify.py {measurement}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
