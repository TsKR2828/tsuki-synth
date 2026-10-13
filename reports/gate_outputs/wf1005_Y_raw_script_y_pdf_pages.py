import sys; sys.stdout.reconfigure(encoding="utf-8")
import re,sys
t=open('alon_pages.txt',encoding='utf-8').read()
parts=re.split(r'\n=====PDFPAGE (\d+)=====\n',t)
d={int(parts[i]):parts[i+1] for i in range(1,len(parts),2)}
a,b=int(sys.argv[1]),int(sys.argv[2])
for n in range(a,b+1):
    print(f'\n######## p.{n}'); print(d[n])
