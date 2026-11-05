# TERRA Manuscript Compression & Reorganization Implementation Plan
**Target**: Reduce Main Manuscript Length to $\le 24$ Pages while Preserving Scientific Integrity, All Protected Claims, Full Statistical Rigor, and Complete Limitation Disclosures  
**Date**: 2026-09-27  
**Status**: REVISED PLAN WITH 7 FINAL SAFEGUARDS RECORDED — PENDING USER APPROVAL (READ-ONLY)

---

## 1. Executive Summary & Core Strategy

The objective of this plan is to compress the TERRA manuscript from its current live state to $\le 24$ pages (meeting standard journal/conference page constraints) through principled structural reorganization, modularization into a primary manuscript and an independently compilable Supplementary Material document, table consolidation, and prose tightening.

### Fundamental Operational Principles:
1. **Zero In-Place Edits**: The canonical `Paper/` tree will **not** be modified during planning, baseline recording, or compression.
2. **Three-Tier Workspace Isolation**: All baseline compilation, active editing, and intermediate builds occur strictly inside separate directories (`CANONICAL_ARCHIVE/`, `COMPRESSION_WORKSPACE/`, `FINAL_PACKAGE/`).
3. **Dynamic Live Baseline Determination**: The current page count, macro tallies, table/figure counts, and hashes are determined dynamically from a copied source during Phase 1; the actual baseline page count is never assumed.
4. **Explicit Active-File Manifest**: Only curated active publication assets are copied; all stale PDFs, backup files (`.bak`), build debris (`.aux`, `.log`), and historical zip bundles in `Paper/` are strictly excluded.
5. **Claim-Level Traceability & Destination Accounting**: Every relocated claim, table, or limitation is explicitly mapped to a supplementary destination with line-level provenance. No content is dropped, and no fabricated scientific proofs or prompt variations may be added.
6. **Frozen Data & Macro Invariant**: Compact tables draw strictly from frozen macro definitions and existing source tables; `generated_stats.tex` is never altered.
7. **Log-Level Compilation Auditing**: Compilation integrity is audited at the raw compiler log level for undefined/multiply-defined citations, labels, and references, rather than relying solely on visual `?` checks.
8. **Promotion Control**: Canonical assets are updated only after clean-room verification and explicit user authorization.

---

## 2. Core Architectural Safeguards & Operating Rules

### 2.1 Three-Tier Workspace Separation
Workspaces are strictly segregated:
```text
CANONICAL_ARCHIVE/      <- Immutable snapshot of the live canonical state; page count determined in Phase 1 (hash-verified)
COMPRESSION_WORKSPACE/  <- Active working tree for baseline recording, reorganization & compression
FINAL_PACKAGE/          <- Staging area for audited compressed main paper, standalone supplement & bundles
```
- **Read-Only Invariant**: The live project root (`Paper/`, `logs/`, `data/`, `prompts/`, `configs/`, etc.) remains strictly read-only by workflow.
- **Report Location**: All baseline logs, disposition records, and audit reports are written strictly outside the canonical tree to `COMPRESSION_WORKSPACE/reports/`.
- **Bundle Location**: All regenerated publication and reproducibility bundles remain confined to `FINAL_PACKAGE/` until promotion.

### 2.2 Safeguard 1: Journal Format Verification (No Presumption)
- In Phase 0, formally inspect and document the exact journal/reviewer author guidelines rather than assuming IEEE two-column format without verification.
- Confirm exact page bounds, reference inclusion/exclusion rules, supplement rules, and font/geometry constraints.
- Document whether IEEE Transactions two-column format (e.g. IEEE TKDE / Access), ACM, or an alternative single-column format is explicitly prescribed.

### 2.3 Safeguard 2: Explicit Active-File Manifest (Debris Exclusion)
The live `Paper/` directory contains historical snapshots, stale binaries (`compiled_submission_main.pdf`, `prev_main.pdf`), backup files (`*.bak_*`, `*.broken_*`), build debris (`*.aux`, `*.log`, `*.out`), unreferenced `.bbl` files, and historical zip archives (`overleaf_bundle_*.zip`).

