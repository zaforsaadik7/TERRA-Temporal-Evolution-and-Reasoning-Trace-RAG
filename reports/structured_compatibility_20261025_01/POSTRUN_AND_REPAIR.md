# Structured-output probe: stopped before API dispatch; local bug corrected

25 October2026, Codex implementation self-verification. User approved preparing/running a five-role fictional-input probe under$1 client cap,no retries/no full study,then instructed continue. The incomplete trailing clause in the original reply is preserved literally in HUMAN_PERMISSION.json and is not interpreted as extra permission.

## Actual attempt

One attempt was frozen under plan SHA256 `4f37e57d4a241f0af38e7f7cf1071e5b9f4d1e473c19fa6148cfa1817f0a5d4b`.274 named regression tests passed before admission. Closing input verification covered29443 files and three runtime/tokenizer roots; corpus,graph and MiniLM weights were excluded. Full-study entry and anchor stayed held throughout. Only the separate probe source/anchor were temporarily admitted.

The native worker exited1 after4.53 seconds with `STOPPED_NO_RETRY`,failure_type DispatchHeld. Its single monetary journal entry is HEADER:zero reservations,zero requests/responses,zero completed roles,reference exposure0. The router messages were locally measured at76 tokens. Authentic tokenizers loaded locally; no embedding inference or benchmark retrieval occurred. The bearer callback is deferred until after a successful reservation; this path was never reached, so no credential was loaded by this attempt.

The real endpoint/schema acceptance and usage deltas are therefore STILL UNTESTED. No inference about structured-output compatibility follows from this local failure. No second attempt,paid retry or resume was issued.

## Confirmed local cause and correction

`reserve_with_pacing()` checked elapsed time against the default zero-second wait allowance before its first capacity check. A real monotonic clock advances between reads; therefore even an available endpoint was rejected as 'Local quota wait deadline reached before dispatch'. Offline reproduction with clock readings0 and0.000001 confirms that exact DispatchHeld before any transport. Earlier frozen-clock fixtures concealed the edge case; this is an implementation/test gap, not a provider failure.

After native cleanup and full postchecks completed, the shared pacing source was corrected: a zero-wait policy permits one immediate capacity check. If unavailable, RateWait still propagates with no sleep, no monetary reservation and no HTTP retry. Nonzero deadlines,cancellation and backward-clock checks remain unchanged. Two focused advancing-clock tests cover available/unavailable capacity; an end-to-end advancing-clock static transport probe covers all five roles. Existing request schemas,scientific prompts,strict parsers and accounting rules are unchanged.

`REPAIR_TEST_RESULT.json` and `REPAIR_TEST_OUTPUT.txt` capture the final named regression result and stable code/test hashes. Before-source and executed probe bytes are retained separately. Post-repair code is a new source generation,not retrospectively the executed generation.

## Cleanup and integrity

Native terminal records confirm full-tree termination and closed handles. The separate probe source gate and anchor were restored to held bytes; full-study gates never opened. Pre/post input observations match exactly:29443 files/three roots,digest `0778cda5d95391de988aca885ab532131e70971cdf52a2828076a0730f8be582`. This observation precedes the expressly documented pacing repair. Attempt locks,zero-call journal,trace and frozen controls remain preserved. No manuscript/statistics changes or promotion.

The next checkpoint is review of the local pacing repair and a fresh single-probe freeze/permission. No next paid execution is authorized by this report. The prior671-call failed study and$10.847801358 conditional cost remain separate historical evidence.
