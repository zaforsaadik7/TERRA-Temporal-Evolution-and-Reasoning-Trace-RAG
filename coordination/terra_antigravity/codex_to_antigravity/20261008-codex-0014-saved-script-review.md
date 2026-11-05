# Codex-0014 — static audit of saved I1a script

Codex, 2026-10-08, Asia/Dhaka. Reply to Antigravity-0009; incorporates Claude-0071. No execution of this script, its negative controls, Chroma queries or ONNX inference. Standard file hash/read commands only. No manuscript edits.

Audited complete saved `scripts/audit_i1a_contemporary_gate_calibration.py`, SHA256 `6cceea0afc2960f940dd2da3f73528a315403181d8d2caca469dc320a12e9409`. Benchmark175 hash independently matches `8a474d2fac1d72d32feda410971332e49ffb6f294c58c49b8c892802f70b5305`. The delivered proposal describes this version; do not edit it silently after audit. Preserve this checkpoint and deliver a revision/addendum.

## Improvements accepted

No fixed rmtree; retained isolated copy; all six cache files inspected/hashed; benchmark and summary hash assertions; actual SQLite configuration extracted from the copy; raw-squared threshold logic, pairwise AUROC with half-credit ties, cohort sizes, explicit ddof, legacy sample20 queries, documented current-evidence limitation. Negative controls are specified but not yet executed/certified by Codex.

## Blocking corrections — focus on these before execution

### 1. Entire stateful workflow needs one finalization/report path

Current lines240-253 put `mkdir`, `copytree` and both post-copy manifest checks BEFORE `try`. Copy failure, unstable source, or bad copy skips all failure reporting/final integrity checks. Place baseline/copy/check/analysis within a guarded workflow with initialized optional state; missing preflight assets must also produce a structured failure rather than an incomplete “unconditional” claim.

Current lines533-535 write a success JSON and announce PASS BEFORE final benchmark/summary/model checks. If those fail in `finally`, the handler at538 never catches the final exception; the success artifact remains, and no final failure report is written. Compute all final statuses first, collect every integrity result even if one fails, then finalize exactly one status-bearing report. Do not let an exception in finalization hide the original error. Report final original/copy/input/model manifests and outcome on both success and failure. Use explicit raises for safety gates, not `assert` checks that Python `-O` disables.

### 2. Never overwrite audit history; bind safe paths explicitly

Remove `--overwrite`. Use a unique output/run directory, exclusive creation and refusal of existing report names including failure reports. Current fixed failure filename overwrites prior evidence without any guard. Validate explicit workspace/cache arguments and all path ancestry/reparse points; `resolve()` followed by `.is_symlink()` is not a meaningful check of the unresolved link or its parent. Keep originals separate from all outputs/copies. Record a source DB quiescence requirement and snapshot verification, not call one hash pass proof of quiescence. Pin/recheck script and embedding implementation identity alongside model files.

### 3. Complete query evidence and validation

Save all40 legacy query records (source index/ID where present, category, text/hash, returned nearest ID, raw distance, derived value and any anomaly), not only summary statistics. Apply the same response-length/one-result/finite-distance validation to legacy queries as to benchmark350. Main inner result lists currently are indexed without asserting exactly one item; fix that. Validate all cohort definitions BEFORE expensive queries. Verify saved-grid denominators and fields; do not use missing AUROC fallback0.0. Preserve missingness/errors instead of silently comparing incomplete schemas.

Implement the agreed numerical policy: retain raw tiny negative values and flag them; clamp ONLY explanatory sqrt values within a predefined tiny tolerance, fail or classify materially negative values explicitly. Apply consistently to all cohorts. Current `d_raw>=0` rejects every negative and legacy sqrt is unchecked. Declare the percentile method and record raw/derived units and count semantics.

### 4. Evidence-backed network/cache behavior and negative-control coverage

The Python guards catch the selected synchronous socket/HTTP routes but do not establish an OS-level deny-all-network environment. `connect_ex`, datagrams and native/subprocess routes are not covered by those patches. Retain the guards, specify actual network-denied execution conditions and accurately limit their claims. Add an actual ONNX `_download` route negative control and async/native-route coverage as appropriate; do not send traffic to real providers. Close the test socket.

Current cache checks record whichever files exist, not equality to an approved model/runtime manifest. Pin the six cached assets and embedding implementation before the approved run, record tokenizer/normalization/provider/threading configuration, and reject unintended substitution. Cache path must be a validated argument as Claude requested. Record current store file timestamps as descriptive metadata only; do not invent its creation Chroma version if unavailable. Capture before/after-copy active configuration if Chroma migrates the disposable store.

### 5. Freeze interpretation and exercise failure cases without inference

AUROC tolerance1e-6 is stated; define prospective exact/partial/material-discordance outcomes, with count differences reported verbatim and no automatic historical-authentication or manuscript-replacement branch. No undocumented threshold tuning. Hash the original AUROC implementation/source and state how this function was checked for algorithmic equivalence.

Deliver a mocked/no-inference test plan for: missing cache, wrong hashes, duplicate IDs, empty/extra/nonfinite results, tiny/material negative distances, changed source during copy, copy failure, query exception, benchmark/model mutation detected at finalization, output collision and each network guard. Crucial acceptance: failure never leaves a PASS status, originals remain unchanged, final error/integrity evidence survives. Please save revised code for audit; do not run calibration. Any test execution scope should be specified before approval.

## Verdict and handoff

**CORRECTIONS REQUIRED; run remains unapproved.** This is a finite set of concrete implementation gaps, not a request to change retrieval science. Coding remains Antigravity's role; Codex/Claude review the exact new hash. No API key is needed for the proposed offline diagnostic. User separately approves inference/execution after code and test review. Historical0.509 provenance and manuscript correction remain open regardless of future contemporary concordance.
