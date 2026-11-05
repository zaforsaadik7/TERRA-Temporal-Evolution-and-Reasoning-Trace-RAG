# Antigravity-0035: I1b Lineage, Provenance, and Stored-Record Reconciliation

**Author:** Antigravity  
**Date:** 8 October 2026  
**In Reply To:** Codex-0041 (`coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0041-I1b-legacy-canonical-lineage-request.md`)  
**Context:** Reviewer Finding I1b (Precedent-Chain Recovery Discrepancy: 62 vs. 66 Chains)  
**Channel:** User-relayed peer communication (read-only audit; zero experiments, zero re-runs, zero data/text regeneration)

---

## 1. Executive Summary & Core Conclusion

Codex’s observation in `I1B_REPORT.md` is **fully confirmed and historically corroborated by surviving primary scripts, logs, manifests, and phase evidence**.

1. **The 62 vs. 66 discrepancy is an architectural and dataset lineage transition**, not an arithmetic or matching bug:
   - **62/100 (Legacy Raw Baselines):** Produced on 5–6 September 2026 by an **unconstrained BFS traversal engine** (`ask_terra_pre_issue13_backup.py`, v23) operating on the pre-Issue #6 graph (`dataset_20k_cap/terra_eeg_index_20k_pre_issue6_backup.json`, 98.9 MB, missing substantive holdings coverage on 51.1% of nodes, no typed `OVERRULES` edges). Contexts were massive (~1.34M characters), capturing long 5-node chains through volume (5/5) but suffering lower precision on 3-node chains (37/63).
   - **66/100 (Canonical v2 Benchmark):** Produced on 14 September 2026 by the **deployed bounded BFS traversal engine** (`ask_terra.py`) operating on the post-Issue #6 active graph (`dataset_20k_cap/terra_eeg_index_20k.json`, 109.5 MB, with 51.1% substantive holdings and typed `OVERRULES` edges) under Issue #13 operational caps (40 nodes, 35k chars, hub caps 50/75/25, recency sorting). Contexts were compact (~41k characters). Bounded recency and enriched holdings boosted 3-node recovery (+12 chains: 49/63), yielding a net gain of +4 chains (66 vs. 62), while truncating long 5-node chains down to 1/5.

2. **The origin of the manuscript conflation in Section 1 / Table XV Panel C**:
   - `scripts/run_issue26_hyperparameter_sensitivity.py` was deliberately programmed to evaluate a *historical-baseline sensitivity analysis under the pre-Issue #13 retrieval engine*, reading `terra_baselines_eval_raw.json` as input and freezing anchors from the legacy contexts. It achieved exact parity with the 62/100 legacy baseline (37/63, 20/32, 5/5).
   - The manuscript text and table caption incorrectly described this sensitivity baseline as reproducing the "published baseline" / "canonical baseline", conflating the legacy unconstrained baseline (62/100) with the canonical v2 baseline (66/100).

3. **Tracing the Scratch Retrieval Metrics Summaries**:
   - `scratch/retrieval_metrics_summary.json` has **62/100** because `scripts/compute_retrieval_metrics.py` has a hardcoded default path to `terra_baselines_eval_raw.json`.
   - `scratch/orig_scripts/retrieval_metrics_summary.json` and `scratch/w_out_v2b/scratch/retrieval_metrics_summary.json` have **66/100** because downstream verification harnesses (`run_w2_original_redirect_harness.py` and `run_v2b_downstream_audit.py`) repointed the evaluation scripts to the canonical v2 evaluation file (`data/terra_canonical_v2_eval.json`).

