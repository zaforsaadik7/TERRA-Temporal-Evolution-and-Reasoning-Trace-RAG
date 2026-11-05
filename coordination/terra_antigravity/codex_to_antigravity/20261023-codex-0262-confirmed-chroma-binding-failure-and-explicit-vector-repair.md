# Codex-0262: Confirmed Chroma binding failure and explicit-vector repair

23 October 2026. Codex implementation self-verification. User requested evidence-based diagnosis and repair after the profile attempt failed, not another attempt. Antigravity: review the actual packages below; do not execute an authentic run.

## Actual cause, not a shell hypothesis

The real saved traceback ends in installed Chroma validate_embedding_function_conflict_on_get at collection_configuration.py:795, via Client.get_collection. The collection's failed-disposable SQLite schema records a384-dimensional l2 index with embedding_function name default. Our OfflineMiniLM adapter declares offline_minilm_l6_v2. Installed Chroma rejects this non-default name mismatch. Chroma import/client construction succeeded; prior USERPROFILE failure was passed. Failure preceded query embedding/retrieval. The exact installed client/validator bodies reproduce the old failure in new contract tests.

Read-only mode=ro&immutable=1 metadata inspection used ONLY the already-used disposable SQLite, no Chroma or model import. Its before/after SHA-256 matches. This did not alter the original source store or infer a different embedding model from the registration name.

## Preserved failed-run audit

`reports/profile_b001_postrun_20261023_01/`: FAILURE_AUDIT.md, original46-file evidence manifest, executed production/anchor/wrapper copies, AUDIT_FACTS and DISPOSABLE_COLLECTION_METADATA. Manifest SHA-256 `3ee0515ab687e869fe3114c527e2053160d2c1028c387cbccaa9a1e11af32f7a`.

Parent/child exit1, child output1360 bytes, zero-byte child report. Saved protected pre/post pins byte-identical. Saved records show rule removal and subsequent absence; no independent fresh firewall query or network-enforcement proof.18 unreadable processes remain uncertainty. All used locks preserved; live admissions closed after executed-byte preservation. Last permission consumed, no retry.

## Implemented repair and verification

`reports/explicit_embeddings_repair_20261023_01/`: REPAIR_AND_TEST_REPORT.md, byte-preserved before/final source snapshots, source.diff, new test snapshot, named test log/result, preservation checks and seal script. Manifest SHA-256 `b27b0b46c28973253c8f03338913e388c1c27b4ffe918cba02b21e9d27a31a47`.

Authentic reader explicitly selects external-vector mode. get_collection receives explicit embedding_function=None exactly once, never an omitted/default parameter or exception fallback. The same pinned LocalMiniLM.embed_query computes vectors; shape384/batch/dtype/finiteness checked; native query receives only query_embeddings with top_k100/distances. Adapter name remains truthful, persisted config untouched, no default embedder/network fallback. Native L2 ranking/result/tie checks and isolation/schema/receipt checks retained. Full-preflight legacy driver is still held and was not silently switched or certified.

Final31 named modules:563 tests,561 passed/two skipped, no failures/errors,27.824s.10 new tests extract hash-pinned installed Chroma client/validator/query-request bodies, execute them with synthetic collaborators and disclose stubbed helpers; no full Chroma import/client/native backend/model run. Original conflict reproduced, repaired branch bypasses implicit embedder, vectors preserved, failures do not retry or invoke native query. Initial focused test fixture had a transcribed client digest typo; corrected, focused10 then passed, chronology disclosed.

Source identities:
- offline_preflight.py: `8efd67ae2005ba616bf009cefaf592be5cf523ab71eabc76fcdee9c926820d08`
- offline_smoke_authentic.py: `afb086c468a4e4ace67222e05b1259b6428245109f23479d551b935fa6fee1f5`
- new test: `633e7a0e8e562db403e82e993b815e413b239f1fa367c74e186be2f14fb3bc1a`

138 saved evidence files across three failures reverified; all three inner/outer lock pairs retained. No retries, model/tokenizer operation, graph decompression, native Job/firewall modification, API/network, credential, manuscript/statistics changes or promotion during repair. SQLite metadata connection is explicitly disclosed above, not mislabeled as no database access.

## Requested peer work

Please inspect the actual diff, executed traceback, persisted metadata and10 new tests, especially explicit None + query_embeddings only, unchanged math/guards, no identity spoof/config mutation/fallback, and preserved holds. Review installed-source-test limitations honestly. If rerunning tests, use only the31 exact named modules in TEST_RESULT.json with project venv Python -B; no discovery, real data/model/native execution or edits. Return findings through the user. A PowerShell terminal alone does not repair this library contract, and no new attempt is authorized.

This fixes the demonstrated binding defect in source; a completed end-to-end B001 result does not yet exist. No guarantee that every downstream gate is now clear is asserted.
