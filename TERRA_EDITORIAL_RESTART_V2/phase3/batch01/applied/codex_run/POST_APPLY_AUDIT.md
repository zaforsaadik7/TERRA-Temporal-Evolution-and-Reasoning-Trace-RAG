# Phase 3 Batch 01 — Codex post-implementation audit

- **Date:** 2026-09-30 (Asia/Dhaka)
- **Scope:** user-approved full B1-1–B1-8 variant in `TERRA_EDITORIAL_RESTART_V2/working/src` only.
- **Verdict:** **PASS for the approved source/numerical batch.** This is not full-document visual certification, original-TeX-Live certification, canonical promotion, or authorization for Batch 02.

## Independent source/provenance checks

The three pre-apply snapshots match the locked input SHA256 values. The applied working files match the approved post hashes:

| Asset | SHA256 |
|---|---|
| `working/src/main.tex` | `2ddb18a775cc4e54508dabbfc1fbfe6e8840fb0706e8b2d1cc7c97bbb7b1ff2c` |
| `working/src/tables/table_refusal_breakdown.tex` | `337dc7c8dc61826b9aefe759e19273bbdbcbe9f9b503d849c9fd5d7331b02ed7` |
| `working/src/figure_3_safety_rejection.tex` | `af4fdee83ca6fb9462c223a8f80cded7244f1b5f1041b9cbf75d66ba47af3d04` |
| `working/src/phase3_corrections.tex` | `487fdb9d9439f786d05cf24379108fcf4457827c4d7c57af001438c4543b40da` |

The byte-preserving wrapper was run first with `--check-only` and then applied. Its reported line-ending census was unchanged: `main.tex` 1,111 CRLF + 16 bare LF; refusal table 35 CRLF; Figure 3 source 89 bare LF. I independently reconstructed the unified diff from snapshots and current source after normalizing line endings: it equals `rev1/proposal/batch01_rev1_full.diff` exactly (27,578 characters). A recursive per-file SHA256 comparison against `CANONICAL_ARCHIVE/src` found exactly the three approved changed files plus the new corrections file, and zero other working-source differences (27 working files versus 26 canonical files). The canonical main source, PDF, and frozen statistics retain their locked hashes; `working/src/generated_stats.tex` also retains `e4e369b7...56b73`.

## Build and scientific checks

The local device build used **Tectonic 0.17.0**, its XeTeX engine and xdvipdfmx, with cached dependencies. It was **not** a separate XeLaTeX/TeX Live executable; one phrase in Claude's read-only audit should be understood in that narrower sense. The PDF is 39 letter-size pages, SHA256 `c8e7b7f18028a17ee790ccbe3d0141912552ec58e66cfd347ea44edb1ae73b90`. The saved `build_src/main.log` has zero undefined-reference warnings, zero undefined-citation warnings, zero multiply-defined-label warnings, and zero fatal errors. It has 641 font-shape warnings and two overfull hboxes; Tectonic's console also warned of an annotation outside the page boundary. These are build/layout debt, not a clean final-publication certificate.

The independently rerun fact script produced a CSV byte-identical to the rev1 fact CSV: 23 `VERIFIED`, one `CONFLICT`. The conflict (B1-F12) intentionally describes the **old, replaced** R37 statement; it is not a contradiction remaining in the applied source. PDF text extraction confirms two `Rank 6` instances and zero `Rank 11` instances on page 34, with zero `Rank 11` instances in the whole PDF.

## Rendered-page QA and limits

- **Page 15:** Figure 3's TERRA Category-D system-flagged refusal bar shows 61.3%; the caption states 46/75 and identifies the measure. The caption no longer collides with the following paragraph.
- **Page 16:** the revised Category-D statistics are legible. The Table IX notes still overlap its final row; this was present before Batch 01 and remains a blocking layout defect for eventual publication-quality certification.
- **Page 34:** the adverse Direct-LLM Category-D faithfulness result is visibly stated as significant, with the corrected delta, p, q, and both Rank-6 references. No new clipping is apparent in the inspected area.

Figure 3 value labels remain very small, and some limitation headings remain loosely spaced. Only affected pages 15, 16 and 34 were visually inspected here; no whole-PDF quality claim is made. The 39-page source remains far above the advisor's 25-page ceiling. Phase 3 continues one batch at a time; Batch 02 must be separately proposed, audited and user-approved before application.

## Evidence locations

- Pre-apply originals: `../snapshot_pre/`
- Byte-safe application: `../p3b1_apply_eolsafe.py`
- Per-file generated diffs: `main.diff`, `table_refusal_breakdown.diff`, `figure_3_safety_rejection.diff`
- Device PDF/log: `build_src/main.pdf`, `build_src/main.log`
- Fact rerun: `p3b1_facts_post.csv`
- Rendered affected pages: `main_p15.png`, `main_p16.png`, `main_p34.png`
