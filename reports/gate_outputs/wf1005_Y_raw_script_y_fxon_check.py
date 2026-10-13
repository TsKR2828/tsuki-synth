#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF1005 Y card: is the shipped product WAV == (scalar gain) x (the same score rendered with its FX on, normalize off)?
If yes, product-level frequencies are exactly those of the engine path plus the (deterministic) FX bake, so FX effects can be isolated by
comparing estimators on 'fx_on' vs 'dry'. Scratch only; products/scores read-only."""
import sys, os, json, copy, subprocess
sys.path.insert(0, 'E:/Tsuki-project/_scratch/wf1005/Y/scripts')
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import soundfile as sf
from y_lib import *

REPO = 'E:/Tsuki-project/tsuki-synth'
Y = 'E:/Tsuki-project/_scratch/wf1005/Y'
ARCH = f'{Y}/bin/TsukiSynthCLI_9123db8f_build20260915.exe'
CUR = f'{Y}/bin/TsukiSynthCLI_current.exe'
IDX = json.load(open(f'{Y}/scores/index.json', encoding='utf-8'))
BS = chr(92)
os.makedirs(f'{Y}/scores_fx', exist_ok=True); os.makedirs(f'{Y}/render_fx_arch', exist_ok=True); os.makedirs(f'{Y}/render_fx_cur', exist_ok=True)
out = {}
for key, info in IDX.items():
    sp = f"{REPO}/{info['src_score'].replace(BS, '/')}"
    sc = json.load(open(sp, encoding='utf-8'))
    s2 = copy.deepcopy(sc)
    s2['export'] = dict(s2['export']); s2['export']['normalize'] = False
    s2['export']['filename'] = key + '__fxon'; s2['export'].pop('export_filename', None)
    s2['meta'] = dict(s2['meta']); s2['meta']['id'] = (key + '_fxon').lower()
    fn = f'{Y}/scores_fx/{key}__fxon.score.json'
    json.dump(s2, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for exe, od in ((ARCH, 'render_fx_arch'), (CUR, 'render_fx_cur')):
        r = subprocess.run([exe, fn, '--output', f'{Y}/{od}'], capture_output=True, text=True)
        assert r.returncode == 0, (key, od, r.stdout, r.stderr)
    xp, sr = sf.read(f'{Y}/x/se/{key}.wav', dtype='float64', always_2d=True)
    xr, sr2 = sf.read(f'{Y}/render_fx_arch/{key}__fxon.wav', dtype='float64', always_2d=True)
    xc, _ = sf.read(f'{Y}/render_fx_cur/{key}__fxon.wav', dtype='float64', always_2d=True)
    same_arch_cur = bool(np.array_equal(xr, xc))
    n = min(len(xp), len(xr))
    a = xp[:n].ravel(); b = xr[:n].ravel()
    g = float(np.dot(a, b) / np.dot(b, b))
    resid = a - g * b
    lsb = 1.0 / 8388608
    out[key] = dict(len_product=len(xp), len_fxon=len(xr), gain=g, gain_db=20 * np.log10(g), resid_max_lsb24=float(np.abs(resid).max() / lsb),
                    resid_rms_db_rel=float(20 * np.log10(np.sqrt(np.mean(resid ** 2)) / np.sqrt(np.mean(a ** 2)) + 1e-30)),
                    arch_eq_cur=same_arch_cur)
    print(f"{key:36s} len prod/fxon {len(xp)}/{len(xr)} gain {20*np.log10(g):+.4f} dB resid max {out[key]['resid_max_lsb24']:.2f} LSB24 rel rms {out[key]['resid_rms_db_rel']:.1f} dB arch==cur {same_arch_cur}")
json.dump(out, open(f'{Y}/fxon_check.json', 'w'), indent=1)
