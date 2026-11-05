# TERRA Paper Audit & Single Source of Truth Architecture

This directory enforces that **every single number reported in the TERRA manuscript (`Paper/main.tex`) is derived from a verified, regenerable raw data source via automated LaTeX macros**.

---

## 1. Directory Structure

- `data_inventory.md`: Complete catalog of all telemetry files, raw evaluation logs, and script outputs in the repository with sizes and SHA256 checksums.
- `canonical_run.md`: Technical specification of the frozen canonical run (expanded 140x3) and the pilot ablation subset (35x5).
- `archive/`:
  - `pilot_35query_525eval/`: Archived copies and documentation of the 35-query pilot ablation subset.
  - `expanded_140query_1260eval/`: Archived copies and documentation of the canonical 140-query evaluation set.

---

## 2. The Three-Tier Number Architecture

To eliminate all unverified numbers and prevent manual copy-paste errors:

1. **Benchmark Evaluation Statistics** (Faithfulness, ROUGE-L, win rates, p-values, effect sizes, latencies, power, sample sizes):
   - **Generator**: `Paper/scripts/generate_stats.py`
   - **Output**: `Paper/generated_stats.tex`
   - **Source**: `terra_expanded_eval_raw.json` & `terra_eval_raw_baseline_35x5.json`

2. **Corpus Topology & Graph Metrics** (Opinion counts, directed edges, graph density, clustering coefficient, components):
   - **Generator**: `Paper/scripts/generate_corpus_stats.py`
   - **Output**: `Paper/generated_corpus_stats.tex`
   - **Source**: `dataset_10k_cap/terra_eeg_index_10k.json`

3. **Architectural Hyperparameters & Config Constants** (Fixed design parameters like $T=0.0$, $k=2$, $dL_2 < 1.3$, $\alpha=0.05$):
   - **Whitelist**: `Paper/scripts/allowed_literals.txt`
   - Checked strictly by `Paper/scripts/check_consistency.py`.

---

## 3. Two-Dataset Protocol

- **Primary Canonical Benchmark (140 queries $\times$ 3 runs = 1,260 evaluations)**: All main claims, Table VI (comprehensive breakdown), Table V (ROUGE-L and word counts), Table VII (latencies), Table VIII (statistical significance and power), Abstract, Introduction, and Conclusion numbers MUST come from this dataset.
- **Pilot Ablation Subset (35 queries $\times$ 5 runs = 525 evaluations)**: Exclusively scoped to Table III (Component-Level Ablation Analysis) to isolate the causal contributions of EEG traversal, NLI entailment grading, and Traffic Cop routing.
