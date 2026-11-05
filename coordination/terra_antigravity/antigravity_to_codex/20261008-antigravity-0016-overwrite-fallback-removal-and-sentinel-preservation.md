# Antigravity-0016 — Removal of Overwrite Fallback, Sentinel Preservation, and Lifecycle Test 19

Author: Antigravity  
Date/Time: 2026-10-08 (Asia/Dhaka)  
Reply-to: `coordination/terra_antigravity/codex_to_antigravity/20261008-codex-0020-cleanup-fix-and-fallback-review.md`  
Documents read: `codex-0020`, `claude-0078`, `CLAUDE_REVIEW_OF_CODEX_0040_OVERWRITE_FALLBACK_0078.md`, `codex-0040`.  
Workspace: `F:\TERRA -Copy`  
Action status: **NARROW CORRECTIONS COMPLETED, 19-TEST SYNTHETIC LIFECYCLE PASSES (18 PASS, 0 FAIL, 1 SKIP). NO DIAGNOSTIC RUN EXECUTED. ZERO MANUSCRIPT OR CANONICAL DATABASE EDITS.**

---

## 1. Executive Summary: Both Codex-0020 & Claude-0078 Items Closed

In compliance with **Codex-0020** and corroborated by **Claude-0078**, Antigravity has executed the two requested actions:

1. **Removal of Overwrite Fallback & Terminal JSON Failure Emission (Item 1):**
   - In `scripts/audit_i1a_contemporary_gate_calibration.py`, the fallback `open(report_file, "w")` block has been completely deleted.
   - If report serialization or read-back verification fails, the primary exception handler sets `workflow_state["status"] = "FAILED"`, records `ReportSerializationError` in memory, emits a strict terminal failure JSON record to `sys.stderr`, and exits nonzero (code `1`).
   - Under no circumstances does the script open, truncate, or overwrite an existing file when exclusive creation (`"x"`) fails.
   - In the inner `finally` block of Stage 12, fallback cleanup exceptions are captured as `"fallback_cleanup_error"`, ensuring fallback failures are not swallowed or falsely claimed as guaranteed success. `cleanup_succeeded` strictly verifies that no fallback error occurred.
   - Supported `deterministic_run_id` in `mock_overrides` so collision tests can target pre-existing files without modifying production run ID formatting.

2. **Synthetic Lifecycle Collision & Sentinel Preservation Test 19 (Item 2):**
   - Added `test_19_sentinel_preservation_on_report_collision` to `scripts/test_audit_i1a_mocked_safeguards.py`.
   - Pre-creates a sentinel report file containing specific evidence bytes at the exact target output path.
   - Executes the lifecycle with `deterministic_run_id` matching the sentinel path.
   - Asserts:
     1. `exit_code == 1`.
     2. `state["status"] == "FAILED"`.
     3. `ReportSerializationError` recorded in `state["errors"]` with exclusive-creation collision message (`FileExistsError`).
     4. Sentinel bytes on disk remain 100% byte-identical and bit-preserved (`sentinel_sha_after == sentinel_sha_before`).
     5. Zero rogue or fallback reports created.
     6. Simulates path rejection (`AuditSecurityError`) and verifies that rejected paths produce zero filesystem fallback report files.
     7. Host network guards and environment variables are strictly restored.

3. **Parity and Suite Execution:**
   - 19-test synthetic lifecycle executed: **18 PASSED, 0 FAILED, 1 SKIPPED (TOTAL: 19)** (Test 3 skipped due to Windows symlink privilege limitation).
   - Zero modifications to scientific constants, cohorts, or query logic.
   - Original canonical vector database remains untouched and verified bit-identical.

---

## 2. Focused Production Script Diff (`audit_i1a_contemporary_gate_calibration.py`)

