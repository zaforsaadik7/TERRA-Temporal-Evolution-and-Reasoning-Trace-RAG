# I10 implementation plan — submission and availability requirements

Codex ·26October2026 · **PLAN ONLY**. Requested by the user after I0closure. No implementation, upload, author change, submission or working-source edit is authorized by this planning document. No procedure guarantees zero defects or journal acceptance; this plan specifies evidence, validation and recovery rather than a guarantee.

## 1. Scope and accepted decisions

Use the original `20261008_REVIEWER_INTEGRATED_SUBMISSION_PLAN.md` definition of I10: submission/availability requirements. I11owns final whole-paper scientific/visual/clean-room certification and the final reviewer response. I12requires separate approval of the exact destination and candidate for promotion/submission. I9remains partial; its Springer conversion was rejected/set aside. **Do not restart it or rewrite the accepted paper as an implicit part of I10.**

I0isDONE. Its approved OBJ08disposition retains ROUGE-L system values in prose/TableIII with the self-comparison row omitted. Do not reopen that decision. Accepted source has47files; accepted PDFs are25main/21supplement pages. Use current coordination pointers and verify against I0/I6full hashes, not remembered abbreviated hashes. Original datasets, assessments, frozen statistics, all18limitation themes, accepted scientific qualifications and negative results remain protected.

Produce an isolated submission-preparation package, author-confirmed declarations, an evidence-backed availability/release map and a verified review-package design. Preparation may advance while I9is set aside, but **journal-compliant submission readiness cannot be certified when venue/format/reference requirements remain unresolved**.

## 2. Official policy evidence checked for planning

