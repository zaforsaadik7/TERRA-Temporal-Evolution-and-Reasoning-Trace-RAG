from pathlib import Path
import subprocess,json,re,hashlib,difflib,time,sys
from pypdf import PdfReader
out=Path(__file__).parent; src=out/'candidate_src'
if len(sys.argv)>1: src=out/sys.argv[1]
results=[]
run_id=str(time.time_ns())
for name in ['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main']:
    run=subprocess.run(['F:/TERRA -Copy/scratch/tectonic/tectonic.exe','-C','-k','--keep-logs',name+'.tex'],cwd=src,capture_output=True,text=True,encoding='utf-8',errors='replace')
    i=len(results)+1
    (out/f'build_console_{run_id}_{i}_{name}.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
    results.append({'document':name,'exit':run.returncode,'command':run.args})
    if run.returncode: break
(out/f'build_execution_{run_id}.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
if any(x['exit'] for x in results): raise SystemExit(1)
summary={}
for name in ['main','TERRA_SUPPLEMENT']:
    reader=PdfReader(src/(name+'.pdf')); text='\n'.join(p.extract_text() or '' for p in reader.pages)
    (out/(name+'_text.txt')).write_text(text,encoding='utf-8')
    log=(src/(name+'.log')).read_text(encoding='utf-8',errors='replace')
    summary[name]={'pages':len(reader.pages),'sha256':hashlib.sha256((src/(name+'.pdf')).read_bytes()).hexdigest(),'undefined':re.findall(r"(?:Reference|Citation) .+ undefined",log),'overfull_boxes':len(re.findall('Overfull',log)),'float_too_large':'Float too large' in log}
    print(name,summary[name])
(out/'build_verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
diff=''
for p in src.rglob('*.tex'):
    rel=p.relative_to(src); b=out/'baseline_src'/rel
    before=b.read_text(encoding='utf-8').splitlines(True) if b.exists() else []
    diff+=''.join(difflib.unified_diff(before,p.read_text(encoding='utf-8').splitlines(True),fromfile='baseline/'+str(rel),tofile='candidate/'+str(rel)))
(out/'source.diff').write_text(diff,encoding='utf-8')
if summary['main']['pages']>25: raise SystemExit('Page ceiling exceeded; no publication')
