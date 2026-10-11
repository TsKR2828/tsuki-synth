import os, re, sys
import fitz
roots = ['E:/Tsuki-project/tsuki-synth/output', 'E:/Tsuki-project/tsuki-synth/external_data', 'E:/Tsuki-project/_tools/papers', 'E:/Tsuki-project/tsuki-synth/docs']
skip = ('R3',)
rows = []
for root in roots:
    for dp, dn, fn in os.walk(root):
        if os.sep + 'R3' in dp or '/R3' in dp.replace(os.sep, '/'):
            continue
        for f in fn:
            if f.lower().endswith('.pdf'):
                p = os.path.join(dp, f)
                b = open(p, 'rb').read()
                tail = b[-2048:]
                eof = b'%%EOF' in tail
                try:
                    d = fitz.open(p)
                    pages = d.page_count
                    first = (d[0].get_text()[:90].replace('\n', ' ') if pages else '')
                except Exception as e:
                    pages = -1; first = f'OPEN-FAIL {type(e).__name__}'
                rows.append((p.replace('E:/Tsuki-project/', '').replace(os.sep, '/'), os.path.getsize(p), eof, pages, first))
print('path | bytes | %%EOF in last 2KB | pages(fitz) | first text')
for r in sorted(rows):
    print(' | '.join(str(x) for x in r))
print('total PDFs', len(rows), ' w/o EOF marker or unopenable:', [r[0] for r in rows if (not r[2]) or r[3] <= 0])
