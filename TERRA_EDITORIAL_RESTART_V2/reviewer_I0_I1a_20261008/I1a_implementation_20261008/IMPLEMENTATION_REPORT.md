# I1a wording implementation and bounded PDF audit

Author: Codex. 8 October 2026. User authorized: “Apply the reviewed I1a wording corrections, then compile and audit the PDF within 25 pages.” No further phase or promotion is authorized.

## Outcome

Implemented retained REV1 plus overriding REV2 exactly, in isolated working/src/main.tex only. Build PASS: Tectonic 0.17.0, cached resources only, exit 0, 24 pages (ceiling 25). Independent Claude review remains pending. This is not submission-readiness certification.

## Provenance and scope

- Before source SHA256: 49107cfec13dcd51ec269d53e877984f855d0a7487092991881047576d018275.
- After source SHA256: 35776773180a090e94039c6058e1d359f687fae809cfeb15183ba4f7585d433c.
- Candidate PDF SHA256: b41b87c906b027ee3dfa77dad6089a96baeb055a512f5686784b27fadb105d96.
- baseline_src contains the complete copied 30-file working source tree; baseline_main.pdf preserves the incoming build. dependency_hashes.csv compares every copied source dependency with the final working tree: only main.tex changed. All statistics/correction macros, figures, tables and bibliography are byte-identical. This is a source-tree check, not a fresh audit of every dataset or canonical file in the repository. No dataset, graph, code, supplement or canonical edit was performed.
- source.diff records the actual changes. Macros' usage multiplicity is not invariant because the approved Discussion replacement removes repeated counts; their definition files and calibration values are unchanged.

## Scientific change log

Removed 0.365/0.082/0.509 as untraced and unreproduced, not as proven 10k values. Added dated current-index mean 0.712, population SD 0.122, maximum 1.244 against diagnostic SHA256 2b6a9b556cf6183c985ec44444bd5c22093aacde80256f6fba551e982a88e9a9 and prior arithmetic audits. Retained count/rate macros rendering 0/200 (0.00%) and 41/75 (54.67%), and AUROC 0.9901. The current diagnostic used direct benchmark query text, not Title Match or deployed formatting, and cannot authenticate historical provenance.

Clarified raw squared-L2 calibration units without asserting normalized embeddings. Kept threshold 1.30, correcting its strict helper boundary and separating the domain flag from BFS/retrieval configuration. Qualified current-source evidence; retained previously reviewed canonical no-pre-retrieval-termination disclosure without claiming this diagnostic proves it. Removed unsupported density inference and explicitly qualified unmatched 10k units/configuration. All other limitations and evidence text were left unchanged.

## Build and rendered audit

Fresh candidate and preserved-source control builds both exit 0 at 24 pages. Build logs show zero undefined-reference, multiply-defined-label or duplicate-destination diagnostics; extracted candidate text has zero ?? tokens. Both builds have 427 font-substitution warnings and 2 overfull boxes; underfull warnings increase from 72 to 75. Font substitution and overflow defects are not repaired by this wording batch.

Rendered all 24 pages using Poppler. Visually inspected all pages through four contact sheets for gross clipping, empty pages, broken floats and terminal bibliography defects; inspected edited pages 2, 4, 5, 8, 10 and 23 individually at larger resolution. Edited prose is readable without new observed collision. This is not line-by-line full-document certification: dense/tiny tables and architecture labels remain pre-existing readability work.

Rebuilt baseline comparison shows text reflow on pages 2 and 4–24. Page 1 and 3 text are unchanged. The incoming delivered PDF differs from the fresh control in extraction on all pages, so fresh same-toolchain baseline is the fair comparison. Page 5 routing equation extends into the column gutter and touches the neighbouring text; baseline page 5 has the same defect. This remains a layout follow-up, not a clean whole-paper verdict.

## Evidence and handoff

build/main.pdf is the reviewed candidate; build/main.log and compile_console.txt retain build evidence. baseline_build provides the same-toolchain control; rendered contains all page PNGs, contact sheets and baseline page 5. No existing working/build_test PDF was overwritten. Claude should inspect actual source.diff, dependency hashes, compiled passages and reflow, including the page-5 defect. No new experiment, API call, threshold change, statistics regeneration or promotion occurred. Stop here pending peer review and the next user-approved batch.