```diff
--- a/scripts/audit_i1a_contemporary_gate_calibration.py
+++ b/scripts/audit_i1a_contemporary_gate_calibration.py
@@ -462,10 +462,13 @@ def run_diagnostic_lifecycle(
     mock_overrides: Optional[Dict[str, Any]] = None,
     exit_on_complete: bool = True
 ) -> Tuple[int, Dict[str, Any]]:
-    # Initialize timestamp and unique run identifier
-    run_timestamp = int(time.time())
-    run_uuid = uuid.uuid4().hex[:8]
-    run_id = f"{run_timestamp}_{os.getpid()}_{run_uuid}"
+    # Initialize timestamp and unique run identifier (supporting deterministic test overrides)
+    if mock_overrides and "deterministic_run_id" in mock_overrides:
+        run_id = str(mock_overrides["deterministic_run_id"])
+    else:
+        run_timestamp = int(time.time())
+        run_uuid = uuid.uuid4().hex[:8]
+        run_id = f"{run_timestamp}_{os.getpid()}_{run_uuid}"
     iso_time_utc = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
     enforced_offline_cond = enforced_offline_condition_arg or "UNKNOWN_OR_UNCONFIRMED_ENVIRONMENT"
 
@@ -1154,12 +1157,15 @@ def run_diagnostic_lifecycle(
             # Fallback to ensure actual process restore is unconditionally attempted
             try:
                 uninstall_network_guards()
-            except Exception:
-                pass
+            except Exception as fb_err:
+                workflow_state["offline_execution_environment"]["fallback_cleanup_error"] = str(fb_err)
 
         # Final Status Determination
         # (SUCCESS strictly requires 0 errors, all integrity checks passed, and network guards cleanly uninstalled)
-        cleanup_succeeded = workflow_state.get("offline_execution_environment", {}).get("network_guards_uninstalled", False)
+        cleanup_succeeded = (
+            workflow_state.get("offline_execution_environment", {}).get("network_guards_uninstalled", False) and
+            "fallback_cleanup_error" not in workflow_state.get("offline_execution_environment", {})
+        )
         if (len(workflow_state["errors"]) == 0 and 
             workflow_state["integrity_checks"].get("all_integrity_passed", False) and 
             cleanup_succeeded):
@@ -1185,11 +1191,14 @@ def run_diagnostic_lifecycle(
                 "error_message": str(write_err)
             })
             print(f"CRITICAL REPORT FAILURE: {write_err}", file=sys.stderr)
-            # Try to emit an unambiguous fallback failure record if primary serialization failed
             try:
-                if report_file is not None:
-                    with open(report_file, "w", encoding="utf-8") as f_fallback:
-                        json.dump(workflow_state, f_fallback, indent=2, default=str)
+                terminal_fail_record = {
+                    "critical_event": "REPORT_SERIALIZATION_FAILED",
+                    "status": "FAILED",
+                    "error": str(write_err),
+                    "target_path": str(report_file) if report_file is not None else None
+                }
+                print(f"CRITICAL: Primary report serialization failed. Terminal record:\n{json.dumps(terminal_fail_record, indent=2)}", file=sys.stderr)
             except Exception:
                 pass
```

---

## 3. Focused Test Suite Diff (`test_audit_i1a_mocked_safeguards.py`)

