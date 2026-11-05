"""Approved two-pass filesystem identity check only. No application imports."""
from datetime import datetime, timezone
import hashlib, json, os, sys
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path('F:/TERRA -Copy')
C=R/'reports/profile_candidate_packet_20261023_01/R02'
def save(name,value):
    with (O/name).open('xb') as f:f.write((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
def guarded(path):
    p=Path(path)
    assert p.is_absolute()
    for q in (p,*p.parents):
        assert not (getattr(q.lstat(),'st_file_attributes',0)&0x400),str(q)
    return p
def identity(path):
    p=guarded(path);a=p.stat();h=hashlib.sha256()
    assert p.is_file(),str(p)
    with p.open('rb') as f:
        while block:=f.read(1048576):h.update(block)
    b=p.stat()
    assert (a.st_size,a.st_mtime_ns)==(b.st_size,b.st_mtime_ns),str(p)
    return dict(path=str(p),size_bytes=b.st_size,sha256=h.hexdigest())
def check(row):
    got=identity(row['path'])
    assert all(got[k]==row[k] for k in ('size_bytes','sha256')),row['path']
    return got
def walk(root):
    pending=[guarded(root)];found=set()
    while pending:
        with os.scandir(pending.pop()) as entries:
            for e in entries:
                p=guarded(e.path)
                if e.is_dir(follow_symlinks=False):pending.append(p)
                else:
                    assert e.is_file(follow_symlinks=False),str(p)
                    found.add(str(p).casefold())
    return found
result=dict(status='STOP',execution_authorized=False,scope='FILESYSTEM_ONLY_TWO_PASS',started_utc=datetime.now(timezone.utc).isoformat())
try:
    assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
    assert identity(sys.executable)['sha256']=='3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd'
    assert identity(C/'manifest.json')['sha256']=='96979b0e7a0b0d06ec53040c9b336609ed14a9dd5c8173aff78a0e1db33395b6'
    m=json.loads((C/'manifest.json').read_bytes())
    for row in m['artifacts']+m['preserved_initial_partial_artifacts']:check(row)
    p=json.loads((C/'production_shape.PROFILE_UNAPPROVED.json').read_bytes())
    expected={};complete={}
    def add(row):
        row={k:row[k] for k in ('path','size_bytes','sha256')}
        key=row['path'].casefold()
        assert key not in expected or expected[key]==row,row['path']
        expected[key]=row
    for spec in p['declared_files'].values():
        check(spec);add(spec)
        if 'members' not in spec:continue
        rows=json.loads(Path(spec['path']).read_bytes())
        assert len(rows)==spec['members']['count']
        assert len({r['path'].casefold() for r in rows})==len(rows)
        for row in rows:
            assert any(Path(row['path']).is_relative_to(Path(root)) for root in spec['members']['roots'])
            add(row)
        for root in spec['members']['complete_roots']:
            members={r['path'].casefold() for r in rows if Path(r['path']).is_relative_to(Path(root))}
            assert root not in complete or complete[root]==members
            complete[root]=members
    for number in (1,2):
        observations=[]
        for n,row in enumerate(expected.values(),1):
            observations.append(check(row))
            if n%5000==0:print(f'Pass {number}: {n} files verified',flush=True)
        for root,members in complete.items():assert walk(root)==members,root
        save(f'pass_{number}.json',observations)
    assert (O/'pass_1.json').read_bytes()==(O/'pass_2.json').read_bytes()
    assert p['config']['authorization_id'] is None and p['reviewed_approval'] is None
    assert not Path(p['approval_path']).exists()
    assert not Path(p['config']['evidence_directory']).parent.exists()
    for file,marker in {
        'offline_smoke_production.py':'ENTRY_ADMITTED = False',
        'offline_smoke_authentic.py':'PRODUCTION_ADMITTED = False',
        'offline_smoke_executor.py':'EXECUTION_ADMITTED = False',
        'offline_smoke_windows_assembly.py':'NATIVE_EXECUTION_ADMITTED = False',
        'offline_smoke_entry_anchor.py':'PACKET_PATH = None',
        'launch_offline_smoke_user.ps1':'$LaunchAdmitted = $false'}.items():
        assert marker in (R/'scripts/matched_baseline'/file).read_text()
    result.update(status='PASS',unique_declared_files=len(expected),passes=2,complete_roots=list(complete),admissions_closed=True,candidate_absent=True,pass_sha256=identity(O/'pass_1.json')['sha256'])
except Exception as exc:
    result.update(failure_type=type(exc).__name__,failure_location=str(exc)[:400])
finally:
    result['finished_utc']=datetime.now(timezone.utc).isoformat()
    save('RESULT.json',result);print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='PASS' else 1)
