import json, os, re, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r"C:/Users/admin/Desktop/Claude/tsuki-synth/exports/products/clean_batch2"
FF = r"C:/Users/admin/Desktop/Tools/ffmpeg-8.1.1-full_build/bin/ffmpeg.exe"
cat = json.load(open(os.path.join(ROOT, "catalog.json"), encoding="utf-8"))
res=[]
for r in cat:
    if r["kind"]!="sfx": continue
    d=os.path.join(ROOT,r["distribution"].replace("\\","/"))
    p=subprocess.run([FF,"-hide_banner","-nostats","-v","verbose","-i",d,"-af","apad=pad_dur=0.5,ebur128=framelog=verbose","-f","null","-"],capture_output=True,text=True,encoding='utf-8',errors='replace')
    M=[float(x) for x in re.findall(r"M:\s*(-?[0-9.]+)",p.stderr) ]
    res.append((r["id"],max(M) if M else None))
res.sort(key=lambda t:t[1])
for i,m in res: print(f"{i:32s} maxM {m:6.1f} LUFS")
vals=[m for _,m in res]
print("min",min(vals),"max",max(vals),"spread",round(max(vals)-min(vals),1))
