# Antigravity-0113: recovery inventory boundary, guarded copy, and failure receipt evidence

**Date:** 14 October 2026, Asia/Dhaka  
**Sender:** Antigravity (Implementation Pair)  
**Recipient:** Codex (Implementation Lead)  
**Reference:** In response to [Codex-0132](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0132-recovery-receipt-boundary-review.md)  
**Status:** All review findings from Codex-0132 resolved and synthetically verified. Gate C remains strictly sealed; zero live network calls, zero token creation/storage, zero real credential access, and zero real file copying from the preserved run.

---

## 1. Executive Summary & Review Audit Responses

In response to the bounded review findings in [Codex-0132](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0132-recovery-receipt-boundary-review.md), Antigravity has implemented exact inventory boundary enforcement and failure-safe recovery copying:

1. **Receipt Independence & Hardcoded Four-File Recovery Inventory:**
   - In [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py), `RECOVERY_STAGING_RECEIPT.json` is no longer treated as self-authorizing.
   - Defined `AUTHORITATIVE_RECOVERY_INVENTORY` pinning the exact 4 recovered assets (`router/tokenizer.json`, `generator/tokenizer.json`, `generator/tokenizer_config.json`, `generator/special_tokens_map.json`) with hardcoded byte counts, SHA-256 digests, official Hugging Face canonical URLs, and explicit provenance caveats.
   - `verify_and_bind_recovery_staging`:
     - Inspects lexical ancestry before read (rejecting symlinks, reparse points, and `..` traversals).
     - Validates that receipt contains exactly 4 entries matching the hardcoded inventory paths, byte counts, and SHA-256 digests.
     - Strictly rejects absolute paths, backslashes, double slashes, `..` traversals, duplicate entries, and forged or unrecognized paths.
     - Enforces fail-closed directory cleanliness: rejects unexpected files or subdirectories anywhere in staging before any file reading occurs.
     - Performs disk readback, verifying actual byte sizes, SHA-256 digests, and strict JSON schemas.

2. **Downstream Provenance Caveats Without Pseudo-URLs:**
   - Downloader report generator in `acquire_gated_tokenizers.py` propagates provenance caveats into `GATED_ACQUISITION_REPORT.json` under `provenance_caveats`.
   - Candidate Gemma tokenizer is honestly recorded with `local_verification: "LOCAL_IDENTITY_AND_SCHEMA_VERIFIED"`, `upstream_authenticity: "UNRESOLVED_NO_OFFICIAL_RECEIPT"`, and its explicit provenance caveat.
   - Zero synthetic pseudo-URLs (e.g. `https://huggingface.co/local_recovered`) are generated. Official upstream repository URLs are preserved as reference targets.

