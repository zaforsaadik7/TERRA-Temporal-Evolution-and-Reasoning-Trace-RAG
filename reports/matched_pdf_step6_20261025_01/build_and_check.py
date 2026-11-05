from pathlib import Path
import hashlib, json, shutil, subprocess, re, time
import pymupdf as fitz

ROOT = Path(r'F:\TERRA -Copy')
OUT = Path(__file__).resolve().parent
WORK = ROOT/'TERRA_EDITORIAL_RESTART_V2/working/src'
STUDY = ROOT/'reports/matched_study_r03_20261025_01'
COMPILER = ROOT/'scratch/tectonic/tectonic.exe'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(p): return {f.relative_to(p).as_posix(): {'sha256':digest(f),'bytes':f.stat().st_size} for f in sorted(p.rglob('*')) if f.is_file()}

before = inventory(WORK)
(OUT/'working_before.json').write_text(json.dumps(before,indent=2))
results = {}
for label, source in [('baseline', STUDY/'manuscript_before'), ('candidate',WORK)]:
    dest=OUT/label
    shutil.copytree(source,dest)
    executions=[]
    for i,name in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
        command=[str(COMPILER),'-C','-k','--keep-logs',name+'.tex']
        start=time.monotonic()
        run=subprocess.run(command,cwd=dest,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (OUT/f'{label}_{i}_{name}.console.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
        executions.append({'command':command,'cwd':str(dest),'exit':run.returncode,'seconds':time.monotonic()-start})
        (OUT/f'{label}_execution.json').write_text(json.dumps(executions,indent=2))
        if run.returncode: raise RuntimeError(f'{label} {name} compile failed; inspect saved console')
    summary={}
    for name in ['main','TERRA_SUPPLEMENT']:
        pdf=dest/(name+'.pdf'); doc=fitz.open(pdf)
        log=(dest/(name+'.log')).read_text(encoding='utf-8',errors='replace')
        pages=[page.get_text() for page in doc]
        (OUT/f'{label}_{name}.txt').write_text('\n\f\n'.join(pages),encoding='utf-8')
        summary[name]={'pages':len(doc),'sha256':digest(pdf),'undefined':re.findall(r'(?:Reference|Citation)[^\n]*undefined',log),'multiply_defined':re.findall(r'[^\n]*multiply defined[^\n]*',log),'overfull':log.count('Overfull'),'underfull':log.count('Underfull'),'question_marks':[i+1 for i,t in enumerate(pages) if '??' in t], 'matched_pages':[i+1 for i,t in enumerate(pages) if '0.26885' in t or 'Prospective controlled' in t]}
        render=OUT/f'{label}_{name}_pages';render.mkdir()
        for i,page in enumerate(doc): page.get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).save(render/f'page_{i+1:02}.png')
    results[label]=summary
    (OUT/'BUILD_RESULTS.json').write_text(json.dumps(results,indent=2))
    print(label,json.dumps(summary),flush=True)
assert inventory(WORK)==before,'Working source changed during isolated build'
(OUT/'working_after.json').write_text(json.dumps(inventory(WORK),indent=2))
print('ISOLATED_BUILDS_COMPLETE_WORKING_SOURCE_UNCHANGED',flush=True)
