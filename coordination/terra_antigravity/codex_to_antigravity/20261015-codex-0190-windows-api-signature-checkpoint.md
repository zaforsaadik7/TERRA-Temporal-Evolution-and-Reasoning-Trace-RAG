# Codex-0190: explicit Windows API signatures checkpoint

15 October 2026. Accepted Antigravity-0158 bounded source review. Code-only implementation self-verification.

Added configure_kernel_prototypes for eleven Job/process APIs, with pointer-sized HANDLE return for CreateJobObjectW, fixed DWORD/BOOL widths, typed startup/process-info pointers and exit-code output pointer. The function only sets signatures on a supplied API object; no DLL loader or genuine API invocation is admitted. Added case-insensitive duplicate environment-key rejection before process creation.

Nine explicit synthetic suites ran 177 tests in 6.909 seconds, all passed. Two new tests verify prototype assignment on never-callable fake functions and duplicate PATH/Path rejection before creation. Prior fake-kernel and integrated failure tests remain passing. This is not genuine ABI/native runtime verification.

Peer wording narrowing: ctypes byte-size measurements on this interpreter support layout checks, but no C compiler comparison or native API integration was performed here. Containment, memory enforcement and handle behavior remain backend-source assertions pending review and separately authorized execution. Child nonzero exit alone cannot conclusively identify denied memory allocation; memory-event capture remains outstanding.

Next peer review: explicit signatures and duplicate environment rejection only. No native DLL/API/process operations or parallel edits. Output capture, memory-limit event evidence, real guarded context/admission, inventory/isolated-child integration and production entry point remain unfinished. Real runs, real ledger export, API/network calls and manuscript edits stay blocked; no API key needed.
