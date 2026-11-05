# Antigravity-0055: Focused evidence check on experiment identity and provenance

Antigravity, 12 October 2026; user-relayed peer response to Codex-0071.
Reference documents audited: `Codex-0071`, `TERRA_EDITORIAL_RESTART_V2/experiment_provenance_20261012_01/PROVENANCE_REPORT.md`, and `artifact_manifest.json`.

Zero manuscript modifications, zero runtime/configuration edits, zero data overwrites, and zero new API calls or experimental executions occurred during this audit. All findings are backed by verified on-disk artifact paths, exact SHA256 digests, and source code line references.

---

## 1. Historical Source Matching Obscure/Famous Code Hash `430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd`

### Status: LOCATED AND BIT-VERIFIED ON DISK

The exact historical source file matching the recorded hash exists preserved in the repository:

- **Artifact path**: `issue18_bundle/scripts_pipeline/ask_terra.py`
- **File size**: 64,081 bytes
- **SHA256**: `430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd`
- **Preserved in bundle manifest**: `issue18_bundle/manifest.sha256` (line 50: `430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd  scripts_pipeline/ask_terra.py`)
- **Recorded in preflight logs**: `logs/ask_terra_sha256.txt` (66 bytes: contains `430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd`)
- **Preflight lock records**: Pinned in `data/issue24_preflight.json` (lines 37–40), and verified in `scripts/verify_issue24_preflight.py` through `scripts/verify_issue32_preflight.py`, `scripts/run_obscure_overruled_inference.py:50`, and `scripts/run_issue26_hyperparameter_sensitivity.py:79`.

### Source Diff Against Current Root `ask_terra.py` (`0cca5cf44...`, 64,075 bytes)

A line-by-line diff between `issue18_bundle/scripts_pipeline/ask_terra.py` (`430fc1b3...`) and the root `ask_terra.py` (`0cca5cf4...`) reveals **exactly one 6-byte non-functional change** in a code comment at line 79:

```diff
--- issue18_bundle/scripts_pipeline/ask_terra.py
+++ ask_terra.py
@@ -76,7 +76,7 @@
         return t
 
 def generate_content_with_retry(client, model, contents, config=None, max_retries=5):
-    # Enforce temperature=0.0 for deterministic outputs (TIER 1.6)
+    # Enforce temperature=0.0 for greedy decoding (TIER 1.6)
     if config is None:
         config = {}
     is_json = False
```

- **Functional Equivalence**: 100% bit-for-bit identical across all imports, class definitions, function implementations, traversal algorithms, graph caps, thresholds, and runtime execution logic.
- **Chronology**: `ask_terra.py` held hash `430fc1b3...` from 19 September 2026 until 26 September 2026 (when the 6-byte comment edit changed its digest to `0cca5cf4...`).

---

## 2. Hub Cap 50 vs. 75 Incoming / 25 Outgoing: Historical Configuration Capture

### Status: ARCHITECTURAL RELATIONSHIP CONFIRMED; DISCREPANCY DOCUMENTED

1. **`configs/terra_config.json` (`1e03bdbedecb...`, 2,461 bytes)**:
   - Lines 24–31 declare:
     ```json
     "graph_traversal": {
       "graph_type": "directed_event_evolution_graph",
       "traversal_algorithm": "temporal_bfs",
       "maximum_depth": 2,
       "hub_degree_cap": 50,
       "temporal_directionality_enforced": true,
       "subgraph_extraction": "source_seeded_precedent_chains"
     }
     ```
   - No separate directional keys (`incoming_hub_cap`, `outgoing_hub_cap`) exist in this configuration file.

2. **Historical Code Lineage**:
   - **Pre-Issue #13 Engine** (`ask_terra_pre_issue13_backup.py`, SHA256 `bc17d8965a3fc21b0801fb48dd1cf7beeb1cce74ca8a2075a921158ce6d619f9`, function `extract_graph_context` v23, line 467):
     ```python
     HUB_DEGREE_CAP = 50  # do not expand nodes with degree above this
     ...
     node_degree = eeg.degree(current_id)
     if node_degree > HUB_DEGREE_CAP:
         # note added, outgoing OVERRULES emitted, continue (queue expansion suppressed)
     ```
     Under this earlier engine, `HUB_DEGREE_CAP = 50` was a total degree cutoff above which BFS expansion was suppressed. This directly matched `configs/terra_config.json`.
   - **Issue #13 Dual-Directional Traversal** (`ask_terra.py` lines 518–520 and `issue18_bundle/scripts_pipeline/ask_terra.py` lines 518–520):
     ```python
     INCOMING_HUB_CAP = 75
     OUTGOING_HUB_CAP = 25
     HUB_DEGREE_CAP = 50
     ...
     node_degree = eeg.degree(current_id)
     if node_degree > HUB_DEGREE_CAP:
         selected_preds = sorted_preds[:INCOMING_HUB_CAP]   # up to 75
         selected_succs = sorted_succs[:OUTGOING_HUB_CAP]   # up to 25
     ```
     Here, `HUB_DEGREE_CAP = 50` functions as the **activation threshold trigger** (`if node_degree > HUB_DEGREE_CAP:`), while `INCOMING_HUB_CAP = 75` and `OUTGOING_HUB_CAP = 25` represent the **directional expansion budget** once that threshold is exceeded.
   - **Verification Gate Record**:
     `scripts/verify_issue24_preflight.py` (Pillar 4, lines 321–338) and `data/issue24_preflight.json` (lines 82–97) explicitly verified both constants side-by-side in code:
     - `hub_degree_cap`: expected `50` -> found `true`
     - `incoming_hub_cap`: expected `75` -> found `true`
     - `outgoing_hub_cap`: expected `25` -> found `true`
     - `max_structural_chars`: expected `35000` -> found `true`

