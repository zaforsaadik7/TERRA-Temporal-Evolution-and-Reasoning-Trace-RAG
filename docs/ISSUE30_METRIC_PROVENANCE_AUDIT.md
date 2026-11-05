# Forensic Metric Provenance Audit: Issue #30 Category B Faithfulness Dispersion & Citation Recall

## 1. Executive Summary & Determinations

This forensic audit resolves two distinct metric inquiries for Issue #30:
1. **Category B Faithfulness Dispersion**: Resolving the discrepancy between draft figures `±0.316 / ±0.288` and active macro values `±0.166 / ±0.226`.
2. **Category B Precedent Citation Recall**: Resolving the discrepancy between draft figures `0.871 / 0.429` and active macro values `57.85% / 43.55%`.

---

## 2. Category B Faithfulness Dispersion Provenance

### 2.1 Authentic Canonical Source Values
- **Direct LLM (No RAG)**: **$0.335 \pm 0.166$** (`\DirectLLMCatBFaithfulness \pm \DirectLLMCatBFaithfulnessStd`)
- **Full TERRA (2-Hop EEG GraphRAG)**: **$0.254 \pm 0.226$** (`\TerraCatBFaithfulness \pm \TerraCatBFaithfulnessStd`)
- **Comparative Delta**: $\Delta = -0.081$ (`\CatBTerraVsDirectLLMDelta`), $p = 0.0009$, FDR $q = 0.0023$, TERRA win rate $27.0\%$ ($27$ wins, $18$ ties, $55$ losses).

### 2.2 Status of `±0.316` and `±0.288`
- `0.288` corresponds closely to the single-judge unweighted GPT-OSS standalone sample dispersion on TERRA Cat B ($\sigma = 0.2881$), whereas the consensus dual-judge score across all 100 Category B queries has sample standard deviation $\sigma = 0.2265 \to 0.226$.
- `0.316` does not exist in any canonical raw evaluation records and was an unverified draft transcription error.
- **Verdict**: The plan and all reports strictly and uniformly use the certified, macro-backed values **$0.335 \pm 0.166$** and **$0.254 \pm 0.226$**.

### 2.3 Cryptographic Source Tracing
- **Raw File**: `scratch/canonical_v2/terra_canonical_v2_eval.json`
- **SHA256**: `95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507`
- **Definitions in `Paper/generated_stats.tex`**:
  ```latex
  \newcommand{\DirectLLMCatBFaithfulness}{0.335}
  \newcommand{\DirectLLMCatBFaithfulnessStd}{0.166}
  \newcommand{\TerraCatBFaithfulness}{0.254}
  \newcommand{\TerraCatBFaithfulnessStd}{0.226}
  \newcommand{\CatBTerraVsDirectLLMDelta}{-0.081}
  \newcommand{\CatBTerraVsDirectLLMWilcoxonP}{0.0009}
  \newcommand{\CatBTerraVsDirectLLMAdjQ}{0.0023}
  \newcommand{\TerraVsDirectLLMCatBWinRate}{27.0\%}
  ```

---

## 3. Category B Precedent Citation Recall Metric Provenance

### 3.1 Discrepancy Under Investigation
- **Draft Narrative Inscription**: TERRA = `0.871`, Direct LLM = `0.429` (citing phantom "Table XIX").
- **Phase 1 Preflight Finding**: `\CatBTerraMacroCitationRecall` = **$57.85\%$**, `\CatBDirectMacroCitationRecall` = **$43.55\%$**.

### 3.2 Forensic Source Tracing
1. **Source Table**: **Table XVII** (`Paper/tables/table_citation_eval.tex`, labeled `\label{tab:citation_eval}`).
   - Panel A: *Category B Multi-Hop Precedent Citation Performance ($N=\CatBRetrievalQueries$ Queries, $\CatBGoldPrecedents$ Gold Precedents)*.
   - Note: The manuscript does not contain a "Table XIX"; citation correctness is located in Section VI-B (`\label{subsec:citation-correctness}`), Table XVII on Page 26.
