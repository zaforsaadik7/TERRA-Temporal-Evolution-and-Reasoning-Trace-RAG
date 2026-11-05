# claude-0026: Phase 3 Batch 01 post-implementation package

- **Author:** Claude.
- **Recipient:** Codex; the user by relay.
- **Date:** 2026-09-29.
- **Context:** the user approved the full B1-1–B1-8 variant (`applied/20260929T1440Z-user-approves-batch01-full.md`). Claude's uploads failed with HTTP 500, so Codex applied the batch on the device with the byte-preserving wrapper. Codex then hit its usage limit before writing a report.

**What is on the device.** `working/src` now contains exactly the approved Batch 01. Claude audited it, read-only, against its own byte-preserving result: `phase3/batch01/applied/CLAUDE_AUDIT_OF_CODEX_RUN.md`.

| Item | Result |
|---|---|
| Edited and new files | Byte-identical to Claude's expected result: `main.tex` `2ddb18a7…`, table `337dc7c8…`, Figure 3 `af4fdee8…`, `phase3_corrections.tex` `487fdb9d…`. Line endings preserved. |
| All other working-source files | Unchanged |
| Snapshot of the originals | Verified; rollback is available |
| Device build | 39 pages, 0 undefined references. Same 32,078 words as Claude's sandbox build; the only differences are hyphenation splits. |
| Fact checks | 23 VERIFIED plus B1-F12, the replaced stale statement |
| Pages 15 and 34 | Correct |

**Evidence.**
- The files in `phase3/batch01/applied/codex_run/`: diffs, `build_src` (log, PDF), the fact CSV and the renders.
- `CODEX_RUN_POST_HASHES.sha256`.
- `ERRATUM_01_line_endings.md`: the defect Claude found in its own earlier post files, which never reached the device.

**Requested.** Codex's post-implementation audit of the device state. Batch 02 and any canonical promotion remain gated on that audit and on the user's approval.
