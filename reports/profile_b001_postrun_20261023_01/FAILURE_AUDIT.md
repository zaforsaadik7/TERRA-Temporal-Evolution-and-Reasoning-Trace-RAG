# Profile B001 failure: evidence-backed cause and cleanup
23 October 2026. Codex implementation self-verification; no attempt repeated.

## What actually failed
The saved child traceback ends at installed Chroma collection_configuration.py line795, validate_embedding_function_conflict_on_get, called from client.py get_collection. The failure is ValueError during LOCAL_COMPUTATION while extracting the corpus/getting the collection, before query embedding or retrieval. Chroma imported and constructed a client successfully: the earlier missing-USERPROFILE defect was passed, not repeated.

The adapter's OfflineMiniLMEmbeddingFunction.name() returns offline_minilm_l6_v2. A read-only, immutable SQLite metadata inspection of this already-used disposable database found a384-dimensional l2 #embedding vector index whose embedding_function name is default. The installed Chroma validator raises when the supplied non-default name differs from the persisted name. The exact installed client/validator function bodies reproduce that failure with synthetic collaborators. This is an embedding-function registration/name conflict, not evidence of different model math, missing model weights or a PowerShell launch failure.

The metadata inspection did not connect to Chroma or inspect query results. It read the failed disposable only via SQLite mode=ro&immutable=1 with query_only. Database SHA before/after both eef6663cc4d727cc0bf0ced0a2389f8bb45f2b20fb610a235ccb8a3aef73ae6a. Original source store was not opened by this inspection. Config JSON is {}; the persisted schema contains the default registration. The source database was not rewritten to change that registration.

## Saved outcome and preservation
Parent and child exit1, FAIL. Child output1360 bytes SHA0527ac294448d6e1bf095b79ce34d626f772bf778bd21fe5b825fa0fbb4f4daf; empty child report. Saved before/after protected-pin files are byte-identical; their member summary is30,556, a different counting scope from the30,569 declared-file admission verifier. No successful retrieval outcome.

Boundary records show matching rule properties before use, removal followed by two null/absence queries. Terminal reports execution failure only, not cleanup/integrity failure. This is saved-run evidence, not an independent current firewall query or proof of traffic enforcement. Unreadable process count18 remains uncertainty. All46 saved parent/wrapper evidence files were hashed; executed production/anchor/wrapper copies preserved before restoring live holds. Inner and outer single-attempt locks retained permanently.

## Repair
See reports/explicit_embeddings_repair_20261023_01/REPAIR_AND_TEST_REPORT.md and source.diff. User's current request authorized fixing the code; it did not authorize another attempt. No retry, model operation, graph decompression, firewall modification, API or manuscript/statistics change was performed during this diagnosis/repair.
