import re, zlib, sys
b = open('E:/Tsuki-project/_tools/papers/Alon2015_York_MSc_handpan.pdf', 'rb').read()

def unesc(s):
    s = re.sub(rb'\\([()\\])', rb'\1', s)
    s = re.sub(rb'\\(\d{3})', lambda m: bytes([int(m.group(1), 8)]), s)
    return s

STR = rb'\((?:[^()\\]|\\.)*\)'
TOK = re.compile(rb'\[((?:' + STR + rb'|[^\]()])*)\]\s*TJ|(' + STR + rb')\s*Tj|(-?[\d.]+\s+-?[\d.]+\s+Td)|(Tm)|(ET)', re.S)
ITEM = re.compile(rb'\(((?:[^()\\]|\\.)*)\)|(-?[\d.]+)')

out = []
for m in re.finditer(rb'(\d+) 0 obj\s*<<(.*?)>>\s*stream\r?\n', b, re.S):
    h = m.group(2)
    if b'/Image' in h or b'ObjStm' in h:
        continue
    mm = re.search(rb'/Length (\d+)', h)
    if not mm:
        continue
    ln = int(mm.group(1))
    try:
        t = zlib.decompress(b[m.end():m.end() + ln])
    except Exception:
        continue
    lines = []
    cur = b''
    for tok in TOK.finditer(t):
        if tok.group(1) is not None:
            for it in ITEM.finditer(tok.group(1)):
                if it.group(1) is not None:
                    cur += unesc(it.group(1))
                elif float(it.group(2)) < -180:
                    cur += b' '
        elif tok.group(2) is not None:
            cur += unesc(tok.group(2)[1:-1])
        else:
            if cur:
                lines.append(cur)
                cur = b''
    if cur:
        lines.append(cur)
    out.append((int(m.group(1)), b'\n'.join(lines)))

with open('E:/Tsuki-project/_scratch/wf1004/Q/alon_text.txt', 'wb') as f:
    for n, tx in out:
        f.write(b'\n=====OBJ %d=====\n' % n + tx)
print(len(out))
