# Bounded provenance disclosure: exact wording proposal

Codex, 12 October 2026. PROPOSAL ONLY. No manuscript edits/builds, config changes, experiment or API calls. User authorized preparation, not application. This supersedes the proposed prose of Antigravity-0056, not its independently confirmed evidence.

## P1: main Multi-Run Provenance item

Keep the existing numerical repeatability, concurrency, throttling and task-rubric disclosures. Change the existing date assertions from “ran on” to “are associated with file dates of”, and “on 14 September” to “with file dates of 14 September”. Describe other listed dates as recorded file dates, not proven execution dates. Do not promote all dates to logged timestamps.

Replace the sentence asserting that the pilot judge's identity is unrecorded with:

> The stored pilot ablation records identify a single Llama-3.3-70B judge, unlike the canonical dual-judge protocol; their scores are not directly comparable, and the historical execution date remains unestablished.

Add this bounded paragraph after the item, before Component-Level Ablation Matrix:

> Recorded provenance varies by experiment. The obscure-suite and famous-contrast records contain an engine hash matching the preserved Issue 18 source (SHA256 430fc1b3...), whose parsed Python syntax matches the inspected root source (0cca5cf4...); only a comment differs. Their records also contain vector-index fingerprints. Primary canonical, pilot, CaseFacts and CLERC result records do not identify their historical engine, graph and vector-index state by equivalent hashes. Temporal-probe prompt, context and candidate hashes identify payloads, not the generating code or graph version. The obscure/famous arms requested the same generator endpoint, but direct-call logs record a server response identifier whereas the engine wrapper records the requested identifier; backend weight invariance is not established. Supplementary Table S9 summarizes these boundaries.

Typesetting: use the existing cross-reference `Supplementary Table~\ref{supp-tab:run_provenance}`, not a hard-coded S9. Break the two hash prefixes with normal texttt syntax. Keep engine syntax equality separate from full runtime/dependency equivalence. Existing unrelated claim about same-day reruns remains outside this bounded new evidence correction and must not become stronger.

## P2: hub parameter clarification

After the current parameter tuple in the Hyperparameter Freezing item, add:

> In the recovered engine, degree greater than 50 activates high-degree handling; 75 incoming and 25 outgoing neighbors are directional selection budgets, subject to limits of 40 visited nodes and 35,000 structural-context characters. These controls describe the recovered source; they do not establish the exact settings of every historical experiment.

No config/runtime constant changes. A selected neighbor is not automatically a separately visited node; retain this distinction. Keep the original pilot/freezing claim attributed to its existing evidence, not infer it from this later code recovery.

## P3: Supplement Table S9 note and pilot row

Keep the authentic `tab:run_provenance` label, current ten rows, dates' source labels and query denominators. Do not rename this table S7. Do not add temporal update as if it were an eleventh original object.

Change pilot Models cell from “date not recorded” to “Single judge: Llama-3.3-70B (recorded endpoint)”; retain Date “date not recorded” and N=35. Add this note after the table:

> N denotes the population described in each row, not a uniform count of model calls. The 35-query ablation has 700 stored observations (four arms, five repeats); CaseFacts and CLERC each have 170 source questions and 510 stored arm-level observations (three arms). Obscure/famous engine hashes match a preserved source file (430fc1b3...), and index fingerprints are recorded. Primary, pilot, CaseFacts and CLERC records lack equivalent historical code/graph/index linkage. Temporal-probe hashes identify prompt/context/candidate payloads. The separate temporal-update file records 106 pair observations from 82 unique queries, a timestamp and active-graph/subgraph hashes; the timestamp is a recorded value, not independently authenticated time. File modification dates elsewhere are not execution dates.

These sample counts were independently inspected: pilot 700 rows, four arms of 175, run indices 1–5 each 140; all 700 judge_model_used fields name databricks-meta-llama-3-3-70b-instruct. Canonical file has 1,750 rows, unlike 350 primary TERRA questions. CaseFacts/CLERC population-to-arm distinctions must remain visible. Note expansion may require more supplement space; no 17-page guarantee is asserted.

## P4: Limitation 13 replacement

> Evaluation blocks differ in recorded dates, configurations and rubrics. File modification dates are not execution timestamps. The obscure/famous records identify a recovered engine source and vector-index fingerprints, but exact historical code/graph/index linkage remains unavailable for the primary, pilot, CaseFacts and CLERC results. Temporal-probe payload hashes do not establish the generating engine or graph version. The pilot records identify a single Llama-3.3-70B judge, unlike canonical dual judging; task-specific scores are not interchangeable. Category B/D context profiles differ without establishing different execution dates. Requested generator endpoint parity does not establish backend weight invariance. See Table~\ref{tab:run_provenance}.

Retain the limitation theme and saved original wording. This removes the now-overbroad “exact historical execution code is not preserved” statement for all blocks, rather than claiming every experiment is recovered.

## Deliberately excluded

Do not copy Antigravity's rewritten Data/Code Availability section. Public release, archive availability, exact cloud weights and reproducibility claims require separate verification. Current source is called inspected root source, not verified current release. Do not change distance units, thresholds, dataset identities, reported outcomes or runtime settings. An available script's name does not certify that it produced a historical result.

## Approval and verification gate

Request approval for P1–P4 as one bounded provenance-disclosure batch. Preserve a byte snapshot, apply only these changes, build main/supplement in isolation and review changed pages. Main must remain within 25 pages. If it exceeds the ceiling, stop and propose a shorter version rather than shrink tables/fonts or remove unique evidence. Supplement has no newly approved page ceiling; report actual pagination and readability. Return exact source diff, hashes, counts, logs and images for peer audit. No canonical promotion or experiment follows from approval.
