#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
physics_verify.py — ear-free verification that TsukiSynth's RENDERED audio
matches the PHYSICS-MODEL predictions.

This closes "落差 D" of the 2026-06 project goal:
    deaf people + AI verify sound by physical theory, NOT by listening.

Pipeline (per probe = engine × MIDI note):
  1. write a probe .score.json  (single note, all FX off, normalize off)
  2. render it via TsukiSynthCLI  (deterministic since the NoiseGen seeding fix)
  3. FFT the sustain segment, peak-pick each partial (parabolic-interpolated)
  4. compare measured partials against the model-predicted partials
  5. report f0 cents error + per-partial % error, then PASS / FAIL

Why the predictions are exact & clean:
  * Chromatic uses tuneChromaticModesToMidi(); Cimbalom uses tensionForNote().
    Both pin the fundamental to the MIDI pitch:  f0 = 440 * 2**((midi-69)/12).
  * Modal partial RATIOS are material/size-independent (E, rho, L, d all cancel
    in f_n / f_1), so they are universal constants:
        tongue_drum (free-free Euler-Bernoulli beam): r_n = (betaL_n / betaL_1)**2
        water_gong  (Kirchhoff circular plate):        r_n = (j_n / j_1)**2
        cimbalom    (stiff string):  r_n ~= n, with an inharmonic stretch
                                     f_n = n*f1*sqrt(1+B n^2) (reported, not failed)
        fm piano (ratio 1):          harmonic, r_n = n

T60_RATIO_TOLERANCE = (0.2, 5.0)   # measured/model ratio must be within this range

Usage:
    python tools/physics_verify.py                 # default probe set
    python tools/physics_verify.py --notes 60 69   # MIDI notes to test
    python tools/physics_verify.py --engines tongue_drum water_gong
    python tools/physics_verify.py --cli <path-to-TsukiSynthCLI.exe>
    python tools/physics_verify.py --levels        # velocity/output-level report
    python tools/physics_verify.py --t60           # modal decay T60 report
    python tools/physics_verify.py --amps          # M2-2d: first-5-partial rel-dB
                                                    # judgment vs --dump-modes theory
                                                    # (modal engines, MIDI 60, +/-3.0dB)
    python tools/physics_verify.py --full          # M1 breadth: note-range scan
                                                    # (>=6 notes/engine) + material
                                                    # scan (modal engines) + velocity
                                                    # x2 -> +6dB judgment (all engines)
                                                    # + M2-2d amplitude judgment
Exit code 0 = all probes within tolerance.
"""

import argparse, json, math, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np

# Pre-existing bug fix (not a M1 addition, not a tolerance change): this was
# only ever written inside the module docstring above, never as real code, so
# report_t60()'s `lo, hi = T60_RATIO_TOLERANCE` raised NameError. Restoring it
# with the exact value already documented/registered in ROADMAP_PHYSICS.md §6
# ("T60 比值 0.2-5.0, informational") so --t60 runs instead of crashing.
T60_RATIO_TOLERANCE = (0.2, 5.0)   # measured/model ratio must be within this range

# ── physics constants (mirror the C++ models) ───────────────────────────────
# Free-free Euler-Bernoulli beam eigenvalues betaL  (BeamModel.h)
BEAM_BETAL = [4.730041, 7.853205, 10.995608, 14.137165, 17.278760]
# True clamped circular Kirchhoff-plate frequency parameters Omega=lambda^2
# (Leissa) used by PlateModel.h. f is proportional to Omega (linear).
PLATE_OMEGA = [10.2158, 21.260, 34.877, 39.771, 51.030, 60.829, 69.666, 84.583]


def beam_ratios(n):
    b1 = BEAM_BETAL[0]
    return [(b / b1) ** 2 for b in BEAM_BETAL][:n]


def plate_ratios(n):
    o1 = PLATE_OMEGA[0]
    return [o / o1 for o in PLATE_OMEGA][:n]   # f proportional to Omega


# Approximate free-edge circular plate Omega=lambda^2 (Leissa, nu~0.33) — for A/B.
PLATE_FREE_OMEGA = [5.253, 9.084, 12.23, 20.52, 21.83, 35.25, 38.55]

def plate_free_ratios(n):
    o1 = PLATE_FREE_OMEGA[0]
    return [o / o1 for o in PLATE_FREE_OMEGA][:n]


def harmonic_ratios(n):
    return [float(k) for k in range(1, n + 1)]


def midi_to_hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


# ── engine probe definitions ────────────────────────────────────────────────
# tol_pct: per-partial pass tolerance (%). inharmonic engines report (not fail)
# the upward stretch of high partials.
ENGINES = {
    "cimbalom": dict(
        engine="cimbalom", ratios=harmonic_ratios, npart=6, tol_pct=3.0,
        inharmonic=True,
        params={"material": "steel", "strike_position": 0.27, "diameter_mm": 0.8},
    ),
    "tongue_drum": dict(
        engine="tongue_drum", ratios=beam_ratios, npart=5, tol_pct=4.0,
        inharmonic=False,
        params={"material": "aluminum", "strike_position": 0.27,
                "thickness_mm": 3.0},
    ),
    "water_gong": dict(
        engine="water_gong", ratios=plate_ratios, npart=6, tol_pct=4.0,
        inharmonic=False,
        params={"material": "bronze", "strike_position": 0.30,
                "thickness_mm": 4.0, "plate_free_edge": False},
    ),
    "water_gong_free": dict(
        # npart=4: free plate has two close modes (~3.91 & 4.16, ~6% apart) that
        # the +/-6% measurement window cannot resolve; first 4 are well-separated.
        engine="water_gong", ratios=plate_free_ratios, npart=4, tol_pct=4.0,
        inharmonic=False,
        params={"material": "bronze", "strike_position": 0.30,
                "thickness_mm": 4.0, "plate_free_edge": True},
    ),
    "fm": dict(
        engine="fm", ratios=harmonic_ratios, npart=6, tol_pct=2.0,
        inharmonic=False,
        params={"fm_preset": 0},
    ),
    "piano": dict(
        engine="piano", ratios=harmonic_ratios, npart=6, tol_pct=3.0,
        inharmonic=True,
        params={"material": "steel"},
    ),
}

F0_TOL_CENTS = 12.0  # fundamental pitch tolerance


# ── M1-1a: per-engine valid MIDI range ──────────────────────────────────────
# Source: ROADMAP_PHYSICS.md §3 M1 task 1a — the plugin's documented "sweet
# spot" playable range per engine (Cim C2-C7 / Chr C3-C6 / FM C1-C7 / Piano
# A0-C8). This is a playability/design range, not a hard DSP limit; §1g of
# the roadmap requires recording (not hiding) any out-of-range failure here.
ENGINE_RANGES = {
    "cimbalom":        (36, 96),    # C2-C7
    "tongue_drum":     (48, 84),    # C3-C6
    "water_gong":      (48, 84),    # C3-C6
    "water_gong_free": (48, 84),    # C3-C6 (same physical instrument as water_gong)
    "fm":              (24, 96),    # C1-C7
    "piano":           (21, 108),   # A0-C8
}


def scan_notes(lo, hi, n=6):
    """M1-1b: n evenly-spaced MIDI notes spanning [lo, hi] inclusive (both
    endpoints always included). Rounded to the nearest integer MIDI note and
    de-duplicated (keeps order) so a narrow range doesn't emit repeats."""
    if n <= 1 or hi <= lo:
        return [lo]
    step = (hi - lo) / float(n - 1)
    notes = [int(round(lo + step * i)) for i in range(n)]
    out = []
    for m in notes:
        if not out or out[-1] != m:
            out.append(m)
    return out


