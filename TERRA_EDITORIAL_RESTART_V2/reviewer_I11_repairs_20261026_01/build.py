from pathlib import Path
import os,sys,json,shutil,subprocess,time,hashlib,re
import pymupdf as f
P=Path(__file__).resolve().parent;tag=sys.argv[1];B=P/'builds'/tag;B.mkdir(parents=True,exist_ok=False)
for src in (P/'candidate/src').rglob('*'):
 if src.is_file() and src.suffix not in ['.bbl','.aux','.pdf','.log','.out']:
  dst=B/src.relative_to(P/'candidate/src');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
env={k:os.environ[k] for k in ['SYSTEMROOT','WINDIR','USERPROFILE','LOCALAPPDATA','APPDATA','TEMP','TMP','COMSPEC'] if k in os.environ};env['PATH']=str(Path(env['SYSTEMROOT'])/'System32')
exe=Path('F:/TERRA -Copy/scratch/tectonic/tectonic.exe');receipts=[]
for i,n in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
 cmd=[str(exe),'-C','--untrusted','-k','--keep-logs','--makefile-rules',f'dependencies_{i}.mk',n+'.tex'];start=time.monotonic()
 with (B/f'console_{i}_{n}.txt').open('wb') as log:r=subprocess.run(cmd,cwd=B,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 receipts.append({'command':cmd,'exit':r.returncode,'seconds':time.monotonic()-start});(B/'BUILD_EXECUTION.json').write_text(json.dumps(receipts,indent=2),encoding='utf8')
 if r.returncode:print('BUILD_STOP',n,flush=True);sys.exit(r.returncode)
result={}
for n in ['main','TERRA_SUPPLEMENT']:
 d=f.open(B/(n+'.pdf'));render=B/'renders'/n;render.mkdir(parents=True);pages=[]
 for i,page in enumerate(d,1):
  page.get_pixmap(matrix=f.Matrix(1.4,1.4),alpha=False).save(render/f'page_{i:02}.png')
  (render/f'page_{i:02}.txt').write_text(page.get_text(),encoding='utf8')
  spans=[x for b in page.get_text('dict',clip=f.INFINITE_RECT())['blocks'] if 'lines' in b for l in b['lines'] for x in l['spans'] if x['text'].strip()]
  outside=[{'text':x['text'],'bbox':x['bbox']} for x in spans if x['bbox'][0]<-1 or x['bbox'][1]<-1 or x['bbox'][2]>page.rect.width+1 or x['bbox'][3]>page.rect.height+1]
  pages.append({'page':i,'min_font':min(x['size'] for x in spans),'offpage':outside})
 log=(B/(n+'.log')).read_text(encoding='utf8',errors='replace')
 result[n]={'pages':len(d),'sha256':hashlib.sha256((B/(n+'.pdf')).read_bytes()).hexdigest(),'layout':pages,'overfull_lines':[x for x in log.splitlines() if 'Overfull' in x],'undefined_reference_lines':[x for x in log.splitlines() if re.search(r'(Reference|Citation).*undefined|There were undefined',x,re.I)],'missing_character_lines':[x for x in log.splitlines() if 'Missing character' in x]}
(B/'BUILD_RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({n:{k:v for k,v in rec.items() if k!='layout'}|{'offpage_pages':[x['page'] for x in rec['layout'] if x['offpage']]} for n,rec in result.items()},indent=2),flush=True)
