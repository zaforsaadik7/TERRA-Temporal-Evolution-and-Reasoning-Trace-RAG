# Live matched comparison — preparation R01

Codex, 24 October 2026. Planning and static source inspection only. No credentials, authenticated requests, inference, model loading, package installation, manuscript/statistics edits or promotion. Offline feasibility is complete; live readiness is not.

## Evidence and unchanged study intent

Read the original PROTOCOL_DRAFT.md, Codex-0099/0100, current matched_harness.py/scoring_analyzer.py/common_serializer.py, successful cohort audit and Antigravity-0290. The peer acknowledgment SHA256 is 037912616dff96b55cfce6b89324940fc85c81d56c512ad4dcf224120306db26. It is bounded peer concurrence with Codex's evidence, not a second independent full-file audit.

Retain 350 paired queries (100/100/75/75); shared one-query EASY/HARD router decision; both arms evaluated prospectively. Arm H is annotation-matched BM25+dense fusion; Arm T is controlled graph traversal with identical evidence serialization and common budgets. No new-versus-historical comparison. Benchmark exposure and generic procedural scaffolds remain disclosed. Primary proposed endpoint remains Category B paired mean two-judge faithfulness difference, 100 pairs, with fixed-seed 10,000 paired bootstrap resamples and 100,000 sign-flips. These are automated rubric outcomes, not legal correctness.

Existing proposed role descriptors, pending actual workspace availability and response identity evidence:

- Router: Gemma 3 12B IT; databricks-gemma-3-12b.
- Generator and verifier: Llama 3.3 70B Instruct; databricks-meta-llama-3-3-70b-instruct.
- Judge 1: Qwen3-Next-80B-A3B-Instruct; databricks-qwen3-next-80b-a3b-instruct.
- Judge 2: GPT-OSS-120B; databricks-gpt-oss-120b.

These names are prospective descriptors, not confirmed served identities. No substitution follows from availability changes. Account/cloud/region/tier/root URL, deployment mode and effective billing rates remain unresolved. The user's Databricks choice is already recorded; do not ask them to select a provider again.

## Static gaps confirmed

1. MatchedHarness.__init__ rejects AUTHORIZED_LIVE and requires SyntheticMockAdapter callbacks. Keep that old mock boundary intact; introduce a separately reviewed live composition rather than disguising network callbacks as mocks.
2. CallLedger supports pre-call reservation and settlement, but mocked orchestration paths call reserve_call without a priced estimate and settle_call without provider usage/cost. Zero defaults are not live billing evidence. Its prototype $100 default is not approved spend.
3. Callback return types are bare strings/tuples/scores, insufficient to preserve request ID, requested endpoint, returned model identity, finish reason and raw usage. Scoring parsing must be separate from transport/usage settlement.
4. QueryInput defaults category to B while benchmark uses B_Evolutionary. Explicit analysis-only taxonomy mapping is required; no category or gold metadata may enter routing/retrieval/generation.
5. Frozen real prompt texts, structured router/verifier/judge outputs, refusal scoring, missing-score handling, secondary multiplicity family and role-specific output caps still need a single prospective contract. A mock passing score is not a validated judge rubric.
6. Offline hypothetical routes and placeholder judge answers do not measure actual generated-answer judge input lengths. Recompute local bounds from the frozen prompt structure plus the maximum answer reservation without asserting provider-template equality.

## Next implementation batch: code and synthetic fixtures only

Implement isolated live contracts, request construction and usage accounting with injected transport. Import/constructing modules must never read secrets or dispatch requests. Network execution remains explicitly held.

- Immutable RoleConfig binds endpoint descriptor, accepted response identity mapping, context/request-byte bounds, temperature and output/reasoning settings, timeouts and dated price identity. Missing values reject executable config.
- ProviderResult preserves response metadata and raw usage separately from parsed content. Use JSON messages for chat invocations; local rendered templates count local tokens only. No Harmony delimiter strings injected into ordinary provider messages.
- Each logical call has stable query/arm/stage identity; each attempt has separate identity. Persist reservation before dispatch, actual usage and settlement before score parsing. Provider usage takes precedence for accounting; preserve local/provider differences. Validate finite integer usage and versioned rate arithmetic using integer currency units or Decimal, not float budget comparisons.
- On transport timeout or missing usage, retain a conservative unresolved monetary reservation; never assume free, retry automatically, release budget or classify as safe refusal. Endpoint changes, truncation, missing/unaccepted model identity and malformed output are explicit failures. Disable hidden SDK retries. Proposed initial retry count zero; this is not permission to call.
- Injected fixtures cover success, 429, timeout after possible provider acceptance, missing/malformed usage, unknown model, truncation, reasoning usage semantics, cost ceiling under concurrent reservations, interrupted persistence/restart, duplicate logical calls and unknown billing. Reasoning usage must not be double-counted without a documented pricing convention.
- Preserve existing mock harness behavior; named synthetic tests only. No real tokenizers/stores/network/model initialization. Do not enable live gates or change existing study data.

## Remaining packet before a key is requested

Freeze real prompts/parsers/rubric and parity tests; complete live orchestration integration; record endpoint-specific context and output limits, provider identity mapping and price evidence; derive priced conservative attempt envelopes; peer-review code and packet. All 350 shared router calls plus at most 700 verifier, 700 generator and 1,400 judge calls total 3,150 logical calls before separately allocated smoke/retries. Refusal short-circuits can reduce calls, not justify a smaller guaranteed cap. No dollar estimate is defensible until effective rates/deployment mode are known.

Budget formula: sum over role/attempt of reserved input tokens times input rate plus reserved billable output/reasoning tokens times applicable rate, plus fixed deployment charges where applicable. Use per-role explicit caps and price units; no inference of actual charges from an illustrative public list rate. Propose one active request initially; shared generator/verifier endpoint rate budget is aggregated. Wall-time estimate remains pending endpoint quotas/latency, separate from the local offline 34-minute duration.

After the reviewed packet is concrete, ask for non-secret workspace URL/cloud/endpoint and billing configuration. Then notify the user that a locally stored Databricks key is needed for a separately authorized bounded metadata check. Metadata GET and billable inference smoke are separate scopes. Smoke allocation, full study spend, retries and live execution each require actual user authorization. No live calls under this preparation request.

## Official public documentation checked 24 October 2026

- https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/api-reference — JSON task-specific requests; usage fields; server-added prompt text can contribute to prompt_tokens. Treat local tokenization as a local estimate, not a provider usage certificate.
- https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits — limits depend on model/deployment/tier; input/output rate reservations and query limits are distinct. Published model output limits do not confirm the user's workspace limits.
- https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/supported-models — model availability reference, not authenticated workspace evidence.

Public documentation is mutable and must be refreshed at final price/endpoint freeze. No historical provider configuration or exact backend weights are certified by these pages.
