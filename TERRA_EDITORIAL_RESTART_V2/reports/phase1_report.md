# Phase 1 report: read-only evidence reconciliation (R01–R32)

- Author: Claude (implementer). Auditor: Codex. Date: 2026-09-28.
- **Authorization:** `coordination/terra_restart/user_authorizations/20260928T0031Z-user-authorizes-phase1-and-graph-recalc.md`. The user wrote "I APPROVE PHASE 1" and "I APPROVE BOTH", covering Phase 1 and the R28 recalculation.
- **Scope honoured:**
  - The working/canonical manuscript, macros, datasets, raw results, bundles and checklist are unchanged.
  - No LLM/API calls were made. No project script that writes files was run.
  - All outputs are under `evidence/phase1/`, `ledgers/` and `reports/`.
  - Every correction is a **proposal** for Phase 3 item-by-item approval.
- **Method:**
  - Every number was re-derived from row-level artifacts with standalone scripts, which are saved beside their outputs.
  - Three sub-audits (P1-E, P1-F, P1-G) were delegated to sub-agents under the same read-only rules.
  - Claude re-verified their HIGH findings before accepting them: the faithfulness = mean of two judges (1750/1750); the Clopper–Pearson interval for 1/5 vs 5/5; the single trace template; the line 399 judge text; the two wrong bibliography author lists.
  - Two sub-agent runs were cut off by a rate limit and resumed. Their outputs are complete.

## 1. Headline finding: stale-run leakage

The manuscript mixes numbers from **at least three evaluation states**: canonical v2, an older ~6 Sept TERRA run, and the 10k graph. Several numbers also have no source at all. The metric/run dictionary (`ledgers/metric_run_dictionary.csv`) maps each run to the objects it feeds.

**Old-run or old-graph values still printed:**

| Printed value | Where | Actual source | Canonical v2 / current value |
|---|---|---|---|
| 56.0% TERRA bar | Fig. 3 | 42/75, old run | 46/75 = 61.3% under the same system-flag estimand (48/75 = 64% rubric) |
| "42 refusals / 31 refutations" | Table XII router note | old run | 46 system flags; 48/25/2/0 under the v2 rubric |
| 1,330 ops (3.80/q); 258 generator calls; $3.01/1k | Table XXI | old run | 1,261 non-zero stages (3.60/q); 211 calls (60.3%); modelled $5.12/1k |
| 1 of 5 chains with CI [47.8, 100] | R10 | CI belongs to 5/5 (old run) | 1/5 → [0.51, 71.64] |
| 20/20 chains | R10 | old run | 16/32 |
| 1,042 links / 6 broken | R10 | old run | 664 links / 4 broken |
| 72/75 clean Cat C refusals | R10 | old run | 75/75 |
| diameter 15 / ASPL 4.713 | Table III | 10k graph | 20k graph: 13 / 4.305 |

**Hardcoded or unsourced values:**
- Fig. 2 betweenness values (no source script; exact recomputation disagrees);
- Limitation 6's "80% from 10/75" (Direct LLM fatal errors are actually 4/75);
- temporal-probe κ 0.70 and the probe macros;
- CLERC fabrication and in-corpus/external split literals;
- Table XXI decoupled retrieval/NLI columns;
- the ">75% at 1.0" ceiling claim.

**Phase 2/3 consequence:** each number must be tied to one named run, recomputed or labelled before prose compression starts. Otherwise summarising would freeze wrong values into shorter text.

## 2. Architecture description vs deployed behavior (new R31, R32; HIGH)

**R31 (out-of-domain refusals).**
- Row-level telemetry shows that 74/75 Category C refusals, and 7 of 46 Category D refusals, happened because the hard-path context was **empty**.
- The hard-path vector query is category-filtered and returned nothing on the 20k index.
- The deterministic empty-context check then refused the query before any LLM grading (<1 ms).
- The "geometric pre-filter terminates 41/75 pre-retrieval" figure is an offline calibration; in code, the distance check only sets a router-prompt flag.
- The NLI gate does account for all 16 Category B refusals and 39 of 46 Category D refusals.

**R32 (fast path).** The fast path runs lightweight retrieval **and** the NLI gate in 110/110 rows. The text says "router + generator only", "NLI bypassed" and "0.0 ms retrieval".

**Why this matters:** these correct how the safety results are attributed, not the counts. A reviewer reading the code or data would find the mismatch.

## 3. Findings by item (full detail in `ledgers/correction_register_phase1.csv`)

**HIGH, confirmed (14 items):**

| Item | Finding |
|---|---|
| R03 | Claim matrix: 40 claims, of which 16 overclaim and 5 are unsupported |
| R04 | The "reasoning traces" are a single procedural scaffold; the domain phrase mismatches the node category in 18,247 nodes |
| R06 | Line 399 names the wrong judge |
| R08/R29 | Mixed estimands and runs; FDR raw vs clamped families unlabelled |
| R09 | CaseFacts/CLERC mislabelled columns and mismatched comparisons |
| R10 | Old-run constructs; 0.76× "lift" is a deficit |
| R12 | Benchmark templating and graph-derived gold paths; hop/node off-by-one |
| R13 | Cost and operations |
| R18 | Pilot causal wording; the "Cat D safety" metric counts refusals only |
| R21 | Two bibliography entries with wrong authors (one also has a wrong title); five citation-claim mismatches |
| R22 | Temporal-probe overstatement; unsourced κ |
| R28 | Graph metrics |
| R31, R32 | See Section 2 |

**MED/LOW, confirmed:**
- R07: edge equation;
- R11: numbers reproduce, caption and wording issues;
- R19: latency populations;
- R23: conclusion;
- R24: limitation reframe;
- R25: hardcoded cross-references.

**Proposed, needs Codex check:**
- R30: three CRS-added OVERRULES edges look mis-resolved by the fuzzy matcher.

**Open (editorial or decision, out of Phase 1 evidence scope):** R01, R02, R05 (not audited; carried forward), R14–R17, R20, R26, R27.

## 4. What reproduced cleanly (safe to keep)

- Table III, except diameter/ASPL.
- Panel A refusal counts for all five systems.
- Both FDR families.
- All obscure-suite inferential statistics.
- The 20k edge counts.
- The benchmark SHA.
- Latency medians and percentiles.
- Router accuracy counts.
- CaseFacts Overruled CIs and judge concordance.
- Table X sensitivity (raw vs clamped).

## 5. Risks and blocked items

1. **Temporal probe (R22) is partly BLOCKED.** No per-row probe data exists, and the only summary file conflicts with the macros.
   - **Options:** (a) find the per-row file on the device; (b) present the probe as unreproducible and qualify it heavily; (c) move it to limitations.
   - **Decision owner:** user, in Phase 3.
2. **Pipeline code is not version-pinned.** `ask_terra.py` post-dates the run. Findings R31/R32 therefore rest primarily on telemetry, with code as corroboration.
3. **Page budget impact.** The corrections are mostly substitutions and qualifiers, so they add almost no length. R31/R32 add about one limitation paragraph. The 25-page target is unaffected in direction.
4. **Scope creep.** Regenerating Table XXI and the R10 values is a pure read of existing data, not a new experiment. It still needs Phase 3 approval because it changes macros.

## 6. Recommended next step (requires the user's decision)

- **Codex audit** of this Phase 1 package, especially R30, R31, R32 and the sub-agent findings.
- **Then Phase 2** (per the V2 plan), once the user approves it.
  - Suggested entry condition: a single "number provenance" freeze. Every printed number is mapped to RUN-V2-CANON, a labelled other run, or BLOCKED before any compression.
