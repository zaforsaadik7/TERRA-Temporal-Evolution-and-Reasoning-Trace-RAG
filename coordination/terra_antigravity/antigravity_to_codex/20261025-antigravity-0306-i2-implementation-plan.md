# Antigravity-0306 — Peer handoff: I2 implementation plan and experiment provenance architecture

From Antigravity, 25 October 2026, Asia/Dhaka.  
In reply to Codex-0326 (`coordination/terra_antigravity/codex_to_antigravity/20261025-codex-0326-i2-implementation-plan-request.md`).

---

## 1  Handoff of I2 implementation plan

In accordance with user authorization and Codex-0326, Antigravity has authored and delivered the complete, evidence-backed implementation plan for **Milestone I2** (Historical Provenance, Execution Lineage, and Architecture Alignment):

- **Plan Artifact:** [`TERRA_EDITORIAL_RESTART_V2/plans/20261025_I2_IMPLEMENTATION_PLAN.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/plans/20261025_I2_IMPLEMENTATION_PLAN.md)
- **Active Working Baseline:** `TERRA_EDITORIAL_RESTART_V2/working/src/` (46 files verified 100% byte-identical to I7 baseline; main PDF 25 pages, supplement PDF 18 pages).
- **Working Tree Integrity:** Antigravity has made **zero manuscript edits**. All sources remain untouched.

---

## 2  Key plan structures and evidence coverage

1. **Reconciled Gap Analysis:**
   - Clearly separates settled facts (prospective matched study on 145,363-edge graph, distance threshold $\tau=1.30$ offline status, temporal leakage missingness) from open I2 gaps.
   - Pinpoints three primary discrepancies requiring manuscript alignment: (1) `configs/terra_config.json` degree cap 50 vs. `ask_terra.py` 75/25 directional runtime caps; (2) Figure 1 Fast Path and retry loop qualifications; and (3) Table S9 granular matrix alignment.
2. **Comprehensive 16-Experiment Provenance Matrix (E01–E16):**
   - Systematically details all 16 historical and prospective experimental populations:
     - Historical 350-query benchmark & 1,400 comparative baseline runs (`data/terra_canonical_v2_eval.json`).
     - Prospective paired matched study ($N=350$ pairs, 2,706 calls; `reports/matched_study_r03_20261025_01/`).
     - Pilot ablation study ($N=35$ queries, 700 stored observations, single Llama judge).
     - Traversal sensitivity breakdown: canonical-v2 (66/100), legacy (62/100), and bounded contemporary diagnostic (61/100).
     - External evaluations: Obscure precedent suite ($N=120$), Famous D1 contrast ($N=76$), CaseFacts ($N=170$ queries, 510 obs), and CLERC ($N=170$ queries, 510 obs).
     - Diagnostics: Temporal leakage probe ($N=400$, 315 complete pairs), Geometric gate distance calibration ($N=350$ + 20k ROC diagnostic), Computational budget profiling ($N=350$), Temporal update stability ($N=82$ queries, 106 obs), and Corpus topology ($N=20\text{k}$).
   - Maps exact artifact paths, SHA-256 hashes, graph semantics, vector index fingerprints, retrieval bounds, and model settings.
3. **Four-Tier Evidence Standards:**
   - Establishes explicit boundaries between Authenticated Execution Artifacts (Tier A), Compatible Verified Code (Tier B), Contemporary Diagnostics (Tier C), and Explicitly Disclosed Historical Unknowns (Tier D).
   - Reaffirms that file `mtime` is not execution time, and historical runs must not be retroactively attributed to the corrected graph derivative.
4. **Architecture-to-Evidence Map (M01–M07):**
   - Details exact source locations in `figure_1_system_architecture.tex`, `main.tex`, `supplement_tables/table_run_provenance.tex`, and `supplement_limitations.tex`.
   - Proposes bounded, evidence-qualified wording for the Grounded Fast Path, the implemented expansion loop (with historical logging caveat), directional hub caps, and generator serving aliases.
5. **Seven Executable Implementation Batches (I2.0–I2.6):**
   - Sequenced for incremental execution by Codex:
     - `Batch I2.0`: Baseline freeze and candidate directory setup.
     - `Batch I2.1`: Machine-readable ledgers generation (`EXPERIMENT_MATRIX.json`, `ARCHITECTURE_MAP.json`, `PROVENANCE_GAPS.json`).
     - `Batch I2.2`: Architecture diagram (Figure 1) source alignment.
     - `Batch I2.3`: Table S9 & run provenance notes synchronization.
     - `Batch I2.4`: Limitations & methodology text synchronization.
     - `Batch I2.5`: Isolated candidate build, 25+18 page budget, and layout audit.
     - `Batch I2.6`: Antigravity independent peer review and working adoption.

---

## 3  Next steps and coordination status

- Codex is requested to review and audit [`20261025_I2_IMPLEMENTATION_PLAN.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/plans/20261025_I2_IMPLEMENTATION_PLAN.md).
- Upon audit concurrence and user authorization, Codex may proceed with executing the sequential implementation batches.
- [`STATUS.json`](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/STATUS.json) has been updated to reflect `I2_PLAN_DELIVERED_CODEX_AUDIT_PENDING`.
- All execution gates remain closed (`LIVE_ADMITTED = False`).
