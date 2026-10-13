#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Builds the per-product markdown tables for the Y report from the raw JSON (so no number is transcribed by hand)."""
import sys, json
sys.path.insert(0, 'E:/Tsuki-project/_scratch/wf1005/Y/scripts')
sys.stdout.reconfigure(encoding='utf-8')
from y_lib import CANT_RATIO, note_midi
Y = 'E:/Tsuki-project/_scratch/wf1005/Y'
R = json.load(open(f'{Y}/measure_stage2.json', encoding='utf-8'))
D60 = json.load(open(f'{Y}/direct60.json'))
BUMP = json.load(open(f'{Y}/extras.json'))['bumps']
PR = json.load(open(f'{Y}/product_ratio.json'))
NAME = {'akashic__Akashic_Light_Tap': 'Akashic Light Tap', 'clockwork__Clockwork_Bell_Strike': 'Clockwork Bell Strike',
        'clockwork__Clockwork_Gear_Click': 'Clockwork Gear Click', 'forest__Forest_Acorn_Tap': 'Forest Acorn Tap',
        'ocean__Ocean_Droplet_Tap': 'Ocean Droplet Tap', 'ocean__Ocean_Bubble_Pop': 'Ocean Bubble Pop',
        'ocean__Ocean_Bubble_Pop_Deep': 'Ocean Bubble Pop Deep', 'rabbit__Rabbit_Ding': 'Rabbit Ding',
        'rabbit__Rabbit_Ding_Angry': 'Rabbit Ding Angry', 'rabbit__Rabbit_Carrot_Button': 'Rabbit Carrot Button',
        'restraint__Restraint_Bolt_Click': 'Restraint Bolt Click', 'akashic__Library_Opening_Bell': 'Library Opening Bell (D4，第 1 個音)'}
MAT = lambda r: r['material']


def fmt(v, nd=2, sign=False):
    if v is None: return '—'
    return f'{v:+.{nd}f}' if sign else f'{v:.{nd}f}'


print('### TABLE_BASE')
print('| 商品 | 音名 | 引擎／材質 | 事件長度 → note-off（0.9×） | 模型模態數 | 備註 |')
print('|---|---|---|---|---|---|')
for k, r in R.items():
    gl = f"有滑音 {r['glide']['from_note']}→{r['note']}／{r['glide']['duration_ms']} ms" if r['glide'] else ''
    ob = f"{r['n_events_src']} 個事件，只量第 1 個" if r['n_events_src'] > 1 else ''
    print(f"| {NAME[k]} | {r['note']} ({r['f_et']:.1f} Hz) | {r['engine']}／{MAT(r)} | {r['duration_s']} s → {0.9*r['duration_s']:.3f} s | {len(r['model'])} | {'；'.join(x for x in (gl, ob) if x)} |")

print('\n### TABLE_A (模態比)')
print('| 商品 | 乾聲：第二模態／基頻（懸臂梁錨點 6.2669） | 乾聲：第三模態／基頻（錨點 17.5475） | 論文式單幀（起音後 6 ms）前三強峰是不是模態 | 成品 WAV：第二模態比（Q 法重量） | 2×、3× 附近（乾聲／成品） |')
print('|---|---|---|---|---|---|')
frame = {}
for k, r in R.items():
    f1 = r['model'][0]['f']
    labs = []
    for f, d in r['paper_frame_top4'][:3]:
        mm = [i for i, m in enumerate(r['model']) if abs(f / m['f'] - 1) < 0.01]
        labs.append(f"{'模態' + str(mm[0] + 1) if mm else '非模態'}({d:+.0f})")
    m2 = next((m for m in r['modes_free'] if m['i'] == 1 and 'ratio_meas' in m), None)
    m3 = next((m for m in r['modes_free'] if m['i'] == 2 and 'ratio_meas' in m), None)

    def cell(m, anc):
        if m is None: return '無（模型只有 2 個模態或超過 0.42 fs）'
        ok = m['win_ms'] >= 6 and m['rel_peak_db'] >= -40
        e = 100 * (m['ratio_meas'] / anc - 1)
        return f"{m['ratio_meas']:.4f}（{e:+.3f}%）" if ok else f"（{m['ratio_meas']:.2f}，{m['rel_peak_db']:.0f} dB／窗 {m['win_ms']:.0f} ms，量測器解析度不足，不計）"
    p = PR[k]['modes']
    p2 = next((x for x in p if x['i'] == 2), None)
    pcell = '—' if p2 is None or p2['level_db_vs_f1'] < -50 else f"{p2['ratio_meas']:.3f}（{p2['err_pct_vs_model']:+.2f}%，{p2['level_db_vs_f1']:+.0f} dB）"
    b = BUMP[k]
    d2, d3 = b['dry_free']['2x_level_db'], b['dry_free']['3x_level_db']
    p2x, p3x = b['product']['2x_level_db'], b['product']['3x_level_db']
    fx = lambda v: '無(<−90)' if v is None else f'{v:.0f}'
    print(f"| {NAME[k]} | {cell(m2, CANT_RATIO[1])} | {cell(m3, CANT_RATIO[2])} | {'、'.join(labs)} | {pcell} | 2×：{fx(d2)}／{fx(p2x)}；3×：{fx(d3)}／{fx(p3x)} dB |")

