# Codex-0185: evidence writer and boundary ownership checkpoint

15 October 2026. Continued user-approved Codex-0182 code-only batch. Implementation self-verification; not independent certification.

## Implemented

- New offline_smoke_evidence.py: exclusive folder/file creation, flushed/fsynced JSON records, preserved partial writes, transcript closure/hash before simulated success record, failure records for failed startup, propagated terminal-write errors. This is no-overwrite behavior, not write protection/WORM storage. Parent containment/reparse validation remains a caller prerequisite.
- New offline_smoke_boundary.py: typed rule identity, fake-backend preconditions for elevation/service/complete enabled profiles/known interpreter processes/collisions, exact rule read-back, ownership checks before deletion, verified removal and ambiguous-creation query/recovery. Foreign or mismatched rules are never automatically deleted. Retry is rejected after a creation attempt. This is a mock-verifiable controller, NOT a native Windows firewall adapter.
- Corrected outer lifecycle: retain boundary and mark cleanup pending when child termination is unconfirmed. Removing it could reconnect a still-running child. Protected post-hashes remain NOT_VERIFIED. Normal confirmed termination still permits ownership-safe teardown.

Prior lifecycle preserved at reports/codex_smoke_lifecycle_checkpoint_20261015_01/. New files do not replace the reviewed offline_preflight driver.

## Verification

Command: venv/Scripts/python.exe -B -m unittest tests.test_offline_smoke_boundary_synthetic tests.test_offline_smoke_evidence_synthetic tests.test_offline_smoke_lifecycle_synthetic tests.test_offline_adapters_synthetic tests.test_master_launch_ledger_synthetic.

154 tests passed in 7.803 seconds; shell exit 0. Only temporary fixtures and fake callbacks/backends were exercised. Collision messages are expected negative-test output in temp directories, not a real ledger export.

SHA-256:
- boundary module: 035482c478f140f96327a8471c9e89145449b45475bd71c02eef6ea12bb1f101
- evidence module: 92ca8c66de617e2df1df80c80c4405cf6a379a89acd2a4fc4ca90346dc0c6274
- lifecycle module: 9b34ef59e9024d0a3f95f7dd9f623d1c9938a8c4742325434cd7433e4fa5bd90

## Remaining, not completed

Native Windows rule/property/environment adapter, process-tree supervisor and memory policy, guarded production config/authorization, authentic isolated child, full protected inventory lifecycle, entry-point integration, durable recovery evidence and final full negative matrix. Exact query selection and final launch ledger remain later gated readiness work. Do not equate mock-controller PASS with operational firewall enforcement.

Antigravity peer review requested on these three modules and the two new named synthetic suites, especially ambiguous creation, retained-boundary failure paths and evidence lifecycle. Do not implement overlapping files in parallel. Return concrete findings through the user-relayed mailbox.

No real rule/store/model/graph initialization, real ledger export, network/API call or manuscript change occurred. Real execution stays blocked. No API key is needed.
