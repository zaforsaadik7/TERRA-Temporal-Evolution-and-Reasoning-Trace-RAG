from pathlib import Path
import subprocess,json,shutil,hashlib,re,argparse
import pymupdf as fitz
P=Path(__file__).resolve().parent;R=P.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True,choices=['r02','r03','r04','r05']);args=parser.parse_args()
dest=P/'builds'/args.revision;shutil.copytree(P/'candidate/src',dest)
runs=[]
for i,name in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
 cmd=[str(R/'scratch/tectonic/tectonic.exe'),'-C','-k','--keep-logs',name+'.tex']
 run=subprocess.run(cmd,cwd=dest,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (dest/f'console_{i}_{name}.txt').write_text(run.stdout+run.stderr,encoding='utf-8');runs.append({'command':cmd,'exit':run.returncode})
 (dest/'execution.json').write_text(json.dumps(runs,indent=2))
 if run.returncode:raise RuntimeError('Compile failed; logs preserved')
summary={}
for name in ['main','TERRA_SUPPLEMENT']:
 doc=fitz.open(dest/(name+'.pdf'));log=(dest/(name+'.log')).read_text(encoding='utf-8',errors='replace');pages=[p.get_text() for p in doc]
 summary[name]={'pages':len(doc),'sha256':hashlib.sha256((dest/(name+'.pdf')).read_bytes()).hexdigest(),'overfull':re.findall(r'Overfull[^\n]*',log),'underfull_count':log.count('Underfull'),'undefined':re.findall(r'(?:Reference|Citation)[^\n]*undefined',log),'duplicates':re.findall(r'[^\n]*(?:multiply defined|duplicate destination)[^\n]*',log),'question_marks':[i+1 for i,t in enumerate(pages) if '??' in t]}
 (dest/(name+'.txt')).write_text('\n\f\n'.join(pages),encoding='utf-8')
 out=P/'renders'/args.revision/name;out.mkdir(parents=True)
 for i,page in enumerate(doc):page.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(out/f'page_{i+1:02}.png')
(dest/'BUILD_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
