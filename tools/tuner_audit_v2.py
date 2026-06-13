"""
Tuner audit v2 — regression coverage for Codex review.
Tests detectPitch() with logged bestLag / globalMax / threshold / confidence / note
across all engines × C4/A4/C5 × 44.1k/48k/96k.
"""
import math, sys

# ────────────────────────────────────────────────────────────
# Two candidate algorithms: current code (CUR) vs proposed fix (FIX)
# ────────────────────────────────────────────────────────────

def detect_pitch(data, sample_rate, algo="CUR"):
    """algo: 'CUR' = current code (0.80 threshold, no recovery)
              'FIX' = proposed (0.85 threshold + octave-down recovery + safer zero-lag)"""
    n = len(data)
    min_lag = max(2, int(sample_rate / 4000.0))
    max_lag = min(int(sample_rate / 20.0), n * 3 // 4)
    if max_lag <= min_lag:
        return None

    # NSDF
    nsdf = [0.0] * (max_lag + 1)
    for tau in range(2, max_lag + 1):
        acf = 0.0
        norm = 0.0
        N = n - tau
        for j in range(N):
            x = data[j]; y = data[j + tau]
            acf += x * y
            norm += x * x + y * y
        nsdf[tau] = (2.0 * acf / norm) if norm > 1e-10 else 0.0

    # Zero-lag lobe end
    zero_lag_end = None
    for tau in range(2, max_lag + 1):
        if nsdf[tau] <= 0.0:
            zero_lag_end = tau
            break

    if zero_lag_end is None:
        if algo == "FIX":
            # Safer fallback: scan for first local minimum (NSDF stops descending)
            # This bounds the zero-lag lobe even without a negative crossing
            for tau in range(3, max_lag):
                if nsdf[tau] < nsdf[tau-1] and nsdf[tau] < nsdf[tau+1]:
                    zero_lag_end = tau
                    break
            if zero_lag_end is None:
                zero_lag_end = max(min_lag, int(sample_rate / 2000.0))
        else:
            zero_lag_end = 2  # current code's unsafe fallback

    search_start = max(min_lag, zero_lag_end)

    # Collect positive-lobe peaks
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
    if algo == "CUR":
        if global_max < 0.35: return None
        threshold = global_max * 0.80
    else:  # FIX
        if global_max < 0.45: return None
        threshold = global_max * 0.85

    # First peak above threshold
    best_lag = 0
    best_val = 0.0
    sel_idx = -1
    for i, (lag, v) in enumerate(peaks):
        if v >= threshold:
            best_lag, best_val, sel_idx = lag, v, i
            break

    if best_lag == 0:
        return None

    swap_log = []
    if algo == "FIX":
        # Octave-down recovery: if a peak near 2*bestLag has comparable val,
        # prefer it (we may have picked T/2 when true fundamental is T)
        # Only do ONE swap to avoid drifting to very low freq for clean signals.
        for j in range(sel_idx + 1, len(peaks)):
            cand_lag, cand_val = peaks[j]
            ratio = cand_lag / best_lag
            if 1.85 <= ratio <= 2.15:  # near 2x
                if cand_val >= best_val * 0.90:
                    swap_log.append(f"OCTAVE-DOWN: {best_lag}({best_val:.3f}) -> {cand_lag}({cand_val:.3f})")
                    best_lag, best_val = cand_lag, cand_val
                break
            if ratio > 2.15:
                break

    confidence = best_val

    # Parabolic interpolation
    refined = float(best_lag)
    if 2 < best_lag < max_lag:
        a = nsdf[best_lag - 1]; b = nsdf[best_lag]; c = nsdf[best_lag + 1]
        d = a - 2.0 * b + c
        if abs(d) > 1e-10:
            refined = best_lag + 0.5 * (a - c) / d

    return {
        "sr": sample_rate, "n": n, "min_lag": min_lag, "max_lag": max_lag,
        "zero_lag_end": zero_lag_end, "search_start": search_start,
        "peaks": peaks, "global_max": global_max, "threshold": threshold,
        "best_lag": best_lag, "selected_peak_index": sel_idx,
        "refined_lag": refined, "confidence": confidence,
        "frequency": sample_rate / refined,
        "swap_log": swap_log,
    }


def freq_to_note(freq):
    if freq <= 0: return ("?", 0.0, -1)
    midi = 69.0 + 12.0 * math.log2(freq / 440.0)
    nearest = round(midi)
    cents = (midi - nearest) * 100.0
    names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    return (names[nearest % 12] + str(nearest // 12 - 1), cents, nearest)


# ────────────────────────────────────────────────────────────
# Signal generators
# ────────────────────────────────────────────────────────────

def pure_sine(f, sr, dur=0.18):
    n = int(sr * dur)
    return [0.5 * math.sin(2*math.pi*f*i/sr) for i in range(n)]


def fm_voice(midi_note, sr, type_, dur=0.18):
    """Replicate FMPianoVoice::processSingleSample structure (Piano default + hammer)."""
    freq = 440.0 * 2 ** ((midi_note - 69) / 12.0)
    n = int(sr * dur)
    out = [0.0] * n
    twopi = 2 * math.pi

    # Type 0 = Piano defaults
    atk_scales = [1.20, 1.60, 0.80, 1.40, 0.20, 0.40, 1.10, 0.90]
    bdy_scales = [0.55, 0.45, 0.70, 0.80, 0.80, 0.70, 0.80, 0.65]
    ham_amts   = [0.35, 0.25, 0.10, 0.05, 0.00, 0.00, 0.15, 0.10]

    vel = 1.0
    vel_idx = 0.45 + 0.80 * vel
    vel_atk = 0.50 + 1.10 * vel
    vel_ham = 0.20 + 1.20 * vel
    ratio = 1.0
    index_param = 4.5
    bright = 0.6
    peak_idx = index_param * vel_idx
    note_idx_scale = max(0.45, min(1.0, 1.2 - (midi_note - 48) * 0.012))
    peak_idx *= note_idx_scale

    atk_idx = peak_idx * atk_scales[type_] * vel_atk
    bdy_idx = peak_idx * bdy_scales[type_]
    note_scale = max(0.3, 1.0 + (midi_note - 60) * 0.025)
    atk_time = 0.045 / note_scale
    atk_coeff = math.exp(-6.9078 / (atk_time * sr))
    bdy_time = (1.0 - bright * 0.95) * 4.0 + 0.1
    bdy_time /= note_scale
    bdy_coeff = math.exp(-6.9078 / (bdy_time * sr))

    ham_level = ham_amts[type_] * vel_ham
    ham_time = 0.015 + 0.030 * (1.0 - vel)
    ham_coeff = math.exp(-6.9078 / (ham_time * sr))
    ham_hp_coeff = 1.0 - math.exp(-twopi * 1500.0 / sr)
    ham_lp_coeff = math.exp(-twopi * 6000.0 / sr)

    carrier_inc = freq * twopi / sr
    mod_inc = freq * ratio * twopi / sr
    c_ph = 0.0; m_ph = 0.0
    last_mod = 0.0
    fb_amt = 0.02 * 0.7
    ham_hp = 0.0; ham_lp = 0.0
    seed = midi_note * 17 + 1000
    cur_atk = atk_idx; cur_bdy = bdy_idx; cur_ham = ham_level

    # Simple AR envelope (skip ADSR detail — full attack 5ms)
    amp_env = 0.0
    atk_rate = 1.0 / (0.005 * sr)
    sustain = 0.0  # Piano sustain=0
    decay_t = 3.5  # Piano decay
    dec_rate = math.exp(-6.9078 / (decay_t * sr))

    for i in range(n):
        # AR env
        if amp_env < 1.0 and i * atk_rate < 1.0:
            amp_env = i * atk_rate
        else:
            amp_env = max(sustain, amp_env * dec_rate)

        # FM
        mod_sig = math.sin(m_ph + fb_amt * last_mod)
        last_mod = mod_sig
        idx = cur_atk + cur_bdy
        carrier_sig = math.sin(c_ph + idx * mod_sig)
        cur_atk *= atk_coeff
        cur_bdy *= bdy_coeff

        # Hammer noise (white through bandpass)
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        wn = (seed / 0x40000000) - 1.0
        ham_hp += ham_hp_coeff * (wn - ham_hp)
        wn_hp = wn - ham_hp
        ham_lp = ham_lp_coeff * ham_lp + (1 - ham_lp_coeff) * wn_hp
        ham_sig = ham_lp * cur_ham
        cur_ham *= ham_coeff

        sample = (carrier_sig + ham_sig) * 0.2 * amp_env
        out[i] = sample

        c_ph += carrier_inc
        m_ph += mod_inc

    # Normalize to avoid clip-induced artifacts
    peak = max(abs(x) for x in out) or 1.0
    return [0.6 * x / peak for x in out]


def fm_epiano_3stack(midi_note, sr, dur=0.18):
    """E.Piano 3-stack: A(1:1), B(14:1), C(3:1 +4c)."""
    freq = 440.0 * 2 ** ((midi_note - 69) / 12.0)
    n = int(sr * dur)
    out = [0.0] * n
    twopi = 2 * math.pi

    stacks = [
        # (ratio, peak_idx, level, decay_ms, fb, detune_cents)
        (1.0,  2.2, 0.75, 650.0, 0.02, 0.0),
        (14.0, 4.5, 0.30,  80.0, 0.00, 0.0),
        (3.0,  1.4, 0.18, 900.0, 0.00, 4.0),
    ]

    state = []
    for r, idx, lvl, dec_ms, fb, det in stacks:
        det_mul = 2 ** (det / 1200.0) if det != 0 else 1.0
        f = freq * det_mul
        state.append({
            "c_ph": 0.0, "m_ph": 0.0,
            "c_inc": f * twopi / sr,
            "m_inc": f * r * twopi / sr,
            "idx": idx, "decay": math.exp(-6.9078 / (dec_ms * 0.001 * sr)),
            "lvl": lvl, "fb": fb * 0.7,
            "last_mod": 0.0,
        })

    amp_env = 0.0
    atk_rate = 1.0 / (0.005 * sr)
    sustain = 0.3  # E.Piano sustain
    decay_t = 1.2
    dec_rate = math.exp(-6.9078 / (decay_t * sr))

    for i in range(n):
        if amp_env < 1.0 and i * atk_rate < 1.0:
            amp_env = i * atk_rate
        else:
            amp_env = max(sustain, amp_env * dec_rate)

        mix = 0.0
        for s in state:
            mod_sig = math.sin(s["m_ph"] + s["fb"] * s["last_mod"])
            s["last_mod"] = mod_sig
            carr = math.sin(s["c_ph"] + s["idx"] * mod_sig)
            mix += carr * s["lvl"]
            s["idx"] *= s["decay"]
            s["c_ph"] += s["c_inc"]
            s["m_ph"] += s["m_inc"]

        out[i] = mix * 0.2 * amp_env

    peak = max(abs(x) for x in out) or 1.0
    return [0.6 * x / peak for x in out]


def cimbalom_voice(midi_note, sr, dur=0.18):
    """Approximate Cimbalom: 3 detuned harmonic strings."""
    freq = 440.0 * 2 ** ((midi_note - 69) / 12.0)
    n = int(sr * dur)
    out = [0.0] * n
    twopi = 2 * math.pi

    # 3 strings with ±5 cents detuning
    detunes = [-5.0, 0.0, 5.0]
    harms = [(1, 1.0, 4.0), (2, 0.55, 3.5), (3, 0.35, 3.0),
             (4, 0.22, 2.5), (5, 0.14, 2.0), (6, 0.09, 1.7), (7, 0.06, 1.5)]

    amp_env = 0.0
    atk_rate = 1.0 / (0.003 * sr)

    for i in range(n):
        t = i / sr
        if i * atk_rate < 1.0:
            amp_env = i * atk_rate
        sample = 0.0
        for det in detunes:
            f0 = freq * 2 ** (det / 1200.0)
            for mult, amp, dec_t in harms:
                f = f0 * mult
                env = math.exp(-t / dec_t)
                sample += amp * env * math.sin(twopi * f * t)
        out[i] = sample * 0.05 * amp_env

    peak = max(abs(x) for x in out) or 1.0
    return [0.6 * x / peak for x in out]


def chromatic_tongue(midi_note, sr, dur=0.18):
    """Tongue drum: free-free beam modes (inharmonic)."""
    freq = 440.0 * 2 ** ((midi_note - 69) / 12.0)
    n = int(sr * dur)
    out = [0.0] * n
    twopi = 2 * math.pi
    ratios = [1.0, 2.756, 5.404, 8.933, 13.344]
    amps   = [1.0, 0.55, 0.30, 0.15, 0.08]
    decays = [1.2, 0.8, 0.5, 0.3, 0.2]

    for i in range(n):
        t = i / sr
        sample = 0.0
        for r, a, dec in zip(ratios, amps, decays):
            f = freq * r
            sample += a * math.exp(-t/dec) * math.sin(twopi * f * t)
        out[i] = sample * 0.1

    peak = max(abs(x) for x in out) or 1.0
    return [0.6 * x / peak for x in out]


def chromatic_plate(midi_note, sr, dur=0.18):
    """Water gong: Kirchhoff plate modes (inharmonic)."""
    freq = 440.0 * 2 ** ((midi_note - 69) / 12.0)
    n = int(sr * dur)
    out = [0.0] * n
    twopi = 2 * math.pi
    ratios = [1.0, 1.730, 2.328, 2.892, 3.439, 3.987]
    amps   = [1.0, 0.7, 0.5, 0.4, 0.3, 0.2]
    decays = [2.0, 1.5, 1.2, 1.0, 0.8, 0.6]

    for i in range(n):
        t = i / sr
        sample = 0.0
        for r, a, dec in zip(ratios, amps, decays):
            f = freq * r
            sample += a * math.exp(-t/dec) * math.sin(twopi * f * t)
        out[i] = sample * 0.1

    peak = max(abs(x) for x in out) or 1.0
    return [0.6 * x / peak for x in out]


# ────────────────────────────────────────────────────────────
# Runner
# ────────────────────────────────────────────────────────────

def run_test(label, sig_fn, midi, sr, algos):
    expected_freq = 440.0 * 2 ** ((midi - 69) / 12.0)
    exp_note, _, _ = freq_to_note(expected_freq)
    sig = sig_fn(midi, sr)

    line = f"{label:36s} sr={sr/1000:4.1f}k MIDI{midi:3d} exp={exp_note}({expected_freq:.1f}Hz)"
    print(line)
    for algo in algos:
        r = detect_pitch(sig, sr, algo)
        if r is None:
            print(f"   {algo}: NO DETECTION")
            continue
        note, cents, _ = freq_to_note(r["frequency"])
        match = "OK" if note == exp_note else "FAIL"
        peak_str = ", ".join(f"({l},{v:.2f})" for l,v in r["peaks"][:5])
        if len(r["peaks"]) > 5: peak_str += "..."
        print(f"   {algo}: {note}({cents:+5.1f}c) f={r['frequency']:7.2f} "
              f"lag={r['best_lag']} conf={r['confidence']:.3f} "
              f"gmax={r['global_max']:.2f} thr={r['threshold']:.2f} "
              f"sel#{r['selected_peak_index']} [{match}]")
        if r.get("swap_log"):
            for s in r["swap_log"]: print(f"     {s}")
        print(f"      peaks: {peak_str}")


def main():
    algos = ["CUR", "FIX"]
    print("="*100)
    print("TUNER REGRESSION AUDIT — Codex coverage")
    print("CUR = threshold 0.80, gmax 0.35, no recovery (current code)")
    print("FIX = threshold 0.85, gmax 0.45, safer zero-lag, octave-down recovery")
    print("="*100)

    midis = {"C4": 60, "A4": 69, "C5": 72}
    rates = [44100, 48000, 96000]

    print("\n--- Pure sine ---")
    for nname, midi in midis.items():
        for sr in rates:
            run_test(f"sine {nname}", lambda m, s, nn=nname, mi=midi: pure_sine(440.0*2**((mi-69)/12), s),
                     midi, sr, algos)

    print("\n--- FM Piano (type=0, default) ---")
    for nname, midi in midis.items():
        for sr in rates:
            run_test(f"FMPiano {nname}", lambda m, s: fm_voice(m, s, 0), midi, sr, algos)

    print("\n--- FM E.Piano 3-stack (type=1) ---")
    for nname, midi in midis.items():
        for sr in rates:
            run_test(f"FM EP-3stk {nname}", lambda m, s: fm_epiano_3stack(m, s), midi, sr, algos)

    print("\n--- Cimbalom (3-string detuned harmonic) ---")
    for nname, midi in midis.items():
        for sr in rates:
            run_test(f"Cimbalom {nname}", cimbalom_voice, midi, sr, algos)

    print("\n--- Chromatic tongue drum (free-free beam, inharmonic) ---")
    for nname, midi in midis.items():
        for sr in rates:
            run_test(f"Chrom tongue {nname}", chromatic_tongue, midi, sr, algos)

    print("\n--- Chromatic water gong (Kirchhoff plate, inharmonic) ---")
    for nname, midi in midis.items():
        for sr in rates:
            run_test(f"Chrom plate {nname}", chromatic_plate, midi, sr, algos)


if __name__ == "__main__":
    main()