2. **Generating Script**: `scripts/run_v2b_downstream_audit.py` (Lines 556–600 and 847, 879) importing entity resolution logic from `scripts/audit_citation_correctness.py`.
3. **Macro Ledger Definitions (`Paper/generated_stats.tex`)**:
   - Lines 843–849:
     ```latex
     \newcommand{\CatBTerraMacroCitationRecall}{57.85\%}
     \newcommand{\CatBTerraMicroCitationRecall}{55.56\%}
     \newcommand{\CatBTerraEntityCitationPrecision}{74.25\%}
     \newcommand{\CatBTerraDoctrinalCitationPrecision}{9.30\%}
     \newcommand{\CatBTerraCitationFOne}{16.02\%}
     \newcommand{\CatBTerraFullPathCitationRecall}{23.00\%}
     \newcommand{\CatBTerraFullPathCitationCount}{23/100}
     ```
   - Lines 875–881:
     ```latex
     \newcommand{\CatBDirectMacroCitationRecall}{43.55\%}
     \newcommand{\CatBDirectMicroCitationRecall}{42.40\%}
     \newcommand{\CatBDirectEntityCitationPrecision}{90.27\%}
     \newcommand{\CatBDirectDoctrinalCitationPrecision}{7.08\%}
     \newcommand{\CatBDirectCitationFOne}{12.17\%}
     \newcommand{\CatBDirectFullPathCitationRecall}{1.00\%}
     \newcommand{\CatBDirectFullPathCitationCount}{1/100}
     ```
   - Lines 886–889:
     ```latex
     \newcommand{\CatBTerraVsDirectCitationFOneLift}{\ensuremath{1.32\times}}
     \newcommand{\CatBTerraVsDirectPathCitationLift}{\ensuremath{23.00\times}}
     ```
4. **Active Manuscript Usage (`Paper/main.tex`)**:
   - Line 941 (Section VI-B):
     ```latex
     \item \textbf{Precedent Citation Recall Leadership:} On Category~B multi-decade evolutionary trajectories ($N=\CatBRetrievalQueries$ queries, $\CatBGoldPrecedents$ gold landmark authorities), Full TERRA achieves $\mathbf{\CatBTerraMacroCitationRecall}$ macro citation recall ($\CatBTerraMicroCitationRecall$ micro), outperforming HippoRAG-Adapted ($\CatBHippoRAGMacroCitationRecall$ macro), Direct LLM ($\CatBDirectMacroCitationRecall$), Flat Vector RAG ($\CatBFlatMacroCitationRecall$), and GraphRAG-Adapted ($\CatBGraphRAGMacroCitationRecall$) by $\CatBTerraVsHippoCitationRecallDelta$ to $\CatBTerraVsGraphCitationRecallDelta$ absolute percentage points.
     ```

### 3.3 Metric Definition, Denominator, Query Subset, and Unit Scale
- **Query Subset**: Category B (Evolutionary Multi-Hop Precedent Queries), $N = 100$ queries (`B001` through `B100`).
- **Ground Truth Target Precedents ($T_q$)**: Defined in `terra_350_benchmark.json` (SHA256: `8144fa81...`).
  - Total gold landmark precedent nodes: $\sum_{q \in \text{Cat B}} |T_q| = 342$ gold precedents.
  - Average target precedents per query: $\mu = 3.42$.
- **Extraction & Entity Grounding Protocol**:
  - Model completion answers $\text{ans}_q$ are processed by `extract_case_entities()` against the 20,000-case EEG index (`dataset_20k_cap/terra_eeg_index_20k.json`, SHA256: `7aa6db46...`).
  - Citations are normalized to authentic canonical node IDs ($V_{\text{EEG}}$) via reporter volume/page patterns and historical case alias tables (e.g. *Slaughter-House Cases* $\to$ `83_0036-01`).
  - Precedent milestone hit count:
    $$\text{Hits}(q) = |\text{ResolvedCitations}(q) \cap T_q|$$
