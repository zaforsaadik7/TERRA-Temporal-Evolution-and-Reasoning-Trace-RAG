# Provider accounting contracts: synthetic checkpoint

Codex implementation self-verification, 24 October 2026. Reply to preparation R01 / Codex-0291. User authorized continuing implementation. No live call authority inferred.

## Implemented

New scripts/matched_baseline/provider_accounting.py adds immutable role/price/call/result contracts, JSON-message request construction, bounded strict JSON response parsing and integer-nanodollar usage accounting. Explicit configuration includes endpoint/accepted model identities, role/context/output/request/response/timeout limits and versioned price identity. Only reasoning included in completion-token billing is supported; other conventions require a new reviewed contract.

Reservations are written, flushed and fsynced before the synthetic response path proceeds. Settlement records actual provider usage and response metadata before output validation. Unknown model identity, incomplete output and malformed assistant content remain chargeable known-usage attempts and halt subsequent dispatch. Timeouts, HTTP errors including 429, missing/malformed usage and oversized responses retain their reservation as unresolved and halt. No automatic retries or duplicate logical-call dispatch. Shared router versus arm-specific stage identities enforced. Actual usage exceeding the reserved envelope is recorded honestly, then stops; already incurred provider charges cannot be undone or universally capped by client code.

Budget reservations are serialized by an in-process lock; this is NOT a multi-process ownership or billing reconciliation system. Fresh journal creation is exclusive. Existing/partial journals cannot be resumed automatically; inspection is read-only and issues no authority. Persistence failures poison the instance. Journal inspection checks event sequencing/transitions, not authenticity against external tampering. Future execution requires a separately frozen single-owner run and evidence manifests.

Synthetic dispatch accepts only static response bytes, not arbitrary callbacks or SDK clients. dispatch_live unconditionally raises. LIVE_ADMITTED remains False. No secret reads, network libraries, provider connection, SDK retry behavior, model/tokenizer initialization or database access implemented or exercised.

## Tests and source preservation

Named command: venv/Scripts/python.exe -B -m unittest tests.test_provider_accounting_synthetic tests.test_matched_baseline_synthetic

Final result: 72 tests in 0.232s, OK; no failures/errors/skips. First iteration: 69 tests OK before three added malformed-content/oversize/settlement-persistence tests and durable response metadata refinement. Static fixture prices and synthetic.invalid endpoints are explicitly not approved production settings. Temporary journals only; no real asset tests.

Cases cover actual versus local token counts; no double-counting reasoning; integer ceiling arithmetic; configuration validation; request bounds; model changes; truncation; malformed content/usage; 429/timeout uncertain billing; pre-dispatch caps; single logical attempts; thread-concurrent reservations; persistence failures; partial/corrupt transition inspection; exclusive file collisions and permanently held live dispatch. Existing 41-test matched baseline suite remains passing. Prior harness/serializer/analyzer bytes compared against preparation manifest; no edits.

## Remaining integration

This is the provider-contract/accounting component, not a ready Databricks network adapter or live run. Next bind real prompt/rubric/parsers and paired orchestration to these envelopes; introduce separately held transport and accepted endpoint/usage mapping; implement frozen single-owner run/evidence storage, cancellation/rate limits and explicit bounded request failures. Strict role output/reasoning settings may require endpoint-specific extensions after documentation/config review.

No numeric production price or spend cap adopted; no workspace availability certified. Fixed deployment charges are outside this token-price contract and must be absent or separately budgeted before use. Provider-added prompt text and unknown usage can defeat local estimates; conservative reservations and a bounded authorized endpoint check remain required. No claim of atomic hard spend guarantee across an unknown remote provider.

No credentials needed yet. Original scientific data, frozen offline packet, historical evidence and manuscript/statistics untouched. Peer review requested through the user-relayed mailbox; no automatic dispatch to Antigravity.
