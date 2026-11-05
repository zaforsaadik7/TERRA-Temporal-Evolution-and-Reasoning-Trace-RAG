# Phase 3 Batch 01 proposal, rev1 (append-only; still not applied)

- **Author:** Claude.
- **Date:** 2026-09-29.
- **Trigger:** `codex_to_claude/20260929-codex-0022-phase3-batch01-proposal-audit.md` (CORRECTIONS REQUIRED).
- **Unchanged:** the Batch 01 proposal and its files as delivered. This rev1 supersedes the diff variants only.
- **Status:** no working source has been modified.

## Corrections made (all of Codex's points accepted)

1. **The second "Rank 11" is fixed.** Limitation 6 (`main.tex:1057`) has a later sentence reading "While the pre-specified hypothesis test in Table XXIII (Rank 11) evaluates continuous faithfulness…". It now says **Rank 6**, which is part of B1-8.
   - After applying the edits, `p3b1_apply_rev1.py` asserts that the patched `main.tex` no longer contains "Rank 11", "0.0629" or "10/75" (fail-closed).
   - The rebuilt PDF has **0** occurrences of "Rank 11". Page 34 shows "Rank 6" in both places, and the render was inspected (`evidence/renders/rev1_full_p-34.png`).
2. **The R37 fact check now asserts rank and q.** New fact B1-F14 checks the Phase 1 R08 raw row for Direct LLM / Category D: **Rank 6**, q = 1.27×10⁻⁴, q < 0.05, Δ < 0, which favours Direct LLM. It is VERIFIED.
   - In `p3b1_facts_rev1.csv`, 23 facts are VERIFIED. The one CONFLICT is the printed stale statement being corrected: B1-F12, R37.
3. **The core-only variant is withdrawn.** It edited Limitation 6 while leaving R37's false conclusion in place. There are now only two candidates:

| Variant | Items | Limitation 6 | Dry-run result |
|---|---|---|---|
| **full (recommended)** | B1-1 to B1-8, including the B1-7 layout fix and B1-8/R37 with both rank references corrected | Fully corrected: 10/75 → 4–8/75, Δ/p/q, Rank 6 ×2 | 39 pages; PDF `7dff6dc9…`; no undefined references; box warnings 148 (baseline 156) |
| no-r37 (fallback only if you decline R37) | B1-1 to B1-4, B1-6, B1-7 | **Left entirely untouched**: B1-5 and B1-8 deferred until R37 is resolved | 39 pages; PDF `7fa5dd26…` |

The diffs are `proposal/batch01_rev1_full.diff` and `proposal/batch01_rev1_no-r37.diff`. The corrections file is unchanged: `../proposal/phase3_corrections.tex`.

## Layout debt recorded (not in this batch)

These pre-existing defects remain:
- the Table IX notes overlap the bottom row on p. 16;
- the Figure 3 value labels are tiny;
- the inter-word spacing is loose in some limitation-heading lines, for example Limitation 6 on p. 34.

They are tracked for a later layout batch and the final full-PDF review. This numeric batch does not certify the paper's overall layout or prose.

## Decisions requested

1. Approve the **full** variant, B1-1 to B1-8. This includes:
   - **B1-7**, removing the `\vspace{-5mm}` that causes the Figure 3 caption collision;
   - **accepting R37**, with the Limitation 6 correction.
2. If R37 is declined, the no-r37 fallback leaves Limitation 6 untouched.

After approval, Claude will:
1. record hashes of the affected working files;
2. apply exactly the approved variant to `TERRA_EDITORIAL_RESTART_V2/working/src`;
3. build with the original toolchain on your computer;
4. return the working-source diff, the dependency hashes, the build log, the rendered pages and the fact ledger for Codex's source-diff and PDF review.
