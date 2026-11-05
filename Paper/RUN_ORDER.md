# Macro Generation and Build Run Order Protocol

This document defines the strict execution order and file-writing semantics for LaTeX macro generation in TERRA, derived from the forensic audit in `logs/macro_writers.txt`.

---

## 1. File Writing Behaviors and Macro Provenance

### A. Base Overwriters
- **`Paper/scripts/generate_stats.py`**:
  - **Behavior**: **OVERWRITES** `Paper/generated_stats.tex` (`open(OUTPUT_TEX, "w")`).
  - **Contents**: Computes canonical baseline evaluation metrics (350 queries $\times$ 5 pipelines) and component ablation metrics (35 queries $\times$ 4 configs $\times$ 5 runs).
  - **Critical Invariant**: **NEVER run `generate_stats.py` alone.** Running it alone will wipe out all macros appended by subsequent domain-specific scripts, reducing macro count and breaking the paper build with undefined macros in `main.tex`.

- **`scripts/audit_and_sync_paper.py`**:
  - **Behavior**: **OVERWRITES** `Paper/generated_stats.tex` only when explicitly invoked with `--update-latex`. In default read-only mode, it performs audits without modifying any files.

### B. Domain Metric Appenders
The following scripts read the existing `Paper/generated_stats.tex`, parse the current registry, and append domain-specific macros to the file:
1. **`scripts/compute_budget_and_gate_metrics.py`**:
   - **Behavior**: **READ AND APPEND** (`open("r")`, appends, writes back `"w"`).
   - **Contribution**: Appends 73 operational latency, cost budget, and NLI gating macros.
2. **`scripts/compute_clerc_metrics.py`**:
   - **Behavior**: **READ AND APPEND** (`open("r")`, appends, writes back `"w"`).
   - **Contribution**: Appends 36 CLERC external benchmark generalization and citation accuracy macros.
3. **`scripts/compute_retrieval_metrics.py`**:
   - **Behavior**: **READ AND APPEND** (`open("r")`, appends, writes back `"w"`).
   - **Contribution**: Appends 28 multi-hop precedent-chain retrieval quality macros.

---

## 2. Issue #18 Macro Isolation (`generated_obscure_stats.tex`)

To guarantee absolute non-interference with the cumulative 885 macros in `Paper/generated_stats.tex`:
- **File**: `Paper/generated_obscure_stats.tex` (prefixed with `\Obsc...`).
- **Dedicated Generator**: `Paper/scripts/generate_obscure_stats.py`.
- **Inputs**:
  - `scratch/obscure_overruled_summary.json`
  - `scratch/famous_d1_summary.json`
  - `scratch/cross_suite_summary.json`
- **Verification Script**: `Paper/scripts/verify_obscure_macros.py`.
- **CI Enforcement**: `Paper/scripts/check_consistency.py` scans `Paper/generated_obscure_stats.tex` and enforces cryptographic SHA-256 header matches against all three input JSONs.

---

## 3. Canonical Build and Verification Workflow

If a full regeneration of all paper statistics is required, execute in this strict sequential order:
1. Run `Paper/scripts/generate_stats.py` (writes baseline/ablation foundation).
2. Run `scripts/compute_retrieval_metrics.py` (appends retrieval metrics).
3. Run `scripts/compute_clerc_metrics.py` (appends CLERC metrics).
4. Run `scripts/compute_budget_and_gate_metrics.py` (appends budget/gate metrics).
5. Run `Paper/scripts/generate_obscure_stats.py` (generates isolated obscure precedent macros).
6. Run `Paper/scripts/check_consistency.py` (asserts zero undefined macros and verifies all SHA-256 headers).

---

## 4. Critical Invariants and Execution Restrictions

1. `Paper/scripts/generate_stats.py` is now verified safe for `TerraCatDRejection` and `TerraCatDRejectionRate`: it repoints both macros directly to `scratch/category_d_rubric_summary.json` (authoritative value `42/75 (56.0\%)`, verified via redirection harness with 0 differing macros against the restored file). However, because it overwrites `Paper/generated_stats.tex`, running it alone on the real file still wipes out subsequent appender blocks; full regeneration must follow Section 3 build order.
2. compute_retrieval_metrics.py and compute_budget_and_gate_metrics.py truncate everything after their own header; never run them on the real file.
