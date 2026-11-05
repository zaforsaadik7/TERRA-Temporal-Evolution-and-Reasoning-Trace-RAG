# Experiment identity inventory: read-only checkpoint

Codex, 12 October 2026. User authorized moving to the next read-only experiment identity task. No experiment, retrieval, runtime import, API, manuscript modification or statistics regeneration occurred. Hashing and JSON inspection establish present artifact identity and recorded metadata, not authenticated historical execution. Antigravity peer review is pending.

## Primary findings

1. `configs/terra_config.json` declares hub_degree_cap=50, while current `ask_terra.py:518–519` uses incoming=75/outgoing=25. Config also says Euclidean L2 whereas the approved store diagnostic established raw squared-L2. Do not silently repair configuration or retroactively substitute current settings. This confirms a disclosure/configuration-to-current-code mismatch, not which historical settings ran.
2. Canonical-v2 has 1,750 rows: 1,400 `_source_run=sept6_baseline_rejudged`, 350 `issue6_deployed`. None records ask_terra_sha256, chroma_fingerprint, temperature or max_tokens at top level. Model identifiers exist, but missing fields cannot be filled from the later configuration as execution facts. None-valued generation identifiers do not by themselves identify refusals or failures.
3. All 120 obscure-suite and 76 famous-D1 rows record code hash `430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd`, temperature 0.0, max_tokens 4096 and a common Chroma fingerprint. This is stronger recorded provenance than the primary canonical file. It still requires the corresponding preserved code and a validated fingerprint interpretation. A recorded code hash is not the source file itself.
4. Their recorded generator identifiers differ: obscure rows contain 60 `meta-llama-3.3-70b-instruct-121024`, 54 `databricks-meta-llama-3-3-70b-instruct`, 6 None; famous rows 38/31/7 respectively. These may be serving aliases; equivalence is not established here. Do not assume different weights or claim exactly identical serving snapshots without evidence.
5. Temporal-update results explicitly record executed_at `2026-09-23T15:04:40.722369+00:00`, active graph hash `7aa6db46...`, five subgraph hashes, 106 observations and 82 unique queries. This is recorded execution metadata, stronger than mtime, not independently timestamp-authenticated evidence. Preserve 106 versus 82 denominator distinction.

## Fourteen-block matrix

Paths below are relative to F:/TERRA -Copy. Exact hashes and sizes of 29 inspected inputs are in artifact_manifest.json. Settings described only in manuscripts or current code remain source-described, not proven historical parameters.

| Block | Results or evidence artifact | Code/configuration evidence | Status / missing link |
|---|---|---|---|
| Baseline generations | terra_baselines_eval_raw.json; canonical-v2 baseline rows | Existing baseline adapters and S2 disclose top-k/context/settings | Results identity pinned; historical per-arm graph/index/code hashes not authenticated in this checkpoint |
| Primary TERRA | data/terra_canonical_v2_eval.json; scratch/terra_350_issue6_dual_judged.json | Current ask_terra.py and configs/terra_config.json pinned separately | Exact historical code and graph payload snapshot unavailable; current config/code discrepancy above |
| Dual-judge scores | canonical-v2 faithfulness_qwen, faithfulness_gpt and raw_judge_scores fields | eval_terra.py present/pinned; S9 judge names | Combined scores recorded; cannot treat later evaluator file as proved historical revision |
| Pilot ablation | terra_true_ablation_pilot_raw.json | Main describes 35 queries/repeats; earlier single-judge protocol | Raw file pinned, not fully parsed this pass; actual historical graph/code/judge identity unresolved |
| Temporal probe | data/temporal_leakage_dual_judged.json, 400 rows | Per-row created_at, prompt/context/candidate hashes, judge evaluations; preflight manifest | Recorded payload evidence present; prompts/cutoff implementation and graph-version linkage need extraction; missing judgments not removed from scope |
| Category D rubric | scratch/category_d_rubric_summary_v2.json and issue6 TERRA rows | scripts/certify_category_d_issue6.py identifies source paths | Current certification script is not historical proof; 46 pre-generation and 48 rubric refusals are distinct measures |
| CaseFacts | scratch/casefacts_120_eval_raw.json, 360 pipeline-instance rows; scratch/casefacts_50_refusal_eval_raw.json | compute_casefacts_metrics.py explicitly reads those files; raw timestamp/judge fields | 120+50 source questions, not 170 total pipeline rows. Need historical harness/graph linkage; metric utility not executed |
| CLERC | scratch/clerc_120_eval_raw.json, 360 pipeline-instance rows; scratch/clerc_50_refusal_eval_raw.json | compute_clerc_metrics.py explicitly names these paths | 120 native positives + 50 TERRA negative controls; output schemas differ; need nested generation/configuration extraction |
| Obscure suite | scratch/obscure_raw_responses.json, 120 rows | Recorded code hash, index fingerprint, 0.0/4096; current inference runner pinned | Recorded identities available; matching historical code copy/serving alias proof requested |
| Famous D1 | scratch/famous_d1_raw_responses.json, 76 rows | Same recorded code/fingerprint/settings as obscure | Distinct population, not all 75 Category-D questions; historical code/alias linkage unresolved |
| Historical sensitivity | data/issue26_hyperparameter_sensitivity.json; older raw results | Current sensitivity script pinned; prior I1b set comparisons | 62/100 older, 66/100 canonical, 61/100 bounded remain distinct; no fresh traversal executed |
| Distance calibration | Approved reviewer_I0_I1a contemporary run package | Prior reviewed diagnostic/harness; current copied store | Contemporary grid concordance, not historical calibration origin; not deployed title-match route |
| Latency/cost | Canonical-v2 timings; reviewer_I1c approved export | Existing reviewed latency verifier and named-field cell checks | Route/category populations distinguished; modelled cost is not metered invoice; no new utility executed |
| Topology | dataset_20k_cap/terra_eeg_index_20k.json pinned; corrected derivative separately archived | Prior graph audits specify undirected largest WCC for diameter/path | Current active artifact identifiable; historical payload and corrected derivative must not be conflated |

## Preserved uncertainty

R33/R34 correction retains graph-summary timing as inference and distinct Category B/D serialized profiles without proving separate dates/code. Current source compatibility does not establish the exact September execution file. Hashes of result files prove their identity today, not that any referenced code/configuration produced them. The original graph's 145,366 edges and corrected derivative's 145,363 remain distinct; no result was reassigned.

All claims above were obtained by read-only file inspection, hashing and simple JSON counts. No code generator, scoring utility, model or database was imported/executed. No substantive results recomputed. This checkpoint is an inventory, not a full experimental reproducibility certificate or final closure of reviewer point 2.

## Next bounded evidence request

Ask Antigravity for existing (not reconstructed) code matching 430fc1b3..., historical configuration capture showing caps, graph/index fingerprints for primary/pilot/external experiments, and documented relationship of the two generator identifiers. If unavailable, mark unavailable and propose qualified provenance disclosures. Its reply must cite exact artifacts and fields, not fill gaps from later code. Any new extraction utility belongs to Antigravity under the user's coding arrangement and returns for source audit first. No experiment, manuscript patch, runtime config edit or graph change follows automatically.
