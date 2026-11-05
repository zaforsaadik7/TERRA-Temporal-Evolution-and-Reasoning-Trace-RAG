# Single live attempt: failed partial run, audited 25 October 2026

Codex implementation self-verification. No retry, resume, new provider request or credential read was performed for this audit. Scientific analysis and manuscript/statistics updates were not performed.

The authorized run ended with FAIL after 83 completed query pairs (A001–A083), during A084's T-arm verifier. Native worker exit1 and outer exit1 are saved. Worker elapsed5004.27 seconds; outer5282.04 seconds. Both native records confirm complete-tree termination and closed handles. Controller protected-integrity PASS and before/after inventory observations are identical:30563 inputs/five complete roots.

## Confirmed cause

The saved response for `A084:T:verifier`, model `meta-llama-3.3-70b-instruct-121024`, has finish_reason `stop` and usage960 input/111 output tokens. Its content looks like the requested JSON object but ends with an extra quotation mark after the reason string (`...709).""}`). The unchanged frozen strict parser reproduces `ContractError: Invalid JSON`. Response SHA256 `c0735744a4a25278c98ed6018c01d30edf8f95969b8ff5d36f34498337ab1cd1`.

This is a confirmed output-format failure, not a timeout, missing-usage, model-ID, native-memory or price-cap failure. The complete original response is preserved in events.jsonl. It was not repaired and accepted after the fact. Only this response fails the frozen envelope/content validators among all671 saved responses.

## Accounting and saved-results consistency

-671 unique reservations,671 persisted requests,671 persisted responses,671 settlements; no unresolved reservations and no repeated call key.
-Conditional reference cost and exposure:10,847,801,358 nanodollars = $10.847801358 at the accepted but unconfirmed1USD/DBU assumption. This is not an independently verified invoice or available-credit balance.
-83 saved completed artifacts reconstruct successfully from raw responses, requests, retrieval/evidence records, composition traces and settlements through the unchanged frozen result validator. All other assigned queries remain incomplete/unattempted; this is not a350-query study.
-No primary Category B result is available: these completed IDs are the leading Category A portion of the fixed input order. Do not infer a matched-study outcome from the partial subset.

The final file check and source gate closure are recorded separately in CURRENT_INPUT_VERIFICATION.json and GATE_CLOSURE.json. Executed entry/anchor bytes are preserved before restoring the exact held source versions. Attempt locks and raw artifacts remain intact; no stale-lock takeover is allowed. The saved native failure and partial financial evidence must remain part of the experiment history.

## Next technical work

Prepare a separately reviewed output-format reliability correction against this exact saved failure, with deterministic offline regression coverage and provider capability evidence before selecting a new request policy. Do not silently relax the scientific parser or salvage this response into the completed cohort. Any new paid attempt, reuse/resume policy or changed protocol requires explicit human approval after that review; the consumed single-attempt authorization does not authorize it.
