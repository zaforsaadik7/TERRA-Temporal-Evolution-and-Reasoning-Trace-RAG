# Codex-0222 — DLL load argument contract

Author: Codex, 15 October 2026 (Asia/Dhaka). Code-only implementation self-verification.

Added load_injected_windows_library in offline_smoke_windows_assembly.py. It requires a reviewed absolute local Windows System32 directory, rejects UNC/relative/parent-traversal/alternate-stream/mismatched paths, constructs an absolute kernel32.dll path, calls the explicitly supplied loader once with winmode=0x800 (System32 dependency search) and use_last_error=False, then applies the complete 18-export signature binding. The last-error setting matches the current backends' immediate calls to the real GetLastError export rather than ctypes private-error swapping. No fallback or retry.

Four tests use a Mock loader and fake callable exports: exact arguments and combined binding, path rejection before loading, load failure propagation without fallback, and pre-argument production rejection. Directory naming and string agreement alone do not verify the actual Windows system-directory identity, DLL bytes, reparse containment or OS behavior. Genuine admission must supply those checks. load_authentic_windows_library remains an unconditional rejection; this helper does not choose or invoke ctypes.WinDLL and is not genuine loader admission.

All 272 tests passed across the same 20 named synthetic suites in 6.806 seconds, exit 0. No wildcard discovery; temporary ledger collision is expected negative-test output.

Byte copies in reports/codex_dll_load_contract_20261015_01/:

- offline_smoke_windows_assembly.py: c00f25bfd9a57263008db48ad05c374b4931ffa3463a94d090bbd667d90df75b
- test_offline_smoke_component_integration_synthetic.py: baf4a295c72aff67b74f4c8ed5eae2b06bb034caf98f189f9dd2dac77469f6ee

Remaining: genuine worker and loader/executor admission, independent parent-to-child context transport, production entries and complete reviewed constituent/launch packet. No real DLL loading, process/job/firewall operation, authentic store/graph/model/tokenizer access, credentials, network/API or manuscript action occurred. No API key needed. This is another code-only component, not production readiness or execution authority. Peer review can be batched; no fresh code-only approval is requested.
