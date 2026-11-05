# Pre-Registration: Component-Level Ablation Design (TERRA Architecture)

- **Document Version:** 1.0 (Frozen Pre-Registration)
- **Date:** 2026-09-05
- **Status:** APPROVED / FROZEN PRIOR TO EXECUTION
- **Target Output File:** `terra_true_ablation_pilot_raw.json`

---

## 1. Objective and Methodological Rationale

The objective of this ablation suite is to isolate the direct causal contribution of each architectural subsystem within TERRA (Temporal-Evolution and Reasoning-Trace RAG) by toggling individual components off while holding all other modules, prompts, embeddings, and generative models strictly invariant.

This experimental design supersedes earlier preliminary drafts that conflated baseline pipelines (`Flat Vector RAG`, `Direct LLM`) with component ablations. Under this pre-registered protocol, every ablation is an exact derivative of the Full TERRA inference engine.

---

## 2. Formal Component Matrix

| Configuration Identifier | Traffic Cop Router | EEG BFS Traversal | ChromaDB Thinking Traces | NLI Smart Grader | Context Formulation & Prompt | Generator LLM & Temp |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Full TERRA (Production)** | **ON** | **ON** ($d=2$) | **ON** ($k=2$) | **ON** ($\tau=0.7$) | Production Prompt | Pinned ($T=0.0$) |
| **True Ablation 1 (w/o EEG)** | **ON** | **OFF** | **ON** ($k=2$) | **ON** ($\tau=0.7$) | Production Prompt | Pinned ($T=0.0$) |
| **True Ablation 2 (w/o NLI)** | **ON** | **ON** ($d=2$) | **ON** ($k=2$) | **OFF** | Production Prompt | Pinned ($T=0.0$) |
| **True Ablation 3 (w/o Router)** | **OFF** (Force Hard) | **ON** ($d=2$) | **ON** ($k=2$) | **ON** ($\tau=0.7$) | Production Prompt | Pinned ($T=0.0$) |

---

## 3. Detailed Component Isolation Specifications

### 3.1 True Ablation 1: w/o EEG Traversal (`disable_eeg_traversal=True`)
* **What is held constant:** The query passes through the Traffic Cop router. Category A queries take the fast path. Complex queries query ChromaDB for semantic thinking traces ($k=2$) filtered to in-domain categories. The retrieved traces are graded by the NLI Smart Grader, and answers are generated using the production generative prompt.
* **What is removed:** Multi-hop BFS citation traversal (`extract_graph_context`) across predecessor and neighbor nodes in the Event Evolution Graph is completely disabled (`structural_context = ""`, `_structural_connections = []`).
* **Distinction from Flat RAG:** Unlike the external `Flat Vector RAG` baseline (which bypasses the router, retrieves raw text chunks without thinking traces, and lacks the NLI grader), Ablation 1 isolates the exact marginal value of topological citation graph connectivity over vector-only thinking trace retrieval.

### 3.2 True Ablation 2: w/o NLI Smart Grader (`disable_nli_grader=True`)
* **What is held constant:** The query passes through the Traffic Cop router, queries ChromaDB for thinking traces, expands multi-hop citations via the EEG graph ($d=2$), and constructs the full structured chronological context. Generation uses the production generative prompt.
* **What is removed:** The autonomous NLI entailment gate (`smart_grader`) and the dynamic self-correction expansion loop are disabled. The engine unconditionally sets `context_is_valid = True`, never issues a safety refusal, and generates directly from the assembled context.
* **Distinction from Direct LLM:** Unlike `Direct LLM` (which operates with zero retrieval context), Ablation 2 provides the generator with complete graph and trace context but removes the verification firewall. This isolates the exact contribution of the NLI gate in preventing adversarial hallucination and rejecting out-of-domain deception.

