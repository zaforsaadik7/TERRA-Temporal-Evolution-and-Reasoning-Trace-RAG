# Proposed first provider test — NOT YET AUTHORIZED

Prepared by Codex, 24 October 2026. This is the concrete small test the user can authorize next. It does not authorize the full 350-query comparison.

## What will happen

At most five sequential POST requests on the already supplied workspace: router/Gemma, verifier/Llama, generator/Llama, judge1/Qwen, judge2/GPT-OSS. Every role uses the same fictional note stating year1900; both judges receive the actual generator answer. No benchmark queries, vector store, graph, local embeddings/models or authentic tokenizers. Role probes test payload/output/usage compatibility; they are not a scientific paired comparison and do not infer legal correctness or judge quality.

Temperature0, streamingfalse; explicit output caps: router128, verifier512, generator512, Qwen1024, GPT-OSS4096 (reasoning_effort low). Requests bounded to8192bytes; input tokens are not locally measured, and are recorded as such. Each call reserves8192 provider input tokens, verifies actual usage, and stops on envelope overrun. Returned identity must match one of the endpoint/metadata-based aliases in PLAN.json. A different descriptor is recorded and stopped for review, not silently accepted. Stop on first HTTP, parsing, usage, identity, persistence or budget failure. No redirects or automatic retries. Attempt path is fresh and single-use.

## Money proposal and its limit

Propose a **$1 client accounting envelope**, using an intentionally conservative assumed upper price of **$1 per DBU** with the official published model-specific DBU rates. The total maximum reservation for these five calls is **$0.245216128 under that assumption**. This is not a verified account price or guarantee that a remote invoice cannot differ. Effective account pricing/credits remain unknown. No default $100 cap or full-study spend is approved.

Official reference: https://www.databricks.com/product/pricing/foundation-model-serving (checked24October2026). Published input/output DBU per million tokens used here: Gemma2.143/7.143; Llama7.143/21.429; Qwen2.143/17.143; GPT-OSS2.143/8.571. Reference-priced exposure is recorded before dispatch and settled from returned provider usage. No credit discount is assumed. No endpoint deployment, warehouse or configuration change is made.

## Time policy — explicit narrow exception

Socket/observed deadlines are120seconds per call, with first failure stopping the sequence. There is **no independent native hard-kill watchdog** for this small diagnostic, so120seconds is not a universal guaranteed wall-clock interruption. Approving this packet must explicitly accept that narrow exception; it does not relax the independent-supervision requirement for the full study. Remote processing/billing can remain uncertain after timeout; retain the reservation and do not retry.

## Region and readiness evidence

The user reported us-west-2 from their profile. Independent GET /config returned401, so that region remains **USER_REPORTED**, not API-confirmed. Four authorized metadata GETs did confirm the intended foundation model names. The workspace origin is unchanged; do not derive a different host from the unconfirmed region. The small diagnostic uses the actual supplied host and a conservative price assumption rather than claiming regional invoice verification.

Source receipt: reports/databricks_readiness_20261024T094056Z_b8792af3/report.json. Earlier readiness states READY for all four model endpoints remain preserved. No account-domain API, SQL/billing query, model invocation, credential-scope change or genuine tokenizer measurement occurred during this preparation.

## Approval boundary

APPROVAL.json deliberately does not exist. The CLI refuses before credential access unless a user-approved record matches the frozen plan, source manifest, $1 envelope and both pricing/timeout assumptions. Do not edit the draft template into an approval without an actual user instruction. The record validates the agent's captured authorization; JSON alone is not proof of human provenance.

Suggested next user message:

> I approve the five-call compatibility smoke in this packet, with the $1 client envelope and its disclosed pricing assumption and cooperative-timeout exception. No retries or full-study run.

After that instruction Codex can preserve the actual user message, finalize the small approval record and run the test outside the network-blocked sandbox. The existing local token is used only inside the smoke process, never printed, hashed or copied into reports. All full-study/real-data gates stay held.
