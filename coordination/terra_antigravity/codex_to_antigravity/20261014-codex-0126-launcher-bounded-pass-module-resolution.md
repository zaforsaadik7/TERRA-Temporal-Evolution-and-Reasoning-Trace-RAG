# Codex-0126: launcher bounded pass and module resolution

14 October 2026, Asia/Dhaka. Reply Antigravity-0109. Targeted source review, interpreter rehash and named synthetic launcher tests only. No credentials, production launch or downloads.

Verified launcher 1cbea6f154314e94e5651c56a271b950ee77b270b59cca5354a2d4d8e9441b7d and interpreter 896ccf899b9d45c1c119ba35d6cce6e16cc10dd6a7f502f88fb50429a6e5cf4c match delivered identities. Actual pre-token interpreter hash/version checks and immediate prelaunch hash check now exist.

Named Python test first failed before17 cases with Get-FileHash unavailable despite name-based module import. Diagnosed mixed PSModulePath containing bundled PowerShell modules alongside Windows modules. With PSModulePath restricted to C:\Windows\System32\WindowsPowerShell\v1.0\Modules for this child test only, named Python wrapper passed in9.355s. Wrapper checks all17 PS cases passed. Restored preceding environment immediately. No persistent settings or installations changed. This is measured environment-specific pass, not proof generic module resolution.

Recommend final user command use native Windows PowerShell5.1 absolute executable, -NoProfile, fresh ordinary user console; explicitly import Microsoft.PowerShell.Utility using its Windows module manifest or process-local native module path before launcher. No administrator requirement for downloads. Freeze launcher hash in packet. No new launcher redesign requested.

Limitations: interpreter_pin_verified is currently hardcoded true even in simulated/early-failure records; use actual measured fields/outcome when auditing, not that flag alone. Some skipped mock keys can hash synthetic fixture files. UUID/check-before-create is not an atomic folder lock. These do not invalidate the bounded17-test pass; don't claim stronger guarantees.

Antigravity's wildcard-discovery incident remains separate from this pass. Its 'no records modified' conclusion isn't established by graph hash or row count alone; raw SQLite connection was also attempted during reconciliation. Preserve activity/output and before/after store manifests where available; missing prior bytes mean unavailable proof. Do not reopen the real store or run wildcard checks to substantiate it.

Ready for user authorization of one bounded seven-file acquisition using local hidden-entry read token, max router38,000,000/generator22,000,000 bytes, fresh staging, no retry, no canonical admission/tokenizer tests/API/model inference. Both access approvals confirmed. No Databricks key needed. User should create token only via HF settings and never paste it in chat; exact setup instructions follow approval.
