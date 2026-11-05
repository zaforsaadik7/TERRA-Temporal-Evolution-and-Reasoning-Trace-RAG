"""Authorized byte comparison and SQLite metadata only, on fresh copies."""
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

ROOT = Path('F:/TERRA -Copy')
OUT = ROOT / 'reports/sqlite_drift_diagnosis_20261023_01'
SOURCES = {
    'accepted': ROOT / 'reports/task3_authorized_inventory_20261022_01/store_copy/chroma.sqlite3',
    'current': ROOT / 'dataset_20k_cap/vector_db_20k/chroma.sqlite3',
}
EXPECTED = {
    'accepted': 'c7fc28f24403303b384f73f3eac349629661a430aeee3c05e899c8d5e27b475d',
    'current': '6a582ce87816aba771db2a54b91853ecf8ec818981120d67682c39730588189c',
}

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def metadata(path):
    con = sqlite3.connect(path.as_uri() + '?mode=ro&immutable=1', uri=True)
    try:
        con.execute('PRAGMA query_only=ON')
        result = {}
        for name in ('page_size', 'page_count', 'freelist_count', 'schema_version', 'user_version', 'application_id', 'encoding', 'auto_vacuum'):
            result[name] = con.execute('PRAGMA ' + name).fetchone()[0]
        result['schema'] = con.execute('SELECT type,name,tbl_name,rootpage,sql FROM sqlite_master ORDER BY type,name').fetchall()
        return result
    finally:
        con.close()

OUT.mkdir(exist_ok=False)
report = {'scope': 'binary comparison and metadata only; no user table rows or embeddings read', 'sqlite_library': sqlite3.sqlite_version}
try:
    before = {k: digest(p) for k,p in SOURCES.items()}
    assert before == EXPECTED, 'Source identity changed; stop'
    copies = {}
    for key,path in SOURCES.items():
        target = OUT / (key + '.sqlite3')
        with path.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst, 1024*1024)
        assert digest(target) == EXPECTED[key]
        copies[key] = target
    report['source_before'] = before
    report['metadata'] = {k: metadata(p) for k,p in copies.items()}
    blocks = []
    changed_bytes = 0
    with copies['accepted'].open('rb') as a, copies['current'].open('rb') as b:
        offset = 0
        while True:
            x,y = a.read(4096),b.read(4096)
            if not x and not y:
                break
            if x != y:
                count = sum(v != w for v,w in zip(x,y)) + abs(len(x)-len(y))
                blocks.append({'offset': offset, 'different_bytes': count})
                changed_bytes += count
            offset += 4096
    report['binary_difference'] = {'block_size': 4096, 'changed_blocks': blocks, 'different_bytes': changed_bytes}
    report['source_after'] = {k: digest(p) for k,p in SOURCES.items()}
    report['copies_after'] = {k: digest(p) for k,p in copies.items()}
    assert report['source_after'] == before and report['copies_after'] == before
    report['status'] = 'COMPARISON_COMPLETE_NO_BASELINE_ACCEPTANCE'
finally:
    with (OUT / 'comparison.json').open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
print(json.dumps({'status': report['status'], 'changed_blocks': len(blocks), 'different_bytes': changed_bytes, 'metadata_equal': report['metadata']['accepted'] == report['metadata']['current']}))
