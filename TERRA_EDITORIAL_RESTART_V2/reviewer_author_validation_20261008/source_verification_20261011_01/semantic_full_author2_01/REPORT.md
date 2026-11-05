# Independent Author 2 source audit

Author: Codex. Date: 11 October 2026. Scope: all 76 Author 2 entries in the specified ledger, assessed for Column N attribution, quotation/paraphrase fidelity, pinpoint and historical/contextual scope. Ratings, answers, refusal judgments, datasets and manuscript claims were not reassessed. No workbook, manuscript, data or original ledger was edited.

## Coverage and method

All 76 assigned IDs have an individual disposition in findings.json, grouped into 40 distinct passage assessments. Duplicate passages share source reasoning but each ID remains separately recorded. Input ledger SHA256: `7022BE9E93A90482862E8A38639C88B8BB91ECA3E67CF978DE3449888A7A5817`. The JSON includes a source-identity manifest so the main agent can reconcile the reviewed files.

I read the workspace AGENTS.md, both coordination START_HERE/PROTOCOL/STATUS records, relevant current Antigravity assessment-validation message and latest Claude reply. The historical review and restart plan were consulted for preservation/scope context. Peer workbook-format PASS claims were treated as administrative evidence, not passage validation.

The principal evidence is the preserved U.S. Reports text, including the target passage, surrounding opinion or argument, reporter page markers, and opening case context. Selected extra listed authorities were inspected for case identity and subject distinction. The assessment does not certify each additional citation's complete doctrine. It does not reconstruct an answer-specific legal analysis from ratings or from absent query context. No skill or external legal-review service was used.

This was a source-text audit, not a complete visual PDF audit. A string match is insufficient: counsel advocacy, syllabus, plurality and adjacent case text must be distinguished. Citation/term metadata also requires care. Missing target pages are evidence limitations, not automatically quotation errors.

## Important findings

1. **Item 052 has a substantive attribution defect.** Its sentence appears in Mr. O'Connor's points for appellants at 61 U.S. 396, not the People's Ferry syllabus. Mr. Benedict's opposing points follow, then the Court's opinion. The quoted sentence cannot be represented as a Court syllabus merely because it appears in the official report. See preserved USREPORTS-61-393.txt lines 29–34 and 140–195, particularly 176–183. A replacement Court passage or explicit counsel-argument label is needed.

2. **Items 005–008 need the syllabus annotation repaired.** Window Glass asks whether the agreement violates Sherman law when it concerns production rather than distribution. The editorial annotation instead frames a question about whether it concerns production. The opinion sentence at 411 and reversal at 413 are supported; neither cures that altered question. The page-413 running header names adjacent Rooker, but the final Window Glass paragraphs and disposition still precede the Rooker case title.

3. **Item 068's locator can be resolved.** The [primary hosted Dallas code](https://codelibrary.amlegal.com/codes/dallas/latest/dallas_tx/0-0-0-88389) places the luminance sentence at §51A-7.1605(h), while the source field names Division 51A-7.200. The page's following subsection references “this district”; citywide scope and historical applicability are not established. The displayed edition was 4/2026 Code S-32.

4. **Items 012 and 074 quote Baker at 237; 186 is the case opening.** Item 074's URL leads to Reynolds although the passage is Baker. Items 063–066 quote Flora's 1960 rehearing opinion at 146, not simply the case opening 145. These are locator/link improvements, not fabricated passages.

5. **Several sources are metadata-only.** Items 010, 016, 019, 034, 039 and 054 establish case identity but provide no substantive holding. Thompson's 1866 decision versus December Term 1865 and Cayuga's 1872 decision versus December Term 1871 are confirmed by GPO records. Daniel Ball's source field states December Term 1870; [GPO records January 23, 1871](https://www.govinfo.gov/app/details/USREPORTS-77/USREPORTS-77-557). Add decision year 1871 and pinpoint 563 rather than confusing term and calendar year.

6. **Syllabus and plurality labels largely matter and are often already correct.** Goss, Gregg, Lottawanna, Stapf, Illinois Brick, Repair/Asphalt and Maintenance excerpts are explicitly syllabus/headnote material. Lockett's Part III plurality and Dennis's Vinson plurality quoting Hand are appropriately labeled. Do not turn these into unanimous Court quotations or collective holdings of all authorities listed beside them.

