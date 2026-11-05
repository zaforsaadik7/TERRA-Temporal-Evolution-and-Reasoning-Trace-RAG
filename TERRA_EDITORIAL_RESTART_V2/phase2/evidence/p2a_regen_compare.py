"""Phase 2A (read-only w.r.t. user data): compare macros produced by a SANDBOXED replay of
scripts/generate_stats_v2.py (inputs: staged canonical v2 eval, benchmark, rubric v2, raw baselines, issue6 cache,
issue42 calibration artifact; outputs written only to /tmp) against the FROZEN working generated_stats.tex.
Replay patches (documented): ablation input replaced by a stub (752 MB file not transferable) -> Ablation* macros
EXCLUDED from verdicts; pilot 35x5 raw (219 MB, transfer timeout) not loaded -> pilot parity asserts skipped.
Verdicts: MATCH / DIFF / FROZEN_ONLY(not produced by v2 head) / REPLAY_ONLY."""
import re, sys, csv, json
FROZEN, REPLAY, OUT = sys.argv[1:4]
def parse(path):
    s = open(path, encoding='utf-8').read(); d = {}; i = 0
    for m in re.finditer(r'\\newcommand\{\\([A-Za-z]+)\}', s):
        j = m.end()
        if j >= len(s) or s[j] != '{': continue
        depth = 0; k = j
        while k < len(s):
            if s[k] == '{': depth += 1
            elif s[k] == '}':
                depth -= 1
                if depth == 0: break
            k += 1
        d.setdefault(m.group(1), s[j + 1:k])
    return d, s
F, fs = parse(FROZEN); Rp, rs = parse(REPLAY)
split = fs.index('% --- TEMPORAL PARAMETRIC LEAKAGE PROBE METRICS (TABLE XII) ---')
head_names = set(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}', fs[:split]))
rows = []
for n in sorted(set(F) | set(Rp)):
    zone = 'HEAD(v2-generated)' if n in head_names else 'DOWNSTREAM(preserved)'
    if n.startswith('Ablation'): v = 'EXCLUDED_ABLATION_STUB'
    elif n in F and n in Rp: v = 'MATCH' if F[n].strip() == Rp[n].strip() else 'DIFF'
    elif n in F: v = 'FROZEN_ONLY'
    else: v = 'REPLAY_ONLY'
    rows.append(dict(macro=n, zone=zone, verdict=v, frozen=F.get(n, ''), replay=Rp.get(n, '')))
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
import collections
print(collections.Counter((r['zone'], r['verdict']) for r in rows))
for r in rows:
    if r['verdict'] == 'DIFF': print('DIFF', r['macro'], '| frozen:', r['frozen'][:70], '| replay:', r['replay'][:70])
