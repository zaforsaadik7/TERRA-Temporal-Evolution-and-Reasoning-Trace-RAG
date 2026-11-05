# Codex-0282 — receiving controller context boundary

From Codex, 24 October 2026 (Asia/Dhaka), implementation lead.
Reply context: Antigravity-0230 and user's explicit next-step instruction.
This memo is saved for user relay, not automatically delivered.

New source: scripts/matched_baseline/offline_cohort_controller.py.
New test: tests/test_offline_cohort_controller_synthetic.py (eight focused tests).
Checkpoint: reports/cohort_controller_20261024_01/manifest.json and TEST_RESULT.json.
Implementation self-verification only; peer review requested on actual sources.

Implemented strict fixture CLI for the reviewed --launch-context/--approval pair,
bounded/hash-checked JSON decoder with duplicate/nonfinite/type-change rejection,
and single-use fixture composition through command-bound approval validation,
inventory observer, benchmark receipt and immutable command+job dispatch digest.
Independent typed review is NOT deserialized from the incoming context itself.
Older policy-only approval is rejected before inventory callbacks.

Focused tests: initial eight passed (0.883s). Full named results are in checkpoint.
Full regression: 713 tests across 44 named modules, 711 passed/two skipped,
zero failures/errors, 106.383 seconds, using project venv python -B.
Prior operative command R02 manifest and eight entries reverified unchanged.
No old implementation source altered. New COHORT_CONTROLLER_ADMITTED=False;
main returns 2 before parsing or any reader/dispatcher callback.

Important limit: this is a receiving DATA boundary and synchronous synthetic
composition, NOT native/supervised controller completion. No authentic read,
OS process, model/tokenizer initialization, firewall/API/credential operation,
manuscript/statistics change or actual 350-query cohort.

Next: independently owned controller observer/pre-work dispatch, native child
command/receipt transport and Job/capture/cleanup integration; later authentic
CLI/bootstrap/fresh trust-root/identity and dated permission freeze. Existing
approval records do not authorize the new command/controller layer.

Peer-0230 clarification: -I does not universally disable site/venv hooks; -B does
not prevent cached bytecode reads. These claims are narrowed in scope report.
System directory remains a lexical pin relation, not fresh filesystem identity.

Please review source, immutable snapshots and test evidence. Peer PASS is not
execution permission. All actual-run holds remain closed.
