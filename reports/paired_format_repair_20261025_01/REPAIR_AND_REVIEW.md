# Response-format reliability correction: code complete, live compatibility untested

25 October 2026, Codex implementation self-verification. User authorized the proposed code-only correction and review. No paid requests, credentials, real model/tokenizer operations, scientific statistics, manuscript changes or promotion.

## Concrete correction

New `scripts/matched_baseline/paired_output_format.py` defines simple proposed JSON schemas for the router, verifier and judges, bound to the exact previously reviewed serving endpoint names. The generator remains plain text. Both arms use the same role policy. The judge schema permits numeric or null faithfulness and the existing outcome vocabulary; the unchanged local parser enforces numeric bounds, exact keys and nonempty rationales/reasons.

`paired_dependency_bridge.request_policy()` now includes `response_format` in the actual serialized HTTP body for those exact role/endpoint mappings. `template_policy()` separately forwards only the previously reviewed GPT-OSS low reasoning option to the local tokenizer. No invented local schema-token accounting or provider prompt-equivalence claim is introduced.

The prompt-contract digest now incorporates the versioned output-schema/endpoint contract without changing scientific prompt strings. `paired_study_runtime.validate_composed_result()` checks persisted body fields, schema and reasoning policy against the role and journal endpoint. Tests reject missing, changed and extra fields even when an adversary recomputes the superficial request hashes. Full live context still rejects unreviewed endpoint mappings; legacy synthetic endpoints deliberately retain unstructured fixture requests.

## Evidence and tests

`TEST_RESULT.json` and `TEST_OUTPUT.txt`:271 tests across20 explicitly named suites pass,28.731 unittest seconds, no failures/errors/skips. Recorded source/test/fixture hashes match before/after. The inherited large stress fixture retains its previously disclosed fsync stub; this is not a new durability certification.

Six new tests cover actual static HTTP-body serialization across all five roles and both arms, generator exclusion, no fake schema arguments to local templates, deep-copy isolation, null/range/exact-key validation, persisted schema/body tampering, and paid-usage-before-rejection/no-retry behavior. The historical response fixture is explicitly identified as real saved provider content under a synthetic transport envelope; no historical account files are opened by the suite.

The first focused test invocation found a mock-only missing `reasoning_effort` parameter and duplicate discovery from an imported TestCase class. The test fixture was corrected to support the real low-reasoning contract and imported by module alias; production behavior was not relaxed. Final coverage is271 unique executed tests.

`tests/fixtures/paired_verifier_invalid_json_20261024.json` preserves the exact assistant content from A084:T:verifier, linked to response SHA256 `c0735744a4a25278c98ed6018c01d30edf8f95969b8ff5d36f34498337ab1cd1`. The malformed trailing quotation mark still produces Invalid JSON; the code does not repair, accept or replay that paid response. A static transport regression confirms a similar attempt settles its two sent requests then stops with zero completed pairs and no retry.

Before-source copies, final-source copies, source.diff and per-file manifest accompany this report. Prior failed-attempt audit's110 manifested evidence files are reverified unchanged. Executable admission remains False; anchor remains null; no new attempt namespace or authorization is created. Existing completed partial results belong to their frozen source generation and must be audited using that generation, not silently reinterpreted with the new contract digest.

## Provider evidence and remaining checkpoint

Official [Databricks structured-output documentation](https://docs.databricks.com/aws/en/machine-learning/model-serving/structured-outputs), dated13October2026 and inspected25October2026, documents `response_format` for supported chat models and JSON-schema output. It warns of provider prompt changes affecting token consumption and limits on supported schema constructs. This design avoids unsupported composition/pattern constructs, but the documentation does not prove behavior of these exact deployed endpoints or eliminate every malformed/refused/truncated response.

The new field is therefore a code-complete PROPOSED request policy, not empirically certified compatibility. No claim that six offline tests prevent all future malformed JSON is made. Peer review should inspect the actual source/diff, persisted-body checks and regression fixtures. After review, a separately authorized bounded endpoint compatibility check and renewed accounting/prompt-cap review are needed before proposing a fresh full study. No retry/resume of the failed attempt is permitted. Provider-added schema overhead is not included in prior authentic local prompt measurements or independently certified by the current reference reservation.

## Antigravity task

Read-only review of this saved source/evidence package. Do not rerun tests, open real models/assets, access credentials, invoke providers, modify source/gates or promote. Return attributed findings with exact paths/lines, especially schema compatibility assumptions, journal/body linkage, null semantics and historical-generation separation. Peer concurrence is not paid execution authority.
