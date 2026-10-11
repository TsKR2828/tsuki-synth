"""WF1004-P summariser: parses HostProbe TSUKI_Q09V=1 outputs and evaluates C1/C2 exactly as written in
reports/gate_outputs/wf1004_P_criteria_preregistered.txt.
usage: summarize_p.py <dir with raw_{baseline,candidate}_run{1,2,3}.txt>"""
import re, sys, os, statistics

d = sys.argv[1]
BUDGET = 512 / 48000 * 1000

def parse(path):
    cases = {}
    cur = None
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.rstrip('\n')
        m = re.match(r'\s+Q09V case=(.*)$', line)
        if m:
            cur = m.group(1).strip(); cases[cur] = {'twin': {16: [], 32: []}}; continue
        if cur is None: continue
        c = cases[cur]
        m = re.search(r'Q09V product pool of this engine class = (\d+) \((.*?)\), product twin steals = (\d+)', line)
        if m: c['prod_pool'] = int(m.group(1)); c['prod_class'] = m.group(2); c['prod_steals'] = int(m.group(3)); continue
        m = re.search(r'Q09V steals pool16 = (\d+) \(held (\d+)\), pool32 = (\d+) \(held (\d+)\), pool128 = (\d+)', line)
        if m: c['steal16'], c['held16'], c['steal32'], c['held32'], c['steal128'] = map(int, m.groups()); continue
        m = re.search(r'Q09V max active voices at block end: pool16 = (\d+), pool32 = (\d+), pool128 = (\d+)', line)
        if m: c['maxact16'], c['maxact32'], c['maxact128'] = map(int, m.groups()); continue
        m = re.search(r'Q09V identity: max\|VST3 - twin16\| = (\S+), max\|VST3 - twin32\| = (\S+), max\|VST3 - twinProd\| = (\S+)', line)
        if m: c['id16'], c['id32'], c['idprod'] = map(float, m.groups()); continue
        m = re.search(r'Q09V output: max\|twin16 - twin32\| = (\S+) .*first differing sample = (.*)$', line)
        if m: c['d1632'] = float(m.group(1)); c['firstdiff'] = m.group(2).strip(); continue
        m = re.search(r'Q09V VST3 processBlock .*?blocks = (\d+), mean = (\S+) ms, p99 = (\S+) ms, max = (\S+) ms, max/budget = (\S+), blocks >= budget = (\d+)', line)
        if m:
            c['vst'] = dict(blocks=int(m.group(1)), mean=float(m.group(2)), p99=float(m.group(3)), max=float(m.group(4)), viol=int(m.group(6)))
            continue
        m = re.search(r'Q09V twin\(synth only\) pool(\d+) rep(\d+): blocks = (\d+), mean = (\S+) ms, p99 = (\S+) ms, max = (\S+) ms, max/budget = (\S+), blocks >= budget = (\d+), steals = (\d+), maxActive = (\d+)', line)
        if m:
            c['twin'][int(m.group(1))].append(dict(mean=float(m.group(4)), p99=float(m.group(5)), max=float(m.group(6)), viol=int(m.group(8)), steals=int(m.group(9))))
    return cases

def tw(c, pool):
    r = c['twin'][pool]
    return dict(mean=statistics.mean(x['mean'] for x in r), p99med=statistics.median(x['p99'] for x in r),
                p99max=max(x['p99'] for x in r), max=max(x['max'] for x in r), viol=sum(x['viol'] for x in r), n=len(r))

runs = {}
for which in ('baseline', 'candidate'):
    for r in (1, 2, 3):
        p = os.path.join(d, f'raw_{which}_run{r}.txt')
        if os.path.exists(p): runs[(which, r)] = parse(p)

out = []
P = out.append
P(f'WF1004-P summary of {d}   (budget {BUDGET:.4f} ms)')
P('')
for key in sorted(runs):
    cs = runs[key]
    P(f'=== {key[0]} run {key[1]} ===')
    for name, c in cs.items():
        P(f' case {name}')
        P(f'   product pool of engine class = {c.get("prod_pool")} ({c.get("prod_class")}), product-twin steals = {c.get("prod_steals")}')
        P(f'   steals pool16={c.get("steal16")} (held {c.get("held16")}) pool32={c.get("steal32")} (held {c.get("held32")}) pool128={c.get("steal128")}; maxActive 16/32/128 = {c.get("maxact16")}/{c.get("maxact32")}/{c.get("maxact128")}')
        P(f'   identity max|VST3-twin16|={c.get("id16")} max|VST3-twin32|={c.get("id32")} max|VST3-twinProd|={c.get("idprod")}; max|twin16-twin32|={c.get("d1632")} first diff {c.get("firstdiff")}')
        v = c.get('vst')
        if v: P(f'   VST3 (full chain): mean {v["mean"]:.3f} p99 {v["p99"]:.3f} max {v["max"]:.3f} ms, blocks>=budget {v["viol"]}/{v["blocks"]}')
        for pool in (16, 32):
            if c['twin'][pool]:
                t = tw(c, pool)
                P(f'   twin pool{pool} ({t["n"]} reps): mean {t["mean"]:.3f} | p99 median-of-reps {t["p99med"]:.3f} (worst rep {t["p99max"]:.3f}) | worst block {t["max"]:.2f} | blocks>=budget total {t["viol"]}')
    P('')

