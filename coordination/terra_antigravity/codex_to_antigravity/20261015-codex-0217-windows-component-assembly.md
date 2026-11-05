# Codex-0217 — Windows component assembly

Author: Codex, 15 October 2026 (Asia/Dhaka). Code-only implementation self-verification, not genuine native execution certification.

Added offline_smoke_windows_assembly.py. assemble_windows_dispatch wires WindowsJobBackend, ChildOutputCapture, SmokeProcessSupervisor and SmokeChildDispatcher, binding timeout, memory and output limits from config. It checks the canonical absolute child_output.log location against the evidence directory. Construction does not call kernel APIs: DeferredCaptureJobBackend creates capture handles only when suspended process creation is reached, after dispatcher request checks and job creation. Capture containment is rechecked then. A failed capture setup prevents child creation; a recorded attempt forbids retry. Existing backend cleanup owns capture/process handles.

Five new integration tests verify lazy construction and limit binding, foreign evidence-directory rejection before native calls, production rejection before path access, capture failure before child creation with no retry, and capture allowlist/STARTUPINFOEX/suspended flags passing through the assembled backend. Fake kernel APIs only: no DLL loads, genuine handles or child processes. Existing supervision and cleanup tests remain in the named suites.

All 255 tests passed across the existing 20 explicitly named synthetic suites in 7.641 seconds, exit 0. Temporary ledger collision output is expected. No wildcard discovery.

Byte-preserved checkpoint: reports/codex_windows_assembly_20261015_01/:

- offline_smoke_windows_assembly.py: 94742299a0bf9c4d7f4dded988c4f86fac8bc257967ad124368eb8c9ff7d88fc
- test_offline_smoke_component_integration_synthetic.py: eb7c739294baaddb84cb3f62b3050b461b6bacd95d7260bc83fdbb81a52a76a8

Remaining: the reviewed genuine DLL/API binding and PowerShell executor, genuine worker admission/report labels, parent/child production CLI with complete constituent verification, then execution-packet freeze. No production entry is enabled by this assembly; is_synthetic=False rejects. Injected APIs are a testing interface, not a sandbox or permission mechanism. Path resolution does not eliminate every filesystem race. No real-data access, model/tokenizer execution, native Job/firewall execution, secrets, network/API calls or manuscript changes occurred. No API key needed.

Antigravity: review source and tests without parallel edits or genuine operations. The user relays this memo; it does not establish automatic communication.
