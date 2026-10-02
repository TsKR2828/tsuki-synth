"""Python replica of SimpleReverb.h (ALGO wet) and EffectChain IR wet path
(JUCE Convolution Normalise::yes = 0.125/sqrt(max channel energy), then x kIrWetMakeupGain=26.9).
Purpose: (1) validate replica vs D9c evidence (IR - ALGO@size0.5 ~ 0 dB),
(2) measure ALGO wet level dependence on fx_reverb_size / fx_reverb_decay (IR path has none),
(3) compare worst-case sine gain max|H(f)| and L1 norm (peak bound) between paths.
Replica only -- not the product binary. Mono (left channel) analysis."""
import numpy as np, soundfile as sf, sys
from scipy.signal import lfilter, resample_poly, fftconvolve

SR = 48000
COMB = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617]
AP = [556, 441, 341, 225]
scale = SR / 44100.0
combN = [max(1, int(c * scale)) for c in COMB]
apN = [max(1, int(a * scale)) for a in AP]
d1 = 0.5 * 0.4; d2 = 1.0 - d1

def algo_wet(x, size=0.5, decay=None):
    out = np.zeros_like(x)
    for N in combN:
        if decay is None:
            fb = size * 0.28 + 0.7
        elif decay == 0.0:
            fb = 0.0
        else:
            fb = float(np.clip(0.001 ** ((N / SR) / decay), 0.0, 0.9995))
        b = np.zeros(N + 2); b[N] = 1.0; b[N + 1] = -d1
        a = np.zeros(N + 1); a[0] = 1.0; a[1] = -d1; a[N] += -fb * d2
        out += lfilter(b, a, x)
    for M in apN:
        b = np.zeros(M + 1); b[0] = -1.0; b[M] = 1.5
        a = np.zeros(M + 1); a[0] = 1.0; a[M] = -0.5
        out = lfilter(b, a, out)
    return out * 0.15

def load_ir(path):
    h, sr = sf.read(path, always_2d=True)
    h = h.astype(np.float64)
    if sr != SR:
        from math import gcd
        g = gcd(SR, sr)
        h = resample_poly(h, SR // g, sr // g, axis=0)
    energy = max(float(np.sum(h[:, c] ** 2)) for c in range(h.shape[1]))
    h = h * (0.125 / np.sqrt(energy))
    return h[:, 0]

def ss_rms_db(y, burst):
    win = 512
    vals = []
    for s in range(max(0, burst - win * 8), burst - win + 1, win):
        seg = y[s:s + win]
        vals.append(20 * np.log10(np.sqrt(np.mean(seg ** 2))))
    return float(np.mean(vals))

rng = np.random.default_rng(271828)
burst = 2 * SR
x = np.concatenate([rng.uniform(-1, 1, burst), np.zeros(SR)])

ref = ss_rms_db(algo_wet(x, 0.5), burst)
print("ALGO wet steady-state RMS relative to size=0.5 default (replica, white noise):")
for s in (0.0, 0.25, 0.5, 0.75, 1.0):
    print("  fx_reverb_size=%.2f : %+6.2f dB" % (s, ss_rms_db(algo_wet(x, s), burst) - ref))
for d in (0.3, 1.0, 3.0, 10.0, 30.0):
    print("  fx_reverb_decay=%5.1f s : %+6.2f dB" % (d, ss_rms_db(algo_wet(x, decay=d), burst) - ref))

K = 26.9
base = sys.argv[1]
irs = {
    "Stairwells": base + "/Stairwells/CCRMA Stairwell Stanford University California.wav",
    "Venues": base + "/Venues/Conrad Prebys Concert Hall Seat F111 UC San Diego California.wav",
    "Sanctuaries": base + "/Sanctuaries/St Paul's Cathedral San Diego California.wav",
}
print("\nIR wet (x26.9) minus ALGO@0.5, white-noise steady-state (replica validation vs D9c -0.131/+0.108/-0.028 dB):")
hs = {}
for name, p in irs.items():
    h = load_ir(p); hs[name] = h
    y = fftconvolve(x, h)[:len(x)] * K
    print("  %-12s %+6.2f dB   (IR length %.2f s)" % (name, ss_rms_db(y, burst) - ref, len(h) / SR))

def algo_ir(size=0.5, decay=None, secs=40):
    imp = np.zeros(secs * SR); imp[0] = 1.0
    return algo_wet(imp, size, decay)

print("\nWorst-case gain comparison (single-channel wet impulse response):")
print("  %-26s %10s %10s %12s" % ("path", "max|H| dB", "rms|H| dB", "L1 (peak bd)"))
def report(label, h):
    H = np.abs(np.fft.rfft(h, n=1 << int(np.ceil(np.log2(len(h))))))
    print("  %-26s %+10.2f %+10.2f %12.1f" % (label, 20*np.log10(H.max()),
          10*np.log10(np.mean(H**2)), np.sum(np.abs(h))))
for s in (0.0, 0.5, 1.0):
    report("ALGO size=%.1f" % s, algo_ir(s))
for name, h in hs.items():
    report("IR %s x26.9" % name, h * K)