7. **Evidence gaps are separately dispositioned.** Civil Rights Cases' local/GPO extract contains only page 3; Pace's local/GPO/LOC extract only page 583. Online judicial-text reproductions support the selected sentences at 11 and 585 respectively, but authenticated target-page scans were not obtained. The truncated extracts must not be used to conclude that the sentences are absent from the opinion. Bryant has no preserved primary copy; attempted GPO and LOC retrievals failed. Its online reproduction indicates certiorari denial followed by a dissent, supporting provisional identity/posture rather than primary-scan verification.

8. **Item 048 has available relevant evidence but unresolved exact-query applicability.** Snow's preserved text at 543 describes the Mississippi collision identified in the source field. Therefore “exact scenario not located” should not be read as “primary Snow text unavailable.” The original query was not audited, and neither exact-scenario applicability nor controlling authority is certified. The 1857 term header is not itself independently sufficient proof of decision calendar year.

9. **Item 067 is heading-only support.** Official Denver legislative search-index excerpts support the §36-6 heading, but Municode supplied no readable text and official document opens returned 410. No dated adopted/current code, numerical limits or exception analysis is certified. This is distinct from an incorrect quotation.

N/A entries 014, 017, 018 and 049 have no source passage to validate. Their assertions that the underlying query is nonlegal remain unaudited rather than being counted as source failures or independently confirmed applicability decisions.

## Disposition counts

| Disposition | IDs |
|---|---:|
| source_supported_bounded | 32 |
| correction_needed | 6 |
| source_supported_with_locator_gap | 20 |
| bibliographic_only | 6 |
| not_applicable_no_source | 4 |
| reproduction_supported_primary_scan_incomplete | 5 |
| available_source_exact_scenario_unresolved | 1 |
| primary_evidence_unavailable_reproduction_only | 1 |
| limited_primary_web_support_version_unresolved | 1 |

Counts concern source-audit dispositions only; they are not study results, rating scores or a legal-validity rate.

## Group-by-group findings

Each group below explicitly identifies every assigned ID. Full dimension fields and recommendations are repeated per ID in findings.json.

### wickard: AUTH2-ITEM-001, AUTH2-ITEM-002, AUTH2-ITEM-003, AUTH2-ITEM-004

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Court opinion, not dissent.

Fidelity: Faithful sentence with ordinary apostrophe/hyphen normalization.

Pinpoint/date: 317 U.S. 127–128 is correct.

Scope: Aggregation of similarly situated wheat production affecting market demand; not a generic power over any activity. The Act reference is contextual, not a separately verified statutory extract.

Evidence: USREPORTS-317-111.txt:651–667.

Recommendation for main-agent assessment: Retain historical and wheat-market context.

### window_glass: AUTH2-ITEM-005, AUTH2-ITEM-006, AUTH2-ITEM-007, AUTH2-ITEM-008

Disposition: **correction_needed**. Evidence availability: `preserved_source_available`.

Attribution: First sentence is opinion at 411; inserted material is syllabus at 403; disposition at 413 belongs to this case despite adjacent Rooker header.

Fidelity: Opinion sentence/disposition faithful. Editorial formulation changes the syllabus question: it is whether the agreement violates Sherman law WHEN it concerns production, not whether it concerns production.

Pinpoint/date: Add 411 for opinion and 403 for syllabus; 413 disposition correct.

Scope: Fact-dependent labor allocation under shortage, not a categorical exemption for all production restraints.

Evidence: USREPORTS-263-403.txt:9–27; USREPORTS-263-403.txt:341–352; USREPORTS-263-403.txt:final Window Glass paragraphs before ROOKER title.

Recommendation for main-agent assessment: Rewrite the syllabus annotation to preserve the conditional question; distinguish its text from opinion.

### goss: AUTH2-ITEM-009

Disposition: **source_supported_with_locator_gap**. Evidence availability: `preserved_source_available`.

Attribution: Explicit Goss syllabus attribution correct; not McLaurin or Green.

Fidelity: Faithful shortened syllabus passage.

Pinpoint/date: Syllabus 373 U.S. 683; underlying opinion 684–689.

Scope: Race-based minority-to-majority transfers; Brown citation is Brown II, 349 U.S. 294, not Brown I. Other listed cases are not established by this excerpt.

Evidence: USREPORTS-373-683.txt:8–24; USREPORTS-339-637.txt:opening syllabus; USREPORTS-391-430.txt:opening syllabus.

Recommendation for main-agent assessment: Add syllabus page; retain case-specific transfer scope.

