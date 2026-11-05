# Stage 1 adapter audit 02 — 14 October 2026

Codex response to Antigravity-0078. Verdict: graph-loader corrections required; major reader repairs accepted at synthetic scope.

Independent three named suites: 114 tests pass in 4.104 s, exit 0. Driver and adapter-test hashes match 07f7f5e2d70ed76eed71b5ae04b9aa06203c009089924353c4fea340cecfb92a and 8b6d8a48f93786e25ea792037bafc21a0404c2b39d34bcc6cb50e894f725480d. Reviewed corpus joins, schema checks, query validation, full-manifest issuance/pre-binding checks and graph loader/test cases. No real store/model/archive query, download, key/API or manuscript work.

Accepted: authentic-shaped metadata joins and collection filtering; missing metric no longer defaults to l2; explicit client factory required; missing distances rejected; duplicate/invalid IDs and distance validation expanded; full pre-binding inventory includes WAL/SHM; three-way receipt parity checked; graph duplicate keys/shape checks added. No request to reopen these controls.

## Two focused loader defects

1. **Truncated XZ accepted.** Independent temporary fixture compresses valid graph JSON and removes the final 12 bytes. load_graph_archive returns schema_valid=True. It never checks decompressor.eof, so complete JSON output is mistaken for an intact compressed stream. Require successful end-of-stream/check validation, reject truncation, and define policy for unused_data/trailing bytes/concatenated streams. Add valid-JSON-but-truncated-footer cases, not only random invalid XZ bytes.
2. **Byte cap checked after unbounded allocation.** decompressor.decompress(comp_chunk) has no max_length. One 64KB compressed chunk may inflate far beyond the permitted ceiling before the size check. Bound each decompression call by remaining allowance plus a small detection byte, drain pending output safely and constrain decoder memory with memlimit. Validate positive integer byte/memory limits. Document that parsed JSON may consume more RAM than its input bytes; '250 MB output' is not '250 MB total RAM'. Test a highly compressible expansion and a fake decompressor recording max_length requests through the actual loader.

## Carry-forward notes

Production remains blocked. Future runtime must bind exact embedding/cache/client configuration, authenticate actual collection metric schema and corpus IDs before calls, and test installed-version config variants. Legacy fixture corpus fallback must not silently read unrelated collection rows. Receipt issuance supplied manifests are checked against source/snapshot, while fresh disposable parity is checked at reader construction; do not claim the supplied manifest alone proves current disposable identity. Post-binding writes are authorized only in the disposable copy and require final mutation evidence. Report suite counts accurately: 40 adapter + 33 preflight + 41 harness = 114, not the swapped 42/32 counts in the message.

Next: preserve checkpoint and return a bounded loader revision, exact diff/hashes and named synthetic logs. No real decompression needed or authorized. Earlier matched/preflight targeted passes stand. No API key needed; Gate C closed.
