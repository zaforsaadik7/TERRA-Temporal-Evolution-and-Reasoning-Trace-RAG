# Native integration and qualification

Codex implementation self-verification, 24 October 2026.

The paid source entry is `scripts/matched_baseline/paired_production_native.py`.
It returns2 BEFORE control/credential/data access while LIVE_ADMITTED=False.
The external `paired_production_anchor.py` has no plan path/SHA admitted.
No switch/environment variable can open the paid source gate.

The complete paid bootstrap now has an outer owner, a controller and a worker:
the outer Job independently contains the controller and descendants; the
controller verifies complete inputs, creates an isolated copy chain, supplies
the digest-bound receipt handoff and owns the worker Job. Both levels use
suspended creation, Job assignment BEFORE resume, memory/output/deadline
observations and complete-tree exit checks. Source/cache/snapshot and complete
input inventories are checked after the worker stops. Role locks and an exclusive
attempt directory prevent silent controller/worker restart or reuse.

The worker independently decodes the plan-bound context and actual approval,
validates receipt/source and exact benchmark identities, constructs the genuine
cached MiniLM/Chroma/tokenizer factories, and joins them to the measured HTTP,
quota, accounting, persistence and reconstruction pipeline. Credential loading is
deferred until a permitted request has a durable reservation; the secret is never
part of control manifests, argv, inherited environment or persisted HTTP headers.
This paid branch is SOURCE ONLY and was not executed during preparation.

The launch approval binds context/input identity and the complete native contract.
The approval's own pin is excluded from its internal launch digest to avoid a
cycle, while the FINAL external plan SHA still includes that approval pin.
The anchor is excluded from the packet it pins and must be independently pinned
with the entry by the final launcher. Proposed admitted source bytes are staged
for review only; the live source remains held. A real human approval is absent
from all UNAPPROVED artifacts. These records are not machine-generated permission.

## Real qualification found an actual cleanup race

The first harmless qualification ran a single sleeping Python child with a
one-second deadline and128MiB limit, without models, credentials or provider calls.
Legacy SmokeProcessSupervisor reported termination_confirmed=False. Its record
and original fixture are preserved; this was NOT counted as a successful test.

Inspection found that legacy cleanup could skip its exit wait after a kill API
error. The repaired production adapter is `paired_native_job.py`. Job termination
is asynchronous: the immediate root TerminateProcess can report failure while
the process is exiting. The new backend observes BOTH the root handle and the
Job active count, and the owner still waits even after a reported kill error.
No failed kill return is treated as proof of exit. Unknown exit retains recovery
status; timeout remains a failed attempt even when cleanup succeeds.

The second real qualification reproduced `Windows API failed: TerminateProcess`:
the root was not yet signaled, Job active count was0, and the bounded exit wait
then observed the complete tree empty. The record confirms exit code1,
termination_confirmed=True, handles_closed=True and no cleanup errors. See
NATIVE_TIMEOUT_QUALIFICATION_RESULT.json and native_timeout_qualified_01/.
Two deterministic synthetic tests cover this race and the still-live failure
case. The failed legacy fixture is preserved in NATIVE_TIMEOUT_FIXTURE_RESULT.json.

The local350-query prompt measurement uses the existing healthy-path preparation
controller under nested real Jobs, without provider transport. The final review
report links its actual terminals and observed peak memory/elapsed limits.
Its input/code generation is preserved; the new paid adapter's repair was made
in a new module, not by modifying code in that running measurement's pin set.

These observations do not prove OS primitives can never block or formally verify
every native path. Storage is polled, input checks are observations rather than
filesystem locks, and private injected seams are trusted. No firewall rule was
created, removed or claimed as network isolation during this preparation.
Local measurement uses the Python-level InProcessNetworkBlocker; it is not an
independent certificate of every possible native network effect.
