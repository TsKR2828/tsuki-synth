import sys, json
sys.path.insert(0,'E:/Tsuki-project/_scratch/wf1005/Y/scripts')
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from y_lib import *
Y='E:/Tsuki-project/_scratch/wf1005/Y'; REPO='E:/Tsuki-project/tsuki-synth'; CLI=f'{Y}/bin/TsukiSynthCLI_current.exe'
IDX=json.load(open(f'{Y}/scores/index.json',encoding='utf-8')); BS=chr(92)
out={}
for key,info in IDX.items():
    sp=f"{REPO}/{info['src_score'].replace(BS,'/')}"
    dm=dump_modes(CLI,sp,REPO)['events'][0]['partials']; f1=dm[0]['freq']
    xp,sr=read_mono(f'{Y}/x/se/{key}.wav')
    src=json.load(open(sp,encoding='utf-8')); nxt=src['events'][1]['time'] if len(src['events'])>1 else None
    win_end=min((nxt-0.01) if nxt else min(len(xp)/sr,0.8),1.2)
    pk=peaks_long(xp,sr,0.003,win_end,floor_db=-70); top=pk[0][1]
    c1=[p for p in pk if abs(p[0]/f1-1)<0.03]
    row={'f1_peak_hz':c1[0][0] if c1 else None,'modes':[]}
    for i in range(1,len(dm)):
        c=[p for p in pk if abs(p[0]/dm[i]['freq']-1)<0.03]
        if c and c1:
            lvl=c[0][1]-c1[0][1]
            row['modes'].append({'i':i+1,'ratio_meas':c[0][0]/c1[0][0],'model_ratio':dm[i]['freq']/f1,'err_pct_vs_model':100*(c[0][0]/c1[0][0]/(dm[i]['freq']/f1)-1),'level_db_vs_f1':lvl})
    out[key]=row
    print(key.split('__')[1],[(m['i'],round(m['ratio_meas'],3),f"{m['err_pct_vs_model']:+.2f}%",f"{m['level_db_vs_f1']:+.0f}dB") for m in row['modes'] if m['level_db_vs_f1']>-50])
json.dump(out,open(f'{Y}/product_ratio.json','w'),indent=1)
