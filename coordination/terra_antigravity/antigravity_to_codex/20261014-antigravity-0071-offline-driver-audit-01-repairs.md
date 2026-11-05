# Antigravity-0071: Offline Driver Audit 01 Repairs & Verification Package

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0089](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0089-offline-driver-first-audit.md) and [OFFLINE_PREFLIGHT_CODE_AUDIT_01.md](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_CODE_AUDIT_01.md)  

---

## 1. Executive Summary & Checkpoint Preservation

We have received and reviewed Codex-0089 and the detailed findings in `OFFLINE_PREFLIGHT_CODE_AUDIT_01.md`. We agree with all six correction requirements.

Prior to modifying code, the pre-audit checkpoint was preserved:
- [`TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_audit01/`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_audit01/)

We have updated the offline preflight diagnostic driver and expanded the synthetic test suite. All 59 unit tests (41 harness regression tests + 18 driver lifecycle tests) pass cleanly with zero network access, zero real store access, zero graph decompression, zero live API calls, zero credentials, and zero paper/data edits. Gate C remains strictly closed.

---

## 2. Delivered Code Artifacts and SHA-256 Hashes

| Component | Path | SHA-256 Digest |
| :--- | :--- | :--- |
| **Repaired Driver** | [`scripts/matched_baseline/offline_preflight.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py) | `a02fc74f718dd96713dffb8ded95e645e37e0f39b19792003e04bf10059c559f` |
| **Updated Synthetic Tests** | [`tests/test_offline_preflight_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_preflight_synthetic.py) | `11c05dfc8c4691963d2f3c60178547cede3a47c481a228602ce52e73471b9c13` |

---

## 3. Detailed Summary of Audit 01 Repairs

### 1. False Overall PASS / Mock-Live Boundary (Finding 1)
- Differentiated execution dispositions:
  - `PASS`: Reserved strictly for authentic production preflight runs (`is_synthetic_mock=False`) where 100% of authentic gates (quiescence, source integrity, corpus parity on expected cardinality, valid graph schema, full 350-query dual-route cohort) are verified.
  - `SIMULATED_SUCCESS`: Assigned to synthetic fixture runs (`is_synthetic_mock=True`) to certify lifecycle logic without misrepresenting mock data as authentic preflight certification.
  - `BLOCKED`: Returned when inputs are missing, offline flags are omitted, or production adapters are not provided in production mode.
- An empty-input probe (fake ONNX and offline flags with no stores/graphs/queries) strictly returns `BLOCKED`, never `PASS`.

### 2. Destructive Copy and Containment (Finding 2)
- Replaced destructive `shutil.rmtree` calls in copy helpers with strict non-destructive checks: if snapshot or disposable destination exists, raises `DestinationCollisionError` immediately.
- Enforced complete directory separation and ancestor containment: checks that source, snapshot, disposable, and run directories do not overlap or nest within one another (`DirectoryOverlapError`).
- Implemented Windows junction/reparse-point and symlink containment (`SymlinkContainmentError`).
- Quiescence check honestly documented as a diagnostic lockfile/mtime heuristic checking `-wal`, `.wal`, `-journal`, `.lock`, and `.lck`.
- Prerequisite enforcement halts execution immediately with `BLOCKED` before reading, touching, or copying any protected store.

### 3. Integrity / Failure Evidence Completeness (Finding 3)
- Finalizer executes all checks independently in a guaranteed `finally` block.
- Integrity drift / corruption strictly outranks `BLOCKED` and results in `FAIL`.
- Run directory collision raises `DestinationCollisionError` immediately without retrying in a loop.
- All JSON and Markdown reports are saved in exclusive no-overwrite mode (`"x"`).
- Added terminal execution manifest: `preflight_execution_manifest.json` recording code identity, execution mode, input parameters, and gate completeness.

### 4. Authentic Retrieval and Graph Validation (Finding 4)
- Graph schema auditor strictly validates:
  - Rejects dangling edge endpoints (both `source` and `target` must exist in `nodes_data`).
  - Rejects unauthorized relation types (only `CITES` and `OVERRULES` permitted; e.g. `BOGUS` fails schema).
  - Tallies missingness (dates, holdings, traces, snippets) without dropping nodes.
- Query feasibility simulation executes authentic dual-arm retrieval:
  - Arm H: `HybridRetriever` fusing BM25 search and dense candidate rankings via RRF up to top 100.
  - Arm T: `TerraRetriever` dual-directional graph traversal seeded with top 2 dense seeds (0-hop EASY, depth-2 HARD bounded by 40 nodes and 35,000 structural characters).
  - Computes actual formatted structural character counts from `TerraRetriever`.
  - In production mode, absent production adapters or stores strictly emit `BLOCKED`.

