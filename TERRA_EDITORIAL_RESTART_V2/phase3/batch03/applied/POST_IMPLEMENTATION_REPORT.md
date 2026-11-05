# Phase 3 Batch 03: post-implementation report (Claude)

- **Date:** 2026-10-05. **Approval:** `user_authorizations/20261005T1600Z-user-approves-batch03.md` ("approve all": B3-0 to B3-9, including B3-5's grader-call sentence). Working source only.
- **Method:** Claude re-verified the device pre-state (Batch 02 hashes and modification times), applied the approved script to a byte-exact copy, confirmed the result was identical to the proposal's diff and override, and wrote the files with modification-time guards.

## Files written (verified by re-staging from the device)

| File | SHA256 | Line endings |
|---|---|---|
| `main.tex` | `4db36f960d2bb2f3252aca50b529f6183e26e0233d672820823c90be6aa43efd` | 1,112 → 1,107 CRLF; 16 bare LF unchanged |
| `tables/table_computational_budget.tex` | `479218faac1ff570bfcb1baad568cd8ecba425ece411e31dcf08e0412326fc60` | 44 CRLF, unchanged |
| `phase3_corrections_b3.tex` (new) | `446ddffce774d0799f9064c5a2a7c7412faf45244f4dace4da463f387fac3ced` | LF |

These equal the planned hashes in `EXPECTED_POST_HASHES.sha256`. Pre-state copies are in `snapshot_pre/`. The Batch 01 and 02 files and the `generated_*.tex` files are unchanged (hashes re-read from the device: `phase3_corrections.tex` 487fdb9d…, `phase3_corrections_b2.tex` 69f38e25…, `figure_3_safety_rejection.tex` af4fdee8…, `table_refusal_breakdown.tex` 337dc7c8…, `table_citation_eval.tex` 9abd1084…, `generated_stats.tex` e4e369b7…, `generated_corpus_stats_20k.tex` b5cbef2c…, `generated_obscure_stats.tex` a836b442…).

## Checks

- **Build** (sandbox XeLaTeX, from the files as they now sit on the device): 39 pages, 0 undefined references, 0 multiply-defined labels. The two overfull boxes were already present in the Batch 02 build. The text is identical to the approved dry run, and none of the stale strings (C069, "one cent", "bypasses retrieval entirely", "reconciling with", 268,682, "indispensable", "TERRA Operational Setting") remain.
- **Override regeneration:** re-running `p3b3_values.py` on the device source reproduces `phase3_corrections_b3.tex` byte for byte (123 macros computed, 82 identical to the frozen values, 41 overridden).
- **Facts after apply:** 16 of 16 VERIFIED (`p3b3_facts_post.csv`).
- **Not done:** the device's own compiler (Tectonic) was not run, and Codex has not audited Batches 02 and 03. No canonical promotion and no layout certification. The rest of R31 and R32 is still outstanding (Batch 04), so other sections still describe the pre-filter and fast path the old way.
