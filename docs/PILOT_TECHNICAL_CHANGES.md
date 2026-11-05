# Pilot Technical Changes (Round 10: Tasks D1–D5)

This document details the technical fixes implemented in the audit and model-calling infrastructure following Round 9 pilot evaluation.

**Invariant Declaration**: None of these technical changes alters labels, prompts, arms, queries, or analysis definitions. All taxonomy definitions, prompt templates, retrieval algorithms, evaluation rubrics, statistical hypotheses, and mathematical test definitions remain identical to pre-registered specifications.

---

## 1. D1: Judge Response Parsing & Token Doubling

### Problem
In Round 9, 8 of 8 live judge calls to `databricks-gpt-oss-120b` failed with `TypeError: expected string or bytes-like object, got 'list'`. The provider returns `message.content` as a structured list of content blocks (combining reasoning/thought blocks with text blocks) rather than a flat string. Additionally, reasoning models consuming significant reasoning tokens risk truncating the final JSON payload under a 1024-token budget (`finish_reason == "length"`).

### Technical Fix
- **Content Block Parsing**: `extract_text_from_message_content` inspects `message.content`. If `content` is a list of blocks, it extracts and joins all blocks with `type == "text"` (or containing a `"text"` key) while explicitly filtering out reasoning blocks (`type in ["reasoning", "thought", "thinking"]`). Handles `None`, strings, dicts, and SDK response objects.
- **Finish Reason Tracking & Token Doubling**: Captures `finish_reason`. If `finish_reason == "length"`, doubles `max_tokens` on retry (`1024 -> 2048 -> 4096`).
- **Failure Logging**: On any parse or validation failure, appends the raw content prefix (first 2,000 characters), judge model, `query_id`, `arm`, attempt number, and error message to `logs/judge_failures_<suite>.jsonl`. Failures are never written to the main cache.

---

## 2. D2: Evidence Quote Verification as Audit Aid

### Problem
In Round 9, 6 of 8 calls to `databricks-qwen3-next-80b-a3b-instruct` failed quote verification due to brittle exact-substring matching on raw text containing markdown links `[text](url)` and ellipsis jumps (`...`). Furthermore, failing quote verification previously converted a valid legal classification into a `JUDGE_ERROR`, which biased exclusions toward complex or lengthy answers.

### Technical Fix
- **Comprehensive Normalization**: Both evidence quote and generated answer are normalized via NFKC Unicode normalization, whitespace collapsing, curly quote/dash unification, markdown link stripping (`[text](url)` replaced with `text`), and backtick/asterisk stripping.
- **Ellipsis Handling**: The quote is split on `"..."` or ellipsis character `'…'`. Every segment with length $\ge 12$ characters must be a substring of the normalized answer. The total quote length must be $\le 200$ characters.
- **Audit Aid Decoupling**: If quote verification fails across all 3 retry attempts, the judge's parsed taxonomy label is KEPT, and `quote_verified` is set to `False`. `JUDGE_ERROR` is returned only if the JSON is unparseable or the classification label is not one of the pre-registered 5 taxonomy classes.
- **Reporting**: Reports the per-judge `quote_unverified` count in the evaluation report and item-level audit trail.

---

## 3. D3: Never Cache `JUDGE_ERROR`

### Problem
In Round 9, when a technical fault caused `JUDGE_ERROR`, that error was written into `scratch/pilot_obscure_judge_cache.json`. When resuming or retrying, the cache lookup succeeded and returned `JUDGE_ERROR`, preventing the engine from ever retrying the query.

### Technical Fix
- `judge_cache[key] = judgment` and `save_judge_cache_atomic(...)` are guarded by `if judgment.get("classification") != "JUDGE_ERROR":`.
- Failed judgments go solely to `logs/judge_failures_<suite>.jsonl`.
- Resuming execution automatically retries any un-judged or failed evaluations.

---

## 4. D4: Atomic Saves with Windows File-Lock Retries

### Problem
On Windows systems, concurrent background tasks, indexing services, or virus scanners frequently place transient locks on open JSON cache files, triggering `PermissionError: [WinError 5] Access is denied` during `os.replace(temp_path, target_path)`.

