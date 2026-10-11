import json, os, re, math, sys, zipfile, hashlib, csv
import numpy as np
Q = 'E:/Tsuki-project/_scratch/wf1004/Q'
CAND = 'E:/Tsuki-project/tsuki-synth/exports/products/clean_batch2_v1_1_candidate'
se = json.load(open(f'{Q}/q_measure_se.json'))
al = json.load(open(f'{Q}/q_measure_album.json'))
cat = json.load(open(f'{CAND}/catalog_v1_1.json', encoding='utf-8'))
rep = json.load(open(f'{CAND}/loop_ready/loop_ready_report.json', encoding='utf-8')) if os.path.exists(f'{CAND}/loop_ready/loop_ready_report.json') else None
P = print

def tpmax(r):
    return max(r['tp_dbtp'].values())
def tpmin(r):
    return min(r['tp_dbtp'].values())

P('=== A. FORMAT (soundfile vs ffprobe vs README claim 48k/24bit/stereo) ===')
bad = []
for r in se:
    f = r['ffprobe']
    ok = (r['sr'] == 48000 and r['ch'] == 2 and r['subtype'] == 'PCM_24' and f['sr'] == 48000 and f['ch'] == 2
          and f['bits'] == 24 and f['codec'] == 'pcm_s24le' and int(f['nb']) == r['frames'])
    if not ok: bad.append(r['file'])
P(f'SE zip WAV count={len(se)}  all 48k/24bit/2ch/pcm_s24le & ffprobe nb_samples==frames: {len(bad)==0} bad={bad}')
bad = []
for r in al:
    f = r['ffprobe']
    ok = (r['sr'] == 44100 and r['ch'] == 2 and r['subtype'] == 'PCM_16' and f['codec'] == 'pcm_s16le' and int(f['nb']) == r['frames'])
    if not ok: bad.append(r['file'])
P(f'Album WAV count={len(al)} all 44.1k/16bit/2ch: {len(bad)==0} bad={bad}')

P('\n=== B. TRUE PEAK / SAMPLE PEAK (own meters: scipy resample_poly 4x/8x/32x; ffmpeg ebur128 prints 1 decimal) ===')
sfx = [r for r in se if not r['file'].startswith('loop_ready/')]
lp = [r for r in se if r['file'].startswith('loop_ready/')]
for name, grp in (('SE distribution 43', sfx), ('SE loop_ready 6', lp), ('Album WAV 7', al)):
    tmax = max(tpmax(r) for r in grp); tmin = min(tpmin(r) for r in grp)
    over = [r['file'] for r in grp if tpmax(r) > -1.0]
    over8 = [r['file'] for r in grp if r['tp_dbtp'].get('8', 0) > -1.0]
    spk = [r['sample_peak_dbfs'] for r in grp]
    P(f'{name}: TP(any of 4x/8x/32x) range {tmin:.4f} .. {tmax:.4f} dBTP; files with any-meter TP > -1.000: {len(over)}/{len(grp)}; with 8x TP > -1.000: {len(over8)}; sample-peak range {min(spk):.4f} .. {max(spk):.4f} dBFS')
P('README(SE) claim: distribution -0.949 .. -1.048 dBTP (3 meters); loop-ready -0.996 .. -1.002 dBTP; Album README: -1.00 .. -1.83 dBTP')
P('\nper-file (SE distribution): file | sample peak | TP4 | TP8 | TP32 | spread(4..32) | within README -0.949..-1.048?')
for r in sfx:
    t = r['tp_dbtp']; sp = max(t.values()) - min(t.values())
    inr = (-1.048 <= min(t.values())) and (max(t.values()) <= -0.949)
    P(f"{r['file'][:55]:55s} {r['sample_peak_dbfs']:9.4f} {t['4']:9.4f} {t['8']:9.4f} {t.get('32', float('nan')):9.4f} {sp:7.4f} {'Y' if inr else 'NO'}")
P('\nper-file (loop-ready):')
for r in lp:
    t = r['tp_dbtp']
    P(f"{r['file'][-60:]:60s} sp={r['sample_peak_dbfs']:.4f} tp4={t['4']:.4f} tp8={t['8']:.4f} tp32={t.get('32', float('nan')):.4f} inR={-1.002 <= min(t.values()) and max(t.values()) <= -0.996}")
P('\nper-file (album):')
for r in al:
    t = r['tp_dbtp']
    P(f"{r['file']:55s} sp={r['sample_peak_dbfs']:.4f} tp4={t['4']:.4f} tp8={t['8']:.4f} tp32={t.get('32', float('nan'))}")

P('\n=== C. LOUDNESS vs README / catalog ===')
mm = [r['ebur']['maxM'] for r in sfx]
P(f'SE 43 distribution: max momentary (400ms) range {min(mm):.3f} .. {max(mm):.3f} LUFS (README: -28.4 .. -5.4)')
im = [r['ebur']['I'] for r in al]
P(f'Album 7 WAV: ebur128 integrated {min(im)} .. {max(im)} LUFS (1 decimal) (README loudnorm: -13.98 .. -14.35)')

