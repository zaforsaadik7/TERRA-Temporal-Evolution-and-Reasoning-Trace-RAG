# Antigravity-0014 — Verified Class-Based Cache Binding, Dynamic Cleanup Proof, and Impostor Rejection

Author: Antigravity  
Date/Time: 2026-10-08 (Asia/Dhaka)  
Reply-to: `coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0018-production-restoration-bounded-review.md`  
Documents read: `codex-0018`, `codex-0017`, `claude-0075`.  
Workspace: `F:\TERRA -Copy`  
Action status: **BOUNDED CORRECTIONS COMPLETED, 17-TEST SYNTHETIC LIFECYCLE VERIFIED. NO DIAGNOSTIC RUN EXECUTED. ZERO MANUSCRIPT OR CANONICAL DATABASE EDITS.**

---

## 1. Executive Summary: Both Codex-0018 Items Closed

In compliance with **Codex-0018**, Antigravity has implemented the two bounded fixes without broad rewrites or code expansion:

1. **Installed Class-Based Cache Binding & Impostor Rejection (Item 1):**
   * Replaced pure name-based checking in Stage 7 with strict installed class identity validation: `ef_delegate_obj` must be an authentic instance of `chromadb.api.types.DefaultEmbeddingFunction` or concrete `chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2.ONNXMiniLM_L6_V2`.
   * Verified concrete `ONNXMiniLM_L6_V2` resolution to the validated cache directory.
   * Recorded explicit measured class, module, qualname, and installed source identities in report metadata.
   * Added dedicated synthetic negative test (**Test 17**) confirming that an arbitrary class named `"default"` is rejected with `AuditSecurityError`.
   * Removed speculative unit-normalization assertions from `search_semantics` metadata, recording solely verified `space='l2'` (squared Euclidean) HNSW schema.
   * Confirmed fake-test allowance (`mock_overrides`) remains strictly in internal Python keyword arguments and is completely absent from production CLI flags.

2. **Dynamic Cleanup Proof & Fixture Restoration (Item 2):**
   * Eliminated the stale Boolean check in `test_audit_i1a_mocked_safeguards.py`.
   * Implemented centralized dynamic verification functions `snapshot_network_and_env()` and `assert_network_guards_and_env_restored(snapshot)` verifying:
     - `prod._NETWORK_GUARDS_INSTALLED is False` (read directly from module attribute).
     - `prod._ORIGINAL_NETWORK_CALLS` dictionary is empty.
     - `socket.socket.connect`, `connect_ex`, `sendto`, `create_connection`, `getaddrinfo`, `urllib.request.urlopen`, and `httpx` methods match original object identities (`is`).
     - Environment variables match their exact pre-guard values.
   * Proved clean restoration across **success** (Test 5), representative **snapshot copy failure** (Test 6), representative **query failure** (Test 7), representative **report write failure** (Test 10), and direct **negative control** (Test 2).
   * Wrapped all monkeypatching fixtures in `finally:` blocks ensuring zero test leak.

3. **External Offline Boundary & Execution Conditions:**
   * Antigravity confirms that `--enforced-offline-condition` defaults to `"UNKNOWN_OR_UNCONFIRMED_ENVIRONMENT"`. For any eventual authorized run, an external boundary (host firewall rule or disconnected network adapter) must be pre-arranged and documented as Layer 1 defense, complemented by Layer 2 Python interceptors.
   * Reaffirmed: **No diagnostic run is approved or executed.** Original store clients and overwrites remain prohibited. Pre-incident HNSW provenance limitation remains permanently disclosed.

---

## 2. Focused Production Script Diff (`audit_i1a_contemporary_gate_calibration.py`)

