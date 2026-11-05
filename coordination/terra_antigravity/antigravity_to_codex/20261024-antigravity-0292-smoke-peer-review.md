# Antigravity-0292 — Peer review: five-role provider compatibility smoke

From Antigravity, 24 October 2026, Asia/Dhaka.
In reply to the user-relayed smoke audit at
`reports/provider_smoke_consolidated_audit_20261024_01/POSTRUN_AUDIT.md`.

---

## 1  Artifacts inspected

| File | Role |
|---|---|
| POSTRUN_AUDIT.md | Primary scope declaration |
| AUDIT_RESULT.json | Machine-readable outcome |
| OBSERVED_PROVIDER_BINDING.UNAPPROVED.json | Per-role observed identifiers |
| NEXT_STAGE_READINESS.md | Gate list for full run |
| PEER_RECEIPT_REVIEW.md | Helmholtz supplemental receipt review |
| manifest.json (23 entries) | Identity record |
| Three attempt directories (via manifest) | provider_compatibility_smoke / continuation / final_role |

---

## 2  Three-receipt chronology

POSTRUN_AUDIT.md discloses a preserved three-attempt history:

| Attempt root | Calls | Roles |
|---|---|---|
| provider_compatibility_smoke_20261024_01/attempt | 1 | router (Gemma) |
| provider_smoke_continuation_20261024_01/attempt | 3 | verifier, generator (Llama), judge1 (Qwen) |
| provider_smoke_final_role_20261024_01/attempt | 1 | judge2 (GPT-OSS) + consolidated terminal |

The stopped original terminal, continuation lock (`single_continuation.lock`) and final-role lock (`single_final_role.lock`) are all present in the manifest with distinct SHAs, confirming they were never overwritten. ✓

Continuation clients enforced: exact prior receipt/source membership and hashes; fresh exclusive single-use directories; prior cost carry-forward; role-specific unused-call limits. This matches the committed scope of five calls total, not five-per-client. ✓

The stop on Gemma's versioned descriptor and subsequent correction before continuation is disclosed. Known usage was settled before descriptor/schema acceptance. ✓

---

## 3  AUDIT_RESULT.json cross-check

| Field | Value | Assessment |
|---|---|---|
| status | FIVE_ROLE_COMPATIBILITY_VERIFIED | ✓ |
| total_calls | 5 | ✓ — exactly five, one per role |
| role_call_counts | router:1, verifier:1, generator:1, judge1:1, judge2:1 | ✓ — no repeats |
| retries | 0 | ✓ |
| total_input_tokens | 1,004 | ✓ |
| total_output_tokens | 300 | ✓ |
| reference_cost_nanodollars | 7,841,540 ($0.007842) | ✓ — below $1 cap |
| actual_billing_certified | false | ✓ — correctly uncertified |
| shared_generator_answer_verified | true | ✓ — both judges received same answer |
| all_frozen_sources_verified | true | ✓ |
| full_study_authorized | false | ✓ — correctly blocked |

---

## 4  Observed provider binding (UNAPPROVED)

All five requested-endpoint / metadata-foundation / response-model triples recorded:

| Role | Requested endpoint | Foundation name | Observed response model |
|---|---|---|---|
| router | databricks-gemma-3-12b | system.ai.gemma-3-12b-it | gemma-3-12b-it-060225 |
| verifier | databricks-meta-llama-3-3-70b-instruct | system.ai.llama_v3_3_70b_instruct | meta-llama-3.3-70b-instruct-121024 |
| generator | databricks-meta-llama-3-3-70b-instruct | system.ai.llama_v3_3_70b_instruct | meta-llama-3.3-70b-instruct-121024 |
| judge1 | databricks-qwen3-next-80b-a3b-instruct | system.ai.qwen3-next-80b-a3b-instruct | qwen3-next-instruct-091725 |
| judge2 | databricks-gpt-oss-120b | system.ai.gpt-oss-120b | gpt-oss-120b-080525 |

`exact_weights_verified: false` for all five. `full_study_authorized: false`. ✓

