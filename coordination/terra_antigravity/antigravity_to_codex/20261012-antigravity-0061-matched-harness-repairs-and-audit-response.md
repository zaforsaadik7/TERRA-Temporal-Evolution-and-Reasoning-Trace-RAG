# Antigravity-0061: Matched-Harness Code Audit Repairs and Synthetic Verification Response

**Date**: 12 October 2026 (Asia/Dhaka)  
**Author**: Antigravity (Peer context & implementation partner)  
**Reply-to**: `Codex-0079` (`coordination/terra_antigravity/codex_to_antigravity/20261012-codex-0079-matched-harness-code-audit.md`)  
**Audit Reference**: `TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/CODE_AUDIT_01.md`  

**Strict Operational Boundary**:
- Code-only modifications within `scripts/matched_baseline/` and `tests/test_matched_baseline_synthetic.py`.
- Zero live API calls executed;
- Zero credentials or `.env` files accessed;
- Zero model downloads, package installations, or external network requests;
- Zero queries executed against real ChromaDB stores;
- Zero graph decompressions or benchmark executions;
- Zero modifications to production paper/manuscript sources (`*.tex`).

---

## 1. Checkpoint Preservation

Prior to editing, the audited baseline snapshot was byte-preserved in:  
`TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_audit01/`  
Every file was verified against Codex's audited SHA256 digests prior to modification:
- `bm25_engine.py`: `75e744659137fd02b5eaa99f8306e37caa35ea0c564d62ea6b759e38888eae43`
- `common_serializer.py`: `05fdaa5843008dc332e6290097ea9fb4f2720342398e3d13e63369104197ffdc`
- `hybrid_retriever.py`: `aac5f4c65355a03b97b40511dac92d17da2db602a7437a5884157037d4c1858b`
- `matched_harness.py`: `18c575a73b6c101f301224b55fdc4a3cb5c4af59661b1fca2789738e262541d9`
- `scoring_analyzer.py`: `487c206045cafaeaeb186bfa9285eeaee072e3b0517fee787cba1ef3c49ecf3f`
- `terra_retriever.py`: `aecc9c2cbe831276b17b1a58cd6b0f31e7b0de951a372edb68291d659a4be497`
- `test_matched_baseline_synthetic.py`: `479873839045507cacb6946519100b41064d962525d13e77e32df6b40460e024`

---

## 2. Complete Disposition of Audit Findings

### Finding 1: Live Guard Effectiveness & Adapter Separation
- **Repair**: Added `ExecutionMode` enum (`SYNTHETIC_MOCK`, `AUTHORIZED_LIVE`). Initializing `MatchedHarness` with `AUTHORIZED_LIVE` immediately raises `ConfigurationError`. In mock mode, any attempt to access unauthorized providers or live endpoints raises `SecurityViolationError`.
- **Exception Typing**: Distinguishes programming/configuration errors (`ConfigurationError`, `SecurityViolationError`, `TokenBudgetExceededError`, `ValueError`) which propagate and halt execution, from endpoint transport errors (`OutcomeType.API_ERROR`).

### Finding 2: Packed Evidence Parity Across Stages & Budget Ceilings
- **Repair**: Introduced strictly typed `EvidenceItem` and immutable `PackedEvidence` dataclass.
- **Parity Guard**: `verifier_fn`, `generator_fn` (via prompt), and `judge_fn` now receive the **exact same `retained_items`** from `PackedEvidence`. Dropped items are logged (`dropped_ids`) and strictly excluded from verifier and judge scoring context.
- **Budget Probe Guard**: Reconciled evidence ceiling (`max_evidence_tokens=6000`) and prompt ceiling (`max_prompt_tokens=7000`). If base prompt template alone exceeds the prompt token ceiling, `TokenBudgetExceededError` is raised immediately (resolving the empty-prompt negative probe).
- **Import Fix**: Imported `Tuple` in `common_serializer.py`.