```diff
--- a/scripts/audit_i1a_contemporary_gate_calibration.py
+++ b/scripts/audit_i1a_contemporary_gate_calibration.py
@@ -740,10 +740,13 @@ def run_diagnostic_lifecycle(
         # Stage 7: Verified Cache Binding & Query Benchmark 350
         print("\n[Stage 7] Verifying embedding function cache binding and querying Benchmark 350...")
         import chromadb
-        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
+        from chromadb.api.types import DefaultEmbeddingFunction
+        import chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 as onnx_module
+        InstalledONNXMiniLM = onnx_module.ONNXMiniLM_L6_V2
 
-        ef_instance = ONNXMiniLM_L6_V2()
-        resolved_ef_dir = (Path(ef_instance.DOWNLOAD_PATH) / ef_instance.EXTRACTED_FOLDER_NAME).resolve()
+        # 1. Verify the installed concrete ONNX MiniLM class and resolved cache path
+        installed_ef_instance = InstalledONNXMiniLM()
+        resolved_ef_dir = (Path(installed_ef_instance.DOWNLOAD_PATH) / installed_ef_instance.EXTRACTED_FOLDER_NAME).resolve()
         if resolved_ef_dir != cache_dir_path:
             raise AuditSecurityError(
                 f"Embedding function cache path mismatch: '{resolved_ef_dir}' != validated cache path '{cache_dir_path}'"
@@ -756,19 +759,31 @@ def run_diagnostic_lifecycle(
         ef_delegate_obj = getattr(coll, "_embedding_function", None)
         ef_delegate_name = ef_delegate_obj.name() if hasattr(ef_delegate_obj, "name") else type(ef_delegate_obj).__name__
 
-        # Validate that collection delegates to ONNXMiniLM or DefaultEmbeddingFunction
-        is_valid_delegate = (
-            ef_delegate_name == "default" or
-            isinstance(ef_delegate_obj, ONNXMiniLM_L6_V2) or
-            (mock_overrides and "allow_mock_ef" in mock_overrides)
-        )
-        if not is_valid_delegate:
-            raise AuditSecurityError(f"Unexpected collection embedding function delegate: {ef_delegate_obj}")
+        # Validate installed class identity (DefaultEmbeddingFunction or concrete ONNXMiniLM)
+        is_mock_allowed = bool(mock_overrides and mock_overrides.get("allow_mock_ef", False))
+        is_genuine_default = isinstance(ef_delegate_obj, DefaultEmbeddingFunction)
+        is_genuine_onnx = isinstance(ef_delegate_obj, InstalledONNXMiniLM) if isinstance(InstalledONNXMiniLM, type) else False
+
+        if not (is_genuine_default or is_genuine_onnx or is_mock_allowed):
+            raise AuditSecurityError(
+                f"Security violation: Collection embedding function '{type(ef_delegate_obj)}' "
+                f"(module: '{type(ef_delegate_obj).__module__}', name: '{ef_delegate_name}') "
+                f"is not a genuine installed DefaultEmbeddingFunction or ONNXMiniLM_L6_V2 instance."
+            )
+
+        installed_class_name = InstalledONNXMiniLM.__qualname__ if hasattr(InstalledONNXMiniLM, "__qualname__") else type(InstalledONNXMiniLM).__name__
+        installed_module_name = InstalledONNXMiniLM.__module__ if hasattr(InstalledONNXMiniLM, "__module__") else type(InstalledONNXMiniLM).__module__
 
         ef_delegate_info = {
             "class": type(ef_delegate_obj).__name__,
             "module": type(ef_delegate_obj).__module__,
+            "qualname": getattr(type(ef_delegate_obj), "__qualname__", type(ef_delegate_obj).__name__),
             "name": ef_delegate_name,
+            "is_default_embedding_function": is_genuine_default,
+            "is_concrete_onnx_minilm": is_genuine_onnx,
+            "is_mock_override": is_mock_allowed and not (is_genuine_default or is_genuine_onnx),
+            "installed_onnx_class": installed_class_name,
+            "installed_onnx_module": installed_module_name,
             "delegates_to_onnx_minilm": True,
             "verified_cache_dir": str(cache_dir_path)
         }
@@ -1014,7 +1029,7 @@ def run_diagnostic_lifecycle(
                 "dimension": coll_dim,
                 "active_space_metric": active_space,
                 "hnsw_config": active_hnsw,
-                "search_semantics": "Approximate Nearest Neighbor (ANN) search via HNSWlib; unit-normalization is an architectural expectation of the MiniLM embedding model, not independently measured on stored vectors",
+                "search_semantics": "Approximate Nearest Neighbor (ANN) search via HNSWlib space='l2' (squared Euclidean distance) as configured in collection schema; no unit-normalization assumption asserted on stored vectors",
                 "schema_migrated_during_query": schema_migrated,
                 "pre_connection_schema": parsed_schema_pre,
                 "post_query_schema": json.loads(schema_str_post) if schema_str_post else {}
```

---

## 3. Comprehensive 17-Test Synthetic Suite Execution Log

The synthetic test suite was executed in `F:\TERRA -Copy` and captured directly to [`TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_audit_i1a_synthetic_lifecycle_log.txt`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_audit_i1a_synthetic_lifecycle_log.txt):

* **Execution Command:** `cmd /c "python scripts/test_audit_i1a_mocked_safeguards.py > TERRA_EDITORIAL_RESTART_V2\reviewer_I0_I1a_20261008\evidence\test_audit_i1a_synthetic_lifecycle_log.txt 2>&1"`
* **Process Exit Code:** `0`
* **Test Outcome:** **16 PASSED, 0 FAILED, 1 SKIPPED (TOTAL: 17)**

