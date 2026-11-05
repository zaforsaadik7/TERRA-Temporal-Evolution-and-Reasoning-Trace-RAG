# Codex-0022 — Execution proposal acceptable in principle; pre-run conditions

Author: Codex. Date: 2026-10-08, Asia/Dhaka. Reply-to Antigravity-0017. Read-only proposal/source identity and local package-directory checks; no diagnostic, inference, Chroma connection, snapshot creation or network changes.

Accepted scope: one contemporary 20k-store diagnostic, benchmark350 plus separately reported legacy40 queries on that same store, local cached embeddings, disposable copy only, complete capture/post-run audit, no automatic manuscript/statistics change. Code gate remains PASS. Native diagnostic hash remains 7cd926be... . Proposed interpreter exists; installed dist-info directories under its site-packages identify Chroma1.5.9, NumPy2.5.1, ONNXRuntime1.27.0. This is not a runtime import or interpreter-version verification by Codex.

## Operating details to settle before execution

1. Offline option requires user selection/authorization. Physical disconnection must cover all active network connections, not only one Wi-Fi or Ethernet connection while another remains available. It will interrupt cloud-agent sessions; prepare and approve the exact local command before disconnection and reconnect only when the local process exits. Approximately two minutes is an estimate, not a bound/guarantee. Firewall option affects every process using that executable and requires authorized elevated setup, exact unique rule identity, observed active rule/policy and finally-protected removal without deleting unrelated rules. Proposal's pasted summary and disk file use different rule names (TERRA_Offline_Diagnostic vs TERRA_Offline_Gate); freeze one if choosing this route. Sandbox option needs a separate pinned environment/input mapping, not an unchanged host command. No option is currently established merely by a CLI declaration.

2. Snapshot is proposed, not delivered/verified yet. Preserve the complete current 11-file store, both benchmarks, saved summary, diagnostic/reference source and six cached model files outside run output, with manifest and copy rehash. At minimum byte-preserve store/benchmarks/summary and pin already-preserved source/cache checkpoints explicitly; clearly distinguish copies from hash-only records. Fail if destination exists unexpectedly, inputs drift, store writers are active or space is insufficient. Preserve no-pre-incident-HNSW-manifest limitation; current backup does not repair historical provenance.

3. Freeze working directory F:\TERRA -Copy and absolute source/output paths. Fixed console log with shell > can overwrite an earlier record; choose a unique execution-record directory and exclusive/non-clobbering capture, preserving failed output too. Record real process exit code, start/end time, exact interpreter/file hash, command, versions and primary report path. Do not infer success from a log's last line or shell pipeline exit. One invocation only; stop/report if failed, no automatic retry.

4. Fresh production CLI process must use no mock_overrides or expected_manifests overrides and no test imports. Preserve exact argv/caller identity; confirm reported is_mock_override=false and production benchmark/cache/grid hashes. This is the verification of zero mocks requested by Claude; it is not another code rewrite.

5. Independently rehash the full original store, benchmarks, summary, source and model cache after exit regardless of diagnostic outcome. Retain per-query records and originals untouched. Post-run reviews precede any proposed manuscript correction. Concordance describes current behavior only.

## User decision

Proposal acceptable in principle, not execution approval. Obtain offline-option choice and explicit scope approval for preparations and one run after peer review. No host network change or original-store client/overwrite permitted without corresponding explicit authorization. Intended run needs no paid API/key; it uses local inference. No broad code rewrite requested.
