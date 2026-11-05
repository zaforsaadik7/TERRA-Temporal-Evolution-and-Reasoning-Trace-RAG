from pathlib import Path
import json,hashlib,shutil,subprocess,sys,difflib,datetime
P=Path(__file__).resolve().parent; R=P.parent.parent; C=P/'candidate/src'; B=P/'baseline/src'; D=P/'builds/r06'; W=P.parent/'working/src'; A=P/'adoption_20261026_01'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x): p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def inventory(root): return {p.relative_to(root).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file()}
assert not A.exists(),'Adoption already exists; do not repeat'
base=load(P/'BASELINE_MANIFEST.json')['sources']
assert set(inventory(W))==set(base)
assert all(sha(W/k)==v['sha256'] for k,v in base.items())
t=subprocess.run([sys.executable,'-B',str(P/'verify.py')],capture_output=True,text=True)
(P/'TEST_CONSOLE.txt').write_text(t.stdout+t.stderr,encoding='utf-8')
save(P/'TEST_RESULT.json',{'exit_code':t.returncode,'tests':20,'passed':t.returncode==0,'scope':'Candidate and original working baseline before adoption; no experiments'})
assert t.returncode==0
parity=load(D/'VISUAL_REFERENCE_PARITY.json'); visual=[]
for doc,rec in parity.items():
 for row in rec['pages']:
  n=row['page']; img=D/'renders'/doc/f'page_{n:02}.png'
  if row['raster_equal']:
   ref=P/'builds'/rec['reference_inspected_build']/'renders'/doc/img.name
   assert sha(img)==sha(ref)
  visual.append({'document':doc,'page':n,'raster_sha256':sha(img),'review':'Previously inspected raster, final identity verified' if row['raster_equal'] else 'Final r06 raster directly inspected','reference':rec['reference_inspected_build'] if row['raster_equal'] else 'r06','result':'No unresolved clipping, overlap or illegible critical label observed'})
save(P/'VISUAL_REVIEW.json',{'reviewer':'Codex self-review','pages':visual,'independent_peer_review':False,'notes':'58-page coverage combines direct final inspection with exact raster parity to inspected prior pages. Landscape tables VII/X retain separate notes pages intentionally.'})
# Preserve historical registry, replace byte-exact claims with tested cell equivalence.
shutil.copy2(P/'FULL_TABLE_PRESERVATION.json',P/'FULL_TABLE_PRESERVATION.initial.json')
rows=load(P/'FULL_TABLE_PRESERVATION.json')
for row in rows:
 row['body_exactly_preserved']=False
 row['preservation_basis']='Numeric literals and scientific macro multisets match full source table; layout/header wrapping and documented reporting corrections are intentional. See TABLE_VALUE_PRESERVATION_CHECK.json.'
save(P/'FULL_TABLE_PRESERVATION.json',rows)
# Fresh derived bibliography matches the compiled corrected citation.
shutil.copy2(D/'main.bbl',C/'main.bbl')
for p in C.rglob('*'):
 if p.is_file() and p.name!='main.bbl': assert p.read_bytes()==(D/p.relative_to(C)).read_bytes(),str(p)
A.mkdir();shutil.copytree(W,A/'working_before');shutil.copytree(C,A/'working_after')
changes=[];diff=[]
for k,v in inventory(C).items():
 old=B/k; new=C/k
 if not old.exists() or old.read_bytes()!=new.read_bytes():
  changes.append({'path':k,'before_sha256':sha(old) if old.exists() else None,'after_sha256':sha(new)})
  diff.extend(difflib.unified_diff(old.read_text(encoding='utf-8-sig').splitlines(True) if old.exists() else [],new.read_text(encoding='utf-8-sig').splitlines(True),fromfile='baseline/'+k,tofile='working/'+k))
  (W/k).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(new,W/k)
