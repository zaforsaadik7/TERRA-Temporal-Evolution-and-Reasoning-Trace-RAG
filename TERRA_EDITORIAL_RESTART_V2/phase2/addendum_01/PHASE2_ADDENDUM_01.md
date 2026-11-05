# Phase 2 Addendum 01 (append-only correction)

- **Author:** Claude.
- **Date:** 2026-09-29.
- **Trigger:** `codex_to_claude/20260929-codex-0019-phase2-audit.md` (CORRECTIONS REQUIRED).
- **Unchanged:** the delivered Phase 2 report, ledgers and scripts are left exactly as delivered. Where they differ, this addendum supersedes them.
- **Scope:**
  - This is a reporting correction under the existing Phase 2 authorization.
  - No manuscript, macro, data, code or graph edits.
  - No experiments and no LLM calls.
  - Phase 3 not started.

All five of Codex's required corrections are accepted.

## 1. Number-provenance status semantics (item 1)

**What was wrong.** v1 labelled a macro TRACED when all its numeric components occurred *anywhere* in a named file. That check sometimes allowed ×100 conversion or ignored the sign, and it did not identify a key, run, population or metric. Some v1 REPRODUCED rows were no better: they came from value co-occurrence in Phase 1 recomputation *output text*.

**The fix.** `p2a_ledger_rev1.py` re-derives the status of every row into `number_provenance_ledger_rev1.csv`. The file keeps the v1 status next to the new one and adds a `source_key` column. The revised definitions are in the script header. In brief:

| Rev1 status | Meaning | Count |
|---|---|---|
| REPRODUCED_DIRECT | Recomputed in Phase 2 from canonical v2 rows, the graph or the code by a stated per-macro rule | 135 |
| REPRODUCED_REPLAY | Equals the output of the project generator re-run in a sandbox. This reproduces generator(inputs); it does not audit the generator's logic. | 236 |
| REPRODUCED_PHASE1_KEYED | Equals a *named field* of a Phase 1 read-only recomputation; the key is recorded | 104 |
| REPRODUCED_METHOD | Reproduced only under an alternative percentile or SD rule | 4 |
| SOURCE_KEYED | Equals **one** identified key path of an upstream summary whose key names agree with the macro name. The run and population are inherited from that artefact. Provenance is located, but the value is **not recomputed**. | 217 |
| GENERATOR_OUTPUT_MATCH | The Issue 26 macros equal the committed generator output `.tex` | 69 |
| CANDIDATE_MATCH | The value co-occurs in a file, but no single name-consistent key was found. **This is not provenance.** | 53 |
| CANDIDATE_WEAK | Only round values matched, or the source is ambiguous | 45 |
| CONSISTENT | Arithmetic consistency only | 18 |
| MINOR_MISMATCH | Last digit, or <0.2% | 14 |
| **CONFLICT_MEASURED_P2** | **A Phase 2 recomputation contradicts the frozen value: the 17 Table XXI cells plus the 4 R35 p-values** | **21** |
| CONFLICT_PHASE1 | Contradicted by Phase 1 evidence or register adjudication, not re-measured in Phase 2: R13 ops and cost (30), R28 (2), R10 (5) | 37 |
| BLOCKED / UNVERIFIED / LAYOUT | Unchanged | 56 / 223 / 4 |

**Transitions from v1:**

| v1 status | Rev1 status | Rows |
|---|---|---|
| TRACED (309) | SOURCE_KEYED | 217 |
| | GENERATOR_OUTPUT_MATCH | 69 |
| | CANDIDATE_MATCH | 21 |
| | REPRODUCED_PHASE1_KEYED | 2 |
| TRACED_WEAK (70) | CANDIDATE_WEAK | 45 |
| | REPRODUCED_PHASE1_KEYED | 25 |
| REPRODUCED (480) | REPRODUCED_DIRECT | 135 |
| | REPRODUCED_REPLAY | 236 |
| | REPRODUCED_PHASE1_KEYED | 77 |
| | **CANDIDATE_MATCH (downgraded)** | **32** |
| CONFLICT (58) | CONFLICT_MEASURED_P2 | 21 |
| | CONFLICT_PHASE1 | 37 |

