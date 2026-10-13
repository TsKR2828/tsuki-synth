#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WF1005 Y card: run facts (tool versions, binary hashes, renderer-equality checks, read-only proof)."""
import sys, os, json, hashlib, subprocess, glob, platform
sys.path.insert(0, 'E:/Tsuki-project/_scratch/wf1005/Y/scripts')
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np, scipy, soundfile
import fitz
from y_lib import dump_modes

Y = 'E:/Tsuki-project/_scratch/wf1005/Y'
REPO = 'E:/Tsuki-project/tsuki-synth'
BS = chr(92)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


print('python', platform.python_version(), '| numpy', np.__version__, '| scipy', scipy.__version__, '| soundfile', soundfile.__version__, '| PyMuPDF', fitz.__doc__.split(':')[0])
for p in ('bin/TsukiSynthCLI_current.exe', 'bin/TsukiSynthCLI_9123db8f_build20260915.exe'):
    print('sha256', sha(f'{Y}/{p}'), p)
print('build CLI sha256', sha(f'{REPO}/build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe'), '(build/TsukiSynthCLI_artefacts/Release/TsukiSynthCLI.exe; copied unchanged into scratch bin/)')
pdf = 'E:/Tsuki-project/_tools/papers/Alon2015_York_MSc_handpan.pdf'
d = fitz.open(pdf)
print('paper', pdf, 'bytes', os.path.getsize(pdf), 'pages', d.page_count, 'sha256', sha(pdf), 'md5', hashlib.md5(open(pdf, 'rb').read()).hexdigest())
# renderer equality on the 28 dry renders
same = 0; n = 0
for f in sorted(glob.glob(f'{Y}/render_cur/*.wav')):
    b = os.path.basename(f)
    n += 1
    if open(f, 'rb').read() == open(f'{Y}/render_arch/{b}', 'rb').read(): same += 1
print(f'dry renders: current CLI vs archived product renderer 9123db8f byte-identical {same}/{n}')
same = 0; n = 0
for f in sorted(glob.glob(f'{Y}/render_fx_cur/*.wav')):
    b = os.path.basename(f)
    n += 1
    if open(f, 'rb').read() == open(f'{Y}/render_fx_arch/{b}', 'rb').read(): same += 1
print(f'fx-on renders: current CLI vs archived renderer byte-identical {same}/{n}')
# dump-modes equality for the 12 scores
IDX = json.load(open(f'{Y}/scores/index.json', encoding='utf-8'))
eq = 0
for key, info in IDX.items():
    sp = f"{REPO}/{info['src_score'].replace(BS, '/')}"
    a = dump_modes(f'{Y}/bin/TsukiSynthCLI_current.exe', sp, REPO)['events'][0]['partials']
    b = dump_modes(f'{Y}/bin/TsukiSynthCLI_9123db8f_build20260915.exe', sp, REPO)['events'][0]['partials']
    eq += json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
print(f'dump-modes partial tables, current vs archived renderer identical {eq}/{len(IDX)}')
# determinism: render the same dry score twice with the current CLI
key = 'restraint__Restraint_Bolt_Click'
os.makedirs(f'{Y}/render_det', exist_ok=True)
for i in (1, 2):
    subprocess.run([f'{Y}/bin/TsukiSynthCLI_current.exe', f'{Y}/scores/{key}__dry.score.json', '--output', f'{Y}/render_det/r{i}'], capture_output=True)
print('determinism (Bolt Click dry rendered twice, byte-identical):', open(f'{Y}/render_det/r1/{key}__dry.wav', 'rb').read() == open(f'{Y}/render_det/r2/{key}__dry.wav', 'rb').read())