### 3.3 True Ablation 3: w/o Traffic Cop Router (`force_hard_path=True`)
* **What is held constant:** All retrieval, graph expansion, NLI grading, and generation mechanisms operate in full production mode.
* **What is modified:** The SLM complexity router is bypassed. **Every query**, including single-point factual lookups (Category A) and out-of-context queries (Category C/D), is forced into Path B (vector retrieval + BFS graph expansion + NLI grading).
* **Investigation of Category C and D under Forced Hard Path:**
  - *Headline latency motivation (Category A):* Isolates the exact latency speedup delivered by fast-routing simple factual queries directly to generation without launching multi-hop BFS graph searches.
  - *Defensive firewall hypothesis (Categories C & D):* In Full TERRA, out-of-scope or unconstitutional queries are often flagged early by the router's domain classification. Under `force_hard_path=True`, these queries are forcibly injected into vector retrieval and EEG graph expansion. This reveals whether spurious nearest-neighbor embeddings from unrelated SCOTUS precedents create context pollution that degrades downstream NLI rejection accuracy, or whether the NLI grader alone is resilient enough to maintain safe rejection even after aggressive retrieval.
  - *Category B Invariance Assertion:* Because Category B queries naturally require Path B in Full TERRA, forcing Path B for Category B under Ablation 3 serves as an internal consistency check (Ablation 3 Cat B metrics should show no significant difference from Full TERRA Cat B).

---

## 4. Evaluation Metrics and Per-Category Hypotheses

For each configuration across the 35 benchmark queries ($N=5$ repeated runs, 700 total evaluations), all metrics are logged and reported with **per-category breakdowns** rather than only aggregate summaries:

1. **Category A (Single-Point Factual, 10 queries):**
   - **Median & P95 Total Latency (ms):** Measures the operational speedup delivered by the router ($T_{\text{hard}} - T_{\text{fast}}$).
   - **Stage Latency (ms):** Profiling `routing_ms`, `retrieval_ms`, `grading_ms`, `generation_ms`.
   - **False Refusal Count & Rate:** Verifies that fast routing does not sacrifice factual recall or trigger unwarranted refusals.

2. **Category B (Multi-Hop Evolutionary, 10 queries):**
   - **Faithfulness ($0.0$--$1.0$):** Scored by decoupled LLaMA 3.3 70B judge. Tests the hypothesis that EEG topological context significantly improves multi-hop synthesis over vector-only traces (Ablation 1 vs. Full TERRA).
   - **ROUGE-L Recall:** Lexical alignment against human reference precedent trajectories.

3. **Category C (Out-of-Context, 10 queries):**
   - **Safety Rejection Rate (%):** Interception accuracy of out-of-domain queries. Tests whether bypassing the router (Ablation 3) or removing NLI (Ablation 2) induces hallucinated compliance on non-SCOTUS subjects.

4. **Category D (Adversarial Deception Traps, 5 queries):**
   - **Safety Rejection Rate (%):** Interception accuracy when prompted to apply overruled precedents (e.g., *Plessy* separate-but-equal). Directly isolates the safety contribution of the NLI Grader (Ablation 2) and tests whether the Router (Ablation 3) aids adversarial defense.

5. **Positive Regression Check:**
   - Pre-registered assertion that Full TERRA with default flags produces 100% byte-for-byte or deterministic parity with the pre-ablation baseline implementation on identical seeds and prompts.

---

## 5. Artifact and Data Provenance

1. **Output Raw Log:** `terra_true_ablation_pilot_raw.json`
2. **Integrity Rule:** SHA256 checksum computed immediately upon completion and registered in `Paper/audit/data_inventory.md` and `Paper/audit/canonical_run.md`.
3. **Manuscript Propagation:** Macro generator `Paper/scripts/generate_stats.py` will ingest `terra_true_ablation_pilot_raw.json` directly to emit Table III macros (`\AblationFull...`, `\AblationOne...`, `\AblationTwo...`, `\AblationThree...`), ensuring zero hand-typed values in `main.tex`.

---

## 6. Post-Run Empirical Nuance: Router Trade-off Between Latency and Out-of-Context Refusal

The empirical results across the full $N=5$ suite reveal a critical architectural nuance for the manuscript Discussion and Limitations sections:
* **The Classical Narrative:** The router is primarily framed as an operational efficiency mechanism that cuts latency by $4.89\times$ on single-point factual inquiries while remaining safety-neutral.
* **The Empirical Nuance on Category C:** Bypassing the router (Ablation 3) actually **improves** out-of-context (Category C) safety rejection from **40.0% to 80.0%**. When out-of-domain queries are fast-routed to direct generation, they bypass the NLI Smart Grader. When forced into retrieval and graph expansion, the retrieved constitutional precedents have zero entailment with non-legal topics, prompting the NLI Grader to issue a safe refusal.
* **Preserved Architectural Claim:** The router achieves sub-two-second latency on straightforward queries and maintains 100% adversarial defense (Category D), but at the cost of some Category C refusal completeness. This trade-off will be explicitly articulated in the Section VI discussion.

