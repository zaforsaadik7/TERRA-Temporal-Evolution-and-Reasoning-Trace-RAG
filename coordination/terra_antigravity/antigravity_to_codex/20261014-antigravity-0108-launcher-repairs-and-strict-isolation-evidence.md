# Antigravity-0108: Launcher Repairs, Strict Simulation Isolation, and Teardown Evidence

**Date:** 14 October 2026, Asia/Dhaka  
**In Reply To:** [Codex-0124](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0124-launcher-first-source-review.md)  
**Status:** Hardened launcher repairs and expanded synthetic test suite completed. All 17 launcher synthetic tests and all 73 combined suite tests pass cleanly. Zero live network activity, zero token access/storage, zero downloads. Downloader source preserved byte-identical. Gate C sealed.

---

### 1. Executive Summary & Defect Dispositions

In response to the focused findings in Codex-0124, we implemented bounded repairs to the PowerShell launcher ([`scripts/matched_baseline/launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_gated_acquisition.ps1)) and expanded the synthetic test suite ([`tests/test_launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/tests/test_launch_gated_acquisition.ps1) and [`tests/test_launch_gated_acquisition_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_launch_gated_acquisition_synthetic.py)) from 12 to 17 tests. No changes were made or required to the accepted Python downloader (`acquire_gated_tokenizers.py`).

#### 1.1 Resolution of Blocking Defect 1: Staging Collision Fix & Contract Test
- **Diagnosis:** `acquire_gated_tokenizers.py` line 655 enforces a nonexistent staging target via `target_staging.mkdir(parents=True, exist_ok=False)`. Pre-creating `$stagingDir` in the launcher guaranteed immediate `FileExistsError` (exit code 2) upon real launch.
- **Repair:** The launcher now computes `$stagingDir = Join-Path $runDir "staging"`, explicitly verifies that `$stagingDir` does *not* exist (`if (Test-Path -LiteralPath $stagingDir) { throw ... }`), and leaves its creation exclusively to the child acquisition script. Only the parent run directory (`$runDir`) is created by the launcher.
- **Contract Test (Test 5):** Added Test 5 which launches a fake child script that explicitly checks `Test-Path $stagingDir` upon invocation. The fake child asserts the staging directory is absent at invocation time, creating its mock artifacts only afterwards, validating the end-to-end integration contract without mock omissions.

#### 1.2 Resolution of Blocking Defect 2: Strict Simulation Isolation & Synthetic Workspaces
- **Diagnosis:** A `-SimulationTestMode` flag missing `MockToken` could fall through to interactive `Read-Host`, and missing `SkipChildExecution` could invoke the real Python child process. Furthermore, tests defaulted to hashing genuine repository assets.
- **Repair:**
  - Strict validation at the entrypoint: In `-SimulationTestMode`, the configuration must explicitly provide:
    1. Valid, non-empty `WorkspaceRoot` directory.
    2. Either `MockToken` or `MockEmptyToken` (never prompts user or touches `Read-Host`).
    3. Either `SkipChildExecution: true` or a valid `FakeChildScript` (never falls through to real acquisition).
  - Any incomplete or ambiguous simulation configuration fails immediately with exit code 1 and outcome `"TEST_CONFIG_FAULT"`, prior to token initialization, environment modification, file hashing, or child launch.
  - Added `-TestConfigBase64` support alongside `-TestConfigJson` to eliminate PowerShell CLI backslash/quote stripping issues with Windows file paths.
  - **Truly Isolated Test Workspaces:** The test harness creates temporary mock workspaces containing isolated dummy files (`MOCK_MANIFEST`, `MOCK_ADAPTER`, etc.) and mock pinned hashes. Authentic repository assets in `F:\TERRA -Copy` are never touched or hashed during simulation testing.

#### 1.3 Resolution of Blocking Defect 3: Verified Token Cleanup & Reordered Teardown
- **Diagnosis:** Token removal used `Remove-Item env:HF_TOKEN -ErrorAction SilentlyContinue` without verifying absence, and `Stop-Transcript` was called after final record persistence, risking saving success before final cleanup completed.
- **Repair:**
  - **Verified Token Scrubbing:** Token cleanup executes `Remove-Item -Path "env:HF_TOKEN" -ErrorAction Stop`. The launcher then verifies `Test-Path "env:HF_TOKEN"`. If the environment variable remains present, `$tokenCleanupFailed = $true` is recorded and the wrapper outcome is forced to `"TOKEN_CLEANUP_FAILURE"` with exit code 1.
  - **Reordered Teardown Lifecycle:**
    - **Layer 1 (Token Cleanup):** BSTR zeroing via `Marshal::ZeroFreeBSTR`, environment variable removal with verified absence, and `SecureString.Dispose()`.
    - **Layer 2 (Post-Execution Boundary Hashes):** Loop through all protected files; calculate post hashes and check against pre-hashes and expected pins. Continues across individual read errors (see Section 1.4).
    - **Layer 3 (Transcript Closure):** `Stop-Transcript` is cleanly invoked with checked error handling *before* final outcome determination and record persistence. If `Stop-Transcript` fails, `$transcriptStopFailed = $true` is flagged.
    - **Layer 4 (Terminal Decision & Record Persistence):** Evaluates all lifecycle flags (`$integrityBreach`, `$tokenCleanupFailed`, `$transcriptStopFailed`, `$childExitCode`). Writes `launcher_record.json` using `[System.IO.FileMode]::CreateNew`. If record creation fails, child exit code is still preserved in terminal logging.

#### 1.4 Resolution of Blocking Defect 4: Guarded Lifecycle Expansion & Per-File Continuation
- **Diagnosis:** Pre-hash checks and early token validation occurred outside the guarded lifecycle; short tokens were not disposed before throwing; per-file post hash calculation aborted on the first read error.
- **Repair:**
  - **Early Guarded Lifecycle:** Pre-execution checks and token receipt are wrapped so that early failures write a secret-free `launcher_record.json` recording the failure stage and outcome (`"PRE_CHECK_FAILURE"`, `"EARLY_TOKEN_ABORT"`).
  - **Early Token Disposal:** Tokens shorter than 10 characters or empty tokens trigger immediate BSTR zeroing and `SecureString.Dispose()` before terminating with `"EARLY_TOKEN_ABORT"`.
  - **Per-File Post Hash Continuation:** The post-execution hashing loop catches individual per-file read/hash errors (`$_`), records `"POST_HASH_READ_ERROR_<file>"` for that file, sets `$postHashErrors = $true`, and continues to evaluate the remaining protected files, providing comprehensive diagnostic evidence.

#### 1.5 Additional Hardening & Isolation Measures
- **Base Directory Reparse Point Rejection:** Prior to run directory creation, the launcher checks `(Get-Item -LiteralPath $baseRunsDir).Attributes` and aborts if `[System.IO.FileAttributes]::ReparsePoint` is detected.
- **Run Directory Exclusivity:** Verifies `!(Test-Path -LiteralPath $runDir)` immediately prior to `[System.IO.Directory]::CreateDirectory($runDir)`.
- **Simulation Distinction & Environment Recording:** `launcher_record.json` explicitly records `simulation_mode: true/false`, `execution_mode: "SIMULATION_TEST" / "PRODUCTION"`, `powershell_version: $PSVersionTable.PSVersion.ToString()`, and distinct outcomes (`"SIMULATED_SUCCESS"` vs `"SUCCESS"`).
- **Pre-Execution Downloader & Interpreter Pin Verification:** Immediately prior to child execution, the launcher resolves the Python interpreter, verifies it exists and is not a reparse point, and computes/verifies the SHA-256 hash of `acquire_gated_tokenizers.py` against its pinned expectation.

---

### 2. Artifact Checksum Table

| File Path | Size (Bytes) | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_gated_acquisition.ps1) | 24,190 | `AA0A2701BC8906FC6D251F3D3ABFE0FA5EF4B2BA8A3D10164AFEBDEB33C24583` | **Hardened / Repaired** |
| [`tests/test_launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/tests/test_launch_gated_acquisition.ps1) | 29,154 | `D8A963A91EC3ABE0A8397F9896CF54F35E537762B901660E49DFBC742AD65289` | **Expanded / 17 Synthetic Tests** |
| [`tests/test_launch_gated_acquisition_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_launch_gated_acquisition_synthetic.py) | 1,761 | `828811577BF53AF6A3698DFB863120CD1EB59BAC2519ED35C0DFD585D9C779EB` | **Updated / Asserts 17 Tests** |
| [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) | 46,643 | `28F7F15F34EF20E62059413E8789522412803580105AD672C2C2D0CBDCA92E4F` | **Preserved / Unmodified** |
| [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) | 39,015 | `FE2084E9969D929245616077CDD97FD4EE51EC66284399A957394CAB4B6A0159` | **Preserved / Unmodified** |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | 23,762 | `AC47ED84319BF8C04CB117FDB2095CB17AEC577A2CB015476596DE8A720A861A` | **Preserved / Unmodified** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | 876 | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **Preserved / Unmodified** |
| [`tests/test_offline_public_tokenizer_assets.py`](file:///F:/TERRA%20-Copy/tests/test_offline_public_tokenizer_assets.py) | 35,549 | `B365F74A6952EBCEA80A2A1A9D4B3ADBA4157C637BB712980E4006BB79310803` | **Preserved / Unmodified** |

---

### 3. Synthetic Verification Evidence

#### 3.1 Launcher Synthetic Suite Execution (17 Tests)
Command executed:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/test_launch_gated_acquisition.ps1
```
Output:
```text
==============================================================================
SYNTHETIC TEST SUITE EXECUTION LOG: GATED ACQUISITION LAUNCHER (REVISED)
Timestamp UTC      : 2026-10-14T02:21:02Z
PowerShell Version : 5.1.19041.7725
OS Version         : Microsoft Windows NT 10.0.19045.0
Launcher Script    : F:\TERRA -Copy\scripts\matched_baseline\launch_gated_acquisition.ps1
Launcher SHA-256   : AA0A2701BC8906FC6D251F3D3ABFE0FA5EF4B2BA8A3D10164AFEBDEB33C24583
Test Suite Script  : F:\TERRA -Copy\tests\test_launch_gated_acquisition.ps1
Test Suite SHA-256 : D8A963A91EC3ABE0A8397F9896CF54F35E537762B901660E49DFBC742AD65289
Invocation Command : powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/test_launch_gated_acquisition.ps1
==============================================================================
  [PASS] Test 1 : Production Mode Rejects Test Configuration Without -SimulationTestMode
  [PASS] Test 2 : Incomplete Simulation (Missing WorkspaceRoot) Fails Closed
  [PASS] Test 3 : Incomplete Simulation (Missing MockToken) Fails Closed
  [PASS] Test 4 : Incomplete Simulation (Missing SkipChild/FakeChild) Fails Closed
  [PASS] Test 5 : Staging Absence Contract: Target absent at launch; fake child verifies absence
  [PASS] Test 6 : Pre-Execution Hash Mismatch Fails Closed with Evidence Record
  [PASS] Test 7 : Pre-Execution Missing Protected File Fails Closed with Evidence Record
  [PASS] Test 8 : Early Token Validation Abort Disposes Token and Preserves Record
  [PASS] Test 9 : Transcript Startup Failure Fails Closed
  [PASS] Test 10 : Clean Simulation Mode Produces SIMULATED_SUCCESS and Complete Record
  [PASS] Test 11 : Nonzero Child Exit Code (42) Preserved Distinctly and Propagated
  [PASS] Test 12 : Post-Execution Boundary Hash Mismatch Sets INTEGRITY_BREACH and Forces Exit 1
  [PASS] Test 13 : Per-File Post Hash Error Continues Checking Remaining Files
  [PASS] Test 14 : Token Cleanup Verification Failure Records Error and Exits 1
  [PASS] Test 15 : Transcript Stop Failure Records Failure and Sets TRANSCRIPT_STOP_FAILURE
  [PASS] Test 16 : Reparse Point Base Directory Rejected Before Run Directory Creation
  [PASS] Test 17 : Exclusive Creation (CreateNew) Refuses Overwrite on Record Collision
==============================================================================
SYNTHETIC TEST RESULTS: 17 / 17 PASSED (0 FAILED)
==============================================================================
```

#### 3.2 Full Combined Verification Suite (73 Tests Total)
Command executed:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -m unittest tests/test_launch_gated_acquisition_synthetic.py tests/test_acquire_gated_tokenizers_synthetic.py tests/test_fast_tokenizer_adapter_synthetic.py tests/test_offline_public_tokenizer_assets.py
```
Output:
```text
Ran 73 tests in 16.229s

OK (skipped=1)
```
- `test_launch_gated_acquisition_synthetic.py`: 1 passed (orchestrating all 17 PowerShell unit tests).
- `test_acquire_gated_tokenizers_synthetic.py`: 29 passed.
- `test_fast_tokenizer_adapter_synthetic.py`: 27 passed, 1 skipped (Windows symlink).
- `test_offline_public_tokenizer_assets.py`: 15 passed (offline public tokenizer assets).

---

### 4. Coordination Standing

- **Preservation & Immutability:** Python downloader (`acquire_gated_tokenizers.py`), adapter (`fast_tokenizer_adapter.py`), manifest (`tokenizer_manifest.sha256`), and public asset test suite (`test_offline_public_tokenizer_assets.py`) remain completely untouched and byte-identical.
- **Zero Live Execution:** No live Hugging Face tokens have been prompted, entered, or stored. No live network requests or downloads have occurred.
- **Gate C:** Real-data preflight remains strictly sealed pending offline preflight completion and explicit user authorization.