Source checked26October2026: [Artificial Intelligence and Law submission guidelines](https://link.springer.com/journal/10506/submission-guidelines). The live guidance calls for double-anonymous review, editable sources, a150–250word abstract,4–6keywords, author–year citations and a Data Availability Statement. Mathematical manuscripts may use LaTeX; the publisher template is recommended. Substantive LLM use requires disclosure; limited copyediting has a narrower exception. Supplementary files need citations/captions and Online Resource naming. Author consent and applicable declarations must be supplied. The page warns that submission-system changes affect placement of author details/statements; older title-page instructions coexist with newer interface instructions. These are **candidate-venue requirements**, not evidence that the user has finally selected this journal or that IEEE25pages complies.

Supporting official sources:

- [SNAPP anonymous-review instructions](https://www.springernature.com/gp/snapp/submitting/how-to-submit/double-anonymous): review files require identity removal, including metadata; declaration placement follows the system.
- [Research data policy](https://www.springernature.com/gp/authors/research-data-policy): availability statements must identify access arrangements and reuse conditions.

During implementation, save a dated rule register with sourceURL, section, retrieved text excerpt within reasonable bounds, retrieval time and content digest where a local snapshot is retained. Recheck immediately before I12submission; website access today does not prove future portal fields. Do not log in, create a submission draft or contact editors merely to resolve policy. Conflicting public instructions become explicit questions for the author or later authorized portal inspection.

## 3. Local observations to reconcile

Observed in the accepted source, not independently confirmed biographical facts:

- `main.tex` uses IEEEtran conference layout and identifies Md.EmamZaforSaadik and Md.RaihanMolla with BUBT affiliation. That identified master is not an anonymous review file.
- Its availability paragraph identifies a GitHub repository but explicitly declines to certify public access, full-package archival deposition or license coverage. The corrected graph is a local derivative with public release pending.
- Local directories `canonical_v2_reproducibility_bundle/` and `issue18_bundle/` contain historical manifests. Their presence is not proof of current completeness, public release, rights clearance or replayability.
- The assessment supplement discloses non-expert AI assistance, overlapping assignments and unblinded reconciliation. Preserve these qualifications. Separate tool use in the evaluated system from AI assistance in research/coding/assessment/manuscript production.
- A previous proposal about corresponding authorship/University of Wyoming is not an author decision. Never add an advisor, change order/affiliation or assign corresponding authorship automatically.

Read only relevant current records; no credential files or environment dumps. Mark source facts, author statements, public observations and unavailable evidence separately.

## 4. Authorization and package boundaries

After implementation approval, use fresh `TERRA_EDITORIAL_RESTART_V2/reviewer_I10_<date>_01/`; choose another suffix if occupied. Freeze exact47sources, PDFs and accepted manifests; verify source membership/hashes before and after. Preserve prior progress/status bytes before index updates.

Allowed within the approved implementation: local inventory and documents; public read-only journal/repository/DOI checks; isolated copies and packaging; anonymous candidate edits limited to identity/declaration/availability metadata; cached offline builds of those candidates; evidence-based proposed patches; synthetics for validators; review packet preparation. All scientific wording changes require an explicit proposed diff and evidence, not silent redesign.

Not authorized: source-store connections, inference, API-key reads, live provider runs, reanalysis/scoring, author-rating edits, historical-statistics generation, corpus/index modification, archive rewriting, Git push, license application on behalf of rights holders, DOI creation/deposition, public upload, changing repository visibility, emailing authors/editors, starting a submission or canonical promotion. Do not read a secret merely to prove it was excluded. Do not duplicate allCAPcorpora/vectorstores or hash the whole workspace indiscriminately.

Keep three distinct outputs: an untouched identified baseline; a private identified editor/author-information packet; and a separate anonymous reviewer package. Only the latter is a review-export candidate. Existing working sources/PDFs remain unchanged unless the user later approves exact adoption.

## 5. Work packages and acceptance tests

### A. Freeze and build the compliance matrix

1. Reconcile I0closure, original I10definition, latest relevant peer evidence, current47-file membership and PDF hashes. Stop on unexplained source drift; do not roll back to old bytes automatically.
2. Create `BASELINE_MANIFEST.json`, `AUTHORITY.md`, `POLICY_SOURCES.json` and `COMPLIANCE_MATRIX.json`.
3. Each matrix row has stable ID, exact requirement, policy/source/date, applicability, actual candidate evidence, status, responsible package, proposed repair and blocker. Use `VERIFIED`, `DRAFT`, `AUTHOR_CONFIRMATION_REQUIRED`, `POLICY_CONFLICT`, `NOT_APPLICABLE_WITH_BASIS`, `DEFERRED_I9`, `BLOCKED`.
4. Measure actual rendered abstract words/keywords, bibliography/citation mode, supplementary names, identification and declarations against candidate rules. Macro expansion must be accounted for; rawTeX word counts are diagnostic only. Do not change typography/reference style just to turn matrix cells green.
5. Record the venue decision as confirmed only with actual user/author evidence. If unavailable, produce a clearly conditional ArtificialIntelligenceandLaw profile plus venue-neutral files. I10preparation can proceed, but venue-specific readiness remains blocked.

Acceptance: every applicable rule has evidence or a specific unresolved owner; no blanket compliance assertion. The IEEE25page target and journal-format compliance occupy separate fields.

### B. Assemble a single author-decision packet

Prepare `AUTHOR_DECISIONS.md` and `DECLARATIONS_REGISTER.json`, prefilled only from attributable evidence. Ask once for unresolved facts while continuing independent inventory. Missing fields are explicit pending values in private drafts, never plausible guesses. Required subjects:

- Exact author names/order, accurate institutional affiliations at the work date, corresponding author/contact, anyORCIDs actually supplied; all-author approval of final content/contributions/accountability.
- Target journal/article type, willingness to resolve any I9reference/format requirement, and advisor treatment of supplementary material if not documented.
- Funding/support including hosted-credit support if relevant, conflicts, acknowledgments/permissions, prior dissemination/preprints/overlap and concurrent-submission status. Do not fill “none” from silence.
- Contribution roles based on actual human activities; noAIauthorship. An adviser is not automatically an author, and a funding source is not automatically a conflict.
- Assessment participation/source use, consent to disclose assessor identity/roles, and any institutional ethics review or applicability determination. Do not invent an ethics exemption/IRBnumber; public court data alone does not settle the status of author-assessment records.
- Desired availability arrangement and ownership/permission for code, benchmark references, annotations and outputs; no assumed consent for public human-assessment workbooks or rawchat logs.

Build publication-ready wording only after facts are confirmed. Draft private title-page/editor fields and declaration text separately; final placement follows the verified current system, not a universal title-page rule. Remove private confirmation details from anonymous exports.

Acceptance: confirmed versus unknown facts distinguishable; no false “no funding/no conflicts/ethics not applicable”; no manufactured author consent. If required human facts are absent, mark the corresponding completion gate pending rather than repeatedly asking broad permission.

### C. Prepare accurate AI-use disclosure

Create `AI_USE_INVENTORY.json` from actual records: function, tool/interface, model/version as recorded, date if known, outputs affected, human review and evidential limitations. Cover assessment source-finding/interpretation/proposed ratings/rationale drafting, code/analysis support and substantive manuscript assistance as applicable. Model names supplied by authors remain reported identities, not authenticated provider attestations; do not retrofit today's product names into historical use.

Draft a concise Methods/appropriate-section disclosure and separate private administrative answers. Preserve Author1human-first versus Author2AI-proposed workflow and later cross-author reconciliation. Do not call the whole process copyediting or blind independent legal assessment. Human author review/accountability is necessary but cannot manufacture independent ground truth. Verify factual descriptions with authors; neither this plan nor a disclaimer transfers authorship to an AI.

Acceptance: no substantiveAIuse concealed under copyediting; no release of private prompts/source identifiers simply to satisfy disclosure; no weakening of I6limitations.

### D. Verify actual availability and rights

Create `AVAILABILITY_INVENTORY.json` and `RIGHTS_AND_RESTRICTIONS.json`. For every claimed component record local path, fullhash/bytes, study/version, source, observed publicURL/commit/release, access test/date, license/terms evidence, redistribution status, privacy/redaction requirement, planned package destination and unmet dependency. Include:

- Benchmark queries/reference answers/categories; historical canonical and external-suite results; corrected and historical graph distinctions; scaffold/annotation construction; prompts/rubrics/configurations; matched-study outputs and descriptive/analysis ledgers; required correction layers and manuscript sources.
- Author-assessment original/reconciled records treated separately and private by default. A masked derived ledger may be a candidate only after consent/privacy review. Do not export original workbooks/source quotations or rationales under this plan; the previously excluded rewriting/export issue stays excluded.
- Model/tokenizer assets, corpus/external dataset excerpts, third-party software and curated relations: identify terms and rights per component. Download access or public visibility is not permission to redistribute. Where uncertain, prefer source references/instructions/manifests over bundled third-party bytes.

Use public unauthenticated repository checks when authorized; record whether the *specific* required version/files are actually present. AGitHubhomepage or404does not establish an entire release's completeness or permanent unavailability. Never extract credentials fromgitremoteURLs or signedlinks. No rootlicense file observed at planning time is only an observation, not a full rights audit.

Draft `DATA_CODE_AVAILABILITY.md` that matches verified access. If public release is pending, say so; “available on request” needs an actual responsibleauthor and viable arrangement. Don't inventDOIs, anonymouslinks, repositoryaccess or perpetualhosting. Verified publicstatus and redistributionclearance are distinct gates.

Acceptance: every availability claim resolves to an observed accessible artifact or explicit truthful condition; no “released” solely because a localbundle exists. Missing public deposition may remain a future action if the chosen policy permits the stated arrangement; required inaccessible supporting evidence blocks submission readiness.

### E. Build a minimal local reproducibility candidate

Prepare `REPRODUCIBILITY_MANIFEST.json`, `REPRODUCE_OFFLINE.md` and an explicitly local archive only when its members pass rights/privacy checks. Use an allowlist, not a workspaceZIP. Separate identifiedprivate, anonymousreview and potentialfuturepublic manifests; apublicmanifest is only a proposal untilI12permission.

Give distinct procedures for: building PDFs; reproducing saved descriptive/statistical derivations from frozen outputs; reconstructing optional corpus/index assets; and performing costly future provider experiments. Default workflow must not launch paidcalls, downloadmodels, invoke historical mutablegenerators or regenerate working macros. Record environment/versions/commands and unsupported historical linkage rather than promise bitwise reproduction of remoteLLMresponses.

Exclude .envfiles, tokens, credentials, serving-account metadata, usernames/absolutehomepaths, rawprivatechats, gitobjects/config, environmentdumps, caches, staleauxfiles and duplicategigabytecorpora. Review exact allowlisted files for accidental secrets/identifiers before copy/export; report findings by file/line/type, never echo matched secretvalues. Hash retained originals and any redacted derivative separately; document every redaction and its scientific effect. Do not falsify old manifests to make derivative bytes look original.

Acceptance: deterministic member list; collision/pathtraversal/reparse checks; fullhashverification; no silently required externalworkspacefile. A harmless local extraction/membercheck belongs here; final fresh clean-room rebuild/certification remainsI11. ProviderexecutionneverfollowsfromREADMEinspection.

### F. Prepare and audit the anonymous candidate

Copy from the accepted baseline into isolated `candidate/anonymous/src/`. Keep an `ANONYMIZATION_CHANGELOG.json` recording every exact identity/administrative edit, old/newhash and remaining risk. Inspect visible text, sourcecomments, authorblocks, figureannotations, supplementtext, acknowledgments, PDFmetadata/bookmarks/attachments, filenames, links and repositoryidentifiers. Neutralize author-identifying links in the review variant with a truthful access arrangement; don't replace an accessible URL with a fake anonymous endpoint.

Use neutral assessor labels while preserving qualifications, AIassistance and the factual study design. Do not remove adverse evidence or scientific provenance just because it is awkward. If scientific traceability and anonymity conflict, prepare a private editorial explanation/decision; don't silently erase the necessary evidence. Do not promise impossible anonymity against publicpreprints/searches.

Build isolated candidates with the recorded cached toolchain, preserve logs, then inspect all pages affected by identity/declaration/linkreflow and metadata. Compare actual diff and scientific values/objects/18themes; validate actual internal and crossdocumenttargets after any filenamechange. Strip prohibited metadata through reproducible generation, not a screenshot-onlycheck. Maintain accepted workingPDFs intact.

Enforce25mainphysicalpages for any candidate proposed under the current advisorcontract. If identity/declaration changes push past it, keep the candidate isolated and report measured options; no unreadable shrinkage or unapproved content deletion. I9referenceformat/templatechanges remain explicitly deferred. An anonymousIEEEcandidate may be privacy-ready while still failing the target'scitationstyle: report both facts.

Acceptance: no knownidentifiers in reviewer-visible files except explicitly justified/approved exceptions; no privacy leak from associated source/archive; scientificdiffbounded; actual linkswork; pagecountverified. Partialanonymization is not labelled ready.

### G. Supplement and editor-information packaging

Prepare `SUBMISSION_FILE_MAP.json`: purpose, reviewvisibility, sourcefile, buildoutput, intendedportalfield, OnlineResourcelabel/caption where applicable, checksum and unresolvedplacement. Preserve a role-to-filename map so renaming cannot break xr-hyper or scientific references. Check the reviewversion independently from the lateridentifiedpublicationversion; do not add authornames to anonymoussupplements because generic SIinstructions ask for them.

Draft coverletter and administrative statements locally if needed, clearly marked for authorreview. The final I11five-pointresponse remains separate and must not imply expertcomponentcomplete. Authors confirm originality, non-simultaneoussubmission and any overlap; do not auto-certify. Editorial identifiers/titlepageinformation stay private until actualsubmission requirements are confirmed. No messages are sent.

Acceptance: each file has one role/visibility; captions and citations resolve; private fields cannot accidentally enter reviewerZIP; any contradiction between genericSIidentityinstructions and anonymous-reviewpolicy has a recorded resolution or blocker.

### H. Validation, peer review and final status

Produce `VALIDATION_RESULT.json`, `PROTECTION_RESULT.json`, exact source/archive manifests, `OPEN_ITEMS.json` and `FINAL_REPORT.md`. Validate stableIDs/requiredfields/statusvocabulary, outputmembership, no placeholder or pendingauthorfield in a file labelled ready, no unsupported publicreleaseclaim and no anonymous/private collision. Small syntheticnegative fixtures should reject pathtraversal, duplicatearchivepaths, alteredhashes, privatefileinclusion, unsupportedavailability and unresolvedrequirementmarkedverified. Do not run broad projecttests or researchscripts.

Rehash selectedinputs/47workingsources/PDFs at the end; source membership must match. Preserve interrupted/rejectedoutputs and logs. Hash the final reviewpacket before Antigravityreceives it; request checks of actualfilevisibility, declarations/AIuse, availability/rights evidence, immutableprotection and unresolvedI9boundaries. The mailbox is user-relayed, not a livewake. Peerconcurrence is evidence, not authorconsent/submissionpermission. Resolve comments through newaddenda rather than modifying someoneelse'sreport.

## 6. Completion criteria and legitimate blockers

**I10 DONE** requires an author-confirmed requirements/declarations record, verified truthfulavailability arrangements, rights/privacy dispositions, a manifest-based local reproducibilitycandidate, anonymous/private submissionfilemap with reviewchecks, reconciledactualpeerreview and an honest venue/format dependencydecision. No required disclosure may be silently pending inside a “ready” export.

If the journal has not been selected, authorfacts/consents are missing, an essential supportingdataset cannot be made accessible lawfully, or I9format conflict is unresolved, record `PREPARATION_COMPLETE_BLOCKED` with the exact item, owner and nextdecision. Do not relabel that as completedsubmissioncompliance. Venue-neutraloutputs remain usable. No extra research or restorationofrejectedSpringerformat is inferred. A human may approve a narrower explicitlydefined I10preparationmilestone, but originalI10readiness remains separatelyreported.

I11starts from the frozen I10candidate and performs final fullreading/page-by-page/clean-room verification. I12alone authorizes exactpromotion/publicrelease/submission. On genuine I10completion, roadmap moves from9complete/1partial/3pending to10complete/1partial/2pending. Until then retain9/1/3.

## 7. Recovery and economical execution

- Unexpected baseline drift: save discrepancy and verify actual accepted successor; never silently reset47files.
- Policy conflict/stalewebpage: preserve source/date and record the narrow unresolved rule. Only later authorized author/editor clarification resolves it; no inventedportaltest.
- Missing authorfact: keep privatedraftpending; batch the minimum unanswered questions, continue all independentwork, and avoid repeatedpermissionrequests.
- Rights/privacy failure: exclude affectedcomponent fromexport, retain a manifestreference and viableaccessproposal; never sanitize originaldata inplace.
- Build/anonymity/linkfailure: repair onlyisolatedcandidate; rerun affectedchecks and actualpages. No sourceadoption bystealth.
- Review finding afterfreeze: create a newgeneration/diff and refresh changedidentities; previouspeerreviewdoesnotautomaticallycarryover.
- Completionreport must state what was prepared, verified, missing and prohibited; hashes are integrityevidence, not legal/scientific validation.

Use targeted source/manifests and cachedbuilds; avoid fullcorpus scans, verbose repeatedreports and retesting unchangedresearch. Work in one sustained authorizedbatch where possible, with only genuinelymissing humanfacts or externalactionpermissions stopping dependentwork. This planningturn does not begin implementation.
