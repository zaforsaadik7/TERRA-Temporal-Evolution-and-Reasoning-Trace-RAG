# Phase 1 evidence notes: R13, R19, R31 (new), R32 (new)

- Author: Claude (implementer)
- Status: read-only evidence. Nothing here edits the manuscript or macros. All corrections are **proposals** for Phase 3.
- Inputs (read-only):
  - `scratch/canonical_v2/terra_canonical_v2_eval.json` (sha256 `95e775e2…`, 350 `5_Full_TERRA` rows, all `_source_run = issue6_deployed`);
  - `ask_terra.py` (sha256 `0cca5cf4…`, mtime 2026-09-26);
  - `logs/v2_nli_router_model.txt`;
  - `scripts/compute_budget_and_gate_metrics.py`;
  - working `main.tex`/`generated_stats.tex` (byte-identical to the archive snapshot).
- **Caveat on the code:** `ask_terra.py` post-dates the deployed run of 14 Sept. No version-pinned copy of the pipeline code exists in `canonical_v2_reproducibility_bundle/`. Wherever a finding rests on code, it is cross-checked against **row-level telemetry**, which is authoritative for what actually ran.
- Script: `r31_deployed_path_audit.py`. Output: `r31_deployed_path_audit.json`.

## R31 (NEW, HIGH): how Category C and part of Category D were refused in the deployed run

**Telemetry (per category, TERRA):**

| Category | n | Refused (`safety_rejected`) | Empty context | Refused ∧ empty | Grading < 1 ms | Route |
|---|---|---|---|---|---|---|
| A | 100 | 2 | 0 | 0 | 0 | EASY 100 |
| B | 100 | 16 | 0 | 0 | 0 | HARD 100 |
| C | 75 | 75 | 74 | 74 | 74 | HARD 75 |
| D | 75 | 46 | 7 | 7 | 0 | HARD 65, EASY 10 |

**Mechanism.**
- In `ask_terra.py` the hard-path vector query is filtered to `category == "civil_rights"` (the "v43" comment dates it to the 10k corpus).
- Every hard-path row with no exact-title seed has an **empty** context. That covers all 74 empty Category C rows and the 7 empty Category D rows (D027, D044, D051–D053, D055, D056).
- The single non-empty Category C row (C047, the Paris 2024 medal count) has a context made **only** of an exact-title seed. The substring "The United States" matched a 1904 case titled *The United States*.
- **Inference:** in the deployed 20k run, the category-filtered hard-path vector retrieval contributed no documents. Hard-path context came from exact-title seeding, the abstract seed map, and graph expansion.
- The obscure-suite limitation (main.tex line 1061) already says: "category-filtered vector retrieval returned no candidates". This is the same effect, surfaced there but not in the main-benchmark narrative.
- `smart_grader()` fails any empty or <50-character context deterministically, before any LLM call. This explains the <1 ms grading.

**Manuscript statements this qualifies:**

1. **Tier 2 geometric pre-filter** (lines 208–213, 984, 1009). The paper says 41/75 Category C queries "exceed the geometric proximity boundary and are terminated immediately pre-retrieval, incurring only 1 operation each".
   - In the code, the d<sub>L2</sub> < 1.3 check (`is_query_in_domain`) only sets a "Domain Relevance Flag" string in the router prompt. It terminates nothing.
   - In telemetry, all 75 Category C rows have `retrieval_ms` > 0 (mean 3,347 ms).
   - The 41/75 figure is an **ex-post calibration** of the threshold (Table XXI Panel B), not deployed behavior.
2. **"Tier 3 NLI grader = primary safeguard"** (line 214) and the defense-in-depth claims (lines 246, 1031). For Category C, 74/75 refusals came from the deterministic empty-context check, not from semantic entailment. For Category D, 7 of the 46 refusals did too.
3. **Table XXI operation counts** (Category C = 2.53 ops/query, 23 generator calls) are from the pre-v2 Sept-6 accounting. In v2, Category C made 0 generator calls.

**Proposed Phase 3 correction** (wording to be approved item by item):
- Describe the deployed Category C behavior factually: out-of-domain queries produced no retrievable context under category-filtered retrieval plus exact-title seeding, and the deterministic empty-context gate refused them.
- Report the geometric threshold analysis as an offline calibration of a *candidate* pre-filter, not a deployed stage.
- Keep the NLI gate's role for non-empty contexts: all 16 Category B refusals, and 39 of the 46 Category D refusals (including the 8 fast-path Category D refusals).
- Add a limitation: the out-of-domain safety result depends on retrieval returning nothing, which is a corpus/filter property, not a verified semantic judgement.
- **Severity: HIGH.** This touches a headline safety mechanism. It changes how a result is attributed, not the counts.

