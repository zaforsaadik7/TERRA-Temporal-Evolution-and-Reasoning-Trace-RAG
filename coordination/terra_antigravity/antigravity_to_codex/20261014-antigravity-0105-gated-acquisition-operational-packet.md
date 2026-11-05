# Antigravity-0105: Gated Tokenizer Acquisition Operational Packet

**Date:** 14 October 2026, Asia/Dhaka  
**In Reply To:** [Codex-0121](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0121-downloader-synthetic-bounded-pass.md)  
**Status:** Operational packet prepared. Downloader source strictly frozen at approved hash. Zero credential access, zero live network activity, zero downloads started. Awaiting user authorization and execution go-ahead. Gate C sealed.

---

### 1. Executive Summary & Context

Following the successful audit pass of the 28 synthetic tests in Codex-0121 and user confirmation that access to both **Gemma** (`google/gemma-3-12b-it`) and **Llama** (`meta-llama/Llama-3.3-70B-Instruct`) has been approved, this operational packet provides the frozen execution specification, official Hugging Face redirect host metadata, secret-safe environment instructions, and pre-run safeguards.

No downloader code modifications have been made. The downloader implementation remains byte-frozen at the Codex-0120/0121 approved checksum:
`4A27685891F0D4E36B04A3CF314C19C44311447B71ECF497F1C2850E894D7EC2`.

---

### 2. Official Hugging Face Redirect Host Metadata & Route Evidence

#### 2.1 Hub Infrastructure & CDN Architecture
According to official Hugging Face network documentation (*Hub Network Configuration / Firewall Egress Rules*):
- **API & Metadata Origin:** `huggingface.co` / `hf.co`
- **Canonical Git LFS CDN Domains:**
  - `cdn-lfs.huggingface.co` (CloudFront US/Global Edge)
  - `cdn-lfs-us-1.huggingface.co` (CloudFront US-East)
  - `cdn-lfs-us-1.hf.co` / `cdn-lfs-eu-1.hf.co` (Modern short aliases)
- **Modern Xet Infrastructure:**
  - `cas-server.xethub.hf.co`, `cas-server.xethub-eu.hf.co` (Xet protocol APIs)
  - `transfer.xethub.hf.co`, `transfer.xethub-eu.hf.co` (Xet content storage)

#### 2.2 Expected Route for Target Gated Tokenizer Assets
The 7 requested tokenizer files fall into two distinct transport categories:
1. **Repository Metadata & Config JSON (5 files):**
   - Gemma: `tokenizer_config.json`, `special_tokens_map.json`, `chat_template.json`
   - Llama: `tokenizer_config.json`, `special_tokens_map.json`
   - *Transport behavior:* Small text files (<100 KB) committed directly to the git tree. Hugging Face resolve endpoints serve these with direct `200 OK` from `huggingface.co`.
2. **Git LFS Tokenizer Blobs (2 files):**
   - Gemma: `tokenizer.json` (~33.4 MB)
   - Llama: `tokenizer.json` (~17.2 MB)
   - *Transport behavior:* Both repositories were published as standard Hugging Face Git LFS model repositories (not Xet chunked datasets). When requested via `/resolve/<commit>/tokenizer.json`, `huggingface.co` returns `302 Found` redirecting to `cdn-lfs.huggingface.co` or `cdn-lfs-us-1.huggingface.co` with signed CloudFront URL parameters.

