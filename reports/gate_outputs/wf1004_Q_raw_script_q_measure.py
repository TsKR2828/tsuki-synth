#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF1004 Q card: read-only independent measurement of shipped product WAVs.
Inputs : zips extracted to scratch (x/se, x/album) + candidate folder (read only).
Outputs: E:/Tsuki-project/_scratch/wf1004/Q/q_measure.json (+ stdout table).
No threshold in this script is a GATE tolerance: flags are descriptive only.
"""
import json, math, os, re, subprocess, sys, hashlib
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

FF = os.path.expandvars(r'%USERPROFILE%\Desktop\Tools\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe')
FP = FF.replace('ffmpeg.exe', 'ffprobe.exe')
ROOT = 'E:/Tsuki-project/_scratch/wf1004/Q/x'
CAND = 'E:/Tsuki-project/tsuki-synth/exports/products/clean_batch2_v1_1_candidate'


def db(x):
    return -999.0 if x <= 0 else 20 * math.log10(x)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def ffprobe(p):
    r = subprocess.run([FP, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', p],
                       capture_output=True, text=True)
    return json.loads(r.stdout)


def ebur(p):
    """ffmpeg ebur128 summary: I, LRA, true peak (dBFS, 1-decimal print) and max momentary
    (400 ms) via metadata frame log. Tail padded 0.5 s like X1 so the window scans the whole file."""
    cmd = [FF, '-hide_banner', '-nostats', '-i', p, '-af',
           'apad=pad_dur=0.5,ebur128=peak=true:metadata=1,ametadata=mode=print:key=lavfi.r128.M:file=-',
           '-f', 'null', '-']
    r = subprocess.run(cmd, capture_output=True, text=True)
    err = r.stderr
    ms = [float(m.group(1)) for m in re.finditer(r'lavfi\.r128\.M=(-?[\d.]+|-?inf)', r.stdout)
          if m.group(1) not in ('-inf',)]
    # summary block is at the end of stderr
    blk = err[err.rfind('Summary:'):] if 'Summary:' in err else ''
    def g(pat):
        m = re.search(pat, blk)
        return float(m.group(1)) if m else None
    return dict(I=g(r'I:\s+(-?[\d.]+) LUFS'), LRA=g(r'LRA:\s+(-?[\d.]+) LU'),
                tp_ebur_dbfs=g(r'Peak:\s+(-?[\d.]+) dBFS'),
                maxM=max(ms) if ms else None)


def true_peak(x, up):
    """x: (n, ch) float64. chunked resample_poly; returns max |.| linear."""
    n = x.shape[0]
    CH = 48000 * 8
    PAD = 4096
    best = 0.0
    for c in range(x.shape[1]):
        s = 0
        while s < n:
            a = max(0, s - PAD)
            b = min(n, s + CH + PAD)
            y = resample_poly(x[a:b, c], up, 1)
            lo = (s - a) * up
            hi = lo + min(CH, n - s) * up
            best = max(best, float(np.max(np.abs(y[lo:hi]))))
            s += CH
    return best


def code_stats(p, info):
    """integer-code stats: full-scale hits and flat-top runs at max code."""
    sub = info.subtype
    if sub == 'PCM_24':
        xi, sh = sf.read(p, dtype='int32', always_2d=True)[0] >> 8, 8
        fs_pos, fs_neg = 8388607, -8388608
    elif sub == 'PCM_16':
        xi = sf.read(p, dtype='int16', always_2d=True)[0].astype(np.int32)
        fs_pos, fs_neg = 32767, -32768
    else:
        return None
    n_fs = int(np.sum((xi >= fs_pos) | (xi <= fs_neg)))
    mx = int(np.max(np.abs(xi)))
    at_max = (np.abs(xi) == mx)
    # longest run of consecutive samples (same channel) at the file's max |code|
    best = 0
    for c in range(xi.shape[1]):
        a = at_max[:, c].astype(np.int8)
        if a.any():
            d = np.diff(np.concatenate(([0], a, [0])))
            st = np.where(d == 1)[0]; en = np.where(d == -1)[0]
            best = max(best, int((en - st).max()))
    # longest run of identical consecutive non-zero values >= 0.5 full scale (flat top / hard clip proxy)
    flat = 0
    half = 0.5 * fs_pos
    for c in range(xi.shape[1]):
        v = xi[:, c]
        same = (v[1:] == v[:-1]) & (np.abs(v[1:]) >= half)
        if same.any():
            d = np.diff(np.concatenate(([0], same.astype(np.int8), [0])))
            st = np.where(d == 1)[0]; en = np.where(d == -1)[0]
            flat = max(flat, int((en - st).max()) + 1)
    return dict(code_max=mx, full_scale_hits=n_fs, n_at_max_code=int(at_max.sum()),
                max_run_at_max_code=best, max_flat_run_ge_half_fs=flat)


def edges(x, sr):
    """leading/trailing silence + edge behaviour. x (n,ch) float."""
    a = np.max(np.abs(x), axis=1)
    nz = np.nonzero(a > 0)[0]
    out = {}
    if len(nz) == 0:
        return dict(all_zero=True)
    out['lead_exact_zero_ms'] = nz[0] / sr * 1000
    out['trail_exact_zero_ms'] = (len(a) - 1 - nz[-1]) / sr * 1000
    for thr_db in (-80, -60):
        t = 10 ** (thr_db / 20)
        k = np.nonzero(a > t)[0]
        out[f'lead_below_{-thr_db}dBFS_ms'] = k[0] / sr * 1000
        out[f'trail_below_{-thr_db}dBFS_ms'] = (len(a) - 1 - k[-1]) / sr * 1000
    out['first_sample_abs'] = float(a[0])
    out['last_sample_abs'] = float(a[-1])
    w = int(sr * 0.010)
    out['first10ms_rms_dbfs'] = db(float(np.sqrt(np.mean(x[:w] ** 2))))
    out['last10ms_rms_dbfs'] = db(float(np.sqrt(np.mean(x[-w:] ** 2))))
    pk = int(np.argmax(a))
    out['peak_pos_ms'] = pk / sr * 1000
    return out


def seam(x, sr):
    """Seam descriptor between last sample and first sample (wrap) for loops.
    Descriptive only. d1 = adjacent difference (max over channels); d2 = second difference
    across the seam (x[0]-2x[N-1]+x[N-2])  [curvature at the seam]."""
    n = x.shape[0]
    d1 = np.max(np.abs(np.diff(x, axis=0)), axis=1)         # in-file steps, n-1
    jump = float(np.max(np.abs(x[0] - x[-1])))
    d2 = np.max(np.abs(x[2:] - 2 * x[1:-1] + x[:-2]), axis=1)
    seam_d2 = float(np.max(np.abs(x[0] - 2 * x[-1] + x[-2])))
    seam_d2b = float(np.max(np.abs(x[1] - 2 * x[0] + x[-1])))
    # HF burst: energy of first difference in +-1 ms around the seam vs. median of sliding 2 ms windows in file
    w = int(sr * 0.001)
    y = np.concatenate([x[-w:], x[:w]])
    e_seam = float(np.mean(np.diff(y, axis=0) ** 2))
    dd = np.sum(np.diff(x, axis=0) ** 2, axis=1) / x.shape[1]
    win = 2 * w
    cs = np.cumsum(np.concatenate(([0.0], dd)))
    wins = (cs[win:] - cs[:-win]) / win
    e_med = float(np.median(wins)); e_max = float(np.max(wins))
    e_seam_all = e_seam * x.shape[1] / x.shape[1]
    return dict(jump=jump, jump_pct_of_instep=float(np.mean(d1 <= jump) * 100),
                instep_p50=float(np.percentile(d1, 50)), instep_p99=float(np.percentile(d1, 99)),
                instep_max=float(d1.max()),
                seam_curv=seam_d2, seam_curv2=seam_d2b, curv_p99=float(np.percentile(d2, 99)), curv_max=float(d2.max()),
                seam_hf_vs_median_db=(10 * math.log10(e_seam / e_med) if e_med > 0 and e_seam > 0 else None),
                seam_hf_vs_max_db=(10 * math.log10(e_seam / e_max) if e_max > 0 and e_seam > 0 else None))


def measure(p, label, ups=(4, 8, 32), longfile_limit=4_000_000):
    info = sf.info(p)
    x, sr = sf.read(p, dtype='float64', always_2d=True)
    n, ch = x.shape
    r = dict(file=label, sr=sr, ch=ch, subtype=info.subtype, frames=n, dur_s=n / sr)
    pj = ffprobe(p)
    s0 = pj['streams'][0]
    r['ffprobe'] = dict(codec=s0.get('codec_name'), sr=int(s0['sample_rate']), ch=s0['channels'],
                        bits=s0.get('bits_per_sample'), nb=s0.get('nb_samples') or s0.get('duration_ts'),
                        dur=float(pj['format']['duration']))
    pk = float(np.max(np.abs(x)))
    r['sample_peak_dbfs'] = db(pk)
    tps = {}
    for up in ups:
        if up == 32 and n > longfile_limit:
            continue
        tps[up] = db(true_peak(x, up))
    r['tp_dbtp'] = tps
    r['dc_mean_lin'] = [float(v) for v in x.mean(axis=0)]
    r['dc_mean_dbfs'] = [db(abs(float(v))) for v in x.mean(axis=0)]
    r['rms_dbfs'] = db(float(np.sqrt(np.mean(x ** 2))))
    r['code'] = code_stats(p, info)
    r['edges'] = edges(x, sr)
    if ch == 2:
        l, rr = x[:, 0], x[:, 1]
        r['lr_max_abs_diff'] = float(np.max(np.abs(l - rr)))
        den = math.sqrt(float(np.sum(l * l) * np.sum(rr * rr)))
        r['lr_corr'] = float(np.sum(l * rr) / den) if den > 0 else None
    r['ebur'] = ebur(p)
    r['sha256'] = sha(p)
    return r, x


if __name__ == '__main__':
    which = sys.argv[1]
    out = []
    if which == 'se':
        base = f'{ROOT}/se'
        files = []
        for w in sorted(os.listdir(base)):
            d = f'{base}/{w}'
            if os.path.isdir(d) and w != 'loop_ready':
                files += [f'{w}/{f}' for f in sorted(os.listdir(d)) if f.endswith('.wav')]
        for w in sorted(os.listdir(f'{base}/loop_ready')):
            files += [f'loop_ready/{w}/{f}' for f in sorted(os.listdir(f'{base}/loop_ready/{w}')) if f.endswith('.wav')]
    else:
        base = f'{ROOT}/album'
        files = [f'WAV/{f}' for f in sorted(os.listdir(f'{base}/WAV'))]
    for f in files:
        r, x = measure(f'{base}/{f}', f)
        if f.startswith('loop_ready/'):
            r['seam'] = seam(x, r['sr'])
        out.append(r)
        t = r['tp_dbtp']
        print(f"{f[:70]:70s} {r['sr']} {r['ch']}ch {r['subtype']} {r['dur_s']:.3f}s sp={r['sample_peak_dbfs']:.4f} "
              f"tp={ {k: round(v, 4) for k, v in t.items()} } I={r['ebur']['I']} maxM={r['ebur']['maxM']}", flush=True)
    json.dump(out, open(f'E:/Tsuki-project/_scratch/wf1004/Q/q_measure_{which}.json', 'w'), indent=1)
