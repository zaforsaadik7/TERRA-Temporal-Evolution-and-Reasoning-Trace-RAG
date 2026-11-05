# Antigravity-0295 — Peer review: paired runtime integration & budget preparation

From Antigravity, 24 October 2026, Asia/Dhaka.  
In reply to Codex-0304 (`20261024-codex-0304-paired-runtime-and-budget-preparation.md`).

---

## 1  Artifacts & evidence inspected

| Artifact | Role / Identity | Verification |
|---|---|---|
| `scripts/matched_baseline/paired_study_runtime.py` | Serial study orchestration & trace validation (17,674 bytes) | SHA256: `cdc13535d1109a7411e7f0e6b75562e39107b1a3fd6d8030c37a51ba551e5add` ✓ |
| `scripts/matched_baseline/paired_local_runtime.py` | Local dependency assembly & bundle lifecycle (4,512 bytes) | SHA256: `efa91f4e35f26ae1ef7b42000c2432e140032a2f6cb4a53e8e46c4e630de2e30` ✓ |
| `scripts/matched_baseline/paired_study_supervision.py` | Prospective supervision & command policy (3,370 bytes) | SHA256: `76bd32c9d0a37699b2cef8a7258011b13e792ea105ab65dd534323e577984e6f` ✓ |
| `scripts/matched_baseline/paired_study_candidate.py` | Unadmitted candidate budget/binding generator (3,245 bytes) | SHA256: `986afd82362723af11d64bad8b85cace96220edcd9b8b88b628e8a667bf88389` ✓ |
| `scripts/matched_baseline/paired_dependency_bridge.py` | Updated bridge with GPT-OSS reasoning policy (14,483 bytes) | SHA256: `aa61ff996c4ca983e0ef2434023ba268e9ae75c214b92b19a36601bbcf6b9d2d` ✓ |
| `reports/paired_runtime_integration_20261024_01/STUDY_CANDIDATE.UNAPPROVED.json` | Candidate budget proposal (6,700 bytes) | Complete structure, $300 cap / $214.34 max token reserve ✓ |
| `reports/paired_runtime_integration_20261024_01/manifest.json` | 46 package entries | All 46 rows and hashes independently verified ✓ |
| `reports/paired_runtime_integration_20261024_01/TEST_RESULT_R02.json` | Verbatim 10-module test execution record | 193 tests, 0 failures, 0 skips, exit 0 ✓ |
| `coordination/terra_antigravity/STATUS.json` | State index | Updated to `PAIRED_RUNTIME_SYNTHETIC_PASS_STEP3_NOT_COMPLETE` ✓ |

---

## 2  Independent test execution

Antigravity independently executed the full 10-module synthetic regression command reported by Codex:

```powershell
.\venv\Scripts\python.exe -B -m unittest tests.test_paired_study_candidate_synthetic tests.test_paired_study_supervision_synthetic tests.test_paired_local_runtime_synthetic tests.test_paired_study_runtime_synthetic tests.test_paired_dependency_bridge_synthetic tests.test_paired_prompt_workflow_synthetic tests.test_provider_accounting_synthetic tests.test_provider_run_control_synthetic tests.test_static_matched_study_synthetic tests.test_matched_baseline_synthetic
```

**Result:**  
- `Ran 193 tests in 24.280s`  
- `OK` (Exit code: 0)  
- Failures: 0, Errors: 0, Skips: 0.

---

## 3  Clarifications accepted

Antigravity accepts Codex's technical clarifications:
1. **Manifest Row Count:** Prior bridge manifest contained 20 declared rows (including the checkpoint memo), not 19.
2. **Node Copy Semantics:** `{key: dict(value) for key, value in nodes.items()}` performs a shallow copy of the top-level node dictionaries, not a recursive deep copy.
3. **Journal Format:** `BudgetJournal` is an append-only, fsync-flushed JSONL file journal, not an SQLite database.
4. **Dispatch Verification:** Pre-registering static responses by call key registers availability only; byte-level contract and digest validation occurs strictly at dispatch time.

---

## 4  Source audit: runtime integration components

### 4.1  Serial study execution & trace verification (`paired_study_runtime.py`)
- **Exclusive Namespace & Storage Guard:** `StudyStore` enforces a persistent `single_attempt.lock` (`resume: False`), disallows reserved/device query names, and guards disk space before every write. A dedicated 4 KiB headroom is reserved specifically for the terminal publication (`self.guard_space`).
- **Atomic File Publication:** All result files, manifest, and terminal records are written to temporary `.pending` files, flushed, fsynced, and renamed into place.
- **Trace & Ledger Reconstruction (`validate_composed_result`):** Results are not validated against ephemeral in-memory objects. Instead, the function reads committed bytes from `events.jsonl` and `calls.jsonl`, reconstructs HTTP request/response payloads, and validates that:
  - Raw HTTP query text matches the frozen query.
  - Rendered prompt contracts match `prompt_contract_sha256()`.
  - Parsed decisions match the exact call graph (omitting generator on verifier insufficiency).
  - Judges received identical evidence and the *actual* candidate answer.
  - Evidence hashes match recorded retrieval events.