The 32 downgraded rows are v1 "reproduced" values whose Phase 1 match was co-occurrence only.

**Spot check.** A sample of 25 SOURCE_KEYED rows from JSON sources had semantically appropriate keys, for example:
- `RouterOverallSafeHandlingRate` → `router_evaluation_summary.json:performance_metrics.overall_safe_handling_rate_pct`;
- `ClercTerraCiteRecall` → `clerc_metrics_summary.json:generation_metrics.5_Full_TERRA.citation_recall`.

**Caveat on the name-agreement heuristic.** It is token overlap, so SOURCE_KEYED should be read as "located", not "certified".

**Legacy-source rows.** Six rows keyed to `scratch/citation_correctness_summary.json` now carry a note: that file is the **legacy** (1,042-link) citation audit, so for those values attribution to the canonical v2 run is not established.

The **conflict count of 58 is unchanged**. Only 21 of those conflicts are new Phase 2 measurements; the remaining 37 rest on Phase 1 reasoning.

## 2. Literal inventory (item 2)

`p2a_literal_rev1.py` produces `literal_occurrences_rev1.csv` (occurrence level) and `literal_facts_rev1.csv` (fact level).

**Step 1: context screen of the 1,208 v1 RESULT_LIKE tokens:**

| Class | Tokens | What it covers |
|---|---|---|
| STYLE | 31 | All in figures: opacity, rotate, draw/fill mixes, aspect, axis limits, enlarge, `at={…}`, `compat` and similar |
| SPEC | 119 | Design or method parameters printed as text, such as T=0.0, τ, k, seeds, 150-word cap, corpus size |
| MATERIAL | 1,058 | Printed numeric result statements; includes the data coordinates in Figure 3 |

Of the 46 figure RESULT_LIKE tokens, 31 are now STYLE, 13 MATERIAL and 2 SPEC. That covers Codex's "at least 23".

**Step 2: MATERIAL occurrences mapped to fact IDs with a source key, population and run.** There are 66 facts.

| Fact family | Facts | Result |
|---|---|---|
| F-RB (refusal breakdown Panel A, canonical v2 `safety_rejected`) | 25 | All verified |
| F-RT (router literal cells, `route_taken`) | 6 | All verified. For the Category D row only the literal 75 and 65 are checked; the EASY cell is the macro `RouterCatDFalseEasyCount` = 10, reproduced directly. |
| F-FDR (Table full_fdr_family, against Phase 1 R08 raw-policy recomputation: rank, p, q, paired counts, Δ) | 20 | All verified. The R08 conflicts lie elsewhere, in the text, the figure and the clamped/raw labelling, not in these table cells. |
| F-FIG3 (Figure 3 bars) | 10 | 9 verified; **TERRA Category D = 56.0 conflicts with v2 61.3% (46/75), R08** |
| F-KC (known-conflict literals: Limitation 6 "10/75", "72/75", "20/20", legacy link counts, and the table-note "p = 0.0312 significant", R36) | 5 | Conflict or inference conflict |

**Occurrence status (1,058 MATERIAL tokens):**

| Status | Tokens |
|---|---|
| VERIFIED | 272 |
| CONFLICT | 6 |
| CONFLICT_INFERENCE | 1 |
| **UNMAPPED_BLOCKED** | **779** |

**UNMAPPED_BLOCKED** means the literal is not source-certified. It must not be relied on in Phase 3 until it is mapped to a keyed fact or bound to a verified macro.

The v1 `value_match` column is withdrawn as a provenance signal. It remains in v1 only as a search aid.

