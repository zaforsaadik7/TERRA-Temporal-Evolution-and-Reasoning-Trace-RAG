# Relay to Antigravity: request for an execution proposal (drafted by Claude, claude-0080)

Claude has no live channel to Antigravity; the user relays this file. Please read first: Codex-0021 (`coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0021-report-preservation-gate-pass.md`) and Claude-0079 (`TERRA_EDITORIAL_RESTART_V2/audits/20261008_i0_i1a_claude/CLAUDE_REVIEW_OF_CODEX_0041_GATE_PASS_0079.md`).

Status: the bounded code gate is closed for script 7cd926be...c41f and tests 6b6577f1...7bfd. No further code rewrite is requested. NOTHING is authorized to run, open a store, or call any model or API.

Please write a proposal only (no execution) covering:
1. Externally enforced offline conditions: the concrete mechanism (for example adapter or VM network disabled, or a blocked-outbound sandbox user), how it will be verified before and after, and its effect on the user's other sessions. Do not change network settings or install firewall rules without the user's permission. "UNKNOWN" is not proof.
2. Exact interpreter path and version, the exact command line (explicit --workspace-root, --onnx-cache-dir, --enforced-offline-condition), and installed chromadb, onnxruntime, numpy versions.
3. A byte-preserved snapshot of the current 11 store files with manifest (path, size, sha256), plus hashes of both benchmarks, the saved summary and the six ONNX cache files, stored outside the run's scratch/output tree. The original store is never opened by Chroma or overwritten; keep the incident history and the unavailable pre-incident HNSW provenance disclosed.
4. One run only, one output folder, complete stdout/stderr capture with its hash.
5. Explicit confirmation that no mock hooks (mock_overrides, allow_mock_ef, mock_cleanup_fn and the others) are active, and that the report records this.

After the proposal: Codex and Claude review it, then the user decides separately. Any result must pass the post-run audit before it can inform a manuscript correction, and a match shows contemporary behavior only, not historical provenance.
