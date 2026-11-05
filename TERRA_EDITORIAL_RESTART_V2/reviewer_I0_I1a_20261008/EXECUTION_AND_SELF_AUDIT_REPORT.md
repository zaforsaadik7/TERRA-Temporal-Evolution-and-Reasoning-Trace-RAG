# I0 + I1a checkpoint: baseline and distance-calibration reconciliation

Codex; 2026-10-08, Asia/Dhaka. Implementation self-verification and documentary audit, not an independent legal/scientific certification. User authorized starting the Claude-recommended I0/I1a work and preparing reports for Claude. No release-wording patch was explicitly approved or applied.

## Outcome

**Baseline preservation: PASS. Documentary tracing of the distance conflict: COMPLETE for accessible evidence. Numerical correction/calibration gate: NOT CLOSED.** No primary query-level distance artifact was found in the bounded search; a request for Antigravity is filed. Do not advance to manuscript correction, chain-recovery audit, new experiments or promotion on this report.

The latest user assigns coding to Antigravity, with Codex/Claude auditing. No new Python/experimental script was written. Standard filesystem/hash commands and existing PDF utilities were used for preservation and inspection. Existing computation scripts were read, not run. No provider call, key replacement, new embedding inference, model download, vector-database query, benchmark rerun, or statistics generation occurred.

## I0: preserved state and identity

Snapshot: `baseline/working_src/` contains the current working source tree; `baseline/r30corr_v1/` contains all 12 corrected-graph derivative files. Accepted Batch 1 main PDF and delivered supplement are preserved separately. The two graph copies remain historically distinct; derivative attribution is not applied to old results.

`baseline_manifest.csv` records 51 preserved files: 44 baseline files and 7 documentary evidence files, with relative paths, byte counts and individual SHA256s. This is a scoped active-source/derivative/evidence snapshot, not a claim to have copied every dataset or every project file again. Large historical protected inputs remain in their existing preserved locations.

| Artifact | Identity / status |
| --- | --- |
| Current working main source | `49107cfec13dcd51ec269d53e877984f855d0a7487092991881047576d018275` |
| Accepted Batch 1 main PDF | `d9cbd3928f5b1d0b788a54bb5bec399b3e6aedc70bce79aaface22d494f04596`; 24 pages, Letter |
| Delivered supplement | Preserved six-page artifact; producing parent source still unavailable from prior investigation |
| Original archive | Preserved; not substituted for current accepted working source |

`protected_inputs_check.csv` independently rehashes all 131 paths listed in Batch 1's protected baseline. Expected values for only the two previously authorized Batch 1 changes (main and Figure 1) are taken from that accepted checkpoint. **131/131 match; no new drift detected.** Source-tree snapshot comparison is also recorded in `snapshot_verification.csv`.

Reviewer letter: the user's pasted five-point letter is preserved in `REVIEWER_LETTER.md`; its original sent-to-reviewer PDF identity is still unknown. Do not assume the reviewer's table/page numbers identify a different version without checking scientific labels. The current inspected PDF actually contains the cited contradiction on page 5 and Table XII on page 21.

I0 requirements not settled here: exact submission-template/page-count convention and final author/venue confirmation. Artificial Intelligence and Law is the reviewer-proposed target; the advisor's 25-page ceiling remains the project constraint. These decisions need not prevent tracing saved evidence, but must be settled before formatting. No claim that every I0 submission decision is complete.

## I1a: results reproduced documentary, not recomputed from observations

### A. Contradiction appears in the actual PDF

Read working source line 210 and inspected rendered page 5. It describes the 20,000-case index and in-domain mean `0.365 ± 0.082`, maximum `0.509`, together with the Table XII reference.

Read the frozen macros and table source, extracted PDF text and inspected rendered page 21. Table XII Panel B reports:

| Threshold | In-domain count / 200 | In-domain rate | OOD count / 75 |
| --- | --- | --- | --- |
| 0.90 | 9 | 4.50% | 72 |
| 1.00 | 2 | 1.00% | 62 |
| 1.10 | 1 | 0.50% | 54 |
| 1.20 | 1 | 0.50% | 47 |
| 1.25 | 0 | 0.00% | 44 |
| 1.30 | 0 | 0.00% | 41 |
| 1.35 | 0 | 0.00% | 35 |
| 1.40 | 0 | 0.00% | 32 |

The threshold counts are monotone and their displayed percentages arithmetically agree with the stated denominators. They do not conflict with zero false rejection at 1.30. **They do conflict with a maximum of 0.509 if the population and distance definition are the same.** Under the inspected script's `distance >= threshold` rule, a maximum of 0.509 implies zero rejections at every listed threshold, not 9/200 at 0.90.

This establishes a real reader-facing inconsistency, not which measurement is empirically correct. No replacement number is authorized or proposed as verified.

