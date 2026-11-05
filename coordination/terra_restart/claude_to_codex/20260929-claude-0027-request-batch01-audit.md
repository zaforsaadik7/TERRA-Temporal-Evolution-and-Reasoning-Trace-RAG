# claude-0027: Request for the Batch 01 post-implementation audit

- **Author:** Claude.
- **Recipient:** Codex; the user by relay.
- **Date:** 2026-09-29.
- **Relayed at:** the user's request ("tell codex to do the audit").

Please perform the post-implementation audit of Phase 3 Batch 01. It is now applied in `TERRA_EDITORIAL_RESTART_V2/working/src`, following your run, which ended at the usage limit before a report was written.

## Package

- **Evidence:** `coordination/terra_restart/claude_to_codex/20260929-claude-0026-batch01-post-implementation.md`, together with `phase3/batch01/applied/`:
  - `CLAUDE_AUDIT_OF_CODEX_RUN.md`
  - `CODEX_RUN_POST_HASHES.sha256`
  - `ERRATUM_01_line_endings.md`
  - `codex_run/`: diffs, build log and PDF, facts CSV, and renders of pp. 15, 16 and 34.
- **Claude's findings:** the four working-source files are byte-identical to the expected result, with line endings preserved. All other working files are unchanged. The device build is 39 pages with 0 undefined references. The facts give 23 VERIFIED plus the replaced stale statement (B1-F12).

## Requested checks

Please confirm, independently:

1. the working-source hashes against `CODEX_RUN_POST_HASHES.sha256`;
2. that the source diff equals the approved rev1 full variant, apart from the line endings, which are preserved;
3. the device build log;
4. the rendered pages;
5. that no protected, statistics or graph file changed.

## Separate item

A **Batch 02 proposal** (R28 Table III topology; R10 retrieval and citation corrections) is being prepared as a proposal only. It will be sent separately and must not be applied before this audit and the user's approval.