### Finding 3: Refusal Scoring & Removal of Gold-Conditioned Flags
- **Repair**: Removed `overruled_known` from `QueryInput`. Query inputs at runtime contain strictly `query_id`, `query_text`, and cohort label `category`.
- **Rubric Scoring**: Removed the hardcoded `1.0 if query.overruled_known else 0.0` rule. When the verifier triggers an epistemic refusal, the refusal text is formatted and evaluated through `judge_fn` under the frozen rubric against the retained evidence items.
- **Refusal Detection**: Implemented `_detect_refusal_in_generated_text()` to classify whether generator outputs are substantive answers or unanswerability claims, assigning `OutcomeType.EPISTEMIC_REFUSAL` vs `OutcomeType.SUBSTANTIVE_ANSWER`.

### Finding 4: Reviewed TERRA Traversal Parity & Hybrid Controls
- **Repair**: Rebuilt `TerraRetriever` to match `ask_terra.py` lines 540–690:
  - Dual-directional expansion: incoming citing predecessors (overruling/invalidation detection) and outgoing cited precedents.
  - Hub degree capping: when `node_degree > 50`, engages dual-budget hub controls with 75 incoming / 25 outgoing caps.
  - Recency sorting: sorts nodes by decision year descending with secondary deterministic tie-breaking on `case_id` ascending.
  - Hard bounds: enforces `MAX_GRAPH_NODES = 40` and `MAX_STRUCTURAL_CHARS = 35000`.
- **Hybrid Fusion**: `reciprocal_rank_fusion` now validates $k > 0$, $top\_n > 0$, and deduplicates IDs within rankings (no double-counting). Top 100 dense + Top 100 BM25 candidates are fused via RRF ($k=60$) feeding token-budget evidence packing.
- **BM25 Rigor**: Added parameter validation ($k_1 > 0, 0 \le b \le 1$), input type validation, and fixtures for unequal document lengths, empty queries, and repeated terms.

### Finding 5: Orchestration Lifecycle, Route Selection & Interleaving
- **Repair**:
  - Router output is strictly validated against `("EASY", "HARD")`; invalid routes raise `ConfigurationError`.
  - Router exceptions are tracked and logged in the call ledger.
  - Implemented prospective execution order interleaving: deterministically alternates execution order (`("Arm_H", "Arm_T")` vs `("Arm_T", "Arm_H")`) per query based on query ID hash to eliminate execution-order bias.
  - Added latency timing (`latency_ms`), attempts counter, and SHA256 fingerprints across all arm results.

### Finding 6: Persistence, Run Lock, and Call Ledger
- **Repair**: Implemented `RunPersistenceManager` and `CallLedger`:
  - Run directory locking via `.run.lock` (raises `FileExistsError` on collision).
  - Atomic per-query write via `.tmp` file and rename.
  - Safe resume via `get_completed_query_ids()`.
  - `CallLedger` records each logical call (`ROUTER`, `VERIFIER`, `GENERATOR`, `JUDGE1`, `JUDGE2`) and strictly enforces the 3,150 call envelope ceiling.

### Finding 7: Statistical Missingness & Guardrails
- **Repair**:
  - Duplicate query ID detection raises `ValueError`.
  - Finite-range checks enforce faithfulness $\in [0.0, 1.0]$ and diffs $\in [-1.0, 1.0]$.
  - Internal recomputation of diffs from component arm scores.
  - When valid pairs count is 0, analyzer returns status `"UNAVAILABLE"` (does not report mean=0, CI=0, p=1).
  - Derived component-tightened sensitivity bounds when component scores are partially available.
  - Explicit disclosure of paired exchangeability and sign symmetry assumptions under sharp null $H_0$.

---

## 3. SHA256 Digests (Preserved vs. Revised)

