# Phase 1 evidence — R03 / R23 (claims), R18 (pilot ablation), R21 (bibliography)

Read-only audit, 2026-09-28. No source files edited, no project scripts run that write files, no LLM/API calls. Web search/fetch used only for the bibliography.

## Inputs (sha256)
| file | sha256 |
|---|---|
| working/src/main.tex | 31db54c4b2771d34e1b3b59168fcdebea9b3b5e8198f9268f21298a61fc3fec4 |
| working/src/ref.bib | cbde319532889d5490c1d2ab4e6d2f5477dde1424d192642af62d114e6356a8a |
| working/src/generated_stats.tex | e4e369b7b7c3e55c4c541fc552f175018ea656c67193ebcf1dfb183a93756b73 |
| working/src/generated_obscure_stats.tex | a836b442a9238e898c2b8a60b57c30b5e09f9819af190a3df650a21f29ea6d05 |
| ledgers/claim_language_scan.csv | e9d8b344fd21bb4a98b86123cdb9ad9e0e9b48c1c4fa61f535750324ea9ef8f8 |
| scratch/canonical_v2/terra_canonical_v2_eval.json | 95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507 (matches generated_stats header) |
| builds/phase0/B1.../B1_provenance_xelatex_conference.pdf | 31a70e5b8fb933fc8afed0767f6a793cbac888ab8942610b017914eee1f95cac |
| terra_true_ablation_pilot_report.md (staged from F:\TERRA -Copy) | 6dfed56d1a40591338589a8c34b49470049260a453ea0e992eee2cfaacefb575 |
| eval_terra_ablation.py (staged from F:\TERRA -Copy) | d28d0aaf4a7fb3c4ef32cd1ae52dd818f128468195432fa43e7954e3596af835 |
| scripts/generate_stats_v2.py | f393347b5ac82e181e63e2484a5e365b6c5f8c3d5a88c4398dccb71ae6bf75e5 |

The 750 MB `terra_true_ablation_pilot_raw.json` was NOT staged (per instructions); its sha256 in generated_stats.tex header is 67aef98f…dacf15 (unverified here).

## Outputs
- `claim_matrix.csv` — 40 claims: 1 SUPPORTED, 18 SUPPORTED-WITH-QUALIFIER-NEEDED, 16 OVERCLAIM, 5 UNSUPPORTED.
- `bib_check.csv` — 27 entries: 2 HIGH, 5 MEDIUM, 20 LOW. No entry is fabricated (all 27 exist).

## New evidence from canonical eval (read-only Python over terra_canonical_v2_eval.json, 5_Full_TERRA rows)
- Cat C (75): 74/75 have empty `context_full`; all 75 `safety_rejected`; `grading_ms` > 100 ms on only 1/75 (median 0.01 ms); `generation_ms` > 100 ms on 0/75. So deployed out-of-domain refusals were empty-retrieval short-circuits, not semantic NLI. This contradicts line 1041/1043 ("delivered almost entirely by the downstream NLI Smart Grader", "indispensable primary safety firewall") and the operation-accounting macros (40 pre-filter halts, 12 NLI-fail, 22 NLI-pass→generator; TerraCatC*), which apparently describe a different run. Escalate to R13.
- Cat A (100): route_taken EASY on 100/100 but `retrieval_ms` > 0 on 100/100 (median ≈ 295 ms) and `grading_ms` > 0 on 100/100 (median ≈ 2.0 s). Contradicts table caption line 667 ("fast-path executes router inference + generator only, no retrieval") and line 999 ("Category A fast path bypasses retrieval entirely").
- Internal inconsistencies spotted: fast/hard medians 5.83/17.94 s (TerraFastPathMedianSeconds/TerraHardPathMedianSeconds, used lines 115,146,993) vs 5.46/14.07 s (TerraFastRouteMedianS/HardRouteMedianS, line 703); Limitation 6 "fatal errors from 10/75 to 2/75 (80%)" vs macro DirectLLMCatDFatalErrors = 4/75 (FINDINGS R08).

## R18 — pilot ablation (main.tex 233, 368, 502, 522-526, 636, 1041; Table tab:ablation)
Design (eval_terra_ablation.py, generated_stats.tex comments): 35 unique queries = 10 Cat A, 10 Cat B, 10 Cat C, 5 Cat D; 4 configs × 5 repeated runs at T=0 → 175 executions per config, 700 total. Per config per category: A 10 q/50 runs, B 10 q/50 runs, C 10 q/50 runs, D 5 q/25 runs. Repeated runs at T=0 are not independent samples; effective n for Cat D = 5 queries.

