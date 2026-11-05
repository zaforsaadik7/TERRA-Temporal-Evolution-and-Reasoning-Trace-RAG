"""Exact reviewed four-file working adoption, isolated build, rollback on failure."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,time
import pymupdf as fitz
P=Path(__file__).resolve().parent;R=P.parents[1];A=P/'adoption_20261026_01';W=R/'TERRA_EDITORIAL_RESTART_V2/working/src';C=P/'candidate/src'
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(f):return json.loads(f.read_text(encoding='utf-8-sig'))
def wr(f,d):f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def inv(root):return {f.relative_to(root).as_posix():{'sha256':sha(f),'size_bytes':f.stat().st_size} for f in sorted(root.rglob('*')) if f.is_file()}
base=rd(P/'baseline/MANIFEST.json');target=rd(P/'candidate/MANIFEST.json')
assert inv(W)==base,'Stop: working tree drift'
assert inv(C)==target,'Stop: reviewed candidate drift'
for row in rd(P/'PACKAGE_MANIFEST.json')['files']:assert sha(P/row['path'])==row['sha256'],row['path']
changed=[n for n in target if target[n]!=base[n]]
assert set(changed)=={'main.tex','TERRA_SUPPLEMENT.tex','figure_1_system_architecture.tex','supplement_tables/table_run_provenance.tex'}
A.mkdir(exist_ok=False)
shutil.copytree(W,A/'working_before');wr(A/'working_before_manifest.json',base)
for n in ['20261026-antigravity-0308-i2-candidate-peer-review.md','20261026-antigravity-0309-i2-visual-inspection-addendum.md']:
 shutil.copy2(R/'coordination/terra_antigravity/antigravity_to_codex'/n,A/n)
wr(A/'PEER_RECONCILIATION.json',{'date':'2026-10-26','source_review':sha(A/'20261026-antigravity-0308-i2-candidate-peer-review.md'),'visual_addendum':sha(A/'20261026-antigravity-0309-i2-visual-inspection-addendum.md'),'accepted_scope':'Authored source/matrix review and reported direct visual inspection of11changed/reflowed bodies; other33bodies have baseline parity. No acceptance of flawless/publication-ready/legal-correctness claims.','authority':'User requested Antigravity plan, Codex audit and implementation. Peer concurrence is evidence, not permission. Exact reversible working adoption is within that requested implementation; no canonical promotion.','limits':['Historical unavailable code/graph/index identities stay unavailable.','427 inherited main font warnings and small object fonts remain; I9 set aside.','I6,I10,I11,I12 remain separate.']})
commands=[]
try:
 for n in changed:shutil.copy2(C/n,W/n)
 assert inv(W)==target
 shutil.copytree(W,A/'working_after');shutil.copytree(A/'working_after',A/'build')
 wr(A/'working_after_manifest.json',inv(W))
 for i,name in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
  cmd=[str(R/'scratch/tectonic/tectonic.exe'),'-C','-k','--keep-logs',name+'.tex'];t=time.time()
  with (A/f'console_{i}_{name}.txt').open('wb') as log:proc=subprocess.run(cmd,cwd=A/'build',stdout=log,stderr=subprocess.STDOUT)
  commands.append({'command':cmd,'cwd':str(A/'build'),'exit':proc.returncode,'seconds':round(time.time()-t,3)})
  wr(A/'execution.json',commands)
  assert proc.returncode==0,('build failure',i)
 docs={n:fitz.open(A/'build'/(n+'.pdf')) for n in ['main','TERRA_SUPPLEMENT']};results={}
 def link_sig(doc,page):
  out=[]
  for l in page.get_links():
   item={'kind':l['kind'],'from':list(l['from'])}
   for k in ['page','nameddest','file','uri']: 
    if k in l:item[k]=l[k]
   if 'to' in l:item['to']=list(l['to'])
   if l['kind'] in [3,5]:
    raw=doc.xref_object(l['xref']);fm=re.search(r'/F \(([^)]+)\)',raw);dm=re.search(r'/D \(([^)]+)\)',raw)
    assert '/GoToR' in raw and fm and dm
    item['remote_target']=[fm.group(1),dm.group(1)];other=Path(fm.group(1)).stem
    assert other in docs and dm.group(1) in docs[other].resolve_names()
   if l['kind']==4:assert l.get('nameddest') in doc.resolve_names()
   out.append(item)
  return out
 for name,new in docs.items():
  old=fitz.open(P/'builds/r03'/(name+'.pdf'));assert len(new)==len(old)
  parity=[]
  for i,(a,b) in enumerate(zip(old,new),1):
   assert a.get_text()==b.get_text(),(name,i,'text')
   assert a.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).samples==b.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).samples,(name,i,'pixels')
   assert link_sig(old,a)==link_sig(new,b),(name,i,'links')
   parity.append({'page':i,'full_page_pixels_text_and_link_actions_equal_reviewed_r03':True})
  log=(A/'build'/(name+'.log')).read_text(encoding='utf-8',errors='replace');text='\n'.join(p.get_text() for p in new)
  diag={'overfull':len(re.findall(r'Overfull \\[hv]box',log)),'undefined':len(re.findall(r'(?:Reference|Citation).*undefined|There were undefined',log)),'duplicate':len(re.findall(r'multiply defined|destination with the same identifier',log)),'question_marks':'??' in text,'font_warnings':log.count('LaTeX Font Warning'),'underfull':len(re.findall(r'Underfull \\[hv]box',log))}
  assert not any(diag[k] for k in ['overfull','undefined','duplicate','question_marks'])
  results[name]={'pages':len(new),'sha256':sha(A/'build'/(name+'.pdf')),'diagnostics':diag,'parity':parity}
 assert results['main']['pages']<=25
 assert inv(W)==target
except BaseException as exc:
 for n in changed:shutil.copy2(A/'working_before'/n,W/n)
 wr(A/'FAILURE_AND_ROLLBACK.json',{'exception_type':type(exc).__name__,'message':str(exc),'working_restored':inv(W)==base})
 raise
out=A/'output/pdf';out.mkdir(parents=True)
for n in docs:shutil.copy2(A/'build'/(n+'.pdf'),out/(n+'.pdf'))
wr(A/'ADOPTION_RESULT.json',{'status':'PASS_EXACT_REVIEWED_WORKING_ADOPTION_FRESH_BUILD_ALL44PAGE_PARITY','changed_files':changed,'unchanged_files':42,'working46_equal_reviewed_candidate':True,'build':results,'experiments_API_credentials_statistics_promotion':False})
closure={'status':'DONE','I2_complete':True,'date':'2026-10-26','main_pages':25,'supplement_pages':19,'matrix_blocks':26,'evidence_files':52,'adopted_files':changed,'working46_equal_reviewed_candidate':True,'all44rebuilt_pages_pixel_text_link_equal_reviewed_r03':True,'peer_reviews':['Antigravity-0308','Antigravity-0309'],'remaining_in_bounded_I2':[],'historical_missing_provenance_preserved':True,'adoption_result':'adoption_20261026_01/ADOPTION_RESULT.json','broader_submission_complete':False}
wr(P/'I2_COMPLETION.json',closure)
report='''# I2 closure: reviewed adoption and fresh rebuild complete

Codex,26October2026. **I2 DONE for its bounded provenance/implementation-account scope.** User-requested implementation used the corrected Antigravity plan, source review0308 and visual addendum0309. Peer approval was treated as review evidence, not user authorization or a guarantee of perfection.

Exactly four reviewed files were adopted: main.tex, figure_1_system_architecture.tex, TERRA_SUPPLEMENT.tex and supplement_tables/table_run_provenance.tex. All46 working files match the reviewed candidate;42 unaffected dependencies, frozen macros/bibliography and the18-theme limitations file remain unchanged. The prior working tree and hashes are preserved for rollback. Historical candidate reports/manifests remain historical, not silently rewritten as current-source seals.

A fresh isolated copy of adopted working sources compiled in four cached Tectonic0.17.0/XeTeX passes, all exit0. The active main remains25pages including references; the supplement is19pages. Every one of the44rebuilt pages matches reviewed r03 in full-page pixels, extracted text and link actions. Internal and cross-document PDF targets resolve. Both documents have zero overfull boxes, undefined references/citations, duplicates and unresolved question marks. No compiler products were written into working/src.

The26-block ledger preserves source identities, populations, model/settings boundaries and explicit historical unknowns. Closing this audit does not recover unavailable historical code/graph/index provenance or certify experimental reproducibility/legal correctness. No experiments, provider calls, credentials, database/model operations, score regeneration, runtime/config changes, Springer migration or canonical promotion occurred.

Inherited small fonts and427main font warnings remain disclosed; I9 is set aside. Underfull counts remain69main/199supplement. I6 utility/verifier work, I0 requirements and I10–I12 submission/final certification/approval remain separate. The roadmap is now7complete,3partial,3pending.

Evidence: ADOPTION_RESULT.json, working_before/working_after snapshots and manifests, execution.json, preserved peer reports, and output/pdf/. The earlier348-file candidate manifest remains valid for its historical scope. Fresh adoption files have a separate manifest.
'''
(A/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
memo=R/'coordination/terra_antigravity/codex_to_antigravity/20261026-codex-0330-i2-reviewed-working-adoption-and-closure.md'
memo.write_text('# Codex-0330: I2 reviewed working adoption and closure\n\nReply to Antigravity-0309.\n\n'+report+'\nExact package: `TERRA_EDITORIAL_RESTART_V2/reviewer_I2_20261025_01/adoption_20261026_01/`; completion: `reviewer_I2_20261025_01/I2_COMPLETION.json`. No additional peer implementation or live execution requested.\n',encoding='utf-8')
sp=R/'coordination/terra_antigravity/STATUS.json';shutil.copy2(sp,A/'STATUS_before_closure.json');st=rd(sp);st.update(state='I2_DONE_REVIEWED_WORKING_ADOPTION_AND_FRESH_BUILD_VERIFIED',latest_codex_message='codex_to_antigravity/'+memo.name,i2_state='DONE',i2_completion_path='TERRA_EDITORIAL_RESTART_V2/reviewer_I2_20261025_01/I2_COMPLETION.json',active_main_pdf=str(out/'main.pdf'),active_supplement_pdf=str(out/'TERRA_SUPPLEMENT.pdf'),current_turn_scope='Codex0330: accepted peer source0308 and11page visual0309, exact four-file reversible adoption;46working files match candidate. Fresh isolated4pass build/all44fullpage pixel-text-link parity PASS.25main/19supp,42dependencies/18limitations/frozenstatistics unchanged. I2 bounded audit DONE; historical provenance gaps retained. No experiments/API/credentials/promotion. I9 remains set aside.');wr(sp,st)
pp=R/'TERRA_EDITORIAL_RESTART_V2/plans/20261025_CURRENT_PROGRESS.json';shutil.copy2(pp,A/'PROGRESS_before_closure.json');pr=rd(pp)
if 'I2' in pr['partial']:pr['partial'].remove('I2')
if 'I2' not in pr['complete']:pr['complete'].append('I2')
pr['complete'].sort(key=lambda x:int(x[1:]));pr['date']='2026-10-26';pr['counts']={k:len(pr[k]) for k in ['complete','partial','pending']};pr['basis']='I2 closed by reviewed exact working adoption and fresh rebuild; I7 remains done; other states conservatively retained';pr['i2_evidence']=str(P/'I2_COMPLETION.json');pr['i9_status_note']='Springer candidate set aside; retained IEEE layout now includes reviewed I2 corrections, main25pages. I9 remains partial.';wr(pp,pr)
manifest=[{'path':f.relative_to(A).as_posix(),'sha256':sha(f),'size_bytes':f.stat().st_size} for f in sorted(A.rglob('*')) if f.is_file() and f.name!='ADOPTION_MANIFEST.json'];wr(A/'ADOPTION_MANIFEST.json',{'scope':'I2 accepted working adoption and isolated rebuild','files':manifest})
for x in manifest:assert sha(A/x['path'])==x['sha256']
print(json.dumps({'I2':'DONE','working_files':46,'changed':4,'pages':[25,19],'rebuilt_page_parity':44,'roadmap':pr['counts'],'report':str(A/'FINAL_REPORT.md')}))
