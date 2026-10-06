import re, glob, statistics, sys, os
run_dir = sys.argv[1] if len(sys.argv) > 1 else 'E:/Tsuki-project/_scratch/wf1003/V/run'
cases = {}
for f in sorted(glob.glob(os.path.join(run_dir, 'out_pool*_run*.txt'))):
    m = re.search(r'out_pool(\d+)_run(\d+)', f)
    pool, run = int(m.group(1)), int(m.group(2))
    cur = None
    pf = None
    for line in open(f, encoding='utf-8', errors='replace'):
        line = line.rstrip()
        mm = re.search(r'Q09V case=(.*)$', line)
        if mm:
            cur = mm.group(1).strip()
            continue
        if cur is None:
            mp = re.search(r'\[(PASS|FAIL)\]', line)
            continue
        d = cases.setdefault(cur, {'steals': None, 'active': None, 'ident': {}, 'vst': {}, 'twin': {}})
        if 'Q09V steals' in line:
            d['steals'] = line.strip()
        elif 'Q09V max active' in line:
            d['active'] = line.strip()
        elif 'Q09V identity' in line:
            d['ident'][(pool, run)] = line.strip()
        elif 'Q09V VST3 processBlock' in line:
            m2 = re.search(r'mean = ([\d.]+) ms, p99 = ([\d.]+) ms, max = ([\d.]+) ms, max/budget = ([\d.]+), blocks >= budget = (\d+)', line)
            d['vst'][(pool, run)] = tuple(float(x) for x in m2.groups())
        elif 'Q09V twin(synth only)' in line:
            m2 = re.search(r'pool(\d+) rep(\d+): blocks = (\d+), mean = ([\d.]+) ms, p99 = ([\d.]+) ms, max = ([\d.]+) ms, max/budget = ([\d.]+), blocks >= budget = (\d+)', line)
            tp, rep = int(m2.group(1)), int(m2.group(2))
            d['twin'].setdefault(tp, []).append((run, rep) + tuple(float(x) for x in m2.groups()[3:]))

def agg(rows, idx):
    return [r[idx] for r in rows]

print("=== per-case aggregates (all HostProbe runs x 5 reps) ===")
for name, d in cases.items():
    print(f"\n## {name}")
    print(d['steals']); print(d['active'])
    for tp in (16, 32):
        rows = d['twin'].get(tp, [])
        if not rows: continue
        means = agg(rows, 2); p99s = agg(rows, 3); maxs = agg(rows, 4); viol = agg(rows, 6)
        print(f"  twin pool{tp}: n_reps={len(rows)} mean(ms) median={statistics.median(means):.4f} | p99(ms) median={statistics.median(p99s):.4f} | max(ms) median={statistics.median(maxs):.4f} worst={max(maxs):.4f} (max/budget worst={max(maxs)/10.6667:.4f}) | blocks>=budget: min={min(viol):.0f} max={max(viol):.0f} total={sum(viol):.0f}")
    for pool in (16, 32):
        rows = [(k, v) for k, v in d['vst'].items() if k[0] == pool]
        if not rows: continue
        means = [v[0] for k, v in rows]; p99 = [v[1] for k, v in rows]; mx = [v[2] for k, v in rows]; viol = [v[4] for k, v in rows]
        print(f"  VST3 built pool{pool}: runs={len(rows)} mean median={statistics.median(means):.4f} | p99 median={statistics.median(p99):.4f} | max worst={max(mx):.4f} (max/budget={max(mx)/10.6667:.4f}) | blocks>=budget total={sum(viol):.0f}")
    ids = sorted(d['ident'].items())
    for k, v in ids[:1]:
        print("  identity sample", k, v)
    # identity per pool summary
    for pool in (16, 32):
        vals = [v for k, v in d['ident'].items() if k[0] == pool]
        zero16 = all('max|VST3 - twin16| = 0,' in x for x in vals)
        zero32 = all(re.search(r'twin32\| = 0\s', x) for x in vals)
        print(f"  VST3 built pool{pool}: identical to twin16 in all {len(vals)} runs: {zero16}; identical to twin32: {zero32}")
