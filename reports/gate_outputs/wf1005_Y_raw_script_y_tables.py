import sys, json
sys.path.insert(0,'E:/Tsuki-project/_scratch/wf1005/Y/scripts')
sys.stdout.reconfigure(encoding='utf-8')
from y_lib import CANT_RATIO
Y='E:/Tsuki-project/_scratch/wf1005/Y'
R=json.load(open(f'{Y}/measure_stage2.json',encoding='utf-8'))
print('anchor ratios',[round(x,4) for x in CANT_RATIO])
print('\n== A. modal ratios (dry free render, narrow-band measured; model from dump-modes) vs cantilever anchor ==')
for k,r in R.items():
    row=[]
    for m in r['modes_free']:
        if 'ratio_meas' not in m: continue
        i=m['i']
        mod=r['model'][i]['ratio']
        anc=CANT_RATIO[i] if i<len(CANT_RATIO) else None
        row.append(f"m{i+1}: meas {m['ratio_meas']:.4f} model {mod:.4f} anchor {anc:.4f} (meas-anc {100*(m['ratio_meas']/anc-1):+.3f}% model-anc {100*(mod/anc-1):+.3f}%) rel-peak {m['rel_peak_db']:+.1f}dB")
    print(k.split('__')[1],'|',' ; '.join(row))
print('\n== B. paper-style frame (6 ms, Hamming2048/FFT32768, sidelobes suppressed): top4 (Hz,dB) and ratios of the three strongest over the lowest of them ==')
for k,r in R.items():
    print(k.split('__')[1],[(round(f,1),round(d,1)) for f,d in r['paper_frame_top4']],[round(x,3) for x in r['paper_frame_top3_ratios_over_lowest']])
print('\n== C. T60 fundamental ==')
for k,r in R.items():
    t=r['t60_f1']; print(f"{k.split('__')[1]:24s} note {r['note']:3s} model {t['model']:.4g} free_env {t['free_env']:.4g} free_sch {t['free_schroeder']:.4g} | as-authored(slope) {t['dry_as_authored_env']:.4g} | product(slope) {t['product_env']:.4g}")
print('\n== D. f0: engine (dry) vs product (cents vs model f1; model f1 vs ET) ==')
for k,r in R.items():
    d=r['f0_dry_noglide_or_dry']; p=r['f0_product']; a=r['f0_dry_as_authored']
    fm=lambda v: 'n/a' if v is None else f'{v:+.2f}'
    print(f"{k.split('__')[1]:24s} model-ET {r['model_f1_cents_vs_ET']:+.3f}c | dry E1 {fm(d['E1_cents_vs_model'])} E2/3% {fm(d['E2_bw3_cents_vs_model'])} E2/6% {fm(d['E2_bw6_cents_vs_model'])} | product E1 {fm(p['E1_cents_vs_model'])} E2/3% {fm(p['E2_bw3_cents_vs_model'])} E2/6% {fm(p['E2_bw6_cents_vs_model'])} | dry-as-authored E1 {fm(a['E1_cents_vs_model'])} E2/3% {fm(a['E2_bw3_cents_vs_model'])} glide={bool(r['glide'])}")
print('\n== E. beating ==')
for k,r in R.items():
    b=r['beating']; print(k.split('__')[1],'min pair spacing Hz',round(r['min_pair_spacing_hz'],1),'| dry-free minima',b['free_minima'],'spectrogram-bin minima',b['free_spectrogram_bin_minima'],'| product minima',b['product_minima'],'rate',None if b['product_rate_hz'] is None else round(b['product_rate_hz'],1))
