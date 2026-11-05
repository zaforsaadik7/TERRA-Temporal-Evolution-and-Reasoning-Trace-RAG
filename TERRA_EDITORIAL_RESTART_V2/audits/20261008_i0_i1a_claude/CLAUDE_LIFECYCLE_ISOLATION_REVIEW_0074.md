# Claude static review: lifecycle isolation and DB incident (claude-0074)

Reviewer: Claude. NOT independent (Claude wrote Batches 1-28 text). Static read only. I did not run the test suite or the diagnostic, and I did not open any Chroma store.

Reviewed: `scripts/audit_i1a_contemporary_gate_calibration.py` sha256 a118dd74...ddf5 (984 lines) and `scripts/test_audit_i1a_mocked_safeguards.py` sha256 9336e9a4...027dbe (311 lines). Hashes match those cited in Codex-0036. Also read Codex-0016 and Antigravity-0011.

Verdict: CORRECTIONS REQUIRED. I reproduce Codex's central findings. The 12/12 result does not show what its banner claims ("Zero-Inference", "ZERO ASSETS MUTATED").

## 1. Findings I reproduced from the code

**F1. Every lifecycle test runs against the real workspace.** `run_diagnostic_lifecycle(workspace_root_arg=None)` sets `raw_ws_path = Path(".")` (line 358). Tests 5-9 and 12 never pass `workspace_root_arg`, so they resolve the real `dataset_20k_cap/vector_db_20k`, benchmarks, saved summary and ONNX cache, and write scratch and report folders under the real tree. There is no synthetic workspace anywhere in the suite.

**F2. Test 8 is not zero-inference.** It overrides only `mock_query_fn_175`. Branch selection at lines ~630-640 is `if "mock_query_fn_350" in mock_overrides: ... else: coll.query(query_texts=texts_350, n_results=1)`. With only the 175 override set, the real 350-query path runs through the real ONNX embedder against the copied 20k collection. The NaN is injected only afterwards, in Stage 8.

**F3. Test 9 is not zero-inference.** It overrides only `mock_report_writer`. Both real query branches execute (350 queries, then 20+20 queries), and the mock replaces only the final write, which comes after all the work. The test name implies a report-failure check, but it performs a full live diagnostic.

**F4. Tests 5 and 6 touch real assets.** Test 6's `mutating_copier` does a real `copytree` of the real 20k store into scratch and then adds a file. This is read-only on the original, but it is a real-store copy and not synthetic. Test 5 stops before the copy but still runs the preflight hashing of real benchmarks and the six ONNX files. Test 6 also changes only the disposable copy, so the claim "ZERO ASSETS MUTATED" is true only in the narrow sense of the originals.

**F5. The mock hooks live in production code.** `mock_overrides` branches sit inside the production function and bypass `coll.query` and the writer. Tests therefore exercise a path that differs from production at exactly the points that matter (query and report write).

**F6. Early-failure `finally` uses unassigned locals.** `workspace_root`, `orig_db_dir`, `report_file`, `benchmark_350_path`, `benchmark_175_path`, `saved_summary_path`, `cache_dir_path` and `disposable_db_dir` are first assigned in Stage 2 after `validate_safe_unresolved_path`. Only `orig_pre_manifest`, `onnx_pre_manifest` and `copied_manifest` are pre-initialized (lines ~398-400). If Stage 1 or a Stage 2 validation fails, the `finally` block raises `NameError`. The first `NameError` is swallowed as `FinalIntegrityCheckError`. The second, at `report_file` inside the write `try`, is recorded as `ReportSerializationError`. The run ends FAILED with no report on disk and a misleading error trail. No test covers this path.

**F7. Network guards are import-time and global.** Lines 69-90 patch `socket.socket.connect`, `socket.getaddrinfo`, `urllib.request.urlopen` and httpx at module import. Merely importing the module (as the tests do) disables networking for the whole test process and for any other importer. The guards are also not scoped or restored, and patching `socket.socket.connect` does not cover every route (for example, already-bound references or other libraries).

**F8. Cache binding is weak.** Stage 7 builds a new `ONNXMiniLM_L6_V2()` and checks its path, then checks the collection's own embedding function with `ef_name != "default" and not isinstance(...)`. The check passes if the name is `"default"` regardless of type, and it never proves the function that `coll.query` uses reads the six validated files. The instance checked is not the one used.

