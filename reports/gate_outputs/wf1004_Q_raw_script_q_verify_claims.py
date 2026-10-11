import json, math, os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, 'E:/Tsuki-project/_scratch/wf1004/Q')
REPO = 'E:/Tsuki-project/tsuki-synth'
BS = chr(92)
X = 'E:/Tsuki-project/_scratch/wf1004/Q/x/se'

# (a) reverb in all 43 scores
cat = json.load(open(f'{REPO}/exports/products/clean_batch2_v1_1_candidate/catalog_v1_1.json', encoding='utf-8'))
nr = 0; miss = []
for c in cat:
    if c['kind'] != 'sfx':
        continue
    sc = json.load(open(f"{REPO}/{c['score'].replace(BS, '/')}", encoding='utf-8'))
    rv = sc['global'].get('effects', {}).get('reverb', {})
    if rv.get('wet', 0) and rv['wet'] > 0:
        nr += 1
    else:
        miss.append(c['title'])
print('(a) sfx scores with reverb wet>0:', nr, '/ 43; without:', miss)

# (b) 2x / 3x peaks near f1 in the 12 tongue-drum-class files
rows = json.load(open('E:/Tsuki-project/_scratch/wf1004/Q/q_tongue.json'))
import importlib.util
src = open('E:/Tsuki-project/_scratch/wf1004/Q/q_tongue.py', encoding='utf-8').read()
# reuse peaks() only
ns = {}
exec(src.split('rows = []')[0], ns)
peaks = ns['peaks']
for r in rows:
    key = r['file']
    x, sr = sf.read(f"{X}/{key.split('__')[0]}/{key}.wav", dtype='float64', always_2d=True)
    m = x.mean(axis=1)
    a, b = int(r['window_s'][0] * sr), int(r['window_s'][1] * sr)
    pk = peaks(m[a:b], sr)
    f1 = r['f1_meas']; ref = max(q[1] for q in pk)
    hit = []
    for mult in (2.0, 3.0):
        for q in pk:
            if abs(q[0] / (mult * f1) - 1) < 0.03 and q[1] > -50:
                hit.append((mult, round(q[0], 1), round(q[1], 1)))
    print('(b)', key, 'peaks near 2x/3x f1 (>-50 dB):', hit)

# (c) measured/model T60 ratio range
rat = []
for r in rows:
    if r.get('t60_f1_meas'):
        rat.append((r['t60_f1_meas'] / r['t60_f1_model'], r['file'], 'f1'))
    if r.get('t60_p2_meas') and r.get('t60_p2_model'):
        rat.append((r['t60_p2_meas'] / r['t60_p2_model'], r['file'], 'p2'))
rat.sort()
print('(c) measured/model T60 ratios: min', rat[0], 'max', rat[-1], 'n', len(rat))

# (d) loop-ready last-sample levels
meas = json.load(open('E:/Tsuki-project/_scratch/wf1004/Q/q_measure_se.json'))
for r in meas:
    if r['file'].startswith('loop_ready'):
        xx, sr = sf.read(f"{X}/{r['file']}", dtype='float64', always_2d=True)
        print('(d)', os.path.basename(r['file'])[:40], 'first sample abs', round(float(np.max(np.abs(xx[0]))), 5), 'last sample', round(20 * math.log10(float(np.max(np.abs(xx[-1]))) + 1e-12), 1), 'dBFS')

# (e) PDF inventory classification
inv = open('E:/Tsuki-project/_scratch/wf1004/Q/q_pdfs.txt', encoding='utf-8').read().split('\n')[1:]
stubs = []; good = []; bad = []
for l in inv:
    p = l.split(' | ')
    if len(p) < 5:
        continue
    size = int(p[1]); pages = int(p[3]); first = p[4]
    if any(s in first for s in ('Enable JavaScript', "Making sure you're not a bot", 'Access Denied', 'Accéder au contenu', 'Go to main content', 'Error')) or (size < 30000):
        stubs.append((p[0], size))
    elif pages <= 0 or p[2] == 'False':
        bad.append((p[0], size, pages))
    else:
        good.append(p[0])
print('(e) real/openable', len(good), 'web-stub pages', len(stubs), 'damaged', bad)
print('    stubs:', stubs)
