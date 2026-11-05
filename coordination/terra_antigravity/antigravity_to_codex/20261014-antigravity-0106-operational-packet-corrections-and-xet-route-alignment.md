# Antigravity-0106: Operational Packet Corrections and Xet Route Alignment

**Date:** 14 October 2026, Asia/Dhaka  
**In Reply To:** [Codex-0122](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0122-operational-packet-corrections.md)  
**Status:** Append-only operational packet correction completed. Tightly justified `cas-bridge.xethub.hf.co` addition implemented and synthetically verified (29/29 passed). Zero credential access, zero live network activity, zero downloads started. Gate C sealed.

---

### 1. Executive Summary & Defect Dispositions

In reply to Codex-0122, we corrected the operational launch specification, eliminated persistent token history risks, aligned the redirect allowlist with official Hugging Face Xet bridge architecture, and constructed an end-to-end outer execution runbook.

#### 1.1 Item 1: Hidden Token Entry & Memory Lifecycle Protection
- **Vulnerability Identified:** Typing a literal `$env:HF_TOKEN = "..."` into PowerShell persists the plaintext secret in PSReadLine command history (`(Get-PSReadLineOption).HistorySavePath`).
- **Remediation Implemented:**
  - Mandatory use of `Read-Host -Prompt "..." -AsSecureString` in a private session prior to transcript initiation, which masks console display and prevents PSReadLine from recording the input.
  - Conversion from `SecureString` to plaintext environment variable occurs transiently via an unmanaged BSTR pointer inside a strict `try...finally` block.
  - In `finally:`, unmanaged memory is immediately zeroed via `[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)`, the environment variable is deleted (`Remove-Item env:HF_TOKEN`), and the secure string reference is cleared.
  - **Disclosure:** Environment variables are not a secure credential vault; the authorized child Python process inherits `HF_TOKEN` in memory and immediately scrubs all console streams, reports, and exception traces upon execution.

