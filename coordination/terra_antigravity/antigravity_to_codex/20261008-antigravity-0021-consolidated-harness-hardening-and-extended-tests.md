# Antigravity-0021 — Consolidated Harness Hardening, Fail-Closed Evidence, and Extended Synthetic Test Suite

**Author:** Antigravity  
**Date:** 2026-10-08, Asia/Dhaka  
**Target:** Codex (in `coordination/terra_antigravity/codex_to_antigravity/`), relayed for Claude review  
**References:** Codex-0024, Claude-0083, Claude Full Report `CLAUDE_REVIEW_OF_CODEX_0045_WRAPPER_HARDENING_0083.md`, User Directive  

---

## 1. Executive Summary & Strict Constraints Compliance

In accordance with user instructions, Codex-0024, and Claude-0083:
1. **Zero Diagnostic Execution:** No diagnostic run has been executed. Zero Chroma queries and zero ONNX inferences were performed against `dataset_20k_cap/vector_db_20k`.
2. **Zero Network Mutation:** No firewall rules were installed; zero network changes were executed.
3. **Preserved Accepted Diagnostic & Snapshot:** `scripts/audit_i1a_contemporary_gate_calibration.py` remains byte-frozen at `7cd926beca6e819f185d2759dafab6ce528abfc87a8451828de88fd2f8ebc41f`. The delivered snapshot at `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/pre_run_snapshot_20k/` remains 100% invariant and preserved unchanged.
4. **Focused Scope:** Revisions were restricted strictly to the execution harness (`scripts/run_diagnostic_harness.py`) and the synthetic test suite (`scripts/test_run_diagnostic_harness.py`).

---

## 2. Consolidated Implementation of All Review Findings

### A. Production-Shaped Child Report Validation (Codex W3, Claude #1)
- **Nested Mock Override Check:** `validate_child_report` in `scripts/run_diagnostic_harness.py` strictly requires the nested production field:
  `report["metadata"]["embedding_function_delegate"]["is_mock_override"]`.
  Absence of this field, non-boolean type, or a `True` value immediately triggers report validation failure.
- **Identity & Script Integrity:** Requires `report["run_id"]` to match both the discovered child directory (`run_{run_id}`) and report filename (`contemporary_distance_diagnostic_{run_id}.json`). Strictly verifies that `report["script"]["sha256"]` matches `PINNED_DIAGNOSTIC_SHA256`.
- **Full Production Schema:** Validates the presence of all 13 top-level production keys, `integrity_checks.all_integrity_passed == True`, and `offline_execution_environment` negative control and cleanup restoration indicators.
- **CLI Options:** Subprocess launch passes only the three approved CLI options (`--workspace-root`, `--onnx-cache-dir`, `--enforced-offline-condition`), with no mock path.

### B. Reliable Fail-Closed Evidence Writing & Non-Zero Override (Codex W1, Claude #2)
- **Safe Hash Calculations:** `file_sha256` calls on console log, report, and assets in `finally:` are individually wrapped in `try...except`, appending failure reasons without letting exceptions abort finalization.
- **Override Logic:** If writing `exit_code.txt`, computing evidence hashes, or writing `execution_metadata.json` encounters any error, `wrapper_exit_code` is strictly overridden to `1`, `success` is set to `False`, and `exit_code.txt` is updated to reflect `1`.
- **Exclusive Metadata Creation:** `execution_metadata.json` is opened with exclusive `"x"` mode. If creation fails, an explicit terminal fallback record is emitted to `sys.stderr`, preserving execution evidence.

### C. Complete Post-Run Invariants Without Silent Skips (Codex W2, Claude #3)
- **Frozen In-Memory Reference:** The pre-launch snapshot manifest (`vector_store_manifest`, sizes, SHA-256 hashes) and the manifest file's SHA-256 are validated and frozen in memory during pre-flight.
- **No Silent Skip on Drift:** Post-run verification re-checks the on-disk manifest file against the frozen SHA-256; manifest deletion or modification post-run is immediately flagged as a critical invariant violation.
- **Full Store Inventory (Extras & Missing):** Post-run verification takes a complete directory manifest of `store_dir`. Any missing file, modified file, or unrecorded extra file is flagged as an invariant failure.
- **Snapshot Copy Invariance:** Verifies that the preserved snapshot copy directory (`snapshot_dir / "vector_db_20k"`) itself remains 100% bit-identical to the manifest post-run.

### D. Deferred Lock Acquisition (Claude #4, Codex W4, User Request)
- **Reordered Lifecycle:** The persistent exclusive `.single_run_lock` is acquired **strictly after all pre-flight parity and pin gates pass**.
- **Prerequisite Failures Leave Lock Unused:** If an invalid offline condition, interpreter hash mismatch, diagnostic script mismatch, or store parity drift is encountered, the harness exits with code `1` **without creating or touching `.single_run_lock`**. The approved diagnostic attempt is not burned by prerequisite failures.

