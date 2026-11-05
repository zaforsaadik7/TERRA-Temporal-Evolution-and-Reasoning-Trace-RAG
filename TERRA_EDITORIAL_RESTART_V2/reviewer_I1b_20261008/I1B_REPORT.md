# I1b: stored-record reconciliation of 66 versus 62 chains

Codex, 8 October 2026. Authorization: user said “okay, lets start working on the next task” after the proposed read-only I1b audit. This report does not authorize manuscript correction, a new retrieval/model run or promotion.

## Finding

Both numbers reproduce under the same existing matcher, but on different stored contexts. The paper's claim that the sensitivity baseline exactly reproduces the primary canonical result is false as stated. This is a dataset/provenance conflation, not a four-query arithmetic typo.

| Stored input | Full recovery | Gold-node hits | Macro recall | Micro recall | Complete 3/4/5-node strata |
|---|---:|---:|---:|---:|---|
| terra_baselines_eval_raw.json | 62/100 | 295/342 | 86.0833% | 86.2573% | 37/63, 20/32, 5/5 |
| data/terra_canonical_v2_eval.json | 66/100 | 302/342 | 88.9167% | 88.3041% | 49/63, 16/32, 1/5 |

The 100 Category B benchmark queries have 342 targets, partitioned 63/32/5 by length. Neither evaluation file has duplicate pipeline/query keys. The other three retrievers produce identical aggregate values between these files: Flat 1/100 (macro 26.8%, micro 26.3158%); GraphRAG 9/100 (35.7333%, 35.0877%); HippoRAG 21/100 (68.5167%, 66.9591%). Panel A/B TERRA macros match canonical-v2 results at printed precision. Panel C historical macros match the older records. No value should be blindly changed from 62 to 66 or vice versa.

## Per-query differences

All 100 TERRA Category B context strings differ between the files. Mean stored length is 1,342,599.82 characters in the older file versus 41,268.11 in canonical v2. Gold match sets differ on 36 queries. Thirteen newly complete recoveries and nine lost complete recoveries produce the net increase of four:

- Gained: B036, B044, B046, B051, B053, B056, B058, B067, B071, B074, B078, B094, B100.
- Lost: B001, B021, B027, B041, B061, B081, B082, B083, B087.

stored_context_recount.json contains all 100 targets, matched target sets, full-recovery decisions and context lengths, not just the aggregate difference.

## What the sensitivity parity actually supports

The saved data/issue26_hyperparameter_sensitivity.json baseline has 62/100 and the older 37/20/5 stratum counts. Its saved gold intersections equal the older stored-context intersections on 100/100 queries, but canonical-v2 intersections on only 64/100. Its full-context ID sets equal those extracted from older contexts on 100/100, but canonical-v2 sets on 0/100. Its traversal-header sets also match older contexts on 100/100.

These comparisons substantiate the saved sensitivity result's relationship to the older raw records. They do NOT rerun or independently certify the traversal engine, nor prove byte-identical text reproduction. The sensitivity script reads terra_baselines_eval_raw.json, freezes anchors from its context, and evaluates conditional traversal. Its parity checks test sets and metrics, not complete context bytes, fresh vector retrieval or the generator. “100/100 bit-identical parity” is therefore too broad even for the older input.

Canonical-v2 Category B records carry _source_run=issue6_deployed. Older records carry timestamps from 5 September 2026. These are recorded fields, not authenticated code/configuration lineage. Why each stored context changed, and the exact code/graph/settings of that transition, are not established by the present arithmetic. Antigravity is asked for the existing provenance records, not a new experiment.

## Metric boundary

Used only the existing pure match_node_in_context function, extracted through AST without importing or running production modules. It counts target IDs anywhere in context, or a title prefix (before ' v. ') longer than four characters. “Full path” means every target matches; it does not verify ordered connected citation edges, legal correctness, or that each title substring uniquely identifies the intended case. Reproduction of this operational metric is not independent validation of entity matching. Any stricter metric would be a separate approved methodology change, not a silent repair here.

## Recommended bounded correction, not applied

Keep canonical-v2 Panel A/B counts and the historical sensitivity counts. Identify Panel C as a separate legacy-context-conditioned sensitivity analysis rather than an exact reproduction of canonical-v2 performance. Replace the caption, Section 1 heading, notes and main sensitivity paragraph's “published/canonical baseline” and “bit-identical” language with explicit older-record identity, matched-set scope and the fact that 62/100 is distinct from primary 66/100. Clarify that frozen context-derived anchors do not re-evaluate original vector retrieval. Avoid calling the bounded 61/100 sensitivity result the canonical-v2 engine without lineage proof. Preserve adverse length-specific differences, particularly old 5/5 versus current 1/5.

Exact replacement wording should follow Claude review and any existing provenance evidence from Antigravity, then a user-approved isolated edit/build/PDF checkpoint. No fresh traversal or API call is needed to demonstrate the present contradiction.

## Evidence and safeguards

evidence_manifest.csv pins 11 source/record files. Benchmark hash 8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3; older raw 54e4b34b7c435b612690409dbf59a066ea53c7bc99497dcd683af8e22cc40d63; canonical v2 95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507; sensitivity 6c85eeccf6fb98fee17672d467942e7cb74cb206d80d53dcad473c4eb6d54f07. Reproduction command is recorded in REPRODUCE.md and writes no protected output. Full production generators were not executed: they overwrite statistics/summaries or perform new retrieval.

Working main remains 35776773180a090e94039c6058e1d359f687fae809cfeb15183ba4f7585d433c. No manuscript, statistics, datasets, graph, runtime code, supplement or PDF changed. No new build or rendered-PDF certification was needed or performed for this read-only evidence gate. Existing 24-page candidate remains the I1a package. This is Codex's evidence audit; Claude review is pending.