### wampler: AUTH2-ITEM-010

Disposition: **bibliographic_only**. Evidence availability: `preserved_source_available`.

Attribution: Bibliographic record, not an opinion excerpt.

Fidelity: Title/citation/year/date supported.

Pinpoint/date: 282 U.S. 172; decided December 8, 1930.

Scope: Establishes case identity only.

Evidence: USREPORTS-282-172.txt:10–13.

Recommendation for main-agent assessment: No substantive validation follows from metadata.

### overton: AUTH2-ITEM-011

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Overton Park Court opinion; not Yamashita.

Fidelity: Bracketed capital T is editorial. Otherwise faithful selected portion.

Pinpoint/date: 401 U.S. 416 correct.

Scope: APA arbitrary/capricious review: searching inquiry but narrow review; court cannot substitute its judgment. No Yamashita proposition is proved.

Evidence: USREPORTS-401-402.txt:571–588.

Recommendation for main-agent assessment: Name Overton Park explicitly beside quote; preserve review limits.

### baker: AUTH2-ITEM-012, AUTH2-ITEM-074

Disposition: **source_supported_with_locator_gap**. Evidence availability: `preserved_source_available`.

Attribution: Baker Court opinion, not Reynolds; item 074 URL leads to Reynolds despite Baker text.

Fidelity: Faithful sentence.

Pinpoint/date: Quoted text is at 369 U.S. 237, not the opening page 186.

Scope: Justiciability and trial/remand, not a final merits ruling or population apportionment standard.

Evidence: USREPORTS-369-186.txt:2033–2049.

Recommendation for main-agent assessment: Add Baker 237 and direct Baker URL, especially item 074.

### gideon: AUTH2-ITEM-013, AUTH2-ITEM-033

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Gideon Court opinion.

Fidelity: Editorial capital A and omitted lead-in preserve selected sentence, but criminal-justice lead-in matters.

Pinpoint/date: 372 U.S. 344 correct.

Scope: Criminal prosecution of an indigent defendant, not every civil litigant or every police encounter. Massiah, Terry, Hamilton and Cohen address different issues; this quote supplies no collective holding for all listed authorities. Betts overruled in Gideon.

Evidence: USREPORTS-372-335.txt:350–365; USREPORTS-372-335.txt:opening syllabus; USREPORTS-377-201.txt:opening; USREPORTS-368-52.txt:opening; USREPORTS-366-117.txt:opening; USREPORTS-392-1.txt:opening.

Recommendation for main-agent assessment: Keep criminal context; do not infer holdings of adjacent listed cases.

### na: AUTH2-ITEM-014, AUTH2-ITEM-017, AUTH2-ITEM-018, AUTH2-ITEM-049

Disposition: **not_applicable_no_source**. Evidence availability: `not_applicable_no_source_asserted`.

Attribution: No source passage supplied.

Fidelity: N/A is a placeholder, not a quotation.

Pinpoint/date: Not applicable.

Scope: The ledger alone cannot independently establish that each underlying query is nonlegal. No judgment about refusal or rating.

Evidence: .

Recommendation for main-agent assessment: Retain no-source disposition; query applicability remains outside this source-only evidence.

### shelley: AUTH2-ITEM-015

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Court opinion.

Fidelity: Faithful.

Pinpoint/date: 334 U.S. 20 correct.

Scope: State judicial enforcement of racially restrictive covenants; not a holding that private covenants standing alone violate Fourteenth Amendment.

Evidence: USREPORTS-334-1.txt:740–751; USREPORTS-334-1.txt:opening syllabus.

Recommendation for main-agent assessment: Retain judicial enforcement qualification.

### crockett: AUTH2-ITEM-016

Disposition: **bibliographic_only**. Evidence availability: `preserved_source_available`.

Attribution: Bibliographic entry.

Fidelity: Citation, case name and June 22, 1914 supported; R.Y. is a metadata styling issue.

Pinpoint/date: 234 U.S. 725.

Scope: No substantive holding supplied. Opening page also ends a preceding case; its Affirmed is not independently the Crockett disposition.

Evidence: USREPORTS-234-725.txt:16–20.

Recommendation for main-agent assessment: Metadata-only disposition.

### pierson: AUTH2-ITEM-019

Disposition: **bibliographic_only**. Evidence availability: `preserved_source_available`.

Attribution: Case reference only.