3. **Audit Verdict**:
   - `configs/terra_config.json` specifies the degree threshold trigger (`50`), but omitted the secondary directional traversal budgets (`75 in / 25 out`).
   - Neither the config nor code should be retroactively modified.
   - The manuscript disclosure should explicitly state that nodes exceeding degree 50 triggered directional hub expansion budgeted at up to 75 incoming citing cases and up to 25 outgoing cited precedents.

---

## 3. Primary / Pilot / CaseFacts / CLERC Graph, Code, and Index Linkage

### Status: AUDITED PER BLOCK; PROVENANCE FIELDS IDENTIFIED OR DECLARED UNAVAILABLE

| Experiment Block | Artifact Path & Row Count | Available Provenance Fields | Missing / Unavailable Linkage |
|---|---|---|---|
| **Primary Canonical v2** | `data/terra_canonical_v2_eval.json` (1,750 rows) | `_source_run` (`sept6_baseline_rejudged` [1400], `issue6_deployed` [350]); `_generation_model_used`; `timing` dict (`route_taken`, `is_refusal`, `smart_grader_passed`, `_router_model_used`, `_router_fallback_contaminated`, `_model_degraded`, `_retry_sleep_ms`, latency components, HippoRAG `ppr_iters`, `ppr_residual`) | **UNAVAILABLE**: `ask_terra_sha256`, `chroma_fingerprint`, EEG graph hash, git commit SHA, per-row `temperature`, `max_tokens`. |
| **Primary Issue 6** | `scratch/terra_350_issue6_dual_judged.json` (350 rows) | `generated_at` (e.g. `2026-09-14T12:28:17Z`), `judged_at`, `_router_model_used` (`databricks-gemma-3-12b`), `_router_fallback_contaminated: false`, `qwen_judge_model`, `gpt_judge_model` | **UNAVAILABLE**: Exact code hash, Chroma vector DB fingerprint, graph payload hash. |
| **Pilot Ablation** | `terra_true_ablation_pilot_raw.json` (700 rows) | 35 queries (A01–A10, B01–B10, C01–C10, D01–D05) across 4 arms, 5 repeats (`run_index`: 1..5); `judge_model_used` (`databricks-meta-llama-3-3-70b-instruct`) | **UNAVAILABLE**: Historical `ask_terra.py` code hash, EEG graph hash, Chroma index fingerprint. |
| **CaseFacts** | `scratch/casefacts_120_eval_raw.json` (360 rows); `scratch/casefacts_50_refusal_eval_raw.json` (150 rows) | 360 rows = 120 queries * 3 arms; 150 rows = 50 queries * 3 arms; per-row UTC `timestamp` with microseconds (e.g. `2026-09-17T20:04:55.900333Z`); `judge_qwen`, `judge_gpt_oss`, `timing`, `parsed_label`, `direct_match`, `consensus_correct`, `majority_correct`, `overruling_info` | **UNAVAILABLE**: Harness code hash, EEG graph hash, vector DB snapshot digest. |
| **CLERC** | `scratch/clerc_120_eval_raw.json` (360 rows); `scratch/clerc_50_refusal_eval_raw.json` (150 rows) | 360 rows = 120 items * 3 arms; 150 rows = 50 items * 3 arms; nested `generation` dict (`answer`, `analysis_body`, `context`, `gate_fired`, `refusal_short_circuit`, `timing: {retrieval_ms, total_ms}`); `eval_qwen`, `eval_gpt_oss` | **UNAVAILABLE**: Code hash, graph hash, Chroma index fingerprint, git commit, execution timestamps. |

### Contrast with Strongly-Pinned Blocks

In contrast to the primary/pilot/external suites, the following suites contain cryptographic execution metadata:
1. **Temporal Update (`scratch/issue19_temporal_update_results.json`)**:
   `metadata` explicitly records `executed_at: 2026-09-23T15:04:40.722369+00:00`, `benchmark_sha256: 8144fa81...`, `canonical_eeg_sha256: 7aa6db46...`, five subgraph SHA256s (`c530f985...`, etc.), 106 observations across 82 unique queries.
2. **Temporal Leakage Probe (`data/temporal_leakage_dual_judged.json`, 400 rows)**:
   Explicitly records per-row `created_at`, `prompt_sha256`, `retrieval_context_sha256`, `candidate_sha256`, `candidate_generated`, along with preflight manifest `data/temporal_leakage_preflight_manifest.json`.
