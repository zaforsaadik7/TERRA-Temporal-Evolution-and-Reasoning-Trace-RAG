# Claude review of Codex-0041 / Codex-0021 checkpoint (claude-0079)

Claude, NOT independent (Claude wrote Batches 1-28 text). Static only: nothing executed, no store opened, the saved 18 PASS/1 SKIP log not rerun by me.

Checkpoint reviewed: script 7cd926be...c41f, tests 6b6577f1...7bfd (both re-hashed by me from the staged copies; log 1d8f2485... not seen by me).

## Verdict: bounded code-repair gate PASS, agreed. Not an execution approval.

Confirmed in source:
- The write-mode fallback is gone. The only report opens left are `"x"` (line 434) and read-back `"r"` (line 438). The report-failure handler sets FAILED, records `ReportSerializationError`, and prints a terminal record to stderr, with no filesystem write.
- Test 19 (line 1112) pre-creates a sentinel at a deterministic run-id path and asserts the bytes are unchanged after collision.
- Earlier closed items remain closed in my reading: constants (grid 0.90-1.40, ONNX manifest, ad6f26e8 reference), class-based delegate check, cleanup before status.

Residuals I would carry forward (not blockers for the code gate):
1. `allow_mock_ef` and the other `mock_overrides` hooks remain inside production code. CLI does not pass them, but the report should record `mock_overrides` presence so a mocked run can never be mistaken for a live one.
2. Windows symlink/reparse behavior is untested (disclosed by Codex); the SKIP should stay visible in any run record.
3. I did not verify installed-chromadb behavior (class vs factory for `DefaultEmbeddingFunction`) or the `copytree` handling of open handles; both are run-time facts, not source facts.

## Conditions I would require before the user approves a run
1. **Offline arrangement:** a concrete, externally enforced one (for example, the machine's network adapter or VM network disabled, or a dedicated sandbox user with outbound blocked), described by the user in the report field. In-process interceptors are a second layer only. Do not change network settings without the user's permission, given effects on their sessions.
2. **Pinned execution:** exact interpreter path and version, exact command line with explicit `--workspace-root`, `--onnx-cache-dir` and `--enforced-offline-condition`, and the installed chromadb/onnxruntime/numpy versions recorded before the run.
3. **Pre-run snapshot:** a byte-preserved copy of the current 11 store files with a manifest (path, size, sha256), plus hashes of both benchmarks, the saved summary and the six ONNX files; stored outside the run's scratch/output tree and treated read-only.
4. **Single run:** one execution, one output folder; no rerun that could mask a first result; stderr/stdout capture saved with its hash.
5. **Post-run audit before any use:** Codex and Claude audit the per-query ledger (350 + 40 rows), aggregate concordance, and protected-input invariants. The classification is contemporary only. It does not authenticate the historical 10k provenance.
6. **No downstream action:** no manuscript change, threshold change, generated-statistics edit, paid API call or 10k extension follows from the result without a separate user decision.

## Gate
No run, inference or store opening is authorized by this review. Remaining before a run: the offline arrangement (Antigravity proposes, user decides), the input snapshot, and the user's separate approval. Relay to Antigravity is the user's.
