import sys, json
sys.path.insert(0,'E:/Tsuki-project/_scratch/wf1005/Y/scripts')
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from y_lib import *
Y='E:/Tsuki-project/_scratch/wf1005/Y'; REPO='E:/Tsuki-project/tsuki-synth'; CLI=f'{Y}/bin/TsukiSynthCLI_current.exe'
IDX=json.load(open(f'{Y}/scores/index.json',encoding='utf-8')); BS=chr(92)
out={}
def t_to(db,sr,lvl):
    ip=int(np.argmax(db)); seg=db[ip:]
    k=np.nonzero(seg<=seg[0]-lvl)[0]
    return (ip+k[0])/sr if len(k) else None
for key,info in IDX.items():
    sp=f"{REPO}/{info['src_score'].replace(BS,'/')}"
    dm=dump_modes(CLI,sp,REPO)['events'][0]['partials']; f1=dm[0]['freq']; t60=dm[0]['decay']
    xs,sr=read_mono(f'{Y}/render_cur/{key}__dry.wav')
    xb,_=read_mono(f"{Y}/render_cur/{key}__{'free_noglide' if info['glide'] else 'free'}.wav")
    r={}
    for lab,x in (('as_authored_dry',xs),('free',xb)):
        an=analytic_mode(x,sr,f1,t60); db=env_db(an,sr,1.0)
        r[lab]={'t_minus30':t_to(db,sr,30),'t_minus60':t_to(db,sr,60)}
    out[key]=r
    print(f"{key:36s} noteOff {0.9*info['duration']:.3f}s | as-authored: -30 dB at {r['as_authored_dry']['t_minus30']}  -60 dB at {r['as_authored_dry']['t_minus60']} | free: -60 dB at {r['free']['t_minus60']} (model T60 {t60:.3f})")
json.dump(out,open(f'{Y}/direct60.json','w'),indent=1)
# control for bump test: strongest peak near 1.5x and 2.5x f1 in product vs near 2x/3x
ctl={}
for key,info in IDX.items():
    sp=f"{REPO}/{info['src_score'].replace(BS,'/')}"
    dm=dump_modes(CLI,sp,REPO)['events'][0]['partials']; f1=dm[0]['freq']
    xp,sr=read_mono(f'{Y}/x/se/{key}.wav')
    src=json.load(open(sp,encoding='utf-8')); nxt=src['events'][1]['time'] if len(src['events'])>1 else None
    win_end=min((nxt-0.01) if nxt else min(len(xp)/sr,0.8),1.2)
    pk=peaks_long(xp,sr,0.003,win_end,floor_db=-90); top=pk[0][1]
    row={}
    for h in (1.5,2,2.5,3,3.5):
        c=[p for p in pk if abs(p[0]/(h*f1)-1)<0.03]
        row[str(h)]=(c[0][1]-top) if c else None
    ctl[key]=row
    print(key,{k:(round(v,1) if v is not None else None) for k,v in row.items()})
json.dump(ctl,open(f'{Y}/bump_control.json','w'),indent=1)
