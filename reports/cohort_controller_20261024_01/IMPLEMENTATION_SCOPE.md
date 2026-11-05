# Receiving CLI/context boundary — code-only checkpoint

24 October 2026, Codex implementation self-verification.

New offline_cohort_controller.py and eight named synthetic tests only. Existing
command R02 identities verified before regression; no previous source changed.

The fixture CLI accepts exactly the ordered --launch-context/--approval pair
derived from independent ControllerCommand. No abbreviation, additional flags,
duplicate option or path change is accepted. Failure consumes the fixture actor.
Context bytes have an 8 MiB bound and reviewed raw SHA; duplicate keys, nonfinite
JSON, invalid UTF-8 and structural changes fail closed. Canonical re-encoding
distinguishes integer zero from boolean false. The returned typed command comes
from independent review, NOT hydration of untrusted wire contents.

FixtureController composes parsing, injected context/approval readers, the existing
approval DATA validator with the NEW command digest, exact rule/owner checks,
inventory observation, benchmark receipt and single immutable controller dispatch.
Dispatch digest combines command and bound job digests. Old policy-only approvals
are rejected. Real human permission is not established by these test records.

All callbacks are trusted mock/fixture collaborators. Bounds apply after callback
returns bytes; no claim of bounded physical reads, timeout or safe native actor.
The independent typed review transport/trust root, authentic receiving CLI,
isolated Python bootstrap, native observer/Job/capture/cleanup, child command,
fresh inventory/authority freeze and PS user launcher remain unfinished.

This is synchronous fixture composition, NOT a genuinely supervised controller.
No real files from benchmark/store/cache/graph/tokenizers, model initialization,
native Windows operations, firewall, network, APIs, credentials or manuscript/
statistics changes. main stops before parser/readers, returns 2; new hold False.

Clarification of peer-0230 wording: -I ignores user-site/PYTHON* and unsafe path
injection; it does not universally suppress site hooks/venv packages. -B stops
bytecode writes, not reads. Runtime closure remains a future identity obligation.
