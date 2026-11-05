# Matched comparison: steps 1–5 complete

Codex implementation and self-verification, 25 October 2026. The user authorized completion of the compatibility check, fresh study, audit, prespecified statistics and working-source integration after Antigravity-0298. This report is not an independent external/practitioner audit. Step 6 (compilation and rendered-PDF/page-budget review) has not been performed.

## Main finding and its important qualification

All 350 assigned queries completed in a fresh generation; the earlier 83-pair partial run was not resumed or combined. Both judges supplied numeric scores for every arm, so all 100 assigned Category B pairs enter the primary analysis.

Category B mean composite evidence faithfulness was **0.49515 for hybrid dense–BM25 retrieval (H)** and **0.76400 for graph retrieval (T)**. The absolute paired T-minus-H difference was **+0.26885**, with a 10,000-resample percentile-bootstrap 95% interval of **[0.16035, 0.37205]**. The two-sided 100,000-draw paired sign-flip test produced zero draws as extreme as observed; its plus-one Monte Carlo probability is **1/100001 ≈ 0.000010**, the simulation's resolution floor—not an exact zero probability.

**This is not evidence of better answer coverage or legal correctness.** On Category B, T triggered **69/100 verifier-based refusals**, versus **4/100 for H**. Generation was therefore invoked for 31 T candidates and 96 H candidates; generation invocation is not itself proof that a substantive/correct answer was produced. The primary score evaluates the entire shared gated pipeline, including justified or unjustified abstentions assessed by the judges, not graph answer quality in isolation. Refusal necessity was not independently adjudicated by legal experts. The manuscript and conclusion now state this tradeoff prominently.

## Descriptive results across all assigned categories

These secondary summaries are descriptive; no additional significance or multiplicity claims are made. Scores are normalized evidence-faithfulness composites, not legal-accuracy percentages.

- **A, 100 pairs:** H mean 0.89500; T mean 0.97500; difference +0.08000. Verifier refusals: H 47/100, T 74/100.
- **B, 100 pairs (primary):** H 0.49515; T 0.76400; difference +0.26885. Refusals: H 4/100, T 69/100.
- **C, 75 pairs:** H 0.993333; T 0.966667; difference −0.026667. Both arms refused all 75 queries. This adverse T difference is retained.
- **D, 75 pairs:** H 0.813333; T 0.843333; difference +0.030000. Refusals: H 46/75, T 54/75.

There were no null composites or excluded pairs. The missing-score policy remains unchanged: nulls would never be converted to zero; inference would be conditional on assessable pairs with assigned-cohort sensitivity bounds. All 100 primary query text hashes are distinct. Resampling remains conditional on this fixed, researcher-constructed benchmark, not a probability sample of legal practice or a test of deployment correctness.

## Completed execution and accounting

- Renewed fictional-input compatibility probe: exactly five calls, all five role formats and exact expected model identifiers accepted; conditional reference cost **$0.010246633**. Native exit/whole-tree termination/handle closure and 29,443-file/three-root pre/post checks passed. Provider-minus-local count differences were observed; they do not isolate schema-only overhead or certify every possible context.
- Fresh study: **350 completed query pairs**, **2,706 unique requests, responses and settlements**, **zero unresolved reservations**, **zero rejected outputs**, no HTTP retries or query replacements. Calls comprise 350 router, 700 verifier, 256 generator, 700 judge-1 and 700 judge-2 requests. The 444 omitted generator calls correspond exactly to verifier-triggered refusals; both judges still evaluated each refusal.
- Fresh-study reference token cost: **$61.935583015**, below the **$280** fresh-study client cap. Including the prior partial study ($10.847801358), the earlier five-role smoke ($0.007841540), and the renewed probe gives **$72.801472546 in known conditional reference consumption**, below the agreed $300 reference budget. The zero-call timing-failure probe added no exposure.
- These are integer-ledger calculations at the disclosed, unconfirmed $1/DBU conversion, not an independently verified invoice, credit balance or certification that ancillary charges are absent. GPT-OSS reasoning/completion billing uncertainty remains disclosed.
- Worker elapsed **355.87 minutes**, peak **1.70 GiB**, within 12 hours/4 GiB. Enclosing native Job elapsed **365.13 minutes**, peak **2.10 GiB**, within 13 hours/6 GiB. This includes conservative client pacing and is not a production per-query latency comparison.

