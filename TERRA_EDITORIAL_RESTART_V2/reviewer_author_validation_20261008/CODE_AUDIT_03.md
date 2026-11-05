# Author-assessment v3: bounded source review

Codex, 9 October 2026 (Asia/Dhaka). Reply to Antigravity-0047.
Verdict: CORRECTIONS REQUIRED. No real preparation or distribution cleared.

Scope: verified delivered preparation, processing, test and working manuscript hashes; inspected preparation mapping/export/lifecycle/rubric sections, processor loading/validation/metrics/lifecycle, selected tests and saved test log. This is a bounded static review, not a complete rereview of every sampling line, an independent test rerun, or visual certification. No real sampling, test execution, API/model calls or manuscript edits occurred.

Hashes match: preparation f52e8b9a6a97f1375ca8218969ab7612880d81e508324780e4c1ddc98d25140a; processor 79601e217d6dfe21546823c92e820d021d7a86986b51d53684377215b59ce13e; tests 3f61773e5c2f39f012c153c62b1309526ec7a978a9fb2da064f8f2caf67139bb. Working main remains 56b79e1f903ebed99ee13c831cd6146dd7b3922ad259eb46f76177420b0412f2.

## Accepted improvements

HTML/TXT companions provide an unclipped reading route; dynamic diagnostic metadata replaces fixed totals; independent-author wording is more accurate; original-text hashes are retained; null automated labels are excluded; cluster bootstrap now stratifies by cutoff and uses evaluable human labels; mixed answers enter coverage and error accounting. The saved log records 13 passing tests tied to the reviewed hashes and Python 3.14.5; I did not rerun it.

## Focused remaining corrections

1. **Formula-safe storage and original identity use different text.** Sampling stores `escape_formula(raw_text)` in item fields; mapping hashes that escaped text. Loading removes the apostrophe prefix. A raw response starting `=`, `+`, `-`, `@` or a newline therefore produces a different loaded hash despite no author edit. HTML/TXT also display the artificial prefix. Keep raw source text internally and hash it; escape only spreadsheet/TSV storage, or use explicit string cell types with a reversible storage contract. Include an actual prepare/load/validate round trip for each prefix and a naturally occurring apostrophe-prefix string. The current repeated-character continuation test does not close this issue.

2. **Immutable validation is partial and fail-open.** `validate_author_records_against_mapping` skips missing expected text hashes; it checks neither the issued cutoff/cluster nor `item_digest`. A modified cutoff can change the assessor's interpretation while passing validation. Require valid mapping schema and mandatory hashes; verify all assessor-visible immutable fields against issued values. Include edited-cutoff/cluster and absent-hash negative cases. Preserve returned originals before analysis.

3. **Full lifecycle repair is not implemented.** Neither production lifecycle wraps operations in unconditional final integrity checks. Preparation exceptions before Step 8 bypass final rehashes. Processor tampering errors, parse failures and `sys.exit(2)` on incompleteness bypass final rehashes and terminal integrity manifest. Metrics are written before final verification and can remain after drift failure. Record FAILED/INCOMPLETE/VERIFIED outcomes and unconditional input checks without overwriting evidence; consumers must not accept metrics lacking a verified terminal record. Test failure paths, not only successful CLI execution.

4. **Production hash bypass has returned.** Preparation CLI adds `--no-verify-hash`; an absolute input path also silently defaults to no pin unless the caller provides one. Use required production pins independent of path spelling. Keep synthetic fixture injection outside the production CLI or explicitly segregate and label it so it cannot certify real extraction.

5. **Strict useful-answer yield still omits mixed answers.** Mixed supported responses that fully address the issue enter broad yield only. Add strict supported-and-responsive yield across all substantive outputs, retaining the pure-only breakdown. Clearly distinguish observed contradiction from all legal errors and report uncertain/unassessed outcomes; author ratings cannot establish licensed legal correctness.

6. **Exact boolean validation is still not exact.** Membership `value in (True, False)` accepts numeric 0/1, but point classification uses identity `is True` while bootstrap uses `is True`/`is False`. Numeric labels can therefore produce inconsistent point and bootstrap classifications. Validate `type(value) is bool`, treating null as unavailable and other types as schema errors. Add numeric/string-label controls.

Further bounded notes: rubric improvement removes the overruled-precedent conflation, but calling operative leakage 'aligned with Level-2' needs an explicit correspondence to the actual automated severity definition, not just a heading. Temporal-yes judgments still can pass without sources when correctness is uncertain; require source evidence or an explicit unavailable-evidence explanation. Companion source layout is promising but has not been viewed in a browser; Excel continuation rows remain too short for 25,000-character chunks, so instructions must make the companion the authoritative reading route. No need to pretend every Excel preview is fully visible.

## Next checkpoint

Preserve v3 and return a bounded diff, new hashes and saved synthetic positive/negative test evidence. Prioritize items 1-4 and endpoint instructions before real workbook preparation. Analysis repairs can be reviewed separately before returned files are scored. Do not change manuscript or run real extraction on this review's authority.