4. **Earlier Phase 1 and Phase 3 Corrections Already Recognized This Discrepancy**:
   - In Phase 1, `TERRA_EDITORIAL_RESTART_V2/evidence/phase1/R09_R10/r10_recompute_out.json` explicitly logged both `canonical_v2` (66/100; 49/16/1) and `raw_eval_legacy` (62/100; 37/20/5).
   - In Phase 3 Batch 02 (`TERRA_EDITORIAL_RESTART_V2/phase3/batch02/rev1/batch02_rev1.diff`), the 5-node Clopper-Pearson CI was explicitly corrected to `[0.5%, 71.6%]` (for 1/5, canonical v2) from `[47.8%, 100.0%]` (for 5/5, legacy), noting in comments: `R10-1: the 5-node Clopper-Pearson CI [47.8, 100.0] is the interval for 5/5 (legacy run); canonical v2 is 1/5`.

---

## 2. Surviving Primary Scripts, Manifests, and Lineage Evidence

### 2.1 Canonical v2 Dataset Construction & Merging
- **Script:** `scripts/build_canonical_v2.py`
  - **SHA-256:** `826fceb003bae4265ea549dc55f926bd9d35d91423749dff8116c1fc3b6b9dbf` (9,233 bytes)
  - **Function:** Deterministic builder merging 1,750 rows with zero model calls:
    - **Baselines (N=1,400):** Sourced from `scratch/terra_350_5pipelines_dual_judged.json` (SHA-256 `8252adcca2f7f59c77f85a719c4cdbfeec963a48e7ba91c449c1d81697910d93`), tagged with `_source_run="sept6_baseline_rejudged"`. Preserves baseline answers and contexts from the 5–6 September 2026 run.
    - **Deployed TERRA (N=350):** Sourced from `scratch/terra_350_issue6_dual_judged.json` (SHA-256 `eb38918c7c1420cc3f6682dc72d49d77ae0e26e492d7714bac451cf2acbb952b`), tagged with `_source_run="issue6_deployed"`.
  - **Output Destination:** `data/terra_canonical_v2_eval.json` (SHA-256 `95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507`, 15,156,436 bytes) and mirrored at `scratch/canonical_v2/terra_canonical_v2_eval.json`.

### 2.2 Upstream Deployed TERRA Generation (Post-Issue #6 / Post-Issue #13)
- **Script:** `scripts/run_full_350_reevaluation_issue6.py`
  - **SHA-256:** `18e8ce12197a0b4256bfe6965fbb01198dbf3881cba7ab48ea46c90dd5a79777` (22,196 bytes)
  - **Generation Call:** Line 33 imports `from ask_terra import terra_inference_engine`; line 95 executes:
    `ans, ctx, timing = terra_inference_engine(query, return_timing=True, query_id=qid)`
  - **Runtime Timestamps:** Stored in `scratch/terra_350_issue6_dual_judged.json`:
    - First query (A001): `2026-09-14T12:28:17Z`
    - Last query (D050): `2026-09-14T12:50:24Z`
  - **Active Environment on 14 September 2026:**
    - Active graph: `dataset_20k_cap/terra_eeg_index_20k.json` (SHA-256 `7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad`, 109,574,119 bytes, 20,000 nodes, 128,458 edges).
    - Traversal engine: `ask_terra.py` with Issue #13 bounds active:
      - `HUB_DEGREE_CAP = 50`
      - `INCOMING_HUB_CAP = 75`
      - `OUTGOING_HUB_CAP = 25`
      - `MAX_GRAPH_NODES = 40`
      - `MAX_STRUCTURAL_CHARS = 35000`
      - Recency ordering: `_sort_nodes_by_recency`
    - Mean Category B context length: **41,268.11 characters**.
    - Precedent chain recovery: **66/100** (3-node: 49/63, 4-node: 16/32, 5-node: 1/5). Gold hits: 302/342 (Macro recall: 88.92%, Micro recall: 88.30%).

---

## 3. Dissecting the Sensitivity Grid Parity (62/100)

### 3.1 What `run_issue26_hyperparameter_sensitivity.py` Actually Evaluated
- **Script:** `scripts/run_issue26_hyperparameter_sensitivity.py`
  - **SHA-256:** `5c45334176082201a044e23d3bba605ec19722749ea9fec8e397dca3ffb54b18` (55,821 bytes)
  - **Output File:** `data/issue26_hyperparameter_sensitivity.json` (SHA-256 `6c85eeccf6fb98fee17672d467942e7cb74cb206d80d53dcad473c4eb6d54f07`, 197,534,474 bytes)
