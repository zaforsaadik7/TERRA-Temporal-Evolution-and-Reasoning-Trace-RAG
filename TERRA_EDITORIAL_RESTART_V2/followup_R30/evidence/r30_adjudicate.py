"""Read-only: join graph OVERRULES edges with the reference table (Wikipedia mirror of CRS R45319,
fetched 2026-09-28) by exact U.S. citation of the overruled case (node id = vol_page) and overruling
title; report matches, mismatches, and reference pairs absent from the graph, plus whether intended
targets exist as corpus nodes. Joins with the full-opinion evidence file."""
import json, csv, re, sys
IDX, REF, RAW_CSV, SENT, OUT = sys.argv[1:6]
idx = json.load(open(IDX)); N = idx['nodes']
ref = list(csv.DictReader(open(REF)))
def nid_of(cite):
    v, p = re.match(r'(\d+) U\.S\. (\d+)', cite).groups(); return f'{int(v)}_{int(p):04d}-01'
def key(t): return re.sub(r'[^a-z]', '', re.sub(r'\bdept\.', 'department', t.lower()).split(' v')[0])[:6]
raw = {(r['source'], r['target']): r for r in csv.DictReader(open(RAW_CSV))}
sent = json.load(open(SENT))
ov = [e for e in idx['edges'] if e.get('relation') == 'OVERRULES']
refnid = {}
for r in ref:
    refnid.setdefault(nid_of(r['overruled_cite']), []).append(r)
out = []; matched_ref = set()
for e in ov:
    s, t = e['source'], e['target']; st = N[s]['title']
    cand = [r for r in refnid.get(t, []) if key(r['overruling']) == key(st) or key(r['overruling'])[:4] == key(st)[:4]]
    same_src = [r for r in ref if key(r['overruling'])[:4] == key(st)[:4]]
    if cand:
        verdict = 'MATCH_REFERENCE_BY_EXACT_CITE'; intended = ''
        for r in cand: matched_ref.add((r['overruling'], r['overruled_cite']))
    else:
        verdict = 'NOT_IN_REFERENCE_FOR_THIS_OVERRULING_CASE'
        intended = '; '.join(f"{r['overruled']} {r['overruled_cite']} (node {nid_of(r['overruled_cite'])} {'present' if nid_of(r['overruled_cite']) in N else 'ABSENT'})" for r in same_src)
    rr = raw[(s, t)]; sv = sent[f'{s}->{t}']
    out.append(dict(edge=f'{s}->{t}', overruling=st, overruled_in_graph=N[t]['title'], overruled_graph_cite=rr['target_cite'],
        added_in_issue6=rr['added_in_issue6'], reference_verdict=verdict, reference_candidates_for_same_overruling_case=intended,
        cites_to_target=rr['cites_to_target'], same_sentence_overruling_statements=sv['n_sentences'], evidence_class=rr['evidence_class']))
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
missing = [r for r in ref if (r['overruling'], r['overruled_cite']) not in matched_ref]
print('edges', len(out), 'match', sum(o['reference_verdict'].startswith('MATCH') for o in out))
for o in out:
    if not o['reference_verdict'].startswith('MATCH'): print('MISMATCH', o['overruling'], '->', o['overruled_in_graph'], o['overruled_graph_cite'], '| reference:', o['reference_candidates_for_same_overruling_case'])
print('\nreference pairs NOT represented as an OVERRULES edge:')
for r in missing: n = nid_of(r['overruled_cite']); print(' ', r['overruling'], '->', r['overruled'], r['overruled_cite'], '| node', 'present' if n in N else 'ABSENT')
