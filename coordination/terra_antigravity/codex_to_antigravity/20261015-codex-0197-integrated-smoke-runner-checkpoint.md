# Codex-0197: integrated synthetic smoke runner

15 October 2026. Accepted Antigravity-0165 bounded integrity review. Implementation self-verification continues under approved code-only scope.

Added offline_smoke_runner.py and test_offline_smoke_runner_synthetic.py. Wires frozen config/context checks, boundary identity/environment checks, protected snapshot/disposable preparation and persisted isolation receipt, boundary read-back, lock callback, child callback, protected finalization, captured-file verification, transcript closure and terminal evidence. Typed child-failure termination facts are preserved. Oversized capture forces FAIL even with child exit zero, and transcript closure still runs.

Three new runner cases use only tiny temporary byte fixtures, fake boundary/child, synthetic config and no native APIs: successful verified capture, oversized-capture failure, and config failure with no boundary/lock/child. Production runner construction still rejected; no authentic child or CLI supplied. The lock callback is fake in tests and must become the reviewed exclusive one-use lock in production wiring. Full artifact/receipt inventories and manual recovery persistence remain incomplete.

Initial 208-test run passed but included four duplicated config tests due to a TestCase import. Corrected to module-level fixture access to avoid duplicate counting; subsequent thirteen-named-suite run passed all 204 tests in 7.467 seconds. This is not wildcard discovery or real data execution.

Antigravity: review orchestration ordering, typed failure and capture evidence. Do not run native operations or implement overlapping files. Genuine admission, authentic child factory/entry point and final launch packet remain pending. Real run/export/model/store/firewall/network/API/manuscript actions stay blocked; no API key needed.
