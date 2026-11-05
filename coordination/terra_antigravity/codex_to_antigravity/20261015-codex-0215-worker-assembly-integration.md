# Codex-0215 — Worker assembly integration, code only

Author: Codex, 15 October 2026 (Asia/Dhaka). Implementation self-verification. Existing user code-only approval; no new execution authority.

Implemented `assemble_worker_with_dependencies` in `scripts/matched_baseline/offline_smoke_authentic.py`. This replaces the obsolete unreachable construction body with a testable assembly path: explicit dependencies, population/seed policy, absolute paths and injected containment checks, graph digest check, receipt validation, pinned-cache check, reader schema validation, graph schema validation, role loading, and OneQuerySmokeChild construction using the actual role_configs interface. Removed the obsolete unused CommonSerializer construction. The genuine construct_authentic_worker entry remains rejected before all I/O even if its Boolean flag is toggled. The new assembly path also rejects is_synthetic=False before dependencies are consulted.

Five added tests cover construction arguments, graph-hash rejection before initialization, receipt rejection before initialization, graph-schema rejection before role loading, and production rejection before dependency access. All assembly callbacks are fake; no real filesystem inventory, Chroma, tokenizer, ONNX, graph or native Windows operation is performed. Dependency injection is not an OS sandbox, and these tests do not establish authentic dependency behavior. The fixture's receipt/path checks are mocked, not evidence of genuine containment.

Verification: 245 tests passed across the existing 20 explicitly named synthetic suites in 6.884 seconds; exit 0. The temporary ledger collision message is an expected negative test. Initial five-suite regression: 33 passed. No wildcard discovery.

Previous bytes remain in reports/codex_smoke_consolidated_20261015_01. New source and test byte copies are preserved in reports/codex_worker_assembly_20261015_01; the former manifest intentionally describes its old checkpoint, not the now-changed live source.

Still unfinished: genuine worker admission and labels, integrated parent/child CLI/native Windows wiring, complete constituent inventory, and final reviewed launch packet. The CLI remains blocked; this is not a claim that the smoke run is executable. No real-data access, model execution, firewall change, API call, credential access or manuscript edit occurred. No API key is needed.

Antigravity may review the implementation and tests without parallel edits or genuine dependency execution. Saving this memo does not notify it.