Fidelity: Case identity/year supported.

Pinpoint/date: 386 U.S. 547.

Scope: No quoted holding or legal proposition to validate.

Evidence: USREPORTS-386-547.txt:1–6.

Recommendation for main-agent assessment: Metadata-only disposition.

### olmstead: AUTH2-ITEM-020, AUTH2-ITEM-021, AUTH2-ITEM-022, AUTH2-ITEM-023

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Court majority opinion, not Brandeis dissent.

Fidelity: Faithful.

Pinpoint/date: 277 U.S. 464 correct; next page begins 465 after passage.

Scope: Historical wiretapping without physical entry rationale. Katz source rejects controlling trespass rationale; quotation alone must not be treated as current doctrine.

Evidence: USREPORTS-277-438.txt:1035–1054; USREPORTS-389-347.txt:253–268.

Recommendation for main-agent assessment: Retain historical scope.

### trenton: AUTH2-ITEM-024, AUTH2-ITEM-025, AUTH2-ITEM-026, AUTH2-ITEM-027

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Trenton Potteries Court opinion, not Standard Oil.

Fidelity: Faithful.

Pinpoint/date: 273 U.S. 397 correct.

Scope: Price-fixing removes competition even if prices claimed reasonable. Quote does not certify every Sherman §1 issue or provide statutory text.

Evidence: USREPORTS-273-392.txt:218–235; USREPORTS-221-1.txt:opening.

Recommendation for main-agent assessment: Identify Trenton Potteries as passage source.

### civil_rights: AUTH2-ITEM-028, AUTH2-ITEM-029, AUTH2-ITEM-030, AUTH2-ITEM-031

Disposition: **reproduction_supported_primary_scan_incomplete**. Evidence availability: `local_primary_extract_incomplete_web_reproduction_available`.

Attribution: Bradley majority passage in online judicial-text reproduction; not Harlan dissent.

Fidelity: Reproduction supports wording except typographic capitalization/hyphenation.

Pinpoint/date: Online reproduction places passage at 109 U.S. 11; local extract only page 3.

Scope: Fourteenth Amendment state-action discussion; cannot generalize to all constitutional/statutory protection against private conduct.

Evidence: USREPORTS-109-3.txt only page 3; https://supreme.justia.com/cases/federal/us/109/3/ judicial opinion text near page 11; GovInfo case PDF also one page; LOC full scan fetch 403.

Recommendation for main-agent assessment: Preserve reproduction-supported status; obtain actual page 11 scan for scan-level confirmation.

### katz: AUTH2-ITEM-032

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Court opinion, not Harlan concurrence.

Fidelity: Faithful with normalized quote marks.

Pinpoint/date: 389 U.S. 353 correct.

Scope: Rejection of controlling Olmstead/Goldman trespass rationale; not itself Harlan's full two-part reasonable-expectation test.

Evidence: USREPORTS-389-347.txt:253–268.

Recommendation for main-agent assessment: Retain narrow attribution.

### thompson: AUTH2-ITEM-034

Disposition: **bibliographic_only**. Evidence availability: `preserved_source_available`.

Attribution: Bibliographic case identification.

Fidelity: 1866 decision versus December Term 1865 distinction confirmed.

Pinpoint/date: 70 U.S. 155; GPO January 15, 1866.

Scope: Case starts after previous opinion and is followed by The Louisiana. Louisiana drifting-vessel material is not Thompson.

Evidence: USREPORTS-70-155.txt:case boundary and final Louisiana heading; https://www.govinfo.gov/app/details/USREPORTS-70/USREPORTS-70-155.

Recommendation for main-agent assessment: Metadata-only; retain term/year distinction.

### gregg: AUTH2-ITEM-035, AUTH2-ITEM-036

Disposition: **source_supported_with_locator_gap**. Evidence availability: `preserved_source_available`.

Attribution: Expressly labeled Gregg syllabus, summarizing Stewart/Powell/Stevens joint opinion; not all listed cases' collective text.

Fidelity: Faithful syllabus sentence.

Pinpoint/date: Add Gregg syllabus 428 U.S. 156–157; underlying discussion 188–195.

Scope: Guided capital sentencing; does not establish every companion-case result. Woodson rejects mandatory scheme; Lockett/Godfrey qualify application.

Evidence: USREPORTS-428-153.txt:100–115; USREPORTS-428-153.txt:1650–1667; USREPORTS-428-280.txt:opening syllabus; USREPORTS-428-242.txt:opening; USREPORTS-428-262.txt:opening; USREPORTS-446-420.txt:opening.

