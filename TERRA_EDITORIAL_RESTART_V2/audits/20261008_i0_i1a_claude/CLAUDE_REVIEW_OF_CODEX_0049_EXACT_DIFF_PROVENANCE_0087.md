# Claude review of Codex-0049 / Codex-0028: exact-diff provenance (claude-0087)

Reviewer: Claude. NOT independent (Claude wrote the Batch 1-28 text). Static only. I did not run the test suite, the wrapper or the diagnostic, and I opened no Chroma store. Coordination is user-relayed; I have no live channel to Codex or Antigravity.

Read: Codex-0049, Codex-0028, Antigravity-0024. Staged and compared the real files myself.

## 1. What I reproduced

| Artifact | SHA-256 (my rehash) | Bytes | Lines | Matches claim |
| --- | --- | --- | --- | --- |
| evidence/audit_i1a_contemporary_gate_calibration_checkpoint_7cd926.py | 7cd926beca6e819f185d2759dafab6ce528abfc87a8451828de88fd2f8ebc41f | 61,161 | 1,233 | yes |
| scripts/audit_i1a_contemporary_gate_calibration.py | c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d | 62,968 | 1,272 | yes |
| evidence/diagnostic_7cd926_to_c37dda_exact.diff | b3e1126d5be419ead4513f72533de2b9dae3da837b3566833c07a426f63c282a | 4,678 | 92 | hash yes; see 3a |

The old-checkpoint hash is also the 7cd926be... I recorded as the code-gate pin in claude-0079, so the surviving file is the version I reviewed then, as far as a hash can show.

Independent comparison: `diff -u` of old versus current gives five hunks (old lines 423, 730, 738, 850, 866). Excluding headers, it shows 41 added lines and 2 deleted lines.

- The only deleted lines are the two former identifier defaults, `qid = q.get("query_id", "sample_in_q")` and `q.get("query_id", "sample_out_q")`.
- Every added line is one of: the new `resolve_benchmark_identifier` function; the `isinstance(bench_175, list)` check; the 40-record `query` text and uniqueness check in Stage 6; the replacement `qid, src_field = resolve_benchmark_identifier(q)` with the `query_sha256` computation; and the two new ledger keys `source_field` and `query_sha256`.
- Nothing else differs: no threshold grid, `MAX_DISTANCE_CEILING`, `FLOAT_TOLERANCE`, squared-L2 or sqrt transformation, AUROC, concordance classification, network guards, "x"-mode writer, read-back, fallback removal or cleanup code is touched.

Strongest check: applying the saved diff with `patch` to a copy of the old checkpoint reproduces a file whose SHA-256 is exactly c37ddaa72ab5c410d43756af40d27003b446f0ad19ea182454ec0f097e67094d. So the saved diff is complete (no hidden hunks) and sufficient to turn the old source into the current one.

## 2. Verdict

Corroborated. The missing-byte-diff limitation I raised in claude-0086 is closed at source level: the change from the previously gated 7cd926be... to c37ddaa7... is confined to identifier resolution, Benchmark 175 list/text/uniqueness validation, and the query-hash/source-field ledger additions. I agree that no special acceptance of that limitation is needed. The code-gate PASS in claude-0079 is therefore carried over to c37ddaa7... with these bounded additions, which I reviewed in claude-0086.

This is a diagnostic source-provenance result only. It does not authenticate the historical vector store, the earlier incident, or the historical calibration.

## 3. Minor discrepancies (none affects the verdict)

a. Antigravity-0024 lists the diff as 4,586 bytes and 99 lines. The file on disk is 4,678 bytes and 92 lines (CRLF line endings; `patch` reports stripping trailing CRs). The SHA-256 matches what Codex-0028 and Antigravity-0024 both give, so the artifact is the intended one and only the prose figures are off. My own regenerated diff (cc7dc2c0..., 4,620 bytes) differs from it only in where the blank separator lines fall; the 43 changed lines are the same set. That is the "line boundaries" difference Codex mentions.

b. Antigravity-0024 describes the changes as "18 / 13 / 8+8 lines". My count is 41 added and 2 deleted. The descriptive counts are loose; the diff itself governs.

c. The diff headers carry parenthetical hash text, so it is a record for reading, not a byte-exact `git diff` output. Immaterial given the patch round-trip in section 1.

d. Antigravity-0024 states the wrapper enforces the 40-ID uniqueness too and that the diagnostic does so in Stage 6. I confirm the diagnostic does (the added `len(set(legacy_40_ids)) != 40` check), which corrects my claude-0086 note 2 that said uniqueness was enforced only by the wrapper. Both layers enforce it.

## 4. Not verified

- The test file ecd894be... , the harness test file d32f5dd6... and the 45-test log c85cd9e7... : I did not hash or read them in this pass. I rely on the hashes quoted by Antigravity-0024.
- The checkpoint's custody before it was copied into evidence/ (a hash match shows content identity, not who preserved it or when).
- Whether the wrapper at b7f59c41... is unchanged since claude-0086; I did not rehash it in this pass.

## 5. Boundaries and what is still open

No run is approved. This verdict does not authorize the diagnostic, a 10k run, an API call, threshold tuning, a firewall or network change, a manuscript edit or canonical promotion.

Still required before any run, all on the user's side or separate gates: the user's chosen externally enforced offline arrangement with a dated authorization; a frozen command and working directory in a byte-preserved execution package (hash-pinning source is not a write-protected snapshot); explicit single-run approval; then the post-run audit. Historical calibration (main line 210) stays OPEN, and the DB incident still needs its factual addendum. Relaying this to Antigravity is the user's.
