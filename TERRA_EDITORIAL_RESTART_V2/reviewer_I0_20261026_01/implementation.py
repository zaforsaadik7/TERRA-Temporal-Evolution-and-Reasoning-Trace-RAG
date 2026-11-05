"""One-shot local I0 inventory. No experimental, provider or manuscript writes."""
from pathlib import Path
import csv, datetime, hashlib, json, re, shutil

ROOT=Path('F:/TERRA -Copy'); T=ROOT/'TERRA_EDITORIAL_RESTART_V2'
P=T/'reviewer_I0_20261026_01'; W=T/'working/src'
AD=T/'reviewer_I6_20261026_01/adoption_20261026_01'
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def safe(p):
    p=p.absolute()
    assert p.is_relative_to(ROOT),str(p)
    for q in [p,*p.parents]:
        if q==ROOT.parent: break
        assert not q.is_symlink() and not (getattr(q.stat(),'st_file_attributes',0)&0x400),str(q)
    return p
def record(p):
    safe(p); return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def txt(p): return p.read_text(encoding='utf-8-sig')
def save(n,o):
    f=P/n; f.parent.mkdir(parents=True,exist_ok=True)
    assert not f.exists(),str(f)
    temp=f.with_name(f.name+'.part'); temp.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); temp.rename(f)
def md(n,s):
    f=P/n;f.parent.mkdir(parents=True,exist_ok=True)
    with f.open('x',encoding='utf-8') as z:z.write(s)