Only the following **26 active canonical constituents** will be copied into `CANONICAL_ARCHIVE/` and `COMPRESSION_WORKSPACE/src/`:
1. `Paper/main.tex` (Active manuscript root)
2. `Paper/ref.bib` (Active BibTeX bibliography)
3. `Paper/main.bbl` (Active precompiled bibliography)
4. `Paper/generated_stats.tex` (Canonical experiment macros)
5. `Paper/generated_obscure_stats.tex` (Obscure precedent macros)
6. `Paper/generated_corpus_stats_20k.tex` (20k corpus metrics)
7. `Paper/figure_1_system_architecture.tex` (System architecture diagram)
8. `Paper/figure_2_hub_centrality.tex` (Hub centrality diagram)
9. `Paper/figure_3_safety_rejection.tex` (Safety rejection diagram)
10. `Paper/tables/table_sensitivity_raw_vs_clamped.tex` (Table I)
11. `Paper/tables/table_refusal_breakdown.tex` (Table II)
12. `Paper/tables/table_full_fdr_family.tex` (Table XXIII / Full FDR family)
13. `Paper/tables/table_system_comparison.tex` (Table IV)
14. `Paper/tables/table_temporal_leakage_probe.tex` (Table V)
15. `Paper/tables/table_casefacts_eval.tex` (Table VI)
16. `Paper/tables/table_clerc_eval.tex` (Table VII)
17. `Paper/tables/table_retrieval_eval.tex` (Table VIII)
18. `Paper/tables/table_computational_budget.tex` (Table IX)
19. `Paper/tables/table_router_eval.tex` (Table X)
20. `Paper/tables/table_citation_eval.tex` (Table XI)
21. `Paper/tables/table_obscure_overruled_eval.tex` (Table XII)
22. `Paper/tables/table_temporal_update_stability.tex` (Table XIII)
23. `Paper/tables/table_baseline_specifications.tex` (Table XIV)
24. `Paper/scripts/check_consistency.py` (Canonical CI check harness)
25. `Paper/scripts/allowed_literals.txt` (CI literal whitelist)
26. `Paper/scripts/generate_stats.py` (Macro generator reference)

All other files in `Paper/` are strictly excluded from the compression workspace.

### 2.4 Safeguard 3: Read-Only Consistency CI Execution
- Forensic audit of `Paper/scripts/check_consistency.py` confirms that all file open calls use mode `"r"` or `"rb"`; there are zero file write operations.
- To guarantee absolute isolation, CI execution during compression will be invoked exclusively with `--target COMPRESSION_WORKSPACE/src/`, executing only against copied assets.

### 2.5 Safeguard 4: Frozen Macro & Table Source Invariant
- Compact and merged tables must draw exclusively from frozen macro definitions (`\Terra...`, `\CatB...`, `\Obsc...`) and existing table LaTeX sources.
- **Prohibition**: Never alter `generated_stats.tex`, `generated_corpus_stats_20k.tex`, or `generated_obscure_stats.tex`. Never recalculate, resynthesize, or alter raw experimental numbers.

### 2.6 Safeguard 5: Final Package Bundling & Clean-Room Supplement Compilation
- The final distribution bundle staged in `FINAL_PACKAGE/` must contain both the compressed main manuscript and the standalone Supplementary Material document.
- Both documents must successfully compile to PDF from clean-room extraction in an isolated temporary environment.

### 2.7 Safeguard 6: Log-Level LaTeX Warning & Collision Audit
- Rather than relying solely on visual checks for visible `?` characters, Phase 11 compilation audits must parse raw compiler logs (`tectonic` stdout/stderr or `.log`) via automated regex scanning:
  - `LaTeX Warning: Reference .* undefined`
  - `LaTeX Warning: Citation .* undefined`
  - `LaTeX Warning: Label .* multiply defined`
  - `LaTeX Warning: There were undefined references`
- Any occurrence of the above represents a hard compilation gate failure.
- Non-fatal box warnings (overfull/underfull `\hbox`) must be cataloged and verified benign.

### 2.8 Safeguard 7: Line-Level Limitation Traceability & Cross-Reference Remapping
- The Supplementary Material will use an independent namespace:
  - `Supplementary Section S1`, `Supplementary Section S2`, ...
  - `Supplementary Table S1`, `Supplementary Table S2`, ...
  - `Supplementary Figure S1`, `Supplementary Figure S2`, ...
- Every limitation in Supplementary Section S2 must explicitly cite its exact source line range in `Paper/main.tex` (Lines 1051–1104) and original section anchor.
- Internal references to main-paper sections (e.g. `Section~\ref{subsec:eval-metrics}`) must be decoupled into explicit cross-document prose (e.g. *"Main Manuscript Section~IV-B"*), preventing unresolved reference errors.
- **Prohibition on Content Fabrication**: No synthetic proofs or prompt variations may be added. Only canonical, preexisting evidence may populate the supplement.

