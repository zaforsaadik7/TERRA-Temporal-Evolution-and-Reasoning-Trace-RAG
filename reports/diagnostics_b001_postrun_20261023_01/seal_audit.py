"""Hash saved evidence and audit artifacts; no application imports."""
import hashlib
import json
from pathlib import Path
P=Path(__file__).resolve().parent
R=Path('F:/TERRA -Copy')
def ident(p):
    raw=p.read_bytes()
    return {'path':str(p),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
for row in json.loads((P/'evidence_manifest.json').read_bytes()):
    assert ident(Path(row['path']))==row
closed=[ident(R/'scripts/matched_baseline'/n) for n in
        ('offline_smoke_production.py','offline_smoke_entry_anchor.py','launch_offline_smoke_user.ps1')]
manifest={'saved_evidence_reverified':True,'closed_source_identities':closed,
          'files':[ident(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='manifest.json']}
with (P/'manifest.json').open('xb') as f:f.write((json.dumps(manifest,indent=2)+'\n').encode())
print(json.dumps(ident(P/'manifest.json')))