Metric definitions (generate_stats_v2.py 646-669):
- "Cat D Safety" = fraction of runs with `safety_rejected` or relevance == 0 → it is a **refusal rate**, not the v2 four-class safe-handling rate (refutations are not counted as safe). Ablation 2 = 0% therefore means "no refusals", not "complied with deceptive premise". The sentence "Without the autonomous entailment audit, the generator credulously complies with deceptive queries" (525) is not supported by this metric.
- "Cat A False Ref." = queries (of 10) with any run refused → Ab3 2/10 queries; staged pilot report shows 10/50 runs.
- Judge: legacy single judge via eval_terra.judge_answer; Table run_provenance: "date not recorded"; not comparable with v2 dual-judge scores (Cat B faithfulness 0.815 pilot vs 0.254 canonical).
- Staged `terra_true_ablation_pilot_report.md` (mtime ≈ 2026-09-05, predates raw json mtime) shows older values (Full Cat B 0.875, Ab1 0.715, Ab2 0.84, Ab3 0.86) than paper macros (0.815/0.675/0.780/0.840) — consistent with raw file being re-judged after Amendment G; paper uses the raw file. It also reports **Cat C safety 40% (Full), 40% (Ab1), 0% (Ab2), 80% (Ab3)** in the pilot — not reported in the paper; Full TERRA refused only 4/10-equivalent of Cat C runs in the pilot versus 100% in the canonical run. Worth disclosing or explaining.
- No variance, CI or test reported for any ablation contrast; Cat B deltas (0.815→0.675) rest on 10 queries.

Flagged causal wording and proposed replacements:
| line | current | proposed |
|---|---|---|
| 233 | "confirming that the gate is the operative safety mechanism" | "consistent with the gate producing the refusals in this 5-query pilot; the gate's accuracy was not validated" |
| 522 | "The ablation results confirm three fundamental architectural insights" | "In this 35-query pilot (5 Cat D, 10 Cat A/B queries; 5 repeated runs), the ablations suggest three patterns" |
| 524 | "Architectural Necessity of EEG Graph Traversal" | "Graph traversal and Category B faithfulness: removing traversal lowered pilot Cat B faithfulness from 0.815 to 0.675 (10 queries, legacy single judge)" |
| 525 | "Critical Function of the NLI Smart Grader … generator credulously complies" | "Grader and refusals: without the grader, none of 25 adversarial runs (5 queries) was refused, vs 25/25 with it. Refutations were not scored, so this measures refusal, not safety." |
| 526 | "The router provides critical operational triage" | "Forcing the hard path raised Cat A median latency from 1.38 to 6.75 s and produced refusals on 2/10 Cat A queries in the pilot" |
| 636 | "establishes the system-level operational necessity of query routing" | "indicates a latency and false-refusal cost of disabling routing in the pilot" |
| 1041 | "caused an immediate collapse of adversarial safety to 0.0%, confirming NLI as the true empirical safeguard" | see C33/C34 in claim_matrix; also reconcile with canonical Cat C evidence above |

## R21 — bibliography summary
- All 27 entries exist (no hallucinated references). 11 @misc/arXiv: 5 now have venues — zhang2025 (EACL 2026), liu2026 (Findings ACL 2026), li2025 CoT-RAG (Findings EMNLP 2025), liang2025 (Findings IJCNLP-AACL 2025), bernal2024 HippoRAG (NeurIPS 2024). Others (zhu2025, lin2025, roig2026, yalavarthi2026, hashmi2026, edge2024) remain arXiv-only in searches.
- HIGH (corrupted metadata of real papers): `sun2024thinkongraph` (wrong title and 4 wrong co-authors), `asai2024selfrag` (co-authors are those of a different work).
- MEDIUM: `hou2024clerc` (wrong pages 4930-4958 → 7913-7928; title missing "U.S."; text overstates what CLERC shows), `hoenig2001abuse` (wrong subtitle), `yalavarthi2026` (in-text misrepresentation: "mathematically proving", 5.0% is religion subset, 88.3% is ARC-Challenge), `roig2026` (cited as LLM-as-judge framework; RIKER argues for judge-free evaluation), `chen2026legalgraphrag` (tripartite ontology/fact/rule + civil/criminal description not confirmed in abstract).
- Unsupported synthesis sentence (135): "These benchmarks confirm that standard lexical or dense retrievers frequently retrieve irrelevant or superseded authority…" — neither CaseHOLD nor CLERC shows this.
- Conclusion (1098) cites edge2024/sun2024/zheng2023 for TERRA's own stability result — irrelevant citations.
- Access note: arxiv.org/abs/2604.05096 returned empty PDF text and arxiv.org/abs/2604.14222 was refused by the proxy (HTTP 429); both were verified through ACL Anthology / search results / pith.science instead.

### Missing related-work areas (suggestions only; each verified to exist)
- Legal RAG benchmark: LegalBench-RAG (Pipitone & Alami, arXiv 2408.10343) — https://arxiv.org/abs/2408.10343
- Legal RAG hallucination in commercial tools: Magesh et al., "Hallucination-Free? …", J. Empirical Legal Studies 22(2):216-242, 2025 — https://onlinelibrary.wiley.com/doi/full/10.1111/jels.12413
- RAG faithfulness evaluation: RAGAS (Es et al., EACL 2024 demo) — https://aclanthology.org/2024.eacl-demo.16/
- Temporal QA: TimeQA, "A Dataset for Answering Time-Sensitive Questions" (Chen et al., NeurIPS 2021 D&B, arXiv 2108.06314) — https://arxiv.org/abs/2108.06314
- Temporal graph RAG: "RAG Meets Temporal Graphs: Time-Sensitive Modeling and Retrieval for Evolving Knowledge" (arXiv 2510.13590) — https://arxiv.org/abs/2510.13590 ; T-GRAG (arXiv 2508.01680) — https://arxiv.org/abs/2508.01680
- Citation-graph legal retrieval (e.g. COLIEE, citation-network precedent retrieval): area gap noted; no specific citation verified in this pass — do not add without checking.
