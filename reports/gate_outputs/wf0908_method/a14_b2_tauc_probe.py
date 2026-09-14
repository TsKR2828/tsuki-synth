#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""A14 B-2 Rule-10 before/after probe
(docs/workcards/WF0908_P2_a14_tauc_rule10.md §3 step 4).

Reuses the A14 R2 rerun method
(reports/decision_packets/A14_weak_fundamental_ruling.zh-TW.md 附錄 B):
an independent Python mirror of HammerImpulse::pianoHammerTauC() /
keytrackScale() / forceSpectrumMagnitude(), cross-checked against
--dump-modes output from the actual CLI binary (--cli), for a given
--variant {before, after} (which formula the mirror uses -- must match
what --cli was actually built from).

Produces, written to <outdir>/<label>_*.json|csv:
  1. G5/G6/D7 (and C4/A4 for context): tau_c / x=2*f1*tau_c / H(f1) (Python
     mirror, self-validated against --dump-modes center-string p1 amplitude)
     + measured 2nd-1st partial dB (from --dump-modes directly, no formula).
  2. noteComp reverse-solved from --dump-modes at v=0.5 (tauCRef == actual
     tau_c exactly at that velocity, so the dumped center-string p1
     amplitude equals sin(pi/8) * H(f1, tauCRef) * gain with no
     velocity-shape confound) for MIDI 61/64/67/69/79/91/98
     (ModalResonator::loudnessCompensationGain(), CimbalomEngine.h).
  3. MIDI 37->87 sweep peak/RMS (renders a14_sweep_piano.score.json from
     output/wf0907/R2/, reused verbatim -- same score works for either
     binary).

Usage (repo root; workdir must be OUTSIDE the repo):
  python reports/gate_outputs/wf0908_method/a14_b2_tauc_probe.py \
      --cli build-wf/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe \
      --label after --variant after \
      --workdir C:\temp\wf0908_p2_probe_after
