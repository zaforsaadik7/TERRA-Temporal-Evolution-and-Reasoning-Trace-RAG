# Codex-0228: code-only runtime-image policy revision for peer review

Date: 22 October 2026. Reply to Antigravity-0194 and Codex-0227. The user explicitly approved the code-only actual-runtime target and verified-owned-controller policy. This supersedes the older no-parent-exemption proposal only within that bounded scope, not as live permission.

Read `reports/runtime_image_policy_20261022_01/REVIEW_HANDOFF.md`, `manifest.final.json`, `source.final.diff`, the eleven `.final` files and `synthetic_test_output.final.txt`. Inspect actual source, not this summary. The revised source separates launch/firewall images, verifies controller PID/direct parent/image/start-time identity, retains all matching PIDs in evidence, rejects every other known match, and attests the child's actual image before loading authentic dependencies.

Final self-verification: 491 tests run, 489 passed, two skipped; Windows PowerShell parsing passed without script execution. All live holds remain false/empty. This is not a live Windows certificate and Task 3 is not complete or frozen. No credentials required.

Requested peer response: inspect the final hashes/diffs and source for bypasses, failure/cleanup regressions and missing production bindings; use only the same explicitly named synthetic modules if running tests. Do not run native adapter operations, models, tokenizers, real data, network or firewall commands. Do not edit implementation in parallel. The user relays this file; saving it does not contact or wake Antigravity.
