# Review and Implementation Report

**Package:** `reviewer_author_data_cleanup_20261112_01`  
**Prepared:** 12 November 2026  
**Status:** Candidate source/PDF built; dataset-link integration remains pending because the referenced dataset-information Google Doc could not be accessed.

## Scope and preservation

- Created an isolated package with the copied manuscript at `src/` and an untouched rollback copy at `baseline/src/`.
- The active manuscript under `working/src/` was not edited.
- Source inventory: 59 files in both baseline and candidate. `main.tex` is the only changed source file; all 58 other files match by SHA-256.
- All separate table source files are identical. The inline `table`, `table*`, and `longtable` blocks in `main.tex` also compare byte-for-byte equal. No table content or formatting was changed.

## Authors

The candidate lists the five names in the row order from the author-details table and includes the supplied email addresses:

1. Md. Emam Zafor Saadik — `sayhitosaadik@gmail.com`
2. Muhammad Raihan Molla — `mdraihan2328@gmail.com`
3. Ahmed Shafkat — `ahmedshafkat@bubt.edu.bd`
4. Dr. Md. Motaharul Islam — `motaharul@cse.uiu.ac.bd`
5. Bijon Mallik — `bijon@bubt.edu.bd`

The source table did not provide verified institutional affiliations or designate a corresponding author. I therefore did not infer affiliations from email domains or assign corresponding-author status. Those details remain to be confirmed before a submission-ready author block. Scholar profile links were not inserted in the byline because they are not affiliation/contact fields and were not verified for publication use.

## Funding acknowledgment placement

The paper now states: “This work was supported by Peers Lab and United International University.” It appears in the first-page `\thanks` footnote. This is the appropriate provisional IEEE-style location for financial support; a separate acknowledgments section is normally used for non-financial contributions. No grant number, funding program, or additional contribution is claimed because none was supplied. The current venue remains IEEE conference-style source; the eventual journal’s instructions still govern final placement and wording.

## Off-topic/content review

The review did not identify a substantive passage that could safely be called unrelated to the paper’s research question. The background, architecture, benchmark, provenance, results, limitations, and availability statements support the paper’s claims or qualify their evidential limits. I did not delete research prose merely to shorten the paper.

Removed only stale source comments that were template/editorial instructions (including a comment about whether the funding-footnote command was needed and table-section markers). These comments were not typeset. The separate `OFF_TOPIC_REVIEW.md` records the reasoning and potentially confusing-but-relevant material retained.

## Data and code availability

The GitHub repository is public and its page lists source-code/project folders and files: https://github.com/zaforsaadik7/TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG. The visible root does not establish that all datasets, raw results, the complete corpus, or the vector store are deposited there; no repository release or dataset landing-page identifier was found in the reviewed public page. The candidate statement distinguishes code availability from dataset availability and does not claim a complete public data release.

The dataset-information Google Doc supplied in the request could not be read through the available web reader. The desktop browser check also stopped because the computer-use tool could not verify the current browser URL, so no document contents were read or edited. Therefore the dataset-specific links, versions, and access/reuse terms requested for the paper are not yet added. The Google Doc content (or an exported PDF/DOCX/text copy) is required to complete this part without inventing links or permissions.

## Build and visual checks

- Main PDF: 24 pages, US Letter.
- Supplement PDF: 34 pages, A4 landscape.
- Both compiled successfully with Tectonic 0.17.0. Cross-reference auxiliary files were used to compile both documents; temporary `.aux` files copied into `src/` were removed afterward.
- Extracted PDF text contains no unresolved `??` references.
- Rendered pages 1 and 10 of the main PDF were inspected. The author list and funding footnote appear on page 1; the repository link and qualified availability wording appear on page 10; the cross-reference to Supplementary Table S9 resolves.
- Tectonic emitted existing layout warnings, including underfull boxes and a 1.1 pt overfull box in the availability paragraph. They did not prevent compilation; this copy has not undergone full page-by-page visual certification.

## Files

- Main source: `src/main.tex`
- Preserved baseline source: `baseline/src/main.tex`
- Main PDF: `output/pdf/main.pdf`
- Supplement PDF: `output/pdf/TERRA_SUPPLEMENT.pdf`
- Off-topic assessment: `OFF_TOPIC_REVIEW.md`
- Integrity summary and PDF hashes: `output/INTEGRITY_CHECK.json`
- Build logs: `output/pdf/main_build.log`, `output/pdf/supplement_build.log`

## Required follow-up before treating this package as complete

1. Provide the dataset-information document contents so exact dataset URLs, identifiers, versions, licenses, and availability can be checked and inserted.
2. Confirm each author’s institutional affiliation and name spelling, and designate the corresponding author.
3. Confirm any grant/program identifier or required funder wording if either organization has one.
4. Rebuild and inspect the final candidate after those confirmed facts are inserted.

## Official style sources consulted

- IEEE Author Center, “Structure Your Article,” first-footnote section: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/
- IEEE Editorial Style Manual for Authors: https://journals.ieeeauthorcenter.ieee.org/wp-content/uploads/sites/7/IEEE-Editorial-Style-Manual-for-Authors.pdf
