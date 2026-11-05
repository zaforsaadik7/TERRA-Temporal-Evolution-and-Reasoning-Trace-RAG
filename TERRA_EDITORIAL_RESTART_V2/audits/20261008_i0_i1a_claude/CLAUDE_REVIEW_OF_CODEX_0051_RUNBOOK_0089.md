# Claude review of Codex-0051 / Codex-0030 / Antigravity-0026: hardened runbook (claude-0089)

Reviewer: Claude. NOT independent (Claude wrote the Batch 1-28 text). Static only. I ran no test, wrapper, diagnostic, Python probe or firewall query, and opened no Chroma store. Coordination is user-relayed; I have no live channel to Codex or Antigravity.

Read: Codex-0051, Codex-0030, Antigravity-0026 (runbook text in its section 4), and the staged wrapper source for the version claim in item 5.

## 1. Accepted improvements

Unique internal rule Name with the same DisplayName; collision check before creation and outside the `try`; `-Profile Any -Enabled True`; quoted absolute command at the live `scripts/` path; pre-run rehash of interpreter, wrapper and diagnostic; `try/finally` teardown with a removal check. ReadOnly attributes on the six package files and removal of the builder are accidental-overwrite protection only (I did not check them; Codex did). They can be cleared, so hash checking stays the real control.

## 2. Codex's three remaining corrections: I agree with all

1. **Cleanup ownership.** `finally` removes by the fixed Name unconditionally. The collision check sits outside the `try`, so a collision does abort before it, but if `New-NetFirewallRule` itself fails partway or an identically named rule appears between check and creation, `finally` could delete a rule this run did not create. Track a `$created` flag set only after creation returns, keep the returned rule's identity, and remove only when it is true. `-ErrorAction SilentlyContinue` on removal and on the post-check hides access or query errors; an error is not proof of absence. Cleanup failure must be a failed operational outcome, not a warning.
2. **Enforcement checks are thin.** The runbook checks only `Action` and `Enabled` on the rule object. Direction, profile coverage and the program path live partly on the associated application filter (`Get-NetFirewallApplicationFilter`) and should be read back. Also required: that the firewall profiles are actually enabled and the Windows Firewall service is running. A third-party firewall or disabled profile would leave a correct-looking rule with no effect. If enforcement cannot be confirmed, stop before launching Python.
3. **Exit code and after-hashes.** Native nonzero exits do not trigger `$ErrorActionPreference = "Stop"`. Save `$LASTEXITCODE` immediately after the single invocation, keep it separate from cleanup status, and never let a successful cleanup mask a failed child or the reverse. Step 5 only prints text. Rehash the live wrapper, diagnostic and interpreter after the run (also after failure) and compare to the pins. The wrapper does not hash its own source, so this is the only check on it. Save console, firewall and hash evidence to a unique no-overwrite record directory.

## 3. Additional findings from me

4. **Python version claim is overstated.** Antigravity-0026 says Runtime Gate 2 records the interpreter version in `execution_metadata.json`. In the wrapper source, the Gate 2 probe (line ~158) prints only chromadb, numpy and onnxruntime versions; I found no `sys.version` or `--version` in the wrapper. The only place the interpreter version is written is the diagnostic's own report (`sys.version`, line ~1063). So the version will be captured at run time only through the child report. The "3.14.5" figure is peer-reported from a `--version` call; 3.14.3 stays as superseded manifest text, corrected by addendum. The post-run audit should read `sys.version` from the report and compare it with whatever version the user accepts.
5. **Runbook prose and script disagree.** Section 3 says the benchmarks and the SQLite file are re-verified immediately before launch. The script's Step 1 hashes only the interpreter, wrapper and diagnostic. The other inputs are checked inside the wrapper's own gates. Either add them to Step 1 or say so; do not claim more than the script does.
6. **No administrator check.** Rule creation needs elevation. With `$ErrorActionPreference = "Stop"` an unelevated session fails at creation, which is safe, but the runbook should check elevation first and say who runs it, and the user must approve the elevated install and the removal as separate steps.
7. **Leftover-rule recovery.** If a failed earlier attempt leaves the rule in place, the collision check will abort every later attempt. Define a manual removal-by-exact-Name step and when it is allowed. The same applies to the never-deleted single-run lock: define that the lock stays and that a second attempt needs a new, reviewed approval.
8. **Firewall-profile and service state, and other users of the interpreter.** Beyond item 2, Codex asks for a read-only check of other running processes that use the pinned `python.exe`. I agree; the user needs that list before choosing, because the block affects all of them. I cannot see which tools run under that Python.
9. **Over-claim remains.** Section 2.7 still says the rule "physically prevents outbound socket connections" and that the Stage 1 socket probe "confirms" it. The rule is untested, and the Stage 1 probe is a Python-level guard, not firewall proof. If the user wants independent evidence, an optional, separately approved single connect attempt from the pinned interpreter would be needed; I do not propose adding one without approval.
10. **Transcript.** Add `Start-Transcript` to a unique no-overwrite path so the console is kept even if the wrapper fails before it writes its own log.

## 4. Verdict

Runbook direction ACCEPTED; runbook NOT YET READY for authorization. Required: a corrected runbook that implements Codex's three corrections plus items 4 to 10, then re-review by Codex and me. No code gate is reopened. I did not verify the file attributes, the firewall state or the Python version.

## 5. Boundaries

A runbook is a proposal, not authorization. No run, firewall install or removal, network change, 10k run, API call, threshold tuning, manuscript edit or promotion is authorized. Still needed from the user: offline arrangement choice with a dated authorization, and separate single-run permission. Line 210 calibration stays OPEN pending the post-run audit. Relaying this to Antigravity is the user's.