"""
import argparse
import json
import math
import os
import subprocess
import sys
import wave

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUTDIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Python mirror of src/physics/HammerImpulse.h (both variants). Constants
# copied verbatim from that file; kept in exact lockstep with it.
# ---------------------------------------------------------------------------
K_TAU_C_FELT = 0.0020
PIANO_TAUC_MIN = 0.0003
PIANO_TAUC_MAX = 0.0080
K_ALPHA_ANCHOR = [36, 60, 96]
K_HAMMER_K = [4.0e8, 4.5e9, 1.0e12]
K_HAMMER_ALPHA = [2.3, 2.5, 3.0]
MASS_ANCHOR = [24, 36, 48, 60, 72, 84, 96, 108]
MASS_KG = [0.012, 0.011, 0.010, 0.009, 0.008, 0.007, 0.006, 0.005]


def interp_flat(anchor, values, midi):
    if midi <= anchor[0]:
        return values[0]
    if midi >= anchor[-1]:
        return values[-1]
    seg = 0
    while seg + 2 < len(anchor) and midi >= anchor[seg + 1]:
        seg += 1
    t = (midi - anchor[seg]) / float(anchor[seg + 1] - anchor[seg])
    return values[seg] + (values[seg + 1] - values[seg]) * t


def alpha_for(midi):
    return interp_flat(K_ALPHA_ANCHOR, K_HAMMER_ALPHA, midi)


def logk_for(midi):
    log10k = [math.log10(v) for v in K_HAMMER_K]
    return 10.0 ** interp_flat(K_ALPHA_ANCHOR, log10k, midi)


def mass_for(midi):
    return interp_flat(MASS_ANCHOR, MASS_KG, midi)


def piano_hammer_g(midi, v):
    a = alpha_for(midi)
    inv_ap1 = 1.0 / (a + 1.0)
    stiff = (mass_for(midi) / logk_for(midi)) ** inv_ap1
    return stiff * (v ** (2.0 * inv_ap1 - 1.0))


def keytrack_scale(midi):
    k = 0.32
    semis = midi - 69
    scale = 2.0 ** (-semis * k / 12.0)
    return min(max(scale, 0.4), 2.6)


def tauc_before(midi, v):
    """B4 (2026-08-27) formula: pitch shape implicit in g(note,v)/g(69,0.5)."""
    v = min(max(v, 0.02), 1.0)
    gg = piano_hammer_g(midi, v)
    gref = piano_hammer_g(69, 0.5)
    val = K_TAU_C_FELT * (gg / gref)
    return min(max(val, PIANO_TAUC_MIN), PIANO_TAUC_MAX)


def tauc_after(midi, v):
    """A14 B-2 formula: pitch shape = keytrackScale(), velocity shape =
    g(note,v)/g(note,0.5) (same note in numerator and denominator)."""
    v = min(max(v, 0.02), 1.0)
    gg = piano_hammer_g(midi, v)
    gref = piano_hammer_g(midi, 0.5)
    val = K_TAU_C_FELT * keytrack_scale(midi) * (gg / gref)
    return min(max(val, PIANO_TAUC_MIN), PIANO_TAUC_MAX)


def tauc(variant, midi, v):
    return tauc_after(midi, v) if variant == "after" else tauc_before(midi, v)


def force_spectrum_magnitude(omega_rad, tau_c):
    if tau_c <= 0.0 or not math.isfinite(omega_rad):
        return 1.0
    pi = math.pi
    x = omega_rad * tau_c / pi
    denom = 1.0 - x * x
    if abs(denom) < 1e-4:
        return pi * 0.25
    return abs(math.cos(omega_rad * tau_c * 0.5) / denom)


def midi_freq(midi):
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


# ---------------------------------------------------------------------------
# Score generation (piano engine, single note, effects off, no normalize --
# same diagnostic setup as output/wf0907/R2/gen_scores.py).
# ---------------------------------------------------------------------------
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def midi_to_name(m):
    return NAMES[m % 12] + str(m // 12 - 1)


def write_single_note_score(path, midi, velocity, dur=1.0):
    fid = os.path.basename(path)
    if fid.endswith(".score.json"):
        fid = fid[: -len(".score.json")]
    else:
        fid = os.path.splitext(fid)[0]
    d = {
        "$schema": "TsukiSynth Score v1",
        "meta": {"title": fid, "id": fid, "author": "wf0908-p2",
                  "description": "A14 B-2 before/after single-note probe"},
        "global": {"bpm": 120, "sample_rate": 48000, "master_volume": 1.0,
                   "effects": {
                       "reverb": {"decay": 1.0, "wet": 0.0},
                       "delay": {"time_ms": 0, "feedback": 0, "wet": 0},
                       "distortion": {"type": "overdrive", "drive": 0,
                                      "instability": 0, "wet": 0}}},
        "events": [{"time": 0.0, "duration": dur, "engine": "piano",
                    "note": midi_to_name(midi), "velocity": velocity,
                    "params": {"material": "steel", "diameter_mm": 1.0}}],
        "export": {"filename": fid, "format": "wav", "bit_depth": 24,
                   "normalize": False, "tail_silence_ms": 500},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return path


def dump_modes(cli, score_path):
    out = subprocess.run([cli, "--dump-modes", score_path],
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise RuntimeError("dump-modes failed for %s:\n%s\n%s"
                           % (score_path, out.stdout, out.stderr))
    return json.loads(out.stdout)


def center_string(event):
    strings = event["strings"]
    return strings[len(strings) // 2]


def read_wav_mono(path):
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        sw = w.getsampwidth()
        ch = w.getnchannels()
        raw = w.readframes(n)
    if sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        as_int = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8)
                  | (b[:, 2].astype(np.int32) << 16))
        as_int[as_int >= (1 << 23)] -= (1 << 24)
        data = as_int.astype(np.float64) / (1 << 23)
    elif sw == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / (2 ** 31)
    else:
        raise ValueError("unsupported sampwidth %d" % sw)
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    return sr, data


def db(x):
    return 20 * math.log10(max(x, 1e-20))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--variant", required=True, choices=["before", "after"])
    ap.add_argument("--workdir", required=True,
                    help="render output dir; must be OUTSIDE the repo")
    args = ap.parse_args()

    cli = os.path.abspath(args.cli)
    workdir = os.path.abspath(args.workdir)
    if (workdir + os.sep).startswith(REPO + os.sep):
        sys.exit("refusing to render inside the repo: " + workdir)
    os.makedirs(workdir, exist_ok=True)
    scoredir = os.path.join(REPO, "output", "wf0908", "P2")
    os.makedirs(scoredir, exist_ok=True)

    result = {"label": args.label, "variant": args.variant, "cli": cli}

    # ---- 1. G5/G6/D7 (+C4/A4 context): tau_c/x/H(f1) mirror + measured
    #         2nd-1st partial dB from --dump-modes (v=0.45, matching A14's
    #         own diagnostic velocity). ----
    tauc_rows = []
    for midi, name in [(60, "C4"), (69, "A4"), (79, "G5"), (91, "G6"), (98, "D7")]:
        score = write_single_note_score(
            os.path.join(scoredir, "b2_%s_v45.score.json" % name.lower()), midi, 0.45)
        dump = dump_modes(cli, score)
        ev = dump["events"][0]
        cs = center_string(ev)
        f1 = cs[0]["freq"]
        p1_amp_measured = cs[0]["amp"]
        p2_amp_measured = cs[1]["amp"]
        meas_p2_minus_p1_db = db(p2_amp_measured) - db(p1_amp_measured)

        tc = tauc(args.variant, midi, 0.45)
        x = 2.0 * f1 * tc
        Hf1 = force_spectrum_magnitude(2.0 * math.pi * f1, tc)
        Hf1_db = db(Hf1)
        # self-validation: predicted p1 amplitude ratio vs A4 anchor should
        # track the dumped p1 amplitude via H(f,tauc) alone (both share the
        # same sin(n*pi/8)*spectralTilt^0 factor at n=1, so the *ratio*
        # p1_amp(note)/p1_amp(A4) predicted by H alone should match the
        # dumped ratio up to noteComp/gain -- reported, not asserted, see
        # the accompanying report for the self-check).
        tauc_rows.append({
            "note": name, "midi": midi, "f1_hz": f1,
            "tau_c_ms": tc * 1000.0, "x": x,
            "H_f1_db": Hf1_db,
            "measured_p2_minus_p1_db": meas_p2_minus_p1_db,
            "measured_p1_amp": p1_amp_measured,
            "measured_p2_amp": p2_amp_measured,
        })
        print("[tauc] %-3s tau_c=%.4fms x=%.4f H(f1)=%.3fdB meas(p2-p1)=%.3fdB"
              % (name, tc * 1000.0, x, Hf1_db, meas_p2_minus_p1_db))

    # ---- 2. noteComp reverse-solve at v=0.5 (tauC(actual)==tauCRef exactly
    #         at v=0.5, so dumped p1 amp = sin(pi/8)*H(f1,tauCRef)*gain,
    #         gain = noteComp/sqrt(numStrings)). ----
    notecomp_rows = []
    for midi in [61, 64, 67, 69, 79, 91, 98]:
        score = write_single_note_score(
            os.path.join(scoredir, "b2_notecomp_midi%d_v50.score.json" % midi), midi, 0.5)
        dump = dump_modes(cli, score)
        ev = dump["events"][0]
        n_strings = len(ev["strings"])
        cs = center_string(ev)
        f1 = cs[0]["freq"]
        p1_amp = cs[0]["amp"]
        tc_ref = tauc(args.variant, midi, 0.5)
        Hf1 = force_spectrum_magnitude(2.0 * math.pi * f1, tc_ref)
        sin_strike = math.sin(math.pi * 0.125)  # n=1, strike_position=0.125
        gain = p1_amp / (sin_strike * Hf1)
        note_comp = gain * math.sqrt(n_strings)
        note_comp_clamped = min(max(note_comp, 0.25), 4.0)
        notecomp_rows.append({
            "midi": midi, "n_strings": n_strings, "f1_hz": f1,
            "p1_amp": p1_amp, "tau_c_ref_ms": tc_ref * 1000.0,
            "gain": gain, "note_comp_reverse_solved": note_comp,
            "saturated": abs(note_comp - 4.0) < 1e-3 or abs(note_comp - 0.25) < 1e-3,
        })
        print("[noteComp] MIDI %3d  nStrings=%d  gain=%.4f  noteComp~=%.4f%s"
              % (midi, n_strings, gain, note_comp,
                 "  (SATURATED @4.0)" if abs(note_comp - 4.0) < 1e-3 else ""))

    # ---- 3. MIDI 37->87 sweep peak/RMS (render existing sweep score). ----
    sweep_score = os.path.join(REPO, "output", "wf0907", "R2", "a14_sweep_piano.score.json")
    sweep_dir = os.path.join(workdir, "sweep")
    os.makedirs(sweep_dir, exist_ok=True)
    out = subprocess.run([cli, sweep_score, "--output", sweep_dir],
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise RuntimeError("sweep render failed:\n%s\n%s" % (out.stdout, out.stderr))
    wavs = [f for f in os.listdir(sweep_dir) if f.lower().endswith(".wav")]
    if len(wavs) != 1:
        raise RuntimeError("expected 1 wav, got %s" % wavs)
    sr, x = read_wav_mono(os.path.join(sweep_dir, wavs[0]))
    gap = 2.5
    sweep_rows = []
    for i, m in enumerate(range(37, 88)):
        s = int(i * gap * sr)
        e = int((i * gap + 2.4) * sr)
        seg = x[s:min(e, len(x))]
        if len(seg) == 0:
            continue
        pk = db(np.max(np.abs(seg)))
        rms = db(math.sqrt(np.mean(seg ** 2)))
        sweep_rows.append({"midi": m, "peak_dbfs": round(pk, 3), "rms_dbfs": round(rms, 3)})
    peak_span = sweep_rows[-1]["peak_dbfs"] - sweep_rows[0]["peak_dbfs"]
    rms_span = sweep_rows[-1]["rms_dbfs"] - sweep_rows[0]["rms_dbfs"]
    print("[sweep] MIDI37->87 peak span = %.3f dB, rms span = %.3f dB" % (peak_span, rms_span))

    result["tauc_table"] = tauc_rows
    result["notecomp_table"] = notecomp_rows
    result["sweep_rows"] = sweep_rows
    result["sweep_peak_span_db"] = peak_span
    result["sweep_rms_span_db"] = rms_span

    out_json = os.path.join(OUTDIR, "a14_b2_probe_%s.json" % args.label)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("wrote", out_json)


if __name__ == "__main__":
    sys.exit(main())
