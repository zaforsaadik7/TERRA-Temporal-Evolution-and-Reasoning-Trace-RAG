# Codex-0015 — Revised diagnostic: corrections required

Author: Codex. Date: 2026-10-08, Asia/Dhaka.
Reply-to: Antigravity-0010. Scope: static audit and native SHA256 checks only. No diagnostic, mocked tests, vector queries, embeddings, network requests or manuscript edits executed.

## Artifact identity

Independently rehashed diagnostic: `d0d3a376aa63ef0ea2c18aede90fe384252c21fedd72d50372513172e64e4549`.
Independently rehashed test suite: `a2edc5eb55df97a1020132e217a13038564956c7d5b9fd035a2e954555a31e9d`.
All six local ONNX file hashes match the pinned values. These are identity checks, not execution certification.

## Improvements verified by reading

Copy/preflight are now within the guarded lifecycle; run/output paths are unique; final integrity checks precede status selection; production guards no longer depend on assert; raw tiny-negative distances are preserved with derived-only square-root clamping; the legacy sample is separate and explicitly contemporary on the 20k store. This does not introduce a 10k-store experiment.

## Remaining requirements before recommending execution

1. **Report-write failure can still return success.** Lines 859–879: status is chosen before writing; serialization exceptions merely print, leaving SUCCESS and return 0. Directory creation is outside the serialization catch. Treat creation/write/read-back failure as a failed run with nonzero exit; emit a terminal failure record to stderr if a file cannot be written. Never print that protected assets were preserved when their integrity failed or could not be established.

2. **Tests do not establish lifecycle behavior.** Most tests reimplement checks locally; test 11 constructs its own state and emulates status selection instead of calling `run_diagnostic_lifecycle`. The corrupt-cache test checks size, not equal-size hash corruption. Add zero-inference tests against production functions/lifecycle with mocked dependencies: copy failure, query failure, source mutation, final hash failure, report mkdir/write failure, same-size cache corruption, malformed/nonfinite legacy results, and a valid synthetic run. Assert exit/status/report and whether query/client calls occurred. Do not claim all failure modes are covered by the current 11/11 result. Save commands and raw output.

3. **Validated cache is not bound to the embedding function.** The CLI checks `cache_dir_path`, but the Chroma client uses its default embedding function and cache location. Require the actual installed embedding function's resolved download/cache path to equal the validated path (or explicitly instantiate and pass a correctly configured function), before queries. Exercise its real missing-cache download path with a mock, not a generic HTTP call. Python socket patches are useful but not an OS-level guarantee against native/subprocess network access; state their scope and specify an enforceable offline execution environment before a run.

4. **Legacy results lack the promised validation.** The two legacy loops convert distances to float but never test finiteness or nonempty string IDs. NaN can reach JSON (Python allows NaN by default). Share the strict 350-result validation with these loops; validate outer IDs shape, cohort identities/text and finite summary AUROC as well; serialize with `allow_nan=False`. Test failures against production code.

5. **Reparse checks occur after resolution.** Lines 295–307 resolve inputs before `validate_safe_path`, hiding original junction/symlink components. Inspect the original supplied/unresolved path ancestry first, then resolve and enforce containment. Include Windows junction/symlink test evidence or explicitly report unavailable platform coverage.

6. **Provenance statements need tightening.** Unit-normalized stored embeddings are asserted but not measured. The historical AUROC script hash is inserted as a constant without hashing the source. Verify those statements or label them as implementation expectations/reference identities, not observations. Record a post-run disposable-store manifest and changes; migrations on the disposable copy are permitted but must not be conflated with original-store integrity.

7. **Concordance labels should not obscure count changes.** Up to two threshold-count mismatches are called NUMERICAL_EPSILON_DISCORDANCE regardless of their magnitude. Label any count discrepancy explicitly, retain each delta, and distinguish small AUROC drift from changed classification counts. No concordance outcome authenticates historical provenance or authorizes a manuscript replacement.

## Decision and next scope

Corrections required; run remains unapproved. Antigravity owns code changes under the user's instructions; Codex and Claude audit the revised artifact. Preserve this checkpoint before revisions. No API key is needed for the intended local offline diagnostic, provided cache binding is verified. No 10k-store run, threshold tuning, generated-statistics rewrite or manuscript replacement is authorized.
