import soundfile as sf, numpy as np, sys, glob, os
sys.stdout.reconfigure(encoding='utf-8')
M=r"C:/Users/admin/Desktop/Claude/tsuki-synth/exports/products/clean_batch2/masters"
files=["originals/Original_AI_Radiance_Complete.wav","originals/Original_AI_Radiance_Movement2.wav","sfx_library/akashic/Magic_Dark_OneShot_C4.wav","sfx_library/rabbit/Impact_Stomp_OneShot_E2.wav","sfx_library/restraint/Impact_Dark_OneShot_C2.wav","classical/fur_elise_complete.wav"]
for f in files:
    x,sr=sf.read(os.path.join(M,f),dtype='float64',always_2d=True)
    pk=np.max(np.abs(x))
    # flat-top runs: >=3 consecutive samples within 1e-6 of channel peak magnitude
    runs=0; maxrun=0
    for c in range(x.shape[1]):
        a=np.abs(x[:,c]); near=a>=pk*0.999
        # count runs of consecutive identical values among near-peak samples
        idx=np.where(near)[0]
        if len(idx)==0: continue
        r=1
        for i in range(1,len(idx)):
            if idx[i]==idx[i-1]+1 and abs(x[idx[i],c]-x[idx[i-1],c])<1e-7: r+=1
            else:
                if r>=3: runs+=1
                maxrun=max(maxrun,r); r=1
        if r>=3: runs+=1
        maxrun=max(maxrun,r)
    n_near=int(np.sum(np.abs(x)>=pk*0.999))
    print(f"{f}: sr={sr} peak={pk:.5f} ({20*np.log10(pk):.2f} dBFS) near-peak samples={n_near} flat-top runs>=3: {runs} max identical run: {maxrun}")
