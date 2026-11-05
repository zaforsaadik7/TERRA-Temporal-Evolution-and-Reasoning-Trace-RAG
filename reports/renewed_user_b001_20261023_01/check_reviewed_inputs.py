"""One pre-freeze filesystem identity check. No application imports."""
import hashlib
import json
from pathlib import Path
import stat

ROOT=Path('F:/TERRA -Copy'); OUT=Path(__file__).resolve().parent
proposal=ROOT/'reports/pin_family_repair_20261023_01/packet.bound.proposal.json'
def check(row):
    p=Path(row['path'])
    for q in (p,*p.parents):
        s=q.lstat()
        if q.is_symlink() or getattr(s,'st_file_attributes',0)&0x400: raise ValueError('Reparse boundary: '+str(q))
    before=p.stat()
    if not stat.S_ISREG(before.st_mode): raise ValueError('Nonordinary file')
    with p.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
    after=p.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns): raise ValueError('Changed during hash: '+str(p))
    if (digest,after.st_size)!=(row['sha256'],row['size_bytes']): raise ValueError('Identity mismatch: '+str(p))
    return str(p)
report={'stage':'PRE_FREEZE_FILESYSTEM_CHECK','parent_attempted':False,'checked_files':0}
try:
    raw=proposal.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='eb6404cb4e3912e652c1026408d69ccecac3d194f2170563e6237dc2dce56618'
    packet=json.loads(raw)
    members={}
    for spec in packet['declared_files'].values():
        check(spec); report['checked_files']+=1
        if 'members' not in spec: continue
        rows=json.loads(Path(spec['path']).read_bytes())
        assert len(rows)==spec['members']['count']
        local=set()
        for row in rows:
            path=row['path']; identity=(row['sha256'],row['size_bytes'])
            if path in local: raise ValueError('Duplicate member')
            local.add(path)
            if path in members and (members[path]['sha256'],members[path]['size_bytes'])!=identity: raise ValueError('Conflicting identity')
            members[path]=row
        for root in spec['members']['complete_roots']:
            actual=set()
            pending=[Path(root)]
            while pending:
                directory=pending.pop()
                for entry in directory.iterdir():
                    s=entry.lstat()
                    if entry.is_symlink() or getattr(s,'st_file_attributes',0)&0x400: raise ValueError('Reparse member')
                    if entry.is_dir(): pending.append(entry)
                    elif entry.is_file(): actual.add(str(entry))
            assert actual=={p for p in local if Path(root) in Path(p).parents}, 'Complete membership changed'
    for i,row in enumerate(members.values()):
        check(row); report['checked_files']+=1
        if i%5000==0: print('VERIFIED_MEMBERS',i,flush=True)
    for name in ('evidence','snapshot','disposable','single_use_lock'):
        assert not Path(packet['candidate_paths'][name]).exists(), 'Candidate path already exists: '+name
    report.update(status='PASS',unique_members=len(members),limits='Point-in-time byte check, not a filesystem lock.')
except Exception as exc:
    report.update(status='STOP',failure=str(exc))
    raise
finally:
    with (OUT/'pre_freeze_check.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