```diff
--- a/scripts/test_audit_i1a_mocked_safeguards.py
+++ b/scripts/test_audit_i1a_mocked_safeguards.py
@@ -1107,11 +1107,114 @@ def test_18_lifecycle_cleanup_failure_handling():
             assert_network_guards_and_env_restored(snap_net)
 
 # ------------------------------------------------------------------------------
+# Test 19: Synthetic Lifecycle Collision & Sentinel Preservation
+# ------------------------------------------------------------------------------
+def test_19_sentinel_preservation_on_report_collision():
+    test_name = "Test 19: Sentinel Preservation On Report Collision"
+    print(f"\n[{test_name}] Verifying pre-existing sentinel report is preserved byte-identical when collision occurs...")
+    from scripts.audit_i1a_contemporary_gate_calibration import run_diagnostic_lifecycle
+    import scripts.audit_i1a_contemporary_gate_calibration as prod_mod
+
+    snap_net = snapshot_network_and_env()
+
+    with tempfile.TemporaryDirectory() as tmpdir:
+        fixtures = build_synthetic_fixtures(Path(tmpdir))
+
+        # 1. Deterministic run ID and pre-existing sentinel file at expected target path
+        det_run_id = "sentinel_collision_run_12345"
+        runs_dir = fixtures["workspace_dir"] / "TERRA_EDITORIAL_RESTART_V2" / "reviewer_I0_I1a_20261008" / "addendum_01" / "runs" / f"run_{det_run_id}"
+        runs_dir.mkdir(parents=True, exist_ok=True)
+        target_report_file = runs_dir / f"contemporary_distance_diagnostic_{det_run_id}.json"
+
+        sentinel_bytes = b'{"SENTINEL_EVIDENCE": "PRE_EXISTING_AUDIT_REPORT_DO_NOT_OVERWRITE", "bytes_guard": [1, 2, 3, 4]}'
+        target_report_file.write_bytes(sentinel_bytes)
+        sentinel_sha_before = hashlib.sha256(sentinel_bytes).hexdigest()
+
+        spy = {}
+        coll_spy = FakeChromaCollectionSpy(spy)
+        import chromadb
+        orig_client = getattr(chromadb, "PersistentClient", None)
+        chromadb.PersistentClient = lambda path: FakeChromaClientSpy(path, coll_spy)
+
+        import chromadb.utils.embedding_functions as ef_module
+        import chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 as onnx_module
+        orig_ef = getattr(ef_module, "ONNXMiniLM_L6_V2", None)
+        orig_onnx_ef = getattr(onnx_module, "ONNXMiniLM_L6_V2", None)
+        mock_ef_cls = make_mock_onnx_class(fixtures["onnx_cache_dir"])
+        ef_module.ONNXMiniLM_L6_V2 = mock_ef_cls
+        onnx_module.ONNXMiniLM_L6_V2 = mock_ef_cls
+
+        try:
+            exit_code, state = run_diagnostic_lifecycle(
+                workspace_root_arg=str(fixtures["workspace_dir"]),
+                onnx_cache_dir_arg=str(fixtures["onnx_cache_dir"]),
+                expected_manifests=fixtures["expected_manifests"],
+                mock_overrides={
+                    "allow_mock_ef": True,
+                    "deterministic_run_id": det_run_id
+                },
+                exit_on_complete=False
+            )
+
+            # 1. Assert exit code is 1 (failure due to report serialization error)
+            assert exit_code == 1, f"Expected exit code 1 on report collision, got {exit_code}"
+
+            # 2. Assert in-memory status is FAILED
+            assert state["status"] == "FAILED", f"Expected state['status'] == 'FAILED', got {state['status']}"
+
+            # 3. Assert ReportSerializationError recorded in state['errors']
+            report_errors = [e for e in state.get("errors", []) if e.get("error_type") == "ReportSerializationError"]
+            assert len(report_errors) == 1, f"Expected 1 ReportSerializationError, got: {state.get('errors')}"
+            assert any(term in report_errors[0]["error_message"] for term in ["File exists", "FileExistsError", "already exists"])
+
+            # 4. Critical Invariant: Verify sentinel file on disk was NOT truncated or overwritten
+            disk_bytes_after = target_report_file.read_bytes()
+            assert disk_bytes_after == sentinel_bytes, "CRITICAL ERROR: Sentinel file was altered or overwritten on collision!"
+            sentinel_sha_after = hashlib.sha256(disk_bytes_after).hexdigest()
+            assert sentinel_sha_after == sentinel_sha_before, f"Sentinel SHA changed: {sentinel_sha_after} != {sentinel_sha_before}"
+
+            # 5. Verify no rogue or fallback report file created in runs_dir
+            all_reports = list(runs_dir.glob("*.json"))
+            assert len(all_reports) == 1, f"Expected only the sentinel report in runs_dir, found: {all_reports}"
+
+            # 6. Verify rejected paths produce zero filesystem fallback reports
+            with tempfile.TemporaryDirectory() as rej_tmpdir:
+                rej_ws = Path(rej_tmpdir) / "workspace"
+                rej_ws.mkdir()
+                orig_check_iso = prod_mod.check_path_isolation
+                prod_mod.check_path_isolation = lambda *args, **kwargs: (_ for _ in ()).throw(prod_mod.AuditSecurityError("Simulated path rejection"))
+                try:
+                    rej_exit, rej_state = run_diagnostic_lifecycle(
+                        workspace_root_arg=str(rej_ws),
+                        exit_on_complete=False
+                    )
+                    assert rej_exit == 1
+                    assert rej_state["status"] == "FAILED"
+                    rej_json = list(Path(rej_tmpdir).rglob("*.json"))
+                    assert len(rej_json) == 0, f"Expected zero reports on disk for rejected paths, found: {rej_json}"
+                finally:
+                    prod_mod.check_path_isolation = orig_check_iso
+
+            # 7. Verify network guards and environment were cleanly restored
+            assert_network_guards_and_env_restored(snap_net)
+
+            record_test(test_name, "PASS", "(sentinel preserved 100% byte-identical; exit 1, status FAILED, zero overwrite; rejected paths produce zero fallback)")
+        finally:
+            prod_mod.uninstall_network_guards()
+            if orig_client:
+                chromadb.PersistentClient = orig_client
+            if orig_ef:
+                ef_module.ONNXMiniLM_L6_V2 = orig_ef
+            if orig_onnx_ef:
+                onnx_module.ONNXMiniLM_L6_V2 = orig_onnx_ef
+            assert_network_guards_and_env_restored(snap_net)
+
+# ------------------------------------------------------------------------------
 # Test Runner
 # ------------------------------------------------------------------------------
 def run_all_tests():
     print("=" * 80)
-    print("EXECUTING FULLY ISOLATED SYNTHETIC LIFECYCLE TEST SUITE (CODEX-0017 / CODEX-0018 / CODEX-0019)")
+    print("EXECUTING FULLY ISOLATED SYNTHETIC LIFECYCLE TEST SUITE (CODEX-0017 / CODEX-0018 / CODEX-0019 / CODEX-0020)")
     print("Status: 100% Synthetic Workspaces, Zero Inference, Zero Production DB Touches")
     print("=" * 80)
 
@@ -1133,6 +1236,7 @@ def run_all_tests():
     test_16_unified_result_validator()
     test_17_impostor_embedding_function_rejection()
     test_18_lifecycle_cleanup_failure_handling()
+    test_19_sentinel_preservation_on_report_collision()
 
     print("\n" + "=" * 80)
     print(f"TEST SUITE SUMMARY: {TEST_RESULTS['passed']} PASSED, {TEST_RESULTS['failed']} FAILED, {TEST_RESULTS['skipped']} SKIPPED (TOTAL: {len(TEST_RESULTS['records'])})")
```

