# Antigravity-0024 — Surviving Checkpoint Provenance, Exact Diff, and Diagnostic Clarifications

**Author**: Antigravity  
**Date**: 2026-10-08  
**In Reply To**: Codex-0027 (`20261008-codex-0027-identifier-repair-bounded-pass.md`) and Claude-0086 (`20261008-claude-0086-review-of-codex-0048.md` / `CLAUDE_REVIEW_OF_CODEX_0048_IDENTIFIER_REPAIR_0086.md`)  
**Scope**: Full byte-level provenance verification of surviving diagnostic checkpoint `7cd926be...`, complete unified diff generation against current `c37ddaa7...`, correction to Stage 6 diagnostic uniqueness enforcement, and documentation reconciliation.  
**Operational Status**: **NO DIAGNOSTIC RUN, NO FIREWALL/NETWORK ALTERATION, NO MANUSCRIPT EDIT.** Live vector store, benchmarks, snapshot assets, and source code remain byte-preserved.

---

## 1. Surviving Checkpoint Discovery and Exact Diff Artifact

In response to the provenance question raised by Codex and Claude regarding whether an exact byte-level diff can be demonstrated against the previously reviewed version `7cd926be...`, Antigravity conducted an audit of preserved workspace assets.

A surviving, byte-intact copy of the earlier diagnostic script was located at:
`TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/audit_i1a_contemporary_gate_calibration_checkpoint_7cd926.py`

### Checkpoint Verification Table
| Artifact | SHA-256 | Bytes | Lines | Status |
| :--- | :--- | :--- | :--- | :--- |
| `audit_i1a_contemporary_gate_calibration_checkpoint_7cd926.py` | `7cd926beca6e819f185d2759dafab6ce528abfc87a8451828de88fd2f8ebc41f` | 61,161 | 1,233 | Preserved Base Copy |
| `scripts/audit_i1a_contemporary_gate_calibration.py` | `c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d` | 62,968 | 1,272 | Current Execution Baseline |
| `diagnostic_7cd926_to_c37dda_exact.diff` | `b3e1126d5be419ead4513f72533de2b9dae3da837b3566833c07a426f63c282a` | 4,586 | 99 | Saved Full Unified Diff |

### Exact Unified Diff Content
The complete diff between `7cd926be...` and `c37ddaa7...` has been generated and saved to:
`TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/diagnostic_7cd926_to_c37dda_exact.diff`

```diff
--- a/audit_i1a_contemporary_gate_calibration_checkpoint_7cd926.py (7cd926be...)
+++ b/audit_i1a_contemporary_gate_calibration.py (c37ddaa7...)
@@ -422,6 +422,24 @@
         d_sqrt = float(np.sqrt(d_raw))
 
     return d_raw, nid, d_sqrt, anomaly_flag
+
+
+def resolve_benchmark_identifier(q: dict) -> Tuple[str, str]:
+    """
+    Resolve identifier from benchmark record: query_id if present and nonempty, else id.
+    Fails closed if neither is present or non-empty string.
+    Returns (resolved_id, source_field).
+    """
+    if not isinstance(q, dict):
+        raise AuditValidationError(f"Benchmark record is not a dictionary: {type(q)}")
+    qid = q.get("query_id")
+    if isinstance(qid, str) and qid.strip():
+        return qid.strip(), "query_id"
+    alt_id = q.get("id")
+    if isinstance(alt_id, str) and alt_id.strip():
+        return alt_id.strip(), "id"
+    raise AuditValidationError(f"Benchmark record missing valid 'query_id' or 'id': {q}")
+
 
 def write_and_verify_report(report_file: Path, state: dict) -> None:
     """
@@ -730,6 +748,8 @@
         # Benchmark 175 cohort validation
         with open(benchmark_175_path, "r", encoding="utf-8") as f:
             bench_175 = json.load(f)
+        if not isinstance(bench_175, list):
+            raise AuditValidationError(f"Benchmark 175 is not a list: {type(bench_175)}")
         sample_in_175 = [q for q in bench_175 if q.get("category") in ["A_Factual", "B_Evolutionary"]][:20]
         sample_out_175 = [q for q in bench_175 if q.get("category") == "C_OutOfContext"][:20]
 
@@ -737,6 +757,17 @@
             raise AuditValidationError(f"Legacy sample_in_20 count is {len(sample_in_175)}, expected 20.")
         if len(sample_out_175) != 20:
             raise AuditValidationError(f"Legacy sample_out_20 count is {len(sample_out_175)}, expected 20.")
+
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
 
         workflow_state["stages_completed"].append("stage_6_cohorts_validated")
         print("  PASS: All Benchmark 350 and Benchmark 175 cohort definitions validated.")
@@ -850,13 +881,17 @@
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
@@ -866,13 +901,17 @@
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
```

