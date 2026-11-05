# Codex-0218 — Combined Windows API signature binding

Author: Codex, 15 October 2026 (Asia/Dhaka). Code-only implementation self-verification.

Added bind_windows_api_library to offline_smoke_windows_assembly.py. It validates all 18 required exports before configuring any signatures, then applies both job/process and capture signature sets to the same supplied library. Tests use callable fake exports that raise on invocation. This prevents accidentally assembling a library with only one signature family configured. Added load_authentic_windows_library as an unconditional pre-load rejection; no DLL-loading implementation is claimed.

Three new tests cover combined binding with zero API invocations, missing-export rejection before partial signature modification, and both production binding and DLL-loading holds. All 258 tests passed across the same 20 named synthetic suites in 7.272 seconds, exit 0. No wildcard discovery; temporary ledger collision is expected negative-test output.

Preserved source/test copies in reports/codex_windows_binding_20261015_01/:

- offline_smoke_windows_assembly.py: 137c6c95ff541c9da1104a73cb59245228e4f94a4a8570c6738f4d1c4885010a
- test_offline_smoke_component_integration_synthetic.py: 4b40d88d63be84452adfc855baa9912057379308c4df6570c6bf51845f31baad

Limits: signature binding alone is not genuine Windows ABI or runtime validation. Last-error semantics must be consistent in the eventual loader; complete genuine loader, worker/report admission, parent/child CLI and constituent/execution packet still remain. This change does not enable any production entry or constitute execution permission. No real DLL loads, native process/job/firewall actions, real-data or model/tokenizer access, credentials, network, APIs or manuscript changes. No API key needed.

Peer review can be batched with subsequent integration work; this memo does not require another user approval to continue existing code-only implementation. No direct notification channel is assumed.
