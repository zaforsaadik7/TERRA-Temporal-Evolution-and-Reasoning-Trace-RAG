# Codex-0186: Windows boundary adapter source checkpoint

15 October 2026. Accepted Antigravity-0154's bounded peer review; continued user-approved code-only implementation. Self-verification, not independent audit.

Added offline_smoke_windows_boundary.ps1 (native operation source), offline_smoke_windows_backend.py (mock-only dispatch), and test_offline_smoke_windows_backend_synthetic.py. PowerShell operations enumerate ActiveStore matching rule identities, reject duplicates, verify application-filter cardinality, and require matching ownership tag/program/direction/action/profile/enabled state before removing a matching PersistentStore rule. Environment inspection returns elevation/service/profile/known interpreter process facts and unreadable-process count without command lines. Source is not an admitted operational adapter yet.

Python backend builds an argument-vector command with base64 JSON identity, no shell interpolation; validates response JSON, rule/program binding and exit-code type; refuses production construction. No real executor is supplied. Fake tests do not run the PowerShell adapter.

Verification: six explicitly named suites (Windows backend, boundary, evidence, lifecycle, offline adapters, master launch ledger) ran 158 tests in 6.540 seconds, all passed. PowerShell AST ParseFile reported no syntax errors; parsing did NOT execute the source. No native firewall property checks are claimed as tested. Existing driver remains unchanged.

Hashes:
- offline_smoke_windows_boundary.ps1: c70bc408b320bfb3b413996f440152c7855ceb4c3bcc673151576ef2c7dca955
- offline_smoke_windows_backend.py: e29cbdc3d891347be880643a278b2fb1b77885b51a412938dbbe6bb4c3877018
- test_offline_smoke_windows_backend_synthetic.py: 40f1a3748b16c9e52017e34fed43b342d768a372ef83f6331b3cac6ce0910daa

Peer wording correction: retaining a boundary avoids deliberately reconnecting an unconfirmed child, but does not prove the native firewall is effective. Concrete evidence and manual recovery remain necessary. Current fake rule identity is not cryptographic ownership, nor is exclusive creation WORM immutability.

Next peer review: inspect these three new files, especially ActiveStore/PersistentStore consistency, duplicate handling, ownership recovery and normalized property values. Do not run native operations or edit overlapping files in parallel. Current tests verify Python dispatch only; PowerShell behavioral mocks and integration coverage remain outstanding.

Remaining batch: process-tree supervisor/memory enforcement policy, real scope/config validator, guarded authentic child/entry point, complete protected inventory integration, durable manual recovery evidence and final negative coverage. Real runs and real ledger export stay blocked. No rule/database/model/network/API/manuscript operation occurred; no API key needed.