### Technical Fix
- **10-Attempt Backoff Loop**: When `os.replace` encounters a `PermissionError`, it retries up to 10 times with a 0.3-second exponential/linear backoff.
- **Direct fsync Fallback**: If all 10 replace attempts fail, the target file is written directly with `flush()` and `os.fsync()` to ensure data integrity without loss, leaving the `.tmp` file as a backup.
- Implemented in both `save_judge_cache_atomic` and `ModelCallCounter.save_state`.

---

## 5. D5: Call Counter Single Choke Point & Deduplication

### Problem
In Round 9, telemetry rows for router, grader, and generation calls appeared in identical duplicate pairs (~2 ms apart), artificially doubling the recorded outbound call count (recording 28 calls instead of the real 17) and prematurely tripping the pilot hard cap.

### Technical Fix
- **Single Choke Point**: Patches `Completions.create` once via `patch_completions_create_once()` with re-entrancy protection (`_CALL_STATE.in_call`) to prevent recursive double-counting when SDK or client wrappers nest calls.
- **Unique Call ID & Deduplication**: Each call generates a UUID `call_id`. Duplicate call IDs within the same dispatch are ignored via thread-locked `_PROCESSED_CALL_IDS`.
- **Verified Invariant**: Tested offline via mock engine: exactly one outbound engine call increments the call counter by 1 and writes exactly one telemetry row to `logs/call_telemetry_<suite>.jsonl`.
- **Pilot Hard Cap**: Raised to 120 calls to accommodate the complete 24-judgment pilot evaluation panel with retries.

---

## 6. E1: Quote Handling Without Length Cap & Retry Decoupling

### Problem
In the Round 10 pilot evaluation, Qwen returned 10 of 12 quotes unverified, and GPT-OSS returned 2 of 12, mostly because quotes ran 252–567 characters against a 200-character cap despite being authentic substrings of the answer. Furthermore, an unverified quote triggered 3 retries even though the parsed label was retained regardless, causing unnecessary API call overhead (53 calls for 24 judgments).

### Technical Fix
- **No Length Cap on Substrings**: `validate_evidence_quote` performs substring verification across normalized text and ellipsis fragments without enforcing any maximum length cap.
- **Separate Overlength Tracking**: Records `quote_len` (integer) and `quote_overlong` (`bool`, True if `len > 200`) as distinct audit fields.
- **Zero Retries on Quote Verification**: An unverified quote sets `quote_verified = False` and logs a failure warning to `logs/judge_failures_<suite>.jsonl`, but retains the parsed label immediately without retrying. Retries (up to 3) are strictly reserved for: unparseable JSON, invalid classification labels, `finish_reason == "length"`, and API/network errors.

---

## 7. E3: Blinding & Text Marker Prevalence Reporting

### Context
Blinding in open-domain legal generation is inherently imperfect: Arm 3 (Full TERRA) can incorporate `[OVERRULES / REPUDIATES]` tags from its prompt context, while Arm 4 contains `[CITES]`, and retrieval arms emit interactive markdown case links `](/case/` that direct generation lacks.

### Technical Fix
- **Prevalence Metrics**: In the analysis report, computes and reports per arm:
  1. Share of answers containing the literal `"[OVERRULES / REPUDIATES]"`
  2. Share of answers containing `"[CITES]"`
  3. Share of answers containing a markdown case link matching `"](/case/"`
- **Per-Judge Audit Counts**: Reports `quote_unverified` and `quote_overlong` counts per judge model.
- **Strictly Non-Exclusionary**: These metrics serve purely as descriptive transparency aids and limitations reporting; they trigger zero data exclusions or test adjustments.

---

## 8. E4: Runner Safeguards for Full Obscure Generation Stage

### Technical Fix
- **Mandatory Confirmation Flag**: Running `--live` on any non-pilot suite (e.g. `obscure`) strictly mandates passing `--confirm-full`. Missing `--confirm-full` causes immediate refusal (`SystemExit`) before any environment setup or model dispatch.
- **Consecutive Error Abort**: If 3 consecutive API errors occur across model requests, the runner immediately halts with `RuntimeError`. Because each successful item is committed to disk via `save_cache_atomic`, the cache on disk is always valid JSON, and resuming execution (`--resume` / rerun) safely skips all completed items.
- **Outbound Call Cap (700 Calls)**: Enforces an outbound model call cap of 700 calls in `ModelCallCounter` for the full generation stage, guarding against runaway loops.
- **Atomic Save Resilience**: Added the 10-attempt `PermissionError` retry loop with 0.3s backoff and direct `fsync()` fallback to `save_cache_atomic` in `run_obscure_overruled_inference.py`.