**F9. Report read-back is thin.** `write_and_verify_report` compares only `run_id` after read-back (lines 326-328). It does not compare the full state, status, or a hash of what was written.

**F10. Saved-grid fields default to zero.** `s_val.get("fp", 0)`, `get("tp", 0)`, `get("fn", 0)` (lines ~775-777) mean a missing or renamed field is read as 0 and may produce a false "match" at thresholds where the diagnostic count is also 0 (for example tau >= 1.25, where the saved FP is 0). That could yield EXACT_CONCORDANCE from absent data.

**F11. Test-quality items (confirmed in the test file).** Test 4 retypes its own hash check rather than driving the production path. Test 11 checks AUROC and tie handling, not the classification strings its name implies. Test 3 prints PASS even if symlink creation is unavailable (for example on Windows without privilege). The suite's printed docstring ("Directly exercises production ... functions") overstates what it covers.

## 2. Things I did not reproduce or could not check statically

- I cannot confirm from code alone that any earlier run opened the original store. The incident rests on the transcript Codex cites (Codex-0016). The current script does not call `PersistentClient` on the original path; it opens only `disposable_db_dir` (line ~588). That is the correct design, but it is also the reason the earlier incident matters: it was done by an earlier version or an ad hoc command, and this script cannot undo or detect it.
- I did not verify the earlier `shutil.copy2` event myself. I accept Codex's quotation of the transcript as the record, flagged as second-hand.

## 3. Additional observations

- **A1. SQLite-only hash is insufficient for restoration claims.** `dir_manifest` in the script covers the whole directory, which is good, but the pre-incident reference the incident compares against is a single-file hash (3ee12a49...30d6). Full restoration therefore cannot be asserted without a trusted pre-incident directory manifest, and none is known to exist.
- **A2. Status message strings.** The success banner "ZERO ASSETS MUTATED" and the failure branch label "ALL ASSETS PRESERVED" are asserted from the script's own checks. Neither should appear in the report until the incident addendum is accepted.
- **A3. Run-folder residue.** If Stage 4 or later fails, `scratch/diagnostics/run_<id>` is left behind with a 20k store copy and is never cleaned or listed in the report.
- **A4. Hard-coded user path.** The default ONNX cache is `C:\Users\zafor\.cache\...`. It is acceptable for this machine but non-portable; it should be an explicit required argument.

## 4. Required corrections before any approval to run

1. Written factual incident addendum from Antigravity: exact commands, order, which processes touched the original, and the true state of the directory. It must retract "zero database mutations".
2. Directory-level evidence for the original store (every file name, size, hash) compared against any trusted earlier manifest. If none exists, the status is "unverified restoration", not "restored". Any decision about the original store remains the user's.
3. A synthetic workspace fixture for every lifecycle test: temp workspace, tiny fake Chroma-like client, fake benchmarks and fake cache files with their own expected hashes, and a fake embedder. No test may touch the real workspace or the real ONNX cache.
4. Tests 8 and 9 must supply every query and writer hook through the fake client so that zero real queries execute, and must assert call counts (zero real `coll.query` calls).
5. Initialize all `finally` locals before `try`; add a test for failure at Stage 1 and at Stage 2.
6. Scope the network guards inside the lifecycle (context manager that restores on exit), and keep a negative control that fails closed.
7. Bind the embedder to the validated files and assert the object used by `coll.query` is that one; reject `name == "default"` as a substitute for the type check.
8. Read-back should compare a content hash of the serialized state, not only `run_id`.
9. Replace `.get(..., 0)` on the saved grid with required-field checks.
10. Fix tests 3, 4 and 11 as noted in F11, and report the log in full.
11. Remove the "ZERO ASSETS MUTATED" and "Zero-Inference" claims until corrections are accepted.

## 5. Boundaries

No run is approved. This review does not authorize the live diagnostic, a 10k run, API calls, threshold tuning, manuscript change or canonical promotion. Any real-asset execution needs a separate user approval after a Codex and Claude re-audit. Historical calibration (main line 210) stays OPEN.
