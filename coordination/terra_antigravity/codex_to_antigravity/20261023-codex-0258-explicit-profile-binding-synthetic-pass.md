# Codex-0258: explicit USERPROFILE binding repair, synthetic PASS

23 October 2026, Asia/Dhaka. User approved code-only profile-binding repair and synthetic regressions following Codex-0257's localized Path.home failure. No new B001 attempt or freeze authorized. Codex implementation self-verification.

Package: `reports/profile_environment_repair_20261023_01/`.
Manifest SHA-256 **9516371eaddebb1b2901ea8d4eaedff955bd99905b9ee258579300e0a5a9c581**.

Read IMPLEMENTATION_AND_TEST_REPORT.md, actual diff/before/final/live sources, proposed environment and test logs. The builder helper returns only explicit PATH/SYSTEMROOT/WINDIR/USERPROFILE from reviewed arguments, without os.environ/filesystem/Chroma access. Shared lexical profile validator rejects missing/non-string/relative/root/traversal/ADS/null/newline/expansion/UNC/device profile forms. Production decoder invokes it after existing safe-key/Python-hook rejection, ahead of native/copy/model operations. Existing cleaner already supports USERPROFILE; no allowlist broadening, credential inheritance or firewall/process relaxation.

Proposal USERPROFILE is C:\Users\zafor, alongside existing system bindings. This is proposal data only; future packet construction must invoke the helper, validate actual profile-directory containment without reading private home contents, and regenerate changed source/driver pins. Historical used packets are not patched/reused. Pure lexical validation here is not a current filesystem identity claim.

Source identities:

- offline_smoke_bindings.py: **e1285774b7750ea71790d10a39374e11ed4b36be03b6eb04d243bb48d6ad0448**
- offline_smoke_production.py: **ab7079ff6db765a94e4f456fd71e5a72dc8fe42f608b2058352d74d41a4812f4**
- test_offline_smoke_runner_synthetic.py: **8c183445cab58638d3945e5c80c36a73d216bde137d68fc5e0f948db60868056** (shared fake packet now has explicit fake profile)
- test_offline_smoke_profile_environment_synthetic.py: **fc9c3d826f9b4656e72be0d2cda37bb5a5902436d1caeaccf1a7b5b4094b75bb**

Five new synthetic tests reproduce actual Path.home/ntpath failure under fake empty environment, demonstrate fixed import-like cache-path resolution through the real cleaner, reject invalid profiles, exclude ambient credentials/profile, and exercise actual decoder rejection/acceptance. No real Chroma import or private home contents. An initial focused run rediscovered an imported TestCase; fixture import was corrected before final accounting. Authoritative full **30 named modules:553 tests /551 passed /two skipped /0 errors/failures,22.558s, exit0**, console and module list preserved. Expected collision diagnostics are negative fixtures, not suite failures.

No new application module added to runtime closure; bindings/driver identities change. All holds/anchors remain closed; saved failed-run46 files reverified and used locks retained. No actual runtime/model/tokenizer/store/native/firewall/API/credential/manuscript/statistics/promotion work or B001 retry. If undertaking an approved peer test rerun, please use pinned venv Python **-B** and the exact30 module list to avoid cache churn/discovery.

Please peer-review actual diagnosis (Codex-0257) and repair/test scope, especially explicit profile propagation and unchanged credential/network safeguards. This fixes the known environment defect, not a guarantee that all later runtime stages pass. No parallel implementation or automatic notification assumed; user relay only.
