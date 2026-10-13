#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF1005 Y card: numbers re-computed from the *printed* tables of Alon (2015) (Tables 4.1, 4.2, 4.3, 6.2-6.12; pages given in the report).
Only derived statistics are written (no table transcription). Input = text extracted from the local PDF into scratch (not committed)."""
import re, json, sys, statistics as st
sys.stdout.reconfigure(encoding='utf-8')
Y = 'E:/Tsuki-project/_scratch/wf1005/Y'
t = open(f'{Y}/alon_pages.txt', encoding='utf-8').read()
parts = re.split(r'\n=====PDFPAGE (\d+)=====\n', t)
d = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}
NOTE = re.compile(r'^[A-G][#b]?\d$')


def parse_modes(pg):
    L = [l.strip() for l in d[pg].split('\n') if l.strip()]
    rows = []; i = 0
    while i < len(L):
        if NOTE.match(L[i]):
            vals = []; j = i + 1
            while j < len(L) and len(vals) < 12:
                try: vals.append(float(L[j])); j += 1
                except ValueError: break
            if len(vals) == 12:
                rows.append(dict(note=L[i], mag=vals[0:4], f=vals[4:8], ratio=vals[8:12])); i = j; continue
        i += 1
    return rows


def parse_t60(pg):
    L = [l.strip() for l in d[pg].split('\n') if l.strip()]
    out = []; i = 0
    while i < len(L):
        if NOTE.match(L[i]):
            vals = []; flags = []; j = i + 1
            while j < len(L) and len(vals) < 3:
                s = L[j]
                try:
                    vals.append(float(s.rstrip('*'))); flags.append(s.endswith('*')); j += 1
                except ValueError: break
            if len(vals) == 3: out.append((L[i], vals, flags))
            i = j; continue
        i += 1
    return out


mode_pages = [('Table 4.1', 78, 'p.78'), ('Table 6.2', 138, 'p.138'), ('Table 6.3', 139, 'p.139'),
              ('Table 6.4', 140, 'p.140'), ('Table 6.5', 141, 'p.141'), ('Table 6.6', 142, 'p.142')]
t60_pg = parse_t60(143), parse_t60(144), parse_t60(145)
t60_tabs = {'Table 6.7': t60_pg[0][:8], 'Table 6.8': t60_pg[0][8:16], 'Table 6.9': t60_pg[1][:8], 'Table 6.10': t60_pg[1][8:16],
            'Table 6.11': t60_pg[2][:9], 'Table 6.12': t60_pg[2][9:18]}
pair = {'Table 4.1': 'Table 6.9', 'Table 6.2': 'Table 6.7', 'Table 6.3': 'Table 6.8', 'Table 6.4': 'Table 6.10',
        'Table 6.5': 'Table 6.11', 'Table 6.6': 'Table 6.12'}
out = {}
n_notes = 0; c123 = []; c124 = []; other = []
r2s = []; r3s = []; r4s = []
per_mode_t60 = {1: [], 2: [], 3: []}
t60_rel2 = []; t60_rel3 = []
all_modes = {}
for tab, pg, pgs in mode_pages:
    rows = parse_modes(pg)
    tt = t60_tabs[pair[tab]]
    assert len(rows) == len(tt), (tab, len(rows), len(tt))
    for row, (nn, tv, fl) in zip(rows, tt):
        assert row['note'] == nn, (tab, row['note'], nn)
        n_notes += 1
        order = sorted(range(3), key=lambda k: row['f'][k])
        f3 = [row['f'][k] for k in order]
        r = [x / f3[0] for x in f3]
        tag = None
        if abs(r[1] - 2) < 0.1 and abs(r[2] - 3) < 0.1: tag = '123'; c123.append((tab, nn)); r2s.append(r[1]); r3s.append(r[2])
        elif abs(r[1] - 2) < 0.1 and abs(r[2] - 4) < 0.15: tag = '124'; c124.append((tab, nn)); r4s.append(r[2])
        else: other.append((tab, nn, [round(x, 2) for x in r]))
        # per-mode T60 by harmonic number (only when top-3 is a clean 1:2:3 family), skipping asterisk-flagged values
        if tag == '123':
            for hn, k in zip((1, 2, 3), order):
                if not fl[k]: per_mode_t60[hn].append(tv[k])
            if not fl[order[1]] and not fl[order[0]]: t60_rel2.append(tv[order[1]] / tv[order[0]])
            if not fl[order[2]] and not fl[order[0]]: t60_rel3.append(tv[order[2]] / tv[order[0]])


def S(a):
    return dict(n=len(a), mean=round(st.mean(a), 3), median=round(st.median(a), 3), min=round(min(a), 3), max=round(max(a), 3))


out['n_note_fields'] = n_notes
out['top3_is_1_2_3'] = len(c123); out['top3_is_1_2_4'] = len(c124); out['top3_other'] = len(other); out['top3_other_list'] = other
out['ratio2_of_123'] = S(r2s); out['ratio3_of_123'] = S(r3s); out['ratio4_of_124'] = S(r4s)
out['t60_by_harmonic_in_123_notes'] = {k: S(v) for k, v in per_mode_t60.items()}
out['t60_2nd_over_1st'] = S(t60_rel2); out['t60_3rd_over_1st'] = S(t60_rel3)
# Table 4.2 recomputation (undamped, pre-tuned instruments; the single flagged 8.9* value excluded as the paper did) and note groups
def midi(n):
    m = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[n[0]]; i = 1
    if n[i] in '#b': m += 1 if n[i] == '#' else -1; i += 1
    return 12 * (int(n[i:]) + 1) + m
inst = {'Inst1': 'Table 6.7', 'Inst2': 'Table 6.8', 'Inst3(pre)': 'Table 6.9', 'Inst4(pre)': 'Table 6.11'}
rec = {}
allv = []; grp = {'low': [], 'mid': [], 'high': []}
for nm, tb in inst.items():
    vals = []
    for (nn, tv, fl) in t60_tabs[tb]:
        for v, f in zip(tv, fl):
            if f: continue
            vals.append(v); allv.append(v)
            m = midi(nn)
            g = 'low' if m <= midi('B3') else ('mid' if m <= midi('E4') else 'high')
            grp[g].append(v)
    rec[nm] = dict(mean=round(st.mean(vals), 2), sd=round(st.stdev(vals), 2), min=min(vals), max=max(vals), n=len(vals))
rec['all'] = dict(mean=round(st.mean(allv), 2), sd=round(st.stdev(allv), 2), min=min(allv), max=max(allv), n=len(allv))
for g, v in grp.items(): rec[g] = dict(mean=round(st.mean(v), 2), sd=round(st.stdev(v), 2), min=min(v), max=max(v), n=len(v))
out['table_4_2_recomputed'] = rec
# Pitch range actually measured (Table 3.1, p.68): B2 .. C5
out['pitch_range_measured'] = 'B2 (123.5 Hz) .. C5 (523.3 Hz)'
json.dump(out, open(f'{Y}/paper_stats.json', 'w'), indent=1)
print(json.dumps(out, indent=1, ensure_ascii=False))
