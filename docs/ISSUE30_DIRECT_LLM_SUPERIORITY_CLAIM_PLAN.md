# Comprehensive Remedial Plan (v2.1): Issue #30 — Direct LLM Non-Inferiority & Overstated Empirical Superiority

## 1. Context & Architectural Overview
- **Vulnerability**: Direct LLM beats TERRA on Category B multi-hop evolutionary precedent chains ($0.335 \pm 0.166$ vs. $0.254 \pm 0.226$, $\Delta = -0.081, p = 0.0009$, FDR $q = 0.0023$, TERRA win rate $27.0\%$).
- **Metric Provenance Resolution**: As documented in `docs/ISSUE30_METRIC_PROVENANCE_AUDIT.md`, all narrative and tabular metrics are strictly macro-backed:
  - **Category B Faithfulness**:
    - Direct LLM: **$0.335 \pm 0.166$** (`\DirectLLMCatBFaithfulness \pm \DirectLLMCatBFaithfulnessStd`)
    - Full TERRA: **$0.254 \pm 0.226$** (`\TerraCatBFaithfulness \pm \TerraCatBFaithfulnessStd`)
    - Historical draft references to `±0.316` and `±0.288` were unverified draft transcription artifacts ($0.288$ was unweighted standalone GPT-OSS single-judge dispersion; canonical dual-judge consensus dispersion is $0.226$).
  - **Category B Precedent Citation Recall (Table XVII, Section VI-B)**:
    - Direct LLM: **$43.55\%$** macro CR (`\CatBDirectMacroCitationRecall`), $42.40\%$ micro CR, $1/100$ full chains cited.
    - Full TERRA: **$57.85\%$** macro CR (`\CatBTerraMacroCitationRecall`), $55.56\%$ micro CR, $23/100$ full chains cited (a **$14.30$ percentage-point difference**, $1.33\times$ relative lift, and $23.00\times$ full path lift).
    - Historical draft references citing `0.871 / 0.429` (and phantom "Table XIX") were stale transcription artifacts conflating power/sensitivity bounds with citation recall. All narrative text is now strictly macro-backed.
- **Core Defect**: While narrative text in Section V-B (Lines 553–555) candidly discloses this comparison, headline tables and summary bullets frame TERRA as outperforming "baselines" without qualifying that superiority applies strictly to *evaluated RAG retrieval baselines* (Flat Vector RAG, GraphRAG-Adapted, HippoRAG-Adapted), and omit the Direct LLM result from key summary lists.
- **Requirement**: Formally qualify all claims: TERRA outperforms *evaluated RAG retrieval baselines* on multi-hop navigation, not LLMs in general. Disclose the full result honestly, clarify Table VIII and Table X bolding with explicit footnotes, harmonize summary bullets, and articulate the parametric fluency trade-off in limitations.
- **Specific Audit Safeguards (v2.1)**:
  1. Standardize exclusively on the canonical CI consistency command: `python Paper/scripts/check_consistency.py --target Paper/`.
  2. Implement dynamic checklist counting: assert only that Item 30 is pending pre-edit, completed post-edit, and that the completed count increases by exactly one ($N_{\text{post}} = N_{\text{pre}} + 1$). Zero hardcoded counts.
  3. Narrow citation claims strictly to reported metrics: *"TERRA’s retrieval evaluation shows stronger Category B citation coverage and full-precedent-path recovery"*, grounded in Table XVII metrics ($\CatBTerraMacroCitationRecall = 57.85\%$ vs. $\CatBDirectMacroCitationRecall = 43.55\%$, a 14.30 percentage-point difference).
  4. Preserve *"consistent with"* phrasing for judge-fluency interpretations; do not assert unproven causal mechanisms.
  5. Strictly zero modifications to `Paper/`, runtime code, datasets, benchmark outputs, bundles, or checklist files until this plan is formally approved.

---

## 2. Targets of Remediation

### 2.1 Table VIII Bolding & Footnote Alignment (`Paper/main.tex:550`)
- **Issue**: Under Faithfulness, TERRA ($\mathbf{0.254 \pm 0.226}$) is bolded while Direct LLM ($0.335 \pm 0.166$) is in the same column.
- **Fix**: Add explicit note in Table VIII footnote:
  ```latex
  \raggedright \footnotesize \textbf{Notes:} Bold denotes top performance among retrieval-augmented (RAG) pipelines; Direct LLM (No RAG) serves as an ungrounded parametric baseline reference. $^\dagger$Against Direct LLM, head-to-head outcomes comprise $\TerraVsDirectLLMCatBWins$ TERRA wins, $\TerraVsDirectLLMCatBTies$ ties, and $\TerraVsDirectLLMCatBLosses$ losses, reflecting parametric fluency on generic summaries versus grounded citation depth.
  ```

### 2.2 Table X Bolding & Footnote Alignment (`Paper/main.tex:605`)
- **Issue**: Under Category B Evolutionary, TERRA ($\mathbf{0.254}$) is bolded over Direct LLM ($0.335$) with no explanatory footnote.
- **Fix**: Add explicit notes line under Table X:
  ```latex
  \vspace{1mm}
  \raggedright \footnotesize \textbf{Notes:} Bold denotes top performance among retrieval-augmented (RAG) pipelines; Direct LLM (No RAG) serves as an ungrounded parametric baseline reference.
  ```