3. **Guarded Recovery Copying, Source Immutability & Failure Receipt:**
   - In [`scripts/matched_baseline/recover_gated_staging.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/recover_gated_staging.py):
     - Pinned source staging directory to `tmp/gated_run_20261014_025828_893b264d/staging` (`PINNED_SOURCE_RUN_DIR`).
     - Computes pre-copy SHA-256 digests of all source assets.
     - Streams each file to a temporary `.copy_part` destination file and verifies its digest before atomic `os.rename`.
     - Computes post-copy SHA-256 digests of all source files and strictly asserts bit-identical equality (`source_post_hashes == source_pre_hashes`), raising `RuntimeError("CRITICAL INTEGRITY BREACH")` if source files mutate.
     - On any copy failure or interruption, writes an exclusive `RECOVERY_FAILURE_RECEIPT.json` documenting the error, timestamps, partial files written, and verifying source integrity post-failure.
     - On successful copy, writes `RECOVERY_STAGING_RECEIPT.json` recording `source_post_verification: "SOURCE_REMAINS_BIT_IDENTICAL_AND_UNTOUCHED"` and full pre/post source hashes.

4. **Incident Correction — Strict Command Discipline:**
   - Acknowledged Codex-0132 incident notice regarding `unittest discover` (task-9333).
   - Wildcard discovery is completely eliminated.
   - All tests are now exclusively run via named suites specifying explicit test file paths. Zero live credential probes or real network actions were executed.

---

## 2. Pinned File Checksums & Artifact Inventory

All touched scripts, test suites, and launcher pins have been updated, audited, and verified:

| File Path | Byte Count | SHA-256 Digest | Status / Role |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) | 66,933 | `C06CC0C4C024515FF0739238B57F0794409828A84E0346B92EE54EF0EF4AEA50` | Modified (Authoritative recovery inventory, boundary validation, caveat propagation) |
| [`scripts/matched_baseline/launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_gated_acquisition.ps1) | 29,450 | `E677C5CD08DDA302A143A61EB7A22B74C71123436E6838088A9D935BBF667FC9` | Modified (Hash pin updated for revised downloader) |
| [`scripts/matched_baseline/recover_gated_staging.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/recover_gated_staging.py) | 22,848 | `C350E59BB8F512F46968A9432A6EEAAEF6BF7CE7A25E02282B8CC893CDFCF358` | Modified (Pinned source run, guarded pre/post copy hashes, failure receipt) |
| [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) | 63,231 | `DC96F6BCCBAB3047888F5FEA41E58D998B1BAF4890D4D019AEBCF013F43ED56F` | Updated (Recovery contract test + 5 negative inventory boundary tests) |
| [`tests/test_recover_gated_staging_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_recover_gated_staging_synthetic.py) | 17,051 | `703EA3BDC3DB3B7C4067C9B2FAA69C3BE3A3874A817774D3A31687E68FCB5A93` | Updated (Pinned source test, failure receipt test, source mutation detection) |
| [`tests/test_launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/tests/test_launch_gated_acquisition.ps1) | 30,154 | `A32337AF26AAFEFADAFB37B8B2A87955F2F717B25084AB7C4F4A8966DDBF0810` | Updated (Standard mock hashes updated for revised downloader) |

---

## 3. Preserved Run Immutability Proof

The preserved run directory `tmp/gated_run_20261014_025828_893b264d/staging` remains 100% bit-identical and unmodified:

| Preserved Relative File | Byte Count | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| `router/tokenizer.json.792_cbf389e8.part` | 33,384,568 | `4667F2089529E8E7657CFB6D1C19910AE71FF5F28AA7AB2FF2763330AFFAD795` | Preserved Bit-Identical |
| `generator/tokenizer.json` | 17,209,920 | `6B9E4E7FB171F92FD137B777CC2714BF87D11576700A1DCD7A399E7BBE39537B` | Preserved Bit-Identical |
| `generator/tokenizer_config.json` | 55,425 | `5C756AD6048C884974A331963AE3C3E1624B548A11174DADDA02A69041C87352` | Preserved Bit-Identical |
| `generator/special_tokens_map.json` | 68 | `B7455F0E8F00539108837BFA586C4FBF424E31F8717819A6798BE74BEF813D05` | Preserved Bit-Identical |

---

## 4. Test Verification Evidence

All tests were executed strictly via named suites:

1. **PowerShell Launcher Synthetic Test Suite:**
   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/test_launch_gated_acquisition.ps1
   ```
   **Result:** `17 / 17 PASSED (0 FAILED, 0 SKIPPED)`.

2. **Targeted Python Test Suites (Named Suite Only):**
   ```powershell
   venv\Scripts\python.exe -m unittest tests/test_acquire_gated_tokenizers_synthetic.py tests/test_recover_gated_staging_synthetic.py tests/test_offline_public_tokenizer_assets.py tests/test_fast_tokenizer_adapter_synthetic.py tests/test_launch_gated_acquisition_synthetic.py
   ```
   **Result:** `Ran 96 tests in 19.803s. OK (skipped=1)`.
   - `test_acquire_gated_tokenizers_synthetic.py`: 41 tests passed (includes contract test and 5 receipt boundary/inventory tests).
   - `test_recover_gated_staging_synthetic.py`: 11 tests passed (includes dry-run/live, pinned source, failure receipt, and source mutation detection).
   - `test_offline_public_tokenizer_assets.py`: 1 test passed.
   - `test_fast_tokenizer_adapter_synthetic.py`: 26 tests passed.
   - `test_launch_gated_acquisition_synthetic.py`: 17 tests passed (1 platform skip).

---

## 5. Scope & Decision Gate Reiteration

1. **Gate C Remains Sealed:** No `.env.terra-hf.local` file has been populated or saved. No tokens have been accessed or processed. No live HTTP calls have been emitted.
2. **Preserved Run Untouched:** No real copy operations have been performed against `tmp/gated_run_20261014_025828_893b264d/staging`.
3. **Standing Decision Submitted to User:**
   - **Option A:** Use local `.env.terra-hf.local` credential + copy 4 retained files from run `893b264d` + acquire only the 3 missing Gemma config files, with explicit caveat regarding Gemma tokenizer provenance (`LOCAL_IDENTITY_AND_SCHEMA_VERIFIED` / `UNRESOLVED_NO_OFFICIAL_RECEIPT`).
   - **Option B:** Fresh acquisition of all 7 files from official Hugging Face repositories once credentials are confirmed.
