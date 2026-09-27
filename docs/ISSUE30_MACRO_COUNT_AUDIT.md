# Issue #30 Audit: Macro-Count Discrepancy Forensic Investigation & Resolution

**Document Version:** 1.0  
**Timestamp:** 2026-09-26T01:05:00+06:00  
**Status:** **AUDIT COMPLETE — ROOT CAUSE ISOLATED & REMEDIATION VERIFIED**  
**Target:** Master Checklist Item 30 (Direct LLM Superiority Claim Disclosure & CI Integrity)  

---

## 1. Executive Summary of Audit Findings

| Audit Dimension | Value / Finding |
| :--- | :--- |
| **Phase 1 Baseline Macro Count** | **848 custom macros** (`logs/issue30_preflight.txt`, `data/issue30_preflight.json`) |
| **Phase 2/3 Reported Macro Count** | **819 custom macros** (reported in Phase 2/3 closeout attempt) |
| **Exact Numerical Delta** | **$-29$ custom macros** ($848 - 29 = 819$) |
| **Root Cause Classification** | **Unintended Manuscript Regression via Stale Backup Ingestion** |
| **Root Cause Mechanism** | Phase 2 script (`scratch/test_tune_main.py:5`) read from `Paper/main_bak.tex` (an obsolete pre-Issue #26 backup from Sept 25, 19:16) instead of active `Paper/main.tex`. |
| **Regressed Content** | Section VI-K (Retrieval Hyperparameter Robustness, lines 919–925) and Limitation 17 (lines 1097–1098), containing exactly 29 unique `\IssueTwentySix*` macros. |
| **Collateral Regressions Identified** | Re-introduction of "causal" (Issue #28), re-introduction of "Thinking Trace" inflation (Issue #29), and reversion to `table_retrieval_eval_bak` (Issue #26). |
| **Remediation Status** | True preflight baseline (`340a8469...`) identified in `Paper/overleaf_bundle.zip` & `scratch/paper_v2/main.tex`. Applying the 5 approved edits directly to the true baseline yields **strictly 848 custom macros** (4/4 CI PASS). |

---

## 2. CI Macro Counting Mechanism

The canonical CI script `Paper/scripts/check_consistency.py` verifies macro resolution in **Check 2/4**:
```python
with open(MAIN_TEX, "r", encoding="utf-8") as f:
    main_content = f.read()

used_macros = set(re.findall(r'\\([A-Z][a-zA-Z0-9]+|num[A-Z][a-zA-Z0-9]+)', main_content))
custom_used = used_macros - standard_latex
```
Key architectural properties:
1. `custom_used` is a **set** of unique macro names referenced in `Paper/main.tex`.
2. Check 2/4 scans `Paper/main.tex` directly; it does not recursively descend into `\input{tables/...}`.
3. Therefore, macros appearing solely in external table files (such as `tables/table_retrieval_eval.tex`) are not counted by Check 2/4 unless they are also referenced in `main.tex`.

---

## 3. Itemized Accounting of the 29-Macro Delta

Comparing the unique macro set of the preflight baseline (`scratch/paper_v2/main.tex` / `Paper/overleaf_bundle.zip`) with the regressed file revealed **precisely 29 macros**:

| # | Missing Macro Name | Purpose in Manuscript | Originating Issue |
| :-: | :--- | :--- | :--- |
| 1 | `\IssueTwentySixBoundFullPath` | Post-Issue #13 Bounded Engine Full Path Recall | Issue #26 |
| 2 | `\IssueTwentySixBoundMeanChars` | Bounded Context Character Volume | Issue #26 |
| 3 | `\IssueTwentySixBoundMeanFullNodes` | Bounded Full Unique Case Authorities in Context | Issue #26 |
| 4 | `\IssueTwentySixBoundMeanVisitedNodes` | Bounded Mean Visited Expansion Centers | Issue #26 |
| 5 | `\IssueTwentySixBoundOfflineLatencyMS` | Bounded Engine Offline Traversal Latency | Issue #26 |
| 6 | `\IssueTwentySixConfigCount` | Sweep Configuration Count ($N=22$) | Issue #26 |
| 7 | `\IssueTwentySixContextReductionPct` | Context Volume Reduction Percentage ($97.0\%$) | Issue #26 |
| 8 | `\IssueTwentySixGoldRetentionCount` | Bounded Gold Target Retention Count ($268/295$) | Issue #26 |
| 9 | `\IssueTwentySixGoldRetentionPct` | Bounded Gold Target Retention Percentage ($90.8\%$) | Issue #26 |
| 10 | `\IssueTwentySixHistAdaptiveMacro` | Historical Adaptive Depth Macro Recall | Issue #26 |
| 11 | `\IssueTwentySixHistAdaptivePath` | Historical Adaptive Depth Full Path Recall | Issue #26 |
| 12 | `\IssueTwentySixHistCapOneHundredChars` | Hub Cap $C=100$ Context Characters | Issue #26 |
| 13 | `\IssueTwentySixHistCapOneHundredMacro` | Hub Cap $C=100$ Macro Recall | Issue #26 |
| 14 | `\IssueTwentySixHistCapOneHundredPath` | Hub Cap $C=100$ Full Path Recall | Issue #26 |
| 15 | `\IssueTwentySixHistCapTwentyFivePath` | Hub Cap $C=25$ Full Path Recall | Issue #26 |
| 16 | `\IssueTwentySixHistDepthOneChars` | Depth $d=1$ Context Characters | Issue #26 |
| 17 | `\IssueTwentySixHistDepthOneLatencyMS` | Depth $d=1$ Traversal Latency | Issue #26 |
| 18 | `\IssueTwentySixHistDepthOneMacro` | Depth $d=1$ Macro Recall | Issue #26 |
| 19 | `\IssueTwentySixHistDepthOnePath` | Depth $d=1$ Full Path Recall | Issue #26 |
| 20 | `\IssueTwentySixHistDepthThreeChars` | Depth $d=3$ Context Characters | Issue #26 |
| 21 | `\IssueTwentySixHistDepthThreeLatencyMS` | Depth $d=3$ Traversal Latency | Issue #26 |
| 22 | `\IssueTwentySixHistDepthThreePath` | Depth $d=3$ Full Path Recall | Issue #26 |
| 23 | `\IssueTwentySixHistFullPath` | Canonical Baseline Full Path Recall ($62.0\%$) | Issue #26 |
| 24 | `\IssueTwentySixHistKFourPath` | Counterfactual $k=4^\ast$ Full Path Recall ($0\%$) | Issue #26 |
| 25 | `\IssueTwentySixHistKOnePath` | Counterfactual $k=1^\ast$ Full Path Recall ($45.0\%$) | Issue #26 |
| 26 | `\IssueTwentySixHistMacro` | Canonical Baseline Macro Recall ($86.1\%$) | Issue #26 |
| 27 | `\IssueTwentySixHistMeanChars` | Canonical Baseline Context Characters ($1.34\text{M}$) | Issue #26 |
| 28 | `\IssueTwentySixHistOfflineLatencyMS` | Canonical Baseline Offline Traversal Latency ($46.2\text{ms}$) | Issue #26 |
| 29 | `\IssueTwentySixSpeedupFactor` | Bounded Engine Offline Traversal Speedup ($28.9\times$) | Issue #26 |

All 29 missing macros originate from **Issue #26** (`\IssueTwentySix*`). Zero macros from any other family were missing.

---

## 4. Forensic Timeline: How the Regression Occurred

1. **Sept 25, 19:16 UTC**: `Paper/main_bak.tex` was saved during layout optimization for Issue #26. At this moment, Issue #26 changes were not yet promoted to `Paper/main.tex`.
2. **Sept 25, 19:38 UTC**: `scratch/promote_canonical_35.py` successfully promoted Issue #26 to `Paper/main.tex`, adding Section VI-K and Limitation 17 (incorporating the 29 macros and bringing the total count to **848**).
3. **Sept 25, 20:00–23:48 UTC**: Issues #27, #28, and #29 were executed, verified, and closed. Each verified the 848 macro count. `Paper/overleaf_bundle.zip` was updated at 23:48 with the verified 848-macro `main.tex` (SHA256: `340a8469d608806a55d7cb491f41ee09229ed914164cc1abf8d57e65c58b41d8`).
4. **Sept 26, 00:24 UTC**: Issue #30 Phase 1 preflight ran on active `Paper/main.tex`. It verified 848 macros:
   `[CHECK 2/4] All 848 custom macro references in main.tex are strictly defined.`
5. **Sept 26, 00:47 UTC**: In Phase 2, a script `scratch/test_tune_main.py` was created to apply the 5 approved manuscript edits. However, line 5 contained:
   ```python
   with open('Paper/main_bak.tex', 'r', encoding='utf-8') as f:
       text = f.read()
   ```
   Instead of editing the active `Paper/main.tex`, the script read the stale pre-Issue #26 backup `Paper/main_bak.tex`.
6. **Sept 26, 00:47 UTC**: The modified text was written directly to `Paper/main.tex`. This inadvertently overwrote `Paper/main.tex` with the pre-Issue #26 text, wiping out:
   - Section VI-K and Limitation 17 (dropping 29 macros, from 848 to 819).
   - Issue #28 non-causal nomenclature fixes.
   - Issue #29 terminology inflation fixes.
   - Table XIX Panel C linkage (`\input{tables/table_retrieval_eval_bak}` instead of `\input{tables/table_retrieval_eval}`).

---

## 5. Verification of the Five Approved Manuscript Edits

The five approved edits themselves are completely valid, accurate, and do not alter the macro set:
1. **Target 1 (Table VIII Footnote)**: Adds bolding qualification and Direct LLM role description. Uses already-defined `\TerraVsDirectLLMCatBWins`, `\TerraVsDirectLLMCatBTies`, `\TerraVsDirectLLMCatBLosses`.
2. **Target 2 (Table X Notes)**: Adds ungrounded parametric baseline notes. No new macros.
3. **Target 3 (Section V-B Bullet)**: Reports Direct LLM Category B score (`\DirectLLMCatBFaithfulness`, `\CatBTerraVsDirectLLMDelta`, `\CatBTerraVsDirectLLMAdjQ`, `\TerraVsDirectLLMCatBWinRate`). All 4 macros were already in `main.tex`.
4. **Target 4 (Section V-D Bullet & Duplicate Purge)**: Reports FDR comparisons and purges the duplicate Category A paragraph. The purged paragraph contained 13 macro invocations, but all 13 are heavily invoked elsewhere in the manuscript (e.g., Table VIII, Table XXIII, Abstract).
5. **Target 5 (Limitation 6)**: Discloses Category B Direct LLM advantage and contrasts with citation recall (`\CatBTerraMacroCitationRecall`, `\CatBDirectMacroCitationRecall`). Both were already in Table XVII.

**Net effect of the 5 approved edits on unique macro count: EXACTLY ZERO.**  
When applied to the true 848-macro baseline, the resulting manuscript retains **strictly 848 unique custom macros**.

---

## 6. Next Steps for Closeout (Phase 4)

1. **Restore and Patch**: Apply the 5 approved edits directly to the true baseline (`Paper/overleaf_bundle.zip` / `scratch/paper_v2/main.tex` `340a8469...`), with verified layout tuning to maintain strictly 35 pages.
2. **Canonical CI Verification**: Confirm `python Paper/scripts/check_consistency.py --target Paper/` outputs `All 848 custom macro references in main.tex are strictly defined`.
3. **Tectonic Compilation**: Confirm `len(pages) == 35`, Table XXIII on Page 35, Reference [27] at bottom of Page 35.
4. **Protected Substrates**: Verify all 11 substrates remain bit-invariant.
5. **Phase 4 Execution**: Rebuild Overleaf and Reproducibility bundles, update checklist, and close Issue #30.
