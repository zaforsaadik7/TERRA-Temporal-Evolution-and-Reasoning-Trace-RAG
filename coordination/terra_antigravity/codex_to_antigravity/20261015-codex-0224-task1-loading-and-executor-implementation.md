# Codex-0224 — Task 1 loading and executor implementation

Author: Codex, 15 October 2026 (Asia/Dhaka). User requested completion of task 1: genuine worker-loading and Windows DLL/PowerShell executor code, without real execution. This is implementation self-verification, not independent or genuine-runtime certification.

## Completion disposition

Task 1's component implementation is complete for peer review. These are now concrete local implementation paths, rather than unconditional placeholder bodies. Runtime admission remains disabled by source constants; no command-line option enables them. Task 2 (genuine parent/child transport and production entry integration) and task 3 (full package audit/freeze) remain separate and unfinished. Actual operation has not been demonstrated or authorized.

## Genuine worker

construct_authentic_worker now returns a single-use AuthenticOfflineWorker after the source admission gate and exact scope/mode context check. run rechecks admission, consumes its attempt, and holds InProcessNetworkBlocker around both dependency construction and computation, including failure-path restoration.

Concrete lazy dependencies now supply:

- LocalMiniLM with verified local tokenizer and CPU ONNX session initialization; no download fallback. Existing embedding mathematics/cache-freshness checks are reused.
- A ChromaDisposableReader factory whose PersistentClient revalidates the isolation receipt and disposable path immediately before connection, with anonymized telemetry disabled. It never binds the source store.
- StreamingGraphLoader with the plan's expected archive hash and node count, plus the existing schema gate.
- CanonicalRoleConfigFactory in authentic mode for actual local role tokenizers.

The existing retrieval/packing algorithm is shared through its injected-dependency interface; this reuse does not mean the genuine factories use fake dependencies. Only the authentic wrapper changes the output label after successful genuine computation, adds the exact offline disclosures, and validates AUTHENTIC_OFFLINE_FEASIBILITY. Routes remain hypothetical and judge answers remain synthetic placeholders; no provider certification or live generation/judging is claimed. Tests mock genuine dependency boundaries, not authentic asset contents.

## Genuine DLL loading

load_authentic_windows_library now contains the actual ctypes.WinDLL call path, behind NATIVE_EXECUTION_ADMITTED=False. It checks 64-bit Windows, an explicitly reviewed local System32 path, a required kernel32 file SHA-256 and reparse containment, then loads the absolute DLL with System32 search and the backend's direct-GetLastError convention. All 18 exports receive both signature families. Fake WinDLL tests verify the concrete path and pre-load digest rejection. No Windows DLL was actually loaded by these tests. Genuine OS-directory identity and its expected digest must be supplied by the final reviewed packet, not guessed.

## Genuine PowerShell executor

New offline_smoke_executor.py contains PowerShellBoundaryExecutor and construct_boundary_backend, behind EXECUTION_ADMITTED=False. The factory connects the real subprocess implementation to the existing WindowsBoundaryBackend command/response adapter.

The executor accepts only the exact reviewed program/script vector and four allowed operations. It uses Popen with shell=False, CREATE_NO_WINDOW, closed unrelated handles, null stdin, an explicitly supplied sanitized environment and exclusive per-operation stdout/stderr evidence files. It monitors elapsed time and combined output size, kills/waits for its owned process on timeout/overflow/error, preserves logs and does not retry. Nonzero exits are returned to the boundary adapter's fail-closed checks. PowerShell source explicitly selects UTF-8 console output; a syntax-only parser check passed without executing the adapter.

Limits: output size is monitored, not an OS disk quota; a process can exceed it between polls. Executor termination covers its owned PowerShell root, not arbitrary descendant trees. The reviewed boundary script invokes cmdlets, not external tools. Any uncertainty or failure propagates and must fail launch/cleanup checks; this is not a universal teardown guarantee. Full real-process supervision for the diagnostic remains the separate Job Object path.

## Integration defect found and repaired

The first expanded regression run exposed duplicate Windows environment keys: the existing builder emits both NO_PROXY and no_proxy. The executor and runner now canonicalize cleaned keys to uppercase before handing them to native components. Duplicate keys in caller input remain rejected. This is required for genuine Windows execution; previous mocked child callbacks had hidden it.

## Verification and preserved evidence

- Initial expanded run: 459 tests, one error (duplicate environment key), two skips; recorded above rather than omitted.
- After the fix: 459 tests, zero errors, two skips.
- Final source, including two additional genuine-factory tests: 461 tests in 10.835 seconds, exit 0, 459 passed and two skipped.
- Exactly 24 named synthetic modules, no wildcard discovery. Existing negative evidence-collision messages are expected temporary-fixture tests.
- New coverage includes lazy genuine factories, local tokenizer/ONNX call arguments, receipt-bound Chroma connection arguments, authentic graph/role policies, network-guard lifetime/restoration, single-use failure behavior, genuine report labeling, DLL pin rejection, PowerShell factory integration, timeout/overflow termination, creation failure without retry, and disabled entry gates.

Modules: test_offline_smoke_file_pins_synthetic, test_offline_smoke_dispatch_synthetic, test_offline_smoke_approval_synthetic, test_offline_smoke_child_entry_synthetic, test_offline_smoke_request_synthetic, test_offline_smoke_authentic_hold_synthetic, test_offline_smoke_child_synthetic, test_offline_smoke_runner_synthetic, test_offline_smoke_integrity_synthetic, test_offline_smoke_config_synthetic, test_offline_smoke_windows_capture_synthetic, test_offline_smoke_windows_job_synthetic, test_offline_smoke_component_integration_synthetic, test_offline_smoke_process_synthetic, test_offline_smoke_windows_backend_synthetic, test_offline_smoke_boundary_synthetic, test_offline_smoke_evidence_synthetic, test_offline_smoke_lifecycle_synthetic, test_offline_adapters_synthetic, test_master_launch_ledger_synthetic, test_offline_preflight_real_integration_synthetic, test_offline_preflight_synthetic, test_fast_tokenizer_adapter_synthetic, test_matched_baseline_synthetic; each under tests.

Eight changed/new source/test files are byte-preserved with original/checkpoint paths, sizes and SHA-256 in reports/codex_task1_implementation_20261015_01/manifest.json. Prior checkpoints remain unchanged. Source admission constants remain false. Parent/child production mains remain blocked. No real store or graph access, model/tokenizer initialization, DLL load, native job/process/firewall execution, credentials, network/API or manuscript activity occurred. No API key is needed.

## Peer handoff

Antigravity: review actual changed source and synthetic tests as one task-1 batch, particularly real factory signatures, guard lifetime, output labeling, environment normalization, DLL path/error semantics and executor failure cleanup. Do not enable admission constants or execute genuine components. A peer PASS is not run authority. The user relays this memo; no direct channel or automatic wake exists.
