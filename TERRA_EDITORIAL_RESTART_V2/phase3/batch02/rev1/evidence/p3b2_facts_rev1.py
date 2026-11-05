"""Batch 02 rev1: additional fact checks for the new/changed literals (644, 16, 97.0%, doctrinal CP ordering). Read-only.
Usage: python -X utf8 p3b2_facts_rev1.py <repo_root> <phase1_evidence_dir> <src_dir> <out_csv>"""
import csv, json, os, re, sys
ROOT, P1, SRC, OUT = sys.argv[1:5]
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from audit_citation_correctness import build_case_lookup_index, extract_case_entities
rows = []
def fact(i, loc, pr, chk, ok, src): rows.append(dict(fact_id=i, location=loc, printed=pr, check=chk, result='VERIFIED' if ok else 'CONFLICT', source=src))
nodes = json.load(open(os.path.join(ROOT, 'dataset_20k_cap', 'terra_eeg_index_20k.json'), encoding='utf-8'))['nodes']
t2n, a2n = build_case_lookup_index(nodes)
cv = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
tot = valid = exact = 0; bad = []
for r in cv:
    if r['pipeline'] != '5_Full_TERRA': continue
    links, _, _ = extract_case_entities(r.get('answer_full', '') or '', '5_Full_TERRA', nodes, t2n, a2n)
    for lk in links:
        tot += 1; valid += bool(lk['is_valid']); exact += lk['target'] in nodes
        if not lk['is_valid']: bad.append((r['query_id'], lk['target']))
fact('B2R-F01', 'main.tex links item', '660/664 pass the validator; 4 fail', 'project extractor on canonical v2 (read-only import)', (tot, valid) == (664, 660) and len(bad) == 4, 'scripts/audit_citation_correctness.py; data/terra_canonical_v2_eval.json')
fact('B2R-F02', 'main.tex links item; table note', '644 of 664 have an identifier that exists as written (97.0%)', 'identifier in graph nodes, independent count', exact == 644 and f'{100*exact/tot:.1f}' == '97.0', 'active graph 7aa6db46; canonical v2')
fact('B2R-F03', 'main.tex links item', 'the other 16 links with a non-existent identifier were accepted on caption match', '664-644 = 20 non-existent; 4 fail validator; 20-4 = 16 pass via title/alias', tot - exact == 20 and (tot - exact) - len(bad) == 16, 'same')
t = open(os.path.join(P1, 'R09_R10', 'r10_citation_recompute_out.txt'), encoding='utf-8').read().split('===== legacy')[0]
d = {m.group(1): float(m.group(2)) for m in re.finditer(r'(\d_\w+)\s+macroCR=.*?DEP\(xfaith\)=([\d.]+)', t)}
mac = open(os.path.join(SRC, 'generated_stats.tex'), encoding='utf-8').read()
g = lambda n: re.search(r'\\newcommand\{\\%s\}\{([\d.]+)' % n, mac).group(1)
macv = (g('CatBTerraDoctrinalCitationPrecision'), g('CatBHippoRAGDoctrinalCitationPrecision'), g('CatBFlatDoctrinalCitationPrecision'), g('CatBDirectDoctrinalCitationPrecision'), g('CatBGraphRAGDoctrinalCitationPrecision'))
T, H, F, D, G = d['5_Full_TERRA'], d['4_HippoRAG_Adapted'], d['2_Flat_Vector_RAG'], d['1_Direct_LLM'], d['3_GraphRAG_Adapted']
fact('B2R-F04', 'main.tex Doctrinal Support Precision item', 'TERRA 9.30 > Hippo 9.06, Direct 7.08, GraphRAG 6.29; < Flat 14.15 (judge-weighted)', 'Phase 1 recomputation vs frozen macros', macv == ('9.30', '9.06', '14.15', '7.08', '6.29') and T > H and T > D and T > G and T < F and F == max(d.values()), 'r10_citation_recompute_out.txt; generated_stats.tex')
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter(r['result'] for r in rows))
for r in rows:
    if r['result'] != 'VERIFIED': print(r)
