"""Phase 3 Batch 07 (PROPOSAL): R21 bibliography metadata and citing-sentence fixes (R03/R21).
Fail-closed, byte-preserving. Usage: python -X utf8 p3b7_apply.py <src_dir> <new_main_bbl> <diff_out> [--check-only]
ref.bib and main.bbl are replaced; main.bbl is the BibTeX output of the new ref.bib (generated in the dry run)."""
import difflib, hashlib, os, re, sys
SRC, NEWBBL, DIFF = sys.argv[1:4]
CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = {'main.tex': 'bf435febc12375acec7e6ea016c686f6bf6e5b32172e97b458af7c151c3c8f7e',
       'ref.bib': 'cbde319532889d5490c1d2ab4e6d2f5477dde1424d192642af62d114e6356a8a',
       'main.bbl': '7be341df38710db2cfa9a61f4c6ed3bedbc038a2c04b0a67728025f3ac35bfb3'}
NL = '\r\n'
def entry(*lines): return NL.join(lines)
NEW_ENTRIES = {  # whole-entry replacements (arXiv @misc -> published @inproceedings); metadata read from the publisher pages
 'zhang2025respectingtemporalcausalconsistencyentityevent': entry(
  '@inproceedings{zhang2025respectingtemporalcausalconsistencyentityevent,',
  '      title={Respecting Temporal-Causal Consistency: Entity-Event Knowledge Graph for Retrieval-Augmented Generation},',
  '      author={Ze Yu Zhang and Zitao Li and Yaliang Li and Bolin Ding and Bryan Kian Hsiang Low},',
  '      booktitle={Proceedings of the 19th Conference of the European Chapter of the Association for Computational Linguistics (EACL)},',
  '      pages={2017--2054},', '      year={2026},', '      doi={10.18653/v1/2026.eacl-long.90}', '}'),
 'liu2026raglearningunderstandinglimits': entry(
  '@inproceedings{liu2026raglearningunderstandinglimits,',
  '      title={RAG or Learning? Understanding the Limits of LLM Adaptation under Continuous Knowledge Drift in the Real World},',
  '      author={Hanbing Liu and Lang Cao and Yang Li},',
  '      booktitle={Findings of the Association for Computational Linguistics: ACL 2026},',
  '      pages={11234--11252},', '      year={2026},', '      doi={10.18653/v1/2026.findings-acl.546}', '}'),
 'li2025cotragintegratingchainthought': entry(
  '@inproceedings{li2025cotragintegratingchainthought,',
  '      title={CoT-RAG: Integrating Chain of Thought and Retrieval-Augmented Generation to Enhance Reasoning in Large Language Models},',
  '      author={Feiyang Li and Peng Fang and Zhan Shi and Arijit Khan and Fang Wang and Weihao Wang and Xin Zhang and Yongjian Cui},',
  '      booktitle={Findings of the Association for Computational Linguistics: EMNLP 2025},',
  '      pages={3119--3171},', '      year={2025},', '      doi={10.18653/v1/2025.findings-emnlp.168}', '}'),
 'liang2025reasoningrag12': entry(
  '@inproceedings{liang2025reasoningrag12,',
  '      title={Reasoning RAG via System 1 or System 2: A Survey on Reasoning Agentic Retrieval-Augmented Generation for Industry Challenges},',
  '      author={Jintao Liang and Gang Su and Huifeng Lin and You Wu and Rui Zhao and Ziyue Li},',
  '      booktitle={Findings of the Association for Computational Linguistics: IJCNLP-AACL 2025},',
  '      pages={1954--1966},', '      year={2025},', '      doi={10.18653/v1/2025.findings-ijcnlp.122}', '}'),
 'bernal2024hipporag': entry(
  '@inproceedings{bernal2024hipporag,',
  '      title={HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models},',
  '      author={Bernal Jim{\\\'e}nez Guti{\\\'e}rrez and Yiheng Shu and Yu Gu and Michihiro Yasunaga and Yu Su},',
  '      booktitle={Advances in Neural Information Processing Systems (NeurIPS)},',
  '      year={2024}', '}'),
}
FIELD_EDITS = {'ref.bib': [  # field-level fixes, each must match once
 ('title={Think-on-Graph: Deep Reasoning on Knowledge Graphs with Large Language Models},', 'title={Think-on-Graph: Deep and Responsible Reasoning of Large Language Model on Knowledge Graph},'),
 ('author={Jiashuo Sun and Chengjin Xu and Lixin Su and Zhengren Dai and Yan Zhang and Xinhua Zhang},', 'author={Jiashuo Sun and Chengjin Xu and Lumingyuan Tang and Saizhuo Wang and Chen Lin and Yeyun Gong and Lionel Ni and Heung-Yeung Shum and Jian Guo},'),
 ('author={Akari Asai and Sewon Min and Zexuan Zhong and Danqi Chen},', 'author={Akari Asai and Zeqiu Wu and Yizhong Wang and Avi Sil and Hannaneh Hajishirzi},'),
 ('title = {The Abuse of Power: The Pervasive Fallacy of Analyzing Statistical Power for Data Analysis},', 'title = {The Abuse of Power: The Pervasive Fallacy of Power Calculations for Data Analysis},'),
 ('title={{CLERC}: A Dataset for Legal Case Retrieval and Retrieval-Augmented Analysis Generation},', 'title={{CLERC}: A Dataset for {U.S.} Legal Case Retrieval and Retrieval-Augmented Analysis Generation},'),
 ('pages={4930--4958},', 'pages={7913--7928},'),
 ('Steven Truitt and Jonathan Larson}', 'Steven Truitt and Dasha Metropolitansky and Robert Osazuwa Ness and Jonathan Larson}'),
 ('booktitle={Advances in Neural Information Processing Systems (NeurIPS)},\r\n      year={2023},', 'booktitle={Advances in Neural Information Processing Systems (NeurIPS), Datasets and Benchmarks Track},\r\n      year={2023},'),
 ('year={2026},\r\n  doi={10.18653/v1/2026.acl-long.1738}', 'pages={37455--37484},\r\n  year={2026},\r\n  doi={10.18653/v1/2026.acl-long.1738}'),
], 'main.tex': [
 # R21: Liu and Cao description
 ('introduced Chronos to track dynamic events in an Event Evolution Graph (EEG),', 'introduced a continuous-knowledge-drift benchmark and Chronos, a time-aware retrieval method that organizes evidence into an Event Evolution Graph (EEG),'),
 # R21: LegalGraphRAG description; statutory-only contrast softened (its graph also covers non-statutory sources)
 ('deploying multi-agent reasoning over a tripartite legal knowledge graph (ontology, fact, and rule layers) for statutory civil and criminal law, while', 'deploying a Researcher, Auditor and Adjudicator multi-agent system over a hierarchical legal graph that organizes legal sources by abstraction level, while'),
 ('However, these systems model codified statutory rules or formal legislative amendment events; in contrast, common-law judicial systems require', 'However, these systems organize legal sources by abstraction level or model formal legislative amendment events; common-law judicial systems additionally require'),
 # R21: CoT-RAG claim
 ('establishing that retrieving structured reasoning sub-cases and decision trees significantly mitigates logical biases compared to unstructured text retrieval.', 'which combines knowledge-graph-guided chain-of-thought generation with retrieval and reports gains of $4.0\\%$ to $44.3\\%$ across nine public reasoning datasets.'),
 # R21: CLERC / CaseHOLD claim
 ('while the Common Law Case Law Retrieval Benchmark (CLERC) \\cite{hou2024clerc} measures multi-step precedent retrieval. These benchmarks confirm that standard lexical or dense retrievers frequently retrieve irrelevant or superseded authority unless procedural reasoning context is explicitly preserved.', 'while CLERC \\cite{hou2024clerc}, a dataset for U.S. legal case retrieval and retrieval-augmented analysis generation, evaluates case retrieval and analysis drafting. As we read them, neither benchmark specifically targets superseded or overruled authority, which is the gap that TERRA\'s evaluation addresses.'),
 # R21: Yalavarthi claims
 ('More critically, the evaluation mechanisms governing these routers are fundamentally flawed.', 'More critically, the evaluation mechanisms governing these routers are themselves open to question.'),
 ('conducted a SHAP explainability analysis on the widely adopted Corrective RAG (CRAG) architecture, mathematically proving that its standard T5-based evaluator functions purely as a named entity alignment detector. Consequently, the CRAG evaluator misclassified $88.3\\%$ of conceptual science tasks as ambiguous and achieved only $5.0\\%$ accuracy on non-entity queries.', 'conducted a SHAP explainability analysis of the T5-based retrieval evaluator in the widely adopted Corrective RAG (CRAG) architecture, finding that it prioritizes named-entity matching over semantic understanding and shows domain-transfer limitations on scientific questions.'),
 # R21: judge-framework citation (RIKER proposes ground-truth-generated evaluation, not an LLM judge)
 ('Evaluated via an LLM-as-a-judge framework \\cite{roig2026scalablereliableevaluationai} using', 'Evaluated via an LLM-as-a-judge framework \\cite{zheng2023judging} using'),
 # R21: CLERC expansion not verified against the paper
 ('(\\textit{Case Law Evaluation and Retrieval Corpus}; Findings of NAACL 2025)', '(Findings of NAACL 2025)'),
 # R21: irrelevant closing citations
 ('(Section~\\ref{subsec:temporal-update-stability}) \\cite{edge2024graphrag, sun2024thinkongraph, zheng2023judging}.', '(Section~\\ref{subsec:temporal-update-stability}).'),
]}
STALE_TEX = ['mathematically proving', 'tripartite', 'Common Law Case Law Retrieval Benchmark', 'multi-step precedent retrieval', 'cite{roig2026', 'Case Law Evaluation and Retrieval Corpus', 'fundamentally flawed']
raw = {f: open(os.path.join(SRC, f), 'rb').read() for f in PRE}
for f, h in PRE.items():
    if sha(raw[f]) != h: sys.exit(f'FAIL-CLOSED: pre-hash mismatch for {f}')