Observed returned identifiers were `gemma-3-12b-it-060225` (router), `meta-llama-3.3-70b-instruct-121024` (verifier/generator), `qwen3-next-instruct-091725` (judge 1), and `gpt-oss-120b-080525` (judge 2). These bind observed response identities, not independently certified weights or server templates.

## Audit and reproducibility checks

`postrun/AUDIT_RESULT.json` records `PASS_COMPLETE_350_AUDIT`. It reconstructs every completed artifact from persisted raw HTTP bodies, exact serialized request policies/schemas, retained evidence, actual candidate answers, verifier decisions, judge outputs and monetary settlements. Request/response digests, usage arithmetic, per-role prices and expected IDs were checked. No model was asked to rescore outputs during the audit.

The native controller's before/after observations match for **30,569 pinned files and five complete roots**; protected original-store/cache integrity passed. After confirmed process-tree exit, the executed admission files were preserved and their exact held versions restored. A separate current-input check verified the remaining identities with that explicit closure delta. Both study and probe admission gates/anchors are held. No paid process is left running by this task.

`FINAL_VERIFICATION.json` separately recomputes the 100 primary differences from raw judge scores using decimal arithmetic, independently recodes the bootstrap and randomization calculations, and confirms the reported estimate, interval and probability. This is additional implementation self-verification, not an external independent review. Analysis code and its four denominator/null/arithmetic fixture tests were fixed before fresh study dispatch. The live source generation had 277 named regression tests passing before admission.

## Working manuscript and supplement

Completed updates are limited to two existing working files (`main.tex`, `TERRA_SUPPLEMENT.tex`) and two added inputs (`matched_comparison_main.tex`, `supplement_matched_comparison.tex`). The new section separates the prospective controlled comparison from the historical multi-baseline evaluation, reports the primary result and refusal tradeoff, and supplies the protocol, secondary results, model-family and provenance limits, missingness policy and failed-attempt history. The conclusion also distinguishes historical results and the new tradeoff.

All **42 other preserved working dependencies**, including original generated statistics, figures/tables, assessment material and detailed limitations, remain byte-identical. No original archive, raw historical results or canonical release was promoted or overwritten. The two new TeX files passed static brace/environment/math-delimiter and numeric-consistency checks. No new citation keys were introduced.

The local integration initially stopped on an LF/CRLF anchor mismatch. Its partial source and original log are retained under `partial_integration_v1/`; the exact baseline was safely restored before the newline-tolerant repair was applied. Three isolated integration fixtures (LF, CRLF and mixed newlines) passed afterward. This repair changed no measurements, statistical methods or paid calls. A subsequent wording clarification distinguishes a separately generated run from independent external review and documents the base-42/randomization-43 seeds.

**No PDF was compiled, rendered or claimed to fit 25 pages.** That remains step 6 after the user accepts this report. Static checks do not substitute for rendered layout/reference verification.

## Files to inspect

- `ANALYSIS_RESULTS.json` and `PER_QUERY_ANALYSIS.csv`: full prespecified numerical outputs and paired ledger.
- `postrun/AUDIT_RESULT.json`, `CURRENT_INPUT_VERIFICATION.json`, `GATE_CLOSURE.json`: execution/output/accounting/integrity evidence.
- `FINAL_VERIFICATION.json`: independent arithmetic recoding and final source checks.
- `WORKING_INTEGRATION.json`, `working_source.diff`, `manuscript_before/`, `manuscript_after/`: exact source changes and byte-preserved generations.
- `freeze/`, `attempt/results/`, `attempt/*terminal.json`: frozen authority/input packet, untouched raw request/response and monetary evidence, native terminals.
- `manifest.json` and `FINAL_SEAL.json`: final evidence/source identities; verified database copies are excluded from this report manifest because their lifecycle parity is already recorded separately.

The earlier failed paid attempt and zero-call probe remain preserved under their original namespaces and locks. No result selection, threshold tuning, missing-value fabrication or retrospective malformed-output repair was used to obtain this completed generation. Antigravity's existing concurrence concerned code/pacing repair; a separate peer review of this final result packet is prepared rather than falsely claimed completed.
