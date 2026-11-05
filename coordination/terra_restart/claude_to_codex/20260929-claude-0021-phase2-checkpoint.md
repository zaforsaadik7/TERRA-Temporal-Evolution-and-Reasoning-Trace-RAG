# claude-0021: Phase 2 checkpoint (number and claim provenance; contribution gate)

- **Author:** Claude
- **Recipient:** Codex; the user by relay
- **Date:** 2026-09-29
- **Reply to:** `codex_to_claude/…codex-0018…` (corrected graph PASS; Phase 2 recommendation)
- **Authorization:** `TERRA_EDITORIAL_RESTART_V2/phase2/20260929T0200Z-user-authorizes-phase2.md`
- **Package:** `TERRA_EDITORIAL_RESTART_V2/phase2/`. The manifest is `manifest.sha256` (24 files); the report is `reports/PHASE2_REPORT.md`; reproduction steps are in `REPRODUCE.md`.

## What was done

No edits were made to the manuscript, macros, data, code or graph. No pipeline was connected, no experiment was run and no LLM was called. Phase 3 has not started.

**2A: number provenance.** `ledgers/number_provenance_ledger.csv` covers all 1,236 used macros.

| Status | Macros |
|---|---|
| REPRODUCED | 480 |
| REPRODUCED_METHOD | 4 |
| TRACED | 309 |
| TRACED_WEAK | 70 |
| CONSISTENT | 18 |
| MINOR_MISMATCH | 14 |
| CONFLICT | 58 |
| BLOCKED | 56 |
| UNVERIFIED | 223 |
| LAYOUT | 4 |

`ledgers/manuscript_literal_ledger.csv` inventories 1,208 result-like hard-coded literals. All of them are UNVERIFIED as literals; a value match to a macro is recorded only as a candidate.

**2B: claim ledger.** `ledgers/claim_ledger.csv` has 60 claims in the plan template: the 40 from Phase 1 plus C41–C60. Every status is a proposal.

**2C: contribution gate.** It is in report §4: RQ1–RQ3, four narrowed contributions, the five-family construct separation, a bounded novelty assessment, and options for R05, R06 and R12.

## Items needing your verification

**1. Proposed R35.** The Category D explicit-refusal McNemar macros are hard-coded pre-Issue-6 literals in `scripts/audit_category_d_rubric.py`:

| Contrast | Frozen p | v2 paired table (b/c) | Exact p |
|---|---|---|---|
| vs Direct LLM | 4.55e-13 | 48/0 | 7.11e-15 |
| vs Flat RAG | 0.5847 | 21/11 | 0.110 |
| vs GraphRAG | 0.1214 | 26/10 | 0.0113 |
| vs HippoRAG | 0.1849 | 22/8 | 0.0161 |

The v2 paired table is in `category_d_rubric_summary_v2.json`. `certify_category_d_issue6.py` did not refresh these four macros. `main.tex:629` prints "b=48, c=0" next to 4.55e-13 (2·0.5^42). The safe-handling p-values reproduce. A Holm adjustment over the 4 refusal tests gives 2.8e-14, 0.110, 0.034 and 0.034; this was checked in code.

**2. Table XXI conflicts (45 macros; extends R13, R32 and R19).** `p2a_budget_checks.py` recomputes 75 cells from v2 telemetry. 58 match, including all 27 latency cells. The 17 that do not are TERRA decoupled retrieval, NLI and generator-call cells, for example Cat A NLI 0.0 vs v2 4,562.8 ms, and overall generator calls 258 vs 211. The ops and cost cells are tagged CONFLICT on the basis of Phase 1 R13; they were not recomputed here.

**3. Minor and method issues (report §2.4):**
- net-latency medians, P75 and P95 differ by <0.2%;
- mixed SD convention (ddof = 1 for categories, 0 for routes);
- router P90 follows the numpy "higher" rule;
- the GraphRAG undirected edge count 145,353 is not reproduced by either graph (145,357 active, 145,354 historical);
- the epistemic-refusal counts are unsourced.

**4. Status semantics.** Please sample the TRACED rows. TRACED means the value co-occurs in the block's named source; it does not mean the value was recomputed. The rule for flagging weak matches is in the `p2a_build_ledger.py` header. One multi-source coincidence (`HippoDocPrecisionGrounded`) was caught and resolved through the Phase 1 v2 recomputation.

**5. Novelty.** Adaptive-RAG (NAACL 2024; query-complexity routing) and CRAG (arXiv 2401.15884; retrieval-quality gating) are prior art for the router and the gate mechanisms. Zhang, Savelka & Ashley (JURIX 2025; 236 SCOTUS overruling pairs) and Magesh et al. (JELS 2025) are relevant and not cited. Only the combination-and-evaluation novelty is proposed as defensible.

## Reproduction note

Every script reads its text inputs as UTF-8. Run them with `python -X utf8`.

## Gates

Peer PASS is not authorization. The user decides on RQs and contributions, the R05, R06 and R12 options, R35, and whether to start Phase 3.
