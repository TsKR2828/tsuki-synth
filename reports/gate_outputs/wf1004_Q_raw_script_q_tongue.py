#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF1004 Q card step 4: informational modal measurements on shipped tongue-drum-class (engine beam/tongue_drum)
single-event product WAVs. NOT a GATE; no tolerance is set or changed. Reads product WAVs from the extracted
copy in scratch, reads scores (read-only), runs `TsukiSynthCLI --dump-modes` (prints JSON to stdout, writes nothing)."""
import json, math, os, subprocess, sys
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt, hilbert, get_window

REPO = 'E:/Tsuki-project/tsuki-synth'
CLI = f'{REPO}/exports/renderer_archive/TsukiSynthCLI_9123db8f_build20260915.exe'
X = 'E:/Tsuki-project/_scratch/wf1004/Q/x/se'
BS = chr(92)
CAT = json.load(open(f'{REPO}/exports/products/clean_batch2_v1_1_candidate/catalog_v1_1.json', encoding='utf-8'))

TARGETS = ['akashic__Akashic_Light_Tap', 'clockwork__Clockwork_Bell_Strike', 'clockwork__Clockwork_Gear_Click',
           'forest__Forest_Acorn_Tap', 'ocean__Ocean_Droplet_Tap', 'ocean__Ocean_Bubble_Pop',
           'ocean__Ocean_Bubble_Pop_Deep', 'rabbit__Rabbit_Ding', 'rabbit__Rabbit_Ding_Angry',
           'rabbit__Rabbit_Carrot_Button', 'restraint__Restraint_Bolt_Click', 'akashic__Library_Opening_Bell']
NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def note_midi(n):
    p = NOTE[n[0]]; i = 1
    if n[i] in '#b':
        p += 1 if n[i] == '#' else -1; i += 1
    return 12 * (int(n[i:]) + 1) + p


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def peaks(seg, sr, fmax=20000):
    n = len(seg)
    w = get_window('blackmanharris', n)
    nfft = 1 << int(math.ceil(math.log2(n * 8)))
    S = np.abs(np.fft.rfft(seg * w, nfft))
    f = np.fft.rfftfreq(nfft, 1 / sr)
    m = 20 * np.log10(S / S.max() + 1e-12)
    idx = [i for i in range(2, len(S) - 2) if S[i] > S[i - 1] and S[i] >= S[i + 1] and m[i] > -60 and f[i] < fmax]
    out = []
    for i in idx:
        a, b, c = m[i - 1], m[i], m[i + 1]
        d = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0
        out.append((f[i] + d * (f[1] - f[0]), b - 0.25 * (a - c) * d))
    return sorted(out, key=lambda t: -t[1])


def t60(x, sr, f0, bw=0.03, t_start=0.0):
    """narrowband envelope log-slope T60 (same family of method as physics_verify --t60, own implementation).
    fit between -5 dB and -30 dB below the envelope's max after t_start; returns None if range not reached."""
    lo, hi = f0 * (1 - bw), min(f0 * (1 + bw), sr * 0.45)
    sos = butter(4, [lo, hi], btype='band', fs=sr, output='sos')
    y = sosfiltfilt(sos, x)
    env = np.abs(hilbert(y))
    k = np.convolve(env, np.ones(int(sr * 0.002)) / int(sr * 0.002), mode='same')
    db = 20 * np.log10(k + 1e-12)
    i0 = int(t_start * sr)
    ip = i0 + int(np.argmax(db[i0:]))
    pk = db[ip]
    seg = db[ip:]
    try:
        a = int(np.nonzero(seg <= pk - 5)[0][0])
        b = int(np.nonzero(seg <= pk - 30)[0][0])
    except IndexError:
        return None, pk
    t = np.arange(a, b) / sr
    sl, ic = np.polyfit(t, seg[a:b], 1)
    return (-60.0 / sl if sl < 0 else None), pk


