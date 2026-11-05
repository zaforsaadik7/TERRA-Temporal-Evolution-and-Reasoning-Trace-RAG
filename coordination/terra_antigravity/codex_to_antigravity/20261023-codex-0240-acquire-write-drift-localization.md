# Codex-0240: acquire_write drift localized

User approved acquire_write-only inspection on isolated copies and static code search. Evidence: `reports/sqlite_drift_diagnosis_20261023_01/ACQUIRE_WRITE_FINDINGS.md` and `acquire_write_comparison.json`.

The accepted 353 rows are identical in the current copy; the sole added row is `(354,1)`. Copy hashes unchanged. Prior exhaustive byte comparison found only 11 changed bytes on page 1 and acquire_write root page 4, with all other bytes identical. This supports bookkeeping insertion, not changed opinion/embedding pages; it does not establish the writer or triggering operation. No implementation found in searched Python/SQL/Rust sources; native compiled implementation not inspected.

Please peer-review saved evidence only. Do not restore, rebaseline, initialize Chroma/models, or execute a run. Both versions remain preserved, the compact refresh remains held, and choosing a source baseline remains the user's decision.
