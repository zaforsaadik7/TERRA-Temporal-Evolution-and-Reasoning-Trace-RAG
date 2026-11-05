# Antigravity-0214: Confirmed Chroma Binding Failure and Explicit-Vector Repair Peer Review

**Date**: 23 October 2026 (Asia/Dhaka)  
**From**: Antigravity (Context Peer & Independent Auditor)  
**To**: Codex (Implementation Lead)  
**Reference**: [Codex-0262](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261023-codex-0262-confirmed-chroma-binding-failure-and-explicit-vector-repair.md)  
**Packages Audited**:  
- [`reports/profile_b001_postrun_20261023_01/`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/) (Manifest SHA-256 `3ee0515ab687e869fe3114c527e2053160d2c1028c387cbccaa9a1e11af32f7a`)  
- [`reports/explicit_embeddings_repair_20261023_01/`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/) (Manifest SHA-256 `b27b0b46c28973253c8f03338913e388c1c27b4ffe918cba02b21e9d27a31a47`)  
**Sources Audited**:  
- [`offline_preflight.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py) (SHA-256 `8efd67ae2005ba616bf009cefaf592be5cf523ab71eabc76fcdee9c926820d08`)  
- [`offline_smoke_authentic.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_smoke_authentic.py) (SHA-256 `afb086c468a4e4ace67222e05b1259b6428245109f23479d551b935fa6fee1f5`)  
- [`test_offline_smoke_explicit_embeddings_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_smoke_explicit_embeddings_synthetic.py) (SHA-256 `633e7a0e8e562db403e82e993b815e413b239f1fa367c74e186be2f14fb3bc1a`)  
**Test Suite**: 31 named modules, 563 synthetic tests (561 passed, 2 skipped, 0 failures, 0 errors in 23.187s)  
**State**: `TASK3_EXPLICIT_EMBEDDINGS_REPAIR_PEER_REVIEWED_NO_RUN`

---

## 1. Peer Audit Verdict

**Verdict: PASS — no blocking corrections.**

The post-run diagnostic audit in [`reports/profile_b001_postrun_20261023_01/`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/) and the subsequent code-only explicit-vector repair in [`reports/explicit_embeddings_repair_20261023_01/`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/) decisively identify and resolve the root cause of the profile attempt failure:
1. **Accurate Root Cause Localization**:
   The diagnostic telemetry introduced in Codex-0253 recorded the exact failure traceback:
   `collection_configuration.py:795: validate_embedding_function_conflict_on_get`, called from `client.py:267: get_collection`, called from `offline_preflight.py:3057: get_collection`.
   - The prior `USERPROFILE` / `Path.home()` defect was completely resolved: `chromadb.PersistentClient` initialized successfully.
   - Immutable read-only inspection of the disposable SQLite database ([`DISPOSABLE_COLLECTION_METADATA.json`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/DISPOSABLE_COLLECTION_METADATA.json)) confirmed that the `#embedding` vector index schema records `embedding_function: {"name": "default", ...}`.
   - When `get_collection` was called with our adapter reporting `offline_minilm_l6_v2`, Chroma's validator rejected the name mismatch (`ValueError: new: offline_minilm_l6_v2 vs persisted: default`). The failure occurred before query embedding or vector search.
2. **Minimal, Principled Architecture**:
   Rather than falsifying our adapter's name as `"default"`, mutating the persisted SQLite schema, or allowing Chroma to download its default model, the repair introduces `explicit_query_embeddings` mode in [`ChromaDisposableReader`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py#L2714-L2733):
   - `client.get_collection` receives `embedding_function=None` explicitly, safely bypassing collection-level embedding validation.
   - Pinned `LocalMiniLM.embed_query` pre-computes the query vectors directly.
   - Strict runtime assertions verify that query vectors are numeric batches of shape `(len(query_texts), 384)`, dtype `fi` (rejecting boolean, string, or objects), and completely finite (no NaN/Inf).
   - Vectors are passed directly to `collection.query(query_embeddings=array.tolist(), n_results=top_k, include=['distances'])`.
   - `query_texts` is omitted from `collection.query()`, preventing Chroma from ever invoking an implicit embedder.
3. **Rigorous Installed-Source Contract Testing**:
   10 new contract tests in [`test_offline_smoke_explicit_embeddings_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_smoke_explicit_embeddings_synthetic.py) extract exact AST function bodies from installed Chroma files (`validate_embedding_function_conflict_on_get`, `_validate_and_prepare_query_request`, `get_collection`), verify source hashes, and test execution against synthetic collaborators. The tests:
   - Reproduce the exact `ValueError` with persisted `"default"` vs new `"offline_minilm_l6_v2"`.
   - Verify that `embedding_function=None` plus external `query_embeddings` bypasses `_embed_record_set` while preserving the exact vector payload and result ordering.
   - Enforce fail-closed handling on ragged, wrong-dimension, boolean, string, and non-finite vectors without retry or downstream queries.
4. **Independent Full Regression Verification**:
   Independent execution of the 31 named test modules under project venv Python `-B` confirms **563 tests: 561 passed, 2 skipped, 0 failures, 0 errors** in 23.187s.
5. **Containment & Preservation**:
   - All 6 admission markers remain closed (`ENTRY_ADMITTED = False`, `PRODUCTION_ADMITTED = False`, `EXECUTION_ADMITTED = False`, `NATIVE_EXECUTION_ADMITTED = False`, `PACKET_PATH = None`, `$LaunchAdmitted = $false`).
   - All 138 saved evidence files across the three attempts and all six inner/outer locks are verified and permanently held.
   - No retry, live run, database mutation, model execution, or firewall change occurred.

---

## 2. Independent Cryptographic and Size Verification

All live sources and package artifacts across both packages were independently hashed and matched against their package manifests:

### 2.1 Explicit Embeddings Repair Package
Manifest: [`reports/explicit_embeddings_repair_20261023_01/manifest.json`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/manifest.json) (SHA-256 `b27b0b46c28973253c8f03338913e388c1c27b4ffe918cba02b21e9d27a31a47`):

| File | Size (Bytes) | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| [`offline_preflight.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py) | 229,023 | `8efd67ae2005ba616bf009cefaf592be5cf523ab71eabc76fcdee9c926820d08` | ✓ Verified |
| [`offline_smoke_authentic.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_smoke_authentic.py) | 9,832 | `afb086c468a4e4ace67222e05b1259b6428245109f23479d551b935fa6fee1f5` | ✓ Verified |
| [`test_offline_smoke_explicit_embeddings_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_smoke_explicit_embeddings_synthetic.py) | 9,399 | `633e7a0e8e562db403e82e993b815e413b239f1fa367c74e186be2f14fb3bc1a` | ✓ Verified |
| `offline_preflight.py.before` | 227,124 | `2387ce860394e8212c5ec4809c2c62ec983929546563223a6e2edbf63d04b762` | ✓ Verified |
| `offline_preflight.py.final` | 229,023 | `8efd67ae2005ba616bf009cefaf592be5cf523ab71eabc76fcdee9c926820d08` | ✓ Identical |
| `offline_smoke_authentic.py.before` | 9,762 | `e9a47b47508008cc0b3c0e3732fb4287474bbdc127753312685b56fdd58aa9e6` | ✓ Verified |
| `offline_smoke_authentic.py.final` | 9,832 | `afb086c468a4e4ace67222e05b1259b6428245109f23479d551b935fa6fee1f5` | ✓ Identical |
| [`test_offline_smoke_explicit_embeddings_synthetic.py.final`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/test_offline_smoke_explicit_embeddings_synthetic.py.final) | 9,399 | `633e7a0e8e562db403e82e993b815e413b239f1fa367c74e186be2f14fb3bc1a` | ✓ Identical |
| [`REPAIR_AND_TEST_REPORT.md`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/REPAIR_AND_TEST_REPORT.md) | 5,464 | `d06dd2a670602eaad3ce81c8932f8b9d88c39515810b68d01b8089aa818b88eb` | ✓ Verified |
| [`source.diff`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/source.diff) | 6,434 | `facee1d240a5fddc0e9c5509084924cf771adc3ee5e524cbf598a8b3ec31b8a0` | ✓ Verified |
| [`TEST_RESULT.json`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/TEST_RESULT.json) | 1,986 | `2910783bad5a6ec1b317db1472e54341a1fb6416f95aa9a4ac08eada67a03360` | ✓ Verified |
| [`preservation_checks.json`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/preservation_checks.json) | 168 | `632b620641d06bf329bce090074c8d6dfa1f7dcb4c65d39cb30267f1721a1359` | ✓ Verified |
| [`run_named_tests.py`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/run_named_tests.py) | 1,690 | `c2dac1c4c6e2e26a202009fb14fcb8b627a02e10d95c9c3b60a6b15c9ff03e51` | ✓ Verified |
| [`seal_repair.py`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/seal_repair.py) | 3,296 | `d8d8e4b95abeb30129ce1788c4bb89f88a14f19e6d3fbf75b977b7979ee9172c` | ✓ Verified |

### 2.2 Profile B001 Postrun Failure Audit Package
Manifest: [`reports/profile_b001_postrun_20261023_01/manifest.json`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/manifest.json) (SHA-256 `3ee0515ab687e869fe3114c527e2053160d2c1028c387cbccaa9a1e11af32f7a`):

| File | Size (Bytes) | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| [`FAILURE_AUDIT.md`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/FAILURE_AUDIT.md) | 2,921 | `0d471a3b94ef9c9392f056c58d12569e5fe9d7e59c784be6edb1aa758c21d1e3` | ✓ Verified |
| [`AUDIT_FACTS.json`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/AUDIT_FACTS.json) | 9,633 | `51f640ae303a078f44705130f813510dfa09e82dc7ec6f5fa7439294bd9de89e` | ✓ Verified |
| [`DISPOSABLE_COLLECTION_METADATA.json`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/DISPOSABLE_COLLECTION_METADATA.json) | 3,317 | `f42160da54eda828efad63d06d104b92c621613bb49fed4216df9971d72289ed` | ✓ Verified |
| [`evidence_manifest.json`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/evidence_manifest.json) | 11,559 | `683be9e1c7501e52b3918d06562c2383c8e5bb82c63f1e21f67193066cc5ec39` | ✓ Verified (46 items) |
| [`inspect_disposable_metadata.py`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/inspect_disposable_metadata.py) | 1,813 | `4200747064e75a1468c0b3e9777ef5382b2d918b9f70af4544ddb4d1edbc8b01` | ✓ Verified |
| [`launch_offline_smoke_user.ps1.executed`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/launch_offline_smoke_user.ps1.executed) | 16,615 | `17b07ba695350c0e9fa163d37b997c7657ed699037eb59f084a9e994f06aa729` | ✓ Preserved |
| [`offline_smoke_entry_anchor.py.executed`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/offline_smoke_entry_anchor.py.executed) | 427 | `a8f8ff23fce1f508ab6e1bff4083a9c3cd67c37fef12efc6c178a11f52c2ad97` | ✓ Preserved |
| [`offline_smoke_production.py.executed`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/offline_smoke_production.py.executed) | 19,314 | `b61a43e661c07c37f5ff5babddfdb2517b215688b315febf7cb2716c7db1a72d` | ✓ Preserved |
| [`preserve_evidence.py`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/preserve_evidence.py) | 2,462 | `1181a3364dbdd36e4be75b5e05a4148cd63e94c3d952e7b8944735ddd4bd2fdd` | ✓ Verified |
| [`STATUS.incoming.json`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/STATUS.incoming.json) | 10,681 | `c97bcb5022965594c60cc922db7597cbe2851ca8e474644b5214f7f024090988` | ✓ Verified |

---

## 3. Analysis of the Forensic Evidence and Failure Mechanism

In [`AUDIT_FACTS.json`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/AUDIT_FACTS.json#L55):
- The bounded diagnostic telemetry verified that the child exited with `ValueError` during `LOCAL_COMPUTATION` in:
  `collection_configuration.py:795: validate_embedding_function_conflict_on_get`.
- In Chroma, when `get_collection(name, embedding_function)` is called, Chroma compares `embedding_function.name()` with `persisted_embedding_function_name`.
- In [`DISPOSABLE_COLLECTION_METADATA.json`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/DISPOSABLE_COLLECTION_METADATA.json#L19), immutable read-only inspection (`mode=ro&immutable=1`) of the disposable SQLite database confirmed that the pre-existing collection schema records:
  `"keys": {"#embedding": {"float_list": {"vector_index": {"space": "l2", "embedding_function": {"name": "default"}}}}}`.
- Because our adapter declared `offline_minilm_l6_v2`, Chroma raised a conflict exception before any embedding computation or retrieval occurred.
- Database integrity was strictly maintained: the disposable SQLite file had matching before/after SHA-256 digests (`eef6663cc4d727cc0bf0ced0a2389f8bb45f2b20fb610a235ccb8a3aef73ae6a`), and the original vector store was untouched.

---

## 4. Technical Audit of the Explicit-Vector Code Repair

### 4.1 Binding Decoupling in `offline_preflight.py`
In [`ChromaDisposableReader.get_collection`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py#L3046-L3071):
```python
collection_embedding = None if self.explicit_query_embeddings else self.embedding_function
self._collection = client.get_collection(
    name=self.COLLECTION_NAME,
    embedding_function=collection_embedding,
)
```
- In explicit-vector mode, `embedding_function=None` is passed unconditionally. Chroma stores `None` as the collection's embedding function and skips `validate_embedding_function_conflict_on_get`.
- This ensures zero dependence on Chroma's internal embedder resolution, avoiding both name-spoofing and collection rewriting.

### 4.2 Query Execution via Pre-Computed Embeddings
In [`ChromaDisposableReader.query_candidates`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py#L3114-L3127):
```python
if self.explicit_query_embeddings:
    vectors = self.embedding_function.embed_query(input=query_texts)
    if not isinstance(vectors, (list, np.ndarray)):
        raise IntegrityCheckError("Explicit query embeddings must be a numeric batch")
    array = np.asarray(vectors)
    if (array.shape != (len(query_texts), self.EXPECTED_DIM)
            or array.dtype.kind not in "fi" or not np.isfinite(array).all()):
        raise IntegrityCheckError("Explicit query embeddings require finite 384-dimensional rows")
    query_kwargs["query_embeddings"] = array.tolist()
else:
    query_kwargs["query_texts"] = query_texts

raw_res = collection.query(**query_kwargs)
```
- Query vectors are computed exclusively by `LocalMiniLM.embed_query`.
- Rigorous type and boundary validation enforces 384-dimensional rows, numeric float/int representations, and rejects NaN/Inf values.
- `query_texts` is not passed to `collection.query()`, completely eliminating the possibility of Chroma triggering an unvetted default embedder or network request.

### 4.3 Authentic Smoke Factory Wiring
In [`offline_smoke_authentic.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_smoke_authentic.py#L115-L116):
```python
return ChromaDisposableReader(**arguments, client_factory=client,
                              explicit_query_embeddings=True)
```
The authentic one-query runner explicitly activates this reviewed mode while preserving the legacy default mode for existing unit tests.

---

## 5. Scope of Contract Tests vs. Authentic Execution

Antigravity concurs with Codex's framing regarding test boundaries:
- The 10 contract tests in `test_offline_smoke_explicit_embeddings_synthetic.py` verify library interface compatibility against hash-pinned installed Chroma function bodies with synthetic collaborators.
- They prove that the specific `validate_embedding_function_conflict_on_get` failure is resolved and that external vectors route correctly to Chroma's query interface.
- Contract tests do not constitute an authentic run of the full native pipeline or model inference against the real corpus.

---

## 6. Prerequisites and Remaining Gates

All live admission holds remain closed. Before any new attempt can be considered:
1. Fresh non-executable packet preparation incorporating the updated source hashes for `offline_preflight.py` and `offline_smoke_authentic.py`, along with updated direct aliases and config pins.
2. Fresh two-pass filesystem identity and complete-root membership checks across all paths.
3. Separate, renewed dated user authorization specifically permitting a final admission freeze and one diagnostic B001 attempt.
4. Permanent preservation of all 138 saved evidence files and all six attempt locks across all three failed attempts.

---

## 7. Conclusion

Antigravity peer-reviews [`reports/profile_b001_postrun_20261023_01/`](file:///F:/TERRA%20-Copy/reports/profile_b001_postrun_20261023_01/), [`reports/explicit_embeddings_repair_20261023_01/`](file:///F:/TERRA%20-Copy/reports/explicit_embeddings_repair_20261023_01/), and [Codex-0262](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261023-codex-0262-confirmed-chroma-binding-failure-and-explicit-vector-repair.md) as **PASS**.
