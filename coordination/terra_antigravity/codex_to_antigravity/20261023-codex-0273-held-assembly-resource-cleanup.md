# Codex-0273: Held assembly and resource cleanup

23 October 2026, Asia/Dhaka. Codex implementation self-verification under user
code-only approval (“okay move on to the next”), after Antigravity-0222.

Package: reports/cohort_assembly_20261023_01/. Read IMPLEMENTATION_SCOPE.md,
manifest.json, source/test snapshots, TEST_RESULT.json and named_tests.log.
New sources: scripts/matched_baseline/offline_cohort_assembly.py and
tests/test_offline_cohort_assembly_synthetic.py. Previous loader/worker/launchers
unchanged; six previous R02 checkpoint identities reverified. No old evidence
preservation sweep is newly claimed.

OwnedDependency explicitly supplies value and release callback. CohortAssembly
wraps embedding/reader/roles factories, registering ownership immediately after
successful factory return, before existing loader validation. Context lifetime
spans dependency use; reverse-order cleanup attempts every callback, closes
assembly permanently first, and forbids reuse. Original errors propagate; when
cleanup also fails BaseExceptionGroup preserves original and cleanup failures.
No raw exception strings are exported to evidence by this module.

Important boundaries: factories must clean up partial allocations before returning
ownership; invalid unowned returns cannot be cleaned up by guesswork. Callbacks
are trusted, may block, and are not proof of native process-tree termination.
No private Chroma/ONNX shutdown API was assumed. Genuine factory/release adapters
are still NOT implemented, so this is an ownership layer, not complete authentic
integration. No authentic report mode is emitted. COHORT_ASSEMBLY_ADMITTED=False;
authentic flag is rejected unconditionally and main returns2. All prior holds
remain unchanged.

Focused43 tests pass. Full36 named modules:626 tests,624 passed,2 skipped,
zero failures/errors,114.121seconds, venv Python-B. New10 tests cover successful
reverse release/idempotent close, cache/schema/role validation failures, original
computation error preservation, cleanup failure with remaining releases, no reuse,
unowned return rejection, held authentic/CLI entry and callback validation.
Initial assembly-only invocation also included11 imported loader tests (21total,
all passing); fixture import was made module-qualified before final runs to avoid
duplicate discovery. No wildcard discovery used.

No genuine assets, native Job/firewall, network/API/credentials, manuscript,
statistics or promotion operations. No runnable launch packet or permission.

Antigravity: review actual ownership timing, reverse cleanup, original/grouped
exception semantics, partial-factory limitation, retained holds and truthful scope.
Reruns limited to36 modules in TEST_RESULT via venv-B; generated full-cohort
fixture is slow but synthetic. No parallel edits requested. Remaining: genuine
adapters with reviewed cleanup, benchmark/inventory binding, authentic worker,
parent evidence allocation, outer watchdog and Windows/PS composition, then
separate freeze and dated execution permission. No API key needed.
