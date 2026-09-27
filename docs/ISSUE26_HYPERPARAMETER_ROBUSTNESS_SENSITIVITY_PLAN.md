# Issue #26 Implementation Plan: Retrieval Hyperparameter Robustness & Traversal Horizon Sensitivity

**Document Version:** 5.0 (Audited Revision: Reclassification of $k=1^\ast$ as Audit-Time Counterfactual, Formal Retraction of Decomposed Anchor Claims, Exact Extraction Definition for $U_{\text{baseline}}(q)$, and Multi-Tier Parity Invariants)  
**Date:** 2026-09-24  
**Status:** **AWAITING USER AUDIT APPROVAL BEFORE EXECUTION**  
**Target Issue:** Issue #26 (Tier 2, Master Checklist Item 26)  
**Reviewer Issues Addressed:** Second Review Issue #11 (*BFS depth does not obviously cover the benchmark's longest reasoning chains — BFS depth sensitivity sub-requirement*) & Checklist Item 26 (*Lack of robustness analysis for core retrieval hyperparameters*)  
**Cross-References:** Issue #9 (Direct Evidence Retrieval & Hop-Length Recall), Issue #10 (Computational Budget Profiling), Issue #19 (Dynamic Knowledge Drift & Taxonomy Filter Constraints), Issue #24 (Hyperparameter Freeze Documentation), Issue #25 (Corpus Scope vs. Task Scope Disparity)

---

## 1. Executive Summary & Audit Revisions (Version 5.0)

### 1.1 Resolution of Seed Provenance & $k=1^\ast$ Counterfactual Status (Directive 1 & 2)
- **Reclassification of $k=1^\ast$ as Audit-Time Counterfactual**:
  In response to the audit finding that historical seed generation cannot be separated reproducibly from `context_full`, the $k=1$ condition is **formally removed from the production-grounded sweep** and designated as an **audit-time counterfactual experiment** ($k=1^\ast$).
- **Formal Retraction of Decomposed Seed Claims**:
  We formally retract any claim that exact-title seeds ($S_{\text{exact}}$), query-expansion seeds, or primary vector seeds can be individually decomposed or isolated from `context_full`. Because `context_full` records the initialized `Depth 0` anchors without individual upstream source tags, separating them post-hoc would constitute an unverified reconstruction.
- **Counterfactual Definition for $k=1^\ast$**:
  The $k=1^\ast$ condition is defined strictly as an audit-time ablation where traversal is initialized from only the single primary anchor $s_1(q)$ (the first anchor appearing in the frozen context-derived anchor list for query $q$). It simulates single-anchor graph retrieval to evaluate sensitivity to minimal seed breadth, and is explicitly labeled as a counterfactual ablation across all tables and prose.
- **Counterfactual Definition for $k=4^\ast$**:
  The $k=4^\ast$ condition expands the seed beam to top-4 vector traces from ChromaDB under `where={"category":{"$eq":"civil_rights"}}`. As established in Issue #19, this taxonomy filter is defective on the current index; therefore, $k=4^\ast$ is explicitly designated as an **audit-time current-index counterfactual experiment** and annotated with a disclosure footnote.

### 1.2 Production-Grounded Sweep Scope
The **production-grounded sensitivity sweep** is strictly defined over configurations that use the **frozen context-derived seed anchors** intact (all 241 anchors extracted from `terra_baselines_eval_raw.json`, mean 2.41 seeds/query, min 2, max 5, matching `\CatBMeanSeedsPerQuery`):
1. **Depth Horizon Sensitivity**: $d \in \{1, 2, 3\}$ (with canonical hub cap $C=50$)
2. **Hub Degree Threshold Sensitivity**: $C \in \{25, 50, 100\}$ (with canonical depth $d=2$)
3. **Full Factorial Surface**: $(d, C) \in \{1, 2, 3\} \times \{25, 50, 100\}$ ($9$ configurations)
4. **Adaptive Depth Strategy**: $d_{\text{adapt}} \in \{1, 2, 3\}$ (with canonical hub cap $C=50$, $1$ configuration)
In all production-grounded configurations, the seed set is the inviolable 241 frozen anchors, guaranteeing 100% production grounding without synthetic seed subsetting or filtering.

### 1.3 Precise Extraction Definition for $U_{\text{baseline}}(q)$ and $U_{\text{sweep}}(q)$ (Directive 3)
To eliminate any ambiguity regarding node extraction:
- **Extraction Source**:
  Both $U_{\text{baseline}}(q)$ and $U_{\text{sweep}}(q)$ are extracted directly from the compiled context string `context_full(q)`. Grader-delivered context (`grading_context`) is NOT used because it was an ephemeral variable during execution and was not serialized in `terra_baselines_eval_raw.json`.
