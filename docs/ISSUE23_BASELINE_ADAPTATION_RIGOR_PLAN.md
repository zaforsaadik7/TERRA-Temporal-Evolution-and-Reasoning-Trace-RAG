# Issue #23 Implementation Plan: Baseline Adaptation Rigor ("GraphRAG-Adapted" / "HippoRAG-Adapted")

**Document Version:** 3.1 (Post-Audit Reconciled Specification & Preflight Synchronization)  
**Date:** 2026-09-24  
**Status:** AUDIT RECONCILED (Preflight Gate Passed 8/8 Pillars)  
**Target Issue:** Issue #23 (Tier 2, Master Checklist Item 23 / Second Review Item #16)  
**Historical Baseline Benchmark Anchor:** `dataset_20k_cap/terra_eeg_index_20k_pre_issue6_backup.json` (SHA256: `012c999babb853e5d8f24caec353afe8303b8edd517965a6430957c26a6653bb`)  
**Active Canonical Graph Index Anchor:** `dataset_20k_cap/terra_eeg_index_20k.json` (SHA256: `7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad`)  
**Canonical Benchmark Anchor:** `terra_350_benchmark.json` (SHA256: `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3`)  
**Primary Evaluated Dataset:** `terra_baselines_eval_raw.json` ($N = 1,750$ evaluations; 350 queries $\times$ 5 pipelines)  
**Synchronized Dual-Judged Datasets:** `scratch/terra_350_issue6_dual_judged.json` and `scratch/terra_350_5pipelines_dual_judged.json`  
**Preflight Verification Report:** `data/issue23_preflight.json` (10/10 protected substrates bit-invariant; 0 violations)  

---

## 1. Executive Summary & Audit Response (Version 3.1 Changes)

This revised implementation plan and its accompanying preflight verification gate resolve all blocking contradictions identified during the plan audits:

1. **Dual Corpus Hash & Substantive Holdings Reconciliation**: Formally distinguishes the historical baseline index anchor (`012c999b...`, 98.9 MB, 145,363 edges) used during the initial 1,750-run baseline benchmark from the active canonical index anchor (`7aa6db46...`, 109.5 MB, 145,366 edges, 56 typed `OVERRULES`) produced by Tier 1 Issue #6. Reconciles both states and establishes an unambiguous, two-level holdings accounting definition:
   - **Substantive Extracted Holdings (`holding_extraction_status == 'SUCCESS'`)**: Exactly **10,228 nodes (51.14%)**, consisting of 8,404 Tier 1 official syllabus headnotes and 1,824 Tier 2 dispositive opinion regex extractions.
   - **Total Populated Holding Text Entries (`bool(substantive_holding)`)**: Exactly **19,997 nodes (99.985% $\approx$ 100.0%)**, which includes the 10,228 substantive extractions PLUS 9,769 Tier 3 raw procedural preamble fallbacks (`FALLBACK`), with exactly 3 nodes having unpopulated preambles.
2. **Restoration of Established 10/10 Protected Core Substrates**: Restores the complete set of 10 established protected substrates in the preflight gate (`scripts/verify_issue23_preflight.py`), including `data/issue21_preflight.json` and `logs/issue21_preflight.txt`, preserving the repo's established protection invariant (10/10 bit-invariant).
3. **Definitive Edge Accounting Equation**: Codifies a single mathematical equation reconciling the 145,363 legacy citation edges with the 145,366 active directed edges (145,310 `CITES` + 56 `OVERRULES`), fully explaining the reclassification of 53 edges and the addition of 3 authoritative CRS edges in Issue #6.
4. **Honest Protocol Lineage: Pre-Run vs. Post-Hoc Amendments**: Retracts claims of "pre-registered frozen parameters" and relabels verification gates as **post-hoc quality control gates**. Discloses the exact lineage of in-flight amendments informed by observed benchmark behavior (including Category A answer regeneration, parser bug remediation, prompt overrides, and programmatic score clamps K, L, M).
5. **Material Context-Budget Asymmetry Disclosure**: Eliminates false claims of "context length parity." Explicitly discloses that baselines use compact character budgets (2,400–5,500 chars), whereas TERRA utilizes up to a **60,000-character ceiling** ($10\times$ to $20\times$ larger). Discloses the fairness implications of the 50,000-character middle-omission judge-side truncation.
6. **Character-Based Budget Reporting & Exact Serving Tokenizer**: Replaces vague tokenizer approximations with exact character-based budget reporting, matching the codebase's literal string-slicing implementation (`len()` and `[:N]`), while documenting the serving-tier tokenizer (`meta-llama/Llama-3.3-70B-Instruct`, vocabulary 128,256) strictly for reference.
7. **Standardized Algorithm Naming**: Exclusively uses **GraphRAG-Adapted (Louvain implementation)** and documents the specific deviation from official Leiden clustering.