# ---- decision evaluation ----
P('=========== CRITERIA EVALUATION (as pre-registered) ===========')
STRESS = ['stress32_chromatic_tongue (synthetic)', 'stress32_chromatic_watergong (synthetic)', 'stress32_chromatic_custom (synthetic)']
PIANO = 'stress32_piano (synthetic)'
MOON = 'moonlight_mvt1_tongue_drum'
c1_ok = True
P('C1  moonlight steals')
for r in (1, 2, 3):
    b = runs.get(('baseline', r), {}).get(MOON); c = runs.get(('candidate', r), {}).get(MOON)
    if b is None or c is None: P(f'  round {r}: missing'); c1_ok = False; continue
    # baseline binary = all-16 -> tied to twin16 (identity max|VST3-twin16| = 0); its steals are twin16's.
    # (the HostProbe's "product twin" is the PER-ENGINE twin of the HostProbe source, so it is not the baseline binary's twin)
    # candidate binary = per-engine -> tied to twin32 for Chromatic (== twinProd), steals are twin32's.
    okb = (b['steal16'] == 64 and b['id16'] == 0.0)
    okc = (c['steal32'] == 0 and c['id32'] == 0.0 and c['idprod'] == 0.0 and c['prod_steals'] == 0)
    P(f'  round {r}: baseline build: twin16 steals={b["steal16"]} (held {b["held16"]}), identity max|VST3-twin16|={b["id16"]};  candidate build: twin32 steals={c["steal32"]}, product-twin steals={c["prod_steals"]}, identity max|VST3-twin32|={c["id32"]} max|VST3-twinProd|={c["idprod"]}  -> {"OK" if (okb and okc) else "FAIL"}')
    c1_ok &= okb and okc
P(f'C1 => {"PASS" if c1_ok else "FAIL"}')
P('')
c2_ok = True
P('C2  Chromatic 32 full load vs Piano 16 full load (same run), strict <=')
for r in (1, 2, 3):
    cs = runs.get(('candidate', r))
    if cs is None: P(f'  round {r}: missing'); c2_ok = False; continue
    pb = cs[PIANO]
    pt = tw(pb, 16)
    P(f'  round {r}: Piano16 twin: p99 median {pt["p99med"]:.3f} ms, violations {pt["viol"]};  VST3: p99 {pb["vst"]["p99"]:.3f}, violations {pb["vst"]["viol"]}   (VST3 pool used by this binary for Piano = {pb.get("prod_pool")})')
    for x in STRESS:
        cx = cs[x]
        tx = tw(cx, 32)
        a = tx['p99med'] <= pt['p99med']
        b = tx['viol'] <= pt['viol']
        va = cx['vst']['p99'] <= pb['vst']['p99']
        vb = cx['vst']['viol'] <= pb['vst']['viol']
        ok = a and b and va and vb
        c2_ok &= ok
        P(f'     {x:44s} twin32: p99 median {tx["p99med"]:.3f} (<= {pt["p99med"]:.3f}: {a}), viol {tx["viol"]} (<= {pt["viol"]}: {b}); VST3(pool {cx.get("prod_pool")}): p99 {cx["vst"]["p99"]:.3f} (<= {pb["vst"]["p99"]:.3f}: {va}), viol {cx["vst"]["viol"]} (<= {pb["vst"]["viol"]}: {vb})  -> {"OK" if ok else "FAIL"}')
    m = cs[MOON]
    P(f'     moonlight on candidate VST3: blocks>=budget {m["vst"]["viol"]}, max block {m["vst"]["max"]:.3f} ms, p99 {m["vst"]["p99"]:.3f}  (reported; not in the inequalities)')
P(f'C2 => {"PASS" if c2_ok else "FAIL"}')
print('\n'.join(out))
