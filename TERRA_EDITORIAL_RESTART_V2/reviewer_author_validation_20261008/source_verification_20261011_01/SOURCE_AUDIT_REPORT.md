# Column N source audit and bounded editorial amendments

Date: 11 October 2026. Author: Codex. Scope: source wording in the two submitted assessment workbooks. This is AI source-checking and editorial work, not independent practitioner validation.

## Outcome

The whole inventory was screened: 152 populated entries, 76 per author, containing 99 distinct Column N texts. Retrieved and preserved 129 of 130 referenced U.S. Reports PDF files, with hashes and extraction evidence. The 419 U.S. 974 URL returned a non-PDF response. Municipal entries also received separate web checks.

Nine same-proposition amendments were made in an Author 1 **copy**. The submitted workbooks remain byte-for-byte unchanged. Author 2 was not edited. No ratings, rationales, candidate answers, identifiers, timestamps, manuscript, model results, or graph were changed.

**The assessment-validation gate is NOT closed.** Full semantic equivalence and attribution of all excerpts have not been established. A whole-inventory screen is not a whole-inventory legal certification. The unresolved queue has 103 entries, including mixed cells, paraphrases, bibliographic notes, OCR mismatches and genuinely disputed wording. That does not mean 103 entries are false.

## Amendments actually made

| Author 1 item | Excel cell | Amendment | Evidence |
| --- | --- | --- | --- |
| 026–029 | N27–N30 | Replace the non-verbatim Jackalow paragraph with two actual opinion passages about boundary fact-finding and the insufficient special verdict. Retain the court/jury distinction instead of implying that boundary construction is never a question for the court. | 66 U.S. 484, 487–488. Official scanned pages visually inspected. |
| 061–065 | N62–N66 | Restore “restrictive agreements” instead of “private agreements” in the Shelley holding. Same covenants and legal proposition. Other passages untouched. | 334 U.S. 1, 20, opinion text. |

Exact before/after text and amendment reasons are in `approved_source_wording_changes.json`. These are subsequent editorial amendments, not original assessor-written observations. Jackalow spelling and punctuation follow the official scan, not the modernized Justia transcription. Its citation does not silently resolve the separate term-versus-decision-year question.

## Important entries left unchanged

- Author 1 item 030: corrupted `sourcewith` text. Its intended missing words are not reliably recoverable from the entry alone. Replacing it would require reconstructing rather than merely undoing a paraphrase.
- Author 1 item 008: the reporter heading says “Argued April 21, 1887,” whereas the submitted entry says May 3. Changing a date is a factual correction, not a same-meaning rewrite.
- Author 1 item 031: the quotation attributed to The Montello concerning judicial notice and the libellants is not found in the cited 78 U.S. 411 text. It is not safe to invent an equivalent quotation.
- Author 1 items 052/054: the purported Burke quotations are not present in the short 389 U.S. 320 opinion. The opinion instead discusses territorial divisions reducing competition and their interstate-commerce effects. An exact replacement must not silently substitute a different proposition.
- Author 1 item 068: the Los Angeles penalty passage paraphrases statutory wording and omits part of the misdemeanor/infraction structure. The official city page supports the core penalty, not the submitted exact quotation. Zoning applicability remains unverified.
- Author 2 item 068: the Dallas phrase is found in §51A-7.1305(k), but that section is district-specific. Matching the phrase does not prove that it controls every sign scenario or validate the original source link.
- Other unmatched quotations are NOT automatically false: old scans contain OCR errors, page headers interrupt sentences, bracketed changes need individual handling, and some statements may be syllabus or historical metadata rather than opinion language.

## Screening counts, before amendments

| Automated classification | Entries |
| --- | ---: |
| Whole excerpt text match under normalization | 36 |
| Substantial quoted fragments match; remainder unresolved | 18 |
| At least one quoted fragment unmatched | 46 |
| Paraphrase or bibliographic note requiring meaning review | 38 |
| No usable U.S. Reports source in this retrieval | 13 |
| Explicit corruption | 1 |
| Total | 152 |