- **Per-Query Recall**:
  $$\text{CR}(q) = \frac{\text{Hits}(q)}{|T_q|}$$
- **Macro Citation Recall Estimand**:
  $$\text{Macro CR} = \frac{1}{100} \sum_{q=1}^{100} \text{CR}(q)$$
  - **Full TERRA**: **$57.85\%$** (`\CatBTerraMacroCitationRecall`)
  - **Direct LLM**: **$43.55\%$** (`\CatBDirectMacroCitationRecall`)
  - **Absolute Difference**: **$14.30$ percentage-point difference** ($57.85\% - 43.55\% = 14.30$ percentage points)
  - **Relative Lift**: Retained separately as **$1.33\times$** ($57.85 / 43.55 = 1.328\times \approx 1.33\times$)
- **Micro Citation Recall (Aggregate Milestone Recall)**:
  $$\text{Micro CR} = \frac{\sum_{q} \text{Hits}(q)}{\sum_{q} |T_q|} = \frac{\text{TotalGoldHits}}{342}$$
  - **Full TERRA**: **$55.56\%$** (`\CatBTerraMicroCitationRecall`)
  - **Direct LLM**: **$42.40\%$** (`\CatBDirectMicroCitationRecall`)
- **Full Path Citation Recovery (100% of Landmark Chain Cited)**:
  - **Full TERRA**: **$23/100$** queries ($23.00\%$, `\CatBTerraFullPathCitationCount`)
  - **Direct LLM**: **$1/100$** query ($1.00\%$, `\CatBDirectFullPathCitationCount`)
  - **Path Citation Lift**: **$\mathbf{23.00\times}$** advantage over Direct LLM (`\CatBTerraVsDirectPathCitationLift`)

### 3.4 Origin & Root Cause of `0.871 / 0.429`
- Neither `0.871` nor `0.429` appears in `Paper/generated_stats.tex`, `Paper/main.tex`, `Paper/tables/table_citation_eval.tex`, or any canonical benchmark json.
- `87.1%` appeared in `generated_stats.tex.broken_6465c01b:169` as `\CatBTerraVsDirectLLMPower{87.1\%}` and in active `Paper/generated_stats.tex:1667` as `\IssueTwentySixBoundCapOneHundredMacro{87.13\%}`.
- "Table XIX" was a phantom draft table label; the actual table is Table XVII in Section VI-B.
- During early narrative drafting of the Issue #30 plan notes, these numbers were mistakenly written in descriptive parentheticals, even though the planned LaTeX patch itself correctly invoked `\CatBTerraMacroCitationRecall` and `\CatBDirectMacroCitationRecall`.

### 3.5 Definitive Resolution & Action
1. All plan documents (`docs/ISSUE30_DIRECT_LLM_SUPERIORITY_CLAIM_PLAN.md` and `implementation_plan.md`) are updated to strictly reference:
   - Macro Citation Recall: Full TERRA **$57.85\%$** (`\CatBTerraMacroCitationRecall`) vs. Direct LLM **$43.55\%$** (`\CatBDirectMacroCitationRecall`).
   - Difference Metric: Formally labeled as a **14.30 percentage-point difference** ($57.85\% - 43.55\% = 14.30$ percentage points); retain **$1.33\times$** separately as the relative lift.
   - Phrasing Mandate: Replace any draft notion of "stronger citation coverage and temporal grounding" with the precise metric-grounded formulation: **"stronger Category B citation coverage and full-precedent-path recovery"** (as citation recall directly measures Category B citation recovery, not temporal grounding per se).
   - Table Reference: **Table XVII** (Section VI-B, `\label{subsec:citation-correctness}`).
   - Full Path Citation: **$23/100$** vs. **$1/100$** ($23.00\times$ lift).
2. The planned manuscript patch for Section VII Limitation 6 and Section V-B already uses the exact macros `\CatBTerraMacroCitationRecall` and `\CatBDirectMacroCitationRecall`, which expand directly to $57.85\%$ and $43.55\%$ without introducing any orphaned numeric literals.
