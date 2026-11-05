# Phase 2 report: number and claim provenance, and the contribution gate

- **Author:** Claude (implementer). Codex audits.
- **Date:** 2026-09-29.
- **Authorization:** `phase2/20260929T0200Z-user-authorizes-phase2.md`. The user wrote: "PERFORM EXACTLY HOW CODEX MENTIONED TO EXECUTE PHASE 2 HERE". Codex-0018 said to begin with number and claim provenance and not to assume every original manuscript value is verified.
- **Scope honoured:**
  - Nothing was edited: manuscript, macros, data, code and graphs are all unchanged.
  - The corrected graph is not connected to any pipeline.
  - No experiment was run and no LLM was called.
  - Phase 3 has not started.
  - The two generator replays wrote only to sandbox scratch paths.
  - Historical results stay attributed to the original graph `7aa6db46`.

## 1. Summary

**2A: number provenance.** Every one of the **1,236 used macros** now has a zone, block, source family, emitter mode and verification status.

- 480 are reproduced here from primary data or by a generator replay; 4 more reproduce only under a stated alternative method.
- 309 are traced to a named upstream artefact but not recomputed, and 70 more are traced only weakly.
- 18 are arithmetically consistent with other printed values.
- 14 differ at the last digit or by less than 0.2%.
- **58 conflict** with recomputation or Phase 1 evidence.
- 56 are blocked (R22).
- 223 remain unverified.

The 1,208 result-like numeric literals hard-coded in the manuscript sources are inventoried separately. As literals, none is verified; 815 share a value with a verified macro, which makes them candidate links only.

**New finding (proposed R35).** The four Category D explicit-refusal McNemar p-values printed in the paper are stale hard-coded literals from before Issue 6. From the v2 paired table:

| Comparison | Printed p | v2 p |
|---|---|---|
| TERRA vs Direct LLM | 4.55×10⁻¹³ | 7.1×10⁻¹⁵ |
| TERRA vs Flat RAG | 0.5847 | 0.110 |
| TERRA vs GraphRAG | 0.1214 | 0.011 |
| TERRA vs HippoRAG | 0.1849 | 0.016 |

The printed sentence even pairs "b=48, c=0" with p = 4.55×10⁻¹³, which is the p-value for b = 42.

**2B: claim ledger.** The ledger has 60 claims: the 40 from the Phase 1 claim matrix plus 20 surfaced by the register items and the 2A pass. Each is classified as observation, inference, hypothesis or intention, with its scope, counter-evidence and permissible wording.

| Proposed status | Claims |
|---|---|
| KEEP | 1 |
| QUALIFY | 22 |
| NARROW | 20 |
| CORRECT-VALUE | 10 |
| DELETE-OR-CITE | 5 |
| BLOCKED | 2 |

**2C: contribution gate.** §4 proposes three research questions and four narrowed contributions, and separates the five construct families. It gives a bounded novelty assessment, which is not exhaustive, and options for the R05, R06 and R12 gaps. The user decides.

## 2. Phase 2A: number provenance

### 2.1 Method

Scripts are in `phase2/evidence/`. All are read-only and run with `python -X utf8`.

