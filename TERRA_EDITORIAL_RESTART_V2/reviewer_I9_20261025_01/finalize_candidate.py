from pathlib import Path
import json,hashlib,re
P=Path(__file__).resolve().parent;R=P.parents[1];S=P/'candidate/src';L=P/'ledgers'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
result=read(P/'I9_COMPLETION.json');assert result['final_revision']=='r34'
review=read(L/'PAGE_REVIEW.json');assert review['all85pages_implementation_visual_review_complete']
for n in ['sn-jnl.cls','sn-basic.bst']:
 official=P/'assets/template/sn-article-template'/('bst/'+n if n.endswith('.bst') else n)
 assert sha(official)==sha(S/n)
matrix=read(L/'TRANSPOSED_CELL_RETENTION.json');assert len(matrix)==11
t=next(x for x in matrix if x['label']=='tab:retrieval_eval')
b=next(x for x in t['transposed_sections'] if 'Panel B:' in x['heading'])
assert len(b['rows'])==6
assert all('Node Recall' in row[1] for row in b['rows'][::2])
assert all('Full Precedent Path Recall' in row[1] for row in b['rows'][1::2])
for pair in range(3):assert b['rows'][2*pair][0]==b['rows'][2*pair+1][0]
budget=next(x for x in matrix if x['label']=='tab:computational_budget')['transposed_sections'][0]
assert budget['rows'][0][0].startswith('Direct LLM') and 'Gen Calls' in budget['headers'][2]
refusal=next(x for x in matrix if x['label']=='tab:refusal_breakdown')['transposed_sections'][0]
assert refusal['rows'][0][0].startswith('Direct LLM') and 'N=100' in refusal['headers'][1]
write(L/'TABLE_ROLE_REGRESSIONS.json',{'status':'PASS','retrieval_panel_B_has_six_distinct_data_rows':True,'node_and_path_recall_are_not_header_rows':True,'chain_length_ditto_labels_forward_filled_from_preceding_explicit_baseline_row':True,'budget_second_header_is_units_not_fake_architecture':True,'refusal_denominators_are_headers_not_fake_pipeline':True,'all11logical_tables_have_recorded_raw_data_matrices':True,'matrices_and_original_source_must_still_be_peer_reviewed':True})
requirements=read(L/'REQUIREMENTS.json')
for x in requirements:
 if x['id']=='R6':x.update(status='IMPLEMENTATION_SELF_VERIFICATION_COMPLETE',evidence='67main+18supp pages inspected directly or by exact pixel/text parity; scientific text read; final links separately verified. External peer review remains R8.')
write(L/'REQUIREMENTS.json',requirements)
result['remaining']=['Resolve the 25-page versus 67-page journal-format contract; no waiver assumed','Antigravity review of the exact I9 candidate and reconciliation of its findings','If accepted under the agreed page contract, adopt the reviewed allowlist and rebuild working sources','SNAPP pdfLaTeX compatibility and complete submission certification remain I10/I11']
result['implementation_self_visual_review_complete']=True
result['all85pages_covered']=True
result['external_peer_review_received']=False
result['working_adoption_performed']=False
write(P/'I9_COMPLETION.json',result)
changed=result['changed_candidate_files']
findings=[{'id':'I9-PAGE','severity':'BLOCKING_DECISION','status':'OPEN','finding':'67main pages exceeds advisor ceiling25','evidence':'builds/r34/BUILD_RESULT.json; PAGE_LIMIT_OPTIONS.md'},
 {'id':'I9-PEER','severity':'ADOPTION_GATE','status':'OPEN','finding':'Exact I9 candidate not yet reviewed by Antigravity','evidence':'peer contains Codex self-review reports on older r13, not external I9 acceptance'},
 {'id':'I9-TEMPLATE','status':'RESOLVED_IMPLEMENTATION_VERIFIED','finding':'IEEE to official Springer sn-basic migration','evidence':'Official901814byte bundle, class/bst identity unchanged'},
 {'id':'I9-FONT','status':'RESOLVED_IMPLEMENTATION_VERIFIED','finding':'Inherited427main font warnings','evidence':'T1 standard encoding and native fonts; no final LaTeX Font Warning or missing glyph; lmtt bx-to-b informational selection disclosed'},
 {'id':'I9-FOOTER','status':'RESOLVED_IMPLEMENTATION_VERIFIED','finding':'Inherited page-enlargement commands intruded into footer under journal layout','evidence':'All three enlargement directives removed; source.diff and rendered-page checks'},
 {'id':'I9-ARCH','status':'RESOLVED_IMPLEMENTATION_VERIFIED','finding':'Tiny/overlapping figure labels, retry semantics and overstrong generated-link label','evidence':'Native8.5/9pt figure; qualified labels; current-source retry evidence and historical caveat retained; finalpage6 inspected'},
 {'id':'I9-GRAPHS','status':'RESOLVED_IMPLEMENTATION_VERIFIED','finding':'Charts had scaled tiny fonts and crowded legend/ticks','evidence':'Native charts, explicit tick interval, 8.5/9pt value/legend labels; values unchanged'},
 {'id':'I9-TABLES','status':'RESOLVED_IMPLEMENTATION_VERIFIED','finding':'Tiny scaled tables and draft conversion row-role defects','evidence':'11transposed9pt logical tables and wrapped corpus table; role regressions, raw matrices, repeated headers and stable labels'},
 {'id':'I9-LINK','status':'RESOLVED_IMPLEMENTATION_VERIFIED','finding':'xr generated dangling same-document destinations for external references','evidence':'xr-hyper + macro-load ordering; all GoToR target filenames and named destinations independently checked'},
 {'id':'I9-CITATION','status':'RESOLVED_IMPLEMENTATION_VERIFIED','finding':'IEEE numeric style and repeated names after author-year migration','evidence':'sn-basic and appropriate citet/citep; same citation keys/ref.bib'},
 {'id':'I9-REPORTING','status':'RESOLVED_IMPLEMENTATION_VERIFIED','finding':'Reversed section range, repeated macro percentages, remediation residue, total-edge nomenclature and unsupported length causal claim','evidence':'REVIEW_DISPOSITIONS.json and source.diff; no quantities regenerated'},
 {'id':'I9-REPRO','severity':'I10_I11_HANDOFF','status':'OPEN_OUTSIDE_I9_CERTIFICATION','finding':'Actual submission-system pdfLaTeX build not verified by local XeTeX','evidence':'Build command uses Tectonic0.17.0; class pdflatex option is not proof of actual engine'}]
