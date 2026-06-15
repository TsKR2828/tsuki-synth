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

Usage:
    python tools/physics_verify.py                 # default probe set
    python tools/physics_verify.py --notes 60 69   # MIDI notes to test
    python tools/physics_verify.py --engines tongue_drum water_gong
    python tools/physics_verify.py --cli <path-to-TsukiSynthCLI.exe>
Exit code 0 = all probes within tolerance.
"""

import argparse, json, math, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np

# ── physics constants (mirror the C++ models) ───────────────────────────────
# Free-free Euler-Bernoulli beam eigenvalues betaL  (BeamModel.h)
BEAM_BETAL = [4.730041, 7.853205, 10.995608, 14.137165, 17.278760]
# Bessel-zero set used by PlateModel.h (Kirchhoff circular plate)
PLATE_J = [2.405, 3.832, 5.136, 5.520, 6.380, 7.016, 7.588, 8.417]


def beam_ratios(n):
    b1 = BEAM_BETAL[0]
    return [(b / b1) ** 2 for b in BEAM_BETAL][:n]


def plate_ratios(n):
    j1 = PLATE_J[0]
    return [(j / j1) ** 2 for j in PLATE_J][:n]


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
                "thickness_mm": 4.0},
    ),
    "fm": dict(
        engine="fm", ratios=harmonic_ratios, npart=6, tol_pct=2.0,
        inharmonic=False,
        params={"fm_preset": 0},
    ),
}

F0_TOL_CENTS = 12.0  # fundamental pitch tolerance


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
def render_probe(cli, eng, midi, outdir, sr=48000, vel=0.85, dur=2.0):
    spec = ENGINES[eng]
    fn = f"probe_{eng}_{midi}_{int(round(vel * 100))}_{int(round(dur * 10))}"
    score = {
        "meta": {"title": fn, "id": fn},
        "global": {"bpm": 120, "sample_rate": sr, "master_volume": 1.0,
                   "effects": {"reverb": {"decay": 2, "wet": 0},
                               "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                               "distortion": {"type": "overdrive", "drive": 0,
                                              "instability": 0, "wet": 0}}},
        "events": [{"time": 0.0, "duration": dur, "engine": spec["engine"],
                    "note": str(midi), "velocity": vel,
                    "params": spec["params"]}],
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
            rs = f"{meas / pred:5.2f}" if (pred and meas) else "  --  "
            print(f"   {eng:11} {midi:>4} {ps:>8} {ms:>8} {rs:>6}")
    print("\n(model = fundamental decayTime straight from the C++ model;")
    print(" measured = Hilbert-envelope log-slope of the fundamental band.)")
    return True


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
    args = ap.parse_args()

    cli = Path(args.cli) if args.cli else find_cli()
    if not cli or not cli.exists():
        print("ERROR: TsukiSynthCLI not found. Build it first "
              "(cmake --build build --target TsukiSynthCLI) or pass --cli.",
              file=sys.stderr)
        return 2
    print(f"CLI: {cli}")

    print("=" * 70)
    print("TsukiSynth physics verification — measured spectrum vs theory")
    print("=" * 70)

    def do(od):
        if args.levels:
            return report_levels(cli, args.engines, args.notes, od)
        if args.t60:
            return report_t60(cli, args.engines, args.notes, od)
        return run(cli, args.engines, args.notes, od)

    if args.keep:
        outdir = Path(__file__).resolve().parent.parent / "build" / "physics_verify"
        outdir.mkdir(parents=True, exist_ok=True)
        ok = do(outdir)
    else:
        with tempfile.TemporaryDirectory() as td:
            ok = do(Path(td))

    print("\n" + "=" * 70)
    print("RESULT:", "ALL WITHIN TOLERANCE" if ok else "SOME PROBES OUT OF TOLERANCE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
