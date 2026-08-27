#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B4 Rule 10 report -- tau_c old-vs-new mirror recalculation (narrative aid).

Mirror transcriptions (double precision; C++ uses float, differences are
<0.01% and invisible at table precision) of:

  OLD Felt path  src/physics/HammerImpulse.h (HEAD, unchanged functions):
      tauCForNote(1, v, m) = kTauCFelt
                             * clamp((0.5/clamp(v,.02,1))^0.2, 0.8, 1.2)
                             * clamp(2^(-(m-69)*0.32/12), 0.4, 2.6)
  NEW Felt path  pianoHammerTauC(m, v) (B4, same header):
      g(m,v)   = (mass(m)/K(m))^(1/(alpha(m)+1)) * v^(2/(alpha(m)+1)-1)
      tau_c    = clamp(kTauCFelt * g(m,v)/g(69,0.5), 0.3ms, 8ms)
      alpha    : piecewise-linear in MIDI over anchors C2/C4/C7, flat outside
      log10(K) : same interpolation; mass: linear over C1..C8 anchors, flat
  Force spectrum  forceSpectrumMagnitude():
      H(w) = |cos(w*tau/2)| / |1 - (w*tau/pi)^2|,  removable-singularity
      guard pi/4 at |1-x^2| < 1e-4.