print('\n### TABLE_T60')
print('| 商品 | 音名／論文音區 | 乾聲自由衰減基頻 T60（模型｜包絡法｜Schroeder 法，s） | 論文可比？ | 判定（論文範圍 0.87～5.9 s；基頻峰 1.2～4.2 s） | 出貨版乾聲實際衰到 −60 dB 的時間（s） | 成品 WAV 表觀 T60（斜率法，含殘響，s） |')
print('|---|---|---|---|---|---|---|')
paper_hi = 72
for k, r in R.items():
    t = r['t60_f1']; midi = r['midi']
    if midi < note_midi('B2'): grp = '低於 B2'
    elif midi <= note_midi('B3'): grp = '低音區 B2–B3'
    elif midi <= note_midi('E4'): grp = '中音區 C4–E4'
    elif midi <= note_midi('C5'): grp = '高音區 F4–C5'
    else: grp = f'高於 C5 {midi - paper_hi} 個半音'
    in_rng = midi <= paper_hi
    v = t['free_env']
    if in_rng:
        if 0.87 <= v <= 5.9: verdict = '符合（在範圍內）'
        elif v > 5.9: verdict = f'偏離：{v:.1f} s ＝ 論文最長 5.9 s 的 {v/5.9:.1f} 倍（不計缺陷，見 §4.2）'
        else: verdict = '偏離（低於範圍）'
    else:
        hard = '範圍內' if 0.87 <= v <= 5.9 else ('低於 0.87' if v < 0.87 else '高於 5.9')
        verdict = f'無法判定：音高超出論文量測音域；（硬比：{hard}，不計）'
    d = D60[k]['as_authored_dry']['t_minus60']
    print(f"| {NAME[k]} | {r['note']}／{grp} | {t['model']:.4g}｜{t['free_env']:.4g}｜{t['free_schroeder']:.4g} | {'可' if in_rng else '否'} | {verdict} | {d:.3f} | {t['product_env']:.3g} |")

print('\n### TABLE_F0')
print('| 商品 | 模型基頻 − 平均律 (c) | 乾聲 E1／E2(3%)／E2(6%)（c） | 成品 WAV E1／E2(3%)／E2(6%)（c） | 成品三值最大差（c） | 判定 |')
print('|---|---|---|---|---|---|')
SIX = {'akashic__Akashic_Light_Tap', 'clockwork__Clockwork_Bell_Strike', 'clockwork__Clockwork_Gear_Click', 'ocean__Ocean_Bubble_Pop', 'ocean__Ocean_Bubble_Pop_Deep', 'rabbit__Rabbit_Carrot_Button'}
for k, r in R.items():
    d = r['f0_dry_noglide_or_dry']; p = r['f0_product']
    pv = [p['E1_cents_vs_model'], p['E2_bw3_cents_vs_model'], p['E2_bw6_cents_vs_model']]
    pv2 = [x for x in pv if x is not None]
    spread = max(pv2) - min(pv2)
    dv = [d['E1_cents_vs_model'], d['E2_bw3_cents_vs_model'], d['E2_bw6_cents_vs_model']]
    dmax = max(abs(x) for x in dv)
    tag = 'WF1004 標「無法判定」' if k in SIX else 'WF1004 標「符合」'
    if k in SIX:
        if r['glide']:
            verdict = f'引擎層符合（最大 {dmax:.2f} c）；成品層：設計滑音（{r["glide"]["duration_ms"]} ms）破壞單頻假設，無法判定'
        else:
            verdict = f'引擎層符合（最大 {dmax:.2f} c）；成品層估計器自己差 {spread:.1f} c，仍無法判定'
    else:
        verdict = f'引擎層符合（最大 {dmax:.2f} c）；成品層三值差 {spread:.1f} c'
    print(f"| {NAME[k]}（{tag}） | {r['model_f1_cents_vs_ET']:+.3f} | {dv[0]:+.2f}／{dv[1]:+.2f}／{dv[2]:+.2f} | {pv[0]:+.2f}／{pv[1]:+.2f}／{pv[2]:+.2f} | {spread:.1f} | {verdict} |")

print('\n### TABLE_BEAT')
print('| 商品 | 模型內最近的兩個模態相距（Hz） | 乾聲基頻包絡谷數（Hilbert／論文式頻譜格） | 出貨版乾聲（含 note-off） | 成品 WAV（含殘響）谷數／速率 |')
print('|---|---|---|---|---|')
for k, r in R.items():
    b = r['beating']
    rate = '—' if b['product_rate_hz'] is None else f"{b['product_rate_hz']:.1f} Hz"
    print(f"| {NAME[k]} | {r['min_pair_spacing_hz']:.0f} | {b['free_minima']}／{b['free_spectrogram_bin_minima']} | {b['dry_as_authored_minima']} | {b['product_minima']}／{rate} |")

print('\n### TABLE_P2')
print('| 商品 | 模型：第二模態 T60 ÷ 基頻 T60 | 乾聲量測 | 第二模態峰值電平相對基頻（乾聲，dB） |')
print('|---|---|---|---|')
for k, r in R.items():
    m = r['model']; mf = r['modes_free']
    a = m[1]['t60'] / m[0]['t60']; b = mf[1]['t60_env'] / mf[0]['t60_env']
    print(f"| {NAME[k]} | {a:.3f} | {b:.3f} | {mf[1].get('rel_peak_db', float('nan')):+.1f} |")
