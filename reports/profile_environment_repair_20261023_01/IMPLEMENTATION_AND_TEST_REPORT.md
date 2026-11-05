# Explicit USERPROFILE binding: code-only repair

23 October 2026, Asia/Dhaka. Codex implementation self-verification after user approved the repair and synthetic tests, with no new diagnostic attempt.

## Repair

offline_smoke_bindings.windows_runtime_environment accepts an explicitly reviewed system directory/profile as arguments and returns only PATH, SYSTEMROOT, WINDIR and USERPROFILE. It never reads os.environ or the filesystem and does not import Chroma. A companion validator requires an explicit absolute, drive-qualified, non-root Windows USERPROFILE, rejecting traversal, alternate streams, null/newline characters, variable expansion and UNC/device forms. This is lexical validation; actual directory identity/containment remains a prelaunch preparation responsibility, not a claimed filesystem check here.

The actual production packet decoder now invokes that validator after its existing safe-key/duplicate/PYTHONPATH/PYTHONHOME checks. A packet missing the profile therefore fails during decoding, before native calls, copies or model work. Existing cleaner allowlists already permit USERPROFILE; no change to that allowlist or credential filters was needed. No HOME/PYTHONHOME/PYTHONPATH or arbitrary inherited values were introduced.

runtime_environment.PROPOSAL.json records the intended explicit profile C:\Users\zafor and existing system paths. This is proposal data only, not an executable packet or permission. Future packet preparation must use the helper, verify the reviewed profile directory without inventorying its private contents, and regenerate affected source/driver pins. No used or previously reviewed packet was overwritten. Decoder rejection of those historical missing-profile packets is intentional; they are immutable evidence, not current launch artifacts.

No embedding math, model/cache selection, retrieval algorithm, firewall/process rule, network/credential protection, resource setting, authorization schema or cleanup policy changed. The shared synthetic packet fixture now includes a fake explicit profile so all prior decoder/transport tests exercise the strengthened contract.

## Synthetic evidence

Five new tests: reproduce the original Path.home RuntimeError using actual Path.home/Windows ntpath.expanduser under an empty fake environment; show the explicit profile survives the real CleanChildEnvironmentBuilder and resolves the same import-like default cache expression; prove no ambient profile or fake credential is inherited; reject invalid profile forms; and exercise the real production decoder rejecting a missing profile and accepting the explicit helper binding. No real Chroma import, model file, database connection, firewall or home-directory contents are touched.

An initial focused64-test pass included an imported fixture TestCase being rediscovered. The test imports were corrected to reference the fixture module, avoiding duplicate discovery in the final count. Final authoritative run: exactly30 named modules, **553 tests in22.558s; 551 passed, two skipped, zero failures/errors, exit0**. TEST_RESULT.json lists the modules; synthetic_console.log preserves stdout/stderr. Expected collision/FATAL fixture output is not a test failure. No wildcard discovery. No runtime suites or B001 were dispatched.

## Holds and limits

All admissions remain closed and packet/wrapper anchors null. Old attempt locks and saved evidence remain intact; packaging rechecks the preserved46-file run manifests. Existing source before/final copies and actual source.diff are provided. No new authorization/freeze/attempt, API/credential, actual model/tokenizer/store/native operation, manuscript/statistics change or promotion occurred.

This addresses the environment defect localized in Codex-0257. Synthetic reproduction/resolution does not certify that an authentic run will pass all later stages; the prior attempt stopped before Chroma client creation. Next checkpoint: peer review of code, diff, proposal and tests. No new run command is supplied.
