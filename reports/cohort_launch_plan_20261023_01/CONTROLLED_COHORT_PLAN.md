# Controlled 350-query offline preflight: proposed launcher and resource plan

23 October 2026. Codex. PLAN ONLY: user approved preparation of this plan, not implementation of new launch admission or a real run. All numbers below are proposals for review, not calibrated measurements or execution authority.

## Objective and fixed scientific scope

One prospective offline feasibility attempt over the pinned root terra_350_benchmark.json:350 unique queries, categories A_Factual100/B_Evolutionary100/C_OutOfContext75/D_Adversarial75. Use the same20,000 stored retrieval documents for dense/BM25 and graph-ID agreement, existing pinned384-dimensional MiniLM, native L2 distances, top_k100 and two graph seeds. Evaluate both hypothetical0-hop/EASY and depth2/HARD envelopes for every query:700 route records. Categories, gold answers and target metadata never enter retrieval or routing. No live route classification, generation, judging, answer correctness, causal comparison or paper statistic is produced.

Keep the B001-tested explicit profile environment and external-vector interface. Use the new driver's deterministic<=32-query batches (350 =>11 batches), identical query order and exact ranking cardinality/ID/corpus checks. Role prompt/serializer/tokenizer policy, graph depth/caps/ordering and placeholder-answer caveats remain reviewed dependencies. Do not regenerate or alter corpus/model/statistics.

## Evidence versus unmeasured quantities

B001 report shows local retrieval and envelope computation succeeded for one query; child output46 bytes and report4,017 bytes. Its saved terminal/capture records do not persist calibrated per-stage duration or peak Job memory. The backend can observe peak_memory_bytes, but presence of that code is not a saved measurement. No350x timing extrapolation or hardware-capacity promise is justified. Existing graph default cap40 nodes/35,000 structural characters remains; no new graph traversal expansion is proposed.

## Provisional resource policy for peer/user decision

- Child Job-tree deadline:7,200 seconds (2 hours), replacing—not inheriting—the B001300-second limit. This is a conservative operational ceiling, NOT an empirical runtime prediction. No extension or automatic retry if reached.
- Job-tree committed-memory ceiling:4,294,967,296 bytes (4 GiB), unchanged from B001. Applies to supervised child/descendants, not parent, total host memory, free RAM or a guarantee of fitting. Keep this cap until evidence supports a separately approved change.
- Child stdout/stderr capture:16 MiB, unchanged. Progress output is bounded counters/stages only; no complete prompts, model text, environment values or raw arbitrary exception messages.
- Cohort report:16 MiB encoded maximum, with incremental per-query records<=32 KiB and bounded metadata.350*32 KiB=11,468,800 bytes, leaving space for run metadata under16 MiB. Reject excess before report success; do not truncate substantive results into a PASS.
- Child request:1 MiB; serialized independent context:2 MiB; frozen packet:8 MiB. Prefer pinned benchmark identity plus ordered query-ID/text digests rather than duplicating gold-bearing records. Actual wire sizes verified before admission; ceilings are not proof of current fit.
- Outer supervised wall-clock policy:10,800 seconds proposed total scheduling budget, including a300-second finalization reserve. Do not start new computation inside that reserve. This needs explicit watchdog/source review: the current single-query wrapper does NOT enforce it. Deadline handling must attempt confirmed child-tree termination and ownership-checked cleanup, not blindly kill the parent or remove a rule while descendants may live. Blocking OS/storage operations prevent an unconditional hard-time guarantee; report any overrun/uncertainty honestly.
- Job termination confirmation wait:30 seconds per reviewed bounded poll policy, then retain owned firewall rule and emit manual recovery if termination is unconfirmed. Boundary adapter calls keep the reviewed30-second/1-MiB limits. No blind/wildcard firewall deletion.
- Evidence writes:proposed128 MiB per-run budget for new logs/reports/receipts/manifests, excluding immutable inputs and store copies; stream-check/report limits must enforce it. Current B001 capture limits alone do not enforce this aggregate budget.
- Disk allowance for store protection:two copies of the saved432,097,888-byte source inventory =>864,195,776 bytes before disposable operational growth. Require at least2 GiB free at the designated output volume before copy. This is a conservative floor, not a prediction/guarantee of filesystem capacity. Actual current source size, free space, per-disposable growth cap (proposed512 MiB beyond copied baseline) and stop behavior must be checked/frozen before execution. Preserve partial outputs; no automatic deletion to recover space.

All limits must be carried in the cohort-specific approved config and checked against independent reviewed context. No silent increases, unbounded buffers, automatic retries, process killing outside the owned tree, or budget borrowing from other runs. A limit failure makes the run incomplete/FAIL; partial results cannot stand in for the complete350-query cohort.

## Composition: new scope, reuse reviewed mechanisms

