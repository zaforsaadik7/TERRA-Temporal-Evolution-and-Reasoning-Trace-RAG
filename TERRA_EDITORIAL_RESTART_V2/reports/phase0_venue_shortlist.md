# Phase 0 — Venue shortlist against the advisor's ≤25-page ceiling

Checked 2026-09-28 from official author guidelines. Quartiles were read from SCImago (SJR 2025) pages via an automated page reader and **should be confirmed by a human** before they are cited to the advisor. Nothing here selects a journal; the user and advisor decide.

The advisor's ceiling (the whole main PDF, including references and any appendix, ≤25 pages) applies to every option below.

| Journal | Ranking (SJR 2025) | Length rule (official) | Format / template | Review | Fit | Status |
|---|---|---|---|---|---|---|
| **Information Processing & Management** (Elsevier) | Q1 in all 5 categories, incl. Information Systems and Computer Science Applications | No page or word limit stated | LaTeX double-column permitted via Elsevier CAS template (`cas-dc`, installed here; diagnostic build **B4 = 38 pages** unchanged) | Double-anonymized (separate title page) | Strong: retrieval, RAG, evaluation | **Candidate** |
| **Expert Systems with Applications** (Elsevier) | Q1: Artificial Intelligence; Computer Science Applications; Engineering (misc.) | No page or word limit stated | Elsevier LaTeX template encouraged | Double-anonymized | Good: applied AI systems | **Candidate** |
| **IEEE Access** | Q1: Computer Science (misc.); Engineering (misc.); Materials Science (misc.) | No hard limit; "strongly recommend … under 20 pages"; >20 pages (appendices/supplement excluded) requires a pre-submission inquiry to the EIC | IEEE Access double-column template (could not be downloaded from this sandbox: network blocked); B3 IEEE journal class = **36 pages** is the closest proxy | Single-anonymized (IEEE standard; verify) | Broad; accepts systems papers; open-access APC applies (amount to verify) | **Candidate, only with EIC permission for 21–25 pages** |
| **Artificial Intelligence and Law** (Springer) | Q1 in Law; **Q2 in Artificial Intelligence** | No limit stated (not proof of unlimited) | Springer Nature LaTeX template recommended (not installed; not downloadable here) | Double-anonymous | Best domain fit | **Candidate**; "Q1" holds only for the Law category |
| Knowledge-Based Systems (Elsevier) | — | "preferably no more than 20 double line spaced manuscript pages, including tables and figures" | — | Single-anonymized | — | **Excluded**: far below the achievable length without losing evidence |
| IEEE Computer Society Transactions (e.g. TKDE) | — | 12 formatted pages is the overlength-charge threshold ($220/page); submission limits are journal-specific | — | — | — | **Not recommended** unless its specific submission limit is checked and accepted |

## Consequences for the work (all venues)

- **Unchanged-content page counts:**
  - IEEE conference class under XeLaTeX (provenance build): 39
  - IEEE conference class, Times font: 37
  - IEEE journal class: 36
  - Elsevier CAS double-column: 38
- **Reaching ≤25 means removing about 11–14 pages (30–36%).** The 23 tables and 3 figures stay by default, so running prose must shrink by roughly 40–45%. Results are 49% of the prose (see `ledgers/section_budget_baseline_by_section.csv`), so that is where most of the reduction must come from.
- **Double-anonymized venues (IP&M, ESWA, AI & Law)** need an anonymized review build: author block removed, GitHub/Zenodo links anonymized, self-identifying wording removed. That is a later packaging task, not a content change.
- **Every candidate requires a generative-AI use declaration.** Elsevier asks for a section before the references; IEEE Access states its own disclosure requirements. The authors must write this truthfully; it is flagged here only as a requirement.

## Claude's recommendation (for discussion; not a decision)

**Information Processing & Management** fits best on topic, ranking and length together. It is Q1 in every category, has no stated length cap, permits the double-column LaTeX template, and the unchanged paper already measures 38 pages in that template, so ≤25 is the same size of effort as in IEEE format.

**IEEE Access** is a good second choice if the advisor prefers IEEE, but 21–25 pages there requires EIC permission.

**AI & Law** is the best domain match, but it is Q1 only in Law.

## Sources

- [IP&M guide for authors](https://www.sciencedirect.com/journal/information-processing-and-management/publish/guide-for-authors)
- [ESWA guide for authors](https://www.sciencedirect.com/journal/expert-systems-with-applications/publish/guide-for-authors)
- [KBS guide for authors](https://www.sciencedirect.com/journal/knowledge-based-systems/publish/guide-for-authors)
- [IEEE Access submission guidelines](https://ieeeaccess.ieee.org/authors/submission-guidelines/)
- [IEEE Computer Society author resources](https://www.computer.org/publications/author-resources)
- [AI & Law submission guidelines](https://link.springer.com/journal/10506/submission-guidelines)
- SJR pages: [IP&M](https://www.scimagojr.com/journalsearch.php?q=12689&tip=sid), [ESWA](https://www.scimagojr.com/journalsearch.php?q=24201&tip=sid&clean=0), [IEEE Access](https://www.scimagojr.com/journalsearch.php?q=21100374601&tip=sid), [AI & Law](https://www.scimagojr.com/journalsearch.php?q=13880&tip=sid&clean=0)
