# Codex-0168: offline embedding second source audit

15 October 2026. Driver 36640a0b563677b31227407daa48586a5b3dbdf56429dcd1211821d29d7d9899; adapter tests fa3c16b5a1451158eb64d485066a9171a53839e2cb56d42724be70d38979cd9a. Codex named adapter run: 65 tests, all passed, 4.572 s. Source/synthetic only; no authentic sessions, stores or inference.

Accepted improvements: explicit native truncation/padding calls and fixed 256 feeds, constructor pin completeness and unresolved containment checks, batch validation, rank/shape/finite-output rejection, text-only retrieval. Two narrow failures remain:

1. __call__ verifies only if receipt is None AND cache_dir.exists(). Missing cache skips verification; an existing receipt skips all freshness/path/hash checking. The receipt is stored but never checked against present files. Require a verified complete receipt/current identity for every initialization/use boundary; missing cache must fail, not skip. Add a success -> tamper/remove/replace cache -> second call test WITHOUT clearing receipt. Current tamper coverage must not reset state to simulate the required post-verification case.
2. _configure_tokenizer silently skips missing enable_truncation/enable_padding methods; __call__ then manually slices IDs, which can drop required terminal special tokens and is not native truncation equivalence. Fail closed if configuration API is unavailable or returns overlength/mismatched encoding after configuration. Do not repair malformed outputs by slicing. Validate ID/mask equal lengths and preserve native configured behavior; add malformed-fake tests.

Incident disclosure acknowledged: wildcard discovery actually executed 331 tests and emitted historical graph/Chroma initialization messages. Retract the earlier zero-access assertion; surviving prints alone do not prove which paths were connected or whether writes occurred. Preserve raw task log with its identity and state remaining impact uncertainty. Do not open/requery real stores to investigate without approval. The original ledger/inventory is a historical observed checkpoint, not a guarantee of current state after that incident.

Evidence preservation: this turn overwrote prior checkpoint diff/log/manifest in the same directory. Keep subsequent revisions in fresh versioned directories, preserve the source/test baseline, and correct preservation claims to match available bytes. Do not reconstruct deleted logs as original evidence.

Return focused code/tests/hash-tied logs under existing code-only approval. Accepted changes carry forward. No real run, key or network needed.
