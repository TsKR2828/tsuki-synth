import sys, json
sys.path.insert(0,'E:/Tsuki-project/_scratch/wf1005/Y/scripts')
sys.stdout.reconfigure(encoding='utf-8')
Y='E:/Tsuki-project/_scratch/wf1005/Y'
R=json.load(open(f'{Y}/measure_stage2.json',encoding='utf-8'))
print('paper-style single frame (6 ms after onset; Hamming 2048; FFT 32768; fs 48 kHz => bin 23.4 Hz; window-sidelobe peaks within 4 bins of a stronger peak removed)')
print('each peak: Hz, dB re strongest, and whether it is a model mode (within 1 % of a dump-modes partial) or not')
for k,r in R.items():
    f1=r['model'][0]['f']; out=[]
    for f,d in r['paper_frame_top4']:
        mm=[m for m in r['model'] if abs(f/m['f']-1)<0.01]
        lab=f"mode{r['model'].index(mm[0])+1}" if mm else 'non-mode'
        out.append(f"{f:.1f}Hz {d:+.1f}dB {lab}")
    modes_ok=[x for x in out if 'non-mode' not in x]
    print(f"{k.split('__')[1]:22s} | "+' ; '.join(out))
