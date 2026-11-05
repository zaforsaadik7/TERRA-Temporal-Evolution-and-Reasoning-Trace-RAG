"""User-approved offline comparison and file hashing only; no cached code exec."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import marshal
import os
from pathlib import Path, PureWindowsPath
import struct
import sys
from types import CodeType

R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
C=R/'reports/diagnostics_candidate_packet_20261023_01'
FIELDS=('co_argcount','co_posonlyargcount','co_kwonlyargcount','co_nlocals','co_stacksize',
        'co_flags','co_code','co_names','co_varnames','co_name','co_qualname','co_firstlineno',
        'co_linetable','co_exceptiontable','co_freevars','co_cellvars','co_lnotab')
def save(name,value):
    with (O/name).open('xb') as f:f.write((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
def guarded(path):
    p=Path(path);assert p.is_absolute()
    for q in (p,*p.parents):
        assert not (getattr(q.lstat(),'st_file_attributes',0)&0x400), str(q)
    return p
def identity(path):
    p=guarded(path);before=p.stat();h=hashlib.sha256()
    with p.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk)
    after=p.stat()
    assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns), str(p)
    return {'path':str(p),'size_bytes':after.st_size,'sha256':h.hexdigest()}
def check(row):
    result=identity(row['path'])
    assert all(row[k]==result[k] for k in ('size_bytes','sha256')), row['path']
    return result
def compare_code(left,right,*,location='root',counts=None,depth=0):
    if counts is None:counts=Counter()
    assert depth<=64 and type(left) is CodeType and type(right) is CodeType, location
    counts['code_objects']+=1
    assert counts['code_objects']<=2000
    for name in FIELDS:
        assert type(getattr(left,name)) is type(getattr(right,name)), location+'.'+name
        assert getattr(left,name)==getattr(right,name), location+'.'+name
    assert PureWindowsPath(left.co_filename)==PureWindowsPath(right.co_filename), location+'.co_filename'
    assert len(left.co_consts)==len(right.co_consts), location+'.co_consts'
    def constant(a,b,where,level):
        assert level<=64 and type(a) is type(b), where
        if type(a) is CodeType:
            compare_code(a,b,location=where,counts=counts,depth=level)
        elif type(a) is tuple:
            assert len(a)==len(b), where
            for i,(x,y) in enumerate(zip(a,b)):constant(x,y,where+'.tuple'+str(i),level+1)
        else:
            assert a==b, where
        counts['constants']+=1
    for i,(a,b) in enumerate(zip(left.co_consts,right.co_consts)):
        constant(a,b,location+'.const'+str(i),depth+1)
    return counts
def selftests():
    code=compile('def f(x):\n    try:\n        return x + 1\n    except Exception:\n        return 0\n',
                 'C:/synthetic/fixture.py','exec',dont_inherit=True,optimize=0)
    cached=marshal.loads(marshal.dumps(code))
    compare_code(code,cached)
    variants=[code.replace(co_flags=code.co_flags ^ 1),
              code.replace(co_stacksize=code.co_stacksize+1),
              code.replace(co_exceptiontable=b'\x00'),
              code.replace(co_linetable=b''),
              code.replace(co_filename='C:/synthetic/other.py')]
    nested=code.co_consts[0]
    variants.append(code.replace(co_consts=(nested.replace(co_flags=nested.co_flags ^ 1),*code.co_consts[1:])))
    for changed in variants:
        try:compare_code(code,changed)
        except AssertionError:pass
        else:raise AssertionError('Synthetic mutation not detected')
    return {'roundtrip_positive':True,'negative_mutations_detected':len(variants),
            'compiled_fixture_executed':False}
def walk(root):
    pending=[guarded(root)];found=set()
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                p=guarded(entry.path)
                if entry.is_dir(follow_symlinks=False):pending.append(p)
                else:
                    assert entry.is_file(follow_symlinks=False), str(p)
                    found.add(str(p).casefold())
    return found

result={'status':'STOP','execution_authorized':False,'started_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'APPROVED_BYTECODE_STRUCTURAL_COMPARISON_AND_FILESYSTEM_HASHING_ONLY'}
try:
    assert sys.version_info[:2]==(3,14) and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
    assert identity(Path(sys.executable))['sha256']=='3adbbf2af609e206e3ca18cd55fc7c4b52f5c8bb8218dd99fd5a9e50d7a193cd'
    save('comparison_selftests.json',selftests())
    check({'path':str(C/'manifest.json'),'size_bytes':2459,
           'sha256':'4e5d3075cf93492fda243f272232082df56993a5fc08fad4e9618a7e2e0d29dd'})
    for row in json.loads((C/'manifest.json').read_bytes())['artifacts']:check(row)
    packet=json.loads((C/'production_shape.DIAGNOSTICS_UNAPPROVED.json').read_bytes())
    expected={};complete={}
    def add(row):
        row={k:row[k] for k in ('path','size_bytes','sha256')};key=row['path'].casefold()
        assert key not in expected or expected[key]==row, row['path']
        expected[key]=row
    for spec in packet['declared_files'].values():
        check(spec);add(spec)
        if 'members' not in spec:continue
        rows=json.loads(Path(spec['path']).read_bytes())
        assert len(rows)==spec['members']['count']
        assert len({row['path'].casefold() for row in rows})==len(rows)
        for row in rows:
            assert any(Path(row['path']).is_relative_to(Path(root)) for root in spec['members']['roots'])
            add(row)
        for root in spec['members']['complete_roots']:
            members={row['path'].casefold() for row in rows if Path(row['path']).is_relative_to(Path(root))}
            assert root not in complete or complete[root]==members
            complete[root]=members
    receipts=[]
    for name in ('offline_smoke_production','offline_smoke_authentic','offline_smoke_diagnostics'):
        source=R/'scripts/matched_baseline'/(name+'.py')
        cache=source.parent/'__pycache__'/(name+'.cpython-314.pyc')
        source_id=check(expected[str(source).casefold()]);cache_id=check(expected[str(cache).casefold()])
        assert source_id['size_bytes']<=1048576 and 16<cache_id['size_bytes']<=131072
        raw=cache.read_bytes();source_raw=source.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==cache_id['sha256']
        assert hashlib.sha256(source_raw).hexdigest()==source_id['sha256']
        assert raw[:4]==importlib.util.MAGIC_NUMBER
        flags,mtime,size=struct.unpack('<III',raw[4:16])
        assert flags==0, 'Only reviewed timestamp caches supported'
        assert mtime==(int(source.stat().st_mtime)&0xffffffff) and size==(len(source_raw)&0xffffffff)
        stream=io.BytesIO(raw[16:]);cached=marshal.load(stream)
        assert stream.read(1)==b'', 'Trailing marshal data'
        compiled=compile(source_raw,str(source),'exec',dont_inherit=True,optimize=0)
        counts=compare_code(compiled,cached)
        assert identity(source)==source_id and identity(cache)==cache_id
        receipts.append({'source':source_id,'cache':cache_id,'header_flags':flags,
            'header_mtime':mtime,'header_source_size':size,'code_object_count':counts['code_objects'],
            'constant_count':counts['constants'],'all_compared_fields_equal':True,
            'cached_or_compiled_code_executed':False})
    save('bytecode_equivalence_receipt.json',{'status':'PINNED_STRUCTURAL_COMPARISON_PASS',
        'interpreter':sys.version,'optimization':0,'records':receipts,
        'fields_compared':[*FIELDS,'co_filename (Windows path equality)','co_consts (recursive typed comparison)'],
        'limitations':'Pinned structural comparison, not independent origin/signature proof, execution safety proof, or future admitted-source equivalence.',
        'no_application_imports':True,'model_or_database_operations':False})
    for pass_number in (1,2):
        observations=[]
        for n,row in enumerate(expected.values(),1):
            observations.append(check(row))
            if n%5000==0:print(f'Pass {pass_number}: {n} identities verified',flush=True)
        for root,members in complete.items():assert walk(root)==members, root
        save(f'pass_{pass_number}.json',observations)
    assert not Path(packet['config']['evidence_directory']).parent.exists()
    assert packet['config']['authorization_id'] is None and packet['reviewed_approval'] is None
    assert not Path(packet['approval_path']).exists()
    for relative,marker in {
        'offline_smoke_production.py':'ENTRY_ADMITTED = False',
        'offline_smoke_authentic.py':'PRODUCTION_ADMITTED = False',
        'offline_smoke_executor.py':'EXECUTION_ADMITTED = False',
        'offline_smoke_windows_assembly.py':'NATIVE_EXECUTION_ADMITTED = False',
        'offline_smoke_entry_anchor.py':'PACKET_PATH = None',
        'launch_offline_smoke_user.ps1':'$LaunchAdmitted = $false'}.items():
        assert marker in (R/'scripts/matched_baseline'/relative).read_text()
    result.update(status='PASS',unique_declared_files=len(expected),passes=2,
        complete_roots=list(complete),bytecode_pairs=3,candidate_directory_absent=True,
        admissions_closed=True,cached_code_executed=False)
except Exception as exc:
    result['failure_type']=type(exc).__name__
    # Inputs are pinned file identities, not credentials or runtime payloads.
    result['failure_location']=str(exc)[:400]
finally:
    result['finished_utc']=datetime.now(timezone.utc).isoformat();save('RESULT.json',result)
    print(json.dumps(result),flush=True)
raise SystemExit(0 if result['status']=='PASS' else 1)