## R32 (NEW, HIGH): what the fast path executes

**Manuscript statements:**
- Table VII caption (line 667): the fast path "executes router inference + generator only, no retrieval".
- Router section (line 645): "misroutes … sent to the fast path, where NLI grading is bypassed".
- Line 999: "Category A fast path bypasses retrieval entirely (0.0 ms)".
- Table XXI shows Category A decoupled retrieval = 0.0 and NLI = 0.0.

**Deployed code and telemetry:**
- The fast path is commented as "LIGHTWEIGHT RETRIEVAL + NLI VERIFIED". It runs an unfiltered top-2 vector query plus exact-title case records, then `smart_grader()`.
- All 110 EASY rows have `retrieval_ms` > 0 (median 289 ms) and `grading_ms` > 0 (median 2,324 ms).
- All 110 contexts contain `[VERIFIED CASE RECORD]` and trace lines.
- The 8 flagged fast-path Category D refusals **are** NLI-gate refusals (`NLI_REFUSAL_GATE`). So line 645 contradicts itself.
- Category A v2 means: retrieval 353.4 ms and NLI 4,562.8 ms, versus 0.0/0.0 in Table XXI.

**Table XXI provenance (mixed within one table):**

| Values | Source |
|---|---|
| End-to-end mean/median/p95, routing, generation and tokens | Match v2 exactly |
| Retrieval column (overall 187.5 ms vs v2 1,536.6) | No v2 source |
| NLI for A/C/D (0.0 / 295.2 / 9,066.4 vs v2 4,562.8 / 33.2 / 6,146.1) | No v2 source |
| Ops, generator calls, cost | Pre-v2 |

- The generator script `compute_budget_and_gate_metrics.py` hardcodes decoupled values that differ from **both** the frozen macros and v2 (e.g. overall retrieval 308.1).
- Cat B NLI 9,367.2 matches v2.

**Proposed Phase 3 correction:**
- Describe the fast path as "router → lightweight retrieval (top-2 + exact-title record) → NLI gate → generator".
- Regenerate the Table XXI decoupled columns from v2 telemetry (a pure read of `timing`).
- **Severity: HIGH** (a factual description of the architecture).

## R19: fast-path latency populations (confirmed; resolution proposed)

| Quantity | Value | Population |
|---|---|---|
| `\TerraFastPathMedianSeconds` 5.83 s | Category A median (N=100) | Labelled "fast path" in the abstract, intro and architecture (lines 115, 146) |
| `\TerraHardPathMedianSeconds` 17.94 s | Category B median (N=100) | Labelled "multi-hop precedent chains" |
| `\TerraFastRouteMedianS` 5.46 s | EASY route (N=110) | Line 703 |
| `\TerraHardRouteMedianS` 14.07 s | HARD route (N=240) | Line 703 |
| `\AblationFullLatencyMedianSeconds` 1.38 s | Full config in the **10-query pilot ablation** | Line 526: "fast sub-two-second execution" |
| `\AblationRouterLatencySlowdownFactor` 4.90× | 6.75 / 1.38, pilot-internal | |

**Proposed:**
- Label 5.83/17.94 as Category A / Category B medians, or switch to the route medians 5.46/14.07. Pick one population and use it consistently.
- Scope "sub-two-second" and 4.90× to the pilot ablation. Note that the main-run Category A median is 5.83 s, under concurrent execution with 429 back-off (already disclosed at lines 703 and 1067).

## R13: cost and operations (recap of confirmed values)

- **Table XXI:** $3.01/1k overall and $6.76 Category B, 1,330 ops / 3.80 per query, and 258 generator calls (73.7%). All are **pre-v2** (Sept-6 run).
- **v2 modelled cost** (`logs/v2_nli_router_model.txt`): $5.12/1k overall.

  | Category | Cost per 1k |
  |---|---|
  | A | $0.06 |
  | B | $11.74 |
  | C | $0.24 |
  | D | $7.93 |

  These are **modelled** from chars/4 token estimates at the assumed Databricks per-million-token prices, not metered.
- **v2 generator calls:** 211/350 (60.3%). A 98, B 84, C 0, D 29.
- **v2 non-zero-stage operations:** 1,261 (3.60/query). A 398, B 384, C 225, D 254.
- The "1,522 / 4.35" figure elsewhere is a theoretical operation model (`scratch/analyze_w3_ops.py`), not measured.
- **Proposed:** regenerate the Table XXI Panel A ops, generator-call and cost cells from v2. Label cost as "modelled at list prices". Retire the "$0.014 per query" phrase (it is wrong even under the old values, which give $0.00676).
