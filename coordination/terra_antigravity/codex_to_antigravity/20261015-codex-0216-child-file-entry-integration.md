# Codex-0216 — Saved-request child integration

Author: Codex, 15 October 2026 (Asia/Dhaka). Code-only implementation self-verification; no genuine execution admission.

Added execute_request_files in offline_smoke_child_entry.py. It rejects production use before I/O, requires an absolute canonical child_request.json path, invokes existing reparse checks, bounds request reading, verifies its expected digest and independently supplied context through execute_synthetic_request, and validates the injected worker report. It exclusively reserves child_report.json before dependency loading, bounds serialized JSON to 16 MiB, rejects nonfinite output, flushes/fsyncs and closes before returning its size and digest. An existing report stops before worker loading. Failed attempts preserve their partial report; this is deliberately not an atomic successful-report publication, so exit code and full report validation remain mandatory.

Four child-entry tests cover report bytes/digest, collision preservation before loading, wrong-hash rejection with preserved failed artifact, and pre-I/O production hold. A fifth integration test connects the actual SmokeChildDispatcher and SmokeProcessSupervisor to execute_request_files through FakeJob.resume. The worker and Windows process backend are fake; no real process is launched. This closes a previously untested file handoff, not the production CLI or native backend admission.

All 250 tests passed across the same 20 explicitly named synthetic suites in 6.715 seconds, exit 0. Expected ledger collision output belongs to a temporary negative test. No wildcard discovery.

New byte copies: reports/codex_child_file_entry_20261015_01/:

- offline_smoke_child_entry.py: d8e98dac461c0c558927aabfe9a5da3a63e7b4dc26b5e0c3731174ec1ea6648c
- test_offline_smoke_child_entry_synthetic.py: 1e6f9ee79fc20ee0058964b2b91a6fff441919622186a350cf282181ff4ef64d
- test_offline_smoke_dispatch_synthetic.py: b3dca8798f0d15861ed99ea39575c4beee4655f01c90f6254259846090c3aebd

Current limitations: filesystem checks are not a universal race-proof sandbox; expected digest/context must come from a genuine reviewed parent gate, not self-echoed input. Source CLI main remains blocked before I/O. Genuine worker loading, real native Windows adapter assembly, authentic report labeling and full constituent inventory/launch freeze remain unfinished. No real-data access, model/tokenizer loading, native Job/firewall execution, credentials, network, API or manuscript changes occurred. No API key is needed.

Peer review should inspect the actual diff and negative tests without parallel changes or real dependency execution. User relay remains the only communication channel.
