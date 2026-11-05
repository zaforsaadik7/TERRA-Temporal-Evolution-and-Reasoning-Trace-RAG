"""Read failed disposable SQLite metadata only; no Chroma/model imports."""
import hashlib,json,sqlite3
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path('F:/TERRA -Copy')
packet=json.loads((R/'reports/profile_user_b001_freeze_20261023_01/execution_packet.json').read_bytes())
db=Path(packet['integrity']['disposable'])/'chroma.sqlite3'
assert db.is_relative_to(R/'reports/authentic_smoke_profile_candidate_20261023_01')
for p in (db,*db.parents):
    assert not (getattr(p.lstat(),'st_file_attributes',0)&0x400)
def ident():
    with db.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return {'path':str(db),'size_bytes':db.stat().st_size,'sha256':h}
before=ident()
# Immutable, read-only connection to the already-used disposable, not the source store.
connection=sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True)
try:
    connection.execute('PRAGMA query_only=ON')
    schema=connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='collections'").fetchone()
    columns=[r[1] for r in connection.execute('PRAGMA table_info(collections)')]
    assert 'name' in columns
    selected=[c for c in ('name','dimension','config_json_str','schema_str') if c in columns]
    row=connection.execute('SELECT '+','.join(selected)+' FROM collections WHERE name=?',('thinking_traces',)).fetchone()
    assert row is not None
    data=dict(zip(selected,row))
finally:connection.close()
after=ident()
assert before==after
result={'scope':'USED_DISPOSABLE_SQLITE_METADATA_ONLY','database_unchanged':True,'before':before,'after':after,'collections_schema':schema[0],'collection_metadata':data,'chroma_imported':False,'model_operations':False}
with (O/'DISPOSABLE_COLLECTION_METADATA.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result))
