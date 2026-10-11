import sys, os, numpy as np
a, b = sys.argv[1], sys.argv[2]
names = sorted(f[:-4] for f in os.listdir(a) if f.endswith('.f32'))
print(f"A={a}\nB={b}")
print(f"{'case':46s} {'samples':>9s} {'max|diff|':>12s} {'n_diff':>9s} {'first_diff_s':>13s}  verdict")
bad_unexpected = 0
for n in names:
    pa = os.path.join(a, n + '.f32'); pb = os.path.join(b, n + '.f32')
    if not os.path.exists(pb):
        print(n, 'MISSING in B'); bad_unexpected += 1; continue
    x = np.fromfile(pa, dtype=np.float32); y = np.fromfile(pb, dtype=np.float32)
    if x.shape != y.shape:
        print(n, 'LENGTH MISMATCH', x.shape, y.shape); bad_unexpected += 1; continue
    d = np.abs(x.astype(np.float64) - y.astype(np.float64))
    nd = int((d > 0).sum())
    mx = float(d.max()) if d.size else 0.0
    first = (np.nonzero(d > 0)[0][0] // 2) / 48000.0 if nd else None
    expect_diff = 'EXPECT_DIFF' in n
    if expect_diff:
        verdict = 'DIFF (expected, R10 report)' if nd else 'SAME (no overflow effect)'
    else:
        verdict = 'IDENTICAL' if nd == 0 else 'DIFFERS (UNEXPECTED)'
        if nd: bad_unexpected += 1
    print(f"{n:46s} {x.size//2:9d} {mx:12.3e} {nd:9d} {('%.3f' % first) if first is not None else '-':>13s}  {verdict}")
print('UNEXPECTED_DIFFS =', bad_unexpected)
sys.exit(1 if bad_unexpected else 0)