Recommendation for main-agent assessment: Keep syllabus attribution and add locator; do not label this unanimous Court language.

### lockett: AUTH2-ITEM-037, AUTH2-ITEM-038

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Lockett Part III plurality; label correct.

Fidelity: Faithful selected conclusion, with punctuation normalization and omitted footnote markers.

Pinpoint/date: 438 U.S. 604 correct.

Scope: Capital mitigation principle, including rarest-case reservation and relevant-evidence limits; not text of Gregg linked in source field.

Evidence: USREPORTS-438-586.txt:52–65; USREPORTS-438-586.txt:712–728.

Recommendation for main-agent assessment: Supply direct Lockett URL; retain plurality label.

### cayuga: AUTH2-ITEM-039

Disposition: **bibliographic_only**. Evidence availability: `preserved_source_available`.

Attribution: Bibliographic case note.

Fidelity: 1872 decision and December Term 1871 supported.

Pinpoint/date: 81 U.S. 270; GPO April 1, 1872.

Scope: Not the separate Cayuga at 83 U.S. 177. Extract begins with previous opinion and later includes another case.

Evidence: USREPORTS-81-270.txt:1–54; https://www.govinfo.gov/app/details/USREPORTS-81/USREPORTS-81-270.

Recommendation for main-agent assessment: Metadata-only; guard case boundary and term/year.

### roe: AUTH2-ITEM-040, AUTH2-ITEM-041, AUTH2-ITEM-042, AUTH2-ITEM-043

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Court opinion; bracketed subject is editorial replacement.

Fidelity: Faithful condensed selection but omits intervening privacy-basis qualification; bracket marks replacement transparently.

Pinpoint/date: 410 U.S. 153 correct.

Scope: Historical Roe proposition, not unrestricted right or certification of present doctrine; surrounding opinion recognizes limits. Danforth/Colautti not demonstrated by single Roe sentence.

Evidence: USREPORTS-410-113.txt:1582–1599; USREPORTS-410-113.txt:1670–1683; USREPORTS-428-52.txt:opening; USREPORTS-439-379.txt:opening.

Recommendation for main-agent assessment: Keep historical and nonabsolute scope; use ellipsis/full lead-in if presented as continuous quotation.

### reynolds: AUTH2-ITEM-044, AUTH2-ITEM-045, AUTH2-ITEM-046, AUTH2-ITEM-047

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Reynolds Court opinion.

Fidelity: Faithful fragment after omitted opening lead-in.

Pinpoint/date: 377 U.S. 568 correct.

Scope: Both houses of state legislature; surrounding explanation permits practical deviations, not mechanical exactness. Avery/Hadley are different local-body contexts.

Evidence: USREPORTS-377-533.txt:1402–1425; USREPORTS-377-533.txt:opening syllabus; USREPORTS-390-474.txt:opening; USREPORTS-397-50.txt:opening.

Recommendation for main-agent assessment: Retain state-legislature scope.

### snow: AUTH2-ITEM-048

Disposition: **available_source_exact_scenario_unresolved**. Evidence availability: `local_source_available_query_context_missing`.

Attribution: A relevant Snow source exists locally; N/A is a search-limitation note.

Fidelity: No quotation supplied. 'Text not located' is too broad if read as source unavailability.

Pinpoint/date: 61 U.S. 543 opening describes collision; 1857 is term header, decision-year not independently resolved here.

Scope: Local opening describes descending towboat with lashed vessels and ascending steamer. Exact-query applicability cannot be established without query evidence; no controlling-authority claim made.

Evidence: USREPORTS-61-543.txt:1–22.

Recommendation for main-agent assessment: Say exact-scenario applicability unresolved, rather than implying Snow primary text unavailable.

### lottawanna: AUTH2-ITEM-050, AUTH2-ITEM-051, AUTH2-ITEM-053

Disposition: **source_supported_with_locator_gap**. Evidence availability: `preserved_source_available`.

Attribution: Expressly labeled Lottawanna syllabus.

Fidelity: Faithful syllabus segment; original prints material-men.

Pinpoint/date: Syllabus point 6 at 88 U.S. 559; add locator.

Scope: General maritime law home-port lien rule; adjoining syllabus recognizes state-created liens and legislative change. No broad claim that no lien can exist.

