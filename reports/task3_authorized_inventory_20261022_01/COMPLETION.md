# Authorized inventory: completed; launch freeze blocked

Date: 22 October 2026. Authority: user's `sure` approving file hashing, fresh-copy database metadata inspection and controller-environment checks. This is not launch authorization.

## Evidence and results

- All 11 source-store files and seven MiniLM cache files matched the historical accepted inventory in two scans. The full 11-file store copy matched the source. Final post-inspection checks again confirmed all source/cache hashes, sizes and exact last-write ticks unchanged, and all copied files byte-identical. These are stability observations, not a write lock.
- SQLite metadata was inspected only on `store_copy`, with read-only/immutable connection and query_only enabled. No document or embedding content was read; no Chroma client, tokenizer or model was initialized. The graph was hashed, not decompressed.
- Collection `thinking_traces`, ID `ddbef555-75e4-4c90-8d10-97b4eb239998`, has dimension 384. Native `schema_str` explicitly configures the active #embedding vector index as l2. `config_json_str` is empty (`{}`); collection and segment metadata contain no metric entries. A persisted embedding-name incompatibility is not established by these facts.
- Fifteen tokenizer assets match their two existing manifests. Benchmark, graph and four runtime/native files were hashed in `assets_and_runtimes.json`.
- The initial JSON transcription rounded integer Windows timestamps through JavaScript. Original raw JSON and exact string-valued ticks are preserved separately; `TIMESTAMP_TRANSCRIPTION_ERRATUM.md` explains this. Rechecking exact timestamps resolved the apparent drift; no source mutation was found.
- The initial WMI process-image probe was denied and its owned process was terminated. A subsequent owned-process .NET image check succeeded without elevation. Both outcomes are preserved.

## Bounded code repair and verification

The reader previously ignored native schema configuration when the empty config_json column also existed. `offline_preflight.py` now reads the explicit active #embedding metric, rejects inactive/missing/contradictory declarations, and retains the l2 requirement. Five synthetic regression cases were added in `test_offline_adapters_synthetic.py`. No real adapter execution was used to validate this repair.

The 24 explicitly named synthetic modules ran 481 tests in 12.839 seconds: 479 passed, two skipped, zero failures/errors. Printed collision failures were expected negative-test fixtures. No wildcard discovery was used.

## Unresolved launch blocker

The venv launcher identifies itself as `F:\TERRA -Copy\venv\Scripts\python.exe`, but the actual Python execution process image is `C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe`. Both measured Python versions are 3.14.5 AMD64. The base environment lacks discoverable Jinja2/MarkupSafe; the venv has them. Discovery is not proof of runtime importability.

A firewall rule aimed only at the venv launcher would miss the actual runtime. A rule aimed at the base runtime would also cover the proposed Python controller, and the existing known-other-process check would reject that controller. Distinct executable path strings do not establish distinct runtime images.

No exemption, executable installation/copy, process-gate weakening or firewall action was made. Task 3 cannot yet freeze an executable launch packet.

Recommended decision for the user: authorize code-only design/implementation of separate launcher and actual-firewall-image identities, with a narrowly verified owned-controller-parent exception (both parent and child intentionally offline), rejecting all other matching processes. This changes the process policy and requires explicit acceptance and subsequent review. An alternative is a genuinely separate controller runtime, requiring separate setup scope. Neither choice authorizes a run.

No API key is needed. No network, inference, firewall change, manuscript change or live smoke execution occurred.
