# Codex-0158: Stage 3D third integration audit

14 October 2026. Source review plus named synthetic preflight modules only. Driver 4b7672ebac2dbe1706aa5d7030b0ae606b49bec0c4f829fcd7ca813ead824dc6 and integration tests 44b473547f4b07e58e5d041a5131ca4e9327158c30ee12f15b0c9b422628a35b match Antigravity-0133. Codex run: 73 tests, 72 passed, one skipped, no failures, 3.012 s.

Accepted: authentic factory now rejects explicit injections and unknown modes; verifier sharing enforced; driver passes expected_pins to pre/post inventory; pre-audit failures halt before copies; requested canonical factory failures no longer silently default to mocks. Production still unconditionally blocked; no real run permission requested.

One narrow mock-identity correction remains: authentic factory checks is_synthetic_mock and class-name prefix Mock, but LocalFastTokenizer's actual marker is is_synthetic. A tokenizer declaring is_synthetic=True under an unrelated class name is currently accepted if supplied through a patched constructor. Use the real marker and require explicit false (missing marker must not count as verified authentic identity); remove class-name reliance as proof. Add synthetic negative tests for is_synthetic=True and absent marker on a non-Mock-named fake, plus positive patched construction with explicit is_synthetic=False. No real tokenizer loading needed.

For the later execution packet, require exact full-path pins for the complete production inventory; current canonical defaults use basenames and are only a starting set. Do not claim those defaults alone pin all executed modules, ONNX/cache assets and individual tokenizer files. User-supplied pins must be frozen in a reviewed launch artifact before any production hold is lifted. This is a future packet requirement, not authorization to measure or open real stores now.

Return tiny source/test diff, identities and named logs under existing code-only approval. All other accepted repairs stand. No keys/network/models/store/manuscript activity authorized.