---

## 2. Corpus Hash Reconciliation & Substrate Evolution

The repository contains two distinct, cryptographically authenticated states of the 20,000-opinion Harvard Caselaw Access Project (CAP) index:

```
Corpus State Evolution & Provenance Flow:

[Harvard CAP 20,000 Opinions (1850–1980)]
                   |
                   v
[Historical Index: 2026-09-05 Baseline Run]
File: dataset_20k_cap/terra_eeg_index_20k_pre_issue6_backup.json
SHA256: 012c999babb853e5d8f24caec353afe8303b8edd517965a6430957c26a6653bb
Size: 98,942,977 bytes (98.9 MB)
Content: 20,000 nodes (procedural opening preambles), 145,363 generic CITES edges
Role: Executed during Workstream 1.2 baseline benchmarking (terra_baselines_eval_raw.json)
                   |
                   | (Tier 1 Issue #6: Ingestion of 10,228 substantive legal holdings
                   |  + 56 typed OVERRULES relations from CRS Constitution Annotated)
                   v
[Active Canonical Index: Issues #6, #19, #20, #21, #22]
File: dataset_20k_cap/terra_eeg_index_20k.json
SHA256: 7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad
Size: 109,574,119 bytes (109.5 MB)
Content: 20,000 nodes (10,228 substantive extractions; 19,997 populated holding texts),
         145,366 edges (145,310 CITES + 56 OVERRULES)
Role: Active verified index across all current manuscript tables and regression suites
```

### 2.1 Explicit Hash Disclosures & Certification Scope
1. **Historical Baseline Benchmark Anchor (`012c999b...`)**:
   - Path: `dataset_20k_cap/terra_eeg_index_20k_pre_issue6_backup.json` (preserved bit-identically on disk).
   - SHA256: `012c999babb853e5d8f24caec353afe8303b8edd517965a6430957c26a6653bb`.
   - Node Count: 20,000 nodes.
   - Directed Edge Count: 145,363 edges (all generic `CITES`).
   - Certification: The raw baseline evaluation records in `terra_baselines_eval_raw.json` ($N=1,750$) were executed directly against this pre-Issue #6 index state, as asserted by `baselines/common.py:CORPUS_SHA256`.
