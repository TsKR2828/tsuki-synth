import soundfile as sf, numpy as np, sys, json, os
sys.stdout.reconfigure(encoding='utf-8')
ROOT=r"C:/Users/admin/Desktop/Claude/tsuki-synth/exports/products/clean_batch2"
cat=json.load(open(ROOT+"/catalog.json",encoding='utf-8'))
rows=[]
for r in cat:
    if r["kind"]!="sfx": continue
    x,sr=sf.read(os.path.join(ROOT,r["distribution"].replace("\\","/")),always_2d=True)
    a=np.max(np.abs(x),axis=1)
    pk=a.max(); ipk=int(a.argmax())
    # exclude +-2 ms around the global peak; find next-largest peak
    w=int(0.002*sr)
    b=a.copy(); b[max(0,ipk-w):ipk+w]=0
    second=b.max()
    # count samples within 6 dB of peak
    n6=int(np.sum(a>pk/2))
    rows.append((r["id"],r["title"],ipk/sr*1000,n6,20*np.log10(pk/max(second,1e-12))))
rows.sort(key=lambda t:-t[4])
for i,t,ms,n6,gap in rows[:12]:
    print(f"{i:28s} {t:34s} peak@{ms:8.1f} ms  n(>-6dB)={n6:5d}  peak vs rest(+-2ms excluded) {gap:5.1f} dB")
