from pathlib import Path
import subprocess,json,shutil,hashlib,re,sys
import pymupdf as fitz
P=Path(__file__).resolve().parent;R=P.parents[1];rev=sys.argv[1];D=P/'builds'/rev
shutil.copytree(P/'candidate/src',D)
runs=[]
for i,n in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
    cmd=[str(R/'scratch/tectonic/tectonic.exe')]+([] if '--fetch-missing' in sys.argv else ['-C'])+['-k','--keep-logs',n+'.tex']
    q=subprocess.run(cmd,cwd=D,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (D/f'console_{i}_{n}.txt').write_text(q.stdout+q.stderr)
    runs.append({'command':cmd,'exit':q.returncode})
    (D/'execution.json').write_text(json.dumps(runs,indent=2))
    if q.returncode:
        print((q.stdout+q.stderr)[-4500:]);sys.exit(q.returncode)
result={}
for n in ['main','TERRA_SUPPLEMENT']:
    doc=fitz.open(D/(n+'.pdf'));log=(D/(n+'.log')).read_text(errors='replace')
    pages=[p.get_text() for p in doc]
    result[n]={'pages':len(doc),'sha256':hashlib.sha256((D/(n+'.pdf')).read_bytes()).hexdigest(),'overfull':re.findall(r'Overfull[^\n]*',log),'underfull':log.count('Underfull'),'font_warnings':re.findall(r'[^\n]*(?:Font shape|font shape|Missing character)[^\n]*',log),'undefined':re.findall(r'(?:Reference|Citation)[^\n]*undefined',log),'duplicates':re.findall(r'[^\n]*(?:multiply defined|duplicate destination)[^\n]*',log),'question_marks':[i+1 for i,t in enumerate(pages) if '??' in t]}
    (D/(n+'.txt')).write_text('\n\f\n'.join(pages),encoding='utf-8')
    out=P/'renders'/rev/n;out.mkdir(parents=True)
    for i,p in enumerate(doc):p.get_pixmap(matrix=fitz.Matrix(1.25,1.25),alpha=False).save(out/f'page_{i+1:02}.png')
(D/'BUILD_RESULT.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
