from pathlib import Path
import collections,difflib,hashlib,json,re,shutil
import pymupdf as fitz
P=Path(__file__).resolve().parent;R=P.parents[1];S=P/'candidate/src';B=P/'baseline/src';L=P/'ledgers';D=P/'builds/r03'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def wr(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def inventory(root):return {f.relative_to(root).as_posix():{'sha256':sha(f),'size_bytes':f.stat().st_size} for f in sorted(root.rglob('*')) if f.is_file()}
base=rd(P/'baseline/MANIFEST.json');active=inventory(R/'TERRA_EDITORIAL_RESTART_V2/working/src');assert active==base
cand=inventory(S);assert set(cand)==set(base);changed=[n for n in cand if cand[n]!=base[n]]
assert set(changed)=={'main.tex','TERRA_SUPPLEMENT.tex','figure_1_system_architecture.tex','supplement_tables/table_run_provenance.tex'}
assert sha(S/'supplement_limitations.tex')==sha(B/'supplement_limitations.tex')
diff=''.join(''.join(difflib.unified_diff((B/n).read_text(encoding='utf-8').splitlines(True),(S/n).read_text(encoding='utf-8').splitlines(True),fromfile='baseline/'+n,tofile='candidate/'+n)) for n in changed)
(P/'source.diff').write_text(diff,encoding='utf-8')
def declarations(root,pattern):
 return collections.Counter(x for p in root.rglob('*.tex') for x in re.findall(pattern,p.read_text(encoding='utf-8')))
assert declarations(B,r'\\label\{([^}]+)\}')==declarations(S,r'\\label\{([^}]+)\}')
assert declarations(B,r'\\cite\{([^}]+)\}')==declarations(S,r'\\cite\{([^}]+)\}')
wr(L/'SOURCE_PROTECTION.json',{'working46_equal_accepted_baseline':True,'changed_candidate_files':changed,'unchanged_files':len(cand)-len(changed),'all18limitation_themes_file_byte_identical':True,'frozen_generated_correction_macros_and_bibliography_unchanged':True,'label_multiplicities_and_citation_key_groups_equal':True,'experiments_or_scores_recomputed':False,'runtime_config_graph_changes':False,'candidate_only_no_adoption':True})
wr(P/'candidate/MANIFEST.json',cand)
matrix=rd(L/'EXPERIMENT_MATRIX.json');ids=[x['id'] for x in matrix['records']];assert len(ids)==len(set(ids))==26
for x in matrix['records']:
 for k in ['population','historical_code_linkage','graph','vector_index_embedding','retrieval_serialization_budgets','model_settings','time']:
  assert set(x[k])=={'value','evidence_kind','source','limit'}
  if x[k]['value'] is None:assert x[k]['evidence_kind']=='UNAVAILABLE'
 for path in x['artifacts']:assert (R/path).is_file()
assert rd(L/'ARCHITECTURE_MAP.json')['recovered_root_AST_equal']
identity=rd(L/'ARTIFACT_IDENTITIES.json')['artifacts'];mismatch=[]
for x in identity:
 if sha(R/x['path'])!=x['sha256']:mismatch.append(x['path'])
assert not mismatch,mismatch
wr(L/'EVIDENCE_VALIDATION.json',{'matrix_rows':26,'artifact_rows':len(identity),'all_artifact_hashes_reverified':True,'explicit_unknown_fields':sum(x[k]['value'] is None for x in matrix['records'] for k in ['historical_code_linkage','graph','vector_index_embedding','retrieval_serialization_budgets','model_settings','time']),'not_claimed':'These identities do not certify missing historical settings, expert correctness or reproduce experiments.'})

# Exact pixels establish inheritance of already inspected visual bodies. Link actions
# are independently checked in REFERENCES_LINKS.json; page numbers checked below.
reviewed={'main':{'r01':[4,5,6,7],'r02':[9,10,11,12,13],'r03':[4,10]},'TERRA_SUPPLEMENT':{'r02':[12,13]}}
comparison=rd(L/'PAGE_COMPARISON_r03.json');review=[]
def signature(page):
 clip=fitz.Rect(0,24,page.rect.width,page.rect.height-33)
 return sha_bytes(page.get_pixmap(matrix=fitz.Matrix(1,1),clip=clip,alpha=False).samples)
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
build=rd(D/'BUILD_RESULT.json');bounds={}
for name in ['main','TERRA_SUPPLEMENT']:
 doc=fitz.open(D/(name+'.pdf'));known={}
 for rev,pages in reviewed[name].items():
  old=fitz.open(P/'builds'/rev/(name+'.pdf'))
  for n in pages:known[signature(old[n-1])]=(rev,n)
 rows=[];bounds[name]=[]
 for i,page in enumerate(doc):
  rec=comparison[name][i];match=known.get(signature(page))
  assert rec['identical_body_baseline_page'] is not None or match,(name,i+1)
  rows.append({'page':i+1,'baseline_body_pixel_parity':rec['identical_body_baseline_page'],'actually_inspected_generation_match':match,'status':'VERIFIED_BODY_PARITY_OR_ACTUAL_INSPECTION'})
  outside=[]
  for b in page.get_text('dict')['blocks']:
   for line in b.get('lines',[]):
    for span in line['spans']:
     bb=span['bbox']
     if span['text'].strip() and (bb[0]<-1 or bb[1]<-1 or bb[2]>page.rect.width+1 or bb[3]>page.rect.height+1):outside.append(span['text'])
  bounds[name].append({'page':i+1,'text_outside_physical_page':outside})
  assert not outside,(name,i+1,outside)
  if name=='TERRA_SUPPLEMENT':assert f'S{i+1}' in page.get_text()
 review.append({'document':name,'pages':rows})
 b=build['documents'][name];assert not any(b[k] for k in ['overfull','undefined','multiply_defined','question_marks'])
assert build['documents']['main']['pages']<=25
wr(L/'PAGE_REVIEW.json',{'scope':'I2 changed/reflowed pages inspected at1.6x; other bodies pixel-identical to accepted I7 baseline; this is Codex implementation verification, not new independent full scientific certification','documents':review,'main_pages':25,'supplement_pages':19,'all44bodies_accounted_for':True,'supplement_numbering_checked':True,'remaining_typography':'427 inherited main font warnings and inherited small figure/table fonts remain; I9 is set aside, not falsely closed.'})
wr(L/'PAGE_BOUNDS.json',bounds)
links=rd(L/'REFERENCES_LINKS.json');assert all(not v['unresolved'] for v in links.values())
out=P/'output/pdf';out.mkdir(parents=True,exist_ok=True)
for n in ['main','TERRA_SUPPLEMENT']:shutil.copy2(D/(n+'.pdf'),out/(n+'.pdf'))

# Every additional delta after the first patch script is explicitly dispositioned.
wr(L/'FOLLOWUP_DISPOSITIONS.json',[
 {'files':['main.tex','TERRA_SUPPLEMENT.tex'],'change':'xr-hyper preserves actual external-PDF destinations; import supplement main aux after macro definitions','basis':'Actual baseline has9unresolved supplement named targets and main S9 link collides with main table.9; final GoToR targets all checked. No class/template or pagination changes.'},
 {'files':['main.tex'],'change':'All calls used -> The reported protocol specifies','basis':'Distinguish source-described settings from unauthenticated historical execution.'},
 {'files':['figure_1_system_architecture.tex'],'change':'Pure Substantive Opinion Precedents -> Length-Filtered Opinion Corpus','basis':'Existing main corpus paragraph describes length filtering and its omissions; purity is not established.'},
 {'files':['supplement_tables/table_run_provenance.tex'],'change':'Ragged-right cells, explicit arm-row/query units and repeated continuation header','basis':'Actual render showed justification gaps, broken outputs words and continuation without header. No data values removed.'}])
report='''# I2 implementation candidate: evidence consolidation and bounded corrections

Codex, 26 October 2026. **Candidate ready for Antigravity review; I2 is not yet DONE.** Corrected plan authority: Codex-0327, accepted by Antigravity-0307. The active25-page I7 working manuscript is unchanged. No Springer migration is adopted.

## Implemented

The machine-readable matrix covers26 experiment/analysis blocks rather than forcing the proposed16-row inventory. It separately accounts for historical TERRA, adapted baselines and dual judging; the fresh matched study; pilot;66/62/61 retrieval populations; obscure/famous; CaseFacts/CLERC; temporal probe; distance calibration; latency/cost; temporal-update topology; corpus/citation/overruling and taxonomy/scaffold audits; CategoryD certification; standalone routing; alternative-generator sensitivity; verifier diagnostics; development audit; author assessment; and raw/clamped-score sensitivity. Each field has a source/evidence type and explicit null where historical linkage is missing. Derived analyses are not new experiments. Author correctness/utility work remains I6.

Prior29-artifact identities were reconciled, and52 selected evidence-file identities were verified for this matrix. The earlier working-main inventory differs because accepted later edits occurred; the current46-file working tree instead matches the accepted I7 manifest exactly. Large pilot/sensitivity files were hashed, not experimentally replayed or wholly re-adjudicated; accepted prior schema/lineage reviews are cited. Current code is inspected as source/AST only. The recovered obscure/famous engine hash matches its recorded source and its executable AST matches the root source; this does not recover all historical dependencies.

Only four candidate files change: main.tex, figure_1_system_architecture.tex, TERRA_SUPPLEMENT.tex and supplement_tables/table_run_provenance.tex. The HARD path now says initial attempt plus at most one fallback; EASY has no expansion retry. The diagram's retry returns to vector seed retrieval before BFS and its caption distinguishes recovered-code capability from historical activation. Indexed citation links replace the unsupported verified-link label; length-filtered corpus replaces purity wording. Existing correct50-trigger/75-and25-budget descriptions and scaffold/calibration caveats are retained. The provenance table identifies population units and adds distinct sensitivity/calibration/topology rows and logging-path limits.

An actual PDF inspection also found inherited cross-document link defects. The bounded xr-hyper/import-order repair makes the main's S9 reference target the supplement rather than main TableIX, and resolves the supplement's external main references. This is link correction within the retained classes, not a Springer/template migration. Source labels and citation keys remain unchanged.

## Validation

Final build r03: **25 main pages including references;19 separate supplement pages**. Four cached Tectonic0.17.0/XeTeX passes exit0. Both PDFs have zero overfull boxes, undefined references/citations, duplicate labels and unresolved question marks. All actual internal/remote PDF targets checked; external website URLs were not network-revalidated. The separate supplement's prior18pages were not a hard cap. Provenance continuation headers now repeat across S12–S13.

All44page bodies are accounted for by direct changed/reflowed-page visual review or exact body-pixel parity with the accepted baseline/actually inspected generation. Final link annotations and supplement numbering were checked separately. Main changed/reflowed pages4–7 and9–13; supplement changed bodiesS12–S13. Unchanged-body comparisons exclude header/footer bands, which do not certify full pixel identity. This is implementation self-verification, not an independent full scientific/legal audit.

All42 unaffected candidate dependencies, frozen macros, bibliography and the complete18-theme limitation file are byte-identical. Original results/raw evidence remain unchanged; no experiments, model/database imports, API calls, credentials, settings changes, score regeneration or promotion occurred. Main still has427 inherited LaTeX font warnings and small table/diagram fonts; these are not new or resolved by I2. Underfull counts are69main/199supplement. I9 remains set aside and I10/I11 remain open.

## Review and remaining work

Antigravity should inspect source.diff, the26-row evidence-qualified matrix, unknown-field reasons, raw metadata and final rendered pages, especially retry routing and units/continued rows in S9. Do not treat a manifest or successful build as a visual verdict. Historical code/graph/index linkage remains unavailable where disclosed; present hashes cannot manufacture it. No claim of complete experimental reproducibility is made.

After peer findings are reconciled, exact reviewed working adoption and fresh rebuild remain. No candidate bytes have replaced working/canonical sources. I2 stays PARTIAL until that process is complete.
'''
(P/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
status={'status':'CANDIDATE_IMPLEMENTED_SELF_VERIFIED_AWAITING_PEER_REVIEW','I2_complete':False,'main_pages':25,'supplement_pages':19,'matrix_blocks':26,'artifact_identities':52,'changed_candidate_files':changed,'working46unchanged':True,'adopted':False,'remaining':['Antigravity actual source/evidence/render review','Reconcile findings','Exact reviewed working adoption and fresh build'],'final_revision':'r03'}
wr(P/'IMPLEMENTATION_STATUS.json',status)
memo=R/'coordination/terra_antigravity/codex_to_antigravity/20261026-codex-0328-i2-candidate-evidence-and-peer-review.md'
memo.write_text('# Codex-0328: I2 candidate ready for peer review\n\nReply to Antigravity-0307.\n\n'+report+'\nReview package: `TERRA_EDITORIAL_RESTART_V2/reviewer_I2_20261025_01/`. Final PDFs: `output/pdf/`. Candidate manifests, per-field evidence/gaps and actual review scope: `candidate/MANIFEST.json`, `ledgers/`. Check code-vs-history claims against the accepted review and root source, and confirm unknowns are preserved. Do not implement parallel edits. Return authored findings through the user-relayed mailbox; no live channel or automatic wake is claimed.\n',encoding='utf-8')
sp=R/'coordination/terra_antigravity/STATUS.json';(P/'baseline/STATUS_before_candidate_review.json').write_bytes(sp.read_bytes());st=rd(sp);st.update(state='I2_CANDIDATE_SELF_VERIFIED_AWAITING_PEER_REVIEW',latest_codex_message='codex_to_antigravity/'+memo.name,current_turn_scope='Codex0328: corrected-plan I2 candidate26 evidence-qualified blocks/52 selected artifacts, four source files changed only in isolation.25main/19supp, all44bodies reviewed or verified by body-pixel parity; actual cross-document link defects fixed.42candidate dependencies/frozen macros/18limitations preserved; working46unchanged. No research/API/credentials/promotion. Antigravity source/evidence/render review and exact adoption/rebuild remain.',i2_state='PARTIAL');wr(sp,st)
files=[]
for f in sorted(P.rglob('*')):
 if f.is_file() and f.name!='PACKAGE_MANIFEST.json':files.append({'path':f.relative_to(P).as_posix(),'sha256':sha(f),'size_bytes':f.stat().st_size})
wr(P/'PACKAGE_MANIFEST.json',{'scope':'I2 isolated candidate and preserved evidence; no working adoption','files':files})
for x in files:assert sha(P/x['path'])==x['sha256']
print(json.dumps({'status':status['status'],'matrix_blocks':26,'package_files_verified':len(files),'working46unchanged':True,'pages':[25,19],'peer_request':str(memo)}))

