"""Package proposal and check preserved evidence. No runtime/project imports."""
import hashlib
import json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def ident(p):
    raw=p.read_bytes()
    return {'path':str(p),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
old=R/'reports/semantic_b001_postrun_20261023_01/evidence_manifest.json'
for row in json.loads(old.read_bytes()):assert ident(Path(row['path']))==row
for p in (R/'reports/semantic_user_b001_freeze_20261023_01/outer.single_attempt.lock',
          R/'reports/authentic_smoke_semantic_candidate_20261023_01/single_use.lock'):
    assert p.is_file()
manifest={'execution_authorized':False,'saved_evidence_files_verified':46,'locks_retained':True,
          'artifacts':[ident(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']}
with (O/'manifest.json').open('xb') as f:f.write((json.dumps(manifest,indent=2)+'\n').encode())
print(json.dumps(ident(O/'manifest.json')))
