# Held canonical reader and selected inventory binding — 23 October 2026

Implementation self-verification under user code-only authority. Added input
module and13 tests. All previously reviewed source files remain unchanged.

_read_once checks independently supplied path/size/hash pin, absolute non-traversing
paths, ancestor symlink/reparse rejection and regular single-link input. It checks
path metadata before opening, compares device/inode/size/mtime against fstat on
the open handle, reads size+1 bytes at most (reviewed size <=2MiB), compares full
handle metadata before/after and full path metadata before/after, and hashes
exact returned bytes. Parser consumes those same bytes without reopening.

Windows diagnostic finding: initial focused run76 tests had one error because
path-based ctime and handle-based ctime differed. Thirty generated temporary-file
observations reproduced this difference while device/inode/size/mtime agreed;
for example path ctime1792775862565279800 vs handle ctime1792775862566280300,
both mtime1792775862566280300. Actual root cause/API semantics are not certified;
the directly observed difference motivated comparing ctime only within the same
metadata interface. New deterministic test covers stable cross-interface ctime
difference; another still rejects within-interface post-read drift. No retries
or tolerance loops introduced. Final focused77 tests pass.

Canonical reader entry rejects before filesystem access while
COHORT_INPUT_ADMITTED=False. Its held source requires canonical path/digest and
parses the observed bytes against CohortSpec. Fixture reader requires a guarded
temporary root, rejects the canonical benchmark path and authentic flag, and
returns observed FileReadReceipt plus query-only binding (no answers/gold).
Tests actually read temporary generated files only, including a temporary hardlink
rejection test. No real benchmark or asset opened.

bind_inventory is PURE selected-file data binding: exact typed pins, nonempty
immutable rows/required set, duplicate/case aliases, missing/extra/mutated entries
rejected, benchmark receipt pin/size metadata linked to same selected inventory.
It performs no scan or file existence/freshness check. A test deliberately binds
a non-existent graph fixture pin to demonstrate this limitation. Independent
observed rows and required set must come from the future trusted frozen lifecycle.
Data equality is not a signature, permission, recursive membership closure or
evidence that every requested asset was just hashed. No such certification claimed.

File metadata/hash checks are not an OS lock, race-free namespace sandbox or a
guarantee against an attacker restoring metadata. Pinned bytes protect content;
path provenance remains a bounded observation. The wrapper isn't concurrency-safe.

Remaining: wire observed receipt and selected/full-root inventories into parent
admission and actual worker handoff, allocate parent/child evidence budgets,
pre-child outer watchdog, Windows Job/PS launcher composition, full identity
freeze and fresh dated real-run permission. Reader exists at source; authentic
execution remains blocked by all earlier and new holds. CLI returns2.

No genuine assets, model/session/client, Job/firewall, network/API/credentials,
manuscript/statistics or promotion operation; no historical preservation sweep
newly claimed. Full39 named regression result/log and snapshots are sealed here.
No API key needed.
