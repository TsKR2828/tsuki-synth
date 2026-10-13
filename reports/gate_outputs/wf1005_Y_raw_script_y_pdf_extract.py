import fitz,sys
d=fitz.open('E:/Tsuki-project/_tools/papers/Alon2015_York_MSc_handpan.pdf')
print(d.page_count)
out=open('alon_pages.txt','w',encoding='utf-8')
for i,p in enumerate(d):
    out.write(f'\n=====PDFPAGE {i+1}=====\n'+p.get_text())
out.close()