2. **Active Canonical Index Anchor (`7aa6db46...`)**:
   - Path: `dataset_20k_cap/terra_eeg_index_20k.json`.
   - SHA256: `7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad`.
   - Node Count: 20,000 nodes (10,228 substantive legal holding extractions; 19,997 populated holding fields).
   - Directed Edge Count: 145,366 edges (145,310 precedential `CITES` + 56 typed `OVERRULES`).
   - Certification: The synchronized 350-query dual-judge re-evaluation records in `scratch/terra_350_issue6_dual_judged.json` and `scratch/terra_350_5pipelines_dual_judged.json`, as well as all subsequent verified issues (#19, #20, #21, #22), are certified exclusively against this active index state.

### 2.2 Substantive Holdings Accounting & Disambiguation

To resolve any potential ambiguity between extracted holding coverage and raw string population across the 20,000 index nodes:

1. **Substantive Extracted Holdings (`holding_extraction_status == 'SUCCESS'`)**: Exactly **10,228 nodes (51.14%)**
   - **Tier 1 (Official Headnote / Syllabus Extractions)**: $N = 8{,}404$ nodes ($42.02\%$), where official CAP syllabus text and reporter headnotes were isolated.
   - **Tier 2 (Dispositive Opinion Regex Extractions)**: $N = 1{,}824$ nodes ($9.12\%$), where dispositive holding patterns were matched within the opinion body.
   - Total Substantive Extractions = $8{,}404 + 1{,}824 = 10{,}228$ nodes ($51.14\%$).

2. **Procedural Preamble Fallbacks (`holding_extraction_status == 'FALLBACK'`)**: Exactly **9,772 nodes (48.86%)**
   - **Tier 3 (Raw Preamble Excerpt Populated)**: $N = 9{,}769$ nodes ($48.845\%$), populated with the opening lines of the opinion when explicit syllabus or dispositive holding language could not be isolated.
   - **Unpopulated / Empty Preambles**: $N = 3$ nodes ($0.015\%$: `83_0699-01`, `209_0514-01`, `69_0328-01`).

3. **Total Populated Holding Text Fields (`bool(node.get('substantive_holding'))`)**: Exactly **19,997 nodes (99.985% $\approx$ 100.0%)**
   - Reconciles the two metrics: $10{,}228\ (\text{substantive extractions}) + 9{,}769\ (\text{preamble fallbacks}) = 19{,}997$ populated text entries.
   - String-truthiness checks yield 19,997 / 20,000 ($99.985\%$), while strict extraction-success checks yield 10,228 / 20,000 ($51.14\%$).

---

## 3. Definitive Edge Accounting Equation

To eliminate any ambiguity between the legacy metadata edge count and the active graph edge count, the plan establishes a single, closed accounting equation:

### 3.1 The Canonical Equation
$$\boxed{\text{Total Directed Edges}_{\text{active}} = \text{CITES}_{\text{active}} (145{,}310) + \text{OVERRULES}_{\text{active}} (56) = 145{,}366}$$

### 3.2 Reconciliation against Legacy Metadata Substrate
The transition from the legacy metadata edge count ($145{,}363$) to the active graph edge count ($145{,}366$) is governed by the Tier 1 Issue #6 holding ingestion and typed invalidation audit:
1. **Legacy Baseline Edge Pool**: The pre-Issue #6 index contained **145,363** generic, untyped `CITES` edges.
2. **Reclassification of Existing Citation Links**: Exactly **53** existing citation edges connecting recognized landmark overruling pairs were reclassified from generic `CITES` to typed `OVERRULES` relations.
   $$\text{CITES}_{\text{retained}} = 145{,}363 - 53 = 145{,}310$$
3. **Injection of Missing Authoritative Overruling Links**: Exactly **3** authoritative pre-1980 Supreme Court invalidation edges cataloged by the Congressional Research Service (CRS) *Constitution Annotated* were not captured by CAP's automated citation extractor and were added during Issue #6 to ensure 100% landmark coverage:
   - *Brown v. Board of Education* (1954) $\xrightarrow{\text{OVERRULES}}$ *Plessy v. Ferguson* (1896)
   - *West Coast Hotel Co. v. Parrish* (1937) $\xrightarrow{\text{OVERRULES}}$ *Adkins v. Children's Hospital* (1923)
   - *Brandenburg v. Ohio* (1969) $\xrightarrow{\text{OVERRULES}}$ *Whitney v. California* (1927)
   $$\text{OVERRULES}_{\text{active}} = 53\ (\text{reclassified}) + 3\ (\text{CRS additions}) = 56$$
4. **Final Active Edge Sum**:
   $$145{,}310\ (\text{CITES}) + 56\ (\text{OVERRULES}) = 145{,}366\ \text{Total Directed Edges}$$

### 3.3 Representation in Undirected Baselines
- **GraphRAG-Adapted (Louvain implementation)** converts the directed network to an undirected graph via `G.to_undirected()`. Because citation links between Supreme Court cases are almost strictly unidirectional (decided later $\to$ decided earlier; only 13 intra-year reversals exist per Issue #21), the undirected graph collapses reciprocal links and yields **145,353 undirected edges**.
- **HippoRAG-Adapted** constructs a symmetric transition matrix allowing bidirectional diffusion: for every directed citation $u \to v$, entries $(u, v)$ and $(v, u)$ are added, producing a degree-normalized column-stochastic matrix with $290,706$ non-zero entries (accounting for self-loops and degree normalization).

---

## 4. Protocol Lineage: Pre-Run Protocol vs. Post-Hoc Diagnostic Amendments

The plan explicitly disclaims that the benchmark executed under "pre-registered frozen parameters." Instead, the plan transparently delineates:
1. What was established **prior to execution** (Pre-Run Protocol v1.0).
2. What was modified **in-flight** based on observed benchmark behavior (Post-Hoc Amendments).
3. Which evaluation outputs were **regenerated** vs. **re-judged**.
4. Why the evaluation gates function as **post-hoc quality control gates** rather than untouched pre-registered controls.

### 4.1 Chronological Amendment & Provenance Ledger

| Amendment | Date Effective | Execution Phase | Nature of Change & Diagnostic Trigger | Outputs Regenerated? | Benchmark Informed? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Protocol v1.0** | 2026-09-05 | Pre-Run | Approved baseline protocol: 20k corpus, 350 queries, LLaMA 3.3 70B, $T=0.0$, 4096 tokens, payload interceptor. | None (Initial design) | No |
| **Amendment 1.1** | 2026-09-05 | Pre-Run | Recalibrated Gate 3 community purity from 70% absolute to $\ge 1.5\times$ base-rate enrichment ratio ($Q = 0.6110$). | None | Yes (Corpus base-rate analysis on 20k graph) |
| **Amendment 1.2** | 2026-09-05 | Pre-Run | Formally designated community detection as NetworkX Louvain modularity maximization due to Python 3.14/Windows C-extension incompatibility. | None | No (Environmental constraint) |
| **Amendment 1.3** | 2026-09-05 | Pre-Run | Profiled community scale distribution (top 10 communities cover 76.4% of corpus). | None | Yes (Graph pre-clustering audit) |
| **Amendment 1.4** | 2026-09-05 | Pre-Run | Pre-registered HippoRAG two-pass seed linking (title match + vector fallback). | None | No (Algorithmic design) |
| **Amendment 1.5 (Amendment F)** | 2026-09-05 | In-Flight (Category A) | **Fast-Path Parametric Instruction Parity**: In `ask_terra.py`, the fast path defaulted to RAG negative instruction, causing 18–22% false refusals on single-case lookups. Patched to pass `NEUTRAL_DIRECT_SYSTEM_INSTRUCTION`. | **YES: 100 Category A answers for `5_Full_TERRA` regenerated** via `scripts/apply_amendment_f_cat_a.py`. Superseded logs archived. | **YES: Directly informed by observing false refusals on Category A queries.** |
| **Amendment 1.6 (Amendment G)** | 2026-09-05 | In-Flight (Category A closeout) | **Universal Parser Likert-1 Remediation**: Discovered `_parse_likert` treated discrete float `1.0` as normalized probability 1.0 ($1 \to 5$ silent score inversion). Patched parser across all scripts. | **NO text regenerated. Retroactively re-evaluated judge scores across all 313 non-refusal records** via `scripts/apply_amendment_g.py`. | **YES: Directly informed by finding 32 inverted scores in checkpoint audit.** |
| **Amendment 1.7 (Amendment H)** | 2026-09-06 | In-Flight (Category B closeout) | **In-Memory Checkpoint Race Remediation**: Runner in-memory state overwrote out-of-band disk patch on B041. Executed quiescent patching protocol; live re-judged B041 and B092. Certified Category B (`AMENDMENT_H_VERIFIED.lock`). | **NO text regenerated. Quiescent re-judge of B041 and B092.** | **YES: Triggered by Databricks API socket timeouts on B041/B092.** |
| **Amendment 1.8** | 2026-09-06 | In-Flight (Pre-Cat C) | **Category C Metric Framing**: Established Safety Refusal Rate ($\mathcal{R}_{\text{safe}}$) as primary metric; documented Direct LLM and HippoRAG factual rubric inflation artifacts on science/math queries (`C003`, `C073`). Certified Category C (`CATEGORY_C_VERIFIED.lock`). | None | **YES: Triggered by observing critic judge awarding Likert 5 to Direct LLM on CRISPR-Cas9 physics/bio queries.** |
| **Amendment 1.9 (Amendment I)** | 2026-09-06 | In-Flight (Category D start) | **Category D Critic Prompt Override (Option B)**: Query D001 case study: standard RAG judge awarded Flat RAG Likert 4 for faithfully summarizing overruled *Plessy* context. Added Category D critic override to penalize unhedged overruled affirmations. | **NO text regenerated. Re-judged D001 across all 5 pipelines.** | **YES: Directly informed by observing Flat RAG D001 receiving a passing score for affirming separate-but-equal.** |
| **Amendment 1.10 (Amendment J)** | 2026-09-06 | In-Flight (Category D `D001`–`D010`) | **Disentanglement of Faithfulness from Relevance**: Query D004 case study: timid refusals penalized as unfaithful ($F=1$). Implemented 3-tier critic prompt + independent semantic LLM verifier (`invariant_6_cache.json`). Re-judged D001–D010. | **NO text regenerated. Re-evaluated judge scores on D001–D010 (50 records, 21 score shifts).** | **YES: Directly informed by observing GraphRAG D004 refusal being penalized as unfaithful.** |
| **Amendment 1.11 (Amendment K)** | 2026-09-06 | In-Flight (Pre `D011`–`D075`) | **Programmatic Refusal Floor Clamp**: Pre-registered code-level clamp in `runner_core.py`: non-fatal refusals cannot be scored $F < 4$. Verified zero regression on `D001`–`D010`. | None | **YES: Informed by zero-shot held-out test on Gobitis/Barnette showing judge conflating refusal with falsity.** |
| **Amendment 1.12 (Amendment L)** | 2026-09-06 | In-Flight (Query `D011`) | **Symmetric Fatal Affirmation Ceiling Clamp**: On `D011 GraphRAG`, judge awarded $F=5$ despite model adopting fatal error due to historical citation of Juilliard. Clamped verified fatal affirmations to $F = 1$. | **NO text regenerated. Shifted `D011 GraphRAG` ($5 \to 1$).** | **YES: Intercepted by Invariant 6A monitor on live smoke test D011.** |
| **Amendment 1.13 (Amendment M)** | 2026-09-06 | In-Flight (Query `D016` / `D025`) | **Programmatic Refutation Floor Clamp**: On `D016 Flat RAG`, judge penalized genuine refutation citing Katz with $F=1$ due to concluding hedging. Implemented refutation floor clamp ($F \ge 4$). | **NO text regenerated. Shifted `D016 Flat RAG` ($1 \to 4$).** | **YES: Informed by diagnostic spot-check on D016 Olmstead refutation.** |
| **Phase 6 Follow-Up** | 2026-09-06 | Post-Run | Documented Traffic Cop fast-path misclassification on reciprocal landmark traps (`D033`, `D034`) resulting in 2 fatal parametric hallucinations. | None | **YES: Informed by observing fast-path routing failures on Category D.** |

### 4.2 Reclassification of Verification Gates
The five gates originally framed as "Pre-Registered Hard Gates" in protocol drafts are formally reclassified as **Post-Hoc Quality Control & Verification Gates**:
- **Gate 1 (Corpus Parity)**: Post-hoc assertion confirming all pipelines ingested from the identical 20,000-node source file.
- **Gate 2 (Generator Parity)**: Real-time interceptor assertion logging model name, temperature, and token limits to `audit_payloads.jsonl`.
- **Gate 3 (Algorithmic Convergence)**: Pre-flight sanity checks on Louvain modularity ($Q \ge 0.40$) and HippoRAG PPR power iteration residual convergence.
- **Gate 4 (Parameter Transparency)**: Explicit disclosure table documenting architectural differences.
- **Gate 5 (Metric Macro Locking)**: Post-hoc programmatic verification that all reported text numbers derive exclusively from `Paper/scripts/generate_stats.py`.
- **Check 6 (Programmatic Score Verification Clamps)**: Post-hoc automated audit enforcing Amendments K, L, and M on judge scores.

---

## 5. Material Context-Budget Asymmetry & Evaluator Truncation

The plan retracts all prior statements suggesting that context budgets were "matched" or "eliminate context-window length asymmetries." In reality, there is a **large, intentional architectural asymmetry** between the compact baselines and TERRA's extensive multi-hop precedent trajectories.

### 5.1 The 10x–20x Context-Budget Asymmetry

| Pipeline | Retrieval Breadth | Ingested Text Components | Character Ceiling in Code | Approximate LLaMA Tokens | Asymmetry Ratio (vs. Flat RAG) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1_Direct_LLM** | None | Parametric memory only | 0 chars | 0 tokens | $0.0\times$ |
| **2_Flat_Vector_RAG** | $n=2$ traces | 2 thinking traces (~1,200 chars each) | ~3,200 chars max | ~600–850 tokens | **$1.0\times$ (Baseline)** |
| **3_GraphRAG-Adapted (Louvain)** | $k=5$ seeds | 5 extracts (`[:400]`) + 1-hop citations (3 in, 3 out) + parent community summaries | ~5,500 chars max | ~900–1,450 tokens | **$1.7\times$** |
| **4_HippoRAG-Adapted** | $k=5$ opinions | 5 ranked opinion snippets (`[:400]`) + PPR execution header | ~3,500 chars max | ~650–920 tokens | **$1.1\times$** |
| **5_Full_TERRA** | 2–4 seeds + up to 40 graph nodes | Evolution block + structural relations + landmark holding extracts (`[:1200]`) + traces | **60,000 chars hard ceiling** | **~12,000–15,500 tokens** | **$18.8\times$** |

### 5.2 Scientific Framing & Methodological Justification
- **Architectural Trade-Off**: The large context asymmetry is the defining architectural feature of TERRA. Baselines follow their literature-native designs, relying on compact, highly filtered short passages (400-character snippets). TERRA, by contrast, is designed specifically for complex legal doctrine, which requires tracing evolutionary chains across multi-decade precedents.
- **Token Volume & Financial Cost Alignment**: This asymmetry is fully aligned with the computational budget profiling already disclosed in Table XVI: Category B queries average 11,321 prompt tokens for TERRA vs. 653 for Flat RAG ($17.3\times$ token volume, costing $14.07 per 1,000 queries vs. $0.54 for Flat RAG). The paper candidly discloses this cost ratio as the necessary investment to secure 62.0% full trajectory recovery.
- **Removed Claims**: All text claiming that the experimental design "eliminates context-window length asymmetries" or provides "matched token budgets" will be purged from the manuscript.

### 5.3 Evaluator-Side (Critic Judge) Middle-Omission Truncation
In `baselines/runner_core.py:judge_single_prompt()`:
- If `len(context) > 50000`, the critic judge context is truncated using middle omission:
  $$\text{eval\_context} = \text{context}[:25000] + \text{"\n\n...[Middle context omitted for judge brevity]...\n\n"} + \text{context}[-25000:]$$
- **Fairness Analysis**:
  1. **Baselines Unaffected**: Because all baseline contexts are $< 6,000$ characters, the judge evaluates **100% of baseline retrieved context with zero truncation**.
  2. **TERRA Impact**: On complex Category B queries where TERRA compiles $> 50,000$ characters of traversal context, the judge prompt omits the middle 10,000 characters while preserving the first 25,000 characters (seed authorities, procedural traces, and evolution headers) and the final 25,000 characters (terminal citing successors and holding summaries).
  3. **Consequence**: The judge evaluates a compressed 50,000-character context window for TERRA, preventing context-overflow errors on the Databricks judge endpoint while preserving the critical boundary anchors of the precedent chain.

### 5.4 Sequence of NLI Entailment Filtering vs. Budget Truncation
In `ask_terra.py`:
1. `grading_context` is constructed and capped at 60,000 characters (`grading_context = grading_context[:60000]`).
2. The NLI Smart Grader evaluates contextual entailment **BEFORE** generator context truncation.
3. If rejected after Attempt 2, execution short-circuits to an epistemic refusal; the generator is never called.
4. If accepted, `full_compiled_context` is clamped to 60,000 characters (`[:60000]`) and passed to the generator.
5. **Consequence**: The NLI safety gate evaluates raw, untruncated traversal evidence, guaranteeing that budget truncation never conceals unentailed evidence from the safety filter.

---

## 6. Character-Based Budget Reporting & Serving Tokenizer Specification

### 6.1 Authoritative Character-Based Budgeting
Across the entire repository codebase (`ask_terra.py`, `baselines/runner_core.py`, `baselines/graphrag_adapter.py`, `baselines/hipporag_adapter.py`), all context bounds, extract lengths, and truncation ceilings are implemented **exclusively as Python character operations (`len()` and string slicing `[:N]`)**. No local tokenizer library (tiktoken, HuggingFace transformers) is executed in the harness to meter tokens.

Therefore, the plan mandates that all official implementation tables and specifications report **exact character limits as primary**:
- Direct LLM: 0 characters
- Flat Vector RAG: Bounded by $n=2$ traces (~3,200 chars max)
- GraphRAG-Adapted (Louvain): Bounded by component slicing (400 chars/extract, 3 edges/direction, ~5,500 chars max)
- HippoRAG-Adapted: Bounded by component slicing (400 chars/extract, ~3,500 chars max)
- TERRA Generation Context: Hard ceiling at **60,000 characters** (`full_compiled_context[:60000]`)
- TERRA NLI Grading Context: Hard ceiling at **60,000 characters** (`grading_context[:60000]`)
- Critic Judge Truncation: Hard middle-omission split at **50,000 characters** (`[:25000] + ... + [-25000:]`)

### 6.2 Serving-Tier Tokenizer Reference (Informational Only)
Token counts reported in the manuscript are informational conversions provided for context window comparison. The exact serving infrastructure is:
- **Serving Provider**: Databricks Model Serving
- **Model Endpoint**: `databricks-meta-llama-3-3-70b-instruct`
- **Underlying Architecture**: Meta LLaMA 3.3 70B Instruct (`meta-llama/Llama-3.3-70B-Instruct`)
- **Tokenizer**: Official LLaMA 3 Byte-Pair Encoding (BPE) tokenizer
- **Vocabulary Size**: 128,256 tokens
- **Context Window**: 131,072 tokens (128k)
- **Empirical Ratio on SCOTUS Text**: $3.82 \pm 0.31$ characters per token

---

## 7. Standardized Terminology & Louvain Deviation Disclosure

### 7.1 Authoritative Designation
Across all manuscript text, tables, figures, script comments, and LaTeX macros, the Microsoft GraphRAG baseline adaptation shall be designated exclusively as:
> **GraphRAG-Adapted (Louvain implementation)**

The shortened string `GraphRAG-Adapted` is permitted in space-constrained LaTeX table columns, provided the accompanying table footnote explicitly defines it as the Louvain implementation.

### 7.2 Explicit Disclosure of Deviation from Official Leiden Implementation
Section IV-B and Section VI-A will include the following formal disclosure:
> *"**Baseline Implementation Note (GraphRAG Louvain Adaptation)**: Official Microsoft GraphRAG (Edge et al., 2024) executes hierarchical Leiden community detection over entity-relation graphs extracted from text. In our legal benchmarking environment, we adapt GraphRAG to operate directly over the verified 145,363 citation edges of the 20,000-case corpus. Due to Python 3.14 C-extension build constraints on our host evaluation environment, we implement community detection via NetworkX Louvain modularity optimization (`networkx.algorithms.community.louvain_communities`, resolution=1.0, seed=42) rather than the official PyPI `graphrag` C-based Leiden algorithm. While Louvain achieves robust modularity ($Q = 0.6110$) across the citation network, Leiden provides superior theoretical guarantees against internally disconnected communities. Our adaptation implements GraphRAG's dual-level Local Search, combining parent community summary profiles with local 1-hop precedent citation subgraphs."*

---

## 8. Authoritative Preflight Verification Gate (`scripts/verify_issue23_preflight.py`)

The repository enforces an automated, 8-pillar preflight verification script (`scripts/verify_issue23_preflight.py`) that strictly validates all cryptographic, topological, algorithmic, and provenance invariants prior to any manuscript or checklist modifications:

### 8.1 The 8 Verification Pillars & Invariants
1. **Pillar 1: Protected Core Substrates Bit-Invariance (10/10 Established)**:
   - Validates all 10 established protected substrates against their canonical SHA256 hashes:
     * `terra_350_benchmark.json`: `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3`
     * `dataset_20k_cap/terra_eeg_index_20k.json`: `7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad`
     * `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1890.json`: `c530f9858e9b3372dc9079092178e9d8c2239758eda073c35b9fc7b0c49e1f72`
     * `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1930.json`: `14071dba780157b767dfce1f11ef8190722ad94ab9a37e8258bb574a0183c3fc`
     * `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1950.json`: `98d14bfb75d5051429ff4c48c0410300efb5ef7f04112701635f110aff094ddf`
     * `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1970.json`: `5e2b59ac3fce2b9513c9ceb60b6a1cae0c2323150f4936a0410503fd56689f3c`
     * `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1980.json`: `606a6ec126bf7c5ac4cbdbac04f37eee52f7bd524d35e5f12d8dc4ebff3e23b5`
     * `ask_terra.py`: `430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd`
     * `data/issue21_preflight.json`: `9a26a9e35340111773180cadd9f3c271fcecde1a3863609d6abbd2236ba7a9b2`
     * `logs/issue21_preflight.txt`: `91d028cd9ce5079d16bf540cba6546bfa825e5688b3283eb5ef226cc8a3d84d8`
2. **Pillar 2: Dual Index Anchors & Integrity**:
   - Historical Baseline Anchor: `012c999b...` (98.9 MB, pre-Issue #6 baseline substrate).
   - Active Canonical Anchor: `7aa6db...` (109.5 MB, post-Issue #6 active substrate).
3. **Pillar 3: Closed Edge Accounting Equation & Holdings Disambiguation**:
   - Closed Edge Equation: $145{,}310\ (\text{CITES}) + 56\ (\text{OVERRULES}) = 145{,}366\ \text{Total Active Edges}$.
   - Legacy Reconciliation: $145{,}363 - 53 + 3 = 145{,}366$.
   - Holdings Accounting: Exactly **10,228 substantive extractions** (`SUCCESS`: 8,404 syllabus + 1,824 regex; 51.14%) vs **19,997 populated holding text entries** (99.985%, including 9,769 preamble fallbacks; 3 unpopulated).
4. **Pillar 4: Artifact-to-Index Provenance Mapping (Non-Conflation Guarantee)**:
   - `baselines/common.py` asserts `012c999b...`.
   - `terra_baselines_eval_raw.json` contains exactly 1,750 records across 5 matched pipelines.
   - Dual-judged suites certified on active index `7aa6db...`.
5. **Pillar 5: Adapter Algorithmic Parameters Verification**:
   - GraphRAG-Adapted: Louvain modularity (seed=42, res=1.0), top_k=5, 400-char extracts, 3 in / 3 out edges.
   - HippoRAG-Adapted: PPR power iteration (alpha=0.85, tol=1e-6, max_iter=50), top_k=5, 400-char extracts, 2-pass seed linking.
   - Common Generator: LLaMA 3.3 70B, T=0.0, max_tokens=4096.
6. **Pillar 6: Character Budgets & Truncation Hierarchy**:
   - `ask_terra.py`: 60,000-character ceiling, Smart Grader evaluates BEFORE generator context truncation.
   - `runner_core.py`: Flat RAG n=2 traces, Judge 50,000-character middle omission.
7. **Pillar 7: Amendment Timeline, Lockfiles & Programmatic Clamps**:
   - Verified physical presence of all 4 verification lockfiles and integration protocol.
   - Verified programmatic score clamps (Amendments K, L, M) and semantic verifier cache in `runner_core.py`.
8. **Pillar 8: Context Budget Asymmetry Disclosures**:
   - Documents the $18.8\times$ character ceiling asymmetry (TERRA 60k vs. Flat RAG 3.2k).

### 8.2 Execution Results (Preflight PASS)
The script was executed read-only (`python scripts/verify_issue23_preflight.py`):
```text
>>> PREFLIGHT VERIFICATION COMPLETE: ALL 8 PILLARS PASSED ZERO VIOLATIONS <<<
- Protected Core Substrates: 10/10 verified bit-invariant (PASS)
- Dual Index Anchors: 012c999b... (historical) and 7aa6db... (active) verified (PASS)
- Closed Edge Equation: 145,310 + 56 = 145,366 active edges verified (PASS)
- Holdings Disambiguation: 10,228 extracted (51.14%) vs 19,997 populated (99.985%) verified (PASS)
- Provenance Mapping: 1,750 baseline records non-conflation certified (PASS)
- Adapter Parameters: Louvain & HippoRAG PPR verified (PASS)
- Character Ceilings: 60k generator & 50k judge middle omission verified (PASS)
- Amendment Clamps & Lockfiles: K, L, M verified (PASS)
- Context Asymmetry: 18.8x ratio verified (PASS)
Serialized artifacts: data/issue23_preflight.json & logs/issue23_preflight.txt
```

---

## 9. Next Steps (Awaiting Audit Approval)

Upon receipt of formal user approval for this Version 3.1 plan and verified preflight gate, execution will proceed strictly according to the following phased sequence:

1. **Preflight Certification**: Re-confirm preflight gate artifacts (`data/issue23_preflight.json` and `logs/issue23_preflight.txt`).
2. **Manuscript Synchronization (`Paper/main.tex`)**:
   - Update Section IV-B to incorporate the complete Baseline Fairness Matrix, the 10x–20x context-budget asymmetry disclosure, and the Louvain deviation disclosure.
   - Update Section V-A and Section VI-A to incorporate the exact shared-versus-derived topology framing, the dual index hash evolution, the edge accounting equation, the disambiguated holdings accounting (10,228 extracted / 19,997 populated), and the post-hoc amendment timeline.
   - Standardize all occurrences of GraphRAG terminology to `GraphRAG-Adapted (Louvain implementation)`.
3. **Macro Harmonization**: Verify that all baseline macros in `Paper/generated_stats.tex` strictly match `terra_baselines_eval_raw.json` within automated CI tolerance.
4. **Automated CI & Compilation**:
   - Execute `python Paper/scripts/check_consistency.py --target Paper/` to ensure zero orphaned numbers or broken references (4/4 PASS).
   - Compile `Paper/main.tex` via Tectonic to verify clean PDF output strictly preserved at **exactly 35 pages**.
   - Package updated Overleaf and reproducibility archives.
5. **Master Checklist Reconciliation**:
   - Update Issue #23 in `TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md` from `[ ]` to `[x]` with exhaustive documentation of findings, parameter tables, and artifact hashes.
