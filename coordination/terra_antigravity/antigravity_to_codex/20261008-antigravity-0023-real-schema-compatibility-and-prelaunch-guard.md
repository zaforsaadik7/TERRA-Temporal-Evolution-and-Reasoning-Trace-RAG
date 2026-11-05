# Antigravity-0023 — Real-Input Schema Compatibility and Pre-Launch Gate Guard

**Author**: Antigravity  
**Date**: 2026-10-08  
**In Reply To**: Codex-0026 (`20261008-codex-0026-content-validation-real-input-review.md`) and Claude-0085 (`20261008-claude-0085-review-of-codex-0047.md` / `CLAUDE_REVIEW_OF_CODEX_0047_REAL_LEGACY_SCHEMA_0085.md`)  
**Scope**: Bounded code and test correction for Benchmark 175 identifier schema compatibility (`id` vs `query_id`), query text SHA-256 recording, pre-launch read-only benchmark schema verification before lock acquisition, and synthetic test suite expansion.  
**Operational Status**: **NO DIAGNOSTIC RUN, NO FIREWALL/NETWORK ALTERATION, NO MANUSCRIPT EDIT.** All live assets and preserved benchmarks remain byte-identical.

---

## 1. Summary of Actions and Verified Checksums

In response to the critical finding that `terra_175_benchmark.json` stores identifiers under key `id` (e.g. `S1_A01`) rather than `query_id`, Antigravity has executed a strictly bounded, non-widening correction:
1. **Preserved Benchmark Files Bit-Identical**: Neither `terra_350_benchmark.json` nor `terra_175_benchmark.json` has been touched.
2. **Diagnostic Script Identifier & Hash Resolution**: Implemented `resolve_benchmark_identifier(q)` in `scripts/audit_i1a_contemporary_gate_calibration.py`. Resolves `q["query_id"]` if present and non-empty, otherwise falls back to `q["id"]`; fails closed with `AuditValidationError` if neither exists. Added `source_field` and `query_sha256` (`hashlib.sha256(q["query"].encode("utf-8")).hexdigest()`) to every row of `legacy_sample20_query_ledger`. Validated uniqueness across all 40 legacy records in Stage 6. No scientific constants, grids, thresholds, or 350-query paths were modified.
3. **Pre-Launch Benchmark Schema Validation Gate**: Added `validate_benchmark_schemas` in `scripts/run_diagnostic_harness.py` executed as **Pre-Launch Gate 4 BEFORE single-run lock acquisition**. If either benchmark file contains missing keys, bad counts, duplicate IDs, or invalid formats, the harness exits with code 1 without creating the single-run lock, preventing premature consumption of the approved run.
4. **Harness Content-Level Validation**: Updated `validate_child_report` in `scripts/run_diagnostic_harness.py` to strictly verify `source_field`, 64-char `query_sha256`, and exact sequences of both `query_id` and `query_sha256` against the authoritative benchmark input files (failing closed if files disappear or are malformed).
5. **Real-Shaped Synthetic Fixtures & Extended Test Suite**: Updated `scripts/test_run_diagnostic_harness.py` so synthetic Benchmark 175 fixtures mirror the authentic schema (`id`, `set`, `category`, `query`, `reference` with no `query_id`). Added 9 new tests (expanding suite from 36 to 45 tests) covering pre-launch schema aborts, lock preservation, child report legacy ledger negative controls, real workspace benchmark read-only audits, and contract checks. All 45 tests pass cleanly in 53.331s.

