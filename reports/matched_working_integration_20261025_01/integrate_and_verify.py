from pathlib import Path
import hashlib,json,shutil,subprocess,re,difflib
import pymupdf as fitz
R=Path(r'F:\TERRA -Copy');P=Path(__file__).resolve().parent
W=R/'TERRA_EDITORIAL_RESTART_V2/working/src'
REVIEW=R/'reports/matched_pdf_step6_20261025_01'
STUDY=R/'reports/matched_study_r03_20261025_01'
PEER=R/'coordination/terra_antigravity/antigravity_to_codex/20261025-antigravity-0300-step6-pdf-and-page-budget-peer-review.md'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inv(root):return {f.relative_to(root).as_posix():{'sha256':h(f),'size_bytes':f.stat().st_size} for f in sorted(root.rglob('*')) if f.is_file()}
before=inv(W);expected=json.loads((REVIEW/'working_before.json').read_text())
assert set(before)==set(expected)
assert all(row['sha256']==expected[k]['sha256'] for k,row in before.items()),'Working input drift'
for package,key in [(STUDY,'size_bytes'),(REVIEW,'bytes')]:
 rows=json.loads((package/'manifest.json').read_text())['files']
 for row in rows:
  f=Path(row['path']);assert f.stat().st_size==row[key] and h(f)==row['sha256'],str(f)
target=REVIEW/'final_src/main.tex';assert target.is_file()
original=(W/'main.tex').read_text(encoding='utf-8');revised=target.read_text(encoding='utf-8')
diff=''.join(difflib.unified_diff(original.splitlines(True),revised.splitlines(True),fromfile='working_before/main.tex',tofile='working_after/main.tex'))
assert diff.splitlines()[2:]==(REVIEW/'layout_source.diff').read_text(encoding='utf-8').splitlines()[2:],'Reviewed patch mismatch'
assert len(re.findall(r'^@@',diff,re.M))==3
shutil.copytree(W,P/'working_before')
(P/'working_before_manifest.json').write_text(json.dumps(before,indent=2))
(P/'source.diff').write_text(diff,encoding='utf-8')
(P/'AUTHORIZATION.md').write_text('User: okay properly complete it so that we can mark it as done. Applies to annotated three-region working-source integration and rebuild, not canonical promotion or new experiments.\n',encoding='utf-8')
shutil.copy2(target,W/'main.tex')
after=inv(W);assert [k for k in before if before[k]!=after[k]]==['main.tex']
shutil.copytree(W,P/'working_after')
(P/'working_after_manifest.json').write_text(json.dumps(after,indent=2))
build=P/'build';shutil.copytree(W,build)
runs=[]
for i,name in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
 cmd=[str(R/'scratch/tectonic/tectonic.exe'),'-C','-k','--keep-logs',name+'.tex']
 result=subprocess.run(cmd,cwd=build,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (P/f'console_{i}_{name}.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
 runs.append({'command':cmd,'cwd':str(build),'exit':result.returncode})
 (P/'execution.json').write_text(json.dumps(runs,indent=2))
 if result.returncode:raise RuntimeError(f'{name} compile failed; preserved logs, no retry')
results={}
out=P/'output/pdf';out.mkdir(parents=True)
for name in ['main','TERRA_SUPPLEMENT']:
 pdf=build/(name+'.pdf');doc=fitz.open(pdf);prior=fitz.open(REVIEW/'output/pdf'/(name+'.pdf'))
 assert len(doc)==len(prior)
 log=(build/(name+'.log')).read_text(encoding='utf-8',errors='replace')
 problems=re.findall(r'(?:Reference|Citation)[^\n]*undefined|[^\n]*multiply defined[^\n]*',log)
 assert not problems and 'Overfull' not in log
 changed=[];texts=[]
 render=P/f'{name}_pages';render.mkdir()
 for i,page in enumerate(doc):
  texts.append(page.get_text())
  if page.get_pixmap().samples!=prior[i].get_pixmap().samples:changed.append(i+1)
  page.get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).save(render/f'page_{i+1:02}.png')
 assert not changed,changed
 assert not any('??' in text for text in texts)
 (P/(name+'.txt')).write_text('\n\f\n'.join(texts),encoding='utf-8')
 shutil.copy2(pdf,out/(name+'.pdf'))
 results[name]={'pages':len(doc),'sha256':h(pdf),'pixel_identical_to_peer_reviewed_pdf':True,'pixel_changed_pages':changed,'overfull':0,'undefined_or_duplicate_references':problems,'question_marks':False,'underfull':log.count('Underfull')}
assert results['main']['pages']==25 and results['TERRA_SUPPLEMENT']['pages']==18
assert inv(W)==after,'Working files changed during build'
delta=[];unchanged=0
for row in json.loads((STUDY/'manifest.json').read_text())['files']:
 f=Path(row['path']);actual=h(f)
 if actual!=row['sha256']:
  assert f.resolve()==(W/'main.tex').resolve()
  delta.append({'path':str(f),'before':row['sha256'],'after':actual,'reason':'Explicitly approved three-region layout integration'})
 else:unchanged+=1
assert len(delta)==1
receipt={'status':'MATCHED_COMPARISON_WORKING_INTEGRATION_COMPLETE','author':'Codex implementation self-verification','date':'2026-10-25','scope':'Reviewed equation wraps and conclusion capitalization integrated; fresh build and exact rendered parity with peer-reviewed Step6 PDFs','peer_report_sha256':h(PEER),'working_file_count':len(before),'changed_working_files':['main.tex'],'unchanged_working_files':len(before)-1,'source_diff_sha256':h(P/'source.diff'),'build':results,'historical_sealed_package':{'manifest_unchanged':True,'unchanged_rows':unchanged,'intentional_working_source_delta':delta},'network_api_model_calls':0,'statistics_changes':False,'canonical_promotion':False,'I7_I9_full_closure_claimed':False}
(P/'AUDIT_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2),flush=True)
