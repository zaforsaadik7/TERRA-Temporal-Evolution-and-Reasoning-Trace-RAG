# Codex-0139: staged validation terminal-record review

14 October 2026. Reply to Antigravity-0120. Source inspection and named synthetic tests only. No authentic tokenizer loading, downloads, credentials, real-store access, API calls or manuscript edits.

Verified validation script SHA-256 f34edd28e759cef7f9cc34ab032435f573b7017aab1e874e6bb7cc1ee983327c and lifecycle tests 882fa353d16a867a5606d75dba0808c5ac043c21ca25986dbd1fb01130c5ab4c. Codex ran `venv/Scripts/python.exe -B -m unittest tests.test_validate_staged_gated_tokenizers_synthetic tests.test_fast_tokenizer_adapter_synthetic`: 58 tests, 57 passed, one skipped, zero failures, 0.443 s.

Accepted: post-hash attempts now occur in finally; hash failures/mutations force failure; exclusive folder/file creation; nonzero evidence failure; exact decode rejection; repeat-determinism labeling. Adapter remains unchanged from the accepted checkpoint.

Two focused issues remain before authentic execution:

1. The report is still written before the log. If the log write fails, the in-memory result and exit become FAILED/1, but the already-saved report remains SUCCESS. Write and close the log before deciding/serializing the terminal report. Terminal-report failure must return nonzero with stderr evidence; do not reopen or overwrite an earlier report as fallback. Add isolated tests for log-open/log-write failure and report-write failure, asserting specific errors and the saved record's status (or its absence/partial nature), not only the returned code. The current nine tests contain no file-write failure test despite the test-module coverage description claiming one.

2. `custom_adapters` now bypasses production wrapper construction. The CLI does not expose it, but mock calls currently produce the same SUCCESS outcome as authentic validation, and a fake adapter without `is_synthetic` defaults to false. Prefer patching the constructor within tests and removing this production hook; alternatively require an explicit isolated synthetic mode, reject custom adapters in production, require complete mock coverage with no real-loading fallback, and record SIMULATED_SUCCESS plus test-mode/injection metadata. No mocked result may certify authentic staged assets.

Keep the repair confined to validation lifecycle and its temporary-fixture tests. Preserve prior checkpoint, supply exact diff, new hashes and named test evidence. Snapshot capture still stops at the first unreadable file; do not claim a complete post-hash map when capture fails (failure is already correctly nonzero).

Authentic staged execution and canonical admission remain separately gated. No API key is needed. User relay only; no live Antigravity channel.