Evidence: USREPORTS-88-558.txt:40–68; USREPORTS-17-438.txt:opening.

Recommendation for main-agent assessment: Add 559 and preserve general-maritime/home-port qualifiers.

### peoples_ferry: AUTH2-ITEM-052

Disposition: **correction_needed**. Evidence availability: `preserved_source_available`.

Attribution: NOT syllabus: Mr. O'Connor's argument for appellants, before Mr. Benedict's opposing points and Court opinion.

Fidelity: Words are present, but faithful copying does not cure false institutional attribution.

Pinpoint/date: 61 U.S. 396, rather than opening syllabus 393.

Scope: Counsel advocacy in vessel-construction jurisdiction case; cannot elevate broad 'only case' formulation to Court holding. Local extract includes previous case and following McCormick; target sentence lies within counsel section.

Evidence: USREPORTS-61-393.txt:29–34; USREPORTS-61-393.txt:140–195, especially 176–183.

Recommendation for main-agent assessment: Replace with actual Court passage, or explicitly label counsel argument; do not use this as syllabus evidence.

### picco: AUTH2-ITEM-054

Disposition: **bibliographic_only**. Evidence availability: `preserved_source_available`.

Attribution: Case citation only.

Fidelity: Title/year/citation supported.

Pinpoint/date: 411 U.S. 655.

Scope: No holding supplied; identity alone does not validate pollution/navigation proposition.

Evidence: USREPORTS-411-655.txt:1–7.

Recommendation for main-agent assessment: Metadata-only disposition.

### lochner: AUTH2-ITEM-055

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Majority opinion, not Holmes/Harlan dissent.

Fidelity: Faithful sentence, disregarding OCR punctuation artifact.

Pinpoint/date: 198 U.S. 53 correct.

Scope: Historical contract-liberty discussion with police-power qualification immediately following; not categorical contractual immunity or present-law certification.

Evidence: USREPORTS-198-45.txt:321–341.

Recommendation for main-agent assessment: Retain historical/context limits.

### daniel_ball: AUTH2-ITEM-056, AUTH2-ITEM-057, AUTH2-ITEM-058, AUTH2-ITEM-059

Disposition: **source_supported_with_locator_gap**. Evidence availability: `preserved_source_available`.

Attribution: Field's Court opinion, not merely syllabus.

Fidelity: Faithful sentence sequence.

Pinpoint/date: Add 77 U.S. 563; decision January 23, 1871. December Term 1870 is not decision year.

Scope: Navigability in fact; following sentence additionally requires interstate/foreign highway connection for US navigable-water classification.

Evidence: USREPORTS-77-557.txt:270–291; https://www.govinfo.gov/app/details/USREPORTS-77/USREPORTS-77-557.

Recommendation for main-agent assessment: Add 563 and (1871); retain separately labeled December Term 1870.

### pace: AUTH2-ITEM-060

Disposition: **reproduction_supported_primary_scan_incomplete**. Evidence availability: `local_primary_extract_incomplete_web_reproduction_available`.

Attribution: Court opinion in online judicial-text reproduction.

Fidelity: Online text supports sentence; missing local page is not contradictory evidence.

Pinpoint/date: 106 U.S. 585 supported by reproduction; preserved/GPO/LOC extracts only 583.

Scope: Historical rationale compares punishments within interracial offense, not punishment of same-race relationships; do not convert to general equality proposition or current doctrine.

Evidence: USREPORTS-106-583.txt only 583 including preceding Plainview note; https://supreme.justia.com/cases/federal/us/106/583/ judicial text at 585; GPO and LOC fetched PDFs each only one page.

Recommendation for main-agent assessment: Obtain page 585 scan for primary scan-level confirmation.

### bryant: AUTH2-ITEM-061

Disposition: **primary_evidence_unavailable_reproduction_only**. Evidence availability: `no_local_primary_copy_primary_web_fetch_failed_reproduction_available`.

Attribution: Online reproduction shows certiorari denial followed by Brennan dissent joined by Stewart/Marshall; citation alone is metadata.

Fidelity: Reproduction supports case/year and October 29, 1974; no local 419-974 source.

Pinpoint/date: 419 U.S. 974; primary GPO/LOC fetches unsuccessful.

Scope: Certiorari denial is not merits affirmance; dissent following order is not Court holding.

Evidence: https://supreme.justia.com/cases/federal/us/419/974/; Failed GPO detail/PDF and LOC PDF retrieval; no preserved 419-974.txt.