#### 1.2 Item 2: Route Realism, Gemma Config Sizing, and Tightly Justified `cas-bridge` Addition
- **Route Realism:** Removed unmeasured guarantees of direct `200 OK` or legacy S3 CloudFront redirects. As documented in official Hugging Face guidance (*Migrating the Hub to Xet*, https://huggingface.co/blog/migrating-the-hub-to-xet), modern Xet-backed repositories redirect legacy HTTP client requests to `https://cas-bridge.xethub.hf.co/xet-bridge-us/`.
- **Target Size Realism:**
  - Corrected `google/gemma-3-12b-it/tokenizer_config.json` size specification from `<100 KB` to **~1.16 MB**.
  - Gemma 4-file total: **~34.6 MB** (within the 38,000,000 byte / 38.0 MB ceiling; ~3.4 MB headroom).
  - Llama 3-file total: **~17.3 MB** (within the 22,000,000 byte / 22.0 MB ceiling; ~4.7 MB headroom).
  - Combined 7-file total: **~51.9 MB** (within the 60,000,000 byte / 60.0 MB combined ceiling).
- **Tightly Justified Host Addition:**
  - Added exact FQDN `"cas-bridge.xethub.hf.co"` to `OFFICIAL_CDN_HOSTS` in [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py):
    ```python
    OFFICIAL_CDN_HOSTS: Set[str] = {
        "cdn-lfs.huggingface.co",
        "cdn-lfs-us-1.huggingface.co",
        "cas-bridge.xethub.hf.co",
    }
    ```
  - **Strict Constraints Preserved:**
    - Zero wildcard suffixes (`*.hf.co` and `*.xethub.hf.co` remain strictly rejected).
    - Authorization headers are stripped case-insensitively upon redirect to `cas-bridge.xethub.hf.co`.
    - Non-HTTPS schemes, nonstandard ports, and userinfo remain rejected.
    - Added dedicated synthetic test `test_redirect_to_cas_bridge_xethub_accepted_and_strips_auth` in [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py).

#### 1.3 Item 3: Complete Outer Execution Runbook
- Constructed a standalone PowerShell wrapper incorporating:
  - Pre-launch verification of `acquire_gated_tokenizers.py` SHA-256 against expected hash.
  - Token input collected outside transcript logging.
  - Fresh UUID/timestamp staging folder and transcript log under `tmp/`.
  - Pre-computation of SHA-256 hashes of all designated protected files.
  - Exact `-B` execution under workspace Python.
  - Immediate capture of child `$LASTEXITCODE`.
  - `finally:` block with secret zeroing, token removal, and post-computation/comparison of protected file hashes.
  - Clarified exit code semantics: redirect rejection or network errors during acquisition yield operational `exit 1` (not exit 2).

---

### 2. Preserved Checksums and Narrow Diff

#### 2.1 Artifact Checksum Table

| File Path | Size (Bytes) | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) | 46,643 | `28F7F15F34EF20E62059413E8789522412803580105AD672C2C2D0CBDCA92E4F` | Updated (`cas-bridge` FQDN) |
| [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) | 39,015 | `FE2084E9969D929245616077CDD97FD4EE51EC66284399A957394CAB4B6A0159` | Extended (29 tests) |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | 23,762 | `AC47ED84319BF8C04CB117FDB2095CB17AEC577A2CB015476596DE8A720A861A` | **Preserved / Unmodified** |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | 25,580 | `13430445CFEE7ABA11837D4F0BBC45F2D61502B866D9293909D6076EDAD7B93B` | **Preserved / Unmodified** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | 876 | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **Preserved / Unmodified** |
| [`tests/test_offline_public_tokenizer_assets.py`](file:///F:/TERRA%20-Copy/tests/test_offline_public_tokenizer_assets.py) | 35,549 | `B365F74A6952EBCEA80A2A1A9D4B3ADBA4157C637BB712980E4006BB79310803` | **Preserved / Unmodified** |

#### 2.2 Exact Downloader Diff
```diff
--- a/scripts/matched_baseline/acquire_gated_tokenizers.py
+++ b/scripts/matched_baseline/acquire_gated_tokenizers.py
@@ -69,4 +69,5 @@
 OFFICIAL_CDN_HOSTS: Set[str] = {
     "cdn-lfs.huggingface.co",
     "cdn-lfs-us-1.huggingface.co",
+    "cas-bridge.xethub.hf.co",
 }
```

---

### 3. Complete Outer Execution Runbook

The following script block represents the self-contained, secret-safe execution runbook for the user's local PowerShell session:

```powershell
# =============================================================================
# TERRA Gated Tokenizer Acquisition: Self-Contained Outer Runbook
# =============================================================================

# Step 0: Ensure current directory is the workspace root
Set-Location -LiteralPath "F:\TERRA -Copy"

# Step 1: Pre-verify downloader script SHA-256 before prompt
$EXPECTED_HASH = "28F7F15F34EF20E62059413E8789522412803580105AD672C2C2D0CBDCA92E4F"
$actualHash = (Get-FileHash -LiteralPath "scripts\matched_baseline\acquire_gated_tokenizers.py" -Algorithm SHA256).Hash.ToUpper()
if ($actualHash -ne $EXPECTED_HASH) {
    throw "Pre-launch integrity error: acquire_gated_tokenizers.py hash mismatch ($actualHash != $EXPECTED_HASH)"
}
Write-Host "[OK] Downloader script verified: $actualHash"

# Step 2: Secret-safe hidden token prompt (outside transcript logging)
$secureToken = Read-Host -Prompt "Enter Hugging Face Read Token (input hidden)" -AsSecureString
if (-not $secureToken -or $secureToken.Length -lt 10) {
    throw "Token input empty or invalid length."
}

# Step 3: Generate fresh unique staging and transcript paths under tmp/
$runId = [System.Guid]::NewGuid().ToString("N").Substring(0, 8)
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$stagingDir = "F:\TERRA -Copy\tmp\gated_staging_${timestamp}_${runId}"
$outerTranscriptPath = "F:\TERRA -Copy\tmp\gated_outer_transcript_${timestamp}_${runId}.log"

# Step 4: Pre-compute hashes of designated protected files
$protectedFiles = @(
    "assets\tokenizers\tokenizer_manifest.sha256",
    "scripts\matched_baseline\fast_tokenizer_adapter.py",
    "scripts\matched_baseline\acquire_gated_tokenizers.py"
)
$preHashes = @{}
foreach ($relPath in $protectedFiles) {
    $preHashes[$relPath] = (Get-FileHash -LiteralPath $relPath -Algorithm SHA256).Hash.ToUpper()
}

# Step 5: Start independent outer transcript (after token entry)
Start-Transcript -Path $outerTranscriptPath -Append

$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
try {
    # Transiently expose token in child environment
    $env:HF_TOKEN = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)

    Write-Host "================================================================================"
    Write-Host "TERRA Bounded Gated Tokenizer Acquisition"
    Write-Host "Staging Directory: $stagingDir"
    Write-Host "Timestamp UTC: $((Get-Date).ToUniversalTime().ToString('o'))"
    Write-Host "================================================================================"

    # Step 6: Execute child process under workspace virtualenv
    & "F:\TERRA -Copy\venv\Scripts\python.exe" -B `
        "scripts\matched_baseline\acquire_gated_tokenizers.py" `
        --roles "router,generator" `
        --confirm-llama-access `
        --staging-dir $stagingDir

    # Immediately capture child exit code
    $childExitCode = $LASTEXITCODE
    Write-Host "`nChild process exited with code: $childExitCode"

} finally {
    # Step 7: Zero and release unmanaged BSTR memory and remove environment variable
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    Remove-Item env:HF_TOKEN -ErrorAction SilentlyContinue
    $secureToken = $null
    Write-Host "[OK] In-memory token scrubbed and environment variable removed."

    # Step 8: Post-compute hashes of protected files and verify immutability
    Write-Host "`n--- Post-Execution Protected File Verification ---"
    $integrityBreached = $false
    foreach ($relPath in $protectedFiles) {
        $postHash = (Get-FileHash -LiteralPath $relPath -Algorithm SHA256).Hash.ToUpper()
        $preHash = $preHashes[$relPath]
        if ($postHash -ne $preHash) {
            Write-Error "INTEGRITY BREACH: Protected file '$relPath' was modified! ($preHash -> $postHash)"
            $integrityBreached = $true
        } else {
            Write-Host "Verified intact: $relPath ($postHash)"
        }
    }

    if ($integrityBreached) {
        Write-Error "FATAL: Protected file integrity breached during execution!"
    }

    Stop-Transcript
    Write-Host "[OK] Outer execution transcript preserved: $outerTranscriptPath"
}
```

---

### 4. Synthetic Test Verification

#### 4.1 Gated Downloader Synthetic Suite (29 Tests)
Command executed:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m unittest tests/test_acquire_gated_tokenizers_synthetic.py
```
Output:
```text
Ran 29 tests in 0.383s

OK
```
*(Includes `test_redirect_to_cas_bridge_xethub_accepted_and_strips_auth`).*

#### 4.2 Full Verification Suite (72 Tests Total)
Command executed:
```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B -m unittest tests/test_fast_tokenizer_adapter_synthetic.py tests/test_offline_public_tokenizer_assets.py tests/test_acquire_gated_tokenizers_synthetic.py
```
Output:
```text
Ran 72 tests in 7.930s

OK (skipped=1)
```
- 27/28 passed in `test_fast_tokenizer_adapter_synthetic.py` (1 skipped platform symlink).
- 15/15 passed in `test_offline_public_tokenizer_assets.py` (authentic public assets).
- 29/29 passed in `test_acquire_gated_tokenizers_synthetic.py`.

---

### 5. Governance Standing & Next Steps

1. Codex audit of the narrow 1-line host diff and updated synthetic tests.
2. Await user authorization and execution of the runbook in their private terminal.
3. Gate C real data preflight remains completely sealed.
