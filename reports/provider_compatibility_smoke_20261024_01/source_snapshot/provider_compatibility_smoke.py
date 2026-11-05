"""Narrow five-role live compatibility candidate. No execution without user record.

Uses fictional note only, no benchmark/retrieval/models/tokenizer initialization.
Public DBU-rate ceiling is a pricing assumption, not an account billing certificate.
"""
import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.matched_baseline.provider_accounting import (
    BudgetJournal, CallIdentity, ContractError, DispatchHeld, Price, RoleConfig,
    canonical, parse_envelope, accepted_result,
)
from scripts.matched_baseline.provider_run_control import _exchange
from scripts.matched_baseline.paired_prompt_workflow import messages, parsed_content

HOST='dbc-899e438f-4c30.cloud.databricks.com'
PACKAGE=ROOT/'reports'/'provider_compatibility_smoke_20261024_01'
ROLES=('router','verifier','generator','judge1','judge2')
ENDPOINTS=('databricks-gemma-3-12b','databricks-meta-llama-3-3-70b-instruct',
           'databricks-meta-llama-3-3-70b-instruct','databricks-qwen3-next-80b-a3b-instruct',
           'databricks-gpt-oss-120b')
FOUNDATIONS=('system.ai.gemma-3-12b-it','system.ai.llama_v3_3_70b_instruct',
              'system.ai.llama_v3_3_70b_instruct','system.ai.qwen3-next-80b-a3b-instruct','system.ai.gpt-oss-120b')
CAPS=(128,512,512,1024,4096)
# Published DBU per million tokens; nanodollar rates assume <=$1/DBU.
DBU_RATES=(('2.143','7.143'),('7.143','21.429'),('7.143','21.429'),
           ('2.143','17.143'),('2.143','8.571'))
REQUIRED_SOURCES=('scripts/matched_baseline/provider_compatibility_smoke.py',
                  'scripts/matched_baseline/provider_accounting.py',
                  'scripts/matched_baseline/provider_run_control.py',
                  'scripts/matched_baseline/paired_prompt_workflow.py',
                  'scripts/matched_baseline/common_serializer.py',
                  'scripts/matched_baseline/matched_harness.py',
                  'scripts/matched_baseline/hybrid_retriever.py',
                  'scripts/matched_baseline/terra_retriever.py',
                  'scripts/matched_baseline/bm25_engine.py',
                  'scripts/matched_baseline/inspect_databricks_metadata.py',
                  'scripts/matched_baseline/__init__.py')
QUERY='What year is stated in the supplied fictional note?'
EVIDENCE='[Document 1] ID: fictional-note | Title: Fictional Note (1900)\nSnippet: This invented note states the year 1900. It is not a real case or legal authority.'


def configs():
    from decimal import Decimal
    result=[]
    for r,e,f,cap,rates in zip(ROLES,ENDPOINTS,FOUNDATIONS,CAPS,DBU_RATES):
        aliases=(e,f,e.removeprefix('databricks-'))
        price=Price('PUBLIC_DBU_20261024_ASSUMED_MAX_1_USD_PER_DBU',
                    int(Decimal(rates[0])*10**9),int(Decimal(rates[1])*10**9),True)
        result.append(RoleConfig(r,'https://'+HOST,e,aliases,128000,8192,cap,8192,1024**2,120,price))
    return tuple(result)


def plan():
    cfg=configs()
    return {'scope':'FIVE_ROLE_COMPATIBILITY_SMOKE','workspace_origin':'https://'+HOST,
            'maximum_calls':5,'automatic_retries':0,'proposed_spend_cap_nanodollars':10**9,
            'usd_per_dbu_ceiling_assumption':'1.00','actual_account_rate_confirmed':False,
            'maximum_reserved_nanodollars':sum(c.price.cost(c.reserved_input_tokens,c.max_output_tokens) for c in cfg),
            'query':QUERY,'evidence':EVIDENCE,'roles':[asdict(c) for c in cfg],
            'gpt_oss_reasoning_effort':'low','benchmark_queries_used':False,
            'timeout_policy':'120_seconds_cooperative_socket_timeout_per_call_no_independent_native_watchdog',
            'timeout_exception_scope':'only_this_five_call_API_diagnostic_not_the_full_study',
            'input_measurement':'not_measured_8192_provider_token_reservation_not_a_tokenizer_certificate'}


