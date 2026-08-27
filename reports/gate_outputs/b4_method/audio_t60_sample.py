#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B4 Rule 10 report -- audio-level decay-slope (T60) sampling, before vs after.

Complements t60_f0_felt_events.py (model-level, exact): here the T60 claim
is checked on the RENDERED AUDIO of the affected pieces, using the intact
before renders (Temp\\b4_render_before, SHA256-verified against
affected_render_before.csv) and the after renders (Temp\\b4_render_after),
with the SAME windows, SAME band, SAME fit on both sides.

Method (same family as tools/physics_verify.py measure_t60: narrowband
+/-3% Butterworth bandpass around the note's model fundamental, Hilbert
envelope, least-squares log-slope):
  * 4th-order Butterworth bandpass, +/-3% of the sampled note's
    center-string model f0 (from t60_f0_felt_events_after.csv -- proven
    identical before/after), filtfilt (zero-phase).
  * Window = the note's own sustain (note start + settle margin -> note-off)
    or the piece tail (last-event end -> EOF), fixed per sample below.
  * Fit region inside the window: from t_start+settle until the envelope
    first drops 45 dB below the region peak (or the window ends) --
    keeps the fit off the noise floor / appended tail silence.
  * T60 = -60 / slope(dB/s). Also reported: fitted span (dB) and window,
    because a mixture band (other events / reverb / delay in-band) makes
    the number a WINDOWED DECAY SLOPE, not a pure modal T60 -- it is
    still a valid before/after change detector because both sides use
    identical windows on deterministic renders.

Sampled notes (felt events; band-purity notes inline):
  physical_piano  C4/E4/G4 sustain windows are single-note pure (no other
                  event has a partial inside the +/-3% band); C5 sustain
                  band also contains C4's partial 2 (~523.5 Hz), which by
                  window start has decayed >80 dB -- negligible.
  ai_radiance_m3  last felt event F4 (t=21.30): window from its onset
                  +0.15 s to last-event end; the piece's reverb
                  (decay 4.6, wet .38) and delay (wet .11) are in-band ->
                  mixture slope, identical both sides.
  akashic_action  D5 string sustain; the companion plate event is also at
                  D5 -> mixture of string+plate decay (plate unchanged).
  ocean_action    D1 band tail [0.9, 6.0]: the felt string (T60 1.12 s)
                  dies within ~1.5 s; the band is then dominated by the
                  UNCHANGED plate event (model T60 56.6 s at 36.7 Hz), so
                  the span over this window is small by physics; reported
                  with its span for honesty.

Usage (from the repo root):
    python reports/gate_outputs/b4_method/audio_t60_sample.py