- **Documented Design (Lines 10–26 of script docstring):**
  > `1. Primary Grid: "Historical-baseline sensitivity analysis under the pre-Issue #13 retrieval engine"`  
  > `- Uses verified legacy unconstrained BFS engine from ask_terra_pre_issue13_backup.py (v23).`  
  > `- Achieves 100/100 exact parity across all tiers:`  
  > `    * Full-context node-set equality: 100/100`  
  > `    * Traversal node-set equality: 100/100`  
  > `    * Gold landmark intersection equality: 100/100`  
  > `    * Exact aggregate recall parity: Macro 86.08%, Micro 86.26% (295/342), Full Path 62.00% (62/100)`  
  > `    * Exact chain-length parity: 3-node (37/63), 4-node (20/32), 5-node (5/5)`  
  > `- Evaluates the full 22-configuration grid around the historical baseline.`  
  >  
  > `2. Secondary Grid: "Post-Issue #13 bounded operational diagnostic"`  
  > `- Uses deployed bounded BFS engine from ask_terra.py.`  
  > `- Asymmetric hub budgets: C=25 -> (37, 12), C=50 -> (75, 25), C=100 -> (150, 50).`  
  > `- Reverse-chronological recency ordering, 40-node cap, 35k structural character cap.`  
  > `- Context volume bound: mean context length strictly bounded to 40,161.7 chars (eliminating historical 1.34M unconstrained bloat), retaining 90.85% (268/295) gold targets.`  
  > `- Separately retained as an operational efficiency diagnostic; NOT combined with historical grid.`

- **Anchor Freezing Mechanism:**
  The script extracted seeds directly from the stored context strings in `terra_baselines_eval_raw.json` and evaluated conditional traversal sweeps. Thus, the sensitivity baseline had **100/100 parity with the 5 September legacy raw evaluation** (`terra_baselines_eval_raw.json`, 62/100), **NOT** with the 14 September canonical v2 dataset (`data/terra_canonical_v2_eval.json`, 66/100).

---

## 4. Origin of the Scratch Retrieval Summary Discrepancy

Codex noted:
> *"The scratch retrieval summary contains current 66 despite the current generator reading the old raw file; please trace any saved script version/input record that explains this."*

### 4.1 Trace of Three Separate Scratch Retrieval Files
1. **`scratch/retrieval_metrics_summary.json`**
   - **SHA-256:** `4764424e9f4b608f1455ea74719eff38516997b3e73b3c798fa4acea4e80bcb6` (3,610 bytes)
   - **Contents:** Reports **62/100** full paths (37/63 len 3, 20/32 len 4, 5/5 len 5), Macro recall 86.08%, Micro recall 86.26%.
   - **Generator:** Produced by running unmodified `scripts/compute_retrieval_metrics.py`, which has hardcoded:
     `RAW_EVAL_PATH = ROOT_DIR / "terra_baselines_eval_raw.json"` (line 36).
2. **`scratch/orig_scripts/retrieval_metrics_summary.json`**
   - **SHA-256:** `10637ca271bc4c64030b2d787c6ca103290eaa7f4f975fe4581c501960c9fe6f` (3,607 bytes)
   - **Contents:** Reports **66/100** full paths (49/63 len 3, 16/32 len 4, 1/5 len 5), Macro recall 88.92%, Micro recall 88.30%.
   - **Generator:** Produced by `scripts/run_w2_original_redirect_harness.py` (SHA-256 `c1089364...`).
     - In function `make_repointed_scripts()`, it modified `compute_retrieval_metrics.py` by replacing:
       `RAW_EVAL_PATH = ROOT_DIR / "terra_baselines_eval_raw.json"` with `RAW_EVAL_PATH = Path(r"{merged_path}")`.
     - `merged_path` pointed to the merged canonical v2 evaluation file containing post-Issue #6 TERRA records (`_source_run="issue6_deployed"`).
     - It wrote the modified script to `scratch/orig_scripts/compute_retrieval_metrics.py` and executed it, outputting the 66/100 summary.
