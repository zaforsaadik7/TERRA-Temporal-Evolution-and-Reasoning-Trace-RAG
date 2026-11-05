# Codex-0294 — provider HTTP and run controls

Codex, 24 October 2026. User-relayed peer checkpoint, implementation self-verification.

Read reports/provider_run_control_20261024_01/IMPLEMENTATION_AND_REVIEW_SCOPE.md and manifest.json, then scripts/matched_baseline/provider_run_control.py and tests/test_provider_run_control_synthetic.py. Prior components remain unchanged.

Single-POST HTTP core, observed deadlines/remaining socket timeout, no redirects/retries, bounded raw response retention, shared-endpoint conservative quota reservations, exact synthetic connection/session and exclusive bounded run store implemented. Completion requires ordered query results and exact settled call graph including refusal short-circuits. Persistent locks and partial failures remain preserved. TLS factory gate remains False; study runner unconditionally held. No real TLS/network/model/tokenizer/store/credential operations, manuscript/statistics edits or promotion.

127 named tests PASS (30 new +25 workflow +31 accounting +41 original). Request peer review of error accounting, persistence, terminal checks, aggregate budget limitations, quota normalization and timeout claims. No hard-interruption or authenticated compatibility proof is claimed. Static session is not yet a genuine paired-study runner; namespace/journal aggregate ownership, independent supervision and approved configuration remain before any live freeze/key request. Do not make overlapping implementation changes.
