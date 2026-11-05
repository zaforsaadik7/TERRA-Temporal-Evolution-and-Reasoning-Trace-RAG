# Codex-0266: Cohort explicit-vector wiring and synthetic PASS

23 October 2026. Codex implementation self-verification. User approved code-only integration/synthetic testing for full350-query offline preflight after Antigravity-0216; no genuine full-cohort execution or production-hold change authorized.

Package: `reports/cohort_preflight_integration_20261023_01/`, manifest SHA-256 `030aab67538057a31ebf057a7d181c1008a5240f0f09263e414e082ca1f5333c`. Read IMPLEMENTATION_AND_TEST_REPORT.md, actual source.diff, before/final snapshots, new tests and named log/result.

OfflinePreflightDriver now delegates reader construction to an external-vector-aware helper; supplied query embedder selects the B001-tested explicit None binding/query_embeddings path. Missing authentic embedder fails closed. Dense rankings use batches<=32 with exact query-ID mapping, exact batch cardinality, nonempty/unique valid candidate IDs restricted to shared corpus. Retrieval receives query text only, no category/gold/target fields. Failure stops without retry; prior corpus/graph failures prevent dense-query work. Native top_k100/L2/result checks, model math and tokenization unchanged. Legacy synthetic no-embedder fixtures retained.

New10 tests include actual driver/reader integration over a generated350-query100/100/75/75 benchmark and temporary two-document graph/SQLite corpus with synthetic vectors/mock tokenizers. Emits700 hypothetical envelopes in11 dense batches (ten32 and one30), proving plumbing—not authentic corpus/model results. Also tests count/ID/candidate rejection, second-batch failure/no retry, graph-failure inference exclusion, mandatory embedder and unchanged production block even with execution flag.

Final32 named modules573 tests:571 passed/two skipped, no failures/errors,26.342s. Project venv Python-B, no discovery. Source before hash8efd67ae2005ba616bf009cefaf592be5cf523ab71eabc76fcdee9c926820d08; final34db0423fc35e2fbdc74c9ad40bdd40fc139e3aa2f3a8058af7064d8ec2b94e3. New test34b54e4984199f2fb3c04e596d3b637eac74814fbe1f1620d63b72d7755085b7.

184 original evidence files and four inner/outer attempt-lock pairs verified intact. All six admission holds closed. No genuine dataset/store/cache/graph/model runtime, Job/firewall/API/network/credential/manuscript/statistics or promotion operation. Successful B001 artifacts remain immutable; consumed one-query packet cannot be used for the cohort or this revised source.

Antigravity: review actual diff and new tests, helper selection, query ordering/bounds and failure paths, production block and scope disclosures. If rerunning tests, only32 named modules in TEST_RESULT.json with project venv Python-B, no discovery or genuine data/model/native work. Return findings through user; no parallel implementation requested.

Remaining operational work is a separately reviewed full-cohort controlled child/report/launcher composition, explicit resource/time/output bounds (do not assume B001300s sufficient), refreshed identity/membership pins and new dated execution approval. Do not simply unhold the legacy driver or enlarge the one-query packet. No API key needed for offline preparation. This checkpoint is code integration, not a launch-ready cohort packet or finished matched-baseline experiment.
