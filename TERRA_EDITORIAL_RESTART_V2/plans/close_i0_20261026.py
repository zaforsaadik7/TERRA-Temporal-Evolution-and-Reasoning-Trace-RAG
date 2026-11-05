from pathlib import Path
import hashlib,json,shutil
R=Path('F:/TERRA -Copy');T=R/'TERRA_EDITORIAL_RESTART_V2';P=T/'reviewer_I0_20261026_03';C=P/'closure_20261026_01';W=T/'working/src'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
assert not C.exists(); C.mkdir()
m=load(P/'PACKAGE_MANIFEST.json')
for r in m['files']:assert h(P/r['path'])==r['sha256'],r['path']
b=load(P/'BASELINE_MANIFEST.json')['source']
assert set(b)=={f.relative_to(W).as_posix() for f in W.rglob('*') if f.is_file()}
for k,r in b.items():assert h(W/k)==r['sha256'],k
peer=R/'coordination/terra_antigravity/antigravity_to_codex/20261026-antigravity-0314-i0-candidate-peer-review.md'
recon=load(T/'reviewer_I0_peer_reconciliation_20261026_01/RECONCILIATION.json');assert h(peer)==recon['peer_sha256']
st=R/'coordination/terra_antigravity/STATUS.json';pr=T/'plans/20261025_CURRENT_PROGRESS.json'
for p in [st,pr,P/'I0_COMPLETION.json']:shutil.copy2(p,C/('prior_'+p.name))
approval='Yes, I approve keeping the current representation of the ROUGE-L trade-off in prose and Table III, with the reference-versus-itself row omitted. Please close I0 and advance progress to 9 complete, 1 partial, 3 pending.'
write(C/'USER_RATIFICATION.json',{'date':'2026-10-26','source':'latest human message relaying the explicit approval statement to Codex','approval_text':approval,'scope':'Ratify current OBJ08 prose/TableIII representation and omit reference self-comparison row; close I0. No manuscript edit or broader scientific/promotion authority.'})
obj=load(P/'LEXICAL_OBJECT_DISPOSITION.json');obj.update({'item_specific_removal_authorization':'USER_RATIFIED_20261026','I0_closure_blocker':False,'scientific_scope':'20system values retained; original three1.000reference-self-comparison values intentionally omitted by approved disposition. Not a claim of literal table identity.'});write(C/'OBJ08_FINAL_DISPOSITION.json',obj)
comp={'status':'DONE','I0_complete':True,'date':'2026-10-26','scope':'Accepted baseline and reviewer requirements freeze/consolidation; not final scientific or venue certification','implementation_package':str(P),'implementation_peer_review':str(peer),'peer_sha256':h(peer),'remaining_in_bounded_I0':[],'user_ratification':'USER_RATIFICATION.json','verified_package_entries':len(m['files']),'working_sources_unchanged':47,'main_pages':25,'supplement_pages':21,'original_object_count':26,'original_label_destinations':25,'approved_prose_representations':1,'limitation_themes':18,'reviewer_point5_fully_satisfied':False,'canonical_promotion':False,'roadmap_counts':{'complete':9,'partial':1,'pending':3}}
write(C/'I0_COMPLETION.json',comp)
progress=load(pr);progress['complete']=['I'+str(i) for i in range(9)];progress['partial']=['I9'];progress['counts']=comp['roadmap_counts'];progress['i0_evidence']=str(C/'I0_COMPLETION.json');progress['basis']='I0 baseline/requirements completed after Antigravity0314concurrence and explicit user OBJ08representation ratification. I9partial/setaside; I10–I12pending. Missing expert validation and venue compliance remain disclosed.'
status=load(st);status.update({'state':'I0_DONE_PEER_REVIEWED_USER_RATIFIED','i0_state':'DONE','i0_completion_path':(C/'I0_COMPLETION.json').relative_to(R).as_posix(),'latest_codex_message':'codex_to_antigravity/20261026-codex-0337-i0-user-ratified-closure.md','current_turn_scope':'I0closed after peer0314and actual user relay approval for existing OBJ08representation.84reviewed package entries/47working sources reverified. No manuscript/PDF/scientificchanges;25main/21supp. Historical reviewed84entrypackage preserved, new separate closuremanifest. Roadmap9complete/1partial/3pending; I9setaside; I10–I12pending. No submission/venue/expert-validity claim.'})
report='''# I0 complete — reviewed baseline and requirements

26October2026. **I0 DONE.** Antigravity0314concurrence reconciled; user approved retaining the ROUGE-L trade-off in prose and TableIII with the reference-versus-itself row omitted. All20system metric values remain; the original three1.000self-comparison values are deliberately omitted under this disposition. No literal table-identity or unqualified losslessness claim.

All84reviewed implementation entries and all47working source hashes/membership reverified. Manuscript and PDFs unchanged:25main/21supp. Original26objects accounted for as25active label/destinations plus1approved prose representation;18limitation themes,10reviewer obligations,32historical R findings and F01–F06 indexed. Corrected graph and historical provenance remain distinct. Peer review coverage limits in the prior reconciliation remain applicable; no peer rerun is invented.

The historical implementation report/completion record remain unchanged as pre-closure evidence. This folder contains the authoritative final I0completion and user ratification, preserving prior coordination/progress bytes. Separate closuremanifest avoids invalidating the earlier84entrymanifest.

Roadmap: **9complete (I0–I8),1partial (I9),3pending (I10–I12).** I9Springer conversion stays set aside. I10submission/availability requirements, I11full scientific/visual/clean-room certification and I12separate promotion/submission approval remain. Reviewerpoint5expertassessment and independent verifier gold are still absent; journal compliance is unconfirmed. I0administrative/evidence closure does not turn those gaps into completed research.

No manuscript edits, new experiments, provider/credential/database/model operations, format conversion, public release or canonical promotion occurred.
'''
(C/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
write(C/'VERIFICATION.json',{'reviewed84_entries_unchanged':True,'working47_unchanged':True,'peer_identity_match':True,'prior_snapshots_preserved':True,'closure_authority':'USER_RATIFICATION.json'})
write(pr,progress);write(st,status)
write(C/'CLOSURE_MANIFEST.json',{'files':[{'path':f.relative_to(C).as_posix(),'bytes':f.stat().st_size,'sha256':h(f)} for f in sorted(C.rglob('*')) if f.is_file()]})
for row in load(C/'CLOSURE_MANIFEST.json')['files']:assert h(C/row['path'])==row['sha256']
assert load(pr)['counts']=={'complete':9,'partial':1,'pending':3}
assert load(st)['i0_state']=='DONE'
print(json.dumps(comp))
