import soundfile as sf, numpy as np, sys, glob, os
sys.stdout.reconfigure(encoding='utf-8')
M=r"C:/Users/admin/Desktop/Claude/tsuki-synth/exports/products/clean_batch2"
bad=0; n=0; pks=[]
for f in glob.glob(M+"/masters/**/*.wav",recursive=True)+glob.glob(M+"/distribution/**/*.wav",recursive=True):
    x,sr=sf.read(f,dtype='float64',always_2d=True); n+=1
    pk=np.max(np.abs(x)); pks.append(pk)
    runs=0
    for c in range(x.shape[1]):
        v=x[:,c]; near=np.abs(v)>=pk*0.9999
        d=np.diff(v); eq=(np.abs(d)<1e-9)&near[1:]&near[:-1]
        # runs of >=2 consecutive equal near-peak diffs => >=3 identical samples
        if np.any(eq[1:]&eq[:-1]): runs+=1
    if runs: bad+=1; print("FLAT-TOP:",os.path.relpath(f,M),pk)
print(f"files {n}, flat-top files {bad}, max peak {max(pks):.5f}")
