# Claude review of Codex-0038 / Codex-0018 (claude-0076)

Claude, NOT independent. Static only: nothing executed, no store opened, installed ONNX files not rehashed, the 15 PASS/1 SKIP log not rerun.

Reviewed: script 142da3d8...79ca, tests 3844ed1e...6571 (hashes match Codex-0038 identities as staged).

Verdict: major repairs PASS at source level; two focused fixes remain, as Codex states.

## Independently confirmed repairs
- `GRID_THRESHOLDS` (line 275) is `[0.90,1.00,1.10,1.20,1.25,1.30,1.35,1.40]`, matching the saved-summary keys I read in claude-0075.
- `APPROVED_ONNX_CACHE_MANIFEST` equals the d0d3a3 checkpoint values (model 90387606/4f148ba8..., tokenizer.json 711661/da0e7993..., tokenizer_config 518/7702051b..., config b567c7d5..., special_tokens b6d346be..., vocab 07eced37...). Match to installed files remains Codex's native-hash claim, not mine.
- `REFERENCE_HISTORICAL_AUROC_SCRIPT_SHA256` is back to ad6f26e8..., which I rehashed from `scripts/compute_budget_and_gate_metrics.py`.
- Lifecycle now calls `uninstall_network_guards()` (line 1146) in the final block; default offline declaration is `UNKNOWN_OR_UNCONFIRMED_ENVIRONMENT` (lines 470, 1169); report writing is skipped when path validation fails.

## Remaining fixes (reproduced)
1. **Delegate check still accepts a name.** Lines 760-766: `ef_delegate_name == "default" or isinstance(..., ONNXMiniLM_L6_V2) or (mock_overrides and "allow_mock_ef" in mock_overrides)`. Any object whose `name()` returns "default" passes. A mock-bypass flag also sits inside the production check. Replace with an exact type-and-module check on the concrete delegate (Codex says installed DefaultEmbeddingFunction source supports this; I did not read installed chromadb), and move test substitution out of production code, for example by injecting a fake client class that the check can distinguish.
2. **Stale-state cleanup test.** Tests import `_NETWORK_GUARDS_INSTALLED` by value (line 362, similarly 428, 456) and then assert it is False (lines 404, 447, 487). A `from module import name` binds the boolean at import time, so the assertion never sees later changes. Read it as `module._NETWORK_GUARDS_INSTALLED` after each lifecycle call, and also check the patched callables are the originals.

## Small observations
- `uninstall_network_guards()` sits at the end of the `finally` body after report writing; if code before it raised outside a `try`, it would not run. Wrap in its own try/finally.
- Offline declaration remains a free-text argument. Prospective execution conditions should be recorded by the user before any run (for example: network physically disconnected or firewall rule, who confirmed, when). I cannot judge them from here.
- The word "disposable snapshot evaluated" in the success banner is acceptable; the earlier zero-mutation banner is gone.

## Gate
Diagnostic remains unapproved: it needs the two fixes, a Codex and Claude re-audit, a user-confirmed offline condition, and separate user permission. No manuscript, data, original-store, 10k, API or promotion action is authorized. Relay to Antigravity is the user's.
