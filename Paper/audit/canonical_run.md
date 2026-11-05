# Canonical Benchmark Run Definition & Freezing (Pre-Phase-1)

**Status:** Frozen  
**Date:** 2026-09-05  

---

## 1. Primary Canonical Evaluation Run (Expanded 140x3)

The primary canonical evaluation run provides the empirical basis for all main benchmark results, statistical significance testing, ROUGE-L lexical recall, word counts, and latency distributions reported in the manuscript.

### Raw Data Files & Checksums
- **Evaluation Log**: `terra_expanded_eval_raw.json`
  - **SHA256**: `01ead3707bdae0c2bb9d158c4970ad06aa3a956c413bfcd494bd80430d860932`
  - **Record Count**: 1,260 inferences
  - **Queries**: 140 unique constitutional law queries
  - **Repeated Runs**: $N = 3$ passes per query-pipeline pair
  - **Pipelines**: 
    - `1_Direct_LLM` (420 records)
    - `2_Flat_RAG` (420 records)
    - `3_TERRA_GraphRAG` (420 records)
  - **Categories**:
    - `A_Factual` (Single-point lookups, 360 records)
    - `B_Evolutionary` (Multi-hop chronological precedent tracking, 360 records)
    - `C_OutOfContext` (Jurisdictional boundary testing, 360 records)
    - `D_Adversarial` (Adversarial legal traps, 180 records)
- **Generations File**: `terra_expanded_generations.json`
  - **SHA256**: `19d725f03b8db9d8a12bddcaef0a97ea64aca659cf88b652e643c97c9b508439`

### Serving & Model Specifications
- **Generator Model**: `meta-llama/Llama-3.3-70B-Instruct` (served via Databricks Model Serving, deterministic inference at temperature $T = 0.0$).
- **LLM Judge**: `meta-llama/Llama-3.3-70B-Instruct` (evaluating on a continuous Likert scale $[0.0, 1.0]$ with chain-of-thought natural language rationale extraction).
- **Execution Script**: `eval_terra_expanded.py`

---

## 2. Component Ablation Study (Option A: True Component Ablations)

The 35-query ablation suite isolates the direct causal contribution of each architectural subsystem within TERRA by toggling components off while holding all other modules, embeddings, and models invariant:
1. **Full TERRA:** Complete production architecture (Router + EEG + Traces + NLI).
2. **Ablation 1 (w/o EEG):** Router + Traces + NLI (isolates topological citation BFS traversal).
3. **Ablation 2 (w/o NLI):** Router + EEG + Traces (isolates NLI semantic entailment verification gate).
4. **Ablation 3 (w/o Router):** Forced Hard Path (isolates Traffic Cop operational triage and latency reduction).

### Raw Data Files & Checksums
- **True Component Ablation Evaluation Log**: `terra_true_ablation_pilot_raw.json`
  - **SHA256**: `236bff516e5b36fefd9dcb62be81e791f8d06f7ffefc44731c9f816f7fbae2bb`
  - **Record Count**: 700 inferences (35 queries $\times$ 4 configurations $\times$ 5 repeated runs)
  - **Judge Model**: `meta-llama/Llama-3.3-70B-Instruct` (decoupled critic judge)
- **True Component Ablation Generations**: `terra_true_ablation_pilot_generations.json`
  - **SHA256**: `d59d7b999074f3859b97ea3274d46bb522f38cc47f23c9b1b4bda0fe13d47f4b`
- **Preliminary Pilot Dataset (Archived)**: `terra_eval_raw_baseline_35x5.json` (SHA256: `2bf73bd28f64227d2d8b92c19ea71445bb8e5599ad7f1d594b92838c314b2704`)

---

## 3. Corpus & Citation Graph Index

The Event Evolution Graph index serves as the underlying structural citation graph:
- **Corpus Index**: `dataset_10k_cap/terra_eeg_index_10k.json`
  - **SHA256**: `a6da204eadcd0d39ecb61354bb256668ef6dedc385c265e917bfb90c2eb97901`
  - **Nodes**: 10,009 SCOTUS opinions
  - **Edges**: 37,918 unique directed citation edges
  - **Graph Density**: $\rho = 0.000379$
  - **Average Degree**: $\langle k \rangle = 3.7884$
  - **Average Clustering**: $C = 0.1634$
