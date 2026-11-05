"""Hash verification artifacts and preserved run evidence only."""
import hashlib
import json
from pathlib import Path
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
def ident(p):
    raw=p.read_bytes()
    return {'path':str(p),'size_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
assert json.loads((O/'RESULT.json').read_bytes())['status']=='PASS'
for row in json.loads((R/'reports/semantic_b001_postrun_20261023_01/evidence_manifest.json').read_bytes()):
    assert ident(Path(row['path']))==row
for relative in ('semantic_user_b001_freeze_20261023_01/outer.single_attempt.lock',
                 'authentic_smoke_semantic_candidate_20261023_01/single_use.lock'):
    assert (R/'reports'/relative).is_file()
with (O/'STATUS.incoming.json').open('xb') as f:f.write((R/'coordination/terra_antigravity/STATUS.json').read_bytes())
manifest={'execution_authorized':False,'old_evidence_files_reverified':46,'old_locks_retained':True,
          'artifacts':[ident(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json']}
with (O/'manifest.json').open('xb') as f:f.write((json.dumps(manifest,indent=2)+'\n').encode())
print(json.dumps({'manifest':ident(O/'manifest.json'),
                 'receipt':ident(O/'bytecode_equivalence_receipt.json'),
                 'result':ident(O/'RESULT.json')}))
