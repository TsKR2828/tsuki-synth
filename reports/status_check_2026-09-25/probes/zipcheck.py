import json, os, zipfile, hashlib, sys, io
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r"C:/Users/admin/Desktop/Claude/tsuki-synth/exports/products/clean_batch2"
cat = json.load(open(os.path.join(ROOT, "catalog.json"), encoding="utf-8"))
print("catalog rows", len(cat))
from collections import Counter
print(Counter(r["kind"] for r in cat))
print(Counter(r["group"] for r in cat))
print("keys", sorted(cat[0].keys()))
for zname in ["TsukiSynth_Worldview_SE_Pack_v1.0.zip","TsukiSynth_Album_Vol1.zip"]:
    zp = os.path.join(ROOT,"packages",zname)
    with zipfile.ZipFile(zp) as z:
        infos = z.infolist()
        print("\n==", zname, len(infos), "entries; testzip:", z.testzip())
        names = [i.filename for i in infos]
        for i in infos:
            if not i.filename.lower().endswith(('.wav','.mp3')):
                print("  non-audio:", i.filename, i.file_size)
        # map catalog
        if "SE" in zname:
            exp = {}
            for r in cat:
                if r["kind"]!="sfx": continue
                arc = f"{r['group']}/{os.path.basename(r['distribution'].replace(chr(92),'/'))}"
                exp[arc]=r
        else:
            exp={}
            for r in cat:
                if r["kind"]!="music" or r["id"]=="ai_radiance_complete": continue
                exp["WAV/"+os.path.basename(r['distribution'].replace(chr(92),'/'))]=r
                exp["MP3/"+os.path.basename(r['preview'].replace(chr(92),'/'))]=None
        audio=[n for n in names if n.lower().endswith(('.wav','.mp3'))]
        missing=[a for a in exp if a not in names]
        extra=[a for a in audio if a not in exp]
        print("  audio in zip:", len(audio), "expected:", len(exp), "missing:", missing, "extra:", extra)
        # sha256 compare against catalog dist_sha256
        bad=0; checked=0
        for arc,r in exp.items():
            if r is None or arc not in names: continue
            h=hashlib.sha256(z.read(arc)).hexdigest(); checked+=1
            if h!=r.get("dist_sha256"): bad+=1; print("  SHA MISMATCH", arc)
            # compare to on-disk distribution
        print("  sha checked", checked, "mismatch", bad)
        # also list any preview/master duplicates
        if "README.txt" in names:
            print("  README head:\n   ", z.read("README.txt").decode('utf-8')[:600].replace("\n","\n    "))