---

## 3. Explicit Limitation Remapping Architecture (All 18 Limitations)

Every one of the 18 original limitations from `Paper/main.tex` (Lines 1051–1104) is mapped to an explicit main-paper grouped subsection and a dedicated Supplementary Section, preserving line-level traceability:

| Orig # | Source Line Range in `Paper/main.tex` | Original Limitation Title in Live Manuscript | Main Paper Grouped Destination | Supplementary Section Destination | Remapping / Cross-Reference Strategy |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **1** | Line 1051 | Absence of Licensed Legal Practitioner Evaluation (Most Critical Limitation for Deployment) | Section VI-C.1: Evaluator Scope & Absence of Licensed Legal Practitioners | Supplementary Section S2.1 | Primary deployment caveat in main paper; unabridged text in S2.1 referencing Main Manuscript Section~IV-B; preserves Line 1051 source anchor. |
| **2** | Line 1052 | Metric Disentanglement and Refusal-Volume Masking | Section VI-C.2: Evaluation Methodology, Rubrics & Metric Disentanglement | Supplementary Section S2.2 | Main paper summarizes refusal distortion; S2.2 carries unabridged empirical breakdown; preserves Line 1052 source anchor. |
| **3** | Line 1053 | Evaluation Rubric Resolution and Likert Normalization | Section VI-C.2: Evaluation Methodology, Rubrics & Metric Disentanglement | Supplementary Section S2.3 | Main paper discusses Likert ceiling effects; S2.3 references rubric calibration details; preserves Line 1053 source anchor. |
| **4** | Line 1054 | Jurisdictional and Temporal Corpus Boundaries | Section VI-C.5: Corpus Boundaries, Filtering Biases & Domain Generalizability | Supplementary Section S2.4 | Main paper defines 1850–1980 boundary; S2.4 details docket distribution and exclusions; preserves Line 1054 source anchor. |
| **5** | Lines 1055–1056 | Hosted API Output Variability at $T=0.0$, Run-to-Run Identity, and Sensitivity Verification | Section VI-C.2: Evaluation Methodology, Rubrics & Metric Disentanglement | Supplementary Section S2.5 | Main paper reports non-zero API variance; S2.5 preserves temperature sensitivity data; preserves Lines 1055–1056 source anchor. |
| **6** | Lines 1057–1059 | Parametric Pretraining Confounders, Latent Weights, and Temporal Containment Bounds | Section VI-C.4: Failure Modes, Fatal Errors ($2/75$) & Refusal Asymmetry | Supplementary Section S2.6 | Main paper retains full disclosure of the 2 fatal errors (D033/D034); S2.6 details Level-2 leakage suppression; preserves Lines 1057–1059 source anchor. |
| **7** | Line 1060 | Fixed Graph Traversal Horizon and Multi-Hop Boundary Limits | Section VI-C.3: Graph Traversal Horizons, Taxonomies & Hyperparameters | Supplementary Section S2.7 | Main paper notes 2-hop BFS horizon constraint (CF_INC_058); S2.7 analyzes deep precedent chains; preserves Line 1060 source anchor. |
| **8** | Lines 1061–1062 | Oracle Relation Labels, Exact-Title Seeding, and a Bundled Ablation | Section VI-C.3: Graph Traversal Horizons, Taxonomies & Hyperparameters | Supplementary Section S2.8 | Main paper candidly admits curated OVERRULES tag reliance; S2.8 documents exact seeding heuristics; preserves Lines 1061–1062 source anchor. |
| **9** | Lines 1063–1065 | False Refusals on Answerable Queries (Categories A and B) | Section VI-C.4: Failure Modes, Fatal Errors ($2/75$) & Refusal Asymmetry | Supplementary Section S2.9 | Main paper reports exact false refusal counts; S2.9 provides query-level failure breakdown; preserves Lines 1063–1065 source anchor. |
| **10** | Lines 1066–1068 | Latency Measurement Caveats | Section VI-C.4: Failure Modes, Fatal Errors ($2/75$) & Refusal Asymmetry | Supplementary Section S2.10 | Main paper notes gross vs. net latency and HTTP 429 throttling; S2.10 preserves backoff profiles; preserves Lines 1066–1068 source anchor. |
| **11** | Lines 1069–1071 | Same-Family Generation, NLI Grading, and Category D Verifier | Section VI-C.2: Evaluation Methodology, Rubrics & Metric Disentanglement | Supplementary Section S2.11 | Main paper discloses model-family alignment biases; S2.11 provides cross-family verification; preserves Lines 1069–1071 source anchor. |
| **12** | Lines 1072–1074 | Unflagged Textual Refusals | Section VI-C.4: Failure Modes, Fatal Errors ($2/75$) & Refusal Asymmetry | Supplementary Section S2.12 | Main paper reports unflagged refusal counts (D034, D061, D068, D070); S2.12 documents exact response strings; preserves Lines 1072–1074 source anchor. |
| **13** | Lines 1075–1077 | Mixed-Date Evaluation Blocks | Section VI-C.2: Evaluation Methodology, Rubrics & Metric Disentanglement | Supplementary Section S2.13 | Main paper notes chronological clustering; S2.13 provides temporal block stratification analysis; preserves Lines 1075–1077 source anchor. |
| **14** | Lines 1078–1080 | Corpus Length-Filtering Bias and Concise Landmark Exclusion | Section VI-C.5: Corpus Boundaries, Filtering Biases & Domain Generalizability | Supplementary Section S2.14 | Main paper discloses length-filtering exclusions; S2.14 documents excluded concise landmark list; preserves Lines 1078–1080 source anchor. |
| **15** | Lines 1081–1083 | Citation Extraction Precision, Same-Year Chronology, and Provenance Uncertainty | Section VI-C.3: Graph Traversal Horizons, Taxonomies & Hyperparameters | Supplementary Section S2.15 | Main paper addresses regex extraction precision; S2.15 details graph chronology verification steps; preserves Lines 1081–1083 source anchor. |
| **16** | Lines 1084–1086 | Rule-Based Doctrinal Taxonomy, Lexical Polysemy, Truncation, and Residual Fallback Bias | Section VI-C.3: Graph Traversal Horizons, Taxonomies & Hyperparameters | Supplementary Section S2.16 | Main paper discusses keyword taxonomy limitations; S2.16 preserves full category definitions; preserves Lines 1084–1086 source anchor. |
| **17** | Line 1087 | A Priori Hyperparameter Selection and Sensitivity Analysis Scope | Section VI-C.3: Graph Traversal Horizons, Taxonomies & Hyperparameters | Supplementary Section S2.17 | Main paper notes fixed pre-evaluation hyperparameters; S2.17 references complete sensitivity sweeps; preserves Line 1087 source anchor. |
| **18** | Lines 1088–1104 | Task-Corpus Domain Asymmetry and Private-Law Generalizability Scope | Section VI-C.5: Corpus Boundaries, Filtering Biases & Domain Generalizability | Supplementary Section S2.18 | Main paper delineates federal constitutional scope vs. private-law domains; S2.18 details domain transferability bounds; preserves Lines 1088–1104 source anchor. |

