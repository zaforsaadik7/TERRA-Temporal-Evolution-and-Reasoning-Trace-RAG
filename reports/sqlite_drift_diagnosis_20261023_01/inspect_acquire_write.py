import hashlib
import json
import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parent
prior = json.loads((root / 'comparison.json').read_text())
result = {'scope': 'acquire_write rows only on isolated copies'}
for key in ('accepted', 'current'):
    path = root / (key + '.sqlite3')
    def digest():
        with path.open('rb') as f:
            return hashlib.file_digest(f, 'sha256').hexdigest()
    before = digest()
    assert before == prior['copies_after'][key]
    con = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        con.execute('PRAGMA query_only=ON')
        rows = con.execute('SELECT id, lock_status FROM acquire_write ORDER BY id LIMIT 1001').fetchall()
        assert len(rows) <= 1000, 'Unexpected row count; stop'
    finally:
        con.close()
    after = digest()
    assert before == after
    result[key] = {'rows': rows, 'sha256_before': before, 'sha256_after': after}
with (root / 'acquire_write_comparison.json').open('x') as f:
    json.dump(result, f, indent=2)
print(json.dumps(result))