### 2.3 Section V-B Summary Bullet on Category B (`Paper/main.tex:621`)
- **Issue**: Summary bullet mentions outperforming HippoRAG, GraphRAG, and Flat Vector RAG, but omits Direct LLM entirely, unlike all neighboring bullets.
- **Fix**: Update bullet to explicitly report Direct LLM with metric-grounded phrasing:
  ```latex
  \item \textbf{Evolutionary Multi-Hop Performance (Category B):} On multi-decade precedent trajectories, TERRA achieves $\TerraCatBFaithfulness$ faithfulness, significantly outperforming all evaluated retrieval baselines: HippoRAG ($\HippoRAGCatBFaithfulness$, $\Delta=\CatBTerraVsHippoRAGDelta$, $q=\CatBTerraVsHippoRAGAdjQ$), GraphRAG ($\GraphRAGCatBFaithfulness$, $\Delta=\CatBTerraVsGraphRAGDelta$, $q=\CatBTerraVsGraphRAGAdjQ$), and Flat Vector RAG ($\FlatRAGCatBFaithfulness$, $\Delta=\CatBTerraVsFlatDelta$, $q=\CatBTerraVsFlatRAGAdjQ$). A non-retrieval Direct LLM scores higher on Category~B ($\DirectLLMCatBFaithfulness$, $\Delta=\CatBTerraVsDirectLLMDelta$, $q=\CatBTerraVsDirectLLMAdjQ$; TERRA win rate $\TerraVsDirectLLMCatBWinRate$), consistent with dual judges rewarding fluent ungrounded parametric prose over grounded retrieval constraints, whereas TERRA's retrieval evaluation shows stronger Category~B citation coverage and full-precedent-path recovery.
  ```

### 2.4 Section V-D Narrative Bullets & Duplicate Removal (`Paper/main.tex:733–742`)
- **Issue**: Table XII includes Direct LLM Cat B and Combined A+B, but the narrative bullets omit them. Line 741 is an accidental verbatim copy-paste of Line 622.
- **Fix**: Add the Direct LLM bullet and purge the duplicate Line 741:
  ```latex
  \item \textbf{Against Direct LLM (Non-Retrieval Reference):} On Category~B, Direct LLM achieves higher faithfulness than TERRA ($\Delta = \CatBTerraVsDirectLLMDelta$, $p = \CatBTerraVsDirectLLMWilcoxonP$, FDR $q = \CatBTerraVsDirectLLMAdjQ$, Table~\ref{tab:full_fdr_family}, Rank~8), whereas on combined in-domain queries (Categories~A+B), TERRA leads by $\mathbf{\CombinedTerraVsDirectLLMDelta}$ ($p = \CombinedTerraVsDirectLLMWilcoxonP$, FDR $q = \CombinedTerraVsDirectLLMAdjQ$), driven by Category~A ($\CatATerraVsDirectLLMDelta$, $q = \CatATerraVsDirectLLMAdjQ$).
  ```

### 2.5 Section VII Limitation 6 Category B Disclosure (`Paper/main.tex:1055`)
- **Issue**: Limitation 6 focuses on Category D and obscure precedents, without mentioning Category B parametric memory.
- **Fix**: Add a connecting sentence in Limitation 6 grounded in reported metrics:
  ```latex
  Similarly, on Category~B (Evolutionary Precedents), Direct LLM achieves higher judge-scored faithfulness ($\DirectLLMCatBFaithfulness$ vs.\ $\TerraCatBFaithfulness$, $\Delta=\CatBTerraVsDirectLLMDelta$, $q=\CatBTerraVsDirectLLMAdjQ$), consistent with base model fluency on generic historical narratives, whereas TERRA's retrieval evaluation shows stronger Category~B citation coverage and full-precedent-path recovery ($\CatBTerraMacroCitationRecall$ macro citation recall vs.\ $\CatBDirectMacroCitationRecall$ for Direct LLM; Section~\ref{subsec:citation-correctness}).
  ```

---

## 3. Strict Verification & Invariant Gates (All 10 Must Pass)
1. **Gate 1**: Zero broad superiority claims over LLMs in general; superiority claims strictly qualified to *evaluated RAG retrieval baselines*.
2. **Gate 2**: Table VIII footnote and Table X notes explicitly qualify that bold denotes top performance among retrieval-augmented (RAG) pipelines, with Direct LLM serving as an ungrounded parametric baseline.
3. **Gate 3**: Section V-B summary bullet harmonized with Direct LLM metrics, using *"consistent with"* and *"TERRA's retrieval evaluation shows stronger Category B citation coverage and full-precedent-path recovery"*.
4. **Gate 4**: Section V-D FDR bullets report Direct LLM Category B ($\Delta = -0.081$) and Combined In-Domain ($\Delta = +0.173$); duplicate Line 741 is completely purged.
5. **Gate 5**: Section VII Limitation 6 articulates Category B parametric memory grounded in citation recall metrics ($\CatBTerraMacroCitationRecall = 57.85\%$ vs. $\CatBDirectMacroCitationRecall = 43.55\%$, a 14.30 percentage-point difference).
6. **Gate 6**: All 11 protected core substrates remain 100% bit-invariant against pre-edit manifest.
7. **Gate 7**: Frozen historical archives (`Paper/prev_main.tex` and `ask_terra_pre_issue13_backup.py`) preserved byte-for-byte.
8. **Gate 8**: Canonical CI consistency audit `python Paper/scripts/check_consistency.py --target Paper/` yields 4/4 PASS with 848 custom macros resolved and 0 orphaned numeric literals.
9. **Gate 9**: Strict 35-page budget invariant maintained (`len(pages) == 35`, References [1]–[27] cleanly terminating on Page 35, 0 lines on Page 36).
10. **Gate 10**: Overleaf and Reproducibility bundles rebuilt; checklist dynamically verified to increase completed count by exactly one ($N_{\text{post}} = N_{\text{pre}} + 1$).