1. Define a distinct COHORT_OFFLINE_FEASIBILITY scope with new config/request/approval/report contracts and null-by-default independent anchors. Do not relax ONE_QUERY_OFFLINE_SMOKE validators to accept arbitrary counts or reuse any consumed lock/path/approval. Cohort identity includes exact350 ordered IDs/text hashes, distribution, input digests, two routes,20k documents, algorithm/batch settings and resource policy.
2. Compose a dedicated cohort worker using the existing guarded MiniLM/tokenizer loading, receipt-bound disposable reader, graph loader and role serialization. Reuse verified component implementations where possible; do not duplicate their math. The legacy driver's unconditional production block stays in place: do not delete it or pretend its SIMULATED_SUCCESS is authentic success. Extract/use reviewed computation helpers within the separately admitted worker, or propose another explicit source-reviewed design before implementation.
3. Load protected model/store/graph assets once per owned child. Validate full corpus/schema/dense-sparse-graph membership before queries. For every query:external embedding -> native dense candidates -> hybrid and graph evidence -> two route envelopes. Stop on first malformed batch, missing/duplicate query, outside-corpus candidate, source drift, resource/network/error/failed envelope. Save valid partial records as incomplete, never impute or retry. Completion requires all350 IDs and700 unique (ID,route) rows.
4. Parent/controller retains pre/post complete identities and source quiescence; receipt-verified source->snapshot->disposable parity; mandatory failure-path finalization; suspended child creation and Job assignment before resume; explicit environment including reviewed USERPROFILE; in-process network blocker and scoped outbound firewall rule; verified-controller-only matching-process policy. Unknown/unreadable process uncertainty remains disclosed. No source Chroma connection or source mutation.
5. Fresh PowerShell5.1 user wrapper and independently pinned launch record/packet/anchor. Reuse proven function coverage/identity mechanisms without trust-root cycles. Requires user-started Administrator session, exact hashes, no policy bypass/self-elevation/retries. Firewall targets actual base Python, not just venv redirector. No credentials or API endpoint. Parent/child diagnostics remain bounded, stage-tagged and message/locals/source-text redacted.
6. Proposed new artifact root reports/authentic_cohort_candidate_<frozen-id>/, unique rule/owner, exclusive evidence and persistent inner/outer locks. This plan creates none of them. Allocate actual names/paths only in the reviewed held candidate; never reuse B001 directories.

## Report and supervision telemetry

Persist elapsed monotonic duration for setup, corpus extraction/BM25, graph load, each dense batch, each route-envelope phase, and cleanup; cumulative/peak child Job memory, output/disk growth, termination result and limit-hit signals. Collect from actual supervision state, not inferred file mtimes. Report unavailable measurements explicitly, not as zero. Bound telemetry volume and write with integrity/finalization semantics on errors too.

Manifest/batch ledger binds every row to benchmark SHA and ordered query digests. Schema must distinguish AUTHENTIC_OFFLINE_FEASIBILITY from synthetic fixtures, declare local pinned ONNX/tokenizers/disposable retrieval, hypothetical routes, synthetic judge placeholder, provisional provider ceilings, provider_certified=false and live_api_calls=0. Record700 per-query route token/count/fit metrics and retained/dropped evidence counts, full graph missingness, all retrieval ID membership checks, actual failure coverage, and incomplete status if fewer queries finish. Category summaries are descriptive bookkeeping, not answer-quality evaluation. Do not record gold answers or credential/private profile contents.

## Implementation acceptance tests (all synthetic first)

- Distinct scope/cardinality/order/pin/authority validation; reject B001 packets, stale approvals, missing/extra queries, duplicate IDs/route rows and payload leakage.
- Cohort worker on generated350 records and temporary2-document fixtures, then adversarial fixtures:bad schema/corpus graph, partial batches, NaN/wrong-dimensional vectors, token overflow, storage/capture/report limits, child crashes and timeout.
- Exact32-batch maximum and350/700 completion accounting; no category/gold injection, implicit Chroma embedder or live provider dispatch.
- Injected clock/Job/filesystem/capture adapters for child deadline, aggregate evidence/disk-growth budgets, outer finalization reserve, confirmed termination/removal, unconfirmed termination/owned-rule retention, and cleanup exceptions. Tests must prove no unrelated process/rule affected.
- Verify actual Windows API signatures/ownership and parser/extracted PS functions without real native execution during code-only phase. Run only explicit named test modules with project venv Python-B; no discovery.
- Preserve byte-snapshots/diffs and all184 existing evidence files/eight corresponding inner/outer locks. All genuine execution holds remain closed during code/test review.

## Gates and user actions

A. Peer review this plan and identify any resource/scope/cleanup flaw. Proposed limits remain unapproved; do not characterize them as calibrated.
B. User approves bounded code-only cohort contracts/composition and synthetic tests under the reviewed plan. Implementation and source/negative-fixture peer review; no native/model/store operation follows from a test PASS.
C. Fresh non-executable candidate, full wire-size/identity/membership and runtime compatibility reviews, two-pass filesystem check under explicit scope, then separately dated permission for final freeze and one full-cohort offline attempt with exact limits/rule/recovery. Any new controlled calibration run would itself require separate user approval and is NOT authorized by this plan; none is assumed necessary or silently added.
D. User Administrator launch once, then saved-output/cleanup/integrity audit and peer review. Only complete350/700 validated records close the full offline preflight. Failure needs preserved evidence and a new decision, not retries.

Later live-provider endpoint/context testing, financial cap, smoke/full matched comparison, analysis and manuscript integration are separate phases. API credentials are not needed for the offline plan or offline attempt. No manuscript/statistics update or canonical promotion follows from offline feasibility alone.