---

## 4. Comprehensive 15-Phase Execution Plan

### Phase 0 — Journal and Scope Confirmation
- Formally inspect and document submission venue / author guidelines:
  - Exact maximum page limit for the main manuscript.
  - Policy on reference list inclusion/exclusion from the page limit.
  - Policy on Supplementary Material (permitted, separate document, separate review, page/file size bounds).
  - Format requirement (IEEE two-column transactions format confirmed or alternative documented).
- **Gate**: Journal constraints formally recorded in `COMPRESSION_WORKSPACE/reports/phase0_journal_constraints.txt`.

### Phase 1 — Dynamic Live Baseline Audit
- Copy the **26 active canonical constituents** from `Paper/` into an isolated scratch harness within `COMPRESSION_WORKSPACE/`.
- Compile the copied source via Tectonic (`SOURCE_DATE_EPOCH=1780000000`).
- Dynamically inspect and measure:
  - Actual baseline page count via PyMuPDF/PdfReader.
  - Compiler command line and exit code.
  - SHA-256 digests of `Paper/main.tex` and compiled baseline PDF.
  - Total macro definitions (dynamically parsed from `generated_stats.tex` and `check_consistency.py`).
  - Active table and figure counts (dynamically enumerated from source).
  - Reference count and citation keys.
  - Canonical CI status (`python Paper/scripts/check_consistency.py --target COMPRESSION_WORKSPACE/src/`).
- **Gate**: Baseline report written strictly to `COMPRESSION_WORKSPACE/reports/compression_phase1_baseline.txt`; canonical files untouched. **STOP FOR USER REVIEW.**

