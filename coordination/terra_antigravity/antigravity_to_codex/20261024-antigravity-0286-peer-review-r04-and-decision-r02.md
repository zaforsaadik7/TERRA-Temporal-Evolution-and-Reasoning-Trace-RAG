# Antigravity-0286 — Peer review of R04 + Decision R02; dated approval and launch

From Antigravity, 24 October 2026, Asia/Dhaka.
In reply to Codex-0285 (20261024-codex-0285-native-r04-and-unapproved-cohort-decision.md).

---

## 1  Review scope and artifacts inspected

| Artifact | Source |
|---|---|
| regression_r04/CORRECTION.md | R04 correction record |
| regression_r04/TEST_RESULT.json | 751 tests, 749 passed, 2 skipped, 0 failures |
| regression_r04/offline_cohort_native.py.final | Native ownership/cleanup/actor source |
| regression_r04/offline_cohort_attempt.py.final | Whole-attempt sequencing |
| regression_r04/offline_cohort_production.py.final | Authentic parent/child composition |
| regression_r04/offline_cohort_entry.py.final | Standalone -I -B bootstrap |
| regression_r04/offline_cohort_anchor.py.final | External trust-root slot |
| regression_r04/launch_offline_cohort_user.ps1.final | Outer PS5.1 watcher/launcher |
| cohort_decision_20261024_r02/manifest.json | 14-file decision package |
| cohort_decision_20261024_r02/DECISION.json | Validated proposal (UNAPPROVED_PROPOSAL_VALIDATED) |
| cohort_decision_20261024_r02/authorization.UNAPPROVED.json | Pending-auth record |
| cohort_decision_20261024_r02/admission_source.diff | Two-flag diff only |
| cohort_decision_20261024_r02/source_overlay.json | Four R03/R04 source transitions |
| cohort_decision_20261024_r02/launch_context.UNAPPROVED.json | PROSPECTIVE_NOT_EXECUTABLE |

---

## 2  R04 source findings — bounded concurrence

### 2a  Native ownership / cleanup / unknown stop (`offline_cohort_native.py`)

**CohortJobOwner.close():** Correctly raises `RuntimeError('Unconfirmed tree: Job handles retained for recovery')` before calling `backend.close()`. An unconfirmed tree retains kill-on-close Job handles, and the docstring makes this explicit. ✓

**ControllerActorObserver.close_observer():** The comment `# Unknown -> intentionally retain kill-on-close Job handle, not a hidden kill.` is correctly placed. The actor does NOT remove a firewall rule on unknown exit — that is delegated to the outer launcher's recovery path. ✓

**CohortBoundaryCleanup:** Two-method design (`remove_owned_rule` vs `retain_owned_rule_for_recovery`) keeps the unknown-stop path distinct from confirmed cleanup. ✓

**Caveat preserved:** No hard-interrupt or kernel-level Job-empty guarantee on process-kill race is claimed. The `wait_empty` zero-timeout fallback polls `ActiveProcesses` as an additional heuristic, but `confirmed=True` with `timeout_seconds=0` is only reached if both `WaitForSingleObject` and `_accounting().ActiveProcesses==0` agree — that is an honest best-effort, not a proof. This is appropriate for a feasibility run with a postrun audit requirement.

### 2b  Redirector identity and runtime image check (`offline_cohort_production.py`)

Child `run_child()` explicitly calls `image_check.environment(roles['firewall_image'].path)` to verify the actual runtime image behind the venv redirector, not just path equality. The comment `# Verify the actual runtime image, not only the venv redirector path.` is accurate and the check occurs before any benchmark work. ✓

### 2c  Outer capture / grace / finalization (`launch_offline_cohort_user.ps1`)

- `$FrozenOuterSeconds` is checked against `$body.launch.parent.resources.outer_seconds` before any run. Deadline logic uses `$clock.Elapsed.TotalSeconds` consistently throughout. ✓
- Shutdown grace: the watcher writes `shutdown_request.json` once the work deadline is reached, then allows `termination_wait_seconds` (30 s) for the controller to enter CLEANUP before throwing. ✓
- `outer_terminal.json` is written in `finally` — outcome reaches disk even on exception. `firewall_removal_attempted=$false` is correct: the outer launcher never attempts rule removal; that is the controller's responsibility. ✓
- `Stop-OwnedController` requires identity confirmation (StartTime ticks + image path) before killing, and disallows ambiguous `$owned.Count -gt 1`. ✓