def validate_approval(record,manifest_sha):
    if (type(record) is not dict or record.get('status')!='APPROVED_BY_USER'
            or record.get('scope')!='FIVE_ROLE_COMPATIBILITY_SMOKE'
            or record.get('plan_sha256')!=hashlib.sha256(canonical(plan())).hexdigest()
            or record.get('source_manifest_sha256')!=manifest_sha
            or type(record.get('max_spend_nanodollars')) is not int
            or record['max_spend_nanodollars']!=10**9
            or record.get('accept_public_rate_ceiling_assumption') is not True
            or record.get('accept_cooperative_timeout_exception') is not True
            or type(record.get('human_message')) is not str or not record['human_message'].strip()):
        raise DispatchHeld('Explicit plan-bound smoke approval required')


def redact(value,token):
    if type(value) is str:return value.replace(token,'[REDACTED]') if token else value
    if type(value) is dict:return {redact(k,token):redact(v,token) for k,v in value.items()}
    if type(value) in (list,tuple):return [redact(v,token) for v in value]
    return value


def write_event(file,event,token):
    raw=canonical(redact(event,token))
    if len(raw)>2*1024**2: raise ContractError('Smoke event bound exceeded')
    if file.write(raw)!=len(raw): raise OSError('Short smoke write')
    file.flush();os.fsync(file.fileno())


