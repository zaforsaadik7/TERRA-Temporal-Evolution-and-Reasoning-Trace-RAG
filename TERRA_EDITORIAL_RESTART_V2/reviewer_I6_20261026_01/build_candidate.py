from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys,time
import pymupdf as fitz
P=Path(__file__).resolve().parent;R=P.parents[1]; rev=sys.argv[1];D=P/'builds'/rev
D.mkdir(parents=True,exist_ok=False)
for x in (P/'candidate/src').rglob('*'):
 if x.is_file():q=D/x.relative_to(P/'candidate/src');q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(x,q)
commands=[]
for i,n in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
 cmd=[str(R/'scratch/tectonic/tectonic.exe'),'-C','-k','--keep-logs',n+'.tex'];t=time.time()
 with (D/f'console_{i}_{n}.txt').open('wb') as log:cp=subprocess.run(cmd,cwd=D,stdout=log,stderr=subprocess.STDOUT)
 commands.append({'command':cmd,'exit':cp.returncode,'seconds':round(time.time()-t,3)})
 (D/'execution.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf-8')
 if cp.returncode:print('BUILD_FAIL',rev,i);sys.exit(cp.returncode)
result={'revision':rev,'engine':'Tectonic0.17.0 XeTeX; cached-only','commands':commands,'documents':{}}
for n in ['main','TERRA_SUPPLEMENT']:
 f=D/(n+'.pdf');doc=fitz.open(f);text='\n'.join(p.get_text() for p in doc);log=(D/(n+'.log')).read_text(encoding='utf-8',errors='replace')
 result['documents'][n]={'pages':len(doc),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'overfull':len(re.findall(r'Overfull \\[hv]box',log)),'underfull':len(re.findall(r'Underfull \\[hv]box',log)),'undefined':len(re.findall(r'(?:Reference|Citation).*undefined|There were undefined',log)),'multiply_defined':len(re.findall(r'multiply defined|destination with the same identifier',log)),'question_marks':'??' in text,'font_warnings':log.count('LaTeX Font Warning')}
 (D/(n+'.txt')).write_text(text,encoding='utf-8')
(D/'BUILD_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'revision':rev,'documents':result['documents']}))
