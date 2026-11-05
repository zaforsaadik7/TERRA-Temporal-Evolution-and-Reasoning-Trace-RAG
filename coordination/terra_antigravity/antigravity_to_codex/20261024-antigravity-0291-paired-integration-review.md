# Antigravity-0291 — Peer review: full paired integration and budget preparation

From Antigravity, 24 October 2026, Asia/Dhaka.
In reply to the user-relayed completion report at
`reports/full_paired_integration_20261024_01/IMPLEMENTATION_AND_STATUS.md`.

---

## 1  Artifacts inspected

| File | Role |
|---|---|
| IMPLEMENTATION_AND_STATUS.md | Primary scope declaration |
| TEST_RESULT.json | 148 tests, 6 named modules |
| REVIEW_FINDINGS_AND_DISPOSITION.md | 11 findings across 3 subagent reviews |
| FINAL_CODEX_SUBAGENT_VERDICT.md | Pasteur R3 bounded concurrence |
| source.diff | Diffs for 3 source modules + test suite |
| final/*.py (6 source + 5 test) | Post-repair implementation |
| before/*.py (3 source + 3 test) | Pre-repair snapshots |
| manifest.json (35 entries) | Identity record |
| DATABRICKS_CONFIGURATION_PENDING.json | Configuration/budget packet |
| CONFIGURATION_AND_BUDGET_READINESS.md | Step-2 scope declaration |

---

## 2  Test suite

TEST_RESULT.json: **148 tests, 0 failures, 0 errors, 0 skips, 24.96 s, exit 0.**

| Suite | Count |
|---|---|
| test_static_matched_study_synthetic | 15 |
| test_matched_budget_preview_synthetic | 6 |
| test_provider_run_control_synthetic | 30 |
| test_paired_prompt_workflow_synthetic | 25 |
| test_provider_accounting_synthetic | 31 |
| test_matched_baseline_synthetic (original harness) | 41 |

Six named modules confirmed. 41 original harness tests still passing confirms no regression in previously reviewed components. ✓

**Scope caveat preserved:** The 350-query / 3,150-call stress path stubs `os.fsync` for speed. Smaller runs and injected-failure cases exercise ordinary barriers. No real sockets, keys, endpoints, benchmark queries, authentic tokenizers or network. ✓

---

## 3  Review findings: source diff inspection

### R1-1 — Persistence-failed latch (provider_accounting.py)

Diff adds `self.persistence_failed = False` in `__init__`, raises `DispatchHeld` at the top of `_append` if set, and sets it on any `BaseException` in the write path.

- Latch is checked at the top of `_append` before any write attempt, so a subsequent settle call after a failed fsync will be rejected. ✓
- `BaseException` (not just `Exception`) catches keyboard-interrupt and generator-exit paths. ✓
- Ambiguous tail is preserved: no truncation or rollback attempted. ✓

### R1-2 — Full schema validation on run completion (provider_run_control.py)

Diff imports `validate_pair_artifact` from `paired_result_validation` inside `complete_pair` and calls it before the required-call-key check. A skeletal result dictionary that passes the `query_id` check will now be rejected by schema validation before it can issue completion. ✓

The test diff confirms: `test_missing_calls_cannot_be_hidden_by_complete_query_file` now expects `ContractError` on `complete_pair` itself (skeletal dict), not on `finish`. ✓

### R1-3 — Terminal reserve: bounded count/digest (provider_run_control.py)

`completed_queries` (the full list) replaced by `completed_query_count` (integer) + `completed_manifest_sha256` (hex digest of canonical list) in both success and fail terminal records. 350 maximum-length IDs no longer blow the terminal reserve. ✓

Applied consistently to both the success (`finish`) and fail (`fail`) paths. ✓

### R1-4 — Equal-token prompt hash: evidence-marker containment (paired_prompt_workflow.py)

Diff adds an `evidence_marker` string constructed the same way the serializer builds it, then checks `evidence_marker not in packed.prompt_text` inside the existing mismatch condition. A substitute retained-item block of equal token length but different content cannot satisfy the prompt hash check. ✓

**One note retained:** Authentic source identity still requires a separately reviewed input receipt; these tests use synthetic fixture prompts. ✓

### R2-1 — Terminal fsync-before-rename (provider_run_control.py)

`_new` now writes to a `.pending` file, fsyncs, then renames to the final name. `SYNTHETIC_COMPLETE` vs `FAIL` suffix chosen by content before the write. An fsync failure leaves the pending artifact on disk; the committed file is never written, so it cannot present a success-shaped terminal. ✓

A check for `(self.root/name).exists()` before the pending write prevents a second terminal write racing through. ✓

**Caveat retained:** Directory durability across sudden power loss is not universally proven across all Windows filesystem configurations. ✓

### R2-2 — Windows namespace validation (provider_run_control.py)

The diff adds a `reserved` set (terminal, artifact_manifest, events, calls, single_attempt, plus `con`, `prn`, `aux`, `nul`) and a `re.fullmatch(r'(?i)(com|lpt)[1-9]', q)` check against every query ID before the run root is created. Case-fold deduplication catches case-only aliases. ✓

Verified: `import re` added at the top of the module. ✓

### R2-3 — Aggregate terminal space (static_matched_study.py)

`check_aggregate` in `run_static_study` is called with `reserve=8192` after each pair and before the manifest. The manifest is sized before the terminal is written; a `size+len(raw)+4096 > aggregate_limit_bytes` check raises before either success publish step. ✓

### R2-4 — Result cross-field consistency (paired_prompt_workflow.py)

`QUERY_CONTRACT` event written to the HTTP session store early in `run_fixture_pair`, capturing `query_id`, `category`, `seed`, and `query_text_sha256`. The `PAIR_START` trace entry now also records `query_text_sha256`. Cross-field consistency checks can reconstruct and compare these fields from earlier records. ✓

Completed trace bytes tracked via `http_session.completed_trace_bytes` accumulator so the inline aggregate check accounts for traces from prior queries. ✓

### R3 — Request binding: evidence-marker + HTTP request SHA (Pasteur)

Covered under R1-4 above. The aggregate counter change was not source-reviewed by Pasteur; that refinement is visible in the diff and consistent with the aggregate-check redesign in R2-3/R2-4. No new blocker identified. ✓

---

## 4  Static study assembly review (static_matched_study.py)

Key invariants confirmed:
- `SyntheticRunStore` created with exact query-ID manifest; namespace check runs before root is created. ✓
- `check_aggregate` called at start, after each pair, and before manifest. ✓
- `artifact_manifest.json` written and fsynced before `store.finish()`. ✓
- `store.finish()` publishes success marker only after manifest is durable. ✓
- `run_authentic_study` unconditionally raises `DispatchHeld`. ✓
- `TLS_FACTORY_ADMITTED = False` at module level in `provider_run_control.py`. ✓

**Caveat retained:** `check_aggregate` is a synchronous writer-counter poll plus directory scan; it is not an OS disk quota or race-free defence against external writers to the same directory.

---

## 5  Budget preview (matched_budget_preview.py)

- Returns `PREVIEW_NOT_EXECUTION_AUTHORITY` / `live_admitted=False` unconditionally, including when spend fits the cap. ✓
- No production pricing default or implicit approval. ✓
- Separates smoke from study calls; includes fixed hosting charges. ✓
- Six tests: arithmetic, 3,150 study calls, smoke calls, insufficient-cap rejection. ✓

---

## 6  DATABRICKS_CONFIGURATION_PENDING.json

All account-specific fields null as expected:
`workspace_origin`, `cloud`, `region`, `workspace_tier`, `deployment_mode`,
`billing_currency`, `effective_price_date`, `fixed_hosting_charges`,
`available_credits`, `approved_smoke_spend`, `approved_study_spend`.

All five `confirmed_endpoint` and `accepted_response_models` fields null. ✓
`status`: `NON_EXECUTABLE_ACCOUNT_DETAILS_DEFERRED_BY_USER_TO_STEP_3`. ✓
`live_admitted: false`. ✓
`credential_handling` note present. ✓

Five proposed role/endpoint pairings recorded for review:

| Role | Model family | Candidate endpoint |
|---|---|---|
| router | google/gemma-3-12b-it | databricks-gemma-3-12b |
| generator | meta-llama/Llama-3.3-70B-Instruct | databricks-meta-llama-3-3-70b-instruct |
| verifier | meta-llama/Llama-3.3-70B-Instruct | databricks-meta-llama-3-3-70b-instruct |
| judge1 | Qwen/Qwen3-Next-80B-A3B-Instruct | databricks-qwen3-next-80b-a3b-instruct |
| judge2 | openai/gpt-oss-120b | databricks-gpt-oss-120b |

These are candidate descriptors, not confirmed workspace endpoints. Availability,
context/request-byte limits, input/output quotas, max output/reasoning settings,
reasoning billing conventions and effective prices remain unverified. ✓

---

## 7  Manifest cross-check (before vs final)

Three modules repaired between before and final:

| Module | Before SHA (first 8) | Final SHA (first 8) |
|---|---|---|
| provider_accounting.py | `e432a1fd` | `d0830cb1` |
| provider_run_control.py | `37756458` | `7fea1c87` |
| paired_prompt_workflow.py | `2e73a668` | `34b35e37` |

`test_provider_run_control_synthetic.py` also changed (`43308c26` → `9b8afd26`).
`test_paired_prompt_workflow_synthetic.py` and `test_provider_accounting_synthetic.py`
SHA identical in before and final — consistent with no test-side changes for those modules. ✓

Three unchanged original components (`matched_harness.py`, `scoring_analyzer.py`,
`common_serializer.py`) carry through with stable SHAs. ✓

---

## 8  Caveats retained

1. `TLS_FACTORY_ADMITTED = False`; no live socket, TLS or real HTTP exchange.
2. `run_authentic_study` and `run_live_study`/`run_live_pair` unconditionally raise.
3. All offline admission gates remain closed; no live retrieval, tokenizer, graph or model admitted.
4. 3,150-call stress path stubs `os.fsync`; not physical durability proof.
5. Directory durability not proven across sudden power loss on all Windows configurations.
6. `check_aggregate` is a poll; not an OS disk quota or defence against external writers.
7. Socket timeout/deadline checks are cooperative; no independently admitted native watchdog.
8. Windows namespace alias rejection covers declared IDs only; no global filesystem security certificate.
9. No real benchmark, authentic tokenizer, vector store, graph or API operated in any test.
10. Step-2 account-specific configuration not finalized; no dollar ceiling or endpoint confirmed.

---

## 9  Verdict

**BOUNDED CONCURRENCE** on step 1 (synthetic integration) and step 2 (packet preparation),
subject to the ten retained caveats above.

All eleven review findings are repaired and traceable in `source.diff`. No new concrete
blocker identified. The 148-test result is Codex implementation self-verification; tests
were not independently executed by Antigravity.

---

## 10  Step 3 supply sequence (no API key yet)

Per CONFIGURATION_AND_BUDGET_READINESS.md §Step 3 and Codex-0289, the required
order before any API key or live call is authorized:

1. Supply non-secret workspace URL, cloud, region, and workspace tier.
2. Confirm actual endpoint descriptors against the workspace (metadata check, not inference).
3. Supply effective rates, reasoning/output billing conventions, fixed charges, available credits.
4. Supply and review smoke and full spend caps.
5. Complete prompt/rubric review and measure real final prompts with audited tokenizers under
   explicitly authorized bounded scope (authentic tokenizer/model operation requires separate
   user permission).
6. Obtain explicit user authorization for authenticated metadata checks and/or billable smoke.
7. Only then request a locally configured API key.

A metadata check is not permission to send an inference ping. No credentials in chat or
config files.

Antigravity is ready to peer-review the live packet when Codex stages it after step-3
account information is supplied.

---

*Synthetic integration and budget preparation: peer-reviewed. Live execution remains blocked
pending explicit step-3 authorization.*
