# TERRA: evidence-preserving editorial restart from the 39-page manuscript

Status: proposed plan only; no manuscript implementation is authorized by this document.

Prepared 2026-09-28. Claude is the prospective implementer; Codex is the independent auditor. Each execution phase requires approval and ends with a review checkpoint. Earlier compression approvals do not transfer to this restart.

## 1. Objective and order of priorities

Produce a precise, coherent, readable research article from the preserved 39-page manuscript, provisionally targeting 25–26 pages. Scientific accuracy and completeness take priority over pagination. Preserve the meaning of all unique methodological details, results, qualifications, limitations, tables, and diagrams. Improve prose by synthesis and removal of demonstrated repetition, not by suppressing evidence or making stronger claims.

“Q1-worthy” is a quality objective, not a certification or acceptance guarantee. There is no universal Q1 prose format. The target journal, article type, official template, page-count convention, supplementary-material policy, and current author instructions must be verified. The earlier 25-page maximum and the newly requested 25–26-page working range must be explicitly reconciled; 26 pages cannot be declared venue-compliant without that evidence.

The priority order is: correct science; complete evidence; understandable narrative; readable figures/tables; authentic venue compliance; compactness. A failed priority cannot be compensated for by a lower page count.

## 2. Verified restart baseline and findings

The restart source is `CANONICAL_ARCHIVE/`, not the currently promoted `Paper/` and not any earlier compressed manuscript.

- Archived `src/main.tex`: SHA256 `31db54c4b2771d34e1b3b59168fcdebea9b3b5e8198f9268f21298a61fc3fec4`.
- Archived `main.pdf`: 39 pages; SHA256 `757ad2ec03a205649cc97ee2bd06e30c06f41bc47dd857ced3019f3a8b7a38f3`.
- Archived `src/generated_stats.tex`: SHA256 `e4e369b7b7c3e55c4c541fc552f175018ea656c67193ebcf1dfb183a93756b73`.
- All 29 archived entries match the preservation manifest. The manifest distinguishes 26 active constituents, the PDF, and two historical bundles; the bundles are not active build inputs.
- The archived PDF renders Tables I–XXIII. The current 23-page `Paper/main.pdf` yields no rendered TABLE-caption matches in text extraction, corroborated by the inspected page overviews.
- The current `Paper/main.tex` has an outer conditional exclusion spanning approximately lines 335–747, with nested exclusions. Substantial experimental and empirical material is therefore present in source but absent from the PDF.
- The current source also defines reference fallbacks through `\anchorlabel`, including labels for evidence not actually rendered. A clean undefined-reference count under that mechanism is not proof of scientific-object integrity.
- Current rendered prose includes malformed reference wording such as “Table Supplementary Table S14, Panel A.”

These findings explain why the previous source-search and compilation gates could pass while the readable paper deteriorated. Earlier technical certification must not be treated as certification of information preservation or publication quality.

The preserved original also needs correction and presentation work. Inspection found densely scaled tables/notes and inefficient terminal appendix/reference pagination. It is an authoritative record of the study, not a guarantee that every sentence or caption is accurate.

Examples requiring evidence-based adjudication before compression:

1. Original `main.tex:115` says all computationally heavy operations are offline, despite online retrieval, verification, generation, and latency measurements.
2. Original `main.tex:139` describes a three-way router; implementation/specification evidence uses EASY/HARD classification. Distinguish route classification from the retrieval sources consulted downstream.
3. Original `main.tex:117` presents attention-dilution/context-cliff mitigation as an experimental conclusion. Identify a direct supporting experiment or describe this as design motivation rather than an established result.
4. Original `main.tex:399` describes LLaMA judging and elimination of circular bias. Reconcile the actual judge configuration separately for each canonical and legacy evaluation block; model separation does not eliminate every evaluation bias.
5. Original `main.tex:233` misdescribes insufficient context being passed as “false-non-entailment.” Distinguish false-positive entailment from false-negative entailment and preserve the admission that verifier errors are unquantified.
6. The FDR table notes identify ranks 5–7 and 11/12/15/16 with categories that do not match the displayed rows. Correct the explanatory text against frozen row identities. Do not alter numerical results or infer a new test from a stale note. Qualify “zero false refusals” to its particular gate/population rather than the whole system.
7. Broad novelty, “proves,” “ensures,” safety, and deployment language needs claim-level scrutiny against cited sources and actual experiments.