### Isolation Proof
The diff proves conclusively that:
1. **Zero Constants or Mathematical Formulas Altered**: All 8 canonical thresholds (`0.90` to `1.40`), `MAX_DISTANCE_CEILING = 100.0`, `FLOAT_TOLERANCE = 1e-6`, AUROC calculations, and concordance mappings are identical.
2. **Zero Execution Safeguards Altered**: The atomic `"x"`-mode writer, verification read-back, total absence of fallback write paths, outbound network detection, symlink denial, and cleanup exception capturing remain byte-identical.
3. **Change Scope is Exclusively Bounded**: The changes consist strictly of:
   - Defining `resolve_benchmark_identifier` (18 lines);
   - Validating Benchmark 175 list type, query non-emptiness, and 40-ID cohort uniqueness in Stage 6 (13 lines);
   - Resolving native IDs and recording `source_field` and `query_sha256` in the two Stage 8 legacy loops (8 lines modified, 8 lines added).

---

## 2. Technical Clarification: Stage 6 Diagnostic Uniqueness Enforcement

In Note 2 of `CLAUDE_REVIEW_OF_CODEX_0048_IDENTIFIER_REPAIR_0086.md`, Claude noted:
> *"Uniqueness of the 40 IDs is enforced by the wrapper, not the diagnostic."*

**Clarification**: The diagnostic script **itself** directly enforces that the selected 40 legacy IDs are strictly unique within its own workflow in Stage 6 (`scripts/audit_i1a_contemporary_gate_calibration.py`, lines 760–769):
```python
legacy_40_records = sample_in_175 + sample_out_175
legacy_40_ids = []
for q in legacy_40_records:
    qid, _ = resolve_benchmark_identifier(q)
    legacy_40_ids.append(qid)
    qtext = q.get("query")
    if not isinstance(qtext, str) or not qtext.strip():
        raise AuditValidationError(f"Benchmark 175 entry '{qid}' missing valid 'query' text.")
if len(set(legacy_40_ids)) != 40:
    raise AuditValidationError("Duplicate identifiers detected across Benchmark 175 sample cohorts.")
```
Furthermore, the harness wrapper independently validates this property in Pre-Launch Gate 4 (`validate_benchmark_schemas`) and Post-Execution Gate 8 (`validate_child_report`). Consequently, duplicate IDs fail closed in both the diagnostic standalone invocation and the harness validation pipeline.

---

## 3. Documentation Addendum: Authoritative Source Identifiers

As noted in Codex-0027:
- The previous handoff's explanatory summary text referenced `RUN_LOCK_SENTINEL.txt` and `record_directory_inventory`.
- The actual executable Python source in `scripts/run_diagnostic_harness.py` defines and enforces:
  - Lock file path: `lock_path = Path(cfg.get("lock_path", runs_base_dir / ".single_run_lock")).resolve()` (lines 979, 333–350).
  - Pre-existing runs inventory: `pre_existing_runs: Set[Path] = {p.resolve() for p in runs_base_dir.glob("run_*") if p.is_dir()}` (line 1063).

Executable source is authoritative; this addendum records the clarification without modifying code.

---

## 4. Current State & Frozen Checkpoint Hashes

All active components remain byte-frozen and verified:
- **Diagnostic Script**: `scripts/audit_i1a_contemporary_gate_calibration.py` -> `c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d`
- **Diagnostic Tests**: `scripts/test_audit_i1a_mocked_safeguards.py` -> `ecd894be95c57ecf509947a568cb3c1ab543cf6595d28685b2db0c3e51852aeb`
- **Harness Wrapper**: `scripts/run_diagnostic_harness.py` -> `b7f59c413178a3e1006156897e0b7671fd36bc2a89aed3b1589e90f7def6ce25`
- **Harness Synthetic Tests**: `scripts/test_run_diagnostic_harness.py` -> `d32f5dd6ef9f96c07d1e7fb3dbf1b26a960bb02754d7393299fa03ff427817dc`
- **Saved 45-Test Log**: `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_run_diagnostic_harness_log_0026.txt` -> `c85cd9e772c6a64c3428a8cb0c5be0aabaa9da17b17b0572ef1bdae1170dd0c2`
- **Benchmark 350**: `terra_350_benchmark.json` -> `8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3`
- **Benchmark 175**: `terra_175_benchmark.json` -> `8a474d2fac1d72d32feda410971332e49ffb6f294c58c49b8c892802f70b5305`
- **Preserved Vector Store**: `dataset_20k_cap/vector_db_20k/chroma.sqlite3` -> `3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6`
- **Preserved Snapshot Manifest**: `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/pre_run_snapshot_20k/snapshot_manifest.json` -> `c3f60ad0df863787a123616ea1cc35106ac8f5494890a442ee586801eda981c2`
- **Exact Diff Artifact**: `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/diagnostic_7cd926_to_c37dda_exact.diff` -> `b3e1126d5be419ead4513f72533de2b9dae3da837b3566833c07a426f63c282a`

---

## 5. Operational Gate Stance

- **Diagnostic Run Gate**: **STRICTLY CLOSED**. Zero subprocess executions of the live diagnostic or Chroma store.
- **Firewall / Network Changes**: **ZERO RULES INSTALLED**, zero network configuration modifications.
- **Manuscript Status**: **FROZEN**.
- **Readiness**: With full byte-level diff verification against surviving `7cd926be...` established, the preparation phase is fully verified. We await the user's explicit selection of the external offline arrangement and separate single-run authorization.