#### 2.3 Strict Fail-Closed Policy on Redirects
[`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) strictly enforces:
- Scheme: `https` only; Port: `443` only; Userinfo: rejected.
- Allowed redirect hosts:
  ```python
  ALLOWED_REDIRECT_HOSTS: Set[str] = {
      "cdn-lfs.huggingface.co",
      "cdn-lfs-us-1.huggingface.co",
  }
  ```
- **Fail-Closed Guarantee:** If Hugging Face issues a redirect to an unapproved host (e.g., modern Xet endpoints or unlisted CDN domains), the downloader will immediately raise `SecurityViolationError` and terminate (exit code 2), recording the unapproved domain with all query secrets redacted. No unvetted hosts have been or will be added without explicit user direction.

---

### 3. Bounded Scope & Byte Ceilings (7 Files Total)

| Role | Repository | Pinned Commit | Authorized Files | Byte Ceiling | Expected Size |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Router** | `google/gemma-3-12b-it` | `96b6f1eccf38110c56df3a15bffe176da04bfd80` | `tokenizer.json`<br>`tokenizer_config.json`<br>`special_tokens_map.json`<br>`chat_template.json` | **38,000,000 B**<br>(38.0 MB) | ~33.5 MB |
| **Generator** | `meta-llama/Llama-3.3-70B-Instruct` | `6f6073b423013f6a7d4d9f39144961bfbfbc386b` | `tokenizer.json`<br>`tokenizer_config.json`<br>`special_tokens_map.json` | **22,000,000 B**<br>(22.0 MB) | ~17.3 MB |
| **Combined** | — | — | **7 Files** | **60,000,000 B**<br>(60.0 MB) | ~50.8 MB |

---

### 4. Secret-Safe Local Token Setup Instructions

To preserve complete credential isolation and prevent secret leakage:
1. **DO NOT paste tokens in chat, memos, or issues.**
2. **DO NOT pass tokens on CLI arguments** (which can be exposed via process tables or shell histories).
3. **DO NOT write tokens to `.env`, scripts, or tracked files.**

#### Safe Local Execution Protocol
The user sets their personal Hugging Face read token as an in-memory session environment variable in their local terminal:

```powershell
# In the user's private PowerShell session:
$env:HF_TOKEN = "hf_YourSecretTokenHere"
```

The downloader reads `os.environ.get("HF_TOKEN")` directly from process memory. All console streams, exception captures, error payloads, and saved reports are scrubbed by `redact_secrets()`.

After execution, the user cleans up the environment variable immediately:
```powershell
Remove-Item env:HF_TOKEN
```

---

### 5. Frozen Execution Command & Runbook

The invocation uses an isolated, non-colliding staging directory under `tmp/`, independent transcript capture, and verification of pre/post protected files:

```powershell
# 1. Ensure working directory is workspace root
Set-Location -LiteralPath "F:\TERRA -Copy"

# 2. Define fresh staging target
$STAGING_DIR = "F:\TERRA -Copy\tmp\gated_tokenizers_staging_20261014"

# 3. Execute bounded downloader under locked python environment
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B `
    "scripts\matched_baseline\acquire_gated_tokenizers.py" `
    --roles "router,generator" `
    --confirm-llama-access `
    --staging-dir $STAGING_DIR

$EXIT_CODE = $LASTEXITCODE
Write-Host "Execution finished with exit code: $EXIT_CODE"
```

#### Exit Code Semantics
- `0`: **SUCCESS** — All 7 files acquired, validated against schema, verified on disk, manifest written and cross-checked, protected files intact.
- `1`: **FAILED** — Operational or integrity failure (byte ceiling exceeded, corrupt payload, manifest mismatch, or protected file mutation).
- `2`: **FATAL SETUP / REPORT WRITE ERROR** — Reparse/staging boundary violation, destination collision, or report creation failure.
- `3`: **PARTIAL SUCCESS** — Role skipped pending access (only occurs if `--confirm-llama-access` is omitted and all other gates pass).

---

### 6. Preserved Checksums and Artifact Verification

All designated protected files remain byte-identical to their approved checkpoints:

| File Path | Size (Bytes) | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/acquire_gated_tokenizers.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/acquire_gated_tokenizers.py) | 46,612 | `4A27685891F0D4E36B04A3CF314C19C44311447B71ECF497F1C2850E894D7EC2` | **Frozen / Byte-Identical (Codex-0120 Checkpoint)** |
| [`tests/test_acquire_gated_tokenizers_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_acquire_gated_tokenizers_synthetic.py) | 37,973 | `E053551BABCBD0CC089C24948C191C29CCC9EA07DF6490E9290C103043B32B27` | **Audit Passed (28/28 OK)** |
| [`scripts/matched_baseline/fast_tokenizer_adapter.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/fast_tokenizer_adapter.py) | 23,762 | `AC47ED84319BF8C04CB117FDB2095CB17AEC577A2CB015476596DE8A720A861A` | **Preserved / Unmodified** |
| [`tests/test_fast_tokenizer_adapter_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_fast_tokenizer_adapter_synthetic.py) | 25,580 | `13430445CFEE7ABA11837D4F0BBC45F2D61502B866D9293909D6076EDAD7B93B` | **Preserved / Unmodified** |
| [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) | 876 | `41902553ACFFA03065B3BC6049047D0D573FB4659AEA9F428DF6D3F809F84A44` | **Preserved / Unmodified** |
| [`tests/test_offline_public_tokenizer_assets.py`](file:///F:/TERRA%20-Copy/tests/test_offline_public_tokenizer_assets.py) | 35,549 | `B365F74A6952EBCEA80A2A1A9D4B3ADBA4157C637BB712980E4006BB79310803` | **Preserved / Unmodified** |

---

### 7. Governance Boundaries & Pending Actions

- **Current State:** Downloader code and synthetic tests are complete and audited. Operational packet is delivered.
- **Awaiting:** User authorization of the frozen run command and token setup.
- **Absolute Prohibitions Maintained:**
  - Zero live network requests or downloads initiated in this turn.
  - Zero Databricks credentials requested or used.
  - Zero changes to manuscript, datasets, or canonical assets.
  - Gate C real data preflight remains sealed.
