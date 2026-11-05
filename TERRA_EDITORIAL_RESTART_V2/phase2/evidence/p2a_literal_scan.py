"""Phase 2A: inventory of hard-coded numeric literals in the manuscript sources (R26).

Read-only. Usage: python -X utf8 p2a_literal_scan.py <repo_root> <number_provenance_ledger.csv> <out_csv>
Scans working/src/main.tex and working/src/tables/*.tex and figure_*.tex (comments stripped). Each numeric token
that is not part of a macro name, label/ref/cite key, or LaTeX dimension/layout argument is classified:
  YEAR            4-digit 1700-2039 (case years, dates)
  CITATION        reporter-style citation or CAP id (e.g. 347 U.S. 483, 347_0483-01)
  STRUCTURAL      section/table/figure/equation/hop-count style numbers, list markers, 1-10 small integers in prose
  RESULT_LIKE     everything else (percentages, decimals, counts > 10, ratios)
For RESULT_LIKE tokens, 'value_match' records whether the same numeric value (at printed precision) is the
leading number of a used macro whose ledger status is REPRODUCED/REPRODUCED_METHOD/TRACED ('VERIFIED_MACRO'),
of any other used macro ('OTHER_MACRO'), or of none ('NONE'). A value match is a candidate link only.
"""
import csv, glob, os, re, sys
from collections import Counter

ROOT, LEDGER, OUT = sys.argv[1:4]
SRC = os.path.join(ROOT, 'TERRA_EDITORIAL_RESTART_V2', 'working', 'src')
files = [os.path.join(SRC, 'main.tex')] + sorted(glob.glob(os.path.join(SRC, 'tables', '*.tex'))) + sorted(glob.glob(os.path.join(SRC, 'figure_*.tex')))

led = list(csv.DictReader(open(LEDGER, encoding='utf-8')))


def lead(v):
    s = v.replace('{,}', '').replace('\\,', '')
    s = re.sub(r'(?<=\d),(?=\d{3})', '', s)
    m = re.search(r'\d+(?:\.\d+)?', s)
    return m.group(0) if m else None


ver, oth = set(), set()
for r in led:
    x = lead(r['frozen_value'])
    if x is None:
        continue
    (ver if r['verification_status'] in ('REPRODUCED', 'REPRODUCED_METHOD', 'TRACED') else oth).add(x)

SKIP_ARGS = re.compile(r'\\(definecolor|colorlet|color|texttt|tikzset|draw|node|fill|path|label|ref|eqref|cite\w*|autoref|cref|Cref|url|href|includegraphics|input|include|begin|end|newcommand|renewcommand|setlength|addtolength|vspace\*?|hspace\*?|resizebox|scalebox|multicolumn|multirow|cline|cmidrule|arraystretch|fontsize|rule|raisebox|parbox|makebox|columnwidth|linewidth|textwidth)\b\s*(\[[^\]]*\])?\s*(\{[^{}]*\}\s*){0,4}')
DIM = re.compile(r'-?\d*\.?\d+\s*(pt|em|ex|cm|mm|in|bp|sp|\\(line|text|column)width|\\baselineskip)')
CITE = re.compile(r'\b\d{1,3}\s+(U\.\s?S\.|S\.\s?Ct\.|L\.\s?Ed\.(\s?2d)?|F\.(2d|3d|\s?Supp\.)|How\.|Wall\.|Pet\.|Dall\.|Cranch|Wheat\.)\s+\d{1,4}|\b\d{1,3}_\d{3,4}-\d{2}\b')
NUM = re.compile(r'(?<![\w\\])[+-−]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w\\])[+-]?\d+(?:\.\d+)?')

rows = []
for fp in files:
    rel = os.path.relpath(fp, SRC)
    for ln, raw in enumerate(open(fp, encoding='utf-8'), 1):
        line = re.sub(r'(?<!\\)%.*', '', raw)
        if not line.strip():
            continue
        spans = []
        for rx in (SKIP_ARGS, DIM):
            spans += [(m.start(), m.end(), 'LAYOUT') for m in rx.finditer(line)]
        spans += [(m.start(), m.end(), 'CITATION') for m in CITE.finditer(line)]
        for m in NUM.finditer(line):
            a, b = m.start(), m.end()
            tok = m.group(0)
            # part of a macro name like \TerraCatA... never contains digits, but guard for \x123
            cls = None
            for s, e, t in spans:
                if s <= a < e:
                    cls = t
                    break
            if cls == 'LAYOUT':
                continue
            val = tok.replace(',', '').lstrip('+-−')
            ctx = line[max(0, a - 50):b + 40].replace('\n', ' ').strip()
            if cls is None:
                v = float(val)
                if re.fullmatch(r'1[7-9]\d\d|20[0-3]\d', val):
                    cls = 'YEAR'
                elif re.search(r'(Section|Sec\.|Table|Fig\.|Figure|Eq\.|Appendix|Phase|Issue|Amendment|Step|Tier|Layer|Panel|Pillar|R|#|~)\W{0,3}$', line[max(0, a - 12):a]) or (v <= 10 and '.' not in val):
                    cls = 'STRUCTURAL'
                else:
                    cls = 'RESULT_LIKE'
            vm = ''
            if cls == 'RESULT_LIKE':
                vm = 'VERIFIED_MACRO' if val in ver else ('OTHER_MACRO' if val in oth else 'NONE')
            rows.append(dict(file=rel, line=ln, token=tok, class_=cls, value_match=vm, status='UNVERIFIED' if cls == 'RESULT_LIKE' else 'N/A', context=ctx))
with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['file', 'line', 'token', 'class_', 'value_match', 'status', 'context']); w.writeheader(); w.writerows(rows)
print(len(rows), Counter(r['class_'] for r in rows))
print('RESULT_LIKE by value_match', Counter(r['value_match'] for r in rows if r['class_'] == 'RESULT_LIKE'))
print('RESULT_LIKE by file', Counter(r['file'] for r in rows if r['class_'] == 'RESULT_LIKE').most_common(12))