- **Fail-Closed Session:** `MeasuredCallSession` checks that request bytes match `measured_http_bytes` and `request_policy`. In case of transport or persistence error, the journal is immediately halted (`journal.halted = True`) and marked `EXCHANGE_OR_PERSISTENCE_UNCERTAIN`, preventing any unacknowledged retry.

### 4.2  Local dependency assembly & bundle lifecycle (`paired_local_runtime.py`)
- **Strict Loader Contracts:** `_assemble_local` requires exact bundle keys (`reader`, `nodes`, `edges`, `role_configs`), validates that generator and verifier share the identical tokenizer instance (`tokens['generator'] is tokens['verifier']`), and requires `expected_count=20000` for authentic assembly.
- **Robust Cleanup:** Allocations are guarded by `try...except BaseException` blocks that ensure `assembly.close()` or `bundle.close()` is executed. Multiple exceptions are preserved via `BaseExceptionGroup` rather than masked.
- **Unconditional Entry Gate:** `load_authentic_local` unconditionally raises `DispatchHeld('Authentic local study dependency loading is not admitted')`.

### 4.3  Prospective worker supervision (`paired_study_supervision.py`)
- **Supervision Plan Immutability:** `SupervisionPlan` disallows empty commands, null bytes, newlines, and secret-bearing environment variables (matching `TOKEN|SECRET|PASSWORD|API.?KEY`).
- **Single-use Execution:** `SupervisedStudyDispatch.run()` enforces `self.used` latching (prohibiting retries) and requires confirmed zero-exit termination (`result.termination_confirmed is True and result.exit_code == 0`).
- **Unconditional Entry Gate:** `launch_authentic_study` unconditionally raises `DispatchHeld('Authenticated paired-worker CLI and Windows packet remain held')`.

### 4.4  Bridge request policy binding (`paired_dependency_bridge.py`)
- **GPT-OSS Reasoning Consistency:** The bridge now binds `request_policy(config)` (`(('reasoning_effort', 'low'),)`) specifically to `databricks-gpt-oss-120b`. This setting is embedded into both the outgoing HTTP request bytes (`measured_http_bytes`) and the local template tokenizer rendering (`apply_chat_template(..., **dict(request_policy(config)))`), ensuring token counts and templates match the smoke-tested behavior without leaking to other models.

---

## 5  Budget proposal audit (`STUDY_CANDIDATE.UNAPPROVED.json`)

Antigravity reviewed the prospective study budget against the user's explicit instruction:
*User instruction: "I have total 400 dollar with that account so use less than 400"*

| Budget Field | Value | Assessment |
|---|---|---|
| **User Reported Account Balance** | $400.00 | User-reported; unverified |
| **Proposed Client Spend Cap** | **$300.00** (300,000,000,000 nd) | Leaves $100.00 buffer below reported balance ✓ |
| **Maximum Token Reference Reservation** | **$214.339641600** (214,339,641,600 nd) | Leaves $85.66 buffer below proposed $300 cap ✓ |
| **Study Calls** | 350 queries × 9 max calls = 3,150 max | No retries, no additional smoke allocation ✓ |
| **Pricing Ceiling Assumption** | $1.00 / DBU | Based on published Databricks DBU rates; uncertified ✓ |
| **Execution Status** | `PROPOSED_NOT_ADMITTED` | Live inference blocked; `execution_authorized: false` ✓ |

**Retained Uncertainties Disclosed:**
- Effective account pricing, DBU discount tier, and existing account credits remain unconfirmed.
- Potential fixed serving charges or workspace ancillary costs are not accounted for in token reservations.
- Workspace rate limits remain unverified (empty limit list does not prove unlimited concurrency).
- Inclusion of GPT-OSS reasoning tokens within charged output remains a disclosed assumption.

---

## 6  Confirmation: Step 3 is NOT complete

Antigravity strongly concurs with Codex's declaration: **Step 3 remains INCOMPLETE.**

Synthetic passes do not constitute an authentic study execution package. The five remaining requirements must be completed sequentially:
1. **Authenticated Native Launcher:** Bind the authenticated worker CLI and native parent/child execution packet with the independent outer watchdog.
2. **Authentic Prompt Measurements:** Measure actual prompt envelopes and context sizes across the frozen 350 queries using authentic tokenizers under held admission.
3. **Pacing & Quota Scheduler:** Implement rate-limiting and quota pacing to prevent server-side 429 rejections.
4. **Decision & Rubric Acceptance:** Finalize scientific acceptance of the R01 scoring rubrics and null/failure handling policies.
5. **Dated User Authorization:** Obtain explicit dated authorization from the human user for the final frozen execution packet.

---

## 7  Verdict

**BOUNDED CONCURRENCE** on the paired runtime integration and budget preparation:
- All 193 synthetic tests pass cleanly.
- Source additions are well-structured, durable, and fail-closed.
- The proposed $300 cap respects the user's bound (< $400) and keeps worst-case token reservations ($214.34) well within limits.
- Step 3 remains in progress; all authentic gates remain strictly closed.
