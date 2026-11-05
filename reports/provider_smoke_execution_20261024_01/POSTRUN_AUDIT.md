# First live compatibility smoke — stopped at identity gate

Codex implementation self-verification, 24 October2026 (Asia/Dhaka). One authorized attempt, no retry or full-study execution.

## Actual outcome

Frozen CLI status STOPPED_NO_RETRY, process exit1. Attempt folder: reports/provider_compatibility_smoke_20261024_01/attempt. Exactly one reserved/settled call, router/Gemma; no other roles called. Completed-role list is empty because the identity gate is applied before role acceptance. HTTP exchange itself succeeded.

Saved response: model `gemma-3-12b-it-060225`, finish_reason stop, content `{"route":"EASY"}`, prompt_tokens76, completion_tokens7, total_tokens83. The returned versioned model descriptor is not among the frozen accepted aliases (endpoint descriptor, metadata foundation identifier and endpoint without databricks prefix). Source accepted_result rejects it before content parsing. Therefore this is an observed identity-mapping mismatch, not a connectivity, credential, rate-limit, malformed-output or token-budget failure. No exact backend-weight/tokenizer equivalence inferred from the family name.

Response SHA256 e4bee916a3e85f8c45bc0095896d3729fcd24bb9e5cd8e63e233bd7a90a81ab5. Request SHA256 0ce900e541a858e3dc0c600cc03ee7d4b9a11a84914c3bca89beaba4e4a71700. Usage was durably settled before rejection, without envelope violation. Reference-priced cost212869nanodollars ($0.000212869) at the approved assumed $1/DBU ceiling; actual account billing is not certified. The $1 cap was retained and never increased.

## Authority and integrity

Actual user message is preserved in HUMAN_PERMISSION.md and APPROVAL.json under the frozen smoke package. Plan and source manifest matched reviewed SHA256 identities before credential access. The explicit environment approval allowed this paid, five-call-maximum diagnostic outside the network-blocked sandbox; the first identity failure stopped the attempt after one POST. Persistent single_attempt.lock and all receipts remain intact. No second attempt or unauthorized role call followed.

Postrun audit independently read the saved events/ledger, checked the exact posted request against frozen prompt construction, verified the selected response's fields/usage and reason for rejection, checked sequence/settlement and all frozen source/package identities. No genuine model/tokenizer/store operation locally, no benchmark input, manuscript/statistics change or promotion. Existing full-study gates remain held. No .env file was opened, hashed or copied by this audit; only the smoke process read the local token.

## Next disposition

OBSERVED_IDENTITY_ALIAS_PROPOSAL.UNAPPROVED.json records the observed descriptor and evidence. It does not modify the frozen allowlist or assert backend equivalence. An explicitly reviewed updated identity mapping and fresh permission would be needed for any new paid attempt, since the user required no retries. Do not rerun the existing command or edit its preserved evidence/approval.
