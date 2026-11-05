# Evidence allocation and outer watchdog core — 23 October 2026

Implementation self-verification under existing user code-only authority.
New lifecycle module and14 tests. Existing execution module changes only telemetry
artifact maximum to min(global evidence cap, writer allocation), allowing a child
share smaller than128MiB without widening global evidence policy. Byte-preserved
before copy equals preceding execution.final; exact diff supplied. Old execution
manifest live-source entry is superseded intentionally; historical snapshots stay.

EvidenceAllocation requires exact independently reviewed root/shares, positive
integer capacities, parent >= capture ceiling, child >= report ceiling, sum exactly
the existing total. Tests use32MiB parent+96MiB child=128MiB, a synthetic example
not live budget authorization/calibration. FixtureEvidenceLease creates a fresh
exclusive temporary root and distinct parent/child writer directories; each owner
slot is consumed before open, no retry/reuse or overwrites. Writers use their own
fixed ByteBudget share; there is no mutable cross-process aggregate counter.
No OS quota or access control against arbitrary code/unmodeled writers is claimed.
Native child transport/root ownership receipts and external-growth observers remain
unimplemented; public lease is fixture-only, real flag rejected before filesystem.

OuterLifecycleWatchdog polls a trusted injected observer for an independently owned
actor beginning BEFORE setup/copy/hash. Allowed phases SETUP/COPY/HASH/CHILD/CLEANUP
cannot regress; malformed/late/nonzero/incomplete exits fail. Work phases stop at
outer limit minus finalization reserve; already-observed cleanup can use the reserve
up to full outer limit. Timing checked before/after state observations, so a late
blocking callback cannot produce success. Unknown clock never generates a fake
elapsed duration or positive inferred wait budget. Wait allowance is min(termination
wait, reliably observed outer time remaining), zero when unavailable/exhausted.

On failure, requests graceful stop of the known actor; attempts bounded stop
confirmation; if unconfirmed retains a recovery record. Never removes firewall
rules, blindly kills processes, or equates actor stop with child-tree termination.
close_observer must release only safe observational resources, not a kill-on-close
Job handle. Those properties are requirements for the FUTURE native adapter,
not something mocked callback names can prove. Success is explicitly
ACTOR_SUCCESS_REQUIRES_CHILD_AND_INTEGRITY_AUDIT, not cohort success.

This is an active injected polling CORE, not a running background thread/process
or hard wall-clock enforcement. It cannot interrupt a blocking observer, pause,
shutdown or wait callback; those must be bounded in an independently reviewed
native supervisor. Already-running child limits remain in existing CohortSupervisor;
the two loops have not yet been connected to Windows Job/controller code.

COHORT_LIFECYCLE_ADMITTED=False; genuine lease/watchdog construction rejects and
main returns2. No previous holds lifted, no commands/launch admission created.
Focused105 tests pass;14 new tests cover split validation, exclusive directories,
partial byte preservation, worker telemetry under child share, setup-to-cleanup
fake actor, pre-child deadline, late blocking observation, cleanup reserve,
unknown stop/recovery/no firewall deletion, bad clock, phase regression, failed
shutdown and held native entry. No real Job/firewall/process or model/store.

Remaining: bind allocation and launch policy to frozen parent admission, native
independent setup/controller observer plus watchdog dispatch before setup work,
actual child Job/Windows state/capture and cleanup integration, PS launcher,
complete identity/authority freeze and separate dated real-run permission.
No API/network/credentials/manuscript/statistics/promotion or genuine asset access.
Temporary generated evidence writes only; no historical preservation sweep claimed.
Full41 named synthetic suites/log/result and source snapshots are sealed here.