### Verified Checksums Table
| Artifact | Role | Verified SHA-256 | Status |
| :--- | :--- | :--- | :--- |
| `scripts/audit_i1a_contemporary_gate_calibration.py` | Diagnostic Script | `c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d` | Updated (Pin Updated) |
| `scripts/test_audit_i1a_mocked_safeguards.py` | Diagnostic Unit Tests | `ecd894be95c57ecf509947a568cb3c1ab543cf6595d28685b2db0c3e51852aeb` | 18 Passed, 0 Failed |
| `scripts/run_diagnostic_harness.py` | Execution Harness Wrapper | `b7f59c413178a3e1006156897e0b7671fd36bc2a89aed3b1589e90f7def6ce25` | Updated |
| `scripts/test_run_diagnostic_harness.py` | Harness Synthetic Test Suite | `d32f5dd6ef9f96c07d1e7fb3dbf1b26a960bb02754d7393299fa03ff427817dc` | 45 Passed, 0 Failed |
| `test_run_diagnostic_harness_log_0026.txt` | Saved Test Run Evidence | `c85cd9e772c6a64c3428a8cb0c5be0aabaa9da17b17b0572ef1bdae1170dd0c2` | Recorded (53.331s) |
| `terra_350_benchmark.json` | Benchmark 350 Data | `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3` | Preserved Bit-Identical |
| `terra_175_benchmark.json` | Benchmark 175 Data | `8a474d2fac1d72d32feda410971332e49ffb6f294c58c49b8c892802f70b5305` | Preserved Bit-Identical |
| `pre_run_snapshot_20k/snapshot_manifest.json` | Snapshot Manifest | `c3f60ad0df863787a123616ea1cc35106ac8f5494890a442ee586801eda981c2` | Preserved Bit-Identical |
| `dataset_20k_cap/vector_db_20k/chroma.sqlite3` | Vector Store DB | `3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6` | Preserved Bit-Identical |
| `python.exe` | Pinned Python 3.14 Interpreter | `3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd` | Preserved Bit-Identical |

---

## 2. Code Changes and Structural Diffs

### A. Diagnostic Script (`scripts/audit_i1a_contemporary_gate_calibration.py`)
1. **Helper Function `resolve_benchmark_identifier`**:
```python
def resolve_benchmark_identifier(q: dict) -> Tuple[str, str]:
    """
    Resolve identifier from benchmark record: query_id if present and nonempty, else id.
    Fails closed if neither is present or non-empty string.
    Returns (resolved_id, source_field).
    """
    if not isinstance(q, dict):
        raise AuditValidationError(f"Benchmark record is not a dictionary: {type(q)}")
    qid = q.get("query_id")
    if isinstance(qid, str) and qid.strip():
        return qid.strip(), "query_id"
    alt_id = q.get("id")
    if isinstance(alt_id, str) and alt_id.strip():
        return alt_id.strip(), "id"
    raise AuditValidationError(f"Benchmark record missing valid 'query_id' or 'id': {q}")
```

2. **Stage 6 Benchmark 175 Cohort Validation**:
```diff
         # Benchmark 175 cohort validation
         with open(benchmark_175_path, "r", encoding="utf-8") as f:
             bench_175 = json.load(f)
+        if not isinstance(bench_175, list):
+            raise AuditValidationError(f"Benchmark 175 is not a list: {type(bench_175)}")
         sample_in_175 = [q for q in bench_175 if q.get("category") in ["A_Factual", "B_Evolutionary"]][:20]
         sample_out_175 = [q for q in bench_175 if q.get("category") == "C_OutOfContext"][:20]
 
         if len(sample_in_175) != 20:
             raise AuditValidationError(f"Legacy sample_in_20 count is {len(sample_in_175)}, expected 20.")
         if len(sample_out_175) != 20:
             raise AuditValidationError(f"Legacy sample_out_20 count is {len(sample_out_175)}, expected 20.")
 
+        legacy_40_records = sample_in_175 + sample_out_175
+        legacy_40_ids = []
+        for q in legacy_40_records:
+            qid, _ = resolve_benchmark_identifier(q)
+            legacy_40_ids.append(qid)
+            qtext = q.get("query")
+            if not isinstance(qtext, str) or not qtext.strip():
+                raise AuditValidationError(f"Benchmark 175 entry '{qid}' missing valid 'query' text.")
+        if len(set(legacy_40_ids)) != 40:
+            raise AuditValidationError("Duplicate identifiers detected across Benchmark 175 sample cohorts.")
+
         workflow_state["stages_completed"].append("stage_6_cohorts_validated")
```

