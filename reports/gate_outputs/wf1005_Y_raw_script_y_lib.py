# WF1005 Y card measurement helpers (own implementation; no tolerance defined here, nothing is judged in this file)
import math, json, subprocess
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt, hilbert, get_window

CANT = [1.8751041, 4.6940911, 7.8547574, 10.9955407, 14.1371684]   # clamped-free eigenvalues (same constants as physics_verify.py)
CANT_RATIO = [(b / CANT[0]) ** 2 for b in CANT]                    # 1, 6.2669, 17.5475, 34.3861, 56.8426
NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def note_midi(n):
    p = NOTE[n[0]]; i = 1
    if n[i] in '#b':
        p += 1 if n[i] == '#' else -1; i += 1
    return 12 * (int(n[i:]) + 1) + p


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def cents(a, b):
    return 1200 * math.log2(a / b)


def read_mono(path):
    x, sr = sf.read(path, dtype='float64', always_2d=True)
    return x.mean(axis=1), sr


def dump_modes(cli, score, cwd):
    r = subprocess.run([cli, '--dump-modes', score], capture_output=True, text=True, cwd=cwd)
    return json.loads(r.stdout)


def bandpass(x, sr, lo, hi):
    hi = min(hi, sr * 0.45)
    sos = butter(4, [lo, hi], btype='band', fs=sr, output='sos')
    return sosfiltfilt(sos, x)


def mode_bw(f, t60):
    """half bandwidth (Hz): max(3 % of f, 5/T60) -- wide enough that the filter does not smear short decays; capped at 0.3 f"""
    return min(max(0.03 * f, 5.0 / max(t60, 1e-3)), 0.3 * f)


def analytic_mode(x, sr, f, t60):
    bw = mode_bw(f, t60)
    y = bandpass(x, sr, f - bw, f + bw)
    return hilbert(y)


def env_db(an, sr, smooth_ms=1.0):
    env = np.abs(an)
    n = max(1, int(sr * smooth_ms / 1000))
    k = np.convolve(env, np.ones(n) / n, mode='same')
    return 20 * np.log10(k + 1e-15)


def t60_envelope(an, sr, t0=0.0, lo=-5.0, hi=-30.0):
    """T60 from the narrow-band envelope log slope between lo and hi dB below the post-t0 envelope maximum (extrapolated to 60 dB).
    returns (t60 or None, peak_db, dynamic range reached)"""
    db = env_db(an, sr)
    i0 = int(t0 * sr)
    ip = i0 + int(np.argmax(db[i0:]))
    pk = db[ip]
    seg = db[ip:]
    try:
        a = int(np.nonzero(seg <= pk + lo)[0][0])
        b = int(np.nonzero(seg <= pk + hi)[0][0])
    except IndexError:
        return None, pk
    if b - a < 4:
        return None, pk
    t = np.arange(a, b) / sr
    sl, ic = np.polyfit(t, seg[a:b], 1)
    return (-60.0 / sl if sl < 0 else None), pk


def t60_schroeder(an, sr, t0=0.0, lo=-5.0, hi=-35.0):
    """T60 from the Schroeder backward-integrated energy decay curve of the narrow-band signal (EDC), line fit lo..hi dB, extrapolated to 60 dB"""
    y = np.real(an)
    i0 = int(t0 * sr)
    e = y[i0:] ** 2
    edc = np.cumsum(e[::-1])[::-1]
    db = 10 * np.log10(edc / edc[0] + 1e-30)
    try:
        a = int(np.nonzero(db <= lo)[0][0]); b = int(np.nonzero(db <= hi)[0][0])
    except IndexError:
        return None
    if b - a < 4:
        return None
    t = np.arange(a, b) / sr
    sl, ic = np.polyfit(t, db[a:b], 1)
    return (-60.0 / sl if sl < 0 else None)


def inst_freq(an, sr):
    ph = np.unwrap(np.angle(an))
    return np.diff(ph) * sr / (2 * math.pi)


