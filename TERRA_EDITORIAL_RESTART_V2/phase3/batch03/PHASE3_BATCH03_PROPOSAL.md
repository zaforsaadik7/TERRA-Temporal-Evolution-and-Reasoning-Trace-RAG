# Phase 3 Batch 03 proposal: Table XXI and section VII-M regenerated from the canonical v2 run (NOT APPLIED)

- **Author:** Claude. **Date:** 2026-10-05.
- **Basis:** Phase 1 register **R13** (cost and operations), with the Table XXI and section VII-M parts of **R32** (fast-path composition) and **R31** (the geometric pre-filter did not stop queries in the deployed run). The Phase 2 ledger already marks these cells as conflicts with the v2 measurements (CONFLICT_PHASE1 or CONFLICT_MEASURED_P2); this batch replaces them with values recomputed from the raw v2 rows.
- **Pre-state:** the Batch 02 rev1 post-state. `main.tex` is `af093e96…`, and `tables/table_computational_budget.tex` is `4960a2eb…`. The apply script checks both hashes and fails closed otherwise.
- **Review status:** reviewed by Claude only. Codex has no capacity this week, and **its audit is deferred**.
- **Nothing is applied.** The user's approval is required, item by item.

## Why this batch exists

Table XXI Panel A mixed two runs. Its end-to-end latencies, routing, generation and tokens match v2, but its operations, generator calls and cost cells came from the older September run. The section's own prose then disagreed with the table: 1,522 operations at 4.35 per query in the text against 1,330 and 3.80 in the table, and $5.12 per 1,000 queries in the text against $3.01 in the table. The text also gave Category B's cost as "approximately one cent" per query ($0.014) and described the Category C and D operation paths (40 queries stopped by the pre-filter, query C069 and others) with counts from the old run. None of that matches the canonical v2 telemetry.

## Method (no new experiments; Claude's code reads the raw v2 rows only)

- `evidence/p3b3_values.py` recomputes all 123 macros in scope from `data/terra_canonical_v2_eval.json` (sha256 `95e775e2…`) and writes `proposal/phase3_corrections_b3.tex` with only the macros whose value changes (41, of which 5 are new remainder macros). **82 of the 123 reproduce the paper's existing values exactly**, which validates the method.
- **Operations** use the paper's own stated definition (a stage that recorded non-zero time counts). **Generator calls** count queries with non-zero generation time. **Tokens and modelled cost** use the project's own formulas (`scripts/compute_budget_and_gate_metrics.py`), applied to v2. The cost reproduces the project's own cost log (`logs/v2_nli_router_model.txt`): $5.12 overall, with $0.06, $11.74, $0.24 and $7.93 for Categories A to D.
- **Retrieval time is route-aware.** See `ERRATUM_02_R32_retrieval_column.md`.
- **Frozen files are untouched.** The override is loaded after the Batch 02 override.
- `evidence/p3b3_apply.py` is byte-preserving and fail-closed: each edit must match exactly once, and post-conditions assert that the stale strings are gone.

## What changes in the numbers

| Cell | Paper now | v2 |
|---|---|---|
| Operations per query (overall; A, B, C, D) | 3.80; 3.00, 5.00, 2.53, 4.53 | 3.60; 3.98, 3.84, 3.00, 3.39 |
| Operations, prose (total; per query) | 1,522; 4.35, and 1,330 in the table | 1,261; 3.60 |
| Generator calls (overall; A, B, C, D) | 258 (73.7%); 100, 100, 23, 35 | 211 (60.3%); 98, 84, 0, 29 |
| Modelled cost per 1,000 queries (overall; B; C; D) | $3.01; $6.76; $0.58; $4.37 (the text says $5.12) | $5.12; $11.74; $0.24; $7.93 |
| Category B cost per query; ratio to Flat | $0.014 ("about one cent"); 26× | $0.0117; 22× |
| Retrieval, Category A and overall (ms) | 0.0; 187.5 | 353.4; 288.5 |
| NLI grading, A, C, D, overall (ms) | 0.0, 295.2, 9,066.4; 4,682.4 | 4,562.8, 33.2, 6,146.1; 5,304.2 |
| Mean context, Category C and D (characters) | 7,231 and 268,682 raw | 508 and 25,928 |

The Category B, C and D retrieval values do not change, and all end-to-end latencies, routing and generation values do not change.

## Items

