"""Read-only immutable SQLite comparison of isolated COPIES, never original stores."""
import hashlib
import json
from pathlib import Path
import sqlite3

BASE = Path(__file__).resolve().parent
paths = {'older_snapshot': BASE/'older_snapshot.sqlite3', 'current_copy': BASE/'current_store/chroma.sqlite3'}
report = {'baseline_limit': 'Older preserved snapshot is NOT the exact a184ae23 pre-incident baseline.', 'databases': {}}
def encode(v):
    if isinstance(v, bytes):
        return ['blob', len(v), hashlib.sha256(v).hexdigest()]
    return [type(v).__name__, v]
for label, path in paths.items():
    conn = sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1', uri=True)
    try:
        conn.execute('PRAGMA query_only=ON')
        schema = conn.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name,tbl_name").fetchall()
        info = {'schema': schema, 'tables': {}, 'quick_check': conn.execute('PRAGMA quick_check').fetchall()}
        for name, in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            quoted = '"'+name.replace('"','""')+'"'
            row_hashes = []
            for row in conn.execute('SELECT * FROM '+quoted):
                payload = json.dumps([encode(v) for v in row], ensure_ascii=False, separators=(',',':')).encode()
                row_hashes.append(hashlib.sha256(payload).digest())
            aggregate = hashlib.sha256()
            for h in sorted(row_hashes):
                aggregate.update(h)
            info['tables'][name] = {'rows': len(row_hashes), 'content_multiset_sha256': aggregate.hexdigest()}
        report['databases'][label] = info
    finally:
        conn.close()
old = report['databases']['older_snapshot']; new = report['databases']['current_copy']
report['schema_equal'] = old['schema']==new['schema']
report['changed_tables'] = {name: {'older': old['tables'].get(name), 'current': new['tables'].get(name)}
    for name in sorted(old['tables'].keys() | new['tables'].keys()) if old['tables'].get(name)!=new['tables'].get(name)}
with paths['older_snapshot'].open('rb') as a, paths['current_copy'].open('rb') as b:
    ah=a.read(100); bh=b.read(100)
    report['header_changed_offsets']=[i for i in range(min(len(ah),len(bh))) if ah[i]!=bh[i]]
    size=int.from_bytes(ah[16:18],'big'); size=65536 if size==1 else size
    a.seek(0); b.seek(0); changed=[]; page=0
    while True:
        aa=a.read(size); bb=b.read(size)
        if not aa and not bb: break
        page+=1
        if aa!=bb: changed.append(page)
    report['page_size']=size; report['changed_page_count']=len(changed); report['changed_pages']=changed
with (BASE/'semantic_comparison.json').open('x',encoding='utf-8') as out:
    json.dump(report,out,indent=2)
print('SCHEMA_EQUAL',report['schema_equal'])
print('CHANGED_TABLES',report['changed_tables'])
print('CHANGED_PAGES',report['changed_page_count'])
print('HEADER_CHANGED_OFFSETS',report['header_changed_offsets'])