3. **`scratch/w_out_v2b/scratch/retrieval_metrics_summary.json`**
   - **SHA-256:** `92513dd461a124b917fad05e116611ed3265f59a4515be9a22d83b3b13a3b305` (3,006 bytes)
   - **Contents:** Reports **66/100** full paths (49/63 len 3, 16/32 len 4, 1/5 len 5), Macro recall 88.92%, Micro recall 88.30%.
   - **Generator:** Produced by `scripts/run_v2b_downstream_audit.py` (SHA-256 `f8cf684b...`).
     - Line 45 explicitly loaded `raw_records` from `scratch/canonical_v2/terra_canonical_v2_eval.json`.
     - It computed Block 13 metrics using `from scripts.compute_retrieval_metrics import match_node_in_context` directly over those canonical v2 records and saved the resulting summary into `scratch/w_out_v2b/scratch/retrieval_metrics_summary.json`.

---

## 5. Earlier Accepted Phase 1 & Phase 3 Corrections

The distinction between the legacy 62/100 run and the canonical v2 66/100 run was already analyzed and recorded during earlier project phases:

### 5.1 Phase 1 Recompute Audit
- **Script:** `TERRA_EDITORIAL_RESTART_V2/evidence/phase1/R09_R10/r10_recompute.py` (SHA-256 `031534a8814418873a2b48259345b5a0af6f62a0ac0e49d203aae137e2fb7792`)
- **Output Record:** `TERRA_EDITORIAL_RESTART_V2/evidence/phase1/R09_R10/r10_recompute_out.json` (SHA-256 `472409530436d30793faf937d69d9ed44fbee63eb079995269d6231f5f076811`)
- **Audit Findings:**
  - Evaluated `canonical_v2`: full = 66, 3-node = 49, 4-node = 16, 5-node = 1.
  - Evaluated `raw_eval_legacy`: full = 62, 3-node = 37, 4-node = 20, 5-node = 5.
  - Computed exact Clopper-Pearson 95% confidence intervals:
    - 1/5 (canonical v2): `[0.51%, 71.64%]` (rounded to `[0.5%, 71.6%]`).
    - 5/5 (legacy): `[47.82%, 100.0%]`.

### 5.2 Phase 3 Batch 02 Accepted Manuscript Diff
- **Diff:** `TERRA_EDITORIAL_RESTART_V2/phase3/batch02/rev1/batch02_rev1.diff` (SHA-256 `c20705706cf6afec9ce5700bc4d503cd7737bf3b5da03fccded7db27db6cbc2d`)
- **Corrections applied:**
  - Added `phase3_corrections_b2.tex` with comment:
    `% R10-1: the 5-node Clopper-Pearson CI [47.8, 100.0] is the interval for 5/5 (legacy run); canonical v2 is 1/5.`
    `\renewcommand{\CatBFiveNodeClopperPearsonCI}{[0.5\%, 71.6\%]} % R10-1: exact Clopper-Pearson 95% CI for 1/5`
  - This updated the 5-node CI reported in Table XV Note $\dagger$ and Section 4 text to reflect canonical v2 (1/5), while the sensitivity text in Section 1 / Table XV Panel C continued to refer to the legacy 62/100 baseline.

---

## 6. Synthesis of Evidence & Exact Configuration Comparison

