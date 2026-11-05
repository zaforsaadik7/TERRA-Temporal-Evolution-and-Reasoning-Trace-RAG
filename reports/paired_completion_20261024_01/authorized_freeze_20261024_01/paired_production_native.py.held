"""Full paired-study native bootstrap SOURCE. Paid entry held before all I/O.

Reuses the same nested Job owner/backend and copy lifecycle as local preparation.
The future freeze must independently pin this entry AND its external anchor;
the anchor is excluded from the packet it pins to avoid a digest cycle.
"""
import argparse
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
import sys
import time

LIVE_ADMITTED = False
ROOT=Path(__file__).resolve().parents[2]


def launch_binding(plan):
    from scripts.matched_baseline.paired_preparation_native import encode,sha
    # Approval is produced AFTER reviewing this complete launch contract. Its
    # own byte hash must not recursively be included in the approval's binding.
    return sha(encode({k:v for k,v in plan.items() if k!='approval_pin'}))


def validate_controls(plan,context_raw,approval_raw):
    from scripts.matched_baseline.paired_preparation_native import encode,sha,unique
    from scripts.matched_baseline.paired_worker_contract import decode_worker_context,verify_worker_approval,LIVE_SCOPE
    context=decode_worker_context(context_raw,expected_sha256=plan['context_pin']['sha256'],reviewed_raw=context_raw)
    if (context.scope!=LIVE_SCOPE or asdict(context.plan)!=plan['source_plan']
            or context.reviewed_input_manifest_sha256!=sha(encode(plan['inputs']))
            or Path(context.output_root)!=Path(plan['attempt_dir'])/'results'):
        raise ValueError('Context/input/native namespace differs')
    envelope=unique(approval_raw)
    if (type(envelope) is not dict or set(envelope)!={'worker_approval','launch_binding_sha256'}
            or envelope['launch_binding_sha256']!=launch_binding(plan)):
        raise ValueError('Native command/resource launch binding differs')
    approval=envelope['worker_approval']
    if type(approval) is not dict:raise ValueError('Actual user approval is missing')
    approval_bytes=encode(approval)
    verify_worker_approval(approval_bytes,expected_sha256=sha(approval_bytes),
        reviewed_raw=approval_bytes,context=context)
    return context


def load_live_plan(path,expected_sha):
    from scripts.matched_baseline.paired_preparation_native import guard,unique,encode,sha,read_pinned
    with guard(path).open('rb') as f:raw=f.read(16*1024**2+1)
    if len(raw)>16*1024**2 or sha(raw)!=expected_sha:raise ValueError('Native plan pin differs')
    p=unique(raw)
    required={'schema','scope','attempt_dir','context_pin','approval_pin','credential_path','inputs','roots',
        'source_plan','source_manifest','cache_manifest','system_directory','kernel32','python_image',
        'python_runtime','worker_script','resources'}
    if type(p) is not dict or set(p)!=required or encode(p)!=raw or p['schema']!='TERRA_PAIRED_LIVE_NATIVE_V1':
        raise ValueError('Exact canonical live native plan required')
    if p['scope']!='PAIRED_350_LIVE_COMPARISON':raise ValueError('Wrong native scope')
    attempt=guard(p['attempt_dir'])
    if not attempt.is_relative_to(ROOT/'reports') or attempt==ROOT/'reports':raise ValueError('Dedicated output required')
    if Path(p['credential_path'])!=ROOT/'.env.terra-databricks.local':raise ValueError('Unreviewed local secret path')
    if (type(p['inputs']) is not list or not p['inputs']
            or len({row['path'].casefold() for row in p['inputs']})!=len(p['inputs'])):
        raise ValueError('Unique complete input pins required')
    for pin in p['inputs']:
        path=guard(pin['path'])
        if path.name.startswith('.env') or path.name=='paired_production_anchor.py' or path.is_relative_to(attempt):
            raise ValueError('Secret/anchor/output cannot participate in packet input hash')
    r=p['resources']
    if (set(r)!={'child_seconds','outer_seconds','memory_bytes','outer_memory_bytes','output_bytes','evidence_bytes'}
            or any(type(v) is not int or v<=0 for v in r.values()) or r['child_seconds']>=r['outer_seconds']
            or r['child_seconds']>12*3600 or r['outer_seconds']>13*3600
            or r['memory_bytes']>4*1024**3 or r['outer_memory_bytes']>6*1024**3):
        raise ValueError('Unreviewed native resource envelope')
    context_raw=read_pinned(p['context_pin'],4*1024**2)
    approval_raw=read_pinned(p['approval_pin'],65536)
    return p,validate_controls(p,context_raw,approval_raw)


