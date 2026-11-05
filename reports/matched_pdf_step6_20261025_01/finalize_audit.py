from pathlib import Path
import hashlib,json,shutil,re
import pymupdf as fitz
R=Path(r'F:\TERRA -Copy');P=Path(__file__).resolve().parent;W=R/'TERRA_EDITORIAL_RESTART_V2/working/src'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((P/'working_before.json').read_text())
current={f.relative_to(W).as_posix():{'sha256':h(f),'bytes':f.stat().st_size} for f in sorted(W.rglob('*')) if f.is_file()}
assert current==before
changed=[rel for rel,row in before.items() if h(P/'final_src'/rel)!=row['sha256']]
assert changed==['main.bbl','main.tex'],changed
assert h(P/'final_src/main.bbl')==h(P/'candidate/main.bbl')
aux=(P/'final_src/main.aux').read_text()
cited=set(k for group in re.findall(r'\\citation\{([^}]+)\}',aux) for k in group.split(','))
bibkeys=set(re.findall(r'\\bibitem\{([^}]+)\}',(P/'final_src/main.bbl').read_text()))
assert cited <= bibkeys, sorted(cited-bibkeys)
study=R/'reports/matched_study_r03_20261025_01';seal=json.loads((study/'FINAL_SEAL.json').read_text())
assert h(study/'manifest.json')==seal['manifest_sha256']
for row in json.loads((study/'manifest.json').read_text())['files']:
 f=Path(row['path']);assert f.stat().st_size==row['size_bytes'] and h(f)==row['sha256'],str(f)
results=json.loads((P/'FINAL_BUILD_RESULTS.json').read_text())
assert results['main']['pages']<=25
for n,r in results.items():assert not any(r[k] for k in ['overfull','undefined','multiply_defined','question_marks'])
bounds={}
for name in results:
 doc=fitz.open(P/'final_src'/(name+'.pdf'));outside=[]
 for i,page in enumerate(doc):
  for word in page.get_text('words'):
   x0,y0,x1,y1=word[:4]
   if x0<0 or y0<0 or x1>page.rect.width+0.5 or y1>page.rect.height+0.5:outside.append({'page':i+1,'text':word[4]})
 bounds[name]=outside
 assert not outside,outside