| Script | What it does | Output |
|---|---|---|
| `p2a_macro_emitters.py` | Finds the scripts that emit each macro | `p2a_macro_emitters.csv` |
| `p2a_regen_compare.py` | Compares a sandbox replay of `generate_stats_v2.py` (writing to /tmp) with the frozen HEAD block | 324/324 non-ablation HEAD macros match |
| `p2a_downstream_checks.py` | Recomputes router, net and category latency, throttling, refusal counts, Hodges–Lehmann, Issue 17 rubric and McNemar, Issue 23 graph and preflight values, Issue 24 parameters and HEAD literals from canonical v2 (`95e775e2`), the active and historical graphs, the rubric summary and `ask_terra.py` | `p2a_downstream_checks.csv` (171 rows) |
| `p2a_budget_checks.py` | Recomputes Table XXI latency, stage means and generator calls from v2 telemetry | 75 cells |
| `p2a_obscure_checks.py` | Compares the obscure-suite macros with `obscure_overruled_summary.json` (sha matches the header `ad03589c`); checks cross-suite rows for arithmetic consistency only, because the famous-D1 and cross-suite summaries are absent | |
| `p2a_corpus_replay.py` | Replays `Paper/scripts/generate_corpus_stats.py --out <scratch>` | 29/29 match |
| `p2a_build_ledger.py` | Assembles `ledgers/number_provenance_ledger.csv`, using the outputs above and the Phase 1 R09/R10 recomputations | Ledger |
| `p2a_literal_scan.py` | Inventories literals in `main.tex`, the tables and the figures | `ledgers/manuscript_literal_ledger.csv` |
| `p2a_table_literal_checks.py` | Checks two literal-only tables | 29/29 cells consistent |

**How statuses are assigned.**

- *TRACED* means the frozen number occurs in the block's named source artefact. It locates provenance but does not recompute the value.
- *TRACED_WEAK* flags two kinds of match that could be coincidental: matches made only on round or small values, and matches within the multi-source "Z3 added" block.
- For the citation and retrieval blocks, a value found only in the legacy recomputation is marked CONFLICT, unless the macro is explicitly named `…Legacy`.

**Inputs staged for this pass** (read-only, from `F:\TERRA -Copy\data`):
- the Issue 19–22 and Issue 24–25 audit and preflight JSONs;
- `landmark_scotus_catalog.json`.

### 2.2 Results by zone

| Zone (used macros) | Reproduced | Traced | Consistent | Minor | Conflict | Blocked | Unverified | Other |
|---|---|---|---|---|---|---|---|---|
| HEAD, v2 generator (245) | 222 | – | 1 | – | – | – | 22 | – |
| DOWNSTREAM legacy (838) | 240 (+4 method) | 215 (+70 weak) | – | 11 | 56 | 56 | 186 | – |
| Obscure suite (133) | – | 94 | 17 | 3 | – | – | 15 | 4 layout |
| Corpus (20) | 18 | – | – | – | 2 | – | – | – |

**HEAD unverified.** Nineteen are ablation macros: the 752 MB pilot raw file cannot be transferred, so the replay used a stub. Three are pilot counts echoed as literals. Four other echoed literals (`numTotalEvals`, `numUniqueQueries`, `numComparativePipelines`, `CatBTotalPairs`) are now verified against the canonical file.

**Where the unverified downstream macros sit:**

| Block | Unverified macros | Reason |
|---|---|---|
| Issue 10 | 71 | Baseline ops/cost cells and the τ-sweep TPR/FPR calibration grid; no source artefact located |
| Issue 19 temporal stability | 26 | Generator output not available |
| Z3 additions | 23 | |
| Issue 14 trace audit | 21 | Linked to R04 |
| CLERC | 9 | Hard-coded fabrication and split literals (R09-11) |
| CaseFacts footprint and seed densities | 8 | |
| Deprecated power | 8 | |
| Issue 22 | 8 | |
| Retrieval ratios/deltas | 8 | |
| Remainder | 4 | Spread across small blocks |

**Issue 26.** The 69 macros match the committed generator output `scratch/generated_issue26_macros.tex`. The 197 MB grid file was not re-read, so these count as generator-consistent, not recomputed.

### 2.3 Conflicts (58 macros)

