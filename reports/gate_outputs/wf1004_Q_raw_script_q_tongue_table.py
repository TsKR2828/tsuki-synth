import json, math
rows = json.load(open('E:/Tsuki-project/_scratch/wf1004/Q/q_tongue.json'))
f0 = {k: v for k, _, _, v in [(a, b, c, d) for a, b, c, d in json.load(open('E:/Tsuki-project/_scratch/wf1004/Q/q_f0check.json'))]}
CANT = [1.0, (4.6940911 / 1.8751041) ** 2, (7.8547574 / 1.8751041) ** 2, (10.9955407 / 1.8751041) ** 2, (14.1371684 / 1.8751041) ** 2]
print('independent cantilever eigenvalue ratios (betaL 1.8751041/4.6940911/7.8547574/10.9955407/14.1371684): ' + ' : '.join(f'{r:.4f}' for r in CANT))
print('file | note/material | model modes f (Hz) / model T60 (s) [dump-modes, archived master renderer 9123db8f] | FFT-peak f1 vs model (c) | inst-freq f1 vs model (c, bw3%) | partial ratio meas (model) for modes with rel level > -50 dB | FX')
for r in rows:
    k = r['file']
    est = f0[k]
    mm = []
    for m in r['modes']:
        if m.get('meas_f') and m['rel_db'] > -50:
            mm.append(f"{m['ratio_to_f1_meas']:.3f}({m['ratio_to_f1_model']:.3f}, {m['rel_db']:+.0f}dB)")
    mod = ' / '.join(f"{a:.0f}Hz,{c:.3g}s" for a, b, c in r['model_modes'][:3])
    rv = r['reverb'] or {}
    print(f"{k} | {r['note']} {r['material']} {r['engine']} {r['boundary']} | {mod} | {r.get('f1_cents_vs_model', float('nan')):+.1f} | {est['iface_bw3'][1]:+.1f} | {'; '.join(mm)} | reverb wet {rv.get('wet')} decay {rv.get('decay')}")
print()
print('model p2/p1 T60 ratio (dump-modes) and measured T60 f1/p2 on the FX-baked product WAV (method-limited, see report):')
for r in rows:
    mt = r['model_modes']
    if len(mt) > 1:
        print(f"{r['file']:36s} model T60 p1 {mt[0][2]:.3g}s p2 {mt[1][2]:.3g}s ratio {mt[1][2]/mt[0][2]:.3f} | measured f1 {r.get('t60_f1_meas')} p2 {r.get('t60_p2_meas')} | window {r['window_s'][1]-r['window_s'][0]:.2f}s")
