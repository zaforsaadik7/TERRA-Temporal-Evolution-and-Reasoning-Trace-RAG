"""Seal the I11 implementation self-audit without adopting manuscript changes."""
import collections,hashlib,json,re,subprocess,time,zipfile
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[1];S=P/'baseline/src';W=P.parent/'working/src'
def rd(p):return Path(p).read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def out(n,o):(P/n).write_text(json.dumps(o,indent=2,ensure_ascii=False),encoding='utf-8')
def write(n,t):(P/n).write_text(t,encoding='utf-8')

# Fix evidence pointers to exact current lines; do not alter original findings' science.
findings=json.loads(rd(P/'FINDINGS.json'))
anchors={1:r'\enlargethispage{14',2:r'\noindent\textbf{Faithfulness.}',3:'because TERRA writes longer',4:'recovers the full chain on',5:r'$\mathbf{\HippoRAGCatAFaithfulness}$',6:'Table~\\ref{tab:refusal_breakdown}, Panel~B; Figure',7:'gold-precedent omission rate',8:'Hyperparameter Freezing and Benchmark Isolation',9:r'\label{fig:system_architecture}',10:'Propositional SAT solver',11:r'overlapping CIs; $\TerraAnswerOnlyFaithfulnessMean$'}
for i,x in enumerate(findings,1):
 f=Path(x['artifact']).relative_to(W);s=rd(S/f);a=anchors[i];assert a in s,(i,a)
 x['source_line']=s.count('\n',0,s.index(a))+1
out('FINDINGS.json',findings)

# Complete table/equation inventory includes tables without explicit labels.
g=json.loads(rd(P/'SOURCE_INCLUDE_GRAPH.json'));envs=[]
unlabelled={'supplement_assessment.tex':18,'supplement_matched_comparison.tex':19,'supplement_utility_audit.tex':19}
for d,files in g.items():
 for f in files:
  if f.startswith(('generated_','phase3_')):continue
  s=rd(S/f)
  for m in re.finditer(r'\\begin\{(table\*?|figure\*?|longtable|tabular|equation|align\*?)\}',s):
   envs.append({'document':d,'file':f,'line':s.count('\n',0,m.start())+1,'environment':m.group(1),'review_basis':'actual page reading including captions/notes/panels','unlabelled_or_new_table_page':unlabelled.get(f),'references':'OBJECT_REFERENCE_REGISTER.json and per-page notes'})
out('ENVIRONMENT_OBJECT_INVENTORY.json',envs)
i0=json.loads(rd(P.parent/'reviewer_I0_20261026_03/OBJECT_MAP.json'))
labels={x['label'] for x in json.loads(rd(P/'OBJECT_REFERENCE_REGISTER.json'))['labels']}
historical=[]
for x in i0['objects']:
 lab=x['original'].get('label'); historical.append({'id':x['id'],'original_label':lab,'label_still_present':lab in labels,'disposition':'APPROVED_OBJ08_PROSE_TABLE_III' if x['id']=='OBJ08' else 'CURRENT_LABEL_PRESENT' if lab in labels else 'REQUIRES_REVIEW'})
out('HISTORICAL_OBJECT_RECONCILIATION.json',{'objects':historical,'ratification':'reviewer_I0_20261026_03/closure_20261026_01/OBJ08_FINAL_DISPOSITION.json','new_tables':'ENVIRONMENT_OBJECT_INVENTORY.json','limits':'Label survival verifies presence, not cell correctness or readability; those are separately reviewed.'})

# Correct the supporting receipt path: first guessed root AUDIT_RESULT was absent.
sup=json.loads(rd(P/'SUPPORTING_EVIDENCE_MANIFEST.json'))
for x in sup:
 if not x['exists']:
  old=x['path'];target=R/'reports/matched_study_r03_20261025_01/postrun/AUDIT_RESULT.json'
  x.update(path=str(target),exists=target.is_file(),sha256=sha(target) if target.is_file() else None,path_reconciliation=f'Initial root-level path {old} absent; actual accepted postrun subdirectory used.')
