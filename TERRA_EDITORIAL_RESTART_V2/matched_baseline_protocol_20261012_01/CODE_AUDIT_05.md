# Matched harness audit 05 — 13 October 2026

Reviewer: Codex. Verdict: corrections required; no live execution approval.

Scope: reviewed revision and checkpoint diff; ran only the supplied synthetic suite and independent temporary-data probes. No API, credential, real corpus/store query, download, experiment or manuscript edit.

## Confirmed repairs

All 30 supplied tests pass (0.047 s, exit 0). All eight source/test SHA-256 hashes match Antigravity-0064.

Independent probes confirm: normal settled ledger reload retains $0.10; a depth-two chain returns s/a/b, not c; EASY zero-hop returns only s; an incurred $1.10 against a $1 cap is recorded as BUDGET_BREACH before ConfigurationError. These earlier defects are closed at the tested scope. Independent partial judge scores are now retained in the source.

## Two reproduced blockers

1. **Structural cap bypass.** With max_structural_chars=10 and a first seed holding of 1,000 characters, retrieve() returns that entire holding. The admission condition exempts the first seed through `if ordered_visited`. Furthermore `_compute_node_chars` sums field values, not formatted evidence: identifiers, labels and separators are absent. Remove the first-seed exemption and define the structural representation precisely; measure that representation consistently. Do not claim an exact serialized limit unless tested against the actual formatter. Preserve the separate common token-packing limit.

2. **Malformed ledger accepted on reload.** A synthetic standalone COMPLETED entry with call_index=999 and cost_usd=-10 is accepted without a preceding reservation. Cumulative spend becomes -$10; a subsequent $5 reservation then passes a $1 cap. Replay must validate schema, finite nonnegative quantities, permitted statuses, reservation-before-settlement, immutable call identity/index, unique monotonic reservation indices, and exactly one terminal transition. Reject malformed journals before dispatch; never repair or overwrite them silently.

## Source-level follow-up

The judge handler still catches ValueError from the callback itself together with conversion/range errors. An unexpected programmer ValueError is therefore treated as a failed score and execution continues. Separate callback invocation from narrowly handled response parsing; unexpected programming failures must stop with preserved failure evidence. Add a callback-ValueError negative test alongside the intended malformed-score test.

## Bounded next revision

Preserve this checkpoint, revise these controls, and add focused synthetic regression tests exercising production functions. Include first-seed oversize, formatted-character boundary, malformed ledger cost/transition/identity/index cases, and programmer versus parsing failures. Return exact diff, hashes and saved test output. Do not reopen verified depth/EASY/over-cap fixes unnecessarily.

This remains a synthetic prototype: provider pricing/usage wiring, exact production tokenizer, real corpus parity and offline preflight are not certified by this audit. No API key is needed for these repairs. Live execution remains blocked pending the later explicitly authorized gates.
