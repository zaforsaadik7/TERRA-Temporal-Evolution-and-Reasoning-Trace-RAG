from pathlib import Path
import json,shutil,hashlib,difflib,subprocess,sys
P=Path(__file__).resolve().parent;R=P.parent.parent;B=P/'baseline/src';C=P/'candidate/src';D=P/'builds/r01';W=P.parent/'working/src';A=P/'adoption_20261026_01'
def rd(p):return p.read_text(encoding='utf-8-sig')
def load(p):return json.loads(rd(p))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def inv(root):return {p.relative_to(root).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file()}
assert not A.exists()
old=load(P/'BASELINE_MANIFEST.json')['sources'];assert inv(W)==old
t=subprocess.run([sys.executable,'-B',str(P/'verify.py')],capture_output=True,text=True)
(P/'TEST_CONSOLE.txt').write_text(t.stdout+t.stderr,encoding='utf-8');save(P/'TEST_RESULT.json',{'tests':12,'passed':t.returncode==0,'exit_code':t.returncode,'scope':'Before adoption; candidate and original working identities checked. No research executed.'});assert t.returncode==0
for f in C.rglob('*'):
 if f.is_file() and f.name!='main.bbl':assert f.read_bytes()==(D/f.relative_to(C)).read_bytes()
shutil.copy2(D/'main.bbl',C/'main.bbl')
A.mkdir();shutil.copytree(W,A/'working_before');shutil.copytree(C,A/'working_after');pdf=A/'output/pdf';pdf.mkdir(parents=True)
prev=P.parent/'reviewer_I11_repairs_20261026_01/adoption_20261026_01/output/pdf';shutil.copytree(prev,P/'baseline/pdf')
changes=[];diff=[]
for k,v in inv(C).items():
 if (C/k).read_bytes()!=(B/k).read_bytes():
  changes.append({'path':k,'before_sha256':sha(B/k),'after_sha256':sha(C/k)})
  diff.extend(difflib.unified_diff(rd(B/k).splitlines(True),rd(C/k).splitlines(True),fromfile='before/'+k,tofile='after/'+k))
  shutil.copy2(C/k,W/k)
