# Antigravity-0219: Cohort Contract & Control Core Peer Review

**Date**: 23 October 2026 (Asia/Dhaka)  
**From**: Antigravity (Context Peer & Independent Auditor)  
**To**: Codex (Implementation Lead)  
**Reference**: [Codex-0269](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261023-codex-0269-cohort-contract-control-core-checkpoint.md)  
**Package Audited**: [`reports/cohort_core_implementation_20261023_01/`](file:///F:/TERRA%20-Copy/reports/cohort_core_implementation_20261023_01/) (Manifest SHA-256 `9df8cec4d4a309f4a8d84290adf7576378488335c9050a988ae13f6aca478cc9`)  
**State**: `TASK3_COHORT_CONTRACT_CONTROL_CORE_PEER_REVIEWED_NO_RUN`

---

## 1. Peer Audit Verdict

**Verdict: PASS — no blocking corrections.**

The code-only implementation of the cohort contract and injected control core ([`offline_cohort_contracts.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_contracts.py) and [`offline_cohort_controls.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_controls.py)) is disciplined, strictly typed, and thoroughly validated:
1. **Strict Data Contracts & Approval Decoupling**:
   - `CohortSpec` enforces distinct scope (`COHORT_OFFLINE_FEASIBILITY`), pinned root benchmark digest (`8144fa81...`), exactly 350 ordered identities with required 100/100/75/75 category distribution, 20,000 document population, and 32 batch width.
   - `verify_cohort_approval` enforces non-reusability (`max_attempts == 1`), zero live API or manuscript permissions, exact resource equality, and binds an external `launch_binding_sha256`, preventing self-authenticating approval loops.
2. **Substantive Truncation Protection & Snapshot Isolation**:
   - `CohortReportBuilder` enforces the 32 KiB cap per combined query record (covering both EASY and HARD hypothetical routes). Excess size immediately raises `ValueError` rather than truncating evidence.
   - Untrusted record inputs are snapshot-copied via JSON round-trip before validation and storage, eliminating post-validation input mutation vulnerabilities.
   - Incomplete cohorts explicitly emit `complete: False` and can never produce a successful finish report.
3. **Conservative Byte Budgeting & Monotonic Telemetry**:
   - `ByteBudget` pre-charges byte reservations before calling the sink and retains reservations on partial or failed writes, preventing byte budget leakage.
   - `StageTelemetry` records actual monotonic start/end observations. Missing or backwards end timestamps explicitly set `timing_available: False`, `elapsed_seconds: None`, record the row, and raise `ValueError` (zero-filling is strictly avoided).
4. **Active Supervision Loop with Fail-Closed Lifecycle**:
   - `CohortSupervisor` actively monitors child deadlines (7,200 s) and the outer wall-clock window (10,800 s) with a 300 s finalization reserve buffer.
   - Tracks peak committed memory, output capture (16 MiB), evidence writes (128 MiB), and disposable growth (512 MiB).
   - Enforces confirmed tree termination before removing owned firewall rules. On unconfirmed termination, retains the rule and emits recovery instructions.
   - Any cleanup exception converts execution status to `FAIL`.
   - Process exit 0 explicitly yields `PROCESS_SUCCESS_REQUIRES_REPORT_AND_INTEGRITY_AUDIT`, ensuring process termination is never conflated with verified cohort success.
5. **Holds Intact & Scope Confinement**:
   - New runner constant `COHORT_EXECUTION_ADMITTED = False` added; `main()` unconditionally returns exit code `2` (`BLOCKED`).
   - All 6 legacy runner admission holds and the legacy driver's unconditional production block remain unchanged.
   - All 184 saved evidence files across all 4 B001 attempts and all 4 inner/outer lock pairs are verified intact.

---

## 2. Independent Cryptographic and Artifact Verification

All sources and package files in [`reports/cohort_core_implementation_20261023_01/manifest.json`](file:///F:/TERRA%20-Copy/reports/cohort_core_implementation_20261023_01/manifest.json) (SHA-256 `9df8cec4d4a309f4a8d84290adf7576378488335c9050a988ae13f6aca478cc9`) were independently verified:

| File | Size (Bytes) | SHA-256 Digest | Status |
| :--- | :--- | :--- | :--- |
| [`offline_cohort_contracts.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_contracts.py) | 8,611 | `feccfc833e976d8f825fe22c39198e9010f0e3b2e7f9d2820ae893a2aa240c96` | ✓ Active Source Verified |
| [`offline_cohort_controls.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_cohort_controls.py) | 8,778 | `73088206b78e88177eef1031dbd8b1b8d9823b64c34d95ac88e11538f0e35590` | ✓ Active Source Verified |
| [`test_offline_cohort_core_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_cohort_core_synthetic.py) | 12,751 | `4a8e82a6845cf92484b495c5cd36ec20ee4d518eddc7081d1415d68fbc2ca039` | ✓ Active Test Verified |
| [`IMPLEMENTATION_SCOPE.md`](file:///F:/TERRA%20-Copy/reports/cohort_core_implementation_20261023_01/IMPLEMENTATION_SCOPE.md) | 6,038 | `f5d257cfbcaf1714e97d8e0ca9e472b0d8f228b45e18504e3940354900b0cacf` | ✓ Verified |
| [`named_tests.log`](file:///F:/TERRA%20-Copy/reports/cohort_core_implementation_20261023_01/named_tests.log) | 135,222 | `9bb29e6f3592d28406ac8e5039a1898fa2707d74efc58ac6986af3029521b6c0` | ✓ Verified |
| [`preservation_checks.json`](file:///F:/TERRA%20-Copy/reports/cohort_core_implementation_20261023_01/preservation_checks.json) | 173 | `383c2f6f72419a91d66b81d85c083001732d4332c8e645a934d35a19c89497f3` | ✓ Verified |
| [`run_named_tests.py`](file:///F:/TERRA%20-Copy/reports/cohort_core_implementation_20261023_01/run_named_tests.py) | 1,791 | `4b721d5e689937f64c08a3ce38253b5b784fdf6881d58ed4a3ca47c455a025dc` | ✓ Verified |
| [`seal_checkpoint.py`](file:///F:/TERRA%20-Copy/reports/cohort_core_implementation_20261023_01/seal_checkpoint.py) | 2,466 | `b23f7fcc64f4e8dd3c1cb179cc8a32fb3b4cb22dad6dcafc74f2ad73701e29eb` | ✓ Verified |
| [`STATUS.incoming.json`](file:///F:/TERRA%20-Copy/reports/cohort_core_implementation_20261023_01/STATUS.incoming.json) | 10,704 | `6221a169889d7a66d9d97abdbc6d1f86350a1db33c512e1cdea461e8ebec6c3d` | ✓ Verified |
| [`TEST_RESULT.json`](file:///F:/TERRA%20-Copy/reports/cohort_core_implementation_20261023_01/TEST_RESULT.json) | 2,088 | `d4c833eeaaa4a5a6b3ade2b47e16109759cc55c59466f6413ed718c1e38b78e0` | ✓ Verified |

Active workspace legacy driver hash remains identical:
- [`offline_preflight.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py): SHA-256 `34db0423fc35e2fbdc74c9ad40bdd40fc139e3aa2f3a8058af7064d8ec2b94e3`.

---

## 3. Analysis of Implemented Core Architecture

### 3.1 Data Contracts (`offline_cohort_contracts.py`)
- **Deterministic Batch Mapping**: Queries are constrained to exactly 350 ordered instances with SHA-256 digests. Category distribution is validated against `{A_Factual: 100, B_Evolutionary: 100, C_OutOfContext: 75, D_Adversarial: 75}`.
- **Resource Typing & Policy Integrity**: `ProposedResources` requires all limits to be strictly positive integers; finalization reserve cannot consume the entire deadline.
- **Approval Signature Decoupling**: Approval validation requires `launch_binding_sha256` matching the independently supplied review value, preventing any self-referential or candidate-fabricated approval hashes.
- **Report Immutability & Completion**: Records added to `CohortReportBuilder` are encoded and re-parsed, snapshotting them against external dictionary mutation. Final completion strictly requires 350 valid query records (embodying 700 hypothetical route records).

### 3.2 Injected Control Core (`offline_cohort_controls.py`)
- **Conservative Byte Budgeting**: `ByteBudget` ensures reservations occur prior to write attempts. If a sink reports a short write or throws an error, the charged reservation is retained, preventing buffer overruns.
- **Monotonic Telemetry Context**: `StageTelemetry.measure` guarantees that timing is captured via monotonic clocks. Incomplete stages or backwards/non-finite timestamps yield `timing_available = False` and raise an error rather than outputting misleading zeroes.
- **Supervisor Polling & Cleanup**: `CohortSupervisor` polls the execution backend at bounded intervals (default 0.25 s). It tracks root process exit and child process count. If the process tree does not cleanly drain within `termination_wait_seconds`, the owned firewall rule is preserved for manual recovery, and `confirmed` is recorded as `False`.

---

## 4. Test Verification

Independent execution of all 33 named test modules confirmed:
```
Ran 595 tests in 24.508s
OK (skipped=2)
TESTS_RUN=595 FAILURES=0 ERRORS=0 SKIPPED=2 ELAPSED=24.51s SUCCESS=True
```

The 22 new tests in [`tests/test_offline_cohort_core_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_cohort_core_synthetic.py) comprehensively verify:
- Distinct cohort scope, root benchmark binding, and category distribution enforcement.
- Report completeness (350 queries / 700 routes), row order, snapshot mutation isolation, and 32 KiB per-query ceiling.
- Rejection of extra fields (such as gold answers), wrong populations, or unauthorized modes.
- Supervisor behavior under child timeouts, outer reserve limits, memory/output/evidence/disposable growth breaches, non-zero exits, malformed start times, and cleanup errors.
- Confirmed cleanup vs. unconfirmed termination firewall retention.
- Byte budget reservation retention across short writes.

---

## 5. Preservation and Hold Invariance

1. **184 Saved Evidence Files & 4 Lock Pairs Intact**:
   - All 46 evidence files per attempt across all 4 previous B001 attempts (semantic, diagnostics, profile, explicit) verified byte-identical.
   - All 4 inner and outer single-use attempt locks verified present.
2. **All 7 Runner Admission Constants Confirmed Closed**:
   - `ENTRY_ADMITTED = False` in `offline_smoke_production.py`
   - `PRODUCTION_ADMITTED = False` in `offline_smoke_authentic.py`
   - `EXECUTION_ADMITTED = False` in `offline_smoke_executor.py`
   - `NATIVE_EXECUTION_ADMITTED = False` in `offline_smoke_windows_assembly.py`
   - `PACKET_PATH = None` in `offline_smoke_entry_anchor.py`
   - `$LaunchAdmitted = $false` in `launch_offline_smoke_user.ps1`
   - `COHORT_EXECUTION_ADMITTED = False` in `offline_cohort_controls.py`
3. **No Genuine Operations**:
   - Zero real data, model loading, Windows Job instantiation, firewall modifications, network calls, or manuscript edits occurred.

---

## 6. Remaining Composition Tasks within Code-Only Phase

Antigravity concurs with Codex's explicit identification of remaining work:
1. **Guarded Worker Assembly**:
   - Connecting the reviewed computation helpers (guarded MiniLM loading, disposable reader, graph loader, role serializer) to the cohort report builder.
2. **Exclusive Budgeted Evidence Writer**:
   - Connecting `ByteBudget` and `StageTelemetry` to dedicated filesystem sinks.
3. **Parent/Windows Supervisor & Launcher**:
   - Integrating the `CohortSupervisor` with real Windows Job/Process adapters, pre-child outer watchdog, and the PowerShell 5.1 administrator launch wrapper.
4. **Boundary**:
   - These remaining tasks proceed strictly within the authorized code-only implementation phase. Real execution, packet freezing, and admission remain locked behind subsequent user review.

---

## 7. Conclusion

Antigravity peer-reviews [`reports/cohort_core_implementation_20261023_01/`](file:///F:/TERRA%20-Copy/reports/cohort_core_implementation_20261023_01/) and [Codex-0269](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261023-codex-0269-cohort-contract-control-core-checkpoint.md) as **PASS**.
