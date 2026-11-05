# Held local adapter source — 23 October 2026

Implementation self-verification under existing user code-only authority.
Added offline_cohort_adapters.py and8 synthetic tests. Existing reviewed source
files and launchers remain unchanged. COHORT_NATIVE_ADMITTED=False; genuine
runtime construction and local embedding reject before imports or asset access.
No live gates are patched in tests. CLI returns2 unconditionally.

The injected runtime seam exercises the same argument/wrapping contract intended
for genuine factories: embedding is requested in canonical authentic mode; reader
receives explicit_query_embeddings=True and a receipt-rechecking client factory;
client requests anonymized_telemetry=False. Graph loader receives exact reviewed
SHA256 and20000 population, roles receive authentic mode. This does not certify
an installed provider/runtime or allow mock outputs to become authentic results.

Genuine source lazily binds existing receipt/path/hash/graph/schema/role code and
a cohort-local subclass of canonical OfflineMiniLMEmbeddingFunction. Subclass
initializers reproduce the successful B001 local tokenizer/configuration and
CPUExecutionProvider ONNX loader; embedding arithmetic remains inherited.
Every genuine model initialization and query method retains the new closed gate;
the consumed one-query smoke module's old admission gate is not modified.

LocalHandle exposes only the required cache/embed/schema/corpus/query calls.
Release invalidates future wrapper calls and clears its owned reference. Role
release clears a new owned mapping without mutating the factory's original map.
No Chroma add/update/upsert/delete/reset/stop or guessed native close operation.
These are reference releases, not proof of thread/client/session shutdown or
immediate memory reclamation. Escaped raw references, shared library caches and
concurrent calls are not controlled by this wrapper. Native lifetime termination
must be confirmed by the future dedicated child/Windows Job parent lifecycle.
Factories must roll back partial failures before ownership is returned.

Focused51 tests pass. Full37 named suite log/result and snapshots are sealed.
Tests use fake runtime callbacks, generated query/graph fixtures and prior
installed-source contracts; no real third-party client/model initialization.
No network, native Job/firewall, credentials/API, manuscript/statistics, promotion
or authentic asset operation. No historical preservation sweep newly claimed.

Still required: independently frozen receipt/inventory/benchmark binding,
authentic worker/report wiring, network guard across genuine loading and work,
parent evidence/budget ownership, outer watchdog, Windows/PS controller and final
review/freeze. Genuine factory bodies are SOURCE ONLY and not runtime-certified.
Actual cohort execution requires fresh dated approval; no API key needed now.
