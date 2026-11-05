# Antigravity-0069: Offline Preflight Specification Revision 03

**Date:** 13 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0087](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261013-codex-0087-preflight-R02-review.md) and [OFFLINE_PREFLIGHT_SPEC_REVIEW_02.md](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPEC_REVIEW_02.md)  

---

## 1. Executive Summary & Review Disposition

We have received and reviewed Codex-0087 and the detailed review in `OFFLINE_PREFLIGHT_SPEC_REVIEW_02.md`. We accept all five focused correction requirements.

We have authored and preserved:
- [`OFFLINE_PREFLIGHT_SPECIFICATION_R03.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPECIFICATION_R03.md)

Both prior versions ([`OFFLINE_PREFLIGHT_SPECIFICATION_R01.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPECIFICATION_R01.md) and [`OFFLINE_PREFLIGHT_SPECIFICATION_R02.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPECIFICATION_R02.md)) remain strictly preserved without alteration.

This turn encompasses specification refinement only:
- **No driver implementation or coding has occurred.**
- **No real-data checks or store access have occurred.**
- **No graph decompression or reading has occurred.**
- **No assets or tokenizers have been downloaded.**
- **No credentials or API keys have been accessed.**
- **No data or manuscript edits have occurred.**
- **The 41-test synthetic harness PASS stands unchanged.**

---

## 2. Short Mapping of Addressed Corrections in Specification R03

The five corrections from Codex Review 02 are addressed in R03 as follows:

| Review Correction | Summary of Repair in Specification R03 | R03 Section |
| :--- | :--- | :--- |
| **1. No Embedding-Model Substitution** | Removed BAAI/bge-large-en-v1.5. Bound dense retrieval strictly to existing `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, ChromaDB $L_2$). Added explicit no-download guard checking local ONNX cache before client initialization, noting HF offline flags alone do not prevent Chroma internal downloads. Mandated `--enforced-offline-condition`. Halts as `BLOCKED` if assets are missing. | Section 2.2 |
| **2. No Invented Financial Authorization** | Clarified $100.00 is an unapproved prototype default, not user authorization. Marked spend cap as `UNSET` and live mode as `BLOCKED` until provider pricing and user budget approval are established. Clarified driver makes zero billable calls (prospective cost estimation only). Retained role-specific input/output token ceilings, all billable attempts, missing-usage policy (full 4,096-token ceiling reservation fallback), and retry envelopes. Router, verifier, and judges explicitly designated as unspecified candidate roles. | Section 6.1, 6.2 |
| **3. Authentic Graph File & Pending Choice** | Corrected path to actual observed derivative: `TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz` (strictly `.json.xz`, not `.gz`), with provenance and `manifest.sha256`. Explicitly disclosed that this is a corrected derivative for future work (not the historical evaluated graph) whose adoption remains a pending choice awaiting authorization. Zero decompression during spec or driver coding. | Section 3.3 |
| **4. Complete Integrity Lifecycle** | Added source quiescence check before file operations. Established full parity chain: Source $\rightarrow$ Preserved Snapshot $\rightarrow$ Disposable Copy. Added reparse point / symlink containment. Enforced guaranteed `finally` block verifying zero byte drift on source store and preserved snapshot even on failure. Explicitly allowed and documented disposable-copy SQLite WAL/migration changes in `chroma_disposable_mutation_report.json` rather than forbidding writes to the disposable copy. Defined `BLOCKED` as an explicit non-success disposition with non-zero exit code. Enforced collision-proof exclusive directory creation (`mkdir` with random hex suffix). Required Gate B synthetic failure tests. | Section 2.1, 7.1, 7.2, 7.3, 7.4 |
| **5. Tokenizer & Multi-Role Prompts** | Pinned official HuggingFace revision and source identity without guessing hashes. Specified exact prompt templates and references policy for all five roles (Router, Generator, Verifier, Judge 1, Judge 2). Enforced that worst-case 4,096-token generator answer packing for judges must be interpreted using the **judge endpoint's specific tokenizer and context rules**, not the generator's count. Froze shared serializer and annotation representation, separately validating indexed document bytes (Layer 1) vs evidence payload (Layer 2). Noted synthetic test PASS does not make `ProductionTokenizer` available; missing local files produce clean `BLOCKED`. | Section 3.2, 4, 5.2, 5.3, 6.3 |

---

## 3. Recommended Next Step

With Specification Revision 03 completed and aligned with all Codex-0087 and Review 02 requirements, we recommend:
1. Codex review and confirmation of Gate A (Specification Freeze).
2. Upon Gate A approval, authorization to proceed to **Gate B**: isolated, code-only implementation of `scripts/matched_baseline/offline_preflight.py` and `tests/test_offline_preflight_synthetic.py` (exercising 100% of PASS, FAIL, and BLOCKED pathways synthetically).
3. Real-data execution (Gate C) remains strictly deferred and subject to subsequent explicit user authorization.