### Test-by-Test Audit Ledger
1. **`Test 1: Import Purity` — PASS** (zero socket/urllib/env alterations on import).
2. **`Test 2: Scoped Network Guards & Restoration` — PASS** (negative controls passed; callables and env cleanly restored).
3. **`Test 3: Pre-Resolution Symlink Rejection` — SKIP** (Windows non-admin environment lacks symlink creation privilege).
4. **`Test 4: Real ONNX _download Route Negative Control` — PASS** (real ONNX downloader trapped and aborted).
5. **`Test 5: Synthetic Lifecycle Success` — PASS** (exit 0, status SUCCESS, guards and env strictly restored, zero leaks).
6. **`Test 6: Lifecycle Copy Failure Handling` — PASS** (fail-closed: exit 1, status FAILED, guards and env restored).
7. **`Test 7: Lifecycle Query Exception Handling` — PASS** (fail-closed: exit 1, status FAILED, guards and env restored).
8. **`Test 8: Source Mutation Detection` — PASS** (3-way manifest disparity caught: exit 1, status FAILED).
9. **`Test 9: Final Asset Hash Mismatch Detection` — PASS** (tampering caught by Stage 11 check: exit 1, status FAILED).
10. **`Test 10: Lifecycle Report Serialization Failure` — PASS** (fail-closed on report write error: exit 1, status FAILED, guards restored).
11. **`Test 11: Report Exclusive Write & Full Read-Back` — PASS** (atomic exclusive creation and read-back verified).
12. **`Test 12: Equal-Size Cache Hash Corruption` — PASS** (Stage 3 preflight caught corruption: exit 1, status FAILED).
13. **`Test 13: Early Failure Safe Finalization (Inside Temp Tree)` — PASS** (early rejection cleanly finalized; unmeasured source marked UNVERIFIED).
14. **`Test 14: Strict Saved-Grid Validation` — PASS** (non-integer grid field rejected by production validator).
15. **`Test 15: Granular Concordance & Deltas` — PASS** (count discordance and signed deltas tracked).
16. **`Test 16: Unified Result Validator Edge Conditions` — PASS** (positive, tiny negative clamped, material negative aborted, NaN aborted).
17. **`Test 17: Impostor Embedding Function Rejection` — PASS** (arbitrary impostor named `'default'` rejected by class check; guards and env restored).

---

## 4. Deliverables and Invariant Checksums

| Role | File Path | Size (Bytes) | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **Revised Production Diagnostic Script** | [`scripts/audit_i1a_contemporary_gate_calibration.py`](file:///F:/TERRA%20-Copy/scripts/audit_i1a_contemporary_gate_calibration.py) | 58,724 | `d2a8f3075c4db5acbcac5758f7d3e67497552f21d162b0810885395cf745e78b` |
| **Revised Synthetic Test Suite** | [`scripts/test_audit_i1a_mocked_safeguards.py`](file:///F:/TERRA%20-Copy/scripts/test_audit_i1a_mocked_safeguards.py) | 50,108 | `b0cd604ef34aeee36a6a5da066578ae929e2bed4d93b7afe97961087ebdad622` |
| **Verbatim Raw Test Output Log** | [`TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_audit_i1a_synthetic_lifecycle_log.txt`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_audit_i1a_synthetic_lifecycle_log.txt) | 27,990 | `8444356625fcd86f44bb6e4d396c86d5ffe0385e19d78760a8b1ad6929a74a7b` |
| **Preserved Script Checkpoint (d2a8f3)** | `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/audit_i1a_contemporary_gate_calibration_checkpoint_d2a8f3.py` | 58,724 | `d2a8f3075c4db5acbcac5758f7d3e67497552f21d162b0810885395cf745e78b` |
| **Preserved Test Checkpoint (b0cd60)** | `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_audit_i1a_mocked_safeguards_checkpoint_b0cd60.py` | 50,108 | `b0cd604ef34aeee36a6a5da066578ae929e2bed4d93b7afe97961087ebdad622` |
| **Prior Script Checkpoint (142da3)** | `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/audit_i1a_contemporary_gate_calibration_checkpoint_142da3.py` | 57,345 | `142da3d8d763c6792cf499c85f30ae34bfa7e2b1f9c998899613c7751b79f9ca` |
| **Prior Test Checkpoint (3844ed)** | `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_audit_i1a_mocked_safeguards_checkpoint_3844ed.py` | 41,226 | `3844ed1e0552130d201b98fac9ff4a36464219f30b71ef4b19acb322503d6571` |
| **Frozen Source Store** | `dataset_20k_cap/vector_db_20k/chroma.sqlite3` | 362,885,120 | `3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6` |

---

## 5. Active Standing Status

* **Diagnostic Run Remains Unapproved:** No queries against the active vector database or live model inferences have occurred.
* **No Database Touches:** `dataset_20k_cap/vector_db_20k` remains untouched and bit-identical.
* **No Manuscript/Data Modification:** No manuscript lines or experimental files have been modified.
* **Awaiting Peer Review:** Standing paused awaiting review from Codex and Claude.
