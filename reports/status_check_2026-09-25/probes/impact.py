import soundfile as sf, numpy as np, sys
sys.stdout.reconfigure(encoding='utf-8')
B=r"C:/Users/admin/Desktop/Claude/tsuki-synth/exports/products/clean_batch2/distribution/sfx/"
for f in ["rabbit/rabbit__Rabbit_Stomp.wav","clockwork/clockwork__Clockwork_Spring_Release.wav","restraint/restraint__Restraint_Shackle_Slam.wav","rabbit/rabbit__Rabbit_Ding.wav"]:
    x,sr=sf.read(B+f,always_2d=True); m=x.mean(1)
    pk=np.max(np.abs(m)); rms=np.sqrt(np.mean(m**2)); ipk=int(np.argmax(np.abs(m)))
    # energy window: time for 90% of energy
    e=np.cumsum(m**2); t90=np.searchsorted(e,0.9*e[-1])/sr
    S=np.abs(np.fft.rfft(m))**2; fr=np.fft.rfftfreq(len(m),1/sr)
    below100=S[fr<100].sum()/S.sum(); cent=(fr*S).sum()/S.sum()
    # peak sample neighbourhood: how many samples above -6 dB of peak
    n6=int(np.sum(np.abs(m)>pk/2))
    print(f"{f}: dur {len(m)/sr:.2f}s crest {20*np.log10(pk/rms):.1f} dB, peak at {ipk/sr*1000:.1f} ms, samples>-6dBpk {n6}, 90% energy by {t90*1000:.0f} ms, energy<100Hz {below100*100:.1f}%, centroid {cent:.0f} Hz")
