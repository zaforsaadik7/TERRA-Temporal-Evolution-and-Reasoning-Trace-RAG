"""Batch 12 facts (read-only). Usage: python3 -X utf8 p3b12_facts.py <repo_root> <out_csv>"""
import csv, json, os, re, subprocess, collections, sys
ROOT, OUT = sys.argv[1:3]; rows = []
def fact(i, pr, ok, src): rows.append(dict(fact_id=i, printed=pr, result='VERIFIED' if ok else 'CONFLICT', source=src))
g = json.load(open(os.path.join(ROOT, 'dataset_20k_cap', 'terra_eeg_index_20k.json'), encoding='utf-8'))['nodes']
norm, ph, mism = set(), collections.Counter(), 0
for n in g.values():
    x = n['thinking_trace']; m = re.search(r'under (.*?) jurisprudence', x); p = m.group(1) if m else ''
    ph[p] += 1; mism += p != n['category'].replace('_', ' ').title()
    norm.add(re.sub(r'under .*? jurisprudence', 'under D jurisprudence', re.sub(r'\(\d{4}\)', '(Y)', x.replace(n['title'], 'T'))))
fact('B12-F01', 'one distinct trace text across 20,000 nodes after masking title, year, domain phrase (%d)' % len(norm), len(g) == 20000 and len(norm) == 1, 'dataset_20k_cap/terra_eeg_index_20k.json')
fact('B12-F02', 'domain phrase differs from node category in %d of 20,000 nodes (printed 18,247)' % mism, mism == 18247, 'same')
cr = sum(1 for n in g.values() if n['category'] == 'civil_rights_equal_protection')
fact('B12-F03', '"Civil Rights Equal Protection" in %d traces; %d nodes have that category (printed 19,298 and 1,153)' % (ph['Civil Rights Equal Protection'], cr), ph['Civil Rights Equal Protection'] == 19298 and cr == 1153, 'same')
fact('B12-F04', 'no trace contains an issue/test/holding text: every trace has exactly five "Step n:" markers and ends with "Pronounce holding, enter judgment, and transmit mandate."', all(len(re.findall(r'Step \d:', n['thinking_trace'])) == 5 and n['thinking_trace'].rstrip().endswith('transmit mandate.') for n in g.values()), 'same')
out = subprocess.run(['grep', '-rl', '--include=*.py', 'def build_structured_trace', ROOT], capture_output=True, text=True).stdout.strip()
fact('B12-F05', 'build_structured_trace source not found in the staged tree (found: %r)' % out[:60], out == '', 'grep over staged tree (absence of evidence only)')
fact('B12-F06', 'docs/REASONING_TRACE_SPECIFICATION.md not in the staged tree', not os.path.exists(os.path.join(ROOT, 'docs', 'REASONING_TRACE_SPECIFICATION.md')), 'staged tree (absence of evidence only)')
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r['fact_id'], r['result'], r['printed'][:130])
