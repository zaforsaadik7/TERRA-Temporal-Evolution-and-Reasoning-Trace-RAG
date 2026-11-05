# Master Execution Plan: Resolution of Issue #3 (Phases 3 to 5)
## Temporal Parametric Leakage Through the Pretrained Generator

---

### Executive Overview & Scientific Scope

**Issue #3** is a Tier-1 make-or-break issue in the TERRA evaluation framework. Its purpose is to resolve the fundamental scientific question:

> **Whether temporal parametric leakage from the pretrained generator is a plausible confounder of the historical evaluation, and how effectively the TERRA architecture contains such leakage when modern knowledge conflicts with temporally restricted historical evidence.**

This document establishes the end-to-end, foolproof execution specification for completing **Phase 3 (Multi-Pipeline Execution)**, **Phase 4 (Metric Extraction & Dual-Judge Adjudication)**, **Phase 4.5 (Forensic Audit of Critical Slices)**, **The User Gate Review**, and **Phase 5 (Manuscript Integration & Overleaf Synchronization)**.

---

### 1. Preregistered Foundational Audit & Invariants Check

Before initiating Phase 3 execution, all prerequisite assets and invariants from Phases 1, 2, and 2B must be validated as frozen and certified:

| Component | Status | Artifact / Location | Verified Invariants |
|---|:---:|---|---|
| **Probe Dataset ($N=50$)** | **Certified** | [`data/temporal_leakage_probe_50.json`](file:///f:/TERRA%20-Copy/data/temporal_leakage_probe_50.json) | Bimodal sampling ($p_{90} \ge 18$, $p_{50} \le 4$), 0 intermediate degrees; 5 historical cutoffs ($T \in \{1890, 1930, 1950, 1970, 1980\}$); 7 balanced SCOTUS domains; 100% query sanitization ($Q \cap \text{future} = \emptyset$). |
| **Verifier Controls ($N=10$ pairs)** | **Certified** | [`data/temporal_leakage_verifier_controls_10.json`](file:///f:/TERRA%20-Copy/data/temporal_leakage_verifier_controls_10.json) | 10 balanced proposition control pairs ($N=20$ evaluations); aligned to canonical domains; VP-10 aligned to *U.S. v. Reliable Transfer Co.* (421 U.S. 397). |
| **Temporal Subgraphs ($\mathcal{G}_{\le T}$)** | **Certified** | [`dataset_20k_cap/temporal_subgraphs/`](file:///f:/TERRA%20-Copy/dataset_20k_cap/temporal_subgraphs/) | 5 deterministic subgraphs; universal node provenance ($\text{year} \le T$); universal edge provenance; all future `OVERRULES` edges strictly pruned. |
| **Temporal Vector DB Views** | **Certified** | [`dataset_20k_cap/temporal_vector_db/`](file:///f:/TERRA%20-Copy/dataset_20k_cap/temporal_vector_db/) | 5 isolated ChromaDB collections (`thinking_traces_T1890` through `T1980`); exact embedding parity without re-embedding artifacts. |
| **Temporal Cleanliness Audit** | **Certified** | [`scratch/temporal_integrity_audit_report.json`](file:///f:/TERRA%20-Copy/scratch/temporal_integrity_audit_report.json) | 0 violations across 6 dimensions (nodes, edges, overrulings, holding text, vector docs, two-layer trace audit). |
| **Canonical Verifier Probe** | **Certified** | [`scratch/temporal_leakage_verifier_audit.json`](file:///f:/TERRA%20-Copy/scratch/temporal_leakage_verifier_audit.json) | $\hat{P}(\text{ENTAILED} \mid \text{absent}) = 0.0\%$ (0/10); $\hat{P}(\text{ENTAILED} \mid \text{present}) = 100.0\%$ (10/10); overall accuracy 100%, F1 = 1.000. |

> [!IMPORTANT]
> **Zero-Out-Edge Probe User Mandate**:
> The six foundational early-corpus probes (`TLP-05`, `TLP-08`, `TLP-09`, `TLP-10`, `TLP-19`, `TLP-20` — targeting cases decided between 1857 and 1905, evaluated at $T=1890$ and $T=1930$) have target nodes with zero out-edges in the EEG index due to the machine-citation volume cutoff. As explicitly mandated by the user, these probes are **kept as-is** to reflect the authentic architectural boundaries of the corpus. The methodology section in Phase 5 will include the exact required disclosure text.

---

### 2. Phase 3 Architecture: The Dedicated Multi-Pipeline Runner

#### 2.1 Why `scripts/eval_baselines.py` Cannot Be Used
[`scripts/eval_baselines.py`](file:///f:/TERRA%20-Copy/scripts/eval_baselines.py) is hardcoded for the general 350-query benchmark over the static 1980 corpus (`dataset_20k_cap/vector_db_20k` and `terra_eeg_index_20k.json`). Running the temporal leakage experiment through it is impossible because:
1. It reads `terra_350_benchmark.json`, not `data/temporal_leakage_probe_50.json`.
2. It has no mechanism to switch vector collections or EEG subgraphs per-query based on cutoff year $T$.
3. It does not execute the paired **Condition A** (Default Benchmark Prompt) vs. **Condition B** (Explicit Historical Grounding Instruction).
4. It does not implement **single-candidate caching** with cryptographic identity invariants (`candidate_sha256_ungated == candidate_sha256_gated_input`).
5. It lacks the required explicit NLI gate attribution telemetry (`nli_gate_refusal`, `other_safety_intervention`).

#### 2.2 New Script Specification: `scripts/run_temporal_leakage_phase3.py`
We will construct [`scripts/run_temporal_leakage_phase3.py`](file:///f:/TERRA%20-Copy/scripts/run_temporal_leakage_phase3.py) as a dedicated, fully self-contained execution script adhering to the following specifications:

```
                                  Query q_i (Cutoff T)
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
          Condition A (Default)                         Condition B (Explicit Pre-T)
                    │                                             │
      ┌─────────────┼─────────────┐                 ┌─────────────┼─────────────┐
      ▼             ▼             ▼                 ▼             ▼             ▼
  Direct LLM    Flat Vector     TERRA           Direct LLM    Flat Vector     TERRA
  (No RAG)      (T-Scoped VDB)  (G_<=T & VDB_T) (No RAG)      (T-Scoped VDB)  (G_<=T & VDB_T)
   [1 Gen]        [1 Gen]         │              [1 Gen]        [1 Gen]         │
                                  ▼                                             ▼
                            Candidate y_cand                              Candidate y_cand
                             (1 Gen Call)                                  (1 Gen Call)
                             SHA256 Stored                                 SHA256 Stored
                                  │                                             │
                    ┌─────────────┴─────────────┐                 ┌─────────────┴─────────────┐
                    ▼                           ▼                 ▼                           ▼
               Ungated Out                 NLI Gate                  Ungated Out                 NLI Gate
               y_ungated = y_cand          Evaluation                y_ungated = y_cand          Evaluation
                                                │                                                 │
                                       ┌────────┴────────┐                               ┌────────┴────────┐
                                       ▼                 ▼                               ▼                 ▼
                                    Entailed         Not Entailed                     Entailed         Not Entailed
                                  y_gated = y_cand   y_gated = Refusal              y_gated = y_cand   y_gated = Refusal
```

#### 2.3 Execution Accounting & API Call Budget
The execution strictly enforces the single-candidate design to eliminate generation jitter between gated and ungated variants:

- **Condition A**:
  - Direct LLM: 50 calls
  - Flat Vector RAG: 50 calls
  - TERRA Candidate Generation: 50 calls (yields 50 Ungated + 50 Gated instances)
  - Subtotal: **150 generator API calls** $\to$ 200 evaluated instances
- **Condition B**:
  - Direct LLM: 50 calls
  - Flat Vector RAG: 50 calls
  - TERRA Candidate Generation: 50 calls (yields 50 Ungated + 50 Gated instances)
  - Subtotal: **150 generator API calls** $\to$ 200 evaluated instances
- **Total Generator Calls**: Exactly **300 API calls** producing **400 evaluated response instances**.
- **NLI Gate Calls**: 100 verifier evaluations on TERRA candidates (50 Condition A + 50 Condition B).

#### 2.4 Dynamic Horizon Context-Switching Protocol (Option A)
For each query $q$ with cutoff year $T \in \{1890, 1930, 1950, 1970, 1980\}$:
1. **Subgraph Context**: The runner dynamically binds the active graph traversal (`ask_terra.eeg`) to [`dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T{T}.json`](file:///f:/TERRA%20-Copy/dataset_20k_cap/temporal_subgraphs/).
2. **Vector View (Option A Direct Collection Injection)**: Rather than attempting to rebind `ask_terra.chroma_client` (which points to the 1980 corpus `./dataset_20k_cap/vector_db_20k`), `TemporalHorizonContext` connects directly to the separate persistent store [`dataset_20k_cap/temporal_vector_db`](file:///f:/TERRA%20-Copy/dataset_20k_cap/temporal_vector_db) via an isolated client and injects the collection object `thinking_traces_T{T}` directly into `ask_terra.collection`.
3. **Hard Provenance Assertion**:
   ```python
   # Dynamic runtime assertion on retrieved evidence
   for doc_meta in retrieved_metadatas:
       doc_year = extract_year(doc_meta.get("date", ""))
       assert doc_year <= T, f"Temporal violation: doc year {doc_year} > cutoff {T}"
   ```

#### 2.5 Condition Prompts
- **Condition A (Default Benchmark Prompt)**:
  - Direct LLM: Standard neutral legal query prompt (`"User Legal Query: {query_text}\n\nAnswer:"`).
  - Flat Vector RAG: Standard neutral RAG prompt using top-2 retrieved traces from `thinking_traces_T{T}`.
  - TERRA: Standard TERRA traversal and synthesis prompt over $\mathcal{G}_{\le T}$ and `thinking_traces_T{T}`.
- **Condition B (Explicit Temporal Grounding Prompt)**:
  - Direct LLM: Explicit historical restriction (`"You are an expert legal historian. Answer the following question strictly as of the year {T}, reflecting only the legal precedents and constitutional jurisprudence established at or before {T}. Do NOT mention, apply, or rely upon any decisions, statutes, or doctrines decided after {T}."`).
  - Flat Vector & TERRA: Augmented prompt instructing the model that the inquiry is strictly bounded to the legal state at year $T$, requiring grounding strictly in the provided pre-$T$ record.

#### 2.6 Cryptographic Pairing & Attribution Invariants
Every execution record in [`scratch/temporal_leakage_eval_raw.json`](file:///f:/TERRA%20-Copy/scratch/temporal_leakage_eval_raw.json) will contain:
```json
{
  "query_id": "TLP-01",
  "cutoff_year": 1890,
  "condition": "Condition_A",
  "pipeline": "5_TERRA_gated",
  "prompt_sha256": "...",
  "retrieval_context_sha256": "...",
  "candidate_sha256": "...",
  "candidate_generated": true,
  "nli_gate_evaluated": true,
  "nli_gate_passed": true,
  "nli_gate_refusal": false,
  "other_safety_intervention": false,
  "final_action": "release",
  "answer_full": "...",
  "context_full": "..."
}
```
**Runtime Assertion**:
`assert rec_ungated["candidate_sha256"] == rec_gated["candidate_sha256"]`

---

### 3. Phase 4: Metric Extraction, Dual-Judge Adjudication & Statistical Analysis

Once all 400 response records are stored in `scratch/temporal_leakage_eval_raw.json`, Phase 4 processes them through the preregistered evaluation pipeline:

#### 3.1 Lexical & Entity Diagnostics
Automated extraction of explicit temporal intrusion:
- **PCMR (Post-$T$ Case Mention Rate)**: Automated regex scanning of `answer_full` for any case names listed in `future_case_names`.
- **PYAR (Post-$T$ Year Reference Rate)**: Automated regex scanning of `answer_full` for calendar years $> T$.

#### 3.2 Dual-Judge Adjudication Protocol
Two independent model-based judges (`databricks-qwen3-next-80b-a3b-instruct` and `databricks-gpt-oss-120b`) evaluate each response under blinded conditions:

1. **Severity Classification (Level 0 / 1 / 2)**:
   - **Level 0 (Clean)**: No post-$T$ legal reliance or mention.
   - **Level 1 (Mention / Non-Prejudicial Note)**: Mentions subsequent history in a historical disclaimer but grounds operative answer strictly in pre-$T$ law.
   - **Level 2 (Substantive Leakage - Primary Metric SPTLR)**: Operative legal conclusion relies upon, projects, or asserts post-$T$ doctrine as controlling law.
2. **Temporal Grounding Score (TGS 1–5)**:
   - Evaluates adherence to contemporaneous historical legal doctrine.
   - Inter-rater agreement reported as **quadratic weighted Cohen's $\kappa$** and **Spearman's $\rho$**.
3. **Historical Legal Correctness Rate (HLCR)**:
   - Evaluates whether the pre-$T$ answer accurately captures historical doctrine via `required_historical_elements` and `forbidden_future_elements`.
   - **Refusal Decoupling**: Explicit NLI safety refusals are logged as `Safe Refusal` and are not credited as substantive doctrine, preventing artificial score inflation.
4. **Disagreement Adjudication**:
   - Automated keyword diagnostic filter acts as first tie-breaker.
   - Any unresolved discrepancy is reviewed under the preregistered rubric prior to experimental unblinding.

#### 3.3 Statistical Hypothesis Testing Suite
Implemented in `scripts/analyze_temporal_leakage_results.py`:

- **Primary Confirmatory Hypothesis ($H_1$)**:
  $$H_1: \text{SPTLR}(\text{TERRA}_{\text{gated}}, A) < \text{SPTLR}(\text{Flat Vector RAG}, A)$$
  Tested using a **one-sided paired McNemar exact test** at $\alpha = 0.05$.
- **Secondary Hypothesis Family ($H_2$–$H_6$)**:
  - $H_2$: $\text{SPTLR}(\text{TERRA}_{\text{gated}}, A) < \text{SPTLR}(\text{Direct LLM}, A)$
  - $H_3$: $\text{SPTLR}(\text{TERRA}_{\text{gated}}, B) < \text{SPTLR}(\text{Flat Vector RAG}, B)$
  - $H_4$: $\text{SPTLR}(\text{TERRA}_{\text{gated}}, B) < \text{SPTLR}(\text{Direct LLM}, B)$
  - $H_5$: $\text{SPTLR}(\text{TERRA}_{\text{gated}}, A) < \text{SPTLR}(\text{TERRA}_{\text{ungated}}, A)$
  - $H_6$: $\text{SPTLR}(\text{TERRA}_{\text{gated}}, B) < \text{SPTLR}(\text{TERRA}_{\text{ungated}}, B)$
  - Controlled for Family-Wise Error Rate (FWER) at $\alpha = 0.05$ using the **Holm step-down procedure**.
- **Confidence Intervals**:
  - 10,000-resample paired query-level bootstrap over the 50 queries to compute 95% CIs on paired difference $\Delta$.
- **NGLIR & NE Rule**:
  - Computed on denominator $D = \{i : \hat{y}_{i, \text{ungated}} \text{ exhibits Level-2 leakage} \land \text{candidate\_generated} \land \text{nli\_gate\_evaluated}\}$.
  - If $|D| = 0$, reported as **Not Estimable (NE)**.

---

### 4. Phase 4.5: Forensic Audit of Critical Slices

Prior to presenting findings, an automated script [`scripts/audit_temporal_leakage_forensics.py`](file:///f:/TERRA%20-Copy/scripts/audit_temporal_leakage_forensics.py) will generate [`scratch/temporal_leakage_forensic_audit.json`](file:///f:/TERRA%20-Copy/scratch/temporal_leakage_forensic_audit.json):
1. **100% Audit of Level-2 Substantive Leakage**: Complete excerpt and rationale for every response classified as Level-2 across all pipelines.
2. **100% Audit of NLI Interceptions**: Complete trace of candidate text vs. gated refusal for every query where the NLI gate intervened.
3. **20% Stratified Sample of Level-0 Clean Outputs**: Verification of false-negative absence.

---

### 5. [GATE REVIEW] Stop & User Inspection Protocol

> [!CAUTION]
> **MANDATORY HARD STOP**:
> No manuscript files (`Paper/*.tex`, `Paper/tables/*.tex`) or Overleaf bundles will be touched during Phases 3 or 4.
> Execution halts completely at the Gate Review. We will report:
> 1. The full empirical results table (matching Table XII specification).
> 2. Primary McNemar $p$-value and secondary Holm-adjusted $p$-values.
> 3. Dual-judge inter-rater reliability metrics ($\kappa$, $\rho$).
> 4. Detailed breakdown of any Level-2 leakage cases and NLI gate interventions.
> 
> **We will wait for your explicit approval before proceeding to Phase 5.**

---

### 6. Phase 5: Manuscript Integration & Overleaf Bundle Synchronization

Upon receiving explicit user approval at the Gate Review, Phase 5 will be executed as follows:

#### 6.1 Target 1: Methodology Disclosure (User-Mandated Wording)
In [`Paper/sections/03_system_architecture.tex`](file:///f:/TERRA%20-Copy/Paper/sections/03_system_architecture.tex) (or [`Paper/sections/06_experiments.tex`](file:///f:/TERRA%20-Copy/Paper/sections/06_experiments.tex)):
Insert the exact mandated sentence:
> *"Six probes (12%) targeting historical cases decided between 1857 and 1905 (evaluated at cutoffs T=1890 and T=1930) have target nodes with zero out-edges in the EEG due to the corpus citation-parsing boundary. Arc evolution cases for these entries are historically verified against primary legal sources but are not EEG graph edges. All leakage metrics are computed identically across all 50 probes regardless of arc status."*

#### 6.2 Target 2: Section III-B-3 ("Temporal Parametric Containment Firewall")
Formalize the temporal containment firewall in [`Paper/sections/03_system_architecture.tex`](file:///f:/TERRA%20-Copy/Paper/sections/03_system_architecture.tex) using the preregistered text.

#### 6.3 Target 3: Table XII Generation & Section VI-F Narrative
- Generate [`Paper/tables/table_temporal_leakage_probe.tex`](file:///f:/TERRA%20-Copy/Paper/tables/table_temporal_leakage_probe.tex) populated with live empirical metrics.
- Embed in [`Paper/sections/06_experiments.tex`](file:///f:/TERRA%20-Copy/Paper/sections/06_experiments.tex) with detailed experimental narrative.

#### 6.4 Target 4: Section VII-B Limitation 6
Update Limitation 6 in [`Paper/sections/07_discussion.tex`](file:///f:/TERRA%20-Copy/Paper/sections/07_discussion.tex) articulating the distinction between latent parametric weights and operative doctrinal leakage.

#### 6.5 Target 5: CI Integrity & Master Checklists
- Run [`Paper/scripts/check_consistency.py`](file:///f:/TERRA%20-Copy/Paper/scripts/check_consistency.py) $\to$ verify **4/4 PASS**.
- Compile PDF via Tectonic $\to$ verify 0 broken references (`??`).
- Run [`Paper/scripts/package_overleaf_bundle.py`](file:///f:/TERRA%20-Copy/Paper/scripts/package_overleaf_bundle.py) $\to$ synchronize Overleaf bundles.
- Update [`TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md`](file:///f:/TERRA%20-Copy/TERRA_43_ISSUES_MASTER_CHECKLIST_new%20ones%20added.md) and [`TERRA_40_ISSUES_MASTER_CHECKLIST.md`](file:///f:/TERRA%20-Copy/TERRA_40_ISSUES_MASTER_CHECKLIST.md) to `[x] **RESOLVED & VERIFIED**`.

---

### 7. Step-by-Step Implementation Sequence & Verification Gates

```
Step 1: Build Dedicated Phase 3 Runner
  └─ Create scripts/run_temporal_leakage_phase3.py
  └─ Smoke-test on 2 queries (1 High, 1 Lower) to verify T-switching & SHA256 invariants

Step 2: Full Phase 3 Execution
  └─ Run 50 queries x 2 conditions across all pipelines (300 generator calls)
  └─ Continuous atomic checkpointing to scratch/temporal_leakage_eval_raw.json

Step 3: Phase 4 Metrics & Dual-Judge Evaluation
  └─ Create & run scripts/adjudicate_temporal_leakage.py
  └─ Dual judges (qwen3-80b & gpt-oss-120b) score all 400 instances
  └─ Run scripts/analyze_temporal_leakage_results.py (McNemar, Holm, Bootstrap, Kappa)

Step 4: Phase 4.5 Forensic Audit
  └─ Run scripts/audit_temporal_leakage_forensics.py
  └─ Inspect all Level-2 cases, NLI interventions, and clean slices

Step 5: [GATE REVIEW CHECKPOINT]
  └─ Present complete results and forensic tables to user
  └─ HALT AND WAIT FOR USER APPROVAL

Step 6: Phase 5 Manuscript Updates (Post-Approval Only)
  └─ Add mandated zero-out-edge sentence
  └─ Embed Table XII and update sections 03, 06, 07
  └─ Run CI (4/4 PASS), compile PDF, package Overleaf bundle, update master checklists
```