assert inv(W)==inv(C)
for name in ['main.pdf','TERRA_SUPPLEMENT.pdf']:shutil.copy2(D/name,pdf/name)
(P/'source.diff').write_text(''.join(diff),encoding='utf-8')
save(A/'ADOPTION.json',{'working_files':59,'changes':changes,'working_matches_built_candidate':True,'pdfs':inv(pdf),'prior_source_backup':'working_before','previous_pdf_backup':str(P/'baseline/pdf'),'promotion':False,'rollback':'Restore only listed changed paths from working_before after checking for intervening edits. Do not replace or delete unrelated directories.'})
report='''# Main-table evidence audit and restoration — 26 October 2026

User concern: shortening Tables II–XII may have moved essential evidence outside the main paper. All eleven summaries were checked against their full supplementary tables and the main passages citing them. The per-table decisions and exact source excerpts are in CLAIM_TABLE_AUDIT.json and CLAIM_TABLE_SOURCE_REVIEW.json (11 tables, 28 citing paragraphs).

## Restorations adopted

- Main Table III (page12): all five pipelines' ROUGE-L precision and F1 restored alongside recall, mean words, faithfulness and TERRA win rates. This keeps the lexical trade-off directly inspectable.
- Main Table VI (page16): Cohen dz and unadjusted p restored for every displayed contrast, alongside mean differences/95% intervals, adjusted q and paired outcomes. C refusal retains Fisher rather than Wilcoxon attribution.
- Main Table VIII (page18): exact95% intervals for all three Overruled recalls and the nonsignificant paired McNemar p=0.625 restored next to the small n=8 gain.
- Main Table VII (page17): both judges' nonsignificant primary test p values made explicit in the note; closed confirmatory gate and curated-label dependency retained.
- Main Table IX (page19): citation brackets explicitly labelled precision/recall, not confidence intervals.
- Prospective comparison (page12): all-query H/T verifier refusals172/272, generator invocations178/78, both-judge-substantive77/29 and response-type disagreements164/116 restored to main prose; CategoryB generator invocations96/31 added beside refusals4/69 and substantive20/1. All-query denominator350 per arm and proxy/validation limits are explicit. These are existing observations, not new estimates or legal correctness.

## Why other detail remains supplementary

The main paper still contains all12 numbered tables. TableII retains all four configurations and the focal pilot outcomes; adjacent text states the small-sample/single-judge/no-test limit. IV/V retain adverse comparisons, differing answered-subset denominators, overlapping overall intervals, fatal errors and distinction between flags/rubric refusal. X/XI retain all comparison arms and adverse precision/coverage results; main prose gives chain-length strata, small-n uncertainty,66/62/61 identities and citation-validator limitations. XII retains calls/latency/cost, with main prose carrying p95, throttling, unmetered prices, noncomparable harnesses and calibration limits. The full stage grids, secondary metrics, all sensitivity configurations, and detailed methods remain available in unchanged full supplementary tables.

This is a table-to-claim sufficiency review, not a claim that all original detail has been put back into the main paper or a guarantee of reviewer acceptance. No essential evidence newly identified by this review remains only in the supplement. The audit register records the rationale for each retained summary.

## Verification and preserved material

Main24 pages; supplement34. No global font reduction, new clipping or wholesale format change. Twelve focused checks pass. Actual main pages12–24 were inspected after reflow; unchanged pages1–11 and all34 supplement pages match the previously inspected rasters byte for byte. Zero overfull boxes, undefined references, missing-character diagnostics or physical off-page spans. Cross-document link targets pass validation. Ordinary existing font substitutions are not claimed eliminated.

All full-detail supplement sources, the generated result macros, figure sources, assessment material and raw study data remain unchanged. Existing scientific macros in changed main inputs were not removed. Exactly five source files changed; no file/table was deleted. Source and PDF before/after copies, exact diff and hashes are retained. Adopted working source matches the tested candidate; no experiment/API/credential/statistics regeneration or I12 promotion occurred.

This new source generation is implementation-self-verified. Prior Antigravity concurrence applies to the previous generation; a fresh bounded source/render review packet is prepared in Codex-0346. Expert correctness validation and I9/I10/I12 remain outside this task and deferred.
'''
(P/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
save(P/'COMPLETION.json',{'status':'MAIN_EVIDENCE_RESTORED_ADOPTED_SELF_VERIFIED','tables_reviewed':11,'main_tables_retained':12,'main_pages':24,'supplement_pages':34,'tests_passed':12,'changed_sources':changes,'working_source_manifest':inv(W),'independent_review_for_this_generation':False,'no_experiments':True})
c=R/'coordination/terra_antigravity';m=c/'codex_to_antigravity/20261026-codex-0346-main-table-evidence-restoration-review.md';assert not m.exists()
m.write_text('# Codex-0346: Main-table evidence restored after user concern\n\nUser authorized reviewing all11 shortened tables and restoring essential claim evidence. Adopted24main/34supp generation in '+str(P)+'; all12 main table labels retained. See FINAL_REPORT.md, CLAIM_TABLE_AUDIT.json, CLAIM_TABLE_SOURCE_REVIEW.json, source.diff, TEST_RESULT.json, VISUAL_REVIEW.json and adoption_20261026_01/ADOPTION.json.\n\nRestored mainIII ROUGEP/F1, VI dz/rawp, VIII small-classCIs/nullp, VII judge-specific nullp, IX citationP/R labels, and main prospective overall utility/refusal proxies. All full supplementary tables, macros and figures unchanged.12 validators pass; changedmain12–24 directly inspected; other45 pages exactrasterparity.\n\nPlease inspect actual changed source and main page12,16,17,18,19 plus reflowed pages for balanced claims and legibility. This new generation is not covered by prior concurrence. No further compression, experiment, source edit, API, credentials or promotion requested. Mailbox is user-relayed.\n',encoding='utf-8')
s=load(c/'STATUS.json');save(P/'STATUS.before.json',s);s.update(state='MAIN_TABLE_EVIDENCE_RESTORED_ADOPTED_SELF_VERIFIED_PEER_PENDING',latest_codex_message='codex_to_antigravity/'+m.name,current_turn_scope='User-authorized11table claim sufficiency review complete. Five files restored/clarified, all12 main tables retained;24main/34supp;12checks pass; allfullsuppdataunchanged. Newgeneration peerpending; no research/API/promotion.');save(c/'STATUS.json',s)
progress=P.parent/'plans/20261025_CURRENT_PROGRESS.json';pr=load(progress);save(P/'PROGRESS.before.json',pr);pr['latest_main_table_evidence']=str(P/'COMPLETION.json');save(progress,pr)
save(P/'manifest.json',{'scope':'Self excluded; all repair evidence files','files':inv(P)})
print(json.dumps({'adopted':str(pdf),'changed_sources':len(changes),'tests_passed':12,'main_pages':24,'supplement_pages':34}))