Recommendation for main-agent assessment: Keep bibliographic identity provisional pending primary copy; do not describe denial as merits decision.

### stapf: AUTH2-ITEM-062

Disposition: **source_supported_with_locator_gap**. Evidence availability: `preserved_source_available`.

Attribution: Expressly Stapf syllabus, not Delgadillo.

Fidelity: Faithful with added comma normalization.

Pinpoint/date: Syllabus at 287 U.S. 129; underlying holding 132.

Scope: Round-trip voyage to Germany by irregularly admitted seaman; Delgadillo shipwreck/involuntary Cuba episode is distinguishable. No inference all overseas diversions constitute entry.

Evidence: USREPORTS-287-129.txt:16–28; USREPORTS-332-388.txt:opening syllabus and 389–391.

Recommendation for main-agent assessment: Add syllabus locator and retain factual distinction.

### flora: AUTH2-ITEM-063, AUTH2-ITEM-064, AUTH2-ITEM-065, AUTH2-ITEM-066

Disposition: **source_supported_with_locator_gap**. Evidence availability: `preserved_source_available`.

Attribution: 1960 rehearing Court opinion recounts earlier decision.

Fidelity: Faithful selected sentence.

Pinpoint/date: 362 U.S. 146, not opening 145. 1957 Term is compatible with 1958 first decision and 1960 rehearing.

Scope: Federal income-tax refund jurisdiction under §1346(a)(1); not all tax proceedings. Statutory reference contextual, not independently quoted current statute.

Evidence: USREPORTS-362-145.txt:43–75; USREPORTS-357-63.txt:opening.

Recommendation for main-agent assessment: Add 146; preserve term/decision-year distinction.

### denver: AUTH2-ITEM-067

Disposition: **limited_primary_web_support_version_unresolved**. Evidence availability: `primary_index_excerpt_available_full_current_code_unavailable`.

Attribution: Section heading only, not operative limits.

Fidelity: Heading supported by indexed official Denver legislative documents; live Municode provided no readable code; document fetches returned 410.

Pinpoint/date: §36-6 heading confirmed in indexed legislative material.

Scope: No numerical noise limits, exceptions, or historical effective version supplied or independently established.

Evidence: https://denver.legistar.com/View.ashx?GUID=9256551A-49F9-4840-A90E-B38B5D6C8DC3&ID=13759982&M=F indexed official legislative excerpt; https://library.municode.com/co/denver/codes/code_of_ordinances empty readable response.

Recommendation for main-agent assessment: Record heading-only support; obtain dated adopted code if substantive limits matter.

### dallas: AUTH2-ITEM-068

Disposition: **correction_needed**. Evidence availability: `primary_hosted_code_available`.

Attribution: Primary municipal code-host text at §51A-7.1605(h).

Fidelity: Sentence exact in primary hosted code.

Pinpoint/date: Exact subsection resolved; source field Div. 51A-7.200 does not identify quoted §51A-7.1605(h).

Scope: District-specific provision: following subsection says 'this district'. A citywide luminance rule or historical effective version cannot be inferred.

Evidence: https://codelibrary.amlegal.com/codes/dallas/latest/dallas_tx/0-0-0-88389 lines 15,28–35; displayed 4/2026 Code S-32.

Recommendation for main-agent assessment: Correct locator to §51A-7.1605(h); retain district and version limits.

### illinois_brick: AUTH2-ITEM-069

Disposition: **source_supported_with_locator_gap**. Evidence availability: `preserved_source_available`.

Attribution: Correctly Illinois Brick syllabus summarizing Hanover Shoe.

Fidelity: Faithful except '§4' rendered s.4 and normal quote typography.

Pinpoint/date: 431 U.S. 720 syllabus; Hanover Shoe opening 392 U.S. 481 is not location of this sentence.

Scope: Direct-purchaser pass-on discussion; Reiter addresses property injury and does not erase Illinois Brick rule. Listed sources must not be fused.

Evidence: USREPORTS-431-720.txt:20–29; USREPORTS-392-481.txt:opening; USREPORTS-442-330.txt:opening.

Recommendation for main-agent assessment: Add syllabus page and preserve attribution.

### cooper: AUTH2-ITEM-070

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Cooper Court opinion; not Brown or McLaurin quote.

Fidelity: Bracketed initial T marks selected clause; faithful.

