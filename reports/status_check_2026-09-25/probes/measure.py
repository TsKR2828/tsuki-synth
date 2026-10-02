import json, os, re, subprocess, sys, glob
import soundfile as sf, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r"C:/Users/admin/Desktop/Claude/tsuki-synth/exports/products/clean_batch2"
FF = r"C:/Users/admin/Desktop/Tools/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe"
cat = json.load(open(os.path.join(ROOT, "catalog.json"), encoding="utf-8"))
def ebur(path):
    p = subprocess.run([FF,"-hide_banner","-nostats","-i",path,"-af","ebur128=peak=true+sample:framelog=quiet","-f","null","-"],capture_output=True,text=True,encoding='utf-8',errors='replace')
    err=p.stderr
    I=re.findall(r"I:\s+(-?[0-9.]+|-inf) LUFS",err)
    tp=re.findall(r"True peak:\s*\n\s*Peak:\s+(-?[0-9.]+|-inf) dBFS",err)
    sp=re.findall(r"Sample peak:\s*\n\s*Peak:\s+(-?[0-9.]+|-inf) dBFS",err)
    return (I[-1] if I else None, tp[-1] if tp else None, sp[-1] if sp else None)
out=[]
for r in cat:
    d=os.path.join(ROOT,r["distribution"].replace("\\","/"))
    info=sf.info(d)
    x,sr=sf.read(d,dtype='float64',always_2d=True)
    full=int(np.sum(np.abs(x)>=0.99999))
    I,tp,spk=ebur(d)
    rj=os.path.join(ROOT,r["master"].replace("\\","/"))+".render.json"
    clip=None
    if os.path.exists(rj):
        clip=json.load(open(rj,encoding='utf-8')).get("samples_at_or_above_full_scale")
    row=dict(id=r["id"],kind=r["kind"],sr=info.samplerate,ch=info.channels,sub=info.subtype,dur=round(info.duration,2),
             I=I,TP=tp,SP=spk,cat_TP=r.get("dist_tp"),cat_I=r.get("dist_lufs"),dist_fullscale=full,master_clip=clip)
    out.append(row)
    print(row)
json.dump(out,open(os.path.join(os.path.dirname(__file__),"measure_out.json"),"w",encoding='utf-8'),ensure_ascii=False,indent=1)