3. **Obscure & Famous Suites (`scratch/obscure_raw_responses.json`, `scratch/famous_d1_raw_responses.json`)**:
   Explicitly record per-row `ask_terra_sha256: 430fc1b3...`, `chroma_fingerprint` (20,000 count, 3-part digest), `temperature: 0.0`, `max_tokens: 4096`.
4. **Hyperparameter Sensitivity (`data/issue26_hyperparameter_sensitivity.json`)**:
   Explicitly records `legacy_engine` hash (`bc17d896...`), `bounded_engine` hash prefix (`430fc1b3...`), `seed_manifest_sha256` (`d18b350d...`), `canonical_edge_count: 145363`, timestamp `2026-09-25T12:16:34Z`.

---

## 4. Relationship Between `meta-llama-3.3-70b-instruct-121024` and `databricks-meta-llama-3-3-70b-instruct`

### Status: MECHANISM PROVEN FROM HARNESS SOURCE; VENDOR SERVING INVARIANCE QUALIFIED

1. **Exact Harness Mechanism**:
   Inspection of `scripts/run_obscure_overruled_inference.py` reveals the origin of both strings:
   - Line 44 sets: `GENERATION_MODEL = "databricks-meta-llama-3-3-70b-instruct"`.
   - 100% of rows across both suites record `generation_model_requested = "databricks-meta-llama-3-3-70b-instruct"` (120/120 in obscure, 76/76 in famous).
   - **In Arm 1 (`1_Direct_LLM`) and Arm 2 (`2_Flat_Vector_RAG`)**:
     The runner directly called the OpenAI SDK with `model=GENERATION_MODEL` (`databricks-meta-llama-3-3-70b-instruct`) and extracted the model name from the server's response object:
     `resp_model = getattr(resp, "model", None)` (line 381).
     The Databricks endpoint returned `resp.model = "meta-llama-3.3-70b-instruct-121024"`.
     Therefore, 100% of Arm 1 and Arm 2 records (60 obscure, 38 famous) set:
     - `generation_model_served = "meta-llama-3.3-70b-instruct-121024"`
     - `_generation_model_used = "meta-llama-3.3-70b-instruct-121024"`
   - **In Arm 3 (`3_Full_TERRA`) and Arm 4 (`4_TERRA_Unlabeled`)**:
     The runner delegated generation to `ask_terra.terra_inference_engine()`.
     In `ask_terra.py` (lines 212–227), `CleanResponseOpenAI` hardcoded `model_used=openai_model` (recording the input argument string `"databricks-meta-llama-3-3-70b-instruct"`, rather than reading `response.model`).
     In `run_obscure_overruled_inference.py` lines 535–536, `generation_model_served` was explicitly hardcoded to `None`, and `_generation_model_used` was logged from engine timing:
     - When generation occurred: recorded `"databricks-meta-llama-3-3-70b-instruct"` (54 obscure, 31 famous).
     - When NLI refusal occurred: recorded `None` (6 obscure, 7 famous).

2. **Reconciliation**:
   - Both strings refer to requests routed to the exact same configured endpoint: `databricks-meta-llama-3-3-70b-instruct`.
   - `"meta-llama-3.3-70b-instruct-121024"` is the server-emitted response descriptor for that endpoint; `"databricks-meta-llama-3-3-70b-instruct"` is the client-side endpoint alias.
   - The apparent divergence in the JSON output is entirely an artifact of harness logging instrumentation (direct response property extraction vs. wrapper input parameter echo vs. refusal `None`).

3. **Vendor Serving Snapshot Boundary (Crucial Qualification)**:
   - Client-side logs prove that all non-refusal calls targeted the same endpoint.
   - However, client records cannot independently prove whether Databricks maintained invariant weights or modified backend checkpoints over time without Databricks vendor serving deployment records.
   - Therefore, the disclosure should report: *All calls targeted the `databricks-meta-llama-3-3-70b-instruct` endpoint, which returned server identifier `meta-llama-3.3-70b-instruct-121024` on inspected direct completions; weight invariance across deployment dates is an assumption of the managed serving platform rather than an independently audited hash.*

---

## 5. Summary and Proposed Disclosures

1. **Obscure Code Identity**: Historical code matching `430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd` is preserved at `issue18_bundle/scripts_pipeline/ask_terra.py`, functionally identical to current `ask_terra.py` aside from one 6-byte comment edit.
2. **Hub Traversal**: Disclose that `hub_degree_cap: 50` in config acts as the node degree activation threshold, which in production engaged a dual-budget traversal allowing up to 75 incoming citing cases and 25 outgoing cited precedents.
3. **Primary Linkage Gaps**: Explicitly disclose that primary Canonical v2, pilot ablation, CaseFacts, and CLERC do not record per-run code or index hashes, in contrast to the later temporal-update, temporal-probe, and obscure suites.
4. **Model Serving Identity**: Disclose the logging mechanism linking `meta-llama-3.3-70b-instruct-121024` and `databricks-meta-llama-3-3-70b-instruct`, while explicitly qualifying vendor serving invariance.

Antigravity stands ready to review subsequent read-only provenance reconciliations.
