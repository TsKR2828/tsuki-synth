#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF1005 Y card: secondary informational checks (scratch scores only; products/scores read-only).
 (a) 2x / 3x bumps: does the dry (FX-off) render contain the small peaks near 2*f1 / 3*f1 that the WF1004 Q card saw in the shipped WAVs?
 (b) velocity -> number of peaks / relative modal level (paper App. B / Fig 2.14: stronger strike -> more peaks) on a probe built from the Bolt Click parameters
 (c) strike position -> relative modal amplitude (paper sec 4.3)
 (d) register -> fundamental T60 with fixed material/geometry parameters (paper Table 4.2 note-group trend)"""
import sys, os, json, copy, subprocess
sys.path.insert(0, 'E:/Tsuki-project/_scratch/wf1005/Y/scripts')
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from y_lib import *

REPO = 'E:/Tsuki-project/tsuki-synth'
Y = 'E:/Tsuki-project/_scratch/wf1005/Y'
CLI = f'{Y}/bin/TsukiSynthCLI_current.exe'
IDX = json.load(open(f'{Y}/scores/index.json', encoding='utf-8'))
BS = chr(92)
os.makedirs(f'{Y}/scores_x', exist_ok=True); os.makedirs(f'{Y}/render_x', exist_ok=True)
out = {}

# ---------------- (a) 2x / 3x bumps ----------------
a_res = {}
for key, info in IDX.items():
    v_free = 'free_noglide' if info['glide'] else 'free'
    xb, sr = read_mono(f'{Y}/render_cur/{key}__{v_free}.wav')
    xp, _ = read_mono(f'{Y}/x/se/{key}.wav')
    sp = f"{REPO}/{info['src_score'].replace(BS, '/')}"
    dm = dump_modes(CLI, sp, REPO)['events'][0]['partials']
    f1 = dm[0]['freq']
    src = json.load(open(sp, encoding='utf-8'))
    nxt = src['events'][1]['time'] if len(src['events']) > 1 else None
    win_end = min((nxt - 0.01) if nxt else min(len(xp) / sr, 0.8), 1.2)
    row = {}
    for lab, x in (('dry_free', xb), ('product', xp)):
        a_s = 0.003
        pk = peaks_long(x, sr, a_s, min(win_end, len(x) / sr), floor_db=-90)
        top = pk[0][1]
        r = {}
        for h in (2, 3):
            c = [p for p in pk if abs(p[0] / (h * f1) - 1) < 0.03]
            r[f'{h}x_level_db'] = (c[0][1] - top) if c else None   # relative to strongest peak in the window
            r[f'{h}x_freq_hz'] = c[0][0] if c else None
        row[lab] = r
    a_res[key] = row
    d = row['dry_free']; p = row['product']
    f = lambda v: 'none>-90' if v is None else f'{v:.1f} dB'
    print(f"{key:36s} 2x dry {f(d['2x_level_db']):>10s} prod {f(p['2x_level_db']):>10s} | 3x dry {f(d['3x_level_db']):>10s} prod {f(p['3x_level_db']):>10s}")
out['bumps'] = a_res

# ---------------- probes from Bolt Click parameters ----------------
bolt = json.load(open(f"{REPO}/{IDX['restraint__Restraint_Bolt_Click']['src_score'].replace(BS, '/')}", encoding='utf-8'))
dryfx = {'reverb': {'decay': 2.0, 'wet': 0.0}, 'delay': {'time_ms': 0, 'feedback': 0.0, 'wet': 0.0},
         'wall': {'distance_m': 0.0, 'material': 'wood'}, 'distortion': {'type': 'overdrive', 'drive': 0.0, 'instability': 0.0, 'wet': 0.0}}


def probe(tag, note=None, vel=None, sp=None, dur=None):
    s = copy.deepcopy(bolt)
    s['events'] = [copy.deepcopy(bolt['events'][0])]
    ev = s['events'][0]
    if note: ev['note'] = note
    if vel is not None: ev['velocity'] = vel
    if sp is not None: ev['params']['strike_position'] = sp
    ev['duration'] = dur if dur else 30.0
    s['global']['effects'] = dryfx
    s['export'] = {'filename': tag, 'format': 'wav', 'bit_depth': 24, 'normalize': False, 'tail_silence_ms': 200}
    s['meta'] = {'title': tag, 'id': tag.lower()}
    fn = f'{Y}/scores_x/{tag}.score.json'
    json.dump(s, open(fn, 'w', encoding='utf-8'), indent=1)
    return fn


def dm_of(fn):
    return dump_modes(CLI, fn, REPO)['events'][0]['partials']


# (b) velocity
b_res = {}
for v in (0.25, 0.5, 0.65, 0.95):
    fn = probe(f'probe_vel_{int(v*100)}', vel=v)
    dm = dm_of(fn)
    subprocess.run([CLI, fn, '--output', f'{Y}/render_x'], capture_output=True)
    x, sr = read_mono(f'{Y}/render_x/probe_vel_{int(v*100)}.wav')
    pk = suppress = None
    pks = peaks_frame(x, sr, 0.006, floor_db=-60)
    # sidelobe suppression like stage 2
    rad = 4 * sr / 2048
    keep = []
    for f, dd in pks:
        if all(abs(f - g) > rad for g, _ in keep): keep.append((f, dd))
    amps = [p['amp'] for p in dm]
    b_res[v] = dict(n_modes_model=len(dm), amp_ratio_m2_m1_db=20 * np.log10(amps[1] / amps[0]), n_peaks_above_m40=len([1 for f, dd in keep if dd > -40]),
                    n_peaks_above_m60=len(keep), peak_abs=float(np.abs(x).max()))
    print('velocity', v, b_res[v])
out['velocity'] = b_res

# (c) strike position
c_res = {}
for spos in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5):
    fn = probe(f'probe_sp_{int(spos*100)}', sp=spos)
    dm = dm_of(fn)
    amps = [p['amp'] for p in dm]
    c_res[spos] = dict(amps=amps, m2_over_m1_db=20 * np.log10(amps[1] / amps[0]), m3_over_m1_db=20 * np.log10(amps[2] / amps[0]) if len(amps) > 2 else None)
    print('strike_position', spos, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in c_res[spos].items() if k != 'amps'})
out['strike_position'] = c_res

# (d) register
d_res = {}
for nm in ('G3', 'D4', 'G4', 'C5', 'G5', 'C6', 'G6'):
    fn = probe(f'probe_note_{nm}', note=nm)
    dm = dm_of(fn)
    d_res[nm] = dict(f1=dm[0]['freq'], t60_f1=dm[0]['decay'], t60_f2=dm[1]['decay'] if len(dm) > 1 else None, n=len(dm))
    print('register', nm, d_res[nm])
out['register'] = d_res
json.dump(out, open(f'{Y}/extras.json', 'w'), indent=1, default=float)
