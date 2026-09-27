# IMPLEMENTATION PLAN: ISSUE #32 — SPURIOUS "SHAP-VERIFIED NLI" CLAIM

**Document Version**: 3.0.0 (Authoritative Issue #31 Manifest Reconciled & Dynamic Accounting Compliant)  
**Target Issue**: Issue #32 (Tier 3: Terminology, Framing & Claims)  
**Related Review Items**: Second Review Track B — Framing & Terminology Invariants  
**Author**: Antigravity AI  
**Status**: REVISED DRAFT — PENDING USER APPROVAL (Execution strictly withheld)  

---

## 1. Executive Summary & Problem Formulation

### 1.1 Issue Description
In `Paper/main.tex` (Section II: Related Work, paragraph 5, Line 139), the manuscript currently states:
> *"Furthermore, it replaces flawed entity-alignment evaluators with a \textbf{SHAP-verified NLI entailment grader} and utilizes a continuous three-way Traffic Cop router to dynamically balance textual, graphical, and procedural data."*

### 1.2 Root Cause Analysis
The phrase **"SHAP-verified"** was introduced into earlier drafts as an editorial conflation. 
In the preceding paragraph (Section II, Line 137), the manuscript correctly reviews prior literature:
> *“Yalavarthi \cite{yalavarthi2026opensourcereproductionexplainabilityanalysis} conducted a SHAP explainability analysis on the widely adopted Corrective RAG (CRAG) architecture, mathematically proving that its standard T5-based evaluator functions purely as a named entity alignment detector.”*

While Yalavarthi (2026) applied SHAP (Shapley Additive Explanations) to demonstrate that CRAG's T5 evaluator relied on superficial entity matching rather than semantic entailment, **TERRA itself was never evaluated or trained using SHAP**. 

TERRA’s NLI Smart Grader is an autonomous zero-shot/few-shot natural language inference gate implemented via `databricks-meta-llama-3-3-70b-instruct` operating under strict semantic entailment rubrics (Section III-C). Describing TERRA's NLI grader as "SHAP-verified" is scientifically inaccurate and creates a severe credibility vulnerability during peer review.

### 1.3 Core Mandate & Resolution
1. **Completely eliminate** the phrase `"SHAP-verified"` from TERRA's architectural description in `Paper/main.tex` (Line 139).
2. Replace it with `"an autonomous NLI entailment grader"`, harmonizing with the exact nomenclature used across:
   - Section I (Line 115): *"autonomous semantic entailment grader"*
   - Section I Contributions (Line 124): *"specialized Natural Language Inference (NLI) grader"*
   - Table I (Line 21 & Notes): *"Autonomous NLI semantic entailment gate"*
   - Section III-C (Line 233): *"autonomous NLI Smart Grader"*
   - Section VII (Line 1031): *"NLI Smart Grader"*
3. **Preserve legitimate literature references**: Keep Line 113 (Introduction overview of evaluator failure modes) and Line 137 (Yalavarthi's SHAP analysis of CRAG) intact, ensuring that SHAP is cited exclusively where it was actually performed in the literature.
4. **Preserve Explainable AI (XAI) Section III-D**: Confirm that Section III-D (`\subsubsection{Explainable AI (XAI) and Topological Provenance}`) continues to detail TERRA's four actual explainability layers (Graph Traversal Provenance, Dynamic Hyperlinked Attribution, NLI Entailment Transparency, Routing Decision Transparency) without conflating them with SHAP.
5. **Authoritative Substrate & Archive Manifest**: Import the exact paths and SHA256 checksums from the authoritative `data/issue31_preflight.json` manifest (11 protected substrates and 2 frozen archives).
6. **Explicit Canonical Raw Evaluation Artifact Hashing**: Separately identify and verify the canonical raw evaluation artifact (`scratch/canonical_v2/terra_canonical_v2_eval.json`) with its verified size (`15,156,436` bytes) and SHA256 hash.
7. **Dynamic Progress Accounting**: Compute all checklist progress counts ($N_{\text{pre}}$, $N_{\text{post}}$, Tier 3 resolved/pending) dynamically from the active checklist state rather than hardcoding assumed numbers. Assert strictly:
   $$N_{\text{post}} = N_{\text{pre}} + 1$$
8. **Strict Page Budget & Substrate Invariance**:
   - Maintain the strict 35-page budget (`len(pages) == 35`).
   - Keep Table XXIII at the top of Page 35 and Reference [27] at the bottom of Page 35.
   - Maintain 100% bit-for-bit text identity across 34 of 35 pages (only Page 3 exhibits the localized 4-character change).
   - Preserve all protected substrates, frozen archives, and canonical evaluation artifacts.

---

## 2. Exhaustive Repository Scope & Authoritative Preflight Manifest

### 2.1 Workspace Search for "SHAP"
An exhaustive scan across all text, code, LaTeX, and JSON files in the workspace reveals the following exact occurrences:
1. `Paper/main.tex`:
   - Line 113: General literature review of Agentic RAG evaluator limitations (*"Mathematical explainability analyses, such as SHAP, have proven that standard evaluators act merely as superficial named entity alignment detectors..."*).
   - Line 137: Specific literature citation to Yalavarthi (2026) regarding CRAG (*"Yalavarthi \cite{yalavarthi2026opensourcereproductionexplainabilityanalysis} conducted a SHAP explainability analysis on the widely adopted Corrective RAG (CRAG) architecture..."*).
   - **Line 139: The spurious claim (*"replaces flawed entity-alignment evaluators with a SHAP-verified NLI entailment grader..."*) — TARGET FOR REMOVAL.**
2. `Paper/prev_main.tex`:
   - Frozen historical archive (lines 111, 135, 137). Protected substrate; strictly immutable.
3. Checklists (`TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md` Line 613, `TERRA_40_ISSUES_MASTER_CHECKLIST.md` Line 191):
   - Issue #32 tracker items.

Zero occurrences exist in `ask_terra.py`, `scripts/`, `tables/`, or benchmark datasets.

### 2.2 Baseline Hashes & Metrics
- `Paper/main.tex`: `97238eed4e38e2f212696bdbb45275a359051f092a2d3aedddbe108dfc8d61aa`
- `Paper/generated_stats.tex`: `3d7024b19b106577508c7b89d4a7e59c3f65a7eb10a746a34e3b7facc333acd8` (851 macros)
- `Paper/main.pdf`: `c4dee1d5bcb2e122cc0ac40da66de89eb8c12ebef57ea648cd4a5ea622fbb871` (422,229 bytes, 35 pages)
- Canonical CI Status: 4/4 PASS under `python Paper/scripts/check_consistency.py --target Paper/`.

### 2.3 Authoritative Protected Substrates & Frozen Archives Manifest
Reconciled directly from `data/issue31_preflight.json`, the preflight gate verifies and asserts the following exact paths and SHA256 checksums:

#### 11 Protected Substrates:
1. `terra_350_benchmark.json`: `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3`
2. `dataset_20k_cap/terra_eeg_index_20k.json`: `7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad`
3. `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1890.json`: `c530f9858e9b3372dc9079092178e9d8c2239758eda073c35b9fc7b0c49e1f72`
4. `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1930.json`: `14071dba780157b767dfce1f11ef8190722ad94ab9a37e8258bb574a0183c3fc`
5. `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1950.json`: `98d14bfb75d5051429ff4c48c0410300efb5ef7f04112701635f110aff094ddf`
6. `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1970.json`: `5e2b59ac3fce2b9513c9ceb60b6a1cae0c2323150f4936a0410503fd56689f3c`
7. `dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1980.json`: `606a6ec126bf7c5ac4cbdbac04f37eee52f7bd524d35e5f12d8dc4ebff3e23b5`
8. `ask_terra.py`: `430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd`
9. `data/issue21_preflight.json`: `9a26a9e35340111773180cadd9f3c271fcecde1a3863609d6abbd2236ba7a9b2`
10. `logs/issue21_preflight.txt`: `91d028cd9ce5079d16bf540cba6546bfa825e5688b3283eb5ef226cc8a3d84d8`
11. `ask_terra_pre_issue13_backup.py`: `bc17d8965a3fc21b0801fb48dd1cf7beeb1cce74ca8a2075a921158ce6d619f9`

#### 2 Frozen Archives:
1. `Paper/prev_main.tex`: `f2491d5ed857639e983e71582811a4f85a76ebaeb516fa029fdb5fce3ca9bcc4`
2. `ask_terra_pre_issue13_backup.py`: `bc17d8965a3fc21b0801fb48dd1cf7beeb1cce74ca8a2075a921158ce6d619f9`

#### Canonical Raw Evaluation Artifact (Separately Verified):
- **Path**: `scratch/canonical_v2/terra_canonical_v2_eval.json`
- **Size**: `15,156,436` bytes ($N=1,750$ evaluation records across 350 queries $\times$ 5 comparative pipelines)
- **SHA256**: `95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507`

---

## 3. Anticipated Reviewer Pushbacks & Proactive Defenses

| Potential Pushback | Risk Level | Proactive Architectural Defense in Plan |
|---|:---:|---|
| **Pushback 1**: *"Does TERRA claim to provide feature-level Shapley value explanations for legal reasoning?"* | **High** | Completely eliminated. Purging `"SHAP-verified"` ensures no reviewer can interpret TERRA as claiming additive feature attribution. Section III-D explicitly defines TERRA's explainability as *topological provenance* (graph paths, markdown links, qualitative NLI justifications, routing decisions). |
| **Pushback 2**: *"Why is Yalavarthi (2026) cited in Related Work if TERRA does not use SHAP?"* | **Medium** | Yalavarthi is cited strictly as prior literature motivation for why keyword and entity-matching evaluators (like CRAG's T5) fail on conceptual tasks, justifying the necessity of an NLI-based entailment gate. Line 137 makes this attribution unambiguous. |
| **Pushback 3**: *"Does modifying Line 139 cause paragraph re-wrapping, column overflow, or page count expansion?"* | **Critical** | Pre-tested in Tectonic. Replacing `a SHAP-verified` (15 chars) with `an autonomous` (13 chars) produces an exact 10-line paragraph on Page 3 (lines 73–82), with Section III heading starting at line 83. Page count is strictly 35 pages, with 34/35 pages 100% bit-identical. |
| **Pushback 4**: *"Are any macros or consistency checks broken by this edit?"* | **Low** | `"SHAP-verified"` is literal text; no macros are modified or deleted. Canonical CI (`check_consistency.py`) will pass 4/4 with all 851 custom macros resolved. |

---

## 4. Multi-Phase Implementation Plan

### Phase 1: Preflight Verification & Baseline Freezing
1. Execute `scripts/verify_issue32_preflight.py` to cryptographically verify:
   - All 11 protected substrates match their golden hashes from `data/issue31_preflight.json`.
   - Both 2 frozen archives match their golden hashes.
   - Canonical raw evaluation artifact (`scratch/canonical_v2/terra_canonical_v2_eval.json`) matches its size (`15,156,436` bytes) and golden hash (`95e775e2...`).
   - Canonical CI passes 4/4 on baseline `Paper/main.tex`.
   - Main PDF has exactly 35 pages with Table XXIII and Ref [27] on Page 35.
   - Line 139 contains `"a SHAP-verified NLI entailment grader"`.
2. Generate baseline preflight artifact: `data/issue32_preflight.json` and log `logs/issue32_preflight.txt`.

### Phase 2: Controlled Manuscript Edit in `Paper/main.tex`
1. Perform exact string replacement at Line 139 of `Paper/main.tex`:
   ```latex
   <<<< TARGET: Paper/main.tex (Line 139)
   Furthermore, it replaces flawed entity-alignment evaluators with a SHAP-verified NLI entailment grader and utilizes a continuous three-way Traffic Cop router to dynamically balance textual, graphical, and procedural data.
   ====
   >>>> REPLACEMENT: Paper/main.tex (Line 139)
   Furthermore, it replaces flawed entity-alignment evaluators with an autonomous NLI entailment grader and utilizes a continuous three-way Traffic Cop router to dynamically balance textual, graphical, and procedural data.
   <<<<
   ```
2. Verify:
   - Zero occurrences of `"SHAP-verified"` remain in `Paper/main.tex`.
   - Remaining occurrences of `"SHAP"` are strictly confined to literature reviews (Line 113 and Line 137).
   - No other lines or sections in `Paper/main.tex` are touched.

### Phase 3: Canonical CI Consistency & Macro Invariant Verification
1. Run `python Paper/scripts/check_consistency.py --target Paper/`.
2. Verify all 4 checks pass:
   - Check 1: Raw checksums (5/5 PASS).
   - Check 2: Custom macro resolution (851/851 PASS, 0 undefined).
   - Check 3: Orphaned literals (0 found).
   - Check 4: Abstract alignment (8/8 PASS).
3. Verify `Paper/generated_stats.tex` remains bit-identical (SHA256: `3d7024b1...`).

### Phase 4: Tectonic Compilation & 35-Page Geometry Validation
1. Compile `Paper/main.tex` via `scratch/tectonic/tectonic.exe --keep-intermediates Paper/main.tex`.
2. Verify compilation exits with return code 0.
3. Validate PDF geometry via `pypdf`:
   - Total pages: strictly 35 (`len(reader.pages) == 35`).
   - Page 35 top float: `TABLE XXIII` confirmed.
   - Page 35 terminal text: `[27] L. Zheng et al., "Judging LLM-as-a-judge..."` confirmed.
   - Pages 1–2 and 4–35: 100% bit-for-bit text-identical to baseline.
   - Page 3: Only the 10-line paragraph on lines 73–82 exhibits the localized text diff, with line count preserved.

### Phase 5: Distribution Bundle Regeneration & Dynamic Checklist Progression
1. Run `scripts/rebuild_issue32_bundles.py` to:
   - Rebuild `Paper/overleaf_bundle.zip` (22 constituent files) and synchronize to root `TERRA_Overleaf_Bundle.zip`.
   - Rebuild `TERRA_Reproducibility_Bundle.zip` (including preflight, closeout, plan, and publication artifacts).
   - Generate external manifest `logs/issue32_reproducibility_manifest.json`.
   - Verify extracted bundle files match source files bit-for-bit in clean temporary directories.
   - Re-verify canonical CI, 35-page PDF geometry, and protected substrate hashes.
   - Dynamically parse the checklist `TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md`:
     ```python
     matches = re.findall(r'^- \[([ x])] \*\*(\d+)\.', chk_text, flags=re.MULTILINE)
     completed_items_pre = [num for mark, num in matches if mark == 'x']
     pending_items_pre = [num for mark, num in matches if mark == ' ']
     n_pre = len(completed_items_pre)
     n_total = len(matches)

     # Derive Tier 3 counts dynamically
     tier3_items = [str(i) for i in range(27, 41)] + ['43']
     tier3_resolved_pre = len([num for num in completed_items_pre if num in tier3_items])
     tier3_pending_pre = len([num for num in pending_items_pre if num in tier3_items])

     assert "32" in pending_items_pre, "Item 32 must be in pending items"
     ```
   - Mark Item 32 complete from `[ ]` to `[x]`.
   - Re-parse and assert dynamic increments:
     ```python
     completed_items_post = [num for mark, num in post_matches if mark == 'x']
     n_post = len(completed_items_post)
     assert n_post == n_pre + 1, f"Expected N_post = N_pre + 1, got {n_pre} -> {n_post}"

     tier3_resolved_post = len([num for num in completed_items_post if num in tier3_items])
     tier3_pending_post = len([num for num in post_pending if num in tier3_items])
     assert tier3_resolved_post == tier3_resolved_pre + 1
     assert tier3_pending_post == tier3_pending_pre - 1
     ```
   - Dynamically re-render the Progress Summary table at the bottom of the checklist using the dynamically derived variables:
     - Tier 3: `resolved={tier3_resolved_post}`, `pending={tier3_pending_post}`
     - Total: `{n_post} / {n_total} ({n_post/n_total*100:.1f}%)`
   - Write deterministic closeout log `logs/issue32_closeout.txt`.
2. Run independent acceptance script `scripts/verify_issue32_closeout.py` to confirm all 10 acceptance gates pass.

---

## 5. Verification Checkpoints & Acceptance Criteria

| Checkpoint | Command / Script | Acceptance Threshold |
|---|---|---|
| **CP-1: Preflight Gate** | `python scripts/verify_issue32_preflight.py` | 11 substrates, 2 archives from `data/issue31_preflight.json`, and canonical raw eval JSON (`scratch/canonical_v2/terra_canonical_v2_eval.json`) match golden hashes. |
| **CP-2: Manuscript Diff** | `git diff Paper/main.tex` | Exactly 1 line modified (Line 139: `"SHAP-verified"` removed). |
| **CP-3: CI Consistency** | `python Paper/scripts/check_consistency.py --target Paper/` | 4/4 PASS, 851 custom macros resolved, 0 orphaned literals. |
| **CP-4: Page Budget** | `pypdf` page counter on `Paper/main.pdf` | Exactly 35 pages; Table XXIII top, Ref [27] bottom. |
| **CP-5: Page Invariance** | Text diff across all 35 pages | Exactly 34/35 pages 100% identical; only Page 3 diffs. |
| **CP-6: Overleaf Bundles** | Hash comparison | `Paper/overleaf_bundle.zip` == `TERRA_Overleaf_Bundle.zip`. |
| **CP-7: Repro Bundle** | External manifest verification | Manifest SHA256 matches `TERRA_Reproducibility_Bundle.zip`. |
| **CP-8: Checklist Count** | Dynamic verification | Assert strictly: $N_{\text{post}} = N_{\text{pre}} + 1$; Tier 3 resolved incremented by 1; Tier 3 pending decremented by 1. |
| **CP-9: Closeout Gates** | `python scripts/verify_issue32_closeout.py` | ALL 10 GATES PASS. |

---

## 6. Strict Non-Execution Commitment
In strict adherence to instructions:
- **No changes** will be made to `Paper/main.tex`, `Paper/generated_stats.tex`, datasets, bundles, or the master checklist until the user reviews and explicitly approves this revised implementation plan.
- All testing was conducted strictly in temporary scratch sandboxes and immediately cleaned up.
- Awaiting user authorization to proceed to Phase 1.
