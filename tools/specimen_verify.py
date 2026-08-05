#!/usr/bin/env python3
"""Compare a real-specimen measurement bundle with a model mode dump.

The v1 contract covers modal frequency, relative amplitude, T60 and optional
phase.  The v2 contract additionally carries calibrated pressure/force points
so absolute acoustic transfer and complex radiation directivity can be judged
when (and only when) the model dump contains matching physical predictions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


CONTRACT = "TsukiSynth Specimen Measurement v1"
CONTRACT_V2 = "TsukiSynth Specimen Measurement v2"
MODE_DUMP_CONTRACT = "TsukiSynth Mode Dump v2"
SCHEMA_DIR = Path(__file__).resolve().parent.parent / "specimens" / "schema"
SCHEMA_PATHS = {
    CONTRACT: SCHEMA_DIR / "specimen_measurement.schema.json",
    CONTRACT_V2: SCHEMA_DIR / "specimen_measurement_v2.schema.json",
}
REQUIRED_ARTIFACT_ROLES = {
    "raw_excitation",
    "raw_response",
    "excitation_calibration",
    "response_calibration",
    "uncertainty_analysis",
}
V2_REQUIRED_ARTIFACT_ROLES = {"analysis_config", "derived_frf"}
V2_ACOUSTIC_ARTIFACT_ROLES = {
    "raw_acoustic_response", "acoustic_calibration", "derived_acoustic_transfer",
}
EXIT_CODES = {"PASS": 0, "FAIL": 1, "REFUSED": 2, "UNVERIFIED": 3}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _claim(name: str, requested: bool, status: str, message: str,
           modes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": name,
        "requested": requested,
        "status": status,
        "message": message,
    }
    if modes is not None:
        result["modes"] = modes
    return result


def _refused(message: str, specimen_id: str | None = None,
             details: list[str] | None = None) -> dict[str, Any]:
    return {
        "contract": "TsukiSynth Specimen Verification Report v1",
        "specimen_id": specimen_id,
        "status": "REFUSED",
        "exit_code": EXIT_CODES["REFUSED"],
        "summary": message,
        "provenance": details or [],
        "claims": [],
    }


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _schema_errors(bundle: Any) -> list[str]:
    if not isinstance(bundle, dict) or bundle.get("$schema") not in SCHEMA_PATHS:
        known = ", ".join(repr(item) for item in SCHEMA_PATHS)
        return [f"$schema: expected one of {known}"]
    schema = _load_json(SCHEMA_PATHS[bundle["$schema"]])
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(bundle),
                    key=lambda error: tuple(str(part) for part in error.absolute_path))
    rendered = []
    for error in errors:
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        rendered.append(f"{path}: {error.message}")
    return rendered


def _verify_artifacts(bundle_path: Path, artifacts: list[dict[str, Any]],
                      required_roles: set[str] | None = None) -> tuple[bool, list[str]]:
    base = bundle_path.parent.resolve()
    roles: set[str] = set()
    role_paths: set[tuple[str, str]] = set()
    hash_cache: dict[Path, str] = {}
    messages: list[str] = []
    ok = True
    for artifact in artifacts:
        role = artifact["role"]
        role_path = (role, artifact["path"])
        if role_path in role_paths:
            ok = False
            messages.append(f"duplicate artifact entry: {role}: {artifact['path']}")
            continue
        role_paths.add(role_path)
        roles.add(role)
        relative = Path(artifact["path"])
        if relative.is_absolute():
            ok = False
            messages.append(f"{role}: absolute paths are forbidden")
            continue
        candidate = (base / relative).resolve()
        try:
            candidate.relative_to(base)
        except ValueError:
            ok = False
            messages.append(f"{role}: path escapes the measurement bundle directory")
            continue
        if not candidate.is_file():
            ok = False
            messages.append(f"{role}: file not found: {relative.as_posix()}")
            continue
        actual = hash_cache.get(candidate)
        if actual is None:
            actual = _sha256(candidate)
            hash_cache[candidate] = actual
        if actual.lower() != artifact["sha256"].lower():
            ok = False
            messages.append(f"{role}: SHA256 mismatch ({actual})")
        else:
            messages.append(f"{role}: SHA256 verified ({actual})")

    missing = sorted((required_roles or REQUIRED_ARTIFACT_ROLES) - roles)
    if missing:
        ok = False
        messages.append("missing required artifact roles: " + ", ".join(missing))
    return ok, messages


def _event_from_dump(dump: dict[str, Any], source_index: int) -> dict[str, Any] | None:
    matching = [event for event in dump.get("events", [])
                if event.get("source_index") == source_index]
    return matching[0] if len(matching) == 1 else None


def _wrap_phase_error(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _resolve_bundled_path(bundle_path: Path, relative_text: str) -> Path | None:
    base = bundle_path.parent.resolve()
    relative = Path(relative_text)
    if relative.is_absolute():
        return None
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate


def _complex_level_db(real: float, imag: float) -> float:
    magnitude = math.hypot(real, imag)
    if magnitude <= 0.0:
        raise ValueError("complex pressure/force magnitude must be positive")
    return 20.0 * math.log10(magnitude / 20.0e-6)


def _acoustic_key(point: dict[str, Any]) -> tuple[int, float, float, float]:
    return (int(point["model_partial_index"]), float(point["radius_m"]),
            float(point["azimuth_deg"]), float(point["elevation_deg"]))


def verify_bundle(bundle_path: Path, dump_path: Path | None = None) -> dict[str, Any]:
    bundle_path = Path(bundle_path)
    try:
        bundle = _load_json(bundle_path)
    except Exception as exc:
        return _refused(f"cannot read measurement bundle: {type(exc).__name__}: {exc}")

    specimen_id = ((bundle.get("specimen") or {}).get("id")
                   if isinstance(bundle, dict) else None)
    try:
        errors = _schema_errors(bundle)
    except Exception as exc:
        return _refused(f"cannot load validation schema: {type(exc).__name__}: {exc}", specimen_id)
    if errors:
        return _refused("measurement bundle does not satisfy the v1 schema",
                        specimen_id, errors)

    all_numbers: list[Any] = []
    for mode in bundle["measured_modes"]:
        all_numbers.extend(value for key, value in mode.items() if key != "model_partial_index")
    for point in bundle.get("acoustic_measurements", []):
        all_numbers.extend(point.values())
    all_numbers.extend(bundle["model"]["uncertainty"].values())
    all_numbers.extend(bundle["acceptance"].values())
    if not all(_finite_number(value) for value in all_numbers):
        return _refused("NaN or infinity is forbidden in measurement data", specimen_id)

    required_roles = set(REQUIRED_ARTIFACT_ROLES)
    if bundle["$schema"] == CONTRACT_V2:
        required_roles.update(V2_REQUIRED_ARTIFACT_ROLES)
        scopes = bundle["claim_scope"]
        if scopes["absolute_spl"] or scopes["radiation_directivity"]:
            required_roles.update(V2_ACOUSTIC_ARTIFACT_ROLES)
    provenance_ok, provenance = _verify_artifacts(
        bundle_path, bundle["artifacts"], required_roles)
    if not provenance_ok:
        return _refused("measurement artifact provenance failed", specimen_id, provenance)

    if dump_path is None:
        relative_dump = bundle["model"].get("mode_dump_path")
        if not relative_dump:
            return _refused("mode dump path was not supplied", specimen_id, provenance)
        dump_path = _resolve_bundled_path(bundle_path, relative_dump)
        if dump_path is None:
            return _refused("model.mode_dump_path escapes the measurement bundle directory",
                            specimen_id, provenance)
    else:
        dump_path = Path(dump_path)
    if not dump_path.is_file():
        return _refused(f"mode dump not found: {dump_path}", specimen_id, provenance)
    actual_dump_hash = _sha256(dump_path)
    expected_dump_hash = bundle["model"]["mode_dump_sha256"].lower()
    if actual_dump_hash != expected_dump_hash:
        provenance.append(f"mode_dump: SHA256 mismatch ({actual_dump_hash})")
        return _refused("mode-dump provenance failed", specimen_id, provenance)
    provenance.append(f"mode_dump: SHA256 verified ({actual_dump_hash})")

    try:
        dump = _load_json(dump_path)
    except Exception as exc:
        return _refused(f"cannot read mode dump: {type(exc).__name__}: {exc}",
                        specimen_id, provenance)
    if dump.get("contract") != MODE_DUMP_CONTRACT:
        return _refused(f"mode dump must use {MODE_DUMP_CONTRACT!r}", specimen_id, provenance)

    event = _event_from_dump(dump, bundle["model"]["event_source_index"])
    if event is None:
        return _refused("mode dump must contain exactly one matching source_index",
                        specimen_id, provenance)
    predicted = event.get("partials")
    if not isinstance(predicted, list) or not predicted:
        return _refused("selected model event has no predicted partials",
                        specimen_id, provenance)

    predicted_by_index: dict[int, dict[str, float]] = {}
    for index, partial in enumerate(predicted):
        values = (partial.get("freq"), partial.get("amp"), partial.get("decay"),
                  partial.get("body_mag", 1.0))
        if not all(_finite_number(value) for value in values):
            return _refused(f"model partial {index} contains a non-finite number",
                            specimen_id, provenance)
        freq, amp, decay, body_mag = map(float, values)
        if freq <= 0.0 or decay <= 0.0 or abs(amp * body_mag) <= 0.0:
            return _refused(f"model partial {index} is not physically comparable",
                            specimen_id, provenance)
        predicted_by_index[index] = {
            "frequency_hz": freq,
            "magnitude_linear": abs(amp * body_mag),
            "t60_s": decay,
        }
        if _finite_number(partial.get("phase_deg")):
            predicted_by_index[index]["phase_deg"] = float(partial["phase_deg"])

    predicted_acoustic_by_key: dict[tuple[int, float, float, float], dict[str, float]] = {}
    for point_index, point in enumerate(event.get("acoustic_transfer", [])):
        if not isinstance(point, dict):
            return _refused(f"model acoustic point {point_index} is not an object",
                            specimen_id, provenance)
        required = ("model_partial_index", "radius_m", "azimuth_deg", "elevation_deg",
                    "pressure_per_force_real_pa_n", "pressure_per_force_imag_pa_n")
        if any(name not in point or not _finite_number(point[name]) for name in required):
            return _refused(f"model acoustic point {point_index} is incomplete or non-finite",
                            specimen_id, provenance)
        if (not isinstance(point["model_partial_index"], int)
                or isinstance(point["model_partial_index"], bool)):
            return _refused(f"model acoustic point {point_index} has a non-integer partial index",
                            specimen_id, provenance)
        key = _acoustic_key(point)
        if key in predicted_acoustic_by_key:
            return _refused(f"duplicate model acoustic coordinate: {key}",
                            specimen_id, provenance)
        if key[0] not in predicted_by_index or key[1] <= 0.0:
            return _refused(f"model acoustic point {point_index} has an invalid partial or radius",
                            specimen_id, provenance)
        real = float(point["pressure_per_force_real_pa_n"])
        imag = float(point["pressure_per_force_imag_pa_n"])
        try:
            level_db = _complex_level_db(real, imag)
        except ValueError as exc:
            return _refused(f"model acoustic point {point_index}: {exc}",
                            specimen_id, provenance)
        predicted_acoustic_by_key[key] = {
            "real": real, "imag": imag, "level_db": level_db,
            "phase_deg": math.degrees(math.atan2(imag, real)),
        }

    measured_by_index: dict[int, dict[str, Any]] = {}
    for mode in bundle["measured_modes"]:
        index = mode["model_partial_index"]
        if index in measured_by_index:
            return _refused(f"duplicate measured model_partial_index: {index}",
                            specimen_id, provenance)
        if index not in predicted_by_index:
            return _refused(f"measured partial index {index} is absent from model dump",
                            specimen_id, provenance)
        if mode["t60_u_s"] >= mode["t60_s"]:
            return _refused(f"partial {index}: t60 uncertainty reaches or exceeds T60",
                            specimen_id, provenance)
        measured_by_index[index] = mode

    measured_acoustic_by_key: dict[tuple[int, float, float, float], dict[str, Any]] = {}
    for point_index, point in enumerate(bundle.get("acoustic_measurements", [])):
        key = _acoustic_key(point)
        if key in measured_acoustic_by_key:
            return _refused(f"duplicate measured acoustic coordinate: {key}",
                            specimen_id, provenance)
        if key[0] not in predicted_by_index:
            return _refused(f"measured acoustic partial {key[0]} is absent from model dump",
                            specimen_id, provenance)
        if (abs(point["frequency_hz"] - measured_by_index[key[0]]["frequency_hz"])
                > bundle["acquisition"]["frequency_resolution_hz"] + 1.0e-9):
            return _refused(
                f"measured acoustic point {point_index}: frequency is not the matched modal bin",
                specimen_id, provenance)
        try:
            calculated_level = _complex_level_db(
                point["pressure_per_force_real_pa_n"],
                point["pressure_per_force_imag_pa_n"])
        except ValueError as exc:
            return _refused(f"measured acoustic point {point_index}: {exc}",
                            specimen_id, provenance)
        if abs(calculated_level - point["transfer_level_db_re_20upa_per_n"]) > 1.0e-6:
            return _refused(
                f"measured acoustic point {point_index}: transfer level does not match complex Pa/N",
                specimen_id, provenance)
        expected_spl = calculated_level + 20.0 * math.log10(point["reference_force_rms_n"])
        if abs(expected_spl - point["spl_db_re_20upa"]) > 1.0e-6:
            return _refused(
                f"measured acoustic point {point_index}: SPL does not match Pa/N and reference force",
                specimen_id, provenance)
        measured_acoustic_by_key[key] = point

    reference = bundle.get("relative_magnitude_reference_partial_index")
    if reference is None:
        return _refused("relative_magnitude_reference_partial_index is required",
                        specimen_id, provenance)
    if reference not in measured_by_index or reference not in predicted_by_index:
        return _refused("relative-magnitude reference partial must be measured and predicted",
                        specimen_id, provenance)
    if abs(measured_by_index[reference]["relative_magnitude_db"]) > 1.0e-6:
        return _refused("measured reference partial must be exactly 0 dB",
                        specimen_id, provenance)

    scopes = bundle["claim_scope"]
    if not any(scopes.values()):
        return _refused("at least one physical claim must be requested",
                        specimen_id, provenance)
    acceptance = bundle["acceptance"]
    model_u = bundle["model"]["uncertainty"]
    observables = set(dump.get("model_observables", []))
    claims: list[dict[str, Any]] = []

    quality_modes = []
    quality_ok = len(measured_by_index) >= acceptance["min_mode_count"]
    for index, measured in sorted(measured_by_index.items()):
        passed = measured["coherence"] >= acceptance["min_coherence"]
        quality_ok = quality_ok and passed
        quality_modes.append({
            "partial_index": index,
            "coherence": measured["coherence"],
            "minimum": acceptance["min_coherence"],
            "status": "PASS" if passed else "FAIL",
        })
    for key, measured in sorted(measured_acoustic_by_key.items()):
        passed = measured["coherence"] >= acceptance["min_coherence"]
        quality_ok = quality_ok and passed
        quality_modes.append({
            "partial_index": key[0], "acoustic": True,
            "radius_m": key[1], "azimuth_deg": key[2], "elevation_deg": key[3],
            "coherence": measured["coherence"],
            "minimum": acceptance["min_coherence"],
            "status": "PASS" if passed else "FAIL",
        })
    claims.append(_claim(
        "measurement_quality", True, "PASS" if quality_ok else "FAIL",
        f"{len(measured_by_index)} measured mode(s); minimum {acceptance['min_mode_count']}",
        quality_modes))

    requested = scopes["modal_frequencies"]
    if not requested:
        claims.append(_claim("modal_frequencies", False, "N/A", "not requested"))
    elif "modal_frequency_hz" not in observables:
        claims.append(_claim("modal_frequencies", True, "UNVERIFIED",
                             "mode dump does not declare modal_frequency_hz"))
    else:
        mode_results = []
        passed_all = True
        for index, measured in sorted(measured_by_index.items()):
            pred = predicted_by_index[index]["frequency_hz"]
            central = abs(measured["frequency_hz"] - pred) / pred * 100.0
            conservative = central + measured["frequency_u_hz"] / pred * 100.0 \
                + model_u["frequency_relative_pct"]
            passed = conservative <= acceptance["max_frequency_error_pct"]
            passed_all = passed_all and passed
            mode_results.append({
                "partial_index": index, "predicted_hz": pred,
                "measured_hz": measured["frequency_hz"],
                "central_error_pct": central,
                "conservative_error_pct": conservative,
                "limit_pct": acceptance["max_frequency_error_pct"],
                "status": "PASS" if passed else "FAIL",
            })
        claims.append(_claim("modal_frequencies", True,
                             "PASS" if passed_all else "FAIL",
                             "conservative error includes measurement and model uncertainty",
                             mode_results))

    requested = scopes["relative_modal_magnitudes"]
    if not requested:
        claims.append(_claim("relative_modal_magnitudes", False, "N/A", "not requested"))
    elif "relative_modal_amplitude" not in observables:
        claims.append(_claim("relative_modal_magnitudes", True, "UNVERIFIED",
                             "mode dump does not declare relative_modal_amplitude"))
    else:
        ref_linear = predicted_by_index[reference]["magnitude_linear"]
        mode_results = []
        passed_all = True
        for index, measured in sorted(measured_by_index.items()):
            predicted_db = 20.0 * math.log10(
                predicted_by_index[index]["magnitude_linear"] / ref_linear)
            central = abs(measured["relative_magnitude_db"] - predicted_db)
            conservative = central + measured["magnitude_u_db"] \
                + model_u["relative_magnitude_db"]
            passed = conservative <= acceptance["max_relative_magnitude_error_db"]
            passed_all = passed_all and passed
            mode_results.append({
                "partial_index": index, "predicted_relative_db": predicted_db,
                "measured_relative_db": measured["relative_magnitude_db"],
                "central_error_db": central,
                "conservative_error_db": conservative,
                "limit_db": acceptance["max_relative_magnitude_error_db"],
                "status": "PASS" if passed else "FAIL",
            })
        claims.append(_claim("relative_modal_magnitudes", True,
                             "PASS" if passed_all else "FAIL",
                             "relative to the declared reference partial; absolute SPL is not inferred",
                             mode_results))

    requested = scopes["modal_t60"]
    if not requested:
        claims.append(_claim("modal_t60", False, "N/A", "not requested"))
    elif "modal_t60_s" not in observables:
        claims.append(_claim("modal_t60", True, "UNVERIFIED",
                             "mode dump does not declare modal_t60_s"))
    else:
        mode_results = []
        passed_all = True
        model_fraction = model_u["t60_relative_pct"] / 100.0
        for index, measured in sorted(measured_by_index.items()):
            pred = predicted_by_index[index]["t60_s"]
            pred_low, pred_high = pred * (1.0 - model_fraction), pred * (1.0 + model_fraction)
            measured_low = measured["t60_s"] - measured["t60_u_s"]
            measured_high = measured["t60_s"] + measured["t60_u_s"]
            conservative_ratio = max(measured_high / pred_low, pred_high / measured_low)
            central_ratio = max(measured["t60_s"] / pred, pred / measured["t60_s"])
            passed = conservative_ratio <= acceptance["max_t60_ratio"]
            passed_all = passed_all and passed
            mode_results.append({
                "partial_index": index, "predicted_s": pred,
                "measured_s": measured["t60_s"], "central_ratio": central_ratio,
                "conservative_ratio": conservative_ratio,
                "limit_ratio": acceptance["max_t60_ratio"],
                "status": "PASS" if passed else "FAIL",
            })
        claims.append(_claim("modal_t60", True, "PASS" if passed_all else "FAIL",
                             "worst interval ratio includes measurement and model uncertainty",
                             mode_results))

    requested = scopes["complex_phase"]
    if not requested:
        claims.append(_claim("complex_phase", False, "N/A", "not requested"))
    elif "complex_phase" not in observables or any(
            "phase_deg" not in predicted_by_index[index] for index in measured_by_index):
        claims.append(_claim("complex_phase", True, "UNVERIFIED",
                             "current physical model does not emit complex modal phase"))
    else:
        mode_results = []
        passed_all = True
        for index, measured in sorted(measured_by_index.items()):
            if "phase_deg" not in measured or "phase_u_deg" not in measured:
                return _refused(f"partial {index}: requested phase data is missing",
                                specimen_id, provenance)
            central = _wrap_phase_error(measured["phase_deg"],
                                        predicted_by_index[index]["phase_deg"])
            conservative = central + measured["phase_u_deg"] + model_u["phase_deg"]
            passed = conservative <= acceptance["max_phase_error_deg"]
            passed_all = passed_all and passed
            mode_results.append({
                "partial_index": index, "central_error_deg": central,
                "conservative_error_deg": conservative,
                "limit_deg": acceptance["max_phase_error_deg"],
                "status": "PASS" if passed else "FAIL",
            })
        claims.append(_claim("complex_phase", True, "PASS" if passed_all else "FAIL",
                             "wrapped phase error", mode_results))

    requested = scopes["absolute_spl"]
    acoustic_observable = "absolute_pressure_per_force" in observables \
        or "absolute_spl" in observables
    if not requested:
        claims.append(_claim("absolute_spl", False, "N/A", "not requested"))
    elif not acoustic_observable:
        claims.append(_claim(
            "absolute_spl", True, "UNVERIFIED",
            "model has no calibrated force-to-pressure transfer"))
    elif not measured_acoustic_by_key:
        claims.append(_claim("absolute_spl", True, "UNVERIFIED",
                             "bundle has no calibrated acoustic measurement points"))
    else:
        missing = sorted(set(measured_acoustic_by_key) - set(predicted_acoustic_by_key))
        if missing:
            claims.append(_claim(
                "absolute_spl", True, "UNVERIFIED",
                f"model lacks {len(missing)} measured acoustic coordinate(s)"))
        else:
            mode_results = []
            passed_all = True
            model_level_u = model_u.get("absolute_level_db", 0.0)
            for key, measured in sorted(measured_acoustic_by_key.items()):
                predicted_point = predicted_acoustic_by_key[key]
                central = abs(measured["transfer_level_db_re_20upa_per_n"]
                              - predicted_point["level_db"])
                conservative = central + measured["transfer_u_db"] + model_level_u
                passed = conservative <= acceptance["max_absolute_level_error_db"]
                passed_all = passed_all and passed
                mode_results.append({
                    "partial_index": key[0], "radius_m": key[1],
                    "azimuth_deg": key[2], "elevation_deg": key[3],
                    "predicted_db_re_20upa_per_n": predicted_point["level_db"],
                    "measured_db_re_20upa_per_n":
                        measured["transfer_level_db_re_20upa_per_n"],
                    "central_error_db": central,
                    "conservative_error_db": conservative,
                    "limit_db": acceptance["max_absolute_level_error_db"],
                    "status": "PASS" if passed else "FAIL",
                })
            claims.append(_claim(
                "absolute_spl", True, "PASS" if passed_all else "FAIL",
                "absolute pressure/force level; reported SPL uses the declared RMS force",
                mode_results))

    requested = scopes["radiation_directivity"]
    if not requested:
        claims.append(_claim("radiation_directivity", False, "N/A", "not requested"))
    elif "radiation_directivity" not in observables:
        claims.append(_claim(
            "radiation_directivity", True, "UNVERIFIED",
            "model has no complex spatial radiation operator"))
    elif not measured_acoustic_by_key:
        claims.append(_claim("radiation_directivity", True, "UNVERIFIED",
                             "bundle has no calibrated directivity points"))
    else:
        missing = sorted(set(measured_acoustic_by_key) - set(predicted_acoustic_by_key))
        if missing:
            claims.append(_claim(
                "radiation_directivity", True, "UNVERIFIED",
                f"model lacks {len(missing)} measured directivity coordinate(s)"))
        else:
            grouped: dict[int, list[tuple[tuple[int, float, float, float], dict[str, Any]]]] = {}
            for key, measured in measured_acoustic_by_key.items():
                grouped.setdefault(key[0], []).append((key, measured))
            mode_results = []
            passed_all = True
            min_points = acceptance["min_directivity_points"]
            model_level_u = model_u.get("directivity_db", 0.0)
            model_phase_u = model_u.get("directivity_phase_deg", 0.0)
            for partial_index, points in sorted(grouped.items()):
                if len(points) < min_points:
                    passed_all = False
                    mode_results.append({
                        "partial_index": partial_index, "point_count": len(points),
                        "minimum_point_count": min_points, "status": "FAIL",
                    })
                    continue
                measured_max = max(point[1]["transfer_level_db_re_20upa_per_n"]
                                   for point in points)
                predicted_max = max(predicted_acoustic_by_key[point[0]]["level_db"]
                                    for point in points)
                for key, measured in sorted(points):
                    predicted_point = predicted_acoustic_by_key[key]
                    measured_relative = measured["transfer_level_db_re_20upa_per_n"] - measured_max
                    predicted_relative = predicted_point["level_db"] - predicted_max
                    level_error = abs(measured_relative - predicted_relative)
                    conservative_level = level_error + measured["transfer_u_db"] + model_level_u
                    measured_phase = math.degrees(math.atan2(
                        measured["pressure_per_force_imag_pa_n"],
                        measured["pressure_per_force_real_pa_n"]))
                    phase_error = _wrap_phase_error(
                        measured_phase, predicted_point["phase_deg"])
                    conservative_phase = (phase_error + measured["phase_u_deg"]
                                          + model_phase_u)
                    passed = (conservative_level <= acceptance["max_directivity_error_db"]
                              and conservative_phase
                              <= acceptance["max_directivity_phase_error_deg"])
                    passed_all = passed_all and passed
                    mode_results.append({
                        "partial_index": partial_index, "radius_m": key[1],
                        "azimuth_deg": key[2], "elevation_deg": key[3],
                        "predicted_relative_db": predicted_relative,
                        "measured_relative_db": measured_relative,
                        "conservative_level_error_db": conservative_level,
                        "level_limit_db": acceptance["max_directivity_error_db"],
                        "conservative_phase_error_deg": conservative_phase,
                        "phase_limit_deg": acceptance["max_directivity_phase_error_deg"],
                        "status": "PASS" if passed else "FAIL",
                    })
            claims.append(_claim(
                "radiation_directivity", True, "PASS" if passed_all else "FAIL",
                "per-mode normalized complex pressure/force pattern",
                mode_results))

    requested_statuses = [item["status"] for item in claims if item["requested"]]
    if "FAIL" in requested_statuses:
        status = "FAIL"
    elif "UNVERIFIED" in requested_statuses:
        status = "UNVERIFIED"
    else:
        status = "PASS"
    return {
        "contract": ("TsukiSynth Specimen Verification Report v2"
                     if bundle["$schema"] == CONTRACT_V2
                     else "TsukiSynth Specimen Verification Report v1"),
        "specimen_id": specimen_id,
        "status": status,
        "exit_code": EXIT_CODES[status],
        "summary": {
            "requested_claims": sum(1 for value in scopes.values() if value),
            "measured_modes": len(measured_by_index),
            "model_event_source_index": bundle["model"]["event_source_index"],
        },
        "provenance": provenance,
        "claims": claims,
    }


def print_report(report: dict[str, Any]) -> None:
    print(f"SPECIMEN: {report.get('specimen_id') or 'N/A'}")
    for message in report.get("provenance", []):
        print(f"  [PROVENANCE] {message}")
    for claim in report.get("claims", []):
        print(f"  [{claim['status']:10s}] {claim['name']}: {claim['message']}")
        failures = [mode for mode in claim.get("modes", []) if mode.get("status") == "FAIL"]
        for mode in failures:
            print(f"      partial {mode['partial_index']}: {json.dumps(mode, ensure_ascii=False)}")
    print(f"RESULT: {report['status']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify real-specimen measurements without listening")
    parser.add_argument("measurement", help="Specimen Measurement v1/v2 JSON bundle")
    parser.add_argument(
        "--dump-modes",
        help="exact Mode Dump v2 JSON; v2 bundles may instead use model.mode_dump_path")
    parser.add_argument("--json-out", help="write the machine-readable verification report")
    args = parser.parse_args()

    report = verify_bundle(
        Path(args.measurement), Path(args.dump_modes) if args.dump_modes else None)
    print_report(report)
    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return int(report["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