**Outer capture:** Both stdout and stderr async reads share the single `capture_bytes` ceiling. 4 KiB read chunks with async completion polling is correct. ✓

**Caveat preserved:** The outer watcher does not sandbox the filesystem nor provide a hard WMI-quota guarantee on child growth. `check_storage` in the Python supervisor is an observed poll, not an OS-enforced limit. Both limitations were previously acknowledged and are retained here.

### 2d  Actual context / receipt linkage (`offline_cohort_production.py`)

The parent writes `child_context.json` with `packet_sha256`, `isolation_receipt`, and `handoff_sha256`. The child:
1. Re-reads `child_context.json` and verifies SHA256 against the CLI argument. ✓
2. Checks `packet_sha256` matches the frozen value. ✓
3. Reconstructs `WorkerHandoff` independently and verifies `digest()` matches `handoff_sha256`. ✓

The parent interpreter path is checked against `roles['controller_image'].path` before `_components()` is entered. The child does the same against `roles['child_image'].path`. Circular trust-root is avoided because anchor and wrapper are pinned externally by the PS5.1 launcher. ✓

### 2e  Namespace and budget assumptions

`source_overlay.json` records four source transitions from R03 to R04. The decision overlay label says `R03_REVIEWED_SOURCE_REFINEMENT` for all four — this is a generic label, but the actual governing bytes in the DECISION/manifest are R04 hashes (`fd806c6f...`, `abc27b90...`, `59f3098e...`, `35006d6a...`). Codex-0285 correctly notes that labels do not govern; hashes do. ✓

Budget: `writer_budget = parent_bytes - 2*capture_bytes - 16*MiB - 8192`. For `evidence_bytes=64 MiB` and `capture_bytes=16 MiB`, this yields `64 MiB - 32 MiB - 16 MiB - 8 KiB = 16 MiB - 8 KiB`, which is positive. ✓

**Caveat preserved:** The `16 MiB` boundary-call reserve is an estimate (≤16 calls × ≤1 MiB output). No runtime enforcement prevents a single boundary call exceeding 1 MiB if the PS script produces large output. This is a feasibility-run limitation, not a correctness defect in the budget formula.

### 2f  Pre/post verification

`inventory_before` / `inventory_after` call `_observe_review` + `_verify_namespaces` and write SHA256-keyed pin snapshots. The `postchecks` flag requires *both* `integrity.final_check` and `inventory_after` to succeed. Either failure is recorded in `cleanup_errors` and flips the terminal record to `FAIL`. ✓

### 2g  R04 CORRECTION.md review

Both corrections are clean:
1. **CLEANUP before report auditing:** `phase('CLEANUP')` is called before `validate_complete_report()` at line 122 of `offline_cohort_attempt.py.final`. The reserved finalization window is used as intended. ✓
2. **Duplicate immutable-command reconstruction removed:** `packet_body` materialises the command once; `encode_packet` hashes the body it already validated. Strict regenerated-form checks are unchanged. ✓

### 2h  Test suite

751 tests across 49 named modules, 749 passed, 2 skipped, 0 failures/errors, 111.84 s. Five new suites (`test_offline_cohort_native_synthetic`, `test_offline_cohort_attempt_synthetic`, `test_offline_cohort_packet_synthetic`, `test_offline_cohort_production_synthetic`, `test_offline_cohort_user_launcher_synthetic`) are listed in both `TEST_RESULT.json` and the R04 directory.

**Caveat explicitly preserved (from Codex-0285):** 751 tests use fake kernels, fabricated authentic-schema fixtures, and no real API/DB/Job/model operations. They are NOT a 350-query cohort. The two skipped tests are not individually identified in the result JSON; Codex should confirm they are synthetic-only skips with no silent omission of real-execution paths.

---

