# Antigravity-0098: Gemma Official Tree Correction, Revised File Inventory & Cap Proposal

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0115](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0115-gemma-official-tree-correction.md)  
**User Context:** User relays Codex-0115 noting official Gemma tree contradiction (chat_template.json exists; tokenizer.json is 33.4 MB exceeding 25 MB limit) and requests corrected file list and proposed limit without downloading yet.  

---

## 1. Acknowledgment & Factual Retraction

Antigravity acknowledges [Codex-0115](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0115-gemma-official-tree-correction.md) and makes the following explicit corrections:

1. **Retraction of False Template Absence & Erroneous Sizes:**
   - In Antigravity-0097, Antigravity erroneously asserted that `chat_template.json` was absent from the official Gemma tree and cited obsolete size estimates (`tokenizer.json` ~17.5 MB, `tokenizer_config.json` ~46 KB).
   - This was an error caused by conflating generic Gemma model-family documentation with the specific official repository tree.
   - We unequivocally withdraw that claim. As Codex-0115 verified from the official pinned tree URL (`https://huggingface.co/google/gemma-3-12b-it/tree/96b6f1eccf38110c56df3a15bffe176da04bfd80`), **`chat_template.json` explicitly exists (1.62 kB)** and **`tokenizer.json` is displayed as 33.4 MB**, with `tokenizer_config.json` at 1.16 MB.

2. **Correction of Attribution to Codex-0114:**
   - Codex-0114 requested verifying whether `chat_template.json` exists for Gemma; it did not assert its absence.
   - We correct the misattribution in Antigravity-0097 and maintain historical integrity.

3. **Status of Pathway Selection:**
   - Antigravity's recommendation for Manual Browser Download was a peer technical opinion, **not a user decision**. The user has not yet formally selected a pathway or authorized acquisition.
   - No downloads, staging scripts, or file acquisitions have been performed. All boundaries remain strictly sealed.

---

## 2. Official Pinned Tree Inventory & File Justifications

Based on official repository tree inspection at the immutable pinned commits:

### 2.1 Router: `google/gemma-3-12b-it`
**Repository:** `google/gemma-3-12b-it`  
**Pinned Commit:** `96b6f1eccf38110c56df3a15bffe176da04bfd80`  
**Official Tree URL:** `https://huggingface.co/google/gemma-3-12b-it/tree/96b6f1eccf38110c56df3a15bffe176da04bfd80`

| File Name | Displayed Size | Technical Role & Backend Need | Classification |
| :--- | :--- | :--- | :--- |
| `tokenizer.json` | 33.4 MB | Fast tokenizer vocabulary and BPE/Unigram definition. Directly consumed by `tokenizers.Tokenizer.from_file()`. | **Mandatory** |
| `chat_template.json` | 1.62 kB | Standalone official chat template definition. Directly consumable by `JinjaChatTemplateRenderer`. | **Mandatory** |
| `tokenizer_config.json` | 1.16 MB | Tokenizer configuration, special token attributes, and processor metadata. | **Mandatory** |
| `special_tokens_map.json` | 662 B | Mapping of special tokens (`<bos>`, `<eos>`, `<unk>`, pad, etc.). | **Mandatory** |
| `tokenizer.model` | 4.69 MB | Legacy SentencePiece binary model. Not strictly required by the Hugging Face `tokenizers` fast JSON backend, but provides canonical repository fidelity. | **Optional / Recommended for Sibling Parity** |

#### Byte Ceiling Analysis for Gemma 3:
- **Baseline 4-File Subset (Excluding `tokenizer.model`):**
  $33.4\text{ MB} + 1.16\text{ MB} + 1.62\text{ kB} + 662\text{ B} \approx 34.6\text{ MB}$.
  - Proposed 4-File Ceiling: **38,000,000 bytes (38 MB)**.
- **Complete 5-File Sibling Set (Including `tokenizer.model`):**
  $33.4\text{ MB} + 4.69\text{ MB} + 1.16\text{ MB} + 1.62\text{ kB} + 662\text{ B} \approx 39.3\text{ MB}$.
  - Proposed 5-File Ceiling: **45,000,000 bytes (45 MB)**.
- **Recommendation:** We propose adopting the **45,000,000-byte ceiling (5 files)**. This avoids user confusion during manual browser download if the user downloads all tokenizer files shown in the repository tree, while preventing an accidental fail-closed halt on `tokenizer.model`.

---

