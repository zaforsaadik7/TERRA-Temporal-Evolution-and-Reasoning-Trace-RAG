# Phase 3 Batch 02 rev1: post-implementation report (Claude)

- **Date:** 2026-10-05. **Approval:** `user_authorizations/20261005T1500Z-user-approves-batch02-rev1.md` (rev1 in full, isolated working source only).
- **Applied to:** `TERRA_EDITORIAL_RESTART_V2/working/src`. Claude built the files from the approved rev1 apply script on a byte-exact copy of the device source and wrote them with modification-time guards. The device source was unchanged between staging and writing.

## Files written (verified by re-staging from the device)

| File | SHA256 | Line endings |
|---|---|---|
| `main.tex` | `af093e96eeaf6fe76cd7fc1e0838b7bbf88ae8910ed83bd35ce86862bde8aa55` | 1,111 → 1,112 CRLF; 16 bare LF unchanged |
| `tables/table_citation_eval.tex` | `9abd10843c3bb3a6d97fe42557d022f604408008439376e5b13016ac074dae78` | 40 CRLF, unchanged |
| `phase3_corrections_b2.tex` (new) | `69f38e25329f68e99065184ba1f279db1f5eab21cf4f910bcb6ec8be84b1a340` | LF |

These equal the planned hashes in `EXPECTED_POST_HASHES.sha256`. Pre-state copies are in `snapshot_pre/`. The Batch 01 files (`phase3_corrections.tex` 487fdb9d…, `figure_3_safety_rejection.tex` af4fdee8…, `table_refusal_breakdown.tex` 337dc7c8…) are unchanged. The three `generated_*.tex` files keep their original modification times and were not written.

## Checks

- **Build** (sandbox XeLaTeX, from the files as they now sit on the device): 39 pages, 0 undefined references or citations, 0 multiply-defined labels. The text is identical to the rev1 dry run. The PDF contains "13 hops" and "4.305 hops", and none of "resolve directly", "achieving only", "1,042", "20/20", "47.8", "4.713" or "Harmonic".
- **Facts after apply:** the original 9 of 9 VERIFIED (`p3b2_facts_post.csv`) and the rev1 4 of 4 VERIFIED (`p3b2_facts_rev1_post.csv`).
- **Not done:** the device's own compiler (Tectonic) was not run, so Codex should rebuild with it. No canonical promotion. No layout certification: the earlier layout debt (Table IX overlap, Figure 3 labels) is unchanged, and one pre-existing overfull box remains.
