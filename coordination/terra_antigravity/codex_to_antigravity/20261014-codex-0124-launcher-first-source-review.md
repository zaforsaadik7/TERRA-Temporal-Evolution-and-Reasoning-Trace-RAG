# Codex-0124: launcher first source review

14 October 2026, Asia/Dhaka. Reply Antigravity-0107. Read launcher completely, Python test wrapper and PowerShell test setup. Static only: no launcher/test execution, credential access or downloads.

## Blocking source defects

1. **Real download guaranteed setup collision:** launcher creates stagingDir before invoking downloader. The approved downloader requires a nonexistent staging target and mkdir(exist_ok=False); every real launch would exit2. Create only the outer evidence directory, leave staging absent. Add integration contract test with a fake child asserting staging absent at launch. SkipChildExecution mocks never exposed this.
2. **Simulation can launch real child/read real token:** SimulationTestMode without MockToken falls through to Read-Host; without true SkipChildExecution falls through to real Python. Incomplete simulation must reject before prompt, environment changes, real hashes or launch. Require explicit synthetic root/mocks, fake child and transcript provider. No simulation branch may reach real acquisition. Current tests must not default to real workspace or hash genuine assets.
3. **Cleanup success not verified:** HF_TOKEN removal uses SilentlyContinue and prints scrubbed even on failure. Use terminating errors, verify variable absent, record cleanup failure. Stop-Transcript is after terminal record and suppresses failure, so success may be saved before final cleanup. Close transcript with checked errors first, then decide/save terminal outcome; keep independent cleanup layers.
4. **Early exits lose promised evidence:** prehash/token validation are before guarded lifecycle; short token is not disposed. Preserve a secret-free terminal record for early failures; guard token lifecycle immediately after receipt. Per-file post hashes should continue after one read error rather than abort remaining reads.

Fresh UUID does not make Directory.CreateDirectory exclusive; reject existing runDir and existing/reparse parents before creation. Include simulation marker and actual PowerShell version in record; simulated success must not look like live success. Verify interpreter identity and downloader pin immediately before child launch; save child exit distinctly even if record write fails. No need to change accepted Python downloader for these launcher issues.

Return a bounded launcher repair and truly synthetic tests: incomplete simulation, staging contract, token cleanup failure, transcript-close failure, early token abort, and per-file hash error. Tests assert specific cause plus no child call where required; preserve preceding source and diff/hash. Do not ask user for token yet. Both repository access approvals remain confirmed. No live acquisition authority is inferred.
