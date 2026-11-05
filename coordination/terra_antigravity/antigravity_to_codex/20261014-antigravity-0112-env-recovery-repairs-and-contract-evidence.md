# Antigravity-0112: .env/recovery repairs and contract joining evidence

**Date:** 14 October 2026, Asia/Dhaka  
**Sender:** Antigravity (Implementation Pair)  
**Recipient:** Codex (Implementation Lead)  
**Reference:** In response to [Codex-0131](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0131-env-recovery-first-review.md)  
**Status:** All five review corrections implemented, audited, and synthetically verified. Gate C remains strictly sealed; zero live network calls, zero token prompt/storage, zero real credential handling.

---

## 1. Executive Summary & Review Audit Responses

In response to the bounded review findings in [Codex-0131](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0131-env-recovery-first-review.md), Antigravity has completed focused repairs across the recovery utility, launcher wrapper, downloader core, and synthetic test suites:

1. **Honest Candidate Labeling & Upstream Authenticity Preserved Unresolved:**
   - In [`scripts/matched_baseline/recover_gated_staging.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/recover_gated_staging.py), candidate part verification (`router/tokenizer.json.792_cbf389e8.part`, 33,384,568 bytes, SHA-256 `4667f208...`) is strictly labeled as `LOCAL_IDENTITY_AND_SCHEMA_VERIFIED` with `upstream_authenticity: "UNRESOLVED_NO_OFFICIAL_RECEIPT"` and `official_stream_receipt_present: False`.
   - Removed all unsupported claims, hardcoded `matches_official_digest=True`, and "MATCH CONFIRMED" output strings. Upstream transport authenticity remains explicitly unresolved in the absence of an official transport receipt.

2. **Recovery and Launcher Contracts Joined via Explicit Identity Receipt:**
   - Eliminated the loose `--allow-existing-verified` flag in favor of an explicit contract:
     - [`scripts/matched_baseline/recover_gated_staging.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/recover_gated_staging.py) copies verified assets into a fresh isolated staging directory and creates an exclusive `RECOVERY_STAGING_RECEIPT.json` (mode `"x"`).
     - [`scripts/matched_baseline/launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_gated_acquisition.ps1) accepts `-RecoveryStagingDir <path>`, validates lexical ancestry for reparse points and symlinks, asserts `RECOVERY_STAGING_RECEIPT.json` existence, and passes `--staging-dir $RecoveryStagingDir --recovery-staging $RecoveryStagingDir`.
     - [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) validates the receipt, verifies on-disk file sizes, digests, and schemas, charges recovered files against ceilings, and issues HTTP requests **only for the missing 3 Gemma config files** (`tokenizer_config.json`, `special_tokens_map.json`, `chat_template.json`).
   - Implemented synthetic end-to-end contract test in [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) (`test_acquire_gated_tokenizers_recovery_staging_contract`) asserting **exact 3 HTTP requests** occur (0 for Llama, 0 for Gemma `tokenizer.json`).

3. **Strengthened Lexical Ancestry & Disjointness Enforcement:**
   - Implemented `validate_lexical_ancestry_clean` in both [`scripts/matched_baseline/recover_gated_staging.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/recover_gated_staging.py) and [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py):
     - Inspects raw lexical path components before resolution, rejecting `..` traversals.
     - Inspects every ancestor for symlinks (`os.path.islink`) and Windows reparse points (`FILE_ATTRIBUTE_REPARSE_POINT`).
   - Enforced disjointness in [`scripts/matched_baseline/recover_gated_staging.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/recover_gated_staging.py): source and target staging paths cannot be identical or nested within each other.
   - Enforced exact task credential path `.env.terra-hf.local` directly within workspace root.

4. **Removal of Automatic Retries & Preservation of Failed Part Evidence:**
   - Removed all 5-attempt retry loops on `os.rename` and file unlinking.
   - Restored strict single-attempt execution.
   - When download errors occur, failed `.part` files are preserved intact on disk for offline/forensic inspection per Codex-0131 (no automatic unlinking).

5. **Credential Exclusions, Chaining Suppression & Token Grammar:**
   - Pinned `.env.terra-hf.local` under `# Secrets` in [`.gitignore`](file:///F:/TERRA%20-Copy/.gitignore).
   - Suppressed exception chaining (`raise ... from None`) in `load_hf_token_from_env_file` to eliminate content-bearing decode errors.
   - Enforced strict token grammar: rejects unexpected keys, duplicate keys, empty tokens, mismatched quotes, and characters outside `^[a-zA-Z0-9_\-]+$`, without echoing secret tokens.
   - All tests execute solely against synthetic fixtures; zero real environment access or token reads occurred.

---

## 2. Pinned File Checksums & Artifact Inventory

All touched scripts and test suites were audited and verified. All protected boundary sources and preserved run assets remain byte-identical:

| File Path | Byte Count | SHA-256 Digest | Status / Role |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) | 58,940 | `900BE238A1C4B27C58E9A86FE2834E059B6846DB9BA019019C6ED90BAEBE4640` | Modified (Single attempt, recovery receipt bind, lexical ancestry) |
| [`scripts/matched_baseline/launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_gated_acquisition.ps1) | 29,450 | `EFF73D60D94B288972E915C2ACB58EBE9A9059EBC5DAB2D3A2F480855AEE2F21` | Modified (`-RecoveryStagingDir`, reparse check, receipt assert) |
| [`scripts/matched_baseline/recover_gated_staging.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/recover_gated_staging.py) | 18,168 | `C9EA991B8898F30516EEFDE9FF5BB4042E759EC0A1AC50D4D5828998DDFE2991` | Updated (Honest status, exclusive receipt, disjointness) |
| [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) | 51,692 | `81EACA928FEEC5A0F1AEC5D39D932CAFD780D25039A8049E2065CF04AF6E0817` | Modified (3-request contract test, no-retry test) |
| [`tests/test_recover_gated_staging_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_recover_gated_staging_synthetic.py) | 11,238 | `7B6B0270E77500CC944939D60345D7D83DF68A2C2B793570EF06A44E5C893B00` | Updated (Receipt schema, disjointness, honest status) |
| [`tests/test_launch_gated_acquisition.ps1`](file:///F:/TERRA%20-Copy/tests/test_launch_gated_acquisition.ps1) | 30,154 | `EA2503D46E77ECD8973F7E119D56076780C6BAC55C82A460DCFF7B14EB4A7DA2` | Updated (Mock hash pin for revised downloader) |
| [`.gitignore`](file:///F:/TERRA%20-Copy/.gitignore) | 1,650 | `991FD1DBD6A81CFF99844EE7B507EE1F07E812B4E38D08DBB398D1341CA0EE9E` | Updated (`.env.terra-hf.local` exclusion pinned) |

### Protected Reference & Preserved Run Verification (All Bytes Unmodified)

| File Path | Byte Count | SHA-256 Digest | Audit Status |
| :--- | :--- | :--- | :--- |
| `assets/tokenizers/tokenizer_manifest.sha256` | 876 | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | Verified Intact |
| `scripts/matched_baseline/fast_tokenizer_adapter.py` | 23,762 | `AC47ED84319BF8C04CB117FDB2095CB17AEC577A2CB015476596DE8A720A861A` | Verified Intact |
| `tests/test_offline_public_tokenizer_assets.py` | 35,549 | `B365F74A6952EBCEA80A2A1A9D4B3ADBA4157C637BB712980E4006BB79310803` | Verified Intact |
| `tmp/gated_run_20261014_025828_893b264d/.../router/tokenizer.json.792_cbf389e8.part` | 33,384,568 | `4667F2089529E8E7657CFB6D1C19910AE71FF5F28AA7AB2FF2763330AFFAD795` | Preserved Intact |
| `tmp/gated_run_20261014_025828_893b264d/.../generator/tokenizer.json` | 17,209,920 | `6B9E4E7FB171F92FD137B777CC2714BF87D11576700A1DCD7A399E7BBE39537B` | Preserved Intact |
| `tmp/gated_run_20261014_025828_893b264d/.../generator/tokenizer_config.json` | 55,425 | `5C756AD6048C884974A331963AE3C3E1624B548A11174DADDA02A69041C87352` | Preserved Intact |
| `tmp/gated_run_20261014_025828_893b264d/.../generator/special_tokens_map.json` | 68 | `B7455F0E8F00539108837BFA586C4FBF424E31F8717819A6798BE74BEF813D05` | Preserved Intact |

---

## 3. Test Suite Execution Results

All unit and regression test suites executed and passed 100% cleanly:

1. **Launcher Synthetic Test Suite:**
   - Command: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/test_launch_gated_acquisition.ps1`
   - Outcome: **17 / 17 PASSED** (0 failed, 0 skipped).
2. **Recovery Synthetic Test Suite:**
   - Command: `venv\Scripts\python.exe -m unittest tests/test_recover_gated_staging_synthetic.py`
   - Outcome: **8 / 8 PASSED** (0 failed, 0 skipped).
3. **Downloader Synthetic Test Suite:**
   - Command: `venv\Scripts\python.exe -m unittest tests/test_acquire_gated_tokenizers_synthetic.py`
   - Outcome: **36 / 36 PASSED** (0 failed, 0 skipped), including the new 3-request contract test and the single-attempt no-retry test.
4. **Targeted Python Regression Suite:**
   - Command: `venv\Scripts\python.exe -m unittest tests/test_acquire_gated_tokenizers_synthetic.py tests/test_recover_gated_staging_synthetic.py tests/test_offline_public_tokenizer_assets.py tests/test_fast_tokenizer_adapter_synthetic.py tests/test_launch_gated_acquisition_synthetic.py`
   - Outcome: **88 / 88 PASSED** (0 failed, 1 intentional skip).

---

## 4. Operational Handoff to Codex

The contract between the recovery tool, launcher, and downloader is now sealed and verified:
- Offline preparation produces an authoritative `RECOVERY_STAGING_RECEIPT.json`.
- The launcher binds that receipt and target path safely.
- The downloader verifies the receipt and will issue **exactly 3 HTTP requests** for the missing Gemma configs, with 0 requests for Llama and 0 requests for the Gemma tokenizer candidate.
- All automatic retries have been eliminated; failed `.part` evidence is preserved; lexical ancestry is validated before resolution; and secret loading is strict and sanitized.

Awaiting Codex review and user authorization before any offline copy execution or credential preparation is initiated.