rows = []
for key in TARGETS:
    c = next(r for r in CAT if r['kind'] == 'sfx' and os.path.basename(r['distribution'].replace(BS, '/')).startswith(key))
    sp = f"{REPO}/{c['score'].replace(BS, '/')}"
    sc = json.load(open(sp, encoding='utf-8'))
    ev0 = sc['events'][0]
    # onset of event 0 and its analysis window
    t_on = ev0['time']
    nxt = sc['events'][1]['time'] if len(sc['events']) > 1 else None
    path = f"{X}/{key.split('__')[0]}/{key}.wav"
    x, sr = sf.read(path, dtype='float64', always_2d=True)
    mid = x.mean(axis=1)
    r = subprocess.run([CLI, '--dump-modes', sp], capture_output=True, text=True, cwd=REPO)
    dm = json.loads(r.stdout)
    e0 = dm['events'][0]
    model = e0['partials']
    f_expect = hz(e0['midi'])
    win_end = (nxt - 0.01) if nxt else min(len(mid) / sr, 0.8)
    win_end = min(win_end, 1.2)
    a = int((t_on + 0.003) * sr); b = int(win_end * sr)
    seg = mid[a:b]
    pk = peaks(seg, sr)
    # fundamental = strongest peak within +-3% of expected f0 (model f0 = partial[0].freq)
    f1m = model[0]['freq']
    cand = [p for p in pk if abs(p[0] / f1m - 1) < 0.03]
    f1 = cand[0] if cand else None
    row = dict(file=key, engine=ev0['engine'], note=ev0['note'], material=ev0['params'].get('material'),
               boundary=ev0['params'].get('beam_boundary', 'cantilever(default)'),
               exciter=ev0['params'].get('exciter'), thickness_mm=ev0['params'].get('thickness_mm'),
               f_expect_ET=f_expect, model_modes=[(p['freq'], p['amp'], p['decay']) for p in model],
               window_s=(t_on + 0.003, win_end), n_events=len(sc['events']),
               reverb=sc['global'].get('effects', {}).get('reverb'))
    if f1:
        row['f1_meas'] = f1[0]; row['f1_cents_vs_model'] = 1200 * math.log2(f1[0] / f1m); row['f1_cents_vs_ET'] = 1200 * math.log2(f1[0] / f_expect)
    mm = []
    for p in model[:4]:
        c2 = [q for q in pk if abs(q[0] / p['freq'] - 1) < 0.03]
        if c2:
            q = c2[0]
            mm.append(dict(model_f=p['freq'], meas_f=q[0], err_pct=100 * (q[0] / p['freq'] - 1), rel_db=(q[1] - (f1[1] if f1 else 0)),
                           ratio_to_f1_model=p['freq'] / f1m, ratio_to_f1_meas=(q[0] / f1[0] if f1 else None)))
        else:
            mm.append(dict(model_f=p['freq'], meas_f=None, ratio_to_f1_model=p['freq'] / f1m))
    row['modes'] = mm
    row['top_peaks'] = [(round(q[0], 1), round(q[1], 1)) for q in pk[:6]]
    # T60 on fundamental and (if present) 2nd model partial
    seg_t = mid[int(t_on * sr):int(min(win_end + 0.0, len(mid) / sr) * sr)] if nxt else mid[int(t_on * sr):]
    row['t60_f1_meas'], _ = t60(seg_t, sr, f1m)
    row['t60_f1_model'] = model[0]['decay']
    if len(model) > 1 and model[1]['freq'] < sr * 0.4:
        row['t60_p2_meas'], _ = t60(seg_t, sr, model[1]['freq'])
        row['t60_p2_model'] = model[1]['decay']
    rows.append(row)
    print(json.dumps(row, ensure_ascii=False, default=float))
json.dump(rows, open('E:/Tsuki-project/_scratch/wf1004/Q/q_tongue.json', 'w'), indent=1, default=float)
