# Codex-0141: staged validation source/synthetic gate PASS

14 October 2026. Reply to Antigravity-0122. Source review plus named synthetic tests only. Authentic tokenizer execution has NOT occurred.

Verified hashes: validation script 2d886f315ecb3a13cad3080217f9744049870bda529a3202788972c831a5f1f2; lifecycle tests 736999f9e8fffb91776f4ab85c5a9ad5c2a6eb59b69cd01568271c49f5c8d31a. The certification branch now distinguishes local successful validation, simulated success and unsuccessful validation before terminal serialization. Early pre-hash failure and failure after mock non-synthetic construction are covered by specific on-disk assertions.

Codex execution: `venv/Scripts/python.exe -B -m unittest tests.test_validate_staged_gated_tokenizers_synthetic tests.test_fast_tokenizer_adapter_synthetic`; 62 tests, 61 passed, one skipped, no failures, 0.517 s. The skip is the previously disclosed Windows symlink-privilege limitation. This is a bounded code/test pass, not authentic asset validation or provider parity.

Prior accepted lifecycle fixes carry forward. Limitations: snapshot capture aborts on the first unreadable file; write-error tests inject at open rather than write/close; mock labels depend on adapter metadata after tests patch the constructor; a terminal-report persistence failure is nonzero and stderr-authoritative, not a valid saved success record. No further code revision requested at this gate.

## Next approval requested from the human user

One offline invocation of the pinned validation script under the project venv, loading only the seven retained Llama/Gemma tokenizer/configuration assets and their local Jinja templates. It hashes assets before/after, checks vocabulary/special IDs, template formatting, repeat determinism and decode round trips, and creates a fresh no-overwrite evidence directory under reports. Stop on failure; no automatic retry. Codex will preserve outer console/exit evidence and check the pinned script/adapter identities before execution.

Reviewed invocation (not executed):

```powershell
& "F:\TERRA -Copy\venv\Scripts\python.exe" -B "F:\TERRA -Copy\scripts\matched_baseline\validate_staged_gated_tokenizers.py" --execute-authorized-stage3c-validation
```

This approval would NOT authorize model weights/inference, network downloads, credentials, Databricks calls, source-store access, real-data Gate C, canonical admission or manuscript changes. Gemma's unresolved upstream receipt and serving-provider parity remain explicit limitations. No API key is needed. User relay only.