assert all(x['exists'] for x in sup)
out('SUPPORTING_EVIDENCE_MANIFEST.json',sup)

analysis=json.loads(rd(R/'reports/matched_study_r03_20261025_01/ANALYSIS_RESULTS.json'))
utility=json.loads(rd(P.parent/'reviewer_I6_20261026_01/ledgers/UTILITY_SUMMARY.json'))
sourcechecks=json.loads(rd(P.parent/'reviewer_I6_20261026_01/ledgers/SOURCE_CHECK_SUMMARY.json'))
verifier=json.loads(rd(P.parent/'reviewer_I6_20261026_01/ledgers/VERIFIER_FEASIBILITY.json'))
originals=P.parent/'reviewer_author_validation_20261008/issued_20261009_01/COMPLETED'
protected=[]
for name,expected in [('ASSESSMENT_AUTHOR_1_COMPLETED.xlsx','34735965b0636a26570b3053baebfd8b58532888f684e2ee381754c8bdf6832b'),('ASSESSMENT_AUTHOR_2_COMPLETED.xlsx','ce3869f8b0930b6a28df73b5deabffc5e1e7da9c4b2df5a649bec27f838c598b')]:
 q=originals/name;h=sha(q);protected.append({'path':str(q),'sha256':h,'matches_accepted_prior_identity':h==expected,'operation':'hash bytes only; no workbook contents modified or republished'})
assert all(x['matches_accepted_prior_identity'] for x in protected)
out('ORIGINAL_WORKBOOK_PROTECTION.json',protected)
targeted={'scope':'Reading/current-text consistency checks against accepted derivations; no p-value/bootstrap/model/ratings regeneration. Full numeric inventory is not equivalent to individual empirical revalidation.',
 'matched_B':analysis['summaries']['B'],'matched_cohort':{c:{k:s[k] for k in ['assigned','eligible_pairs','H_refusals','T_refusals']} for c,s in analysis['summaries'].items()},
 'utility_all':utility['matched']['ALL'],'utility_B':utility['matched']['B'],'source_checks':sourcechecks,'verifier_sufficiency_reference_count':verifier['independent_reference_sufficiency_available'],
 'calibration':'I7 accepted NUMERIC_CROSSCHECKS and full main5/22/23 reading: AUROC0.9901,200in-domain,75out-of-domain,tau1.30 flags0/200 and41/75. Contemporary diagnostic not historical provenance.',
 'chains':'I7 accepted check/TableX: canonical66/100, legacy62/100,bounded61/100 distinct; no exact historical lineage inferred.',
 'author_aggregates':'Accepted AUTHOR_RECONCILIATION values match S18: original/reconciled A1support43/40of76,contradicted19/22of62; A2support47of76,contradicted12of65 with6uncertain. Not independent legal validation.',
 'numeric_exceptions':['I11-F02','I11-F03','I11-F04','I11-F05','I11-F07','I11-F08','I11-F10']}
out('TARGETED_NUMERIC_AND_SCOPE_CHECKS.json',targeted)

# Build diagnostics classify font substitutions separately from missing references/glyphs.
diag=json.loads(rd(P/'BUILD_DIAGNOSTICS.json'))
for name,row in diag.items():
 log=rd(P/'cleanroom/extracted'/f'{name}.log')
 row['undefined_reference_lines']=[x for x in log.splitlines() if re.search(r'(Reference|Citation).*undefined|There were undefined',x,re.I)]
 row['missing_character_lines']=[x for x in log.splitlines() if 'Missing character' in x]
 row.pop('undefined_lines',None)
 row['font_interpretation']='TU/ptm and TU/pcr shapes substituted; glyphs inspected on all pages/closeups. No missing-character log. Substitution is not a certificate of correct emphasis (F05), legibility (F09) or complete page content (F01).'
