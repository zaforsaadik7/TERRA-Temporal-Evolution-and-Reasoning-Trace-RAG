from pathlib import Path
import json,hashlib,re,datetime
R=Path('F:/TERRA -Copy');T=R/'TERRA_EDITORIAL_RESTART_V2';P=T/'reviewer_I0_20261026_03';W=T/'working/src'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def put(n,o):
    p=P/n;p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def md(n,s):(P/n).write_text(s,encoding='utf-8')
index=load(P/'SOURCE_DOCUMENT_INDEX.json')
def ev(p):
    k=p.relative_to(R).as_posix();index[k]={'path':str(p),'sha256':h(p),'bytes':p.stat().st_size};return k
# Preserve initial self-check report before refining the explicit unresolved gate.
for n in ['FINAL_REPORT.md','I0_COMPLETION.json','VALIDATION_RESULT.json','PACKAGE_MANIFEST.json','SOURCE_DOCUMENT_INDEX.json','OBJECT_MAP.json']:
    q=P/'prior_finalization'/n;q.parent.mkdir(exist_ok=True);assert not q.exists();q.write_bytes((P/n).read_bytes())
old=T/'phase3/batch02/applied/snapshot_pre/main.tex';s=old.read_text(encoding='utf-8-sig')
label=s.index(r'\label{tab:rouge_tradeoff}');a=s.rfind(r'\begin{table}',0,label);b=s.index(r'\end{table}',label)+len(r'\end{table}')
block=s[a:b];macros=sorted(set(re.findall(r'\\([A-Za-z]+)',block)))
metric=[m for m in macros if any(x in m for x in ['Rouge','MeanWords'])]
alltex={f.relative_to(W).as_posix():f.read_text(encoding='utf-8-sig') for f in W.rglob('*.tex')}
cells=[]
for m in metric:
    loc=[{'file':k,'line':i} for k,v in alltex.items() for i,line in enumerate(v.splitlines(),1) if '\\'+m in line]
    cells.append({'macro':m,'current_locations':loc,'retained':bool(loc)})
assert len(metric)==20 and all(c['retained'] for c in cells)
prior=T/'phase1_codex_20261008/peer_review_addendum_01/CODEX_RESPONSE.md'
ev(old);ev(prior)
put('LEXICAL_OBJECT_DISPOSITION.json',{'object':'OBJ08','historical_label':'tab:rouge_tradeoff','historical_source':ev(old),'earlier_explicit_approval_gap':ev(prior),'current_cell_check':cells,'system_metric_cells_retained':20,'source_reference_length_70_8_retained':'70.8' in alltex['main.tex'],'unrendered_original_self_comparison_values':[1.0,1.0,1.0],'representation':'metric/mean-word information moved into prose and CatB performance table','item_specific_removal_authorization':'NOT_RECOVERED','scope':'No lost system metric identified; omission of self-comparison row and table form needs ratification or restoration decision. No manuscript changed.','decision_options':['Ratify current prose/table representation with omission of tautological self-comparison row','Request readable supplementary restoration as separately reviewed manuscript patch'],'scientific_final_certification_owner':'I11','I0_closure_blocker':True})
o=load(P/'OBJECT_MAP.json')
for row in o['objects']:
    if row['id']=='OBJ08':
        row['equivalence_check']='LEXICAL_OBJECT_DISPOSITION.json';row['status']='PARTIAL';row['owner']='I0';row['next_action']='User ratification of existing representation, or authorized compact-table restoration; then I11 final certification.'
put('OBJECT_MAP.json',o)
claims=load(P/'CLAIM_MAP.json');checks=[]
for c in claims['claims']:
    needle=c.get('candidate_text','');path=c.get('source');found=bool(needle and needle in alltex.get(path,''))
    checks.append({'id':c['id'],'file':path,'exact_I7_candidate_text_still_present':found,'interpretation':'unchanged exact passage' if found else 'later accepted I2/I6 edits or formatting may supersede text; no current defect inferred; final claim reading I11'})
