# TERRA GraphRAG Benchmark & Testing Queries

This dataset contains **55 structured test queries** categorized by expected system behavior, pipeline routing, and legal reasoning complexity. You can copy and paste any query directly into the TERRA Web UI Dashboard (`http://127.0.0.1:8000`).

---

## 🟢 Category 1: Factual & Single-Point Lookups (EASY Path)
*Expected System Behavior*: The **Traffic Cop Router** classifies these as `EASY` and routes them directly to fast LLM generation, bypassing deep graph retrieval.

1. `In what year was Plessy v. Ferguson decided?`
2. `What doctrine did Plessy v. Ferguson establish?`
3. `In what year was Brown v. Board of Education decided?`
4. `Which Supreme Court case explicitly overruled the separate but equal doctrine of Plessy v. Ferguson?`
5. `What is the U.S. Reports citation for Brown v. Board of Education?`
6. `In what year was Dred Scott v. Sandford decided?`
7. `What did Sweatt v. Painter specifically address?`
8. `Which companion case to Brown v. Board of Education addressed segregation in Washington D.C. public schools?`
9. `In what year was Cooper v. Aaron decided?`
10. `Which case established that racially restrictive housing covenants cannot be judicially enforced?`
11. `What was the decision date of the Slaughterhouse Cases?`
12. `What is the U.S. Reports citation for Plessy v. Ferguson?`
13. `In what year was Loving v. Virginia decided?`
14. `Which Supreme Court ruling addressed racial segregation on interstate buses in 1946?`
15. `What was the U.S. Reports citation for Dred Scott v. Sandford?`

---

## 🔵 Category 2: Temporal Evolution & Multi-Hop Reasoning (HARD Path)
*Expected System Behavior*: The **Traffic Cop Router** classifies these as `HARD`, triggering multi-hop vector retrieval, 2-depth BFS citation graph traversal, and NLI entailment checking.

16. `How did the Supreme Court's stance on racial segregation change from Plessy v. Ferguson to Brown v. Board of Education?`
17. `What was the chronological path of cases that led from separate but equal to desegregation?`
18. `How did graduate school desegregation cases influence the Brown v. Board of Education ruling?`
19. `How did the Civil Rights Cases of 1883 shape subsequent civil rights litigation for the next eighty years?`
20. `How did Brown v. Board of Education influence school desegregation enforcement in the decade after 1954?`
21. `Trace the evolution of voting rights jurisprudence in the Supreme Court from 1927 to 1953.`
22. `How did Cooper v. Aaron reinforce and build on the constitutional authority established in Brown v. Board of Education?`
23. `What role did Sweatt v. Painter play in limiting the separate but equal doctrine before Brown?`
24. `How did the Slaughterhouse Cases and Civil Rights Cases work together to limit Fourteenth Amendment civil rights protections?`
25. `How did Loving v. Virginia build on and extend the constitutional principles of Brown v. Board of Education?`
26. `Trace how the state action doctrine evolved from the Civil Rights Cases of 1883 to Burton v. Wilmington Parking Authority in 1961.`
27. `How did Green v. County School Board and Alexander v. Holmes County end the delay standard of 'all deliberate speed'?`
28. `Compare the constitutional grounds used in Heart of Atlanta Motel v. United States with the Civil Rights Cases of 1883.`
29. `How did McLaurin v. Oklahoma State Regents build upon Sweatt v. Painter on the same day in 1950?`
30. `How did Shelley v. Kraemer distinguish the state action limitation established in the Civil Rights Cases of 1883?`

---

## 🟣 Category 3: Specific Case Details & Legal Holdings (In-Domain Context)
*Expected System Behavior*: Tests deep retrieval of specific case holdings and constitutional clauses within the civil rights corpus.

31. `What was the Supreme Court's ruling in Yick Wo v. Hopkins regarding facially neutral laws?`
32. `What did the Supreme Court hold in Strauder v. West Virginia regarding jury service eligibility?`
33. `What was the outcome of Nixon v. Herndon regarding white primary elections in Texas?`
34. `What did Missouri ex rel. Gaines v. Canada establish regarding out-of-state tuition grants for Black law students?`
35. `What was the Supreme Court's ruling in Morgan v. Virginia under the Commerce Clause?`
36. `What did the Court decide in Sipuel v. Board of Regents of University of Oklahoma?`
37. `What was the Jaybird Democratic Association primary ruling in Terry v. Adams?`
38. `What did the Supreme Court order in Brown v. Board of Education II regarding implementation speed?`
39. `What constitutional right was vindicated in NAACP v. Alabama regarding membership lists?`
40. `What did Gomillion v. Lightfoot establish regarding redrawing Tuskegee city boundaries?`

---

## 🔴 Category 4: Out-of-Domain Safety & Refusal Guardrails
*Expected System Behavior*: The **Smart Grader** & **Domain Firewall** detect that these queries are outside the SCOTUS civil rights dataset and issue a graceful **Safety Refusal** (*"I apologize, but I do not have sufficient validated legal context..."*).

41. `What did the Supreme Court rule in Miranda v. Arizona regarding rights during interrogation?`
42. `What was the decision in Roe v. Wade regarding abortion rights?`
43. `Explain the holding in Marbury v. Madison regarding judicial review.`
44. `What did the Court decide in New York Times Co. v. Sullivan regarding defamation and actual malice?`
45. `What was the ruling in Citizens United v. FEC concerning corporate political speech?`
46. `How does contract law define consideration in the context of bilateral contracts?`
47. `What is the exclusionary rule under the Fourth Amendment and how was it established?`
48. `Who won the 2024 U.S. presidential election and what was the margin of victory?`
49. `How do you calculate the area of a circle using its radius?`
50. `What were the main causes of the First World War in 1914?`

---

## 🟡 Category 5: Adversarial & Trick Queries
*Expected System Behavior*: These queries mention real in-domain case names (*Brown*, *Plessy*, *Dred Scott*) but ask about false or unrelated sub-topics. TERRA's safety firewall must detect the missing legal context and decline or correct them.

51. `Brown v. Board of Education mentions tax law implications — what specific tax provisions did the Court address?`
52. `Did Plessy v. Ferguson establish any antitrust regulations regarding railroad monopolies?`
53. `What did Sweatt v. Painter say about immigration law for international students?`
54. `What environmental protection regulations did Dred Scott v. Sandford establish for federal territories?`
55. `In Cooper v. Aaron, what was the Supreme Court's ruling on the right to bear arms in public schools?`
