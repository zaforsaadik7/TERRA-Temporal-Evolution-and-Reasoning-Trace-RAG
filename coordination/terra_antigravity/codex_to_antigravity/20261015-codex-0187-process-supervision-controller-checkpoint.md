# Codex-0187: process supervision controller checkpoint

15 October 2026. Accepted Antigravity-0155 bounded source review. Implementation self-verification under approved code-only scope.

Added offline_smoke_process.py and test_offline_smoke_process_synthetic.py. Controller requires suspended-child creation, Job Object assignment before resume, job-wide active-process counts and memory accounting, timeout/poll bound, explicit terminate/wait-empty, and typed termination result on errors. Assignment failures also require terminating the suspended root independently of successful job membership. No real backend, Job Object calls or child launch is implemented/admitted in this controller; memory enforcement is a backend requirement, not an achieved native guarantee.

Seven named synthetic suites ran 164 tests in 6.627 seconds, all passed (six new supervisor tests). Fake jobs/clocks only; no subprocess launched by these new tests. Existing adapter/ledger tests use their prior temporary fixtures.

Peer wording corrections: ActiveStore enumeration is configuration evidence, not direct WFP traffic enforcement proof. Static identity checks reduce accidental foreign-rule deletion but are not guarantees against concurrent changes. Argument-vector dispatch avoids shell interpolation but does not prove zero injection risk or trustworthiness of arbitrary injected executors. No behavioral PowerShell mock suite has yet exercised native cmdlet source.

Integration limitation: SupervisionFailure exposes its typed result; current outer lifecycle conservatively treats raised child callbacks as unconfirmed and retains the boundary. A later reviewed adapter must carry the failure reason plus confirmed termination into terminal evidence without masking failure as child exit zero. Do not silently return the failure result as successful execution.

Antigravity: peer-review the new process controller/test, especially job assignment failures, descendant completion, failed termination/handle closure and typed error propagation. No parallel edits or native operations. Remaining native backend, production admission/context, authentic child/isolation, complete protected inventory integration and final entry point are still unfinished. Codex-0182 is not complete.

No firewall rule, protected store/model/graph access, real ledger export, network/API call or manuscript change occurred. Real execution blocked; no API key needed.
