# Code-only failure diagnostics

23 October 2026, Asia/Dhaka. User approved safe failure logging and synthetic tests without another diagnostic attempt, following Codex-0252. Admissions and anchors remain closed; used attempt records and evidence remain immutable. No worker computation, runtime policy or authorization is changed.

Design: capture the deepest named failure stage and bounded exception-chain traceback metadata in the existing child stdout capture. No raw exception messages, source-line text, locals, query/request values or environment values are emitted. This avoids relying on best-effort secret redaction of arbitrary exception strings. Filename/function/line metadata identifies the failing call site; unknown external error details may still need later review. Logging is not a fix for the previously unlocated RuntimeError, and cannot recover its missing traceback retrospectively.
