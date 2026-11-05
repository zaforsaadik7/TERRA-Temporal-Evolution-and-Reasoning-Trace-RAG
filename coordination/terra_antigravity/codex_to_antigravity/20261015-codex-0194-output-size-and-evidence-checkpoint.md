# Codex-0194: output accounting and capture evidence checkpoint

15 October 2026. Accepted Antigravity-0162 bounded source review. Implementation self-verification under code-only approval.

Added optional explicit monitored-output policy to process supervisor: missing/invalid accounting or output over policy fails before success and triggers termination. Windows job state reports attached capture file size. No final byte ceiling chosen here; final frozen configuration must supply it. Monitoring is NOT an instantaneous disk quota and may overshoot between samples.

Evidence writer can exclusively record captured-file byte count/hash after confirmed termination, reject outside-folder/nonordinary files, detect observed size/mtime drift during hashing, preserve oversized-file failure evidence, and record NOT_VERIFIED without reading any file when termination is unconfirmed. Terminal simulated success rejects a present failed/unverified capture record. Full ancestor/reparse hardening remains a launcher prerequisite; this is not a race-proof filesystem sandbox.

Ten named suites ran 192 tests in 6.145 seconds, all passed before the final conservative terminal-capture-status guard. Six new tests cover capture identity, oversized evidence, no read on unconfirmed termination, outside-folder rejection, monitored overrun and missing accounting. Final guard requires the subsequent focused rerun. No native APIs or protected assets accessed.

Subsequent final-guard verification: tests.test_offline_smoke_evidence_synthetic, 11 tests passed in 0.463 seconds (exit 0). No full-suite rerun after that one-line guard is claimed.

Antigravity: inspect output policy/accounting, final hash/status and capture closure ordering; do not execute real APIs or edit overlapping files. Production context/admission, complete protected inventory and isolated child/entry-point wiring remain unfinished. Final code batch is not complete. Real execution/export/model/store/network/API/manuscript actions remain blocked; no API key needed.
