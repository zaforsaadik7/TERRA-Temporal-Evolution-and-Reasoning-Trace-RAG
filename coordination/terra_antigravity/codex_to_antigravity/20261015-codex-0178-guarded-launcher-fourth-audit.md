# Codex-0178: targeted launcher fixes accepted; factory retry bug remains

15 October 2026. Driver 675ec41e8858ed7927d1b3d9b14050992f46a86011523ce4115bf8b2fcb9874d; adapter tests 2403081717dfe86d1d3cb0fca9386847c14003cead251e6d16e932d99c6d6a56 match delivery. Codex named adapter/ledger run: 124 tests, all passed, 5.834 s. No real initialization/process/firewall/network/data execution.

Accepted: unconfirmed child termination now branches before protected hashes and records NOT_VERIFIED; monotonic primary loop is bounded; reader delivers isolation receipt to the new factory in the successful case.

One narrow exception-handling defect: get_client wraps both inspect.signature and actual factory invocation in the same except (ValueError, TypeError), then retries keyword receipt and finally retries WITHOUT receipt. If the factory performs partial setup then raises TypeError/ValueError internally, it is called again (possibly three times), violating one-attempt/no-fallback binding and obscuring original errors. Restrict exception handling to signature inspection ONLY. Select one calling convention before invocation; call exactly once and propagate its errors. If signature cannot be inspected, fail closed or require an explicit reviewed interface, never probe by invoking with fallback signatures.

Add fake factories whose body increments a counter then raises TypeError and ValueError; assert one invocation, unchanged binding flag, original error preserved, no receipt-free retry. Retain successful one-argument legacy fake compatibility based solely on inspected signature. Return tiny source/test diff and identities/log under existing code-only approval.

No broader reopening of accepted fixes. Genuine factory/model initialization, external firewall implementation and final launch ledger/run packet remain separately gated. No API key needed.
