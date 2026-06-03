"""
Tuner pitch-detection self-audit.
Replicates src/analyzer/TunerView.h detectPitch() in Python and feeds
controlled test signals to identify which step causes the reported bugs.
"""
import math

# -- Algorithm replica (mirrors TunerView.h::detectPitch) --------------

def detect_pitch_verbose(data, sample_rate, label=""):
    n = len(data)
    min_lag = max(2, int(sample_rate / 4000.0))
    max_lag = min(int(sample_rate / 20.0), n * 3 // 4)
    if max_lag <= min_lag:
        return None

    # NSDF from lag 2
    nsdf = [0.0] * (max_lag + 1)
    for tau in range(2, max_lag + 1):
        acf = 0.0
        norm = 0.0
        N = n - tau
        for j in range(N):
            x = data[j]
            y = data[j + tau]
            acf += x * y
            norm += x * x + y * y
        nsdf[tau] = (2.0 * acf / norm) if norm > 1e-10 else 0.0

    # Zero-lag lobe end
    zero_lag_end = 2
    for tau in range(2, max_lag + 1):
        if nsdf[tau] <= 0.0:
            zero_lag_end = tau
            break

    search_start = max(min_lag, zero_lag_end)

    # Peaks in positive lobes after zero-lag lobe
    peaks = []
    in_pos = False
    local_max = -1.0
    local_lag = 0
    for tau in range(search_start, max_lag + 1):
        v = nsdf[tau]
        if v > 0.0:
            if not in_pos:
                in_pos = True
                local_max = -1.0
            if v > local_max:
                local_max = v
                local_lag = tau
        else:
            if in_pos:
                peaks.append((local_lag, local_max))
                in_pos = False
    if in_pos:
        peaks.append((local_lag, local_max))

    if not peaks:
        return None

    global_max = max(v for _, v in peaks)
    if global_max < 0.35:
        return None

    threshold = global_max * 0.80
    best_lag = 0
    confidence = 0.0
    selected_index = -1
    for i, (lag, v) in enumerate(peaks):
        if v >= threshold:
            best_lag = lag
            confidence = v
            selected_index = i
            break

    if best_lag == 0:
        return None

    # Parabolic interpolation
    refined = float(best_lag)
    if 2 < best_lag < max_lag:
        a = nsdf[best_lag - 1]
        b = nsdf[best_lag]
        c = nsdf[best_lag + 1]
        d = a - 2.0 * b + c
        if abs(d) > 1e-10:
            refined = best_lag + 0.5 * (a - c) / d

    freq = sample_rate / refined

    return {
        "label": label,
        "sample_rate": sample_rate,
        "num_samples": n,
        "min_lag": min_lag,
        "max_lag": max_lag,
        "zero_lag_end": zero_lag_end,
        "search_start": search_start,
        "peaks": peaks,
        "global_max": global_max,
        "threshold": threshold,
        "best_lag": best_lag,
        "selected_peak_index": selected_index,
        "refined_lag": refined,
        "confidence": confidence,
        "frequency": freq,
    }


def freq_to_note(freq):
    if freq <= 0:
        return ("?", 0.0, -1)
    midi = 69.0 + 12.0 * math.log2(freq / 440.0)
    nearest = round(midi)
    cents = (midi - nearest) * 100.0
    names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    name = names[nearest % 12] + str(nearest // 12 - 1)
    return (name, cents, nearest)


# -- Test signal generators --------------------------------------------

def pure_sine(freq, sr, dur_s=0.18):
    n = int(sr * dur_s)
    return [0.5 * math.sin(2 * math.pi * freq * i / sr) for i in range(n)]


def harmonic_stack(freq, sr, harmonics, dur_s=0.18):
    """harmonics = list of (multiple, amplitude)"""
    n = int(sr * dur_s)
    out = [0.0] * n
    for mult, amp in harmonics:
        f = freq * mult
        for i in range(n):
            out[i] += amp * math.sin(2 * math.pi * f * i / sr)
    # normalize
    peak = max(abs(x) for x in out) or 1.0
    return [0.5 * x / peak for x in out]


def fm_signal(carrier, modulator, index, sr, dur_s=0.18, decay=True):
    """Two-op FM with optional exp-decay on index"""
    n = int(sr * dur_s)
    out = [0.0] * n
    for i in range(n):
        t = i / sr
        env = math.exp(-3.0 * t) if decay else 1.0
        I = index * env
        mod = math.sin(2 * math.pi * modulator * t)
        out[i] = 0.5 * math.sin(2 * math.pi * carrier * t + I * mod)
    return out


def inharmonic_modes(f0, sr, mode_ratios, mode_amps, decays_s, dur_s=0.18):
    """Simulate beam/plate modal output: f0 * ratios with exp decay"""
    n = int(sr * dur_s)
    out = [0.0] * n
    for r, a, dec in zip(mode_ratios, mode_amps, decays_s):
        f = f0 * r
        for i in range(n):
            t = i / sr
            env = math.exp(-t / max(dec, 1e-3))
            out[i] += a * env * math.sin(2 * math.pi * f * t)
    peak = max(abs(x) for x in out) or 1.0
    return [0.5 * x / peak for x in out]


# -- Print helpers ----------------------------------------------------─

def report(test_label, expected_freq, result):
    print(f"\n-- {test_label}")
    if result is None:
        print(f"  expected {expected_freq:.2f} Hz -> DETECTOR RETURNED NONE")
        return
    f = result["frequency"]
    note, cents, midi = freq_to_note(f)
    exp_note, _, exp_midi = freq_to_note(expected_freq)
    octave_err = (midi - exp_midi) / 12.0 if exp_midi >= 0 else 0
    err_tag = ""
    if midi != exp_midi:
        if (midi - exp_midi) % 12 == 0:
            err_tag = f"  [FAIL] OCTAVE ERROR ({(midi - exp_midi)//12:+d} oct)"
        else:
            err_tag = f"  [FAIL] WRONG NOTE (expected {exp_note} / midi {exp_midi})"
    print(f"  expected: {expected_freq:.2f} Hz ({exp_note})")
    print(f"  sample_rate: {result['sample_rate']}, n_samples: {result['num_samples']}")
    print(f"  min_lag={result['min_lag']}, max_lag={result['max_lag']}, "
          f"zero_lag_end={result['zero_lag_end']}, search_start={result['search_start']}")
    print(f"  peaks ({len(result['peaks'])}): " +
          ", ".join(f"({l},{v:.3f})" for l, v in result["peaks"][:8]) +
          ("..." if len(result["peaks"]) > 8 else ""))
    print(f"  global_max={result['global_max']:.3f}, "
          f"threshold (0.80x)={result['threshold']:.3f}")
    print(f"  selected peak idx={result['selected_peak_index']} -> "
          f"lag={result['best_lag']}, val/conf={result['confidence']:.3f}")
    print(f"  refined_lag={result['refined_lag']:.3f} -> "
          f"freq={f:.2f} Hz -> note={note} ({cents:+.1f}c){err_tag}")

    # expected lag at this sample rate
    exp_lag = result['sample_rate'] / expected_freq
    print(f"  expected_lag~{exp_lag:.1f}, "
          f"selected_lag={result['best_lag']}, "
          f"ratio={result['best_lag']/exp_lag:.3f}")


# -- Test plan --------------------------------------------------------─

def main():
    print("=" * 78)
    print("TUNER PITCH-DETECTION AUDIT")
    print("Algorithm: NSDF, threshold 0.80xglobal_max, no octave correction")
    print("=" * 78)

    # 1) Pure sines at 44.1k
    sr = 44100
    for name, f in [("C4", 261.63), ("A4", 440.0), ("C5", 523.25), ("C3", 130.81)]:
        sig = pure_sine(f, sr)
        report(f"PURE SINE {name} @ {sr}Hz", f, detect_pitch_verbose(sig, sr))

    # 2) Sample rate variations
    for sr in [48000, 96000]:
        for name, f in [("A4", 440.0), ("C5", 523.25)]:
            sig = pure_sine(f, sr)
            report(f"PURE SINE {name} @ {sr}Hz", f, detect_pitch_verbose(sig, sr))

    # 3) FM Piano simulation — strong 2x harmonic from FM
    sr = 44100
    print("\n" + "=" * 78)
    print("FM PIANO SIMULATIONS (rich harmonics)")
    print("=" * 78)
    for name, f in [("C4", 261.63), ("C#4", 277.18), ("D4", 293.66), ("D#4", 311.13)]:
        # carrier=f, modulator=2f, index=4 — typical bell-ish FM
        sig = fm_signal(f, f, 4.0, sr)
        report(f"FM Piano {name} (carrier=mod=f, I=4)", f,
               detect_pitch_verbose(sig, sr))

    # FM with mod ratio 2:1 (E.Piano tine-ish)
    for name, f in [("C4", 261.63)]:
        sig = fm_signal(f, 2 * f, 4.5, sr)
        report(f"FM Piano {name} (carrier=f, mod=2f, I=4.5)", f,
               detect_pitch_verbose(sig, sr))

    # 4) Cimbalom — harmonic stack with strong 2f (string overtone)
    print("\n" + "=" * 78)
    print("CIMBALOM SIMULATIONS (harmonic with strong 2nd partial)")
    print("=" * 78)
    for name, f in [("C4", 261.63), ("A4", 440.0)]:
        # 1f weaker than 2f scenario
        h_weak1 = [(1, 0.5), (2, 1.0), (3, 0.6), (4, 0.4), (5, 0.25)]
        sig = harmonic_stack(f, sr, h_weak1)
        report(f"Cimbalom {name} (1f=0.5, 2f=1.0, 3f=0.6, 4f=0.4)", f,
               detect_pitch_verbose(sig, sr))

    for name, f in [("C4", 261.63), ("A4", 440.0)]:
        # Realistic balance
        h_norm = [(1, 1.0), (2, 0.7), (3, 0.5), (4, 0.35), (5, 0.25)]
        sig = harmonic_stack(f, sr, h_norm)
        report(f"Cimbalom {name} (1f=1.0, 2f=0.7, 3f=0.5)", f,
               detect_pitch_verbose(sig, sr))

    # 5) Chromatic — beam mode ratios (Euler-Bernoulli)
    print("\n" + "=" * 78)
    print("CHROMATIC SIMULATIONS (inharmonic beam/plate modes)")
    print("=" * 78)
    # Tongue drum (beam): mode frequencies follow 1, 6.27, 17.55, 34.39 (clamped-free)
    # ours is more like 1, 2.76, 5.40, 8.93 (free-free)
    beam_ratios = [1.0, 2.756, 5.404, 8.933, 13.344]
    beam_amps   = [1.0, 0.55, 0.30, 0.15, 0.08]
    beam_decays = [1.2, 0.8, 0.5, 0.3, 0.2]
    for name, f in [("C4", 261.63)]:
        sig = inharmonic_modes(f, sr, beam_ratios, beam_amps, beam_decays)
        report(f"Chromatic tongue {name} (free-free beam modes)", f,
               detect_pitch_verbose(sig, sr))

    # Plate modes (water gong): 1, 1.730, 2.328, 2.892, 3.439
    plate_ratios = [1.0, 1.730, 2.328, 2.892, 3.439, 3.987]
    plate_amps   = [1.0, 0.7, 0.5, 0.4, 0.3, 0.2]
    plate_decays = [2.0, 1.5, 1.2, 1.0, 0.8, 0.6]
    for name, f in [("C4", 261.63)]:
        sig = inharmonic_modes(f, sr, plate_ratios, plate_amps, plate_decays)
        report(f"Chromatic plate {name} (Kirchhoff plate modes)", f,
               detect_pitch_verbose(sig, sr))

    # 6) Decay tail — same fundamental but lower amplitude, simulates note end
    print("\n" + "=" * 78)
    print("DECAY-TAIL TEST (low RMS)")
    print("=" * 78)
    sig = pure_sine(261.63, 44100)
    # scale down to simulate decay
    quiet = [x * 0.04 for x in sig]
    rms = math.sqrt(sum(x * x for x in quiet) / len(quiet))
    print(f"  quiet sig RMS = {rms:.4f} (gate is 0.03)")
    report("Quiet C4 sine (sim. note decay)", 261.63,
           detect_pitch_verbose(quiet, 44100))

if __name__ == "__main__":
    main()
