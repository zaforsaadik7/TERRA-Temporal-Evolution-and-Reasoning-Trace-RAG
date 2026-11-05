"""Native local-preparation launcher. No paid/provider/credential code path.

Outer owns controller Job; controller owns worker Job. Both use the existing
audited Windows backend. File identity observations are not filesystem locks.
Operator must supply an independently pinned plan SHA. Permission is supplied
by the actual user/session, not invented by a JSON record or these validators.
"""
import argparse
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
SCOPE='PAIRED_350_LOCAL_PROMPT_MEASUREMENT'
MAX_PLAN_BYTES=16*1024**2


def sha(raw):return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode()


def unique(raw):
    def pairs(rows):
        out={}
        for k,v in rows:
            if k in out:raise ValueError('Duplicate control field')
            out[k]=v
        return out
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite control value')))


def guard(path):
    p=Path(path)
    if not p.is_absolute() or '..' in p.parts:raise ValueError('Absolute bounded path required')
    for item in (p,*p.parents):
        if item.exists() or item.is_symlink():
            st=item.lstat()
            if item.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:
                raise ValueError('Reparse path forbidden')
    return p


def pin_file(path):
    p=guard(path);before=p.lstat()
    if not stat.S_ISREG(before.st_mode):raise ValueError('Regular file required')
    h=hashlib.sha256();size=0
    with p.open('rb') as f:
        opened=os.fstat(f.fileno())
        if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(opened.st_dev,opened.st_ino,opened.st_size,opened.st_mtime_ns):
            raise ValueError('Opened file identity changed')
        for block in iter(lambda:f.read(1024**2),b''):h.update(block);size+=len(block)
        after=os.fstat(f.fileno())
    final=p.lstat()
    attrs=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
    if any(getattr(before,k)!=getattr(final,k) or getattr(opened,k)!=getattr(after,k) for k in attrs):
        raise ValueError('File changed during hash')
    if size!=before.st_size:raise ValueError('File size changed')
    return dict(path=str(p),size_bytes=size,sha256=h.hexdigest())


def write_new(path,value):
    p=guard(path);raw=encode(value)
    with p.open('xb') as f:
        if f.write(raw)!=len(raw):raise OSError('Short control write')
        f.flush();os.fsync(f.fileno())
    return sha(raw)


def read_pinned(pin,limit):
    if pin['size_bytes']>limit or pin_file(pin['path'])!=pin:raise ValueError('Control pin differs')
    with Path(pin['path']).open('rb') as f:raw=f.read(limit+1)
    if len(raw)>limit or sha(raw)!=pin['sha256']:raise ValueError('Control read differs')
    return raw


def load_plan(path,expected_sha):
    p=guard(path)
    with p.open('rb') as f:raw=f.read(MAX_PLAN_BYTES+1)
    if len(raw)>MAX_PLAN_BYTES or sha(raw)!=expected_sha:raise ValueError('Preparation plan pin differs')
    value=unique(raw)
    fields={'schema','scope','human_instruction','date','attempt_dir','reference_packet','rank_ledger',
            'inputs','roots','source_plan','source_manifest','cache_manifest','system_directory',
            'kernel32','python_image','python_runtime','worker_script','resources'}
    if type(value) is not dict or set(value)!=fields or encode(value)!=raw:
        raise ValueError('Exact canonical preparation plan required')
    if (value['schema']!='TERRA_PAIRED_LOCAL_PREPARATION_V1' or value['scope']!=SCOPE
            or value['date']!='2026-10-24'
            or value['human_instruction']!='okay, fully  complete it and then give it to antigravity to review'):
        raise ValueError('Unreviewed preparation scope')
    target=guard(value['attempt_dir'])
    if not target.is_relative_to(ROOT/'reports') or target==ROOT/'reports':raise ValueError('Dedicated report attempt required')
    if type(value['inputs']) is not list or not value['inputs']:raise ValueError('Complete inputs required')
    if len({p['path'].casefold() for p in value['inputs']})!=len(value['inputs']):raise ValueError('Aliased inputs')
    for pin in value['inputs']:
        if set(pin)!={'path','size_bytes','sha256'}:raise ValueError('Exact file pin required')
        path=guard(pin['path'])
        if path.name.startswith('.env') or path.is_relative_to(target):raise ValueError('Secret/output input forbidden')
    r=value['resources']
    if (set(r)!={'child_seconds','outer_seconds','memory_bytes','outer_memory_bytes','output_bytes','evidence_bytes'}
            or any(type(v) is not int or v<=0 for v in r.values())
            or r['child_seconds']>=r['outer_seconds'] or r['child_seconds']>3600 or r['outer_seconds']>4500
            or r['memory_bytes']>4*1024**3 or r['outer_memory_bytes']>6*1024**3):
        raise ValueError('Unbounded preparation resources')
    return value,raw


