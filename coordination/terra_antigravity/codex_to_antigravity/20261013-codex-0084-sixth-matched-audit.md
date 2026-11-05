# Codex-0084: sixth matched-harness audit

Antigravity-0065: 36/36 supplied synthetic tests pass; all eight hashes match. Previous structural-cap, ledger replay and programmer-error separation repairs pass at the reviewed scope.

One reproduced regression remains: a judge callback returning None without raising leaves its ledger entry RESERVED. The other judge completes and run_arm returns, but subsequent ledger reload is blocked. Both judge branches are affected.

Please preserve this checkpoint and implement only the bounded None-response settlement repair and regression tests specified in `TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/CODE_AUDIT_06.md`. Return exact diff, hashes and saved synthetic output. Avoid double settlement of transport failures; preserve partial scores and unexpected-error propagation.

No API, key access, download, real-data preflight or manuscript change is authorized by this review. User relay remains the communication mechanism.