**Known limitation of the mapping.** Fact mapping works per token. Some tokens that belong to a conflicting statement are classed STRUCTURAL because they are ≤10 (the "10" in "10/75"), so the fact carries the conflict even where that particular token is not linked. The mapping for main-text prose is not complete: 779 occurrences remain. It is reported as incomplete, not as verified.

## 3. Literal-table summary corrected (item 3)

The Phase 2 report §2.5 said the two literal-only tables were "29/29 cells consistent". **Corrected:** `p2a_table_literal_checks.csv` records **28 MATCH and 1 CHECK**. The CHECK row is Category D in the router table, where the EASY cell is a macro and the parser could not compare all three cells.

That row was resolved separately:
- the literal 75 (N) and 65 (HARD) match canonical v2 (fact F-RT-CategoryD);
- the macro EASY value of 10 is REPRODUCED_DIRECT.

The v1 CSV is not altered.

## 4. Multiplicity: R35 and a separate safe-handling item (item 4)

**R35 (refusal tests).** This is a value correction only. The four exact McNemar results are secondary or exploratory: they lie outside the pre-specified M = 20 FDR family, which contains no McNemar rows. None may be called confirmatory without a declared family.

| Family | Adjusted p |
|---|---|
| Holm over the 4 refusal tests | 2.8e-14, 0.110, 0.034, 0.034 |
| BH over the 4 refusal tests | 2.8e-14, 0.110, 0.021, 0.021 |

The claim-ledger row C41 was revised accordingly.

**New proposed item R36 (distinct from R35): the safe-handling significance claim.** The claim appears in two places:
- `main.tex:629`: "TERRA achieves a statistically significant advantage over GraphRAG-Adapted … p = 0.0312";
- `tables/table_refusal_breakdown.tex:34`: "yielding a statistically significant safe-handling advantage over GraphRAG-Adapted (b=6, c=0, p=0.0312)".

The four safe-handling tests reproduce. They have b/c = 2/0, 5/0, 6/0 and 3/0, giving p = 0.5, 0.0625, 0.03125 and 0.25. These tests are also outside the M = 20 family.

| Adjustment | Result for the GraphRAG safe-handling test |
|---|---|
| Holm over the 4 safe-handling tests | 0.5, 0.1875, **0.125**, 0.5 (min 0.125) |
| BH over the 4 safe-handling tests | Min 0.125 |
| Holm over all 8 Category D McNemar tests | 0.156 |

The claim therefore rests on one unadjusted test chosen from a set of related comparisons. **It does not survive family-wise or FDR control.** It is registered as claim C61 (status NARROW), with the proposed wording: "73/75 vs 67/75; unadjusted p = 0.031; one of four secondary comparisons; not significant after adjustment (smallest adjusted p = 0.125)".

**The multiplicity scope needs a user decision in Phase 3.** One option is to treat all eight Category D McNemar tests as one secondary family. The other is to report them as unadjusted and exploratory. Either way, the word "significant" should go.

## 5. Claims, research questions and contributions (item 5)

**Claim ledger.** Changed rows are in `claim_ledger_rev1_changes.csv`, with the superseded wording kept. The full `claim_ledger_rev1.csv` has 61 claims.

| Claim | Change |
|---|---|
| C01 | The empty-context refusal mechanism is attributed as *supported inference* (R31), not a proven code path |
| C44 | R33 is phrased as textual *compatibility* with the fallback rule; no code branch and no backfill date is asserted |
| C45 | The three bad edges: endpoints are absent from all recorded contexts and removal changes no replayed traversal *conditional on the current code*; no categorical historical claim |
| C41 | Secondary/exploratory framing, with the family required before any adjusted claim |
| C58 | "211" is the number of **query rows reaching generation**, not an established API-call count. Ops and cost cells rest on R13 reasoning. |
| C61 | Added (R36) |

**Revised research questions.** These replace report §4.2 and are proposed only.

