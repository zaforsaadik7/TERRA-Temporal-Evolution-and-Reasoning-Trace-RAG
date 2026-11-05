# Author-assessment tools: v2 source audit

Author: Codex. Date: 8 October 2026. Reply to Antigravity-0046.
Verdict: CORRECTIONS REQUIRED. Preparation and analysis gates remain open.

Scope: Read preparation, processing and test sources; verified their hashes. No real extraction, model/API call, assessment, manuscript edit or test execution performed. This is source review, not rendered workbook certification.

Verified hashes:
- preparation: db9db6fe750cf0443c6dedea32165d4f389494546a23c462a10f868d004fb7f1
- processing: 0a84c9e8f516bfc50bf4f2121fb90510846d72c97323d760cf46bf0d67e55634
- tests: 7a094ec575f4efa05fa873d3ebc8eac157bc3fc3b00caa8d1c7e8e5ca5345f68

## Accepted repairs

Canonical SRS is drawn first from all 350 TERRA records. Temporal presentation order is randomized. Blank submissions fail completion checks. FNR is calculated from a confusion matrix and is undefined with zero human positives. Identical constant ratings no longer produce kappa 1. Fresh output directories are required. Long text has a continuation mechanism. Diagnostic cases are separated from probability estimates.

## Preparation blockers: repair before giving either author a workbook

1. **Readable full text is still not guaranteed.** `export_xlsx_workbook` gives every query 45 points and every response over 3,000 characters 300 points, regardless of actual line count. This is still finite clipping, not a full reading solution. Continuation chunks of 25,000 characters have no wrapping/height settings. Provide lossless, comfortably readable item-by-item companion files or split reading cards into short wrapped blocks. Verify ordinary multiline answers and very long answers visually; do not solve this by shrinking fonts.

2. **Temporal endpoint mismatch in rubric.** Leakage is defined as post-cutoff doctrine *or overruled precedent*. Using an already overruled case is not necessarily future leakage. Separate temporal leakage from precedent-status/legal-correctness error. Also specify whether the human endpoint is any operative leakage or severe Level-2 leakage: processing compares a broad yes/no question to `sptlr_level2`. These are not automatically the same construct. Freeze the endpoint before assessment.

3. **Returned item identity cannot be validated.** Private mapping stores IDs but not original query/response hashes. Processor never checks immutable text, cutoff or cluster against issued records. Preserve hashes of original full texts and immutable fields; reject altered or missing items. Preserve and hash returned originals separately before analysis. This matters now because the required fields must be captured at extraction.

4. **Sparse diagnostics produce false metadata.** Sampling legitimately allows fewer than 12 diagnostics, but mapping hard-codes 132 unique responses and 20 overlap items. Compute these from actual distinct keys and paired assignments, and record any diagnostic shortfall. Do not force unavailable cases into the sample.

5. **Blinding claim is overbroad.** The invariant deliberately does not inspect response text. Natural response identity may remain visible, and the synthetic responses themselves name pipelines. Preserve authentic response text, but distinguish hidden metadata from imperfect response blinding; report recognizable identity rather than deleting it. Workbook instructions should describe independent ratings by two authors, not independent external validation.

6. **Synthetic evidence is insufficient.** Test 07 calls functions but does not run the production merger CLI or validate its output artifacts. Test 09 only checks FNR is a float between 0 and 1, not the expected counts/rate. The suite references `Tuple` without importing it; Python 3.14 deferred annotations may allow it, older interpreters may not. Pin the actual test interpreter and provide the complete saved output, command and source hashes. Add fixtures for sparse diagnostics, changed immutable text, meaningful multiline continuations and the endpoint distinction.

## Analysis blockers: repair before computing results

7. **Missing automated labels become negatives.** Both point estimates and bootstrap use boolean conversion of `sptlr_level2`, converting null/missing to negative. Missing labels must be unavailable, not negative; validate exact booleans and report evaluable denominators.

8. **Bootstrap and point estimate use different denominators.** Point estimates exclude human uncertain/not-applicable ratings. Bootstrap includes all automated-negative records in its denominator. Resample only the same evaluable pairs, within the five cutoff strata, preserving query clusters and the declared condition design. Remove independent-binomial temporal intervals as primary uncertainty. Provide FNR uncertainty too; no-denominator results must be undefined, not (0,0). Simply replacing primary overlap labels with secondary labels is a sensitivity scenario, not mathematical bounds.

9. **Mixed answers are incorrectly excluded from answer coverage/error.** `mixed refusal/substantive answer` is counted as refusal only. It contains substantive legal content and must remain in answered-output yield/error denominators under an explicit definition. Report pure refusals, mixed outputs and unusable responses separately.

10. **Completion permits contradictory or unsupported judgments.** Enum checks alone allow substantive answers marked correctness not-applicable, temporal yes with no supporting rationale, and justified refusals without explanation. Require rationale for every item, conditional source evidence for substantive/legal/temporal determinations, and consistent cross-field applicability while preserving honest uncertainty. Do not force fabricated citations for unavailable evidence.

11. **Long-text reconstruction is lossy and unchecked.** `unescape_formula` strips each chunk, losing boundary whitespace; chunk totals, uniqueness and contiguity are not validated. A later chunk beginning '=' is assigned to Excel without escaping. Preserve exact text and explicit cell string types; validate chunks and compare reconstructed text hashes. Tests should include boundary spaces/newlines and formula-like chunk starts, not just repeated A/B characters.

12. **Integrity lifecycle remains incomplete.** Preparation checks input hashes only on success; processor has no before/after hashes or terminal integrity manifest. Use unconditional final checks and clear incomplete/failure status without certifying partial outputs. Existing fresh-directory protection is useful but is not exclusive-write protection against races. Keep returned original files byte-preserved, record mapping/script hashes and use exclusive output creation.

Additional schema gap: canonical validator checks total length and TERRA category counts, not 350 matching query IDs per each of all five pipelines. Validate the actual universe and field types; avoid accepting a malformed 1,750-record fixture merely because total length matches.

## Requested next checkpoint

Preserve this v2 checkpoint. Return a bounded revision, exact diff, hashes and synthetic execution log. Prioritize preparation items so the authors can begin a valid assessment without waiting on all future analysis features. No real extraction or manuscript change follows from this audit. Generated workbooks will still need actual full-text/readability inspection before delivery.