Four Author 2 N/A cells have subsequently been identified as no excerpt to verify, not failed legal quotations. Nine entries have editorial amendments. Municipal checks and the identified disputed entries have manual dispositions in `review_ledger.csv`; all remaining unresolved entries are in `unresolved_entries.csv`.

## Method and limits

`verify_source_excerpts_readonly.py` reads the two workbooks without editing them, extracts cited volume/page pairs, downloads public GovInfo PDFs, saves hashes, and compares text after case/punctuation/whitespace normalization. “Verified quotation” in its automated ledger means textual correspondence only. It does not establish case applicability, majority versus dissent, complete legal meaning, accurate pinpoint citation, cutoff-year suitability, or reliability of the associated rating. Some scanned pages contain the tail/head of neighboring opinions. Matches must ultimately be checked inside the intended opinion, not accepted merely because they appear in a downloaded PDF.

`compare_unmatched_fragments.py` supplies candidate alignments for review. Similarity scores never authorize a repair. Nine amendments were separately selected on meaning and source context, not by a similarity threshold. The Jackalow source scan was rendered and visually read on printed pages 487–488. The Shelley replacement was checked against the opinion's holding paragraph.

Municipal references checked:

- Seattle 2021 code: https://seattle.gov/documents/departments/sdci/codes/stormwatercode/2021swcodefinalclean.pdf . The title phrase matches; the broad methods/Appendix F statement remains unresolved.
- Los Angeles official page: https://finance.lacity.gov/general-provisions . Core penalty confirmed, exact wording and exceptions differ.
- Dallas district-specific provision: https://codelibrary.amlegal.com/codes/dallas/latest/dallas_tx/0-0-0-87961 . Wording found; scenario applicability not certified.
- Denver heading: https://nonoise.org/regulation/ordinance/Denver,%20Colorado.pdf . Matches the supplied third-party copy. Current official text not certified.

Foreign-law, scientific and sports statements were not converted into U.S. legal quotations. A bibliographic source note is not automatically defective merely because it is not an opinion quotation.

## Workbook preservation and QA

Author 1 original SHA-256: `34735965b0636a26570b3053baebfd8b58532888f684e2ee381754c8bdf6832b`.

Author 2 original SHA-256: `ce3869f8b0930b6a28df73b5deabffc5e1e7da9c4b2df5a649bec27f838c598b`.

Corrected Author 1 SHA-256: `d7b59f36eaaa416d9b549df7cc7490b7d7e99b71fee416356d225f24be131024`.

Artifact Tool authored the corrected copy. Independent read-back confirms exactly nine value differences, all in the authorized Column N cells. All other values and all cell styles match. Sheet names, row/column dimensions, panes, filters and protection compare unchanged. Both original hashes were checked again after export.

**Visual limitation:** Artifact Tool produced blank range previews despite populated cell data. No Excel/native visual-layout PASS is claimed. Existing row heights are preserved and may truncate long content on screen; no authorized restyling or native Excel review was performed. This is recorded rather than treating a successful export as visual proof.

## Disclosure and next gate

`AUTHOR_1_METHOD_DISCLOSURE.md` records the lead author's AI-assisted, author-reviewed, non-expert process from the user's statements. It must accompany any reporting of these assessments. Do not call them independent legal-expert validation or entirely unaided human assessments.

Do not calculate final assessment outcomes from the amended copy as though its text were the original submission. Preserve original ratings and original agreement analysis separately. Remaining factual/attribution corrections need assessor review because the user's instruction permits only same-meaning wording repairs. Any rating consequence, consensus decision, study-results calculation or manuscript insertion requires its own bounded decision. No request for an unavailable licensed expert is made here.

## Reproduction caution

The retrieval script intentionally refuses to reuse its output directory. Do not rerun it into this preserved folder. The source PDFs, manifest, original ledger, manually reviewed ledger, amendment register, and read-back integrity record are retained for peer audit. The retrieval succeeded once; no benchmark/model/API experiment was run.
