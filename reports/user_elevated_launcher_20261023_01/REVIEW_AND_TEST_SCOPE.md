# User-elevated launcher preparation

23 October 2026 (Asia/Dhaka). Scope: user requested preparation after the agent's non-elevated check stopped the previous permission. No renewed execution permission has been granted. Prior stop and approval records remain preserved.

## Implementation

New source `scripts/matched_baseline/launch_offline_smoke_user.ps1` is a no-argument, source-held outer wrapper for a USER-OPENED 64-bit Administrator Windows PowerShell 5.1 window. LaunchAdmitted=false, LaunchRecordPath=null and LaunchRecordSHA256=null. The current script exits at its hold before any body execution. It never invokes UAC or self-elevation and has no test/bypass switch or retry loop. Existing Python admission flags and root anchor are unchanged.

After future review/freeze/renewed permission, an independently pinned outer launch record would bind exact parent command, packet, authorization, entry anchor, bootstrap files, member manifests, parent evidence and unique wrapper evidence/attempt-lock paths. Record schema fields are visible in Assert-ExactFields. The launcher hashes full declared members before Python starts, rejects manifest conflicts and complete-root membership changes, and rejects reparse ancestry. The original inner parent/child constituent checks remain mandatory; wrapper checks do not replace them.

Owned wrapper evidence is created exclusively. Existing-directory collisions cannot receive a terminal write. Transcript start is mandatory; closure and hash precede terminal status. A persistent dispatch-intent lock is never removed. Parent dispatch occurs once; native exit is captured immediately with local PS 5.1 stderr handling. The wrapper reports parent success only as requiring a post-run audit, not an independent proof of firewall absence. It does not create/remove rules itself.

Before the controller, inherited process environment is cleared to SYSTEMROOT/WINDIR/PATH only, avoiding inherited Python path hooks and credential variables. Original environment values remain in memory for restoration and are never printed or written. Current preparation/tests do not execute that branch. Both location and environment restoration errors count as wrapper failure.

## Trust-root freeze requirement

Do not include the wrapper's own hash inside a record whose digest is embedded in that wrapper: this would form a cycle. The exact frozen wrapper must be independently pinned in the user's eventual launch command/record outside its own inner hash closure, like the Python entry anchor. The packet/member manifest and outer bootstrap inventories must exclude these independently pinned trust roots from their own dependency cycles. No wrapper launch record, admitted packet, populated anchor or runnable command is supplied now.

Final record must also freeze the packet's complete member-manifest bindings and direct bootstrap paths. Assert-LaunchCoverage rejects empty, omitted, extra, duplicate or differing bindings against the packet, including complete-root scope changes. Alias manifest paths are deduplicated against the packet's reviewed declarations. Exact final record, Python admission delta, affected source/driver identities, wrapper root pin, process/version/elevation checks and renewed dated permission must be reviewed before invocation. Existing selected-scope inventories are not full OS dynamic-load certification.

## Tests and limitations

Named module: tests.test_offline_smoke_user_launcher_synthetic. Initial eight focused tests passed in 6.948s. After adding explicit outer coverage checks, all ten focused tests passed in 4.029s. They use Windows PowerShell 5.1's Parser.ParseFile on the source, extract only FunctionDefinitionAst nodes, and exercise those functions on temporary synthetic files. The launcher/main body is NEVER dot-sourced or executed. No models/tokenizers, real store, firewall commands, Windows Job APIs, real controller launch or elevation are exercised.

Tests cover source-hold/parser compatibility, exclusive writes retaining prior bytes on collision, pinned JSON tamper, complete-member/extra-file detection, changed member failure, duplicate rejection, unsafe paths, unknown fields, missing bootstrap coverage and changed complete-root scopes. Initial run had four failures because Get-FileHash was unavailable in the PS5.1 subprocess environment. Replaced hashing with pinned-file .NET stream SHA-256; all eight then passed. This was synthetic debugging, not a retry of the prohibited B001 attempt.

No full wrapper lifecycle/elevated-native integration is certified by function tests. Environment clearing/restoration, transcript behavior, interruption recovery and native parent launch still require static peer review and remain untested operational branches. A success-looking source or parser pass is not launch authorization.
