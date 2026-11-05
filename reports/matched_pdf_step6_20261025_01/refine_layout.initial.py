from pathlib import Path
import shutil, subprocess, json, hashlib, re, difflib
import pymupdf as fitz
P=Path(__file__).resolve().parent
root=P.parents[1]
work=root/'TERRA_EDITORIAL_RESTART_V2/working/src'
dest=P/'final_src'
shutil.copytree(work,dest)
f=dest/'main.tex'; raw=f.read_bytes(); text=raw.decode()
old=r'& \oplus \; \texttt{"\textbackslash nOpinion Snippet: \{text\_snip[:1000]\}"}'
new=r'& \oplus \; \texttt{"\textbackslash nOpinion Snippet:}'+'\n'+r'\\ & \qquad \texttt{\{text\_snip[:1000]\}"}'
assert text.count(old)==1;text=text.replace(old,new)
old=r'\text{EASY}, & \text{if } \text{Low Complexity} \land \text{In-Domain} \\'+'\n'+r'\text{HARD}, & \text{if } \text{High Complexity} \lor \text{Out-of-Domain}'
new=r'\text{EASY}, & \begin{gathered}\text{Low Complexity}\\[-2pt]\land\ \text{In-Domain}\end{gathered} \\[6pt]'+'\n'+r'\text{HARD}, & \begin{gathered}\text{High Complexity}\\[-2pt]\lor\ \text{Out-of-Domain}\end{gathered}'
assert text.count(old)==1;text=text.replace(old,new)
old='In the separate prospective controlled comparison, Among the 100 assessable'
assert text.count(old)==1;text=text.replace(old,'In the separate prospective controlled comparison, among the 100 assessable')
f.write_bytes(text.encode())
(P/'layout_source.diff').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),text.splitlines(True),fromfile='working/main.tex',tofile='isolated_final/main.tex')))
runs=[]
for i,name in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
 cmd=[str(root/'scratch/tectonic/tectonic.exe'),'-C','-k','--keep-logs',name+'.tex']
 run=subprocess.run(cmd,cwd=dest,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (P/f'final_{i}_{name}.console.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
 runs.append({'command':cmd,'exit':run.returncode});(P/'final_execution.json').write_text(json.dumps(runs,indent=2))
 if run.returncode:raise RuntimeError(name+' failed')
summary={}
for name in ['main','TERRA_SUPPLEMENT']:
 doc=fitz.open(dest/(name+'.pdf')); log=(dest/(name+'.log')).read_text(errors='replace');pages=[p.get_text() for p in doc]
 render=P/f'final_{name}_pages';render.mkdir()
 for i,page in enumerate(doc): page.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).save(render/f'page_{i+1:02}.png')
 (P/f'final_{name}.txt').write_text('\n\f\n'.join(pages),encoding='utf-8')
 summary[name]={'pages':len(doc),'sha256':hashlib.sha256((dest/(name+'.pdf')).read_bytes()).hexdigest(),'overfull':log.count('Overfull'),'underfull':log.count('Underfull'),'undefined':re.findall(r'(?:Reference|Citation)[^\n]*undefined',log),'multiply_defined':re.findall(r'[^\n]*multiply defined[^\n]*',log),'question_marks':[i+1 for i,t in enumerate(pages) if '??' in t],'matched_pages':[i+1 for i,t in enumerate(pages) if '0.26885' in t or 'Prospective controlled' in t]}
(P/'FINAL_BUILD_RESULTS.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
