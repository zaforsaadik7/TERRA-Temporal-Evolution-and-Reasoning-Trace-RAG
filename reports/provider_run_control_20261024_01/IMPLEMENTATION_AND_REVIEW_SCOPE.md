# Provider HTTP and run controls: synthetic checkpoint

Codex implementation self-verification, 24 October 2026. Code-only work authorized by the user. No real HTTP connections, credentials, provider/model/tokenizer/store operations, experimental results, manuscript/statistics changes or promotion.

## Implemented

provider_run_control.py adds a single-POST HTTP exchange core, with no redirect following, retry loop or SDK retry. It checks observed cancellation/deadline around connect/request/header/read boundaries, updates socket/connection timeout with remaining duration, accepts only successful JSON responses, validates declared lengths and reads at most the configured response cap plus one byte. Owned connection is closed on exchange failure/success. A real HTTPSConnection factory using the default certificate/hostname-verifying TLS context exists behind TLS_FACTORY_ADMITTED=False; the flag was not opened and the genuine branch was not executed. The public study runner unconditionally raises.

StaticCallSession permits only exact StaticConnection fixtures and one request at a time per session. A conservative endpoint limiter combines generator/verifier use of the same endpoint across roles. Host case/trailing slash do not create separate rate buckets. Input and output minute reservations and hourly calls are distinct; a local quota wait occurs before money reservation or POST. It returns a wait instruction, never sleeps or retries automatically. Reserved quota is not optimistically credited after shorter completions or failed attempts. Shared limits and actual quotas still need workspace evidence; this is not a distributed rate service or a prediction that the provider will accept a call. A wait indicates an earliest expiration; a subsequent admission check is still necessary.

Before the simulated POST, the accounting journal durably reserves cost and the run store durably records the request. Exact response bytes (base64 plus SHA256) are retained before parsing. Known usage is settled before model/content acceptance. Timeouts, 429, redirects, malformed/oversized responses, unresolved usage or persistence failures retain conservative billing exposure and stop the session. An invalid model with known usage is charged and stopped, not treated as a free failure or safe refusal. No exception message or Authorization header is written into the run evidence. Actual credentials are never supplied; the fixture bearer marker is not a secret.

SyntheticRunStore creates an exclusive new directory and persistent single_attempt.lock. No stale-lock adoption, deletion or automatic resume. Query results must follow the declared unique manifest order. Before successful finalization, exact required call identities are checked against all settled ledger entries: shared router, verifier and both judges per arm, plus generator only when the recorded verifier passed. Missing, extra or unresolved calls prevent completion. The marker says SYNTHETIC_COMPLETE/provider_certified=false, not live success. Case/legal/scoring semantics still belong to the paired workflow rather than this persistence layer.

Run evidence writes are bounded and reserve 4 KiB for terminal finalization. Persistent disk failure can still prevent a terminal record; absence is a failure requiring inspection, not a recoverable success. Evidence cap covers this store's files, not external accounting journals or a global OS disk quota. Initial capacity and symbolic-link/reparse ancestry are checked, without claiming race-free path security. A production study must bind the journal and all outputs into one reviewed owned namespace with a complete aggregate budget and independent watchdog.

## Validation

Final command: venv/Scripts/python.exe -B -m unittest tests.test_provider_run_control_synthetic tests.test_paired_prompt_workflow_synthetic tests.test_provider_accounting_synthetic tests.test_matched_baseline_synthetic

127 tests in 1.031s, OK; zero failures/errors/skips. Breakdown: 30 new run-control tests, 25 paired-workflow tests, 31 provider-accounting tests, 41 original matched baseline tests. Earlier incremental runs passed 122 and 126 cases before final call-graph/timeout refinements.

Tests use only static HTTP response objects, synthetic.invalid endpoint descriptors, an explicitly non-secret bearer fixture, injected clocks and temporary files. They cover exact single POST/path, no auth logging, redirect rejection, 429/no retry, request/header/read timeout, cancellation, remaining-time updates, content/length limits, malformed raw-byte preservation, usage before unknown-model failure, terminal stop, shared endpoint rate limits, clock regression, hourly versus token quotas, no spend on local rate wait, persistent run collision, ordered/duplicate query output, missing/unresolved call completion rejection, finalization reserve and pre-POST write/budget failure.

Prior provider-accounting, paired workflow, matched harness, serializer and analyzer source bytes remain unchanged. No broad test discovery or genuine TLS factory test performed.

## Remaining boundary

This is a tested HTTP/persistence/control component, not an executable authenticated study packet. StaticCallSession does not connect the paired workflow to genuine transport or real retrieval/tokenization. TLS timeout and clock polling alone do not prove hard interruption of every native/network stall; an independent admitted watchdog is still required. Rate/history state is process-local and no automatic resume is supported. Effective endpoint limits/pricing, role/prompt/rubric acceptance, authenticated identity checks, secret handling, full run namespace/aggregate budgets and final source freeze remain pending. No key needed for peer review or further code integration.

Review against the official Databricks API/limits references already captured in preparation R01. No new live compatibility or actual account billing certification follows from these static fixtures.
