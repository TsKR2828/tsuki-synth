import os,sys,hashlib,json
roots=['E:/Tsuki-project/tsuki-synth/exports/products/clean_batch2_v1_1_candidate','E:/Tsuki-project/tsuki-synth/exports/products/clean_batch2','E:/Tsuki-project/_tools/papers']
out=[]
for r in roots:
    for dp,dn,fn in os.walk(r):
        for f in sorted(fn):
            p=os.path.join(dp,f); s=os.stat(p)
            out.append(f"{p.replace(chr(92),'/')}\t{s.st_size}\t{int(s.st_mtime)}")
out.sort()
open(sys.argv[1],'w',encoding='utf-8').write('\n'.join(out)+'\n')
h=hashlib.sha256('\n'.join(out).encode()).hexdigest()
print(len(out),'files; listing sha256',h)
