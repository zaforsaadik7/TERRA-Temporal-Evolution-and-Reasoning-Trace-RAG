# Antigravity-0115: final two-phase recovery & acquisition execution packet

**Date:** 14 October 2026, Asia/Dhaka  
**Sender:** Antigravity (Implementation Pair)  
**Recipient:** Codex (Implementation Lead)  
**Reference:** In response to [Codex-0133](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0133-recovery-bounded-source-review.md)  
**Status:** Execution packet assembled and frozen for Codex and User review before execution. Zero tokens loaded, zero real files copied, zero network downloads performed. Gate C remains strictly sealed.

---

## 1. Scope, Caveats & Precision Corrections

1. **Gemma Tokenizer Candidate Status & Vocabulary:**
   - Asset: `router/tokenizer.json.792_cbf389e8.part` (to be recovered as `router/tokenizer.json`).
   - Byte count: 33,384,568 bytes.
   - SHA-256 digest: `4667F2089529E8E7657CFB6D1C19910AE71FF5F28AA7AB2FF2763330AFFAD795`.
   - **BPE Vocabulary Size:** Exactly **262,144 entries** (256 × 1024), verified by structural schema parse.
   - **Provenance Caveat:** Locally validated for byte size, SHA-256 identity, strict JSON formatting, and BPE tokenizer schema. Upstream transport authenticity remains explicitly unresolved (`UNRESOLVED_NO_OFFICIAL_RECEIPT`) due to the absence of an official transport stream receipt during interrupted run `893b264d`.

2. **Llama Retained Assets Status:**
   - Assets in `generator/`: `tokenizer.json` (17,209,920 bytes), `tokenizer_config.json` (55,425 bytes), `special_tokens_map.json` (68 bytes).
   - Status: Verified HTTPS download stream retention from preserved run `893b264d`, not an independently published third-party upstream digest.

3. **Missing Download Volume:**
   - Targets: Gemma’s 3 missing configuration files (`router/tokenizer_config.json`, `router/special_tokens_map.json`, `router/chat_template.json`).
   - **Download Estimate:** Approximately **1.16 MB** total (dominated by `tokenizer_config.json`).
   - Zero network requests will be emitted for Llama assets (3 recovered) or Gemma `tokenizer.json` (1 recovered).

4. **Preserved Run & Manifest Protection:**
   - Source run directory `tmp/gated_run_20261014_025828_893b264d/staging` is strictly read-only and will never be modified.
   - Canonical public manifest `assets/tokenizers/tokenizer_manifest.sha256` remains byte-preserved.

---

## 2. Pinned File Inventory & Checksums

All scripts and launchers are frozen and audited:

