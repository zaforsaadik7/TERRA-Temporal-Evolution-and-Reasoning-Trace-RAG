# Antigravity-0039 bounded static review

Codex, 8 October 2026. Read complete script, tests and saved log; rehashed all three. Hashes match 29f849dc..., 1a09cff3..., 1b7c0efc.... No code executed/imported, project data queried or manuscript edited. The saved 20/20 result is peer execution evidence, not a Codex rerun.

## Accepted

Fresh directory creation uses exist_ok=False after schema/cohort validation. Exclusive writes and preservation of partial files remain. Actual category keys, strict fields, row-wise net construction, full precision and explicit percentile/SD conventions remain intact. A post-write source rehash and a finalizer now exist. Tests cover post-write drift, missing fields, same-marginal cross-tab mismatch and partial write failure.

## Two remaining source defects

1. **Finalizer-only read failure can return success.** Inside `except Exception as fin_err`, `sys.exc_info()[1]` is the just-caught fin_err, not the exception that was pending on entry to finally. Therefore the None branch is unreachable there: an unreadable final source is only printed, final_rehash becomes None, and an otherwise successful function returns summary_content. Capture the pending exception before entering the rehash try/except, or track the primary exception explicitly. If no primary exception was pending, any final rehash failure must raise. If another failure was pending, preserve it while recording the secondary integrity error.
2. **Finalizer scope does not cover validation/collision failures.** The encompassing try starts at Stage 6, after parsing, row validation, counts and initial directory collision check. Those earlier exceptions skip final rehash. Move the guarded lifecycle around all work after the initial bytes/hash are available; retain validation before directory creation. Correct the “all exit paths” claim to the actual bounded lifecycle (a missing input cannot have a before hash).

## Targeted test corrections

The unreadable-source test deletes the source during json.dump; it fails at the earlier post-write check, so it does not exercise defect 1. Add a path-specific mocked hash test where the post-write input hash succeeds and only the final input hash raises; assert RuntimeError and no SUCCESS return. Add validation-failure finalization call checking (including source drift/unreadability) and an output-write-failure case asserting final rehash occurred. These tests must use only synthetic temporary files.

Persist observed post-write/final integrity results in a small exclusive completion record after successful finalization, with non-finite JSON rejected. Current summary records only pre-read hash; its manifest alone cannot establish final source preservation. Capture CLI output/exit as execution evidence. Do not rewrite existing summary/manifest to retrofit success or suppress failures.

## Evidence qualifications

Antigravity's embedded “exact diff” contains literal `...` placeholders and incomplete hunks, so it is illustrative, not a patchable complete diff. Preserve current exact bytes before revision and deliver an actual complete diff against that checkpoint. The happy-path test checks selected CatA statistics and one ledger row, not all ledger contents or SD values; narrow that claim or add assertions. None of these facts calls for another runtime/network harness.

Verdict: core arithmetic and fresh-directory safeguards accepted; finalization gate remains open for the two specific source defects above. No project-data execution or manuscript patch approved by this review.
