# Codex-0276: Held input reader and selected inventory binding

23 October 2026, Asia/Dhaka. Codex implementation self-verification after
Antigravity-0225 and user's “okay,” within existing code-only/synthetic scope.

Package: reports/cohort_input_20261023_01/. Read IMPLEMENTATION_SCOPE.md,
manifest.json, snapshots, TEST_RESULT.json and named_tests.log. Added
offline_cohort_input.py and13 tests; earlier source files untouched. Prior34
loader/assembly/adapter/execution manifest entries reverified unchanged.
No old184-file preservation sweep newly claimed.

Bounded single-stream reader verifies independent path/size/hash pin, guarded
ancestors, regular single-link input, before/after path and handle metadata,
<=2MiB size and exact returned-byte SHA256. Parser consumes those same bytes.
Canonical entry source-held before filesystem access by COHORT_INPUT_ADMITTED=False;
held source requires canonical path/digest. Fixture entry uses temporary generated
files, guarded root containment, rejects canonical path and authentic flag, returns
observed FileReadReceipt plus query-only binding. Actual canonical file remains
unread. Metadata/hash observations are not an OS lock or race-free namespace proof.

Confirmed Windows fixture issue: initial focused76 tests had one metadata error.
Thirty generated temp-file observations reproduced path-vs-handle ctime differences
while device/inode/size/mtime matched. Example and limits saved in scope report.
The reader now compares device/inode/size/mtime across APIs and complete metadata
including ctime before/after WITHIN each same API. No retries/tolerance loops.
New deterministic cross-API difference test accepts stable identity; another
still rejects post-read within-interface drift. Root API cause not independently
certified; this is the observed local behavior, not a universal Windows claim.

bind_inventory is pure equality/selected-set binding: exact typed file pins,
immutable nonempty rows and required-path tuple, alias/missing/extra/mutated row
rejection, and observed benchmark receipt linked to the same pinned inventory.
It does NOT scan, hash assets, verify existence/freshness, certify complete root
membership or sign an authority record. Test deliberately includes a nonexistent
graph pin, showing why independently trusted observation/closure is still needed.

Focused77 tests pass. Full39 named modules:660 tests,658 passed,2 skipped,
zero failures/errors,113.642s, venv-B. New13 tests use generated temporary files,
including hardlink rejection, exact-content observation, size/hash/path/byte cap,
metadata drift/interface distinction, held entries before filesystem, and pure
inventory identity/metadata/alias failures. Existing full retrieval fixture remains
synthetic. No genuine model/client/cache/store/benchmark/graph opened by this work.

All prior gates and new input gate remain closed. No network/API/credentials,
native Job/firewall, manuscript/statistics, promotion, real cohort or launch packet.
No API key needed.

Peer review requested: actual handle/path comparison semantics and read bound,
Windows fixture repair evidence, source-held canonical gate, query-only output,
pure inventory limits and unchanged sources. Rerun only39 modules from TEST_RESULT
via venv-B; no discovery or genuine inputs/native work. Do NOT rerun the sealing
script into this immutable package (exclusive output collisions are intentional).
No parallel edits requested.

Remaining: bind reader receipts and complete frozen source/asset observations into
parent admission/worker handoff; parent/child evidence allocation; pre-child outer
watchdog; Windows Job/PS controller; full identity freeze and separate dated user
permission for an actual cohort attempt. Selected-row equality cannot close those
remaining gates by itself.
