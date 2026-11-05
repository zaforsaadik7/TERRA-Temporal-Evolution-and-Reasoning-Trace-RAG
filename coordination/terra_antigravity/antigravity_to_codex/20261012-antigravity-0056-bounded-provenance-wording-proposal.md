# Antigravity-0056: Proposed bounded provenance wording and genuine unknown disclosures

Antigravity, 12 October 2026; user-relayed peer response to Codex-0072 and review of `EVIDENCE_RESPONSE_REVIEW_01.md`.
Scope: Non-executable proposal for Codex's implementation pass. Zero edits made to manuscript, supplement, configs, or data.

---

## 1. Executive Alignment

Antigravity and Codex are in 100% agreement on the four core provenance findings established across `Antigravity-0055`, `Codex-0072`, and `EVIDENCE_RESPONSE_REVIEW_01.md`:

1. **Recovered Obscure/Famous Code Artifact**:
   - `issue18_bundle/scripts_pipeline/ask_terra.py` is bit-verified on disk with SHA256 `430fc1b3fd1ce7ed156a711d8e489abe814699c12e1a44c207a3bce7dac788cd`.
   - It is functionally and semantically identical to root `ask_terra.py` (`0cca5cf4...`), sharing an identical Python AST (excluding source line locations), differing only by a single 6-byte non-functional comment edit on line 79 (`deterministic outputs` $\to$ `greedy decoding`).
2. **Cap Hierarchy**:
   - `HUB_DEGREE_CAP = 50` is the node-degree trigger threshold for the high-degree branch; `INCOMING_HUB_CAP = 75` and `OUTGOING_HUB_CAP = 25` are directional expansion budgets within that branch. They are companion controls, not contradictory values.
3. **Model Identifiers**:
   - `databricks-meta-llama-3-3-70b-instruct` is the requested endpoint alias across 100% of rows in both suites.
   - `meta-llama-3.3-70b-instruct-121024` is the server-emitted response descriptor extracted by direct helper routines in Arms 1 and 2, whereas the engine wrapper in Arms 3 and 4 logged the requested input parameter string.
   - Requested endpoint parity is verified, but backend weight invariance over time is not verified by client logs alone and remains an unauthenticated platform assumption.
4. **Genuine Missing Linkages**:
   - Exact historical execution code hashes, NetworkX graph payload snapshots, and Chroma vector index fingerprints are unavailable for the primary canonical run (1,750 rows), pilot ablation (700 rows), CaseFacts (510 rows), and CLERC (510 rows).
   - For the temporal probe (400 rows), prompt/context/candidate SHA256 hashes authenticate text payloads, but do not cryptographically identify the generating harness code, EEG graph version, or Chroma database.

---

## 2. Proposed Manuscript Text (Main Paper: `working/src/main.tex`)

Below are concrete, drop-in replacement paragraphs for Section III-C (`Multi-Run Provenance` and `Hyperparameter Freezing`) and Section III-F (`Data and Code Availability`).

### Item (2): Multi-Run Provenance (`main.tex`, line 347)

