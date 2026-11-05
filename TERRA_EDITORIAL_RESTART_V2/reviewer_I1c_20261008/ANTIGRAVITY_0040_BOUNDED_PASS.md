# Antigravity-0040 — bounded source/test-evidence pass

Codex, 8 October 2026. Static review of current checker and synthetic suite; read saved log and rehashed artifacts. No script/test execution or project-data run; no manuscript changes.

Verified identities:

- Checker: `8c54d533c01f88b12820c8e33d580ce27cc2b84c7f2b0471481bcb07d5981fee`
- Tests: `f765ac336316729a96cb76bb43ed51fc3312d7b87e3b228fc52f8a5a377c0d8b`
- Saved log: `ea859f64d7f9cb5d8b50830013b81918ffb06df7aa7cd90e064ed7025fc7929d`

The two previous blockers are fixed in current source: primary exception state is tracked separately; finalizer-only hash failure/drift raises rather than returning success. Validation and directory-collision paths are now within finalization scope after the initial hash gate. Missing input/read failure or initial pinned-hash failure is outside that scope and must not be described as checked final preservation.

Targeted synthetic tests now exercise successful post-write hash followed by finalizer-only unreadability/drift, validation-failure rehash, secondary integrity errors preserving primary exceptions, directory collision and write failure with final rehash. Completion record is exclusively created after successful integrity checks. Core arithmetic, pinned source identity, exact populations and no-clamp net definition remain consistent with the prior review. No pipeline/store/model imports are present.

Saved log records 26 tests passing in 0.507 seconds, with the current script/test hashes. This is peer-generated execution evidence, not an independently rerun suite. Happy-path assertions check cohort counts, selected exact statistics/SDs, sampled ledger rows, manifest hashes and completion hashes; they do not exhaustively verify every numerical output.

Diff/provenance limitation: Antigravity reconstructed the old checkpoint from its transcript rather than preserving it before editing. Complete diff text is now embedded in its response, but Codex has not patch-round-trip verified that reconstructed checkpoint/diff. Therefore this pass assesses the current fully read source, not a certification that only the claimed hunks changed. Prior exact byte preservation remains a process requirement for future revisions.

Execution conditions: pin the current script hash immediately before launch; use canonical input with full hash `95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507`, a fresh evidence directory and captured stdout/stderr plus real exit code. Preserve final completion record and output hashes; recheck source/main hashes afterward. A completion record is not included in the two-output manifest, so capture its hash externally. Completion-record write failures propagate; a partial record must not count as success.

No firewall, new API key, inference or historical benchmark rerun is needed: this is arithmetic on saved JSON records. Output will describe those records only. It cannot authenticate exact historical runtime code or establish causal speed gains. Project-data execution and manuscript adoption remain separate user decisions.

Verdict: bounded checker source and supplied synthetic-test evidence PASS with the stated provenance/testing limits. Ready to request approval for one offline evidence export, not a manuscript edit or supplementary reconstruction.
