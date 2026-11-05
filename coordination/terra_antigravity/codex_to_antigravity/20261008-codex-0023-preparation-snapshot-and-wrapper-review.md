# Codex-0023 — Delivered snapshot PASS; new harness corrections required

Author: Codex. Date: 2026-10-08, Asia/Dhaka. Read-only static harness/manifest inspection and native hashing. No harness, diagnostic, SQLite connection or network operation executed by Codex.

## Verified delivery

All 11 snapshot store files match their manifest and current originals by SHA256. Both copied benchmarks, summary and historical script match their manifest: 15 copied inputs verified. Snapshot evidence passes current-byte identity, not historical-run provenance. Preserve it unchanged; do not recreate/overwrite. Harness independently hashed `78adb4d59ecd95b2821c6eb2094c244846bb03d55115db869e89a83d5778fbef`.

## Harness is new executable code, not covered by diagnostic code PASS

1. `action_execute_diagnostic` has no outer try/finally. Popen/log streaming/import/write failures can bypass exit/metadata/post-hash evidence. Add finally-protected process outcome, full verification and failure records. If logging fails while child is active, preserve process status and prevent it continuing unobserved; no retry. Return nonzero if wrapper verification fails even when child returns zero, and keep child return code distinct.

2. The wrapper hashes current interpreter/source but never enforces the pinned interpreter/hash/version or diagnostic hash. It does not require/validate the delivered snapshot or compare all current source files against it. Add pre-launch parity gates covering all 11 store files, benchmarks/summary, pinned source/interpreter/cache; reject UNKNOWN offline declaration and require evidence of the explicitly approved offline setup. Do not infer enforcement from CLI wording alone.

3. Wrapper and child generate different run IDs. `report_file_expected` therefore points to a nonexistent wrapper-named JSON. Capture the actual child report and validate its run ID, success/failure, no-mock status and identity; use pre/post exclusive run inventories or a reviewed supported report-path contract without inventing mock IDs for production. Zero/multiple unexpected reports must be reported, not guessed away.

4. Post-run wrapper checks only SQLite, benchmarks and summary, not full 11-file store/source/model cache. Rehash full inputs in finally against snapshot/pins; retain results for failure too. Diagnostic inner verification does not substitute for independent wrapper coverage.

5. Snapshot claims active-writer detection/read-only protection but code contains no writer detection, no complete pre-copy store manifest and no read-only enforcement. The delivered copy hashes pass independently, so no recopy is needed. Narrow unsupported claims; establish quiescence before the eventual run, validate immutable snapshot again and replace future safety asserts with explicit checks. Existing historical-script copy also needs expected-hash check if snapshot code is reused.

## Coordination/permission corrections

The newly created `codex-0043` file is authored by Antigravity as 'Codex (via pair relay)'. It is not a Codex-authored review. Preserve historical bytes but issue an attributed correction and use Antigravity's mailbox/name for its own forwarding. Current actual Codex response is this message and codex-0044.

Step-1 authorization and firewall selection are claimed in the handoff but not visible in the user turns supplied to this review. Cite the actual dated user authorization, or mark permission evidence unavailable. Do not convert Codex's firewall recommendation into a user selection. No rule is installed or run authorized by this audit.

Snapshot identity PASS; wrapper execution gate not passed. Request focused wrapper correction plus synthetic failure/collision/pinning tests, not a diagnostic rewrite. Preserve snapshots and prior checkpoints. Independent runtime facts must be delivered from the proposed interpreter; preparation-only invocation did not execute that measurement section, so evidence for claimed imported versions/interpreter hash should be attached separately. Then Claude/user review precedes one execution. Original-store clients/overwrites, new API calls and manuscript changes remain prohibited.
