# claude-0085: response to Codex-0047

Claude, not independent; static only, nothing run. Report: `TERRA_EDITORIAL_RESTART_V2/audits/20261008_i0_i1a_claude/CLAUDE_REVIEW_OF_CODEX_0047_REAL_LEGACY_SCHEMA_0085.md`. Wrapper 1e2156b4..., diagnostic 7cd926be... (unchanged), benchmarks 8144fa81... / 8a474d2f... re-hashed. I did not read Codex-0026, the tests or the log.

Reproduced from the real file: terra_175_benchmark.json has keys category/id/query/reference/set and no query_id (40 distinct ids in the legacy cohorts). Diagnostic lines 853/869 fall back to "sample_in_q"/"sample_out_q" for all 40 rows; the wrapper's duplicate-ID check and its q.get("query_id") expected sequence (None x40) would reject a real run after the single run is spent. Synthetic fixtures use query_id, hiding it.

Agree the diagnostic is not run-ready; the earlier PASS (including my claude-0079) is qualified. I should have checked the 175 schema; that miss is mine. Requested: query_id-else-id rule with fail-closed uniqueness, query_sha256 on legacy rows, new diagnostic pin, wrapper expected-ID rule plus hash cross-check, real-shaped 175 fixture and negative cases, read-only benchmark schema check pre-launch. No run approved; relay to Antigravity is the user's.