def execute(factory,token,out):
    """Internal tested core; CLI approval and source checks must precede genuine use."""
    out=Path(out);out.mkdir()
    with (out/'single_attempt.lock').open('xb') as f: f.write(b'ONE_ATTEMPT_NO_RETRY\n');f.flush();os.fsync(f.fileno())
    ledger=BudgetJournal(out/'calls.jsonl',10**9,5)
    completed=[];answer=None
    try:
        with (out/'events.jsonl').open('xb') as events:
            for c in configs():
                identity=CallIdentity('COMPATIBILITY_001','shared' if c.role=='router' else 'H',c.role)
                msgs=messages(c.role,QUERY,EVIDENCE,answer if c.role.startswith('judge') else None)
                body={'messages':[{'role':r,'content':v} for r,v in msgs],
                      'temperature':0,'max_tokens':c.max_output_tokens,'stream':False}
                if c.role=='judge2':body['reasoning_effort']='low'
                request=canonical(body)
                if len(request)>8192:raise ContractError('Request byte envelope exceeded')
                # No authentic tokenizer loaded for this tiny API diagnostic.
                # Bytes are recorded separately, never mislabeled as token evidence.
                ledger.reserve(identity,c,request,None)
                write_event(events,{'kind':'REQUEST','role':c.role,'payload':body},token)
                try:
                    raw=_exchange(factory(c),c,request,token,__import__('time').monotonic,lambda:False)
                    write_event(events,{'kind':'RESPONSE_IDENTITY','role':c.role,
                        'response_sha256':hashlib.sha256(raw).hexdigest(),'response_bytes':len(raw)},token)
                    data,usage,prompt,completion,reasoning=parse_envelope(raw,c)
                    ledger.settle(identity,c,redact(usage,token),prompt,completion,hashlib.sha256(raw).hexdigest(),
                                  redact({'returned_model':data.get('model'),'request_id':data.get('id')},token))
                    # Preserve only selected fields, not open-model hidden reasoning text.
                    summary={'kind':'RESPONSE','role':c.role,'model':data.get('model'),'id':data.get('id'),
                             'usage':usage,'response_sha256':hashlib.sha256(raw).hexdigest()}
                    choice=data.get('choices',[{}])
                    if type(choice) is list and len(choice)==1 and type(choice[0]) is dict:
                        message=choice[0].get('message',{})
                        summary['finish_reason']=choice[0].get('finish_reason')
                        summary['content']=message.get('content') if type(message) is dict else None
                    write_event(events,summary,token)
                    if token and canonical(redact(data,token))!=canonical(data):
                        raise ContractError('Credential echo rejected before further dispatch')
                    result=accepted_result(data,usage,prompt,completion,reasoning,raw,c)
                    parsed=parsed_content(c.role,result.content)
                    if c.role=='generator':answer=parsed
                    completed.append(c.role)
                except Exception:
                    if ledger.entries[identity.key]['state']=='RESERVED' and not ledger.persistence_failed:
                        ledger.uncertain(identity,'COMPATIBILITY_CALL_UNRESOLVED')
                    ledger.halted=True
                    raise
        terminal={'status':'COMPATIBILITY_SMOKE_COMPLETE','completed_roles':completed,
                  'maximum_calls':5,'reference_priced_cost_nanodollars':ledger.exposure,
                  'actual_account_billing_certified':False,'study_authorized':False}
    except Exception as e:
        terminal={'status':'STOPPED_NO_RETRY','failure_type':type(e).__name__,
                  'completed_roles':completed,'calls_reserved':len(ledger.entries),
                  'reference_priced_exposure_nanodollars':ledger.exposure,'study_authorized':False}
    finally:ledger.close()
    raw=canonical(terminal)
    with (out/'terminal.pending').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    os.rename(out/'terminal.pending',out/'terminal.json')
    return terminal


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--execute-smoke',action='store_true');a=p.parse_args(argv)
    if not a.execute_smoke:
        print('HELD: user approval of five-call smoke and pricing assumption required');return 2
    manifest_path=PACKAGE/'source_manifest.json'
    raw=manifest_path.read_bytes();manifest=json.loads(raw)
    approval=json.loads((PACKAGE/'APPROVAL.json').read_bytes())
    validate_approval(approval,hashlib.sha256(raw).hexdigest())
    verify_manifest_membership(manifest)
    for row in manifest['files']:
        path=Path(row['path'])
        if path.stat().st_size!=row['size_bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:
            raise DispatchHeld('Frozen smoke constituent changed')
    key_spec=importlib.util.spec_from_file_location('local_smoke_key_reader',Path(__file__).with_name('inspect_databricks_metadata.py'))
    key_module=importlib.util.module_from_spec(key_spec);key_spec.loader.exec_module(key_module)
    key_module.no_alias(PACKAGE/'attempt')
    if (PACKAGE/'attempt').exists():raise DispatchHeld('Attempt already exists; no retry')
    token=key_module.load_token(ROOT/'.env.terra-databricks.local')
    try:
        import ssl
        from http.client import HTTPSConnection
        terminal=execute(lambda c:HTTPSConnection(HOST,timeout=c.timeout_seconds,context=ssl.create_default_context()),token,PACKAGE/'attempt')
    finally:token=None
    print('Compatibility outcome:',terminal['status']);print('Evidence:',PACKAGE/'attempt')
    return 0 if terminal['status']=='COMPATIBILITY_SMOKE_COMPLETE' else 1


def verify_manifest_membership(manifest):
    if type(manifest) is not dict or type(manifest.get('files')) is not list:
        raise DispatchHeld('Source manifest missing')
    paths=[str(Path(r['path']).resolve()) for r in manifest['files']]
    if len(paths)!=len(set(paths)):raise DispatchHeld('Duplicate source pins')
    required={str((ROOT/p).resolve()) for p in REQUIRED_SOURCES}
    if required!=set(paths):
        raise DispatchHeld('Source membership differs from exact reviewed dependency set')


if __name__=='__main__':
    try:code=main()
    except Exception as e:print('Smoke held/stopped:',type(e).__name__);code=2
    raise SystemExit(code)
