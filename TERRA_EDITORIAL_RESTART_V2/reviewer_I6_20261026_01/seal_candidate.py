from pathlib import Path
import collections,difflib,hashlib,json,re,shutil
import pymupdf as fitz
P=Path(__file__).resolve().parent;R=P.parents[1];L=P/'ledgers';S=P/'candidate/src';B=P/'baseline/src';D=P/'builds/r03'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
def inventory(p):return {f.relative_to(p).as_posix():{'sha256':sha(f),'size_bytes':f.stat().st_size} for f in sorted(p.rglob('*')) if f.is_file()}
baseline=read(P/'baseline/MANIFEST.json');assert inventory(R/'TERRA_EDITORIAL_RESTART_V2/working/src')==baseline
candidate=inventory(S);changed=[k for k in baseline if candidate.get(k)!=baseline[k]];added=sorted(set(candidate)-set(baseline))
assert set(changed)=={'TERRA_SUPPLEMENT.tex','matched_comparison_main.tex'};assert added==['supplement_utility_audit.tex'];assert len(candidate)==47
assert candidate['supplement_assessment.tex']==baseline['supplement_assessment.tex'] and candidate['supplement_limitations.tex']==baseline['supplement_limitations.tex']
diff=''.join(''.join(difflib.unified_diff(((B/n).read_text(encoding='utf-8') if (B/n).exists() else '').splitlines(True),(S/n).read_text(encoding='utf-8').splitlines(True),fromfile='baseline/'+n,tofile='candidate/'+n)) for n in changed+added)
(P/'source.diff').write_text(diff,encoding='utf-8');write(P/'candidate/MANIFEST.json',candidate)
def labels(p):return collections.Counter(x for f in p.rglob('*.tex') for x in re.findall(r'\\label\{([^}]+)\}',f.read_text(encoding='utf-8')))
old=labels(B);new=labels(S);assert new-old=={'supp:utility-audit':1} and not old-new
for n in baseline:
 if n not in changed:assert candidate[n]==baseline[n]
write(L/'SOURCE_PROTECTION.json',{'working46unchanged':True,'candidate_existing_changes':changed,'candidate_added':added,'candidate_files':47,'unaffected_baseline_files':44,'all18limitation_file_unchanged':True,'existing_assessment_input_unchanged':True,'frozen_macros_and_bibliography_unchanged':True,'only_new_explicit_label':'supp:utility-audit','no_existing_objects_removed_merged_relocated':True})

# Reverify selected immutable inputs, including original workbooks and sampled sources.
inputs=read(L/'INPUT_MANIFEST.json')['files'];sources=read(L/'SOURCE_FILE_MANIFEST.json')['files']
for x in inputs+sources:assert sha(R/x['path'])==x['sha256'],x['path']
write(L/'FINAL_INPUT_VERIFICATION.json',{'selected_inputs_checked':len(inputs),'source_files_checked':len(sources),'all_sha256_unchanged':True,'no_credential_files_read':True,'no_model_database_provider_calls':True})
assert read(L/'INDEPENDENT_RECOUNT.json')['status']=='PASS_INDEPENDENT_LEDGER_RECOUNT'
assert read(L/'AUTHOR_JOIN_VALIDATION.json')['query_and_candidate_hash_matches']==152
tests=(P/'test_final_console.txt').read_text(encoding='utf-8-sig')+(P/'test_source_console.txt').read_text(encoding='utf-8-sig');assert 'Ran 21 tests' in tests and 'Ran 7 tests' in tests and tests.count('OK')==2
write(L/'FINAL_TEST_RESULT.json',{'final_core_tests':21,'source_rule_tests':7,'total_distinct_final_tests':28,'failures':0,'errors':0,'initial_core20tests_superseded_after_guard_hardening':True,'consoles':['test_final_console.txt','test_source_console.txt']})

