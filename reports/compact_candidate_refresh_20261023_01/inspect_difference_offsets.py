import hashlib
import json
from pathlib import Path

root = Path('F:/TERRA -Copy/reports/sqlite_drift_diagnosis_20261023_01')
report = json.loads((root / 'comparison.json').read_text())
differences = []
with (root / 'accepted.sqlite3').open('rb') as a, (root / 'current.sqlite3').open('rb') as b:
    for block in report['binary_difference']['changed_blocks']:
        offset = block['offset']
        a.seek(offset)
        b.seek(offset)
        for i,(x,y) in enumerate(zip(a.read(4096), b.read(4096))):
            if x != y:
                differences.append({'offset': offset+i, 'accepted_byte': x, 'current_byte': y})
page_size = report['metadata']['accepted']['page_size']
pages = sorted({d['offset']//page_size+1 for d in differences})
result = {'byte_differences': differences, 'page_size': page_size, 'affected_pages': pages,
          'schema_objects_rooted_on_affected_pages': [r[:4] for r in report['metadata']['accepted']['schema'] if r[3] in pages],
          'caveat': 'Root-page association does not establish which logical records changed; no user-table rows queried.'}
with (root / 'difference_offsets.json').open('x') as f:
    json.dump(result, f, indent=2)
print(json.dumps(result))
