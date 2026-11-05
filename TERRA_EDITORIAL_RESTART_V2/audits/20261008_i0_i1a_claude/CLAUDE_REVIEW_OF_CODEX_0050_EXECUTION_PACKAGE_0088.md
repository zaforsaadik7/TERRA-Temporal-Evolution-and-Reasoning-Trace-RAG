# Claude review of Codex-0050 / Codex-0029 / Antigravity-0025: execution package and firewall runbook (claude-0088)

Reviewer: Claude. NOT independent (Claude wrote the Batch 1-28 text). Static only. I did not run the tests, the wrapper or the diagnostic, I queried no firewall, and I opened no Chroma store. Coordination is user-relayed; I have no live channel to Codex or Antigravity.

## 1. Package identity: reproduced

I rehashed every file in `reviewer_I0_I1a_20261008/execution_package/` and the live copies in `scripts/`.

| File | SHA-256 (mine) | Matches manifest / claim |
| --- | --- | --- |
| audit_i1a_contemporary_gate_calibration.py | c37ddaa72ab5...67094d | yes (62,968 B) |
| run_diagnostic_harness.py | b7f59c413178...def6ce25 | yes (78,073 B) |
| test_audit_i1a_mocked_safeguards.py | ecd894be95c5...852aeb | yes (61,552 B) |
| test_run_diagnostic_harness.py | d32f5dd6ef9f...7f817dc | yes (69,151 B) |
| diagnostic_7cd926_to_c37dda_exact.diff | b3e1126d5be4...63c282a | yes (4,678 B) |
| execution_package_manifest.json | ac9180143e84...2670bdd | yes (2,743 B) |

The four code files in the package are byte-identical (`cmp`) to the live files under `scripts/`. So the package is a faithful copy of what the live paths hold today. I did not hash the interpreter, the benchmarks, the store or the snapshot manifest in this pass; their values below are quoted from the manifest.

## 2. Findings

**F1. "Frozen" is not established (agree with Codex).** Antigravity-0025 calls the package "immutable". Codex reports ReadOnly=false on every file and a builder that overwrites with `exist_ok=True`/`copy2`/`write_bytes`. I could not check attributes or the builder from here, but nothing in the evidence contradicts Codex, and the claim is not supportable as worded. It is a hash-verified preserved copy. Never rerun the builder over that directory. Corrections go in a new versioned addendum, not an overwritten manifest.

**F2. The package is not what executes, so protecting it is not enough.** The command runs the live `scripts/` files (their workspace root is derived from `__file__`; Codex is right that a copy would derive a different root). The control that matters is therefore a rehash of the live wrapper, diagnostic and interpreter against these pins immediately before launch, plus the post-run rehash. Read-only attributes on the live files are a convenience only, since they are trivially reversible. Add that the wrapper's pin covers the diagnostic (PINNED_DIAGNOSTIC_SHA256) but the wrapper does not pin itself, so the pre-launch rehash of the wrapper has to be done by the person or a separate step. A small window remains between rehash and launch; the post-run rehash is what closes it after the fact.

**F3. Manifest command is superseded.** The manifest still records the relative form `... python.exe scripts/run_diagnostic_harness.py ...`. Codex-0029 supplies an absolute, quoted form with the call operator. I agree the absolute form should be the one authorized, and the manifest should be left as an accepted record with the corrected command in an addendum. Note the wrapper itself builds its child command with `--workspace-root` and `--onnx-cache-dir` (its own code, around line 1100), so the authorized command line is the wrapper's, not the child's; the run record should capture the child command the wrapper prints.

**F4. Python version 3.14.3 is not measured (agree).** The manifest's `version` is hard-coded prose. The wrapper checks the interpreter path/hash and library versions (chromadb 1.5.9, numpy 2.5.1, onnxruntime 1.27.0), not the Python version. The diagnostic does write `sys.version` into its report (line ~1063), so the real version will be recorded at the execution boundary without a separate probe. The post-run audit should compare it with the manifest and flag any mismatch. Treat the executable hash as authoritative until then.

**F5. Firewall rule identity (agree, and stronger).** Creating and removing by DisplayName `TERRA_Offline_Diagnostic` can match, or delete, unrelated rules. Required before any installation: one frozen unique internal `-Name` (for example a name containing a date and a random suffix fixed in advance and written into the runbook); a pre-check that no rule with that Name or that DisplayName exists, stopping if one does; capture of the created rule's full configuration (enabled, outbound, Block, program path, all profiles); removal by that exact Name only, inside a `finally` that also runs on failure, with a post-removal check that the rule is gone; and a recorded cleanup result. Never use wildcards or remove by DisplayName.

**F6. The declared condition is a label, not evidence.** The wrapper accepts `TERRA_Offline_Diagnostic` from a whitelist and only checks that the child report echoes the same string (lines ~1002, 575-588); its own report text says it "does not establish or prove external network firewall enforcement". Two consequences. First, the whitelist also contains `TEST_OFFLINE_FIREWALL`, a test value accepted in the production path, so the wrapper alone cannot tell a real run from a test declaration. Second, if the rule gets a new unique internal Name, the declared label should remain the whitelisted string while the real rule Name, configuration and enforcement evidence are recorded separately in the run evidence. Do not edit code to change this (the code gate is closed); record it as a limitation and capture rule evidence in the runbook.

**F7. Over-claims to avoid.** The rule blocks outbound traffic for that interpreter, so it also affects any other process on the machine that uses that same `python.exe` while it is active. Antigravity's "fully preserves ... cloud agent sessions" and "strictly guaranteeing zero network access" are too strong: the rule has not been tested here, loopback or already-open connections may behave differently, and actual enforcement must be verified on the machine. If any tooling used by the user or other agents runs under that Python, it will lose network for the duration. The user should decide knowing that. I cannot see which tools use it.

**F8. Elevation and approvals.** Creating and removing the rule needs an elevated session. The runbook should name who runs the elevated commands and when, and should require the user's explicit approval for the install and for the removal as separate steps. Option B (disconnecting) remains available but ends cloud sessions, including this one.

**F9. Window of exposure and cleanup on failure.** If the diagnostic fails or the machine loses power mid-run, the rule can stay installed. The runbook should include a manual removal check (by exact Name) as part of the post-run audit, and the same for the single-run lock, which by design is never deleted.

## 3. Verdict

Package byte identity: PASS (reproduced). Code gate: unchanged, not reopened. Operational runbook: NOT YET READY to present for single-run permission. Required first: a corrected runbook that fixes F1 wording, uses the absolute quoted command, adds the unique-Name firewall procedure (F5), records the F6 and F7 limitations, and defines the pre-launch live rehash, the post-run rehash and rule-removal verification. Preservation evidence must be added as an addendum.

## 4. Not verified

File attributes (ReadOnly) and the builder's overwrite behavior (from Codex, not seen by me); the interpreter and library versions; the benchmark, store and snapshot hashes in this pass; the 45-test log; the firewall state. Windows Firewall behavior is untested.

## 5. Boundaries

No run, firewall installation or removal, network change, 10k run, API call, threshold tuning, manuscript edit or promotion is authorized. Line 210 calibration stays OPEN. The user's offline-arrangement choice, dated authorization and separate single-run permission are all still outstanding. Relaying this to Antigravity is the user's.
