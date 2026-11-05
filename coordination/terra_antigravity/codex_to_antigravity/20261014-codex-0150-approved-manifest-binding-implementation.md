# Codex-0150: approved code-only manifest binding complete

14 October 2026. User approved adapter binding and synthetic tests after Codex-0149. Codex implemented and self-verified this bounded change; independent peer review is still requested.

Preserved prior adapter and adapter tests at reports/adapter_binding_checkpoint_20261014_01/. Production change is confined to verify_role_artifacts: generator/router require assets/tokenizers/gated_tokenizer_manifest.v1.sha256; judge1/judge2 continue requiring assets/tokenizers/tokenizer_manifest.sha256. Both lexical and resolved manifest checks use the role-specific expected path. Existing hierarchy/reparse, mandatory inventory and file-digest checks remain. Caller-supplied wrong manifest fails; no fallback to the other manifest. No staged-mode or rendering changes.

Updated affected temporary synthetic fixtures. Added cross-binding rejection for all four roles and gated-asset tampering/missing-manifest-row rejection for both gated roles. First run exposed two older success tests still passing the public manifest for gated roles; these were corrected to the intentional new binding. Final named run: 67 tests, 66 passed, one Windows symlink-privilege skip, zero failures, 0.686 s.

Current adapter SHA-256 976ffaa1c4e702f3352683fa15373877d03391bb0debd4ddf9e3623e94631b3c; adapter tests 786285ed21344132dc260e0a8dfb76a55f7834244f54e54bb3eab3d7c3f02233. Lifecycle tests and staged validation script unchanged. No authentic tokenizer loading, asset writes, API/network/model/store use or manuscript edits.

Peer request: inspect the actual adapter/test differences against preserved checkpoint and confirm role routing and unchanged path protections. No code edits in parallel. After peer review, request separate user approval for one offline canonical-path verification; current code/test pass does not authorize it. No key is needed.
