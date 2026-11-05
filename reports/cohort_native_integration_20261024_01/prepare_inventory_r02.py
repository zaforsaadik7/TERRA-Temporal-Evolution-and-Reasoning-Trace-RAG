"""Filesystem-only prospective cohort plan. stdlib, no project/model imports.

Historical packet supplies PATHS only. All identities/memberships are refreshed
twice; immutable scientific inputs must additionally match historical pins.
Never changes source, admission, inputs or actual attempt directory.
"""
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import stat

ROOT=Path('F:/TERRA -Copy')
OUT=ROOT/'reports/cohort_readiness_20261024_r02'
OUT.mkdir(exist_ok=False)
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,sort_keys=True)
def guard(path):
    path=Path(path)
    if not path.is_absolute() or '..' in path.parts:raise ValueError('Invalid inventory path')
    for part in (path,*path.parents):
        info=part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('Reparse inventory boundary')
    return path
def identity(path):
    path=guard(path);before=path.stat();total=0;h=hashlib.sha256()
    if not stat.S_ISREG(before.st_mode):raise ValueError('Ordinary pinned file required')
    with path.open('rb') as f:
        opened=os.fstat(f.fileno())
        for block in iter(lambda:f.read(1024**2),b''):total+=len(block);h.update(block)
        after=os.fstat(f.fileno())
    final=path.stat();attrs=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
    if (any(getattr(before,k)!=getattr(final,k) for k in attrs)
            or any(getattr(opened,k)!=getattr(after,k) for k in attrs)
            or (opened.st_dev,opened.st_ino,opened.st_size,opened.st_mtime_ns)!=(
                before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)
            or total!=before.st_size):raise ValueError('Inventory changed while hashing')
    return dict(path=str(path),size_bytes=total,sha256=h.hexdigest())
def members(root,excluded=()):
    root=guard(root);stack=[root];found=[]
    while stack:
        directory=stack.pop()
        for path in directory.iterdir():
            path=guard(path);info=path.lstat()
            if path.parent==root and path.name in excluded:continue
            if stat.S_ISDIR(info.st_mode):stack.append(path)
            elif stat.S_ISREG(info.st_mode):
                if info.st_nlink!=1:raise ValueError('Hardlink in complete root')
                found.append(path)
            else:raise ValueError('Unexpected filesystem member')
            if len(found)>100000:raise ValueError('Inventory entry ceiling')
    return sorted(found,key=lambda p:str(p).casefold())
result=dict(status='STOP',scope='FILESYSTEM_ONLY_UNAPPROVED_PLAN',models_loaded=False,
    database_opened=False,network=False,started_utc=datetime.now(timezone.utc).isoformat())
