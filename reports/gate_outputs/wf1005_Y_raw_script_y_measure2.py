#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF1005 Y card, measurement stage 2 (final). Informational only: no GATE, no tolerance defined or changed (R2).
Reads: product WAVs (extracted copy in scratch, sha256 == catalog), dry scratch renders, dump-modes. Writes only JSON/text under scratch Y."""
import sys, os, json, math
sys.path.insert(0, 'E:/Tsuki-project/_scratch/wf1005/Y/scripts')
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from scipy.signal import stft
from y_lib import *

REPO = 'E:/Tsuki-project/tsuki-synth'
Y = 'E:/Tsuki-project/_scratch/wf1005/Y'
CLI = f'{Y}/bin/TsukiSynthCLI_current.exe'
IDX = json.load(open(f'{Y}/scores/index.json', encoding='utf-8'))
ORDER = list(IDX)
BS = chr(92)


def suppress_sidelobes(pk, sr, win=2048, k=4):
    """drop peaks that sit within k FFT-bins (of the 2048-sample frame) of a stronger peak: window-sidelobe leakage, not modes"""
    rad = k * sr / win
    keep = []
    for f, d in pk:
        if all(abs(f - g) > rad for g, _ in keep):
            keep.append((f, d))
    return keep


def estimators(x, sr, f_model, t_on, win_end):
    """Same two f0 estimators as the WF1004 Q card (own re-implementation, same windows): E1 FFT-peak (Blackman-Harris, 8x pad, window 3 ms..win_end)
    near f_model within 3 %; E2 envelope-weighted narrow-band instantaneous frequency (bw 3 % / 6 %), filter applied to the WHOLE file like the Q script,
    analysis window = 3 ms .. -25 dB (30 ms..600 ms)."""
    out = {}
    pk = peaks_long(x, sr, t_on + 0.003, min(win_end, len(x) / sr))
    cand = [p for p in pk if abs(p[0] / f_model - 1) < 0.03]
    out['E1_hz'] = cand[0][0] if cand else None
    out['E1_cents_vs_model'] = cents(cand[0][0], f_model) if cand else None
    for bw in (0.03, 0.06):
        y = bandpass(x, sr, f_model * (1 - bw), f_model * (1 + bw))
        an = hilbert(y)
        env = np.abs(an)
        ip = int(np.argmax(env[:int(0.2 * sr)]))
        a2 = max(ip, int(0.003 * sr))
        db = 20 * np.log10(env[a2:] + 1e-12)
        below = np.nonzero(db <= db[0] - 25)[0]
        b2 = a2 + (int(below[0]) if len(below) else int(0.3 * sr))
        b2 = max(b2, a2 + int(0.03 * sr)); b2 = min(b2, a2 + int(0.6 * sr), len(an) - 2)
        fe = f_weighted(an, sr, a2, b2)
        out[f'E2_bw{int(bw*100)}_hz'] = fe
        out[f'E2_bw{int(bw*100)}_cents_vs_model'] = cents(fe, f_model)
        out[f'E2_bw{int(bw*100)}_win_ms'] = (b2 - a2) / sr * 1000
    return out


def nz(v):
    return float('nan') if v is None else v


res = {}
for key in ORDER:
    info = IDX[key]
    sp_src = f"{REPO}/{info['src_score'].replace(BS, '/')}"
    note = info['note']; midi = note_midi(note); f_et = midi_hz(midi)
    dm = dump_modes(CLI, sp_src, REPO)['events'][0]['partials']
    f1m = dm[0]['freq']
    glide = info['glide']
    r = dict(key=key, note=note, midi=midi, f_et=f_et, engine=info['engine'], duration_s=info['duration'], glide=glide,
             n_events_src=info['n_events_src'], material=info['params'].get('material'),
             model=[dict(f=p['freq'], amp=p['amp'], t60=p['decay'], ratio=p['freq'] / f1m) for p in dm],
             model_f1_cents_vs_ET=cents(f1m, f_et))
    r['min_pair_spacing_hz'] = min(abs(dm[i]['freq'] - dm[j]['freq']) for i in range(len(dm)) for j in range(i + 1, len(dm))) if len(dm) > 1 else None
    v_free = 'free_noglide' if glide else 'free'
    v_dry = 'dry_noglide' if glide else 'dry'
    xb, sr = read_mono(f'{Y}/render_cur/{key}__{v_free}.wav')
    xa, _ = read_mono(f'{Y}/render_cur/{key}__{v_dry}.wav')
    xs, _ = read_mono(f'{Y}/render_cur/{key}__dry.wav')            # as authored (glide kept)
    xp, srp = read_mono(f'{Y}/x/se/{key}.wav')                     # shipped product WAV (reverb + gain baked in)
    assert srp == sr == 48000
    r['len_s'] = dict(free=len(xb) / sr, dry=len(xa) / sr, product=len(xp) / sr)
    # (1) paper-style single frame: 6 ms after onset, Hamming 2048, FFT 32768 (free render, glide removed)
    pk = suppress_sidelobes(peaks_frame(xb, sr, 0.006, floor_db=-60), sr)[:4]
    r['paper_frame_top4'] = [(float(f), float(d)) for f, d in pk]
    top3 = sorted([f for f, d in pk[:3]])
    r['paper_frame_top3_ratios_over_lowest'] = [float(f / top3[0]) for f in top3] if top3 else None
    # (2) per-mode narrow-band: frequency, level, T60 (envelope and Schroeder) on the free render
    modes = []
    for i, p in enumerate(dm[:5]):
        f = p['freq']
        if f > sr * 0.42:
            modes.append(dict(i=i, f_model=f, t60_model=p['decay'], note='>0.42 fs: not measured')); continue
        an = analytic_mode(xb, sr, f, p['decay'])
        t_env, pkdb = t60_envelope(an, sr)
        t_sch = t60_schroeder(an, sr)
        db = env_db(an, sr)
        ip = int(np.argmax(db[:int(0.2 * sr)]))
        a = max(ip, int(0.002 * sr))
        below = np.nonzero(db[a:] <= db[a] - 25)[0]
        b = a + (int(below[0]) if len(below) else int(0.3 * sr))
        b = max(b, a + int(0.005 * sr)); b = min(b, a + int(0.6 * sr), len(an) - 2)
        fm = f_weighted(an, sr, a, b)
        modes.append(dict(i=i, f_model=f, t60_model=p['decay'], t60_env=t_env, t60_schroeder=t_sch, f_meas=fm,
                          cents_vs_model=cents(fm, f), peak_db=float(pkdb), win_ms=(b - a) / sr * 1000))
    for m in modes:
        if m.get('f_meas') and modes[0].get('f_meas'):
            m['ratio_meas'] = m['f_meas'] / modes[0]['f_meas']; m['rel_peak_db'] = m['peak_db'] - modes[0]['peak_db']
    r['modes_free'] = modes
    # (3) f0 estimators: dry (engine level; glide removed for the two glide scores) vs product (Q-card windows)
    src = json.load(open(sp_src, encoding='utf-8'))
    nxt = src['events'][1]['time'] if len(src['events']) > 1 else None
    win_end = (nxt - 0.01) if nxt else min(len(xp) / sr, 0.8)
    win_end = min(win_end, 1.2)
    r['f0_window_end_s'] = win_end
    r['f0_dry_noglide_or_dry'] = estimators(xa, sr, f1m, 0.0, win_end)
    r['f0_dry_as_authored'] = estimators(xs, sr, f1m, 0.0, win_end)
    r['f0_product'] = estimators(xp, sr, f1m, 0.0, win_end)
    # (4) T60 of the fundamental: product (reverb baked) vs dry-as-authored vs free (model intrinsic)
    def t60f(x):
        an = analytic_mode(x, sr, f1m, dm[0]['decay'])
        return t60_envelope(an, sr)[0]
    r['t60_f1'] = dict(model=dm[0]['decay'], free_env=modes[0].get('t60_env'), free_schroeder=modes[0].get('t60_schroeder'),
                       dry_as_authored_env=t60f(xs), product_env=t60f(xp[:int(win_end * sr)] if nxt else xp))
    # (5) beating: paper sec.4.2.3 algorithm (local minima of the magnitude envelope of the fundamental bin)
    def beat(x):
        an = analytic_mode(x, sr, f1m, dm[0]['decay'])
        return beat_minima(env_db(an, sr, 1.0), sr)
    nmin_free, rate_free = beat(xb)
    nmin_prod, rate_prod = beat(xp)
    nmin_auth, rate_auth = beat(xs)
    fr, tt, Z = stft(xb, fs=sr, window='hamming', nperseg=2048, noverlap=1024, nfft=32768)
    kbin = int(np.argmin(np.abs(fr - f1m)))
    nmin_sp, rate_sp = beat_minima(20 * np.log10(np.abs(Z[kbin]) + 1e-15), sr / 1024.0, min_depth_db=1.0)
    r['beating'] = dict(dry_as_authored_minima=nmin_auth, dry_as_authored_rate_hz=rate_auth, free_minima=nmin_free, free_rate_hz=rate_free, product_minima=nmin_prod, product_rate_hz=rate_prod,
                        free_spectrogram_bin_minima=nmin_sp)
    # (6) glide trajectory (authored)
    if glide:
        wide_lo = midi_hz(note_midi(glide['from_note'])) * 0.75; wide_hi = f1m * 1.25
        an = hilbert(bandpass(xs, sr, wide_lo, wide_hi))
        inst = inst_freq(an, sr)
        k = int(0.004 * sr)
        sm = np.convolve(inst, np.ones(k) / k, mode='same')
        traj = {}
        for t_ms in (5, 15, 30, 45, 60, 80, 100, 130, 180, 250):
            i = int(t_ms / 1000 * sr)
            if i < len(sm): traj[t_ms] = float(sm[i])
        r['glide_traj_hz'] = traj
        r['glide_from_hz'] = midi_hz(note_midi(glide['from_note']))
    res[key] = r
    f0d = r['f0_dry_noglide_or_dry']; f0p = r['f0_product']
    print(f"{key:36s} ET {f_et:8.2f} | dry E1 {nz(f0d['E1_cents_vs_model']):+6.2f}c E2_3 {f0d['E2_bw3_cents_vs_model']:+6.2f}c E2_6 {f0d['E2_bw6_cents_vs_model']:+6.2f}c | prod E1 {nz(f0p['E1_cents_vs_model']):+6.2f}c E2_3 {f0p['E2_bw3_cents_vs_model']:+6.2f}c E2_6 {f0p['E2_bw6_cents_vs_model']:+6.2f}c")
    print('    T60 f1', {k2: (round(v, 4) if v else v) for k2, v in r['t60_f1'].items()}, 'beat', r['beating'], 'minpair', r['min_pair_spacing_hz'])
    if glide:
        print('    glide', {k2: round(v, 1) for k2, v in r['glide_traj_hz'].items()}, 'from', round(r['glide_from_hz'], 1), '->', round(f1m, 1))
json.dump(res, open(f'{Y}/measure_stage2.json', 'w'), indent=1, default=float)