---

## 4. Immutable Artifact Hashes and Checkpoints

All current files and their byte-preserved checkpoints are accounted for:

| Role | Working Path / Checkpoint Path | SHA-256 Hash |
| :--- | :--- | :--- |
| **Diagnostic Script** | `scripts/audit_i1a_contemporary_gate_calibration.py` | `7cd926beca6e819f185d2759dafab6ce528abfc87a8451828de88fd2f8ebc41f` |
| **Diagnostic Checkpoint** | `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/audit_i1a_contemporary_gate_calibration_checkpoint_7cd926.py` | `7cd926beca6e819f185d2759dafab6ce528abfc87a8451828de88fd2f8ebc41f` |
| **Synthetic Test Suite** | `scripts/test_audit_i1a_mocked_safeguards.py` | `6b6577f160f0953ff540c5417574ea1f83cf083152f2396fdb0b5ad67abc7bfd` |
| **Test Checkpoint** | `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_audit_i1a_mocked_safeguards_checkpoint_6b6577.py` | `6b6577f160f0953ff540c5417574ea1f83cf083152f2396fdb0b5ad67abc7bfd` |
| **Full Synthetic Log** | `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_audit_i1a_synthetic_lifecycle_log.txt` | `1d8f2485445e241b50bfb903c5ea5872735437b583c4746c0a6628aee14befa2` |
| **Prior Diagnostic Checkpoint** | `.../evidence/audit_i1a_contemporary_gate_calibration_checkpoint_d1a603.py` | `d1a603b1e5bcdcb4e9349869d244cb261d33f48ed6aca01e2c823152b487d0f0` |
| **Prior Test Checkpoint** | `.../evidence/test_audit_i1a_mocked_safeguards_checkpoint_9bd30b.py` | `9bd30ba37473c4cf807d6a102957800232efdd8690d7be3301a827258de0ef0a` |
| **Original Vector Store** | `dataset_20k_cap/vector_db_20k/chroma.sqlite3` | `3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6` *(Verified Invariant)* |

---

## 5. Synthetic Test Suite Execution Summary (19 Tests)

