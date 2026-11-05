# Codex-0127: authorized acquisition stopped on CDN host

14 October 2026, Asia/Dhaka. Read saved launcher/child records and staged directory for user-run bbd49cf5. No retry, credential access or acquisition by Codex.

Evidence: tmp/gated_run_20261014_024001_bbd49cf5/. Child and wrapper exit1, CHILD_EXECUTION_FAILURE. Both roles rejected redirect to us.aws.cdn.hf.co on first tokenizer.json. Each files_acquired is empty; staged directory contains only three evidence files (no finalized assets). Protected pre/post hashes match; launcher errors empty and transcript closed cleanly. Token removal is reported by the launcher; Codex cannot inspect the user's ended environment. Empty disk readback verified=true is vacuous, not verification of downloaded files.

Cause is incomplete approved-host inventory, not a PC capacity or model-access diagnosis. Official https://huggingface.co/docs/hub/models-downloading now explicitly lists us.aws.cdn.hf.co and us.gcp.cdn.hf.co as CDN edges, plus regional LFS/Xet endpoints; machine-readable metadata https://huggingface.co/.well-known/meta.json is documented. My earlier route review should have incorporated this current inventory before launch; this addendum corrects that omission.

Request a narrowly scoped source repair: preserve failed-run artifacts and accepted source; add documented exact CDN edge hosts needed for this HTTP flow, retaining HTTPS443/no-userinfo, external Authorization stripping and rejection of unlisted/lookalike hosts. Do not add whole-domain wildcard or arbitrary auto-discovery. Return exact downloader diff/hash, synthetic redirect/security tests and updated launcher pin. Validate membership from official current metadata/docs; distinguish download CDN endpoints from CAS protocol APIs rather than adding every hostname blindly.

The user's approved single attempt has been consumed. No retry or credentialed probe authorized. After review, request renewed single-attempt user approval with same seven files/caps and fresh staging. No API/model inference, canonical admission or manuscript edits. Existing failed evidence stays intact.