def verify_inputs(plan):
    for n,pin in enumerate(plan['inputs']):
        if pin_file(pin['path'])!=pin:raise ValueError('Input file drift: '+pin['path'])
        if n and n%5000==0:print('INPUT_HASHES',n,flush=True)
    for row in plan['roots']:
        base=guard(row['root']);members=[];stack=[base]
        while stack:
            for path in stack.pop().iterdir():
                guard(path)
                if path.is_dir():stack.append(path)
                elif path.is_file():members.append(path.relative_to(base).as_posix())
                else:raise ValueError('Unexpected input member')
        if sorted(members)!=sorted(row['members']):raise ValueError('Input root membership drift')
    return dict(files=len(plan['inputs']),roots=len(plan['roots']),digest=sha(encode(plan['inputs'])))


@contextmanager
def native_kernel(plan):
    # This fresh preparation process temporarily enables only the reviewed DLL
    # loader, restoring its in-process value. No source admission file changes.
    from scripts.matched_baseline import offline_smoke_windows_assembly as windows
    before=windows.NATIVE_EXECUTION_ADMITTED
    try:
        windows.NATIVE_EXECUTION_ADMITTED=True
        yield windows.load_authentic_windows_library(system_directory=plan['system_directory'],
            reviewed_system_directory=plan['system_directory'],expected_dll_sha256=plan['kernel32']['sha256'])
    finally:windows.NATIVE_EXECUTION_ADMITTED=before


def run_job(plan,plan_path,plan_sha,role,*,handoff_sha=None):
    from scripts.matched_baseline.offline_smoke_windows_assembly import DeferredCaptureJobBackend
    from scripts.matched_baseline.offline_cohort_native import CohortJobOwner
    from scripts.matched_baseline.offline_cohort_contracts import ProposedResources
    r=plan['resources'];attempt=Path(plan['attempt_dir']);outer=role=='controller'
    seconds=r['outer_seconds'] if outer else r['child_seconds']
    resources=ProposedResources(child_seconds=seconds,outer_seconds=seconds+300,
        memory_bytes=r['outer_memory_bytes'] if outer else r['memory_bytes'],
        capture_bytes=r['output_bytes'],evidence_bytes=r['evidence_bytes'])
    args=(plan['python_image']['path'],'-I','-B',plan['worker_script']['path'],
          '--plan',str(plan_path),'--sha',plan_sha,'--role',role)
    if handoff_sha is not None:args+=('--handoff-sha',handoff_sha)
    allowed=('SystemRoot','WINDIR','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','PATH','COMSPEC')
    environment={k:os.environ[k] for k in allowed if k in os.environ}
    environment.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
                       ANONYMIZED_TELEMETRY='False',DO_NOT_TRACK='1')
    def storage():
        total=sum(p.stat().st_size for p in attempt.rglob('*') if p.is_file())
        return dict(evidence_bytes=total,disposable_bytes=0)
    with native_kernel(plan) as kernel:
        backend=DeferredCaptureJobBackend(kernel,cwd=str(ROOT),capture_path=attempt/(role+'_capture.log'),
                                          clock=time.monotonic,pause=time.sleep)
        owner=CohortJobOwner(backend,resources=resources,storage_observer=storage)
        started=time.monotonic();peak=0
        try:
            owner.start(args,environment)
            while True:
                state=owner.state();peak=max(peak,state['peak_memory_bytes'] or 0)
                if state['memory_limit_hit'] or peak>resources.memory_bytes:raise MemoryError('Preparation Job limit')
                if state['output_bytes']>r['output_bytes'] or state['evidence_bytes']>r['evidence_bytes']:
                    raise ValueError('Preparation output allocation exceeded')
                if owner.confirmed:
                    code=state['exit_code'];pid=owner.pid();owner.close()
                    return dict(exit_code=code,termination_confirmed=True,peak_memory_bytes=peak,
                                elapsed_seconds=time.monotonic()-started,pid=pid)
                if time.monotonic()-started>=seconds:raise TimeoutError('Preparation Job deadline')
                time.sleep(.5)
        except BaseException:
            if owner.used and not owner.confirmed:
                owner.terminate();owner.wait_empty(timeout_seconds=30)
            if owner.confirmed:owner.close()
            else:write_new(attempt/('RECOVERY_'+role+'.json'),dict(status='TERMINATION_UNCONFIRMED',role=role))
            raise