Pinpoint/date: 358 U.S. 18 correct.

Scope: Binding Brown interpretation on state authorities in desegregation context; does not supply every listed case's holding.

Evidence: USREPORTS-358-1.txt:658–687; USREPORTS-339-637.txt:opening; USREPORTS-347-483.txt:opening.

Recommendation for main-agent assessment: Retain named Cooper attribution.

### loving: AUTH2-ITEM-071

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Loving Court opinion.

Fidelity: Faithful.

Pinpoint/date: 388 U.S. 12 correct.

Scope: Racial restrictions on marriage, not a Sweatt education passage; separate due-process discussion follows.

Evidence: USREPORTS-388-1.txt:418–433; USREPORTS-339-629.txt:opening.

Recommendation for main-agent assessment: Retain case-specific marriage scope.

### repair_asphalt: AUTH2-ITEM-072

Disposition: **source_supported_with_locator_gap**. Evidence availability: `preserved_source_available`.

Attribution: Pre-opinion headnote/syllabus, correctly labeled despite page header 'Opinion of the Court'.

Fidelity: Faithful except OCR/typography normalization.

Pinpoint/date: 183 U.S. 591; decided January 6, 1902, distinct from October Term 1901 and French patent June 11, 1880.

Scope: Anticipation by identified French patent; no general patentability standard or Hotchkiss holding supplied.

Evidence: USREPORTS-183-591.txt:1–15; USREPORTS-52-248.txt:opening after preceding ORDER.

Recommendation for main-agent assessment: Add syllabus/headnote page; keep dates distinct.

### tinker: AUTH2-ITEM-073

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Tinker Court opinion.

Fidelity: Faithful.

Pinpoint/date: 393 U.S. 506 correct.

Scope: Rights apply with special characteristics of school environment; not unconditional immunity from school discipline or quotation from all listed speech cases.

Evidence: USREPORTS-393-503.txt:128–141; USREPORTS-299-353.txt:opening; USREPORTS-319-624.txt:target title after prior dissent; USREPORTS-364-479.txt:opening; USREPORTS-372-229.txt:opening.

Recommendation for main-agent assessment: Preserve school-context qualification.

### maintenance: AUTH2-ITEM-075

Disposition: **source_supported_with_locator_gap**. Evidence availability: `preserved_source_available`.

Attribution: Explicit syllabus attribution correct.

Fidelity: Faithful fragment with lower-case initial and antecedent omitted.

Pinpoint/date: 366 U.S. 169 syllabus; discussion 169–179.

Scope: 'This' refers to statutory employee-protection arrangement, not unrestricted merger discretion. Compensation versus retention, not all employee rights.

Evidence: USREPORTS-366-169.txt:8–22.

Recommendation for main-agent assessment: Add syllabus locator and antecedent.

### dennis: AUTH2-ITEM-076

Disposition: **source_supported_bounded**. Evidence availability: `preserved_source_available`.

Attribution: Vinson plurality quoting and adopting Learned Hand; attribution correct.

Fidelity: Faithful; [courts] is already bracketed in quoted source.

Pinpoint/date: 341 U.S. 510 correct.

Scope: Historical Smith Act danger formulation; Brandenburg supplies different incitement limits and Cohen a different expression context. Not current test established by this quotation.

Evidence: USREPORTS-341-494.txt:633–648; USREPORTS-395-444.txt:opening; USREPORTS-403-15.txt:opening.

Recommendation for main-agent assessment: Retain plurality/Hand labels and historical scope.


## Machine-readable schema and handoff limits

findings.json has schema_version, author, audit_date, input and input_sha256, scope, limitations, status_definitions, group_count, coverage, findings and source_identity_manifest. Each finding contains id, author, column, group_id, disposition, attribution, quotation_or_paraphrase_fidelity, pinpoint, scope, evidence_availability, evidence, recommendation and ratings_reviewed=false.

Source lines refer to the preserved .txt files relative to ../sources, not PDF page indices. Reporter page numbers are separately supplied in pinpoint. Web references identify the evidence route; failed routes and reproduction-only routes remain explicit. No extracted/source bytes were modified or promoted. The main agent should assess these findings against its own evidence, especially counsel attribution, municipal version/scope and incomplete scans.

Neither supported wording nor an authentic case identity establishes legal correctness of an answer, present controlling law, temporal eligibility for an unseen query, or full validation of Column N. These artifacts are independent source findings with stated limits.