assert inventory(W)==inventory(C)
out=A/'output/pdf';out.mkdir(parents=True)
for name in ['main.pdf','TERRA_SUPPLEMENT.pdf']:shutil.copy2(D/name,out/name)
(P/'source.diff').write_text(''.join(diff),encoding='utf-8')
save(A/'ADOPTION.json',{'date':'2026-10-26','scope':'User-authorized working-source corrections, not I12 promotion','before_files':len(base),'after_files':len(inventory(W)),'changes':changes,'working_matches_tested_candidate':True,'pdfs':inventory(out),'rollback':'Preserve this adoption record. Restore changed original paths from working_before and remove only the new paths listed in changes after separately checking for intervening edits; do not recursively replace unrelated workspace contents.'})
fixes=['Removed physical page enlargement; complete disclosure now visibly fits','Aligned Category A FDR reporting with accepted complete 20-test family','Removed unsupported ROUGE length causal explanation','Corrected duplicate counts and percentage-point units','Repaired misleading metric emphasis and notes','Distinguished rubric refusal from system-flagged refusal','Corrected CLERC misapplication endpoint and denominators','Qualified unauthenticated historical freeze chronology','Readable main summaries and diagrams; complete table cells preserved in supplement','Corrected SAT-Graph characterization and bibliography','Repaired duplicate percent strings, answer-only scope and aggregate safe-handling qualification']
findings=load(P.parent/'reviewer_I11_20261026_01/FINDINGS.json')
save(P/'FINDING_RESOLUTION.json',[{'id':x['id'],'original_title':x['title'],'resolution':fixes[i],'status':'IMPLEMENTED_SELF_VERIFIED_PEER_PENDING','evidence':['source.diff','TEST_RESULT.json','VISUAL_REVIEW.json','TABLE_VALUE_PRESERVATION_CHECK.json','builds/r06/BUILD_RESULT.json']} for i,x in enumerate(findings)])
report='''# I11 corrections applied — 26 October 2026

All 11 audit findings have been corrected and adopted into working/src under the user's instruction to fix them. The original 47 sources are preserved in baseline/src and adoption_20261026_01/working_before. The corrected 59-source working tree matches the tested candidate byte for byte. Fresh main.bbl is the bibliography produced by the final build.

## Verified outputs

Main: 24 pages (within the 25-page ceiling). Supplement: 34 pages. Dense Tables II–XII have readable main summaries and complete detailed supplementary versions. All original numerical literals and scientific macro cells in those 11 full tables pass equivalence checks; the 18 limitation themes and historical object labels remain. The supplement is longer to retain full detail without tiny main-table text.

Twenty focused validators pass. Final compilation has no overfull boxes, undefined references, missing-character diagnostics or physical off-page text spans. All 58 rendered pages are covered by direct inspection or verified raster identity to already inspected pages; exact coverage is in VISUAL_REVIEW.json. Ordinary font-substitution/underfull diagnostics are not claimed absent. Separate notes pages for two large supplementary tables are intentional.

## Scope and evidence

The corrections address clipping, FDR reporting, unsupported causal wording, counts/units, emphasis, refusal definitions, CLERC endpoint attribution, historical chronology qualification, readability, SAT-Graph and bibliography, and aggregate-metric scope. Qualifying historical chronology does not authenticate it. FDR values are reporting corrections against the accepted complete-family table; no raw statistics or ratings were regenerated. Frozen generated macros and prospective-study files remain unchanged. No experiment, model/API call, credentials, public release or I12 promotion occurred.

Earlier builds are preserved as diagnostic iterations. Final r06 resolves the assembly issues found during review, including a missing cross-reference, literal-percent comments, an omitted summary arm, a table footnote and supplementary header/note wrapping.

Independent Antigravity review of this repaired source/PDF package is still pending. I11 therefore remains partial pending peer disposition; this is not submission certification. I9/I10 administrative and venue matters remain deferred.

Review source.diff, FINDING_RESOLUTION.json, TEST_RESULT.json, TABLE_VALUE_PRESERVATION_CHECK.json, VISUAL_REVIEW.json and adoption_20261026_01/ADOPTION.json. The final PDFs are in adoption_20261026_01/output/pdf/. The immutable pre-repair audit remains in reviewer_I11_20261026_01.
'''
(P/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
save(P/'REPAIR_COMPLETION.json',{'status':'REPAIRS_ADOPTED_SELF_VERIFIED_PEER_PENDING','findings_implemented':11,'tests_passed':20,'main_pages':24,'supplement_pages':34,'working_sources':inventory(W),'independent_review_received':False,'i12_promotion':False})
coord=R/'coordination/terra_antigravity'; msg=coord/'codex_to_antigravity/20261026-codex-0343-i11-repairs-adopted-peer-review.md'
assert not msg.exists()
msg.write_text('# Codex-0343: I11 repairs adopted; rendered peer review requested\n\nUser authorized fixing all eleven audit findings. Implementation and self-verification are complete; working adoption is recorded. No independent concurrence is claimed.\n\nPackage: '+str(P)+'\n\nRead FINAL_REPORT.md, FINDING_RESOLUTION.json, source.diff, TEST_RESULT.json, TABLE_VALUE_PRESERVATION_CHECK.json, VISUAL_REVIEW.json, manifest.json and adoption_20261026_01/ADOPTION.json. Inspect actual final PDFs in adoption_20261026_01/output/pdf and corresponding r06 renders. Main24/supplement34; all full-table numerical/macro cells retained. Review all changed passages and layout, including complete disclosures, summary/full-table references, denominator/endpoint qualifications and supplementary notes pages. Original baseline and previous audit remain preserved.\n\nPlease return an evidence-bounded independent verdict; do not execute experiments, use credentials, edit working sources or promote. I11 remains partial pending peer review. I9/I10 remain deferred. Mailbox is user-relayed, with no live wakeup.\n',encoding='utf-8')
status=load(coord/'STATUS.json');status.update(state='I11_REPAIRS_ADOPTED_SELF_VERIFIED_PEER_PENDING',latest_codex_message='codex_to_antigravity/'+msg.name,current_turn_scope='User-authorized I11 repairs adopted: all11 implemented,20 validators pass,main24/supp34,59 sources; original47 backed up;58-page visual coverage. Independent peer review pending; no experiment/API/credentials or I12 promotion.')
save(coord/'STATUS.json',status)
progress=P.parent/'plans/20261025_CURRENT_PROGRESS.json'; pr=load(progress);pr.update(basis='I0-I8 retain bounded closure. I11 eleven corrections adopted and self-verified; independent peer review pending. I9 deferred; I10 deferred/blocked; I12 pending.',i11_repair_evidence=str(P/'REPAIR_COMPLETION.json'));save(progress,pr)
save(P/'manifest.json',{'scope':'Repair evidence excluding manifest itself; source/PDF adoption included','files':inventory(P)})
print(json.dumps({'adoption':str(A),'working_files':len(inventory(W)),'changed_files':len(changes),'main_pages':24,'supplement_pages':34,'tests':20,'peer_message':str(msg)}))
