# Codex-0281 — prospective controller command contract

From Codex, 24 October 2026. User authorized next code-only step after peer-0229.
Implementation self-verification; user-relayed peer review requested, not sent live.

New source: scripts/matched_baseline/offline_cohort_command.py and named synthetic
suite tests.test_offline_cohort_command_synthetic. Prior launch-policy sources
unchanged (all nine previous package entries reverified).

Pure immutable contract binds policy SHA, controller executable/entry argv,
fixed -I -B, launch_context.json/approval.json arguments, cwd, and explicit
PATH/SYSTEMROOT/WINDIR/USERPROFILE. No inherited environment, shell invocation,
credential access, filesystem observations or process dispatch.

Separate command digest does not upgrade old policy approvals. Authentic CLI,
isolated-Python bootstrap/import strategy, independent native observer, child
argv/receipt transport and launcher-to-base-process identity are NOT implemented.
All genuine gates closed. No real data/model/tokenizer/native/firewall/API work.

Evidence: reports/cohort_command_20261024_01/; operative corrected identities
and regression are under regression_r02/. Initial full run passed 704 tests
(two skipped). Self-review subsequently found System32 must be anchored to
kernel32.dll's directory, not nested PowerShell v1.0 directory. Corrected code
and added fixture; earlier snapshots preserved, earlier two live-source entries
superseded. See regression_r02/CORRECTION.md. Initial focused quoting-test
fixture failure also disclosed in IMPLEMENTATION_SCOPE.md.

Operative R02: 705 tests across 43 named modules, 703 passed/two skipped,
zero failures/errors, 107.352 seconds. Command used project venv python -B.

Please inspect actual source/snapshots, R02 manifest and TEST_RESULT.json. This
is only a prospective command data contract, not the completed native integration
or an executable packet. Next work: receiving held CLI/context decoder and
independently supervised controller dispatch. No actual-run permission requested.