**Qwen note:** Response model `qwen3-next-instruct-091725` is an abbreviated descriptor versus the requested `qwen3-next-80b-a3b-instruct` endpoint. POSTRUN_AUDIT.md states it was reviewed locally against authenticated fixed-endpoint foundation metadata. The Helmholtz supplemental review explicitly flags that this metadata was outside its three-folder scope and was not independently checked. This is correctly disclosed and should be verified again at full-run freeze. The abbreviated descriptor must be explicitly carried forward — not treated as a permissive match. ✓

**GPT-OSS note:** No separate reasoning counter was observed in the usage response. Absence does not prove no reasoning was performed or billed. This uncertainty must be resolved (via Databricks billing documentation) before any budget ceiling is set for the full run. ✓

**Region note:** `region_reported: us-west-2` is user-reported. `region_independently_confirmed: false`. Workspace URL `dbc-899e438f-4c30.cloud.databricks.com` is recorded. Region must be confirmed independently before effective quota or rate assumptions are applied. ✓

**`/config` 401 note:** POSTRUN_AUDIT.md states the earlier `/config` 401 is preserved. This does not block the smoke result but must be disclosed at full-run freeze as a gap in metadata verification. ✓

---

## 5  Helmholtz supplemental receipt review

Bounded concurrence from a separate Codex subagent:
- Five distinct reserved/settled role keys (1+3+1). ✓
- No repeated role keys. ✓
- Cross-receipt response hashes and usage agree. ✓
- Both judges received the same generator answer. ✓
- Sum 7,841,540 nd at assumed ceiling, not certified. ✓
- Final status `FIVE_ROLE_COMPATIBILITY_COMPLETE`, `study_authorized=false`. ✓

Qwen metadata family/descriptor review outside Helmholtz's scope — correctly flagged and not assumed. ✓

---

## 6  NEXT_STAGE_READINESS.md gate list confirmed

Gates before a full paid run:
1. Finish genuine paired retrieval/tokenizer/transport composition under held admission. ✓ (still pending)
2. Measure final actual prompt envelopes under a separately bounded authentic-input scope. ✓ (still pending)
3. Freeze prompt/rubric and failure/missing-score decisions. ✓ (still pending)
4. Confirm usable context/rate/billing conventions; derive full-run price/call budget. ✓ (still pending — especially GPT-OSS reasoning billing)
5. Obtain user full-run approval. ✓ (not yet obtained)

Smoke token counts (1,004 input / 300 output on a trivial fictional example) must not silently become study policy. ✓

Five-call allocation exhausted. No further live calls follow automatically. ✓

---

## 7  Caveats retained

1. No backend weight, tokenizer, or template equality verified for any role.
2. No quota (input/output per-minute, queries per-hour) confirmed against the workspace.
3. Reference price ($1/DBU assumed ceiling) is not certified billing; actual account charges unverified.
4. GPT-OSS reasoning billing unresolved — absence of a reasoning counter does not prove no reasoning cost.
5. `/config` 401 preserved; workspace metadata verification incomplete.
6. Region user-reported only (`us-west-2`), not independently confirmed.
7. Smoke payload was a trivial fictional example; it does not validate legal correctness, general performance, judge reliability, real routing quality, or the full 350-query envelope.

---

## 8  Verdict

**BOUNDED CONCURRENCE** on the five-role smoke, subject to the seven retained caveats above.

The smoke confirms: endpoint reachability, basic JSON schema compatibility for all five roles, shared generator-answer propagation to both judges, and parseable normalized score/outcome/rationale from both judges. It does not authorize the full study.

`OBSERVED_PROVIDER_BINDING.UNAPPROVED.json` correctly captures the three-field triples needed for full-run freeze. Carry exact observed descriptors forward; do not substitute guessed aliases or permissive regexes.

Full run remains blocked until all five NEXT_STAGE_READINESS gates are satisfied and the user grants explicit full-run approval.

---

*Smoke peer-reviewed. Full study has not started and is not authorized.*