Inspection scope: archived and current manuscript sources/PDFs, manifests and relevant compression history, statistical/checking scripts, selected runtime/baseline paths, and routing/evaluation specifications. All pages of both PDFs were viewed in contact-sheet overview, with selected pages inspected at larger scale. This is not a completed row-by-row re-audit of every experiment or a full-resolution final visual certification. Dependency closure and that deeper audit are explicit execution tasks below.

## 3. Non-negotiable information-preservation contract

Every unique scientific information item receives an identifier and an explicit final location. An item includes its qualifications, not merely its headline number.

For a result, record: system/configuration; experiment/run/date; population; number of unique queries; repeated observations; denominator; metric/scale; all-query versus answered-only policy; estimate; uncertainty; statistical test/correction; reference artifact; limitation; source location; and final rendered location.

For a method, record its inputs, outputs, decisions, thresholds, failure behavior, assumptions, and tested versus merely proposed status. For a limitation, preserve its cause, affected scope, consequence, and unresolved status.

Each original item must end in one of these states:

- Preserved in main, possibly expressed more concisely.
- Merged with another occurrence, with proof that all unique content remains in main.
- Removed as an exact or semantic duplicate, identifying the surviving main occurrence.
- Removed as genuinely non-scientific/unnecessary presentation, with independent approval and justification.
- Proposed for supplement relocation, but NOT executed without separate user approval. Relocation is not the default compression strategy for this restart.

Do not call a shorter statement equivalent if it loses an assumption, negative finding, denominator, uncertainty, condition, exception, or reproducibility detail. Distinguish corrections of erroneous statements from compression; document the evidence and authorize the correction separately. Preserve the original in the audit trail, not as a known error in the revised paper.

Default: retain all 23 scientific tables and all three figures. Any removal or merge requires object-level dependency analysis and specific approval. Related objects are not interchangeable. Source-file count is not rendered scientific-object count.

## 4. Protected scientific content

The protected ledger must include, at minimum:

- 20,000-opinion corpus, its temporal/domain boundaries, filtering and fallback qualifications.
- Active graph: 145,366 directed edges = 145,310 CITES + 56 OVERRULES; historical benchmark index: 145,363. Keep artifact/version context attached to each.
- Primary benchmark: 350 distinct queries; A=100, B=100, C=75, D=75; five systems and 1,750 evaluation records. Category-B 3/4/5-node path composition: 63/32/5.
- Pilot ablation: 35 distinct queries, five repeated runs, four configurations, 700 execution observations. Repeated observations are not 700 independent queries; pilot Category D has five distinct queries and 25 run observations.
- Direct-LLM Category-B counter-result, all meaningful baseline advantages, answerability/faithfulness trade-offs, lexical-metric limitations, and uncertainty/statistical context.
- Category-D fatalities D033/D034 and 2/75 fatal outcomes; Category-A/B false refusals; refusal versus refutation versus total safe-handling distinctions.
- Curated OVERRULES dependence; absent independent labeled NLI validation; absent licensed-practitioner evaluation; limited external/temporal-leakage validation; corpus/task asymmetry and coverage.
- Retrieval/path recovery versus generated-answer/judge scores versus actual legal correctness. Automated adjudication is not human expert validation.
- Hosted-model variation, model/judge/run provenance, context ceilings, scoring clamps/amendments, and concurrent/sequential latency plus retry/throttling qualifications.
- Complete pre-specified M=20 FDR family, inferential conclusions and negative/non-significant results, and all 18 limitations.

This list supplements, rather than replaces, a complete source-derived ledger. Preserve every relevant table cell, caption, note, citation, equation, algorithmic condition, and implementation qualification, not just these prominent examples.

