# Held dependency ownership — 23 October 2026

Implementation self-verification under existing user code-only approval.
Added assembly module and10 tests; existing loader/worker/launchers untouched.

OwnedDependency requires an explicit callable release. CohortAssembly wraps the
injected embedding, reader and roles factories, registers each returned resource
before the existing loader validates it, and returns plain prepared dependencies.
The caller uses a context manager around their complete useful lifetime. Cleanup
runs in reverse acquisition order, attempts every registered callback, and closes
the assembly permanently before callbacks begin. An original computation/load
failure remains raised; additional cleanup failures are retained alongside it in
a BaseExceptionGroup, without printing raw exception contents to evidence.

No guessed Chroma close API, private native shutdown or ONNX disposal operation
is used. Factories own partial allocations until returning OwnedDependency;
unowned factory returns fail and cannot be magically cleaned up. This is trusted
in-process lifecycle management, not proof that third-party threads or native
processes stopped. A callback may block; no watchdog is supplied here.

Both constructors and CLI reject authentic execution; no genuine factory is
supplied, no authentic report label is emitted, and all earlier holds remain
unchanged. No real source/store/cache/graph/tokenizer/model, network/API/credential,
firewall/Job, manuscript/statistics or promotion operation was performed.

Focused43 tests pass. First assembly-only invocation also discovered11 imported
loader tests (21total); the fixture import was changed to module-qualified access
before the final43-test check, removing duplicate discovery. No test was failing.
Full named36-module result/log and source snapshots are sealed in this package.
No historical evidence preservation sweep is newly claimed.

Still incomplete: real factory/release adapters, independently bound inventories
and benchmark receipts, authentic worker admission without relabeling synthetic
results, parent/child budgets and ownership, outer watchdog, Windows supervisor
and PS wrapper. These require further source work; any real run needs fresh
review/freeze and explicit dated user permission. No API key is needed.