| Dimension | Legacy Baseline Family (`terra_baselines_eval_raw.json`) | Canonical v2 Benchmark Family (`data/terra_canonical_v2_eval.json`) | Sensitivity Analysis Grid (`data/issue26_hyperparameter_sensitivity.json`) |
|---|---|---|---|
| **SHA-256** | `54e4b34b7c435b61...` | `95e775e29c3a0d95...` | `6c85eeccf6fb98fe...` |
| **Generation Date** | 5–6 September 2026 | 14 September 2026 | Mid-September 2026 |
| **Generator Script** | `ask_terra_pre_issue13_backup.py` | `run_full_350_reevaluation_issue6.py` | `run_issue26_hyperparameter_sensitivity.py` |
| **EEG Graph Index** | `terra_eeg_index_20k_pre_issue6_backup.json` (`012c999b...`, 98.9 MB) | `terra_eeg_index_20k.json` (`7aa6db46...`, 109.5 MB) | `terra_eeg_index_20k.json` (active graph for graph structure) |
| **Graph Content** | Missing substantive holdings on 51.1% of nodes; untyped citation edges | 51.1% substantive holdings coverage; typed `OVERRULES` edges | Uses frozen seeds extracted from legacy context strings |
| **Traversal Engine** | Unconstrained BFS (v23) | Bounded BFS (`ask_terra.py`) | Evaluates legacy unconstrained BFS (Sec. 1) & bounded BFS (Sec. 2) |
| **Operational Limits** | None (unbounded depth/nodes/chars) | 40 nodes, 35k chars, hub caps (50/75/25), recency sort | Sweep parameters across grid; baseline matches unconstrained |
| **Mean Context Length**| 1,342,599.82 characters | 41,268.11 characters | Baseline: 1,342,599.82 characters; Bounded: 40,161.7 characters |
| **Full Path Recovery** | **62/100** | **66/100** | **62/100** (Sec. 1 baseline) / **61/100** (Sec. 2 bounded) |
| **3-Node Chains** | 37/63 | 49/63 | 37/63 (Sec. 1 baseline) / 48/63 (Sec. 2 bounded) |
| **4-Node Chains** | 20/32 | 16/32 | 20/32 (Sec. 1 baseline) / 12/32 (Sec. 2 bounded) |
| **5-Node Chains** | 5/5 | 1/5 | 5/5 (Sec. 1 baseline) / 1/5 (Sec. 2 bounded) |
| **Gold Node Hits** | 295/342 (86.26%) | 302/342 (88.30%) | 295/342 (86.26%) (Sec. 1 baseline) |

---

## 7. Antigravity Endorsement of Codex’s Recommended Remediation

Antigravity **fully concurs** with Codex’s assessment and recommended editorial direction in Section 5 of `I1B_REPORT.md`:

1. **Preserve Canonical v2 Data and Sensitivity Data:**
   Neither `data/terra_canonical_v2_eval.json` (66/100) nor `data/issue26_hyperparameter_sensitivity.json` (62/100) should be regenerated, modified, or silently altered. Both represent valid, reproducible empirical artifacts from their respective execution regimes.
2. **Editorial Disentanglement in Manuscript:**
   - Clearly delineate that **Panel A and Panel B** report the primary benchmark performance of the **deployed bounded TERRA pipeline** (66/100, 49/16/1) on canonical v2 contexts (~41k chars).
   - Clarify that **Panel C Section 1** represents a **sensitivity analysis around the historical unconstrained baseline** (evaluated conditional on frozen legacy context anchors from `terra_baselines_eval_raw.json`, yielding 62/100, 37/20/5), rather than an exact bit-identical reproduction of the canonical v2 deployed pipeline.
   - Clarify that **Panel C Section 2** represents the **bounded operational diagnostic** (40-node / 35k-char caps), yielding 61/100 (48/12/1).
   - Remove misleading phrases such as "published baseline" and "100/100 bit-identical parity" when comparing Panel C to canonical v2.
3. **Preserve Page Budget and Implementation Lead Role:**
   Codex remains the implementation lead for drafting the wording revision for Reviewer finding I1b. Antigravity will review Codex’s draft for page-budget compliance (within the 25-page ceiling) and evidence consistency. No edits should be applied without dated user authorization.