### 2.2 Shared Generator & Verifier: `meta-llama/Llama-3.3-70B-Instruct`
**Repository:** `meta-llama/Llama-3.3-70B-Instruct`  
**Pinned Commit:** `6f6073b423013f6a7d4d9f39144961bfbfbc386b`  
**Official Tree URL:** `https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct/tree/6f6073b423013f6a7d4d9f39144961bfbfbc386b`

| File Name | Displayed Size | Technical Role & Backend Need | Classification |
| :--- | :--- | :--- | :--- |
| `tokenizer.json` | 17.2 MB (17,209,920 B) | Fast tokenizer BPE vocabulary and merge table. Directly consumed by `tokenizers.Tokenizer.from_file()`. | **Mandatory** |
| `tokenizer_config.json` | 56.0 kB | Contains special token mappings and the official Jinja chat template. | **Mandatory** |
| `special_tokens_map.json` | 444 B | Mapping of special tokens (`<|begin_of_text|>`, `<|eot_id|>`, etc.). | **Mandatory** |

#### Byte Ceiling Analysis for Llama 3.3:
- Sum of files: $\approx 17.26\text{ MB}$.
- Proposed Ceiling: **22,000,000 bytes (22 MB)**.
- Margin: Provides $\approx 4.7\text{ MB}$ of safe margin without being excessively permissive.

---

## 3. Revised Four-Model Acquisition Budget Summary

| Model Role | Model Repository & Pinned Commit | Allowed Files | Estimated Size | Proposed Ceiling | Access Type |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Judge 2** | `openai/gpt-oss-120b`<br>`b5c939de8f754692c1647ca79fbf85e8c1e70f8a` | 4 files | 27.89 MB | **35,000,000 B** | **Retained & Validated (Stage 3B)** |
| **Judge 1** | `Qwen/Qwen3-Next-80B-A3B-Instruct`<br>`9c7f2fbe84465e40164a94cc16cd30b6999b0cc7` | 4 files | 15.88 MB | **17,000,000 B** | **Retained & Validated (Stage 3B)** |
| **Generator / Verifier** | `meta-llama/Llama-3.3-70B-Instruct`<br>`6f6073b423013f6a7d4d9f39144961bfbfbc386b` | 3 files | ~17.26 MB | **22,000,000 B** | **Pending Gated Acquisition** |
| **Router** | `google/gemma-3-12b-it`<br>`96b6f1eccf38110c56df3a15bffe176da04bfd80` | 5 files | ~39.3 MB | **45,000,000 B** *(revised from 25 MB)* | **Pending Gated Acquisition** |
| **Total** | Across all 4 model families | 16 files | ~100.3 MB | **119,000,000 B** | Zero weights, zero code execution |

---

## 4. Staging Protocol & Immutability Commitments

1. **Isolated Pre-Admission Staging:**
   - Any future acquired files must be staged in:
     - `tmp/gated_acquisition_staging/generator/` (3 Llama files)
     - `tmp/gated_acquisition_staging/router/` (5 Gemma files)
   - They will **not** be placed into canonical `assets/tokenizers/` until audited.

2. **Public Manifest Byte Preservation:**
   - [`assets/tokenizers/tokenizer_manifest.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest.sha256) (SHA-256: `41902553acffa03065b3bc6049047d0d573fb4659aea9f428df6d3f809f84a44`) remains strictly immutable.
   - A separate versioned manifest [`assets/tokenizers/tokenizer_manifest_v2.sha256`](file:///F:/TERRA%20-Copy/assets/tokenizers/tokenizer_manifest_v2.sha256) will be prepared only upon verified admission.

3. **Public Test Integrity Preserved:**
   - The Stage 3B test suite ([`tests/test_offline_public_tokenizer_assets.py`](file:///F:/TERRA%20-Copy/tests/test_offline_public_tokenizer_assets.py), SHA-256: `b365f74a6952ebcea80a2a1a9d4b3adba4157c637bb712980e4006bb79310803`) is preserved unchanged.

---

## 5. Scope & Action Boundaries

- **No Action Permitted Without Prior User Authorization:**
  - Zero downloads (manual or automated) are initiated.
  - Zero staging directories or verification tools are created.
  - No Databricks credentials or API keys requested or needed.
  - Gate C real-data preflight remains strictly sealed.
- **Pending User Decision:**
  1. Approval of revised Gemma ceiling (45,000,000 bytes for 5 files, or 38,000,000 bytes for 4 files).
  2. Selection of Pathway A (Manual Browser Download) vs. Pathway B (Reviewed local script).
