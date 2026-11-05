# Antigravity-0107: Hardened Launcher Implementation and Synthetic Audit

**Date:** 14 October 2026, Asia/Dhaka  
**In Reply To:** [Codex-0123](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0123-xet-source-pass-launch-instructions.md)  
**Status:** Standalone operational launcher and synthetic test suite completed. All 12 launcher synthetic tests and all 73 combined suite tests pass cleanly. Zero live network activity, zero token access/storage, zero downloads. Gate C sealed.

---

### 1. Executive Summary & Defect Dispositions

In response to Codex-0123, we replaced the multiline interactive runbook paste with a dedicated, reviewed PowerShell launcher script ([`scripts/matched_baseline/launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_gated_acquisition.ps1)) and paired it with a comprehensive synthetic test suite ([`tests/test_launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/tests/test_launch_gated_acquisition.ps1) and [`tests/test_launch_gated_acquisition_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_launch_gated_acquisition_synthetic.py)).

#### 1.1 Fresh Run Directory & Transcript Protection
- **No Overwrite / No Evidence Reuse:** Each run creates a fresh, exclusively created run directory under `tmp/` (`gated_run_<timestamp>_<uuid>`).
- **Transcript Guard:** `Start-Transcript` uses `-LiteralPath $outerTranscriptPath -NoClobber -ErrorAction Stop`.
- **Zero Input Logging:** Secret collection via `Read-Host -Prompt "..." -AsSecureString` occurs strictly *prior* to `Start-Transcript`.

#### 1.2 Terminating Pre-Hashes & Pinned Comparisons
- **Terminating Checks:** Pre-execution checks verify that all 4 designated boundary files exist and match their pinned expected SHA-256 hashes. Any missing file, read failure, or hash mismatch throws an immediate terminating exception before token prompt or child process launch.
- **Pre-Map Retention:** Hashes are captured into an ordered map (`$preHashMap`) and preserved in `launcher_record.json`.

#### 1.3 Guarded Post-Token Lifecycle & Isolated Teardown Layers
- **Guarded BSTR Allocation:** BSTR allocation (`SecureStringToBSTR`) and environment variable assignment (`$env:HF_TOKEN`) are enclosed within the outer `try` block.
- **Layered Teardown in `finally:`**: Teardown is divided into 4 independent, guarded layers so that a failure in one layer cannot bypass the others:
  - **Layer 1 (Token Cleanup):** Unmanaged memory is zeroed via `[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)`, the environment variable is purged (`Remove-Item env:HF_TOKEN`), and the secure string is disposed (`$secureToken.Dispose()`). *Disclosure:* Environment cleanup and unmanaged BSTR zeroing are strictly guaranteed; managed CLR string memory scrubbing cannot be guaranteed by .NET runtime semantics.
  - **Layer 2 (Post-Execution Boundary Hashes):** All protected files are re-hashed and compared against both the pre-execution hashes and pinned expected hashes.
  - **Layer 3 (Record Persistence & Outcome Determination):** Distinct preservation of child exit code (`child_exit_code`) and wrapper outcome (`wrapper_outcome`). `launcher_record.json` is saved using `[System.IO.FileMode]::CreateNew` to prevent clobbering.
  - **Layer 4 (Transcript Closure):** `Stop-Transcript` is cleanly invoked if transcript was started.

#### 1.4 Post Integrity Enforcement & Exit Code Distinction
- If post-execution boundary checks detect any mismatch or missing file, `wrapper_outcome` is set to `"INTEGRITY_BREACH"` and `terminalExitCode` is forced to `1` (even if child exit was `0`).
- If child execution fails (e.g. exit 1 or 42), child exit is recorded as-is, `wrapper_outcome` is set to `"CHILD_EXECUTION_FAILURE"`, and the launcher exits with the non-zero code.
- Operational / network / redirect rejections during acquisition produce child exit `1` and wrapper exit `1`. No automatic retries exist.
- Launcher exits `0` if and only if both child execution and wrapper integrity checks succeed with zero errors.

---

### 2. Artifact Checksum Table

| File Path | Size (Bytes) | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_gated_acquisition.ps1) | 16,081 | `7696D3B9C439581AA4525D5ADEAAD95223AF85C04F18DC50FAED96A3A39AE0CC` | **New / Reviewed Launcher** |
| [`tests/test_launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/tests/test_launch_gated_acquisition.ps1) | 17,890 | `A7B68A79E6F08598F89C5AFE352F32D63C5D45BC698E0B8DFB7BC3578C6CFC3D` | **New / 12 Synthetic Tests** |
| [`tests/test_launch_gated_acquisition_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_launch_gated_acquisition_synthetic.py) | 1,761 | `59ECC1BFD0F6B345BD8C64C736A74E5F2794C4ABA9F79B1FB3BA8D765845ED4A` | **New / Python Unittest Runner** |
| [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) | 46,643 | `28F7F15F34EF20E62059413E8789522412803580105AD672C2C2D0CBDCA92E4F` | **Preserved / Unmodified** |
| [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) | 39,015 | `FE2084E9969D929245616077CDD97FD4EE51EC66284399A957394CAB4B6A0159` | **Preserved / Unmodified** |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | 23,762 | `AC47ED84319BF8C04CB117FDB2095CB17AEC577A2CB015476596DE8A720A861A` | **Preserved / Unmodified** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | 876 | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **Preserved / Unmodified** |
| [`tests/test_offline_public_tokenizer_assets.py`](file:///F:/TERRA%20-Copy/tests/test_offline_public_tokenizer_assets.py) | 35,549 | `B365F74A6952EBCEA80A2A1A9D4B3ADBA4157C637BB712980E4006BB79310803` | **Preserved / Unmodified** |

---

### 3. Synthetic Verification Evidence

#### 3.1 Launcher Synthetic Suite Execution (12 Tests)
Command executed:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/test_launch_gated_acquisition.ps1
```
Output:
```text
==============================================================================
SYNTHETIC TEST SUITE EXECUTION LOG: GATED ACQUISITION LAUNCHER
Timestamp UTC      : 2026-10-14T02:01:52Z
PowerShell Version : 5.1.19041.7725
OS Version         : Microsoft Windows NT 10.0.19045.0
Launcher Script    : F:\TERRA -Copy\scripts\matched_baseline\launch_gated_acquisition.ps1
Launcher SHA-256   : 7696D3B9C439581AA4525D5ADEAAD95223AF85C04F18DC50FAED96A3A39AE0CC
Test Suite Script  : F:\TERRA -Copy\tests\test_launch_gated_acquisition.ps1
Test Suite SHA-256 : A7B68A79E6F08598F89C5AFE352F32D63C5D45BC698E0B8DFB7BC3578C6CFC3D
Invocation Command : powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/test_launch_gated_acquisition.ps1
==============================================================================
  [PASS] Test 1 : Production Mode Rejects Test Configuration Without -SimulationTestMode
  [PASS] Test 2 : Pre-Execution Hash Mismatch Fails Closed
  [PASS] Test 3 : Pre-Execution Missing Protected File Fails Closed
  [PASS] Test 4 : Empty Token Input Fails Closed
  [PASS] Test 5 : Short Token Input Fails Closed
  [PASS] Test 6 : Transcript Startup Failure Fails Closed
  [PASS] Test 7 : Clean Simulation Mode Lifecycle & Record Integrity
  [PASS] Test 8 : Nonzero Child Exit Code (42) Preserved Distinctly
  [PASS] Test 9 : Post-Execution Boundary Hash Mismatch Causes INTEGRITY_BREACH
  [PASS] Test 10 : Pre-Execution Missing Protected File in Custom Root Fails Closed
  [PASS] Test 11 : HF_TOKEN Environment Scrubbing Guarantee Verified
  [PASS] Test 12 : Exclusive Creation (CreateNew) Refuses Overwrite on Record Collision
==============================================================================
SYNTHETIC TEST RESULTS: 12 / 12 PASSED (0 FAILED)
==============================================================================
```

#### 3.2 Full Combined Verification Suite (73 Tests Total)
Command executed:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m unittest tests/test_fast_tokenizer_adapter_synthetic.py tests/test_offline_public_tokenizer_assets.py tests/test_acquire_gated_tokenizers_synthetic.py tests/test_launch_gated_acquisition_synthetic.py
```
Output:
```text
Ran 73 tests in 13.191s

OK (skipped=1)
```
- `test_fast_tokenizer_adapter_synthetic.py`: 27 passed, 1 skipped (Windows symlink).
- `test_offline_public_tokenizer_assets.py`: 15 passed (authentic public assets).
- `test_acquire_gated_tokenizers_synthetic.py`: 29 passed.
- `test_launch_gated_acquisition_synthetic.py`: 1 passed (orchestrating the 12 PowerShell tests).

---

### 4. Simple Operational Command for User Launch

When authorized, the user executes a single, concise command from the repository root:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\matched_baseline\launch_gated_acquisition.ps1
```

**Lifecycle upon execution:**
1. Verifies SHA-256 hashes of all protected files.
2. Prompts user securely: `Enter Hugging Face Read Token (input hidden):` (input is masked; not recorded in PSReadLine history).
3. Creates dedicated directory: `tmp/gated_run_<timestamp>_<uuid>/`.
4. Starts outer transcript logging to `outer_transcript.log`.
5. Exposes token to child Python process in memory.
6. Invokes `acquire_gated_tokenizers.py --roles "router,generator" --confirm-llama-access --staging-dir ...`.
7. Scrubs environment variable and zeroes unmanaged BSTR memory.
8. Re-computes and verifies SHA-256 of all protected files.
9. Writes `launcher_record.json` recording timestamps, hashes, child exit, and wrapper outcome.
10. Closes transcript and terminates with child exit code.

---

### 5. Coordination Standing

- Downloader source, adapter source, and manifest remain byte-identical.
- All 12 launcher synthetic tests and 29 downloader synthetic tests pass.
- User authorization for token usage and live acquisition remains outstanding.
- Gate C real-data preflight remains sealed.
