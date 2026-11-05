# Architecture redesign — isolated I9 candidate

Author: Codex, 25 October 2026. Implementation self-review only.

## Scope and identity

Changed only candidate/src/figure_1_system_architecture.tex and this ledger within reviewer_I9_20261025_01. User explicitly authorized this isolated figure redesign. No build, runtime execution, API/model call, data/statistics change, or promotion performed. Parent retains rendering and acceptance review.

Baseline figure: F:\TERRA -Copy\TERRA_EDITORIAL_RESTART_V2\reviewer_I9_20261025_01\baseline\src\figure_1_system_architecture.tex

Baseline and pre-edit candidate SHA-256: DEE5DD42FC278F816ED003BBF2AA5B194666F5B81A878EF3C5B1DF5D55DC6109

Revised candidate SHA-256: BA83D86D3CA458DD4A72562E25A1BE5DA6FB12C98D637272F413065C2DFE48F6

Read-only retry evidence: ask_terra.py, lines 925–1035; SHA-256 0CCA5CF440A1299853C37899647465B5F1F843803898E630D8D5402A3D9FFFBB.

The I9 baseline hash equals the pre-edit candidate hash (DEE5DD42FC278F816ED003BBF2AA5B194666F5B81A878EF3C5B1DF5D55DC6109). Existing baseline remains byte-preserved. Antigravity-0304 concerns I7 adoption; it does not certify this I9 redesign. Older Claude-0102 addresses historical retrieval comparisons, not figure layout.

## Layout

Replaced the very wide horizontal pipeline with a three-column native-size TikZ layout. Card text is explicitly 8.5 pt with 10 pt leading; phase headings are 9 pt. No geometric or font scaling wrappers. Box text width is 3.27 cm, nominal outer width 3.55 cm, column spacing 4.15 cm. The extreme planned arrow lanes are x=-2.02 and x=10.25 cm: about 12.3 cm total including strokes, below the approximately 12.8 cm target. Planned height is approximately 16 cm, below 17 cm. These are source geometry estimates, not rendered measurements.

Offline and online sections have separate tinted backgrounds. Orthogonal branch/retry/failure paths use dedicated lanes; edge labels have opaque white backgrounds. Matched V and G ports explicitly carry the original vector-query and graph-BFS store interfaces without long wires crossing the routing and grading paths. Their legend is part of the figure. Rectangular decision cards replace space-consuming diamonds; arrows and explicit labels preserve decision semantics.

## Scientific information disposition

- Corpus retained: 20,000 authentic SCOTUS opinions, 1850–1980. Unsupported Pure Substantive Opinion Precedents replaced with Length-filtered opinion precedents; length filtering does not establish substantive purity.
- Parser retained: eyecite, cite.corrected_citation(), and 347 U.S. 483 example.
- Graph retained: extracted CITES, curated OVERRULES, Event Evolution Graph, NetworkX DiGraph EEG, 20,000 nodes, and the unchanged CorpusPrecedentEdges macro invocation.
- Scaffold/vector store retained: deterministic procedural substrate, fixed five-step scaffold, ChromaDB PersistentClient, 20,000 generic scaffolds.
- Query/router retained: Plessy-to-Brown example, intent and complexity, structured EASY/HARD routing.
- EASY retained: grounded anchor retrieval without graph expansion, feeding the shared NLI grader rather than the generator.
- HARD retained: vector top-k document anchors, initial n_results=2, BFS depth two, outgoing and incoming edges, NLI entailment verification and entails == True predicate.
- Generator retained: Llama-3.3-70B-Instruct, T=0.0. Unsupported Verified Citation Links replaced with Generated citation links (audited, imperfect).
- Refusal retained: domain and adversarial refusal, fixed refusal notice, and exhausted-attempt branch.
- Retry corrected: first NLI failure enters self-correction, n_results increases by two, arrow returns to vector retrieval, then BFS and grading repeat. Second failure goes to refusal. Two attempts means initial plus one retry, not two additional retries. The old Expand Search Radius wording is replaced by explicit requery behavior; graph depth remains two.

## Retry provenance and limits

Current ask_terra.py initializes n_results=2 and iterates range(2). Each iteration calls collection.query before extract_graph_context(..., max_depth=2); unsuccessful grading increments n_results by two. This supports the revised current-code control-flow edge. It does not prove every historical evaluation used those exact bytes or behavior. The figure explicitly states that historical run behavior is not established here. Current-code details such as category filtering, exact-title seeds, and ablation bypasses are not silently retrofitted into the historical schematic.

## Verification and parent checkpoint

Source-only review checked component and edge coverage against the preserved baseline and inspected the retry code as text. No scientific quantities or existing macro definitions were changed. No compilation or PDF inspection was performed, as requested. Parent should render at native size in the official sn-jnl wrapper, measure actual bounds, inspect wrapping and arrow clearance, and check that its enclosing figure does not rescale the drawing. Fit, compilation and visual acceptance remain unverified until that checkpoint.