- **Mathematical Extraction Rules**:
  Two precise, deterministic node-ID sets are extracted from `context_full(q)`:
  1. **Full Context Node-ID Set ($U_{\text{full}}(q)$)**:
     $$U_{\text{full}}(q) = \left\{ n \in \mathcal{V}_{\text{EEG}} \;\middle|\; n \text{ matches regex } \texttt{\\b(\\d+_\\d+-\\d+)\\b} \text{ in } \text{context\_full}(q) \right\}$$
     This extracts all valid EEG case identifiers appearing anywhere in the compiled context (including seeded case headers, graph expansion context, citation edges/records, and retrieved traces).
  2. **Traversal Visited Node-ID Set ($U_{\text{traversal}}(q)$)**:
     $$U_{\text{traversal}}(q) = \left\{ n \in \mathcal{V}_{\text{EEG}} \;\middle|\; n \text{ matches regex } \texttt{--- Node: .*? \\(Case ID: ([\\w\\-]+), Depth \\d+\\) ---} \text{ in } \text{context\_full}(q) \right\}$$
     This extracts the exact set of node IDs expanded by the BFS queue during graph traversal and written to the `[GRAPH EXPANSION CONTEXT]` block.
- **Symmetric Application**:
  The exact same extraction functions ($U_{\text{full}}$, $U_{\text{traversal}}$, and the gold matcher $V_{\text{retrieved\_gold}}$) are applied symmetrically to both baseline context and all sweep configuration contexts.

### 1.4 Multi-Tier Canonical Parity Gate (Directive 4)
The canonical baseline verification gate ($k=2, d=2, C=50$) enforces:
1. **Complete Node-ID Set Equality**:
   $$U_{\text{full}}^{\text{sweep}}(q) \equiv U_{\text{full}}^{\text{baseline}}(q) \quad \forall q \in \{B001, \dots, B100\}$$
2. **Traversal Visited Node-ID Set Equality**:
   $$U_{\text{traversal}}^{\text{sweep}}(q) \equiv U_{\text{traversal}}^{\text{baseline}}(q) \quad \forall q \in \{B001, \dots, B100\}$$
3. **Gold Landmark Node Intersection Equality**:
   $$V_{\text{retrieved\_gold}}^{\text{sweep}}(q) \equiv V_{\text{retrieved\_gold}}^{\text{baseline}}(q) \quad \forall q \in \{B001, \dots, B100\}$$
   where $V_{\text{retrieved\_gold}}(q) = \{ t \in V_{\text{gold}}(q) \mid \text{match\_node\_in\_context}(t, \text{context\_full}(q), \text{nodes}) = \text{True} \}$ using the exact matcher from `scripts/compute_retrieval_metrics.py`.