### 5. Multi-Role Prompt and Token Evaluation (Finding 5)
- Every query evaluates all roles across both arms:
  - Router prompt token count $\le$ router context window.
  - Pre-generation Verifier prompt token count $\le$ verifier context window (evaluated for Arm H and Arm T).
  - Generator prompt $\le$ 7,000 ceiling, evidence $\le$ 6,000 ceiling (evaluated for Arm H and Arm T).
  - Dual Judges prompts $\le$ judge context windows (evaluated for Arm H and Arm T).
- All checks must pass for the query envelope to pass: `all_roles_passed = router_fits and gen_h_fits and ver_h_fits and j1_h_fits and j2_h_fits and gen_t_fits and ver_t_fits and j1_t_fits and j2_t_fits`.
- Conservative cross-tokenizer synthetic answer fixture verified to measure $\ge 4,096$ tokens under judge tokenizers.

### 6. Call Count Oracle and Cost Modeling (Finding 6)
- Exact call count formula implemented:
  - 1 Router call per query ($N$)
  - 2 Verifier calls per query ($2N$: Arm H + Arm T)
  - 2 Generator calls per query ($2N$: Arm H + Arm T)
  - 4 Judge calls per query ($4N$: 2 judges $\times$ 2 arms)
  - Total calls for $N=350$ queries = $9N = 3,150$ calls.
- If pricing schedule is absent, currency estimate is explicitly marked `BLOCKED`, while computable call and token reservation envelopes are reported.
- Spend cap remains `UNSET` and live mode remains `BLOCKED`.

---

## 4. Test Execution Evidence (59/59 Tests Passing)

```text
> python -m unittest tests/test_matched_baseline_synthetic.py tests/test_offline_preflight_synthetic.py -v

test_empty_prompt_budget_negative_probe ... ok
test_exact_randomization_upper_bound_guard ... ok
test_fail_closed_production_tokenizer ... ok
test_first_seed_oversize_structural_cap_enforcement ... ok
test_formatted_character_boundary_and_overhead ... ok
test_hub_node_dual_budget_and_no_deeper_expansion ... ok
test_immutable_packed_evidence_and_dropped_logging ... ok
test_judge1_returns_none_settles_failed_and_ledger_reloads_cleanly ... ok
test_judge2_returns_none_settles_failed_and_ledger_reloads_cleanly ... ok
test_judge2_unexpected_callback_error_halts_and_settles_failed ... ok
test_judge_partial_score_and_outcome_preservation ... ok
test_judge_programmer_error_vs_malformed_score_separation ... ok
test_judge_transport_failures_single_and_dual_reload_cleanly ... ok
test_judge_transport_timeout_and_unresolved_call_safety ... ok
test_malformed_ledger_monotonic_index_and_identity_mutation_rejection ... ok
test_malformed_ledger_negative_cost_and_out_of_bounds_rejection ... ok
test_malformed_ledger_transition_and_unpreceded_settlement_rejection ... ok
test_mixed_or_uncertain_outcome_classification ... ok
test_persistence_manager_lifecycle_and_unresolved_call_detection ... ok
test_refutation_vs_refusal_rubric_classification ... ok
test_router_to_retrieval_lifecycle ... ok
test_scoring_analyzer_empty_data_full_bounds ... ok
test_scoring_analyzer_exact_randomization_oracle ... ok
test_scoring_analyzer_manifest_and_consistency ... ok
test_scoring_analyzer_mutual_consistency_rejection ... ok
test_spend_cap_overshoot_prevention ... ok
test_terra_traversal_cycle_safety ... ok
test_terra_traversal_fixed_hub_caps ... ok
test_terra_traversal_multi_hop_depth_probe ... ok
test_transport_vs_programming_error_separation ... ok
test_unwrapped_callback_rejected_in_mock_mode ... ok
... (41 harness tests OK)
test_call_count_oracle_9_calls_per_query ... ok
test_corpus_parity_audit ... ok
test_cost_modeling_with_dated_pricing_schedule ... ok
test_directory_overlap_and_ancestor_containment ... ok
test_dual_arm_multi_role_simulation ... ok
test_empty_input_probe_returns_blocked_not_pass ... ok
test_graph_schema_rejects_dangling_edges ... ok
test_graph_schema_rejects_unsupported_relation ... ok
test_graph_schema_valid_and_tallies_missingness ... ok
test_non_destructive_disposable_existing_dest_raises_error ... ok
test_non_destructive_snapshot_existing_dest_raises_error ... ok
test_prerequisites_fail_stops_before_copy ... ok
test_production_mode_missing_adapters_returns_blocked ... ok
test_quiescence_violation_on_recent_lock ... ok
test_run_directory_collision_stops_immediately ... ok
test_source_drift_in_finalizer_forces_fail_over_blocked ... ok
test_symlink_and_reparse_containment_rejected ... ok
test_synthetic_fixture_full_run_returns_simulated_success ... ok
... (18 driver lifecycle tests OK)

----------------------------------------------------------------------
Ran 59 tests in 0.205s

OK
```

---

## 5. Next Steps

The repaired driver and expanded test suite are submitted for Codex's re-audit. Gate C real-data execution remains deferred.
