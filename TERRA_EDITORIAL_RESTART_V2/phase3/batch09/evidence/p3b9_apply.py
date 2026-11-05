"""Phase 3 Batch 09 (PROPOSAL): R03 introduction/abstract/related-work overclaims (C02,C08,C09,C10,C11,C13,C14,C15,C16,C19,C25,C26).
Byte-preserving, fail-closed. Usage: python3 -X utf8 p3b9_apply.py <src_dir> <diff_out> [--check-only]"""
import difflib, hashlib, os, sys
SRC, DIFF = sys.argv[1:3]; CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = {'main.tex': 'b848d57532d80852b5d357e483f1a88b485481f216b920ff2685f2d824db77ea'}
Y = '\\cite{yalavarthi2026opensourcereproductionexplainabilityanalysis}'
H = '\\cite{hashmi2026adaptivequeryroutingtierbased}'
E = [
 # B9-1 abstract (C02, C01)
 ("a small-model Traffic Cop router sends single-point lookups down a fast path and multi-hop questions through citation traversal, and an autonomous semantic entailment grader evaluates retrieved evidence before generation.",
  "a small-model Traffic Cop router sends single-point lookups down a lighter fast path (retrieval and an entailment check, without graph traversal) and multi-hop questions through citation traversal, and an LLM-prompted entailment grader evaluates retrieved evidence before generation."),
 # B9-2 intro motivation (C08)
 ("consequently, static vector indices inevitably accumulate conflicting, time-stamped versions of the same fact. When queried, standard retrievers surface all of these conflicting versions simultaneously based on semantic similarity, leaving the frozen generative model unable to resolve the chronological authority, which induces severe temporal hallucinations. Furthermore, when processing complex logical derivations, standard pipelines retrieve fragmented textual snippets that sever precedential and doctrinal dependencies, proving entirely insufficient for tasks that require deep, multi-hop reasoning.",
  "consequently, static vector indices can accumulate conflicting, time-stamped versions of the same fact. When queried, a retriever that ranks by semantic similarity may surface several of these versions together, which can leave a frozen generator without a basis for choosing the chronologically authoritative one and lead it to state outdated law. Furthermore, for multi-step logical derivations, similarity-based pipelines can retrieve fragmented textual snippets that omit precedential and doctrinal dependencies, which limits their usefulness for multi-hop reasoning. We motivate the design with these mechanisms and do not measure them in isolation."),
 # B9-3 SHAP sentence (C09) and the preceding evaluator sentence
 ("More critically, current Agentic RAG frameworks rely heavily on corrective evaluators that fail fundamentally on conceptual tasks. Mathematical explainability analyses, such as SHAP, have proven that standard evaluators act merely as superficial named entity alignment detectors, failing to comprehend genuine semantic relevance.",
  "More critically, corrective Agentic RAG frameworks depend on retrieval evaluators that may not capture conceptual relevance. A SHAP-based explainability study of the CRAG T5 retrieval evaluator found that it relies primarily on named-entity alignment rather than semantic similarity " + Y + "."),
 # B9-4 routers (C10)
 ("Compounding this, existing query routers are largely restricted to rigid, binary-channel systems (e.g., pure dense versus pure sparse search), resulting in severe evidence-intent mismatches when unrestricted search floods the context window with noisy, irrelevant data.",
  "Many hybrid retrieval systems route between a small fixed set of channels (e.g., dense versus sparse search), while adaptive multi-strategy routing is emerging " + H + "; a mismatch between query intent and retrieved evidence can add noisy context."),
 # B9-5 router description (C11)
 ("a small language model acts as a Traffic Cop router, dynamically allocating retrieval priority across text chunks, graph subgraphs, and procedural reasoning traces, enabling a bimodal execution profile",
  "a small language model acts as a Traffic Cop router that classifies each query as EASY or HARD, selecting a fast path or citation-graph traversal, which produces a bimodal execution profile"),
 # B9-6 grader description (C13)
 ("an autonomous semantic entailment grader replaces flawed keyword-matching heuristics, verifying the true conceptual and structural relevance of the retrieved evidence.",
  "an LLM-prompted entailment grader, rather than a keyword heuristic, decides whether the retrieved evidence is sufficient to support an answer; its accuracy was not independently validated."),
 # B9-7 evaluation summary (C14, C15, C16)
 ("The proposed framework was rigorously evaluated against comparative baselines, including Direct LLM generation and Flat Vector RAG, alongside component-level ablation studies utilizing comprehensive temporal and multi-perspective reasoning benchmarks. Experimental results demonstrate that the model significantly mitigates the attention dilution and ``context cliff'' limitations inherent in processing overly broad retrieved contexts. By seamlessly aligning chronological facts with procedural reasoning, the model substantially reduces temporal hallucinations in grounded retrieval, providing an experimental research framework for context fidelity in temporal legal AI on historical SCOTUS jurisprudence.",
  "The framework was compared with four baselines, including Direct LLM generation and Flat Vector RAG, on a \\numUniqueQueries-query benchmark, with a 35-query pilot ablation. We did not test attention dilution or context-length effects directly, and TERRA's mean retrieved context is longer than the retrieval baselines' (about 18{,}400 versus 2{,}900--4{,}100 characters). In a 50-query temporal leakage probe, TERRA did not leak less than Flat Vector RAG under default prompting (the preregistered hypothesis $H_1$ is not supported, and Flat RAG refused 23 of 50 queries) but gave more historically correct answers (\\TerraGatedHlcrA{} versus \\FlatRagHlcrA{}). The work is offered as an experimental research framework for context fidelity in temporal legal AI on historical SCOTUS jurisprudence."),
 # B9-8 contribution 3 (C19)
 ("We replace superficial keyword-matching heuristics with a specialized Natural Language Inference (NLI) grader that evaluates retrieved evidence to intercept ungrounded generations, providing qualitative reasoning traces and citation provenance.",
  "We use an LLM-prompted entailment (NLI-style) grader, rather than a keyword heuristic, to evaluate retrieved evidence and gate generation, providing qualitative reasoning traces and citation provenance; its interception reliability is not validated beyond a 5-query pilot ablation."),
 # B9-9 related work (C25, C26)
 ("and current routers rely on superficial keyword-matching that triggers catastrophic failure in high-stakes domains.",
  "and many current routers select among a small set of retrieval channels."),
 ("it ensures that structural precedent topology (what happened and when) and operative judicial analysis (issue, test, and holding) are retrieved as a semantically aligned pair. Furthermore, it replaces flawed entity-alignment evaluators with an autonomous NLI entailment grader and utilizes a continuous three-way Traffic Cop router to dynamically balance textual, graphical, and procedural data.",
  "it retrieves each precedent node together with its structured trace of operative judicial analysis (issue, test, and holding). Furthermore, it uses an LLM-prompted entailment grader in place of an entity-alignment evaluator, and a binary Traffic Cop router that selects between a fast path and citation-graph traversal."),
]
STALE = ['sends single-point lookups down a fast path and', 'inevitably accumulate', 'induces severe temporal', 'have proven that standard evaluators', 'rigid, binary-channel', 'dynamically allocating retrieval priority', 'verifying the true conceptual', 'rigorously evaluated against', 'significantly mitigates the attention', 'substantially reduces temporal hallucinations', 'specialized Natural Language Inference', 'triggers catastrophic failure', 'semantically aligned pair', 'continuous three-way']
raw = open(os.path.join(SRC, 'main.tex'), 'rb').read()
if sha(raw) != PRE['main.tex']: sys.exit('FAIL-CLOSED: pre-hash mismatch for main.tex')
txt = raw.decode('utf-8')
for a, b in E:
    if txt.count(a) != 1: sys.exit(f'FAIL-CLOSED: edit matched {txt.count(a)} times: {a[:80]!r}')
    txt = txt.replace(a, b)
for s in STALE: assert s not in txt, f'post-condition: {s!r} still present'
out = txt.encode('utf-8'); c0, c1 = raw.count(b'\r\n'), out.count(b'\r\n')
print('main.tex: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (c0, c1, raw.count(b'\n') - c0, out.count(b'\n') - c1, sha(out)))
open(DIFF, 'w', encoding='utf-8', newline='').writelines(difflib.unified_diff(raw.decode('utf-8').splitlines(True), txt.splitlines(True), 'a/main.tex', 'b/main.tex'))
if CHECK: print('CHECK-ONLY: nothing written'); sys.exit(0)
open(os.path.join(SRC, 'main.tex'), 'wb').write(out); print('WRITTEN')