docs={n:fitz.open(D/(n+'.pdf')) for n in ['main','TERRA_SUPPLEMENT']};build=read(D/'BUILD_RESULT.json');assert build['documents']['main']['pages']<=25
reviewed={'main':{'r01':[12],'r02':list(range(13,26))},'TERRA_SUPPLEMENT':{'r01':[21],'r02':[19],'r03':[20]}}
comparisons=read(L/'PAGE_COMPARISON_r03.json');review={};links={};bounds=[]
def body_sig(page):return hashlib.sha256(page.get_pixmap(matrix=fitz.Matrix(1,1),clip=fitz.Rect(0,24,page.rect.width,page.rect.height-33),alpha=False).samples).hexdigest()
for name,doc in docs.items():
 known={}
 for rev,pages in reviewed[name].items():
  prior=fitz.open(P/'builds'/rev/(name+'.pdf'))
  for i in pages:known[body_sig(prior[i-1])]=[rev,i]
 rr=[];lr=[];bad=[]
 for i,page in enumerate(doc):
  b=comparisons[name][i]['identical_body_baseline_page'];match=known.get(body_sig(page));assert b is not None or match,(name,i+1,'visual coverage')
  rr.append({'page':i+1,'baseline_body_pixel_match':b,'actually_inspected_generation_match':match,'status':'ACCOUNTED_FOR'})
  if name=='TERRA_SUPPLEMENT':assert f'S{i+1}' in page.get_text()
  outside=[]
  for block in page.get_text('dict')['blocks']:
   for line in block.get('lines',[]):
    for span in line['spans']:
     q=span['bbox']
     if span['text'].strip() and (q[0]<-1 or q[1]<-1 or q[2]>page.rect.width+1 or q[3]>page.rect.height+1):outside.append(span['text'])
  assert not outside,(name,i+1,outside);bounds.append({'document':name,'page':i+1,'outside_physical_page':outside})
  for link in page.get_links():
   if link['kind']==4 and link.get('nameddest') not in doc.resolve_names():bad.append({'page':i+1,'target':link.get('nameddest')})
   elif link['kind'] in [3,5]:
    raw=doc.xref_object(link['xref']);fm=re.search(r'/F \(([^)]+)\)',raw);dm=re.search(r'/D \(([^)]+)\)',raw);okay=bool('/GoToR' in raw and fm and dm and Path(fm.group(1)).stem in docs and dm.group(1) in docs[Path(fm.group(1)).stem].resolve_names());rec={'page':i+1,'target_file':fm.group(1) if fm else None,'destination':dm.group(1) if dm else None,'verified':okay};lr.append(rec)
    if not okay:bad.append(rec)
  d=build['documents'][name];assert not any(d[k] for k in ['overfull','undefined','multiply_defined','question_marks'])
 assert not bad,(name,bad);review[name]=rr;links[name]={'remote_links':lr,'unresolved':bad,'external_urls_not_network_revalidated':True}
write(L/'PAGE_REVIEW.json',{'scope':'Codex implementation visual checks on17changed/new/reflowed bodies; other29bodies have accepted I2 baseline pixel parity. Exact pixels/text identify inspected prior generations. Not an independent external peer or legal audit.','documents':review,'total_pages':46,'body_band_excludes_footer_header':True,'supplement_numbering_checked':True})
write(L/'PAGE_BOUNDS.json',bounds);write(L/'REFERENCES_LINKS.json',links)