try:
    historical=json.loads((ROOT/'reports/explicit_user_b001_freeze_20261023_01/execution_packet.json').read_bytes())
    paths={};core={}
    for name,spec in historical['declared_files'].items():
        if 'members' in spec:
            observed=identity(spec['path'])
            if observed['sha256']!=spec['sha256']:raise ValueError('Historical path manifest changed')
            rows=json.loads(Path(spec['path']).read_bytes())
        else:rows=[spec]
        for row in rows:
            paths[str(Path(row['path'])).casefold()]=Path(row['path'])
            if name in {'benchmark','graph','store','cache','tokenizer_manifests'}:
                core[str(Path(row['path'])).casefold()]=row
    base=Path('C:/Users/zafor/AppData/Local/Python/pythoncore-3.14-64')
    source=Path(historical['integrity']['source']);cache=Path(historical['integrity']['cache'])
    tokens=ROOT/'assets/tokenizers';namespace=ROOT/'scripts/matched_baseline'
    roots=[source,cache,tokens,base/'DLLs',ROOT/'venv/Lib/site-packages']
    external={str(namespace/name).casefold() for name in ('offline_cohort_anchor.py','launch_offline_cohort_user.ps1')}
    for key in external:paths.pop(key,None)
    # Include the complete dependency directory except two externally pinned
    # trust-root files. Their identities are recorded separately, not cycled.
    namespace_paths=members(namespace)
    for path in namespace_paths:
        if str(path).casefold() not in external:paths[str(path).casefold()]=path
    stdlib_paths=members(base/'Lib',excluded=('site-packages',))
    for path in stdlib_paths:paths[str(path).casefold()]=path
    for path in base.iterdir():
        if path.is_file():paths[str(path).casefold()]=path
    cfg=ROOT/'venv/pyvenv.cfg'
    values={line.split('=',1)[0].strip().lower():line.split('=',1)[1].strip().lower()
        for line in cfg.read_text().splitlines() if '=' in line}
    if values.get('include-system-site-packages')!='false':raise ValueError('Global site packages not excluded')
    root_maps=[]
    for root in roots:
        rows=members(root)
        root_maps.append(dict(root=str(root),members=sorted(p.relative_to(root).as_posix() for p in rows)))
        for path in rows:paths[str(path).casefold()]=path
    baseline_paths=sorted(paths.values(),key=lambda p:str(p).casefold())
    passes=[]
    for number in (1,2):
        observed=[]
        for i,path in enumerate(baseline_paths,1):
            row=identity(path);observed.append(row)
            expected=core.get(str(path).casefold())
            if expected and (row['sha256'],row['size_bytes'])!=(expected['sha256'],expected['size_bytes']):
                raise ValueError('Immutable scientific input differs from preserved baseline')
            if i%5000==0:print('Filesystem pass',number,'files',i,flush=True)
        for declared in root_maps:
            actual=sorted(p.relative_to(Path(declared['root'])).as_posix() for p in members(Path(declared['root'])))
            if actual!=declared['members']:raise ValueError('Root membership changed during pass')
        if [str(p) for p in members(namespace)]!=[str(p) for p in namespace_paths]:
            raise ValueError('Project namespace changed during pass')
        if members(base/'Lib',excluded=('site-packages',))!=stdlib_paths:
            raise ValueError('Standard library namespace changed during pass')
        save(f'pass_{number}.json',observed);passes.append(observed)
    if passes[0]!=passes[1]:raise ValueError('Two filesystem passes differ')
    benchmark=ROOT/'terra_350_benchmark.json';raw=benchmark.read_bytes()
    benchmark_sha=hashlib.sha256(raw).hexdigest()
    if benchmark_sha!='8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3':
        raise ValueError('Benchmark identity changed')
    rows=json.loads(raw)
    queries=[dict(query_id=r['query_id'],category=r['category'],
        text_sha256=hashlib.sha256(r['query'].encode()).hexdigest()) for r in rows]
    if Counter(q['category'] for q in queries)!={'A_Factual':100,'B_Evolutionary':100,'C_OutOfContext':75,'D_Adversarial':75}:
        raise ValueError('Wrong cohort categories')
    run_id='cohort_20261024_controlled01';attempt=ROOT/'reports'/run_id
    if attempt.exists():raise ValueError('Proposed attempt directory already exists')
    resources=dict(child_seconds=1800,outer_seconds=2400,finalization_reserve_seconds=300,
        memory_bytes=4*1024**3,capture_bytes=16*1024**2,report_bytes=16*1024**2,
        query_record_bytes=32*1024,evidence_bytes=128*1024**2,free_space_floor_bytes=2*1024**3,
        disposable_growth_bytes=512*1024**2,termination_wait_seconds=30)
    spec=dict(queries=queries,benchmark_path=str(benchmark),benchmark_sha256=benchmark_sha,
        scope='COHORT_OFFLINE_FEASIBILITY',expected_documents=20000,batch_size=32)
    graph=Path(historical['declared_files']['graph']['path'])
    plan=dict(workspace=str(ROOT),source_directory=str(source),cache_directory=str(cache),
        graph_archive=str(graph),tokenizer_directory=str(tokens),graph_sha256=identity(graph)['sha256'])
    indexed={r['path'].casefold():r for r in passes[1]}
    role_paths=dict(controller_image=ROOT/'venv/Scripts/python.exe',child_image=ROOT/'venv/Scripts/python.exe',
        firewall_image=base/'python.exe',controller_entry=namespace/'offline_cohort_entry.py',
        child_entry=namespace/'offline_cohort_entry.py',boundary_script=namespace/'offline_cohort_windows_boundary.ps1',
        powershell=Path(historical['windows']['powershell_path']),kernel32=Path(historical['windows']['system_directory'])/'kernel32.dll')
    launch=dict(parent=dict(spec=spec,plan=plan,resources=resources,pins=passes[1],roots=root_maps,
        benchmark_path=str(benchmark),synthetic_fixture=False),
        allocation=dict(root=str(attempt/'evidence'),parent_bytes=64*1024**2,child_bytes=64*1024**2),
        run_id=run_id,artifacts=[[role,indexed[str(path).casefold()]] for role,path in sorted(role_paths.items())],
        rule_name='TERRA_Cohort_20261024_controlled01',owner_tag='TERRA_COHORT_20261024_controlled01',
        poll_seconds=.25,process_policy='ONLY_VERIFIED_OWN_DIRECT_PARENT_ACCEPTED_NO_NETWORK_EXEMPTION')
    save('launch.UNAPPROVED.json',launch)
    save('external_trust_root_observations.json',[identity(namespace/name) for name in ('offline_cohort_anchor.py','launch_offline_cohort_user.ps1')])
    result.update(status='PASS',unique_files=len(passes[1]),complete_roots=len(roots),
        attempt_created=False,authority_record_created=False,source_admission_changed=False,
        byte_total=sum(row['size_bytes'] for row in passes[1]),proposed_resources=resources)
except Exception as exc:
    result['failure_type']=type(exc).__name__;result['failure']=str(exc)
    raise
finally:
    result['finished_utc']=datetime.now(timezone.utc).isoformat();save('RESULT.json',result)
print(json.dumps(result),flush=True)