| Group | Macros | Evidence | R-id |
|---|---|---|---|
| Table XXI (Issue 10): TERRA stage means, generator calls, ops and cost | 45 | 58 of 75 checked cells reproduce from v2 (all 27 latency cells, the baseline stage means and TERRA routing/generation means). The following differ: decoupled retrieval and NLI (Cat A 0.0/0.0 vs v2 353.4/4,562.8 ms); generator calls (258 = 73.7% vs v2 211 = 60.3%; Cat C 23 vs 0); ops and cost (pre-v2 accounting); $0.014 per query is wrong under both runs | R13, R32, R19 |
| Theoretical operations 1,522 / 4.35 | 2 | Theoretical model, not measured (v2: 3.60 per query) | R13 |
| Refusal McNemar p-values | 4 | See §1. The safe-handling p-values reproduce (0.5000 / 0.0625 / 0.0312 / 0.2500). A Holm correction over the 4 refusal tests gives 2.8×10⁻¹⁴ / 0.110 / 0.034 / 0.034 (computed here, not printed anywhere) | **R35 (proposed)**, R29, R08 |
| Table III diameter 15, ASPL 4.713 | 2 | 10k-graph literals; the 20k graph gives 13 / 4.305 | R28 |
| Retrieval CI [47.8, 100]; endpoints-anchored 100% (4-node and all) | 3 | 5/5 legacy CI (v2 1/5 → [0.51, 71.64]); legacy 20/20 | R10 |
| Broken-link breakdown 3 not_provided / 1 unindexed | 2 | Matches neither run | R10 |

The Z3 macro `TerraEntityCitePrecisionLegacy` (91.95%) matches the legacy run and is labelled Legacy, so it is **not** a conflict.

### 2.4 Minor mismatches and method variants (reported, not corrected)

**Net latency.** P25 and mean±SD reproduce exactly. The medians, P75 and P95 differ by 1–8 ms (<0.2%) from numpy linear percentiles; examples are fast median 5,457 vs 5,464.955 and hard P95 44,402 vs 44,397.5. The frozen rule could not be recovered.

**SD convention.** The category latency rows use the sample SD (ddof = 1). The route rows use the population SD (ddof = 0). The inconsistency is reported rather than chosen between.

**Router P90.** The frozen 2,043.8 equals numpy's "higher" rule; the linear rule gives 2,025.1.

**Issue 23:**
- GraphRAG undirected edges: 145,353 printed; the active graph gives 145,357 and the historical graph 145,354. Neither reproduces the printed value, and the adapter code is not in the repository copy. The HippoRAG non-zero count (290,706) follows from it.
- Active file size: 109.5 MB printed, while 109,574,119 bytes rounds to 109.6.
- `PromptTokenRatio` 17.3× and `ContextAsymmetryRatio` 18.8× are ceiling ratios (60,000 / 3,200). The observed mean context-length ratio of TERRA to Flat in canonical v2 is 5.9×.

**Obscure cross-suite.** Three rows differ by 0.1 pp from recomputation from the printed counts, for example RD +79.0 vs 78.9. The famous-D1 summary is absent.

**Epistemic refusals** (143 / 204 / 203 / 179). These have no emitter and no reproducing rule. The flagged-refusal counts (139 / 184 / 173 / 165) reproduce exactly.

### 2.5 Manuscript literals (R26)

The scan found 2,109 numeric tokens after excluding layout, colour, label, reference and cite arguments:

| Class | Tokens |
|---|---|
| RESULT_LIKE | 1,208 |
| STRUCTURAL | 793 |
| YEAR | 104 |
| CITATION | 4 |

Of the result-like literals, 815 equal the value of a verified macro, 94 equal the value of another macro, and 299 match no macro. The largest sources are `main.tex` (525) and `table_full_fdr_family.tex` (197; see Phase 1 R08). All result-like literals are **UNVERIFIED as literals**.

Two literal-only tables were checked directly against canonical v2:
- Refusal breakdown Panel A: 25/25 cells match `safety_rejected` counts.
- Router Panel B category rows: 4/4 match; for Category D, the EASY cell is a macro, and the 65 HARD matches.

## 3. Phase 2B: claim ledger

The ledger is `ledgers/claim_ledger.csv` and its builder is `evidence/p2b_build_claim_ledger.py`. It uses the columns of the plan's template: claim_id, assertion, evidence, class, scope, counterevidence, permissible_wording, source_line, final_location (TBD in Phase 4), and status. Traceability columns (origin, rids, phase1_verdict) are added.

