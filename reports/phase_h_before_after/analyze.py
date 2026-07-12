import numpy as np
import wave, sys, os, json, hashlib

SCORES = [
    ("fur_elise_opening", "fur_elise_opening.wav"),
    ("moonlight_sonata_i_tongue_drum", "moonlight_sonata_i_tongue_drum.wav"),
    ("moonlight_sonata_i_yangqin", "moonlight_sonata_i_yangqin.wav"),
    ("physical_piano", "physical_piano.wav"),
    ("water_gong_clamped", "water_gong_clamped.wav"),
    ("water_gong_free", "water_gong_free.wav"),
]

BASE = os.path.dirname(__file__)

def read_wav(path):
    with wave.open(path, 'rb') as w:
        sr = w.getframerate()
        n = w.getnframes()
        sw = w.getsampwidth()
        ch = w.getnchannels()
        raw = w.readframes(n)
    if sw == 2:
        data = np.frombuffer(raw, dtype='<i2').astype(np.float64) / 32768.0
    elif sw == 3:
        # 24-bit
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        as_int = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
        as_int[as_int >= (1 << 23)] -= (1 << 24)
        data = as_int.astype(np.float64) / (1 << 23)
    elif sw == 4:
        data = np.frombuffer(raw, dtype='<i4').astype(np.float64) / (2**31)
    else:
        raise ValueError(f"unsupported sampwidth {sw}")
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    return sr, data

def dbfs(x):
    r = np.sqrt(np.mean(x**2)) if len(x) else 0.0
    return 20*np.log10(max(r, 1e-12))

def peak_dbfs(x):
    p = np.max(np.abs(x)) if len(x) else 0.0
    return 20*np.log10(max(p, 1e-12))

def top_partials(x, sr, n=6, window_s=2.0):
    n_samp = min(len(x), int(window_s*sr))
    seg = x[:n_samp]
    win = np.hanning(len(seg))
    spec = np.fft.rfft(seg*win, n=len(seg)*4)
    freqs = np.fft.rfftfreq(len(seg)*4, d=1.0/sr)
    mag = np.abs(spec)
    magdb = 20*np.log10(np.maximum(mag, 1e-12))
    # find local maxima at least 20 Hz apart
    peaks = []
    i = 1
    minsep_bins = max(1, int(20 / (freqs[1]-freqs[0])))
    order = np.argsort(magdb)[::-1]
    used = np.zeros(len(freqs), dtype=bool)
    for idx in order:
        if used[idx]:
            continue
        if freqs[idx] < 20:
            continue
        peaks.append((freqs[idx], magdb[idx]))
        lo = max(0, idx-minsep_bins)
        hi = min(len(freqs), idx+minsep_bins)
        used[lo:hi] = True
        if len(peaks) >= n:
            break
    peaks.sort(key=lambda p: -p[1])
    return peaks

def spectral_centroid(x, sr, window_s=2.0):
    n_samp = min(len(x), int(window_s*sr))
    seg = x[:n_samp]
    win = np.hanning(len(seg))
    spec = np.abs(np.fft.rfft(seg*win))
    freqs = np.fft.rfftfreq(len(seg), d=1.0/sr)
    if spec.sum() == 0:
        return 0.0
    return float((freqs*spec).sum() / spec.sum())

def hilbert_env_db(x, sr):
    # crude envelope via analytic signal (numpy has no hilbert; use FFT-based)
    N = len(x)
    Xf = np.fft.fft(x)
    h = np.zeros(N)
    if N % 2 == 0:
        h[0] = h[N//2] = 1
        h[1:N//2] = 2
    else:
        h[0] = 1
        h[1:(N+1)//2] = 2
    analytic = np.fft.ifft(Xf*h)
    env = np.abs(analytic)
    envdb = 20*np.log10(np.maximum(env, 1e-9))
    return envdb

def t60_estimate(x, sr):
    # simple broadband envelope log-slope fit over the first 90% (skip 100ms attack, stop at -50dB or 3s)
    env = hilbert_env_db(x, sr)
    skip = int(0.1*sr)
    ref = env[skip] if skip < len(env) else env[0]
    rel = env[skip:] - ref
    stop_idx = len(rel)
    for i, v in enumerate(rel):
        if v < -50:
            stop_idx = i
            break
    stop_idx = min(stop_idx, int(3.0*sr))
    if stop_idx < sr*0.2:
        stop_idx = min(len(rel), int(sr*0.2))
    t = np.arange(stop_idx) / sr
    seg = rel[:stop_idx]
    if len(seg) < 10:
        return None
    slope, intercept = np.polyfit(t, seg, 1)  # dB/s
    if slope >= -1e-6:
        return None
    t60 = -60.0/slope
    return t60

def sha256_of(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

results = {}
for name, fname in SCORES:
    bpath = os.path.join(BASE, 'before', fname)
    apath = os.path.join(BASE, 'after', fname)
    sr_b, xb = read_wav(bpath)
    sr_a, xa = read_wav(apath)
    same_hash = sha256_of(bpath) == sha256_of(apath)
    entry = {
        'sha_identical': same_hash,
        'rms_before': dbfs(xb), 'rms_after': dbfs(xa),
        'peak_before': peak_dbfs(xb), 'peak_after': peak_dbfs(xa),
        'centroid_before': spectral_centroid(xb, sr_b),
        'centroid_after': spectral_centroid(xa, sr_a),
        'len_before_s': len(xb)/sr_b, 'len_after_s': len(xa)/sr_a,
        'partials_before': top_partials(xb, sr_b),
        'partials_after': top_partials(xa, sr_a),
        't60_before': t60_estimate(xb, sr_b),
        't60_after': t60_estimate(xa, sr_a),
    }
    results[name] = entry

for name, e in results.items():
    print(f"=== {name} ===")
    print(f"  SHA256 identical: {e['sha_identical']}")
    print(f"  RMS  before={e['rms_before']:.3f} dBFS  after={e['rms_after']:.3f} dBFS  delta={e['rms_after']-e['rms_before']:+.3f}")
    print(f"  Peak before={e['peak_before']:.3f} dBFS  after={e['peak_after']:.3f} dBFS  delta={e['peak_after']-e['peak_before']:+.3f}")
    print(f"  Spectral centroid before={e['centroid_before']:.2f} Hz  after={e['centroid_after']:.2f} Hz  delta={e['centroid_after']-e['centroid_before']:+.2f}")
    print(f"  T60(broadband est) before={e['t60_before']}  after={e['t60_after']}")
    print(f"  top partials before: {[(round(f,2), round(d,2)) for f,d in e['partials_before']]}")
    print(f"  top partials after : {[(round(f,2), round(d,2)) for f,d in e['partials_after']]}")
    print()

import pickle
with open(os.path.join(BASE, 'results.pkl'), 'wb') as f:
    pickle.dump(results, f)
