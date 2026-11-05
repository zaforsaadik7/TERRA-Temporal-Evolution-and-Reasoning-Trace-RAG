# Codex-0293 — paired prompts and workflow, synthetic checkpoint

Codex, 24 October 2026. User authorized next implementation. User-relayed mailbox only.

Read reports/paired_prompt_workflow_20261024_01/IMPLEMENTATION_AND_REVIEW_SCOPE.md and manifest.json, then scripts/matched_baseline/paired_prompt_workflow.py and tests/test_paired_prompt_workflow_synthetic.py. R01 prompt texts and strict output/rubric rules are proposed for prospective review, not historically exact or live-approved.

One query-only shared router, both prepacked fixture arms, verifier short-circuit, actual candidate answer to both judges, conservative null-score handling, explicit analysis-only taxonomy adapter and repeatable paired order implemented. Equal retained case IDs require equal content across all route/arm fixtures. Provider charges precede schema parsing; exclusive bounded trace preserves requests/responses and partial failures. Real tokenizers, retrieval and provider transport are not connected. run_live_pair remains unconditionally held.

97 named synthetic tests PASS (25 new +31 provider +41 prior). Existing provider_accounting, matched_harness, common_serializer and scoring_analyzer unchanged. No network/keys/models/stores/scientific results/manuscript/statistics/promotion.

Please review prompts, refusal/null-score policy, information parity, call envelope, failure persistence and analysis mapping. In particular, do not mistake fixture preparation and synthetic counts for authentic retrieval/tokenization. No overlapping implementation requested. Next code-only work is held provider transport and run-level persistence/rate control; no key needed yet.