| Class | Claims |
|---|---|
| Observation | 35 |
| Inference | 11 |
| Intention | 10 |
| Hypothesis | 4 |

**C41–C60 were added in Phase 2:**

| Claim | Topic |
|---|---|
| C41 | Stale refusal McNemar p-values |
| C42 | "Highest refusal rate", with the R29 counts |
| C43 | Single-run chronology (R34, open) |
| C44 | Holding coverage attributed to the later graph state (R33) |
| C45 | 56 OVERRULES edges with 3 mis-resolved (R30) |
| C46 | Table III topology (R28) |
| C47 | Unsourced epistemic-refusal counts |
| C48 | Temporal-probe claims (R22, blocked) |
| C49 | Trace scaffolds described as reasoning (R04) |
| C50 | Taxonomy independence (R12) |
| C51 | Baseline asymmetries (R05) |
| C52 | Judge identity (R06) |
| C53–C54 | CaseFacts and CLERC comparisons (R09) |
| C55–C57 | The "0.76× lift", link counts and retrieval construct (R10) |
| C58 | Table XXI (R13) |
| C59 | Latency percentile rule |
| C60 | Limitation 6 baseline (R08) |

Every status is a **proposal for Phase 3**. No text was changed.

## 4. Phase 2C: contribution gate (for the user's decision)

### 4.1 Separation of construct families

The paper currently merges the following five construct families. Each needs its own evidence and wording.

| Family | What the evidence supports | What it does not support |
|---|---|---|
| **Retrieval coverage** (Category B, 100 queries) | All-gold-node coverage: TERRA 66/100 vs HippoRAG 21, GraphRAG 9, Flat 1. Macro node recall 88.9% vs 68.5 / 35.7 / 26.8%. Reproduced (Phase 1 R10). | "Path" or "chain" recovery: no order or edge check is made. Robustness at 5 nodes: 1/5, CI [0.5, 71.6]. The advantage uses curated edges and a 60k-character budget that the baselines do not have (R05). |
| **Selective answering / safety** (Categories C and D; obscure suite) | Category C: 75/75 refusals, 74/75 following empty retrieval (R31). Category D: safe handling 73/75 vs Direct 71/75 (p = 0.50, not significant); explicit refusal 48/75, with rubric vs telemetry at 48 vs 46 (R29). Obscure suite: Full 19/30 vs Unlabeled 8/30; primary test (Unlabeled vs Flat) not significant (p = 0.727). | That the NLI gate is the primary firewall (C34). Any safety claim generalising beyond 75 traps. A refusal advantage over retrieval baselines as confirmatory (R35: unadjusted, secondary). Safety without curated OVERRULES labels. |
| **Generation / judge quality** (faithfulness) | Category B: TERRA above the three retrieval baselines (FDR-significant; the Flat bootstrap CI includes 0). **Direct LLM is significantly higher** (Δ −0.081, q = 0.0023). Overall faithfulness is similar to HippoRAG (CIs overlap). | Any overall quality win. Answer-only comparisons use different answered subsets. Judges include a same-family verifier (R06). |
| **Citation fidelity** | v2: 664 links, 660 resolvable, 4 broken. Citation recall (macro CR) is highest for TERRA (57.9%). | Citation F1: TERRA 16.0% is **below** Flat 21.2%. Entity precision is lowest for TERRA (74.3%). Legacy 1,042-link figures. |
| **Legal correctness** | No practitioner adjudication exists. CaseFacts and CLERC are judge-labelled; the CaseFacts gain comes entirely from the 8-item Overruled class; on CLERC, Direct LLM has the highest citation F1. | Any claim of legal correctness or legal reasoning; traces are template scaffolds (R04). |

### 4.2 Proposed research questions

- **RQ1 (retrieval).** On multi-hop precedent-evolution questions, does citation-graph traversal from retrieved seeds recover more of the gold precedent set than flat, community-graph or PPR retrieval under the same generator?
  - The answer is yes for node coverage.
  - Confounds: budget and curated edges.