# ── WAV reader (16 / 24 / 32-bit PCM → mono float) ──────────────────────────
def read_wav_mono(path):
    wf = wave.open(str(path), "rb")
    sr, ch, sw, n = (wf.getframerate(), wf.getnchannels(),
                     wf.getsampwidth(), wf.getnframes())
    raw = wf.readframes(n)
    wf.close()
    if sw == 2:
        a = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        a = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        a = np.where(a & 0x800000, a - 0x1000000, a).astype(np.float64) / 8388608.0
    elif sw == 4:
        a = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
    else:
        raise ValueError(f"unsupported sample width {sw}")
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    return sr, a


# ── spectral peak measurement (parabolic-interpolated) ──────────────────────
def measure_partials(sr, x, predicted_freqs):
    start = int(0.02 * sr)
    seg = x[start:start + int(0.50 * sr)]   # onset window: fast-decaying high modes still present
    if len(seg) < int(0.1 * sr):
        seg = x[start:]
    if len(seg) < 64:
        return [None] * len(predicted_freqs)
    seg = seg * np.hanning(len(seg))
    N = 1 << int(math.ceil(math.log2(len(seg) * 4)))   # zero-pad ×4
    spec = np.abs(np.fft.rfft(seg, N))
    binhz = sr / N
    out = []
    for fp in predicted_freqs:
        lo, hi = fp * 0.94, fp * 1.06
        klo, khi = int(lo / binhz), int(hi / binhz) + 1
        klo, khi = max(klo, 1), min(khi, len(spec) - 1)
        if khi <= klo:
            out.append(None); continue
        k = klo + int(np.argmax(spec[klo:khi]))
        a, b, c = spec[k - 1], spec[k], spec[k + 1]
        d = a - 2 * b + c
        delta = 0.5 * (a - c) / d if abs(d) > 1e-12 else 0.0
        out.append(((k + delta) * binhz, float(spec[k])))
    return out


# ── robust fundamental via power-weighted spectral centroid ─────────────────
# Over a long window the centroid of the fundamental band averages the cimbalom's
# multi-string detuned cluster to its true center, while staying correct for a
# clean inharmonic single peak (water gong / tongue drum). NSDF/autocorrelation
# is NOT used: inharmonic modal spectra have no true period, so it mislocates f0.
def measure_f0(x, sr, f0_pred):
    seg = x[int(0.05 * sr):int(1.55 * sr)]
    if len(seg) < int(0.2 * sr):
        seg = x[int(0.02 * sr):]
    if len(seg) < 256:
        return None
    seg = seg * np.hanning(len(seg))
    N = 1 << int(math.ceil(math.log2(len(seg))))
    spec = np.abs(np.fft.rfft(seg, N))
    binhz = sr / N
    klo = max(1, int(f0_pred * 0.94 / binhz))
    khi = min(len(spec) - 1, int(f0_pred * 1.06 / binhz) + 1)
    if khi <= klo:
        return None
    power = spec[klo:khi] ** 2
    if power.sum() <= 0.0:
        return None
    freqs = np.arange(klo, khi) * binhz
    return float((freqs * power).sum() / power.sum())


# ── probe render via CLI ────────────────────────────────────────────────────
def render_probe(cli, eng, midi, outdir, sr=48000, vel=0.85, dur=2.0,
                  params_override=None, tag=""):
    spec = ENGINES[eng]
    # params_override (M1-1c, material scan): merged on top of the engine's
    # default params so callers only need to specify the one field (material)
    # they're varying; everything else stays the harness's standard probe.
    params = dict(spec["params"])
    if params_override:
        params.update(params_override)
    fn = f"probe_{eng}_{midi}_{int(round(vel * 100))}_{int(round(dur * 10))}{tag}"
    score = {
        "meta": {"title": fn, "id": fn},
        "global": {"bpm": 120, "sample_rate": sr, "master_volume": 1.0,
                   "effects": {"reverb": {"decay": 2, "wet": 0},
                               "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                               "distortion": {"type": "overdrive", "drive": 0,
                                              "instability": 0, "wet": 0}}},
        "events": [{"time": 0.0, "duration": dur, "engine": spec["engine"],
                    "note": str(midi), "velocity": vel,
                    "params": params}],
        "export": {"filename": fn, "format": "wav", "bit_depth": 16,
                   "normalize": False, "tail_silence_ms": 200},
    }
    sf = outdir / (fn + ".score.json")
    sf.write_text(json.dumps(score), encoding="utf-8")
    r = subprocess.run([str(cli), str(sf), "--output", str(outdir)],
                       capture_output=True, text=True)
    wav = outdir / (fn + ".wav")
    if r.returncode != 0 or not wav.exists():
        raise RuntimeError(f"render failed for {fn}: {r.stdout}\n{r.stderr}")
    return wav, sf


