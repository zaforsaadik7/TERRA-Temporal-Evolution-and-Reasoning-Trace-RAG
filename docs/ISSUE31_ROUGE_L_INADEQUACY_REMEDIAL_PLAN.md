# Implementation Plan - Issue #31: ROUGE-L Inadequacy for Legal Question Answering (Revision 2)

**Target Issue:** Issue #31 / Second Review Issue #17  
**Vulnerability:** ROUGE-L $F_1$ is 0.123 and correlates poorly with legal soundness ($r = 0.555$ canonical / $r = 0.482$ historical). In the manuscript, Line 582 contains a mathematical self-contradiction asserting that TERRA's ROUGE-L recall ($\TerraCatBRougeRecall = 0.448$) "outperforms" Flat Vector RAG ($\FlatRAGCatBRougeRecall = 0.500$). Additionally, lexical recall was selectively framed by omitting comparisons against GraphRAG-Adapted (0.523), HippoRAG-Adapted (0.536), and ungrounded Direct LLM (0.546), as well as ROUGE-L $F_1$ where all retrieval baselines exceed TERRA due to candidate-length precision penalties. Furthermore, Lines 401 and 579 inaccurately claimed that ROUGE-L was computed using the Python `rouge-score` library, whereas the canonical pipeline implements a deterministic tokenized LCS algorithm.  
**Requirement:**  
1. **Accurate Implementation Provenance:** Accurately describe the ROUGE-L metric as a deterministic tokenized Longest Common Subsequence (LCS) implementation (regex word tokenization `\b\w+\b`, lowercase conversion, dynamic programming LCS calculation), removing erroneous claims of `rouge-score` library provenance in Section IV-B-3 (Line 401) and Table V Note (Line 579).  
2. **Relegate ROUGE-L to Supplementary Status:** Articulate the four acute structural failure modes of $n$-gram matching in judicial QA: (i) precedent invalidation blindness (rewarding citation of dead law), (ii) doctrinal paraphrasing penalties, (iii) verbosity/candidate-length precision asymmetry, and (iv) defensive refusal zero-scoring; frame semantic faithfulness, citation graph recovery, and adversarial safety handling as primary.  
3. **Eliminate Contradiction & Balance Denominator Comparison via Macro Discipline:** Eliminate the Line 582 mathematical contradiction ("0.448 outperforming 0.500"). Enforce strict denominator parity by comparing TERRA answered-only recall ($0.525$, $N=84$) against Flat RAG answered-only recall ($0.527$, $N=87$), rather than Flat RAG all-query recall ($0.500$). Represent both answered-only recall values and TERRA's answered word count via formal macros (`\TerraCatBAnsweredRougeRecall`, `\FlatRAGCatBAnsweredRougeRecall`, `\TerraCatBAnsweredMeanWords`), avoiding raw literals in narrative text. Transparently disclose that TERRA's lower all-query recall ($0.448$) directly reflects 16 safety refusals scored as zero. Disclose the full baseline landscape honestly (Direct LLM 0.546, HippoRAG 0.536 / 0.539, GraphRAG 0.523 / 0.525).  
4. **Macro Stability & Canon Preservation:** Leave all existing canonical metrics and macros in `generate_stats.py` and `Paper/generated_stats.tex` completely unchanged; add strictly three new answered-only macros (`\TerraCatBAnsweredRougeRecall` = 0.525, `\FlatRAGCatBAnsweredRougeRecall` = 0.527, `\TerraCatBAnsweredMeanWords` = 490). Zero changes needed in `allowed_literals.txt` since all values are macrofied. Custom macro references in `main.tex` expand from 848 to 851.  
5. **Strict CI & Page Budget Invariants:** Maintain strictly 35 pages (`len(pages) == 35`), pass CI 4/4 with the canonical command `python Paper/scripts/check_consistency.py --target Paper/` (851 custom macros resolved, 0 undefined, 0 orphaned literals), preserve all 11 protected substrate hashes bit-for-bit, and synchronize distribution bundles upon approval.

---

## 1. Deep Root Cause & Empirical Ground Truth Audit