@contextmanager
def live_components():
    from scripts.matched_baseline import offline_cohort_adapters as adapters
    from scripts.matched_baseline import provider_run_control as providers
    flags=((adapters,'COHORT_NATIVE_ADMITTED'),(providers,'TLS_FACTORY_ADMITTED'))
    if any(getattr(module,name) is not False for module,name in flags):
        raise ValueError('Unexpected preexisting component admission')
    try:
        for module,name in flags:setattr(module,name,True)
        yield
    finally:
        for module,name in flags:setattr(module,name,False)


def claim_role(plan,plan_sha,role):
    from scripts.matched_baseline.paired_preparation_native import guard,write_new
    if role not in ('controller','worker'):raise ValueError('Known owned child role required')
    root=guard(plan['attempt_dir'])
    if (root/'controller_terminal.json').exists() or (root/'outer_terminal.json').exists():
        raise ValueError('Native attempt already finalized; no resume')
    write_new(root/(role+'_attempt.lock'),dict(plan_sha256=plan_sha,role=role,max_attempts=1))


def worker(plan,context,plan_sha,handoff_sha):
    from scripts.matched_baseline.paired_preparation_native import pin_file,read_pinned,unique
    from scripts.matched_baseline.offline_preflight import IsolationReceipt,IntegrityLifecycleManager as Manager
    from scripts.matched_baseline.offline_cohort_execution import bind_benchmark_bytes
    from scripts.matched_baseline.paired_study_runtime import StudyQuery
    from scripts.matched_baseline.paired_local_runtime import _construct_authentic_local,_run_loaded_study
    from scripts.matched_baseline.provider_run_control import create_live_connection
    from scripts.matched_baseline.inspect_databricks_metadata import load_token
    claim_role(plan,plan_sha,'worker')
    attempt=Path(plan['attempt_dir']);pin=pin_file(attempt/'handoff.json')
    if pin['sha256']!=handoff_sha:raise ValueError('Parent handoff pin differs')
    handoff=unique(read_pinned(pin,65536))
    if (set(handoff)!={'plan_sha256','receipt'} or handoff['plan_sha256']!=plan_sha):
        raise ValueError('Parent handoff/context linkage differs')
    receipt=IsolationReceipt(**handoff['receipt'])
    Manager.validate_disposable_containment(receipt=receipt,candidate_dir=Path(receipt.disposable_dir),
        expected_source_dir=Path(context.plan.source_directory),pre_binding=True)
    bench_pin=next(p for p in plan['inputs'] if p['path']==context.spec.benchmark_path)
    raw=read_pinned(bench_pin,2*1024**2)
    binding=bind_benchmark_bytes(raw,spec=context.spec,reviewed_sha256=context.spec.benchmark_sha256,is_synthetic=False)
    queries=tuple(StudyQuery(identity.query_id,text,identity.category)
        for identity,(_,text) in zip(context.spec.queries,binding.query_pairs))
    secret=[]
    def bearer():
        if not secret:secret.append(load_token(plan['credential_path']))
        return secret[0]
    try:
        with live_components():
            bundle=_construct_authentic_local(plan=context.plan,reviewed_plan=context.plan,
                spec=context.spec,query_pairs=list(binding.query_pairs),receipt=receipt)
            return _run_loaded_study(bundle=bundle,queries=queries,configs=dict(context.configs),
                quotas=dict(context.quotas),root=context.output_root,
                cap_nanodollars=context.spend_cap_nanodollars,byte_cap=context.evidence_bytes,
                connection_factory=create_live_connection,bearer=bearer,
                mode='AUTHENTIC_PAIRED_COMPUTATION',pacing=context.pacing,seed=context.seed)
    finally:
        secret.clear()  # reference release, not a claim of memory zeroization


