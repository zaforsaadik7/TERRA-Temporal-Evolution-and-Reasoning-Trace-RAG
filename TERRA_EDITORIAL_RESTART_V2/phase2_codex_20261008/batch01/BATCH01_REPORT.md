# Phase 2 Batch 1 — implementation checkpoint

Author/implementer: Codex. 8 October 2026, Asia/Dhaka. **Implementation self-verification, not independent audit.** User approval is recorded in `USER_AUTHORIZATION.md`; Antigravity and Claude supplied evidence, not execution permission.

## Result and stop

**Approved patch implemented; main rebuild succeeds at 24 pages. Independent Claude audit pending.** No next batch or promotion started. F01 is repaired in the current main figure/dependent prose, but not closed across the package: stale supplementary descriptions remain for the separately approved reconstruction/repair batch.

## Changes — exactly two working files

| File/location | Previous problem | Applied change |
|---|---|---|
| `working/src/main.tex:119` | All heavy computation called offline; fast-route description vague | Offline corpus construction distinguished from online routing/retrieval; EASY anchor retrieval explicitly omits graph expansion. Category A/B latency population labels retained. |
| `working/src/main.tex:145` | Graph traversals called offline | Extraction/scaffold/index construction offline; retrieval, HARD traversal, grading and generation online. Existing latency values explicitly attributed to Category A/B, not EASY/HARD populations. |
| `working/src/main.tex:151` | Caption implied generic BFS/optional proximity flag, did not distinguish branches | Caption separates extracted CITES/curated OVERRULES, deterministic scaffolds and opinion snippets; EASY versus HARD retrieval; evidence checks and empty-context/failed-check refusal. |
| `working/src/main.tex:580` | “parametric Fast Path” | Anchor retrieval and entailment grading without graph expansion. |
| `working/src/figure_1_system_architecture.tex` — edge box | Unsupported classifier/analyzer implication; CITES only | Edge Construction: Extracted CITES Links; Curated OVERRULES Relations. No new edges or graph version. |
| Same — scaffold box | <=150-word synthesis implies the early prototypes describe the indexed population | Deterministic Procedural Substrate / Fixed Five-Step Scaffold. Early 150-word prototypes remain described, correctly distinguished, in main prose. |
| Same — router/branch labels | L2 pre-filter presented as routing mechanism; “HARD/RAG” versus No-RAG EASY | Structured EASY/HARD Decision; HARD branch labelled HARD. This removes misleading branch terminology, not the main's separately disclosed proximity-flag limitations. |
| Same — EASY box and arrow | Direct generation/No RAG bypassed grader | Grounded Fast Path: Anchor Retrieval (No Graph Expansion); arrow joins the shared grader, not the generator. No unverified k=1 value was added. |

`source.diff` is the exact bounded patch. No result table, generated macro, model setting, data record or graph was edited. Original/canonical sources, historical evidence, supplements, delivered PDFs, bundles and checklist remain unchanged.

An additional source check found **1,124 uses of locally defined macro names** in `main.tex`; the before/after per-name usage counters are identical. This corroborates the bounded patch and unchanged statistics files; it is not a new universal result-value certification.

## Baseline and provenance

`baseline/working_src/` is the byte-preserved working dependency tree, including bibliography, existing bbl, tables, figures and frozen macros. `baseline/r30corr_v1/` preserves all **12** previously snapshot-less derivative files, including the 16.6-MB compressed graph; no unavailable uncompressed file was invented. `baseline/main.pdf` preserves the delivered pre-batch PDF. `baseline_manifest.json` records per-file hashes and sizes; it was rechecked before the build.

`protected_baseline.json` retains the prior 131-input identities. Post-patch verification identifies exactly the two allowed working source changes, with **zero unexpected changes**. Historical semantic reports/manifests are unchanged and now identify the *pre-Batch-1* state, not the edited working source.

Before hashes: main `b950bc09242d72796260c6b359324cce7c6283ffcb95f994e78a095b8f817a19`; Figure 1 `55b1f1201479c18f4ac85eeb1138c8d6c037434b398ab0a510ce3c6dc6eb05af`.

After hashes: main `49107cfec13dcd51ec269d53e877984f855d0a7487092991881047576d018275`; Figure 1 `49599139921b02034d53a562530bb5df537e3a81ece0948a9b5ea46f9fe0efd8`; newly built PDF `d9cbd3928f5b1d0b788a54bb5bec399b3e6aedc70bce79aaface22d494f04596`.

## Build and logs

Compiler: existing **Tectonic 0.17.0**. Command:

```powershell
& 'F:/TERRA -Copy/scratch/tectonic/tectonic.exe' -C -k --keep-logs main.tex
# cwd: F:/TERRA -Copy/TERRA_EDITORIAL_RESTART_V2/phase2_codex_20261008/batch01/build/src
```

Exit **0**, **24 pages**, before **24**. Zero undefined references, undefined citations, multiply-defined labels and duplicate-destination diagnostics. **427 font warnings**, compared with 426 in the baseline; this is not a warning-free build. Two overfull diagnostics remain 1.30309/14.04836 pt, same magnitudes as baseline, with line numbers shifted within the enlarged caption's page. Full log and console retained. No new fatal diagnostic occurred.

Source/build utility commands:

```powershell
& 'F:/TERRA -Copy/venv/Scripts/python.exe' -X utf8 'F:/TERRA -Copy/coordination/terra_antigravity/phase2_batch01.py' prepare
# Baseline creation only; refuses to overwrite it. Do not run again.
& 'F:/TERRA -Copy/venv/Scripts/python.exe' -X utf8 'F:/TERRA -Copy/coordination/terra_antigravity/phase2_batch01.py' build
& 'F:/TERRA -Copy/venv/Scripts/python.exe' -X utf8 'F:/TERRA -Copy/coordination/terra_antigravity/phase2_batch01.py' manifest
```

One pre-patch guard initially selected the wrong caption line; it stopped before any source write. Correct line 151 was then used. No failed build or hidden content patch resulted. PDF-operation bookkeeping hook ran successfully before the first authoring patch.

## Rendered review

Extracted page text changes are confined to **1, 2, 3, 4 and 18**; all other 19 page-text strings match baseline. All five changed pages were inspected as images; Figure 1/caption additionally inspected at higher resolution. Observed: EASY arrow reaches the grader without crossing box text; offline labels fit; caption and following equation/body have no collision; affected prose remains within page boundaries. No new clipping/overlap was observed on these pages.

This is bounded post-patch QA, not fresh final whole-document certification. The figure retains the existing scaled layout; small fine-print labels and unrelated tiny result tables still require the later readability review. Do not describe this diagram repair as Q1-layout certification.

## Unchanged scientific caveats / remaining dependencies

Direct-LLM counter-results, false refusals, D033/D034, curated-label dependence, absent practitioner/independent NLI validation and graph-version distinctions are not edited. The inconsistent latency rows and net macros, temporal provenance/inference issues, release-pending wording, stale supplement notes/references and unreadable result tables remain open. The graph release clause was intentionally not changed in Batch 1.

The fresh PDF is `build/src/main.pdf` here. The old `working/build_test/main.pdf` remains the pre-batch artifact; do not mix it with the new working source or claim it was updated. No canonical PDF/source was promoted.

## Independent review request

Claude should inspect this source diff, baseline identities, both Figure 1 versions, all five changed pages, exact numerical/claim preservation, and any unintentional diagram implication. Return PASS/corrections required and stop. No Batch 2 execution follows automatically.
