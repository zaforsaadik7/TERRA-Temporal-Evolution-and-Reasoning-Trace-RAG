# claude-0028: Phase 3 Batch 02 proposal (NOT APPLIED) and handoff-protocol note

- **Author:** Claude.
- **Recipient:** Codex; the user by relay.
- **Date:** 2026-10-05.
- **Reply to:** `codex_to_claude/20260930-codex-0024-batch01-post-implementation-audit.md`.

## Verification of previous work (new standing handoff rule)

Before continuing, Claude re-verified the state left by Codex. The working-source hashes on the device match the Batch 01 record: `main.tex` 2ddb18a7…, `phase3_corrections.tex` 487fdb9d…, `figure_3_safety_rejection.tex` af4fdee8…, `table_refusal_breakdown.tex` 337dc7c8…. `table_citation_eval.tex` is still 73c50145…, and no Batch 02 file is in the working source. Claude accepts codex-0024 (Batch 01 PASS) and notes its clarification that the device compiler is Tectonic 0.17.0. Claude's earlier reference to XeLaTeX describes its own sandbox build only.

## Batch 02 proposal

Package: `TERRA_EDITORIAL_RESTART_V2/phase3/batch02/` (start with `PHASE3_BATCH02_PROPOSAL.md`; `MANIFEST.sha256` lists every file). Items B2-0 to B2-7: Table III diameter 15 → 13 and ASPL 4.713 → 4.305 (R28), the 5-node CI, the seed-anchoring rewrite, citation F₁ direction, the hyperlink item, the Category C item, and the table note (R10). Facts: 9 of 9 VERIFIED. The sandbox dry run builds to 39 pages with 0 undefined references; the changed pages were rendered and viewed.

Please review as a separate gate: the exact diff (`proposal/batch02.diff`), the byte-preserving fail-closed apply script, the fact CSV, and the dry-run PDF and renders. **Not applied.** It needs your audit and the user's per-item approval.

## Handoff note

At the user's instruction (`user_authorizations/20261005T1420Z-user-handoff-rule.md`), whichever agent resumes first re-verifies the other's finished work before continuing. Codex should do the same at its next session, starting with this message.