def controller(plan,plan_path,plan_sha):
    attempt=Path(plan['attempt_dir']);original=None;out={}
    from scripts.matched_baseline.offline_smoke_integrity import SmokeProtectedLifecycle
    from scripts.matched_baseline.offline_preflight import ManifestEntry
    source={k:ManifestEntry(**v) for k,v in plan['source_manifest'].items()}
    cache={k:ManifestEntry(**v) for k,v in plan['cache_manifest'].items()}
    lifecycle=SmokeProtectedLifecycle(source=plan['source_plan']['source_directory'],
        cache=plan['source_plan']['cache_directory'],snapshot=attempt/'snapshot',disposable=attempt/'disposable',
        source_manifest=source,cache_manifest=cache)
    try:
        reference=unique(read_pinned(plan['reference_packet'],16*1024**2))['body']['launch']['parent']
        if (reference['plan']!=plan['source_plan'] or reference['roots']!=plan['roots']
                or plan['rank_ledger']['sha256']!='9e62ac530e162aa93c5b9b94e6a3ee9e7b2e1d895c07459e7edc04704548a6cc'
                or plan['reference_packet']['sha256']!='343b88b51d0c550e547e4336a7129ce4af3af6a972ba377d22b765d9de5cf477'):
            raise ValueError('Historical ranking/asset lineage differs from audited reference')
        out['pins_before']=verify_inputs(plan)
        required=2*sum(v['size_bytes'] for v in plan['source_manifest'].values())+2*1024**3
        if shutil.disk_usage(attempt).free<required:raise OSError('Insufficient preparation copy/free-space reserve')
        receipt=lifecycle.prepare()
        handoff_sha=write_new(attempt/'handoff.json',dict(plan_sha256=plan_sha,receipt=asdict(receipt)))
        out['worker']=run_job(plan,plan_path,plan_sha,'worker',handoff_sha=handoff_sha)
        if out['worker']['exit_code']!=0:raise RuntimeError('Measurement worker failed')
        summary=unique((attempt/'measurement_summary.json').read_bytes())
        if summary['status']!='LOCAL_PROMPT_MEASUREMENTS_PASS':raise ValueError('Local prompt overflow')
    except BaseException as error:
        original=error;out['failure_type']=type(error).__name__
    finally:
        try:lifecycle.final_check();out['protected_integrity']='PASS'
        except BaseException as error:out['integrity_failure']=type(error).__name__;original=original or error
        try:out['pins_after']=verify_inputs(plan)
        except BaseException as error:out['inventory_failure']=type(error).__name__;original=original or error
        out['status']='LOCAL_PREPARATION_PASS' if original is None else 'FAIL'
        write_new(attempt/'controller_terminal.json',out)
    if original is not None:raise original


