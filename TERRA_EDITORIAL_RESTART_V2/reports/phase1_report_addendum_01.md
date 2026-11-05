# Phase 1 report, Addendum 01: corrections after the Codex audit (codex-0010)

- **Author:** Claude.
- **Date:** 2026-09-28.
- **Scope:** reporting corrections only.
- **Unchanged:** `phase1_report.md`, which is kept unmodified (append-only). No manuscript, macro, dataset or graph change was made.
- **Superseding ledger:** `ledgers/correction_register_phase1_rev1.csv` supersedes `correction_register_phase1.csv`, which is kept.

I checked each Codex point against the stored evidence before accepting it. All five are accepted.

## C1. The "method" sentence was overbroad (accepted)

**Replaced sentence** (§ Method): "Every number was re-derived from row-level artifacts".

**Corrected statement:**
- The numbers **examined** in Phase 1 were re-derived from row-level artifacts wherever such artifacts exist.
- Several reported values could **not** be re-derived and remain unsourced or unverifiable:
  - temporal-probe macros and κ 0.70 (R22);
  - Figure 2 centrality values (R28);
  - Table XXI decoupled retrieval/NLI timings (R32);
  - CLERC fabrication and in-corpus/external literals (R09);
  - the ">75% at 1.0" ceiling claim (R24);
  - Limitation 6's "10/75" (R08).
- Findings from sub-agent audits and Codex spot checks are **not** a line-by-line certification of every R01–R32 claim.

## C2. R28 10k provenance (accepted; the measured results are unchanged)

- Amendment 1 of the frozen method named the wrong 10k validation file, because it compared listed edges with unique edges.
- The **current** 10k index reproduces 15/4.713 exactly. See `evidence/phase1/R28/R28_METHOD_AMENDMENT_3_POSTHOC.md`.
- The 20k result stands: diameter 13, ASPL 4.305.
- A replacement in the paper requires an explicit statement of the graph definition.

## C3. R31/R32: observed facts separated from inference (accepted)

**Observed (high confidence), from row-level telemetry:**
- 74 of 75 Category C rows have empty context and <1 ms grading.
- All 75 Category C rows show positive retrieval time.
- 7 of 75 Category D rows have empty context.
- All 110 EASY-route rows show positive retrieval **and** grading time.
- The 8 fast-path Category D refusals are recorded as `NLI_REFUSAL_GATE`.

These observations alone contradict the paper's deployed "pre-retrieval stop" and "no retrieval / NLI bypassed" fast-path descriptions.

**Inferred (provisional), from post-run code dated 26 Sept:**
- that the empty-context branch fired;
- that no NLI call was made for those rows;
- that category-filtered vector retrieval returned no candidates.

I withdraw my Phase 1 report wording that stated the mechanism as fact (§2: "because the hard-path context was **empty** … returned nothing"). The mechanism stays provisional until a version-pinned 14 Sept code or run trace is found. I will not claim that every hard-path vector query returned zero candidates.

## C4. R30 upgraded to a data-integrity blocker (accepted)

**Codex source check:**
- The CRS overruling table lists **Collins v. Hardyman** (not Frisbie v. Collins) for Griffin v. Breckenridge.
- For Edelman v. Jordan it lists **Wyman v. Bowens** among others (not NLRB v. Wyman-Gordon).
- The Hensley opinion showed no support for the Norwood v. Baker edge on the text search performed.

**My position:** the Griffin/Collins and Edelman/Wyman relationships agree with my own understanding of these decisions. However, I did not re-fetch the sources, so this is corroboration, not independent verification.

**Status:** BLOCKER-OPEN for any claim that depends on OVERRULES case identity. That includes the obscure-precedent suite, Category D items that rely on overruling edges, and the 56-edge OVERRULES count.

**Proposed next step** (needs a separate user approval; read-only):
1. Map each source citation to its canonical case ID for the 3 added edges.
2. Do the same for the 53 retyped edges.
3. Run a bounded downstream-impact analysis.

No edge is removed or edited without a separate approval.

## C5. Unsourced metrics stay BLOCKED (accepted)

The proposed Phase 2 "number provenance freeze" **classifies** each printed number as v2, other labelled run, or BLOCKED. It does **not** verify BLOCKED numbers.

- R22 (temporal probe) is marked BLOCKED in rev1.
- The other unsourced values listed in C1 are handled the same way: each must be relabelled, removed with the user's approval, or given a source before it can be printed as a result.

## Revised status

- **Phase 1 evidence work:** complete. Report corrections are applied through this addendum and the rev1 register.
- **Open blockers:**
  - R30 (OVERRULES identity);
  - R22 (temporal probe);
  - the R31/R32 mechanism (provisional; the observations stand).
- **Phase 2:** not started and not authorized.
