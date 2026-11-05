"""Filesystem-only preparation. Standard library only; never imports project code."""
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('F:/TERRA -Copy')
OUT = Path(__file__).resolve().parent

def save(name, obj):
    with (OUT/name).open('xb') as f:
        f.write((json.dumps(obj, indent=2, sort_keys=True)+'\n').encode())

def guarded(path):
    p = Path(path)
    assert p.is_absolute(), str(p)
    for q in (p, *p.parents):
        st = q.lstat()
        assert not (getattr(st, 'st_file_attributes', 0) & 0x400), str(q)
    return p

def identity(path):
    p = guarded(path)
    before = p.stat()
    h = hashlib.sha256()
    with p.open('rb') as f:
        while chunk := f.read(1024*1024):
            h.update(chunk)
    after = p.stat()
    assert (before.st_size, before.st_mtime_ns)==(after.st_size, after.st_mtime_ns), str(p)
    return {'path':str(p), 'size_bytes':after.st_size, 'sha256':h.hexdigest()}

def walk(root):
    pending = [guarded(root)]
    found = set()
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                p = guarded(entry.path)
                if entry.is_dir(follow_symlinks=False):
                    pending.append(p)
                else:
                    assert entry.is_file(follow_symlinks=False), str(p)
                    found.add(str(p).casefold())
    return found

result = {'date_local':'2026-10-23', 'started_utc':datetime.now(timezone.utc).isoformat(),
          'execution_authorized':False, 'status':'FAIL', 'scope':'FILESYSTEM_ONLY_TWO_PASS_IDENTITY'}
try:
    draft_path = ROOT/'reports/semantic_mapping_repair_20261023_01/production_shape.REPAIRED_UNAPPROVED.json'
    assert identity(draft_path)['sha256']=='28c408e7caa501c7c580a2b219d7e71c77dbbfa6bdc1a265a423c2a9e56e9cdd'
    packet = json.loads(draft_path.read_bytes())
    assert packet['config']['authorization_id'] is None and packet['reviewed_approval'] is None
    expected = {}
    complete = {}
    def add(row):
        row = {k:row[k] for k in ('path','sha256','size_bytes')}
        key = row['path'].casefold()
        assert key not in expected or expected[key]==row, row['path']
        expected[key]=row
    for spec in packet['declared_files'].values():
        add(spec)
        got = identity(spec['path'])
        assert all(got[k]==spec[k] for k in ('sha256','size_bytes')), spec['path']
        if 'members' in spec:
            rows = json.loads(Path(spec['path']).read_bytes())
            assert len(rows)==spec['members']['count'], spec['path']
            roots = [Path(r) for r in spec['members']['roots']]
            for row in rows:
                assert any(Path(row['path']).is_relative_to(r) for r in roots), row['path']
                add(row)
            for root in spec['members']['complete_roots']:
                complete[root] = {r['path'].casefold() for r in rows if Path(r['path']).is_relative_to(Path(root))}
    for pass_number in (1,2):
        observations=[]
        for i, row in enumerate(expected.values(),1):
            got=identity(row['path'])
            assert got==row, 'Identity mismatch: '+row['path']
            observations.append(got)
            if i%5000==0:
                print(f'Pass {pass_number}: {i} identities checked', flush=True)
        for root, members in complete.items():
            assert walk(root)==members, 'Membership mismatch: '+root
        save(f'pass_{pass_number}.json', observations)
    candidate = Path(packet['config']['evidence_directory']).parent
    assert not candidate.exists() and not Path(packet['approval_path']).exists()
    holds = {
        'scripts/matched_baseline/offline_smoke_production.py':'ENTRY_ADMITTED = False',
        'scripts/matched_baseline/launch_offline_smoke_user.ps1':'$LaunchAdmitted = $false',
    }
    for path, marker in holds.items():
        text=(ROOT/path).read_text(encoding='utf-8-sig')
        assert marker in text, 'Hold marker missing: '+path
    save('production_shape.IDENTITY_CHECKED_UNAPPROVED.json',packet)
    result.update(status='PASS', unique_files=len(expected), passes=2,
                  complete_roots=list(complete), candidate_directory_absent=True,
                  authority='NULL; no admission or freeze performed')
except Exception as exc:
    result['error']=f'{type(exc).__name__}: {exc}'
finally:
    result['finished_utc']=datetime.now(timezone.utc).isoformat()
    save('IDENTITY_RESULT.json', result)
    print(json.dumps(result), flush=True)
