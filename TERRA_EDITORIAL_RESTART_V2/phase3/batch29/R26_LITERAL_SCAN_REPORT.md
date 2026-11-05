# R26 literal scan, current working source (report only)

- Author: Claude, 2026-10-06. Claude-only, **not independent**; Codex re-check queued.
- Source: `working/src/main.tex` sha256 `b950bc09`; method: the Phase 0 regex `(?<![\\A-Za-z{])\d[\d,\.]*\s?%?` from `\begin{document}`, comment lines omitted (as in `phase0_report_addendum_01.md` C6).
- Digit-run tokens in the main.tex body now: **1104** (Phase 0 baseline 1,331 on the 39-page source). Year-shaped tokens (1800-2099): 56. Digit-run tokens in `tables/*.tex`: 1070 (all files, including tables no longer \input).
- Macros with a purely numeric value across the frozen and override files: 872 distinct values.
- Body literals (3+ characters, non-year) that equal a macro value: **170** (49 distinct). These are the literals that a later macro change would leave stale; they are candidates to macroise or to re-verify by hand after any macro edit.

| Literal | Occurrences | Equal to macro value(s) |
|---|---:|---|
| `100` | 27 | CatBRetrievalQueries, CatBTotalPairs, IssueTwentyFiveCatBConstitutionalPublicCount, TemporalMonotonicInclusion |
| `0.0` | 21 | AblationFullCatAFalseRefusalRate, AblationOneCatAFalseRefusalRate, AblationTwoCatAFalseRefusalRate, AblationTwoCatDSafetyRate |
| `350` | 20 | DirectLLMAnswerOnlyCount, IssueTwentyFourTestQueryCount, RouterTotalQueries, numUniqueQueries |
| `120` | 11 | CaseFactsTrackOneN, ClercNQueries, ObscKappaCleanEvals |
| `3.3` | 10 | ClercFlatRecallOne, ClercTerraRecallOne |
| `20,000` | 8 | CorpusTotalOpinions, CorpusTotalOpinionsRaw, IssueTwentyTwoTotalCorpusSize, IssueTwentyTwoTotalCorpusSizeRaw |
| `1.3` | 7 | HippoRAGCatDHedgeRate |
| `1.30` | 4 | IssueTwentyFourDistThreshold |
| `1.0` | 4 | CatBFlatFullPathRecall |
| `100.0` | 4 | AblationFullCatDSafetyRate, AblationOneCatDSafetyRate, AblationThreeCatDSafetyRate, CatATerraVsDirectLLMPower |
| `20.0` | 4 | AblationThreeCatAFalseRefusalRate, CatBTerraPathRecallLenFive, IssueTwentySixBoundFiveNodePath, IssueTwentyTwoFirstAmendmentBaselineAcc |
| `400` | 3 | TemporalTotalEvaluations |
| `240` | 3 | RouterHardPathCount |
| `500` | 2 | TerraCatBTotalOps |
| `139` | 2 | TerraFlaggedRefusals |
| `0.0032` | 2 | CatBTerraVsFlatRAGWilcoxonP, CatBTerraVsFlatWilcoxonP |
| `1,750` | 2 | numTotalEvals, numTotalEvalsRaw |
| `0.200` | 2 | CombinedMDES |
| `200` | 2 | CombinedPairs, IssueTwentyOneAuditCitationPresentCount, IssueTwentyOneAuditSampleN, IssueTwentyOneAuditTitleCorroboratedCount |
| `92.0` | 2 | ClercDirectMisapplicationOrTrackTwo |
| `8.0` | 2 | CatBFourPlusSeedsPct, TerraGatedRefusalA |
| `99.91` | 1 | IssueTwentyOneStrictlyPriorDatePct |
| `3.1` | 1 | CatBHippoRAGPathRecallLenFour |
| `211` | 1 | TerraAnswerOnlyCount, TerraAnsweredQueries, TerraOverallGenCallsCount |
| `204` | 1 | FlatEpistemicRefusals |
| `145,310` | 1 | IssueTwentyOneTotalCitesEdges, IssueTwentyOneTotalCitesEdgesRaw |
| `384` | 1 | TerraCatBTotalOps, TraceEmbeddingDimensions |
| `525` | 1 | IssueTwentyFourDevTotalEvals |
| `620` | 1 | TerraThrottleSleepSeconds |
| `0.6950` | 1 | TerraOverallRaw |
| `0.7357` | 1 | TerraOverallClamped |
| `110` | 1 | RouterFastPathCount |
| `1.000` | 1 | TerraCatCFaithfulness |
| `0.283` | 1 | CatBMDES |
| `315` | 1 | TemporalValidPairs |
| `28.0` | 1 | CatBGraphRAGNodeRecallLenFive, IssueTwentySixHistCapTwentyFivePath |
| `0.2500` | 1 | TerraVsFlatRAGCatDSafeMcNemarHolmP, TerraVsHippoRAGCatDSafeMcNemarP |
| `0.0625` | 1 | TerraVsFlatRAGCatDSafeMcNemarP |
| `30.0` | 1 | FlatRagRefusalB, ObscJudgeTwoFlatSafePct |
| `80.0` | 1 | CatBTerraNodeRecallLenFive, TerraUngatedHlcrA |

## Reading this
- Equality with a macro value shows a possible duplicate, not an error: a literal can equal a macro by coincidence (counts, years, sample sizes).
- This scan does not check that a literal is *right*; it only locates where a manual re-check is needed after any macro override. All Phase 3 batches edited prose and overrides by hand; each batch report lists the literals it touched.
- Not done: mapping every literal to its source number (would need the generator scripts), and no change was made to the manuscript or macros.
