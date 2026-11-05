"""Phase 3 Batch 01: byte-preserving application of the APPROVED rev1 full variant (B1-1..B1-8).
Takes the 10 edits verbatim from p3b1_apply_rev1.py (ast), preserves each line's own ending, fails closed.
Usage: python -X utf8 p3b1_apply_eolsafe.py <working_src_dir> <rev1_apply_script> <phase3_corrections.tex> [--check-only]
"""
import ast, hashlib, os, shutil, sys

SRC, REV1, CORR = sys.argv[1:4]
CHECK = '--check-only' in sys.argv
PRE = {'main.tex': '31db54c4b2771d34e1b3b59168fcdebea9b3b5e8198f9268f21298a61fc3fec4',
       'tables/table_refusal_breakdown.tex': 'b9bbc21b69783eb07eba798dde100b7098592c081f3b6a4faf3d59441c80bdcb',
       'figure_3_safety_rejection.tex': '8dc435e7a77d242adb8b3890c67b807460584a7e934355ffd198b7a74694b2bb'}
CORR_SHA = '487fdb9d9439f786d05cf24379108fcf4457827c4d7c57af001438c4543b40da'
sha = lambda b: hashlib.sha256(b).hexdigest()

tree = ast.parse(open(REV1, encoding='utf-8').read())
lit = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ('EDITS', 'OPTIONAL'):
        lit[node.targets[0].id] = ast.literal_eval(node.value)
edits = {f: list(v) for f, v in lit['EDITS'].items()}
for f, v in lit['OPTIONAL'].items():
    edits.setdefault(f, []).extend(v)
assert sum(len(v) for v in edits.values()) == 10, 'expected the 10 approved edits'

if sha(open(CORR, 'rb').read()) != CORR_SHA:
    sys.exit('FAIL-CLOSED: phase3_corrections.tex hash mismatch')
out = {}
for f, eds in edits.items():
    p = os.path.join(SRC, f)
    raw = open(p, 'rb').read()
    if sha(raw) != PRE[f]:
        sys.exit(f'FAIL-CLOSED: pre-hash mismatch for {f}')
    txt = raw.decode('utf-8')
    for a, b in eds:
        cands = [(a, b)]
        if '\n' in a:
            cands.append((a.replace('\n', '\r\n'), b.replace('\n', '\r\n')))
        hits = [(x, y) for x, y in cands if txt.count(x) == 1]
        if len(hits) != 1:
            sys.exit(f'FAIL-CLOSED: {f}: edit not matched exactly once: {a[:70]!r}')
        txt = txt.replace(*hits[0])
    out[f] = txt.encode('utf-8')
mt = out['main.tex'].decode('utf-8')
assert 'Rank 11' not in mt and '0.0629' not in mt and '10/75' not in mt and '\\input{phase3_corrections}' in mt
for f, b in out.items():
    before = open(os.path.join(SRC, f), 'rb').read()
    CR, LF = b'\r\n', b'\n'
    c0, c1 = before.count(CR), b.count(CR)
    l0, l1 = before.count(LF) - c0, b.count(LF) - c1
    print('%s: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (f, c0, c1, l0, l1, sha(b)))
if CHECK:
    print('CHECK-ONLY: all pre-hashes and 10 edits verified; nothing written'); sys.exit(0)
for f, b in out.items():
    open(os.path.join(SRC, f), 'wb').write(b)
shutil.copyfile(CORR, os.path.join(SRC, 'phase3_corrections.tex'))
print('WRITTEN: 3 edited files + phase3_corrections.tex')