def find_cli():
    here = Path(__file__).resolve().parent.parent
    cands = list((here / "build").rglob("TsukiSynthCLI.exe"))
    cands += list((here / "build").rglob("tsukisynth-cli*"))
    cands += list((here / "build").rglob("TsukiSynthCLI"))
    cands = [c for c in cands if c.is_file()]
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)


# ── main ────────────────────────────────────────────────────────────────────
def cents(measured, predicted):
    return 1200.0 * math.log2(measured / predicted)


def run(cli, engines, notes, outdir):
    overall_ok = True
    for eng in engines:
        spec = ENGINES[eng]
        for midi in notes:
            f0 = midi_to_hz(midi)
            ratios = spec["ratios"](spec["npart"])
            pred = [f0 * r for r in ratios]
            wav, _ = render_probe(cli, eng, midi, outdir)
            sr, x = read_wav_mono(wav)
            meas = measure_partials(sr, x, pred)

            print(f"\n# {eng:11s} MIDI {midi}  (f0_expected = {f0:8.3f} Hz)"
                  f"{'  [inharmonic: high-partial stretch is expected]' if spec.get('inharmonic') else ''}")
            print(f"   {'n':>2} {'predicted':>11} {'measured':>11} {'err%':>7} {'rel_dB':>6}  note")
            fund_mag = meas[0][1] if meas[0] else 0.0
            f0_meas = measure_f0(x, sr, f0)
            probe_ok = True
            for i, (r, fp, m) in enumerate(zip(ratios, pred, meas), 1):
                if m is None:
                    print(f"   {i:>2} {fp:>11.3f} {'--':>11} {'--':>7} {'--':>6}  NOT FOUND")
                    if i == 1:
                        probe_ok = False
                    continue
                fmeas, mag = m
                rel_db = 20.0 * math.log10(mag / fund_mag) if (fund_mag > 0 and mag > 0) else -120.0
                if i == 1 and f0_meas:
                    fmeas = f0_meas    # centroid: robust to multi-string beating
                errp = (fmeas / fp - 1.0) * 100.0
                if i == 1:
                    c = cents(fmeas, fp)
                    ok = abs(c) <= F0_TOL_CENTS
                    tag = f"f0 {c:+.1f} cents [{'OK' if ok else 'FAIL'}]"
                    probe_ok = probe_ok and ok
                elif rel_db < -45.0:
                    tag = "weak (< -45 dB) - not assessed"
                elif spec.get("inharmonic"):
                    tag = f"stretch {errp:+.2f}%"
                else:
                    ok = abs(errp) <= spec["tol_pct"]
                    tag = f"[{'OK' if ok else 'FAIL'}]"
                    probe_ok = probe_ok and ok
                print(f"   {i:>2} {fp:>11.3f} {fmeas:>11.3f} {errp:>+7.2f} {rel_db:>+6.0f}  {tag}")
            print(f"   -> {'PASS' if probe_ok else 'FAIL'}")
            overall_ok = overall_ok and probe_ok
    return overall_ok


# ── M1-1b: multi-note range scan ────────────────────────────────────────────
def scan_engine_ranges(cli, engines, outdir, n=6):
    # Reuses run()'s exact f0+partial judgment (same tolerances, same printed
    # format) so a wide-range scan can never diverge from the 2-note default.
    print("\n" + "-" * 70)
    print(f"Note-range scan ({n} notes per engine, spanning each engine's "
          "declared valid range):")
    overall_ok = True
    for eng in engines:
        lo, hi = ENGINE_RANGES[eng]
        notes = scan_notes(lo, hi, n)
        print(f"\n### {eng}: valid range MIDI {lo}-{hi} -> probing {notes}")
        ok = run(cli, [eng], notes, outdir)
        if not ok:
            print(f"### {eng}: OUT OF TOLERANCE somewhere in {notes}. "
                  f"Do NOT widen tolerance — shrink the declared valid range "
                  f"(ENGINE_RANGES['{eng}']) or fix the model, per "
                  f"ROADMAP_PHYSICS.md §1g/§1.2.")
        overall_ok = overall_ok and ok
    return overall_ok


# ── M1-1c: material scan ────────────────────────────────────────────────────
# The 3 modal engines whose modal ratios are checked per-material. FM has no
# material param; piano/cimbalom share StringModel so cimbalom stands in for
# the string family here (roadmap 1c names "cimbalom / tongue_drum / water_gong").
MATERIAL_SCAN_ENGINES = ["cimbalom", "tongue_drum", "water_gong"]
MATERIAL_SCAN_MIDI = 60   # C4 — fixed probe note for the material sweep (1c)

# ROADMAP_PHYSICS.md §3 M1-1c: "UI 暴露的 9 種材質" (the 9 materials the UI
# exposes) — NOT all of data/materials.json (14 entries: the extra 5 —
# iron/nylon/bamboo/wood_birch/wood_oak — are in the physics DB and reachable
# from a hand-written score.json, but are not plugin AudioParameterChoice
# options). Source of truth: MaterialDB::getOrderedKeys() in
# src/physics/MaterialDB.h, duplicated here (Python can't include the C++
# header) — keep these two lists in sync if that array ever changes.
UI_MATERIAL_KEYS = ["steel", "copper", "bronze", "aluminum", "brass",
                     "wood_spruce", "wood_maple", "glass", "rubber"]


