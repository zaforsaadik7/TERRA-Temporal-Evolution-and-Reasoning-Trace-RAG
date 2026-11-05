# Codex-0221 — Parent runner composition

Author: Codex, 15 October 2026 (Asia/Dhaka). Code-only implementation self-verification.

Added offline_smoke_parent.py with assemble_parent_runner. It constructs SmokeRunner with an owned, single-attempt child callback. Only when the runner reaches its child stage does the callback assemble the existing Windows dispatcher; it checks the same configuration object is forwarded. Caller overrides of execute_child or is_synthetic in runner arguments are rejected. Production factory use rejects before argument access; parent main unconditionally returns blocked exit 2 before argument parsing or operations.

Three added tests check deferred parent-to-dispatcher construction with successful fake-child evidence, missing-approval failure without dispatcher construction, and production factory/CLI holds. The composition tests patch the Windows dispatcher factory; they do not establish genuine Windows execution. Windows assembly itself remains covered separately by existing fake-kernel tests. Approval absence cannot be replaced by the composition API.

All 268 tests passed across the same 20 named synthetic suites in 7.467 seconds, exit 0. No wildcard discovery. Temporary ledger collision output is expected negative-test evidence.

Preserved copies: reports/codex_parent_assembly_20261015_01/:

- offline_smoke_parent.py: 39cc64251dab6c84e9e46ce95f596c6c47d2fa0a32d9ad303959710d267f312c
- test_offline_smoke_runner_synthetic.py: 6022db0bc5de1413e9f8cd0d9f9052c77727f8d70b95667188078b920dedcce4

Remaining genuine functionality is still unfinished: real DLL loader and PowerShell executor, authentic worker construction/report integration, independently bound parent-to-child context transport, executable production entries, complete constituent inventory and frozen launch packet. This composition does not remove any runtime hold or authorize execution. No genuine store/graph/model/tokenizer, native Job/firewall, credentials, network/API or manuscript action occurred. No API key needed. Existing code-only scope covers continued implementation; peer review may be batched.
