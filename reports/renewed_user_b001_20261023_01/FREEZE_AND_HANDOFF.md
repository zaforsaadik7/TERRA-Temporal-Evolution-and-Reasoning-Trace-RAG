# Renewed user-window attempt: frozen, not invoked by agent

23 October 2026, Asia/Dhaka. Exact renewed permission is in HUMAN_PERMISSION.md. The user reports their window is Windows PowerShell 5.1.19041.7802, 64-bit and Administrator. This agent remains non-elevated; it has not attempted B001.

## Checks completed

Reviewed venv/base interpreter, PowerShell executable and kernel32.dll size/hashes match. Full pre-freeze filesystem check passed: 30,552 unique member files plus 20 declarations (30,572 hash observations). Complete-root membership checks passed for declared complete roots. This is point-in-time evidence, not a lock against later mutations. An initial read-only PowerShell command had a foreach-pipeline parse error, so nothing in that command executed. The corrected expression performed the actual runtime-file checks; neither command invoked any diagnostic, model, store client or firewall operation.

## Reviewed mechanical admission delta

Only three runtime source files changed, with before copies preserved here:

- offline_smoke_production.py: ENTRY_ADMITTED False -> True only. A new repository_code.admitted.json and direct driver pin reflect its changed bytes.
- offline_smoke_entry_anchor.py: exact packet path/hash populated; root excluded from its own packet closure and pinned by outer record.
- launch_offline_smoke_user.ps1: LaunchAdmitted true and exact outer record path/hash populated only. Wrapper is independently pinned by the user's paste command, outside the record/packet hash cycle.

Other worker/native/executor global holds remain false at rest; the reviewed production composition enables/restores them only within authorized execution. No new algorithms, limits, queries, API behavior or permission scopes were added. Before/expected/final file identities are recorded in freeze_metadata.json and final checkpoints.

## Frozen identities

- execution_packet.json: 18,654 bytes; 507bb2ef5fc31e7442339ac1347327f2df030a09c7f6d6f8555638d258281037.
- authorization.json: f8d8e51076ec58cec8102d12783902387568e2b0dbabc3555341983d6d77bbe8.
- entry anchor: 4455b201f94aacb0545d39e2eeddad6f491ebfcfad86989ca4204baec42cf7bd.
- launch_record.json: de60f6cefb036944115d65489deb7df1832221125a3b5b76ebfe65d009fe54ea.
- user launcher: 813f90fa91c7ff3dd21a68f66f106d90f9a88d6431b8aa393a91ff5e387b4c30.

Actual production decoder and exact approval-record validator passed without running the parent. In-memory unissued-receipt stand-in measured request/context 2,901/3,121 bytes. No real receipt or child_request file exists yet. Runtime receipt issuance, exact final request/context bounds, copy parity and environment/process/native checks remain enforced during the one authorized user invocation. PS5.1 parsed the actual frozen wrapper and ran extracted coverage functions against the frozen record/packet; main was not invoked. This is not an elevated or authentic feasibility result.

The candidate parent directory was created empty because SmokeEvidenceWriter requires that parent. No evidence/snapshot/disposable run directories or attempt lock were created. There is no wrapper/parent/child outcome yet. No source-store client connection, model/tokenizer initialization, rule query/change, Windows Job construction, API or manuscript/statistics change occurred during freeze. Schema validation imported the designed lazy runtime modules (including numpy), but constructed no worker/model/client.

## User instruction

Paste COMMAND_FOR_USER.txt exactly ONCE into the already opened Administrator Windows PowerShell 5.1 window. It independently checks the wrapper hash, then invokes the wrapper synchronously with NoProfile and no automatic elevation. Hashing can be quiet for several minutes; do not paste again or close the running window. Return the final output or any STOP/failure. Do not retry, remove attempt locks or run the parent directly. Evidence will be preserved under this folder's wrapper_evidence plus the reviewed candidate parent evidence path. A failure or unconfirmed termination may require ownership-checked manual recovery, not a blind rule deletion.