| Item | Location | Change | Basis |
|---|---|---|---|
| B3-0 | `main.tex` preamble | Adds `\input{phase3_corrections_b3}` after the Batch 02 override | Mechanism |
| B3-1 | Override file | The 41 macro values above, generated from v2 | R13 |
| B3-2 | `table_computational_budget.tex` | Caption, column headers ("Stage Latency", "1k Queries (Modelled)"), the notes (source file, definitions, cost model, remainder, the Category A and C facts, the $4.66 sensitivity), and the Panel B row label "TERRA Operational Setting … pre-filtered" → "Configured threshold … flagged (offline calibration)". The old note's C069 and 4/5/1-operation mechanics are removed. | R13, R31, R32 |
| B3-3 | `main.tex` cost sentence | "at a modelled $5.12 per 1,000 queries", with a statement that the cost is modelled, not metered, prices one grader call (two for refused C and D queries) for every Category B–D query and none for A, and gives $4.66 if a grader call is priced only where grading time was at least 1 ms | R13 |
| B3-4 | `main.tex` operations paragraph | The itemised 4-, 5- and 1-operation account (22 pass, 12 fail, 40 pre-filtered, C069; "exact integer closure") is replaced with a measured account. Category A ran retrieval and grading on all 100 queries; Category B ran all four stages (generator on 84); Category C made no generator calls and, for 74 of 75, had an empty context and under 1 ms of grading; Category D had 46 refusals, 7 on an empty context. | R13, R31, R32 |
| B3-5 | `main.tex` generator-call paragraph | 211 of 350 (60.3%), a 39.7% reduction against the baselines. It says the reduction comes from refusals. **It also adds an adverse fact:** the NLI grader is also a Llama 3.3 70B model and recorded at least 1 ms of grading on 276 of 350 queries, so TERRA's generator plus grader calls exceed the baselines' one call per query. | R13 |
| B3-6 | `main.tex` disclosure paragraph | "operational cost" → "modelled cost"; $0.0117 per query; 22×; "approximately one cent … to secure complete doctrinal authority" → "roughly $0.0117 per query (modelled) to recover the full precedent path on 66/100 Category B queries" | R13 |
| B3-7 | `main.tex` latency subsection | Retitled "Stage Latency Profiling". The lead no longer claims a 0.02 ms reconciliation. It states the route-aware retrieval definition and the unattributed remainder. Items 2–4 are rewritten: Category A does not bypass retrieval (353.4 ms), Category C's low NLI time reflects empty contexts, and Category C generation is 0 because no query reached the generator. | R32, R13 |
| B3-8 | `main.tex` Panel B discussion paragraph | "intercepting 54.67% … before retrieval … remaining … intercepted by downstream NLI entailment grading" → an offline calibration; no query was stopped before retrieval; all 75 Category C refusals were downstream, 74 on an empty context. Also removes "the exclusive operational responsibility of the downstream NLI Smart Grader". | R31 |
| B3-9 | `main.tex` pre-filter discussion (line ~1044) | "operational threshold … intercepting … pre-retrieval" → configured threshold, offline calibration. The "indispensable primary safety firewall" claim is replaced with the measured split: of 139 refusals, 81 on an empty context (74 C, 7 D) and 58 on a non-empty context (A 2, B 16, C 1, D 39). | R31 |

## Verification

- **Check-only** on the real device bytes: every edit matches exactly once. `main.tex` goes from 1,112 to 1,107 CRLF lines, with the 16 bare LF lines unchanged; the table keeps its 44 CRLF lines.
- **Facts:** `evidence/p3b3_facts.py` is independent of the values script. **16 of 16 VERIFIED** (`proposal/p3b3_facts.csv`), including the project's own cost log, the 66/100 figure, the route-aware evidence, and the $4.66 sensitivity.
- **Dry run** (sandbox XeLaTeX, 3 passes): 39 pages, 0 undefined references, 0 multiply-defined labels, and no new overfull boxes (the two that exist were in the Batch 02 build too). The stale strings are gone from the PDF.
- **Rendered pages** `render/dry_p30-30.png`, `dry_p31-31.png` and `dry_p32-32.png` were viewed and read correctly.
- **Planned hashes after applying:** `main.tex` `4db36f96…`, `table_computational_budget.tex` `479218fa…`, new `phase3_corrections_b3.tex` `446ddffc…`.

## Claude's adversarial review of its own draft (what it changed)

1. **The first draft would have introduced an error.** It reported raw logged retrieval means (for example 1,536.6 ms overall and 3,346.8 ms on Category C). For hard-route queries the logged retrieval timer includes routing, so those are not retrieval times. Caught by comparing against the project's script before delivery; fixed with the route-aware definition. See Erratum 02.
2. **The first draft contradicted the next paragraph.** It said the pre-filter stopped nothing, while the Panel B paragraph still said it stopped 54.67% before retrieval. B3-8 and B3-9 fix that.
3. **The modelled cost is not an upper bound.** It prices no grader call for Category A (which ran one) and prices grader calls for 74 Category C queries with under 1 ms of grading. The text says this plainly and gives the $4.66 sensitivity.

## Not covered (Batch 04 and later)

- The rest of R31 and R32: the abstract and introduction, the architecture section (~lines 125, 208–214, 246), the router section (~645), the Table VII caption (~667), the limitations (~1031, 1041–1043), and the safety-mechanism wording across the paper. **Until then other sections still describe the pre-filter and the fast path as the old design did, so the paper is temporarily inconsistent across sections.**
- R19 (the fast-path latency populations), and Table XX's note citing `terra_baselines_eval_raw.json` (R10-15).
- Layout debt, unchanged.

## Recommendation

**Approve B3-0 to B3-9.** They correct values taken from a different run, remove a contradiction between the paper's own table and text, and replace several mechanism claims that the telemetry contradicts. They make two adverse facts visible: the 70B grader calls (B3-5) and the dependence of the Category C refusals on empty contexts (B3-4, B3-8, B3-9). If you want a narrower first step, the safest subset is B3-0 to B3-3, B3-6 and B3-7; B3-8 and B3-9 should then follow, because without them the page contradicts itself. B3-5's extra sentence about the grader can be declined independently.