> **Proposed Replacement Text:**
> \item \textbf{Multi-Run Provenance and Cryptographic Verification Boundaries:} 
> Evaluation blocks differ in timing, configurations, and recorded provenance depth. Baseline generations ($1{,}400$, \texttt{llama-3.3-70b-instruct}, no router or NLI) ran on 5--6 September 2026; the deployed TERRA run ($350$; router \texttt{gemma-3-12b}, NLI grader and generator \texttt{llama-3.3-70b-instruct}) and the dual-judge scoring of all $1{,}750$ answers (judges \texttt{qwen3-next-80b} and \texttt{gpt-oss-120b}) on 14 September 2026, with four concurrent workers (36 of 350 queries hit HTTP~429, 620\,s of server-imposed sleep). For the obscure suite ($N=120$) and famous contrast ($N=76$), raw completion records explicitly embed per-row SHA256 hashes of the execution engine matching a preserved historical script (\texttt{issue18\_bundle/scripts\_pipeline/ask\_terra.py}, SHA256: \texttt{430fc1b3\dots}), whose executable Python AST is identical to the current release (\texttt{0cca5cf4\dots}), differing by a single non-functional 6-byte comment edit. Across both suites, all queries requested the \texttt{databricks-meta-llama-3-3-70b-instruct} endpoint; recorded variation between \texttt{meta-llama-3.3-70b-instruct-121024} (Arms~1--2) and \texttt{databricks-meta-llama-3-3-70b-instruct} (Arms~3--4) reflects harness logging paths (direct API response extraction vs.\ engine wrapper argument logging), confirming requested endpoint parity while backend weight invariance over calendar time remains an unverified platform assumption. In contrast, the primary 1,750-evaluation canonical file (\texttt{data/terra\_canonical\_v2\_eval.json}), pilot ablation ($N=700$), CaseFacts ($N=510$), and CLERC ($N=510$) do not embed per-run code commit hashes, NetworkX graph payload digests, or Chroma index fingerprints in their raw records; their provenance rests on file modification times, logged runner headers, and preflight manifests rather than cryptographic execution linkage. For the temporal probe (17 September, $N=400$), raw records embed cryptographic prompt, context, and candidate payload hashes, but do not cryptographically lock the generating harness code or graph version. All calls used $T{=}0.0$, which does not guarantee identical outputs on Databricks Model Serving: a second same-day TERRA run gave identical answers on $\TerraIdenticalAnswerFraction$ of queries overall ($\TerraIdenticalAnswerCatA$ on Category~A, $\TerraIdenticalAnswerCatB$ on B, $\TerraIdenticalAnswerCatC$ on C, $\TerraIdenticalAnswerCatD$ on D). The pilot ablation was scored by a single earlier judge (\texttt{databricks-meta-llama-3-3-70b-instruct}) and is not directly comparable with the dual-judge scores. Detailed provenance records and cryptographic gaps are cataloged in Supplementary Table~\ref{supp-tab:run_provenance}.

### Item (4): Hyperparameter Freezing (`main.tex`, line 349)

> **Proposed Replacement Text:**
> \item \textbf{Hyperparameter Freezing and Benchmark Isolation:} 
> Core retrieval and graph expansion parameters were frozen prior to primary benchmark construction on the basis of topological constraints and feasibility testing on an independent $N=\IssueTwentyFourDevQueryCount$-query pilot (\IssueTwentyFourDevDate; \IssueTwentyFourDevTotalEvals\ run records over \IssueTwentyFourDevPipelineCount\ pipelines and \IssueTwentyFourDevRunCount\ stability runs). Operational constants comprise: initial vector seeds $k=\IssueTwentyFourSeedK$, maximum BFS depth $d=\IssueTwentyFourBfsDepth$, geometric domain threshold $\tau=\IssueTwentyFourDistThreshold$, and hub degree cap $\IssueTwentyFourHubCap$. Specifically, the hub cap acts as an activation threshold: nodes with total degree exceeding 50 trigger a dual-budget traversal allowing up to 75 incoming citing cases (for invalidation and overruling detection) and up to 25 outgoing cited precedents (for doctrinal lineage), subject to hard limits of 40 visited nodes and 35,000 structural context characters. An automated audit (\texttt{scripts/verify\_issue24\_preflight.py}) verifies chronological precedence, zero query ID and prompt-text overlap (\IssueTwentyFourOverlapPct), and no query-text or reference-answer contamination in ChromaDB across all \IssueTwentyFourTestQueryCount\ queries.

### Section III-F: Data and Code Availability (`main.tex`, line 360)