P('\n=== D. CATALOG vs ACTUAL FILE (43 sfx; zip member path = <group>/<basename of distribution>) ===')
byname = {r['file']: r for r in se}
n_ok_dur = n_ok_sha = 0; durdiff = []
for c in cat:
    if c['kind'] != 'sfx': continue
    base = os.path.basename(c['distribution'].replace('\\', '/'))
    key = f"{c['group']}/{base}"
    r = byname.get(key)
    if r is None:
        P('MISSING in zip:', key); continue
    d = float(c['duration_s']) - r['dur_s']
    durdiff.append((abs(d), key))
    if abs(d) <= 0.0006: n_ok_dur += 1
    if c['dist_sha256'] == r['sha256']: n_ok_sha += 1
    else: P('SHA MISMATCH', key)
P(f'catalog duration_s vs frames/sr: within 0.6 ms: {n_ok_dur}/43; max |diff| = {max(durdiff)[0]*1000:.3f} ms ({max(durdiff)[1]})')
P(f'catalog dist_sha256 == zip member sha256: {n_ok_sha}/43')
# loop-ready rows
for c in cat:
    if c.get('loop_ready_zip_path'):
        key = c['loop_ready_zip_path'].replace('\\', '/')
        r = byname.get(key)
        ok_s = int(c['loop_ready_samples']) == r['frames'] if r else None
        ok_h = c['loop_ready_sha256'] == r['sha256'] if r else None
        P(f"loop {key[-70:]}: catalog samples {c['loop_ready_samples']} vs actual {r['frames'] if r else None} -> {ok_s}; sha {ok_h}; bpm {c['loop_bpm']} bars {c['loop_bars']}")
        exp = round(float(c['loop_bars']) * 4 * 60 * 48000 / float(c['loop_bpm']))
        P(f"      expected N = floor(bars*4*60*48000/bpm+0.5) = {exp}  match={exp == r['frames']}")
# music rows
for c in cat:
    if c['kind'] != 'music': continue
    key = 'WAV/' + os.path.basename(c['album_v1_1_wav'].replace('\\', '/'))
    r = byname.get(key) or next((a for a in al if a['file'] == key), None)
    if r:
        P(f"music {c['id']:28s} dur cat {c['duration_s']} act {r['dur_s']:.3f} | album sha eq {c['album_v1_1_wav_sha256'] == r['sha256']} | cat tp_full {c['album_v1_1_tp_full']} own tp4 {r['tp_dbtp']['4']:.4f} tp8 {r['tp_dbtp']['8']:.4f} | cat lufs {c['album_v1_1_lufs']} ebur I {r['ebur']['I']}")

P('\n=== E. CLIPPING / DC / EDGES / STEREO ===')
P('file | full-scale code hits | max flat run>=0.5FS | DC mean dBFS (L,R) | lead exact-zero ms | lead<-80 ms | trail exact-zero ms | trail<-80 ms | last10ms RMS dBFS | first sample abs | L/R corr | max|L-R|')
allr = se + al
for r in allr:
    e = r['edges']; c = r['code']
    P(f"{r['file'][-52:]:52s} fs={c['full_scale_hits']} flat={c['max_flat_run_ge_half_fs']} atmax={c['n_at_max_code']}/{c['max_run_at_max_code']} dc=({r['dc_mean_dbfs'][0]:.1f},{r['dc_mean_dbfs'][1]:.1f}) "
      f"lz={e['lead_exact_zero_ms']:.2f} l80={e['lead_below_80dBFS_ms']:.2f} tz={e['trail_exact_zero_ms']:.1f} t80={e['trail_below_80dBFS_ms']:.0f} l10={e['last10ms_rms_dbfs']:.1f} fsa={e['first_sample_abs']:.5f} corr={r.get('lr_corr', float('nan')):.4f} dLR={r.get('lr_max_abs_diff', float('nan')):.5f}")

P('\n=== F. LOOP-READY SEAM (descriptive; whether a click is audible is NOT decided here) ===')
for r in lp:
    s = r['seam']
    P(f"{r['file'][-62:]:62s} jump={s['jump']:.5f} (pct of in-file steps <= jump: {s['jump_pct_of_instep']:.1f}%) in-file step p50/p99/max={s['instep_p50']:.5f}/{s['instep_p99']:.5f}/{s['instep_max']:.5f}")
    P(f"      seam curvature d2 (wrap, two positions)={s['seam_curv']:.5f}/{s['seam_curv2']:.5f}  in-file d2 p99/max={s['curv_p99']:.5f}/{s['curv_max']:.5f}  seam HF energy vs file-median 2ms window={s['seam_hf_vs_median_db']:.1f} dB, vs file-max window={s['seam_hf_vs_max_db']:.1f} dB")
