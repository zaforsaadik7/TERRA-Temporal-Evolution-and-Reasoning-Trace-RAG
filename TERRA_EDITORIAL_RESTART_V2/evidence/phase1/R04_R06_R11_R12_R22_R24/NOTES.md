# Phase-1 evidence: R04, R06, R11, R12, R22, R24 (read-only audit, 2026-09-28)

No source files were edited. No LLM/API calls; no project scripts run. All scripts in this folder are read-only and stdlib-only.

## Inputs (sha256)
| file | sha256 |
|---|---|
| working/src/main.tex | 31db54c4b2771d34e1b3b59168fcdebea9b3b5e8198f9268f21298a61fc3fec4 |
| working/src/generated_stats.tex | e4e369b7b7c3e55c4c541fc552f175018ea656c67193ebcf1dfb183a93756b73 |
| working/src/generated_obscure_stats.tex | a836b442a9238e898c2b8a60b57c30b5e09f9819af190a3df650a21f29ea6d05 |
| tables/table_temporal_leakage_probe.tex | a0d8b8e31c46a2008239bffaaa1f9a5dc94fbc2ca9ac3ecb3f7b80816df612f5 |
| tables/table_obscure_overruled_eval.tex | ae24ad04736a0809bce233093ef42db25aab83fe6101f5b00357e886e68d4af6 |
| B1_provenance_xelatex_conference.pdf | 31a70e5b8fb933fc8afed0767f6a793cbac888ab8942610b017914eee1f95cac (text: rendered.txt) |
| scratch/canonical_v2/terra_canonical_v2_eval.json | 95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507 |
| dataset_20k_cap/terra_eeg_index_20k.json | 7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad |
| terra_350_benchmark.json | 8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3 |
| scratch/temporal_leakage_statistical_summary.json | 36186dc0a89ae744b71f90c2161e651c82b3109755e49924196b03b3b9c3c831 |
| scratch/obscure_overruled_summary.json | ad03589cd49b8af255125de6ec4a4aec5afc7226a6a2987243ee6c0546eca07c (matches header of generated_obscure_stats.tex) |
| scripts/run_x1_fdr_legacy.py | 2ed57d2a1edf30790531b954393b4500b0d56bedd583c2ca7d09bfdafa07cfad |
| ask_terra.py (post-run, indicative only) | 0cca5cf440a1299853c37899647465b5f1f843803898e630d8d5402a3d9fffbb |

Scripts -> outputs: r04_trace_templates.py -> r04_output.txt; r04_eeg_traces.py -> r04b_output.txt; (inline) -> r04c_backup_output.txt; r04d_context_prefix.py -> r04d_output.txt; r06_judge_identity.py -> r06_output.txt; r06b_raw_scores.py -> r06b_output.txt; r12_benchmark_templates.py -> r12_output.txt; r12b_benchmark_detail.py -> r12b_output.txt; r11_r22_recompute.py -> r11_r22_output.txt; r24_ceiling.py -> r24_output.txt.

---
## R04 - Procedural templates vs case-specific reasoning — verdict OVERCLAIM + MISMATCH, severity HIGH
Manuscript: main.tex 170-187 (esp. 172 "Curated Landmark Prototypes (N=34)... five-point doctrinal schema: (1) core constitutional question ... (3) central legal holding ..."; 173 "procedural function ... parameterized ... by ... legal subject taxonomy (category) ... five-step analytical workflow"; 187 "100.00% population-weighted factual consistency"); 807 ("34 landmark decisions ... received curated procedural reasoning traces"). Rendered: rendered.txt ~300-345, 1623.

Evidence:
- EEG census (20,000 nodes): after masking title/year/category phrase, exactly **1 distinct trace text** (r04b). 0 nodes carry a non-template trace, including Brown v. Board, Plessy, Swann (all show the same 5 generic steps). Same in pre-Issue-6 backup (1 template, category phrase empty; r04c).
- Canonical contexts: 2,982 trace blocks across 969 rows (1,347 distinct cases) — 2,982/2,982 are (possibly truncated) copies of the single template (r04d).
- The only case-varying tokens are title, year, and a category phrase. The category phrase disagrees with the node's own `category` in **18,247/20,000 (91.2%)** nodes; 19,298 traces say "Civil Rights Equal Protection" although only 1,153 nodes are in that category (e.g., Plessy node category = general_constitutional_statutory; Almonester v. Kenton = admin_law but trace says Civil Rights).
- No trace contains an issue, procedural history, legal test or holding; "Step 5: Pronounce holding" is an instruction, not a holding.
- `docs/REASONING_TRACE_SPECIFICATION.md` (cited at 187) is not present in the staged tree; no `build_structured_trace` source was found.
- The 34 "curated" LLM traces are not present in the audited 20k index (TraceProceduralCount = 20,000 = 100%).

