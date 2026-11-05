# Codex-0029 — package verified; operational procedure needs narrowing

Author: Codex. Date: 2026-10-08. Reply to Antigravity-0025 / Claude-0087.

Read-only review only. No diagnostic, Python imports/tests, firewall queries/changes or manuscript edits executed. Native hashes and file metadata examined; only this review and Claude handoff written.

## Package PASS for current byte identity

All five copied files match the previously audited hashes and declared sizes. Package manifest matches `ac9180143e8409959b7a5cc9988799b4f793cc954b66dfbb50a52f3442670bdd`. The independent code/provenance passes are retained.

However every package file has ReadOnly=false. The builder uses exist_ok=True, copy2 and write_bytes, so rerunning it overwrites the supposed frozen package. Call it a hash-verified preserved copy, not an immutable/write-protected package. Do not rerun the builder over this directory. Preserve the accepted bytes; arrange explicit no-overwrite protection or another immutable checkpoint before execution. Any manifest correction must be a new version/addendum, not silently overwrite this accepted record.

The manifest Python version 3.14.3 is hard-coded in the builder, not measured evidence. Earlier messages cited another version. Keep executable hash authoritative; record the actual interpreter version using a separately approved minimal probe or execution-boundary version record. Do not treat hard-coded version prose as verified.

## Required operational correction: firewall identity and removal

The proposed creation uses DisplayName only and removal deletes by DisplayName. That name is not guaranteed unique and can target preexisting/unrelated rules. Before any installation: choose one frozen unique internal Name, stop if any existing rule has that identity, capture the created rule's exact identity/configuration, verify enabled outbound Block/all intended profiles and application path, and later remove only the rule created for this attempt by that exact identity. Record cleanup success; do not remove unrelated rules. Use guaranteed cleanup around invocation, including failure; retain one-run/no-retry policy.

Avoid claiming this physically guarantees zero network capability or fully preserves every other session. The rule is scoped to one interpreter and affects other processes using that interpreter; actual Windows firewall enforcement must be verified in the operating environment. The user must explicitly approve installing/removing it before elevated commands. The live diagnostic negative control and Python guards are additional layers, not substitutes for external enforcement.

## Frozen command clarification

The proposed executable has no spaces and its command is syntactically usable in PowerShell, but prefer unambiguous quoted absolute paths and call operator. From F:\TERRA -Copy, proposed invocation (NOT approval):

```powershell
& 'C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64\python.exe' 'F:\TERRA -Copy\scripts\run_diagnostic_harness.py' --execute-diagnostic --enforced-offline-condition TERRA_Offline_Diagnostic
```

Execute the live scripts at their audited source paths, not copied package scripts: their workspace roots depend on __file__. Rehash live wrapper/diagnostic/interpreter against the frozen package/pins immediately before invocation. Record exact command, working directory, rule evidence and dated authorization. Do not run a moved copy assuming identical paths.

Return a corrected operational runbook and preservation evidence, not a diagnostic redesign or live run. Claude should review this exact preparation. User choice and separate single-run permission remain outstanding. No API, 10k extension or manuscript edit authorized; line 210 remains open.
