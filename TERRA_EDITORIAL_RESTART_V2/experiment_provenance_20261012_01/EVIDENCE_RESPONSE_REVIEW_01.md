# Review of Antigravity-0055 and correction to initial inventory

Codex, 12 October 2026. Read-only source inspection, SHA256 rehashing and Python AST comparison only; no runtime imports, model/store calls, manuscript/config edits or experiment executions.

## Confirmed recovery

`issue18_bundle/scripts_pipeline/ask_terra.py` hashes to `430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd`, the hash recorded in obscure/famous results. Root ask_terra.py hashes to `0cca5cf440a1299853c37899647465b5f1f843803898e630d8d5402a3d9fffbb`. Independent normalized-text diff finds one changed comment: deterministic outputs to greedy decoding. AST dumps excluding positions are equal. Source bytes are not identical; executable Python syntax is equal. This recovers the recorded source artifact for those suites, not proof of every historical execution or all dependencies.

## Correction to Codex's initial cap interpretation

The initial inventory described 50 versus 75/25 as a configuration mismatch. Inspection of the full branch shows these are distinct simultaneous controls: HUB_DEGREE_CAP=50 triggers the high-degree branch, while INCOMING_HUB_CAP=75 and OUTGOING_HUB_CAP=25 limit directional neighbor selection there. Thus the claimed contradictory cap values are withdrawn. Configuration is incomplete as a description of the directional budgets, not inconsistent merely for containing 50. The code also declares MAX_GRAPH_NODES=40 and MAX_STRUCTURAL_CHARS=35000; global context limits remain separate. data/issue24_preflight.json records all three cap constants as found. This is source/preflight evidence, not proof that all primary or external historical experiments used them.

## Model field reconciliation

Current inference runner directly records response.model for flat/direct arms. TERRA arms explicitly write generation_model_served=None and copy timing's model identifier; the engine's CleanResponseOpenAI assigns model_used from the requested model argument. Therefore mixed identifiers are explained by different logging paths. It is inaccurate to interpret all `_generation_model_used` values as server-returned backend identities. Requested endpoint parity is supported; backend weight invariance is not established by these fields. No vendor claim or API query was made.

## Remaining gaps

Antigravity reports unavailable graph/code/index linkage for primary, pilot, CaseFacts and CLERC, consistent with the inventory's bounded status. Its assertion of cryptographic linkage for the temporal probe must remain specific: prompt/context/candidate hashes identify payloads, not automatically the generating code, graph or vector store. Its detailed pilot/whole-row-schema checks were not all independently repeated in this review. No blanket closure of reviewer point 2.

Original PROVENANCE_REPORT.md and artifact_manifest.json remain delivered records, unchanged. This addendum supersedes the cap-mismatch interpretation only and adds the recovered source linkage. Next step is a bounded proposed manuscript provenance disclosure identifying authentic artifacts, observed settings and unavailable linkage; no scientific/source patch is authorized by the peer verdict alone.
