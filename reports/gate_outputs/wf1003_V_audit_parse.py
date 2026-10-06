"""V-card auditor's own parser (independent of wf1003_V_summarize.py).
Reads one HostProbe output, prints per-case Q09V numbers."""
import re, sys
BUDGET = 512 / 48000 * 1000.0
for path in sys.argv[1:]:
    print(f"==== {path}")
    case = None
    twin = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        s = line.strip()
        m = re.match(r"Q09V case=(.*)", s)
        if m:
            if case:
                for pool, rows in sorted(twin.items()):
                    print(f"  twin pool{pool}: reps={len(rows)} mean[min..max]={min(r[0] for r in rows):.3f}..{max(r[0] for r in rows):.3f} "
                          f"p99[min..max]={min(r[1] for r in rows):.3f}..{max(r[1] for r in rows):.3f} max_worst={max(r[2] for r in rows):.3f} "
                          f"viol per rep={[int(r[3]) for r in rows]} steals={[int(r[4]) for r in rows]} maxActive={[int(r[5]) for r in rows]}")
            case = m.group(1); twin = {}
            print(f"-- {case}")
            continue
        if not s.startswith("Q09V") or case is None:
            continue
        m = re.match(r"Q09V twin\(synth only\) pool(\d+) rep\d+: blocks = \d+, mean = ([\d.]+) ms, p99 = ([\d.]+) ms, max = ([\d.]+) ms, max/budget = [\d.]+, blocks >= budget = (\d+), steals = (\d+), maxActive = (\d+)", s)
        if m:
            twin.setdefault(int(m.group(1)), []).append(tuple(float(x) for x in m.groups()[1:]))
            continue
        print("  " + s)
    if case:
        for pool, rows in sorted(twin.items()):
            print(f"  twin pool{pool}: reps={len(rows)} mean[min..max]={min(r[0] for r in rows):.3f}..{max(r[0] for r in rows):.3f} "
                  f"p99[min..max]={min(r[1] for r in rows):.3f}..{max(r[1] for r in rows):.3f} max_worst={max(r[2] for r in rows):.3f} "
                  f"viol per rep={[int(r[3]) for r in rows]} steals={[int(r[4]) for r in rows]} maxActive={[int(r[5]) for r in rows]}")
    print(f"budget_ms={BUDGET:.4f}")
