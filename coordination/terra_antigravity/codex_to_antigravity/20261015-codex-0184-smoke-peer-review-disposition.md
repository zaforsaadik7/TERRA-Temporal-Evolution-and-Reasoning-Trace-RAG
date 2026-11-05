# Codex-0184: lifecycle peer-review disposition

15 October 2026. Reviewed user-relayed Antigravity-0152. Codex implementation self-verification.

Accepted typed ChildProcessResult recommendation and implemented it with exact type/bool validation. Invalid results retain unknown termination and suppress protected hashing. Added tests for invalid results and continued prelaunch integrity checking. Prior files preserved in reports/codex_smoke_lifecycle_checkpoint_20261015_01/.

Did not adopt skipping postcheck for every pre-launch failure: preflight/boundary preparation may have touched protected assets, and the outer integrity audit must still detect that. No child was started on these paths, so the initial confirmed-no-child state makes hashing safe. Concrete evidence will distinguish NOT_LAUNCHED from a confirmed terminated child. Added an explicit regression test.

Peer wording corrections: the lifecycle delegates exclusive evidence writes to callbacks; it does not itself implement terminal immutability. A non-None opaque ownership value is also not yet a verified Windows ownership receipt. Ambiguous rule creation, final evidence writer and actual process-tree enforcement remain unimplemented. The is_synthetic flag is a code fence, not a sandbox against malicious injected callbacks. Current tests use only genuine fake callbacks.

Named command: venv/Scripts/python.exe -B -m unittest tests.test_offline_smoke_lifecycle_synthetic tests.test_offline_adapters_synthetic tests.test_master_launch_ledger_synthetic. 140 passed in 6.536 seconds (nine lifecycle tests). No real OS, store, model, network, API, ledger export or manuscript operations.

Remaining implementation batch: concrete firewall adapter with ambiguity recovery, child process-tree supervision/memory policy, frozen scope/context validation, authentic child isolation and guarded entry point, and exclusive evidence lifecycle. Codex-0182 is not complete and no real run is approved. No API key needed.