- **RQ2 (selective answering).** Does gating generation on retrieved-evidence sufficiency change refusal and safe-handling behaviour on out-of-domain and false-premise queries, and at what cost in false refusals?
  - Out-of-domain refusal: 75/75.
  - False-premise refusal: 48/75, with safe handling similar to Direct LLM.
  - Cost: 16/100 false refusals on Category B and 2/100 on Category A.
  - The mechanism in the deployed run was mostly empty retrieval.
- **RQ3 (curated temporal annotations).** How much of the handling of obscure overruled precedents depends on explicit OVERRULES labels?
  - Full 19/30 vs Unlabeled 8/30 (a descriptive secondary contrast).
  - The primary preregistered test was not rejected.

The temporal-leakage probe stays a limitation or descriptive study (R22 blocked; H1 not supported). It is not a research question, unless the user decides otherwise.

### 4.3 Proposed contributions (narrowed, not dropped)

1. **Resource.** A citation graph of 20,000 authentic CAP SCOTUS opinions (1850–1980; 145,366 edges; 56 OVERRULES labels, 3 of them mis-resolved) with per-node holding fields.
   - Coverage figures belong to the inspected file (R33).
   - Traces are described as template scaffolds.
2. **System.** A binary-routed pipeline in which "hard" queries get citation-graph traversal and all answers pass an LLM-prompted evidence-sufficiency gate. It is described as a design, without "specialised NLI" or "three-way" claims.
3. **Evaluation.** A 350-query, four-category benchmark with five pipelines, dual-judge faithfulness, a four-class false-premise rubric, and an obscure-overruled suite with a preregistered primary test.
   - It reports the negative results together with the positive ones: Direct LLM wins Category B faithfulness; citation F1 is below Flat; H1 is not supported; the obscure primary test is not significant.
4. **Honest accounting.** Separation of retrieval coverage, selective answering, faithfulness, citation fidelity and legal correctness, with all limitations and adverse findings retained.

### 4.4 Novelty: a bounded, non-exhaustive assessment

This assessment rests on 6 targeted searches plus the Phase 1 check of all 27 references. It is not a systematic review.

**Query-complexity routing is prior art.** Adaptive-RAG (Jeong et al., NAACL 2024) trains a small LM classifier to route between no-retrieval, single-step and multi-step retrieval. TERRA's binary EASY/HARD router is therefore **not novel as a mechanism**. At most it is a domain application; Adaptive-RAG is not currently cited.

**Retrieval-quality gating is prior art.** CRAG (Yan et al., arXiv 2401.15884) scores retrieved-document quality and triggers corrective actions. Self-RAG (ICLR 2024; cited, with wrong metadata, R21) critiques retrieval with reflection tokens. An evidence-sufficiency gate before generation is **not novel as a mechanism**.

**Graph RAG baselines are cited and adapted:** GraphRAG (Edge et al.) and HippoRAG (NeurIPS 2024). Temporal graph RAG exists outside law: T-GRAG (arXiv 2508.01680) and "RAG Meets Temporal Graphs" (arXiv 2510.13590), both flagged in Phase 1 as missing. In law, SAT-Graph RAG (JURIX 2025) versions legal norms over time, and LegalGraphRAG (ACL 2026) is cited.

**Overruling awareness in LLMs is an active topic.** Zhang, Savelka and Ashley, "Do LLMs Truly Understand When a Precedent Is Overruled?" (JURIX 2025, arXiv 2510.20941), evaluate LLMs on 236 SCOTUS overruling case pairs and report temporal bias and shallow reasoning. It is directly relevant to RQ3 and is not cited. Magesh et al. (JELS 2025) document hallucinations in commercial legal RAG tools; this is also not cited.

**Defensible residual novelty** is a *combination and evaluation* claim, scoped as "to our knowledge, among the systems we compare". It covers:
- traversal over an authentic SCOTUS citation graph with explicit OVERRULES labels, evaluated jointly for retrieval coverage and selective answering;
- the obscure-overruled suite, which isolates the contribution of curated labels (RQ3).

