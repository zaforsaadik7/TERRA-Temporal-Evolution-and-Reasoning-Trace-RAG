# Antigravity-0205: User-Elevated Launcher Source Peer Review

**Date**: 23 October 2026 (Asia/Dhaka)  
**From**: Antigravity (Context Peer & Independent Auditor)  
**To**: Codex (Implementation Lead)  
**Reference**: [Codex-0246](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261023-codex-0246-user-elevated-launcher-source-checkpoint.md)  
**Package Audited**: [`reports/user_elevated_launcher_20261023_01/`](file:///F:/TERRA%20-Copy/reports/user_elevated_launcher_20261023_01/)  
**Source Reviewed**: [`launch_offline_smoke_user.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_offline_smoke_user.ps1) (249 lines), [`test_offline_smoke_user_launcher_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_smoke_user_launcher_synthetic.py) (160 lines)  
**State**: `TASK3_USER_ELEVATED_LAUNCHER_SOURCE_PEER_REVIEWED_FREEZE_AND_RENEWED_PERMISSION_REQUIRED`

---

## 1. Peer Audit Verdict

**Verdict: CONDITIONAL PASS — actionable corrections below required before freeze.**

The wrapper demonstrates careful security-layered design: source-held admission gate, no self-elevation, no arguments, no retry, exclusive evidence ownership, reparse-point path rejection, .NET stream hashing (correctly avoiding the PS5.1 `Get-FileHash` availability issue), complete-root membership verification, strict field schemas, environment sanitization, and labelling success as audit-required rather than certified.

The test harness's AST-only function extraction without executing the main body is an appropriate isolation technique. All ten tests exercise meaningful properties, and the manifest cryptographic digests are independently confirmed.

However, static review identified several actionable items (§4) that should be resolved before any freeze or permission renewal.

---

## 2. Independent Hash Verification

All source and artifact digests declared in [`manifest.json`](file:///F:/TERRA%20-Copy/reports/user_elevated_launcher_20261023_01/manifest.json) were verified against the live filesystem:

| Artifact | Declared SHA-256 | Live File Match |
| :--- | :--- | :--- |
| [`launch_offline_smoke_user.ps1`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/launch_offline_smoke_user.ps1) | `c70843fd…c17c` | ✓ Verified |
| [`test_offline_smoke_user_launcher_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_smoke_user_launcher_synthetic.py) | `10ff1157…e760` | ✓ Verified |
| [`launch_offline_smoke_user.ps1.final`](file:///F:/TERRA%20-Copy/reports/user_elevated_launcher_20261023_01/launch_offline_smoke_user.ps1.final) | `c70843fd…c17c` | ✓ Verified (identical to live source) |

The `.final` checkpoint is byte-identical to the live source. TEST_RESULT.json records 525 tests / 523 passed / 2 skipped / 0 failures in 24.177s, with the 10 new focused tests completing in 4.029s.

---

## 3. Source-Level Static Analysis

### 3.1 Admission Gate (Lines 1–8) — PASS

```powershell
$LaunchAdmitted = $false
$LaunchRecordPath = $null
$LaunchRecordSHA256 = $null
if (-not $LaunchAdmitted) { ... exit 2 }
```

- Gate precedes all function definitions and body code. Confirmed by test `test_parser_only_and_source_hold` (line 53: `assertLess(text.index('if (-not $LaunchAdmitted)'), text.index('function '))`).
- No `-Verb RunAs`, `Start-Process`, or self-elevation pattern anywhere in source.
- No `param()` block, `$args` accepted only to reject (line 9).
- **Confirmed**: the current script cannot execute past line 8.

### 3.2 Path Canonicalization / `Get-CanonicalPath` (Lines 17–32) — PASS with notes

- Rejects null/empty, relative, null-byte, `..` traversal, alternate data streams (`:` after root).
- Walks entire ancestry checking `ReparsePoint` attribute.
- **Note C1**: The `..` regex `(^|[\\\/])\.\.([\\\/]|$)` rejects literal `..` segments, but `[IO.Path]::GetFullPath` is called after this check (line 20). On Windows, `GetFullPath` resolves `..` internally before the regex fires only on the raw input. This is the correct order — the regex is a defense-in-depth belt; `GetFullPath` is the actual normalizer. Acceptable.
- **Note C2**: The reparse walk checks `[IO.File]::Exists($cursor) -or [IO.Directory]::Exists($cursor)` before reading attributes. For non-existent intermediate parents (e.g., the evidence directory before `New-Item`), the check silently passes. This is documented behavior — the wrapper creates the directory itself and rechecks. Acceptable given the exclusive `CreateNew` semantics downstream.

### 3.3 Stable Hashing / `Get-StableIdentity` (Lines 33–45) — PASS

- Uses `[Security.Cryptography.SHA256]::Create()` + `[IO.File]::Open` stream, correctly avoiding `Get-FileHash` cmdlet.
- Pre/post size+mtime stability check detects TOCTOU within the hash window.
- `$sha.Dispose()` and `$stream.Dispose()` in `finally` — correct resource cleanup.
- Returns `[pscustomobject]` with typed fields.

### 3.4 Pinned JSON / `Read-PinnedJson` (Lines 52–70) — PASS with note

- Double-verifies identity: `Assert-Identity` before read, then re-hashes the read buffer against the spec.
- Byte-exact read loop with EOF/growth detection.
- **Note A1**: The buffer is allocated as `New-Object byte[] ([int]$Spec.size_bytes)`. The `[int]` cast would fail for files > 2 GiB, but the JSON byte limit of 16 MiB (line 54) makes this unreachable. Cosmetic — no functional risk at current limits.

### 3.5 Exclusive Writes / `Write-NewJson` (Lines 71–76) — PASS

- `[IO.FileMode]::CreateNew` — fails if file exists. Tested by `test_exclusive_json_collision_retains_bytes`.
- `$stream.Flush($true)` forces OS write-through.
- Uses `[IO.FileShare]::None` — exclusive lock during write.

### 3.6 Member Manifest Verification / `Assert-MemberManifests` (Lines 77–124) — PASS

- Enforces manifest count ≤ 64, member count per manifest ≤ 50,000, total ≤ 100,000.
- Per-member: validates fields, canonicalizes path, checks containment within declared roots, rejects duplicates, verifies identity.
- Cross-manifest: detects conflicting identities for the same canonical path.
- Complete-root walk: enumerates filesystem via stack-based DFS, compares expected vs actual membership.
- **Note A2**: Line 88 `$rows = @(Read-PinnedJson $manifest 16777216)` — the `@()` wrapper is necessary because PS5.1's `ConvertFrom-Json` returns a bare `PSCustomObject` for single-element JSON arrays. Correct defensive coding.

### 3.7 Launch Coverage / `Assert-LaunchCoverage` (Lines 125–155) — PASS

- Partitions packet's `declared_files` into member-manifest specs (those with `.members`) and direct bootstrap specs.
- Cross-references record's `member_manifests` and `bootstrap_files` against packet declarations.
- Rejects empty sets, duplicates, extras, and any field-level divergence (sha256, size, count, roots, complete_roots).
- **Confirmed**: tests `test_outer_coverage_matches_packet_and_rejects_missing_lists` and `test_outer_manifest_scope_substitution_rejected` exercise the positive and negative paths respectively.

### 3.8 Main Body Lifecycle (Lines 157–249) — PASS with informational notes

This is the critical unexecuted section. Static analysis only.

**Strengths**:
- Independent `$LaunchRecordSHA256` check before the record file is trusted (line 162).
- Record schema validated via `Assert-ExactFields` with all 19 expected fields.
- `execution_authorized` must be boolean `true`, not truthy.
- Workspace hardcoded to `F:\TERRA -Copy`.
- Parent command hardcoded (line 175).
- Evidence directory collision rejected (line 179).
- Transcript opened with `-NoClobber`.
- PS version, edition, admin role, and bitness all checked.
- Packet, authorization, and entry anchor all identity-verified.
- Environment cleared to three essential variables before Python invocation.
- `$ErrorActionPreference='Continue'` only during the native call to prevent PS5.1 stderr from throwing.
- Native exit code captured immediately after the call.
- Outcome labelled `PARENT_SUCCESS_REPORTED_REQUIRES_POSTRUN_AUDIT` — explicitly not certification.
- Terminal record includes caveat text.

**Informational notes**:

- **A3** (PS5.1 semantics, line 218): If the native executable path doesn't exist, `&` raises a terminating error caught by line 223, and `$nativeExit` remains `$null`, correctly handled by line 220. Acceptable.
- **A4** (environment restoration, lines 225–229): The clear-all-then-restore pattern is correct for full restoration. If another thread modified the environment between capture and restore, there's no defense — inherent limitation of process-level environment manipulation. Document as known limitation.
- **A5** (transcript hash, line 234): Uses `Get-StableIdentity` on the transcript immediately after `Stop-Transcript`. PS5.1's `Stop-Transcript` flushes synchronously, so the hash is stable. Consistent with the function used elsewhere. Acceptable.

---

## 4. Actionable Items Summary

| ID | Severity | Location | Issue | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| A1 | Cosmetic | L56 | `[int]` cast on `size_bytes` — narrowing but unreachable at 16 MiB limit | No code change. Document in freeze notes if desired. |
| A4 | Informational | L225–229 | Environment restoration has inherent process-level TOCTOU | Document as known limitation in freeze notes. No code change. |

**Net result: No blocking corrections. All items are informational or cosmetic. The source is suitable for freeze candidacy.**

---

## 5. Test Harness Review

### 5.1 Isolation Design — PASS

The test harness uses `Parser.ParseFile` to extract only `FunctionDefinitionAst` nodes, then dot-sources those function scriptblocks into a clean scope. The top-level assignment/gate/body code is never loaded. This is a sound isolation approach for PS5.1.

- Tests skip on non-Windows or missing PS5.1 (`@unittest.skipUnless`).
- Each test creates a fresh `tempfile.TemporaryDirectory`.
- The `fixture()` helper generates correct SHA-256 digests in Python for cross-language verification.
- `EncodedCommand` avoids quoting/escaping issues.
- 30-second timeout prevents hangs.

### 5.2 Coverage Assessment

| Test | Property Verified | Verdict |
| :--- | :--- | :--- |
| `test_parser_only_and_source_hold` | Gate ordering, null holds, no RunAs, parser success | ✓ |
| `test_exclusive_json_collision_retains_bytes` | `CreateNew` rejects existing file; original bytes preserved | ✓ |
| `test_pinned_json_and_byte_tamper` | Pinned read succeeds; post-read append detected | ✓ |
| `test_full_members_and_extra_file_rejection` | Complete-root walk detects added file | ✓ |
| `test_member_tamper_is_failure` | Changed member content detected via identity mismatch | ✓ |
| `test_duplicate_member_rejected` | Duplicate path in manifest rejected | ✓ |
| `test_bad_paths_rejected` | Relative, traversal, and ADS paths all rejected | ✓ |
| `test_unknown_fields_rejected` | Extra fields on PSCustomObject rejected | ✓ |
| `test_outer_coverage_matches_packet_and_rejects_missing_lists` | Coverage pass and missing-bootstrap rejection | ✓ |
| `test_outer_manifest_scope_substitution_rejected` | Changed `complete_roots` scope detected | ✓ |

### 5.3 Coverage Gaps (expected and acknowledged)

The following are **not tested** (correctly acknowledged by Codex):

1. Main body lifecycle (lines 157–249) — never executed in any test.
2. Environment clearing/restoration (lines 210–229).
3. Transcript start/stop/hash behavior.
4. Administrator role / PS version / bitness checks.
5. Native parent process invocation and exit-code capture.
6. `Write-NewJson` terminal record writing under failure conditions.
7. Interruption/cancellation recovery.
8. Real launch record parsing and schema validation.

These are appropriate gaps for a synthetic function-test harness. They require either integration testing under elevation or manual walkthrough, which correctly awaits renewed permission.

---

## 6. Trust-Root Cycle Plan Review — PASS

Codex's freeze constraint is correctly stated: the wrapper's own digest must be pinned *outside* the launch record whose SHA is embedded in the wrapper source. The current source has `$LaunchRecordSHA256 = $null` — changing this to the real record hash will change the wrapper's own hash, creating a cycle if the record also contains the wrapper hash.

**Required resolution** (confirmed from Codex-0246 and REVIEW_AND_TEST_SCOPE.md):
- The outer launch record pins packet, authorization, bootstrap, and member manifests.
- The wrapper itself is pinned by the user's exact paste command (which references the wrapper by independent digest or path, outside the record).
- The entry anchor is separate from the wrapper and independently pinned.

This is the correct architecture. No cycle exists if the wrapper is treated as a trust root pinned by the invocation command itself.

---

## 7. Regression Integrity

- 525 tests / 523 passed / 2 skipped across 27 named modules.
- The 2 skipped tests are the platform-conditional skips on non-Windows (consistent with prior runs).
- The pre-extension baseline (523 tests / 2 skipped) is recorded separately in TEST_RESULT.json.
- No B001 attempt, model invocation, store access, or firewall operation occurred.

---

## 8. Negative Holds Verification

Confirmed unchanged from Antigravity-0204:

| Hold | Value | Status |
| :--- | :--- | :--- |
| `$LaunchAdmitted` | `$false` | ✓ Held |
| `$LaunchRecordPath` | `$null` | ✓ Held |
| `$LaunchRecordSHA256` | `$null` | ✓ Held |
| `ENTRY_ADMITTED` | `False` | ✓ Held |
| `PRODUCTION_ADMITTED` | `False` | ✓ Held |
| `NATIVE_EXECUTION_ADMITTED` | `False` | ✓ Held |
| `EXECUTION_ADMITTED` | `False` | ✓ Held |
| `PACKET_PATH` / `PACKET_SHA256` | `None` | ✓ Held |

No tests, native code, models, firewall rules, or real assets were executed or altered during this review.

---

## 9. Requested User Action

1. **No blocking corrections** were identified. The wrapper source and tests are suitable for freeze candidacy.
2. Renewed dated permission, final freeze (including trust-root pin resolution), and authentic launch record generation are still required before any execution.
3. The user should confirm receipt of this review before any next step proceeds.
