#!/usr/bin/env python3
# WF1005 Y card: build DRY scratch score copies (read-only on products/scores). Writes only under scratch Y/scores.
import json, os, sys, subprocess, copy
sys.stdout.reconfigure(encoding='utf-8')
REPO = 'E:/Tsuki-project/tsuki-synth'
Y = 'E:/Tsuki-project/_scratch/wf1005/Y'
BS = chr(92)
CLI = f'{Y}/bin/TsukiSynthCLI_current.exe'
CAT = json.load(open(f'{REPO}/exports/products/clean_batch2_v1_1_candidate/catalog_v1_1.json', encoding='utf-8'))
TARGETS = ['akashic__Akashic_Light_Tap', 'clockwork__Clockwork_Bell_Strike', 'clockwork__Clockwork_Gear_Click',
           'forest__Forest_Acorn_Tap', 'ocean__Ocean_Droplet_Tap', 'ocean__Ocean_Bubble_Pop',
           'ocean__Ocean_Bubble_Pop_Deep', 'rabbit__Rabbit_Ding', 'rabbit__Rabbit_Ding_Angry',
           'rabbit__Rabbit_Carrot_Button', 'restraint__Restraint_Bolt_Click', 'akashic__Library_Opening_Bell']
os.makedirs(f'{Y}/scores', exist_ok=True)
index = {}
for key in TARGETS:
    c = next(r for r in CAT if r['kind'] == 'sfx' and r['distribution'].replace(BS, '/').endswith(key + '.wav'))
    sp = f"{REPO}/{c['score'].replace(BS, '/')}"
    sc = json.load(open(sp, encoding='utf-8'))
    ev0 = sc['events'][0]
    dm = json.loads(subprocess.run([CLI, '--dump-modes', sp], capture_output=True, text=True, cwd=REPO).stdout)
    part = dm['events'][0]['partials']
    max_t60 = max(p['decay'] for p in part)
    base = copy.deepcopy(sc)
    base['events'] = [copy.deepcopy(ev0)]
    base['global']['effects'] = {'reverb': {'decay': 2.0, 'wet': 0.0},
                                 'delay': {'time_ms': 0, 'feedback': 0.0, 'wet': 0.0},
                                 'wall': {'distance_m': 0.0, 'material': 'wood'},
                                 'distortion': {'type': 'overdrive', 'drive': 0.0, 'instability': 0.0, 'wet': 0.0}}
    base['export'] = {'filename': key, 'format': 'wav', 'bit_depth': 24, 'normalize': False, 'tail_silence_ms': 200}
    base['meta'] = dict(base.get('meta', {})); base['meta']['title'] = key; base['meta']['id'] = key.lower()
    variants = {'dry': base}
    free = copy.deepcopy(base)
    free['events'][0]['duration'] = float(int(max_t60 / 0.9) + 2)
    variants['free'] = free
    if 'glide' in ev0:
        ng = copy.deepcopy(free); del ng['events'][0]['glide']; variants['free_noglide'] = ng
        ng2 = copy.deepcopy(base); del ng2['events'][0]['glide']; variants['dry_noglide'] = ng2
    for v, s in variants.items():
        s['meta']['id'] = (key + '_' + v).lower(); s['export']['filename'] = key + '__' + v
        fn = f'{Y}/scores/{key}__{v}.score.json'
        json.dump(s, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    index[key] = dict(src_score=c['score'], note=ev0['note'], engine=ev0['engine'], duration=ev0['duration'],
                      glide=ev0.get('glide'), n_events_src=len(sc['events']), max_t60_model=max_t60,
                      variants=list(variants), params=ev0['params'], velocity=ev0['velocity'])
    print(key, ev0['engine'], ev0['note'], 'dur', ev0['duration'], 'maxT60', round(max_t60, 3), 'variants', list(variants))
json.dump(index, open(f'{Y}/scores/index.json', 'w'), indent=1, ensure_ascii=False)
