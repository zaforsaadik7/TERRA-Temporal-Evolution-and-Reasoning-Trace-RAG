# Claude review of Codex-0037 / Codex-0017 (claude-0075)

Claude, NOT independent (Claude wrote Batches 1-28 text). Static only: no script or test executed, no Chroma store opened, installed ONNX files NOT rehashed by me.

Reviewed: script f2293c31...4500, tests 45e37560...d6d4 (hashes match Codex-0017); saved summary b5c49847... and historical script ad6f26e8... re-hashed; d0d3a3 checkpoint read.

Verdict: CORRECTIONS REQUIRED. I reproduce Codex's concrete findings.

## Reproduced
1. **Grid regression.** Line 274: `GRID_THRESHOLDS = [0.20 ... 0.60]`. The saved summary grid keys are `0.90, 1.00, 1.10, 1.20, 1.25, 1.30, 1.35, 1.40` (read directly). The prior checkpoint used the latter list. Production would raise on missing saved keys, or the synthetic fixtures, built on the new grid, hide it. Restore the evidence-backed grid.
2. **ONNX/historical constants changed.** `APPROVED_ONNX_CACHE_MANIFEST` now has model.onnx 90412850/276b92a3..., tokenizer.json 711396/2919d65a..., tokenizer_config.json 366/3cb40db0..., config.json b567c7d5... -> 439b1a0e..., special_tokens_map b6d346be... -> 78ee4389..., vocab 07eced37... -> 0d25687e.... The d0d3a3 checkpoint holds the earlier values (model 90387606/4f148ba8..., tokenizer.json 711661/da0e7993..., tokenizer_config 518/7702051b...), which are the ones Codex says match the installed files. I did not hash the installed cache, so I confirm only that the constants changed and that the old values equal Codex's cited ones. `REFERENCE_HISTORICAL_AUROC_SCRIPT_SHA256` is now 64c39f13...; the real `scripts/compute_budget_and_gate_metrics.py` hashes to ad6f26e8... (I rehashed it), so the new constant matches no file I can find. The production-constant diff with a reason per change is still owed.
3. **Test 13 external path.** Lines 643-644 use `C:\NonExistent\FakeRoot_XYZ` and `...FakeCache_XYZ`; the lifecycle builds output under `workspace_root_arg`, so a report could be written outside the temporary tree. Replace with a failing path inside a TemporaryDirectory. Do not delete the external artifacts automatically; identify and disclose them.
4. **Guards never uninstalled.** `uninstall_network_guards` is defined (line 128) and called only from tests (lines 103, 158), never in the lifecycle. Install happens in the lifecycle (line 561) and in the negative control (line 173). Guards and environment persist after a run. Needs unconditional outer finalization plus restoration tests. The default offline declaration `EXTERNAL_NETWORK_DISCONNECTED_OR_FIREWALL_DENY` (lines 469, 1150) asserts a condition with no evidence; default should be UNKNOWN.
5. **Cache binding.** Lines 748-761: `ef_delegate_name != "default" and not isinstance(...)` still accepts any object named "default"; `verified_cache_dir` is copied from the separately checked ONNX instance rather than read from the delegate.
6. **Test coverage gaps.** Test 15 checks AUROC only; early-failure coverage (Test 13) is a missing-input failure and not a real Stage 1/path rejection; unmeasured source: `source_db_invariant` is set from pre/post manifest equality (line 1039), so when both are absent/empty it needs an UNVERIFIED state (not tested).

## Accepted (bounded)
Synthetic main lifecycle, removal of import-time patching and the incident disclosure with its historical-provenance limitation, as Codex states. I did not re-check the 11-file store rehash (no store access).

## Additional
- The success path and banner must not carry "ZERO ... MUTATED"-type wording (Codex-0017 notes a conflicting handoff banner).
- A grid test should use the real saved-summary key set as a read-only expected constant, not a fixture-defined one.

## Gate
Diagnostic remains unapproved. No manuscript change, original-store opening, 10k run, API call, calibration run or promotion is authorized. Relay to Antigravity is the user's.
