# Claude audit of Codex-0064: I1a wording implementation and candidate PDF (claude-0101)

Reviewer: Claude. NOT independent (Claude wrote Batch 1-28 text). Static audit of the saved source, diff, logs, PDF text and page images. I did not compile, run, edit or promote anything. I looked at rendered pages 5, 23 and baseline 5 as images and extracted the text of every changed passage from the PDF; I did not view all 24 pages, so this is not a whole-document layout verdict. User-relayed; no live channel.

## 1. Identity and scope (reproduced)

| Item | Result |
| --- | --- |
| working/src/main.tex SHA-256 | 35776773180a090e94039c6058e1d359f687fae809cfeb15183ba4f7585d433c (equals the report) |
| baseline_src/main.tex | 49107cfec13dcd51ec269d53e877984f855d0a7487092991881047576d018275 |
| build/main.pdf | b41b87c906b027ee3dfa77dad6089a96baeb055a512f5686784b27fadb105d96 (equals the report) |
| source.diff | 69021124861c1b97a6e233f7b7e4de97108b0afa23d08d96d8a6f25ee643c88a |
| build/main.log | 738bf8f05d5737e3531a623d94a1d8bc4c9a7cdf92eda5b9fa46773d317277b6 |
| dependency_hashes.csv | 30 rows: 29 unchanged, main.tex changed (baseline 49107cfe, final 35776773) |

Diff round trip: source.diff applied to the baseline main.tex gives the working main.tex byte-for-byte after normalizing line endings (the diff file strips carriage returns; the source mixes endings). A text diff shows exactly eight changed regions (lines 126, 182, 205, 210, 326, 353, 649, 651 of the baseline), matching REV1 plus REV2: nothing else in main.tex changed. Macros, tables, figures, bibliography are byte-identical per the CSV (a source-tree check, as Codex says).

## 2. Edits versus the approved wording

The compiled text matches REV1 (210, 205/equation sentence, 182, 651) and REV2 (126, 649 opening, 326, 353) as approved, with no optional expansion. Checked in the PDF text:

- p2 contribution bullet: "Coarse Domain Flag ... title match or nearest-neighbour proximity ($d_{L2}<1.3$ in the current source). This flag is not itself an early-refusal rule; the canonical evaluation terminated no query before retrieval".
- p4 embedding sentence: "ChromaDB's L2 index setting" (no normalization claim).
- p5 Tier 2: "nearest-neighbour ChromaDB score"; equation (3) unchanged; new sentence defining raw squared L2 and flagged-at-or-above; replacement for the old line 210 with 0.712 / population SD 0.122 / max 1.244, flagged 0/200 (0.00%) and 41/75 (54.67%) from the existing macros, "reproducing the calibration grid in Table XII, Panel B", benchmark-text-only and no-Title-Match caveat, provenance caveat once, canonical no-termination statement.
- p8 (line 326): BFS parameters unchanged; strict $d_{L2}<1.3$ moved to a separate clause attributed to the current source's domain helper.
- p10 (line 353): neutral index-setting wording; helper threshold restated as strict.
- p23 (649/651): reversed-direction sentence corrected; reproduces all eight calibration rows and AUROC 0.9901; the 10k audit "is not a matched-scale comparison ... does not establish a corpus-density effect or scaling law".

Scientific caveats survive: 0.365/0.082/0.509 occur nowhere in the PDF text (baseline: page 5); the density inference is gone; 10k units are marked unreconciled; Title Match and deployed formatting disclosed as not exercised; historical provenance disclaimed; the canonical "no query terminated before retrieval" disclosure is kept. Panel B macros and the AUROC render as before (0.9901; 0.00% 0/200; 54.67% 41/75).

## 3. Build evidence (from the logs and PDF, not rebuilt by me)

Candidate: 24 pages, extracted text has zero "??"; build log has 2 overfull boxes (same lines, 181 and 199, as the control: 1.30 pt and 14.05 pt), underfull 75 versus 72, no undefined-reference or duplicate-destination messages (my search of "undefined" returned only font-shape warnings). Under the 25-page ceiling by one page. Fresh same-toolchain control also 24 pages, so the page count is not due to a toolchain difference. I agree with Codex that the delivered earlier PDF should not be the comparator. This is cached-resource Tectonic output with font substitution warnings (437 warnings in my count of the "Warning" lines; Codex reports 427 font-shape warnings): a pre-existing condition and not repaired by this batch.

## 4. Rendering

Page 5 as an image: the Tier 2 item reads cleanly, the equation and following paragraph are well separated, and the longer paragraph causes no collision. Page 23: the Discussion paragraphs and the replaced 651 paragraph render normally with the Limitations list and references following, no clipping. The page-5 routing equation (2) "Out-of-Domain" touching the neighbouring column is present in the baseline image as well (I compared baseline-05.png): confirmed pre-existing, not caused by this edit. I did not inspect pages 2, 4, 8, 10 or the others as images (Codex did); my confirmation of those edits is from text extraction only.

## 5. Findings (none blocking)

1. **τ is used before it is introduced.** On page 5 the new sentence "values at or above $\tau$ are flagged" comes right after equation (3), which uses the literal 1.3; $\tau$ is first given a value ("τ = 1.30") several lines later. Suggest, in a later pass, "values at or above the threshold $\tau$ (1.30 here)".
2. **Line 182 attachment.** "(all-MiniLM-L6-v2, 384 dimensions, ChromaDB's L2 index setting) and indexed in a local ChromaDB PersistentClient": the index setting now sits inside the embedding-model parenthetical, and "ChromaDB" repeats. Accurate but awkward.
3. **"current source" / "current domain helper"** appears on pages 2, 8, 10 and 23, undated; "the released code" would read better in print. The p23 sentence still states one boundary twice ("flags at or above ... whereas the helper accepts below"). These were my optional refinements in 0100, not applied under the "exact replacements" rule; I raise them again only as polish.
4. **Residual "pre-filter" vocabulary** at the Tier 2 heading, the Computational Budget subsection (heading says "Geometric Gate Calibration"; text calls Panel B a calibration of a "candidate pre-filter"), the Panel B subsection title and its closing sentence ("optional coarse pre-filter to conserve compute"). The code evidence shows the flag only enters the router prompt; the p2 bullet now says so, while the Tier 2 and Panel B wording still suggest a mechanical pre-filter. Outside the approved scope; a user decision whether to align.
5. **Mixed line endings.** The baseline is CRLF; the nine edited or added lines are LF, so the file now has 662 CRLF and 19 LF lines (some LF lines pre-existed). Harmless to LaTeX; it explains why a naive patch against the CRLF source reports failures.
6. **Statistics macros' use multiplicity changed** (the Discussion paragraph no longer repeats the counts); Codex states this. Definitions are unchanged.
7. **Not a submission-readiness verdict.** Dense tables and font substitution remain; the previously noted 25-page ceiling is met only by one page.

## 6. Verdict

The implementation matches the approved REV1/REV2 wording exactly, touches only main.tex, preserves the approved scientific caveats, builds to 24 pages, and introduces no defect I can see in the pages I inspected. I concur with Codex's bounded result at source and text level. Remaining points (section 5) are polish decisions for the user.

## 7. Boundaries

No promotion, canonical edit, next batch, new run, API call or statistics regeneration is authorized by this audit. Whether to apply the polish items in section 5 is the user's decision. Relaying to Codex or Antigravity is the user's.
