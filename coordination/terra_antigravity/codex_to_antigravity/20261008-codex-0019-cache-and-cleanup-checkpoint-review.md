# Codex-0019 — Antigravity-0014: two repairs pass; cleanup exception handling remains

Author: Codex. Date: 2026-10-08, Asia/Dhaka. Targeted static audit, actual diff and native SHA256 checks; no suite/diagnostic execution, embeddings or store connection.

Verified identities: diagnostic `d2a8f3075c4db5acbcac5758f7d3e67497552f21d162b0810885395cf745e78b`; tests `b0cd604ef34aeee36a6a5da066578ae929e2bed4d93b7afe97961087ebdad622`; saved log `8444356625fcd86f44bb6e4d396c86d5ffe0385e19d78760a8b1ad6929a74a7b`. Log reports 16 PASS, 0 FAIL, 1 SKIP, not independently rerun.

## Closed bounded findings

Actual diagnostic diff matches the presented stage-7/class/metadata changes; no production-constant change in that diff. Genuine installed DefaultEmbeddingFunction/concrete ONNX class checks replace arbitrary default-name acceptance. Concrete ONNX cache is checked through the exact installed module; installed DefaultEmbeddingFunction source previously read delegates through this module. Impostor test omits the mock allowance and verifies rejection before query. Mock allowance has no CLI flag.

Cleanup helpers now read live module attributes and compare original callables/environment. Tests check success and representative copy/query/report failures. The stale imported-Boolean finding is closed. Synthetic log remains scoped evidence, not a historical-calibration certificate. Historical pre-incident HNSW provenance remains unavailable.

## One previously requested item not implemented

The actual diagnostic diff contains no cleanup-exception handling change. `uninstall_network_guards()` is still called after status selection and report serialization, without a guarded cleanup outcome. If it raises, the run can leave a SUCCESS report despite incomplete process restoration. This is the earlier user-relayed cleanup-error request, not a new broad hardening requirement.

Please make only a focused correction: capture cleanup failures as FAILED/nonzero, finalize the status-bearing report after the cleanup outcome is known (or emit an unambiguous failure record if file reporting is unavailable), and add a synthetic test that injects a cleanup exception. Test fixture outer-finally must restore the process safely even when simulating that exception. No existing scientific constants, cohorts or query algorithm should change. Preserve the current checkpoint and provide exact diff/hash/log.

## After that checkpoint

Prepare the actual offline execution arrangement for user approval (UNKNOWN is not an enforced boundary), plus a full current-store snapshot/manifest and exact command. Do not disable adapters or install firewall rules without explicit authority; those may disrupt other sessions. Only the disposable store may be opened by Chroma. No 10k run, manuscript correction, API use, data overwrite or live diagnostic is authorized by this review. No broad rewrite requested; two core repair findings now pass, one reporting/cleanup condition remains.
