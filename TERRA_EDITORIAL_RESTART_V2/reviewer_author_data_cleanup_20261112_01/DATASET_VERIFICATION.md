# Dataset Details and Local Count Reconciliation

**Candidate:** `reviewer_author_data_cleanup_20261112_01`  
**Date:** 12 November 2026

## Details supplied by the author and reflected in the candidate

- Primary corpus: 20,000 Supreme Court opinions spanning 1850–1980 (U.S. Reports Volumes 50–448), selected from an initial harvest of 23,010 federal decisions with a minimum 4,000-character rule.
- External sources: [CourtListener bulk data](https://www.courtlistener.com/bulk-data/) and [Harvard Caselaw Access Project](https://case.law/). The manuscript links CAP's [terms](https://case.law/terms/), which designate its Caselaw Data and metadata as CC0 1.0 and request attribution.
- Benchmark: the hand-constructed 350-query `terra_350_benchmark.json`, with 100 Category A, 100 Category B, 75 Category C, and 75 Category D queries.
- Event Evolution Graph (EEG): internal research artifact. The 20k historical index is reported as 145,310 `CITES` plus 56 `OVERRULES` edges. Its corrected prospective derivative removes three mis-resolved `OVERRULES` edges, resulting in 145,363 total edges (145,310 `CITES` plus 53 `OVERRULES`).
- Preprocessed corpus: author reports that upload to the public GitHub repository is underway. The manuscript links the repository but does not claim the corpus artifact is already publicly available; no artifact-specific path, version, or checksum was provided.

The manuscript does not claim that a character-count threshold independently establishes that each retained opinion is substantively classified. It states that no synthetic opinions were added. The federal-government-work copyright statement remains qualified and does not imply that third-party metadata or platform materials are necessarily covered by 17 U.S.C. §105.

## Local graph files checked

| Local file | Nodes | Edges in serialized list | Relation counts | Assessment |
|---|---:|---:|---|---|
| `dataset_10k_cap/terra_eeg_index_10k.json` | 10,009 | 48,599 | 48,599 `CITES` | Does not support supplied 37,918 edge figure. |
| `dataset_10k_cap/terra_eeg_index_10k_pre_backfill_backup.json` | 10,000 | 48,516 | 48,516 `CITES` | Does not support supplied 10,009 / 37,918 pair. |
| `dataset_20k_cap/terra_eeg_index_20k.json` | 20,000 | 145,366 | 145,310 `CITES`; 56 `OVERRULES` | The file's serialized relations establish 145,366 total edges, not 145,363 citation edges. The manuscript separately explains the corrected derivative. |

The user-provided 10k values (10,009 cases and 37,918 citation edges) were not inserted because they do not match either local 10k graph candidate. The 145,363 figure was not labeled as citation-only edges because local relation counts show it is the corrected derivative's total after three `OVERRULES` edges are removed.

## Availability limitations

The benchmark, corrected EEG derivative, raw evaluation records, and the uploaded preprocessed corpus do not yet have a verified, stable public artifact record in this package. A repository home-page link is not evidence that each file is already available, versioned, or covered by a specified reuse license. The Data and Code Availability paragraph preserves that distinction pending the completed upload and its exact artifact location.