out('BUILD_DIAGNOSTICS.json',diag)

exceptions=[{'id':'EX-I9','type':'DEFERRED_ADMINISTRATIVE_AND_TYPOGRAPHIC','status':'OPEN','detail':'IEEE version retained by user; journal-format compliance not certified. New physical readability defect F09 remains substantive despite I9 deferral.'},
 {'id':'EX-I10','type':'DEFERRED_AUTHOR_SUBMISSION_FACTS','status':'OPEN','detail':'Intended journal confirmed. Complete authorship/contact/funding/conflict/prior-publication/concurrent-status/ethics determination not finalized; corrected second-author spelling pending final author package. Consent to ratings/findings reporting is recorded, not workbook-publication or ethics approval.'},
 {'id':'EX-EXPERT','type':'SCIENTIFIC_LIMITATION','status':'OPEN_DISCLOSED','detail':'Reviewerpoint5 expert component unmet; legal correctness and independent verifier error rates unestimated. No expert commission requested.'},
 {'id':'EX-PROVENANCE','type':'SCIENTIFIC_LIMITATION','status':'OPEN_DISCLOSED','detail':'Missing historical run code/graph/index linkage and upstream Gemma receipt caveat retained. Hashing current files does not repair historical lineage.'},
 {'id':'EX-TOOLCHAIN','type':'REPRODUCIBILITY_BOUNDARY','status':'OPEN_DISCLOSED','detail':'Fresh manuscript extraction rebuild matches PDFs. Shared compiler cache not recursively pinned/fully externally traced; no empty-machine hermetic build claim.'},
 {'id':'EX-PEER','type':'REVIEW_PENDING','status':'OPEN','detail':'No actual I11 peer artifact review received. Mailbox request does not wake Antigravity or confer concurrence.'},
 {'id':'EX-VALUES','type':'AUDIT_SCOPE','status':'OPEN_DISCLOSED','detail':'2025macro uses and2942numeric occurrences inventoried; central accepted derivations checked. Not every inherited statistic independently rederived, and no independent legal judgments made.'}]
out('KNOWN_EXCEPTIONS.json',exceptions);out('OPEN_EXCEPTIONS.json',{'findings':[x['id'] for x in findings],'exceptions':exceptions})

