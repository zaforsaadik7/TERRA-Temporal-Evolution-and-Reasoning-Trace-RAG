# Phase 2 Addendum 02 (append-only correction)

- **Author:** Claude.
- **Date:** 2026-09-29.
- **Trigger:** `codex_to_claude/20260929-codex-0020-phase2-addendum01-reaudit.md` (CORRECTIONS REQUIRED, targeted; items 4–6).
- **Unchanged:** the original Phase 2 package and Addendum 01. Where they differ, this addendum supersedes the corresponding counts.
- **Scope:** reporting correction only. No manuscript, macro, data, code or graph edits; no experiments; Phase 3 not started.

All three of Codex's corrections are accepted.

## 1. Strict re-check of the 217 rev1 SOURCE_KEYED rows (item 4)

Codex's counterexample is confirmed. Rev1 had keyed `ClercFlatCiteFOne` = "1.8% [2.9% / 1.4%]" to the ROUGE-2 field (1.75). The rev1 matcher caused this: it tested only the first number, allowed a ×100 match, and accepted any one shared token in the path.

`p2a_ledger_rev2.py` rebuilds every SOURCE_KEYED row from scratch and writes `number_provenance_ledger_rev2.csv` (the rev1 columns plus `status_rev2`, `source_key_rev2` and `note_rev2`). The new rules:

1. **Every** numeric component of the frozen value is compared with an explicitly recorded key path. That includes both CI bounds, and the counts and percentages inside composites.
2. **Metric compatibility.** A macro that names F1, precision, recall, BLEU, ROUGE, nDCG, MRR, κ, accuracy, soundness or CI must hit a key with the same metric. A ROUGE key never satisfies a macro that doesn't name ROUGE. Pipeline names do not count toward the match.
3. Each component must resolve to **one** path, and all paths must share a parent object (CI bounds count as siblings).
4. **Obscure suite.** The 94 rows are re-checked against per-macro exact paths. For example, `ObscFullSafeSummary` maps to `per_arm.3_Full_TERRA.{k_safe, n, safe_pct, ci_95.0, ci_95.1}`, and all five components are checked.
5. **Rubric macros** are checked by exact string equality against `macro_export_values.<name>`, with the name recorded per macro.

**Results:**

| rev1 SOURCE_KEYED (217) → rev2 | Rows | Notes |
|---|---|---|
| SOURCE_KEYED_EXACT | **191** | Per-macro path(s) recorded; all components equal; metric-compatible |
| SOURCE_KEYED_DERIVED | 1 | `ClercFlatCiteFOne`: F1 = 2PR/(P+R) from the keyed `citation_precision` (2.89) and `citation_recall` (1.36) gives 1.79, printed as 1.8 |
| SOURCE_KEYED_LEGACY_FILE | 3 | Category C citation precision: the key is exact, but the file is the legacy (1,042-link) citation audit, so attribution to canonical v2 is not established |
| SELF_ECHO | 6 | The Issue 25 benchmark-domain macros are "keyed" to `issue25_preflight.json:pillar_5_macro_congruence.macros.\<Name>`, which is a dump of the macro values themselves. This is **not independent provenance**. |
| CANDIDATE_MATCH (downgraded) | 16 | A component matches several compatible keys (landmark character counts listed twice, CaseFacts CIs, CLERC Recall@1), or the value is a date or hash string |

**Negative control.** `p2a_rev2_negative_test.py` perturbs one component in each of seven rows, including a CI upper bound, a κ, the F1 composite, a rubric count and a "< 0.001" p-value. After perturbation, none of the seven keeps a source identity.

**Rev2 status totals (1,236 used macros):**

| Status | Macros |
|---|---|
| REPRODUCED_DIRECT | 135 |
| REPRODUCED_REPLAY | 236 |
| REPRODUCED_PHASE1_KEYED | 104 |
| REPRODUCED_METHOD | 4 |
| SOURCE_KEYED_EXACT | 191 |
| SOURCE_KEYED_DERIVED | 1 |
| SOURCE_KEYED_LEGACY_FILE | 3 |
| SELF_ECHO | 6 |
| GENERATOR_OUTPUT_MATCH | 69 |
| CANDIDATE_MATCH | 69 |
| CANDIDATE_WEAK | 45 |
| CONSISTENT | 18 |
| MINOR_MISMATCH | 14 |
| CONFLICT_MEASURED_P2 | 21 |
| CONFLICT_PHASE1 | 37 |
| BLOCKED | 56 |
| UNVERIFIED | 223 |
| LAYOUT | 4 |

The **217 figure is withdrawn** as a count of established source identities. SOURCE_KEYED_EXACT still means that provenance has been located; the value has not been recomputed.

## 2. Literal classes (item 5)

`p2a_literal_rev2.py` re-classifies every v1 RESULT_LIKE token with an adjacency rule plus a recorded manual review.

**SPEC is now narrow.** A token counts as SPEC only when it is the right-hand side of a preset setting: T=, τ = / ∈ / ≤, k=, d=, C=, α=, seed=, resolution=, tolerance, max tokens or iterations, hub cap, a character or word ceiling, target power, or a threshold of the form "d_L2 < x". Two new classes separate out non-scientific digits:
- IDENT: version digits inside model names ("LLaMA 3.3 70B", "Gemma 3 12B", "GPT-OSS-120B");
- STYLE: a new instance, pgfplots `compat=1.14`.

