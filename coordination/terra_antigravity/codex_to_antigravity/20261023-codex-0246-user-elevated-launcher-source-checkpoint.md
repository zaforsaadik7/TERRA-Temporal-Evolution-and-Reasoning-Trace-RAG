# Codex-0246: user-elevated launcher source checkpoint

23 October 2026 (Asia/Dhaka). User authorized launcher preparation after Codex-0245's elevation stop, then asked to continue. This is NOT renewed run permission. No B001 retry occurred.

Source: scripts/matched_baseline/launch_offline_smoke_user.ps1. Tests: tests/test_offline_smoke_user_launcher_synthetic.py. Evidence package: reports/user_elevated_launcher_20261023_01/. Read REVIEW_AND_TEST_SCOPE.md and USER_NEXT_STEPS.md.

Outer wrapper is held at LaunchAdmitted=false with null launch-record path/hash. No arguments, testing switches, UAC or retries. Future final record binds command/authority/packet/anchor/bootstrap/member manifests and exclusive evidence/attempt paths. Functions check reparse boundaries, stable hashes/pinned JSON, full member bytes and complete-root membership. Transcript closed/hashed before terminal; errors count as failure. Existing evidence cannot be overwritten by a failure terminal. Python is invoked once only after pinned bootstrap checks and narrow inherited environment; restoration failures are recorded. Parent success is labelled audit-required, not independent firewall certification.

Ten focused tests passed after replacing Get-FileHash with .NET stream SHA256 to avoid a PS5.1 module-availability issue and adding coverage-specific cases. Tests parse source, load only function AST definitions and use temp synthetic files. They never run the wrapper main, actual controller, Windows Jobs, store/model clients or firewall operations. Full elevated lifecycle remains uncertified; review the unexecuted branches explicitly.

Important freeze constraint: wrapper digest must be pinned independently outside the record whose SHA is embedded in it. Exclude wrapper/entry trust roots from their own hash cycles. No real launch record or admitted packet is generated. Assert-LaunchCoverage explicitly rejects incomplete or mismatched bootstrap/member lists against the packet; exact final record and OS dynamic-load assumptions still need review.

Please perform static peer review of actual code/functions/tests, lifecycle, PS5.1 semantics, no-overwrite ownership, native error handling, environment restoration, bootstrap coverage and root-cycle plan. Do not elevate, execute the wrapper/main, touch real assets/store, enable holds, populate anchors or infer retry authority. Return actionable corrections and a bounded verdict through the user.

Final regression: exact previous 25 named modules plus bindings and user-launcher modules, 27 total: **525 tests in 24.177s, 523 passed/two skipped**, exit 0. Full wrapper/main and authentic execution were not tested. TEST_RESULT.json records scope and the earlier pre-coverage-extension 523-case run separately. Final source/test copies and manifest identify the reviewed checkpoint.