### Phase 2 — Canonical Preservation
- Instantiate `CANONICAL_ARCHIVE/` containing the exact 26 active constituents, compiled baseline PDF, and root bundles.
- Record SHA-256 checksums into `CANONICAL_ARCHIVE/canonical_manifest.json`.
- **Gate**: Canonical archive hash-verified and preserved read-only by workflow.

### Phase 3 — Source Inventory & Reconciliation Gate
- Dynamically parse and reconcile every potential numerical or structural ambiguity from live sources:
  - Graph edge totals (CITES vs. OVERRULES) from `generated_corpus_stats_20k.tex`.
  - Active table and figure tallies from `main.tex` inputs.
  - Total defined macros and abstract claim checks.
  - Full inventory of all 18 limitations, section headings, and hypothesis tests.
- Reconcile any discrepancies between legacy narrative text and live generated macros.
- **Gate**: Reconciliation ledger written to `COMPRESSION_WORKSPACE/reports/phase3_reconciliation_ledger.txt`; zero source-of-truth conflicts.

### Phase 4 — Claim-Level Disposition Mapping
- Author a comprehensive claim-level disposition matrix mapping every section, paragraph block, table, figure, and limitation to:
  1. Main Paper ($\le 24$ pages)
  2. Supplementary Material (Standalone Document)
  3. Archival Repository Package
- For every relocated item, define the exact replacement cross-reference anchor and textual bridge.
- **Gate**: Disposition matrix approved; zero content units unassigned; 100% claim-level traceability.

### Phase 5 — Compression Workspace Initialization
- Populate `COMPRESSION_WORKSPACE/src/` with the active LaTeX assets from the active-file manifest.
- Verify complete independence: compilation in `COMPRESSION_WORKSPACE/` produces artifacts only inside the workspace.
- Ensure all canonical code, data, logs, and benchmark suites remain outside and untouched.
- **Gate**: Workspace independence verified; zero side effects on canonical tree.

### Phase 6 — Standalone Supplement Harness & Remapping
- Create `supplement.tex` in `COMPRESSION_WORKSPACE/src/`:
  - Standalone document preamble, title, authors, and abstract.
  - Independent namespace (`Section S*`, `Table S*`, `Figure S*`).
  - Dedicated bibliography inclusion (`ref.bib`).
  - Relocated full-family tables (e.g. Table XXIII Full FDR Family $\to$ Supplementary Table S1).
  - Complete, unabridged 18-item Limitations register (Supplementary Sections S2.1–S2.18) with line-level source citations and cross-references remapped to explicit main-paper text (e.g. *"Main Manuscript Section~IV-B"*).
  - Only preexisting canonical artifacts (no invented proofs or synthetic templates).
- **Gate**: `supplement.tex` compiles cleanly to PDF via Tectonic with exit code 0, zero fatal errors, and zero unresolved cross-references.

### Phase 7 — Structural Manuscript Reorganization
- Restructure `COMPRESSION_WORKSPACE/src/main.tex` narrative flow into standard journal architecture:
  1. Introduction & Problem Formulation
  2. Related Work & Systematic Taxonomy
  3. Architecture & Methodology (EEG, Traffic Cop Router, NLI Smart Grader)
  4. Corpus Construction & Experimental Setup
  5. Results & Empirical Evaluation (organized around Core Research Questions)
  6. Discussion & High-Level Synthesis
  7. Grouped Limitations Summary (Sections VI-C.1 through VI-C.5, with forward pointers to Supplement S2.1–S2.18)
  8. Conclusion & Broader Impacts
- **Gate**: Restructured manuscript compiles; all core research questions and protected claims remain represented.

### Phase 8 — Table and Figure Consolidation
- Execute approved table consolidations drawing strictly from frozen macro definitions:
  - Consolidate corpus overview tables into a unified presentation.
  - Compact router performance and latency metrics into a single dual-panel table.
  - Consolidate external benchmark evaluations (CaseFacts + CLERC).
  - Compact temporal leakage probe and obscure-overruled analyses.
  - Relocate full $M=20$ FDR hypothesis table to `Supplementary Table S1`.
  - Relocate secondary graph topologies (Figure 2) to `Supplementary Figure S1`.
- Audit table-by-table equivalence (values, denominators, CIs, $p$-values, $q$-values).
- **Gate**: Consolidated tables pass numerical and semantic equivalence check; zero data loss; zero alteration of `generated_stats.tex`.

### Phase 9 — Targeted Prose Compression
- Eliminate narrative redundancy, repetitive phrasing, verbose transitions, and non-essential algorithmic boilerplate.
- Preserve all precise qualifications, statistical hedges, failure mode discussions, and operational caveats.
- Strictly enforce prohibition on upgraded or unhedged causal claims.
- **Gate**: Prose compression audit passes; semantic integrity verified.