General reporting reference: the official [NeurIPS paper-checklist guidance](https://neurips.cc/public/guides/PaperChecklist) supports aligning claims with tested scope, disclosing limitations, and retaining important experimental details in the main paper. It is a useful independent reporting benchmark here, not the target journal and not a source of this project's formatting or page-limit requirements.

## 5. Audit-system changes required before editing

The existing `Paper/scripts/check_consistency.py` is not a sufficient acceptance gate. It uses fixed file paths, does not parse the advertised `--target` option, searches raw source including conditionally excluded material, counts distinct macro names rather than invocations, and checks selected abstract macro presence rather than full abstract/body semantic agreement.

Retain the historical checker unchanged as historical evidence. Build a separate, target-aware, non-mutating auditor in the new isolated workspace. It must report the exact resolved files being checked and fail if they differ from the requested workspace. Demonstrate read-only behavior through pre/post protected-file hashes.

Independent checks must include:

- Source dependency manifest, actual compiler input list, and final PDF identity.
- Active rendered section/table/figure/equation inventory and original-to-final object mapping.
- Unique labels, real destinations, citation resolution, printed numbers, and hyperlink targets. Never manufacture `r@...` fallback definitions or descriptive placeholder labels to hide missing objects.
- Cross-document references through a tested external-reference mechanism or an explicit verified reference map. A main-document reference must identify the right rendered supplementary object, not merely resolve syntactically.
- Searches for accidental conditional exclusion, unresolved placeholders, hidden material, truncation, duplicate objects, fabricated page numbers, and stale references.
- Scientific ledger coverage in active compiled content, plus human semantic review. Neither token matching nor automated similarity is proof of preserved meaning.
- Undefined references/citations, multiply-defined labels, duplicate PDF destinations, fatal/incomplete output, and geometric overflows. Classify legitimate warnings with evidence; do not suppress warnings to achieve a pass.

The actual statistical generator named in frozen headers must be traced. Packaging a similarly named older script is not sufficient reproducibility. Do not execute generators that write statistical macros or tables during this editorial task.

## 6. Phased implementation and approval gates

### Phase 0 — Baseline, venue, permissions, and dependency freeze

Reverify the curated archive and inventory all reachable manuscript/code/data/protocol dependencies. Distinguish source assets from stale PDFs, backup sources, old bundles, and build auxiliaries. Preserve per-file hashes for protected assets; establish an isolated restart workspace without modifying either archive or current `Paper/`.

Verify target-journal requirements and clarify whether references/appendices count. If the journal remains unspecified, record 25–26 only as a project target and withhold venue-compliance certification. Obtain a specific scope for any Claude coordination; do not start Claude editing as part of preflight.

Deliver: baseline/dependency manifest, protected-file scope, exact source/PDF identities, venue requirements or unresolved gate, permitted editing boundaries. Stop for approval.

### Phase 1 — Scientific/provenance reconciliation and complete ledgers

Read the complete archived manuscript, all active tables/figures/bibliography, and experiment-specific source artifacts. Trace each claimed result to the correct frozen macro/raw artifact/run protocol. Confirm model identifiers, evaluation populations, repeated-run dependence, score definitions, exceptions, and test interpretation. Review cited literature through primary sources when needed.

Create numerical, methodological, claim, limitation, citation, and rendered-object ledgers. Resolve the seven identified wording problems and any newly discovered contradictions at the evidence level. If the evidence cannot settle a statement, mark that statement unresolved rather than inventing a correction.

Deliver: row-level ledgers, contradiction decisions, all 18 limitation mappings, reproducibility gaps, proposed precise corrections. No editorial compression yet. Stop for approval.

### Phase 2 — Corrected isolated scientific baseline

Apply only approved accuracy/scope corrections in the new isolated copy. Freeze numerical macros and data. Do not homogenize historical evaluation configurations or update old values to current ones. Inspect affected figures/captions for agreement with actual runtime behavior.

Compile from a clean build directory; verify every original section and scientific object still renders. Audit changed sentences against their evidence and inspect affected PDF pages. Record the corrected baseline page count; it need not remain exactly 39.

Deliver: correction diff, evidence for every correction, full object inventory, compiler transcript, source/PDF hashes, affected-page QA. Stop for approval.

### Phase 3 — Narrative and measured space budget

Design the article around the actual research problem, architectural decisions, experimental design, results, interpretation, and limits. Describe tested outcomes separately from design motivations and future extensions. Do not invent preregistered research questions or experiments retrospectively.

Measure text and float footprint by section in the corrected PDF. Assign provisional section budgets including tables, figures, bibliography, captions, and notes. Identify repeated information by ledger identifiers, not by superficial phrase similarity. Retain important context in the main paper.

Use mostly connected paragraphs; retain lists, algorithms, definitions, or structured limitations only where they improve comprehension. Build paragraphs around purpose, evidence, interpretation, and qualification—not a forced formula or ornate language.

Deliver: section outline, redundancy map, object disposition proposals, measurable page/word budget, approved micro-batches. Do not promise that a 13–14-page reduction is feasible before testing. Stop for approval.

### Phase 4 — Editorial pilot: introduction and related work

Rewrite one approved contiguous block. Consolidate repeated motivation and contribution recaps, distinguish the architecture from prior systems without unsupported universal novelty, and synthesize literature by substantive differences. Preserve citations attached to their claims.

Compare the original and revised PDFs at ordinary reading scale. Independently test whether a reader understands the research problem, specific contribution, scope, and negative qualifications at least as well as before. A concise but evidence-free introduction fails.

Deliver: paragraph-level equivalence ledger, source diff, citation audit, page effect, side-by-side reader-quality assessment. Approve the editorial approach before applying it elsewhere.

### Phase 5 — Methods, corpus, and experimental-design rewrite

Proceed in small batches: architecture and routing; verifier and failure handling; corpus/graph construction; benchmark design; baseline adaptation; evaluation/judge/statistical protocol.

Preserve equations, thresholds, decision rules, labels, source versions, task populations, unique-query versus repeated-run counts, and reproducibility conditions. State online/offline operations accurately. Explain generated procedural traces without implying they are authentic judicial reasoning if they are model-derived representations.

Remove repeated explanations only after marking their surviving main location. Compile and perform source/PDF/meaning review after each batch. No multiple unreviewed batches.

### Phase 6 — Results synthesis with every substantive comparison intact

Rewrite by empirical question rather than repeated promotional findings lists. Let retained tables carry detailed numbers; prose explains what matters, what did not improve, how uncertainty should be interpreted, and the applicable scope. Avoid copying every table row into prose while preserving all decision-relevant quantitative evidence.

Audit all-query/answered-only distinctions, judge versus retrieval metrics, safety categories, pilot versus primary experiments, and statistical test/correction context. Preserve unfavorable and non-significant findings visibly. Do not present a lexical score as legal-quality evidence.

Deliver each batch with exact rendered evidence locations, retained negative findings, changed prose, actual page count, and claim-level audit. Stop for review between blocks.

### Phase 7 — Discussion, all limitations, conclusion, and final abstract

Consolidate interpretation rather than restating the results. Preserve causal uncertainty: component ablation does not independently validate an entailment classifier. Maintain deployment, corpus, expert-evaluation, and generalization boundaries.

All 18 limitations remain individually traceable in main, even if expressed under a smaller number of coherent thematic subsections. Preserve each limitation's practical consequence; do not soften it into generic future work. Rewrite conclusion and abstract last, against the validated body, without broader claims.

Deliver: 18-to-final limitation mapping, discussion claim audit, abstract/body alignment, PDF reader-quality review. Stop for approval.

### Phase 8 — Evidence-preserving table/figure and layout pass

Improve presentation of the retained objects: reduce repetitive notes, explain reusable definitions once with a precise reference, wrap columns sensibly, and use appropriate orientation/width where the venue allows. Preserve cell values and interpretation. Inspect especially the dense original performance tables and long computational/FDR notes.

Use normal document flow and real object labels. Correct appendix/float placement and bibliography separation without forced artificial page anchors. Do not crop PDF pages, hide content, shrink global fonts/margins/line spacing, or apply arbitrary negative spacing to force a count.

Merges or removals are proposed exceptions, not automatic permissions. Approve only when every scientific field remains unambiguous and the reader's understanding improves. Supplement relocation requires a separate user decision; this plan does not authorize recreating the earlier supplement-first compression.

Deliver: object-level before/after comparison, numerical cell audit, full notes/citation preservation, measured space effect and affected-page visual review.

### Phase 9 — Page-budget decision

Compile the integrated draft and compare actual footprint with the approved budget. If it is 25–26 pages, readable, and venue-compatible, stop compression. Do not compress further for arbitrary margin below the target.

If over budget, identify remaining genuine repetition from the ledger and measured PDF flow. Propose one coordinated, bounded change with a credible mechanism; do not repeatedly test arbitrary spacing knobs. If no lossless/readability-preserving solution is supported, report the conflict and seek a specific decision about approved merges, supplements, or permitted length. Never silently weaken the paper to satisfy pagination.

### Phase 10 — Independent whole-document certification

Codex reads every revised section and checks every original information identifier against its actual final rendered location. Verify all table cells/notes, figures, equations, limitations, citations, numerical scopes, and negative findings. Confirm no original core evidence disappeared through conditionals or alias references.

Render and inspect every page at legible scale, not only contact sheets or representative pages. Review table readability, clipping/overlap, equations, captions, heading orphans, float/appendix order, spacing, references, and link destinations. Contact sheets are supplementary overview evidence, not a replacement for page inspection.

Run a separate reader-quality comparison: can a reviewer understand and assess the full experiment from the main paper; is the narrative clearer than the original; are limitations proportionate and explicit; does evidence support the strength of every conclusion? A structural or hash pass cannot override a reader-quality failure.

Deliver: complete ledger disposition, per-page visual findings, reference/object graph, provenance hashes, exact checks/commands, unresolved scientific gaps, and an accept/corrections-required/redo recommendation. Stop for user/reviewer decision.

### Phase 11 — Clean-room package and final handoff, without promotion

Assemble only approved active sources and authentic reproducibility artifacts. Build after extraction into a fresh empty directory without old auxiliary files. Record compiler version, font/package dependencies, environment, exact commands, exit codes, logs, source hashes, and resulting PDF hashes/counts.

Verify that the extracted build reproduces the approved content/object/reference structure and visual layout; if PDF byte hashes differ, investigate metadata/toolchain rather than assume equivalence. Include any separately approved supplement and verify all cross-document dependencies. Confirm protected originals/data/macros remain unchanged.

Deliver the new manuscript package and audit report. Do not overwrite `Paper/`, update distribution bundles/checklists, or call promotion complete. Promotion requires a distinct explicit approval and a fresh pre-promotion manifest, recoverable snapshot, clean canonical rebuild, and final semantic/visual verification against the accepted new package.

## 7. Mandatory execution protocol and Claude coordination

Before every batch, preserve every editable input and dependent source byte-for-byte, including supplements if involved. Hash snapshots, working sources, frozen assets, and PDFs. Capture exact commands and actual exit statuses. Keep experimental and accepted build outputs separate.

If a candidate is rejected, restore all edited sources from the captured snapshots, verify hash identity, and compile into a clean directory. Never reconstruct a rollback manually or restore from an unverified older copy. A PDF from a failed build is not valid pagination evidence.

Claude edits only the approved isolated paths and current batch. Codex audits independently and may request a pause/correction but does not silently patch Claude's manuscript to make the audit pass. Each batch supplies its full changed-file list, before/after snapshots, item-level change ledger, logs, PDFs, and approval status.

Proposed shared checkpoint protocol: Claude marks a batch READY with hashes, then stops; Codex reviews the frozen state and records ACCEPT, CORRECTIONS REQUIRED, or STOP. Claude must not continue across an unaccepted gate. A shared file is a cooperative protocol, not a technical guarantee against an agent that ignores it.

The Claude desktop application was discoverable during planning. Direct coordination may be possible once the relevant project conversation is identified and implementation is authorized. Do not inspect unrelated conversations or send implementation instructions now. Point-in-time inspection and authorized messages do not guarantee continuous real-time supervision or instant interruption. If UI coordination is unreliable, use the same checkpoint reports through the user; file-based approval gates remain mandatory either way.

## 8. Risks: eliminate controllable causes; disclose irreducible uncertainty

Information hidden while tests pass: solve through active compiled-object inventories plus item-to-rendered-location review. Source presence alone is never accepted.

Claims made more impressive by shortening: solve through scoped claim tuples and independent semantic comparison, with protected adverse evidence and limitations.

Wrong historical values or evaluation denominators: solve through artifact/run-specific provenance, frozen data/macros, and verification of every reused value. Do not substitute current code for the historical experiment without evidence.

Dead or misleading references: solve through real labels attached to real objects, clean auxiliary generation, destination testing, and printed-identity review. Ban fabricated fallback reference definitions.

Rollback/provenance drift: solve through byte-preserved snapshots of all edited/dependent assets and accepted immutable checkpoints.

Tables unreadable after compression: solve through native-scale page review and content-preserving redesign; reject a layout that relies on illegibly small text even if it fits.

Wrong journal format or page allowance: solve by obtaining the named venue's official current requirements before final budgeting/compliance claims.

Editorial compression cannot repair missing experiments. Solving the practitioner-evaluation and independent-NLI-validation gaps requires separately authorized study design, appropriately qualified evaluators/labeled data, analysis, and resources. Until such studies exist, accurately limited claims and transparent disclosure are mitigations, not solutions to those evidence gaps. Do not invent professional validation or promise that writing alone guarantees acceptance.

No plan can guarantee zero future risk, reader disagreement, or Q1 acceptance. What can be required is explicit coverage, controlled changes, independent evidence, and a stop whenever a gate fails.

## 9. Current stop and approval request

Only diagnostic inspection, PDF render artifacts, and this planning document were produced. No manuscript, bibliography, source figure/table, numerical macro, dataset, distribution bundle, or checklist was edited for this restart.

Recommended approval: approve this strategy and authorize Phase 0 only. Provide the target journal/article type or explicitly retain the page range as a provisional project goal. Claude should receive the full plan, not only a shortened execution prompt. Every subsequent phase remains subject to its own audit and approval.
