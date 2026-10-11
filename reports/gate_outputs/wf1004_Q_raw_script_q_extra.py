import json, math, os, re, subprocess, sys, zipfile
import numpy as np, soundfile as sf
import q_measure as qm
X = 'E:/Tsuki-project/_scratch/wf1004/Q/x'
CAND = 'E:/Tsuki-project/tsuki-synth/exports/products/clean_batch2_v1_1_candidate'
P = print
se = json.load(open('E:/Tsuki-project/_scratch/wf1004/Q/q_measure_se.json'))

P('=== G. loop-ready re-derivation: wrap-sum of the shipped ORIGINAL file vs shipped loop-ready (independent recompute) ===')
P('Method: y_ref[n] = sum_k x[n+kN] on the shipped original (24-bit float), N = loop-ready frame count; LS-fit one gain g (y_lr ~ g*y_ref); residual in LSB24 (2^-23).')
loops = [r for r in se if r['file'].startswith('loop_ready/')]
for r in loops:
    lr, sr = sf.read(f"{X}/se/{r['file']}", dtype='float64', always_2d=True)
    base = os.path.basename(r['file']).split('__LoopReady')[0]
    world = base.split('__')[0]
    orig, _ = sf.read(f"{X}/se/{world}/{base}.wav", dtype='float64', always_2d=True)
    N = lr.shape[0]
    y = np.zeros_like(lr)
    k = 0
    while k * N < orig.shape[0]:
        seg = orig[k * N:(k + 1) * N]
        y[:len(seg)] += seg
        k += 1
    g = float(np.sum(lr * y) / np.sum(y * y))
    res = lr - g * y
    lsb = 2.0 ** -23
    P(f"{base:32s} N={N} orig_frames={orig.shape[0]} wraps={k} fit_gain={20*math.log10(g):+.4f} dB  max|resid|={np.max(np.abs(res))/lsb:.2f} LSB24  rms|resid|={np.sqrt(np.mean(res**2))/lsb:.3f} LSB24")

P('\n=== H. mono-compatibility (descriptive): mono fold-down (L+R)/2 RMS vs mean per-channel RMS ===')
worst = []
for r in se + json.load(open('E:/Tsuki-project/_scratch/wf1004/Q/q_measure_album.json')):
    pth = f"{X}/se/{r['file']}" if r['file'].endswith('.wav') and not r['file'].startswith('WAV/') else f"{X}/album/{r['file']}"
    x, sr = sf.read(pth, dtype='float64', always_2d=True)
    mono = x.mean(axis=1)
    loss = 10 * math.log10((np.mean(mono ** 2) + 1e-30) / (np.mean(x ** 2) + 1e-30))
    worst.append((loss, r['file'], r.get('lr_corr')))
worst.sort()
for l, f, c in worst[:12]:
    P(f"{f[-60:]:60s} mono fold-down level change {l:+.2f} dB  L/R corr {c:+.3f}")
P(f"all 56 files: fold-down change range {worst[0][0]:+.2f} .. {worst[-1][0]:+.2f} dB; files with corr<0: {sum(1 for w in worst if (w[2] or 0) < 0)}")

P('\n=== I. DC detail: file mean and per-quarter means (dBFS of |mean|, L channel) for the 8 largest file means ===')
dc = sorted(se, key=lambda r: -max(abs(v) for v in r['dc_mean_lin']))[:8]
for r in dc:
    x, sr = sf.read(f"{X}/se/{r['file']}", dtype='float64', always_2d=True)
    q = np.array_split(x[:, 0], 4)
    P(f"{r['file'][-58:]:58s} mean {r['dc_mean_dbfs'][0]:.1f} dBFS ({r['dc_mean_lin'][0]:+.5f})  quarters: " + ' '.join(f"{20*math.log10(abs(float(np.mean(a)))+1e-12):.1f}({float(np.mean(a)):+.5f})" for a in q))

P('\n=== J. start/end abruptness (descriptive): first-sample level re file peak; last-sample level ===')
rows = []
for r in se:
    x, sr = sf.read(f"{X}/se/{r['file']}", dtype='float64', always_2d=True)
    pk = np.max(np.abs(x))
    f0 = float(np.max(np.abs(x[0]))); fl = float(np.max(np.abs(x[-1])))
    rows.append((20 * math.log10(f0 / pk + 1e-12), 20 * math.log10(fl + 1e-12), r['file']))
rows.sort(reverse=True)
P('largest first-sample step re peak (dB):')
for a, b, f in rows[:8]:
    P(f"  {f[-60:]:60s} first sample {a:+.1f} dB re peak; last sample {b:.1f} dBFS")
rows.sort(key=lambda t: -t[1])
P('highest last-sample level (one-shots only, loop-ready excluded):')
for a, b, f in [t for t in rows if not t[2].startswith('loop_ready')][:8]:
    P(f"  {f[-60:]:60s} last sample {b:.1f} dBFS")

P('\n=== K. album MP3 (ffprobe + decode TP/LUFS) ===')
for f in sorted(os.listdir(f'{X}/album/MP3')):
    p = f'{X}/album/MP3/{f}'
    pj = qm.ffprobe(p); s = pj['streams'][0]
    wav = f.replace('.mp3', '_44k16_tpdf.wav')
    pw = qm.ffprobe(f'{X}/album/WAV/{wav}')
    # decode and measure TP (8x) + ebur
    dec = subprocess.run([qm.FF, '-v', 'error', '-i', p, '-f', 'f64le', '-ac', '2', '-ar', str(s['sample_rate']), '-'], capture_output=True)
    d = np.frombuffer(dec.stdout, dtype='<f8').reshape(-1, 2)
    tp = qm.db(qm.true_peak(d, 8)) if d.shape[0] < 3_000_000 else qm.db(qm.true_peak(d, 4))
    eb = qm.ebur(p)
    P(f"{f:40s} codec={s['codec_name']} sr={s['sample_rate']} ch={s['channels']} br={int(s.get('bit_rate', 0))//1000}k dur_mp3={float(pj['format']['duration']):.3f} dur_wav={float(pw['format']['duration']):.3f} decodedTP={tp:.3f} I={eb['I']}")

P('\n=== L. demo reel (listed in release list) ===')
for rel in ('demo/TsukiSynth_Worldview_SE_Pack_Vol1_demo_reel.wav',):
    r, x = qm.measure(f'{CAND}/{rel}', rel, ups=(4, 8))
    P(rel, 'sr', r['sr'], 'ch', r['ch'], r['subtype'], f"{r['dur_s']:.3f}s", 'sample peak', f"{r['sample_peak_dbfs']:.4f}", 'TP', {k: round(v, 4) for k, v in r['tp_dbtp'].items()}, 'I', r['ebur']['I'], 'sha', r['sha256'][:16])