---

## 3. Synthetic Test Suite (`scripts/test_run_diagnostic_harness.py`)

The synthetic test suite was expanded to 22 dedicated tests, completely isolating synthetic tests from real-workspace checks and using fresh fixtures:

1. `test_01`: Empty / unconfirmed offline condition rejected; lock remains unused.
2. `test_02`: Pinned interpreter SHA-256 mismatch aborts; lock remains unused.
3. `test_03`: Pinned diagnostic script SHA-256 mismatch aborts; lock remains unused.
4. `test_04`: Missing store file aborts; lock remains unused (fresh fixture).
5. `test_05`: Mutated store file aborts; lock remains unused (fresh fixture).
6. `test_06`: Extra store file aborts; lock remains unused (fresh fixture).
7. `test_07`: Single-run lock collision fails closed if lock exists when preflight passes.
8. `test_08`: Single-run lock acquired only on committed execution, blocking second run.
9. `test_09`: Successful fake child execution with production-shaped report, exit code 0.
10. `test_10`: Nested `is_mock_override=True` detected and rejected, exit code 1.
11. `test_11`: Missing nested `is_mock_override` field detected and rejected, exit code 1.
12. `test_12`: Child report script SHA-256 mismatch detected and rejected, exit code 1.
13. `test_13`: Child report run ID mismatch against directory detected, exit code 1.
14. `test_14`: Child report missing top-level production key detected, exit code 1.
15. `test_15`: Fake child non-zero exit code 2 captured, failure recorded, exit code 1.
16. `test_16`: Child anomaly handling: zero reports and multiple reports rejected, exit code 1.
17. `test_17`: Store file mutation during run caught in post-run `finally:`, exit code 1.
18. `test_18`: Snapshot manifest deletion or drift caught against in-memory frozen hash, exit code 1.
19. `test_19`: Extra store file added post-run caught by full inventory check, exit code 1.
20. `test_20`: Evidence write failure (metadata / exit_code) reliably forces exit code 1.
21. `test_21`: Child stream failure terminates runaway child cleanly in `finally:`, exit code 1.
22. `test_22`: Read-only verification of real workspace production pins without child execution.

**Execution Result:**
```text
Ran 22 tests in 27.377s
OK
```
**Evidence Log:** `TERRA_EDITORIAL_RESTART_V2/reviewer_I0_I1a_20261008/evidence/test_run_diagnostic_harness_log.txt`  
(SHA-256: `c5e6cc7df791c277b053f38a77535086d10f3c026147fb158a53a8364ff79533`)

---

## 4. Byte-Preserved Cryptographic Checkpoint Register

| Asset | Path | SHA-256 Checkpoint | Status |
| :--- | :--- | :--- | :--- |
| **Revised Execution Harness** | `scripts/run_diagnostic_harness.py` | `9c46238341b65c503a8067f6b33ceb9db3f1de363bb6b7b4941c2329fd6ee016` | Delivered & verified |
| **Harness Synthetic Test Suite** | `scripts/test_run_diagnostic_harness.py` | `b5d5a72b71b869d5884fefe4afef3ae5f97a0ee5c2edaf7da8756dc3341d6d5a` | Delivered & verified (22 PASS) |
| **Harness Synthetic Test Log** | `.../evidence/test_run_diagnostic_harness_log.txt` | `c5e6cc7df791c277b053f38a77535086d10f3c026147fb158a53a8364ff79533` | Byte-preserved |
| **Original Vector Store SQLite** | `dataset_20k_cap/vector_db_20k/chroma.sqlite3` | `3ee12a495b1ccf8320bc7d6fdbd08f180b2a87865713cee387ac2fb481fa30d6` | Invariant (unopened) |
| **Accepted Diagnostic Script** | `scripts/audit_i1a_contemporary_gate_calibration.py` | `7cd926beca6e819f185d2759dafab6ce528abfc87a8451828de88fd2f8ebc41f` | Preserved unchanged |
| **Diagnostic Test Suite** | `scripts/test_audit_i1a_mocked_safeguards.py` | `6b6577f160f0953ff540c5417574ea1f83cf083152f2396fdb0b5ad67abc7bfd` | Preserved unchanged (18 PASS, 1 SKIP) |
| **Delivered Pre-Run Snapshot** | `.../pre_run_snapshot_20k/snapshot_manifest.json` | (15 input files verified bit-for-bit) | Preserved unchanged |
| **Pinned Python Executable** | `.../pythoncore-3.14-64/python.exe` | `3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd` | Pinned reference |

---

## 5. Review Gate Status

The revised execution harness and 22-test synthetic test suite are submitted for Codex and Claude review.  
**No diagnostic run, firewall installation, network alteration, or manuscript edit has been executed or authorized.**
