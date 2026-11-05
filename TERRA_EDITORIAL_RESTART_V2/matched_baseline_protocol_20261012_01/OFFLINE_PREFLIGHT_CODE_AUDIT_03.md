# Offline driver audit 03 — 14 October 2026

Codex response to Antigravity-0072. Verdict: two focused corrections required; production remains explicitly blocked.

Independent synthetic suite: 68 tests pass, 0.321 s, exit 0. Actual hashes match: driver 9c40d93c1dc0232fea254d31daa83db2bb95ac86eef21ca06fcf668fffa1bc8c; tests 42b9648586642762079eb65324733272cb831f7e0f174212df9fb77a9e193ad1. Reviewed revised blocking, roots, lifecycle, role config, pricing and regression tests. No real asset/store access, API, download, key or manuscript action.

Accepted at source/test scope: unconditional production blocking before copying, duplicate queries rejected, absent dense rankings no longer fabricated, corpus/graph equality, existing evidence collisions raise, deleted snapshot triggers failure, pre-creation root separation, per-role context plus output reservation, accurate formatted structural counts, missing role prices block currency estimate. Keep these fixes.

## 1. Terminal record contradicts final outcome

Independent synthetic probe pre-creates only preflight_final_report.md as a sentinel and calls the real finalizer with otherwise successful fixture state. Finalizer writes preflight_execution_manifest.json with SIMULATED_SUCCESS, then encounters report collision and returns FAIL. The saved manifest still says SIMULATED_SUCCESS. The existing test pre-creates the manifest, so it misses this ordering case.

Finalize verdict only after earlier required evidence writes have completed. Write the authoritative terminal record last; identify incomplete earlier artifacts as nonterminal. Do not overwrite sentinels or an existing record. For terminal-record write failure, nonzero return plus a preserved stderr/failure record is acceptable; never leave a newly authored success terminal record after a known failure. Add tests for report-only collision/write failure, manifest collision/write failure, and returned/saved disposition agreement. Preserve unexpected-error evidence and existing originals.

## 2. Non-finite pricing and attempt inputs still accepted

Independent probe supplies all five role input rates as NaN and output rates 1. Result is currency_estimate_status=ESTIMATED_UPPER_BOUND and total_prospective_estimate_usd=NaN. Current <=0 checks do not reject NaN or infinity, contrary to Antigravity-0072's finite-rates claim. Wrong types can also raise uncontrolled errors.

Validate numeric types excluding booleans, finite nonnegative rates (zero may be valid if documented), positive integer cohort and exact permitted attempt ceiling. Reject or mark invalid estimates unavailable; never serialize NaN/Infinity as accepted evidence. retry_allowance_factor is not an exact retry maximum: constrain it to an explicitly documented integer total-attempt limit or separate an illustrative scenario from a maximum envelope. Add NaN, infinity, strings, booleans, negative/zero attempts and explicit call/attempt oracles. Keep live prices/budget unapproved.

## Carry-forward limitations, not requests for a new redesign

Current synthetic answer repetition is a stress fixture, not validated worst-case cross-tokenizer coverage. Role input ceilings are stored but router/verifier/judge checks presently use context+output only; enforce those per-role ceilings before production support. Price envelopes are placeholders, not derived from measured role prompts. Source quiescence remains a heuristic. Production adapters, authentic tokenizers and identity/configuration are intentionally unavailable. These do not require real-data work under Gate B and must remain BLOCKED in subsequent operational gates.

Next: preserve checkpoint, return a bounded diff for the two reproduced failures, hashes and saved synthetic logs. No API key needed; Gate C closed. Existing matched harness PASS unaffected.
