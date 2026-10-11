"""WF1004-P audit: independent sample-by-sample compare of auditor-rendered A/B float32 files
plus R10 numbers for the moonlight case. usage: audit_compare.py <dirA> <dirB>"""
import sys, os, numpy as np
a, b = sys.argv[1], sys.argv[2]
names = sorted(f[:-4] for f in os.listdir(a) if f.endswith('.f32'))
unexpected = 0
for n in names:
    x = np.fromfile(os.path.join(a, n + '.f32'), dtype=np.float32)
    pb = os.path.join(b, n + '.f32')
    if not os.path.exists(pb):
        print(n, 'MISSING_B'); unexpected += 1; continue
    y = np.fromfile(pb, dtype=np.float32)
    if x.shape != y.shape:
        print(n, 'LEN', x.shape, y.shape); unexpected += 1; continue
    eq = np.array_equal(x.view(np.uint32), y.view(np.uint32))  # bitwise, not float ==
    d = np.abs(x.astype(np.float64) - y.astype(np.float64))
    nz = np.nonzero(d > 0)[0]
    first = (nz[0] // 2) / 48000.0 if nz.size else None
    tag = 'EXPECT_DIFF' in n
    if not tag and not eq:
        unexpected += 1
    print(f"{n:44s} n={x.size//2:9d} bitwise_equal={eq} max|d|={d.max():.4e} n_diff={nz.size} first={first}")
    if n.startswith('corpus_moonlight'):
        rms = lambda s: 20*np.log10(np.sqrt(np.mean(s.astype(np.float64)**2)))
        pk = lambda s: 20*np.log10(np.max(np.abs(s.astype(np.float64))))
        diff = x.astype(np.float64) - y.astype(np.float64)
        print(f"   R10: peak A {pk(x):.3f} B {pk(y):.3f} dBFS; RMS A {rms(x):.3f} B {rms(y):.3f}; diff RMS {rms(diff):.2f} dBFS "
              f"(rel A {rms(diff)-rms(x):.2f} dB), diff peak {pk(diff):.2f} dBFS")
        if first is not None:
            k = nz[0] - (nz[0] % 2)
            print(f"   before first diff bitwise equal: {np.array_equal(x[:k].view(np.uint32), y[:k].view(np.uint32))}")
print('UNEXPECTED_DIFFS =', unexpected)