def load_material_keys(materials_path=None):
    """Returns the 9 UI-exposed material keys (§3 M1-1c), after validating
    each one actually exists in data/materials.json (catches drift between
    MaterialDB::getOrderedKeys() and the JSON data file)."""
    if materials_path is None:
        materials_path = Path(__file__).resolve().parent.parent / "data" / "materials.json"
    data = json.loads(Path(materials_path).read_text(encoding="utf-8"))
    available = data["materials"]
    missing = [k for k in UI_MATERIAL_KEYS if k not in available]
    if missing:
        raise RuntimeError(
            f"UI_MATERIAL_KEYS references materials missing from "
            f"{materials_path}: {missing}. MaterialDB::getOrderedKeys() and "
            f"materials.json have drifted apart — fix one or the other.")
    return list(UI_MATERIAL_KEYS)


def scan_materials(cli, outdir, engines=None, materials_path=None):
    # engines: restrict to this subset of MATERIAL_SCAN_ENGINES (honors --engines
    # filtering, same as scan_engine_ranges/judge_velocity); default = all 3.
    scan_engines = [e for e in MATERIAL_SCAN_ENGINES if engines is None or e in engines]
    materials = load_material_keys(materials_path)
    print("\n" + "-" * 70)
    print(f"Material scan (MIDI {MATERIAL_SCAN_MIDI}, f0 + partials, "
          f"{len(materials)} materials x {len(scan_engines)} modal engines):")
    overall_ok = True
    midi = MATERIAL_SCAN_MIDI
    f0 = midi_to_hz(midi)
    for eng in scan_engines:
        spec = ENGINES[eng]
        ratios = spec["ratios"](spec["npart"])
        pred = [f0 * r for r in ratios]
        for mat in materials:
            wav, _ = render_probe(cli, eng, midi, outdir,
                                   params_override={"material": mat},
                                   tag=f"_mat_{mat}")
            sr, x = read_wav_mono(wav)
            meas = measure_partials(sr, x, pred)
            f0_meas = measure_f0(x, sr, f0)

            probe_ok = True
            m0 = meas[0]
            fmeas0 = f0_meas if f0_meas else (m0[0] if m0 else None)
            if fmeas0 is None:
                print(f"   {eng:11} material={mat:12} f0 NOT FOUND  expected={f0:.3f} Hz -> FAIL")
                probe_ok = False
            else:
                c = cents(fmeas0, f0)
                ok = abs(c) <= F0_TOL_CENTS
                probe_ok = probe_ok and ok
                status = "OK" if ok else "FAIL"
                print(f"   {eng:11} material={mat:12} f0 measured={fmeas0:9.3f} Hz "
                      f"expected={f0:9.3f} Hz  {c:+6.1f} cents (tol {F0_TOL_CENTS}) [{status}]")

            fund_mag = m0[1] if m0 else 0.0
            for i, (fp, m) in enumerate(zip(pred, meas), 1):
                if i == 1 or m is None:
                    continue
                fmeas, mag = m
                rel_db = 20.0 * math.log10(mag / fund_mag) if (fund_mag > 0 and mag > 0) else -120.0
                if rel_db < -45.0:
                    continue   # weak partial - not assessed (same rule as run())
                errp = (fmeas / fp - 1.0) * 100.0
                if spec.get("inharmonic"):
                    continue   # inharmonic stretch is reported, not judged (same rule as run())
                ok = abs(errp) <= spec["tol_pct"]
                if not ok:
                    print(f"      partial {i}: measured={fmeas:.3f} Hz expected={fp:.3f} Hz "
                          f"err={errp:+.2f}% (tol +/-{spec['tol_pct']}%) -> FAIL")
                probe_ok = probe_ok and ok

            if not probe_ok:
                print(f"      -> {eng}/{mat} FAILED. Do NOT widen tolerance — "
                      f"record this material as unsupported for {eng} or fix the model, "
                      f"per ROADMAP_PHYSICS.md §1g.")
            overall_ok = overall_ok and probe_ok
    return overall_ok


# ── M1-1d: velocity linearity judgment ──────────────────────────────────────
# velocity x2 -> +6.0 +/- 1.0 dB RMS is the amplitude-proportional-to-force
# physical law (registered in ROADMAP_PHYSICS.md §6: "velocity x2 電平").
# 48/96 (MIDI-velocity-style units, out of 127) give an exact x2 ratio.
VELOCITY_LO = 48 / 127.0
VELOCITY_HI = 96 / 127.0
VELOCITY_DB_TARGET = 6.0    # physical law: amplitude ~ force -> +6 dB per doubling
VELOCITY_DB_TOL = 1.0       # +/-1.0 dB judgment window (ROADMAP_PHYSICS.md §6)
VELOCITY_EXEMPT_ENGINES = {"fm"}   # FM index also rises with velocity -> not a pure amplitude law