letter=P.parent/'reviewer_I0_I1a_20261008/REVIEWER_LETTER.md'
response_index={'letter':{'path':str(letter),'sha256':sha(letter),'authority':'preserved user-relayed letter; original reviewed PDF and correspondence unauthenticated'},'points':[]}
response_body='''# Draft reviewer response — not sent, not submission-certified

Prepared by Codex for author review, 26 October2026. Locations refer to the accepted25-page main and21-page supplement, not the unidentified PDF originally reviewed. This draft describes completed scientific work; the I11 defects below must be corrected and page locations refreshed before sending.

1. **Contradictory calibration and chain results.** The unreproduced distance summary was removed. The contemporary distance-only diagnostic on the20,000-case index reports squared-L2 units, AUROC0.9901, and0/200 in-domain versus41/75 out-of-domain flags at1.30; it does not test title matching or authenticate the historical calibration. Canonical66/100, older stored-context62/100 and separately bounded61/100 recovery are distinguished. Target-set matching does not demonstrate connected-path recovery or complete historical lineage. Locations: main5,19–20,22–23; supplementS12–S13. Remaining I11 repairs: duplicated denominators/units(F04) and unsupported chronology wording(F08).

2. **Implementation and experimental identity.** Figure1 now shows anchor retrieval on EASY and graph expansion on HARD, with evidence checking; the five-step scaffold is generic. Current source settings, pilot/historical blocks and prospective code/graph identities are distinguished. Unavailable historical code/index linkages and mtime limitations are explicitly disclosed, rather than reconstructed from current files. Locations: main3–10/Figure1; supplementS4,S12–S13. Remaining I11 issues: unreadable diagram lettering(F09) and strong freeze claims inconsistent with the qualified record(F08).

3. **Fair controlled comparison.** A fresh350-pair dense–BM25 versus graph-retrieval study used shared source text, graph-derived evidence, serializer, budgets, generator, verifier and judges. CategoryB(n100) T-minus-H composite evidence-faithfulness difference is0.26885,95%bootstrapCI[0.16035,0.37205], paired randomizationp0.000010. T had69/100 verifier refusals versus4/100 for H. The result concerns the full gated pipeline; it does not show superior substantive-answer coverage or legal correctness. Locations: main12/prospective subsection,main24; supplementS18–S20. All2706 settled requests and conditional reference cost are retained. Historical baseline adaptations are not certified as equivalent implementations. The surrounding main12 historical refusal/clamping paragraph is physically clipped(F01), so this response must not claim the main PDF is complete yet.

4. **Reasoning-trace novelty.** The title and narrative now describe generic procedural scaffolds and actual citation-graph traversal. The fixed five-step text is not case-specific legal reasoning; curated prototypes were not the evaluated index. TERRA is used as a project name. No unperformed trace/no-trace ablation or isolated component novelty is claimed. Locations: title,main1–5,discussion23–24; supplementS7. Related-work correctionF10 is required: SAT-Graph is Structure-Aware Temporal retrieval, not a propositional satisfiability verifier.

5. **Legal correctness, useful answering and verifier errors — partially addressed.** Two nonexpert, AI-assisted authors supplied descriptive assessments; workflows and unblinded reconciliation are disclosed. The new utility audit separates generator events, judge response-type proxies and source-span checks. Across350queries/arm, generator invocation is178H/78T and both-judge-substantive proxies77H/29T; on CategoryB these are96/31 and20/1. The source audit covers40sampledqueries/80armoutcomes,948documentoccurrences and1896spanchecks(1873located,23unlocated). These are factual provenance checks, not independent legal adjudication. Although all700 final verifier inputs survive, independently supported sufficiency references do not; false-acceptance/rejection rates, validated supported-answer yield and conditional legal-error rates are not estimated. No blinded legal-expert validation was obtained. We ask the reviewer to consider these narrower observations and explicit limits, without asserting equivalence to the requested expert assessment. Locations: main10,12,24; supplementS15–S20. The author workbook supporting-quotation/rationale repairs were excluded from the completed ratings-only analysis and remain uncertified; consent to report findings is not accuracy validation. F01/F07 must be repaired before the final response.

The paper is not currently ready for submission: I11 identifies eleven findings, I9/I10 remain deferred/incomplete and this draft has not been peer-reviewed or sent. No public release or venue compliance is promised here.
'''
write('REVIEWER_RESPONSE_DRAFT.md',response_body)
requirements=json.loads(rd(P.parent/'reviewer_I0_20261026_03/REQUIREMENTS.json'))
for i in range(1,6):response_index['points'].append({'reviewer_point':i,'draft':'REVIEWER_RESPONSE_DRAFT.md','status':'PARTIALLY_ADDRESSED_EXPERT_COMPONENT_UNMET' if i==5 else 'SCIENTIFIC_WORK_COMPLETED_WITH_I11_REPORTING_REPAIRS_PENDING','evidence':[x for x in sup if any(k in x['path'] for k in (['I7','I0'] if i==1 else ['I2'] if i==2 else ['matched_study','I6'] if i==3 else ['I0'] if i==4 else ['I6']))]})
out('RESPONSE_EVIDENCE_INDEX.json',response_index)

