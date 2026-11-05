# Codex-0292 — provider contracts and usage accounting, synthetic checkpoint

Codex, 24 October 2026. Implementation self-verification, user-relayed only.

Under the user's instruction to proceed, implemented scripts/matched_baseline/provider_accounting.py and tests/test_provider_accounting_synthetic.py. Read reports/provider_accounting_20261024_01/IMPLEMENTATION_AND_TEST_REPORT.md and manifest.json, then actual source/tests. Prior matched harness/serializer/analyzer remain unchanged.

72 named tests PASS: 31 new contracts/accounting tests plus 41 original matched-harness tests. No network, secret access, models, stores, canonical changes or manuscript/statistics work. dispatch_live remains unconditionally held; synthetic dispatch accepts static responses only. Prices and endpoints in tests are fixtures, not user-approved spend/settings.

Please inspect pre-dispatch persistence, uncertain billing retention, integer rounding, usage-before-content rejection, accepted identities, duplicate calls, simultaneous reservations and failure-path poisoning. Caveats explicit: one process owner, thread-level lock only; journal audit reader not tamper-authentication; no automatic resume; no network adapter, rate scheduler or live run composition yet. Provider charges over a violated reservation are recorded and stopped, not erased or claimed impossible. Unsupported reasoning-price conventions/fixed hosting charges remain outside this component.

Return source-backed corrections or bounded concurrence. Do not implement overlapping edits. Next code-only batch binds real prompt/rubric/parsers and orchestration, then separately held provider transport. No key needed for peer review.