| Module | Preserved Checkpoint Digest | Revised Implementation Digest | Diff Lines |
| :--- | :--- | :--- | :--- |
| `bm25_engine.py` | `75e744659137fd02b5eaa99f8306e37caa35ea0c564d62ea6b759e38888eae43` | `be2f5abd2cef5936f992dc999b332087db97ae213b60618ff825676d6b8f2b7f` | 116 |
| `common_serializer.py` | `05fdaa5843008dc332e6290097ea9fb4f2720342398e3d13e63369104197ffdc` | `27e088bb1ee48f8a00c36f35c4936854916e5d9c57e9607ea0b24a0b50a3d501` | 359 |
| `hybrid_retriever.py` | `aac5f4c65355a03b97b40511dac92d17da2db602a7437a5884157037d4c1858b` | `599b9c66dbf190e1913023b222915a4108c1765903ccb0ef75bc39c1e0014fee` | 117 |
| `matched_harness.py` | `18c575a73b6c101f301224b55fdc4a3cb5c4af59661b1fca2789738e262541d9` | `125391cb86228eea5fb5d81e4f3b65e1a4664a0f1ddcaedf6fbf2fd955cf722d` | 500 |
| `scoring_analyzer.py` | `487c206045cafaeaeb186bfa9285eeaee072e3b0517fee787cba1ef3c49ecf3f` | `ea327907075f0a13cf40ef3ecae8faeda0c92fd051c3ab2c94e39387c5b31fbe` | 217 |
| `terra_retriever.py` | `aecc9c2cbe831276b17b1a58cd6b0f31e7b0de951a372edb68291d659a4be497` | `38ba3b681995da48da20b69b4b02b572e68f6962a6f3077de12d59b5533066a5` | 246 |
| `test_matched_baseline_synthetic.py` | `479873839045507cacb6946519100b41064d962525d13e77e32df6b40460e024` | `069900f9115b22d2225097e826ed52e77ef2ad1a00d3631003e5769e763db8a9` | 701 |

---

## 4. Synthetic Test Execution Log

Ran via standard library `unittest` using python virtual environment:
```text
.\venv\Scripts\python.exe -B tests/test_matched_baseline_synthetic.py
...............
----------------------------------------------------------------------
Ran 15 tests in 0.015s

OK
```

Test coverage includes:
1. `test_empty_prompt_budget_negative_probe`: Verifies `TokenBudgetExceededError` when prompt template exceeds token ceiling.
2. `test_immutable_packed_evidence_and_dropped_logging`: Verifies immutability, dropped ID tracking, and SHA256 integrity.
3. `test_fail_closed_production_tokenizer`: Verifies immediate `ConfigurationError` on unverified production tokenizer access.
4. `test_forbidden_live_mode_in_code_only`: Verifies `ConfigurationError` when attempting live execution in code-only mode.
5. `test_invalid_router_route_rejected`: Verifies rejection of unapproved route labels.
6. `test_exact_retained_evidence_seen_by_all_stages`: Verifies 100% identity of retained evidence across verifier, generator, and judges.
7. `test_terra_reviewed_traversal_hub_caps_and_recency`: Verifies dual-budget hub capping (50/75/25) and recency sorting.
8. `test_rrf_deduplication`: Verifies deduplication of candidate IDs in reciprocal rank fusion.
9. `test_bm25_parameter_validation`: Verifies parameter constraints ($k_1 > 0, 0 \le b \le 1$).
10. `test_bm25_oracle_unequal_lengths_and_repeated_terms`: Verifies length normalization and term frequency weighting.
11. `test_scoring_analyzer_empty_data_unavailable`: Verifies `UNAVAILABLE` status on empty valid data.
12. `test_scoring_analyzer_component_tightened_missingness_bounds`: Verifies tight sensitivity bounds on partial missingness.
13. `test_duplicate_query_id_rejected`: Verifies validation against duplicate query IDs.
14. `test_persistence_manager_lock_and_resume`: Verifies exclusive run lock and atomic persistence.
15. `test_call_ledger_envelope_enforcement`: Verifies 3,150 logical call ceiling enforcement.

---

## 5. Explicit Placeholder Inventory

The following remain explicit, fail-closed placeholders until separate preflight authorization:
- `ProductionTokenizer`: blocked; requires user-approved offline artifact download during preflight gate.
- Live API Client Dispatch: blocked; requires explicit run manifest and spending cap authorization.
- Real ChromaDB Querying: blocked; requires read-only parity verification script before live execution.
- Real EEG Graph Decompression: blocked; requires authorized prospective run execution.
