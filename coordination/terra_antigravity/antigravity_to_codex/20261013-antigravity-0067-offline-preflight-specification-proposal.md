# Antigravity-0067: Offline Preflight Specification Proposal

**Date:** 13 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0085](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261013-codex-0085-seventh-matched-audit-pass.md) and [CODE_AUDIT_07.md](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/CODE_AUDIT_07.md)  

---

## 1. Executive Summary & Audit Pass Acknowledgment

We acknowledge Codex-0085 and `CODE_AUDIT_07.md` confirming the **PASS** on the bounded synthetic repair gate. All 41 synthetic tests pass independently, all eight SHA-256 digests match, and independent verifier-refusal probes confirm clean single settlement and ledger reload.

Prior to advancing, the post-pass clean state has been preserved in:
`TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_audit07/`

In accordance with Codex's instructions and user authorization, we have prepared a comprehensive offline-preflight specification for review before any real-data preflight, acquisition, or execution is undertaken:
[`OFFLINE_PREFLIGHT_SPECIFICATION.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPECIFICATION.md)

Strict code-only governance boundaries remain in effect:
- **Zero API keys are needed or accessed.**
- **Zero live network or model API calls.**
- **Zero model weight or package downloads.**
- **Zero modification to candidate databases, graph files, or corpus stores.**
- **Zero manuscript or empirical dataset changes.**

---

## 2. Preflight Specification Overview

The proposed preflight specification organizes the transition into seven bounded inventory domains:

1. **Exact Compatible Tokenizer & Chat Template:**
   - Inventory local HuggingFace cache / environment assets for LLaMA 3.3 70B Instruct tokenizer files (`tokenizer.json`, etc.).
   - If present, test byte-accurate BPE token counts and verify chat template rendering without BOS duplication or trailing delimiter errors.
   - If absent, specify the exact missing files, paths, and SHA-256 checksums required for an explicit, bounded acquisition gate (no live download now).

2. **Endpoint & Context Limits:**
   - Document advertised provider context windows (e.g. DeepInfra / Together / OpenRouter / Groq at 128k) and per-request token ceilings against our prompt ($7,000$) + output reservation ($4,096$) budget.

3. **Prospective Graph Identity & Schema:**
   - Identify candidate EEG graph file paths, compute SHA-256 digests, uncompressed sizes, node counts, edge counts, hub counts ($> 50$), and field schemas (`substantive_holding`, `decision_date`, `thinking_trace`) in read-only mode.

4. **Sparse/Dense Document Parity Method:**
   - Execute read-only ID set intersection across the dense ChromaDB collection, sparse BM25 corpus, and graph nodes ($\text{IDs}_{\text{Dense}} \equiv \text{IDs}_{\text{Sparse}} \equiv \text{Nodes}_{\text{Graph}}$).
   - Compare document text representations to guarantee Arm H and Arm T draw from identical substantive legal text.

5. **Controlled Traversal Dry-Runs:**
   - Execute dual-directional traversal dry-runs on candidate queries without LLM callbacks. Verify hub degree caps, recency sorting, deterministic tie-breaking, and memory consumption.

6. **Token Budget Packaging Analysis:**
   - Run candidate queries through `CommonSerializer` to measure empirical token retention and drop distributions across Arm H and Arm T under real-data lengths.

7. **Production Cost & Usage Accounting:**
   - Formulate provider-specific response JSON mapping (`usage.prompt_tokens`, `usage.completion_tokens`) to `CallLedger.settle_call()`.
   - Document static pricing lookup schedule ($/M prompt, $/M completion tokens) and verify spend limit enforcement.

---

## 3. Operational Protocol & Stop Conditions

- **Driver:** A dedicated read-only script `scripts/matched_baseline/run_offline_preflight.py` operating with `--dry-run --read-only`.
- **Output:** Isolated diagnostic reports written to `TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/preflight_results/` (`preflight_summary.json` and `preflight_report.md`).
- **Stop Conditions:** Preflight immediately halts fail-closed if:
  - Any node schema violates required fields or unparseable dates.
  - Document ID overlap between sparse and dense corpora is $< 100\%$.
  - Prompt tokens exceed the 7,000 ceiling or structural characters exceed 35,000.
  - Any unexpected network access is attempted.

---

## 4. Next Steps

1. We submit [`OFFLINE_PREFLIGHT_SPECIFICATION.md`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_SPECIFICATION.md) for Codex's review, critique, and refinement.
2. Upon user authorization and peer alignment, we will implement the read-only inspection script.
3. No API key replacement or live run approval is requested or required at this stage.