# Capture the named validation run and console, without wildcard discovery.
command=[str(R/'venv/Scripts/python.exe'),'-B',str(P/'test_audit_validators.py')]
start=time.monotonic();run=subprocess.run(command,cwd=P,capture_output=True,text=True)
write('VALIDATOR_TEST_CONSOLE.txt',run.stdout+run.stderr)
out('VALIDATOR_TEST_RESULT.json',{'command':command,'cwd':str(P),'exit':run.returncode,'seconds':time.monotonic()-start,'tests':13,'scope':'synthetic negative audit fixtures plus actual register/parity/archive validations; no research code','stdout_stderr':'VALIDATOR_TEST_CONSOLE.txt'})
assert run.returncode==0

# Final protections cover exact 47-file membership and bytes, primary PDFs and selected receipts.
base=json.loads(rd(P/'BASELINE_MANIFEST.json'))
assert {p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_file()}==set(base['sources'])
assert all(sha(W/rel)==x['sha256'] for rel,x in base['sources'].items())
assert all(sha(x['path'])==x['sha256'] for x in base['pdfs'].values())
assert all(sha(x['path'])==x['sha256'] for x in sup)
out('FINAL_PROTECTION.json',{'47_source_members_and_hashes_unchanged':True,'accepted_pdfs_unchanged':True,'selected_supporting_receipts_unchanged':len(sup),'original_workbooks_match_accepted_hashes':True,'research_and_generated_stats_untouched':True,'experiments_api_calls_credentials_model_or_database_loads':0,'scope':'Selected original workbooks rehashed; no claim to have freshly rehashed every large corpus/store file in this audit.'})

completion={'date':'2026-10-26','implementation_author':'Codex','status':'CORRECTIONS_REQUIRED_REVIEW_PENDING','audit_work_complete':True,'certification_complete':False,'submission_ready':False,'peer_review_complete':False,'pages_read_and_visually_reviewed':46,'main_pages':25,'supplement_pages':21,'all_47_accepted_source_files_unchanged':True,'cleanroom_pdf_parity':'46/46 text+raster+links; named destinations equal','findings':len(findings),'severity_counts':dict(collections.Counter(x['severity'] for x in findings)),'manuscript_repairs_adopted':0,'proposals':'EXACT_PATCH_PROPOSALS.json; proposed_unapplied.diff; REPAIR_DISPOSITIONS.md','reviewer_response':'REVIEWER_RESPONSE_DRAFT.md','limitations':'KNOWN_EXCEPTIONS.json','i11_roadmap_status':'PARTIAL','next_action':'Peer review actual I11 artifacts; then authorize bounded correction candidate/adoption separately. No I12 promotion or release.'}
out('I11_COMPLETION.json',completion)
repair='# Correction dispositions — proposed only\n\nNo accepted source changes. Proposed diff is unbuilt and does not establish a25-page corrected result. F02 is conditional on peer confirmation of the accepted20-test family; never silently edit frozen statistics.\n\n'
for x in findings:repair+=f"## {x['id']} — {x['title']}\n\nLocation: {x['artifact']}:{x['source_line']}; {', '.join(x['rendered_pages'])}.\n\nEvidence: {x['evidence']}\n\nProposed action: {x['proposed_disposition']}\n\nClosure: {x['closure_test']}\n\n"
repair+='''For F09, a concrete layout repair needs a separate isolated build: remove the page12 expansion, measure reflow, use readable main summary tables while retaining full cells in the existing supplement, enlarge Figure1 labels, and inspect every changed page. Do not claim these design choices meet25pages until built. F11 minor duplicates and TableIII emphasis also require a deliberate local copyedit. No experiment or API rerun is indicated by these reporting defects.
'''
write('REPAIR_DISPOSITIONS.md',repair)