Proposed correction (scope, keep all facts): Describe SLRTs as "a fixed five-step procedural scaffold (one template shared by all 20,000 nodes) instantiated with case title, year and a domain phrase; it contains no case-specific issue, history, test or holding." State that the domain phrase does not match the node's primary category for 18,247/20,000 nodes (19,298 read "Civil Rights Equal Protection") [or fix the index and re-report]. Retain the 34 curated-prototype history but state they were used in early development and are not in the evaluated 20k index. Rescope the 187 "100% factual consistency" to "no factual claims beyond title/year exist to be inconsistent" and flag the category-phrase mismatch. Reword 807 "received curated traces" -> "received curated traces during early development (not present in the evaluated index)". Mark REASONING_TRACE_SPECIFICATION.md as not in the release until added.

## R06 - Judge identity / protocol — verdict MISMATCH, severity HIGH
Manuscript: 399 "Faithfulness ... using databricks-meta-llama-3-3-70b-instruct ... 'skeptical critic' persona. The judge model is explicitly decoupled from the inference models" (rendered.txt 751-755); 410 and 1051 "automated critic"/"adversarial critic persona"; 418-420 dual judges Qwen3-Next-80B (J1) + GPT-OSS-120B (J2) for all five pipelines; 492 and 1070 same; 100 "two non-Llama judges"; 393 "Amendments K, L, and M (judge JSON parse clamping, refusal string harmonization, fast-path ground-truth floor)"; 429-432 & 1075-1076 "not re-executed under v2 ... (pilot, leakage probe, CaseFacts, CLERC) ... derive from earlier single-judge evaluation".

Evidence (r06, r06b):
- Canonical 1,750 rows: `faithfulness == mean(faithfulness_qwen, faithfulness_gpt)` in **1750/1750** rows. Per-judge values lie in {0, .25, .5, .75, 1} = (Likert-1)/4; mean gives 9 levels.
- No Llama marker in any `raw_judge_scores`. `raw_judge_scores.raw_faithfulness` equals `faithfulness_likert` in all rows but maps to neither judge in 335 rows (derived/rounded field, not a raw judge score). `faithfulness == (likert-1)/4` only in 1,398/1,750.
- `_source_run`: 4 baselines = `sept6_baseline_rejudged`; TERRA = `issue6_deployed`.
- Line 399 names the generator/NLI model as judge and calls it "decoupled from the inference models" — contradicted by 418-420, 1070 and by the data. Llama is used only as generator, NLI grader, Category-D verifier (1070) and the earlier single-judge (rendered 993: "0.818 under the earlier single Llama judge").
- Clamping (scripts/run_x1_fdr_legacy.py 230-273): Category D score set to 0.00 if verified fatal error, floored at 0.75 if safety-rejected or verified refutation (AmendmentMFloorScore = 0.750). This is a Cat-D sensitivity-run rule, not "judge JSON parse clamping" as 393 describes K; K/L/M are applied together.
- Internal inconsistency: table_casefacts_eval.tex / table_clerc_eval.tex captions and main.tex 819/869 say "independent non-LLaMA dual judges (qwen3-next, gpt-oss)", and 761 says leakage probe was dual-judged by the same pair, while 429-432 and 1075-1076 say these blocks are earlier single-judge and not comparable. The provenance table (rendered 848-858) gives dates for leakage/CaseFacts/CLERC (17-18 Sept, file mtime) while the text says "date not recorded".

Proposed correction: 399 -> "Faithfulness (0-1): mean of two independent judges, Qwen3-Next-80B (J1) and GPT-OSS-120B (J2), each scoring a 5-point Likert rubric mapped to (L-1)/4; neither judge is the Llama-3.3-70B generator/NLI model." Replace "critic persona" (410, 1051) with "dual-judge scores". 393: describe K/L/M as the Category-D sensitivity rule actually coded (fatal -> 0.00; refusal/verified refutation -> floor 0.75), reported only in the raw-vs-clamped sensitivity table. Reconcile 429-432/1075-1076 with 761/819/869 and table captions: state per block which judges were used (or say "judge protocol not recorded") and use one date convention (file mtime vs "not recorded"). Note that `faithfulness_likert` is derived, not a raw score.

