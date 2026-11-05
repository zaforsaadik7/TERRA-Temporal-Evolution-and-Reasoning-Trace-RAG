"""Exact I6 working adoption; isolated build; rollback on verification failure."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,time
import pymupdf as fitz
P=Path(__file__).resolve().parent;R=P.parents[1];A=P/'adoption_20261026_01';W=R/'TERRA_EDITORIAL_RESTART_V2/working/src';C=P/'candidate/src'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def wr(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def inv(root):return {f.relative_to(root).as_posix():{'sha256':sha(f),'size_bytes':f.stat().st_size} for f in sorted(root.rglob('*')) if f.is_file()}
before=rd(P/'baseline/MANIFEST.json');target=rd(P/'candidate/MANIFEST.json');assert inv(W)==before,'Working baseline drift';assert inv(C)==target,'Reviewed candidate drift'
original_manifest=rd(P/'PACKAGE_MANIFEST.json')
for x in original_manifest['files']:assert sha(P/x['path'])==x['sha256'],x['path']
changed=[n for n in before if target.get(n)!=before[n]];added=list(set(target)-set(before))
assert set(changed)=={'matched_comparison_main.tex','TERRA_SUPPLEMENT.tex'} and added==['supplement_utility_audit.tex']
protected=[x for x in rd(P/'ledgers/INPUT_MANIFEST.json')['files'] if '/COMPLETED/ASSESSMENT_AUTHOR_' in x['path'] or x['path'] in ['data/terra_canonical_v2_eval.json','terra_350_benchmark.json'] or x['path'].endswith(('events.jsonl','calls.jsonl'))]
for x in protected:assert sha(R/x['path'])==x['sha256']
A.mkdir(exist_ok=False);shutil.copytree(W,A/'working_before');wr(A/'working_before_manifest.json',before)
old_completion=(P/'I6_COMPLETION.json').read_bytes();(A/'prior_checkpoint').mkdir();(A/'prior_checkpoint/I6_COMPLETION.json').write_bytes(old_completion)
peer=R/'coordination/terra_antigravity/antigravity_to_codex/20261026-antigravity-0311-i6-candidate-peer-review.md';shutil.copy2(peer,A/peer.name)
wr(A/'PEER_RECONCILIATION.json',{'date':'2026-10-26','peer_sha256':sha(peer),'accepted':'Authored source/evidence concurrence and stated actual visual inspection of17changed/reflowed bodies. Existing self-checks/ledgers do not become independent new legal adjudication.','corrections':['I2 active supplement was19pages, not18:21pages adds2.','948document occurrences are not necessarily948unique CAP files.','Original peer memo contains shell-escape/control-character path damage; actual candidate r03 paths/identities were independently resolved; original memo preserved.','Section S4 reference occurs in the included matched_comparison_main.tex, not a new edit to main.tex.','No claim that the peer independently replayed all scripts or re-adjudicated all primary sources is inferred from report/ledger inspection.'],'authority':'User approved implementing complete R01 plan and renewed request complete it. This is authority for exact reversible reviewed working adoption; peer review itself is not permission.','not_approved_or_claimed':'No canonical promotion, submission, new experiments, credentials, score changes or expert legal validation.'})
commands=[]
try:
 for n in changed+added:shutil.copy2(C/n,W/n)
 assert inv(W)==target
 shutil.copytree(W,A/'working_after');shutil.copytree(A/'working_after',A/'build');wr(A/'working_after_manifest.json',target)
 for i,n in enumerate(['TERRA_SUPPLEMENT','main','TERRA_SUPPLEMENT','main'],1):
  cmd=[str(R/'scratch/tectonic/tectonic.exe'),'-C','-k','--keep-logs',n+'.tex'];t=time.time()
  with (A/f'console_{i}_{n}.txt').open('wb') as log:cp=subprocess.run(cmd,cwd=A/'build',stdout=log,stderr=subprocess.STDOUT)
  commands.append({'command':cmd,'cwd':str(A/'build'),'exit':cp.returncode,'seconds':round(time.time()-t,3)});wr(A/'execution.json',commands);assert cp.returncode==0,('Build failed',i)
 docs={n:fitz.open(A/'build'/(n+'.pdf')) for n in ['main','TERRA_SUPPLEMENT']};results={}
 def links(doc,page):
  result=[]
  for l in page.get_links():
   x={'kind':l['kind'],'from':list(l['from'])}
   for k in ['page','nameddest','file','uri']:
    if k in l:x[k]=l[k]
   if 'to' in l:x['to']=list(l['to'])
   if l['kind']==4:assert l.get('nameddest') in doc.resolve_names()
   if l['kind'] in [3,5]:
    raw=doc.xref_object(l['xref']);fm=re.search(r'/F \(([^)]+)\)',raw);dm=re.search(r'/D \(([^)]+)\)',raw);assert '/GoToR' in raw and fm and dm
    x['remote_target']=[fm.group(1),dm.group(1)];other=Path(fm.group(1)).stem;assert other in docs and dm.group(1) in docs[other].resolve_names()
   result.append(x)
  return result
 for n,new in docs.items():
  old=fitz.open(P/'builds/r03'/(n+'.pdf'));assert len(old)==len(new);parity=[]
  for i,(x,y) in enumerate(zip(old,new),1):
   assert x.get_text()==y.get_text(),(n,i,'text')
   assert x.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).samples==y.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).samples,(n,i,'pixels')
   assert links(old,x)==links(new,y),(n,i,'links');parity.append({'page':i,'full_pixels_text_and_link_actions_match_reviewed_r03':True})
  log=(A/'build'/(n+'.log')).read_text(encoding='utf-8',errors='replace');text='\n'.join(p.get_text() for p in new)
  d={'overfull':len(re.findall(r'Overfull \\[hv]box',log)),'undefined':len(re.findall(r'(?:Reference|Citation).*undefined|There were undefined',log)),'duplicate':len(re.findall(r'multiply defined|destination with the same identifier',log)),'question_marks':'??' in text,'font_warnings':log.count('LaTeX Font Warning'),'underfull':len(re.findall(r'Underfull \\[hv]box',log))};assert not any(d[k] for k in ['overfull','undefined','duplicate','question_marks'])
  results[n]={'pages':len(new),'sha256':sha(A/'build'/(n+'.pdf')),'diagnostics':d,'parity':parity}
 assert results['main']['pages']==25 and results['TERRA_SUPPLEMENT']['pages']==21;assert inv(W)==target
 for x in protected:assert sha(R/x['path'])==x['sha256']
except BaseException as exc:
 for n in changed:shutil.copy2(A/'working_before'/n,W/n)
 for n in added:
  f=W/n;assert f.resolve().parent==W.resolve();f.unlink(missing_ok=True)
 wr(A/'FAILURE_AND_ROLLBACK.json',{'exception':type(exc).__name__,'message':str(exc),'restored':inv(W)==before});raise
out=A/'output/pdf';out.mkdir(parents=True)
for n in docs:shutil.copy2(A/'build'/(n+'.pdf'),out/(n+'.pdf'))
result={'status':'PASS_EXACT_REVIEWED_I6_ADOPTION_AND_FRESH_BUILD','existing_changed':changed,'added':added,'unaffected_baseline_files':44,'working_files':47,'all_working_files_equal_reviewed_candidate':True,'all46rebuilt_pages_full_pixel_text_link_parity':True,'protected_raw_and_original_workbook_hashes_unchanged':True,'build':results}
wr(A/'ADOPTION_RESULT.json',result)
closure={'status':'DONE','I6_complete':True,'scope':'Bounded useful-answer/proxy/source-verification and verifier-rate feasibility audit; not independent legal validation or full satisfaction of reviewer point5','date':'2026-10-26','main_pages':25,'supplement_pages':21,'matched_inputs_verified':700,'sample_queries':40,'sample_arm_outcomes':80,'source_occurrences':948,'unlocated_snippet_spans':23,'independent_legal_sufficiency_references':0,'verifier_false_acceptance_rejection_rates':'NOT_ESTIMATED_NO_INDEPENDENT_REFERENCE','final_synthetic_tests':28,'working_files':47,'adopted':True,'adopted_existing_files':changed,'added_source':added,'all46rebuilt_pages_full_pixel_text_link_parity':True,'remaining_in_bounded_I6':[],'adoption_result':'adoption_20261026_01/ADOPTION_RESULT.json','expert_assessment_component_fulfilled':False,'canonical_promotion':False,'broader_submission_complete':False}
wr(P/'I6_COMPLETION.json',closure)
transitions=[{'path':'I6_COMPLETION.json','before_sha256':hashlib.sha256(old_completion).hexdigest(),'after_sha256':sha(P/'I6_COMPLETION.json'),'before_preserved':'adoption_20261026_01/prior_checkpoint/I6_COMPLETION.json','reason':'User-authorized reviewed adoption closes the mutable status index; original417-entry candidate manifest is preserved, not silently rewritten.'}]
for row in original_manifest['files']:
 if row['path']=='I6_COMPLETION.json':assert row['sha256']==transitions[0]['before_sha256']
 else:assert sha(P/row['path'])==row['sha256'],row['path']
wr(A/'HISTORICAL_MANIFEST_TRANSITIONS.json',{'original_manifest_rows':len(original_manifest['files']),'unchanged_rows':len(original_manifest['files'])-1,'transitions':transitions})
report='''# I6 complete: reviewed working adoption and fresh rebuild

Codex,26October2026. **I6 DONE for the approved bounded audit/reporting scope.** The user authorized the full R01 implementation and renewed the request to complete it. Antigravity-0311 supplies peer concurrence and reported actual inspection of17changed/reflowed bodies; its claim of independent ledger checks is retained with the limits in PEER_RECONCILIATION.json, not expanded into expert/source adjudication.

Two existing files were adopted exactly (matched_comparison_main.tex,TERRA_SUPPLEMENT.tex), and supplement_utility_audit.tex was added. All47working files equal the reviewed r03candidate. All44unaffected baseline sources, frozen statistics/bibliography, original assessment input and the18-theme limitations file remain byte-identical. Original XLSX and selected raw/journal hashes were checked before/after. Complete46-file pre-adoption and47-file post-adoption snapshots provide rollback. No model/API/database/credential operations, new human ratings, experimental reruns, statistics-score regeneration, Springer migration or canonical promotion occurred.

Four cached isolated Tectonic0.17.0/XeTeX passes exit0. Main25pages including references; supplement21pages (I2was19, so+2). Every one of46rebuilt pages matches reviewed r03 in full-page pixels, extracted text and link actions; actual cross-document/internal destinations resolve. Both documents have zero overfull boxes, undefined citations/references, duplicate labels and unresolved question marks. The inherited427main font warnings and71/199underfull counts remain disclosed; I9 is still set aside. No compiler products were written into working/src.

The audit preserves the distinction between178H/78T generator invocations,77H/29T concordant-substantive judge labels and validated useful answers. On CategoryB the judge-label proxy is20H/1T, with73H/32T disagreements. These are descriptive event/proxy counts, not legal accuracy. The700actual verifier inputs survive, but no independent sufficiency reference was supplied; false-acceptance/rejection rates remain unestimated. The40-query/80-arm factual check covers948document occurrences, with1,873/1,896normalized spans located and23Snippet spans unlocated, all retained with explicit limits. Targeted historical/external flags remain separate, not population estimates. Original/reconciled author labels and14confirmed amendments remain unchanged. The28final tests and independent recount passed before review; unchanged analysis code was not needlessly rerun at adoption.

This closes an evidence-bounded audit, not the missing legal-expert study. Reviewer point5's expert component remains unfulfilled, and strict legal-correctness yield/verifier error rates are not manufactured. Existing legal/source unknowns remain documented under the approved R01 policy. I0,I9andI10–I12still apply; overall submission readiness is not claimed.

The historical417-entry candidate manifest remains preserved.416entries still match current bytes; its mutable I6_COMPLETION.json entry has an explicit before/after transition with original bytes preserved in prior_checkpoint/. Final adoption evidence has a separate manifest. Original reports and peer messages are not rewritten.

Deliverables:output/pdf/main.pdf and output/pdf/TERRA_SUPPLEMENT.pdf; exact build/source snapshots, execution.json, ADOPTION_RESULT.json, PEER_RECONCILIATION.json, HISTORICAL_MANIFEST_TRANSITIONS.json and ADOPTION_MANIFEST.json beside this report. Roadmap:8complete,2partial,3pending.
'''
(A/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
memo=R/'coordination/terra_antigravity/codex_to_antigravity/20261026-codex-0334-i6-reviewed-adoption-and-closure.md'
memo.write_text('# Codex-0334 — I6 reviewed adoption and closure\n\nReply to Antigravity-0311.\n\n'+report+'\nExact evidence:`TERRA_EDITORIAL_RESTART_V2/reviewer_I6_20261026_01/adoption_20261026_01/`. User implementation permission already covered this reversible adoption; no additional permission round was needed. Peer baseline19not18 and occurrence-vs-unique-file corrections are recorded without modifying the peer memo. No additional implementation requested.\n',encoding='utf-8')
sp=R/'coordination/terra_antigravity/STATUS.json';shutil.copy2(sp,A/'STATUS_before_closure.json');st=rd(sp);st.update(state='I6_DONE_REVIEWED_WORKING_ADOPTION_AND_FRESH_BUILD_VERIFIED',latest_codex_message='codex_to_antigravity/'+memo.name,i6_state='DONE',i6_completion_path='TERRA_EDITORIAL_RESTART_V2/reviewer_I6_20261026_01/I6_COMPLETION.json',active_main_pdf=str(out/'main.pdf'),active_supplement_pdf=str(out/'TERRA_SUPPLEMENT.pdf'),current_turn_scope='Codex0334: user-authorized exact I6 adoption after Antigravity0311review.2existing files changed,1added,47working files equal reviewed r03. Fresh isolated4pass build and all46fullpage pixel/text/link parity PASS;25main/21supp.44baseline dependencies/18limitations/frozenstatistics/originalworkbooks preserved. I6 bounded audit DONE; independent legal-sufficiency references absent and verifier rates unestimated; no expert-validity/full reviewer-point5 claim. No new experiments/API/credentials/promotion. I9setaside.');wr(sp,st)
pp=R/'TERRA_EDITORIAL_RESTART_V2/plans/20261025_CURRENT_PROGRESS.json';shutil.copy2(pp,A/'PROGRESS_before_closure.json');pr=rd(pp)
if 'I6' in pr['partial']:pr['partial'].remove('I6')
if 'I6' not in pr['complete']:pr['complete'].append('I6')
pr['complete'].sort(key=lambda x:int(x[1:]));pr['date']='2026-10-26';pr['counts']={k:len(pr[k]) for k in ['complete','partial','pending']};pr['i6_evidence']=str(P/'I6_COMPLETION.json');pr['basis']='I6 approved bounded audit closed by peer-reviewed exact adoption and fresh rebuild. Missing expert validation remains disclosed. Other states conservatively retained.';pr['i9_status_note']='Springer candidate set aside. Retained IEEE layout includes accepted I2/I6 corrections,25main/21supp; I9remains partial.';wr(pp,pr)
wr(A/'ADOPTION_MANIFEST.json',{'scope':'Final I6 reviewed working adoption and clean rebuild','files':[{'path':p.relative_to(A).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(A.rglob('*')) if p.is_file() and p.name!='ADOPTION_MANIFEST.json']})
for x in rd(A/'ADOPTION_MANIFEST.json')['files']:assert sha(A/x['path'])==x['sha256']
print(json.dumps({'I6':'DONE','adopted_existing_files':2,'added_files':1,'working_files':47,'pages':[25,21],'full_page_parity':46,'roadmap':pr['counts'],'report':str(A/'FINAL_REPORT.md')}))
