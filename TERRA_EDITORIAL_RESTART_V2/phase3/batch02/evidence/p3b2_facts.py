"""Phase 3 Batch 02: clear every number in the edited sentences/cells (sentence-level scope). Read-only.
Usage: python -X utf8 p3b2_facts.py <repo_root> <phase1_evidence_dir> <out_csv>
"""
import csv, json, os, re, sys
from scipy.stats import beta

ROOT, P1, OUT = sys.argv[1:4]
rows = []
fact = lambda i, loc, pr, chk, ok, src: rows.append(dict(fact_id=i, location=loc, printed=pr, check=chk, result='VERIFIED' if ok else 'CONFLICT', source=src))
r28 = json.load(open(os.path.join(P1, 'R28', 'r28_20k_active.json'), encoding='utf-8'))['M1_M2_undirected_largest_wcc']
fact('B2-F01', 'Table III', 'diameter 13 hops (undirected, largest WCC)', 'R28 frozen method on active graph 7aa6db46', r28['diameter'] == 13, 'phase1/R28/r28_20k_active.json')
fact('B2-F02', 'Table III', 'ASPL 4.305 hops (undirected, largest WCC)', 'same', f"{r28['aspl']:.3f}" == '4.305', 'phase1/R28/r28_20k_active.json')
fact('B2-F03', 'Table III / text', 'largest WCC 18,558 nodes (existing macro)', 'same', r28['largest_wcc_size'] == 18558, 'phase1/R28/r28_20k_active.json')
lo, hi = beta.ppf(0.025, 1, 5), beta.ppf(0.975, 2, 4)
fact('B2-F04', 'main.tex 5-node item; table_retrieval_eval note', 'exact Clopper-Pearson 95% CI for 1/5 = [0.5%, 71.6%]', 'scipy beta quantiles (independent of Phase 1)', f'{100*lo:.1f}' == '0.5' and f'{100*hi:.1f}' == '71.6', 'scipy.stats.beta')
r10 = json.load(open(os.path.join(P1, 'R09_R10', 'r10_recompute_out.json'), encoding='utf-8'))['canonical_v2']['5_Full_TERRA']['by_len']
fact('B2-F05', 'main.tex seed-anchoring paragraph', 'full gold-node recovery 16/32 (4-node), 1/5 (5-node); 16 incompletely recovered 4-node chains',
     'Phase 1 v2 retrieval recomputation', r10['4']['full'] == 16 and r10['4']['n'] == 32 and r10['5']['full'] == 1 and r10['5']['n'] == 5 and r10['4']['n'] - r10['4']['full'] == 16, 'phase1/R09_R10/r10_recompute_out.json')
txt = open(os.path.join(P1, 'R09_R10', 'r10_citation_recompute_out.txt'), encoding='utf-8').read().split('===== legacy')[0]
f1 = {m.group(1): float(m.group(2)) for m in re.finditer(r'(\d_\w+)\s+macroCR=.*? F1=([\d.]+)', txt)}
ok = (f1['5_Full_TERRA'], f1['4_HippoRAG_Adapted'], f1['2_Flat_Vector_RAG'], f1['1_Direct_LLM']) == (16.02, 15.02, 21.15, 12.17)
fact('B2-F06', 'main.tex citation F1 item', 'TERRA 16.02% > HippoRAG 15.02% (1.07x), > Direct 12.17% (1.32x), < Flat 21.15% (0.76x)',
     'Phase 1 v2 citation recomputation; ratios', ok and f'{16.02/15.02:.2f}' == '1.07' and f'{16.02/12.17:.2f}' == '1.32' and f'{16.02/21.15:.2f}' == '0.76', 'phase1/R09_R10/r10_citation_recompute_out.txt')
m = re.search(r'links total=(\d+) valid=(\d+).*broken=(\d+)\n broken: (\[.*\])', txt)
broken = eval(m.group(4))
qids = sorted({b[0] for b in broken}); ids = [b[2] for b in broken]
g = json.load(open(os.path.join(ROOT, 'dataset_20k_cap', 'terra_eeg_index_20k.json'), encoding='utf-8'))['nodes']
pad = [i for i in ids if i != '118']
fixed = [re.sub(r'^(\d+)_(\d+)-', lambda k: f"{k.group(1)}_{int(k.group(2)):04d}-", i) for i in pad]
fact('B2-F07', 'main.tex links item; table_citation_eval note', '4 unresolved links: 3 page-padding errors of in-corpus cases (queries B073, D038) + bare /case/118 (B075)',
     'v2 broken list; padded IDs normalise to existing nodes', m.group(3) == '4' and qids == ['B073', 'B075', 'D038'] and len(pad) == 3 and all(f in g for f in fixed) and '118' in ids,
     'phase1/R09_R10/r10_citation_recompute_out.txt; active graph')
fact('B2-F08', 'main.tex links item example', '301_001-01 for 301_0001-01 is NLRB v. Jones & Laughlin', 'graph node title', 'Jones & Laughlin' in g['301_0001-01']['title'], 'active graph')
cv = json.load(open(os.path.join(ROOT, 'data', 'terra_canonical_v2_eval.json'), encoding='utf-8'))
c = [r for r in cv if r['pipeline'] == '5_Full_TERRA' and r['category'].startswith('C')]
fact('B2-F09', 'main.tex Category C item', '74 of 75 probes had no retrieved context; 75/75 clean refusals, 0 citations',
     'canonical v2 context_full empty; Phase 1 CatC clean count', sum(not (r['context_full'] or '').strip() for r in c) == 74 and re.search(r'CatC 5_Full_TERRA\s+emitted=0 clean=75/75', txt) is not None,
     'data/terra_canonical_v2_eval.json; r10_citation_recompute_out.txt')
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter(r['result'] for r in rows))
for r in rows:
    if r['result'] != 'VERIFIED':
        print(r)