put('CLAIM_CURRENT_LOCATION_CHECKS.json',checks)
# Preserve historical numbered subfinding sources instead of inventing absent IDs.
put('FINDING_ID_COVERAGE.json',{'R_ids':sorted(r['id'] for r in load(P/'CLOSURE_REGISTER.json') if re.fullmatch(r'R\d+',r['id'])),'F_ids':['F01','F02','F03','F04','F05','F06'],'reviewer_ids':[r['id'] for r in load(P/'REQUIREMENTS.json')],'limits':'Historical R IDs derived from actual CSV/doc records; no invented consecutiveness or automatic verified closure.'})
md('AUTHORIZATION.md','# User authorization\n\nCurrent26October2026 request:\n\n> implement the whole thing and then report me back like before between that you don\'t need to report or stop. complete it without any error and with best possible outcome. while implementation if you face any errors then solve them by yourself with the best possible solution. after completion, report me back\n\nApplied to reviewed I0 plan0335. Routine local defects repaired, earlier partial attempts preserved. No authority invented to change scientific objects, venue, manuscript or promote.\n')
put('EXECUTION_NOTES.json',{'failed_attempts':[{'directory':'reviewer_I0_20261026_01','cause':'wrong supplement key in adopted JSON; stopped before baseline copy','remedy':'read actual key TERRA_SUPPLEMENT; fresh output02'},{'directory':'reviewer_I0_20261026_02','cause':'old object08 label absent in actual accepted baseline; stopped instead of asserting false parity','remedy':'preserved partial output; fresh output03 explicitly maps source/disposition gap'}],'final_output':'reviewer_I0_20261026_03','experimental_retries':0,'source_or_data_mutations':0,'not_rerun':['compiler','scientific analyses','provider study','models','database'],'script_copies':[ev(T/'plans/implement_i0_20261026.py'),ev(Path(__file__))]})
validation=load(P/'VALIDATION_RESULT.json');validation.update({'original_objects_with_live_label_and_aux':25,'original_objects_in_prose_disposition':1,'all20_system_metric_cells_retained':True,'I0_closure_blockers':['OBJ08 representation/removal approval not established','actual implementation peer review pending'],'status':'PASS_INVENTORY_AND_PROTECTION_WITH_EXPLICIT_CLOSURE_GAPS'})
put('VALIDATION_RESULT.json',validation)
comp=load(P/'I0_COMPLETION.json');comp.update({'status':'IMPLEMENTATION_SELF_VERIFIED_CLOSURE_PENDING','I0_complete':False,'remaining':validation['I0_closure_blockers'],'implementation_complete':True})
put('I0_COMPLETION.json',comp)
put('SOURCE_DOCUMENT_INDEX.json',index)
report='''# I0 implementation report — accepted baseline and requirements

Codex,26October2026. **Implementation and self-verification complete; I0 closure pending the specific checks below.** No manuscript/source/PDF/data changes occurred.

## Completed

- Preserved47accepted build sources and25main/21supplement PDFs. All168I6adoption manifest entries rehashed; working membership/bytes and both PDF identities match the adopted version.
- Corrected graph archive streamed and verified against its full historical manifest digest, preserved in place; no graph decompression/database/model/credential/provider operations.
- Preserved reviewer letter,10atomic reviewer obligations,32historical R findings, F01–F06,13original work-package definitions and18limitation themes. Historical flags remain historical; I11 full-claim certification is not fabricated.
- Mapped all26original scientific objects:25retain active source labels and actual compiled destinations. One original lexical table has a prose/table successor documented below. Peer0313's12main+11supp split is not adopted as fact.
- Page contract records retained IEEE conference layout and25physical main pages including references as the operational ceiling;21supplement pages is an observation, not a cap. Neither final venue compliance nor the advisor's supplement-exclusion rule is authenticated. Springer conversion remains set aside under I9.
- Reviewerpoint5 remains partial: no blinded legal-expert study or independent verifier-sufficiency gold; strict legal yield/verifier rates are not invented. Original ratings,23unlocated snippet spans and all adverse results remain preserved.
- Positive/reference/protection checks passed; four negative fixtures rejected duplicate IDs, unsupported closure, unknown status and missing owner. Current source locations for I7claim patches are separately checked without falsely reopening later accepted edits.

## Exact remaining closure items

1. **Original lexical table OBJ08:** all20system metric/mean-word macro cells remain in current prose/TableIII; reference length70.8and method notes remain. The original three1.000reference-versus-itself cells and table form are not rendered. An8October audit explicitly left item-specific removal approval unresolved; targeted authorization/mailbox search did not recover it. `LEXICAL_OBJECT_DISPOSITION.json` gives current locations and two concrete choices: ratify the accepted prose representation with the tautological self-comparison row omitted, or authorize a readable supplement-table patch. This is a pre-existing authorization/disposition gap, not loss introduced by I0. No source was changed to conceal it.
2. **Antigravity must review this actual package.** Its0313concurrence reviewed the plan only; it cannot stand in for output review. A frozen handoff requests evidence/register/OBJ08 checks. There is no live channel and no notification inferred.

Neither item requires new experimental data or provider calls. The exact historical reviewedPDF/originalcorrespondence remain UNRECOVERED, explicitly mapped by scientific object; this is an allowed documented provenance fallback, not fabricated identity.

## Status

Roadmap remains8complete/2partial/3pending. I0will move toDONE and9/1/3only after the above are reconciled. I9remains partial/setaside; I10submission/availability, I11scientific/visual/clean-room certification, I12separate promotion/submission remain pending. This is not publication-readiness certification.

Earlier stopped inventory attempts01/02are preserved with causes/remedies in EXECUTION_NOTES. Use only03as the review candidate. PACKAGE_MANIFEST pins this output; source/protection records preserve the accepted manuscript and all prior reports. No further action on human decisions is inferred from elapsed time or peer silence.
'''
md('FINAL_REPORT.md',report)
# Independent pass over every output and referenced source identity.
for k,row in index.items():assert h(R/k)==row['sha256'],k
base=load(P/'BASELINE_MANIFEST.json')['source']
assert {p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_file()}==set(base)
for k,row in base.items():assert h(W/k)==row['sha256']
put('FINAL_VERIFICATION.json',{'all_indexed_source_hashes_match':len(index),'working_sources_match':47,'all_outputs_valid_json':all(isinstance(load(f),(dict,list)) for f in P.rglob('*.json')),'source_or_pdf_edits':0,'closure_not_falsely_claimed':True})
put('PACKAGE_MANIFEST.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[{'path':f.relative_to(P).as_posix(),'bytes':f.stat().st_size,'sha256':h(f)} for f in sorted(P.rglob('*')) if f.is_file() and f!=P/'PACKAGE_MANIFEST.json']})
statuspath=R/'coordination/terra_antigravity/STATUS.json';status=load(statuspath)
status.update({'i0_state':'IMPLEMENTATION_SELF_VERIFIED_CLOSURE_PENDING','i0_completion_path':'TERRA_EDITORIAL_RESTART_V2/reviewer_I0_20261026_03/I0_COMPLETION.json','latest_codex_message':'codex_to_antigravity/20261026-codex-0336-i0-implemented-registers-and-object-disposition-review.md','current_turn_scope':'I0 authorized local implementation03:47source freeze/25+21PDF/168adoption hashes;26object inventory including25active labels and OBJ08prose-disposition authority gap;18themes/10reviewer obligations/32Rfindings/F01–F06. No manuscript/science/provider/credential operations. I0notDONE pending actual peer review and original lexical representation disposition; roadmap8/2/3.'})
statuspath.write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':comp['status'],'system_metric_cells':20,'sources_verified':len(index),'package':str(P)}))