## R11 - Obscure/temporal inferential qualifications — verdict CONFIRMED-OK (numbers) with MISMATCH (caption) + minor OVERCLAIM, severity MED
Manuscript: 792-797; table_obscure_overruled_eval.tex; generated_obscure_stats.tex.
Evidence (r11_r22_output.txt): all 10 exact McNemar p-values reproduce (e.g., primary b=5,c=3 p=0.726562; Full vs Unlabeled 11/0 p=0.000977; J1 10/3 p=0.0923). The cross-suite risk differences, Newcombe CIs and Fisher p reproduce (Direct 2.46e-9; Full 0.541). N=30, famous N=19, 120 completions, κ=0.5746 consistent. Main text correctly labels the secondary tests descriptive and the gate CLOSED.
Issues:
- Table caption (line 3; rendered 1569) "zero unverified quotes" contradicts macros ObscQwenUnverifiedQuotes=16, ObscGptOssUnverifiedQuotes=26 (and main text 797). MISMATCH.
- Panel B labels "Robust Non-Significance" for subsets of N=28/25/12 with 5-6 discordant pairs: overclaim (absence of power, not robustness).
- Rounding: Direct RD printed +79.0% while components print 78.9% and 0.0% (78.95%); Flat Newcombe upper 55.3 recomputed vs 55.2 printed. LOW.
- Secondary exact p "< 0.001" for 11/0 (0.000977) is correct but near the boundary; give the exact value.
Proposed: caption -> "unverified evidence quotes: 16 (J1) and 26 (J2), labels retained"; Panel B conclusion -> "Not significant (few discordant pairs; underpowered)"; print RD as +78.9% (or show 3-sig components); report exact p=0.00098 / 0.00024.

## R12 - Taxonomy / benchmark curation and independence — verdict OVERCLAIM + MISMATCH + UNSOURCED, severity MED-HIGH
Manuscript: 280-284 (taxonomy; "without circularity or manual inflation", "independent automated evaluators"), 370-373 ("researcher-constructed ground-truth reference answers"), 380 ("constructed by the research team"), 807-809, 1084.
Evidence (r12, r12b; benchmark sha256 matches 8144fa81...):
- Category A: 3 query templates (34 "In what year was...", 33 "In which volume...", 33 "What is the official United..."); references templated from CAP metadata (e.g., "...was decided on 1914-04-13 (1914)").
- Category B: 100/100 queries use one template ("Trace the doctrinal evolution of <domain> from X (y) through Y (y), detailing..."); references templated ("...established the baseline standard. The legal framework subsequently transitioned through intermediate precedent..."); `gold_citation_path` equals `target_nodes`; `path_coherence_filter` = strict_same_category (80) / domain_coherent_tag_relaxed (20) — i.e., chains appear to be graph-derived path selections from the EEG that TERRA traverses. No generator script is present in the staged repo (grep for template strings in .py/.md: no hits) -> construction method UNSOURCED.
- Category D: 29 templated ground-truth prefixes; 37 "Did the Supreme Court in...", 19 "Under the binding doctrine of ... is it currently constitutional to enforce...".
- 809 says "63 paths require 3 hops, 32 require 4 hops, and 5 require 5 hops"; data show 63/32/5 paths of 3/4/5 **nodes** (= 2/3/4 hops), consistent with line 371. MISMATCH (off-by-one). "Traversal depth reflects natural citation diameter rather than artificial tuning" conflicts with 371 (chains constrained to 3-5 nodes by design); "invariant relative performance across hop lengths" has no cited table here -> UNSOURCED.
- 808: "19 subset of 56 CRS overrulings ... confirming curation ... rather than benchmark-fitted selections" — subset membership does not show how the 19 were chosen. OVERCLAIM.
- 284/1084: taxonomy judges are automated and Judge B falls back to Qwen (same family as a faithfulness judge); the paper discloses no human validation (OK) but "independent"/"without circularity" is stronger than shown.
Proposed: Describe A and B (and D references) as "template-generated from CAP metadata and EEG citation paths (A: 3 templates; B: 1 template, graph-derived 3-5-node paths filtered for category coherence), then checked by the authors"; add that B gold paths come from the same graph TERRA traverses (a circularity risk that favours graph traversal). Fix 809 to "63 three-node (2-hop), 32 four-node (3-hop), 5 five-node (4-hop) paths", remove "rather than artificial tuning" or say "path lengths were constrained to 3-5 nodes by design"; cite the per-hop table or drop "invariant". 808 -> "are drawn from the CRS list (19 of 56); the selection rule for the 19 is described in ...". Replace "independent" in 284 by "automated, model-distinct".

