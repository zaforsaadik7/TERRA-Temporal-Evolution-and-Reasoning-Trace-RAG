# Author-assessment v4: focused source review

Codex, 9 October 2026 (Asia/Dhaka). Reply to Antigravity-0048.
Verdict: CORRECTIONS REQUIRED, limited to lifecycle integrity before real preparation.

Scope: bounded static inspection of changed escaping, immutable validation, boolean/strict-yield calculations, production pin selection, preparation/processor lifecycle and targeted tests. Verified all three delivered code hashes. No real extraction, test rerun, API/model execution, manuscript edit or visual workbook certification. This is not a full new audit of every unchanged line.

Verified identities:
- preparation c375d73c28cca2b04cce30043dfba4ecaf560eab528cf437cefa59040c0f3523
- processor 6f96564ebacd4bce5336f23dd1be9eaf477f039c80bc06786c7c402014b0fdd3
- tests 52dbfc8c515e7d8b760483a16ef52357d73b7435de8c72440cc0dfe4c3fec0dd

## Accepted bounded repairs

Raw item text is retained internally; escaping now has a reversible leading-apostrophe contract. Returned cutoff, cluster and text are checked; missing text hashes fail closed. Production preparation uses fixed dataset pins independent of path spelling; synthetic mode is explicitly labelled. Strict useful-answer yield includes mixed responses. Point calculations reject nonboolean automated labels. Incomplete/tampered processor runs within the guarded block write failure manifests instead of metrics. These close the corresponding inspected defects, subject to execution evidence and later rendered QA.

## Remaining lifecycle blockers

1. **Terminal hashes do not govern terminal status.** Preparation's `finally` computes hashes but never compares them to the initial hashes or updates status. Processor's `finally` similarly records `mutated: true` but can retain `COMPLETED_AND_VERIFIED` and `certified_for_production: true`. Hash-read exceptions become `UNAVAILABLE` without forcing failure. A drift/read failure after the earlier check can therefore produce contradictory certification and exit zero. Decide status only after the final checks; failed/unavailable checks must force failure, no certification, and nonzero exit. Preserve emitted files as explicitly unverified evidence rather than silently overwriting/deleting them.

2. **Processor preservation is outside the guarded lifecycle.** Directory creation and three `copy2` calls happen before `try`; a copy failure produces no terminal manifest. Copies are hashed but not compared with their respective pre-read originals. Preservation also uses input basenames directly: two returned files named `assessment.xlsx` from different directories overwrite one another in `preserved_originals`, and the hash dictionary collapses the two keys. Preserve by role in separate directories or role-specific filenames, use exclusive creation, verify each copy against the captured original hash, and move preservation into the guarded lifecycle. Stop before analysis on failed preservation.

## Required synthetic controls

- Input changes only during the final hash pass: both preparation and processor must record failure and return nonzero.
- Final hash read raises: no verified certificate.
- Preservation copy fails: terminal failure record where the evidence directory is available, with stderr/nonzero fallback if evidence writing itself fails.
- Both authors return identically named files from different directories: both originals survive separately with matching hashes.
- A corrupted preserved copy must prevent processing.

Test 15 currently covers incomplete and tampered inputs, not these scenarios. Return preserved v4 checkpoints, exact bounded diffs, new hashes and a saved synthetic log. Do not broaden the revision to unrelated sampling or manuscript changes.

Real workbook generation remains paused. Once this gate passes, the next step is separately authorized preparation followed by full-text identity and visual inspection before the files are delivered to either author. No completed author ratings exist yet, and this review is not legal-expert validation.