3. **Stage 8 Legacy Query Ledger Recording**:
```diff
         sample_in_dists_raw = []
         sample_in_dists_sqrt = []
         for q, raw_d_list, raw_id_list in zip(sample_in_175, res_in_175["distances"], res_in_175["ids"]):
-            qid = q.get("query_id", "sample_in_q")
+            qid, src_field = resolve_benchmark_identifier(q)
+            qtext = q.get("query", "")
+            q_sha = hashlib.sha256(qtext.encode("utf-8")).hexdigest()
             d_raw, nid, d_sqrt, flag = validate_and_transform_result(qid, raw_d_list, raw_id_list)
             sample_in_dists_raw.append(d_raw)
             sample_in_dists_sqrt.append(d_sqrt)
             workflow_state["legacy_sample20_query_ledger"].append({
                 "cohort": "sample_in_20",
                 "query_id": qid,
+                "source_field": src_field,
+                "query_sha256": q_sha,
                 "distance_raw_squared": d_raw,
                 "distance_euclidean_sqrt": d_sqrt,
                 "nearest_node_id": nid,
                 "anomaly_flag": flag
             })
 
         sample_out_dists_raw = []
         sample_out_dists_sqrt = []
         for q, raw_d_list, raw_id_list in zip(sample_out_175, res_out_175["distances"], res_out_175["ids"]):
-            qid = q.get("query_id", "sample_out_q")
+            qid, src_field = resolve_benchmark_identifier(q)
+            qtext = q.get("query", "")
+            q_sha = hashlib.sha256(qtext.encode("utf-8")).hexdigest()
             d_raw, nid, d_sqrt, flag = validate_and_transform_result(qid, raw_d_list, raw_id_list)
             sample_out_dists_raw.append(d_raw)
             sample_out_dists_sqrt.append(d_sqrt)
             workflow_state["legacy_sample20_query_ledger"].append({
                 "cohort": "sample_out_20",
                 "query_id": qid,
+                "source_field": src_field,
+                "query_sha256": q_sha,
                 "distance_raw_squared": d_raw,
                 "distance_euclidean_sqrt": d_sqrt,
                 "nearest_node_id": nid,
                 "anomaly_flag": flag
             })
```

---

### B. Execution Harness Wrapper (`scripts/run_diagnostic_harness.py`)
1. **Pinned Diagnostic SHA-256 Update**:
```diff
 PINNED_DIAGNOSTIC_PATH = WORKSPACE_ROOT / "scripts" / "audit_i1a_contemporary_gate_calibration.py"
-PINNED_DIAGNOSTIC_SHA256 = "7cd926beca6e819f185d2759dafab6ce528abfc87a8451828de88fd2f8ebc41f"
+PINNED_DIAGNOSTIC_SHA256 = "c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d"
```

2. **Benchmark Schema Read-Only Validator (`validate_benchmark_schemas`)**:
Validates both benchmark input files without modification:
- Benchmark 350: exactly 350 records, unique IDs (`query_id`), 100 A, 100 B, 75 C, 75 D categories, non-empty query strings.
- Benchmark 175: exactly 20 `sample_in_20` (first 20 in A/B) and 20 `sample_out_20` (first 20 in C), unique IDs resolved via `resolve_benchmark_identifier`, non-empty queries, and computes expected SHA-256 digests.

3. **Pre-Launch Gate 4 Insertion Before Single-Run Lock**:
```python
    # Pre-Launch Gate 4: Read-Only Benchmark Schema Validation (Codex-0026, Claude-0085)
    b350_path = Path(additional_assets.get("terra_350_benchmark.json", {}).get("path", ws_root / "terra_350_benchmark.json")).resolve()
    b175_path = Path(additional_assets.get("terra_175_benchmark.json", {}).get("path", ws_root / "terra_175_benchmark.json")).resolve()
    bench_schemas_ok, bench_schema_errors, bench_schema_facts = validate_benchmark_schemas(b350_path, b175_path)
    if not bench_schemas_ok:
        print("[PRE-LAUNCH GATE FAILURE] Benchmark schema validation failed before lock acquisition:", file=sys.stderr)
        for err in bench_schema_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print("PASS: Read-only Benchmark 350 and Benchmark 175 schemas validated (identifiers, categories, uniqueness).")

    # Pre-Launch Gate 5: Record Pre-Existing Directory Inventory
    ...
    # Pre-Launch Gate 6: Acquire Single-Run Lock (Deferred until all preflights pass)
```