Output: reports/gate_outputs/b4_method/audio_t60_sample.csv (+ stdout table)
"""
import csv
import os
import sys
import wave

import numpy as np
from scipy.signal import butter, hilbert, resample_poly, sosfiltfilt

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BEFORE_DIR = r"C:\Users\admin\AppData\Local\Temp\b4_render_before"
AFTER_DIR = r"C:\Users\admin\AppData\Local\Temp\b4_render_after"

# piece dir, wav name, sample label, band f0 (model center-string, Hz),
# window t0, t1 (s), settle (s)
SAMPLES = [
    ("physical_piano", "physical_piano.wav", "C4 sustain", 261.6260, 0.00, 1.00, 0.15),
    ("physical_piano", "physical_piano.wav", "E4 sustain", 329.6280, 1.00, 2.00, 0.15),
    ("physical_piano", "physical_piano.wav", "G4 sustain", 391.9950, 2.00, 3.00, 0.15),
    ("physical_piano", "physical_piano.wav", "C5 sustain", 523.2510, 3.00, 5.00, 0.15),
    ("physical_piano", "physical_piano.wav", "C5 tail",    523.2510, 5.00, 7.575, 0.05),
    ("ai_radiance_m3", "Original_AI_Radiance_Movement3.wav",
                                             "F4 (last felt) decay", 349.2280, 21.30, 22.835, 0.15),
    ("ai_radiance_m3", "Original_AI_Radiance_Movement3.wav",
                                             "F4 band piece tail", 349.2280, 22.835, 32.222, 0.05),
    ("akashic_action_001", "Foley_Soft_OneShot_D5.wav",
                                             "D5 sustain (string+plate)", 587.3300, 0.00, 1.00, 0.15),
    ("akashic_action_001", "Foley_Soft_OneShot_D5.wav",
                                             "D5 tail", 587.3300, 1.00, 3.248, 0.05),
    ("ocean_action_001", "Impact_Dark_OneShot_D1.wav",
                                             "D1 band tail (plate-dominated)", 36.7080, 0.90, 6.00, 0.20),
]

FIT_DEPTH_DB = 45.0


def read_wav_mono(path):
    with wave.open(path, "rb") as w:
        sr = w.getframerate()
        n = w.getnframes()
        sw = w.getsampwidth()
        ch = w.getnchannels()
        raw = w.readframes(n)
    if sw == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        as_int = (b[:, 0].astype(np.int32)
                  | (b[:, 1].astype(np.int32) << 8)
                  | (b[:, 2].astype(np.int32) << 16))
        as_int[as_int >= (1 << 23)] -= (1 << 24)
        data = as_int.astype(np.float64) / (1 << 23)
    elif sw == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / (2 ** 31)
    else:
        raise ValueError("unsupported sampwidth %d" % sw)
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    return sr, data


def band_t60(sr, x, f0, t0, t1, settle):
    # Decimate so the +/-3% band is not vanishingly narrow in normalized
    # frequency (numerical stability); SOS + sosfiltfilt for the same
    # reason. Decimation factor keeps f0 below ~fs/8 after decimation.
    dec = 1
    while sr / (dec * 2) > f0 * 8 and dec < 64:
        dec *= 2
    if dec > 1:
        x = resample_poly(x, 1, dec)
        sr = sr / dec
    lo, hi = f0 * 0.97, f0 * 1.03
    sos = butter(4, [lo / (sr / 2.0), hi / (sr / 2.0)],
                 btype="band", output="sos")
    y = sosfiltfilt(sos, x)
    seg = y[int(t0 * sr):int(t1 * sr)]
    env = np.abs(hilbert(seg))
    env_db = 20.0 * np.log10(np.maximum(env, 1e-12))
    t = np.arange(len(seg)) / sr
    m = t >= settle
    t_fit, e_fit = t[m], env_db[m]
    if not len(t_fit):
        return float("nan"), 0.0, 0.0
    peak = float(e_fit.max())
    below = np.nonzero(e_fit < peak - FIT_DEPTH_DB)[0]
    end = below[0] if len(below) else len(e_fit)
    end = max(end, 16)
    t_fit, e_fit = t_fit[:end], e_fit[:end]
    A = np.vstack([t_fit, np.ones_like(t_fit)]).T
    slope, _ = np.linalg.lstsq(A, e_fit, rcond=None)[0]
    span = float(e_fit[0] - e_fit[-1])
    if slope >= 0:
        return float("inf"), span, t_fit[-1] - t_fit[0]
    return -60.0 / slope, span, t_fit[-1] - t_fit[0]


def main():
    rows = []
    print("%-20s %-28s %9s | %10s %10s %7s | %6s %6s"
          % ("piece", "sample", "band(Hz)", "T60_before", "T60_after",
             "delta%", "spanB", "spanA"))
    for piece, wavname, label, f0, t0, t1, settle in SAMPLES:
        vals = {}
        for tag, root in (("before", BEFORE_DIR), ("after", AFTER_DIR)):
            sr, x = read_wav_mono(os.path.join(root, piece, wavname))
            vals[tag] = band_t60(sr, x, f0, t0, t1, settle)
        tb, sb, db_ = vals["before"]
        ta, sa, da_ = vals["after"]
        delta = ((ta - tb) / tb * 100.0) if (np.isfinite(tb) and tb > 0
                                             and np.isfinite(ta)) else float("nan")
        rows.append([piece, label, "%.4f" % f0, "%.2f" % t0, "%.2f" % t1,
                     "%.4f" % tb, "%.4f" % ta,
                     "%.3f" % delta if np.isfinite(delta) else "n/a",
                     "%.1f" % sb, "%.1f" % sa,
                     "%.2f" % db_, "%.2f" % da_])
        print("%-20s %-28s %9.3f | %10.4f %10.4f %6s%% | %5.1f %6.1f"
              % (piece, label, f0, tb, ta,
                 ("%.3f" % delta) if np.isfinite(delta) else "n/a", sb, sa))

    out_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "audio_t60_sample.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["piece", "sample", "band_f0_hz", "win_t0_s", "win_t1_s",
                    "t60_before_s", "t60_after_s", "delta_pct",
                    "fit_span_before_db", "fit_span_after_db",
                    "fit_len_before_s", "fit_len_after_s"])
        w.writerows(rows)
    print("wrote", out_csv)


if __name__ == "__main__":
    sys.exit(main())
