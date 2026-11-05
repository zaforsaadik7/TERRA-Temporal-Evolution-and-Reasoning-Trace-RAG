# Codex-0207: exact approval-record validator

15 October 2026. Accepted Antigravity-0175 bounded report gate review. Added offline_smoke_approval.py and test_offline_smoke_approval_synthetic.py under code-only scope; implementation self-verification.

Validator checks bounded bytes/digest, duplicate-free exact JSON fields and equality against a separately reviewed record; binds approval ID/date/scope/command/query hash/offline condition/rule/limits to frozen config. Enforces exactly one attempt, rule creation/removal permission, no API calls and no manuscript changes, with strict bool/int separation. This is a source component for the parent admission gate, not yet wired into the runner or a production CLI.

No actual approval file written or execution authority inferred. Expected hash and reviewed record must come from the human-approved external packet; supplying the candidate record to both inputs proves no human origin. Current user's code-only approval is not converted into run permission.

Eighteen named synthetic suites ran 230 tests in 7.091 seconds, all passed. Five new approval tests include broader-scope, wrong-query, changed-reviewed-record and invalid-date rejection. No real filesystem/runtime/model/store/firewall/network/API/manuscript action.

Antigravity: review approval matching and limitations, code-only named tests. Remaining parent admission wiring, full native/asset context, authentic loader/worker/CLI integration and final execution packet are unfinished. No API key needed.
