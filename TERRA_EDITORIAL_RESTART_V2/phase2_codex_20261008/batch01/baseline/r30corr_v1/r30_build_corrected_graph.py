"""Build the versioned corrected graph copy (R30) by exact BYTE-LEVEL removal of the three adjudicated
mis-resolved OVERRULES edge records from the active 20k graph. Every other byte is preserved, so the
derivative differs from the source only by these three records (and their preceding ', ' separators).
Fail-closed: aborts unless the source hash matches, each record occurs exactly once, the output parses,
and the parsed edge set equals the source edge set minus exactly these three pairs.
Usage (repo root):  python -X utf8 <this> <source_json> <output_json> <provenance_json>"""
import sys, json, hashlib, collections
SRC, OUT, PROV = sys.argv[1:4]
EXPECTED_SRC_SHA = '7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad'
REMOVE = [('415_0651-01', '394_0759-01'), ('403_0088-01', '342_0519-01'), ('411_0345-01', '172_0269-01')]
def rec(s, t): return (', {"source": "%s", "target": "%s", "relation": "OVERRULES", "overruling_source": "CRS_R45319_TABLE"}' % (s, t)).encode()
b = open(SRC, 'rb').read(); src_sha = hashlib.sha256(b).hexdigest()
if src_sha != EXPECTED_SRC_SHA: sys.exit(f'ABORT: source sha {src_sha} != expected')
nb = b
for s, t in REMOVE:
    r = rec(s, t); n = nb.count(r)
    if n != 1: sys.exit(f'ABORT: record {s}->{t} occurs {n} times')
    nb = nb.replace(r, b'', 1)
src = json.loads(b); new = json.loads(nb)
E0 = collections.Counter((e['source'], e['target'], e.get('relation')) for e in src['edges'])
E1 = collections.Counter((e['source'], e['target'], e.get('relation')) for e in new['edges'])
removed = E0 - E1; added = E1 - E0
assert not added, 'ABORT: edges added'
assert set(removed) == {(s, t, 'OVERRULES') for s, t in REMOVE} and sum(removed.values()) == 3, f'ABORT: removed={removed}'
assert new['nodes'] == src['nodes'], 'ABORT: node payload changed'
hdr0 = {k: v for k, v in src.items() if k not in ('nodes', 'edges')}; hdr1 = {k: v for k, v in new.items() if k not in ('nodes', 'edges')}
assert hdr0 == hdr1, 'ABORT: header changed'
n = len(new['nodes']); m = len(new['edges'])
rel = collections.Counter(e.get('relation') for e in new['edges'])
open(OUT, 'wb').write(nb); out_sha = hashlib.sha256(nb).hexdigest()
prov = dict(derivative=OUT.replace('\\', '/').split('/')[-1], derivative_sha256=out_sha, derivative_bytes=len(nb),
            source='dataset_20k_cap/terra_eeg_index_20k.json', source_sha256=src_sha, source_bytes=len(b),
            method='byte-level removal of exactly three edge records (each with its preceding ", " separator); all other bytes identical',
            removed_edges=[dict(source=s, target=t, relation='OVERRULES', reason='mis-resolved case identity (R30; intended target absent from corpus)') for s, t in REMOVE],
            counts=dict(nodes=n, edges_listed=m, relations=dict(rel), unique_directed_pairs=len({(e['source'], e['target']) for e in new['edges']})),
            header_fields_unchanged=hdr1,
            header_consistency=dict(total_edges_matches_list=(hdr1['total_edges'] == m),
                                    average_degree_is_edges_over_nodes=(abs(hdr1['average_degree'] - m / n) < 1e-9),
                                    graph_density_is_edges_over_n_n_minus_1=(abs(hdr1['graph_density'] - m / (n * (n - 1))) < 1e-15)),
            policy='Historical results remain attributed to the ORIGINAL graph (7aa6db46...). This derivative is not wired into any pipeline.')
json.dump(prov, open(PROV, 'w', encoding='utf-8'), indent=1)
print(json.dumps(prov, indent=1))
