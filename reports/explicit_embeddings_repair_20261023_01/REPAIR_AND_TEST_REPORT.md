# Explicit-vector collection binding repair
23 October 2026. Codex implementation self-verification under user's request to fix the failed integration.

## Cause and minimal functional change
The actual failed run rejected offline_minilm_l6_v2 versus persisted default during Chroma get_collection. Evidence is in reports/profile_b001_postrun_20261023_01/ including the original structured traceback, immutable disposable-metadata check and executed source copies.

ChromaDisposableReader now has an explicit_query_embeddings mode. Authentic one-query worker construction selects it. In this mode:
- get_collection is called exactly once with embedding_function=None explicitly, disabling collection-managed embedding; no omitted/default argument, exception-driven fallback, identity spoof or config mutation.
- The reviewed LocalMiniLM.embed_query computes the batch using the existing pinned-cache math/guards.
- Exact batch count,384-dimensional rows, numeric non-Boolean dtype and finiteness are checked before query.
- collection.query receives query_embeddings only, with n_results100 and distances included. No query_texts is supplied to Chroma, so its implicit/default embedder cannot be selected by that input path.
- Native distance semantics, downstream result checks/ties, model preprocessing/pooling/normalization, schema/receipt/isolation checks and limits are unchanged.
- Legacy/default reader mode remains available for existing callers/tests. The separately held full-preflight driver has not been silently switched or certified; its future authentic integration must deliberately select/review this mode before use.

This changes the collection interface, not the embedding model or corpus. Explicit vectors are preferable to falsifying our adapter name as default or rewriting the collection.

## Evidence stronger than the original mock
Ten new contract tests extract hash-pinned function bodies from installed Chroma:
client.Client.get_collection, collection_configuration.validate_embedding_function_conflict_on_get, and CollectionCommon._validate_and_prepare_query_request. Only those bodies are compiled/executed, after stripping decorators/import-time annotations/default expressions; all exercised optional arguments are explicit. Server, collection and validation/normalization collaborators are synthetic, and helper checks are stubbed. Full Chroma import, native backend, real collection queries and model loading do NOT occur.

The tests:
- reproduce the original ValueError through the installed client and validator with persisted default;
- verify explicit None plus external vectors passes the same validator and the installed request branch does not invoke _embed_record_set;
- verify unchanged vector payload, no query_texts, same top_k/distance result/tie sorting;
- check bad dimensions/batch counts/non-finite/Boolean/string/ragged vectors, no native query after failure, no retry, collection reuse and authentic factory wiring.

This is an installed-source contract test, not a full runtime success claim. A future real attempt remains needed to verify downstream pipeline execution; no guarantee that every remaining gate will pass is made.

## Results and chronology
Final named regression run:31 modules,563 tests,561 passed/two skipped, zero errors/failures,27.824 seconds. TEST_RESULT.json and named_tests.log preserve the final run. No wildcard discovery. Invoked venv Python with -B; no cache regeneration. Initial focused run stopped on a transcribed client.py digest typo in the new test (b853dbc versus actual b853bdc); the source was not drifting. Corrected the fixture pin;10 focused tests then passed. That initial failure is in the conversation tool transcript, not misrepresented as a passing run or raw log retained here.

Both source .before snapshots are byte-identical to the failed frozen source-manifest rows; .final snapshots/diff and test source are sealed. Application admission constants and anchors were restored closed before repair; no new attempt is authorized. Prior executed artifacts and138 evidence files across three failures are verified unchanged, with all six associated inner/outer locks retained (see preservation_checks.json). No database writes, model/tokenizer execution, native Job/firewall operations, network/API, credentials, manuscript/statistics edits or promotion.

## Peer review request
Antigravity should inspect the actual diff, failed traceback, metadata evidence and all new tests. In particular verify:
1. Explicit None is mandatory, not default-argument omission or exception retry.
2. Every authentic query in this mode uses query_embeddings only, and LocalMiniLM guards/math remain unchanged.
3. The installed-source tests retain the actual conflict and request-branch logic while honestly disclosing synthetic helpers.
4. Receipt/schema/read-only/corpus/ranking/result checks and holds remain effective.
5. Final report does not equate contract tests with completed B001 or full matched-baseline results.

Only the31 explicitly listed modules in TEST_RESULT.json may be rerun with venv Python -B. No wildcard discovery, real database/model/native run, edits to source/runtime artifacts, or new attempt. Antigravity's ability to open PowerShell is not permission to bypass the frozen one-attempt policy. The existing user-window run and saved diagnostics already pinpointed this failure; a different shell alone cannot correct the incompatible collection binding.
