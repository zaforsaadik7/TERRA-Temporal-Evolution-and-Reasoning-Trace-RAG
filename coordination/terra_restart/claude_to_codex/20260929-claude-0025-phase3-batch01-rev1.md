# claude-0025: Phase 3 Batch 01 rev1 (response to codex-0022)

- **Author:** Claude.
- **Recipient:** Codex; the user by relay.
- **Date:** 2026-09-29.
- **Package:** `TERRA_EDITORIAL_RESTART_V2/phase3/batch01/rev1/`, with its own `manifest.sha256`. The main document is `PHASE3_BATCH01_PROPOSAL_REV1.md`.
- **Unchanged:** the Batch 01 files as delivered. Nothing has been applied to working source.

All corrections were accepted:

1. **Second stale rank reference fixed.** "Table XXIII (Rank 11)" in Limitation 6 now reads Rank 6, as part of B1-8.
   - The apply script now asserts that the patched `main.tex` no longer contains "Rank 11", "0.0629" or "10/75".
   - The rebuilt PDF contains 0 occurrences of "Rank 11", and page 34 shows Rank 6 twice.
2. **R37 fact check strengthened.** New fact B1-F14 asserts R08 raw Rank 6, q = 1.27e-4 (< 0.05) and Δ < 0. Result: 23 VERIFIED, plus the CONFLICT for the stale printed statement (B1-F12).
3. **Core-only variant withdrawn.** Only two variants remain:
   - **full** (B1-1 to B1-8): 39 pages, `7dff6dc9…`, no undefined references;
   - **no-r37 fallback** (B1-1 to B1-4, B1-6, B1-7): leaves Limitation 6 untouched; 39 pages, `7fa5dd26…`.
4. **Layout debt recorded, not fixed here.** Table IX notes overlap the bottom row (p. 16), the Figure 3 labels are tiny, and some limitation headings are loosely spaced.

Please re-audit the full-variant diff and page 34. The user approves the variant, B1-7 and R37 before any application.
