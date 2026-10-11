import re, zipfile, json, os
from decimal import Decimal, ROUND_HALF_UP
CAND = 'E:/Tsuki-project/tsuki-synth/exports/products/clean_batch2_v1_1_candidate'
se = {r['file']: r for r in json.load(open('E:/Tsuki-project/_scratch/wf1004/Q/q_measure_se.json'))}
for zn in ('TsukiSynth_Worldview_SE_Pack_v1.1_candidate.zip', 'TsukiSynth_Worldview_SE_Pack_v1.1_candidate_FAB.zip'):
    z = zipfile.ZipFile(f'{CAND}/packages/{zn}')
    txt = z.read('README.txt').decode('utf-8')
    names = [i.filename for i in z.infolist()]
    rows = re.findall(r'^(\S+\.wav)  \|  ([\d.]+) s  \|  (\w+)', txt, re.M)
    miss = [n for n, _, _ in rows if n not in names]
    notin = [n for n in names if n.endswith('.wav') and not n.startswith('loop_ready/') and n not in [r[0] for r in rows]]
    bad = []
    for n, s, t in rows:
        fr = se[n]['frames'] / se[n]['sr']
        exact = (Decimal(se[n]['frames']) / Decimal(se[n]['sr'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if Decimal(s) != exact:
            bad.append((n, s, str(exact)))
    # loop table
    loops = re.findall(r'^\s+(.+?)\s+(\d+) BPM x (\d) bars\s+original\s+([\d.]+) s\s+loop-ready\s+([\d.]+) s', txt, re.M)
    print(zn, 'README file-list rows', len(rows), 'rows not in zip', miss, 'zip WAV(non-loop) not listed', notin, 'duration mismatches (once-rounded half-up, 2dp)', bad)
    print('  loop table rows', len(loops), loops[:2])
    lbad = []
    for name, bpm, bars, o, l in loops:
        # find files
        cand = [n for n in names if os.path.basename(n).startswith(name.replace(' ', '_') + '.wav') or name.replace(' ', '_') in os.path.basename(n)]
        orig = [n for n in cand if not n.startswith('loop_ready')]
        lr = [n for n in cand if n.startswith('loop_ready')]
        oo = (Decimal(se[orig[0]]['frames']) / Decimal(48000)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        ll = (Decimal(se[lr[0]]['frames']) / Decimal(48000)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        if Decimal(o) != oo or Decimal(l) != ll:
            lbad.append((name, o, str(oo), l, str(ll)))
    print('  loop table mismatches:', lbad)
    print('  members:', len(names), 'WAV:', sum(1 for n in names if n.endswith('.wav')))
    m = re.search(r'Measured true peak: (-?[\d.]+) to (-?[\d.]+) dBTP', txt); print('  README TP claim', m.groups() if m else None)