def judge_velocity(cli, engines, notes, outdir):
    # Converts the --levels display (report_levels) into a PASS/FAIL/EXEMPT
    # judgment per ROADMAP_PHYSICS.md M1-1d, without touching --levels itself.
    print("\n" + "-" * 70)
    print(f"Velocity linearity judgment (vel {VELOCITY_LO:.3f} -> {VELOCITY_HI:.3f}, "
          f"expect +{VELOCITY_DB_TARGET:.1f} +/-{VELOCITY_DB_TOL:.1f} dB RMS):")
    print(f"   {'engine':11} {'MIDI':>4} {'rms_lo':>8} {'rms_hi':>8} {'delta_dB':>9}  verdict")
    overall_ok = True
    for eng in engines:
        exempt = eng in VELOCITY_EXEMPT_ENGINES
        for midi in notes:
            lo, _ = render_probe(cli, eng, midi, outdir, vel=VELOCITY_LO)
            hi, _ = render_probe(cli, eng, midi, outdir, vel=VELOCITY_HI)
            _, rlo = measure_levels(*read_wav_mono(lo))
            _, rhi = measure_levels(*read_wav_mono(hi))
            delta = rhi - rlo
            if exempt:
                verdict = "EXEMPT (FM index also scales with velocity)"
            else:
                ok = abs(delta - VELOCITY_DB_TARGET) <= VELOCITY_DB_TOL
                verdict = "PASS" if ok else "FAIL"
                if not ok:
                    print(f"      measured delta={delta:+.2f} dB, expected "
                          f"{VELOCITY_DB_TARGET:+.1f} +/-{VELOCITY_DB_TOL:.1f} dB "
                          f"-> FAIL. Do NOT widen tolerance; record and investigate "
                          f"the engine's velocity->amplitude law per ROADMAP_PHYSICS.md §1g.")
                overall_ok = overall_ok and ok
            print(f"   {eng:11} {midi:>4} {rlo:>8.1f} {rhi:>8.1f} {delta:>+9.1f}  {verdict}")
    return overall_ok


# ── M2-2d: partial-amplitude judgment ───────────────────────────────────────
# ROADMAP_PHYSICS.md §6: "Partial 振幅誤差 | 無（未驗證） | ±3.0 dB（M2）" — the
# theoretical prediction is built ENTIRELY from the model's own --dump-modes
# output (freq/amp/decay per mode, per active string/voice, plus each mode's
# body_mag = the exact |dry+BodyResonance(dry)| transfer magnitude read from
# the model's own live BiquadFilter/BodyResonance state — see
# BodyResonance::magnitudeAt() / BiquadFilter::responseAt() in
# src/dsp/BodyResonance.h / src/dsp/BiquadFilter.h). NONE of this is a
# re-derivation calibrated from rendered audio (that would be circular per
# ROADMAP_PHYSICS.md M2 "不算完成": "振幅預測值是反過來從渲染結果抄的") — it is
# a windowed-synthesis of the model's own documented linear signal chain
# (modal decay + multi-string beating + the body-resonance filter's transfer
# function), run through the IDENTICAL measurement pipeline
# (measure_partials()) used on the real CLI-rendered WAV. See
# reports/gate_outputs/amps_rootcause_analysis.md for the root-cause
# investigation this closes: --dump-modes used to report the raw pre-mix
# ModalResonator amplitude (string 0 only, no BodyResonance), which is not
# what getNextSample() actually renders.
AMPS_SCAN_ENGINES = ["cimbalom", "tongue_drum", "water_gong", "water_gong_free", "piano"]
AMPS_NPART = 5              # "first 5 partials" per ROADMAP_PHYSICS.md M2-2d
AMPS_DB_TOL = 3.0           # ±3.0 dB, registered in §6 — AI must NOT change this
AMPS_WEAK_DB = -45.0        # same "not assessed" floor as run()/scan_materials()
AMPS_PROBE_SR = 48000       # must match render_probe()'s default sr= (judge_amps
AMPS_PROBE_DUR = 2.0        # and dur=) so the theory synthesis and the real render
                             # are windowed/measured over an identical duration.


def dump_modes_partials(cli, score_path):
    """Runs --dump-modes on a single-event probe score and returns that
    event's partials list (each {"freq", "amp", "decay", "body_mag"},
    ascending frequency, string 0 only -- see ScoreRenderer::dumpModes).
    Mirrors model_fundamental_decay()'s subprocess pattern; returns None on
    any failure so callers can report NOT FOUND instead of crashing the whole
    scan. Kept for any external/legacy caller; judge_amps() below uses
    dump_modes_event() to also get the multi-string "strings" array."""
    event = dump_modes_event(cli, score_path)
    return event["partials"] if event else None


