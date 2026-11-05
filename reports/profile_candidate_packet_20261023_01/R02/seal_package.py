"""Hash proposal artifacts and preserved evidence only."""
import hashlib
import json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def ident(p):
    raw=p.read_bytes()
    return {'path':str(p),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
for folder in ('semantic_b001_postrun_20261023_01','diagnostics_b001_postrun_20261023_01'):
    for row in json.loads((R/'reports'/folder/'evidence_manifest.json').read_bytes()):
        assert ident(Path(row['path']))==row
for folder in ('semantic_user_b001_freeze_20261023_01','diagnostics_user_b001_freeze_20261023_01'):
    assert (R/'reports'/folder/'outer.single_attempt.lock').is_file()
before=json.loads((R/'reports/diagnostics_candidate_packet_20261023_01/production_shape.DIAGNOSTICS_UNAPPROVED.json').read_bytes())
after=json.loads((O/'production_shape.PROFILE_UNAPPROVED.json').read_bytes())
changes=[]
def compare(a,b,path='packet'):
    if type(a) is dict and type(b) is dict:
        for key in sorted(set(a)|set(b)):
            if key not in a:changes.append({'path':path+'.'+key,'added':b[key]})
            elif key not in b:changes.append({'path':path+'.'+key,'removed':a[key]})
            else:compare(a[key],b[key],path+'.'+key)
    elif a!=b:changes.append({'path':path,'before':a,'after':b})
compare(before,after)
with (O/'packet_changes.json').open('x') as f:json.dump(changes,f,indent=2)
manifest={'execution_authorized':False,'saved_evidence_files_reverified':92,
 'artifacts':[ident(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json'],
 'preserved_initial_partial_artifacts':[ident(p) for p in sorted(O.parent.iterdir()) if p.is_file()]}
with (O/'manifest.json').open('xb') as f:f.write((json.dumps(manifest,indent=2)+'\n').encode())
print(json.dumps(ident(O/'manifest.json')))
