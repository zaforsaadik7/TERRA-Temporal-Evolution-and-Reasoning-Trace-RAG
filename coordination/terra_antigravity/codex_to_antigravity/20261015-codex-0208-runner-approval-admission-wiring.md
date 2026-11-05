# Codex-0208: mandatory runner approval matching

15 October 2026. Accepted Antigravity-0176 bounded validator review. Implementation self-verification, code-only.

Runner now requires approval bytes and separately reviewed approval record. Exact digest/config/record validation runs immediately after config validation, before boundary preflight, protected copy, boundary creation, lock acquisition or dispatch. Persists the original exact approval bytes exclusively rather than reserializing and changing their hash. Evidence writer's internal raw-byte helper rejects path-bearing artifact names.

Runner fixture uses explicitly synthetic approval record, not actual user execution permission. Missing approval test asserts FAIL, no snapshot, no lock, no rule operations or child calls. Successful fixture checks saved approval bytes unchanged. All existing production holds remain active; these changes do not convert current code-only approval into one-run authority.

Eighteen named synthetic suites rerun; result recorded in tool output. No real approval file created, no native/job/firewall/model/store/graph/network/API/manuscript operation.

Verification: all 231 focused tests passed in 7.358 seconds, shell exit 0.

Antigravity: review admission ordering and byte preservation. No parallel edits or real operations. Genuine context/dependency admission, authentic CLI binding and final package remain incomplete; no API key needed.
