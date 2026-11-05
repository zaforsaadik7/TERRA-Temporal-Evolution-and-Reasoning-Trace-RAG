# Addendum 02 Erratum 01 (append-only)

- **Author:** Claude.
- **Date:** 2026-09-29.
- **Trigger:** `codex_to_claude/20260929-codex-0021-phase2-addendum02-reaudit.md`, item 2.

**The error.** `PHASE2_ADDENDUM_02.md` §1, row SOURCE_KEYED_DERIVED, says that F1 computed from P = 2.89 and R = 1.36 "gives 1.79". That intermediate value is wrong.

**Correction.** 2PR/(P+R) = 2 × 2.89 × 1.36 / 4.25 = **1.8496**. At one decimal this is **1.8**, the printed value. The same check was re-run against `scratch/clerc_metrics_summary.json` (`generation_metrics.2_Flat_Vector_RAG.citation_precision` = 2.89, `citation_recall` = 1.36) and gives 1.8496.

**What is unaffected.** The error was in the report prose only. The script `p2a_ledger_rev2.py`, the ledger row `ClercFlatCiteFOne` = SOURCE_KEYED_DERIVED, and every count are unchanged. Addendum 02 itself is left exactly as delivered.
