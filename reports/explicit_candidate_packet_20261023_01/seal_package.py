"""Seal candidate and verify saved evidence; no operational entry."""
import hashlib,json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def ident(p):
    raw=p.read_bytes()
    return dict(path=str(p),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
count=0
for folder in ('semantic_b001_postrun_20261023_01','diagnostics_b001_postrun_20261023_01','profile_b001_postrun_20261023_01'):
    for row in json.loads((R/'reports'/folder/'evidence_manifest.json').read_bytes()):
        assert ident(Path(row['path']))==row;count+=1
for kind in ('semantic','diagnostics','profile'):
    assert (R/f'reports/{kind}_user_b001_freeze_20261023_01/outer.single_attempt.lock').is_file()
    assert (R/f'reports/authentic_smoke_{kind}_candidate_20261023_01/single_use.lock').is_file()
before=json.loads((R/'reports/profile_candidate_packet_20261023_01/R02/production_shape.PROFILE_UNAPPROVED.json').read_bytes())
after=json.loads((O/'production_shape.EXPLICIT_UNAPPROVED.json').read_bytes())
changes=[]
def compare(a,b,path='packet'):
    if type(a) is dict and type(b) is dict:
        for key in sorted(set(a)|set(b)):
            if key not in a:changes.append(dict(path=path+'.'+key,added=b[key]))
            elif key not in b:changes.append(dict(path=path+'.'+key,removed=a[key]))
            else:compare(a[key],b[key],path+'.'+key)
    elif a!=b:changes.append(dict(path=path,before=a,after=b))
compare(before,after)
with (O/'packet_changes.json').open('x') as f:json.dump(changes,f,indent=2)
with (O/'manifest.json').open('x') as f:json.dump(dict(execution_authorized=False,
    saved_evidence_files_reverified=count,artifacts=[ident(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']),f,indent=2)
print(json.dumps(ident(O/'manifest.json')))
