# Codex-0278: Evidence allocation and outer watchdog core

23 October 2026, Asia/Dhaka. Codex implementation self-verification after
Antigravity-0227 and user's “okay do that,” existing code-only/synthetic scope.

Package: reports/cohort_lifecycle_20261023_01/. Read IMPLEMENTATION_SCOPE.md,
manifest.json, before/final snapshots, execution.diff, TEST_RESULT.json and log.
New lifecycle module/14 tests. Only existing source change: _run_bound telemetry
artifact ceiling now min(global evidence cap, writer allocation). Before copy
verified equal to prior execution.final; old live source entry intentionally
superseded, old snapshots preserved. All50 other prior manifest entries verified
unchanged. Incoming STATUS saved; no historical184-file evidence sweep claimed.

EvidenceAllocation binds independent exact root/shares, nonboolean integer values,
parent >= capture ceiling, child >= report ceiling, sum exactly reviewed total.
Tests use32MiB parent+96MiB child=128MiB as a SYNTHETIC example, not live allocation
approval/calibration. FixtureEvidenceLease exclusively creates fresh temporary root
and disjoint parent/child writer directories, consumes owner slots before opening,
and each writer has its own fixed ByteBudget share. No shared mutable cross-process
counter, OS quota or arbitrary-code namespace sandbox claimed. Per-writer artifact
limits remain32; no global per-attempt artifact-count proof inferred from that.
Genuine owner transport/root receipts and external-growth observer still pending.

OuterLifecycleWatchdog is active INJECTED POLLING CORE for independently owned
setup/controller actor, starting before setup/copy/hash. It checks monotonic time
before/after observations, exact phase/stop/exit state and no phase regression.
Work phases stop at outer minus reserve; already observed CLEANUP may use remaining
reserve up to full limit. Late blocking state callback cannot produce a successful
return. Graceful shutdown request followed by bounded actor-stop confirmation;
unknown stop retains recovery record. No blind kill or firewall removal anywhere,
and actor stop is not treated as child-tree termination. Observer close must be
safe observational release, not closing kill-on-close native Job handle.

Wait allowance=min(termination wait, reliably observed remaining outer time), zero
if timing unavailable/exhausted. elapsed_outer_seconds is the last valid observed
elapsed value, not a measurement of every finalization callback's complete runtime.
Success is ACTOR_SUCCESS_REQUIRES_CHILD_AND_INTEGRITY_AUDIT, never cohort success.
Cannot interrupt blocking state/pause/shutdown/wait/close callbacks: genuine bounded
native observer and independent dispatcher are NOT implemented by mock names.
This is not a running background thread/process or hard wall-clock enforcement.

Focused105 tests pass. Full41 named modules:688 tests,686 passed,2 skipped,
zero failures/errors,111.927s, venv-B. Fourteen new tests use temporary evidence
directories, fake actors/time, allocation rejection/partial preservation, child
telemetry cap integration, pre-child timeout and late observation, cleanup reserve,
unknown stop/recovery/no rule deletion, bad clock, phase/exit failures, graceful
shutdown failure and held real entries. No native process/Job/model/store execution.

COHORT_LIFECYCLE_ADMITTED=False; genuine lease/watchdog rejected; CLI returns2.
Earlier holds closed. No actual cohort, assets, Job/firewall, network/API/credentials,
manuscript/statistics or promotion operation. No API key needed.

Peer review requested: actual split invariants/root exclusivity, telemetry diff,
pre-child timing/reserve logic, last-observed timing caveat, bounded-wait/unknown
stop recovery and absence of rule deletion, source-held native limits. Reruns only
41 modules in TEST_RESULT via venv-B; no discovery, genuine/native work or parallel
edits. Do not rerun sealing script into immutable package.

Remaining: bind allocation into canonical reviewed parent/launch envelope, genuine
independent setup/controller observer plus pre-work dispatch, native child Job,
combined capture/state/external-growth observers and cleanup integration, PS
launcher, complete identity/authority freeze and dated actual-run permission.