### Phase 10 — Limitations Register Grouping
- Group the 18 limitations in the main paper into 5 cohesive thematic subsections:
  1. Section VI-C.1: Evaluator Scope & Absence of Licensed Legal Practitioners (Limitation 1, Line 1051)
  2. Section VI-C.2: Evaluation Methodology, Rubric Resolution & Metric Disentanglement (Limitations 2, 3, 5, 11, 13; Lines 1052, 1053, 1055–1056, 1069–1071, 1075–1077)
  3. Section VI-C.3: Graph Traversal Horizons, Taxonomies & Hyperparameters (Limitations 7, 8, 15, 16, 17; Lines 1060, 1061–1062, 1081–1083, 1084–1086, 1087)
  4. Section VI-C.4: Failure Modes, Fatal Errors ($2/75$) & Refusal Asymmetry (Limitations 6, 9, 10, 12; Lines 1057–1059, 1063–1065, 1066–1068, 1072–1074)
  5. Section VI-C.5: Corpus Boundaries, Filtering Biases & Domain Generalizability (Limitations 4, 14, 18; Lines 1054, 1078–1080, 1088–1104)
- Provide explicit forward references to Supplementary Sections S2.1–S2.18 for the complete unabridged text of each limitation.
- **Gate**: Every original limitation has an explicit main-paper summary and a verified supplementary mapping per the Section 3 table.

### Phase 11 — Independent Dual-Compilation & Log-Level Audit
- Compile both `main.tex` and `supplement.tex` independently in `COMPRESSION_WORKSPACE/`.
- Verify compilation gates:
  - Exit code 0 for both builds.
  - Zero fatal LaTeX errors.
  - **Zero log-level undefined references/citations** (automated regex scan of compiler log for `LaTeX Warning: Reference/Citation/Label ... undefined/multiply defined`).
  - Zero out-of-page text blocks or coordinate overflows ($0 \le y \le 792.0\text{ pt}$).
  - All non-fatal warnings categorized as benign TeX box/font notices.
- **Gate**: Dual compilation passes cleanly; visual inspection confirms layout integrity.

### Phase 12 — Comprehensive Scientific Integrity Audit
- Perform exhaustive cross-comparison between `COMPRESSION_WORKSPACE/` output and `CANONICAL_ARCHIVE/`:
  - Numerical value match (100% of reported metrics, CIs, and test statistics).
  - Comparison directions verified across all comparative baselines.
  - Explicit retention of parity findings (e.g. Direct LLM on Category B).
  - Explicit retention of fatal errors ($2/75$), false refusals, and latency trade-offs.
  - Verification that no unsupported scientific claims were added to the supplement.
- **Gate**: Scientific integrity audit passed and logged to `COMPRESSION_WORKSPACE/reports/phase12_integrity_audit.txt`.

### Phase 13 — Page-Budget Optimization ($\le 24$ Pages)
- Adjust spacing, paragraph flow, and float placements strictly within journal style boundaries.
- No alteration of font size, line baseline, margins, or basic typography.
- **Gate**: Main manuscript compiles to strictly **$\le 24$ genuine pages** with zero out-of-page clipping.

### Phase 14 — Final Packaging, Clean-Room Staging & Promotion Gate
- Assemble `FINAL_PACKAGE/`:
  - Compressed main paper source and compiled PDF ($\le 24$ pages).
  - Standalone supplement source and compiled PDF.
  - Staged Overleaf publication bundle (incorporating main + supplement).
  - Staged reproducibility bundle and external manifest.
  - Comprehensive disposition map and claim traceability matrix.
  - Phase-by-phase audit logs.
- Perform a complete clean-room compilation from `FINAL_PACKAGE/` in a pristine temporary environment.
- Run a comprehensive diff against the repository root proving that zero canonical code, datasets, prompts, configs, or logs were modified.
- **Gate**: Final package presented for explicit user review and promotion authorization. Canonical project root remains unmodified until approval.

---

## 5. Current State & Next Steps

- Implementation plan updated with all 7 safeguards in [`TERRA_MANUSCRIPT_COMPRESSION_PLAN.md`](file:///f:/TERRA%20-Copy/TERRA_MANUSCRIPT_COMPRESSION_PLAN.md).
- **Execution Status**: HALTED. Ready to request approval for **Phases 0–1 only**.
