# Review and Implementation Report

**Package:** `reviewer_author_data_cleanup_20261112_01`  
**Updated:** 12 November 2026  
**Status:** Isolated source/PDF candidate built. Dataset-specific links remain pending the contents of the dataset-information Google Doc.

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

The public GitHub repository is available at https://github.com/zaforsaadik7/TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG. Its visible root lists source-code/project folders and files; that does not establish that the datasets, raw results, full corpus, or vector store are deposited there. No verified dataset landing page, repository release, or archive identifier was found in the public repository page reviewed.

The separate dataset-information Google Doc could not be read using the available web reader; its export URLs were also inaccessible. The desktop browser check stopped because the computer-use tool could not verify the active URL. Accordingly, dataset-specific URLs, versions, and reuse/access terms have not been guessed or inserted. Please provide the document contents or an exported copy to complete this part.

## Build and visual verification

- Main PDF: 24 pages, US Letter. Supplement PDF: 34 pages, A4 landscape.
- Both source documents compiled successfully with Tectonic 0.17.0. The final main PDF has no unresolved `??` references.
- The final main-PDF first page was rendered and visually inspected after the author-block revision. The five authors, affiliations, contact details, corresponding-author labels, and funder footnote are visible without clipping.
- Page 10 was also inspected for the data-availability statement, clickable GitHub link, and resolved Supplementary Table S9 reference.
- Tectonic reports underfull-box warnings and a 1.1 pt overfull box in the data-availability paragraph. These did not prevent compilation; full page-by-page visual certification has not been performed.

## Files

- Candidate source: `src/main.tex`
- Preserved baseline source: `baseline/src/main.tex`
- Main PDF: `output/pdf/main.pdf`
- Supplement PDF: `output/pdf/TERRA_SUPPLEMENT.pdf`
- Off-topic assessment: `OFF_TOPIC_REVIEW.md`
- Integrity evidence and hashes: `output/INTEGRITY_CHECK.json`
- Build logs: `output/pdf/main_build.log`, `output/pdf/supplement_build.log`

## Remaining input

The dataset-information document is still needed to insert and verify dataset links, versions, and access/reuse conditions. The repository/data availability wording in the candidate is intentionally limited until those facts are available.

## Sources

- IEEE Author Center, “Structure Your Article”: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/
- IEEE Editorial Style Manual for Authors: https://journals.ieeeauthorcenter.ieee.org/wp-content/uploads/sites/7/IEEE-Editorial-Style-Manual-for-Authors.pdf
- BUBT official website/contact information: https://www.bubt.edu.bd/
- UIU official contact information: https://www.uiu.ac.bd/contact-us/
