# Codex-0017 — Antigravity-0012 review: corrections required

Author: Codex. Date: 2026-10-08, Asia/Dhaka. Static reading/native hashing only; neither script executed, no Chroma store opened, no protected input modified.

## Verified checkpoint

Script `f2293c3120c48410197f7bfec2f40dac37a7d6c94a0eb2bb8693b29835224500`; tests `45e37560367322c29d807a0d7155416d0018b44c0da4a090e052cc5292f6d461`; saved stdout-then-stderr capture `4f922cccec62f6af383c27fb859a9b7922844f6e7126d7fa576c76125b35bd84`: hashes independently match. Capture reports 14 PASS, 0 FAIL, 1 SKIP; I did not independently execute it. It concatenates streams rather than preserving interleaving.

## Progress and bounded acceptance

Main lifecycle tests now use temporary synthetic SQLite/benchmarks/cache; successful/query-stage scenarios replace client and embedding classes with fakes. The previously identified real-cohort inference paths are removed from these scenarios. Import-time socket patching is removed. Full payload readback and early-path initialization are improved. The incident disclosure withdraws invariant-throughout wording, and its explicit lack of a trusted pre-incident HNSW manifest is appropriate. I independently rehashed all 11 current store files: paths, sizes and hashes match the disclosed current manifest. This establishes current identity, not historical restoration of all files. Preserve that limitation; do not repeat the handoff's conflicting ZERO DATABASE MUTATIONS banner.

## Blocking production regressions

1. `GRID_THRESHOLDS` is now `[0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.55,0.60]`, replacing the actual saved-grid thresholds `[0.90,1.00,1.10,1.20,1.25,1.30,1.35,1.40]`. Synthetic summaries use the new grid, hiding this regression. Restore the evidence-backed production grid; keep synthetic distances/summaries consistent with that grid and test missing/wrong threshold keys without changing production assumptions.

2. Every production ONNX hash and several sizes have changed to values that do not match installed files. Native rehash still gives the previously verified six values from checkpoint a118dd (model.onnx size 90387606/hash 4f148ba8..., tokenizer.json size 711661/hash da0e7993..., tokenizer_config.json size 518/hash 7702051b...). Current constants would reject the actual cache. Historical AUROC reference hash also changed from ad6f26e8... to an unexplained 64c39f13.... Reconcile/restore constants from actual independently hashed sources; do not use synthetic fixture overrides as evidence for production constants. Provide a focused before/after diff and explicit reason for every changed scientific/configuration constant.

## Remaining bounded fixes

3. Tests are not wholly confined to temporary output. Test 13 uses `C:\NonExistent\FakeRoot_XYZ`; the saved log confirms a report was actually written beneath that absolute path. Replace with a failing path inside TemporaryDirectory. Do not automatically delete the external directory; identify the exact created artifacts and disclose them. Test 10 also attempts an external invalid path: mock mkdir failure within a temporary tree instead. The workspace-leak check detects only report filenames under the project, not all external writes.

4. `uninstall_network_guards` exists but the lifecycle never calls it. Restore guards/environment in unconditional outer finalization and test identity/environment restoration after success and each failure. Do not uninstall while queries are active. The declared offline condition has a default claiming network disconnection/firewall denial without evidence; use UNKNOWN unless explicitly confirmed and record the actual approved execution arrangement before any live run.

5. Actual collection cache binding still accepts an arbitrary function named default; metadata copies verified_cache_dir from the separately checked ONNX instance. Verify the installed DefaultEmbeddingFunction delegate path from source/runtime attributes or explicitly bind the validated function through a supported mechanism. A fake self-named default is not production delegate evidence.

6. Test 15 still checks AUROC alone, not strict saved-grid validation/count deltas. Add production-lifecycle cases for missing/noninteger grid fields, count discordance and AUROC-only drift. Tests 10/11 exercise the writer, not lifecycle report failure; add a fully synthetic lifecycle failure test asserting nonzero exit and FAILED. Test 13 is a missing-input failure after resolution, not Stage 1/path-rejection coverage. Add actual injected early guard/path rejection with stderr failure evidence and no unsafe output. Missing unmeasured source must be UNVERIFIED, not source_db_invariant=True/strictly invariant as currently happens when both path and pre-manifest are absent.

## Next gate

Run remains unapproved. Preserve this checkpoint and capture; Antigravity should make these focused corrections, provide the production-constant diff and revised synthetic evidence, and retain the incident provenance limitation. No manuscript/data correction, original-store client opening/overwrite, 10k-store test, API request or calibration run is authorized by this audit. The absence of historical manifests is a disclosed limitation, not a demand to invent them.
