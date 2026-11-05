# R30 follow-up: OVERRULES case-identity and downstream-impact audit

- **Author:** Claude (implementer). Codex audits.
- **Date:** 2026-09-28.
- **Authorization:** `user_authorizations/20260928T1400Z-user-authorizes-overrules-audit.md`. The user answered: "I approve item 1 only".
- **Scope honoured:**
  - Read-only.
  - No change to the graph, dataset, manuscript or macros.
  - No LLM/API calls. The one web fetch was a reference table; see §1.
  - The code comparison (item 2) and Phase 2 were **not** started.
- **Evidence folder:** `evidence/`. It holds the scripts, CSV/JSON outputs and the reference table; hashes are in `manifest.sha256`.

## 1. Sources and method

| Evidence | Source | Notes |
|---|---|---|
| E0: graph edges | Active 20k index `terra_eeg_index_20k.json` (sha `7aa6db46…`) | All 56 edges have `relation = OVERRULES` and `overruling_source = CRS_R45319_TABLE`. The pre-Issue-6 backup (`012c999b…`) identifies which edges were added. |
| E1: structured citation | Full CAP opinion JSON for each of the 47 overruling cases (`dataset_20k_cap/raw_cases/<id>.json`, staged read-only) | Does the overruling opinion's own `cites_to` list contain the overruled case? |
| E2: opinion text | Same CAP files | The majority opinion is screened for sentences that name the target (U.S. citation or distinctive party name) together with an overruling-type cue. This is a **screen**, not a legal reading. |
| E3: reference table | The Wikipedia "List of overruled United States Supreme Court decisions" | See the note below. |

**Why Wikipedia for E3:**
- `build_issue6_holdings_and_edges.py` says the edges were built from "a Wikipedia HTML mirror of CRS Report R45319". The mirror file itself is on a different machine path (`C:/Users/zafor/...`) and is not in the repo.
- The CRS PDF could not be fetched here, because the site's robots rules block automated access.
- I retrieved the Wikipedia rows for all 47 overruling cases on 2026-09-28 and transcribed them to `evidence/r30_reference_table_wikipedia.csv` (60 pairs).
- **Caveat:** the fetch passes through a summarising model, so transcription errors are possible. This is mitigated because:
  - every one of the 53 matches is joined on the **exact U.S. citation** encoded in the node ID, and is independently confirmed by E1;
  - the 3 mismatches are confirmed by the opinion text and by Codex's separate check against the CRS PDF.

**Superseded first pass:** `r30_edge_textcheck.*` searched the node `text` field, which is truncated to 3,000 characters in the index. It is superseded by the full-opinion checks (`r30_edge_rawcheck.*`, `r30_sentence_check.*`) and is kept only for transparency.

**Absence rule:** absence from the reference table was **not** treated as proof of error. No edge in this audit was judged on absence alone.

## 2. Result: 53 consistent, 3 mis-resolved

**53 edges (all retyped from CITES): CONSISTENT.**
- Each matches a reference-table pair by exact overruled-case citation and overruling-case name.
- In each, the overruled case is cited in the overruling opinion (E1 true in 53/53).
- 35 of the 53 also have an automated screen hit (E2). The other 18 do not. That is **not** evidence of error: the screen misses overrulings phrased differently, partial or implicit ones, and ones whose statement sits in another sentence. For example, *Darby*'s "It should be and now is overruled" does not name *Hammer* in the same sentence.
- Several screen hits are false positives. For example, *Chimel*'s "The Court rejected Harris' … claim" is not the overruling statement.
- So E2 is a triage signal only; it does not adjudicate anything.

**3 edges (exactly the 3 added in Issue 6): MIS-RESOLVED.**

| Graph edge | Reference pair | Opinion evidence | Intended node in corpus? |
|---|---|---|---|
| Edelman v. Jordan (1974) → **NLRB v. Wyman-Gordon Co.**, 394 U.S. 759 | Edelman → **Wyman v. Bowens**, 397 U.S. 49; also Shapiro, Zarate, Sterrett | Wyman-Gordon is cited 0 times and mentioned 0 times in any Edelman opinion | Absent (397_0049). Edelman → Shapiro is already a correct edge. |
| Griffin v. Breckenridge (1971) → **Frisbie v. Collins**, 342 U.S. 519 | Griffin → **Collins v. Hardyman**, 341 U.S. 651 | Griffin discusses "Collins v. Hardyman" (10 name hits); Frisbie is never cited | Absent (341_0651) |
| Hensley v. Municipal Court (1973) → **Norwood v. Baker**, 172 U.S. 269 | Hensley → **Baker v. Grice**, 169 U.S. 284, with Wales, Johnson and Stallings | Hensley's list names "Baker v. Grice, 169 U.S. 284 (1898)"; Norwood is never cited | Absent (169_0284) |

**Mechanism (reproduced from the code):**
1. The citation lookup failed, because the intended overruled case is not in the 20k corpus.
2. The resolver then fell through to "Strategy C". That strategy matches the **first party name** of the overruled case as a substring of any corpus title within ±2 years:
   - "wyman" matched "NLRB v. Wyman-Gordon" (1969 vs 1970);
   - "collins" matched "Frisbie v. Collins" (1952 vs 1951);
   - "baker" matched "Norwood v. Baker" (1898).

   These are identity errors from a name heuristic, not legal disagreements.
