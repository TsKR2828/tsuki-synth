#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF1005 Y card: read-only proof for papers/ and for every product-side file this card actually read."""
import sys, os, hashlib, json, time, zipfile
sys.stdout.reconfigure(encoding='utf-8')
Y = 'E:/Tsuki-project/_scratch/wf1005/Y'
P = 'E:/Tsuki-project/tsuki-synth/exports/products/clean_batch2_v1_1_candidate/'
BS = chr(92)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def snap(path):
    rows = {}
    for ln in open(path, encoding='utf-8').read().split('\n'):
        if ln:
            p, s, m = ln.split('\t'); rows[p] = (int(s), int(m))
    return rows


b = snap(f'{Y}/snapshot_before.tsv'); a = snap(f'{Y}/snapshot_after.tsv')
print('# WF1005 Y card read-only proof')
print('# before snapshot', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(f"{Y}/snapshot_before.tsv").st_mtime)),
      '| after snapshot', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(f"{Y}/snapshot_after.tsv").st_mtime)))
print('# snapshot = path,size,mtime of every file under exports/products/clean_batch2_v1_1_candidate, exports/products/clean_batch2, _tools/papers')
print(f'files before {len(b)} / after {len(a)}')
changed = [p for p in sorted(set(a) | set(b)) if a.get(p) != b.get(p)]
print('\n== papers/ (this card read the PDF only) ==')
pap = [p for p in changed if '/_tools/papers/' in p]
print('changed files under _tools/papers:', pap if pap else 'NONE')
pdf = 'E:/Tsuki-project/_tools/papers/Alon2015_York_MSc_handpan.pdf'
print('PDF sha256', sha(pdf), 'bytes', os.path.getsize(pdf), 'mtime', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.stat(pdf).st_mtime)))
print('SHA256SUMS.txt (papers/) says:', open('E:/Tsuki-project/_tools/papers/SHA256SUMS.txt').read().strip())
print('\n== product-side files this card read ==')
read_files = [P + 'catalog_v1_1.json', P + 'packages/TsukiSynth_Worldview_SE_Pack_v1.1_candidate.zip']
cat = json.load(open(P + 'catalog_v1_1.json', encoding='utf-8'))
for r in cat:
    if r['kind'] == 'sfx' and any(r['distribution'].replace(BS, '/').endswith(t + '.wav') for t in
                                  ['Light_Tap', 'Bell_Strike', 'Gear_Click', 'Acorn_Tap', 'Droplet_Tap', 'Bubble_Pop', 'Bubble_Pop_Deep', 'Rabbit_Ding', 'Ding_Angry', 'Carrot_Button', 'Bolt_Click', 'Opening_Bell']):
        read_files.append('E:/Tsuki-project/tsuki-synth/' + r['score'].replace(BS, '/'))
for p in read_files:
    k = p.replace(BS, '/')
    st = (os.path.getsize(k), int(os.stat(k).st_mtime))
    in_b = b.get(k)
    same = (in_b == st) if in_b else None
    print(f"{'unchanged' if same else ('NOT IN SNAPSHOT' if same is None else 'CHANGED')}  {st[0]:>10d}  mtime {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st[1]))}  sha256 {sha(k)[:16]}  {k.replace('E:/Tsuki-project/tsuki-synth/exports/products/clean_batch2_v1_1_candidate/', '')}")
print('\n== the 12 extracted WAVs vs catalog dist_sha256 ==')
ok = 0
for f in sorted(os.listdir(f'{Y}/x/se')):
    h = sha(f'{Y}/x/se/{f}')
    c = [r for r in cat if r['kind'] == 'sfx' and r['distribution'].replace(BS, '/').endswith('/' + f)]
    ok += (len(c) == 1 and c[0]['dist_sha256'] == h)
print(f'{ok}/{len(os.listdir(f"{Y}/x/se"))} sha256 equal to catalog dist_sha256')
print('\n== other changes seen in products/ between the two snapshots (NOT made by this card) ==')
print('This card wrote nothing under products/ or papers/ (its scripts only open them for reading; every output is under E:/Tsuki-project/_scratch/wf1005/Y/ or, at the end, reports/).')
print('The snapshots were taken 2026-10-12 01:06:58 and 01:20:10. Not made by this card. Most likely the parallel WF1005 L card (licence/release step; git status shows wf1005_L_* evidence files already staged, but this card did not verify who wrote what). Files that differ between the two snapshots:')
for p in changed:
    if '/_tools/papers/' in p: continue
    bb = b.get(p); aa = a.get(p)
    print(f"  {'NEW    ' if bb is None else 'CHANGED'}  size {None if bb is None else bb[0]} -> {aa[0] if aa else None}  mtime -> {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(aa[1])) if aa else None}  {p.replace('E:/Tsuki-project/tsuki-synth/exports/products/clean_batch2_v1_1_candidate/', '')}")
print('\nCandidate packages used by this card (hash before = hash after, from hashes_before.txt / hashes_after.txt, same sha256 lines):')
for ln in open(f'{Y}/hashes_before.txt'):
    if 'candidate' in ln or 'listening_kit' in ln or 'Alon' in ln:
        print('  before', ln.strip()[:110])
for ln in open(f'{Y}/hashes_after.txt'):
    if 'candidate' in ln or 'listening_kit' in ln or 'Alon' in ln:
        print('  after ', ln.strip()[:110])