### 1.1 Structural Inadequacy of ROUGE-L in Legal Question Answering
Automated surface lexical metrics (ROUGE-L precision, recall, and $F_1$) fail fundamentally in common-law judicial reasoning due to four structural properties:
1. **Precedent Invalidation & Overruling Blindness (The Most Dangerous Legal Failure Mode):**  
   ROUGE-L measures Longest Common Subsequence (LCS) overlap. In common-law evolution, the central legal question is whether a landmark precedent remains good law or was modified/overruled by subsequent decisions. An $n$-gram overlap metric treats words from an overruled precedent (e.g., *Plessy v. Ferguson*'s "separate but equal") identically to words from the governing authority (*Brown v. Board of Education*). A generative model that credulously recites dead law as active doctrine receives positive lexical reward from ROUGE-L, despite committing a malpractice-level legal failure.
2. **Doctrinal Paraphrasing vs. Exact Lexical Matching:**  
   Judicial synthesis requires extracting legal principles across decades of jurisprudence. Competent legal analysis legitimately expresses rules of law using distinct vocabulary and syntax (e.g., "strict scrutiny requiring a compelling state interest" vs. "narrowly tailored to achieve an overriding governmental objective"). Standard holding summaries in benchmarks are concise (averaging 70.8 words); legitimate semantic paraphrasing receives low LCS overlap.
3. **Severe Candidate-Length Precision & Verbosity Penalty:**  
   ROUGE-L precision is $\text{Precision} = \text{LCS} / |\text{candidate}|$. In high-stakes legal practice, an answer must articulate procedural posture, bridging precedents, and citation anchors (TERRA averages 415 words overall, and 490 words on answered queries). Dividing by 490 words mechanically compresses candidate precision to $\approx 0.086$--$0.103$, capping $F_1$ at $0.123$--$0.134$. In contrast, terse 2-sentence outputs that mechanically mimic reference brevity achieve higher $F_1$ purely through brevity.
4. **Epistemic Refusal Zero-Scoring:**  
   A responsible legal AI system must refuse to answer when precedent is ungrounded or absent. When TERRA's conservative firewall falsely refuses 16 Category B queries, standard lexical evaluators score those responses as $0.0$ LCS overlap. This drags benchmark-wide recall down from $0.525$ (on answered queries) to $0.448$ (overall), penalizing defensive safety under an evaluation metric designed for unconditional generation.
5. **Empirical Correlation Ceiling ($r = 0.555$):**  
   Under whole-query cluster bootstrap analysis (Section IV-B-3, Section V-D), LLM critic Faithfulness correlates with ROUGE-L at only Pearson $r = 0.555$ (historical nominal $r = 0.482$). While statistically significant ($p < 0.0001$), lexical overlap accounts for only $\approx 30.8\%$ of variance ($R^2 = 0.308$), confirming that $n$-gram matching captures only a fraction of substantive legal correctness.

---

### 1.2 Metric Implementation Provenance: Deterministic Tokenized LCS
Inspection of `Paper/scripts/generate_stats.py` (lines 42--75) and `scripts/generate_stats_v2.py` (lines 55--75) reveals the exact implementation:
```python
def tokenize(text):
    if not text:
        return []
    return re.findall(r'\b\w+\b', text.lower())

def lcs(x, y):
    m, n = len(x), len(y)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]
```
The codebase does **not** import or execute Google's `rouge-score` library. Manuscript claims in Line 401 and Line 579 citing `\texttt{rouge-score}` represent an incorrect library attribution. The metric must be described truthfully as the **deterministic tokenized Longest Common Subsequence (LCS) implementation**.

---

### 1.3 Mathematical Contradiction & Denominator Parity Audit
In `Paper/main.tex` (Line 582), the manuscript currently asserts:
> *"Conversely, when evaluating \textbf{ROUGE-L Recall} ($\text{Recall} = \text{LCS}/|\text{ref}|$), which measures substantive doctrinal coverage independent of candidate length, TERRA captures comprehensive legal holdings ($\TerraCatBRougeRecall$), outperforming Flat Vector RAG ($\FlatRAGCatBRougeRecall$) and ensuring high-stakes legal completeness."*

**The Mathematical Contradiction:**  
In `Paper/generated_stats.tex`:
- `\TerraCatBRougeRecall` = **0.448**
- `\FlatRAGCatBRougeRecall` = **0.500**  
Claiming that **0.448** "outperforms" **0.500** is a direct mathematical contradiction.

**Denominator Parity Analysis:**  
Comparing TERRA answered-only recall ($0.525$) to Flat RAG all-query recall ($0.500$) is an apples-to-oranges denominator error. When evaluated on identical terms:
- On **all queries ($N=100$)**: Flat RAG achieves **0.500**, whereas TERRA achieves **0.448** because 16 safety refusals are scored as zero.
- On **answered queries**: Flat RAG reaches **0.527** ($N=87$), while TERRA reaches **0.525** ($N=84$). TERRA does **not** exceed Flat RAG on answered queries; it is comparable ($0.525$ vs. $0.527$), while trailing HippoRAG ($0.539$) and Direct LLM ($0.546$).

**Macro-Ledger Discipline:**  
Rather than hardcoding raw literal `0.527` and whitelisting it in `allowed_literals.txt`, project macro discipline requires emitting a dedicated macro:
```latex
\newcommand{\FlatRAGCatBAnsweredRougeRecall}{0.527}
```
The narrative text in Line 582 strictly invokes this macro:
> *"On answered queries, TERRA reaches \TerraCatBAnsweredRougeRecall\ (averaging \TerraCatBAnsweredMeanWords\ words), comparable to Flat RAG's answered-only \FlatRAGCatBAnsweredRougeRecall; its lower all-query value reflects 16 safety refusals scored as zero."*

---

### 1.4 Exact Empirical Ground Truth Across Canonical Data
Audited directly from `scratch/canonical_v2/terra_canonical_v2_eval.json` ($N=1,750$ rows) and `terra_350_benchmark.json`:

| Pipeline | Total Queries ($N$) | Refused Queries | Answered Queries | Overall Recall (All 100) | Answered Recall ($N_{\text{ans}}$) | Overall Precision | Overall $F_1$ | Mean Words (All 100) | Mean Words (Answered) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Direct LLM (No RAG)** | 100 | 0 | 100 | **0.546** (`\DirectLLMCatBRougeRecall`) | 0.546 | 0.064 (`\DirectLLMCatBRougePrecision`) | 0.115 (`\DirectLLMCatBRougeFOne`) | 612 (`\DirectLLMCatBMeanWords`) | 612 |
| **Flat Vector RAG** | 100 | 13 | 87 | **0.500** (`\FlatRAGCatBRougeRecall`) | **0.527** (`\FlatRAGCatBAnsweredRougeRecall`) | **0.096** (`\FlatRAGCatBRougePrecision`) | **0.147** (`\FlatRAGCatBRougeFOne`) | 481 (`\FlatRAGCatBMeanWords`) | 539 |
| **GraphRAG-Adapted** | 100 | 1 | 99 | **0.523** (`\GraphRAGCatBRougeRecall`) | 0.525 | 0.083 (`\GraphRAGCatBRougePrecision`) | 0.140 (`\GraphRAGCatBRougeFOne`) | 477 (`\GraphRAGCatBMeanWords`) | 481 |
| **HippoRAG-Adapted** | 100 | 2 | 98 | **0.536** (`\HippoRAGCatBRougeRecall`) | 0.539 | 0.085 (`\HippoRAGCatBRougePrecision`) | 0.145 (`\HippoRAGCatBRougeFOne`) | 470 (`\HippoRAGCatBMeanWords`) | 477 |
| **TERRA GraphRAG** | 100 | 16 | 84 | **0.448** (`\TerraCatBRougeRecall`) | **0.525** (`\TerraCatBAnsweredRougeRecall`) | 0.086 (`\TerraCatBRougePrecision`) | 0.123 (`\TerraCatBRougeFOne`) | 415 (`\TerraCatBMeanWords`) | 490 (`\TerraCatBAnsweredMeanWords`) |

**Substantive Judicial Evidence vs. Lexical Overlap:**  
While surface lexical recall against 70.8-word reference summaries shows a mixed ranking influenced by answer brevity and safety refusals, TERRA's actual precedential and judicial reasoning superiority is conclusively demonstrated by:
1. **Topological Precedent Node Recall (Table XVII):** TERRA achieves **88.9%** (`\CatBTerraMacroNodeRecall`), outperforming HippoRAG (68.5%), GraphRAG (35.7%), and Flat RAG (26.8%).
2. **Full Precedent Trajectory Recovery (Table XVII):** TERRA recovers **66.0%** (`\CatBTerraFullPathRecall`) of multi-decade citation trajectories, compared to HippoRAG (21.0%), GraphRAG (9.0%), and Flat RAG (1.0%).
3. **Dual-Judge Faithfulness (Table VIII & IX):** TERRA achieves **0.254** (`\TerraCatBFaithfulness`), significantly outperforming all retrieval baselines (HippoRAG 0.188, Flat RAG 0.184, GraphRAG 0.135; all paired Wilcoxon $q < 0.05$).
4. **Adversarial Safety Handling (Table X):** TERRA achieves **97.3%** total safe handling on overruled precedent traps, compared to **0.0%** for Direct LLM and **1.3%** for Flat RAG.

---

## 2. Invariants & Guardrails

To prevent regressions, compile failures, or page budget overflows, the implementation plan enforces the following strict invariants:
1. **Cryptographic Substrate Preservation:** All 11 protected files identified in `data/issue30_preflight.json` must remain 100% bit-for-bit invariant.
2. **Canonical CI Consistency Command:**
   `python Paper/scripts/check_consistency.py --target Paper/`
   Must pass with 0 errors across all 4 checks:
   - Check 1: Checksums match headers.
   - Check 2: All 851 custom macro references resolved in `main.tex` (baseline 848 + 3 newly invoked macros).
   - Check 3: Zero orphaned numeric literals in `main.tex` (no additions needed to `allowed_literals.txt` since all new values are macrofied).
   - Check 4: Abstract-body parity holds.
3. **Strict 35-Page Budget & Layout Anchoring:**
   - Page Count Invariant: `len(pypdf.PdfReader('Paper/main.pdf').pages) == 35`.
   - Structural Terminal Anchors: Table XXIII must remain at the top of Page 35; Reference [27] (Zheng et al., NeurIPS 2023) must terminate Page 35 cleanly.
   - Text Diff Localization: Modifications are strictly localized to Section IV-B-3 (Page 11--12) and Section V-B (Page 14--15). Extracted text comparison via `pypdf` confirms that non-target pages (Pages 1--10, 13, and 16--35) remain 100% text-identical to baseline.
4. **Canonical Metrics & Macro Stability:**
   - All existing 1,495 macros in `Paper/generated_stats.tex` remain completely unchanged.
   - Strictly add three new answered-only macros:
     ```latex
     \newcommand{\TerraCatBAnsweredRougeRecall}{0.525}
     \newcommand{\FlatRAGCatBAnsweredRougeRecall}{0.527}
     \newcommand{\TerraCatBAnsweredMeanWords}{490}
     ```
5. **Pre-Execution Freezing:** Absolutely NO modifications to `Paper/`, generators, datasets, bundles, or checklist files until this revised plan is approved.

---

## 3. Phased Implementation Breakdown

```mermaid
flowchart TD
    subgraph Phase 1: Preflight Audit
        A1[Verify 11 Substrates in Preflight Manifest] --> A2[Verify CI 4/4 & 35-Page Baseline via Canonical Command]
        A2 --> A3[Generate data/issue31_preflight.json & logs/issue31_preflight.txt]
    end

    subgraph Phase 2: Statistical Engine & Macro Architecture
        B1[Update generate_stats.py to Emit Three Answered Macros] --> B2[Verify Existing Canonical Metrics Remain 100% Unchanged]
        B2 --> B3[Add Three Macros to Paper/generated_stats.tex]
        B3 --> B4[Verify CI Check 2 & 3 Compatibility: 851 Custom Macros Resolved]
    end

    subgraph Phase 3: Surgical Manuscript Remediation
        C1[Edit 1: Section IV-B-3 Line 401 - Tokenized LCS Provenance & Inadequacy] --> C2[Edit 2: Section V Opening Line 495 - Roadmap Realignment]
        C2 --> C3[Edit 3: Table V Note Line 579 - Tokenized LCS Provenance]
        C3 --> C4[Edit 4: Section V-B.1 Line 582 - Denominator Parity via Macros]
    end

    subgraph Phase 4: Compilation & Invariant Verification
        D1[Compile Paper/main.tex with Tectonic] --> D2[Verify Strict 35-Page Budget & Anchors]
        D2 --> D3[Run Canonical CI Audit: python Paper/scripts/check_consistency.py --target Paper/]
        D3 --> D4[Verify 11 Protected Substrates Unchanged]
    end

    subgraph Phase 5: Distribution & Closeout
        E1[Rebuild Overleaf & Reproducibility Bundles] --> E2[Generate logs/issue31_closeout.txt]
        E2 --> E3[Update Master Checklist Item 31 to RESOLVED]
    end

    Phase 1 --> Phase 2
    Phase 2 --> Phase 3
    Phase 3 --> Phase 4
    Phase 4 --> Phase 5
```

---

### Phase 1: Preflight Audit & Cryptographic State Freezing
- **Task 1.1: Cryptographic Baseline Verification:**
  - Execute audit script verifying SHA256 hashes of all 11 protected substrates against `data/issue30_preflight.json`.
  - Verify `Paper/main.tex`, `Paper/generated_stats.tex`, `dataset_20k_cap/terra_eeg_index_20k.json`, and `scratch/canonical_v2/terra_canonical_v2_eval.json`.
- **Task 1.2: CI & Page Budget Baseline Gate:**
  - Run canonical CI: `python Paper/scripts/check_consistency.py --target Paper/` and confirm 4/4 PASS with 848 custom macros.
  - Run `scratch/tectonic/tectonic.exe Paper/main.tex --outdir scratch/test_build` and confirm `len(pages) == 35`.
- **Task 1.3: Generate Preflight Artifacts:**
  - Write `data/issue31_preflight.json` recording hashes of baseline files.
  - Log output to `logs/issue31_preflight.txt`.

---

### Phase 2: Statistical Engine & Macro Architecture
- **Task 2.1: Update Python Statistical Generators:**
  - In `Paper/scripts/generate_stats.py` and `scripts/generate_stats_v2.py`:
    - Ensure all existing canonical metrics remain 100% unchanged.
    - Compute answered-only Category B metrics:
      ```python
      if not r.get("safety_rejected", False):
          ao_r_l.append(r_val)
          ao_w_l.append(words)
      ```
    - Emit strictly three answered-only macros under `% --- CATEGORY B DETAILED ROUGE-L METRICS (TABLE V) ---`:
      ```latex
      \newcommand{\TerraCatBAnsweredRougeRecall}{0.525}
      \newcommand{\FlatRAGCatBAnsweredRougeRecall}{0.527}
      \newcommand{\TerraCatBAnsweredMeanWords}{490}
      ```
- **Task 2.2: Update Macro Ledger (`Paper/generated_stats.tex`):**
  - Add the three macros right after `\newcommand{\TerraCatBMeanWords}{415}`:
    ```latex
    \newcommand{\TerraCatBAnsweredRougeRecall}{0.525}
    \newcommand{\FlatRAGCatBAnsweredRougeRecall}{0.527}
    \newcommand{\TerraCatBAnsweredMeanWords}{490}
    ```
- **Task 2.3: Whitelist Verification:**
  - Confirm that since `0.525` and `0.527` are fully macrofied, no modifications to `Paper/scripts/allowed_literals.txt` are required.
- **Task 2.4: Verify Macro Resolution & Literals CI:**
  - Verify that Check 2 of `python Paper/scripts/check_consistency.py --target Paper/` resolves exactly 851 custom macro references (848 baseline + 3 new).

---

### Phase 3: Surgical Manuscript Remediation (`Paper/main.tex`)

#### Task 3.1: Section IV-B-3 (Line 401) — Provenance & Inadequacy of ROUGE-L
- **Target Location:** `Paper/main.tex`, Line 401.
- **Rationale:** Correct metric provenance to deterministic tokenized LCS scoring (removing `rouge-score` library claim) and articulate the four structural failure modes of $n$-gram matching in judicial QA, keeping length tuned to 1,034 characters to fit cleanly on Page 11 and 12.
- **Original Line 401:**
```latex
    \item \textbf{ROUGE-L F1 and Recall (Supplementary):} Computed for Categories A and B against researcher-constructed ground-truth reference answers using the \texttt{rouge-score} library, providing an LLM-independent supplementary lexical alignment metric. Ground-truth doctrinal claims and reference holdings were cross-referenced against standard public legal reference sources (Cornell Legal Information Institute, Oyez Project, and the Congressional Research Service \textit{Constitution Annotated}) by the research team, without independent professional legal certification. ROUGE-L is reported as a supplementary metric rather than the primary measure of legal quality; the moderate judge--ROUGE correlation ($r = \JudgePearsonR$; Section~\ref{subsec:validation-methodology}) confirms that exact n-gram matching captures only a fraction of legal semantic correctness. Primary conclusions about legal quality are drawn from LLM Faithfulness scores, pairwise win rates, and safety rejection rates.
```
- **Replacement Line 401:**
```latex
    \item \textbf{ROUGE-L F1 and Recall (Supplementary):} Computed for Categories A and B against researcher-constructed ground-truth reference answers via deterministic tokenized LCS matching, providing an LLM-independent supplementary lexical alignment metric. Ground-truth doctrinal claims and reference holdings were cross-referenced against standard public legal reference sources (Cornell LII, Oyez, CRS \textit{Constitution Annotated}) without independent legal certification. ROUGE-L is strictly supplementary: exact n-gram matching cannot distinguish active doctrine from overruled precedent, heavily penalizes substantive paraphrasing and detailed analyses via candidate length, and scores defensive refusals as zero. The modest judge--ROUGE correlation ($r = \JudgePearsonR$; Section~\ref{subsec:validation-methodology}) confirms that lexical matching captures only a fraction of legal semantic correctness; primary conclusions are grounded in dual-judge Faithfulness, citation graph recovery, and adversarial safety rates.
```

---

#### Task 3.2: Section V Opening Roadmap (Line 495) — Roadmap Realignment
- **Target Location:** `Paper/main.tex`, Line 495.
- **Rationale:** Replace "lexical recall" with "semantic faithfulness" in the opening empirical roadmap, keeping character count line-neutral to preserve the page break.
- **Original Line 495:**
```latex
To rigorously evaluate TERRA GraphRAG, we adopt an ablation-first empirical methodology. Rather than presenting aggregated metrics that obscure internal component dynamics, we first dissect the architecture into its constituent mechanisms to isolate the empirical contribution of each subsystem. We then evaluate multi-hop evolutionary reasoning via pairwise win rates and lexical recall, examine factual precision and safety firewalling across the complete \numTotalEvals-evaluation benchmark, profile stage-level latency distributions, and conduct formal statistical significance and power audits.
```
- **Replacement Line 495:**
```latex
To rigorously evaluate TERRA GraphRAG, we adopt an ablation-first empirical methodology. Rather than presenting aggregated metrics that obscure internal component dynamics, we first dissect the architecture into its constituent mechanisms to isolate the empirical contribution of each subsystem. We then evaluate multi-hop evolutionary reasoning via pairwise win rates and semantic faithfulness, examine factual precision and safety firewalling across the complete \numTotalEvals-evaluation benchmark, profile stage-level latency distributions, and conduct formal statistical significance and power audits.
```

---

#### Task 3.3: Section V-B Table V Note (Line 579) — Accurate Metric Provenance
- **Target Location:** `Paper/main.tex`, Line 579.
- **Rationale:** Correct provenance description from `using the \texttt{rouge-score} library` to `via deterministic tokenized LCS matching`.
- **Original Line 579:**
```latex
\raggedright \footnotesize \textit{Note (computation):} F1 values are the mean of per-query F1 scores computed individually per response--reference pair; they are not the harmonic mean of the macro P and R column averages and will not reproduce exactly from those column values due to the nonlinearity of the harmonic mean. \textit{Note (reference set):} All system P/R/F1 values were computed against researcher-constructed reference answers averaging $70.8$ words using the \texttt{rouge-score} library; the canonical reference set is \texttt{terra\_350\_benchmark.json} (SHA256: \texttt{8144fa81...}). The Human Ground Truth row (P/R/F1 = 1.000) reflects each reference evaluated against itself by definition.
```
- **Replacement Line 579:**
```latex
\raggedright \footnotesize \textit{Note (computation):} F1 values are the mean of per-query F1 scores computed individually per response--reference pair; they are not the harmonic mean of the macro P and R column averages and will not reproduce exactly from those column values due to the nonlinearity of the harmonic mean. \textit{Note (reference set):} All system P/R/F1 values were computed against researcher-constructed reference answers averaging $70.8$ words via deterministic tokenized LCS matching; the canonical reference set is \texttt{terra\_350\_benchmark.json} (SHA256: \texttt{8144fa81...}). The Human Ground Truth row (P/R/F1 = 1.000) reflects each reference evaluated against itself by definition.
```

---

#### Task 3.4: Section V-B.1 (Line 582) — Denominator Parity via Macros, Contradiction Elimination & Provenance
- **Target Location:** `Paper/main.tex`, Line 582.
- **Rationale:** Eliminate the numerical contradiction; compare TERRA answered-only recall (`\TerraCatBAnsweredRougeRecall`) against Flat RAG answered-only recall (`\FlatRAGCatBAnsweredRougeRecall`), rather than Flat RAG all-query recall (`\FlatRAGCatBRougeRecall`); explain that TERRA's lower all-query recall ($0.448$) directly reflects 16 safety refusals scored as zero; and contrast surface $n$-gram limitations with substantive citation graph recovery and dual-judge semantic faithfulness.
- **Original Line 582:**
```latex
Crucially, evaluating lexical alignment reveals an important empirical trade-off between output verbosity and reference summary matching. On standard ROUGE-L F1, Flat Vector RAG achieves a higher score ($\mathbf{\FlatRAGCatBRougeFOne}$) than TERRA ($\TerraCatBRougeFOne$), with HippoRAG-Adapted at $\HippoRAGCatBRougeFOne$ and GraphRAG-Adapted at $\GraphRAGCatBRougeFOne$. Because human reference answers are researcher-constructed holding summaries averaging $70.8$ words, candidate-length precision in the denominator ($\text{Precision} = \text{LCS}/|\text{cand}|$) heavily penalizes detailed outputs ($\TerraCatBRougePrecision$ for TERRA vs. $\mathbf{\FlatRAGCatBRougePrecision}$ for Flat RAG). Flat Vector RAG produces terse summaries averaging $\FlatRAGCatBMeanWords$ words that mechanically match reference brevity, whereas TERRA generates comprehensive multi-paragraph doctrinal syntheses averaging $\TerraCatBMeanWords$ words with structured chronological headings, statutory references, and hyperlinked citation provenance. Conversely, when evaluating \textbf{ROUGE-L Recall} ($\text{Recall} = \text{LCS}/|\text{ref}|$), which measures substantive doctrinal coverage independent of candidate length, TERRA captures comprehensive legal holdings ($\TerraCatBRougeRecall$), outperforming Flat Vector RAG ($\FlatRAGCatBRougeRecall$) and ensuring high-stakes legal completeness. We report this trade-off transparently: TERRA sacrifices surface-level lexical precision against short reference summaries in order to deliver exhaustive multi-hop precedent grounding.
```
- **Replacement Line 582:**
```latex
Crucially, evaluating lexical alignment exposes the inadequacy of surface n-gram metrics like ROUGE-L for judicial QA. On standard ROUGE-L F1, Flat Vector RAG scores higher ($\mathbf{\FlatRAGCatBRougeFOne}$) than TERRA ($\TerraCatBRougeFOne$), with HippoRAG at $\HippoRAGCatBRougeFOne$ and GraphRAG at $\GraphRAGCatBRougeFOne$. This divergence reflects two factors: (1)~Because reference holdings average $70.8$ words, candidate-length precision ($\text{Precision} = \text{LCS}/|\text{cand}|$) heavily penalizes detailed legal syntheses ($\TerraCatBRougePrecision$ for TERRA vs.\ $\mathbf{\FlatRAGCatBRougePrecision}$ for Flat RAG), where TERRA provides structured chronological trajectories rather than brief summaries; and (2)~On benchmark-wide \textbf{ROUGE-L Recall}, TERRA\textquotesingle s conservative firewall falsely refuses \TerraCatBFalseRefusals\ Category~B queries (scored as zero overlap), yielding an overall recall of $\TerraCatBRougeRecall$, compared to $\FlatRAGCatBRougeRecall$ for Flat RAG, $\GraphRAGCatBRougeRecall$ for GraphRAG, and $\HippoRAGCatBRougeRecall$ for HippoRAG (and $\mathbf{\DirectLLMCatBRougeRecall}$ for Direct LLM). On answered queries, TERRA reaches \TerraCatBAnsweredRougeRecall\ (averaging \TerraCatBAnsweredMeanWords\ words), comparable to Flat RAG\textquotesingle s answered-only \FlatRAGCatBAnsweredRougeRecall; its lower all-query value reflects 16 safety refusals scored as zero. Crucially, n-gram overlap cannot distinguish valid modern doctrine from overruled precedent: ROUGE-L rewards verbatim citation of dead law, whereas TERRA\textquotesingle s core strengths lie in verified citation graph recovery (Table~\ref{tab:retrieval_eval}) and dual-judge semantic faithfulness ($\TerraCatBFaithfulness$, FDR $q < 0.05$).
```

---

### Phase 4: Compilation, CI Consistency, & Strict Page Budget Verification
- **Task 4.1: Tectonic Compilation:**
  - Compile `Paper/main.tex` using `scratch/tectonic/tectonic.exe Paper/main.tex`.
  - Assert zero compiler errors and returncode 0.
- **Task 4.2: Page Count & Layout Invariant Audit:**
  - Verify `len(pages) == 35` using `pypdf`.
  - Verify that Table XXIII remains at the top of Page 35.
  - Verify that Reference [27] (Zheng et al., NeurIPS 2023) terminates Page 35 cleanly.
  - Verify text diff localization: non-target pages (Pages 1--10, 13, and 16--35) remain 100% text-identical to baseline.
- **Task 4.3: Canonical CI Consistency Audit:**
  - Execute:
    ```powershell
    python Paper/scripts/check_consistency.py --target Paper/
    ```
  - Assert 4/4 passing checks:
    - Check 1: Raw data SHA256 checksums match macro headers.
    - Check 2: All 851 custom macros referenced in `main.tex` are strictly defined (848 baseline + 3 new).
    - Check 3: Zero orphaned numeric literals found in `main.tex`.
    - Check 4: Abstract-to-body claim alignment verified.
- **Task 4.4: Protected Substrate Verification:**
  - Re-verify SHA256 hashes of all 11 protected substrates against `data/issue31_preflight.json` to prove zero collateral damage.

---

### Phase 5: Distribution & Master Checklist Closeout
- **Task 5.1: Synchronize Overleaf Distribution Bundles:**
  - Rebuild `Paper/overleaf_bundle.zip` and root `TERRA_Overleaf_Bundle.zip` from verified `Paper/` directory using `zip -r`.
  - Confirm bit-identical archive hashes.
- **Task 5.2: Rebuild Reproducibility Package:**
  - Rebuild `TERRA_Reproducibility_Bundle.zip` using an external non-self-referential manifest.
  - Record SHA256 hashes in `logs/issue31_closeout.txt`.
- **Task 5.3: Update Master Checklist:**
  - Update `TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md`:
    - Mark Item 31 as `[x] **31. ROUGE-L Inadequacy for Legal Question Answering**`
    - Status: `**RESOLVED & VERIFIED**`
    - Document the complete resolution summary, empirical metrics, line changes, macro additions, and verification hashes.
    - Update progress counter from 34/43 to 35/43 items completed.

---

## 4. Verification Checkpoint Table

| Invariant / Check | Expected Target | Verification Command / Tool |
| :--- | :--- | :--- |
| **Protected Substrates** | 11/11 SHA256 match `data/issue30_preflight.json` | Python hash audit |
| **Existing Metrics** | All existing 1,495 macros 100% invariant | Macro diff vs baseline `generated_stats.tex` |
| **New Macros** | Exactly 3 added: `\TerraCatBAnsweredRougeRecall` (0.525), `\FlatRAGCatBAnsweredRougeRecall` (0.527), `\TerraCatBAnsweredMeanWords` (490) | Check macro definitions |
| **LaTeX Compilation** | Clean exit (returncode 0), 0 errors | `scratch/tectonic/tectonic.exe Paper/main.tex` |
| **PDF Page Budget** | **Strictly 35 pages** (`len(pages) == 35`) | `pypdf.PdfReader('Paper/main.pdf')` |
| **Page 35 Top Anchor** | Table XXIII (Complete FDR Family) | `reader.pages[34].extract_text()[:200]` |
| **Page 35 Bottom Anchor** | Reference [27] (Zheng et al., NeurIPS 2023) | `reader.pages[34].extract_text()[-400:]` |
| **Diff Localization** | Non-target pages (1--10, 13, 16--35) 100% text-identical | `pypdf` page text comparison |
| **Canonical CI Audit** | **4/4 PASS**, 0 undefined macros, 0 orphaned literals | `python Paper/scripts/check_consistency.py --target Paper/` |
| **Macro Parity** | Exactly 851 custom macros resolved in `main.tex` | `check_consistency.py` Check 2 |
| **Orphaned Literals** | 0 unwhitelisted literals in `main.tex` | `check_consistency.py` Check 3 |
| **Distribution Bundles** | Clean, non-corrupt, matching current `Paper/` | Python zip verification |
| **Master Checklist** | Item 31 marked `[x] RESOLVED`, counter 35/43 | Inspection of Checklist markdown |

---

## 5. Explicit Stop Protocol
In accordance with user instructions:
> **"do not proceed with the plan after making it, report me back and wait for my approval to proceed"**
> **"6. Do not modify `Paper/`, generators, datasets, bundles, or checklist files until the revised plan is approved."**

Execution is strictly suspended at this planning stage. No modifications have been made to `Paper/`, statistical generators, baseline datasets, distribution bundles, or the master checklist. Awaiting explicit user approval before initiating Phase 1.