write(L/'FINDINGS.json',findings)
report=f'''# I9 implementation candidate and decision report

25 October 2026. Author: Codex. **I9 remains PARTIAL.** The approved Springer-format migration and implementation self-checks are packaged. The main paper is **67 pages**, including references, against the retained advisor ceiling of **25**; the separate supplement is **18 pages**. No page-limit waiver, external peer acceptance or working adoption is claimed.

## What is implemented

The candidate uses the official Springer Nature December2024 template3.1, unmodified sn-jnl class and sn-basic author-year bibliography. Its two support files match the901814-byte official downloaded bundle. The local compiler remains Tectonic0.17.0/XeTeX, with the class's pdflatex option preventing an incompatible legacy breakurl path. This is not a verified SNAPP pdfLaTeX submission build; I10/I11 retain that requirement.

IEEE front matter/page overrides were removed, six indexing keywords selected, and an anonymous review candidate prepared. The existing identified authorship/affiliation block and complete original source remain preserved in baseline; no author facts or corresponding-author designation were invented. The old generated IEEE main.bbl was excluded from the editable candidate so the bibliography rebuilds in author-year form; ref.bib is byte-identical.

Twelve main-paper logical table objects remain in the main paper: eleven now use native9-point transposed continued layouts with repeated entity/panel headers and one uses a wrapped corpus layout. No scientific object was removed, merged or moved between main and supplement. The architecture is native8.5/9-point vector text with separate arrow lanes, current-code retry qualification and a historical-run caveat; the two charts use readable native fonts and unchanged plotted values. Original smaller/inactive source copies were restored where unnecessary mechanical changes had occurred.

The audit also repaired source-backed reporting/layout issues: total graph-edge terminology, an unsupported candidate-length causal explanation, duplicated author-year names, duplicated CaseFacts percentages already supplied by macros, a reversed section range and internal Fix1 residue. Three inherited page-enlargement commands that caused footer intrusion under the new class were removed. All corrections have source diffs and dispositions; no new scores or inference were computed.

## Verification and exact limits

The final build generation is **r34**. All four cached compiler invocations exited0. Main and supplement have zero overfull boxes, undefined references/citations, duplicate labels/destinations and unresolved question marks. No missing-character or LaTeX font warnings remain. One informational Latin Modern typewriter selection maps extended bold bx to the available standard bold b. Underfull diagnostics remain74main/215supplement and are not suppressed; these do not themselves certify typography.

Codex read and visually inspected all **85 final pages**, directly or by exact pixel/text parity with a previously inspected generation. Final internal and cross-document link targets were separately checked against both actual PDFs. This is implementation self-verification, not an independent external audit or expert legal validation. Original r13 Codex subagent reports remain in peer/ with their actual scope and findings; later subagent usage-limit interruptions do not become fabricated final verdicts. Antigravity has not yet reviewed this I9 candidate.

The active source label multiplicities and citation-key sets match the I7 baseline. All frozen generated/correction macro files, bibliography data and all18limitation themes are preserved. Explicit table-role checks now distinguish six retrieval chain-length/metric data rows from headers, preserve forward-filled baseline ditto grouping, and distinguish computational units/refusal denominators from actual architectures. Draft conversion defects found during review are repaired only in the isolated candidate; matrices plus final rendered cells remain available for peer examination.

All **46 working-source files remain byte-identical to the I7 baseline**. The candidate changes {len(changed)} existing source files, adds the two official support files and omits the stale generated main.bbl. The candidate has not replaced the working tree, canonical manuscript or submitted package. No credential access, model/API call, database operation, experiment, threshold change, statistical regeneration or promotion occurred. Public network access was limited to the official template and standard compiler dependencies; build logs preserve cache fetches.

## Why I9 is not DONE

The approved plan explicitly says to present measured options if readable content does not satisfy25pages in the approved format. The current67-page build is **42pages over**. It is a measured candidate, not a proven minimum achievable length. An IEEE25-page document and a Springer single-column67-page document are different layouts; the source migration, larger objects and repeated readable headers change pagination. No journal-specific25-page maximum was established here.

See PAGE_LIMIT_OPTIONS.md for the concrete decision routes. A confirmed revised page contract or a separately approved scientific restructuring is required before final adoption. External peer review and exact reviewed working adoption/rebuild also remain. The roadmap stays6complete/4partial/3pending; I7 remainsDONE and I9 remainsPARTIAL.

## Evidence and deliverables

Review PDFs: output/pdf/main.pdf and output/pdf/TERRA_SUPPLEMENT.pdf. Editable candidate: candidate/src/. Final source identities: candidate/SOURCE_MANIFEST.json and candidate/MANIFEST.json. Full changes: source.diff. Requirements, object layouts, content retention, typography, references/links, page review and findings are in ledgers/. Exact build inputs/outputs/commands/logs are in builds/r34/. Official template provenance is in assets/ACQUISITION.json. Baseline and all superseded/failed build evidence are preserved.

The final package manifest verifies identities, not scientific truth or publication readiness. No claim of an error-free paper, optimal pagination, journal acceptance or independent legal correctness is made.
'''
(P/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
options='''# Page-limit decision: measured options

Current reviewed-in-implementation candidate:67main pages including references,18separate supplement pages. Preserved I7 IEEE baseline:25main/18supplement. These are actual builds, not page-equivalence estimates or a proof that67is the shortest readable journal draft.

1. **Recommended first decision: confirm whether the advisor's25-page ceiling applies to the selected Springer template.** If the advisor/user explicitly revises that format-dependent ceiling, retain the complete readable journal-format candidate, reconcile Antigravity's review, then adopt/rebuild the exact accepted files. Do not treat this document as a waiver. A journal's recommended template does not itself establish its permitted article length.

2. **Keep25pages and authorize a substantive restructuring proposal.** Candidate objects that could be proposed for relocation, each requiring explicit object-specific acceptance, are Table7 `tab:obscure_overruled_eval` (`tables/table_obscure_overruled_eval.tex`, complete obscure outcomes/tests/robustness), Table8 `tab:casefacts_eval` (complete external CaseFacts evidence), Table9 `tab:clerc_eval` (complete CLERC evidence), Table10 `tab:retrieval_eval` (all retrieval/sensitivity panels and legacy/canonical distinctions), Table11 `tab:citation_eval` (generated citation audit), and Table12 `tab:computational_budget` (all timing/cost/calibration panels). All six are presently in the main paper and have not been moved. Any accepted move must retain the main-text result, denominator, adverse finding, uncertainty and locator, create a real supplement destination first and preserve the complete object once. This is a named proposal list, not permission or a promise that these moves reach25pages. Their ranges overlap narrative pages; subtracting page spans is invalid. A separately frozen reflow trial and complete fact-retention map are necessary. If even that misses25, an actual scope/length decision remains; no automatic deletions follow.

3. **Use the preserved25-page IEEE version for advisor comparison only.** It remains available unchanged, but it does not close the selected journal-format I9 task. Do not relabel it as Springer-compliant.

No option permits tiny fonts, margin manipulation, hidden exclusions, omitted adverse results, changed statistics, weakened qualifications or unapproved object removal. The next action needs the real page-contract decision, not an API key or another experimental run.
'''
(P/'PAGE_LIMIT_OPTIONS.md').write_text(options,encoding='utf-8')
chronology='''# Implementation chronology and evidence limits

All earlierbuilds are superseded by r34 and are not deliverables. Initial network-disabled acquisition failed before download; the authorized official public template acquisition then succeeded with preserved hash. Cached-only early builds exposed missing standard font/TeX assets; bounded compiler fetches were recorded. An article supplement needed the sn-basic bibliography heading interface, the main needed the class pdflatex option to avoid legacy breakurl under XeTeX, and stale IEEE main.bbl had to be excluded. r09 compiled but its analysis writer failed on Windows default encoding; later writers use UTF-8 for extracted text. Those failures are not scientific runs or paid API retries.

The first wrapped/landscape drafts and early transposed layouts were superseded after actual render inspection found crowded cells, unsuitable continuation headers and figure text/arrow collisions. Font size/arrow geometry, repeated continued-block headers, chart ticks/legend and ordinary template body/footer geometry were then repaired. Two inherited empty-first-cell data patterns required explicit row-role fixes: retrieval full-path rows must not be merged into headers, while computational unit rows and refusal denominator rows must be merged into headers. All affected output/matrices are preserved by revision; final role-regression checks and final rendered cells were examined. Never reuse a generic table transpose without those role checks.

The review-correction helper initially had a quoting SyntaxError before any write; an unchanged duplicate build r26 was nevertheless produced by the following orchestrated call. It is superseded, not evidence of an applied fix. The corrected helper and later exact source diff document actual changes. xr-hyper first failed when imported captions expanded macros before the supplement loaded their definitions; moving externaldocument after the frozen macro imports repaired it. The audit helper's first18-theme extraction regex was replaced by exact text-normalized retention plus the authenticated I7 theme ledger, avoiding an unsupported new theme count.

The final artifacts are technical review candidates. Full Codex implementation reading/render checks and mechanical identities are not an external peer verdict, a pdfLaTeX submission-system build or practitioner validation. Working/canonical sources were not modified during these candidate repairs.
'''
(P/'rejected/REVISION_HISTORY.md').write_text(chronology,encoding='utf-8')
memo=R/'coordination/terra_antigravity/codex_to_antigravity/20261025-codex-0324-i9-springer-candidate-and-page-contract.md'
memo.write_text('# Codex-0324: I9 Springer candidate, page-contract decision and peer request\n\n'+report+'\nPlease review the exact r34 source diff, table-role matrices/regressions, source-protection checks, all actual rendered pages and named-link target checks. Inspect specifically retrieval PanelB grouping, computational two-level units, refusal denominators, continued comparisons, font sizes, diagram arrows/ports, footer bounds and retained qualifications. Confirm your actual inspected coverage; do not infer full visual review from a build receipt. Do not implement overlapping edits. Return an authored peer message through the user-relayed mailbox.\n\nThe user approved full I9 implementation and the recommended journal template, but did not waive25pages or authorize any named object relocation. Antigravity-0304 is I7 closure, not this I9 candidate acceptance. This memo does not wake an agent or assert a live direct channel.\n',encoding='utf-8')
statuspath=R/'coordination/terra_antigravity/STATUS.json';(P/'baseline/STATUS_before_candidate_handoff.json').write_bytes(statuspath.read_bytes());st=read(statuspath)
st.update(state='I9_SPRINGER_CANDIDATE_SELF_VERIFIED_PAGE_CONTRACT_AND_PEER_PENDING',latest_codex_message='codex_to_antigravity/'+memo.name,current_turn_scope='Codex-0324: authorized I9 journal-format candidate r34,67main/18supp, all85pages implementation reading/visual checks and final named-link validation; generated stats/ref.bib/18themes preserved, working46unchanged. Zero overfull/undefined/duplicates/missing glyph. Advisor25-page limit unmet, no waiver/object move/working adoption/promotion. Exact candidate external peer review and page decision pending.',i9_state='PARTIAL',i9_completion_path='TERRA_EDITORIAL_RESTART_V2/reviewer_I9_20261025_01/I9_COMPLETION.json')
write(statuspath,st)
progresspath=R/'TERRA_EDITORIAL_RESTART_V2/plans/20261025_CURRENT_PROGRESS.json';progress=read(progresspath);progress['i9_evidence']=str(P/'I9_COMPLETION.json');progress['i9_status_note']='67-page Springer candidate self-verified;25-page contract and external peer/adoption remain open';write(progresspath,progress)
manifest=[]
for f in sorted(P.rglob('*')):
 if f.is_file() and f.name!='PACKAGE_MANIFEST.json':manifest.append({'relative_path':f.relative_to(P).as_posix(),'bytes':f.stat().st_size,'sha256':sha(f)})
write(P/'PACKAGE_MANIFEST.json',{'scope':'I9 candidate and preserved history; not accepted/adopted or canonical release','files':manifest})
for row in manifest:assert sha(P/row['relative_path'])==row['sha256']
print(json.dumps({'status':'CANDIDATE_PACKAGED_I9_PARTIAL','files_verified':len(manifest),'main_pages':67,'supplement_pages':18,'working_adoption':False,'source_changes':len(changed),'report':str(P/'FINAL_REPORT.md')}))
