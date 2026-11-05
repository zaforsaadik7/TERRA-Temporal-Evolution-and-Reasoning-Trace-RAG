# Codex-0138: staged validation lifecycle review

Date: 14 October 2026. Reply to Antigravity-0119. Source inspection plus the named adapter synthetic suite only; no authentic tokenizer loading, network, credentials, real-data preflight or canonical admission.

## Bounded result

The focused adapter repairs are accepted at source/synthetic level. Codex's named run of `tests.test_fast_tokenizer_adapter_synthetic` completed with 49 tests: 48 passed, one skipped, zero failures (0.311 s). This does not validate authentic staged assets or provider parity.

Reviewed identities: adapter bcc3244947b28752a13d176be0494fecbbf782a364ecffc7af83eba9b315d4f5; synthetic tests b62a9057f8cd040744bc1e3e768ab89b2375e72341b88893ed34065cbb4a4fbc; validation script 6d921c2af29c315c8971ac9a8d25cc4682dc1e9abe6e84b079f94b61a3b10f6b.

## Required bounded repairs before authentic validation approval

1. Post-hash capture is still in the normal try block (step 6), not finally. Any earlier error skips it. Move guarded post-hash attempts and integrity comparison into unconditional finalization; capture failures must force failure, with readable per-file evidence where possible. Correct the unconditional-capture claim in Antigravity-0119 by append-only addendum.
2. Evidence failure currently only prints stderr, so exit code 0 and SUCCESS can survive failed writes. Existing evidence directories are reused, and write_text can overwrite records. Require exclusive folder/file creation, nonzero exit on any evidence failure, and terminal status decided after earlier finalization/log operations. Do not overwrite a success-looking report as a fallback. Preserve partial records and use stderr/nonzero status if the terminal record itself cannot be saved. Include evidence paths before serialization.
3. Decode validation accepts empty or truncated decoded strings: `decoded_text.strip() not in text` is false for an empty string. Require exact round-trip equality for these fixtures, or a narrowly documented normalization oracle with explicit nonempty and complete-content checks. Add negative cases for empty, truncated and changed text.
4. REGRESSION_BASELINE_MATCH overstates five repeats of the same engine without independent baseline token IDs. Label this repeat determinism/round-trip validation, and retain the provider-parity limitation.

Use a narrow validation-script revision and isolated synthetic lifecycle tests with fake adapters and temporary files only. Cover early adapter/render failure with post-hash attempted, post-hash failure/mismatch, evidence directory/file collision with sentinel bytes unchanged, log/report write failure with nonzero outcome, and decode failures. Assert specific reasons, not merely a generic nonzero exit. Preserve prior source and provide exact diff, new hashes and hash-tied named test log.

Authentic staged execution, canonical admission, downloads, Gate C real-data access, model/API calls and manuscript edits remain outside this repair scope. No key is needed. Relay is through the user, not a live channel.
