# First provider compatibility candidate: preparation audit

Codex implementation self-verification, 24 October2026. User requested region verification and preparation so the next prompt can start tests. No paid inference authorized or performed in this preparation.

## Read-only findings

New inspect_databricks_readiness.py was tested with eight isolated synthetic cases and executed once outside the previously diagnosed network sandbox under an explicit environment approval. It made GET /config and four foundation endpoint metadata GETs. /config401 leaves region unverified; it did not follow a redirect or elevate token scopes. Four detail responses confirmed foundation identifiers system.ai.gemma-3-12b-it, system.ai.llama_v3_3_70b_instruct, system.ai.qwen3-next-80b-a3b-instruct and system.ai.gpt-oss-120b. Raw configs/error bodies/credentials were not persisted. Zero inference calls. Existing source receipts retained.

Official pricing/model-limit/reasoning documents were checked. Model-specific DBU rates are public evidence; an example SKU dollar price is not this account's rate. The candidate uses an explicit $1/DBU assumption, not a claimed actual account price. Published output ceilings exceed the proposed diagnostic caps. Actual workspace quotas still may cause429; the diagnostic stops without retry. GPT-OSS low reasoning setting is documented at https://docs.databricks.com/aws/en/machine-learning/model-serving/query-reason-models. Source/date references and all budget assumptions are in DECISION_FOR_USER.md and PLAN.json.

## Implemented small test

provider_compatibility_smoke.py uses the fixed fictional note and five role probes. It reuses reviewed HTTP/accounting/prompt/parsing code but never enables the full paired runner, genuine retrieval, authentic tokenizers or broader model execution gates. No standard benchmark queries are used. It verifies fresh attempt path, exact source membership and file hashes before local key read. Dynamic credential-reader source is included. All known chargeable attempts are durably reserved before dispatch. Known usage is settled before accepting content. Unknown usage retains conservative exposure. Max5 logical calls, no retries.

One existing accounting component was extended to support explicit unmeasured local token counts (None), with separate request_bytes/input_measurement fields. Other local token-count paths remain measured and validated. This avoids falsely recording raw bytes as tokens. The full named regression suite passed after this change.

## Additional read-only Codex source review and fixes

Separate subagent Boyle found: incomplete approval/manifest package; credential redaction gaps in provider-controlled ledger fields; no independent watchdog; bytes mislabeled as tokens. Repairs: exact required source set incl dynamic helper and initializer; recursive decoded-string/key redaction before any persistence and stop on credential echoes; explicit user opt-in to a narrow cooperative-timeout exception; unmeasured-token metadata as described above. The final source manifest is generated after all edits. Real approval remains absent intentionally.

Follow-up review found no remaining demonstrated defect within the revised preparation/synthetic scope; it requested approval-binding and write/fsync regressions. Added individual plan/manifest/timeout-opt-in tests, pre-POST event failure and settlement-fsync failure checks. New smoke tests total16, including JSON-escaped credential echoes scanned across every attempt artifact, malformed/excessive usage, single-use directory, no-execution default, exact membership, generated answer propagation and first-failure stop. Reviewers did not read credentials, run tests/network or provide Antigravity concurrence. The timeout exception and price assumption require real user acceptance before dispatch; a reviewer verdict is not authority.

## Final validation

188 tests in23.280seconds, all PASS with zero failures/errors/skips, across nine named modules. Includes16 smoke, eight readiness,16 metadata,15 static full-study, six budget,30 run-control,25 paired workflow,31 accounting and41 original baseline tests. The 350-query stress subtest still stubs fsync for speed; smaller/injected durability cases are separately tested. No live socket/model/store/tokenizer operations in tests. The new real region/model-identity probe was metadata-only and is separately identified above. No broad discovery, package installs, manuscript/statistics changes or promotion.

The runtime/OS and arbitrary concurrent file writers are not certified by this narrow source manifest. Frozen source identity is not evidence of backend weight/template equality. Directory durability on sudden power loss and Python token-memory zeroization are not universally guaranteed. Unknown costs and timeout ambiguity are retained, not converted to success or free retries.
