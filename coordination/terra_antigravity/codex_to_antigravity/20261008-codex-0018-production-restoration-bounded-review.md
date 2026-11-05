# Codex-0018 — Antigravity-0013: major repairs pass, two bounded fixes remain

Author: Codex. Date: 2026-10-08, Asia/Dhaka. Review: targeted static source/test inspection, installed Chroma source reading and native artifact hashes; no tests, inference, diagnostic or Chroma connection executed.

## Verified identities

Script `142da3d8d763c6792cf499c85f30ae34bfa7e2b1f9c998899613c7751b79f9ca`; tests `3844ed1e0552130d201b98fac9ff4a36464219f30b71ef4b19acb322503d6571`; saved log `8bd68cc03d584782d06201acb0857fc847b8155f887a8fa195bb75ce15c2ae4e` independently match. Log reports 15 PASS, 0 FAIL, 1 SKIP; not independently rerun.

## Findings closed at source level

Production eight-point grid and six model-file hashes/sizes match the previously verified evidence-backed constants; historical AUROC reference restored. Offline declaration defaults to UNKNOWN. Lifecycle now calls network-guard restoration. Test 13 uses a temporary tree; unmeasured source identity is explicitly UNVERIFIED. Production-lifecycle malformed-grid and count-discordance tests added. Incident limitation and external historical files are disclosed, not erased. Prior continuous invariance remains withdrawn.

## Two focused corrections

1. Actual cache binding remains name-based. Stage 7 accepts anything whose name is default and unconditionally records delegates_to_onnx_minilm=True. Installed `venv/Lib/site-packages/chromadb/api/types.py` shows the genuine DefaultEmbeddingFunction.__call__ imports `ONNXMiniLM_L6_V2` from `chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2` and instantiates it. Validate the actual installed class identity (DefaultEmbeddingFunction or concrete ONNXMiniLM class), then verify the ONNX class from that exact module and its resolved cache path. Record measured class/module and installed source identities. Reject an arbitrary impostor named default in a synthetic negative test. Keep fake-test allowance separate and absent from production CLI; avoid adding unsupported source-normalization claims.

2. Cleanup test reads a stale Boolean. Test 5 imports `_NETWORK_GUARDS_INSTALLED` by value before the lifecycle and checks the same local immutable value afterwards. That cannot detect a later module-level assignment. Import the module and check `prod._NETWORK_GUARDS_INSTALLED` plus original socket/urllib/httpx callable identities and environment values after success and representative copy/query/report failure. Use finally-protected fixture restoration. Production cleanup is present, but current test does not prove it.

## Execution conditions (not code expansion)

Before seeking user approval, specify the actual external offline arrangement and its evidence; the UNKNOWN default is appropriately honest but is not proof of an enforced offline boundary. Preserve a byte snapshot plus current full-store manifest before an eventual authorized run; original-store clients/overwrites remain prohibited. Retain the explicit absence of pre-incident HNSW provenance. Contemporary concordance cannot authenticate historical execution or authorize replacing line 210.

No further broad rewrite requested: address the two items, provide the small diff and revised synthetic log with hashes. The earlier major regressions are closed; the run still needs these bounded checks, Claude review and explicit user approval. No paid API is needed for the intended verified local-cache diagnostic. No 10k-store extension or manuscript/data change authorized.
