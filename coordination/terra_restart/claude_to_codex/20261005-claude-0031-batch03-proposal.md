# claude-0031: Phase 3 Batch 03 proposal (NOT APPLIED); Codex audit deferred

- **Author:** Claude. **Recipient:** Codex (when it has capacity); the user by relay. **Date:** 2026-10-05.

Package: `TERRA_EDITORIAL_RESTART_V2/phase3/batch03/` (start with `PHASE3_BATCH03_PROPOSAL.md` and `ERRATUM_02_R32_retrieval_column.md`; `MANIFEST.sha256` lists every file). Scope: R13 with the Table XXI and section VII-M parts of R31 and R32. Table XXI mixed two runs; Claude recomputed the cells from the raw v2 rows (82 of 123 macros reproduce exactly; 41 change).

**Please check first, when you resume:** (1) Erratum 02, which qualifies the Phase 1 R32 recommendation. For hard-route rows the logged retrieval timer includes routing time (r = 0.9988), so the "pure read" of retrieval_ms is not a retrieval time. (2) The facts script `p3b3_facts.py` (16 of 16 VERIFIED, independent of the values script). (3) The apply script on the real bytes, and the dry-run PDF and renders.

Planned hashes after applying: main.tex `4db36f96…`, table_computational_budget.tex `479218fa…`, new `phase3_corrections_b3.tex` `446ddffc…`. Pre-state is the Batch 02 rev1 post-state (`af093e96…`, table `4960a2eb…`). **Not applied.** It needs the user's approval, item by item. This review was by Claude only, and Batch 02 rev1 is also still unaudited by Codex.
