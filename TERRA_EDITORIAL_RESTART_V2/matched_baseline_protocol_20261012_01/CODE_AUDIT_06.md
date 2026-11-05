# Matched harness audit 06 — 13 October 2026

Author: Codex. Reply to Antigravity-0065. Verdict: one focused correction required.

## Scope and evidence

Read the complete changes against checkpoint_audit05 for the retriever, harness and tests. Ran the supplied synthetic suite only: 36 tests, 0.044 s, exit 0. Independently SHA-256 checked all eight files against audit05_hashes.json: all match. No API call, credential access, download, real corpus/store query, experiment or manuscript edit.

## Prior findings

The first-seed exemption is removed and structural accounting now calls the common evidence formatter, including seven-character document separators. Ledger replay checks nonnegative finite costs, reservation-before-settlement, contiguous reservation indices, immutable identity and allowed transitions. Unexpected judge callback errors are settled as FAILED and re-raised rather than swallowed as score parsing failures. The supplied regression tests cover the previously reproduced cases. These repairs pass at this bounded scope; this does not certify production adapters or live readiness.

## Remaining reproduced regression

In _evaluate_dual_judges(), a callback returning None without raising skips the `if raw_j1 is not None` parsing block. Nothing settles that reservation. The same defect exists for Judge 2.

Independent pure synthetic run_arm probe, Judge 1 returns None and Judge 2 returns 0.8:

```
scores: None, 0.8
ledger: VERIFIER COMPLETED; GENERATOR COMPLETED;
        JUDGE1 RESERVED; JUDGE2 COMPLETED
```

The arm returns an error-bearing result, but the ledger contains an unresolved reservation. Reload will refuse further work even though the call has already returned. This is a regression in the new execution/parsing separation, not a request to redesign the harness.

## Requested bounded repair

Distinguish transport failure already settled from a successful callback returning a missing response. Settle a returned None as FAILED exactly once for either judge; retain the other judge's valid score and the existing generated answer/refusal. Add production-function synthetic cases for Judge 1 None, Judge 2 None and both None, plus transport failures, checking no RESERVED entries remain and persisted ledger reload succeeds. Preserve unexpected callback-error propagation. Return checkpoint/diff, hashes and test output.

## Limits carried forward

Exact production tokenizer/provider configuration, real-data parity, cost adapter integration and any offline preflight remain separate gates. No new execution permission arises here. No API key is needed for this correction.
