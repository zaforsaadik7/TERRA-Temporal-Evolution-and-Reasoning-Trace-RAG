# Runtime-image / owned-controller revision

Author: Codex. Date: 22 October 2026. Implementation self-verification, not independent review.

## Authority and peer reconciliation

The user approved code and synthetic tests for targeting the actual runtime image and accepting only its verified controller parent. No execution authorization follows. Antigravity-0194 was read in full; it reviews Codex-0226, not the later copied-metadata inventory or this revision. Its no-parent-exemption condition is preserved as historical peer advice; the user's newer explicit code-only approval selects the narrower verified-parent policy. Do not describe this revision as peer-approved.

Antigravity's base-interpreter full-suite failures are peer-reported; Codex separately measured dependency discovery, not whole-suite base-controller suitability. Persisted-name conflict was conditional: the copied metadata's empty config_json does not itself establish that conflict.

## Changes

- Config now separates child launch command from explicit, independently reviewed `firewall_program`. Legacy synthetic configurations may omit it; production packet decoding rejects omission. The actual image must be a pinned constituent. The entry anchor remains empty and entry admission remains false.
- Production uses its own `os.getpid()` as the candidate controller, never a packet-supplied arbitrary exemption. The controller interpreter still must equal this process's sys.executable; the misleading distinct-path requirement was removed.
- PowerShell attests that its immediate parent is that exact PID, obtains the parent's actual MainModule image and start-time ticks, and compares the image to the firewall target. Failure to inspect stops the operation. Subsequent operations bind the exact first-observed start time, preventing acceptance of changed PID identity.
- The complete known matching PID list is retained in evidence. Only the positively attested controller is accepted; every other known matching process stops creation. Duplicate/invalid PID lists and missing/changed controller evidence fail closed. Unreadable-process uncertainty remains explicit, not equivalent to absence.
- The native create branch repeats the matching-process inventory immediately before creation and requires the prior controller attestation. Rule ownership, read-back and verified cleanup remain unchanged. An extra process does not prevent cleanup of an already owned rule.
- Before authentic child dependencies are constructed, a read-only environment attestation checks the child's own actual process image using the same direct-parent mechanism. It does not create/remove a rule or grant a child exemption for rule creation. Raw adapter stdout/stderr remain exclusively captured by the existing executor.
- The controller is accepted by the concurrency check, NOT exempted from the firewall rule. The proposed rule intentionally covers both controller and child actual runtime images. It is not a universal network guarantee.

## Verification

Final run: 491 tests across the same 24 explicitly named synthetic modules, 14.821 seconds, 489 passed, two skipped, zero failures/errors. Output is in `synthetic_test_output.final.txt`. Expected negative-fixture collision messages are preserved. Intermediate 489-test output remains historical; use the final 491-test checkpoint.

New cases cover reviewed image separation, missing production image, valid controller lifecycle, other matching PID rejection, missing/foreign/changed controller identity, malformed inventories, attestation binding to later calls, and child image failure preventing dependency loading. Windows PowerShell source parsing passed; the script was NOT executed. Synthetic tests do not prove the native Windows checks work on this machine.

`manifest.final.json` identifies all 11 changed source/test files and byte-preserved `.final` copies. Ten files have preserved `.before` copies and comparisons in `source.final.diff`; the small config-test addition has only its `.after`/`.final` copies (its pre-edit bytes were not checkpointed). Intermediate snapshots/manifests are retained, not overwritten. `STATUS.json.before` preserves the incoming index.

## Next checkpoint and limits

Peer source/diff review is next, especially the Windows direct-parent/start-time checks, rule targeting, child-before-dependency attestation, and failure cleanup. No genuine PowerShell adapter invocation, firewall operation, model/tokenizer loading, database access, native Job launch, network or manuscript change was performed in this batch. Entry/worker/native/executor admission constants remain false and PACKET_PATH/PACKET_SHA256 remain None.

Task 3 still needs a refreshed complete constituent inventory (including runtime redirector/configuration dependencies), frozen execution packet, review and separately scoped user execution decision. No packet is frozen or certified by this repair. Process enumeration is a time-bounded observation and cannot eliminate races or unreadable-process uncertainty. No API key is needed.
