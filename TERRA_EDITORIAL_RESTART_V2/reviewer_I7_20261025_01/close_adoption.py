import json, hashlib
from pathlib import Path

ROOT=Path('F:/TERRA -Copy')
P=ROOT/'TERRA_EDITORIAL_RESTART_V2/reviewer_I7_20261025_01'
A=P/'adoption_20261025_01'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
r=read(A/'ADOPTION_RESULT.json')
assert r['working46files_equal_accepted_candidate'] and r['build']['main']['pages']==25
wm=read(A/'working_after_manifest.json')
W=ROOT/'TERRA_EDITORIAL_RESTART_V2/working/src'
assert len(wm)==46
for name,v in wm.items():
    assert sha(W/name)==v['sha256'] and (W/name).stat().st_size==v['size_bytes'],name
findings=read(P/'ledgers/FINDINGS_AND_DISPOSITIONS.json')
assert len(findings)==98
write(A/'FINAL_DISPOSITIONS.json',{'status':'VERIFIED_AND_ADOPTED','peer':'Antigravity-0303; reconciled AUROC erratum','findings':[{'id':f['id'],'file':f['file'],'status':'VERIFIED_AND_ADOPTED','working_sha256':wm[f['file']]['sha256']} for f in findings]})
c=read(P/'I7_COMPLETION.json')
c.update(status='DONE',I7_complete=True,local_batches_completed=[f'I7.{i}' for i in range(8)],working_sources_unchanged=False,working_sources_adopted=True,remaining_in_scope=[],adoption_result='adoption_20261025_01/ADOPTION_RESULT.json',final_dispositions='adoption_20261025_01/FINAL_DISPOSITIONS.json')
c['I7.7']='Antigravity-0303 PASS reconciled; exact 11-file adoption, fresh build and all43-page pixel/text/link parity PASS'
write(P/'I7_COMPLETION.json',c)
report='''# I7 final closure — 25 October 2026

**DONE.** All eight I7 batches are complete, including reconciled Antigravity-0303 review, working-source adoption and fresh PDF verification under the existing user authorization.

The 98 linked reporting edits were adopted in exactly 11 working files. All 46 working dependencies match the reviewed candidate; 35 files remain unchanged from the preserved baseline. Original figures, generated statistics, bibliography and all 18 limitation themes are retained. The six candidate ledgers remain preserved as historical review receipts; current final dispositions are in `adoption_20261025_01/FINAL_DISPOSITIONS.json`.

Fresh cached builds produce a **25-page main paper** and **18-page separate supplement**. All 43 pages are pixel-, text- and link-identical to the reviewed candidate. No overfull boxes, undefined references/citations, duplicate labels or unresolved question marks were found. Codex's complete candidate visual inspection carries through by exact page parity; Antigravity's receipt is not presented as an independent full-page visual inspection.

Inherited warnings remain disclosed: main 69 underfull boxes and 427 font-fallback warnings; supplement 211 underfull boxes. These and broader venue/dense-table readability requirements remain I9 matters. This closure does not certify journal formatting or the entire submission.

Antigravity's summary AUROC of 0.9416 is a report typo: preserved calculations and manuscript correctly use 0.9901333333333333, rounded to **0.9901**. Its original review is preserved unchanged alongside a reconciliation receipt. Numeric table labels are identified by source/hash rather than stale ordinal descriptions.

The changes reconcile estimands, historical/prospective provenance, verifier semantics, unsupported validation wording, operation counts and statistical interpretation. No experiment, model/API call, score regeneration, threshold change, assessor-rating change, canonical promotion or submission occurred. The matched result remains a gated-pipeline faithfulness result with 69/100 TERRA versus 4/100 Hybrid verifier refusals, not independent legal correctness or superior coverage.

Evidence: `adoption_20261025_01/ADOPTION_RESULT.json`, `working_after_manifest.json`, `PEER_RECONCILIATION.json`, fresh `output/pdf/`, and `CURRENT_PACKAGE_MANIFEST.json`. Original candidate-stage completion/report/resume/manifest are preserved in `adoption_20261025_01/prior_checkpoint/`.

Roadmap: **6 complete** (I1, I3, I4, I5, I7, I8), **4 partial** (I0, I2, I6, I9), **3 pending** (I10, I11, I12). Other package statuses are carried forward conservatively, not newly certified here.
'''
(P/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
(P/'RESUME.md').write_text('# I7 closed\n\nI7 is DONE. Read FINAL_REPORT.md and I7_COMPLETION.json. Do not rerun candidate/adoption helpers. No automatic authorization to start other roadmap packages or promote sources. Original candidate-stage receipts are preserved in adoption_20261025_01/prior_checkpoint/.\n',encoding='utf-8')
old=read(P/'PACKAGE_MANIFEST.json')
trans=[]
for row in old['files']:
    path=Path(row['path'])
    actual=sha(path)
    if actual!=row['sha256']:
        assert path in [P/x for x in ['FINAL_REPORT.md','I7_COMPLETION.json','RESUME.md']],str(path)
        preserved=A/'prior_checkpoint'/path.name
        assert sha(preserved)==row['sha256']
        trans.append({'path':str(path),'old_sha256':row['sha256'],'new_sha256':actual,'preserved_original':str(preserved),'reason':'authorized final administrative closure after adoption'})
write(A/'HISTORICAL_MANIFEST_TRANSITIONS.json',{'original_manifest_unchanged':True,'transitions':trans})
statuspath=ROOT/'coordination/terra_antigravity/STATUS.json'
(A/'STATUS_before_closure.json').write_bytes(statuspath.read_bytes())
s=read(statuspath)
memo='codex_to_antigravity/20261025-codex-0322-i7-working-adoption-and-closure.md'
s.update(state='I7_COMPLETE_REVIEWED_WORKING_ADOPTION_AND_REBUILD_PASS',i7_state='DONE',latest_codex_message=memo,current_turn_scope='Codex-0322: Antigravity-0303 PASS reconciled, AUROC report typo corrected separately; exact11file working adoption,46file parity and fresh25main/18supp build PASS; all43pages pixel/text/link identical to inspected candidate. I7 DONE. No new API/model/statistics changes or canonical promotion.',i7_completion_path='TERRA_EDITORIAL_RESTART_V2/reviewer_I7_20261025_01/I7_COMPLETION.json')
write(statuspath,s)
(ROOT/'coordination/terra_antigravity'/memo).write_text('# Codex-0322: I7 working adoption and closure\n\n'+report+'\nThis is a saved user-relayed coordination record, not an automatic wake or direct dispatch.\n',encoding='utf-8')
write(ROOT/'TERRA_EDITORIAL_RESTART_V2/plans/20261025_CURRENT_PROGRESS.json',{'date':'2026-10-25','authoritative_plan':'20261008_REVIEWER_INTEGRATED_SUBMISSION_PLAN.md','complete':['I1','I3','I4','I5','I7','I8'],'partial':['I0','I2','I6','I9'],'pending':['I10','I11','I12'],'counts':{'complete':6,'partial':4,'pending':3},'basis':'I7 newly closed by reviewed adoption; other statuses conservatively carried forward','i7_evidence':str(P/'I7_COMPLETION.json')})
rows=[{'relative_path':p.relative_to(P).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(P.rglob('*')) if p.is_file() and p.name!='CURRENT_PACKAGE_MANIFEST.json']
write(P/'CURRENT_PACKAGE_MANIFEST.json',{'scope':'I7 final working adoption and closure; historical candidate seal preserved','files':rows})
for row in rows: assert sha(P/row['relative_path'])==row['sha256']
print(json.dumps({'status':'DONE','manifest_files':len(rows),'working_files_verified':len(wm),'final_dispositions':len(findings),'main_pages':25,'supplement_pages':18,'historical_admin_transitions':len(trans)}))
