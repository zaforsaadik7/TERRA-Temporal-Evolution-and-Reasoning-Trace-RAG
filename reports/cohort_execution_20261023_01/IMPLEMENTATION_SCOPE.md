# Bound benchmark and held execution wiring — 23 October 2026

Implementation self-verification under user code-only approval. Added execution
module and13 tests; refactored shared worker only. Byte-preserved pre-edit worker
must equal prior immutable worker.final, and worker.diff records the actual change.
Prior worker manifest's live-source entry is superseded by this authorized edit;
its old snapshots and all other historical files remain preserved.

BenchmarkBinding validates caller-supplied bytes once (max2MiB), SHA256 before JSON
parsing, duplicate object keys/nonfinite JSON rejection,350 ordered ID/text hashes
and categories against CohortSpec. Returned immutable pairs contain no answer,
gold or category fields. Fixture digests carry synthetic_fixture=True and cannot
pass authentic canonical-digest binding. This function does NOT read a file or
prove its path/transport provenance: canonical path in binding is declared from
spec, not independently observed. Parent input-file identity/receipt remains needed.

Shared _CohortComputation selects mode before any query/row creation. Existing
public PreparedCohortWorker always selects SIMULATED and still rejects authentic
flag. New AuthenticCohortComputation construction is source-held, selecting
AUTHENTIC_OFFLINE_FEASIBILITY only behind that hold. Authentic row source creates
required local-execution disclosures at creation rather than rewriting previously
generated synthetic reports. Mode/strings alone do not prove actual provenance.
Retrieval, batching, graph traversal, formatting and token budgets are unchanged.

Synthetic composition binds bytes before loader callbacks, then holds injected
guard across adapter construction, assembly/load, computation and resource release.
It uses shared budgeted telemetry/query/report writers. Writer closes on failure,
including input-binding failure. Original errors and writer-close failures are
grouped, not overwritten. On computation/guard failure a bounded type-only
FAILED_INCOMPLETE marker is attempted when remaining budget/storage permits.
A computational report can exist before guard/cleanup failure: successful report
content is not terminal process/integrity PASS. Parent must reject failed exit.

Authentic entry is source-held before imports or callbacks, accepts no caller
runtime/report-mode/network-guard override, and in held source uses canonical
digest/genuine runtime plus InProcessNetworkBlocker. Existing ordering/assembly
synthetic-default seams are reused internally for their data/ownership contracts,
NOT as authentic authority. All earlier holds plus COHORT_WIRING_ADMITTED=False
remain closed. Public entry still cannot execute; no new launch record or command.

Focused64 tests pass. Thirteen new tests cover generated-byte binding, wrong
digest/order/category/text/population, duplicate JSON keys, canonical-mode fixture
rejection, guarded orchestration, failed bind/load/worker/guard exits and grouped
writer cleanup failures; real entry blocks before imports. Orchestration success
uses a mock worker; existing generated20k/350 computation regression still tests
actual retrieval/packing with mock tokenizers. Authentic computation/report branch
is source-reviewed only, not genuinely executed or runtime-certified here.

No real benchmark/store/cache/graph/tokenizer/model opened, no Job/firewall,
network/API/credentials, manuscript/statistics or promotion operation. Generated
test temporary files only. No historical preservation sweep newly claimed.

Remaining: full source/input/inventory admission and bounded canonical file reader,
authentic assembly/worker admission review, parent budget/evidence allocation,
pre-child outer watchdog, native Windows Job/PS launcher integration, final freeze
and separate dated permission. Source flags and pure receipts are not authority.
No API key needed for this offline task.
