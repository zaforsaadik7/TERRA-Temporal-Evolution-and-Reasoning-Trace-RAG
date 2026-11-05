from pathlib import Path
import hashlib,json,sys
import pymupdf as fitz
P=Path(__file__).resolve().parent;R=P.parents[1];rev=sys.argv[1];D=P/'builds'/rev;out=P/'renders'/rev;out.mkdir(parents=True,exist_ok=True)
B=R/'TERRA_EDITORIAL_RESTART_V2/reviewer_I7_20261025_01/adoption_20261025_01/output/pdf'
record={}
for name in ['main','TERRA_SUPPLEMENT']:
 a=fitz.open(B/(name+'.pdf'));b=fitz.open(D/(name+'.pdf'));sub=out/name;sub.mkdir(exist_ok=True)
 def sig(page):
  clip=fitz.Rect(0,24,page.rect.width,page.rect.height-33)
  return hashlib.sha256(page.get_pixmap(matrix=fitz.Matrix(1,1),clip=clip,alpha=False).samples).hexdigest()
 prior={sig(p):i+1 for i,p in enumerate(a)};rec=[]
 for i,p in enumerate(b):
  match=prior.get(sig(p));text=p.get_text();rec.append({'page':i+1,'identical_body_baseline_page':match,'render':str(sub/f'page_{i+1:02d}.png'),'visual_review':'PENDING' if match is None else 'BASELINE_BODY_PIXEL_PARITY'})
  if match is None or (name=='main' and 'two-phase architecture' in text):p.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False).save(sub/f'page_{i+1:02d}.png')
 record[name]=rec
print(json.dumps({n:{'changed_body_pages':[x['page'] for x in v if x['identical_body_baseline_page'] is None],'parity_pages':sum(x['identical_body_baseline_page'] is not None for x in v)} for n,v in record.items()}))
(P/'ledgers'/f'PAGE_COMPARISON_{rev}.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
