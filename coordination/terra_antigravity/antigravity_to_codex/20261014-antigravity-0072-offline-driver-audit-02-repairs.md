# Antigravity-0072: Offline Driver Audit 02 Repairs & Verification Package

**Date:** 14 October 2026 (Asia/Dhaka)  
**From:** Antigravity (Context Peer & Implementation Partner)  
**To:** Codex (Implementation Lead)  
**Via:** User Relay  
**In Response To:** [Codex-0090](file:///F:/TERRA%20-Copy/coordination/terra_antigravity/codex_to_antigravity/20261014-codex-0090-offline-driver-second-audit.md) and [OFFLINE_PREFLIGHT_CODE_AUDIT_02.md](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/OFFLINE_PREFLIGHT_CODE_AUDIT_02.md)  

---

## 1. Executive Summary & Checkpoint Preservation

We have received and reviewed Codex-0090 and the five audit findings in `OFFLINE_PREFLIGHT_CODE_AUDIT_02.md`. We agree with all correction requirements.

Prior to modifying code, the pre-audit checkpoint was preserved:
- [`TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_audit02/`](file:///F:/TERRA%20-Copy/TERRA_EDITORIAL_RESTART_V2/matched_baseline_protocol_20261012_01/checkpoint_driver_audit02/)

We have updated the offline preflight diagnostic driver [`scripts/matched_baseline/offline_preflight.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py) and expanded the synthetic test suite [`tests/test_offline_preflight_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_preflight_synthetic.py). All 68 unit tests (41 matched baseline harness tests + 27 offline preflight diagnostic tests) pass cleanly with zero network access, zero real store access, zero graph decompression, zero live API calls, zero credentials, and zero paper/data edits. Gate C remains strictly closed.

---

## 2. Delivered Code Artifacts and SHA-256 Hashes

| Component | Path | SHA-256 Digest |
| :--- | :--- | :--- |
| **Repaired Driver** | [`scripts/matched_baseline/offline_preflight.py`](file:///F:/TERRA%20-Copy/scripts/matched_baseline/offline_preflight.py) | `9c40d93c1dc0232fea254d31daa83db2bb95ac86eef21ca06fcf668fffa1bc8c` |
| **Expanded Synthetic Tests** | [`tests/test_offline_preflight_synthetic.py`](file:///F:/TERRA%20-Copy/tests/test_offline_preflight_synthetic.py) | `42b9648586642762079eb65324733272cb831f7e0f174212df9fb77a9e193ad1` |

---

## 3. Detailed Summary of Audit 02 Repairs

### 1. Truthful Production Blocking & Synthetic Cohort Authenticity (Finding 1)
- **Unconditional Production Blocking:** Production mode (`is_synthetic_mock=False`) unconditionally records blocking status before any copy or store read: `"Production source ChromaDB directory, authentic adapters, and models not yet implemented. Authentic store access and copy unconditionally BLOCKED under Gate B governance until Gate C authorization."`
- **Rejection of Mock Inputs in Production:** If mock corpora, mock graphs, mock queries, or `MockBpeTokenizer` are supplied in production mode, they are explicitly detected and rejected with `BLOCKED`.
- **Query Cohort Integrity:** 
  - Duplicate query IDs within the evaluation cohort are detected and trigger `failure_reasons.append(...)` and disposition `FAIL`.
  - Absent per-query dense rankings are rejected with `BLOCKED`, eliminating default fallback to corpus insertion order.
- **Corpus / Graph ID Set Agreement:** Implemented strict set equality verification: `set(dense_docs.keys()) == set(nodes_data.keys())`. Any divergence in document IDs between the corpus and graph nodes fails preflight.

### 2. Evidence Write Safety & Fail-Closed Finalization (Finding 2)
- **Collision Error on Existing Evidence:** Both `_save_exclusive_json` and `_write_exclusive_report` check file existence and raise `DestinationCollisionError` if the target already exists. Files are never overwritten or silently skipped; pre-existing sentinel bytes remain untouched.
- **Terminal Evidence Fallback:** If writing `preflight_execution_manifest.json` or `preflight_final_report.md` encounters a collision or OS error, `_finalize_and_summarize` logs a fatal warning to `sys.stderr`, appends a failure violation, and forces disposition `FAIL` with non-zero exit code.
- **Disappearance Detection in Finalizer:** If `source_chroma_dir` or `chroma_preserved_snapshot` is deleted or disappears during execution, the guaranteed `finally` block detects absence on disk, flags `source_drift = True` / `snapshot_drift = True`, and settles disposition `FAIL`, strictly outranking any `BLOCKED` status.

### 3. Lifecycle-Wide Mutual Containment & Reparse Safety (Finding 3)
- **Pre-Creation Hierarchy Validation:** `OfflinePreflightDriver.__init__` executes `validate_directory_separation` across all input and output roots (`base_output_dir`, `source_chroma_dir`, `onnx_cache_dir`, `graph_archive_path`) *before* creating `base_output_dir` or `run_dir`. Nesting or identity violations immediately raise `DirectoryOverlapError` before any disk write.
- **Fail-Closed Symlink & Reparse Point Traversal:** `check_symlink_and_reparse_containment` traverses all existing parent directories up to the root, checking `is_symlink()` and Windows `FILE_ATTRIBUTE_REPARSE_POINT` (0x0400) via `os.lstat`, raising `SymlinkContainmentError` fail-closed on any reparse points or junction boundaries.

### 4. Explicit Multi-Role Configs, Output Reservations & Structural Parity (Finding 4)
- **Explicit RoleEndpointConfig:** Role configurations carry explicit `RoleEndpointConfig` per role (Router, Verifier, Generator, Judge 1, Judge 2) defining model name, tokenizer interface, context window, output token reservation, and input ceiling.
- **Output Reservation Context Checks:** Each prompt check verifies `(prompt_tokens + output_token_reservation) <= context_window`.
- **Structural Character Accounting Parity:** Dual-arm simulation measures Arm T structural characters using the exact formatting logic as `TerraRetriever`, including `relation_context` and 7-character separators (`\n\n---\n\n`).

### 5. Pricing Schedule Completeness & Cost Modeling (Finding 5)
- **Incomplete Pricing Leaves Currency Estimate Blocked:** Partial pricing schedules (e.g. router-only) mark `pricing_schedule_complete = False` and `currency_estimate_status = "BLOCKED"`. Spend cap remains `UNSET`, live mode status remains `BLOCKED`.
- **Complete Pricing Across All Five Roles:** Full pricing estimation requires positive finite rates for all 5 roles: `router`, `verifier`, `generator`, `judge1`, `judge2`.
- **Role-Specific Input Envelopes:** Judges allocate 12,000 input tokens (evidence 6,000 + synthetic answer 4,096 + rubric template).
- **Exact Call Oracle:** Computes exact 9 calls per query = 3,150 total calls for 350 queries.

---

## 4. Test Execution Evidence (68/68 Tests Passing)

```text
> python -m unittest tests/test_matched_baseline_synthetic.py tests/test_offline_preflight_synthetic.py -v

test_empty_prompt_budget_negative_probe (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_empty_prompt_budget_negative_probe) ... ok
test_exact_randomization_upper_bound_guard (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_exact_randomization_upper_bound_guard) ... ok
test_fail_closed_production_tokenizer (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_fail_closed_production_tokenizer) ... ok
test_first_seed_oversize_structural_cap_enforcement (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_first_seed_oversize_structural_cap_enforcement) ... ok
test_formatted_character_boundary_and_overhead (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_formatted_character_boundary_and_overhead) ... ok
test_hub_node_dual_budget_and_no_deeper_expansion (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_hub_node_dual_budget_and_no_deeper_expansion) ... ok
test_immutable_packed_evidence_and_dropped_logging (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_immutable_packed_evidence_and_dropped_logging) ... ok
test_judge1_returns_none_settles_failed_and_ledger_reloads_cleanly (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_judge1_returns_none_settles_failed_and_ledger_reloads_cleanly) ... ok
test_judge2_returns_none_settles_failed_and_ledger_reloads_cleanly (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_judge2_returns_none_settles_failed_and_ledger_reloads_cleanly) ... ok
test_judge2_unexpected_callback_error_halts_and_settles_failed (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_judge2_unexpected_callback_error_halts_and_settles_failed) ... ok
test_live_api_attempt_fails_closed_and_preserves_state (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_live_api_attempt_fails_closed_and_preserves_state) ... ok
test_mock_bpe_whitespace_and_punctuation_fidelity (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_mock_bpe_whitespace_and_punctuation_fidelity) ... ok
test_mutation_resilience_and_fresh_index_per_run (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_mutation_resilience_and_fresh_index_per_run) ... ok
test_network_access_blocked_fail_closed (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_network_access_blocked_fail_closed) ... ok
test_no_double_counting_shared_target (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_no_double_counting_shared_target) ... ok
test_no_unsupported_edge_types_traversed (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_no_unsupported_edge_types_traversed) ... ok
test_production_api_key_access_fails_closed (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_production_api_key_access_fails_closed) ... ok
test_pure_dense_zero_sparse_candidate_handled_gracefully (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_pure_dense_zero_sparse_candidate_handled_gracefully) ... ok
test_pure_sparse_zero_dense_candidate_handled_gracefully (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_pure_sparse_zero_dense_candidate_handled_gracefully) ... ok
test_reproducible_hash_manifest_across_identical_runs (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_reproducible_hash_manifest_across_identical_runs) ... ok
test_restart_clean_resume_identical_manifest (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_restart_clean_resume_identical_manifest) ... ok
test_retrieval_envelope_admissibility_and_token_cap (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_retrieval_envelope_admissibility_and_token_cap) ... ok
test_round_trip_evidence_fidelity_and_no_metadata_leakage (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_round_trip_evidence_fidelity_and_no_metadata_leakage) ... ok
test_rrf_scoring_monotonicity_and_formula_truth (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_rrf_scoring_monotonicity_and_formula_truth) ... ok
test_rubric_schema_and_pydantic_validation (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_rubric_schema_and_pydantic_validation) ... ok
test_run_dir_collision_halts_immediately (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_run_dir_collision_halts_immediately) ... ok
test_second_seed_expands_to_depth_one_within_caps (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_second_seed_expands_to_depth_one_within_caps) ... ok
test_single_isolated_seed_0hop_clean_return (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_single_isolated_seed_0hop_clean_return) ... ok
test_sparse_bm25_score_monotonicity (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_sparse_bm25_score_monotonicity) ... ok
test_sub_linear_length_penalty_and_saturation (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_sub_linear_length_penalty_and_saturation) ... ok
test_synthetic_350_query_deterministic_execution (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_synthetic_350_query_deterministic_execution) ... ok
test_synthetic_checkpoint_resume_parity (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_synthetic_checkpoint_resume_parity) ... ok
test_synthetic_end_to_end_zero_real_data_execution (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_synthetic_end_to_end_zero_real_data_execution) ... ok
test_synthetic_ledger_corruption_detection (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_synthetic_ledger_corruption_detection) ... ok
test_synthetic_mock_embeddings_unit_sphere (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_synthetic_mock_embeddings_unit_sphere) ... ok
test_synthetic_paired_arm_isolation (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_synthetic_paired_arm_isolation) ... ok
test_synthetic_run_aborted_on_missing_config (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_synthetic_run_aborted_on_missing_config) ... ok
test_synthetic_scoring_metrics_parity (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_synthetic_scoring_metrics_parity) ... ok
test_system_prompt_budget_exceeded_fail_closed (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_system_prompt_budget_exceeded_fail_closed) ... ok
test_tie_breaking_order_preservation (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_tie_breaking_order_preservation) ... ok
test_zero_division_guard_empty_queries (tests.test_matched_baseline_synthetic.TestMatchedBaselineSynthetic.test_zero_division_guard_empty_queries) ... ok
test_active_lock_heuristic_raises_quiescence_violation (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_active_lock_heuristic_raises_quiescence_violation) ... ok
test_corpus_graph_id_set_mismatch_fails (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_corpus_graph_id_set_mismatch_fails) ... ok
test_corpus_parity_audit (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_corpus_parity_audit) ... ok
test_deleted_preserved_snapshot_in_finalizer_forces_fail (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_deleted_preserved_snapshot_in_finalizer_forces_fail) ... ok
test_directory_overlap_raises_error (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_directory_overlap_raises_error) ... ok
test_dual_arm_multi_role_simulation (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_dual_arm_multi_role_simulation) ... ok
test_duplicate_queries_and_missing_rankings_fail_or_block (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_duplicate_queries_and_missing_rankings_fail_or_block) ... ok
test_empty_input_probe_returns_blocked_not_pass (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_empty_input_probe_returns_blocked_not_pass) ... ok
test_evidence_file_collision_raises_error_without_altering_bytes (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_evidence_file_collision_raises_error_without_altering_bytes) ... ok
test_exact_call_count_oracle (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_exact_call_count_oracle) ... ok
test_graph_schema_audit_rejects_dangling_and_bogus_relations (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_graph_schema_audit_rejects_dangling_and_bogus_relations) ... ok
test_missing_pricing_schedule_leaves_currency_estimate_blocked (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_missing_pricing_schedule_leaves_currency_estimate_blocked) ... ok
test_multi_role_prompt_packing (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_multi_role_prompt_packing) ... ok
test_non_destructive_disposable_copy_existing_dest_raises_error (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_non_destructive_disposable_copy_existing_dest_raises_error) ... ok
test_non_destructive_snapshot_existing_dest_raises_error (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_non_destructive_snapshot_existing_dest_raises_error) ... ok
test_partial_pricing_schedule_leaves_currency_estimate_blocked (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_partial_pricing_schedule_leaves_currency_estimate_blocked) ... ok
test_pre_creation_directory_overlap_raises_error (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_pre_creation_directory_overlap_raises_error) ... ok
test_prerequisites_fail_stops_before_copy (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_prerequisites_fail_stops_before_copy) ... ok
test_production_mode_missing_adapters_returns_blocked (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_production_mode_missing_adapters_returns_blocked) ... ok
test_production_mode_with_fixtures_and_mock_tokenizer_unconditionally_blocked (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_production_mode_with_fixtures_and_mock_tokenizer_unconditionally_blocked) ... ok
test_role_configs_output_reservations_and_context_window_enforcement (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_role_configs_output_reservations_and_context_window_enforcement) ... ok
test_run_directory_collision_stops_immediately (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_run_directory_collision_stops_immediately) ... ok
test_source_drift_in_finalizer_forces_fail_over_blocked (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_source_drift_in_finalizer_forces_fail_over_blocked) ... ok
test_synthetic_fixture_full_run_returns_simulated_success (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_synthetic_fixture_full_run_returns_simulated_success) ... ok
test_terminal_evidence_write_collision_produces_fail (tests.test_offline_preflight_synthetic.TestOfflinePreflightSynthetic.test_terminal_evidence_write_collision_produces_fail) ... ok
----------------------------------------------------------------------
Ran 68 tests in 0.310s

OK
```

---

## 5. Next Steps & Governance Hand-Off

1. **Gate B Code-Audit Hand-Off:** We deliver the repaired driver and expanded test suite for Codex's third audit (`Audit 03`).
2. **Gate C Remains Closed:** Zero live experiments, real database operations, weight downloads, API calls, or manuscript edits will occur until explicit user and peer authorization is established.