def worker(plan,plan_sha,handoff_sha):
    from scripts.matched_baseline.offline_preflight import (
        IntegrityLifecycleManager as Manager,IsolationReceipt,ChromaDisposableReader,
        StreamingGraphLoader,CanonicalRoleConfigFactory,InProcessNetworkBlocker)
    from scripts.matched_baseline.paired_study_runtime import StudyQuery
    from scripts.matched_baseline.paired_dependency_bridge import RetrievalComposition
    from scripts.matched_baseline.paired_prompt_measurement import RecordedRankingReader,parse_recorded_rankings,measure_queries
    from scripts.matched_baseline.paired_study_candidate import candidate
    from scripts.matched_baseline.provider_accounting import RoleConfig,Price
    attempt=Path(plan['attempt_dir']);p=pin_file(attempt/'handoff.json')
    if p['sha256']!=handoff_sha:raise ValueError('Parent handoff differs')
    h=unique(read_pinned(p,65536))
    if set(h)!={'plan_sha256','receipt'} or h['plan_sha256']!=plan_sha:raise ValueError('Unbound handoff')
    receipt=IsolationReceipt(**h['receipt']);source=plan['source_plan']
    Manager.validate_disposable_containment(receipt=receipt,candidate_dir=Path(receipt.disposable_dir),
        expected_source_dir=Path(source['source_directory']),pre_binding=True)
    packet=unique(read_pinned(plan['reference_packet'],16*1024**2))
    if source!=packet['body']['launch']['parent']['plan']:raise ValueError('Historical source lineage mismatch')
    spec=packet['body']['launch']['parent']['spec']
    benchmark_pin=next(p for p in plan['inputs'] if p['path']==spec['benchmark_path'])
    benchmark=unique(read_pinned(benchmark_pin,2*1024**2))
    queries=[]
    for identity,row in zip(spec['queries'],benchmark):
        if (identity['query_id']!=row['query_id'] or identity['category']!=row['category']
                or identity['text_sha256']!=sha(row['query'].encode())):raise ValueError('Query pin differs')
        queries.append(StudyQuery(row['query_id'],row['query'],row['category']))
    if len(queries)!=350 or len(benchmark)!=350:raise ValueError('Exact canonical cohort required')
    historical=parse_recorded_rankings(read_pinned(plan['rank_ledger'],32*1024**2))
    ranks=RecordedRankingReader(historical,queries)
    started=time.monotonic();written=0
    with InProcessNetworkBlocker():
        reader=ChromaDisposableReader(receipt=receipt,disposable_dir=Path(receipt.disposable_dir),
                                     expected_source_dir=Path(source['source_directory']))
        reader.validate_store_schema();corpus=reader.extract_layer1_corpus(expected_count=20000)
        nodes,edges,graph=StreamingGraphLoader.load_graph_archive(Path(source['graph_archive']),
            expected_sha256=source['graph_sha256'],expected_node_count=20000)
        roles=CanonicalRoleConfigFactory.build_role_configs(Path(source['tokenizer_directory']),workspace_root=ROOT)
        tokenizers={r:v.tokenizer for r,v in roles.items()}
        configs={}
        for row in candidate()['roles']:
            row=dict(row);row['price']=Price(**row['price']);row['accepted_models']=tuple(row['accepted_models'])
            c=RoleConfig(**row);configs[c.role]=c
        retrieval=RetrievalComposition(ranks,corpus,nodes,edges)
        with (attempt/'measurements.jsonl').open('xb') as stream:
            def record(row):
                nonlocal written
                raw=encode(row);written+=len(raw)
                if written>64*1024**2:raise ValueError('Measurement journal limit')
                if stream.write(raw)!=len(raw):raise OSError('Short measurement write')
                stream.flush();os.fsync(stream.fileno())
                if row['kind']=='QUERY_COMPLETE' and row['completed']%10==0:
                    print('MEASURED',row['completed'],'/350',flush=True)
            def checkpoint():
                if time.monotonic()-started>plan['resources']['child_seconds']:raise TimeoutError('Measurement deadline')
            summary=measure_queries(queries=tuple(queries),ranking_reader=ranks,retrieval=retrieval,
                configs=configs,tokenizers=tokenizers,record=record,checkpoint=checkpoint)
        summary.update(graph_audit=graph,elapsed_seconds=time.monotonic()-started,
            plan_sha256=plan_sha,rank_ledger_sha256=plan['rank_ledger']['sha256'],
            measurement_journal=pin_file(attempt/'measurements.jsonl'))
        write_new(attempt/'measurement_summary.json',summary)


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);parser.add_argument('--sha',required=True)
    parser.add_argument('--role',choices=('outer','controller','worker'),required=True)
    parser.add_argument('--handoff-sha');args=parser.parse_args(argv)
    plan,raw=load_plan(args.plan,args.sha)
    if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
    if args.role=='worker':
        if not args.handoff_sha:raise ValueError('Parent handoff SHA required')
        worker(plan,args.sha,args.handoff_sha);return 0
    if args.handoff_sha is not None:raise ValueError('Unexpected handoff argument')
    if args.role=='controller':controller(plan,args.plan,args.sha);return 0
    attempt=guard(plan['attempt_dir']);attempt.mkdir()
    write_new(attempt/'single_attempt.lock',dict(plan_sha256=args.sha,scope=SCOPE,max_provider_calls=0))
    verify_inputs(plan)
    result=run_job(plan,args.plan,args.sha,'controller')
    terminal=unique((attempt/'controller_terminal.json').read_bytes()) if (attempt/'controller_terminal.json').exists() else {}
    result.update(controller_status=terminal.get('status'),scope=SCOPE,provider_calls=0,
                  status='PASS' if result['exit_code']==0 and terminal.get('status')=='LOCAL_PREPARATION_PASS' else 'FAIL')
    write_new(attempt/'outer_terminal.json',result)
    print('LOCAL PREPARATION OUTCOME:',result['status'],flush=True)
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        print('PREPARATION FAILURE:',type(error).__name__,str(error),flush=True);raise