def f_weighted(an, sr, a, b, power=1):
    """envelope-weighted (power=1, same as the WF1004 Q script) mean instantaneous frequency over samples a..b"""
    inst = inst_freq(an, sr)
    w = np.abs(an[a:b]) ** power
    return float(np.sum(inst[a:b] * w[:b - a]) / np.sum(w[:b - a]))


def peaks_frame(x, sr, start_s, win=2048, nfft=32768, wtype='hamming', fmax=None, floor_db=-80):
    """paper-style single-frame peak picking (Alon 2015 sec.4.2: Hamming 2048, FFT 32768); parabolic interpolation on dB magnitude"""
    a = int(start_s * sr)
    seg = x[a:a + win]
    if len(seg) < win:
        seg = np.concatenate([seg, np.zeros(win - len(seg))])
    w = get_window(wtype, win)
    S = np.abs(np.fft.rfft(seg * w, nfft))
    f = np.fft.rfftfreq(nfft, 1 / sr)
    m = 20 * np.log10(S / (S.max() + 1e-30) + 1e-15)
    out = []
    fmax = fmax or sr * 0.49
    for i in range(2, len(S) - 2):
        if S[i] > S[i - 1] and S[i] >= S[i + 1] and m[i] > floor_db and f[i] < fmax:
            al, be, ga = m[i - 1], m[i], m[i + 1]
            den = al - 2 * be + ga
            d = 0.5 * (al - ga) / den if den != 0 else 0.0
            out.append((f[i] + d * (f[1] - f[0]), be - 0.25 * (al - ga) * d))
    return sorted(out, key=lambda t: -t[1])


def peaks_long(x, sr, a_s, b_s, floor_db=-70, fmax=None):
    """high-resolution peak picking: Blackman-Harris over [a_s,b_s], 8x zero pad (same family as the WF1004 Q card)"""
    seg = x[int(a_s * sr):int(b_s * sr)]
    n = len(seg)
    w = get_window('blackmanharris', n)
    nfft = 1 << int(math.ceil(math.log2(n * 8)))
    S = np.abs(np.fft.rfft(seg * w, nfft))
    f = np.fft.rfftfreq(nfft, 1 / sr)
    m = 20 * np.log10(S / (S.max() + 1e-30) + 1e-15)
    fmax = fmax or sr * 0.49
    out = []
    for i in range(2, len(S) - 2):
        if S[i] > S[i - 1] and S[i] >= S[i + 1] and m[i] > floor_db and f[i] < fmax:
            al, be, ga = m[i - 1], m[i], m[i + 1]
            den = al - 2 * be + ga
            d = 0.5 * (al - ga) / den if den != 0 else 0.0
            out.append((f[i] + d * (f[1] - f[0]), be - 0.25 * (al - ga) * d))
    return sorted(out, key=lambda t: -t[1])


def beat_minima(env_lin_db, sr, floor_below_peak=40.0, min_depth_db=1.0):
    """paper sec.4.2.3 style: local minima of the magnitude envelope (dB) between the peak and `floor_below_peak` dB below it;
    a minimum counts only if the envelope rises by >= min_depth_db on both sides (so quantisation ripple is not counted).
    returns (n_minima, rate_hz or None = 1/mean spacing)"""
    db = env_lin_db
    ip = int(np.argmax(db))
    seg = db[ip:]
    lim = np.nonzero(seg <= seg[0] - floor_below_peak)[0]
    seg = seg[:lim[0]] if len(lim) else seg
    mins = []
    n = len(seg)
    k = 1
    while k < n - 1:
        if seg[k] < seg[k - 1] and seg[k] <= seg[k + 1]:
            # find local max neighbourhood
            l = k
            while l > 0 and seg[l - 1] >= seg[l]:
                l -= 1
            r = k
            while r < n - 1 and seg[r + 1] >= seg[r]:
                r += 1
            if seg[l] - seg[k] >= min_depth_db and seg[r] - seg[k] >= min_depth_db:
                mins.append(k)
            k = r + 1
        else:
            k += 1
    if len(mins) >= 2:
        sp = np.diff(mins) / sr
        return len(mins), 1.0 / float(np.mean(sp))
    return len(mins), None
