import os, re, zipfile, json
CAND = 'E:/Tsuki-project/tsuki-synth/exports/products/clean_batch2_v1_1_candidate'
PATS = {'[TBD': r'\[TBD', 'TBD': r'TBD', '待月月': r'待月月', 'DRAFT/草稿': r'DRAFT|草稿|draft', 'CANDIDATE/候選': r'CANDIDATE|候選|候補|candidate',
        '非法律意見': r'非法律意見|not legal advice|法的助言ではありません', '未查證/unverified': r'未查證|未確認|unverified|not verified|NOT been checked|没有查证'}
tgt = {}
z = zipfile.ZipFile(f'{CAND}/packages/TsukiSynth_Worldview_SE_Pack_v1.1_candidate.zip')
for n in ('LICENSE.txt', 'README.txt'):
    tgt['SE_zip/' + n] = z.read(n).decode('utf-8')
z = zipfile.ZipFile(f'{CAND}/packages/TsukiSynth_Worldview_SE_Pack_v1.1_candidate_FAB.zip')
tgt['SE_FAB_zip/README.txt'] = z.read('README.txt').decode('utf-8')
z = zipfile.ZipFile(f'{CAND}/packages/TsukiSynth_Album_Vol1_v1.1_candidate.zip')
tgt['Album_zip/README.txt'] = z.read('README.txt').decode('utf-8')
for f in ('LICENSE_SE_PACK_v1_1.txt', 'LICENSE_ALBUM_v1_1.txt', 'LISTING_COPY_v1_1.md', 'PRODUCT_SHEET_v1_1.md', 'FAB_PLATFORM_NOTE.txt', 'DISTROKID_NOTES.md', 'CHANGES_v1_1.md', 'QA_REPORT.md', 'LISTENING_CHECKLIST.md', 'catalog_v1_1.csv'):
    tgt[f] = open(f'{CAND}/{f}', encoding='utf-8-sig').read()
print('file | ' + ' | '.join(PATS))
for k, t in tgt.items():
    print(k, '|', ' | '.join(str(len(re.findall(p, t))) for p in PATS.values()))
print('\n[TBD lines in LICENSE_SE_PACK_v1_1.txt (source) and in the shipped SE zip LICENSE.txt:')
for k in ('LICENSE_SE_PACK_v1_1.txt', 'SE_zip/LICENSE.txt'):
    for i, l in enumerate(tgt[k].split('\n'), 1):
        if 'TBD' in l:
            print(f'  {k}:{i}: {l.strip()[:150]}')
print('\n[TBD lines in LICENSE_ALBUM_v1_1.txt:')
for i, l in enumerate(tgt['LICENSE_ALBUM_v1_1.txt'].split('\n'), 1):
    if 'TBD' in l:
        print(f'  :{i}: {l.strip()[:130]}')
print('\nfirst 14 lines of shipped SE LICENSE.txt:')
print('\n'.join(tgt['SE_zip/LICENSE.txt'].split('\n')[:14]))
print('\nAlbum zip members:', [i.filename for i in z.infolist() if not i.filename.startswith(('WAV/', 'MP3/'))])
print('LICENSE-like file in album zip:', any('LICENSE' in i.filename.upper() for i in z.infolist()))
