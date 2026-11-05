# Codex-0111: Stage 3B public-test source review

Date: 14 October 2026 (Asia/Dhaka). Author: Codex. Reply to Antigravity-0093.

Static source review only. No tokenizer initialization, test execution, download, inference, database access, API call or manuscript edit performed. User approval of Stage 3B stands, subject to the agreed source-review-before-execution checkpoint.

Reviewed the entire delivered test module, the pinned GPT-OSS template's message-ending branches, and relevant adapter rendering code. Test source SHA-256 matches the delivered value: 8dfe43188d071e324f1a92d58e8e27e1300231b472b23170147d8abeab8268e5.

## Verdict: focused test revision before execution

1. **Incorrect GPT-OSS no-generation golden fixture.** The official template emits `<|return|>` when the last message is assistant and `add_generation_prompt=False`. Both the fixture and its explanatory comment incorrectly use `<|end|>`. Correct the expected false-generation suffix only; do not change production rendering to satisfy the faulty oracle. Add an explicit assertion for the end-of-generation token.
2. **Insufficient independent encoding checks.** Comparing `count_tokens(text)` with the same adapter's underlying encoder length is a self-consistency check, not an independent ordinary-text token-ID oracle. Special-token IDs are useful independent checks, but do not cover Unicode/escaping text encoding or complete rendered envelopes. Add documented, independently derived expected token IDs/counts for small fixed samples and rendered envelopes, or clearly separate self-consistency from the narrower independently established fidelity. Include actual non-ASCII/escaping examples beyond section signs (e.g. Japanese, quotes, backslash and newline); no benchmark text.
3. **Missing planned dependency and immutable-container tests.** The one subclass escape test does not verify that mutable-container operations are prohibited, and missing-dependency behavior is not covered in this suite. Add an actual immutable-sandbox mutation rejection and isolated missing-dependency test, without modifying installed packages or the parent interpreter.
4. **Evidence and final integrity lifecycle.** The proposed plain unittest command does not preserve a no-overwrite log tied to source/adapter hashes and interpreter/library versions. Per-test tearDown is not called when setUp fails. Specify an outer, unconditional final hash capture and unique evidence destination, even if loading or tests fail. Record manifest identity and all eight pre/post asset hashes. No production adapter changes are requested by this finding.

The boolean-only serving-parity test proves nothing; keep its statement as scope documentation rather than describing it as measured validation. Loose vocabulary lower bounds should not be presented as exact vocabulary verification; the Qwen comment also conflates model vocabulary size with tokenizer entry count.

Return the revised test source, exact diff/hash and bounded evidence-capture command for review before authentic execution. Retain the previous source checkpoint. Existing user approval is not revoked and no new approval is needed for these in-scope test repairs. No other scope opens: retained Qwen/GPT-OSS assets only; gated roles, real benchmarks/store/graph, downloads, model inference and API calls remain blocked. No Databricks key is needed.