---

## 9. F1: Telemetry Hygiene & Run Isolation

### Context
Offline unit-test and canary runs previously emitted rows into `logs/call_telemetry_obscure.jsonl` when mock clients triggered patched methods, causing the telemetry file to accumulate 502 rows (300 test rows and 202 live rows), even though the call counter correctly recorded 202 calls.

### Technical Fix
- **Field Addition**: Added `run_id` and `mode` (`live` | `test`) to every emitted telemetry row.
- **Path Isolation**: Calls originating in offline unit tests, mocks, or with `mode="test"` write strictly to `logs/test_telemetry/call_telemetry_<suite>.jsonl`, never touching the live telemetry logs.
- **Run ID Filtering**: Breakdown summaries now support filtering by `run_id`.
- **Artifact Archiving**: Archived existing polluted file unchanged as `logs/call_telemetry_obscure_polluted_v0.jsonl` and created `logs/full_artifacts/call_telemetry_obscure_live_only.jsonl` containing exactly 202 rows matching `logs/call_counts.txt`.

---

## 10. F2: Judge-Stage Safeguards in Audit Script

### Technical Fix
- **Judge Call Cap (600 Calls)**: Enforces a hard cap of 600 total judge calls per suite in `scripts/audit_obscure_overruled_benchmark.py` and via `ModelCallCounter`, preventing runaway API loops.
- **5-Consecutive-Error Abort**: Tracks consecutive judge API errors across calls. If 5 consecutive judge calls fail with API exceptions, execution immediately aborts with `RuntimeError` while preserving the existing cache on disk via `save_judge_cache_atomic`.
- **Resumability**: The judge cache is committed atomically after every valid judgment, ensuring zero loss of completed items if an abort occurs.

---

## 11. F3: famous_d1 Suite & Prompt Template Verification

### Technical Fix & Verification
- **Prompt Template Selection**: Verified that `suite="famous_d1"` selects `JUDGE_PROMPT_D1_TEMPLATE` (containing `- Target Precedent:` and `- Modern Rule:`), while `suite="obscure"` selects `JUDGE_PROMPT_TEMPLATE` (containing `- Target Historical Precedent:` and `- Historical Holding:`).
- **Schema Parity**: Verified that mock generation records for `famous_d1` match the 30-field schema of `obscure` records exactly.
- **Audit Acceptance**: Verified that `audit_obscure_overruled_benchmark.py` accepts `--suite famous_d1`, loads all 19 D1 items (9 with EEG overruling cases), and completes report generation without errors.
- **Runner Cap**: Configured `max_cap = 400` calls for `--suite famous_d1` in `run_obscure_overruled_inference.py`.

---

## Verification Summary
All technical changes (D1–D5, E1, E3, E4, F1–F3) have been verified offline:
- Task D6 tests (a)–(g) logged to `logs/judge_fix_tests.txt`.
- Task E2 tests (a)–(c) logged to `logs/judge_fix_tests_v2.txt`.
- Task E4 safeguard tests (1)–(3) logged to `logs/runner_safeguard_tests.txt`.
- Task F2 safeguard tests (1)–(2) logged to `logs/judge_safeguard_tests.txt`.
- Task F3 famous_d1 tests (1)–(3) logged to `logs/famous_d1_tests.txt`.
- Dual-judge offline regression suite (11 unit tests) logged to `logs/judge_unit_tests.txt`.
- Independent corpus slice verifier passed (`logs/independent_corpus_slice_verifier.txt`).
- Temporal leak audit passed (`logs/leak_audit.txt`).
- Arm 4 context audit passed (`logs/arm4_context_audit.txt`).
None of these changes modifies any benchmark query, rubric, prompt, arm definition, or statistical test specification.