def controller(plan,context,plan_path,plan_sha):
    import shutil
    from scripts.matched_baseline.paired_preparation_native import verify_inputs,write_new,unique
    from scripts.matched_baseline.paired_native_job import run_job
    from scripts.matched_baseline.offline_preflight import ManifestEntry
    from scripts.matched_baseline.offline_smoke_integrity import SmokeProtectedLifecycle
    claim_role(plan,plan_sha,'controller')
    root=Path(plan['attempt_dir']);out={};failure=None
    lifecycle=SmokeProtectedLifecycle(source=context.plan.source_directory,cache=context.plan.cache_directory,
        snapshot=root/'snapshot',disposable=root/'disposable',
        source_manifest={k:ManifestEntry(**v) for k,v in plan['source_manifest'].items()},
        cache_manifest={k:ManifestEntry(**v) for k,v in plan['cache_manifest'].items()})
    try:
        out['pins_before']=verify_inputs(plan)
        if shutil.disk_usage(root).free<2*sum(v['size_bytes'] for v in plan['source_manifest'].values())+context.evidence_bytes+2*1024**3:
            raise OSError('Insufficient native study storage reserve')
        receipt=lifecycle.prepare()
        handoff_sha=write_new(root/'handoff.json',dict(plan_sha256=plan_sha,receipt=asdict(receipt)))
        out['worker']=run_job(plan,plan_path,plan_sha,'worker',handoff_sha=handoff_sha)
        if out['worker']['exit_code']!=0:raise RuntimeError('Paired worker failed')
        terminal=unique((Path(context.output_root)/'terminal.json').read_bytes())
        if (terminal.get('status')!='COMPUTATION_COMPLETE_REQUIRES_POSTRUN_AUDIT'
                or terminal.get('count')!=350):raise ValueError('Exact350 completion required')
    except BaseException as error:failure=error;out['failure_type']=type(error).__name__
    finally:
        try:lifecycle.final_check();out['protected_integrity']='PASS'
        except BaseException as error:failure=failure or error;out['integrity_failure']=type(error).__name__
        try:out['pins_after']=verify_inputs(plan)
        except BaseException as error:failure=failure or error;out['inventory_failure']=type(error).__name__
        out['status']='PAIRED_NATIVE_COMPLETE_REQUIRES_POSTRUN_AUDIT' if failure is None else 'FAIL'
        write_new(root/'controller_terminal.json',out)
    if failure is not None:raise failure


def main(argv=None):
    if not LIVE_ADMITTED:
        print('BLOCKED: paid paired native entry is not admitted');return 2
    if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
    from scripts.matched_baseline.paired_production_anchor import PLAN_PATH,PLAN_SHA256
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);parser.add_argument('--sha',required=True)
    parser.add_argument('--role',choices=('outer','controller','worker'),required=True);parser.add_argument('--handoff-sha')
    args=parser.parse_args(argv)
    if PLAN_PATH is None or PLAN_SHA256 is None or (args.plan,args.sha)!=(PLAN_PATH,PLAN_SHA256):
        raise ValueError('External native anchor differs or is absent')
    plan,context=load_live_plan(args.plan,args.sha)
    from scripts.matched_baseline.paired_preparation_native import guard,write_new,verify_inputs,unique
    from scripts.matched_baseline.paired_native_job import run_job
    if args.role=='worker':
        if not args.handoff_sha:raise ValueError('Worker handoff SHA required')
        worker(plan,context,args.sha,args.handoff_sha);return 0
    if args.handoff_sha is not None:raise ValueError('Unexpected parent handoff field')
    if args.role=='controller':controller(plan,context,args.plan,args.sha);return 0
    root=guard(plan['attempt_dir']);root.mkdir()
    write_new(root/'single_attempt.lock',dict(scope=context.scope,plan_sha256=args.sha,max_attempts=1))
    verify_inputs(plan)
    out=run_job(plan,args.plan,args.sha,'controller')
    terminal=unique((root/'controller_terminal.json').read_bytes()) if (root/'controller_terminal.json').exists() else {}
    out.update(status='PAIRED_NATIVE_COMPLETE_REQUIRES_POSTRUN_AUDIT'
        if out['exit_code']==0 and terminal.get('status')=='PAIRED_NATIVE_COMPLETE_REQUIRES_POSTRUN_AUDIT' else 'FAIL')
    write_new(root/'outer_terminal.json',out)
    print('PAIRED NATIVE OUTCOME:',out['status'],flush=True)
    return 0 if out['status']!='FAIL' else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        # Never print credentials, HTTP headers, raw exception messages or stacks.
        print('PAIRED NATIVE FAILURE TYPE:',type(error).__name__,flush=True);raise SystemExit(1)
