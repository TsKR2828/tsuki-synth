"""Informational application of SOUND_DESIGN_KNOWLEDGE.zh-TW.md section-8 style checks to the 43 shipped SFX (+6 loop-ready).
Report-only numbers. No tolerance is set. Constants (20 ms window, band edges) are the doc's candidate constants."""
import json, math, os
import numpy as np, soundfile as sf
X = 'E:/Tsuki-project/_scratch/wf1004/Q/x/se'
REPO = 'E:/Tsuki-project/tsuki-synth'
BS = chr(92)
cat = json.load(open(f'{REPO}/exports/products/clean_batch2_v1_1_candidate/catalog_v1_1.json', encoding='utf-8'))
BANDS = [('sub 20-60', 20, 60), ('bass 60-250', 60, 250), ('lowmid 250-500', 250, 500), ('mid 500-2k', 500, 2000), ('highmid 2-6k', 2000, 6000), ('high 6-20k', 6000, 20000)]
rows = []
for c in cat:
    if c['kind'] != 'sfx':
        continue
    base = os.path.basename(c['distribution'].replace(BS, '/'))
    path = f"{X}/{c['group']}/{base}"
    x, sr = sf.read(path, dtype='float64', always_2d=True)
    m = x.mean(axis=1)
    n = len(m)
    w20 = int(0.02 * sr)
    rms_all = math.sqrt(np.mean(m ** 2)); rms_att = math.sqrt(np.mean(m[:w20] ** 2))
    att = 20 * math.log10(rms_att / rms_all + 1e-12)
    # 10 ms RMS envelope; time from envelope peak until it falls below -40 dB re peak (end of audible event, not file length)
    hop = int(0.01 * sr)
    k = n // hop
    env = np.sqrt(np.mean(m[:k * hop].reshape(k, hop) ** 2, axis=1))
    ip = int(np.argmax(env))
    db = 20 * np.log10(env / env[ip] + 1e-12)
    after = np.nonzero(db[ip:] <= -40)[0]
    t40 = (ip + (after[0] if len(after) else k - ip)) * hop / sr
    S = np.abs(np.fft.rfft(m)) ** 2
    f = np.fft.rfftfreq(n, 1 / sr)
    tot = S[(f >= 20) & (f <= 20000)].sum()
    sh = [100 * S[(f >= lo) & (f < hi)].sum() / tot for _, lo, hi in BANDS]
    rows.append(dict(file=f"{c['group']}/{base}", ptype=c['primary_type'], stype=c['sound_type'], file_s=n / sr, t40_s=t40, att_db=att, mud=sh[2], bands=sh))
print('=== M1. duration classes: UI-type (catalog primary_type == ui) files: file length vs time to -40 dB (10 ms RMS env) ===')
print('doc S4 candidate: micro-interaction 100-300 ms (UI only). Report-only.')
for r in rows:
    if r['ptype'] == 'ui':
        print(f"  {r['file']:58s} file {r['file_s']:.3f}s  envelope falls to -40 dB at {r['t40_s']:.2f}s after start")
print('\n=== M2. attack_energy_ratio (RMS 0-20 ms / RMS whole file, dB), all 43 sfx (report-only; doc says compare within same category) ===')
for r in sorted(rows, key=lambda r: r['att_db']):
    print(f"  {r['file']:58s} {r['ptype']:10s} {r['stype']:8s} {r['att_db']:7.1f} dB")
print('\n=== M3. 6-band energy share (%) and mud_ratio (250-500 Hz share) ===')
ms = np.array([r['mud'] for r in rows])
print(f'mud_ratio over 43 files: min {ms.min():.1f}%  median {np.median(ms):.1f}%  max {ms.max():.1f}% (doc sets NO absolute threshold; outliers vs median only)')
for r in sorted(rows, key=lambda r: -r['mud'])[:6]:
    print(f"  top mud: {r['file']:58s} {r['mud']:.1f}%  bands " + ' '.join(f'{b:.1f}' for b in r['bands']))
json.dump(rows, open('E:/Tsuki-project/_scratch/wf1004/Q/q_sdk.json', 'w'), indent=1)
