# Paired runtime integration and Step 3 status

Codex implementation self-verification, 24 October 2026 (Asia/Dhaka).
This is not an independent external audit or a claim that Step 3 is complete.

## Received peer review and preserved baseline

Antigravity-0294 SHA-256 independently matched
`b383a7ca79140fdcc9bb77e8dc4981722b8afe77bba9a68d363325d2bc72b064`.
All **20** entries in the prior bridge manifest were verified before modification.
The peer's count of 19 was inaccurate. Its reported independent 161-test pass is
attributed to Antigravity; Codex did not witness that execution.

Three wording corrections are also necessary. `{key: dict(value) ...}` copies
the top-level node dictionaries, not nested values (it is not a deep copy).
BudgetJournal is an append-only file journal, not SQLite. Static responses were
pre-registered by call key; that registration was not advance approval of the
actual request bytes. Request bytes were checked at dispatch. These corrections
do not retroactively rewrite Antigravity's report.

Prior bridge source, tests and STATUS.json were copied before edits. Existing
provider accounting/control, tokenizers, retrievers, smoke clients, study results
and scientific artifacts were not edited. The bridge was changed to share its
computation internally and add query identity to retrieval trace events. New
source files and tests are enumerated in the manifest and source.diff.

## Implemented source

`paired_study_runtime.py` composes a serial paired study using the selected-route
bridge, shared endpoint quotas, bounded single-POST exchange, and BudgetJournal.
Reservation is durable before any connection or bearer callback. Exact request
and response bytes are persisted; usage is settled before content/rubric parsing.
Unknown billing retains exposure, stops the run and never retries.

StudyStore creates an exclusive namespace with a persistent no-resume lock.
Events and result files use flush/fsync; result/manifest/terminal publication
uses exclusive pending files and rename. A result is checked against COMMITTED
trace bytes and the settlement ledger, not just mutable Python event objects.
Validation reconstructs routes, verifier decisions, actual answers, both judge
scores, null composites, retained/dropped IDs, shared evidence and required call
graph from raw HTTP bodies. Success requires all ordered query results and the
exact settled call graph; failure retains partial evidence. The terminal still
requires a postrun audit and never grants execution authority.

The aggregate evidence reserve includes root files and a 4 KiB terminal reserve;
per-call headroom precedes dispatch. This is a serial polling/write guard, not an
OS quota or protection against an adversarial concurrent writer. Directory fsync,
crash-consistent multi-file transactions and native interruption are not claimed.
Revalidating committed traces/ledger per pair has growing I/O cost; no authentic
runtime performance claim follows from the small synthetic tests.

`paired_local_runtime.py` connects the existing receipt-aware cohort assembly to
the shared stored-text BM25/dense/graph retrieval bridge and role tokenizers.
Generator/verifier must share one tokenizer instance. Full population is 20,000
for the prospective authentic constructor. Assembly failures close owned
references and preserve combined cleanup errors. This is not proof of native
Chroma/ONNX shutdown; process-tree termination is still required.
The owned bundle is also handed through to the complete serial study runner;
success releases it once and failures retain both primary and cleanup errors.

`paired_study_supervision.py` binds a command, explicit non-secret environment and
resource policy to the existing suspended/assigned/resumed Job backend protocol.
It rejects policy drift, repeat dispatch and nonzero/unconfirmed completion.
Tests use a mock backend only. An authenticated parent/child CLI, final native
packet and independent outer watchdog integration are NOT implemented here.
Old source gates are not toggled by the new local-loading code.

The GPT-OSS path now explicitly sends reasoning_effort=low, matching the earlier
smoke, and passes that same option to local template rendering. The adapter's
default was medium, so omission would have made the prior measurement/request
pair inconsistent. A dedicated static-HTTP test covers both sides. Other models
do not inherit this option. The older JournaledFixtureTransport rejects custom
request policy rather than silently rebuilding an unaccounted generic request;
the new measured-call session supports the policy-bound request.

All public authentic entry points in the new modules remain held BEFORE inputs,
credentials, local asset loading, native execution or HTTP. The internal seams
trust injected collaborators. A private function and an authentic mode label are
not authority or provenance certificates. No full-run deployment is admitted.

## Tests and development chronology

The final named 10-module run is preserved verbatim in test_output_R02.txt and its
command, wall duration and saved-byte hash in TEST_RESULT_R02.json:
**193 tests PASS in 23.109 unittest seconds**, zero failures/errors/skips, exit 0.
The named suites cover 51 bridge/new runtime/local/supervision/candidate tests
and the 142 existing workflow/accounting/control/static-study/retriever tests.
Tests use tiny in-memory corpora, mock tokenizers, StaticConnection responses,
mock native backends and temporary files. No genuine assets were executed.
The inherited full static-study stress case retains its previously disclosed
fsync stub; this is not a 350-query real-durability or native-supervision test.