out = {}
bib = raw['ref.bib'].decode('utf-8')
assert bib.count('\r\n') == bib.count('\n'), 'ref.bib not uniformly CRLF'
for key, new in NEW_ENTRIES.items():
    ms = [m for m in re.finditer(r'@misc\{' + re.escape(key) + r',', bib)]
    if len(ms) != 1: sys.exit(f'FAIL-CLOSED: bib entry {key} not found once')
    s = ms[0].start(); e = bib.index('\r\n}', s) + 3
    bib = bib[:s] + new + bib[e:]
for a, b in FIELD_EDITS['ref.bib']:
    if bib.count(a) != 1: sys.exit(f'FAIL-CLOSED: ref.bib edit matched {bib.count(a)} times: {a[:70]!r}')
    bib = bib.replace(a, b)
out['ref.bib'] = bib.encode('utf-8')
tex = raw['main.tex'].decode('utf-8')
for a, b in FIELD_EDITS['main.tex']:
    if tex.count(a) != 1: sys.exit(f'FAIL-CLOSED: main.tex edit matched {tex.count(a)} times: {a[:70]!r}')
    tex = tex.replace(a, b)
for bad in STALE_TEX: assert bad not in tex, f'post-condition: {bad} still in main.tex'
out['main.tex'] = tex.encode('utf-8')
nb = open(NEWBBL, 'rb').read(); out['main.bbl'] = nb
assert os.environ.get('P3B7_BOOTSTRAP') or (b'responsible reasoning' in nb and b'Z.~Wu' in nb and b'7913' in nb), 'new bbl does not reflect the new ref.bib'
diff = []
for f in out:
    before = raw[f]; after = out[f]
    print('%s: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (f, before.count(b'\r\n'), after.count(b'\r\n'), before.count(b'\n') - before.count(b'\r\n'), after.count(b'\n') - after.count(b'\r\n'), sha(after)))
    if f != 'main.bbl': diff += difflib.unified_diff(before.decode('utf-8').splitlines(True), after.decode('utf-8').splitlines(True), f'a/{f}', f'b/{f}')
open(DIFF, 'w', encoding='utf-8', newline='').writelines(diff)
if CHECK: print('CHECK-ONLY: nothing written'); sys.exit(0)
for f, b in out.items(): open(os.path.join(SRC, f), 'wb').write(b)
print('WRITTEN')