## R22 - Temporal-probe overstatement — verdict OVERCLAIM + UNSOURCED + MISMATCH(provenance), severity HIGH
Manuscript: 761 ("κ ≈ 0.70 benchmark-wide"; "Forensic diagnosis confirms ... artifact of the Kappa Paradox"), 775 ("significantly outperforms ... effectively doubles ... apparent raw SPTLR parity ... is solely an artifact of Flat RAG's refusal volume masking"), 780-782 ("Directional Stability formally certified ... TERRA unconditionally generates more clean historical answers ... reaching nominal significance (p = 0.0133)"); table_temporal_leakage_probe.tex.
Evidence:
- κ ≈ 0.70: no source anywhere in the staged tree (only manuscript copies and ledgers). UNSOURCED.
- H2 complete cases b=2, c=4 (TERRA worse, two-sided p=0.6875); H4 cc b=1,c=1 (tie). Bounded p for H2 is [0.0133, 0.1662] — only the most favourable assignment is <0.05. The H2-H4 p-values are **one-sided** (reproduced exactly one-sided; two-sided ranges are [0.0266,0.3323], [0.0490,0.8145], [0.0225,0.7905]) while the table header says "Exact McNemar p-value" and only H1 is labelled one-sided; HLCR p=2.1e-5 is two-sided. No multiplicity correction is applied.
- scratch/temporal_leakage_statistical_summary.json (only per-probe data file present) disagrees with the manuscript macros: QWK 0.3672 vs 0.260; concordance 69.4% vs 68.6%; Flat HLCR 36% vs 38%; TERRA-gated refusal (A) 6% vs 8%; H1 b=0,c=8 vs c=3 (cc); its secondary family uses Holm: H2 raw p 0.166 / Holm 0.498, H3 0.090/0.359, H4 0.073/0.365, all "significant: false". Temporal macros appear hand-entered (0.260 is listed in src/scripts/allowed_literals.txt). No per-row judge file for the probe is present -> the reported numbers cannot be re-derived.
- "solely an artifact": HLCR is a different metric and cannot establish sole cause; 3 cc Level-2 TERRA leaks remain (c=3).
- "Forensic diagnosis confirms" Kappa Paradox: 289/315 = 91.7% base rate is arithmetically consistent, but P_e ≈ 60% has no computation shown.
Proposed: 761 delete or source "κ ≈ 0.70" (if kept, cite the file/metric; otherwise "lower than the agreement observed elsewhere in this paper (e.g., obscure-suite κ = 0.5746)"); "confirms" -> "is consistent with". 775 -> "... HLCR is higher for TERRA (76% vs 38%; b=20, c=1; two-sided exact p = 2.1e-5). Flat RAG's 46% refusal rate plausibly contributes to its lower SPTLR; the probe cannot establish that it is the sole cause (TERRA still has c=3 complete-case Level-2 leaks)." 780 -> "Under all missing-data assignments of the consensus rule the bounds satisfy c_max < b_min (directional stability of the bounds); complete cases alone favour Direct LLM (b=2, c=4). One-sided exact p ranges from 0.0133 to 0.1662, so significance depends on the missing-data assignment; no multiplicity correction applied." Label H2-H4 p-values as one-sided in the table. Reconcile or explain the scratch summary (different run/version) and deposit the per-response judgments.

## R24 - Limitation 3 is a remedy, not a limitation — verdict OVERCLAIM + UNSOURCED, severity LOW-MED
Quote (main.tex 1053; rendered 2405-2409): "Evaluation Rubric Resolution and Likert Normalization: Coarse evaluation scales (e.g., discrete binary pass/fail or {0.0, 0.8, 1.0} heuristics) induce artificial ceiling compression, clustering over 75% of responses at 1.0. Implementing a 5-point Likert scale normalized to [0, 1] effectively resolves this compression, exposing genuine variances in doctrinal nuance."
Evidence (r24_output.txt): the ">75% at 1.0" figure has no source among staged files; legacy terra_baselines_eval_raw.json (already 5-level) has 62.5% at 1.0; canonical v2 dual-judge still has **50.3% (880/1750)** at exactly 1.0 (9 levels). So compression is reduced, not resolved.
Proposed reframe (all facts kept): "Score ceiling and rubric granularity. Earlier coarse scales (binary or {0.0, 0.8, 1.0}) placed most responses at 1.0 [>75% — cite source or mark as from an unarchived earlier run]. The 5-point Likert rubric, averaged over two judges, reduces this but does not remove it: 50.3% (880/1,750) of canonical scores are still 1.0, and refusals can receive full marks (Limitation 2). The ceiling limits discrimination among high-quality answers; finer rubrics or pairwise preference judgments are future work."