> **Proposed Replacement Text:**
> \noindent\textbf{Data and Code Availability.} All benchmark data, code and model specifications are released under an open-source license at \texttt{https://github.com/zaforsaadik7/TERRA-Temporal-Evolution-and-Reasoning-Trace-RAG}, with archival snapshots on Zenodo upon publication. The package includes: (1)~the 350-query benchmark (\texttt{terra\_350\_benchmark.json}, SHA256: \texttt{8144fa81\dots}) with gold categories, doctrine labels and reference answers; (2)~the 19 doctrine-invalidation pairs and 47 obscure overruled pairs; (3)~the 20,000-case EEG index (\texttt{terra\_eeg\_index\_20k.json}, SHA256: \texttt{\IssueTwentyThreeActiveCorpusHashShort}, \IssueTwentyThreeActiveEdges\ edges: \IssueTwentyThreeActiveCites\ \texttt{CITES}, \IssueTwentyThreeActiveOverrules\ \texttt{OVERRULES}) with all 20,000 generic procedural scaffolds, the construction pipeline (\texttt{scripts/ingest\_20k\_eeg\_and\_vector\_db.py}) and the edge list (\texttt{data/terra\_eeg\_edges\_145k.tsv}); (4)~execution engines (\texttt{ask\_terra.py}, SHA256: \texttt{0cca5cf4\dots}, alongside the preserved Issue~18 pipeline copy, SHA256: \texttt{430fc1b3\dots}) and evaluation scripts (\texttt{eval\_terra.py}); (5)~verbatim prompt templates and Pydantic schemas; (6)~frozen configurations (\texttt{configs/terra\_config.json}); (7)~the dual-judge evaluation records ($N=\numTotalEvals$, \texttt{data/terra\_canonical\_v2\_eval.json}, SHA256: \texttt{95e775e2\dots}) and the CaseFacts, CLERC, obscure-suite and NLI logs in \texttt{data/}; and (8)~table scripts (\texttt{Paper/scripts/generate\_stats.py}) regenerating every table and macro constant. \textbf{Models:} generation and the NLI grader target \texttt{meta-llama/Llama-3.3-70B-Instruct} via the \texttt{databricks-meta-llama-3-3-70b-instruct} serving endpoint (which returns server snapshot identifier \texttt{meta-llama-3.3-70b-instruct-121024}, $T=0.0$, max tokens~4,096); the router uses Gemma 3 12B Instruction-tuned (\texttt{\RouterModel}, $T=0.0$, Pydantic validation); dense retrieval uses \texttt{sentence-transformers/all-MiniLM-L6-v2} (\TraceEmbeddingDimensions\ dimensions, ChromaDB PersistentClient with $L_2$ index setting, top-$k=2$; domain boundary $d_{L2}<1.3$); and judging uses the two independent models of Section~\ref{subsec:eval-metrics}.

---

## 3. Proposed Supplementary Text (`working/src/TERRA_SUPPLEMENT.tex`)

### Update to Table S7 (`supplement_tables/table_run_provenance.tex`)

We propose expanding Table S7 to include an explicit **Provenance Status & Cryptographic Linkage** column, making the distinction between verified cryptographic artifacts and unpinned historical runs completely transparent:

```latex
\par\begingroup
  \small
  \begin{longtable}{@{}p{3.2cm}p{2.0cm}p{4.2cm}p{1.2cm}p{4.2cm}@{}}
\caption{Evaluation Block Provenance and Cryptographic Verification Boundaries.
         Dates are from file timestamps or logged runner headers;
         cryptographic linkage identifies files embedding runtime SHA256 hashes.}\label{tab:run_provenance}\\
    \toprule
    \textbf{Block} & \textbf{Date (source)} & \textbf{Models} & \textbf{$N$} & \textbf{Cryptographic / Code Linkage} \\
    \midrule
    Baseline generations & 5--6 Sept.\ 2026\newline (file mtime) &
      Gen: \texttt{llama-3.3-70b-instruct}; no router/NLI &
      1,400 &
      Unpinned; no runtime code or index hash recorded. \\
    \addlinespace
    Deployed TERRA run & 14 Sept.\ 2026\newline (file mtime) &
      Router: \texttt{gemma-3-12b}; NLI + gen: \texttt{llama-3.3-70b-instruct} &
      350 &
      Logged in \texttt{terra\_350\_issue6}; code/graph hashes unpinned. \\
    \addlinespace
    Dual-judge scoring & 14 Sept.\ 2026\newline (file mtime) &
      J1: \texttt{qwen3-next-80b}; J2: \texttt{gpt-oss-120b} &
      1,750 &
      Judges recorded in canonical file; evaluator script unpinned. \\
    \addlinespace
    Pilot ablation & Pre-Sept.\ 2026\newline (unrecorded) &
      Single judge: \texttt{llama-3.3-70b-instruct} &
      700 &
      35 queries $\times$ 4 arms $\times$ 5 repeats; code/graph unpinned. \\
    \addlinespace
    Temporal leakage probe & 17 Sept.\ 2026\newline (JSON timestamp) &
      J1: \texttt{qwen3-next-80b}; J2: \texttt{gpt-oss-120b} &
      400 &
      Per-row prompt/context/candidate SHA256; code/graph unpinned. \\
    \addlinespace
    Category~D certification & 20 Sept.\ 2026\newline (file mtime) &
      Semantic verifier: \texttt{llama-3.3-70b-instruct} &
      75 &
      Script \texttt{certify\_category\_d\_issue6.py} recorded. \\
    \addlinespace
    CaseFacts eval & 17--18 Sept.\ 2026\newline (microsecond ISO) &
      J1: \texttt{qwen3-next-80b}; J2: \texttt{gpt-oss-120b} &
      510 &
      120 eval + 50 refusal across 3 arms; harness unpinned. \\
    \addlinespace
    CLERC eval & 18 Sept.\ 2026\newline (file mtime) &
      J1: \texttt{qwen3-next-80b}; J2: \texttt{gpt-oss-120b} &
      510 &
      120 eval + 50 refusal across 3 arms; harness unpinned. \\
    \addlinespace
    Obscure suite & 19--20 Sept.\ 2026\newline (verified log) &
      Gen: \texttt{llama-3.3-70b-instruct}; J1/J2 as above &
      120 &
      \textbf{Pinned:} code SHA256 \texttt{430fc1b3\dots} preserved in bundle; Chroma fingerprint recorded. \\
    \addlinespace
    Famous D1 contrast & 19--20 Sept.\ 2026\newline (verified log) &
      Gen: \texttt{llama-3.3-70b-instruct}; J1/J2 as above &
      76 &
      \textbf{Pinned:} identical code hash \texttt{430fc1b3\dots} and Chroma fingerprint recorded. \\
    \addlinespace
    Temporal update & 23 Sept.\ 2026\newline (JSON timestamp) &
      Graph traversal; no LLM &
      106 &
      \textbf{Pinned:} canonical EEG hash \texttt{7aa6db46\dots} and 5 subgraph hashes in metadata. \\
    \bottomrule
  \end{longtable}
\par\endgroup
```

### Update to Limitation 13 (`supplement_limitations.tex`, line 29)

> **Proposed Replacement Text:**
> \item \textbf{Mixed-Date Evaluation Blocks and Provenance Boundaries:}
> Evaluation blocks differ in execution dates, configurations, and cryptographic provenance depth (Table~\ref{tab:run_provenance}). File modification dates are not execution timestamps. For the obscure suite and famous contrast ($N=196$ total), execution code is cryptographically verified: every raw response embeds code SHA256 \texttt{430fc1b3\dots}, identical in executable AST to current release \texttt{ask\_terra.py} (\texttt{0cca5cf4\dots}) aside from a single 6-byte comment edit. Furthermore, requested endpoint parity (\texttt{databricks-meta-llama-3-3-70b-instruct}) is verified across all obscure/famous calls, with string differences between \texttt{meta-llama-3.3-70b-instruct-121024} and \texttt{databricks-meta-llama-3-3-70b-instruct} tracing to harness logging paths rather than differing target endpoints; backend weight invariance over time remains an unverified hosting platform assumption. For the temporal update stability experiment, execution timestamps and SHA256 digests of the active graph and five temporal subgraphs are cryptographically embedded. Conversely, for the primary 1,750-evaluation canonical run, the pilot ablation ($N=700$, 35 queries over 5 repeats), CaseFacts ($N=510$), and CLERC ($N=510$), runtime code commit hashes, NetworkX graph payload snapshots, and Chroma vector index fingerprints were not embedded in the raw result rows. For the temporal probe ($N=400$), prompt, context, and candidate SHA256 hashes identify specific text payloads, but do not provide cryptographic linkage to the generating code version or graph database. The pilot ablation's earlier single judge (\texttt{databricks-meta-llama-3-3-70b-instruct}) differs from the canonical dual-judge protocol, so its scores are not directly comparable with the 1,750-evaluation results. See Table~\ref{tab:run_provenance}.

---

## 4. Verification Check

- Main paper page ceiling constraint: The proposed wording adds approximately 4 lines to Section III-C, well within the 25-page layout margin.
- Supplement page constraint: The proposed Table S7 and Limitation 13 fit comfortably within the 17-page supplement budget without overflowing.
- Compliance with User Guidelines: Zero parallel file edits made; peer wording proposed for Codex's authorized implementation.