### B. A saved aggregate source exists for the table

Found `scratch/budget_and_gate_summary.json`, SHA256 `b5c498473582e82cda3742020f8409cd022485080edf3648d6704d0fb4807d2f`, and a backup `scratch/orig_scripts/budget_and_gate_summary.json`, SHA256 `69b3707042c6ee31058744f50c8e5f78c1bd93f0c4db60e643bcdb81cb017cd7`.

Both contain the same serialized `gate_calibration` block: AUROC `0.9901333333333333` and the eight threshold rows above. This is a named-field documentary match for the table, stronger than matching a number somewhere in a file. The two complete files differ; matching the calibration block does not imply full-file identity or two independent calibrations.

The summary has aggregate counts only: no saved query-ID/distance vector, in-domain maximum, embedding/index fingerprint, exact executed revision, or timestamped configuration adequate to authenticate that calibration run. Its presence does not independently validate the table.

### C. Generating code explains the proposed measurement, but is unsafe to execute as-is

Inspected `scripts/compute_budget_and_gate_metrics.py`, SHA256 `ad6f26e858c79693e13163ccd77446bd77af7af21cb0552b262c68be6b04b5ca`.

- Configured benchmark: `terra_350_benchmark.json`.
- Configured vector database: `dataset_20k_cap/vector_db_20k`, collection `thinking_traces`.
- Queries all benchmark texts for one nearest result; stores the first returned distance keyed by query ID in memory.
- Defines A+B as in-domain, C as OOD, and rejects at `distance >= tau`.
- Writes the aggregate grid/AUROC, but does not persist the primary per-query distance vector or authenticated collection metric/embedding snapshot.
- Also rewrites/appends `Paper/generated_stats.tex`, truncating from its header, and writes the scratch summary. **Not run.** Executing it would violate this read-only scope and could overwrite protected artifacts; a fresh query would also be a new diagnostic on today's index, not recovery of the historical observations.

The code alone does not authenticate whether Chroma's returned distance is squared L2 or another collection-specific metric. Neither inspected geometry script explicitly records the collection metadata/embedding fingerprint needed to resolve this. Do not silently take a square root or assume similarity/distance conversion fixes the paper.

### D. Historical evidence raises a stale-summary possibility, not a verified cause

Found `Paper/audit/firewall_mechanism_correction.md`, SHA256 `5a6e552fc71fd1fd10e45f568b7518c1de1eb3739bdaa1b63abd066dd8b8d480`.

Its September 5 report lists `0.365 ± 0.082` and `0.509` under **Original Paper Claim**, beside a different 175-query audit: A+B N=100, C N=50, D N=25. That audit reports maxima 0.6120 for the 10k index and 1.2170 for the 20k index. These are a different population from the current 350-query calibration and are not replacement values for it.

This confirms that 0.509 already existed as a historical claim in a document that questioned it. It does not establish its original generating population or prove that it is the old 10k maximum: the report's 10k maximum itself is 0.6120. The report also contains strong old architectural statements contradicted by later records. Its `APPROVED & APPLIED` header is an authored historical assertion, not proof of current accuracy or a new permission.

Inspected `scratch/audit_firewall_geometry.py`; it queries the two current local collections against `terra_175_benchmark.json` and prints aggregates, without persisting query-level observations. Not run. Issue 42's judge-calibration script is a different kind of calibration and is not evidence for these vector distances.

## Visual and audit scope

Rendered and visually inspected all of current main pages 5 and 21 using Poppler at 120 dpi. Page 5 visibly carries the 0.509 statement; page 21 visibly carries Table XII's nonzero threshold counts. Page 21's table body remains exceptionally small, consistent with the already tracked readability defect. This is a targeted contradiction audit, not whole-document layout approval. No recompilation was needed or performed because no source changed; retained Batch 1 build evidence is not called a fresh build.

## Completion and next dependency

Complete: current scoped byte-preserved snapshot; 131-path integrity check; Claude-0068 actual review read; PDF-level contradiction verification; frozen-macro/table/aggregate-summary tracing; script safety and historical audit review; Claude handoff and Antigravity information request.

Open: historical query-level calibration distances and provenance; true source of 0.509; empirical recalculation; approved correction text; reviewer PDF identity; venue-format page convention. The 66/62-chain investigation and other I1c findings remain later batches, not silently completed here.

Antigravity is asked to recover primary calibration records and provenance first. If unavailable, it should propose an isolated audit script and feasibility/permission requirements without running vector queries, downloading models, using APIs or touching protected files. Codex/Claude audit that script before execution. A current-index diagnostic must be labelled new evidence, not historical reproduction.

No manuscript release-wording patch, coding implementation, new experiment, API call, canonical modification or promotion occurred. Stop here for Claude's audit and Antigravity's evidence response.