main=(P/'final_main.txt').read_text(encoding='utf-8');supp=(P/'final_TERRA_SUPPLEMENT.txt').read_text(encoding='utf-8')
for token in ['0.26885','0.16035','0.37205','69/100','4/100','legal correctness']:assert token in main,token
for token in ['0.26885','0.16035','0.37205','2706','61.935583','Monte Carlo','seed 42']:assert token in supp,token
output=P/'output/pdf';output.mkdir(parents=True)
for name in results:shutil.copy2(P/'final_src'/(name+'.pdf'),output/(name+'.pdf'))
audit={'status':'STEP6_COMPILE_RENDER_AND_MAIN_PAGE_BUDGET_PASS','author':'Codex implementation self-verification','date_local':'2026-10-25','authorization':'User approved Step 6 with I do after Codex-0316 checkpoint','compiler':'Tectonic 0.17.0','compiler_sha256':h(R/'scratch/tectonic/tectonic.exe'),'cache_only':True,'network_or_provider_calls':0,'results':results,'main_ceiling_including_references':25,'supplement_separate_from_main_ceiling':True,'working_sources_unchanged':True,'sealed_study_660_rows_reverified':True,'isolated_source_changes':changed,'isolated_changes':['Wrap document serialization equation without deleting content','Wrap routing cases within column; same AND/OR conditions','Lowercase duplicated Among in new conclusion'],'render_review':{'overview_pages_inspected':{'main':list(range(1,26)),'supplement':list(range(1,19))},'detail_pages_inspected':{'main':[4,5,11,24],'supplement':[17,18]},'final_pixel_changed_pages_vs_initial_candidate':json.loads((P/'PIXEL_CHANGED_PAGES.json').read_text()),'out_of_page_words':bounds,'scope':'Visual layout inspection, not a new legal/scientific validation'},'warning_comparison':{'baseline_main_overfull':5,'unmodified_integrated_main_overfull':2,'final_main_overfull':0,'final_main_underfull':76,'final_supplement_underfull':209,'underfull_disposition':'Line/box spacing warnings retained; overview and changed-page visual inspection found no associated clipping. Existing dense historical tables were not shrunk.'},'limits':['No canonical promotion or working-source replacement','Independent peer PDF review not yet received','Main-paper 25-page constraint assumed to exclude separate supplement; journal-specific policy remains unverified','Reference pricing and refusal/coverage scientific caveats remain unchanged'],'initial_refinement_stop':'Newline anchor assertion stopped before any isolated edit; original helper and untouched copy preserved as refine_layout.initial.py and refine_initial_no_edits.'}
(P/'AUDIT_RESULT.json').write_text(json.dumps(audit,indent=2)+'\n')
report='''# Step 6: compilation, rendered inspection and page-budget audit

Codex implementation self-verification, 25 October 2026. User approved the previously reserved Step 6. **PASS: main paper 25 pages including references; separate supplement 18 pages.** This checks the advisor\'s main-paper ceiling, not an unverified journal combined-length rule.

## Builds and layout

Tectonic 0.17.0 ran with `-C -k --keep-logs` (cached assets only). Both the pre-study baseline and integrated source were built separately with supplement/main/supplement/main sequencing to resolve external references. Every compilation exited zero. The integrated main already fitted 25 pages, versus 25 for the pre-study baseline; supplement increased from 17 to 18 pages. Baseline and unmodified integrated builds/logs/PDFs are retained.

Rendered overviews were inspected for all 25 main and 18 supplement pages, with full-page inspection of the new results (main 11, supplement 17–18), conclusion (main 24) and equation areas (main 4–5). The new numerical result, interval, refusal tradeoff, limitations and supplement table render without clipping. All three figures and historical table layouts remain present. Existing dense table typography was not reduced to obtain the page count.

Two pre-existing equations exceeded their columns, including the routing case overlapping adjacent text on page 5. Three bounded changes were made **only in final_src/main.tex**: wrapping the document serialization expression; stacking the unchanged AND/OR routing conditions; and changing duplicated capitalized “Among” to “among” in the conclusion. No numbers, thresholds, results, figure/table assets, fonts, margins or limitation content were removed or rescaled. `layout_source.diff` records these changes. The first refinement helper stopped on mixed newline matching before edits; its original and untouched copy are preserved, and the corrected helper completed all builds.

Final main and supplement have zero overfull boxes, undefined references/citations, multiply defined labels or “??” markers. Main retains 76 underfull warnings; supplement 209, primarily spacing in existing tables. They are not suppressed. Extracted word bounds show no text outside pages; this complements rather than replaces rendered inspection. Final main pages 4, 5 and 24 changed in pixels and were inspected at full page size; the other 22 main pages and all 18 supplement pages are pixel-identical to the inspected unmodified integrated rendering.

## Preservation and deliverables

All 46 working-source files remain byte-identical to their pre-Step-6 snapshot. Authored isolated edits are limited to main.tex as described. The compiler also regenerates main.bbl from the unchanged ref.bib and current citations: its bytes equal the unmodified integrated build's generated bibliography, all cited keys resolve, and generated_bibliography.diff records the difference from the stale input bbl. No bibliography entry was manually fabricated or edited. All 660 sealed study manifest rows and the seal digest were reverified. No APIs, credentials, model execution, statistics regeneration, manuscript working-source replacement or canonical promotion occurred.

Final PDFs: `output/pdf/main.pdf` and `output/pdf/TERRA_SUPPLEMENT.pdf`. Reproducible isolated source: `final_src/`. Machine checks and identities: `AUDIT_RESULT.json`, `FINAL_BUILD_RESULTS.json`, `manifest.json`; logs and before/after source receipts are preserved alongside the renders. The old sealed Steps 1–5 package was not edited.

**Step 6 is complete as implementation self-verification.** Antigravity should inspect final PDFs (especially main 4–5, 11–12, 24 and supplement 17–18), the three-region source diff, numerical qualifications and compiler logs. Peer acceptance of these PDFs is not yet claimed. Working-source incorporation of the isolated formatting patch and canonical release remain distinct from this isolated build; no publication or promotion has occurred. The result still measures gated pipeline faithfulness with 69 versus 4 Category B refusals, not verified legal correctness or superior coverage. Reference costs are not audited invoices.
'''
(P/'FINAL_REPORT.md').write_text(report,encoding='utf-8')
memo=R/'coordination/terra_antigravity/codex_to_antigravity/20261025-codex-0317-step6-pdf-and-page-budget-pass.md'
memo.write_text('# Codex-0317: Step 6 PDF and main-page-budget PASS\n\nFrom Codex, 25 October 2026, Asia/Dhaka. User approved Step 6 after Codex-0316.\n\nReport: reports/matched_pdf_step6_20261025_01/FINAL_REPORT.md. Main 25 pages including references; separate supplement 18 pages. Tectonic cache-only builds exit0; no undefined/duplicate references or ?? markers; final zero overfull boxes. Full43-page overview and changed/new passage detail inspection completed. Two existing equation wraps and one capitalization fix isolated in final_src/main.tex, no font/margin/content reduction. Other45 working dependencies preserved; all46 working sources remain unchanged. Sealed660 study rows reverified.\n\nPlease peer-review actual final output/pdf/main.pdf and TERRA_SUPPLEMENT.pdf, layout_source.diff, AUDIT_RESULT.json and logs, particularly main4–5/11–12/24 and supplement17–18. Scientific refusal/coverage and billing caveats remain. No new calls, statistics, working-source replacement or canonical promotion; PDF peer acceptance pending.\n',encoding='utf-8')
status=R/'coordination/terra_antigravity/STATUS.json';(P/'STATUS.before.json').write_bytes(status.read_bytes());s=json.loads(status.read_text());s['state']='MATCHED_COMPARISON_STEP6_PDF_BUDGET_PASS_PEER_REVIEW_PENDING';s['latest_codex_message']='codex_to_antigravity/'+memo.name;s['current_turn_scope']='Codex-0317: user-approved isolated Step6 complete; main25 pages including references/supplement18. Finalzero overfull/undefined/duplicate/??. All43pages overview plus full-size affected/new passages inspected; isolated main3-region layout/case patch only, working46 files unchanged.660sealed rows reverified. NoAPI/model/statistics/promotion. Actual PDF peer review requested; not yet received.';status.write_text(json.dumps(s,indent=2)+'\n')
files=[f for f in sorted(P.rglob('*')) if f.is_file() and f.name!='manifest.json']
(P/'manifest.json').write_text(json.dumps({'files':[{'path':str(f.resolve()),'bytes':f.stat().st_size,'sha256':h(f)} for f in files]},indent=2)+'\n')
print(json.dumps({'status':audit['status'],'pdfs':results,'manifest_files':len(files),'manifest_sha256':h(P/'manifest.json'),'memo':str(memo)},indent=2))
