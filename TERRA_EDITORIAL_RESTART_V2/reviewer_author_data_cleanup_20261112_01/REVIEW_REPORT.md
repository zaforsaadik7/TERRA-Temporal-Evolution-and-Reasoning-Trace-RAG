# Review and Implementation Report

**Package:** `reviewer_author_data_cleanup_20261112_01`  
**Updated:** 12 November 2026  
**Status:** Isolated source/PDF candidate updated with the dataset details supplied in chat and rebuilt. Public access to the in-progress GitHub corpus upload remains unverified.

## Preservation and scope

- Candidate source is under `src/`; the untouched rollback source is under `baseline/src/`.
- The active manuscript under `working/src/` remains byte-identical to the preserved baseline.
- Both baseline and candidate contain 59 source files. Only `main.tex` differs.
- Separate table source files and inline table environments are unchanged. No table content or formatting was changed.

## Author block

The updated table is implemented in the supplied row order, including names and emails:

1. Md. Emam Zafor Saadik — Student, Department of Computer Science and Engineering, Bangladesh University of Business and Technology (BUBT); `sayhitosaadik@gmail.com`.
2. Muhammad Raihan Molla — Student, Department of Computer Science and Engineering, BUBT; `mdraihan2328@gmail.com`.
3. Ahmed Shafkat — Assistant Professor, Department of Computer Science and Engineering, BUBT; corresponding author; `ahmedshafkat@bubt.edu.bd`.
4. Dr. Md. Motaharul Islam — Professor, Department of Computer Science and Engineering, United International University (UIU); corresponding author; `motaharul@cse.uiu.ac.bd`.
5. Bijon Mallik — Lecturer, Department of Computer Science and Engineering, BUBT; `bijon@bubt.edu.bd`.

The author table supplied the institutions and departments. Dhaka, Bangladesh was added from the universities’ official location pages. The byline marks Ahmed Shafkat and Dr. Md. Motaharul Islam as corresponding authors. Row order is preserved; no equal-contribution statement is inferred from the repeated role labels in the table.

## Funding statement

The first-page footnote states: “This work was supported by Peers Lab and United International University.” No grant number, funding program, amount, or additional form of support was supplied or invented. IEEE guidance places financial support in the first footnote/author-affiliation paragraph; a separate acknowledgment is for other contributions. Final venue-specific instructions still control.

## Off-topic/content review

No substantive statement was clearly unrelated to the paper’s research question, methods, results, or limitations. I therefore removed no scientific prose, findings, citations, tables, figures, or caveats. Only source comments that were template/editorial instructions and were not typeset were removed. See `OFF_TOPIC_REVIEW.md` for the retained borderline material and rationale.

## Data and code availability

The manuscript now identifies CourtListener and Harvard's Caselaw Access Project (CAP) as the public sources for the opinion corpus, links to both source sites, and describes the author-supplied collection history: an initial harvest of 23,010 federal decisions and a 20,000-opinion retained corpus from 1850–1980 (U.S. Reports Volumes 50–448) selected with a 4,000-character minimum. The harvest history and no-synthetic-opinion statement are author-supplied and were not independently reconstructed from source records. The manuscript explicitly describes the cutoff as a length filter rather than an independent legal classification and does not claim that length alone proves every item is substantive. CAP's CC0 1.0 designation and request for attribution are linked to CAP's terms page.

The data-availability section links the project's public GitHub repository and says the preprocessed corpus upload is in progress. Because no stable artifact path, release/version, or checksum has yet been supplied or verified, the manuscript does not claim that the derived corpus is already accessible there. The 350-query internal benchmark is described with its A/B/C/D counts. The historical 20k graph is reported with typed edge counts (145,310 `CITES` and 56 `OVERRULES`); the prospective corrected derivative removes three mis-resolved `OVERRULES` edges, leaving 145,363 total edges. It does not call all 145,363 edges citation edges.

The supplied 10k figures (10,009 nodes / 37,918 edges) do not match the local candidate files: the active 10k file contains 10,009 nodes and 48,599 `CITES` edges, while its pre-backfill backup contains 10,000 nodes and 48,516 `CITES` edges. The manuscript therefore omits the unsupported 10k edge count. The benchmark, corrected graph, and raw evaluation records do not yet have a verified public artifact location and reuse terms. See `DATASET_VERIFICATION.md` for the file-level reconciliation and limits.

## Build and visual verification

- Main PDF: 25 pages, US Letter. Supplement PDF: 34 pages, A4 landscape. The main PDF remains within the previously stated 25-page ceiling.
- Both source documents compiled successfully with Tectonic 0.17.0. The final main PDF has no unresolved `??` references.
- The final main-PDF first page was rendered and visually inspected after the author-block revision. The five authors, affiliations, contact details, corresponding-author labels, and funder footnote are visible without clipping.
- The corpus-description page and data-availability pages were rendered and inspected after the dataset update; source links and GitHub link are legible and the updated paragraph fits without the earlier split in the middle of the CAP licensing sentence. No table source or table content changed.
- Tectonic reports existing underfull-box warnings elsewhere in the paper. The data-availability paragraph's earlier 1.1 pt overfull warning is no longer present. Full page-by-page visual certification has not been performed.

## Files

- Candidate source: `src/main.tex`
- Preserved baseline source: `baseline/src/main.tex`
- Main PDF: `output/pdf/main.pdf`
- Supplement PDF: `output/pdf/TERRA_SUPPLEMENT.pdf`
- Off-topic assessment: `OFF_TOPIC_REVIEW.md`
- Integrity evidence and hashes: `output/INTEGRITY_CHECK.json`
- Build logs: `output/pdf/main_build.log`, `output/pdf/supplement_build.log`

## Remaining input

When the GitHub upload is complete, provide or identify the exact dataset artifact path and release/version (preferably with a checksum and license/access terms). The candidate can then replace the provisional “upload in progress” disclosure with a verifiable public data citation. The 10k edge-count discrepancy also needs authoritative provenance if the 10k baseline is to be reported.

## Sources

- IEEE Author Center, “Structure Your Article”: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/
- IEEE Editorial Style Manual for Authors: https://journals.ieeeauthorcenter.ieee.org/wp-content/uploads/sites/7/IEEE-Editorial-Style-Manual-for-Authors.pdf
- BUBT official website/contact information: https://www.bubt.edu.bd/
- UIU official contact information: https://www.uiu.ac.bd/contact-us/