- **RQ1 (system-level retrieval coverage).** On 100 multi-hop precedent-evolution questions, how much of the gold precedent set does the TERRA *system* surface compared with four baseline *systems*? The systems share a generator but differ in context budget (60,000 vs 3,200–5,500 characters) and in access to curated OVERRULES edges. **These differences are confounds.** The comparison is not architecture-isolated.
- **RQ2 (observed refusal and safety trade-offs).** What refusal, safe-handling and false-refusal rates do the systems show on 75 out-of-domain and 75 false-premise queries, and on 200 in-domain queries?
  - This is descriptive. The question does not attribute outcomes to the evidence gate.
  - In the deployed run, 74 of 75 out-of-domain refusals followed empty retrieval.
  - The Category D differences are secondary, unadjusted comparisons: safe handling is not significant after adjustment, and the refusal tests are exploratory.
- **RQ3 (curated-label ablation on a 30-case suite).** On 30 obscure overruled precedents, how does safe handling change when OVERRULES labels are removed from the serialised context: Full 19/30 vs Unlabeled 8/30?
  - The preregistered primary test (Unlabeled vs Flat) was **not rejected** (p = 0.727). The Full-vs-Unlabeled contrast is a secondary, descriptive result.
  - The scope is 30 cases, judge-labelled, κ = 0.575.

**Revised contributions.** These replace report §4.3; they are proposed and narrowed, not dropped.

1. **Resource.** A citation graph of 20,000 CAP SCOTUS opinions (1850–1980, 145,366 edges, 56 OVERRULES labels of which 3 are mis-resolved).
   - The holding-coverage figures belong to the inspected file `7aa6db46`.
   - Recorded run contexts are textually compatible with raw-text fallback for many nodes.
   - Traces are template scaffolds.
2. **System.** A pipeline in which a binary router sends "hard" queries to citation-graph traversal and every answer passes an LLM-prompted evidence-sufficiency check. It is described as a design, with no mechanism-novelty claim, and positioned against Adaptive-RAG and CRAG.
3. **Evaluation with full adverse reporting.** A 350-query, four-category, five-system benchmark with dual-judge faithfulness, a four-class false-premise rubric, and the 30-case label-ablation suite.
   - Negative and null results are reported alongside the positive ones: Direct LLM higher on Category B faithfulness; citation F1 below Flat; H1 not supported; obscure primary test not rejected; safe-handling differences not significant after adjustment.
   - What was contribution 4 ("honest accounting") is now folded in here as reporting practice, as Codex advised; it is **no longer a separate contribution**.

**Holding coverage vs run-time payload.** These two are kept separate throughout: C44 covers the inspected file's coverage; R33 concerns the run-time payload.

## 6. Register status after this addendum

| Item | Status | Needs |
|---|---|---|
| R35 | Proposed; Codex confirmed the stale-value finding | User acceptance |
| R36 | Proposed (new) | Codex verification and user decision |
| R05, R06, R12 | The user's earlier preference to narrow and disclose is recorded as the default proposal | The missing-validation limitations stay visible; no experiment is authorized |

## 7. Files (addendum_01/)

| Script | Output |
|---|---|
| `p2a_ledger_rev1.py` | `number_provenance_ledger_rev1.csv`, `ledger_rev1_summary.json` |
| `p2a_literal_rev1.py` | `literal_occurrences_rev1.csv`, `literal_facts_rev1.csv` |
| `p2b_claim_ledger_rev1.py` | `claim_ledger_rev1_changes.csv`, `claim_ledger_rev1.csv` |

Also in the folder: this report and `manifest.sha256`. Run everything with `python -X utf8`; the inputs are those listed in `phase2/REPRODUCE.md`.

## 8. Next step

A focused Codex re-audit of this addendum. The user then decides on:
- R35 and R36;
- RQ1–RQ3 and contributions 1–3;
- the multiplicity scope for the Category D McNemar tests;
- whether to authorize Phase 3.
