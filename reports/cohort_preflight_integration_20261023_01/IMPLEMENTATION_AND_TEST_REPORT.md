# Full-cohort offline preflight: code-only integration checkpoint

23 October 2026. Codex implementation self-verification. User approved code-only integration and synthetic tests after Antigravity-0216 confirmed B001 offline success. No genuine350-query preflight was performed.

## Changes

OfflinePreflightDriver now constructs readers through _build_disposable_reader. With a supplied reviewed query embedder it explicitly selects the same external-vector interface tested in B001: embedding_function=None at collection binding, then explicit query_embeddings computed by that embedder. Missing authentic embedder fails closed. Legacy synthetic fixtures without an embedder retain their prior interface. Neither helper opens a real client during construction, and the unconditional real-production block remains unchanged.

Dense rankings are collected through _query_dense_rankings in deterministic batches of at most32 query texts. This matches the existing MiniLM default batch width; it bounds the individual query-request batch, not total runtime, total model memory or tokenization work.350 queries produce11 batches (ten32 plus one30). Native top_k100/distance semantics and per-query ordering are unchanged. Model math and tokenization were not altered. Helpers enforce valid unique query IDs, exactly two retrieval input fields, exact result batch cardinality, nonempty unique candidate lists of at most100 IDs and shared-corpus membership. No retries or invented/missing-row fallback. If prior corpus/graph checks failed, the driver does not start dense-query work.

## Tests and evidence

New10-test module tests/test_offline_preflight_cohort_synthetic.py includes a full generated350-record benchmark with100/100/75/75 category counts, temporary two-document SQLite/graph fixtures, synthetic vectors and mock tokenizers. It exercises the actual driver/reader wiring and emits700 hypothetical route envelopes. A strict fake collection accepts only external vectors and fails if an embedder is bound; no permissive query_texts method exists. Other tests cover350-row ID mapping, short/long/missing batch output, duplicate/malformed query identities, invalid/duplicate/out-of-corpus candidates, failure at the second batch without retry/third batch, failed-graph inference exclusion, explicit reader construction and production hold even with execute_authorized_real_preflight=True.

Final32 named modules:573 tests,571 passed/two skipped, zero failures/errors,26.342s. Run used project venv Python -B with exact module names, no discovery. TEST_RESULT.json and named_tests.log retained. Existing installed-Chroma-source contract tests remain in this suite; all real package/model/backend initialization stays out of these tests. The fixture benchmark is not the real benchmark;700 synthetic envelopes are not scientific results or an all350-real-query success claim.

Byte-preserved source baseline SHA8efd67ae2005ba616bf009cefaf592be5cf523ab71eabc76fcdee9c926820d08, final source SHA34db0423fc35e2fbdc74c9ad40bdd40fc139e3aa2f3a8058af7064d8ec2b94e3. Before/final snapshots and source.diff retained. Prior successful B001 source snapshot remains separately preserved; its execution packet is consumed and must not be repointed at this new source.

## Remaining operational work; not launch-ready

The legacy driver's real mode is still unconditionally BLOCKED. This batch does not turn its synthetic reports into an authentic certified report, and does not authorize changing that block. A full-cohort controlled child/report/launcher composition must be reviewed deliberately, rather than using the one-query packet with a larger query count or removing a guard. It must retain the proven profile/external-vector wiring, no-network controls, complete source/cache/graph/tokenizer pins, copy parity, query-ID/category-independent retrieval, exclusive evidence and single-use locks, process/rule ownership/recovery, and explicit real-vs-hypothetical/placeholder disclosures.

The full-cohort time/memory/output bounds must be specified and reviewed; the B001300s budget is not assumed sufficient for350 queries. Fresh identity/membership checks and separate dated permission are prerequisites before a real full-cohort attempt. No API key is needed for the offline preparation; live-provider endpoint certification, financial authorization and API credentials belong to a later separate phase.

No genuine benchmark contents, store, graph archive or model cache were opened through their runtimes, and no real store/model/tokenizer operation, Windows Job/firewall operation, API/network request, credential access, manuscript/statistics change or promotion occurred. All184 saved attempt evidence files and four inner/outer lock pairs are reverified intact at sealing; live admission constants/anchors remain closed. Peer review is requested, not presumed.