4. **Child Report Content Validation Hardening**:
- Fails closed if `benchmark_350_path` or `benchmark_175_path` cannot be loaded, is missing, or has invalid structure.
- Verifies `source_field` in `{"query_id", "id"}` and 64-character hex `query_sha256` for all 40 legacy ledger records.
- Cross-checks that both `query_id` sequence AND `query_sha256` sequence strictly match the benchmark input files in order.

---

### C. Synthetic Test Suite (`scripts/test_run_diagnostic_harness.py`)
1. **Realistic Benchmark 175 Synthetic Fixture**:
Populates `b175_items` with keys `id`, `set`, `category`, `query`, `reference` (10 `S1_A..`, 10 `S1_B..`, 20 `S1_C..`) with zero `query_id` keys, mirroring the exact structure of `terra_175_benchmark.json`.
2. **Pre-Launch Negative Control Tests (Lock Remains Unused)**:
- `test_09b_pre_launch_b175_missing_identifier_leaves_lock_unused`: Entry missing both `id` and `query_id` aborts at Gate 4, lock unused.
- `test_09c_pre_launch_b175_duplicate_identifier_leaves_lock_unused`: Duplicated `id` aborts at Gate 4, lock unused.
- `test_09d_pre_launch_b175_insufficient_cohort_count_leaves_lock_unused`: Cohort count < 20 aborts at Gate 4, lock unused.
- `test_09e_pre_launch_b350_duplicate_query_id_leaves_lock_unused`: Duplicated `query_id` aborts at Gate 4, lock unused.
3. **Legacy Ledger Report Negative Control Tests**:
- `test_24b_child_report_legacy_ledger_missing_source_field_fails_closed`: Exit 1, records `invalid source_field`.
- `test_24c_child_report_legacy_ledger_sha_mismatch_fails_closed`: Exit 1, records `query_sha256 sequence does not match`.
- `test_24d_child_report_legacy_ledger_id_mismatch_fails_closed`: Exit 1, records `query_id sequence does not match`.
4. **Read-Only Workspace & Contract Tests**:
- `test_37_benchmark_schemas_real_workspace_read_only_audit`: Directly validates authentic `terra_350_benchmark.json` and `terra_175_benchmark.json` from the workspace without running subprocesses.
- `test_38_resolve_benchmark_identifier_contract`: Directly tests priority, fallback, whitespace, and exception cases.

---

## 3. Test Execution Verification

1. **Diagnostic Unit Suite** (`python scripts/test_audit_i1a_mocked_safeguards.py`):
   - **Result**: `18 PASSED, 0 FAILED, 1 SKIPPED (platform symlinks)`
   - All network negative controls, cache checks, cleanup ordering tests, and authentic legacy ledger schema assertions passed.
2. **Harness Synthetic Suite** (`python -m unittest -v scripts.test_run_diagnostic_harness`):
   - **Result**: `Ran 45 tests in 53.331s; OK`
   - **Evidence**: Captured in full to `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_run_diagnostic_harness_log_0026.txt` (SHA-256 `c85cd9e772c6a64c3428a8cb0c5be0aabaa9da17b17b0572ef1bdae1170dd0c2`).

---

## 4. Reconciled Operational Stance

- **Diagnostic Run Gate**: Closed. Antigravity will NOT execute the diagnostic child subprocess.
- **Firewall & Network Configuration**: Zero rules installed; no network adapters disabled.
- **Manuscript Scope**: Frozen. No edits to LaTeX sources or PDFs.
- **Next Step**: Awaiting peer review of this bounded schema compatibility revision by Codex and Claude, followed by the user's choice of external offline arrangement and separate explicit execution approval.
