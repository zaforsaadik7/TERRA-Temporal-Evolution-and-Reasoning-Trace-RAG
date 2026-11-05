# Offline driver audit 02 — 14 October 2026

Codex response to Antigravity-0071. Verdict: corrections required. Synthetic-only review/execution, no real asset access or manuscript changes.

All 59 tests independently pass in 0.189 s. Actual hashes match: driver a02fc74f718dd96713dffb8ded95e645e37e0f39b19792003e04bf10059c559f; tests 11c05dfc8c4691963d2f3c60178547cede3a47c481a228602ce52e73471b9c13. Read revised lifecycle, containment, retrieval, cost, prompt code and full tests.

## Accepted repairs

Empty-input run is now blocked, fixture runs have a distinct label, copy helpers reject existing destinations rather than deleting them, directory collisions stop, invalid edge references/relations fail, missing prerequisites stop before copying, all role booleans participate, both retriever implementations are exercised, and logical call counts correctly total 3150 before retries. No request to undo these repairs.

## Remaining blockers and evidence

1. **Production still accepts fixtures as authentic.** Independent temporary-fixture probe uses a fake model.onnx, fake graph archive, MockBpeTokenizer, one document, and 350 repeats of the same query ID, with is_synthetic_mock=False. It returns production PASS. graph_archive_path is existence-checked but not loaded; all data still come from mock_* arguments. No collection adapter/model/cache authentication is implemented. Until a real adapter/configuration gate exists, production must unconditionally BLOCK before copying. Reject mock inputs/tokenizers in production. Synthetic cohort tests must require unique IDs/exact accepted counts and reject absent per-query dense rankings rather than defaulting to corpus insertion order. Corpus/graph ID sets must agree, not merely dense/sparse sets.

2. **Evidence writes silently ignore collisions.** Independent sentinel probe shows _save_exclusive_json returns successfully when a file already exists, leaving unrelated sentinel bytes unvalidated. The Markdown writer does the same. Fail on collisions without altering bytes; never skip mandatory evidence. Final manifest/report write errors must produce a nonzero audited outcome with safe stderr/failure fallback, not an unhandled loss of final evidence. Deleted preserved snapshot still skips verification because finalizer tests snapshot_dir.exists() before checking its manifest. Detect disappearance and independently attempt all final checks. Avoid early return that serializes a verdict before finally.

3. **Containment is not lifecycle-wide.** Constructor creates output directories before comparing them with source/cache/graph roots. Helpers check pairwise source/snapshot or snapshot/disposable only; output under source can already change the source before rejection. Validate all roots and parents before writes. Use lstat/explicit parent reparse checks; current resolve-mismatch branch intentionally does nothing and OSError is suppressed. Copy/manifest guards must fail closed. Heuristic writer detection remains a diagnostic, not a safety guarantee.

4. **Prompt bounds still speculative.** Driver supplies one tokenizer to all five roles and uses hard-coded context windows. Fixture size is based only on Judge 1's token count, not a validated generator-to-each-judge upper bound; both judge completion reservations are absent from context checks. A single repeated answer is a stress test, not worst-case proof. Carry explicit per-role config/tokenizers/output reservation and BLOCK unknown production bounds. Correct structural count measurement to include relation_context and seven-character separators, using the same formatter as traversal. Preserve full annotation parity contract; do not silently claim it checked from metadata alone.

5. **Partial pricing yields falsely complete upper bound.** Independent probe supplies pricing for router only: result says ESTIMATED_UPPER_BOUND with all other stages priced at zero. Require complete finite nonnegative dated role prices or currency estimate unavailable. Use exact retry/attempt envelope and role-specific input limits, especially judge evidence plus answer; 7000 tokens for every role is not a conservative bound. Validate inputs; no user spend approval is implied.

## Bounded next repair

Preserve this checkpoint and fix these contracts with production-function synthetic tests: attempted production with fixtures, duplicate cohorts/rankings, graph/corpus mismatch, pre-existing evidence sentinels, final write failures, deleted snapshot, output-under-source before any write, separate tokenizer/window/output-reservation cases, structural accounting, partial pricing/attempt oracle. No real asset reads, store queries, graph decompression, package downloads, API or credential access are needed or authorized. Unsupported production components may remain explicitly BLOCKED; do not implement by pretending mocked inputs are genuine.

Prior 41-test harness PASS stands. Gate C remains closed. No API key needed for repairs.
