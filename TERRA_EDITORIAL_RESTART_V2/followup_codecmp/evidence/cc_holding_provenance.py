"""Read-only: do the [Holding] snippets serialised in deployed TERRA contexts equal the node
`substantive_holding` field of a given graph file? (tests whether the graph file's node payload is the
run-time payload; edge structure is tested separately by cc_replay_traversal.py)."""
import json, re, sys, hashlib
EVAL = sys.argv[1]; GRAPHS = sys.argv[2:]
d = json.load(open(EVAL)); t = [r for r in d if r['pipeline'] == '5_Full_TERRA']
pat = re.compile(r"'[^']*' \(Case ID: (\d+_\d{4}-\d{2}), Date: [^)]*\)[^\n]*?\. \[Holding\]: ([^\n]*)")
pat2 = re.compile(r"earlier (?:case|precedent) '[^']*' \(Case ID: (\d+_\d{4}-\d{2}), Date: [^)]*\)\. \[Holding\]: ([^\n]*)")
samples = []
for r in t:
    c = r.get('context_full') or ''
    for m in list(pat.finditer(c)) + list(pat2.finditer(c)): samples.append((m.group(1), m.group(2).strip()))
print('holding snippets sampled:', len(samples))
for G in GRAPHS:
    g = json.load(open(G)); N = g['nodes']; eq = 0; pref = 0
    for nid, h in samples:
        sh = (N.get(nid, {}).get('substantive_holding') or '').strip()
        if sh and (h == sh[:250].strip() or h == sh[:600].strip()): eq += 1
        elif sh and h[:60] == sh[:60]: pref += 1
    print(G.split('/')[-1], hashlib.sha256(open(G, 'rb').read()).hexdigest()[:12], f'exact={eq} prefix60={pref} of {len(samples)}')
