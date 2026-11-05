"""Codex-authored reading notes and proposed dispositions, entered after inspection."""
import hashlib,json,re,difflib
from pathlib import Path
P=Path(__file__).resolve().parent; S=P/'baseline/src'; W=P.parent/'working/src'
def rd(p):return Path(p).read_text(encoding='utf-8-sig')
def out(n,o):(P/n).write_text(json.dumps(o,indent=2,ensure_ascii=False),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

main_notes=[
 'Title/abstract/keywords and introduction read. Generic scaffolds and matched refusal tradeoff visible. Identified master author spelling is known deferred I10 issue; long title occupies three lines, no clipping.',
 'Contributions and related work read. Runtime EASY/HARD distinct from A/B/C/D taxonomy; Direct LLM adverse Category B result and nonexpert scope visible. Dense list but readable body.',
 'Corpus, citation audit and misresolved OVERRULES edges read. 145366 historical edges and corrected derivative distinction retained. Case-specific prototype versus evaluated generic scaffold discussion continues next page.',
 'Figure1/caption, prototype versus evaluated generic scaffold and equation1 read. Architecture is semantically corrected; figure lettering is extremely small (closeup reviewed). No off-page glyphs detected.',
 'Routing equation2, domain flag equation3 and traversal equation4 read. At enlarged inspection equation2 lines are separated; do not repeat old overlap finding. Distance diagnostic scope, 200/75 populations and untested title-match branch explicit.',
 'Four explanation layers, implementation details and taxonomy validation read. Automated taxonomy adjudication and no expert ground truth explicit. Formula continues conventionally onto page7.',
 'TableI, Figure2, benchmark construction and A/B/C/D definitions read. 20000 corpus nodes and query target subset distinct. Chart labels small but identifiable when zoomed.',
 'Obscure-suite design, four historical comparator adaptations and baseline details read. Character ceilings and posthoc amendments explicit; historical graph fingerprint cannot authenticate unavailable run code.',
 'Metrics, query-cluster judge calibration and multi-run provenance read. 1787 valid pairs/200 query clusters and historical file dates properly qualified; faithfulness not legal correctness.',
 'Pilot ablations, freeze chronology claim, author assessment and availability read. Provenance-limited historical record does not establish claimed prebenchmark freeze (F08). Proxy/AI disclosure visible.',
 'TablesII/III, pilot-versus-canonical distinction and lexical comparison read. F03 longer-answer causal explanation contradicts 415 versus481 mean words; TableIII bold rule inconsistent (F05). Tiny pilot table.',
 'Matched comparison, utility paragraph, FDR prose and Figure3 read. Physical bottom clips refusal/clamping continuation (F01). FDR q mismatch F02, figure crossreference conflates different refusal definitions F06.',
 'TablesIV/V and complete table notes, router metrics and misroutes read. CategoryA bold emphasis wrong F05; table text extremely small F09. 48 rubric refusals and46 system flags distinguished in notes.',
 'TableVI and full multiplicity prose plus temporal stress design read. Family20 versus secondary Holm8 explicit. Statistical table too small at physical scale; missing judge values disclosed.',
 'Temporal bounds/H1-H6 and obscure primary gate failure read. Refusal masking and missingness carefully qualified, no primary rejection suppressed.',
 'TableVII all panels/notes and obscure-suite robustness/spotcheck read. Gate CLOSED and stronger-judge dependence explicit. Small table, no clipping.',
 'CaseFacts corpus anti-circularity, 34prototypes not evaluated traces, eight Overruled cases and CLERC protocol read. Repeated percentage strings are editorial clutter, not distinct observations.',
 'TableVIII all panels/notes and CLERC drafting/citation audit read, including final paragraph. Author/source checks are not certified legal judgment. No offpage content; dense caption/notes.',
 'TableIX all panels/notes and chain-recovery text read. Double denominators 66/100/100 and1/100/100, and percentage-versus-percentage-point labels are F04. External misapplication remains adverse evidence.',
 'TableX all panels/notes and sensitivity discussion read. Canonical66, legacy62, bounded61 distinguished. Smallest table notes need major zoom; no new false exact-reproduction complaint.',
 'TableXI all panels/notes, citation validity and cost introduction read. Resolved-link check is permissive and not independently verified legal support; pp unit phrasing is F11.',
 'TableXII all panels/notes and cost/latency text read. Modelled cost not invoice; historical freeze chronology claim F08. Table very small, no clipping.',
 'Cost timing remainder, distance-only calibration and temporal topology stability read. No mechanical early prefilter claim. Topology-only stability not online insertions.',
 'Discussion, utility/verifier audit, limitations summary and conclusion read. 69/4 refusal tradeoff preserved. Conclusion dangling0.586 needs label F11; no deployment/legal correctness certificate.',
 'All remaining references read. SAT-Graph citation volume/pages wrong F10. Other metadata checked with explicit primary-source/author-version limits in citation register.'
]
supp_notes=[
 'Cover statement read; intentionally sparse title page, no missing table inferred.',
 'TableS1 ranks1-15 and all cells read. CategoryA Flat/Hippo q values conflict with main prose (F02). Table legible at enlarged page, split header preserved.',
 'TableS1 ranks16-20 and complete statistical note read. Historical bootstrap origin unverified and M20/Holm8 distinction explicit; substantial whitespace after continuation is not lost evidence.',
 'TableS2 baseline adaptation parameters and notes read. Character ceilings/actual endpoint distinctions retained; sparse landscape page, small superscripts.',
 'TableS3 all raw/clamped values/notes read. 0.6950 raw and0.7357 clamped TERRA; delta percentage points. This disclosure is partly clipped out of main12.',
 'TableS4 all four snapshot pairs/overall read. Pure BFS CPU timing and106 observations not106 uniquequeries; full end-to-end utility not inferred.',
 'TableS5 every comparator/cell/note read. SAT-Graph incorrectly described as propositional SAT solver F10. Generic procedural scaffold caveat visible.',
 'TableS6 both panels/all notes read. EASY110/HARD240 historical router,97.14% accuracy and97.3% CategoryD handling explicit. All-category safe-handling label needs careful scope (F11).',
 'TableS7 both panels and first notes read.85missing judgments/bounded sensitivity and underpowered gate tests retained; table continues note on S10.',
 'Complete TableS7 continuation note read. No independent temporal false-negative validation; sparse page due preserved page breaks, not error.',
 'TableS8 graph metrics/caption read. Original graph versus corrected derivative distinction retained; graph weakcomponent diameter13 not wholegraph guarantee.',
 'TableS9 provenance rows read. mtimes explicitly labeled, pilot date not recorded; contradiction with strong freeze chronology statement elsewhere F08.',
 'TableS9 remaining rows and entire note read. Simultaneous hub trigger50 and directional75/25 correctly explained; no historical backend weight proof.',
 'TableS10 gross/net, route/category blocks and note read. Correct110/240 route populations and100/100 category populations, server retry sleep qualified.',
 'Limitation1-6 start read. Expert absence, refusal-volume masking, discrete ceiling, corpus bounds, API variation and parametric memory explicit.',
 'Limitation6 continuation and7-13 start read. L7 mislabels CLERC misapplication rates as precedent omission F07. Other limits retained, no quiet expert-validation claim.',
 'Limitation13 continuation and14-18 read. Corpus filtering/taxonomy/private-law limitations retained. L17 strong prior-freeze chronology F08.',
 'Author-assessment methods/table/notes plus prospective comparison methods read. 76denominators, AI-proposed versus human-first workflows and unblinded reconciliation explicit; no pipeline inference.',
 'TableS11 and prospective history/cost plus utility audit counts read.2706calls/$61.935583 conditional rate, H178/T78 invocations and H77/T29 two-judge proxies consistent with accepted records.',
 'Utility denominators/partitions,40query source sample,948occurrences/1896checks and verifier feasibility read. Zero sufficiency gold; rates unestimated; original quotation corrections not silently reopened.',
 'All six supplement references read. SAT-Graph wrong metadata repeated F10; nonanonymous master, not I10 anonymous derivative.'
]
coverage=[]
for doc,notes in [('main',main_notes),('TERRA_SUPPLEMENT',supp_notes)]:
 rows=json.loads(rd(P/'reading'/doc/'COVERAGE.json'));assert len(rows)==len(notes)
 for row,note in zip(rows,notes):
  row.update(document=doc,human_reading='COMPLETED_BY_CODEX',human_visual='COMPLETED_BY_CODEX',review_date='2026-10-26',review_notes=note,independence='implementation self-audit; not legal-expert or external independent review')
 coverage+=rows;out(f'reading/{doc}/COVERAGE.json',rows)
out('READING_COVERAGE.json',coverage);out('VISUAL_PAGE_REVIEW.json',coverage)

# Every finding cites accepted snapshot bytes, with an explicit owner and closure test.
findings=[]
def finding(i,severity,title,file,line,pages,evidence,repair,closure,status='STILL_PRESENT'):
 findings.append(dict(id=f'I11-F{i:02}',severity=severity,title=title,artifact=str(W/file),artifact_sha256=sha(S/file),source_line=line,rendered_pages=pages,status=status,evidence=evidence,consequence=title,proposed_disposition=repair,owner='Codex correction proposal; user authorizes accepted-source adoption; Antigravity peer checks evidence',closure_test=closure))
finding(1,'BLOCKER','Scientific disclosure extends below the physical bottom of main page12','main.tex',462,['main12'],
 '87 text spans cross the physical page boundary by more than1pt in infinite-rectangle extraction. Normal extraction omits part of the refusal/clamping paragraph; actual raster ends at “counting unflagged textual”. Source explicitly enlarges page by14 baselines. No other audited page crosses this bound.',
 'Remove the 14-baseline enlargement in an isolated correction candidate and reflow. Preserve all refusal and raw/clamped disclosures. If this yields26pages, repair layout locally with evidence retained; do not shrink until unreadable or silently discard text.',
 'All paragraph text must be visibly rendered within the page; inspect page12 and every reflowed page, text/layout parity for unaffected pages, main<=25 with readable type.')
finding(2,'HIGH','Two CategoryA FDR q values disagree between main and complete-family table','main.tex',463,['main12','supplementS2'],
 'Resolved CatATerraVsFlatRAGAdjQ=0.0177 and CatATerraVsHippoRAGAdjQ=0.3623; TableS1 ranks12/15 show0.0189/0.3865. Raw p values agree0.0114/0.2898. These are not rounding equivalents.',
 'Use the reviewed M20 family as a single reporting source. Proposed local correction-layer overrides0.0189/0.3865 align the existing full-family table without editing generated_stats or rerunning tests. Peer must confirm family identity before adoption; significance decisions unchanged.',
 'Trace all20 family inputs to accepted derivation; every occurrence must agree on family, p and q; no empirical/statistical regeneration in this audit.')
finding(3,'HIGH','ROUGE explanation claims longer TERRA answers despite the displayed shorter mean','main.tex',423,['main11'],
 'TableIII reports TERRA415 words, Flat481, Graph477, Hippo470 and Direct612. Prose attributes Flat higher F1/precision to TERRA writing longer chronological syntheses. Answered-only TERRA490 has a different denominator and does not identify this causal explanation.',
 'Delete the unsupported causal clause. Keep length sensitivity definition, all means and separately qualified answered-only comparison. Do not supply another untested causal story.',
 'Read paragraph/TableIII together and check no unsupported length-cause claim remains.')
finding(4,'MEDIUM','Chain counts acquire a duplicate /100 and recall lifts have wrong units','main.tex',597,['main19','main21'],
 'FullPathCount macros already include denominators, yielding66/100/100 and1/100/100. Main19 calls +62.1% and+20.4% recall lifts; displayed recall differences are percentage points. Main21 similarly says “+13.97% to+16.75% points”.',
 'Drop duplicate /100 suffixes; label differences62.1 and20.4 percentage points and citation-recall differences13.97 to16.75percentage points. Keep original counts/macros unchanged.',
 'Rendered source/paragraph count conventions consistent; no /100/100 strings; distinguish ratios from differences.')
finding(5,'MEDIUM','Bold emphasis does not implement table notes','main.tex',443,['main11','main13'],
 'TableIV CatA bolds Hippo0.910 but not TERRA0.941, despite note saying top among RAG. TableIII bolds Direct recall/wordcount under a RAG-only rule and all three TERRA win rates although only73% is largest. Mean words is descriptive, not a benefit direction.',
 'Move TableIV CatA bold to TERRA. For TableIII remove metric-cell bold and state cells are descriptive, with TERRA row named for identification; alternatively define each direction explicitly and apply consistently.',
 'Inspect both tables and captions at readable zoom against numeric extrema, excluding Direct only when note says so.')
finding(6,'MEDIUM','Figure3 is cited as if it depicted the different rubric refusal measure','main.tex',465,['main12','main13'],
 'Prose describing48/75=64.0% rubric refusals cites Figure3, whose TERRA CategoryD system-flag bar is46/75=61.3%. TableV preserves both definitions.',
 'Remove Figure3 from that rubric-rate sentence, or explicitly say it shows the distinct system-flag outcome. Keep both actual values and definitions.',
 'Sentence/figure/table endpoints and denominators must match after rebuild.')
finding(7,'HIGH','Limitation7 mislabels CLERC doctrinal-misapplication rates as precedent omission','supplement_limitations.tex',14,['supplementS16','main18-19'],
 '50.0%/37.5% in CLERC TableIX and prose are OR/AND dual-judge doctrinal-misapplication rates over120 completions; they are not a measured gold-precedent omission rate.',
 'Use the correct endpoint label with120 denominator and preserve incomplete-context explanation as a hypothesis, not a causal finding.',
 'L7, TableIX and CLERC prose must name identical endpoints and populations.')
finding(8,'HIGH','Claimed prebenchmark hyperparameter freeze is not established by the qualified provenance records','main.tex',352,['main10','main22','supplementS17'],
 'SectionV-D.4,TableXIIcaption,L17 assert parameters frozen before benchmark with Augustpilot and chronological audit. I2 E01-E03 unknown time/code/index and TableS9 pilot date-not-recorded do not authenticate this chronology. Present-day code and mtimes are insufficient. Not a finding that the chronology is false.',
 'Qualify as recovered design rationale/current source settings; date and execution order unverified. Preserve benchmark-overlap audit separately because zero overlap is not proof of temporal precedence. Reinstate strong chronology only with contemporaneous authenticated records.',
 'Either produce hash-linked contemporaneous records establishing sequence or consistently qualify all three claims; no mtime-to-run inference.',status='EVIDENCE_UNAVAILABLE')
finding(9,'HIGH','Essential main-paper tables and Figure1 are illegibly small at normal physical size','main.tex',154,['main4','main11','main13','main14','main16','main18-22'],
 'Font spans include Figure1minimum2.18pt and table content/notes around2.54-4.87pt on several pages. Full-page and 3x closeups reviewed. No overfull-box warning proves readability; known I9 deferral cannot certify this away.',
 'Plan measured local repagination/rebalancing with essential summaries readable in main and detailed supporting cells readable in supplement; preserve all objects/18limits and<=25main. Do not restart Springerconversion or globally shrink.',
 'Inspect actual-size pages and closeups after chosen local design; pagecap and retained-cell checks both pass. User-deferred I9 remains explicit.')
finding(10,'HIGH','SAT-Graph mechanism and bibliography are incorrect','supplement_tables/table_system_comparison.tex',16,['supplementS7','main25','supplementS21'],
 'S5 says propositional SAT solver. Publisher paper DOI10.3233/FAIA251598 defines Structure-Aware Temporal graph and deterministic structural/version/provenance primitives, not Boolean satisfiability. Publisher PDF pp282-287; official IOS book volume416, whereas ref.bib says395/586-591.',
 'Replace cell by deterministic structural/temporal retrieval and provenance primitives, no SAT-solver claim. Correct only this bib entry to volume416/pages282--287 against linked primary sources.',
 'Inspect full cited paper and official volume metadata, then verify both bibliography renderings and S5cell.')
finding(11,'LOW','Redundant count formatting and a dangling conclusion value impair clarity','main.tex',706,['main17-19','main24','supplementS8'],
 'Repeated count macros plus literal percentages produce strings such as50/50(100.0%)(100.0%). Conclusion parentheses end with unlabelled0.586. S6 all-cohort “safe handling” is not a validated legal-safety measure for ordinary A/B answers.',
 'Remove duplicated textual percentages without changing macros. Label0.586 explicitly as historical answered-subset faithfulness. Qualify S6 aggregation as rubric/no-recorded-fatal-outcome accounting, not legal safety.',
 'Read rendered sentences for unique count/percent reporting and endpoint labels; no numeric/ratings changes.')
out('FINDINGS.json',findings)

limitations=[]
s=rd(S/'supplement_limitations.tex')
lim_matches=list(re.finditer(r'\\item\s+(?:\\label\{[^}]+\})?\\textbf\{([^}]+)\}',s))
for i,m in enumerate(lim_matches,1):
 end=(lim_matches[i].start() if i<len(lim_matches) else len(s))
 limitations.append({'id':f'L{i:02}','title':m.group(1),'file':'supplement_limitations.tex','line':s.count('\n',0,m.start())+1,'source_present':True,'rendered_pages':([15] if i<=5 else [15,16] if i==6 else [16] if i<=12 else [16,17] if i==13 else [17]),'review':'theme retained; accuracy separately audited','finding_ids':(['I11-F07'] if i==7 else ['I11-F08'] if i==17 else []),'text_sha256':hashlib.sha256(s[m.start():end].encode()).hexdigest()})
assert len(limitations)==18;out('LIMITATION_REGISTER.json',limitations)

# Exact proposals are intentionally UNAPPLIED. Each replacement is anchored to the snapshot.
edits=[]
def proposal(file,old,new,why):
 text=rd(S/file);assert old in text,(file,old[:60]);edits.append({'file':file,'old':old,'new':new,'finding':why,'occurrences':text.count(old),'status':'PROPOSED_NOT_ADOPTED'})
proposal('main.tex',r'\enlargethispage{14\baselineskip}','% Removed unsafe page enlargement; natural reflow requires page-budget/layout review.','I11-F01')
proposal('main.tex',", because TERRA writes longer chronological syntheses (mean words in Table~\\ref{tab:cat_b_performance}).", ". Mean lengths are reported in Table~\\ref{tab:cat_b_performance}; these aggregate comparisons do not identify a causal explanation for the F1 difference.",'I11-F03')
proposal('main.tex',r'\CatBTerraFullPathCount$/100',r'\CatBTerraFullPathCount$','I11-F04')
proposal('main.tex',r'\CatBFlatFullPathCount$/100',r'\CatBFlatFullPathCount$','I11-F04')
proposal('main.tex',r'$\mathbf{\HippoRAGCatAFaithfulness}$',r'$\HippoRAGCatAFaithfulness$','I11-F05')
proposal('main.tex',r'$\TerraCatAFaithfulness$ & $\mathbf{\TerraCatBFaithfulness}$',r'$\mathbf{\TerraCatAFaithfulness}$ & $\mathbf{\TerraCatBFaithfulness}$','I11-F05')
proposal('main.tex',r'$q=\CatATerraVsFlatRAGAdjQ$',r'$q=0.0189$','I11-F02: conditional on peer confirmation of M20 family')
proposal('main.tex',r'$q=\CatATerraVsHippoRAGAdjQ$',r'$q=0.3865$','I11-F02: conditional on peer confirmation of M20 family')
proposal('main.tex',r'; Figure~\ref{fig:safety_rejection}',r'; Figure~\ref{fig:safety_rejection} separately shows system-flagged refusals','I11-F06')
proposal('main.tex',r'a $\CatBTerraVsFlatNodeRecallDelta$ node-recall lift',r'a 62.1-percentage-point node-recall difference','I11-F04')
proposal('main.tex',r'and $\CatBTerraVsHippoNodeRecallDelta$ and $\CatBTerraVsHippoPathRecallFactor$ over HippoRAG',r'and a 20.4-percentage-point node-recall difference and $\CatBTerraVsHippoPathRecallFactor$ path-recovery factor over HippoRAG','I11-F04')
proposal('supplement_limitations.tex',r'the gold-precedent omission rate during drafting on CLERC ($\ClercTerraMisapplicationTrackOne$;',r'the dual-judge doctrinal-misapplication flags during drafting on CLERC ($\ClercTerraMisapplicationTrackOne$ across 120 completions, OR/AND respectively;','I11-F07')
proposal('main.tex',r'were frozen before benchmark construction on the basis of topological constraints and feasibility testing on an independent',r'are described in the recovered design account as based on topological constraints and feasibility testing on a separate','I11-F08')
proposal('main.tex',r'An automated audit verifies chronological precedence, zero query ID and prompt-text overlap',r'The available records do not authenticate historical freezing dates or chronological precedence. An automated overlap audit reports zero query ID and prompt-text overlap','I11-F08')
proposal('tables/table_computational_budget.tex',r'was frozen prior to benchmark construction and evaluation',r'is the recovered configured value; its historical freezing date is not authenticated','I11-F08')
proposal('supplement_limitations.tex',r'were fixed prior to benchmark construction and evaluation based on topological network constraints and preliminary feasibility testing on an independent',r'are described in the recovered design account as based on topological network constraints and preliminary feasibility testing on a separate','I11-F08')
proposal('supplement_limitations.tex',r'The development audit does not establish global optimality or exclude all contamination.',r'The available records do not authenticate the historical freezing date or execution order. The development audit does not establish global optimality or exclude all contamination.','I11-F08')
proposal('main.tex',r'overlapping CIs; $\TerraAnswerOnlyFaithfulnessMean$',r'overlapping CIs; historical answer-only faithfulness $\TerraAnswerOnlyFaithfulnessMean$','I11-F11')
proposal('supplement_tables/table_system_comparison.tex','Propositional SAT solver checking logical consistency','Deterministic structural/temporal retrieval and provenance primitives','I11-F10')
bib=rd(S/'ref.bib'); start=bib.index('@inproceedings{demartim2025satgraphrag,');end=bib.index('\n}',start)+2
old=bib[start:end];proposal('ref.bib',old,old.replace('volume={395}','volume={416}').replace('pages={586--591}','pages={282--287}'),'I11-F10')
out('EXACT_PATCH_PROPOSALS.json',edits)
texts={e['file']:rd(S/e['file']) for e in edits}
for e in edits:texts[e['file']]=texts[e['file']].replace(e['old'],e['new'])
diff=''.join(''.join(difflib.unified_diff(rd(S/f).splitlines(True),t.splitlines(True),fromfile='accepted/'+f,tofile='PROPOSED_UNBUILT/'+f)) for f,t in texts.items())
(P/'proposed_unapplied.diff').write_text(diff,encoding='utf-8')

# Curated primary-source registry: metadata checks are not a claim of full-paper expert review.
sources={
'zhang2025respectingtemporalcausalconsistencyentityevent':('https://aclanthology.org/2026.eacl-long.90/','Title/authors/year/EACL2017-2054 and temporal-causal eventgraph abstract checked; bibkey year is internal, not publication year.'),
'liu2026raglearningunderstandinglimits':('https://aclanthology.org/2026.findings-acl.546/','Title/authors/2026/pages11234-11252 and Chronos/continuous-drift abstract checked.'),
'zhu2025rightanswerrighttime':('https://arxiv.org/abs/2510.16715','STAR-RAG title/authors/2025 and time-aligned rule-graph abstract checked.'),
'li2025cotragintegratingchainthought':('https://aclanthology.org/2025.findings-emnlp.168.pdf','Authoritative PDF first page resolves misleading HTML author variants; Xin Zhang/Yongjian Cui correct. Nine-dataset4.0-44.3% abstract statement matches.'),
'liang2025reasoningrag12':('https://aclanthology.org/2025.findings-ijcnlp.122.pdf','PDF firstpage confirms Gang Su rather than HTML concatenation; title/year/pages1954-1966 match. Survey categorization abstract checked.'),
'lin2025comprehensivesurveyreinforcementlearningbased':('https://arxiv.org/abs/2510.16724','Title/year/author list checked; duplicated HuiLiu also occurs in source metadata, not silently deduplicated. Survey-level support only.'),
'roig2026scalablereliableevaluationai':('https://arxiv.org/abs/2601.08847','Title/JV Roig/2026 version confirmed; uncited entry does not render in bibliography. No requirement to add it.'),
'putta2026casefactsbenchmarklegalfactchecking':('https://aclanthology.org/2026.acl-long.785/','Title/authors/2026/pages17246-17265 and dataset/web-search-noise claim checked.'),
'yalavarthi2026opensourcereproductionexplainabilityanalysis':('https://arxiv.org/abs/2603.16169','Title/author/2026 and CRAG evaluator entity-alignment/domain-transfer abstract checked.'),
'hashmi2026adaptivequeryroutingtierbased':('https://arxiv.org/abs/2604.14222','Title/author/2026 and adaptive multi-tier retrieval abstract checked.'),
'edge2024graphrag':('https://arxiv.org/abs/2404.16130','Title/authors/2024 first submission; entity graph/community summaries in abstract support original method distinction. Current2025revision does not invalidate original year.'),
'sun2024thinkongraph':('https://arxiv.org/abs/2307.07697','Title/authors and iterative LLM/KG exploration checked; conference2024 supported by author ICLR paper. No local implementation equivalence inferred.'),
'zheng2023judging':('https://arxiv.org/abs/2306.05685','Title/authors/NeurIPS2023 track and judge-bias/human-preference scope checked; not legal validation.'),
'lewis2020retrieval':('https://proceedings.neurips.cc/paper/2020/hash/6b493230-Abstract.html','Official title/authors/year and parametric-plus-retrieved-memory method checked; not a claim that local flat baseline is the original trained architecture.'),
'guu2020realm':('https://proceedings.mlr.press/v119/guu20a.html','Official title/authors/2020/pages3929-3938 and retriever pretraining method checked.'),
'asai2024selfrag':('https://openreview.net/pdf?id=hSyW5go0v8','ICLR2024 officialpaper title/authors and reflection-token method checked; no equivalence to TERRA verifier inferred.'),
'bernal2024hipporag':('https://proceedings.neurips.cc/paper_files/paper/2024/hash/6ddc001d07ca4f319af96a3024f6dbd1-Abstract.html','Official title/authors/2024 and knowledge-graph/PPR method checked. Local adaptedbaseline remains distinct.'),
'hoenig2001abuse':('https://doi.org/10.1198/000313001300339897','Publisher title/authors/55(1),19-24,2001 and critique of postexperiment power checked.2012online date not substituted for issueyear.'),
'chen2026legalgraphrag':('https://aclanthology.org/2026.acl-long.1738/','Official title/authors/2026/pages37455-37484 and hierarchical legal graph/threeagent abstract checked. Detailed S5feature cells not all independently replicated.'),
'demartim2025satgraphrag':('https://journals.sagepub.com/doi/pdf/10.3233/FAIA251598','Full six-page paper inspected: Structure-Aware Temporal, not SATsolver; printed282-287. Official IOSbook https://www.iospress.com/catalog/books/legal-knowledge-and-information-systems confirms volume416. FindingF10.'),
'cushman2021eyecite':('https://joss.theoj.org/papers/10.21105/joss.03617','Official title/authors/2021/6(66),3617 checked. Citation parser not doctrinal adjudicator.'),
'hou2024clerc':('https://aclanthology.org/2025.findings-naacl.441/','Official title/eightauthors/2025/pages7913-7928 and two tasks checked. Bibkey2024 not displayed year; an initially guessed .444 URL was unrelated and discarded.'),
'zheng2021casehold':('https://arxiv.org/abs/2104.08671','Primary author preprint confirms title/authors/2021/ICAIL and holding-identification task. ACM DOI retrieval returned403; exact finalpublisher page range not independently fetched.'),
'dubey2024llama3':('https://arxiv.org/abs/2407.21783','Title/year confirmed. Currentv3 begins Aaron Grattafiori; bib begins Dubey, corresponding to historical author-version attribution. Must select/version-pin before cosmetic metadata update; model-serving identity not certified by this citation.'),
'he2023debertav3':('https://arxiv.org/abs/2111.09543','Title/threeauthors/ICLR2023 publication comment checked; original2021 submission is not conference year.'),
'reimers2019sentencetransformers':('https://aclanthology.org/D19-1410/','Official title/authors/2019/pages3982-3992 checked. Citation alone does not certify deployed embedding preprocessing.'),
'feinstein1990high':('https://pubmed.ncbi.nlm.nih.gov/2348207/','Primary-article indexed abstract/title/authors/1990/43(6),543-549 checked; correct DOI90158-L. Guessed ScienceDirect90158 link unavailable; no fabricated fetch success.'),
'katz2017general':('https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0174698','Publisher article exists with matching title/authors/2017/e0174698; outcome-prediction literature context, no legal correctness claim.'),
'chalkidis2020legalbert':('https://aclanthology.org/2020.findings-emnlp.261/','Official title/authors/year/pages2898-2904 checked; pretrained legal-language-model context.'),
'guha2023legalbench':('https://proceedings.neurips.cc/paper_files/paper/2023/hash/89e44582fd28ddfea1ea4dcb0ebbf4b0-Abstract-Datasets_and_Benchmarks.html','Official title/authors/2023 and162tasks/sixreasoningtypes checked. No claim TERRA evaluated LegalBench.'),
'magesh2025hallucination':('https://onlinelibrary.wiley.com/doi/full/10.1111/jels.12413','Publisher title/year and legal-RAG hallucination scope checked; rates around17% for Lexis/PracticalLaw,33%Westlaw inTableB1. Main over17% phrase should preferably read at least/about17%, not imply all tools strictly exceed17%.')}
bib=rd(S/'ref.bib');keys=re.findall(r'@\w+\{([^,]+),',bib);assert set(keys)==set(sources)
cited={doc:set() for doc in ['main','TERRA_SUPPLEMENT']}
for doc in cited:
 closure=json.loads(rd(P/'SOURCE_INCLUDE_GRAPH.json'))[doc]
 for file in closure:
  for m in re.finditer(r'\\cite(?:\[[^]]*\])?\{([^}]+)\}',rd(S/file)):cited[doc].update(k.strip() for k in m.group(1).split(','))
reg=[]
for key in keys:
 url,note=sources[key];reg.append({'key':key,'primary_or_primary_index_url':url,'access_date':'2026-10-26','cited_in':[d for d in cited if key in cited[d]],'check':'BIBLIOGRAPHIC_AND_BOUNDED_CLAIM_SUPPORT_CHECK','observation':note,'limits':'Not independent replication of cited experiment; full-paper reading only where explicitly stated; author metadata version limits retained.'})
out('CITATION_REGISTER.json',{'entries':reg,'entry_count':len(reg),'cited_counts':{d:len(v) for d,v in cited.items()},'undefined_citekeys':{d:sorted(v-set(keys)) for d,v in cited.items()},'uncited_entries':sorted(set(keys)-set.union(*cited.values()))})
print('Curated',len(coverage),'pages,',len(findings),'findings,',len(limitations),'limitations and',len(reg),'references; proposals unapplied.')
