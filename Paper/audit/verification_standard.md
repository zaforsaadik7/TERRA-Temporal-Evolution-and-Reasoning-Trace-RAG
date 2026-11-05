# Standing Verification Standard: Dual-Tier Evaluation & Audit Protocol

- **Document Version:** 1.0 (Mandatory Repository Standard)
- **Date Effective:** 2026-09-05
- **Status:** ACTIVE & MANDATORY FOR ALL REMAINING WORKSTREAMS

---

## 1. Purpose and Background

Across multiple research phases in the TERRA repository, audit history revealed a consistent failure pattern: automated scripts produce artifacts that pass all structural, shape, and count invariants (e.g., matching target numbers, non-null fields, correct keys), yet conceal substantive defects upon qualitative review of actual content. Historical examples include:
1. **Civil Rights Keyword Inflation:** A crude lexical match on `"state"` and `"board"` inflated the apparent civil-rights corpus fraction to 59.8% when substantive coverage was 4.99%.
2. **Procedural Cert-Denial Singletons:** 2,500 procedural one-line orders artificially diluted graph connectivity and average node degree.
3. **Domain Boundary Firewall Invariance:** Vector pre-filtering ($d_{L2} < 1.3$) intercepted 0% of out-of-domain queries at 10k scale, despite the system appearing safe due to downstream NLI gating.
4. **Category B Path Collapses & Syntactic Templating:** 100 Category B queries collapsed into 2-node endpoints due to citation edge directionality, while 19 Category D3 queries adhered to an identical fill-in-the-blank syntactic formula.
5. **Conversational Summary Narration Drift:** While the underlying LaTeX/macro pipeline held up perfectly ($\JudgePearsonR = 0.399$), the conversational reporting layer hallucinated an ungrounded literal figure ($r = 0.612$) in chat text, demonstrating that agent narration must be subjected to the same skepticism as experimental code.

To permanently eradicate this class of errors, this document establishes a **mandatory, standing Verification Standard** that must be fulfilled and documented before any dataset, benchmark, evaluation run, or ablation study is declared audited and frozen.

---

## 2. The Verification Standard

Every future workstream deliverable (including Workstreams 1.1, 1.2, 1.3, and full ablation reruns) must satisfy all tiers:

### Tier 0: Narration & Conversational Summary Skepticism (Source-Macro Invariance)
**Numeric claims stated in conversational summaries, chat responses, or markdown walkthroughs are explicitly deemed provisional and non-authoritative.**
1. **Never Trust Un-Traced Chat Numbers:** Any quantitative claim reported in an agent message or summary must cite the specific macro name (e.g., `\JudgePearsonR`) or source data path.
2. **Direct Source Verification:** Human reviewers and agents must verify all numbers against `Paper/generated_stats.tex` or `Paper/generated_corpus_stats.tex` before accepting them as true.
3. **Manuscript Invariance:** `Paper/main.tex` must never hardcode experimental result numbers; all results must flow strictly from programmatic macro generators verified by `check_consistency.py`.
4. **Citation-Attribution Invariance:** A verified citation is not proof of an attributed claim. Every specific quantitative finding, empirical score band, or threshold attributed to an external paper (e.g., modularity values, accuracy numbers) must be verified directly against the cited source text, not accepted on plausible author/year familiarity. Plausible but ungrounded attributions are treated as hallucinations.

### Tier 1: Programmatic Invariant Proof (Automated Shape & Cryptographic Grounding)
The deliverable must pass automated assertions verifying:
1. **Exact Allocations:** Exact query counts, category splits, and subtype distributions matching pre-registered protocols.
2. **Schema & Typology:** Zero missing keys, correct data types, valid range constraints, and non-empty payload strings.
3. **Graph & Relational Invariants:** Topological properties (e.g., path length bounds $3 \le k \le 5$, acyclicity where required, node existence in underlying indices).
4. **Cryptographic Checksumming:** Permanent SHA256 registration in `Paper/audit/data_inventory.md` and integration into LaTeX macro pipelines via `check_consistency.py`.

### Tier 2: Substantive Content Spot-Check Audit (Qualitative Human/Domain Review)
Automated shape checks alone are **explicitly deemed insufficient** for sign-off. Before freezing:
1. **Representative Stratified Sample:** A random sample of at least 5 items per category/subtype (or ~10% of total payload) must be drawn.
2. **Substantive Correctness Review:** The actual text, legal premises, holding summaries, and retrieved trajectories must be read and verified for:
   - **Doctrinal Accuracy:** Are legal claims supported by verified primary/secondary authorities?
   - **Topological Coherence:** Do multi-hop paths represent a genuine legal and narrative evolution, rather than coincidental procedural citations?
   - **Syntactic Diversity:** Are queries formulated with natural authorial variation, devoid of repetitive synthetic boilerplate templates?
   - **Appropriate Difficulty:** Does the test item genuinely challenge the designated architectural mechanism without artificial ambiguity?
3. **Consolidated Audit Reporting:** Findings must be compiled into a single consolidated report presenting both programmatic metrics and the sampled content text before approval.

---

## 3. Implementation Checklist for Future Workstreams

Before declaring any workstream complete:
- [ ] Tier 1 script executed and automated assertions passed without warnings.
- [ ] Tier 2 qualitative spot-check completed on a random sample of actual text.
- [ ] Fallback paths (if any) explicitly reported and surfaced, with zero silent degradations.
- [ ] SHA256 checksum recorded in `Paper/audit/data_inventory.md`.
- [ ] End-to-end `build_paper.py` consistency pipeline executed and clean.
