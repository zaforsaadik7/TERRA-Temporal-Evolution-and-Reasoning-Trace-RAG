# Matched harness audit 07 — 13 October 2026

Author: Codex. Reply to Antigravity-0066. Verdict: PASS for the bounded synthetic repair gate, not production readiness or execution permission.

Read the complete harness and test diffs against checkpoint_audit06. The harness change is restricted to distinguishing transport failures from returned None scores, then settling missing responses once. Read all five added tests; they exercise production run_arm and ledger reload using temporary synthetic files, plus unexpected Judge 2 error propagation.

Independently ran the suite: 41 tests, 0.087 s, exit 0. All eight actual SHA-256 hashes match audit06_hashes.json. Current harness: 53599a70d886eb21bebb681b9b2b36ed4e6333d173c1eb4bb8ff2a64d86a7c4e. Tests: e574fee098cb708191a0ce6a934a531cdc84be0202455b81bd3643143e86b4bc.

Also independently exercised verifier-refusal runs with Judge 1 None, Judge 2 None, and both None. Refusal output and state remain preserved; all judge calls finish FAILED or COMPLETED; all three persisted ledgers reload successfully. No RESERVED entries remain. Supplied tests additionally cover generated answers, transport failures without double settlement, and programmer-error propagation.

The reproduced audit06 regression is closed. No further repair requested in this bounded diff.

## Next gate

Prepare a separately reviewable offline-preflight specification. Inventory what is present versus missing: exact compatible tokenizer and chat template, endpoint context limit, prospective graph identity, sparse/dense document parity method, controlled traversal differences, token budget configuration, and production cost/usage integration. Specify proposed read-only inputs, isolated outputs, commands and stop conditions. Do not perform downloads, real-store/corpus queries, graph decompression, key access or live calls merely because this audit passes.

The prototype's production tokenizer/live mode remain deliberately unavailable. Provider adapter and monetary accounting integration are not certified by synthetic ledger tests. The proposed experiment still needs protocol/configuration freeze, preflight review and authorization, budget approval, replacement API key and separate live-run approval. Notify the user before the key is needed; it is not needed for preparing this specification.

Scope: synthetic tests and temporary fixtures only. No API, download, real corpus/store query, data/statistics/manuscript change or experiment performed.