# Check actual rendered values and every cell of the new table, not only source text.
sup=' '.join(' '.join(p.get_text() for p in docs['TERRA_SUPPLEMENT']).split());main=' '.join(' '.join(p.get_text() for p in docs['main']).split())
for val in ['948','1896','1873','23','669','700','50.86','22.29','22.00','8.29']:assert val in sup,val
expected_table={'Assigned queries':[350,350,100,100],'Verifier-triggered refusals':[172,272,4,69],'Generator invocations':[178,78,96,31],'Both judges: substantive':[77,29,20,1],'At least one judge: substantive':[204,129,73,23],'Judges disagree on response type':[164,116,73,32]}
for label,vals in expected_table.items():assert re.search(re.escape(label)+r'\s+'+r'\s+'.join(map(str,vals)),sup),(label,vals)
assert '20/100 H versus 1/100 T' in main
write(L/'RENDERED_VALUE_CHECKS.json',{'all_new_table_cells_verified_in_actual_PDF':expected_table,'main_adverse20H_1Tproxy_verified':True,'source_count_cells_and_percentages_verified':True,'all_new_claims_are_proxy_or_factual_location_qualified':True})
out=P/'output/pdf';out.mkdir(parents=True,exist_ok=True)
for n in docs:shutil.copy2(D/(n+'.pdf'),out/(n+'.pdf'))
write(L/'CLAIM_CHANGE_REGISTER.json',{'C01':'New main response-type20H/1Tproxy with explicit non-coverage qualification','C02':'Separate supplementary event/response-type table and disagreement accounting','C03':'40query/80arm factual provenance sample with probability/targeted separation','C04':'948primary occurrences,1873/1896normalized spans;23unlocated allSnippet, not automatically errors','C05':'700exact verifier inputs; no distinct sufficiency gold, no confusion/error rates manufactured','C06':'Existing original/reconciled author labels/table unchanged and not pooled with new answers','C07':'Expert-assessment component remains absent; no full reviewer-point5 satisfaction or deployment claim'})
write(L/'HUMAN_DEPENDENCIES.json',{'new_assessor_ratings_requested':False,'unknown_legal_interpretations':'Retained as unknown under approved R01 default; no AI judgments attributed to authors','source_rationale_rewriting':'Still excluded; original workbooks unchanged','source_check_scope':'Mechanical factual audit completed; semantic/legal sufficiency not adjudicated','required_external_dependency':'Antigravity must perform actual code/evidence/source/render review before adoption. Mailbox is user-relayed; no live dispatch assumed.'})
report='''# I6 implementation candidate and verification report

Codex,26October2026. **Implementation candidate ready; I6 remains PARTIAL pending independent peer review and exact working adoption/rebuild.** The user approved complete implementation of plan R01 with autonomous routine repairs. No new legal-expert/human assessment, provider call or score regeneration was authorized or performed.

## What is implemented and what the evidence supports

The read-only analysis inventories1,750historical arm rows and700fresh matched arm outcomes without pooling cohorts. All700actual verifier HTTP request bodies are hash-bound to their recorded events/accounting and frozen query text. Matched generation was invoked178times for H and78for T; operational refusals were172/350and272/350. Both judges called77H/29Tresponses substantive overall, and20/100H versus1/100T in CategoryB. They disagree on response type164H/116T overall and73H/32T in CategoryB. These are descriptive event and named judge-label proxies, not strict answer coverage, supported-answer yield or legal accuracy. Existing matched primary scores and p-values are unchanged.

Original/reconciled author CSVs reproduce all accepted counts and14confirmed amendments. All152assignment query/candidate hashes match the original canonical or temporal source records; none labels the new matched candidates. The authors'76-row denominators, AI assistance, nonexpert status, overlaps and unblinded reconciliation stay explicit. Both original XLSX files retain their accepted hashes. ColumnN/O rewriting was not reopened.

The fixed40-query probability sample (10percategory, both arms) produced80factual source checks:948document occurrences, all with available CAP source files and exact normalized title/date matches. Of1,896Holding/Snippet spans,1,873located under declared Unicode/whitespace normalization;23were unlocated, all Snippet fields. No unlocated text was fabricated, automatically called false or silently corrected. Field-level locations, source opinion type, quote candidates, explicit-year diagnostics and unknowns are retained. These are mechanical provenance comparisons, not complete answer/holding/legal validation. The sample is post-hoc and already exposed, not a new blinded human study.

The separate targeted ledger accounts for20historical cases (known D033/D034 fatal cases and positive-category refusal flags) and669external adverse-flag records. Recorded adverse labels are not independently confirmed legal errors. Available primary IDs/context IDs were checked; unavailable identities/interpretation remain explicit. The targeted census is not pooled unweighted with the probability sample. Reviewer-point5's expert component remains unfulfilled.

Critically, exact verifier inputs do not supply independent sufficiency references. All700reference-sufficiency labels remain unavailable. Verifier false-acceptance/rejection rates, strict legally correct-answer yield and conditional legal-error rates are consequently not estimated; the audit reports the feasibility/denominator evidence rather than fabricating a confusion matrix or new ratings. This is the approved evidence-bounded fallback, not a claim that a missing expert study has been completed.

## Implementation and validation

Final candidate r03:25main pages including references,21separate supplement pages. Four cached Tectonic0.17.0/XeTeX passes exit0. Both PDFs have zero overfull boxes, undefined references/citations, duplicate labels and unresolved question marks. Actual internal/remote PDF targets and all new table cells/numeric claims were verified. All46page bodies are accounted for through actual changed/reflowed-page inspection or scoped exact body-pixel parity to an inspected generation/accepted I2 baseline; final link targets and supplement numbering checked separately. This is implementation self-verification, not external peer acceptance.

Twenty-eight distinct final synthetic tests pass (21core,7source-rule tests); source fixtures distinguish majority/dissent/headnote spans, paraphrases and empty strings. An independently coded ledger recount reproduces all cohort/status/author totals. The core reference guard was hardened to exclude unreviewed reference-basis names; rerun summaries were byte-identical and the earlier receipts preserved. Repeated tests were limited to actual code changes/new source-rule coverage.

Only two existing candidate files change:matched_comparison_main.tex and TERRA_SUPPLEMENT.tex. One new source,supplement_utility_audit.tex,adds a real labelled section. All44unaffected baseline sources, original assessment input, frozen macros/bibliography and the18-theme limitations file remain byte-identical. All46active working files still match the accepted I2 generation. No working adoption or canonical promotion occurred; no templates, fonts or pagination settings were changed. The inherited427main font warnings remain, with underfull71main/199supplement (main baseline69); small inherited objects are not relabelled readable or fixed by I6.

Early CLI inspection exposed a Windows default-encoding read failure before writes; explicit UTF-8 fixed it. First rendered draft exposed missing spaces around numeric prose, fixed in later candidate revisions without value changes; original drafts/builds remain preserved. No experimental/API retry occurred. The source comparison involved selected local raw CAP JSON, not database/model execution.

## Remaining and review request

I6.0–I6.4local scope and the isolated I6.6candidate are implemented. A concrete combined evidence/code/source/render packet is ready for I6.5/I6.7; preparing it together avoids two relay cycles without weakening either review. I6.8exact adoption and fresh full-page parity rebuild remains held until peer findings are reconciled. No new blanket implementation permission is requested. The real external dependency is the user-relayed Antigravity review; Codex cannot truthfully invent or silently bypass it.

Peer focus:confirm denominators/proxy boundaries, input-byte joins, author hash matches, all23unlocated-span dispositions, representative primary-source comparisons, targeted/nonprobability separation and the actual17changed/reflowed page images. Unavailable legal judgments must not become invented labels. If a missing essential source task is found, keep it visible rather than administratively closing I6. Existing unknown legal interpretation remains an explicit approved outcome.

Deliverables:ledgers/,tests and saved logs,source.diff,candidate/MANIFEST.json,builds/r03/,renders/r03/,output/pdf/. Masked80-case reviewer view is in review/; private linkage is separate and must not be publicly/blindly bundled. Original blinding-map contents are not copied into public outputs. Final certification/submission/I9 and the broader roadmap remain separate.
'''
(P/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
status={'status':'I6_CANDIDATE_IMPLEMENTED_SELF_VERIFIED_PEER_AND_ADOPTION_PENDING','I6_complete':False,'main_pages':25,'supplement_pages':21,'matched_inputs_verified':700,'sample_queries':40,'sample_arm_outcomes':80,'source_occurrences':948,'unlocated_spans':23,'independent_legal_sufficiency_references':0,'final_synthetic_tests':28,'working46unchanged':True,'candidate47files':True,'adopted':False,'remaining':['Actual Antigravity code/evidence/source/render review','Reconcile findings','Exact working adoption and isolated fresh rebuild with full-page parity'],'final_revision':'r03'}
write(P/'I6_COMPLETION.json',status)
memo=R/'coordination/terra_antigravity/codex_to_antigravity/20261026-codex-0333-i6-analysis-source-audit-and-candidate-review.md'
memo.write_text('# Codex-0333 — I6 implementation candidate: combined code/evidence/source/render review\n\n'+report+'\nReview exact main render pages12–25and supplementS19–S21under `renders/r03/`; other29bodies have recorded I2 parity. Review28tests and independent recount, raw event pointers and request hashes, source spans against CAP files, and the case/reference limits before recommending adoption. Do not infer actual visual inspection from logs. Preserve your original review and identify actual inspected scope. No parallel implementation or provider/model/credential work.\n',encoding='utf-8')
sp=R/'coordination/terra_antigravity/STATUS.json';shutil.copy2(sp,P/'baseline/STATUS_before_candidate_review.json');st=read(sp);st.update(state='I6_CANDIDATE_SELF_VERIFIED_PEER_SOURCE_AND_VISUAL_REVIEW_PENDING',latest_codex_message='codex_to_antigravity/'+memo.name,i6_state='PARTIAL',i6_completion_path='TERRA_EDITORIAL_RESTART_V2/reviewer_I6_20261026_01/I6_COMPLETION.json',current_turn_scope='Codex0333: user-approved R01 implemented locally through factual/proxy ledgers and candidate.700actual verifier inputs verified;40query/80arm source sample948occurrences,23unlocatedSnippet spans; targeted20historical/669external flags separately accounted; author152hashjoins/14amendments unchanged.28final tests and independent recount PASS. Candidate25main/21supp;17changed/reflowed bodies inspected,29baseline parity; links/values checked. Working46unchanged; no new human/expert labels, model/API/credentials, stats regeneration, Springer migration or promotion. Actual Antigravity evidence/code/source/render review and adoption/rebuild remain; I6notDONE.');write(sp,st)
rows=[{'path':f.relative_to(P).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(P.rglob('*')) if f.is_file() and f.name!='PACKAGE_MANIFEST.json']
write(P/'PACKAGE_MANIFEST.json',{'scope':'I6 candidate and local evidence, not accepted working release; private review linkage must not enter public/blinded packages','files':rows})
for x in rows:assert sha(P/x['path'])==x['sha256']
print(json.dumps({'status':status['status'],'package_files':len(rows),'inputs_postverified':len(inputs),'primary_and_external_files_postverified':len(sources),'source_changes':changed,'new_source':added,'pages':[25,21],'peer_request':str(memo)}))