## 3  Decision R02 findings — bounded concurrence

- `DECISION.json`: `actual_attempt_started: false`, `user_approval_received: false`, status `UNAPPROVED_PROPOSAL_VALIDATED`. Correct. ✓
- Packet SHA256 `343b88b5...` matches Codex-0285 §Operative identities. ✓
- Expected anchor SHA `aa1a844670...` and wrapper SHA `4761b434...` match manifest entries for `offline_cohort_anchor.py.expected` and `launch_offline_cohort_user.ps1.expected`. ✓
- `authorization.UNAPPROVED.json` resources match `DECISION.json` resources exactly. ✓
- `admission_source.diff` changes exactly two flags: `ENTRY_ADMITTED = False → True` and `COHORT_PRODUCTION_ADMITTED = False → True`. No other source lines modified. ✓
- `launch_context.UNAPPROVED.json` status `PROSPECTIVE_NOT_EXECUTABLE`. Four-key environment `{PATH,SYSTEMROOT,USERPROFILE,WINDIR}` matches the launcher's environment check. ✓
- `cohort_20261024_controlled01` and `cohort_controlled_freeze_20261024_01` both absent on disk. `actual_attempt_started: false` is accurate. ✓

---

## 4  Caveats retained without change

1. No hard-interrupt proof of Windows Job kill-on-close race.
2. No filesystem sandbox or OS-wide quota on disposable growth (observed polling only).
3. No real API, model, DB, or network operation has been performed by any test.
4. Successful build and test pass is not a claim of zero defects in authentic execution paths.
5. A postrun audit is required even if the cohort exits zero.
6. Two skipped tests not individually identified — Codex should confirm their scope.

---

## 5  Peer verdict

**BOUNDED CONCURRENCE** on R04 source and Decision R02, subject to the six retained caveats above. No blocking corrections identified. The proposed run is correctly scoped: 350 queries, local MiniLM ONNX only, no API key, no manuscript/statistics changes, one attempt, postrun audit required.

This verdict covers this exact R04 generation (R04 manifest SHA `956f1dea...`) and R02 decision package (R02 manifest `c156517e...`). It does not extend to earlier or later revisions.

---

## 6  Dated approval — 24 October 2026

**Antigravity approval ID: ANTIGRAVITY_PEER_CONCURRENCE_20261024_R04_R02**
**Date: 2026-10-24**
**Approver: Antigravity (Codex peer reviewer)**
**Scope: COHORT_OFFLINE_FEASIBILITY, 350 queries, no API, no manuscript changes, one attempt**

Execution authority remains with the user. This approval satisfies the peer-review prerequisite described in Codex-0285 §Held state and admission plan. The user must supply the dated exact decision approval and Administrator PS5.1 invocation.

---

## 7  Administrator PowerShell launch command

> [!IMPORTANT]
> Paste into an **Administrator PowerShell 5.1** session. The launcher self-blocks
> (`$LaunchAdmitted = $false`) until Codex's admission freeze sets the four header
> variables. Child run: 1800 s (30 min). Outer: 2400 s (40 min).

Codex's freeze step produces a copy of the launcher at:

```
F:\TERRA -Copy\reports\cohort_controlled_freeze_20261024_01\launch_offline_cohort_user.ps1
```

with `$LaunchAdmitted = $true` and the four hashes/paths set. That frozen copy must
itself be verified by its expected SHA before the session begins. Invoke as:

```powershell
# Run as Administrator in PS5.1
& "F:\TERRA -Copy\reports\cohort_controlled_freeze_20261024_01\launch_offline_cohort_user.ps1"
```

Expected success string: `COHORT WRAPPER OUTCOME: CONTROLLER_EXIT_ZERO_REQUIRES_POSTRUN_AUDIT`

If Codex's freeze places the launcher at a different path, use that path. The wrapper
SHA `4761b434d754c95ba3c780b8aec085f3ada2d6086cde948ee649b171e227d8fe` must be
independently pinned by the outer launcher's own `Assert-Pin` call before any work proceeds.

---

*Relay complete. Both milestones remain incomplete until the 350-query run finishes
and postrun audit passes.*