def dump_modes_event(cli, score_path):
    """Runs --dump-modes and returns the full first-event dict: "partials"
    (string 0's modes, kept for back-compat) plus "strings" (every active
    string's/voice's modes, each already detuned/gain-scaled exactly as the
    C++ model's noteOn() computed them -- see CimbalomVoice::
    getAllStringModes() / ChromaticVoice::getModes()). Every mode also carries
    "body_mag". Returns None on any failure."""
    r = subprocess.run([str(cli), "--dump-modes", str(score_path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        events = json.loads(r.stdout)["events"]
        return events[0] if events else None
    except Exception:
        return None


def synth_theory_signal(strings, sr, duration):
    """THEORY-ONLY windowed synthesis (no rendered-audio input, per the
    no-circularity rule above): sums every active string's/voice's modal
    partials as decaying sinusoids
        x(t) = sum_s sum_i  amp_i,s * body_mag_i,s * exp(-t/decay_i,s)
                             * sin(2*pi*freq_i,s*t)
    `body_mag` folds in the model's own BodyResonance transfer magnitude at
    that mode's frequency (steady-state/quasi-static approximation -- valid
    because the body filter's own settling time, a few ms for its Q=1.4-1.8
    resonances, is short next to the decay times of every partial this gate
    judges; see BodyResonance::totalResponse()'s doc-comment). Summing
    multiple strings' slightly-detuned copies reproduces the real multi-string
    beating pattern using the model's own per-string frequency/gain math
    (CimbalomVoice::noteOn), not a Python re-derivation of the detuning
    formula. All modes (not just the first AMPS_NPART) are included since
    higher partials still land inside neighbouring partials' +/-6% search
    windows used by measure_partials()."""
    n = int(round(duration * sr))
    t = np.arange(n) / sr
    x = np.zeros(n)
    for voice_modes in strings:
        for m in voice_modes:
            amp = m["amp"] * m.get("body_mag", 1.0)
            decay = m["decay"] if m["decay"] > 1e-9 else 1.0e9
            x += amp * np.exp(-t / decay) * np.sin(2.0 * np.pi * m["freq"] * t)
    return x


def judge_amps(cli, engine, midi_note, outdir):
    """M2-2d: renders one probe, compares the first AMPS_NPART partials'
    measured relative amplitude (dB re fundamental) against a THEORY-ONLY
    windowed-synthesis prediction (see synth_theory_signal()) built from
    --dump-modes' full multi-string mode list + body_mag, run through the
    same measure_partials() pipeline used on the real render. Partial 1 (the
    fundamental) is the 0 dB reference for both sides by construction and is
    not itself judged; partials 2..AMPS_NPART are judged within
    +/-AMPS_DB_TOL dB. Returns (probe_ok, rows) where rows is a list of
    per-partial dicts for the caller to print/tally."""
    # tag="_amps": run_full() shares one outdir across scan_engine_ranges()
    # and scan_amps(), and both probe MIDI 60 with the harness's default
    # vel/dur -- without a distinguishing tag their probe filenames collide
    # (CLI refuses to overwrite an existing render), so scan_amps' probe
    # needs its own filename even though it renders identical parameters.
    wav, sf = render_probe(cli, engine, midi_note, outdir, tag="_amps",
                            sr=AMPS_PROBE_SR, dur=AMPS_PROBE_DUR)
    event = dump_modes_event(cli, sf)
    rows = []
    if not event or not event.get("partials"):
        return False, rows
    partials = event["partials"][:AMPS_NPART]
    pred_freqs = [p["freq"] for p in partials]

    # Theory-only prediction: windowed-synthesis of the FULL multi-string
    # mode list (not just the first AMPS_NPART partials of string 0 -- see
    # synth_theory_signal()'s docstring), measured with the identical
    # measure_partials() pipeline used on the real render below. Zero
    # rendered-audio input anywhere in this block.
    strings = event.get("strings") or [event["partials"]]
    synth = synth_theory_signal(strings, AMPS_PROBE_SR, AMPS_PROBE_DUR)
    synth_meas = measure_partials(AMPS_PROBE_SR, synth, pred_freqs)
    synth_fund_mag = synth_meas[0][1] if synth_meas[0] else 0.0

    sr, x = read_wav_mono(wav)
    meas = measure_partials(sr, x, pred_freqs)
    fund_mag = meas[0][1] if meas[0] else 0.0
    f0_meas = measure_f0(x, sr, pred_freqs[0])

    probe_ok = True
    for i, (p, m) in enumerate(zip(partials, meas), 1):
        sm = synth_meas[i - 1]
        pred_db = (20.0 * math.log10(sm[1] / synth_fund_mag)
                   if (synth_fund_mag > 0 and sm and sm[1] > 0) else -120.0)
        if m is None:
            rows.append(dict(n=i, freq=p["freq"], pred_db=pred_db,
                              meas_db=None, err_db=None, verdict="NOT FOUND"))
            if i == 1:
                probe_ok = False   # fundamental must be found (same as run())
            continue
        fmeas, mag = m
        if i == 1 and f0_meas:
            fmeas = f0_meas   # centroid: robust to multi-string beating (same as run())
        meas_db = 20.0 * math.log10(mag / fund_mag) if (fund_mag > 0 and mag > 0) else -120.0
        if i == 1:
            rows.append(dict(n=i, freq=fmeas, pred_db=0.0, meas_db=0.0,
                              err_db=0.0, verdict="ref (0 dB)"))
            continue
        if meas_db < AMPS_WEAK_DB:
            rows.append(dict(n=i, freq=fmeas, pred_db=pred_db, meas_db=meas_db,
                              err_db=None, verdict="weak (< -45 dB) - not assessed"))
            continue
        err_db = meas_db - pred_db
        ok = abs(err_db) <= AMPS_DB_TOL
        probe_ok = probe_ok and ok
        rows.append(dict(n=i, freq=fmeas, pred_db=pred_db, meas_db=meas_db,
                          err_db=err_db, verdict="PASS" if ok else "FAIL"))
    return probe_ok, rows


def scan_amps(cli, outdir, engines=None, midi_note=60):
    """M2-2d: runs judge_amps() for every modal engine (FM excluded -- non-
    physical synthesis, per module docstring / ROADMAP_PHYSICS.md §0) at
    MIDI 60 (middle C), printing the same per-partial table style as run()."""
    scan_engines = [e for e in AMPS_SCAN_ENGINES if engines is None or e in engines]
    print("\n" + "-" * 70)
    print(f"Partial-amplitude judgment (MIDI {midi_note}, first {AMPS_NPART} partials, "
          f"rel-dB vs --dump-modes theory, tol +/-{AMPS_DB_TOL} dB):")
    overall_ok = True
    for eng in scan_engines:
        probe_ok, rows = judge_amps(cli, eng, midi_note, outdir)
        f0 = midi_to_hz(midi_note)
        print(f"\n# {eng:11s} MIDI {midi_note}  (f0_expected = {f0:8.3f} Hz)")
        print(f"   {'n':>2} {'freq':>11} {'pred_dB':>8} {'meas_dB':>8} {'err_dB':>7}  verdict")
        if not rows:
            print("   -- NOT FOUND (--dump-modes returned no partials) -> FAIL")
            probe_ok = False
        for r in rows:
            meas_s = f"{r['meas_db']:>+8.2f}" if r['meas_db'] is not None else f"{'--':>8}"
            err_s = f"{r['err_db']:>+7.2f}" if r['err_db'] is not None else f"{'--':>7}"
            print(f"   {r['n']:>2} {r['freq']:>11.3f} {r['pred_db']:>+8.2f} {meas_s} {err_s}  {r['verdict']}")
        if not probe_ok:
            print(f"   -> {eng} FAILED. Do NOT widen the +/-{AMPS_DB_TOL} dB tolerance "
                  f"(ROADMAP_PHYSICS.md §6) — investigate the impulse-excitation model "
                  f"or record the discrepancy per §1g.")
        print(f"   -> {'PASS' if probe_ok else 'FAIL'}")
        overall_ok = overall_ok and probe_ok
    return overall_ok


# ── M1-1e: --full mode ──────────────────────────────────────────────────────
def run_full(cli, engines, outdir, skip_amps=False):
    """Runs the complete M1 verification breadth: multi-note range scan (1b)
    for every engine, material scan (1c) for the 3 modal engines, and the
    velocity-linearity judgment (1d) for every engine. Also runs the M2-2d
    partial-amplitude judgment for every modal engine, so --full covers M1+M2.
    Exit-code-affecting; every sub-check must pass for --full to report
    success.

    skip_amps=True restricts --full to its M1 scope (1b+1c+1d), for CI while
    M2-2d remediation is still in progress. This is NOT a tolerance change and
    NOT a silent gate-shrink: the M2 GATE (--amps) is unaffected and still
    FAILs honestly, CI runs a separate always-visible non-blocking --amps step,
    and M2 stays "In progress" in ROADMAP_PHYSICS.md until 2d passes for real.
    Scope decision approved by 月月 2026-07-09 (delegated via Fable) — see
    TODO.md CI-coupling entry."""
    print("=" * 70)
    print("--full: M1 verification breadth (range scan + material scan + velocity)"
          + (" [--skip-amps: M1 scope only, M2-2d amplitude judgment NOT run]"
             if skip_amps else " + M2 amplitude judgment"))
    print("=" * 70)

    range_ok = scan_engine_ranges(cli, engines, outdir, n=6)

    material_engines = [e for e in engines if e in MATERIAL_SCAN_ENGINES]
    material_ok = True
    if material_engines:
        material_ok = scan_materials(cli, outdir, engines=material_engines)
    else:
        print("\n(material scan skipped: none of the requested --engines are "
              f"in {MATERIAL_SCAN_ENGINES})")

    # Velocity judgment uses one representative note per engine (MIDI 60, or
    # the engine's declared range midpoint if 60 falls outside it) — the
    # physical law being checked (amplitude ~ velocity) is note-independent.
    vel_notes = []
    for eng in engines:
        lo, hi = ENGINE_RANGES[eng]
        vel_notes.append(60 if lo <= 60 <= hi else (lo + hi) // 2)
    # judge_velocity takes one shared note list; since engines may need
    # different representative notes, run it once per engine with its own note.
    velocity_ok = True
    for eng, midi in zip(engines, vel_notes):
        velocity_ok = judge_velocity(cli, [eng], [midi], outdir) and velocity_ok

    amps_engines = [] if skip_amps else [e for e in engines if e in AMPS_SCAN_ENGINES]
    amps_ok = True
    if amps_engines:
        amps_ok = scan_amps(cli, outdir, engines=amps_engines)
    elif skip_amps:
        print("\n(amplitude judgment SKIPPED by --skip-amps: M1-scope run; the M2 "
              "GATE `--amps` is unaffected and must still pass separately)")
    else:
        print("\n(amplitude judgment skipped: none of the requested --engines are "
              f"in {AMPS_SCAN_ENGINES})")

    print("\n" + "=" * 70)
    print("--full summary:")
    print(f"   1b note-range scan   : {'PASS' if range_ok else 'FAIL'}")
    print(f"   1c material scan     : {'PASS' if material_ok else 'FAIL'}")
    print(f"   1d velocity judgment : {'PASS' if velocity_ok else 'FAIL'}")
    print(f"   2d amplitude judgment: "
          f"{'SKIPPED (--skip-amps)' if skip_amps else ('PASS' if amps_ok else 'FAIL')}")

    return range_ok and material_ok and velocity_ok and amps_ok


def measure_levels(sr, x):
    seg = x[:int(1.5 * sr)] if len(x) > int(1.5 * sr) else x
    if len(seg) == 0:
        return (-120.0, -120.0)
    to_db = lambda v: 20.0 * math.log10(v) if v > 1e-9 else -120.0
    peak = float(np.max(np.abs(seg)))
    rms = float(np.sqrt(np.mean(seg * seg)))
    return (to_db(peak), to_db(rms))


def report_levels(cli, engines, notes, outdir):
    # Quantifies the ad-hoc per-engine output gains (cimbalom x0.15 /
    # chromatic x0.2 / fm x1.0) ear-free, and checks the physical law
    # amplitude is proportional to velocity (doubling velocity ~ +6 dB RMS).
    print("Per-engine output level @ matched note (vel 0.85):")
    print(f"   {'engine':11} {'MIDI':>4} {'peak dBFS':>10} {'rms dBFS':>9} "
          f"{'velx2->dB':>10}")
    for eng in engines:
        for midi in notes:
            lo, _ = render_probe(cli, eng, midi, outdir, vel=0.425)
            hi, _ = render_probe(cli, eng, midi, outdir, vel=0.85)
            _, rlo = measure_levels(*read_wav_mono(lo))
            phi, rhi = measure_levels(*read_wav_mono(hi))
            print(f"   {eng:11} {midi:>4} {phi:>10.1f} {rhi:>9.1f} "
                  f"{rhi - rlo:>+9.1f}")
    print("\n(+6 dB = amplitude scales linearly with velocity = physical;")
    print(" FM expected >+6 dB because higher velocity also raises FM index.)")
    return True


def model_fundamental_decay(cli, score_path):
    # Ground-truth decay from the C++ model itself (--dump-modes), avoiding any
    # Python re-derivation drift (the model's decayTime uses the natural,
    # pre-MIDI-tuning frequency, which a formula on the tuned f0 would get wrong).
    r = subprocess.run([str(cli), "--dump-modes", str(score_path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)["events"][0]["partials"][0]["decay"]
    except Exception:
        return None


def measure_t60(sr, x, f0):
    # Hilbert envelope of the fundamental band, log-slope fit extrapolated to -60 dB.
    try:
        from scipy.signal import butter, sosfiltfilt, hilbert
    except Exception:
        return None
    nyq = sr / 2.0
    lo, hi = max(20.0, f0 * 0.8) / nyq, min(nyq * 0.99, f0 * 1.2) / nyq
    if not (0.0 < lo < hi < 1.0):
        return None
    band = sosfiltfilt(butter(4, [lo, hi], btype="band", output="sos"), x)
    env = np.abs(hilbert(band))
    seg = env[int(np.argmax(env)):]
    if len(seg) < int(0.15 * sr):
        return None
    logenv = 20.0 * np.log10(np.maximum(seg, 1e-9) / max(seg[0], 1e-9))
    t = np.arange(len(seg)) / sr
    # clean decay region, before any note-off accelerated damping (~1.5 s)
    mask = (logenv <= -3.0) & (logenv >= -28.0) & (t < 1.5)
    if mask.sum() < 20:
        return None
    slope = np.polyfit(t[mask], logenv[mask], 1)[0]   # dB/s (negative)
    return (-60.0 / slope) if slope < -1e-3 else None


def report_t60(cli, engines, notes, outdir):
    print("Modal decay T60 - measured (audio) vs model ground truth (--dump-modes):")
    print(f"   {'engine':11} {'MIDI':>4} {'model':>8} {'meas':>8} {'ratio':>6}")
    all_ok = True
    for eng in engines:
        if eng == "fm":
            continue   # FM decay is ADSR, not modal damping
        for midi in notes:
            f0 = midi_to_hz(midi)
            wav, sf = render_probe(cli, eng, midi, outdir, dur=3.0)
            sr, x = read_wav_mono(wav)
            pred, meas = model_fundamental_decay(cli, sf), measure_t60(sr, x, f0)
            ps = f"{pred:7.2f}s" if pred else "   --  "
            ms = f"{meas:7.2f}s" if meas else "   --  "
            if pred and meas:
                ratio = meas / pred
                rs = f"{ratio:5.2f}"
                lo, hi = T60_RATIO_TOLERANCE
                if ratio < lo or ratio > hi:
                    rs += " << FAIL"
                    all_ok = False
            else:
                rs = "  --  "
            print(f"   {eng:11} {midi:>4} {ps:>8} {ms:>8} {rs:>6}")
    print("\n(model = fundamental decayTime straight from the C++ model;")
    print(" measured = Hilbert-envelope log-slope of the fundamental band.)")
    return all_ok


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Verify rendered audio vs physics model.")
    ap.add_argument("--cli", default=None, help="path to TsukiSynthCLI executable")
    ap.add_argument("--engines", nargs="+", default=list(ENGINES.keys()),
                    choices=list(ENGINES.keys()))
    ap.add_argument("--notes", nargs="+", type=int, default=[60, 69],
                    help="MIDI notes (default C4 A4)")
    ap.add_argument("--keep", action="store_true", help="keep temp renders")
    ap.add_argument("--levels", action="store_true",
                    help="report per-engine output levels instead of partials")
    ap.add_argument("--t60", action="store_true",
                    help="report modal decay times vs the damping model")
    ap.add_argument("--amps", action="store_true",
                    help="M2-2d: judge first-5-partial relative amplitude (dB "
                         "re fundamental) vs --dump-modes theory, all modal "
                         "engines (FM excluded) at MIDI 60; tol +/-3.0 dB "
                         "(ROADMAP_PHYSICS.md §6)")
    ap.add_argument("--full", action="store_true",
                    help="M1 verification breadth: note-range scan (all engines) "
                         "+ material scan (modal engines) + velocity judgment "
                         "(all engines) + M2-2d amplitude judgment (modal "
                         "engines); exit 0 only if every sub-check passes")
    ap.add_argument("--skip-amps", action="store_true",
                    help="with --full: restrict to M1 scope (1b+1c+1d), omit the "
                         "M2-2d amplitude judgment. For CI while M2 remediation "
                         "is in progress (月月-approved 2026-07-09); the M2 GATE "
                         "`--amps` is unaffected. No effect without --full.")
    args = ap.parse_args()

    cli = Path(args.cli) if args.cli else find_cli()
    if not cli or not cli.exists():
        print("ERROR: TsukiSynthCLI not found. Build it first "
              "(cmake --build build --target TsukiSynthCLI) or pass --cli.",
              file=sys.stderr)
        return 2
    print(f"CLI: {cli}")

    if not args.full:
        print("=" * 70)
        print("TsukiSynth physics verification — measured spectrum vs theory")
        print("=" * 70)

    def do(od):
        if args.full:
            return run_full(cli, args.engines, od, skip_amps=args.skip_amps)
        if args.levels:
            return report_levels(cli, args.engines, args.notes, od)
        if args.t60:
            return report_t60(cli, args.engines, args.notes, od)
        if args.amps:
            return scan_amps(cli, od, engines=args.engines)
        return run(cli, args.engines, args.notes, od)

    if args.keep:
        outdir = Path(__file__).resolve().parent.parent / "build" / "physics_verify"
        outdir.mkdir(parents=True, exist_ok=True)
        ok = do(outdir)
    else:
        with tempfile.TemporaryDirectory() as td:
            ok = do(Path(td))

    print("\n" + "=" * 70)
    if args.full or args.amps:
        print("RESULT:", "ALL WITHIN TOLERANCE" if ok else "SOME CHECKS FAILED")
    else:
        print("RESULT:", "ALL WITHIN TOLERANCE" if ok else "SOME PROBES OUT OF TOLERANCE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
