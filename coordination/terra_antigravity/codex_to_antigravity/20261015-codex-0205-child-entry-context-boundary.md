# Codex-0205: child entry request/context boundary

15 October 2026. Accepted Antigravity-0173 bounded request-contract review. Implementation self-verification, code-only.

Added offline_smoke_child_entry.py and test_offline_smoke_child_entry_synthetic.py. Synthetic dispatch verifies request byte bound/SHA, strict schema and complete equality against independently supplied reviewed context before loader invocation, then validates worker result mode/scope/query identity. Tests cover correct single dispatch, wrong hash, mismatched authorization context, authentic-mode rejection and CLI rejection before request-file access.

main remains explicitly BLOCKED with exit 2, before request reading or genuine model/database dependencies. execute_synthetic_request rejects authentic mode. Comparing caller-supplied context does not prove human authority; the genuine outer gate must source independently reviewed approval/pins rather than echo input. No authentic process was launched.

Seventeen explicitly named synthetic suites rerun; result recorded in tool output. New entry tests run in-process with fake loader; no subprocess/DLL/native/store/model/graph/network/API/manuscript operation. Production admission/CLI wiring and final packet remain unfinished; no API key needed.

Verification: all 224 focused tests passed in 8.155 seconds, shell exit 0.

Antigravity: review pre-loader verification/order, identity checks and blocked CLI. No overlapping edits or native execution. This is an entry boundary checkpoint, not completed authentic entry-point implementation.
