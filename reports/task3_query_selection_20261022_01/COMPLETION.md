# Authorized first Category B input selection

Date: 22 October 2026. Codex implementation self-verification. Authority: user replied `yeah you may` to the request to inspect benchmark query IDs/categories/text and select the first Category B query. This approves input selection only, not a smoke run.

Selected B001, category B_Evolutionary, record 101 in original file order (zero-based index 100). The exact UTF-8 query text is preserved in selected/query_selection.json and selected/packet.with_query.proposal.json. Query SHA-256: 55ae112d6bf9526988d3a7e412255200f5d684779724c4c83f3cb8d6d87c6723.

The selection is deterministic, not based on answer quality, gold targets or prior performance. It concerns civil-rights/equal-protection doctrinal evolution from Minor to Brown; this selection does not evaluate that legal question.

## Scope and evidence

- Before/after benchmark SHA-256 remains 8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3. Population: 350. Projected category counts were A_Factual 100, B_Evolutionary 100, C_OutOfContext 75, D_Adversarial 75.
- The stdlib-only projection helper reads/scans the source JSON bytes. Excluded values necessarily occur in those bytes, but are skipped structurally rather than passed to json.loads, unescaped into application values, used for selection or included in outputs. Record field names are decoded for projection/duplicate checks. Allowed fields are id/query_id (identifier aliases), category and query; actual records use query_id/category/query.
- Five synthetic tests passed in 0.007 seconds. Tests include a guarded JSON decoder rejecting a synthetic excluded-value sentinel, nested/escaped values, first-in-file rather than ID sorting, duplicate/trailing malformed input, and missing/conflicting query identity.
- The initial helper recognized B followed by space/punctuation but not the actual underscore label. It stopped with no output directory. A field-only category/count inspection identified B_Evolutionary; the helper added underscore recognition, tests passed, and selection completed with exit 0. The initial helper is preserved as select_query.initial_label_stop.py. This was preparation, not a diagnostic execution attempt or retry.
- Original packet.proposal.json remains unchanged. A new packet copy includes the exact selected input, retains execution_authorized=false and execution_packet=null, and keeps authorization_id/authorization_sha256/reviewed_approval null. The input-read gate was removed from its remaining-gates list; no other gate was removed.

No retrieval worker, model, tokenizer, database client, graph decompression, firewall operation, native Job execution, network/API call, credential read or manuscript edit occurred. Production source and all admission constants were unchanged. The root anchor remains None/None. No approval record was fabricated.

Next: peer review the populated candidate, inventory/native assumptions and proposed 300-second / 4 GiB / 16 MiB limits, then obtain a separate exact one-attempt execution decision if the package is ready. This input-selection approval must not be repurposed as execution authority. No API key is needed.