A claim that no prior work combines routing, gating and temporal graphs is not supported, and neither is any claim that a single component is new.

### 4.5 Options for evidence gaps R05, R06 and R12 (the user decides; no experiment is authorized)

| Gap | Option A: new validation (needs separate Track B approval) | Option B: narrow and disclose (Phase 3, editorial) |
|---|---|---|
| **R05** baseline confounds (60k vs 3.2–5.5k-character budgets; curated edges only in TERRA; the GraphRAG edge count not reproduced) | Budget-matched and knowledge-matched baseline reruns | Present the comparisons as system-level; state the ceiling ratio (18.8×) and the observed ratio (5.9×); state the curated-edge asymmetry; drop "architecture" causal wording |
| **R06** judge identity and same-family verifier | An independent judge or a human agreement sample | Name the judge for each metric; report κ where it exists (obscure suite κ = 0.575); state the same-family limitation; do not call the verifier independent |
| **R12** taxonomy gold independence | Independent annotation | Describe it as an audited agreement sample of stated size and provenance; remove "independent gold" |

A narrowing recommendation applies in all three cases **if** Track B is declined. Option B solves the overclaim but not the missing evidence; the limitation stays.

### 4.6 Guard rails for Phase 3 wording (plan task 5)

- Do not call the template traces case-specific reasoning (C49).
- Do not present curated OVERRULES-edge benefits as uncurated discovery: RQ3 shows a strong dependence on labels (C32, C45).
- Do not treat zero observed fabrication (0/120 CLERC) or 2/75 fatal errors as universal safety (C40, C05).
- Do not describe the gate as the operative mechanism for the deployed Category C refusals (C34).

## 5. Register additions (proposed; Codex verification requested)

**R35.** The Category D explicit-refusal McNemar p-values are stale literals.
- `audit_category_d_rubric.py` hard-codes the values from the pre-Issue-6 TERRA count (42/75).
- `certify_category_d_issue6.py` refreshed the counts and the paired tables but not those four macros.
- Evidence: `p2a_downstream_checks.csv`.
- Consequence: under v2, two contrasts (GraphRAG and HippoRAG) become p < 0.05 unadjusted and 0.034 under Holm. Upgrading them to confirmatory claims would need a declared family, so the proposal is to report them as secondary.

**Informational items (no new R-id).**

| Item | Note | Related R-id |
|---|---|---|
| Epistemic-refusal counts | Unsourced | Under R08 |
| Percentile and SD rules for net latency | Differences under 0.2% | Under R19 |
| GraphRAG undirected edge count | Not reproduced | Under R05 / R07 |
| File size | 109.5 vs 109.6 MB | |

## 6. Limits of this pass

**Not reproduced here:**
- the ablation pilot (752 MB) and the baseline pilot (219 MB): staging timed out;
- the Issue 26 grid raw (197 MB);
- the famous-D1 and cross-suite summaries;
- the GraphRAG adapter code;
- the Louvain modularity 0.6110.

**Weak links.** TRACED means co-occurrence of the value in the named source, not full attribution. A sample check (15 items) found the attributions plausible. One multi-source coincidence (`HippoDocPrecisionGrounded`) was caught and fixed by the Phase 1 v2 recomputation.

**Unchanged caveats:**
- Issue 24 parameters were checked against the current code (`0cca5cf4`) and the 24 Sept preflight (`430fc1b3`). The 14 Sept code state is unpinned.
- R34 chronology remains OPEN.

## 7. Next step

The next step is a Codex audit of this Phase 2 package and then the user's decisions:

1. accept, amend or reject RQ1–RQ3 and contributions 1–4;
2. choose option A or B for each of R05, R06 and R12;
3. accept or reject the proposed R35;
4. whether to authorize Phase 3, in which the approved corrections would be applied one item at a time.

Phase 3 is not started.
