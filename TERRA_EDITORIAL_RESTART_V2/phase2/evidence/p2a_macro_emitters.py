"""Phase 2A (read-only): for every macro USED in the rendered sources, locate the script(s) that emit its
\\newcommand, and classify how the value is produced.
Emitter search: every .py under scripts/, scratch/, Paper/scripts/, TERRA_EDITORIAL_RESTART_V2/working/src/scripts/
and the repo root; a line 'emits' a macro if it contains 'newcommand' and the macro name followed by '}'.
Value mode (per emitting line):
  LITERAL_IN_SCRIPT  - the frozen value string appears verbatim on the emitting line (hand-typed in code)
  COMPUTED           - the emitting line interpolates an expression ({...} / % / format) and does not contain the value
Also marks whether the only emitters are 'generate_stats_v2.py' (canonical v2 generator).
Output: CSV macro -> emitters, modes, and uses."""
import csv, re, os, sys, glob, json, collections
ROOT, BASE, OUT = sys.argv[1:4]
rows = list(csv.DictReader(open(BASE, encoding='utf-8')))
used = [r for r in rows if int(r['total_uses']) > 0]
pyfiles = []
for pat in ['scripts/*.py', 'scratch/*.py', 'Paper/scripts/*.py', 'TERRA_EDITORIAL_RESTART_V2/working/src/scripts/*.py', '*.py', 'baselines/*.py']:
    pyfiles += glob.glob(os.path.join(ROOT, pat))
lines = []
for f in sorted(set(pyfiles)):
    try: txt = open(f, encoding='utf-8', errors='replace').read().split('\n')
    except Exception: continue
    for i, l in enumerate(txt):
        if 'newcommand' in l: lines.append((os.path.relpath(f, ROOT), i + 1, l))
out = []
for r in used:
    m = r['macro']; pat = re.compile(r'\\\\?' + re.escape(m) + r'\}')
    em = [(f, n, l) for f, n, l in lines if pat.search(l)]
    val = r['frozen_value'].strip()
    modes = []
    for f, n, l in em:
        vcore = val.replace('\\%', '%')
        lit = (val and (val in l or vcore in l.replace('\\\\%', '%').replace('\\%', '%')))
        modes.append('LITERAL_IN_SCRIPT' if lit else 'COMPUTED')
    files = sorted({f for f, _, _ in em})
    out.append(dict(macro=m, frozen_value=val, defined_in=r['defined_in'], uses=r['total_uses'], uses_by_file=r['uses_by_file'],
                    n_emitters=len(files), emitters=';'.join(files)[:600],
                    v2_generator_emits=any(f.endswith('generate_stats_v2.py') for f in files),
                    any_literal=('LITERAL_IN_SCRIPT' in modes), any_computed=('COMPUTED' in modes),
                    literal_emitters=';'.join(sorted({f for (f, _, _), md in zip(em, modes) if md == 'LITERAL_IN_SCRIPT'}))[:400]))
with open(OUT, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
c = collections.Counter()
for o in out:
    k = 'NO_EMITTER_FOUND' if o['n_emitters'] == 0 else ('V2_GENERATOR' if o['v2_generator_emits'] else 'OTHER_SCRIPT')
    k += '/' + ('LITERAL' if o['any_literal'] and not o['any_computed'] else 'COMPUTED' if o['any_computed'] and not o['any_literal'] else 'MIXED' if o['n_emitters'] else '-')
    c[k] += 1
print('python files scanned', len(set(pyfiles)), 'newcommand lines', len(lines), 'used macros', len(used))
for k, v in sorted(c.items()): print(k, v)
