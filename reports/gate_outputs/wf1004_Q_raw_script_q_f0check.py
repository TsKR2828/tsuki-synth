import json, math, os
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, hilbert
X = 'E:/Tsuki-project/_scratch/wf1004/Q/x/se'
rows = json.load(open('E:/Tsuki-project/_scratch/wf1004/Q/q_tongue.json'))
out = []
for r in rows:
    key = r['file']
    x, sr = sf.read(f"{X}/{key.split('__')[0]}/{key}.wav", dtype='float64', always_2d=True)
    m = x.mean(axis=1)
    f_model = r['model_modes'][0][0]
    est = {}
    for bw in (0.03, 0.06):
        sos = butter(4, [f_model * (1 - bw), f_model * (1 + bw)], btype='band', fs=sr, output='sos')
        y = sosfiltfilt(sos, m)
        an = hilbert(y)
        env = np.abs(an)
        ph = np.unwrap(np.angle(an))
        inst = np.diff(ph) * sr / (2 * math.pi)
        # window: from 3 ms to the time where envelope falls 25 dB below its max (but at least 30 ms)
        ip = int(np.argmax(env[:int(0.2 * sr)]))
        a = max(ip, int(0.003 * sr))
        db = 20 * np.log10(env[a:] + 1e-12)
        below = np.nonzero(db <= db[0] - 25)[0]
        b = a + (int(below[0]) if len(below) else int(0.3 * sr))
        b = max(b, a + int(0.03 * sr))
        b = min(b, a + int(0.6 * sr))
        w = env[a:b]
        # envelope-weighted mean instantaneous frequency
        fe = float(np.sum(inst[a:b] * w[:-1] if False else inst[a:b] * w[:b - a]) / np.sum(w[:b - a]))
        est[f'iface_bw{int(bw*100)}'] = (fe, 1200 * math.log2(fe / f_model), (b - a) / sr)
    out.append((key, f_model, r['f1_cents_vs_model'], est))
    print(key, f"model {f_model:.3f}Hz fftpk {r['f1_cents_vs_model']:+.2f}c", {k: f"{v[0]:.2f}Hz {v[1]:+.2f}c win {v[2]*1000:.0f}ms" for k, v in est.items()})
json.dump(out, open('E:/Tsuki-project/_scratch/wf1004/Q/q_f0check.json', 'w'), indent=1)
