# Codex-0219 — Explicit offline report mode contract

Author: Codex, 15 October 2026 (Asia/Dhaka). Code-only implementation self-verification.

validate_smoke_report now accepts an independently specified expected_mode, default SIMULATED. The only additional recognized contract is AUTHENTIC_OFFLINE_FEASIBILITY. A report cannot self-select this mode: existing child entry and parent dispatcher still use the SIMULATED default and reject it. No authentic producer or execution entry is enabled.

The authentic offline contract requires exact typed disclosures: retrieval LOCAL_DISPOSABLE_STORE, embedding LOCAL_PINNED_ONNX, tokenization LOCAL_PINNED_TOKENIZERS, routes HYPOTHETICAL_EASY_AND_HARD, judge_answer SYNTHETIC_PLACEHOLDER, provider_certified false, live_api_calls integer zero. This avoids describing hypothetical role packing and placeholder judge answers as an actual routed/generated/judged evaluation. These are required report claims, not independent verification that the claimed execution occurred; eventual admission must substantiate them with source and asset evidence.

Three added tests cover default-mode rejection of authentic-labeled output, explicit-mode validation plus misleading/incorrect typed disclosure rejection, and missing-disclosure rejection. All fixtures are synthetic dictionaries. All 261 tests passed across the existing 20 named synthetic suites in 6.730 seconds, exit 0. No wildcard discovery. Temporary ledger collision remains an expected negative test.

Byte copies under reports/codex_report_modes_20261015_01/:

- offline_smoke_report.py: dc13cc7bd07bf09460f049224b37e192daeafd992abbb0bc20e73b3cb3f45c9c
- test_offline_smoke_child_entry_synthetic.py: 0ca2f58a00e1f5d8c5931735d214f0b9523d1015bfe8f369316f7e89a4951fb3

Genuine worker loading, DLL loader/executor, production parent/child CLI and complete reviewed launch inventory remain unfinished. This is a pure report-contract change, not genuine worker admission. No real store, graph, model/tokenizer, Windows native/firewall, credentials, network/API or manuscript activity. No API key needed. Peer review can be batched; existing code-only authority permits continued implementation without another approval round.