3. A secondary defect: the resolver iterates `ndata.get("citations", [])`, but that field is a **string**, not a list. Its citation regex therefore never fires. Resolution relied on node IDs, whose volume and page happen to encode the official citation, and then on the name heuristic.

**This supersedes the Phase 1 wording.** The "serious suspicion" about the Hensley edge (Codex-0010) is resolved: that edge is also mis-resolved.

## 3. Downstream impact

| Dependent object | Uses a mis-resolved edge? | Evidence | Impact |
|---|---|---|---|
| Main 350-query benchmark: TERRA deployed contexts | **No** | Across all 350 TERRA contexts, only 2 OVERRULES pairs were ever serialised: Barnette→Gobitis (4 rows) and Brown→Plessy (3 rows). Both are correct. | None on any reported benchmark number |
| Category D (overruled-precedent items) | **No** | The overruled targets of Category D are 9 distinct nodes across 13 query-target links. All 9 are among the 53 consistent edges. | None |
| Category A item A022 (Hensley decision date) | No | It uses the Hensley node, not the edge | None |
| Obscure overruled-precedent suite (30 items) | **No** | All 30 item edges are among the 53 consistent edges. Two items use Hensley's *correct* edges (OBS_010 → Stallings, OBS_018 → Johnson). The paper excludes "three edges whose overruling opinions never mention the target case as corrupted". My E1 check finds exactly these 3 edges uncited, so the excluded three are, with high likelihood, the mis-resolved ones. No exclusion list was found in the repo, so this is an inference. | None on suite results. The exclusion wording should say *why*: the edges were mis-resolved. |
| Graph topology (Table III) | Marginal | The active graph minus the 3 edges equals the pre-Issue-6 topology exactly (verified: same node set; the edge-set difference is exactly these 3). R28 already computed both: diameter 13 / 13; ASPL 4.30495 vs 4.30498; largest WCC 18,558 vs 18,558. | Unchanged at the printed precision (13, 4.305, density 0.000363, mean degree 14.54) |
| Edge counts in text/macros | **Yes** | `\IssueTwentyOneOverrulesEdges` = 56; `\IssueTwentyThreeActiveOverrules` = 56; `\IssueTwentyThreeCrsAddedEdges` = 3; `\CorpusPrecedentEdges` / `\IssueTwentyThreeActiveEdges` = 145,366; Table baseline_specifications "56 OVERRULES"; line 393 accounting equation | Counts are structurally correct as a description of the file. Legally, only 53 are consistent. Wording must not call all 56 "authoritative". |
| Provenance wording | **Yes** | Line 165: "56 authoritative typed OVERRULES edges imported from CRS annotations … denoting explicit judicial abrogation"; line 808: "19 ⊂ 56 … cataloged by the official CRS". The edges came from a Wikipedia mirror of CRS, were resolved by a heuristic, 3 are wrong, and several overrulings are partial or implicit. | Needs scoping |
| "19 ⊂ 56" claim (line 808) | Unit mismatch | 19 Category D *queries* map to 9 distinct OVERRULES edges | Needs correction, independent of the 3 bad edges |

**Coverage limitation (not assessed):** reference-table pairs whose overruling case is **not** among the 47 overruling nodes were not checked. The build restricted itself to overruling year ≤ 1980, and I fetched only rows for the 47. So this audit checks the *correctness* of the 56 edges, not the *completeness* of the OVERRULES layer. Seven reference pairs for the 47 cases have no edge because the overruled case is absent from the corpus: Bakelite, Collins v. Hardyman, Baker v. Grice, Zarate, Sterrett, Wyman v. Bowens, and Sapir.

## 4. Proposed corrections (proposals only; Phase 3 needs item-by-item approval)

1. **Data (needs separate user approval; nothing done):** retire or relabel the 3 mis-resolved edges. The intended targets are absent from the corpus, so the correct edge cannot be substituted. The options, for the user to choose between, are:
   - (a) remove the 3 edges;
   - (b) keep them in the file but mark them `verification_status = MISRESOLVED` and exclude them from any OVERRULES count.

   Neither option changes any reported benchmark result (§3).
2. **Manuscript wording:**
   - State "53 verified OVERRULES edges", or "56 tagged edges, of which 3 were found mis-resolved".
   - Describe the source as "the Wikipedia list mirroring CRS R45319, resolved to corpus nodes by citation and name matching, and audited against the overruling opinions".
   - Replace "explicit judicial abrogation" with "overruled in whole or in part".
   - Fix "19 ⊂ 56" to "19 Category-D queries over 9 OVERRULES edges".
   - Update the accounting line (R07) accordingly.
3. **Obscure suite:** state that the 3 excluded edges were mis-resolved identities. Tie this to the audit file, keeping the remark that this attribution is inferred.
4. **Codebase note (for reproducibility):** document the Strategy C heuristic and the string-typed `citations` field as known defects of the build script.

## 5. Status

- R30 moves from BLOCKER-OPEN to **RESOLVED-AS-FINDING**: 3 of 56 edges are mis-resolved, 53 are consistent, and no reported benchmark result depends on the 3.
- Two decisions remain the user's:
  - the data disposition (4.1);
  - the wording corrections, in Phase 3.
- The code comparison (item 2) and Phase 2 have **not** started and need separate approval.
