# **Review Notes v3: TERRA — Judicial GraphRAG Paper** 

Third-round review — all major prior issues verified as resolved 

This round checks every issue raised in Review Notes v1 and v2 against this manuscript, then does a fresh pass over the newly added material (Table VIII's refusal breakdown, Table X/XI's full FDR family, the expanded Limitations). The short version: this is a genuinely careful revision, not a cosmetic one. 

## **1. Every Previously Flagged Issue — Verified Fixed** 

### **Section IV.C / Fig. 2 topology (previously: frozen/un-recomputed)** 

Now genuinely recomputed for the 20,000-node graph: diameter changed 15→11 hops, average shortest path changed 4.713→4.318, and the entire top-5 betweenness-centrality ranking and hub examples are different cases with different values (Simpson v. Shepard, Fay v. Noia, Ashwander v. TVA, Crowell v. Benson, Dahnke-Walker v. Bondurant — none of which match the old 10k-corpus list). Max degree in the text (Simpson v. Shepard, 276) now matches Table II exactly. This is a real fix, not a re-labeling. 

### **Fig. 1 generator model (previously: contradicted body text)** 

Fig. 1 now labels the generator “Llama-3.3-70B-Instruct,” matching Section III.B.6's databricks-meta-llama-3-3-70b-instruct. Consistent. 

### **HippoRAG's 165/350 refusal count (previously: untraceable)** 

Table VIII now gives a full per-category refusal breakdown for all five pipelines, and every row sums correctly: HippoRAG 62+2+74+27 = 165/350 (47.1%); TERRA 0+0+75+40 = 115/350 (32.9%); Flat RAG 184/350 (52.6%); GraphRAG 173/350 (49.4%). The headline abstract comparison is now fully verifiable from the paper itself. 

### **Table IX's “N=20” FDR family (previously: only 9 of 20 tests shown)** 

Now resolved properly, not just re-labeled: the new Table X shows the 9 headline comparisons, and Appendix A (Table XI) reports the complete, ranked, unredacted 20-test family (4 baselines × 5 evaluation slices, each combination appearing exactly once). All 9 rows in Table X match their corresponding rows in Table XI exactly. We independently re-derived the Benjamini-Hochberg step-up q-values from the reported p-values and ranks ≈ for all 20 rows — 19 of 20 reproduce exactly; one (Rank 6–7, q 0.0004) differs by roughly what you'd expect from the p-values being displayed rounded to 4 significant figures rather than a computation error, and it doesn't change any significance conclusion. This table is now genuinely auditable. 

### **Ablation vs. main-benchmark sourcing (previously: unclear which benchmark a number** 

### **came from)** 

Section VI.A now explicitly states the ablation study's 0.815 Category B figure comes from the 35-query pilot subset, while the main benchmark's 0.695 comes from the expanded 100-query set — addressed directly in prose. The “4.90× operational speedup” claim in Section VI.C is now explicitly cited as “(Table III)”, and the “zero false refusals” claim is now backed by the full 100-query result (0/100, Table VIII), not just the 10-query ablation subset. 

### **“Closely matching Direct LLM” latency wording (previously: overstated)** 

Now correctly reworded: “closely matching Flat RAG's 2.95s and executing 37% faster than Direct LLM's 4.86s median” — the 37% figure checks out arithmetically. 

### **“Fatal constraint violation” (previously: undefined)** 

Now formally defined in Section III.B.1, and the abstract's “10/75 fatal errors” claim is backed by a genuine root-cause breakdown (6 hub-truncation cases + 4 router-misclassification cases = 10) in the new Limitations subsection — this is a real methodological addition, not just a definition patch. 

## **2. Minor Items Still Worth a Look (non-blocking)** 

- The 145,363-edge total for the 20,000-node graph is no longer broken down into PRECEDES vs. OVERRULES counts (the earlier 10k-node draft explicitly reported 722 PRECEDES / 4 OVERRULES). Since OVERRULES edges are architecturally central to the paper's whole motivation, a reviewer will likely ask for this split at the current scale. 

- Byline changed from four authors to two (Saadik and Molla) between this draft and the previous one — worth confirming this is an intentional, agreed authorship change rather than an artifact of merging drafts. 

- One FDR q-value (Rank 6–7 in Table XI, ≈ 0.0004) doesn't re-derive exactly from the displayed p-values; likely just p-value display rounding, but worth a quick recompute from full precision before camera-ready to be safe. 

- Table VIII's Category A refusal count is being used elsewhere as the “false refusal” count (since any refusal on a straightforward factual query is by definition unwarranted). That equivalence is reasonable but is never stated explicitly — a one-line clarification would remove any ambiguity for a reviewer. 

## **3. Verdict** 

**Yes — this version is in genuinely good shape for a Q1 submission.** Every internal contradiction identified across two prior review rounds has been substantively resolved, not just reworded, and this pass did not surface any new arithmetic or cross-reference errors of the kind found before. The statistical reporting (full FDR family with independently-verified q-values, effect sizes, bootstrap CIs, an honest limitations section that includes a result unfavorable to TERRA) is now at a level that should hold up under reviewer scrutiny. 

The remaining gap for a top-tier venue is the one already acknowledged in the paper itself: all faithfulness and safety scoring still relies on an LLM-as-judge rather than licensed legal practitioners. This is honestly disclosed as future work and the code/benchmark are being released for independent replication, which is the right way to handle it — but a Q1 reviewer in a legal-AI-focused venue may still ask whether even a small pilot human-expert evaluation could be run before final acceptance. That's a scope question for you and your students, not a correctness issue with the paper as written. 

Note: this review covers internal numerical consistency, cross-reference accuracy, and statistical reporting as presented in the manuscript text. It does not independently verify the underlying experimental code, raw logs, or the correctness of the LLM-as-judge scoring methodology itself. 