```text
================================================================================
EXECUTING FULLY ISOLATED SYNTHETIC LIFECYCLE TEST SUITE (CODEX-0017 / CODEX-0018 / CODEX-0019 / CODEX-0020)
Status: 100% Synthetic Workspaces, Zero Inference, Zero Production DB Touches
================================================================================

[Test 1: Import Purity] Verifying that importing module has zero network side-effects...
  PASS: Test 1: Import Purity (socket and urllib unpatched on import)

[Test 2: Scoped Network Guards & Restoration] Testing fail-closed network blockers and clean restoration...
  PASS: Test 2: Scoped Network Guards & Restoration (fail-closed negative controls passed; callables and env cleanly restored)

[Test 3: Pre-Resolution Symlink Rejection] Testing pre-resolution symlink and reparse point checks...
  SKIP: Test 3: Pre-Resolution Symlink Rejection (platform requires elevated privileges to create symlinks)

[Test 4: Real ONNX _download Route Negative Control] Testing real ONNX downloader fails closed under active guards...
  PASS: Test 4: Real ONNX _download Route Negative Control (real ONNX download route trapped and aborted)

[Test 5: Synthetic Lifecycle Success] Running end-to-end production lifecycle on synthetic fixtures...
  PASS: Test 5: Synthetic Lifecycle Success (exit 0, status SUCCESS, guards and env strictly restored, zero leaks)

[Test 6: Lifecycle Copy Failure Handling] Testing production lifecycle handling when snapshot copy fails...
  PASS: Test 6: Lifecycle Copy Failure Handling (exit 1, status FAILED, assets preserved, guards restored)

[Test 7: Lifecycle Query Failure Handling] Testing production lifecycle handling when collection query fails...
  PASS: Test 7: Lifecycle Query Failure Handling (exit 1, status FAILED, assets preserved, guards restored)

[Test 8: Lifecycle Source Mutation Handling] Testing production lifecycle handling when source DB mutates during copy...
  PASS: Test 8: Lifecycle Source Mutation Handling (exit 1, status FAILED, error logged, guards restored)

[Test 9: Lifecycle Final Asset Hash Mismatch] Testing production lifecycle handling when source asset hash mutates...
  PASS: Test 9: Lifecycle Final Asset Hash Mismatch (exit 1, status FAILED, error logged, guards restored)

[Test 10: Lifecycle Report Serialization Failure] Testing production lifecycle handling when report serialization fails...
  PASS: Test 10: Lifecycle Report Serialization Failure (exit 1, status FAILED, guards restored)

[Test 11: Report Write & Readback Unit Test] Testing write_and_verify_report atomic write and read-back...
  PASS: Test 11: Report Write & Readback Unit Test (atomic write, read-back verification, and error traps validated)

[Test 12: Equal-Size Cache Corruption Handling] Testing preflight rejection when ONNX cache asset has identical size but corrupted SHA256...
  PASS: Test 12: Equal-Size Cache Corruption Handling (corrupted cache asset caught in preflight; exit 1, status FAILED)

[Test 13: Early Path Failure Safe Finalization] Testing safe finalization when preflight fails before variables are initialized...
  PASS: Test 13: Early Path Failure Safe Finalization (missing benchmark caught in preflight; exit 1, status FAILED, zero UnboundLocalErrors)

[Test 14: Strict Saved-Grid Validation] Testing strict validation of saved budget and gate summary schema...
  PASS: Test 14: Strict Saved-Grid Validation (all structural and type corruptions caught)

[Test 15: Granular Concordance Classification & Metric Deltas] Testing metric delta calculations and concordance categorization...
  PASS: Test 15: Granular Concordance Classification & Metric Deltas (all concordance and delta categories validated)

[Test 16: Unified Result Distance Validator] Testing result distance validation, clamping, and error thresholds...
  PASS: Test 16: Unified Result Distance Validator (all distance boundaries and validation rules confirmed)

[Test 17: Impostor Embedding Function Rejection] Verifying rejection when collection._embedding_function is an arbitrary impostor named 'default'...
  PASS: Test 17: Impostor Embedding Function Rejection (arbitrary impostor named 'default' rejected by class check)

[Test 18: Lifecycle Cleanup Failure Handling] Verifying cleanup failure results in status=FAILED, exit_code=1, and on-disk FAILED report...
  PASS: Test 18: Lifecycle Cleanup Failure Handling (cleanup failure captured: status=FAILED, exit_code=1, disk report=FAILED)

[Test 19: Sentinel Preservation On Report Collision] Verifying pre-existing sentinel report is preserved byte-identical when collision occurs...
  PASS: Test 19: Sentinel Preservation On Report Collision (sentinel preserved 100% byte-identical; exit 1, status FAILED, zero overwrite; rejected paths produce zero fallback)

================================================================================
TEST SUITE SUMMARY: 18 PASSED, 0 FAILED, 1 SKIPPED (TOTAL: 19)
================================================================================
```

---

## 6. Readiness and Acknowledgment of Next Steps

Antigravity confirms:
1. The exclusive-creation safeguard is absolute: exclusive collisions or write failures emit terminal stderr diagnostics and exit code `1`; pre-existing audit evidence files remain bit-identical.
2. Rejected paths trigger no fallback report writes.
3. Fallback cleanup exceptions are captured as explicit errors rather than swallowed.
4. **The diagnostic run remains unapproved.** No live inference, no vector database connection, and no manuscript edits will occur until explicit user instructions and Layer 1 offline arrangements are approved.
