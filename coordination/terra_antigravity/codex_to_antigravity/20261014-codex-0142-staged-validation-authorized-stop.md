# Codex-0142: authorized offline validation stopped on Gemma vocabulary check

14 October 2026. User approved the single invocation proposed in Codex-0141. Codex executed it once; no retry, network, credentials, model inference, store access, canonical admission or manuscript edits.

Run: 20261014_045527_99442807. Child exit 1, FAILED, NOT_CERTIFIED. Llama wrapper loaded and verified vocabulary 128256. Gemma wrapper loaded, but validation stopped because expected vocabulary 262144 differs from observed 262145. Special-ID, template and encoding stages were not reached.

All seven staged file hashes and staged manifest match the pins before/after. Script, adapter and interpreter outer hashes also remain unchanged.

Evidence:
- reports/gated_validation_evidence_20261014_045527_99442807/validation_report.json: 454eaa1f7a9745e344477a9c4d9968d8af42038969bf734c661b991b88f87f23
- Same directory validation.log: 5240ae57cff24fbe547e27c0f9442da2c1201dfade577220b1150aa76330aaa8
- reports/codex_stage3c_outer_2e4c1b2ea7954f9bb135727aef0003c5/: preserved console_output.txt, exit_code.txt and source_before/source_after.csv.

Requested follow-up: reconcile base-vocabulary size versus effective tokenizer size including added tokens against retained JSON/configuration bytes. Do not simply loosen the assertion or edit assets. Return an evidence-backed narrow expected-size correction (if warranted), synthetic fixtures representing the actual added-token structure, new source identities and test evidence. Keep the failed run intact. Any new authentic validation invocation needs renewed user approval.

This is a validation-expectation mismatch, not evidence of asset mutation. No Databricks key is needed. User relay only.
