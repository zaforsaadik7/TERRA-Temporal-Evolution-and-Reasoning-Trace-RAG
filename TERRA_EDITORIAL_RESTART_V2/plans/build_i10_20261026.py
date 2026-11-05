from pathlib import Path
import json,hashlib,shutil,subprocess,time,re,zipfile
import pymupdf as fitz
R=Path('F:/TERRA -Copy');P=R/'TERRA_EDITORIAL_RESTART_V2/reviewer_I10_20261026_01';B=P/'build/r01';S=P/'candidate/anonymous/src'
B.mkdir(parents=True,exist_ok=False)
for f in S.rglob('*'):
 if f.is_file():d=B/f.relative_to(S);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
execs=[]
for i,n in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
 cmd=[str(R/'scratch/tectonic/tectonic.exe'),'-C','-k','--keep-logs',n+'.tex'];start=time.time()
 with (B/f'console_{i}.txt').open('wb') as f:cp=subprocess.run(cmd,cwd=B,stdout=f,stderr=subprocess.STDOUT,timeout=180)
 execs.append({'command':cmd,'cwd':str(B),'exit':cp.returncode,'seconds':round(time.time()-start,3)})
 (B/'execution.json').write_text(json.dumps(execs,indent=2)+'\n',encoding='utf-8');assert cp.returncode==0
output=P/'output/pdf';output.mkdir(parents=True)
result={};names=['zafor','saadik','raihan','molla','bubt','bangladesh university','github.com/zaforsaadik7']
for n in ['main','TERRA_SUPPLEMENT']:
 pdf=B/(n+'.pdf');doc=fitz.open(pdf);texts=[p.get_text() for p in doc];alltext='\n'.join(texts)
 metadata=doc.metadata;assert not metadata.get('author')
 bad=[x for x in names if x in (alltext+json.dumps(metadata)).lower()];assert not bad
 uris=[l.get('uri','') for page in doc for l in page.get_links() if l.get('uri')]
 assert not any(x in u.lower() for u in uris for x in names)
 assert doc.embfile_count()==0
 log=(B/(n+'.log')).read_text(encoding='utf-8',errors='replace')
 r={'pages':len(doc),'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'metadata':metadata,'identity_pattern_matches':0,'embedded_files':0,'overfull':len(re.findall(r'Overfull \\[hv]box',log)),'undefined':len(re.findall(r'(?:Reference|Citation).*undefined|There were undefined',log)),'duplicate':len(re.findall(r'multiply defined|destination with the same identifier',log)),'underfull':len(re.findall(r'Underfull \\[hv]box',log)),'font_warnings':log.count('LaTeX Font Warning'),'question_marks':'??' in alltext}
 assert not r['undefined'] and not r['duplicate'] and not r['overfull'] and not r['question_marks']
 assert len(doc)<=25 if n=='main' else True
 (B/(n+'.txt')).write_text(alltext,encoding='utf-8')
 # Extract the actual expanded abstract from page1 rather than raw TeX macros.
 if n=='main':
  abstract=texts[0].split('Abstract',1)[1].split('Keywords',1)[0].strip(' —\n-')
  r['rendered_abstract']=abstract;r['abstract_words_whitespace']=len(abstract.split());r['abstract_words_hyphen_compounds']=len(re.findall(r"[A-Za-z0-9]+(?:[’'\-][A-Za-z0-9]+)*",abstract))
  r['abstract_150_250_whitespace']=150<=r['abstract_words_whitespace']<=250
  # All known author names omitted, no AI declarations inserted pending confirmations.
 render=P/'renders'/n;render.mkdir(parents=True)
 for i,page in enumerate(doc,1):page.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False).save(render/f'page_{i:02}.png')
 shutil.copy2(pdf,output/pdf.name);result[n]=r
(P/'BUILD_RESULT.json').write_text(json.dumps({'engine':'Tectonic0.17.0/XeTeX/cache-only','execution':execs,'documents':result},indent=2)+'\n',encoding='utf-8')
print(json.dumps({n:{k:v for k,v in d.items() if k in ['pages','overfull','undefined','abstract_words_whitespace','abstract_words_hyphen_compounds','font_warnings']} for n,d in result.items()}))