def csvread(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
inputs={}
def evidence(p):
    key=p.relative_to(ROOT).as_posix()
    if key not in inputs:inputs[key]=record(p)
    return key
def snapshot(root):return {p.relative_to(root).as_posix():record(p) for p in sorted(root.rglob('*')) if p.is_file()}

assert not P.exists(),'Existing output: do not overwrite'
P.mkdir()
shutil.copy2(__file__,P/'implementation.py')
before=snapshot(W); assert len(before)==47
accepted=snapshot(AD/'working_after')
assert set(before)==set(accepted)
assert all(before[k]['sha256']==accepted[k]['sha256'] for k in before)
ar=load(AD/'ADOPTION_RESULT.json'); assert ar['status'].startswith('PASS_')
for n,pdf in [('main','main.pdf'),('supplement','TERRA_SUPPLEMENT.pdf')]:
    f=AD/'output/pdf'/pdf; assert digest(f)==ar['build'][n]['sha256']
    assert ar['build'][n]['pages']==(25 if n=='main' else 21)
manifest=load(AD/'ADOPTION_MANIFEST.json'); checked=0
for row in manifest['files']:
    f=AD/row['path']
    # Account for documented mutable index transitions if present; immutable adoption files must match.
    assert f.stat().st_size==row['bytes'] and digest(f)==row['sha256'],str(f)
    checked+=1
for rel,r in before.items():
    dest=P/'baseline/src'/rel; dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(W/rel,dest)
    assert digest(dest)==r['sha256']
for pdf in ['main.pdf','TERRA_SUPPLEMENT.pdf']:
    dest=P/'baseline/pdf'/pdf;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(AD/'output/pdf'/pdf,dest)
save('BASELINE_MANIFEST.json',{'source':before,'pdfs':[record(P/'baseline/pdf'/p) for p in ['main.pdf','TERRA_SUPPLEMENT.pdf']],'accepted_manifest_entries_verified':checked,'source_matches_I6':True})
for f in ['STATUS.json']:
    shutil.copy2(ROOT/'coordination/terra_antigravity'/f,P/('prior_'+f))
shutil.copy2(T/'plans/20261025_CURRENT_PROGRESS.json',P/'prior_PROGRESS.json')
plan=T/'plans/20261008_REVIEWER_INTEGRATED_SUBMISSION_PLAN.md';pt=txt(plan);evidence(plan)
evidence(T/'plans/20261026_I0_IMPLEMENTATION_PLAN.md')
review=ROOT/'coordination/terra_antigravity/antigravity_to_codex/20261026-antigravity-0313-i0-implementation-plan-review.md';evidence(review)
letter=T/'reviewer_I0_I1a_20261008/REVIEWER_LETTER.md';evidence(letter)
shutil.copy2(letter,P/'baseline/REVIEWER_LETTER.md')
for f in [AD/'ADOPTION_RESULT.json',AD/'ADOPTION_MANIFEST.json',AD/'FINAL_REPORT.md',T/'reviewer_I6_20261026_01/I6_COMPLETION.json',T/'reviewer_I2_20261025_01/I2_COMPLETION.json',T/'reviewer_I7_20261025_01/I7_COMPLETION.json',T/'reviewer_I7_20261025_01/adoption_20261025_01/FINAL_DISPOSITIONS.json'] : evidence(f)

# Referenced graph preserved in place with contemporary streaming identity, no parsing.
G=T/'derived_graphs/r30corr_v1'; graph=G/'terra_eeg_index_20k_r30corr_v1.json.xz'
gref=next(x.split()[0] for x in txt(G/'manifest.sha256').splitlines() if x.endswith('  '+graph.name))
assert digest(graph)==gref
deps=[{'role':'corrected_graph_archive','preservation':'VERIFIED_IN_PLACE','historical_attribution':'not substituted for missing historical lineage',**record(graph)}]
for f in G.iterdir():
    if f.is_file() and f!=graph: evidence(f)
save('DEPENDENCY_ROLES.json',{'dependencies':deps,'not_in_scope':['vector database connections','full CAP corpus inventory','credentials','API endpoints'],'source_dependencies':'All47 build sources copied and independently hash matched; graph archive verified in place.'})
save('IDENTITY_RECONCILIATION.json',{'accepted_generation':'I6adoption_20261026_01','working_files':47,'accepted_manifest_verified':checked,'compiler_evidence':evidence(AD/'execution.json'),'current_page_counts':{'main':25,'supplement':21},'rebuild_performed':False,'older_Batch1':'historical lineage only','Springer':'set aside'})

# Build active input graph so unused historical sources cannot masquerade as rendered objects.
texts={k:txt(W/k) for k in before if k.endswith('.tex')}
def tree(start):
    seen=set(); queue=[start]
    while queue:
        k=queue.pop()
        if k in seen:continue
        assert k in texts,k;seen.add(k)
        for inc in re.findall(r'\\(?:input|include)\{([^}]+)\}',texts[k]):
            p=inc if inc.endswith('.tex') else inc+'.tex'
            if p in texts: queue.append(p)
    return seen
active={d:tree(f) for d,f in [('main','main.tex'),('supplement','TERRA_SUPPLEMENT.tex')]}
labels={}
for d,files in active.items():
    aux=txt(AD/'build'/('main.aux' if d=='main' else 'TERRA_SUPPLEMENT.aux'))
    evidence(AD/'build'/('main.aux' if d=='main' else 'TERRA_SUPPLEMENT.aux'))
    for k in files:
        for m in re.finditer(r'\\label\{([^}]+)\}',texts[k]):
            label=m[1]; a=re.search(r'\\newlabel\{'+re.escape(label)+r'\}\{\{([^}]*)\}\{([^}]*)\}',aux)
            labels.setdefault(label,[]).append({'document':d,'file':k,'line':texts[k][:m.start()].count('\n')+1,'rendered_number':a[1] if a else None,'rendered_page':a[2] if a else None,'compiled_aux_match':bool(a)})
objfile=T/'ledgers/object_register.csv';evidence(objfile); oldobjects=csvread(objfile);assert len(oldobjects)==26
objects=[]
for o in oldobjects:
    matches=labels.get(o['label'],[])
    assert len(matches)==1 and matches[0]['compiled_aux_match'],(o['object_id'],matches)
    refs=[]
    for d,files in active.items():
        for k in files:
            for line,s in enumerate(texts[k].splitlines(),1):
                if re.search(r'\\(?:ref|autoref|pageref|cref)\{(?:main-|supp-)?'+re.escape(o['label'])+r'\}',s):refs.append({'document':d,'file':k,'line':line})
    objects.append({'id':o['object_id'],'original':o,'current':matches[0],'incoming':refs,'status':'RESOLVED_VERIFIED','scope':'source/compiled-destination continuity; prior I6 full-render verification reused, not a new visual audit'})
assert sum(o['original']['env'].startswith('table') for o in objects)==23
save('OBJECT_MAP.json',{'objects':objects,'original_tables':23,'original_figures':3,'peer_12plus11_split':'not assumed; current locations derived from actual include graph','new_objects':{l:v for l,v in labels.items() if l.startswith(('tab:','fig:')) and l not in {o['label'] for o in oldobjects}}})
limfile=T/'ledgers/limitations_register.csv';evidence(limfile);lims=csvread(limfile)
limtext=texts['supplement_limitations.tex']; chunks=list(re.finditer(r'\\item\b',limtext));assert len(lims)==len(chunks)==18
lm=[]
for i,(l,m) in enumerate(zip(lims,chunks)):
    end=chunks[i+1].start() if i+1<len(chunks) else len(limtext);s=limtext[m.start():end]
    title=re.search(r'\\textbf\{(.+?)\}',s,re.S)
    assert title
    lm.append({'id':l['lim_id'],'original_theme':l['title'],'current_heading':title[1],'source':'supplement_limitations.tex','line':limtext[:m.start()].count('\n')+1,'text_sha256':hashlib.sha256(s.encode()).hexdigest(),'status':'RESOLVED_VERIFIED','scope':'18-theme sequence and accepted I6 unchanged-source protection; no claim underlying limitation solved'})
save('LIMITATION_MAP.json',lm)

# Every known finding receives a row, retaining the actual historical disposition.
corfiles=[T/'ledgers'/n for n in ['correction_register.csv','correction_register_phase1.csv','correction_register_phase1_rev1.csv']]
hist={}
for f in corfiles:
    evidence(f)
    for row in csvread(f):
        rid=row.get('id','');hist.setdefault(rid,[]).append({'source':f.relative_to(ROOT).as_posix(),'row':row})
findingdoc=ROOT/'docs/TERRA_COMPARATIVE_REVIEWER_ASSESSMENT.md';evidence(findingdoc)
for rid,title in re.findall(r'^### (R\d+)\s+[—–-]\s+(.+)$',txt(findingdoc),re.M):hist.setdefault(rid,[]).append({'source':findingdoc.relative_to(ROOT).as_posix(),'heading':title})
handoff=ROOT/'coordination/terra_antigravity/CONTEXT_HANDOFF.md';evidence(handoff)
frows=re.findall(r'^\| (F0[1-6]) \| (.*?) \| (.*?) \|',txt(handoff),re.M);assert len(frows)==6
reqs=[]
spec=[('REV1A','distance calibration','I1','ADDRESSED_WITH_SCOPE_LIMITATION','I1a current diagnostic reproduces threshold grid; original summary figures untraced and removed.'),('REV1B','66/62 chain and reproduction','I1','ADDRESSED_WITH_SCOPE_LIMITATION','Different stored historical/canonical outcomes separated; exact historical lineage unavailable.'),('REV2A','Figure1 and implementation account','I2','ADDRESSED_WITH_SCOPE_LIMITATION','Current source and architecture reconciled; unavailable historical code/index linkage disclosed.'),('REV2B','per-experiment graph/code/configuration','I2','ADDRESSED_WITH_SCOPE_LIMITATION','26 experiment blocks recorded with explicit unknowns.'),('REV3','fair paired comparison','I5','RESOLVED_VERIFIED','350 paired queries completed and audited; refusal disparity and design limits retained.'),('REV4','reasoning-trace novelty/title','I3','RESOLVED_VERIFIED','Approved proper-name and generic scaffold framing, not case-specific reasoning.'),('REV5A','useful-answer/coverage/error reporting','I6','ADDRESSED_WITH_SCOPE_LIMITATION','Operational and judge proxies only; strict legal correctness unestimated.'),('REV5B','independent verifier error rates','I6','PARTIAL','No independent sufficiency references; rates not estimated.'),('REV5C','blinded legal-expert assessment','I6','PARTIAL','Unavailable, author and automated checks cannot substitute; no request for experts.'),('REV5D','reliability scope under external weakness','I6','ADDRESSED_WITH_SCOPE_LIMITATION','Negative outcomes and limitations retained.')]
owners={'I1':T/'reviewer_I0_I1a_20261008/EXECUTION_AND_SELF_AUDIT_REPORT.md','I2':T/'reviewer_I2_20261025_01/I2_COMPLETION.json','I3':T/'working/src/main.tex','I5':ROOT/'reports/matched_study_r03_20261025_01/FINAL_REPORT.md','I6':T/'reviewer_I6_20261026_01/I6_COMPLETION.json'}
for id,title,owner,status,meaning in spec:
    ev=evidence(owners[owner]);reqs.append({'id':id,'requirement':title,'source':letter.relative_to(ROOT).as_posix(),'owner':owner,'status':status,'disposition':meaning,'evidence':[ev],'evidence_class':'accepted package/source record; not independent reproduction in I0','residual_owner':'I11' if status!='RESOLVED_VERIFIED' else None,'next_action':'Carry qualifications into final reviewer response; no new experiment authorized.'})
save('REQUIREMENTS.json',reqs)
closure=list(reqs)
for rid,entries in sorted(hist.items()):
    if not rid:continue
    closure.append({'id':rid,'source_history':entries,'status':'ADDRESSED_WITH_SCOPE_LIMITATION','owner':'I11','disposition':'Historical finding and disposition preserved. I7 adopted correction ledger/current source supplies candidate treatment; final all-claim certification belongs to I11. No blanket scientific closure inferred.','evidence':[evidence(T/'reviewer_I7_20261025_01/adoption_20261025_01/FINAL_DISPOSITIONS.json')],'next_action':'Check original finding against current text in I11; preserve scientific unknowns.','review_coverage':'I0 historical register consolidation; not fresh scientific re-adjudication'})
for rid,finding,needed in frows:
    status='PARTIAL' if rid=='F06' else 'ADDRESSED_WITH_SCOPE_LIMITATION'
    closure.append({'id':rid,'original_finding':finding,'required_evidence':needed,'source':handoff.relative_to(ROOT).as_posix(),'status':status,'owner':'I9' if rid=='F06' else 'I11','evidence':[evidence(AD/'FINAL_REPORT.md'),evidence(T/'reviewer_I7_20261025_01/I7_COMPLETION.json')],'disposition':'F06 font/readability remains I9; other historical findings tracked against adopted correction evidence, no claim that old artifact defects persist.','next_action':'Retain current typography caveats; I11 verifies full source/PDF against finding.'})
save('CLOSURE_REGISTER.json',closure)
claimsfile=T/'reviewer_I7_20261025_01/ledgers/CLAIMS.json';evidence(claimsfile)
claims=load(claimsfile)
for c in claims:
    c['historical_status']=c.pop('status',None);c['I0_status']='INDEXED_ACCEPTED_I7_NOT_REDECIDED';c['current_source_sha256']=before[c['source']]['sha256'] if c.get('source') in before else None
save('CLAIM_MAP.json',{'claims':claims,'accepted_disposition_reference':evidence(T/'reviewer_I7_20261025_01/adoption_20261025_01/FINAL_DISPOSITIONS.json'),'later_qualifications':[r for r in reqs if r['id'].startswith('REV5')],'protected_counterevidence':['Direct LLM CategoryB counter-result','D033/D034','historical false refusals','curated annotations','weak external results','matched CategoryB verifier refusals T69/H4','23 unlocated snippets are not proven legal errors']})
titles=dict(re.findall(r'^### (I\d+) [—–-] (.+)$',pt,re.M));assert len(titles)==13
progress=load(T/'plans/20261025_CURRENT_PROGRESS.json')
save('PACKAGE_STATUS.json',[{'id':id,'title':title,'status':'PARTIAL' if id in progress['partial'] else 'DONE' if id in progress['complete'] else 'PENDING','evidence_scope':'I0 consolidates accepted current index; does not independently recertify all packages'} for id,title in titles.items()])
save('REVIEWER_VERSION.json',{'status':'UNRECOVERED','preserved_letter':evidence(letter),'source_status':'User-pasted letter, original correspondence and sent-PDF identity explicitly unauthenticated','search_scope':['preserved REVIEWER_LETTER.md','integrated submission plan','coordination findings/handoff','I2/I6/I7 accepted records'],'historical_pdf_candidate':'Not assigned by page count or similarity','mapping':'scientific object/label rather than reviewer page numbers'})
save('FORMAT_AND_PAGE_CONTRACT.json',{'layout_observed':r'\documentclass[conference]{IEEEtran}','source':evidence(W/'main.tex'),'compiler':'Tectonic0.17.0/XeTeX per accepted I6 execution evidence','main_pages':25,'supplement_pages':21,'main_ceiling':25,'count_convention':'all physical main PDF pages including references and main appendices','convention_authority':'conservative operational rule, not authenticated verbatim advisor definition','supplement_ceiling':None,'supplement_exclusion_from_advisor_rule':'NOT_AUTHENTICATED','retention_authority':'User explicitly retained prior25page version and set aside Springer in conversation; this is an attributed summary not reconstructed verbatim correspondence','venue':'Artificial Intelligence and Law proposed in preserved letter; final author/advisor venue confirmation unavailable','venue_compliant':False,'I9':'partial, Springer set aside','I10':'live instructions/anonymity/availability still pending'})
md('AUTHORITY_AND_SCOPE.md','# I0 execution authority and boundaries\n\nUser authorized full implementation in the current26October2026 conversation: implement the whole thing and report after completion; routine in-scope fixes authorized. This record summarizes authority; it does not manufacture advisor correspondence. I0 only inventories existing local evidence, copies accepted47sources/PDFs and writes linked registers. No manuscript/experimental/API/credential/model/database/format/promotion operation occurred.\n')
md('REVIEWER_RESPONSE_MATRIX.md','# Internal reviewer response evidence matrix\n\nNot a sent letter or final I11response.\n\n'+'\n'.join('- **'+r['id']+' '+r['requirement']+'** — '+r['status']+'. '+r['disposition']+' Owner '+r['owner']+'.' for r in reqs)+'\n\nPoint5 remains partially addressed. Expert evaluation was not performed; useful-answer and verifier measures are proxies/feasibility results, not legal correctness. Reviewer acceptance of this narrower evidence is not presumed.\n')
save('PEER_RECONCILIATION.json',{'plan_peer':evidence(review),'verdict':'concurrence','implementation_peer_review':'PENDING_USER_RELAY','not_automatic':'plan review does not independently review produced registers','clarifications':['12main+11supp object split not assumed: actual original object IDs/include locations counted','graph hash proves current identity not historical correctness or immutable storage guarantee','no claim all coordination records silently rewritten','no expert/legal validity inferred']})

# Validator positive and negative fixtures; no real experimental tests.
allowed={'RESOLVED_VERIFIED','ADDRESSED_WITH_SCOPE_LIMITATION','PARTIAL','OPEN','SUPERSEDED_WITH_EVIDENCE','EVIDENCE_UNAVAILABLE','DEFERRED_BY_USER'}
def validate(rows):
    ids=[r['id'] for r in rows];assert len(ids)==len(set(ids))
    for r in rows:
        assert r['status'] in allowed
        assert r.get('owner') and r.get('next_action')
        if r['status']=='RESOLVED_VERIFIED':assert r.get('evidence')
validate(closure)
negative=[]
for name,rows in [('duplicate',[reqs[0],reqs[0]]),('unsupported_closed',[dict(reqs[0],status='RESOLVED_VERIFIED',evidence=[])]),('unknown_status',[dict(reqs[0],status='FAKE')]),('missing_owner',[dict(reqs[0],owner=None)])]:
    try:validate(rows)
    except AssertionError:negative.append(name)
    else:raise AssertionError(name)
assert len(negative)==4
for r in objects:assert r['current']['compiled_aux_match']
after=snapshot(W);assert before==after
for k,r in inputs.items():assert digest(ROOT/k)==r['sha256'],k
assert digest(graph)==gref
save('SOURCE_DOCUMENT_INDEX.json',inputs)
save('FINAL_PROTECTION.json',{'all47working_files_and_memberships_unchanged':True,'selected_evidence_inputs_unchanged':len(inputs),'graph_unchanged':record(graph),'pdfs_unchanged':all(digest(AD/'output/pdf'/pdf)==digest(P/'baseline/pdf'/pdf) for pdf in ['main.pdf','TERRA_SUPPLEMENT.pdf']),'original_manuscript_edits':0,'credentials_read':0,'API_calls':0})
save('VALIDATION_RESULT.json',{'status':'PASS_SELF_VERIFICATION','working_files':47,'original_objects':26,'original_tables':23,'original_figures':3,'limitation_themes':18,'reviewer_obligations':len(reqs),'historical_finding_ids':len(hist),'F_findings':len(frows),'negative_validator_cases_rejected':negative,'schema_and_status_reference_checks':True,'protected_input_checks':True,'peer_final_pending':True})
save('I0_COMPLETION.json',{'status':'SELF_VERIFIED_PEER_PENDING','I0_complete':False,'implementation_complete':True,'date':'2026-10-26','remaining':['Antigravity review of actual frozen implementation registers and reconciliation'],'no_scientific_gap_concealed':True,'roadmap_counts':progress['counts']})
md('FINAL_REPORT.md','# I0 implementation — baseline and requirements package\n\n26October2026. Implementation and local validation complete; actual implementation peer review remains pending. The prior plan concurrence is not substituted for reviewing these outputs.\n\nAccepted47working sources and25main/21supp PDF baseline were preserved and checked against I6adoption. All adopted manifest entries were rehashed; working bytes and exact membership remain unchanged. Corrected graph archive verified in place against its recorded fullSHA256, without database/model operations.\n\nThe preserved user-relayed reviewer letter is indexed; the exact PDF reviewed and original correspondence are unauthenticated. Requirements therefore use stable scientific object identities. All26original objects (23tables/3figures) match active source labels and compiled destinations;18limitation themes mapped. Original package titles restored in the new register; prior reports remain untouched. Historical findings and accepted correction records are linked without pretending their old OPEN/candidate flags were fresh uncorrected manuscript defects. Final all-claim adjudication remains I11.\n\nReviewerpoint5 remains partially addressed: no expert assessment or independent verifier-sufficiency references; strict legal yield and verifier error rates unestimated. Original human ratings, unlocated spans and adverse outcomes remain intact. IEEE25page operational rule is distinct from unconfirmed journal/advisor supplement policy. I9conversion remains set aside; no venue-compliance claim.\n\nFour negative validator fixtures rejected duplicate IDs, unsupported closed findings, unknown statuses and missing owners. Protection and reference validations passed. No scientific reruns, providercalls, credentials, database opening, manuscript changes, format migration or promotion.\n\nProgress conservatively remains8complete/2partial/3pending until actual output review and reconciliation. Successful I0closure would yield9/1/3. Next packages retain original definitions: I9format/readability(partial), I10submission/availability, I11final certification, I12separate promotion/submission approval.\n\nReview baseline/ and JSON registers; VALIDATION_RESULT, FINAL_PROTECTION, PEER_RECONCILIATION and I0_COMPLETION identify exact scope and residual gate.\n')
save('PACKAGE_MANIFEST.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[dict(path=p.relative_to(P).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(P.rglob('*')) if p.is_file()]})
print(json.dumps({'package':str(P),'status':'SELF_VERIFIED_PEER_PENDING','sources':47,'objects':26,'limitations':18,'manifest_entries':checked,'historical_findings':len(hist)}))
