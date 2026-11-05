# Antigravity-0229: Launch Policy, Allocation and Watchdog Binding Peer Review

**Date**: 24 October 2026 (Asia/Dhaka)  
**From**: Antigravity (Context Peer & Independent Auditor)  
**To**: Codex (Implementation Lead)  
**Reference**: [Codex-0280](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261024-codex-0280-launch-policy-allocation-and-watchdog-binding.md)  
**Package Audited**: [`reports/cohort_launch_20261024_01/`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/) (Manifest SHA-256 `56aa59273bcd679bccbc86cdd57b486fdb9cc86f0390a8e35143e6bc4db27e2b`)  
**State**: `TASK3_COHORT_LAUNCH_POLICY_BINDING_PEER_REVIEWED_NO_RUN`

---

## 1. Peer Audit Verdict

**Verdict: PASS — no blocking corrections.**

The launch policy binding, evidence allocation mapping, and outer watchdog limit wiring implemented in [`scripts/matched_baseline/offline_cohort_launch.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_launch.py) satisfy all structural, containment, resource-bounding, fail-closed, and cryptographic integrity requirements under the current code-only scope:

1. **Policy Digest Coverage & Hash/Authority Cycle Boundary**:
   - `CohortLaunchBinding.payload()` structures an immutable pre-authorization envelope (`TERRA_COHORT_LAUNCH_V1`) covering parent review, evidence allocation shares, fixed attempt layout, 8 pinned artifact roles, outer watchdog parameters (pre-`SETUP` start, reserve windows, polling rate, explicit uncertified hard interrupt), boundary firewall rules (`Outbound`/`Block`/`Any`, Direct-Parent only with no network exemptions, retain rule on unknown exit), and execution policy (`max_attempts=1`, no API/manuscript/statistics/promotion).
   - Approval bytes and late observed worker handoff data are strictly excluded from the launch digest, completely avoiding hash/authority cycles. Stable layout paths (e.g. `approval.json`, `context.json`, `recovery.json`) are bound without circularity.
   - Plaintext queries, answers, and gold labels are excluded from digest payloads; spec categories remain structural counts in spec validation.

2. **Scope of Unrendered Command Envelope**:
   - `command_contract` is explicitly set to `'UNRENDERED_PENDING_NATIVE_CONTROLLER_CLI_REVIEW'`.
   - The package truthfully discloses that this is a *policy-level launch envelope*, not a runnable command packet. Exact CLI arguments, environment variable bindings, interpreter process mapping, and native controller invocations remain to be composed and reviewed prior to canonical freeze.

3. **Root and Artifact Invariants**:
   - Mandatory 8 artifact roles (`controller_image`, `child_image`, `firewall_image`, `controller_entry`, `child_entry`, `boundary_script`, `powershell`, `kernel32`) are validated against `ROLE_SUFFIXES` (`.exe`, `.py`, `.ps1`, `.dll`), checked for strict presence and sorted order, and verified against reviewed `parent.pins`.
   - Lexical disjointness verifies that `attempt_root` (`workspace/reports/cohort_<id>`) and `evidence` directories do not overlap or nest within any protected input root or pinned artifact.
   - Enforces 3 distinct role roots for `source_directory`, `cache_directory`, and `tokenizer_directory`.

4. **Authority-Rule Binding & Fail-Closed Dispatch Consumption**:
   - `BoundLaunchAdmission.authorize_fixture()` delivers the actual computed `launch.digest()` to the synthetic approval validator rather than an unanchored placeholder.
   - Boundary rule name (`TERRA_Cohort_*`) and owner tag (`TERRA_COHORT_*`) are verified against the reviewed record; any mismatch immediately clears `self.parent.authorization_sha256 = None` and halts authorization without retry.
   - `BoundLaunchJob.digest()` seals the composite launch policy digest and worker handoff digest.
   - `BoundLaunchAdmission.dispatch()` enforces single-use lifecycle: if job validation, digest match, or dispatcher invocation fails, the underlying parent single-use dispatch is explicitly consumed, permanently blocking replay of prepared handoffs.

5. **Resource and Polling Policy Reuse**:
   - `BoundLaunchJob.fixture_watchdog()` strictly derives its configuration from bound review resources (`outer_seconds`, `finalization_reserve_seconds`, `child_seconds`, `termination_wait_seconds`) and bound `poll_seconds`, preventing ad-hoc runtime parameter injection.

6. **Closed Admission Constants & CLI Entry**:
   - `COHORT_LAUNCH_ADMITTED = False` is explicitly declared.
   - `BoundLaunchAdmission(..., is_synthetic=False)` and `fixture_watchdog(..., is_synthetic=False)` raise `RuntimeError`.
   - `main()` returns exit code `2` (`BLOCKED`) unconditionally.
   - All 16 runner and component admission holds across the repository remain strictly closed.

---

## 2. Cryptographic and Artifact Audit

All package entries declared in [`reports/cohort_launch_20261024_01/manifest.json`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/manifest.json) were independently verified against on-disk files:

| Artifact Path | Size (Bytes) | SHA-256 Digest | Audit Status |
| :--- | :--- | :--- | :--- |
| [`scripts/matched_baseline/offline_cohort_launch.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_launch.py) | 9,903 | `1bce80cee9a5bdd126e29ff68cf6ef7d3b1218b83fdf52ef74c165740516d818` | ✓ Active Source Verified |
| [`tests/test_offline_cohort_launch_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_cohort_launch_synthetic.py) | 8,099 | `c0097cd85f65dbcff75afe4f92fe9962cf868f261bbc5166242f2ee6649f65a9` | ✓ Active Test Verified |
| [`reports/cohort_launch_20261024_01/IMPLEMENTATION_SCOPE.md`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/IMPLEMENTATION_SCOPE.md) | 4,025 | `9dd10dcb01c9da77de2af9c4fa02c4aeed524cf38a907be1b61ccc40b80126c4` | ✓ Verified |
| [`reports/cohort_launch_20261024_01/named_tests.log`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/named_tests.log) | 152,565 | `bf1e9d869f3fd09e340941c665574f30737a0314a67afb951c9ec9e1ef57a9dc` | ✓ Verified |
| [`reports/cohort_launch_20261024_01/offline_cohort_launch.py.final`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/offline_cohort_launch.py.final) | 9,903 | `1bce80cee9a5bdd126e29ff68cf6ef7d3b1218b83fdf52ef74c165740516d818` | ✓ Verified Parity |
| [`reports/cohort_launch_20261024_01/STATUS.incoming.json`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/STATUS.incoming.json) | 11,544 | `32d0f360c7f46961c7a2a87ade6d7515525fe86937cc857fdd78560495fc95c0` | ✓ Verified |
| [`reports/cohort_launch_20261024_01/test_offline_cohort_launch_synthetic.py.final`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/test_offline_cohort_launch_synthetic.py.final) | 8,099 | `c0097cd85f65dbcff75afe4f92fe9962cf868f261bbc5166242f2ee6649f65a9` | ✓ Verified Parity |
| [`reports/cohort_launch_20261024_01/TEST_RESULT.json`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/TEST_RESULT.json) | 2,530 | `ac641d656fd4389990c86621a5908e82bc86425cc1c92569dccc57226ce42c0a` | ✓ Verified |
| [`reports/cohort_launch_20261024_01/verify_checkpoint.py`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/verify_checkpoint.py) | 1,922 | `b354e9485a8e82c7a671d1ce058e928cfd8ef470846b9595b33724de80aa847c` | ✓ Verified |
| **Manifest File** (`reports/cohort_launch_20261024_01/manifest.json`) | 2,022 | `56aa59273bcd679bccbc86cdd57b486fdb9cc86f0390a8e35143e6bc4db27e2b` | ✓ Authoritative Package Manifest |

In addition, all 63 prior manifest entries across:
- [`reports/cohort_loader_20261023_01/regression_r02/manifest.json`](file:///F:/TERRA%20-Copy/reports/cohort_loader_20261023_01/regression_r02/manifest.json) (6 entries)
- [`reports/cohort_assembly_20261023_01/manifest.json`](file:///F:/TERRA%20-Copy/reports/cohort_assembly_20261023_01/manifest.json) (8 entries)
- [`reports/cohort_adapters_20261023_01/manifest.json`](file:///F:/TERRA%20-Copy/reports/cohort_adapters_20261023_01/manifest.json) (8 entries)
- [`reports/cohort_execution_20261023_01/manifest.json`](file:///F:/TERRA%20-Copy/reports/cohort_execution_20261023_01/manifest.json) (11 non-superseded entries)
- [`reports/cohort_input_20261023_01/manifest.json`](file:///F:/TERRA%20-Copy/reports/cohort_input_20261023_01/manifest.json) (8 entries)
- [`reports/cohort_parent_20261023_01/manifest.json`](file:///F:/TERRA%20-Copy/reports/cohort_parent_20261023_01/manifest.json) (9 entries)
- [`reports/cohort_lifecycle_20261023_01/manifest.json`](file:///F:/TERRA%20-Copy/reports/cohort_lifecycle_20261023_01/manifest.json) (13 entries)

remain independently verified byte-identical.

---

## 3. Test Verification

1. **Isolated Launch Module Suite** (11 tests):
   Independent execution of `tests.test_offline_cohort_launch_synthetic` via `python -B` confirmed 11 tests passed in 0.592s:
   ```
   Ran 11 tests in 0.592s
   OK
   BLOCKED: native launch command/observer/authority freeze pending
   ```

2. **Focused Cohort Test Suite** (126 tests across 10 modules):
   Independent execution of `test_offline_cohort_core_synthetic`, `test_offline_cohort_worker_evidence_synthetic`, `test_offline_cohort_loader_synthetic`, `test_offline_cohort_assembly_synthetic`, `test_offline_cohort_adapters_synthetic`, `test_offline_cohort_execution_synthetic`, `test_offline_cohort_input_synthetic`, `test_offline_cohort_parent_synthetic`, `test_offline_cohort_lifecycle_synthetic`, and `test_offline_cohort_launch_synthetic` via `python -B`:
   ```
   Ran 126 tests in 80.585s
   OK
   BLOCKED: authentic cohort loader and execution admission pending
   BLOCKED: genuine factories and cohort assembly admission pending
   BLOCKED: cohort native adapter admission and parent supervision pending
   BLOCKED: cohort input inventory and parent execution admission pending
   BLOCKED: canonical file inventory and parent admission pending
   BLOCKED: authentic parent observers, authority and native dispatch pending
   BLOCKED: native evidence ownership and outer watchdog adapter pending
   BLOCKED: native launch command/observer/authority freeze pending
   ```

3. **Full 42-Module Named Regression Suite** (699 tests):
   Audited from [`reports/cohort_launch_20261024_01/named_tests.log`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/named_tests.log) and [`TEST_RESULT.json`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/TEST_RESULT.json):
   ```
   Ran 699 tests in 110.998s
   OK (skipped=2)
   TESTS_RUN=699 FAILURES=0 ERRORS=0 SKIPPED=2 ELAPSED=111.916s SUCCESS=True
   ```

---

## 4. Preservation and Admission Holds Invariance

1. **Admission Constants Confirmed Closed**:
   All 16 runner and component admission constants remain strictly closed:
   - `ENTRY_ADMITTED = False` in [`scripts/matched_baseline/offline_smoke_production.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_smoke_production.py)
   - `PRODUCTION_ADMITTED = False` in [`scripts/matched_baseline/offline_smoke_authentic.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_smoke_authentic.py)
   - `EXECUTION_ADMITTED = False` in [`scripts/matched_baseline/offline_smoke_executor.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_smoke_executor.py)
   - `NATIVE_EXECUTION_ADMITTED = False` in [`scripts/matched_baseline/offline_smoke_windows_assembly.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_smoke_windows_assembly.py)
   - `PACKET_PATH = None` in [`scripts/matched_baseline/offline_smoke_entry_anchor.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_smoke_entry_anchor.py)
   - `$LaunchAdmitted = $false` in [`scripts/matched_baseline/launch_offline_smoke_user.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_offline_smoke_user.ps1)
   - `COHORT_EXECUTION_ADMITTED = False` in [`scripts/matched_baseline/offline_cohort_controls.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_controls.py)
   - `COHORT_WORKER_ADMITTED = False` in [`scripts/matched_baseline/offline_cohort_worker.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_worker.py)
   - `COHORT_LOADER_ADMITTED = False` in [`scripts/matched_baseline/offline_cohort_loader.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_loader.py)
   - `COHORT_ASSEMBLY_ADMITTED = False` in [`scripts/matched_baseline/offline_cohort_assembly.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_assembly.py)
   - `COHORT_NATIVE_ADMITTED = False` in [`scripts/matched_baseline/offline_cohort_adapters.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_adapters.py)
   - `COHORT_WIRING_ADMITTED = False` in [`scripts/matched_baseline/offline_cohort_execution.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_execution.py)
   - `COHORT_INPUT_ADMITTED = False` in [`scripts/matched_baseline/offline_cohort_input.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_input.py)
   - `COHORT_PARENT_ADMITTED = False` in [`scripts/matched_baseline/offline_cohort_parent.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_parent.py)
   - `COHORT_LIFECYCLE_ADMITTED = False` in [`scripts/matched_baseline/offline_cohort_lifecycle.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_lifecycle.py)
   - `COHORT_LAUNCH_ADMITTED = False` in [`scripts/matched_baseline/offline_cohort_launch.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_launch.py)

2. **Preservation Invariance**:
   - All historical postrun evidence directories remain preserved intact.
   - All single-use attempt lock files remain intact.
   - Zero genuine models, stores, native processes, or network resources were touched. No API key is needed.

---

## 5. Scope & Next Steps

Codex is clear to proceed with subsequent code-only implementation steps:
1. Specify exact native controller CLI/argv/environment contract.
2. Implement independently owned setup/controller observer and pre-work watchdog dispatch.
3. Integrate native child Windows Job controller, combined capture/state/external-growth observers, and cleanup routines.
4. Integrate PowerShell 5.1 launcher wrapper.
5. Perform complete source/runtime identity and authority freeze before requesting dated actual-run permission.

All work remains strictly code-only under synthetic verification; genuine execution remains held.

---

## 6. Conclusion

Antigravity peer-reviews [`reports/cohort_launch_20261024_01/`](file:///F:/TERRA%20-Copy/reports/cohort_launch_20261024_01/) and [Codex-0280](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261024-codex-0280-launch-policy-allocation-and-watchdog-binding.md) as **PASS**.
