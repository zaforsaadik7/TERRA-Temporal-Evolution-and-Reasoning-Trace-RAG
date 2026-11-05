# Authorized user-window attempt: failed before boundary/copy/child

23 October 2026 (Asia/Dhaka). Codex implementation self-audit after user returned WRAPPER OUTCOME: FAIL. No retry or defect repair was performed. Only used launch admissions were closed as containment; frozen executed artifacts and all evidence remain preserved.

## Saved outcome

Wrapper evidence: reports/renewed_user_b001_20261023_01/wrapper_evidence/. Parent exit 1, parent_attempted=true, wrapper outcome FAIL. Outer transcript SHA-256 8a12c46ebea7c2fc4f2f8db13364828a4771d1efb3c0e88c3b55ed145f991ed8. The user-window transcript records Desktop PS5.1.19041.7802.

Parent evidence: reports/authentic_smoke_candidate_20261022_01/evidence/. terminal.json status FAIL, child_exit=null, child_capture=null, transcript_closed=true. Parent transcript is empty, SHA-256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.

## Two confirmed preparation defects — Codex responsibility

1. Actual execution_packet.json windows.script_path points to inventory/boundary_script.json, not scripts/matched_baseline/offline_smoke_windows_boundary.ps1. The member inventory was mistakenly used as the native script artifact. The saved environment-operation stderr explicitly rejects the JSON file as lacking a .ps1 extension. PowerShell failed before executing the boundary adapter. This is not a firewall privilege, service or profile finding.
2. integrity source/cache relative keys and rel_path fields use Windows backslashes. IntegrityLifecycleManager.compute_manifest normalizes to forward slashes. The final protected-directory checks therefore report file-key mismatch, not demonstrated changed content. Expected snapshot aggregate generation inherited the same separator problem. The earlier synthetic decode/shape tests and peer reviews did not catch these real-evidence semantic mapping defects.

No code/data repair or rerun is implied by diagnosis. A future bounded repair needs to bind the actual script file (not its list manifest), normalize relative keys/entries and aggregate convention to the lifecycle implementation, and add integration negatives that reproduce these exact defects using synthetic files before any new freeze/permission.

## Stage and safety evidence

The parent stops in boundary.preflight's environment operation, before integrity.prepare, boundary creation, inner single-run lock or child request/dispatch. The candidate directory contains evidence only, no snapshot/disposable. No child was launched, no local model/tokenizer computation occurred, and no source-store client connection occurred. The environment adapter never executed, so no firewall rule creation or firewall-state query was performed by this attempt. No independent firewall-absence query is claimed.

file_pins_before.json and file_pins_after.json are identical and record full declared verification of 30,552 unique members. Those manifests include all store/cache bytes and show their declared identities still matched. This does not erase the protected-lifecycle failure or turn this into success.

## Admission containment

After reading evidence, reset ENTRY_ADMITTED=false, Python anchor path/hash=None, and wrapper LaunchAdmitted=false with null record path/hash. These files now match their pre-freeze bytes; therefore old frozen live-root expectations intentionally no longer match. The executed .final source copies, approval, packet and launch record are NOT rewritten. Outer single-attempt lock and wrapper/parent evidence remain untouched. No rule cleanup was attempted because no rule creation occurred.

The permission's attempt is used/stopped; do not rerun the command, bypass the wrapper, remove locks, or reuse the authorization. New implementation scope and separately renewed execution authority are required for any future attempt. The user may close the returned idle PowerShell window; no script process remains active according to the returned prompt and parent/wrapper exit evidence. No independent process-table audit was performed.