4. **Exact Aggregate Metric Equality (Authoritative Issue #9 Record)**:
   - Macro Node Recall: **$86.1\%$** ($86.08\%$)
   - Micro Node Recall: **$86.3\%$** ($86.26\%$, $295 / 342$)
   - Full Precedent Path Recall: **$62.0\%$ ($62 / 100$)**
   - 3-Node Chains ($N=63$): Path Recall **$58.7\%$ ($37 / 63$)**, Node Recall **$86.2\%$**
   - 4-Node Chains ($N=32$): Path Recall **$62.5\%$ ($20 / 32$)**, Node Recall **$83.6\%$**
   - 5-Node Chains ($N=5$): Path Recall **$100.0\%$ ($5 / 5$)**, Node Recall **$100.0\%$**

### 1.5 Preservation of Authoritative Baseline
The authoritative baseline evaluated under Issue #9 from `terra_baselines_eval_raw.json` (SHA256: `95e775e29c3a0d95...`) is permanently preserved as the sole ground truth. Intermediate scratch figures ($88.9\%$, $66.0\%$) are fully discarded.

---

## 2. Core Substrates & Invariant Anchors

| Substrate | Path | Expected SHA256 (first 16 chars) | Role in Issue #26 |
| :--- | :--- | :--- | :--- |
| **Benchmark Suite** | `terra_350_benchmark.json` | `8144fa81cf98899d...` | Read-only source for 100 Category B queries and gold targets |
| **Canonical EEG Index** | `dataset_20k_cap/terra_eeg_index_20k.json` | `7aa6db466100ae38...` | 20,000-case graph (145,366 edges) traversed across all grid points |
| **ChromaDB Vector Store** | `dataset_20k_cap/vector_db_20k` | SQLite DB (`thinking_traces`, 20k records) | Queried only for the $k=4^{\ast}$ counterfactual condition |
| **Operational Pipeline** | `ask_terra.py` | `430fc1b3fd1ce7ed...` | Reference implementation for traversal logic (PROTECTED) |
| **Raw Baseline Eval** | `terra_baselines_eval_raw.json` | `95e775e29c3a0d95...` | Authoritative source of context-derived seed anchors & baseline (PROTECTED) |
| **5 Temporal Subgraphs** | `dataset_20k_cap/temporal_subgraphs/*` | `c530f985...`, `14071dba...`, etc. | Verified bit-invariant (Pillar 1) |
| **Prior Preflight Data** | `data/issue21_preflight.json`, `logs/*` | `9a26a9e3...`, `91d028cd...` | Verified bit-invariant (Pillar 1) |

---

## 3. Mathematical Grid Specification & Empirical Metrics

### 3.1 Sweep Configurations ($N=22$ Total)

The grid is structured into two cleanly segregated tiers:

#### Tier 1: Production-Grounded Sensitivity Grid ($N=10$)
All Tier 1 configurations use the exact, un-manipulated 241 frozen context-derived seed anchors:
1. **Factorial Depth $\times$ Hub Cap Grid ($N=9$)**:
   - Depth horizon: $d \in \{1, 2, 3\}$
   - Hub degree cap threshold: $C \in \{25, 50, 100\}$
   - Traversal logic: exact reproduction of the canonical traversal with deterministic integer hub scaling:
     $$\text{cap}_{\text{in}}(C) = \text{int}(1.5 \times C), \quad \text{cap}_{\text{out}}(C) = \text{int}(0.5 \times C)$$
     - $C=25 \implies \text{cap}_{\text{in}}=37, \;\text{cap}_{\text{out}}=12$
     - $C=50 \implies \text{cap}_{\text{in}}=75, \;\text{cap}_{\text{out}}=25$ (Canonical Baseline)
     - $C=100 \implies \text{cap}_{\text{in}}=150, \;\text{cap}_{\text{out}}=50$
2. **Adaptive Depth Strategy ($N=1$)**:
   - Evaluated at canonical hub cap $C=50$ using the mechanical heuristic based on temporal span query language:
     - $d_{\text{adapt}}(q) = 3$ if $\exists s \in \mathcal{S}_{\text{span}} : s \in T_q.\text{lower}()$ AND $|S_q| \le 2$
     - $d_{\text{adapt}}(q) = 1$ if $|S_q| \ge 4$
     - $d_{\text{adapt}}(q) = 2$ otherwise
     where $\mathcal{S}_{\text{span}} = \{\text{"eighty years"}, \text{"chronological"}, \text{"evolution"}, \text{"over the decades"}, \text{"path of cases"}, \text{"decade after"}, \text{"years following"}\}$.

#### Tier 2: Audit-Time Counterfactual Seed Sweep ($N=12$)
1. **Single-Seed Anchor Counterfactual ($k=1^\ast$, $N=9$)**:
   - Traversal initialized strictly from the primary anchor $s_1(q)$ (first anchor from frozen list), evaluated across $(d \in \{1, 2, 3\}) \times (C \in \{25, 50, 100\})$.
   - Core representative reported in Table XIX Panel C is $(k=1^\ast, d=2, C=50)$.
2. **Expanded Vector Seed Counterfactual ($k=4^\ast$, $N=3$)**:
   - Seed beam expanded to top-4 vector traces from ChromaDB under `where={"category":{"$eq":"civil_rights"}}`, evaluated across $d \in \{1, 2, 3\}$ at $C=50$.
   - Explicitly annotated with the Issue #19 taxonomy filter disclosure footnote.
   - Core representative reported in Table XIX Panel C is $(k=4^\ast, d=2, C=50)$.

#### Summary of Reported Configurations in Table XIX Panel C ($N=8$ Core Rows)
1. **Canonical Baseline**: $k=2, d=2, C=50$ (Production-Grounded)
2. **Depth Horizon $d=1$**: $k=2, d=1, C=50$ (Production-Grounded)
3. **Depth Horizon $d=3$**: $k=2, d=3, C=50$ (Production-Grounded)
4. **Hub Degree Cap $C=25$**: $k=2, d=2, C=25$ (Production-Grounded)
5. **Hub Degree Cap $C=100$**: $k=2, d=2, C=100$ (Production-Grounded)
6. **Adaptive Depth $d_{\text{adapt}}$**: $k=2, d_{\text{adapt}}, C=50$ (Production-Grounded)
7. **Counterfactual Single Seed $k=1^\ast$**: $k=1^\ast, d=2, C=50$ (Audit-Time Counterfactual)
8. **Counterfactual Expanded Seed $k=4^\ast$**: $k=4^\ast, d=2, C=50$ (Audit-Time Counterfactual)

### 3.2 Recorded Evaluation Metrics
For every configuration, the sweep runner computes and exports:
- **Macro Node Recall ($\%$)**: $\frac{1}{|Q|}\sum_{q \in Q} \frac{|V_{\text{retrieved}}(q) \cap V_{\text{gold}}(q)|}{|V_{\text{gold}}(q)|}$
- **Micro Node Recall ($\%$)**: $\frac{\sum_{q \in Q} |V_{\text{retrieved}}(q) \cap V_{\text{gold}}(q)|}{\sum_{q \in Q} |V_{\text{gold}}(q)|}$
- **Full Precedent Path Recall ($\%$)**: $\frac{1}{|Q|}\sum_{q \in Q} \mathbb{I}[V_{\text{gold}}(q) \subseteq V_{\text{retrieved}}(q)]$
- **Chain-Length Disaggregated Path Recall**:
  - 3-Node Chains ($N=63$, 2 citation hops)
  - 4-Node Chains ($N=32$, 3 citation hops)
  - 5-Node Chains ($N=5$, 4 citation hops)
- **Context Volume & Complexity**:
  - Mean Graph Nodes Visited per Query ($|U_{\text{traversal}}(q)|$)
  - Mean Context Character Volume & Estimated Prompt Tokens
- **Traversal Latency**:
  - Mean Retrieval + Traversal Latency (ms)
  - Median Traversal Latency (ms)

---

## 4. Multi-Phase Implementation Plan

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PHASE IMPLEMENTATION FLOW                       │
└────────────────────────────────────────────────────────────────────────┘
  Phase 1: Preflight Verification & Deterministic Sweep Engine
      │   - Verify 10/10 protected substrates
      │   - Extract 241 frozen context-derived seed anchors from terra_baselines_eval_raw.json
      │   - Run scripts/run_issue26_hyperparameter_sensitivity.py (22 configs)
      │   - Enforce multi-tier canonical parity gate (U_full, U_traversal, V_gold, metrics)
      │   - Serialize data/issue26_hyperparameter_sensitivity.json & audit log
      ▼
  Phase 2: Macro Ledger Synchronization & CI Audit
      │   - Export \IssueTwentySix* macros to Paper/generated_stats.tex
      │   - Run check_consistency.py (Assert 4/4 PASS)
      ▼
  Phase 3: Table XIX Panel C Integration & Manuscript Authoring
      │   - Embed Panel C into Paper/tables/table_retrieval_eval.tex (with k=1* and k=4* footnotes)
      │   - Author \subsubsection in Section VI-G (line 917) using neutral scientific framing
      │   - Synchronize Section VII-B Limitation 17
      ▼
  Phase 4: Layout Optimization & Hard 35-Page Budget Verification
      │   - Local whitespace absorption on Pages 27–31
      │   - Compile with Tectonic; assert len(pages) == 35
      │   - Verify 0 undefined refs/citations; all 27 refs on Page 35
      ▼
  Phase 5: Distribution Packaging, Master Checklist, & Closeout
          - Rebuild and verify TERRA_Overleaf_Bundle.zip
          - Rebuild and verify TERRA_Reproducibility_Bundle.zip + manifest
          - Update Master Checklist Item 26
```

### Phase 1: Preflight Verification & Deterministic Sweep Engine
- **Task 1.1 — Substrate Invariance Preflight**:
  - Check SHA256 hashes of all 10 protected core substrates.
- **Task 1.2 — Standalone Sweep Runner (`scripts/run_issue26_hyperparameter_sensitivity.py`)**:
  - Load `dataset_20k_cap/terra_eeg_index_20k.json`, `terra_350_benchmark.json`, and `terra_baselines_eval_raw.json`.
  - Extract the 241 frozen context-derived seed anchors from `terra_baselines_eval_raw.json`.
  - Implement deterministic traversal algorithm parameterized by $(d, C, \text{seeds})$:
    - Queue initialization with designated seeds.
    - BFS expansion with hub-degree check ($> C$) using deterministic integer caps $(\text{int}(1.5 C), \text{int}(0.5 C))$.
    - Context generation producing `context_full`.
  - Execute the 22 configurations across all 100 Category B queries.
  - **Execute Multi-Tier Canonical Parity Gate**:
    1. Complete Node-ID Set Equality: $U_{\text{full}}^{\text{sweep}}(q) == U_{\text{full}}^{\text{baseline}}(q)$ for 100/100 queries.
    2. Traversal Visited Node-ID Set Equality: $U_{\text{traversal}}^{\text{sweep}}(q) == U_{\text{traversal}}^{\text{baseline}}(q)$ for 100/100 queries.
    3. Gold Landmark Node Intersection Equality: $V_{\text{retrieved\_gold}}^{\text{sweep}}(q) == V_{\text{retrieved\_gold}}^{\text{baseline}}(q)$ for 100/100 queries.
    4. Exact Aggregate Metric Parity: 86.1% macro, 86.3% micro, 62.0% full path (37/63, 20/32, 5/5).
  - Serialize complete output to `data/issue26_hyperparameter_sensitivity.json` and human-readable audit log `logs/issue26_hyperparameter_sensitivity.txt`.

### Phase 2: Macro Ledger Generation & CI Consistency
- **Task 2.1 — Define Structured LaTeX Macros (`Paper/generated_stats.tex`)**:
  - Under prefix `\IssueTwentySix*`, export exact numerical values for:
    - Depth sensitivity: `\IssueTwentySixDepthOneMacroNodeRecall`, `\IssueTwentySixDepthOneFullPathRecall`, `\IssueTwentySixDepthOneLatencyMs`, `\IssueTwentySixDepthOneNodes`, `\IssueTwentySixDepthThreeMacroNodeRecall`, `\IssueTwentySixDepthThreeFullPathRecall`, `\IssueTwentySixDepthThreeLatencyMs`, `\IssueTwentySixDepthThreeNodes`
    - Seed counterfactuals: `\IssueTwentySixCounterfactualSeedOneFullPathRecall`, `\IssueTwentySixCounterfactualSeedFourFullPathRecall`, `\IssueTwentySixCounterfactualSeedOneLatencyMs`, `\IssueTwentySixCounterfactualSeedFourLatencyMs`
    - Hub cap sensitivity: `\IssueTwentySixHubCapTwentyFiveFullPathRecall`, `\IssueTwentySixHubCapOneHundredFullPathRecall`
    - Adaptive depth: `\IssueTwentySixAdaptiveMacroNodeRecall`, `\IssueTwentySixAdaptiveFullPathRecall`, `\IssueTwentySixAdaptiveNodes`, `\IssueTwentySixAdaptiveLatencyMs`
- **Task 2.2 — Automated CI Audit**:
  - Run `python Paper/scripts/check_consistency.py --target Paper/` to ensure all macro definitions are valid LaTeX, strictly resolved, and contain zero orphaned literals (4/4 checks PASS).

### Phase 3: Publication Table & Manuscript Integration
- **Task 3.1 — Table XIX Master Architecture (`Paper/tables/table_retrieval_eval.tex`)**:
  - Embed **Panel C: Retrieval Hyperparameter Robustness & Traversal Horizon Sensitivity Grid** into `table_retrieval_eval.tex`.
  - Format with 6 columns matching Panels A & B:
    - `Configuration`: Canonical Baseline, Depth Horizon ($d=1, 2, 3$), Hub Cap ($C=25, 50, 100$), Adaptive Depth ($d_{\text{adapt}}$), Counterfactual Seed Beam ($k=1^\ast, 4^\ast$)
    - `Macro Node Recall` $\uparrow$
    - `Full Path Recall` $\uparrow$
    - `Chain-Length Path Recall (3-Node / 4-Node / 5-Node)`
    - `Mean Visited Nodes`
    - `Mean Latency (ms)` $\downarrow$
  - Include explicit table note:
    *Note: Configurations in Tier 1 (depth horizon, hub degree cap, and adaptive depth) evaluate variations over the frozen context-derived seed anchors. Conditions marked with $^\ast$ represent audit-time counterfactual ablations: $k=1^\ast$ initializes traversal from a single primary anchor to test minimal seed sensitivity; $k=4^\ast$ evaluates expanded vector retrieval under the known Issue #19 taxonomy filter constraint.*
- **Task 3.2 — Author Manuscript Section VI-G Text**:
  - Replace line 917 placeholder in `Paper/main.tex` with:
    `\subsubsection{Retrieval Hyperparameter Robustness and Traversal Horizon Sensitivity}`
  - Discuss:
    1. *Depth Horizon Sensitivity*: Why $d=1$ truncates multi-hop citation lineages, how $d=2$ achieves an empirically favorable balance between recall and context volume, and why $d=3$ yields modest incremental recall gains at substantial graph expansion cost.
    2. *Seed Beam Breadth ($k$)*: The sensitivity of single-seed vs. multi-seed anchoring, reporting $k=1^\ast$ and $k=4^\ast$ transparently as audit-time counterfactuals.
    3. *Hub Degree Thresholds*: Balancing stepping-stone traversal against high-degree hub expansion.
    4. *Adaptive Depth Traversal*: Profiling how dynamic depth assignment performs relative to static depth configurations.
- **Task 3.3 — Synchronize Section VII-B Limitation 17**:
  - Update Limitation 17 to cross-reference Section VI-G, confirming that empirical sensitivity sweeps profile the behavior of the retrieval architecture across parameter horizons.

### Phase 4: Layout Optimization & Hard 35-Page Budget Verification
- **Task 4.1 — Local Whitespace Absorption**:
  - Absorb all added text in Section VI-G and Panel C in Table XIX locally on Pages 27–31 using compact list formatting and local `\enlargethispage` adjustments.
  - Verify that Section VII (Discussion) begins cleanly at the top of Page 32.
- **Task 4.2 — Tectonic Compilation & Verification**:
  - Compile with Tectonic: `.\scratch\tectonic\tectonic.exe --keep-intermediates Paper/main.tex`.
  - Assert strictly 35 pages (`assert len(pypdf.PdfReader('Paper/main.pdf').pages) == 35`).
  - Verify 0 undefined references (`??`), 0 undefined citations (`[?]`), and confirm that all 27 references terminate cleanly on Page 35.

### Phase 5: Distribution Packaging, Master Checklist, & Closeout
- **Task 5.1 — Overleaf Distribution Sync**:
  - Re-run `Paper/scripts/package_overleaf_bundle.py`.
  - Copy to root `TERRA_Overleaf_Bundle.zip` and verify bit-identical SHA256 checksums.
- **Task 5.2 — Reproducibility Package & External Manifest**:
  - Rebuild `TERRA_Reproducibility_Bundle.zip` incorporating `scripts/run_issue26_hyperparameter_sensitivity.py` and `data/issue26_hyperparameter_sensitivity.json`.
  - Adhere to the non-self-referential hashing policy: write outer ZIP hash to `logs/issue26_reproducibility_manifest.json` and external closeout log `logs/issue26_closeout.txt`.
  - Verify extraction and SHA256 matches of all constituent files.
- **Task 5.3 — Master Checklist Update**:
  - Update Issue #26 in `TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md` to **COMPLETE — AUDIT VERIFIED**.

---

## 5. Verification Gates Summary

| Gate # | Objective | Verification Target | Success Criteria |
| :---: | :--- | :--- | :--- |
| **G1** | **Protected Substrates** | Checksum verification of 10 core files | 10/10 Bit-Invariant matches |
| **G2** | **Multi-Tier Parity Gate** | Complete node-ID set + traversal set + gold intersection | 100/100 $U_{\text{full}}$ matches; 100/100 $U_{\text{traversal}}$ matches; 100/100 $V_{\text{retrieved\_gold}}$ matches; 86.1%/62% aggregate match |
| **G3** | **Macro Resolution CI** | `python Paper/scripts/check_consistency.py --target Paper/` | 4/4 CHECKS PASSED; 0 orphaned literals |
| **G4** | **PDF Compilation & Page Budget** | `tectonic.exe` + `pypdf` page assertion | **Strictly 35 pages**; 0 undefined refs/cites |
| **G5** | **Overleaf Sync** | `Paper/overleaf_bundle.zip` vs. `TERRA_Overleaf_Bundle.zip` | Bit-identical SHA256 |
| **G6** | **Reproducibility Manifest** | `logs/issue26_reproducibility_manifest.json` | Non-self-referential outer ZIP hash; byte-identical closeout |

---

## 6. Execution Safeguards & Stop Condition

1. **Zero Premature Modification**: Datasets, baseline evaluations, and protected substrates are strictly untouched.
2. **Explicit User Approval Hold**: Execution will begin only upon explicit user command.