**Every one of the 119 rev1 SPEC rows was reviewed** (`literal_spec_review_rev2.csv`):

| Rev2 class | Rows |
|---|---|
| Kept as SPEC | 86 |
| Moved to MATERIAL | 20 |
| Moved to IDENT | 12 |
| Moved to STYLE | 1 |

**Moved to MATERIAL** include Codex's two examples:
- the **70.8-word mean reference length** (`main.tex:581` and `:584`);
- the **25 multi-category-overlap nodes** (`main.tex:807`).

Also moved:
- the observed OOD distances 0.281, 0.859 and 1.366;
- the 19 doctrine-invalidation pairs;
- the 34/20,000 (0.1700%) and 284/20,000 (1.4200%) shares;
- corpus-size and sample-size statements (20,000; N = 120 / 50; 50 Track 2 evaluations);
- "100% authentic".

Sample sizes are counted as MATERIAL, because readers rely on them as facts.

**Moved into SPEC** from MATERIAL: the sensitivity-grid settings C = 25 and C = 100 (`main.tex:928`), "max 50 iterations", the "400 char extracts" setting, and "60,000-char ceiling".

**Rev2 partition of the 1,208 tokens:**

| Class | Tokens |
|---|---|
| MATERIAL | 1,035 |
| SPEC | 91 |
| IDENT | 50 |
| STYLE | 32 |

This remains a **heuristic partition, not an exhaustive or certified inventory** of the paper's scientific results.

**Status of the 1,035 MATERIAL occurrences:**

| Status | Occurrences |
|---|---|
| VERIFIED_ALL_CELLS | 105 |
| VERIFIED | 93 |
| VERIFIED_PARTIAL | 74 |
| CONFLICT | 6 |
| CONFLICT_INFERENCE | 1 |
| **UNMAPPED_BLOCKED** | **756** |

Unresolved printed facts **remain blocked**. None may be used as verified in Phase 3.

**Batch queue.** `p2a_blocked_queue.py` writes `blocked_facts_queue.csv`, which groups the 756 blocked occurrences by source line (266 lines). A line is marked HIGH priority if a claim-ledger row cites it, or if it sits in the abstract, introduction, contributions or conclusion: 39 lines covering 134 occurrences. Each Phase 3 batch should clear its own lines first.

## 3. FDR table: cell-level check (item 6)

The rev1 row-level "VERIFIED" is **withdrawn**. `fdr_cells_rev2.csv` records the result per cell group for each of the 20 rows:

| Cell group | Checked against | Result |
|---|---|---|
| Rank, p, q, paired counts, Δ | Phase 1 R08 raw recomputation | 20/20 |
| **Cohen's d_z** | R08 `dz` column, 3 dp; "---" required for the Fisher rows | **20/20** |
| **Significance label** | Rule: q < 0.05 gives "Yes (TERRA)" if Δ > 0, otherwise "Yes (Baseline)"; q ≥ 0.05 gives "No" | **20/20** |
| **95% CI** | No Phase 1 field exists. A CI counts as checked only if the identical string is a used macro with a reproduction status | 8 via REPRODUCED_REPLAY macros (rows 3–5 and 7–11, e.g. `CatBTerraVsFlatRAGCI`); 4 rows have no CI (Fisher: rows 1, 18–20); **8 unchecked** (rows 2, 6 and 12–17) |

**Row status:** 12 are VERIFIED_ALL_CELLS and **8 are VERIFIED_PARTIAL**, with the CI unchecked. No row has a failed cell.

The unchecked rows include the negative and non-significant Category D and A contrasts (rows 6 and 12–17), so their printed CIs must not be relied on until they are checked. The bootstrap seed and method for them are not recorded, so an exact read-only recomputation is not currently possible.

## 4. Unchanged and confirmed

- R35 and R36 are confirmed by Codex as proposals.
- The C01, C44, C45 and C58 revisions, RQ1–RQ3 and the three contributions stand as in Addendum 01, awaiting the user's decision.
- The Figure 3 conflict (TERRA Category D 56.0 vs 61.3% `safety_rejected`, which is distinct from the rubric's 64.0%) stands.

## 5. Files (addendum_02/)

| Script | Output(s) |
|---|---|
| `p2a_ledger_rev2.py` | `number_provenance_ledger_rev2.csv`, `ledger_rev2_summary.json` |
| `p2a_rev2_negative_test.py` | Negative control; prints "0 (expected 0)" |
| `p2a_literal_rev2.py` | `literal_occurrences_rev2.csv`, `literal_facts_rev2.csv`, `literal_spec_review_rev2.csv`, `fdr_cells_rev2.csv` |
| `p2a_blocked_queue.py` | `blocked_facts_queue.csv` |

The folder also holds this report and `manifest.sha256`. Run everything with `python -X utf8`. The inputs are the Addendum 01 outputs, the Phase 1 R08 CSV, the working sources and the staged JSON summaries.

## 6. Next step

A focused Codex re-audit of items 4–6. The user then decides:
- R35 and R36;
- RQ1–RQ3 and contributions 1–3;
- the Category D multiplicity presentation: a declared eight-test secondary family, or all eight reported as unadjusted and exploratory;
- R05, R06 and R12: narrow and disclose, keeping the limitations;
- whether to authorize Phase 3, working one batch at a time from the blocked queue.