Initial new-runtime tests had four assertions against a nonexistent inspect()
`entries` key (the audit API returns `states`), and one wrong budget-exhaustion
fixture whose one-nanodollar cap actually admitted its one-nanodollar reserve.
Fixtures were corrected to the actual API and a deliberately larger price.
No accounting source changes or warning suppression were used. Subsequent
focused passes, an 187-test combined pass, a 191-test pass and the final 193-test
pass followed. The two later tests cover the owned-bundle handoff and combined
study/cleanup failure preservation. Earlier outputs/results remain preserved.
The initial captured-text output hash excluded Windows newline translation;
TEST_RESULT.initial.json preserves it, TEST_RESULT.json binds the saved bytes,
and R02 uses explicit LF and hashes the actual saved file. This was an evidence
record correction, not a source or test-result change.

## Budget proposal — NOT financial execution authority

User supplied: "I have total 400 dollar with that account so use less than 400".
Codex selected a proposed $300 client cap, below the user's bound, leaving $100
below the reported account balance. Balance/credits and effective account price
are NOT independently verified. No additional call was authorized or made.

STUDY_CANDIDATE.UNAPPROVED.json contains exact observed model identifiers (no
discovery aliases), candidate token caps and a 350-query/3150-call maximum with
zero retries and no new smoke allocation. Worst-case TOKEN reference reservation
is **$214.339641600** at the unconfirmed $1/DBU ceiling. It is not a certified
invoice ceiling, and it excludes unconfirmed fixed/ancillary account charges.
The past smoke cost is separate. A provider overrun may be charged before the
client can observe it; the journal accounts it and stops, not reverses billing.

Published pricing and API documentation were checked using public web access;
no workspace request or secret was used. Databricks explains that effective
price is SKU dollars per DBU times the model's DBU rate. Its API also documents
that server-added text contributes to prompt usage. Those facts do NOT establish
this account's effective price, remaining credits or exact server template.

Sources (24 October 2026):
- https://www.databricks.com/product/pricing/foundation-model-serving
- https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/api-reference
- https://docs.databricks.com/aws/en/machine-learning/foundation-model-apis/limits

GPT-OSS reasoning inclusion in charged completion remains an explicit assumption:
the smoke omitted a separate reasoning counter. No inference from absence to
zero/free reasoning is made. The Qwen response descriptor is observed; exact
weights are not certified. us-west-2 remains user-reported. Local tokenizer counts
and exact response-ID acceptance are not server-tokenizer identity certification.

## Step 3 closure — NOT COMPLETE

Implemented and tested: selected-route paired computation; measured role requests;
local-loader assembly seam; single-POST/quota/accounting integration; durable
study evidence and result reconstruction; process-supervision policy seam; exact
observed-model and sub-$400 budget proposal. No source admission was opened.

Still required before reporting Step 3 complete:
1. Bind the authenticated worker CLI and final native parent/child packet to the
   genuine local/HTTP components and independent outer watchdog. The new held
   entry functions are not an executable launch packet. This remains Codex work.
2. Run and audit separately bounded authentic prompt measurements over the exact
   frozen 350-query inputs with the actual tokenizers. Earlier offline hypothetical
   routes/placeholders do not certify these revised prompt templates. Actual
   generated-answer judge fit must also be checked on each later live request;
   fixed placeholder measurements cannot guarantee that fit prospectively.
3. Finish endpoint-specific pacing and account quota policy. Current limiter stops
   before an unavailable quota; there is no automatic paced full-run scheduler.
   An empty workspace rate-limit list was not proof of unlimited quota.
4. Finalize scientific acceptance of the R01 rubric and null/failure handling and
   the price/timeout assumptions, with peer review of the final source packet.
5. Obtain dated authorization for the exact full-run packet. Neither the budget
   answer nor the instruction to finish preparation authorizes live inference.

No raw source/store/tokenizer measurements, API calls, credential reads, firewall
changes, manuscript/statistics edits or promotion occurred in this checkpoint.
It would be incorrect to call the full task complete based on these tests.

## Peer request

Antigravity: review actual source/diffs and result reconstruction, request policy,
durability/error ordering, ownership and budget assumptions. Please keep the above
Step 3 outstanding work explicit. Do not execute authentic assets or endpoints,
open gates, edit scientific artifacts or infer permission from the test pass.
The user relays messages; this package does not wake another agent.
