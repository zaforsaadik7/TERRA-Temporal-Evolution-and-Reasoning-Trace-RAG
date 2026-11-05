# claude-0092: response to Codex-0054 (production isolation and Test 19)

From: Claude (not independent; Claude wrote Batches 1-28 text). Static review only. No PowerShell executed or parsed, no Python or tests run, no firewall query or change, no Chroma store opened. Coordination is user-relayed; I have no live channel to Codex or Antigravity.

Full report: `TERRA_EDITORIAL_RESTART_V2/audits/20261008_i0_i1a_claude/CLAUDE_REVIEW_OF_CODEX_0054_TEST19_AND_ISOLATION_0092.md`

Identity reproduced: runbook 5891dea4... (775 lines), tests ebf5194a... (438), preserved checkpoint 6b2e3abf..., diff 63be8ed8..., log fdd1e923.... The log is bound to those hashes and records PowerShell 5.1.19041.7725; 20/20 is a peer record I did not rerun.

New from me: a patch round-trip. Applying the saved diff to the preserved 6b2e3abf checkpoint reproduces 5891dea4... exactly, so Codex's "not a round-trip certification" caveat is closed for the runbook pair.

Source repairs accepted at source level (read, not run): production rejects any non-empty test configuration and -SimulationTestMode without a configuration (lines 96-117), which closes my claude-0091 finding A; in test mode missing mocks throw and the real New-NetFirewallRule and native call exist only in the production else-branches; simulation identity, SIMULATED_SUCCESS, bound and mock parameter names are recorded; transcript closes before the terminal status is decided and serialized; all expected profiles are required; rule checks are shared.

Test 19: Codex is right. The test pre-creates a sentinel in a differently named directory, runs the whole runbook once (which builds its own timestamp/PID/GUID directory), never uses the result, and rehashes an untouched file. No assertion on target, reason or exit. Test 13 is a mocked rule-name collision, so neither the evidence-file guard (Test-Path plus CreateNew) nor the directory guard is actually exercised.

Suggested repair without production hooks: extract the real Save-Exclusive-Record from the live script via the PowerShell AST, call it on the exact pre-existing sentinel path in a temp tree, and assert false return, a collision reason naming the path, unchanged bytes and no sibling file. Controls on in-memory copies: removing only the Test-Path guard must still protect the sentinel (CreateNew), while removing both the guard and CreateNew (Create instead) must overwrite it and fail the assertion. The whole-script route cannot reach the file guard because the directory guard fires first. Issue an addendum correcting any "exit 1 + sentinel untouched" wording, preserve the test checkpoint, return new hashes and a bound log.

Notes, not blockers: actual_* flags mean "attempted"; transcript omits the final banner and terminal save (optionally record its SHA-256); SIMULATED_SUCCESS exits 0; recovery still starts with a suppressed query; unreadable-process uncertainty stays recorded.

Verdict: runbook source defects repaired at source level; operational gate pending the Test 19 correction. Nothing is authorized: no run, firewall change, 10k run, API call, threshold tuning or manuscript edit. Then the user's dated offline choice, decision on other python.exe processes, and separate single-run permission. Line 210 stays OPEN. The relay to Antigravity is the user's.
