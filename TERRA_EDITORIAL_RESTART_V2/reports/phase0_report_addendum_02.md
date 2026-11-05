# Phase 0 report — Addendum 02 (minor qualifications from codex-0007)

- Author: Claude
- Date: 2026-09-28
- Scope: Phase 0 bookkeeping only. No manuscript, archive, statistics or data file was touched.

## D1. The "70 years" subcount in Addendum 01, C6 — definition corrected

The 70 are the R26 digit-run tokens that **exactly equal a 4-digit number in 1800–2099**, regex `(1[89]|20)\d\d\s?` applied to each of the 1,331 tokens. This is a *year-shaped token* count, not a count of years used as years. It includes:

- run dates ("2026" ×13);
- range endpoints ("1850", "1980" ×12);
- venue years ("NAACL 2025").

Codex's 58 "standalone year tokens" and 63 broad `19xx`/`20xx` matches use different rules; none of the three is wrong under its own definition. I therefore withdraw "of which 70 are years" and replace it with "70 year-shaped tokens under the rule above". The 1,331 total is independently reproduced and remains an upper inventory count, not a tally of erroneous values.

## D2. Reproduction script is now fail-closed

`builds/phase0/scripts/reproduce_phase0_builds_v2.sh` supersedes v1 as a PASS/FAIL check. v1 is kept unaltered as the delivered record. Changes:

- `-halt-on-error`;
- no `|| true` error masking;
- a missing PDF fails the build;
- each PDF SHA256 is compared with the expected value;
- the script exits non-zero on any failure.

Evidence from this sandbox:

| Test | Result |
|---|---|
| Clean run | 4/4 PASS, exit 0; hashes identical to the stored PDFs |
| Negative test 1: one expected hash tampered | `FAIL B2 …`, `OVERALL FAIL`, exit 1 |
| Negative test 2: undefined control sequence injected into B4 | `FAIL B4: build exit 1`, `OVERALL FAIL`, exit 1 |

This remains valid only for the recorded TeX Live 2023/Debian toolchain.
