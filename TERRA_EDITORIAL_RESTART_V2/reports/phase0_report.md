# Phase 0 report — identity, venue, isolation, baselines

- Implementer: Claude. Independent audit requested from Codex.
- Authorization: user turn "I APPROVE PHASE 0" (recorded in `coordination/terra_restart/user_authorizations/20260927T2338Z-user-authorizes-phase0.md`)
- Date: 2026-09-27/28 (UTC/Dhaka)
- Scope honored: no manuscript text, statistics, dataset, bundle, checklist, `CANONICAL_ARCHIVE/` or `Paper/` file was modified. All writes went to the new `TERRA_EDITORIAL_RESTART_V2/` and to `coordination/`.

## 1. Identity (V2 task 0.1)

- **Canonical manifest:** 27/27 active and baseline-PDF files in `CANONICAL_ARCHIVE/canonical_manifest.json` matched SHA256 when staged. The two historical bundles were deliberately not copied (not build inputs).
- **Pinned identities:** the seven pinned identities in `evidence_manifest.json` still match (main.tex 31db54c4…, main.pdf 757ad2ec… 39 pages, generated_stats.tex e4e369b7…).
- **Snapshot and working copy:** `archive_snapshot/` and `working/src/` are byte copies. `diff -r` reports them identical. Per-file hashes are in `manifests/phase0_manifest.sha256`, and on-disk verification after transfer is recorded in §6.

## 2. Page rule and venue (tasks 0.2–0.3)

- **Working rule (user/advisor, agreed with Codex):** the complete main PDF must be **≤ 25 pages**, including references and any appendix. There is no supplement.
- **Venue:** not chosen. `reports/phase0_venue_shortlist.md` lists candidates checked against official guidelines:
  - Information Processing & Management, Expert Systems with Applications, IEEE Access (21–25 pages needs EIC permission) and Artificial Intelligence and Law (Q1 in Law only);
  - excluded: Knowledge-Based Systems (≈20 double-spaced pages) and the IEEE Computer Society Transactions (12-page threshold).
- **Next input needed:** the choice needs the **user and advisor**. It is the main open input for Phase 1+ budgeting. Phases 1–3 (reconciliation, contribution gate, corrected baseline) do not depend on the venue; template-specific shortening (Phase 4+) does.

## 3. Diagnostic builds of the unchanged content (task 0.4)

All builds are byte-deterministic (two runs, identical SHA256) with `SOURCE_DATE_EPOCH` fixed. There are 0 undefined references/citations in every build.

| Build | Change from working source | Pages | PDF SHA256 (prefix) | Notes |
|---|---|---|---|---|
| B1 provenance | none; XeLaTeX (Latin Modern) | **39** | 31a70e5b | Text-equivalent to archive main.pdf (6 hyphenation tokens) |
| B2 | none; pdfLaTeX (Times) | **37** | 78696ef6 | 26 float labels identical to B1 |
| B3 | `[conference]`→`[journal]` only | **36** | 1068d126 | Author block renders inline; must be ported if a journal class is used |
| B4 | front matter ported to Elsevier `cas-dc`, natbib, microtype expansion off | **38** | d9892073 | A4; 92 small overfull boxes (<10 pt) from IEEE-sized tables |

The IEEE Access and Springer templates could not be downloaded here (sandbox network blocked). If one of those venues is chosen, the user can place the official template zip in the workspace.

**Conclusion:** in every format, reaching ≤25 pages needs **about 30–36% fewer pages**. With all 26 floats retained, that means roughly **40–45% less running prose**.

## 4. Ledgers and baselines (task 0.5, V2 §3)

| File | Content |
|---|---|
| `object_register.csv` | 26 floats (12 table, 11 table*, 2 figure, 1 figure*) with label, B1 number/page, source line, incoming `\ref` count, caption |
| `limitations_register.csv` | All 18 limitations (L01–L18) with title, label, source line, status OPEN |
| `correction_register.csv` | R01–R24 seeded OPEN with source locations; R25–R26 newly proposed (below) |
| `macro_value_baseline.csv` | All 1,758 frozen macros with value, definition line, use counts per file (522 unused) |
| `rendered_number_baseline_B1.csv` | 5,338 numeric tokens with page and context: the tripwire baseline |
| `section_budget_baseline*.csv` | Prose tokens by section: Results 49%, Discussion 13%, Setup 13%, Methods 13% |
| `claim_language_scan.csv` | 231 strong-claim triggers with line context (e.g. "strictly" 20, "confirms" 14, "forensic" 13, "certified" 13) for Phase 1–2 |
| `build_visual_ledger.csv` | B1–B4 entries |
| Empty templates | `information_ledger.csv`, `claim_ledger.csv`, `semantic_change_ledger.csv`, populated from Phase 1 onward |

## 5. New findings from the Phase 0 inventory (proposed; Codex to verify)

- **R25 — hardcoded cross-references.**
  - Line 1073 says "Table~IX" for the sensitivity analysis, but that table renders as **Table X** in B1.
  - Line 393 says "Table~XVI" for prompt-token counts (probably the computational budget table, which renders as XXI).
  - Line 492 says "Tables~I--XXIII".
  - **Figure 1, Figure 3 and the sensitivity table have no `\ref` anywhere in the text.** These are real object-reference defects in the original.
- **R26 — hardcoded numbers.** About 1,331 numeric literals are typed directly in the `main.tex` body rather than via macros. Any correction or consistency check must cover literals as well as macros; this confirms that the overlay validator's literal scan is necessary. 522 of 1,758 frozen macros are unused, which is harmless but relevant to consumer-coverage checks.

## 6. Verification after transfer to the user's disk

See the checkpoint message. All workspace files were committed and then re-staged, and their SHA256 values were compared with `manifests/phase0_manifest.sha256`.

## 7. Open items and stop

- **Open:** journal choice (user + advisor); human confirmation of SJR quartiles; Codex verification of R25–R26.
- **Stop:** Phase 0 ends here. Phase 1 (evidence reconciliation, no prose rewriting) requires a separate explicit user approval.
