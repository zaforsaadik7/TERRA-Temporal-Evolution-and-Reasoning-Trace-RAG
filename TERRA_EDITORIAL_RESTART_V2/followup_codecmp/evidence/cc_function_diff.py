"""Read-only: per top-level function, compare source across pinned code versions (identical / changed /
absent) and write unified diffs of changed functions."""
import ast, sys, difflib, hashlib, json
files = sys.argv[1:-1]; OUT = sys.argv[-1]
def fns(p):
    s = open(p, encoding='utf-8').read(); t = ast.parse(s)
    return {n.name: ast.get_source_segment(s, n) for n in t.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}, hashlib.sha256(s.encode()).hexdigest()
V = {f: fns(f) for f in files}
names = sorted(set().union(*[set(v[0]) for v in V.values()]))
rep = {'files': {f: V[f][1] for f in files}, 'functions': {}}
diffs = []
for n in names:
    srcs = [V[f][0].get(n) for f in files]
    row = {}
    for i in range(1, len(files)):
        a, b = srcs[i-1], srcs[i]
        k = f'{files[i-1].split("/")[-1]} -> {files[i].split("/")[-1]}'
        if a is None and b is None: row[k] = 'absent'
        elif a is None: row[k] = 'added'
        elif b is None: row[k] = 'removed'
        elif a == b: row[k] = 'identical'
        else:
            row[k] = 'changed'
            diffs.append(f'\n######## {n}: {k}\n' + ''.join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), n=1)))
    rep['functions'][n] = row
json.dump(rep, open(OUT + '.json', 'w'), indent=1); open(OUT + '.diff', 'w').write(''.join(diffs))
for n, row in rep['functions'].items(): print(f'{n:40s}', ' | '.join(row.values()))
