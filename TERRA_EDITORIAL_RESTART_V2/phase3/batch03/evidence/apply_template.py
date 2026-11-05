"""Phase 3 Batch 03 (PROPOSAL): Table XXI Panel A and section VII-M regenerated from canonical v2 (R13, with the R32 fast-path and R31 pre-retrieval statements in that section).
Byte-preserving and fail-closed (see ERRATUM_01_line_endings.md). Usage: python -X utf8 p3b3_apply.py <src_dir> <phase3_corrections_b3.tex> <diff_out> [--check-only]
Pre-state = Batch 02 rev1 post-state. Writes nothing unless every pre-hash matches and every edit occurs exactly once."""
import difflib, hashlib, os, shutil, sys
SRC, CORR, DIFF = sys.argv[1:4]
CHECK = '--check-only' in sys.argv
sha = lambda b: hashlib.sha256(b).hexdigest()
PRE = {'main.tex': 'af093e96eeaf6fe76cd7fc1e0838b7bbf88ae8910ed83bd35ce86862bde8aa55',
       'tables/table_computational_budget.tex': '4960a2eb32696d87@@'}
EDITS = {'main.tex': @@MAIN_EDITS@@,
         'tables/table_computational_budget.tex': @@TAB_EDITS@@}
out, diff = {}, []
for f, eds in EDITS.items():
    raw = open(os.path.join(SRC, f), 'rb').read()
    pre = PRE[f].rstrip('@')
    if not sha(raw).startswith(pre): sys.exit(f'FAIL-CLOSED: pre-hash mismatch for {f}')
    txt = raw.decode('utf-8')
    for a, b in eds:
        cands = [(a, b)] + ([(a.replace('\n', '\r\n'), b.replace('\n', '\r\n'))] if '\n' in a else [])
        hits = [(x, y) for x, y in cands if txt.count(x) == 1]
        if len(hits) != 1: sys.exit(f'FAIL-CLOSED: {f}: edit not matched exactly once: {a[:80]!r}')
        txt = txt.replace(*hits[0])
    out[f] = txt.encode('utf-8')
    diff += difflib.unified_diff(raw.decode('utf-8').splitlines(True), txt.splitlines(True), f'a/{f}', f'b/{f}')
mt, tt = out['main.tex'].decode('utf-8'), out['tables/table_computational_budget.tex'].decode('utf-8')
for bad in ('generator latency collapses to', 'C069', 'one cent', 'Isolated Graph Retrieval', 'bypasses retrieval entirely', 'reconciling with reported', 'Decoupled Wall-Clock', 'Logged Stage', 'TerraCatCPreFilterExceedingHaltedCount', 'TerraCatCFailNliHaltedCount', 'indispensable primary safety firewall', 'before retrieval. The remaining', 'operational responsibility of the downstream'):
    assert bad not in mt, f'post-condition: {bad!r} still in main.tex'
for bad in ('C069', 'terra_baselines_eval_raw', '268,682', 'Decoupled Component', 'TERRA Operational Setting', 'Logged Stage'):
    assert bad not in tt, f'post-condition: {bad!r} still in the table'
for f, b in out.items():
    before = open(os.path.join(SRC, f), 'rb').read(); c0, c1 = before.count(b'\r\n'), b.count(b'\r\n')
    print('%s: CRLF %d -> %d, bare LF %d -> %d, sha256 %s' % (f, c0, c1, before.count(b'\n') - c0, b.count(b'\n') - c1, sha(b)))
diff += difflib.unified_diff([], open(CORR, encoding='utf-8').read().splitlines(True), '/dev/null', 'b/phase3_corrections_b3.tex')
open(DIFF, 'w', encoding='utf-8', newline='').writelines(diff)
if CHECK: print('CHECK-ONLY: nothing written'); sys.exit(0)
for f, b in out.items(): open(os.path.join(SRC, f), 'wb').write(b)
shutil.copyfile(CORR, os.path.join(SRC, 'phase3_corrections_b3.tex'))
print('WRITTEN')
