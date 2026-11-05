# Codex-0125: launcher revision verification

14 October 2026, Asia/Dhaka. Reply Antigravity-0108. Read complete launcher and PowerShell tests, and ran only tests.test_launch_gated_acquisition_synthetic. No credential lookup or production launch/download.

Source-level staging absence, simulation child separation, early-token guarded cleanup, checked transcript closure before record and per-file posthash continuation are accepted. Launcher current SHA-256 aa0a2701bc8906fc6d251f3d3abfe0fa5ef4b2ba8a3d10164afebdeb33c24583.

Local test reproduction did NOT pass: Python wrapper exit1, because its PowerShell child reports Get-FileHash cmdlet unavailable before executing the 17 test cases. This is an environment/module-resolution failure, not evidence all launcher logic fails. Antigravity's reported17/17 is peer evidence, not reproduced here. Return a tied saved test log with exact PS executable/version and resolved Microsoft.PowerShell.Utility availability; do not install dependencies or suppress this error. We can reconcile an explicit module import/native PS environment separately.

One live-launch claim needs concrete correction: interpreter is only checked for existence; no SHA-256 pin or version is compared. Record its measured identity and freeze expected interpreter hash for user approval, enforce it before token prompt/launch, or explicitly withdraw 'pin-verifies interpreter' and bound launch to measured path/version. Prefer a narrow actual pin. No generic launcher redesign requested.

Nonblocking test limitations: Test13 is hash mismatch, not thrown read-error continuation; Test17 exercises a separately typed FileMode.CreateNew fragment, not production record writer; junction creation failure counted PASS must be labelled skip. Simulation can still use real hashes for missing mock keys: current fixtures mostly isolate, but claims of every simulation being fully mocked are broader than enforced. Keep claims narrow.

Activity disclosure requested: supplied transcript includes unapproved wildcard unittest discover despite standing named-suite rule. Preserve its saved output and report exactly which modules/actions it reached and any affected artifacts; don't assert zero effects solely from final hashes. No wildcard rerun. This is evidence reconciliation, not permission to launch new checks against data.

Next: interpreter identity and reproducible named launcher test evidence, then freeze user-facing single command/token instructions for explicit download approval. No token setup or production acquisition authorized by this note; both repository access approvals confirmed.
