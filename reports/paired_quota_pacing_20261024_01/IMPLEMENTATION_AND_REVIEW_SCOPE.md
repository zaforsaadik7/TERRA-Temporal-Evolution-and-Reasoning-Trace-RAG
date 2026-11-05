# Quota pacing and worker-context admission contracts

Codex implementation self-verification, 24 October 2026, Asia/Dhaka.
Code-only continuation of Step 3. No authentic execution or financial authority.

## Peer reconciliation

Antigravity-0295 independently matched SHA-256
`3a7e160b2fb34841b5679069157cac9aaa9320b5a05a6bcd375488f9f8633cc0`.
All46 rows of the prior runtime manifest matched before editing. Source/test and
STATUS.json before copies are preserved. Antigravity's independent193-test pass
is attributed to its report, not a Codex-witnessed external execution.

Two peer wording limits remain: the existing storage guard checks logical bytes
against an evidence allocation, not physical free disk space. A local scheduler
cannot guarantee the provider will never reject a request with429. Also, the
$1/DBU factor is an assumed dollar ceiling, not a published or verified account
price. No change to the proposed300USD cap or214.339641600USD reference token
reservation follows from this reconciliation.

## Implemented quota pacing

`paired_quota_pacing.py` adds immutable wait/tick/check limits and shared-endpoint
quota validation. Conflicting generator/verifier quotas and a single request
larger than its quota fail before any HTTP connection. Pacing uses the existing
shared EndpointLimiter. An unavailable UNSENT request may wait in cancellable
ticks of at most one second, with durable QUOTA_WAIT events. Deadline, check-count,
clock, cancellation and evidence failures stop before monetary reservation.
No sent request is replayed. Waiting on local admission is not a provider retry.

`paired_study_runtime.py` accepts an explicit PacingPolicy and injected clock/pause,
records the quota/pacing configuration in the study contract, and rechecks full
request/response evidence headroom AFTER pacing before reserving money. This
second check is needed because wait logs themselves consume evidence capacity.
The default policy remains fail-fast (zero wait); no genuine quota or wait policy
was selected, inferred from an empty list, or silently activated.

Fake-clock integration demonstrates a full paired computation waiting180 simulated
seconds on one shared Llama endpoint, then sending exactly nine unique HTTP fixture
calls, with nine reservations/settlements. Cancellation and short wait deadlines
do not create an additional monetary reservation, secret read or HTTP connection.
Rate reservations remain conservative; short answers do not refund local capacity.
Account-specific quotas, a reviewed chosen pacing policy and an independent outer
watchdog covering all wait time are still required before authentic execution.

## Implemented worker context / approval contracts

`paired_worker_contract.py` adds bounded strict canonical JSON decoding against an
independently supplied digest and independently reviewed bytes. It validates the
350-row cohort identity/category contract, local loader plan, dedicated output
namespace, explicit role configurations, exact observed endpoint/model mapping,
shared quotas and pacing. Output cannot overlap the declared protected assets or
the benchmark/graph input file. Complete input-manifest identity is required.

The top-level scopes are distinct:
- `PAIRED_350_LOCAL_PROMPT_MEASUREMENT`: zero spend, zero provider calls.
- `PAIRED_350_LIVE_COMPARISON`: at most3150 calls, one attempt, and a positive
  client cap no greater than the proposed300USD ceiling.

The reused CohortSpec describes the existing canonical input identity. Its old
offline scope field does not authorize paid inference. The NEW separately bound
approval requires matching top-level scope, context and input-manifest digests,
dated human-decision record, attempt/call/spend limits and explicit API permission.
An old offline-cohort approval cannot satisfy that live approval contract.
Manuscript changes and promotion remain disallowed. Unknown fields, embedded
credential fields, model-discovery aliases, extra CLI switches and substituted
CLI paths are rejected.

These are consistency validators, not human-authority/provenance certificates.
No genuine approval record or populated launch packet was created. The complete
input manifest must still be observed/verified by the eventual parent. Receipt,
parent/child command, native resources and independent outer-watchdog bindings
are still separate required work. `main()` returns2 BEFORE parsing or reading
files. A module that rejects invalid inputs is not a functioning native launcher.

## Verification

Final R02 named twelve-module run: **222 tests PASS in24.555 seconds**, exit0,
zero failures/errors/skips. Exact command/output and27 source/test digests are in
TEST_RESULT_R02.json/test_output_R02.txt. All27 digests matched before AND after
that execution. Earlier221-test result is preserved, superseded by R02. A final
headroom repair and its extra test were added while that earlier run was active;
the unambiguous pinned R02 generation is the final validation evidence.

New tests cover local input/output/hourly quota windows, bounded waits, fail-fast
default, cancellation, regressing/frozen clocks, shared quota conflicts, wait-log
failure, full paired no-replay pacing and post-wait storage headroom. Worker tests
use explicit synthetic350-row identities and fictional approval records only;
they never open the actual benchmark or assets. The inherited static350-query
stress case retains its disclosed fsync stub. Other tests use temporary files and
static HTTP fixtures; no real sleeping, network, model or native API execution.

## Step 3 status

Completed in this batch: local scheduler implementation and integration; strict
worker-context/approval/CLI consistency contracts. Public authentic entries stay
held. Existing provider accounting, candidate prices, local assets, scientific
artifacts, native source flags and all historical attempt directories unchanged.

Step3 remains IN PROGRESS. Remaining work: actual native parent/child bootstrap
and independently supervised launch packet; bounded authentic revised-prompt
measurements; account-specific quota/pacing selection; rubric/assumption acceptance;
final source/input/decision freeze and dated user authorization. The current
user's less-than400USD instruction is a budget constraint, not live-call permission.

Next implementation should connect these validated contexts to the native parent
and child bootstrap, including source/input/receipt and resource-policy binding.
Do not replace that work with another freely supplied mode flag or a successful
synthetic callback. Authentic measurement and live execution remain separate.

No credentials, workspace/API calls, actual model/tokenizer/store operations,
firewall changes, manuscript/statistics changes or promotion occurred.

## Peer review request

Antigravity: review source.diff and actual final code/tests, especially pacing
ordering, cancellation/budget boundaries, post-wait evidence reserve, shared
endpoint policy and live-vs-measurement scope separation. Do not infer prevention
of all429s, native execution readiness or user authority from these tests. No
genuine execution, gate changes or parallel implementation requested.