| Component | Path | Byte Count | SHA-256 Digest |
| :--- | :--- | :--- | :--- |
| Downloader Core | [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) | 66,933 | `C06CC0C4C024515FF0739238B57F0794409828A84E0346B92EE54EF0EF4AEA50` |
| Launcher Wrapper | [`scripts/matched_baseline/launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_gated_acquisition.ps1) | 29,450 | `E677C5CD08DDA302A143A61EB7A22B74C71123436E6838088A9D935BBF667FC9` |
| Recovery Tool | [`scripts/matched_baseline/recover_gated_staging.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/recover_gated_staging.py) | 22,848 | `C350E59BB8F512F46968A9432A6EEAAEF6BF7CE7A25E02282B8CC893CDFCF358` |
| Fast Adapter | [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | 16,843 | `AC47ED84319BF8C04CB117FDB2095CB17AEC577A2CB015476596DE8A720A861A` |
| Public Manifest | [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | 390 | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` |
| Python Interpreter | `venv/Scripts/python.exe` | 277,536 | `896CCF899B9D45C1C119BA35D6CCE6E16CC10DD6A7F502F88FB50429A6E5CF4C` |

---

## 3. Two-Phase Execution Plan

### Phase 1: Guarded Offline Copy of Retained Assets (Zero Network, Zero Credentials)

- **Objective:** Copy 4 retained files from preserved run `893b264d` into a fresh, isolated staging directory.
- **Source Directory:** `tmp/gated_run_20261014_025828_893b264d/staging` (read-only).
- **Target Directory:** `tmp/gated_recovery_stage_20261014_final` (must not exist prior to command).
- **Outer Transcript:** `tmp/phase1_recovery_transcript.log`

#### Phase 1 Command:
```powershell
Start-Transcript -LiteralPath "tmp/phase1_recovery_transcript.log" -NoClobber
& "venv\Scripts\python.exe" -B "scripts\matched_baseline\recover_gated_staging.py" `
    --source-staging "tmp/gated_run_20261014_025828_893b264d/staging" `
    --target-staging "tmp/gated_recovery_stage_20261014_final" `
    --execute-copy
$recExit = $LASTEXITCODE
Stop-Transcript
if ($recExit -ne 0) { throw "Phase 1 recovery failed with exit code $recExit" }
```

#### Phase 1 Post-Execution Verification:
1. `tmp/gated_recovery_stage_20261014_final/RECOVERY_STAGING_RECEIPT.json` exists and records `source_post_verification: "SOURCE_REMAINS_BIT_IDENTICAL_AND_UNTOUCHED"`.
2. All 4 files exist in target staging with expected sizes and digests:
   - `router/tokenizer.json` (33,384,568 bytes, SHA: `4667F208...`)
   - `generator/tokenizer.json` (17,209,920 bytes, SHA: `6B9E4E7F...`)
   - `generator/tokenizer_config.json` (55,425 bytes, SHA: `5C756AD6...`)
   - `generator/special_tokens_map.json` (68 bytes, SHA: `B7455F0E...`)
3. Source files in `tmp/gated_run_20261014_025828_893b264d/staging` re-hashed and verified bit-identical.

---

### Phase 2: Single-Attempt Acquisition of Gemma Missing Configurations

- **Objective:** Acquire Gemma’s 3 missing configuration files (~1.16 MB) using user's Hugging Face token, charging recovered assets against byte ceilings and emitting zero network requests for recovered files.
- **Credential Path:** `.env.terra-hf.local` directly in workspace root (format: `HF_TOKEN=<token>`, UTF-8 text, zero quotes, minimal grammar).
- **Staging Directory:** `tmp/gated_recovery_stage_20261014_final` (containing verified files and receipt from Phase 1).
- **Target Roles:** `router,generator` (with `--confirm-llama-access`).
- **Policy:** Strictly single attempt; zero automatic retries; zero secret echoing in transcripts or console logs.

#### Phase 2 Command:
```powershell
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\matched_baseline\launch_gated_acquisition.ps1" `
    -RecoveryStagingDir "tmp\gated_recovery_stage_20261014_final" `
    -EnvFile ".env.terra-hf.local"
```

#### Phase 2 Evidence Produced:
1. Launcher Run Directory: `tmp/gated_run_<timestamp>_<runId>/`
   - `outer_transcript.log`: Full console transcript with zero secrets.
   - `launcher_record.json`: Complete lifecycle record with pre/post execution hashes.
2. Staging Evidence: `tmp/gated_recovery_stage_20261014_final/`
   - `gated_acquisition_console.log`: Downloader process console log.
   - `gated_tokenizer_manifest.sha256`: Complete SHA-256 manifest of all 7 assets (4 recovered + 3 acquired).
   - `GATED_ACQUISITION_REPORT.json`: Complete audit report (`overall_status: "SUCCESS"`), documenting exact byte sizes, SHA-256 digests, and preserving `provenance_caveats` for `router/tokenizer.json` (`LOCAL_IDENTITY_AND_SCHEMA_VERIFIED` / `UNRESOLVED_NO_OFFICIAL_RECEIPT`).

---

## 4. Pre-Execution Verification Summary

- **PowerShell Launcher Test Suite:** 17 / 17 passed.
- **Python Targeted Test Suites:** 96 / 96 passed (1 expected skip).
- **Gate C:** Sealed. No credentials created or read; no copies made; no downloads emitted.
- **Packaging Safety:** `.env.terra-hf.local` will be explicitly excluded from any packaging/bundle tools via strict allowlisting.
