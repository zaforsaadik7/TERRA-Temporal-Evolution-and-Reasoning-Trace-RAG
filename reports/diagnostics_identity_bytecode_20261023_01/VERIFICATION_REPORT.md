# Diagnostics candidate: structural cache comparison and fresh file identity

23 October 2026, Asia/Dhaka. Codex implementation self-verification under the user's explicit approval to verify source/cache correspondence and refresh filesystem identities. This did not authorize a freeze or another B001 attempt.

## Results

PASS: three pinned application .pyc/source pairs match the tested structural comparison under the pinned Python 3.14.5 base interpreter, optimize=0. The exact source/cache hashes, timestamp header fields and code-object/constant counts are in bytecode_equivalence_receipt.json. All header magic values match the running interpreter; only the observed timestamp flags=0 are accepted; source size and timestamp match. Inputs are size-capped, hash-checked before deserialization and rechecked afterwards; trailing marshal data is rejected. Only these already identified files were deserialized; no code object was executed or application module imported.

The comparison covers seventeen listed scalar/tuple/byte code fields plus Windows-path filename equality and recursively typed co_consts, including nested code objects. This includes flags, argument/local/stack metadata, free/cell variables, qualification, first line, line table and exception table, not merely the peer's earlier co_code/co_consts/co_names selection. Matched code-object counts: production25, authentic19, diagnostics8. The verifier's fixed synthetic positive round-trip and six negative mutation checks passed, including nested flags, exception table, line table, stack metadata and filename differences. The compiled fixture was never executed.

This is a reproducible **pinned structural comparison**, not independent origin/signature proof, a guarantee of execution safety, proof of every private interpreter detail, or a certificate for later changed source. In particular, a future admission edit changes source bytes: this receipt must not silently be presented as equivalence for the future admitted production file. Recheck/classify affected caches when freezing that state. No .pyc deletion, rewrite or blanket admission was performed.

Python emitted co_lnotab deprecation warnings while comparing that additional legacy attribute; these were not suppressed and were not comparison failures. See fields_compared for the exact scope, rather than a claim of unspecified complete cryptographic source fidelity.

## Freshness

Two filesystem-only SHA-256/size passes verified **30,568 unique declared paths** against the exact Codex-0254 candidate. Four complete-root memberships matched in both passes: base DLLs, MiniLM cache, source vector store and venv site-packages. The count is two higher than the earlier30,566 because the diagnostics source and its cache are now included. Counts include deduplicated top-level declaration and member paths; do not conflate them with member-only counts.

Observation window: 2026-10-23 08:38:20–08:39:22 UTC. pass_1.json and pass_2.json preserve all identities. Each file and ancestor is checked for reparse attributes; size/mtime stability is checked around hashing. These matching observations are not continuous locking, proof of source quiescence during later execution, or a runtime/native compatibility test.

Source/cache/model/graph/runtime files were streamed as ordinary bytes for hashing only. No SQLite connection/query, Chroma client, graph decompression, model/tokenizer operation, Windows Job/firewall query/change, API/network, credentials, manuscript/statistics or promotion work. The interpreter and standard-library verifier executed; tested application cache/source code objects did not. No named synthetic runtime suite or B001 was run.

## Held state and preservation

The original candidate/decision remain unmodified and invalid for execution: null authority, nonexistent approval file, unused candidate directory. All source/worker/native/executor holds remain false, packet anchors None and wrapper held. Existing failed-run evidence and locks remain preserved; saved evidence hashes are rechecked during sealing. No attempt directory, runtime request/receipt or executable command was created.

Next: peer review of actual verifier, self-checks, receipt and two-pass observations. Then a separately renewed dated permission and fresh reviewed admission freeze are needed for any future attempt. The old RuntimeError remains unlocated; these checks do not repair it or constitute another run.
