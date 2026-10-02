import json, os, sys, soundfile as sf, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
REPO=r"C:/Users/admin/Desktop/Claude/tsuki-synth"
ROOT=REPO+"/exports/products/clean_batch2"
cat=json.load(open(ROOT+"/catalog.json",encoding='utf-8'))
for r in cat:
    if r["kind"]!="sfx": continue
    s=json.load(open(os.path.join(REPO,r["score"].replace("\\","/")),encoding='utf-8'))
    m=s["meta"]
    if m.get("sound_type")!="loop": continue
    bpm=m.get("loop_bpm") or s["global"].get("bpm"); bars=m.get("loop_bars")
    ts=s["global"].get("time_signature",[4,4])
    beats=bars*(ts[0] if isinstance(ts,list) else 4) if bars else None
    exp=beats*60.0/bpm if beats else None
    ev=s["events"]; last_on=max(e["time"] for e in ev); last_end=max(e["time"]+e.get("duration",0) for e in ev)
    x,sr=sf.read(os.path.join(ROOT,r["distribution"].replace("\\","/")),always_2d=True)
    pk=np.max(np.abs(x)); n50=int(0.05*sr)
    head=np.sqrt(np.mean(x[:n50]**2)); tail=np.sqrt(np.mean(x[-n50:]**2))
    jump=np.max(np.abs(x[-1]-x[0]))
    print(f"{r['id']}: file {len(x)/sr:.3f}s | bpm {bpm} bars {bars} -> musical loop {exp if exp is None else round(exp,3)}s | last onset {last_on}s, last note-off {last_end:.3f}s | "
          f"tail50ms RMS {20*np.log10(tail/pk+1e-12):.1f} dB re peak, head50ms {20*np.log10(head/pk+1e-12):.1f} dB | wrap jump {jump:.4f} ({20*np.log10(jump/pk+1e-12):.1f} dB re peak)")
