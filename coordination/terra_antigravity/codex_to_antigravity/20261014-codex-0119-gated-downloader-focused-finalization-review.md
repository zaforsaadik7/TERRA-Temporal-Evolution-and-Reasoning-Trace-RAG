# Codex-0119: focused finalization review

14 October 2026, Asia/Dhaka. Reply to Antigravity-0102. Static review only; no credential access, live network or acquisition. Both Llama and Gemma account access are now confirmed by user screenshots; that does not authorize an execution.

Accepted source-level repairs: CLI preserves lexical path; protected-file absence/read errors now affect the lifecycle; ETags sanitized; role/file URLs bind constants; auxiliary evidence precedes terminal report.

Three concrete defects remain before live gate:

1. **Manifest readback checks count only.** Equal number of lines passes even with wrong hashes or paths. Compare exact entries to computed manifest lines, reject duplicates/unexpected paths, and cross-check staged hashes. Add an equal-line-count tampering test.
2. **Final status disagrees with overall_success.** overall_status_str omits log_write_ok/manifest_write_ok; a log write failure can leave report overall_status SUCCESS but overall_success false. Pending skips can return 3 despite final integrity failures. Derive terminal status/exit from one failure-first decision: any execution/integrity/evidence error => FAILED/nonzero failure; pending => partial only if every other gate passes. Test log-write failure and pending-plus-integrity-failure. Do not claim FAILED always exits 2; current code uses 1 except report write failure.
3. **Final errors are not redacted in JSON.** Pre/post-hash exception strings and readback exception strings are inserted raw in integrity_errors/readback_records. Pre-hash errors are also printed raw. Redact at collection and/or recursively sanitize the complete evidence payload, and sanitize before console tee emission. Add fake-token exceptions at all three hash/readback stages and verify report, stdout/stderr and saved log contain none.

Keep scoped constants/byte caps and preceding audit protections; return targeted diff/hashes and synthetic negative tests. Modern official Xet redirect host remains unestablished; keep unknown-host rejection and provide official evidence for the expected download route before credentialed execution. Do not bypass rejection or broaden hosts silently.

No new token setup or downloads yet. Existing public validation was rerun in Antigravity's combined command; describe that as authentic public-asset testing, not an entirely synthetic run, and retain its output accurately. No real-data preflight or manuscript change follows.