SELF-VALIDATION before anything is tabulated (script aborts on failure):
  v1  new tau_c(69, 0.5) == 2.000 ms exactly (anchor identity);
  v2  finite-ratio velocity exponents at MIDI 36/60/96 == -0.394/-0.429/
      -0.500 (+/-1e-3) -- the same identity tests/physics_models_repro.cpp
      testPianoHammerContactSolver() asserts against the C++;
  v3  the mirror's center-string spectral-shaping ratio
          20*log10(H(2*pi*f0, tau(0.756)) / H(2*pi*f0, tau(0.378)))
      is compared against the MEASURED center-string fundamental amp
      ratio 20*log10(p1_amp(v96)/p1_amp(v48)) from the anchor CSVs
      (anchor_partials_before.csv with tau_old, anchor_partials_after.csv
      with tau_new -- the dumped relative amps carry the H(tau(v)) shaping
      but not the linear force~velocity factor, so the ratio isolates
      exactly the term the mirror computes). Asserted <= 0.2 dB at C2/C4
      in both eras; C7 rows are printed for transparency but not asserted
      -- there f0 sits on force-spectrum SIDELOBES where H is extremely
      steep in tau, so the last-digit rounding of the published anchors
      visibly moves the single-string number (the honest sensitivity
      caveat, not an error; the authoritative C7 sensitivity numbers in
      the report are the gate's own recorded predicted/measured deltas).
  The gate-level 3-string band-aggregate predictions (+6.25/+7.79/+19.12
  dB, b4_f3_redefine_alpha_recheck.txt) are also printed next to the
  mirror's single-string figures for context, unasserted.

Output: tauc_curve_mirror.csv + stdout tables.
Usage:  python reports/gate_outputs/b4_method/tauc_curve_mirror.py
"""
import csv
import math
import os
import sys

K_TAU_C_FELT = 0.0020
ALPHA_MIDI = [36, 60, 96]
ALPHA_VAL = [2.3, 2.5, 3.0]
K_VAL = [4.0e8, 4.5e9, 1.0e12]
MASS_MIDI = [24, 36, 48, 60, 72, 84, 96, 108]
MASS_VAL = [0.012, 0.011, 0.010, 0.009, 0.008, 0.007, 0.006, 0.005]
TAU_MIN, TAU_MAX = 0.0003, 0.0080


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def interp_flat(anchors, values, m):
    if m <= anchors[0]:
        return values[0]
    if m >= anchors[-1]:
        return values[-1]
    for i in range(len(anchors) - 1):
        if anchors[i] <= m < anchors[i + 1]:
            t = (m - anchors[i]) / (anchors[i + 1] - anchors[i])
            return values[i] + (values[i + 1] - values[i]) * t
    return values[-1]


def alpha_of(m):
    return interp_flat(ALPHA_MIDI, ALPHA_VAL, m)


def K_of(m):
    logk = interp_flat(ALPHA_MIDI, [math.log10(k) for k in K_VAL], m)
    return 10.0 ** logk


def mass_of(m):
    return interp_flat(MASS_MIDI, MASS_VAL, m)


def g_fn(m, v):
    a = alpha_of(m)
    inv = 1.0 / (a + 1.0)
    return (mass_of(m) / K_of(m)) ** inv * v ** (2.0 * inv - 1.0)


def tau_new(m, v):
    v = clamp(v, 0.02, 1.0)
    return clamp(K_TAU_C_FELT * g_fn(m, v) / g_fn(69, 0.5), TAU_MIN, TAU_MAX)


def tau_old(m, v):
    speed = clamp(v, 0.02, 1.0)
    hertz = clamp((0.5 / speed) ** 0.2, 0.8, 1.2)
    keytrack = clamp(2.0 ** (-(m - 69) * 0.32 / 12.0), 0.4, 2.6)
    return K_TAU_C_FELT * hertz * keytrack


def H(f, tau):
    x = 2.0 * math.pi * f * tau / math.pi
    denom = 1.0 - x * x
    if abs(denom) < 1e-4:
        return math.pi / 4.0
    return abs(math.cos(math.pi * x / 2.0) / denom)


def db(x):
    return 20.0 * math.log10(x)


LAW_DB = 20.0 * math.log10(2.0)
V_LO, V_HI = 48.0 / 127.0, 96.0 / 127.0


def predicted_delta(m, f0, tau_fn):
    return LAW_DB + db(H(f0, tau_fn(m, V_HI)) / H(f0, tau_fn(m, V_LO)))


def read_anchor_csv(path):
    out = {}
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[(int(row["midi"]), int(row["vel_midi"]))] = (
                float(row["center_string_f0_hz"]), float(row["p1_amp"]))
    return out


def main():
    # v1
    t = tau_new(69, 0.5)
    assert abs(t - K_TAU_C_FELT) < 1e-15, t
    # v2
    for m, want in ((36, -0.394), (60, -0.429), (96, -0.500)):
        got = (math.log(tau_new(m, 0.9) / tau_new(m, 0.45))
               / math.log(0.9 / 0.45))
        assert abs(got - want) < 1e-3, (m, got, want)
    # v3: mirror H-shaping vs measured center-string p1_amp ratios
    here = os.path.dirname(os.path.abspath(__file__))
    eras = (("before", tau_old,
             read_anchor_csv(os.path.join(here, "anchor_partials_before.csv"))),
            ("after", tau_new,
             read_anchor_csv(os.path.join(here, "anchor_partials_after.csv"))))
    print("v3 center-string spectral shaping 48->96 (dB): mirror H-ratio vs "
          "measured p1_amp ratio (anchor CSVs):")
    for era, tau_fn, table in eras:
        for m in (36, 60, 96):
            f0, a_lo = table[(m, 48)]
            _, a_hi = table[(m, 96)]
            meas = db(a_hi / a_lo)
            mir = db(H(f0, tau_fn(m, V_HI)) / H(f0, tau_fn(m, V_LO)))
            note = ""
            if m != 96:
                assert abs(mir - meas) <= 0.2, (era, m, mir, meas)
            else:
                note = "  (C7 sidelobe region: not asserted, see docstring)"
            print("   %-6s MIDI %3d f0=%9.3f  mirror %+7.2f  measured %+7.2f"
                  "  diff %+0.3f%s" % (era, m, f0, mir, meas, mir - meas, note))
    print("v1/v2/v3 OK -- mirror faithful to the C++ identities and the "
          "measured C2/C4 shaping\n")
    print("context (unasserted): gate 3-string band-aggregate predicted "
          "deltas after B4 = +6.25 / +7.79 / +19.12 dB at C2/C4/C7 "
          "(b4_f3_redefine_alpha_recheck.txt); mirror single-string figures "
          "printed below.\n")

    def nominal(m):
        return 440.0 * 2.0 ** ((m - 69) / 12.0)

    notes = [("C1", 24), ("D1", 26), ("C2", 36), ("C4", 60), ("A4", 69),
             ("D5", 74), ("C7", 96), ("C8", 108)]
    rows = []
    print("tau_c curve, v=0.5 (anchor velocity):")
    print("   note MIDI  alpha        K(N*m^-a)  mass(kg)   old_tau  new_tau  new/old  vel_exp_new")
    for name, m in notes:
        to, tn = tau_old(m, 0.5), tau_new(m, 0.5)
        a = alpha_of(m)
        vexp = 2.0 / (a + 1.0) - 1.0
        rows.append([name, m, "%.4f" % a, "%.4g" % K_of(m),
                     "%.6f" % mass_of(m),
                     "%.6f" % to, "%.6f" % tn, "%.4f" % (tn / to),
                     "%.4f" % vexp])
        print("   %-4s %4d  %.3f  %14.4g  %.6f  %6.3f ms %6.3f ms  %.3f   %+.3f (old -0.2)"
              % (name, m, a, K_of(m), mass_of(m), to * 1e3, tn * 1e3,
                 tn / to, vexp))

    print("\nfundamental-band velocity response 48/127 -> 96/127 (dB), "
          "old vs new (f0 = 12-TET nominal):")
    print("   note MIDI  pred_old  pred_new   (law 6.02; excess = "
          "contact-time spectral shaping at f0)")
    rows2 = []
    for name, m in notes:
        f0 = nominal(m)
        po = predicted_delta(m, f0, tau_old)
        pn = predicted_delta(m, f0, tau_new)
        rows2.append([name, m, "%.4f" % f0, "%.3f" % po, "%.3f" % pn])
        print("   %-4s %4d   %+7.2f   %+7.2f" % (name, m, po, pn))

    print("\nper-piece amplitude shift of changed felt fundamentals "
          "(20*log10[H(f0,tau_new)/H(f0,tau_old)] at the event velocity):")
    events = [("ocean D1 v=0.85", 26, 36.708, 0.85),
              ("akashic D5 v=0.35", 74, 587.330, 0.35),
              ("piano C4 v=0.80", 60, 261.626, 0.80),
              ("piano C5 v=0.85", 72, 523.251, 0.85),
              ("m3 A4 v=0.46", 69, 440.000, 0.46),
              ("m3 F4 v=0.42", 65, 349.228, 0.42)]
    rows3 = []
    for label, m, f0, v in events:
        dh = db(H(f0, tau_new(m, v)) / H(f0, tau_old(m, v)))
        rows3.append([label, m, "%.3f" % f0, "%.2f" % v,
                      "%.6f" % tau_old(m, v), "%.6f" % tau_new(m, v),
                      "%+.2f" % dh])
        print("   %-20s tau %6.3f -> %6.3f ms   f0 shift %+6.2f dB"
              % (label, tau_old(m, v) * 1e3, tau_new(m, v) * 1e3, dh))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "tauc_curve_mirror.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["# tau_c curve at v=0.5"])
        w.writerow(["note", "midi", "alpha", "K", "mass_kg",
                    "tau_old_s", "tau_new_s", "ratio", "vel_exp_new"])
        w.writerows(rows)
        w.writerow(["# predicted f0-band velocity delta 48->96 (dB)"])
        w.writerow(["note", "midi", "f0_hz", "pred_old_db", "pred_new_db"])
        w.writerows(rows2)
        w.writerow(["# felt fundamental amplitude shift at event velocity"])
        w.writerow(["event", "midi", "f0_hz", "vel",
                    "tau_old_s", "tau_new_s", "f0_shift_db"])
        w.writerows(rows3)
    print("\nwrote", out)


if __name__ == "__main__":
    sys.exit(main())