eq=json.loads(rd(P/'PDF_EQUIVALENCE.json'));lay=json.loads(rd(P/'FONT_AND_LAYOUT_FINDINGS.json'))
report=f'''# I11 retained-package audit — corrections required

Codex implementation self-audit,26October2026. **The audit implementation is complete; final I11 certification is not.** Actual Antigravity review of this package remains pending. No accepted manuscript edits or promotion occurred.

## Work completed

Read and individually visually inspected all25main+21supplement pages, including table panels/notes, references and18limitations. Six additional main-page closeups were inspected(4,5,11,12,13,20). Page-specific authored observations are in READING_COVERAGE.json and VISUAL_PAGE_REVIEW.json; they are not inferred from text extraction. PARAGRAPH_COVERAGE records source groups; ENVIRONMENT_OBJECT_INVENTORY includes unlabelled newer tables.

Preserved all47accepted source files and both PDFs. A46-input source archive deliberately excludes the derived main.bbl; a fresh extraction built supplement→main→supplement→main using cache-only/untrusted Tectonic0.17.0, without stale manuscript auxiliaries. All four commands exited0. The rebuilt25/21-page outputs match all46accepted pages in extracted text,1.4x raster bytes and link signatures; named destinations also match. PDF_EQUIVALENCE has per-page hashes. **Reproducibility reproduced defects; it did not establish correctness.** Shared internal compiler cache dependencies are declared but not completely pinned/traced; an empty-machine hermetic build is not certified.

Inventoried80source labels,98references,2025macro uses and2942hardcoded numeric occurrences; checked internal/cross-PDF links with no invalid resolved-page target. Inventoried31bibliography entries(30cited in main,6in supplement; one uncited), with bounded primary-source/metadata checks and explicit fetch/version limits. Critical endpoint/proxy values were checked against selected accepted I1/I2/I6/I7 and matched-study records, not regenerated. An inventory is not an assertion that every inherited statistic was independently rederived.

Both original assessment workbooks match their accepted hashes. No new legal assessment or quotation/rationale repair was performed, and no original ratings were changed. All selected supporting receipts and accepted-source/PDF bytes remained unchanged. Thirteen audit-validator tests passed, including negative fixtures for missing page coverage, unsupported closure, stale hash, traversal/case aliases, broken cross-PDF target and false readiness. No experiments, API calls, credentials, model/database loading, research generators or new statistical inference occurred.

## Findings preventing a clean certificate

1. **F01/blocker:** main12's14-baseline page enlargement pushes part of the refusal/clamping disclosure below the physical PDF boundary.87spans cross the page bound by>1pt; the raster is visibly cut. A no-overfull log does not detect this.
2. **F02/high:** main CategoryA q values0.0177/0.3623 disagree with full-family TableS1 values0.0189/0.3865. No rounding explanation; family reporting must be reconciled.
3. **F03/high:** the lexical explanation says TERRA writes longer answers, but TableIII shows415words versusFlat481. Delete unsupported causal language.
4. **F04/medium:** doubled66/100/100 and1/100/100; recall differences mislabeled as percentages instead of percentage points.
5. **F05/medium:** TableIV incorrectly bolds Hippo0.910 instead of TERRA0.941 for CategoryA; TableIII bold conventions also disagree with its note.
6. **F06/medium:** a64%rubric-refusal sentence cites Figure3's distinct61.3%system-flag measure without distinguishing them.
7. **F07/high:** L7 calls CLERC50.0%/37.5%misapplication flags a gold-precedent omission rate.
8. **F08/high/evidence unavailable:** strong prebenchmark parameter-freeze chronology is unestablished by the historically qualified records. This is not a finding that the claimed sequence is false.
9. **F09/high:** Figure1 and several essential tables are too small at normal physical size. Figure1minimum2.18pt; main13table spans reach2.54pt. Magnification permits inspection but does not solve physical readability. I9deferral remains explicit.
10. **F10/high:** supplementS5 incorrectly calls SAT-Graph a propositional SAT solver; the cited publisher paper describes Structure-Aware Temporal retrieval. Bibliography saysvolume395/pages586–591; official volume416/pages282–287 are required. Primary sources are linked in CITATION_REGISTER.
11. **F11/low:** duplicate count/percentage strings, an unlabeled0.586in the conclusion and an overbroad all-category safe-handling label need clarity corrections.

All findings have exact current source hashes/lines, consequences, owners, proposals and closure tests in FINDINGS.json. Exact text proposals and an unbuilt diff are supplied, **not adopted**. F09needs measured local layout work; the rejected Springerconversion is not restarted. The main remains25pages as audited, but there is no claim a corrected candidate will remain25until rebuilt and checked.

## Build and protection interpretation

Main:427font-warning lines,71underfull,0overfull; supplement0font-warning,199underfull,0overfull. No undefined-reference or missing-character diagnostics. Main warnings are TU/ptm/pcr substitutions, including407bold-normal warnings; glyphs were inspected, but substitution counts cannot excuse wrong emphasis, tiny type or clipping.

Earlier accepted pixel-parity/build and limited visual reports remain historical artifacts, not rewritten. This new full inspection supersedes any inference that accepted-page parity proves full physical-page content or unrestricted readability. In particular, the page12 defect survives identical builds.

## Reviewer and roadmap disposition

REVIEWER_RESPONSE_DRAFT.md addresses the actual preserved user-relayed five-point letter, not the simulated assessment. It is unsent, carries current locations and explicitly leaves expert validation unfulfilled. The prospective primary result remains0.26885 withCI[0.16035,0.37205], accompanied byT69/H4CategoryBverifier refusals; useful/legal answering is not certified. I6's700surviving verifier inputs have zero independent sufficiency references, so verifier error rates stay unestimated. Original quotation/rationale repairs remain outside the completed ratings-only assessment.

I9format/readability and I10author/submission facts remain deferred/incomplete. The identified master is not an anonymous review variant; no anonymous-package/public-release certification is claimed. Journal intent is confirmed, but complete author/declaration/venue requirements are unresolved. Consent to report assessment findings is not ethics clearance or workbook-publication permission.

Roadmap after this audit:9complete(I0–I8),2partial(I9,I11),2pending(I10,I12). Prior package completion milestones are retained; newly found current defects are explicitly owned by I11and block certification. Separate fields: audit_work_complete=true, certification_complete=false, submission_ready=false. Peer review is pending; no unconditionalPASS or publication-ready claim.

## Next concrete action

Give Antigravity the frozen Codex-0342packet for actual source/PDF/primary-source review, especially F01,F02,F08,F10and the coverage limits. After review, a separately authorized isolated correction candidate can repair reporting/layout and undergo full changed-page/page-budget verification. The current I11plan requires proposals and explicit accepted-source adoption authority; this implementation did not silently broaden the audit into manuscript rewriting. No new paid study or API key is indicated.
'''
write('FINAL_AUDIT_REPORT.md',report)
out('IMPLEMENTATION_LIMITS.json',{'self_audit_not_independent':True,'peer_pending':True,'secondary_I10_variant':'not re-audited; unadopted/deferred, not primary target','all_historical_statistics_independently_rederived':False,'all_external_URLs_live_checked':False,'legal_sources_adjudicated':False,'cleanroom_cache_fully_pinned':False,'real_figures_and_all46pages_visually_inspected':True,'physical_page_clipping_and_tiny_fonts_block_certification':True,'automatic_inventory_is_not_human_validation':True})

# Seal a review manifest, excluding itself. Includes scripts/renders/inputs/rebuild evidence.
entries=[]
for p in sorted(P.rglob('*')):
 if p.is_file() and p.name!='I11_REVIEW_MANIFEST.json':entries.append({'relative_path':p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
out('I11_REVIEW_MANIFEST.json',{'author':'Codex','status':'SELF_AUDIT_CORRECTIONS_REQUIRED_PEER_PENDING','entries':entries})
print(json.dumps({'completion':completion,'manifest_entries':len(entries),'manifest_sha256':sha(P/'I11_REVIEW_MANIFEST.json')},indent=2))
