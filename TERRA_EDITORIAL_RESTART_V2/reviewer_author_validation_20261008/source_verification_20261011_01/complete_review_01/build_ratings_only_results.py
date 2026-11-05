"""Read-only original XLSX analysis. Writes only a fresh ratings-only output folder."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import openpyxl

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ORIGINALS = BASE / 'issued_20261009_01' / 'COMPLETED'
OUT = HERE / 'ratings_only_results_20261012_01'
EXPECTED = {1: '34735965b0636a26570b3053baebfd8b58532888f684e2ee381754c8bdf6832b',
            2: 'ce3869f8b0930b6a28df73b5deabffc5e1e7da9c4b2df5a649bec27f838c598b'}
FIELDS = ['response_status', 'source_correctness', 'temporal_leakage',
          'responsiveness', 'citation_authenticity', 'refusal_justification']
COLS = dict(zip('GHIJKL', FIELDS))
ALLOWED = {
 'response_status': {'substantive answer', 'refusal', 'mixed refusal/substantive answer'},
 'source_correctness': {'supported', 'contradicted', 'uncertain', 'not applicable'},
 'temporal_leakage': {'yes', 'no', 'uncertain', 'not applicable'},
 'responsiveness': {'addresses requested issue', 'partly addresses', 'does not address', 'uncertain'},
 'citation_authenticity': {'authentic and supports proposition', 'authentic but misapplied', 'cannot locate', 'no citation/not applicable'},
 'refusal_justification': {'justified', 'potentially unnecessary', 'uncertain', 'not applicable'},
}

def digest(p):
 return hashlib.sha256(p.read_bytes()).hexdigest()

def write_csv(path, rows, names):
 with path.open('x', encoding='utf-8-sig', newline='') as f:
  w = csv.DictWriter(f, fieldnames=names); w.writeheader(); w.writerows(rows)

raw, cleaned, norms = [], [], []
for author in (1, 2):
 p = ORIGINALS / f'ASSESSMENT_AUTHOR_{author}_COMPLETED.xlsx'
 if digest(p) != EXPECTED[author]: raise ValueError(f'Original hash drift: {author}')
 s = openpyxl.load_workbook(p, read_only=True, data_only=True)['Assessments']
 found = []
 for row_number, values in enumerate(s.iter_rows(min_row=2, values_only=True), 2):
  if values[0] is None:
   if any(v is not None for v in values[:12]): raise ValueError('Nonblank assessment with no ID')
   continue
  r = {'author': author, 'assessment_id': values[0], 'original_row': row_number,
       'cluster_group': values[1], 'task_classification': values[2], 'cutoff_label': values[3]}
  r.update(dict(zip(FIELDS, values[6:12])))
  raw.append(r); found.append(values[0]); c = dict(r)
  for field in FIELDS:
   value = r[field]
   if not isinstance(value, str): raise ValueError(f'Missing rating: {r["assessment_id"]} {field}')
   normalized = value.strip()
   if field == 'citation_authenticity' and normalized == 'no citation': normalized = 'no citation/not applicable'
   if normalized not in ALLOWED[field]: raise ValueError(f'Unexpected label: {r["assessment_id"]} {field}: {value!r}')
   if normalized != value:
    norms.append({'assessment_id': r['assessment_id'], 'field': field, 'original_value': value, 'normalized_value': normalized})
   c[field] = normalized
  cleaned.append(c)
 if len(found) != 76 or len(set(found)) != 76 or set(found) != {f'AUTH{author}-ITEM-{i:03}' for i in range(1, 77)}:
  raise ValueError('Assessment inventory mismatch')

revised = [dict(r) for r in cleaned]
by_id = {r['assessment_id']: r for r in revised}
with (HERE / 'CONFIRMED_RATING_AMENDMENTS_20261012.csv').open(encoding='utf-8-sig', newline='') as f:
 amendments = list(csv.DictReader(f))
if len(amendments) != 14: raise ValueError('Expected 14 approved amendments')
seen = set()
for a in amendments:
 key = (a['assessment_id'], a['cell'])
 if key in seen: raise ValueError('Duplicate amendment')
 seen.add(key); row = by_id[a['assessment_id']]; field = COLS[a['cell'][0]]
 if int(a['cell'][1:]) != row['original_row'] or row[field] != a['original_value']:
  raise ValueError('Amendment precondition mismatch')
 if a['final_value'] not in ALLOWED[field]: raise ValueError('Invalid final label')
 row[field] = a['final_value']
changed = sum(x[f] != y[f] for x, y in zip(cleaned, revised) for f in FIELDS)
if changed != 14: raise ValueError('Changed-cell count mismatch')

summary = []
for version, records in [('original_normalized', cleaned), ('reconciled', revised)]:
 for author in (1, 2):
  subset = [r for r in records if r['author'] == author]
  for field in FIELDS:
   counts = Counter(r[field] for r in subset)
   for label, count in sorted(counts.items()):
    summary.append({'version': version, 'author': author, 'field': field, 'label': label,
                    'count': count, 'denominator': len(subset), 'percent': round(100*count/len(subset), 4)})
  answered = [r for r in subset if r['response_status'] != 'refusal']
  supported = sum(r['source_correctness'] == 'supported' for r in answered)
  contradicted = sum(r['source_correctness'] == 'contradicted' for r in answered)
  for label, count, denominator in [('non_refusal_coverage', len(answered), len(subset)),
                                    ('supported_answer_yield', supported, len(subset)),
                                    ('contradicted_among_non_refusals', contradicted, len(answered))]:
   summary.append({'version': version, 'author': author, 'field': 'descriptive_proxy', 'label': label,
                   'count': count, 'denominator': denominator,
                   'percent': round(100*count/denominator, 4) if denominator else None})

for author in (1, 2):
 if digest(ORIGINALS / f'ASSESSMENT_AUTHOR_{author}_COMPLETED.xlsx') != EXPECTED[author]: raise ValueError('Post-read hash drift')
OUT.mkdir(exist_ok=False)
names = list(raw[0])
write_csv(OUT / 'original_ratings.csv', raw, names)
write_csv(OUT / 'original_normalized_ratings.csv', cleaned, names)
write_csv(OUT / 'reconciled_ratings.csv', revised, names)
write_csv(OUT / 'normalization_log.csv', norms, ['assessment_id','field','original_value','normalized_value'])
write_csv(OUT / 'descriptive_results.csv', summary, ['version','author','field','label','count','denominator','percent'])
record = {'status': 'PASS_RATINGS_ONLY', 'assessment_rows': 152, 'confirmed_rating_changes': changed,
          'format_normalizations': len(norms), 'original_hashes': EXPECTED,
          'quotes_answers_rationales_exported': False, 'pipeline_results_or_population_inference': False,
          'output_hashes': {p.name: digest(p) for p in OUT.glob('*.csv')}}
with (OUT / 'verification.json').open('x', encoding='utf-8') as f: json.dump(record,f,indent=2)
print(json.dumps(record, indent=2))
print(json.dumps([r for r in summary if r['field'] == 'descriptive_proxy'], indent=2))
