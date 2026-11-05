"""Continue only four UNUSED smoke calls; never repeat the saved Gemma call.

Routine deployment-name review is smoke-only, not backend-weight certification.
"""
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts.matched_baseline import provider_compatibility_smoke as original
from scripts.matched_baseline.provider_accounting import (
    BudgetJournal,CallIdentity,ContractError,DispatchHeld,canonical,parse_envelope,accepted_result,
)
from scripts.matched_baseline.provider_run_control import _exchange,_no_reparse
from scripts.matched_baseline.paired_prompt_workflow import messages,parsed_content

PACKAGE=ROOT/'reports/provider_smoke_continuation_20261024_01'
PRIOR=original.PACKAGE/'attempt'
REQUIRED_SOURCES=original.REQUIRED_SOURCES+('scripts/matched_baseline/provider_smoke_continuation.py',)


def reviewed_descriptor(role,model,config):
    if type(model) is not str:return False
    if model in config.accepted_models:return True
    normalized=model.lower().replace('_','-').replace('.','-')
    stems={'router':r'gemma-3-12b-it','verifier':r'(?:meta-)?llama-(?:v)?3-3-70b-instruct',
           'generator':r'(?:meta-)?llama-(?:v)?3-3-70b-instruct',
           'judge1':r'qwen3-next-80b-a3b-instruct','judge2':r'gpt-oss-120b'}
    return re.fullmatch(stems[role]+r'(?:-[0-9]{4,8})?',normalized) is not None


def prior_router(path):
    terminal=json.loads((path/'terminal.json').read_bytes())
    rows=[json.loads(x) for x in (path/'calls.jsonl').read_bytes().splitlines()]
    events=[json.loads(x) for x in (path/'events.jsonl').read_bytes().splitlines()]
    if (terminal.get('status')!='STOPPED_NO_RETRY' or terminal.get('calls_reserved')!=1
            or [x['kind'] for x in rows]!=['HEADER','RESERVE','SETTLE']
            or rows[1]['key']!='COMPATIBILITY_001:shared:router' or rows[2]['envelope_violation']):
        raise DispatchHeld('Prior attempt is not exactly one settled router call')
    replies=[e for e in events if e['kind']=='RESPONSE']
    if len(replies)!=1 or replies[0]['role']!='router':raise DispatchHeld('Prior router evidence incomplete')
    reply=replies[0]
    if (reply['model']!='gemma-3-12b-it-060225' or reply['finish_reason']!='stop'
            or reply['response_sha256']!=rows[2]['response_sha256']
            or parsed_content('router',reply['content'])!={'route':'EASY'}):
        raise DispatchHeld('Prior router review mismatch')
    cost=rows[2]['cost']
    if type(cost) is not int or not 0<=cost<10**9:raise DispatchHeld('Prior cost invalid')
    return {'accepted_after_review':True,'model':reply['model'],'route':'EASY',
            'prior_reference_cost_nanodollars':cost,'exact_weights_verified':False}


def validate_prior_evidence(rows,prior=PRIOR):
    if type(rows) is not list or len(rows)!=3:raise DispatchHeld('Exact prior evidence set required')
    expected={str((prior/n).resolve()) for n in ('terminal.json','calls.jsonl','events.jsonl')}
    paths=[str(Path(r['path']).resolve()) for r in rows]
    if len(set(paths))!=3 or set(paths)!=expected:raise DispatchHeld('Prior evidence membership mismatch')
    for row in rows:
        p=Path(row['path']);_no_reparse(p)
        if p.stat().st_nlink!=1 or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            raise DispatchHeld('Prior receipt changed')


def execute_remaining(factory,token,out,prior):
    review=prior_router(prior)
    out=Path(out);out.mkdir()
    with (out/'single_continuation.lock').open('xb') as f:f.write(b'FOUR_UNUSED_ROLES_ONLY\n');f.flush();os.fsync(f.fileno())
    with (out/'router_review.json').open('xb') as f:f.write(canonical(review));f.flush();os.fsync(f.fileno())
    ledger=BudgetJournal(out/'calls.jsonl',10**9-review['prior_reference_cost_nanodollars'],4)
    completed=['router'];answer=None;observed={'router':review['model']}
    try:
        with (out/'events.jsonl').open('xb') as events:
            for c in original.configs()[1:]:
                identity=CallIdentity('COMPATIBILITY_001','H',c.role)
                msgs=messages(c.role,original.QUERY,original.EVIDENCE,answer if c.role.startswith('judge') else None)
                body={'messages':[{'role':r,'content':v} for r,v in msgs],
                      'temperature':0,'max_tokens':c.max_output_tokens,'stream':False}
                if c.role=='judge2':body['reasoning_effort']='low'
                request=canonical(body)
                if len(request)>8192:raise ContractError('Request byte bound exceeded')
                ledger.reserve(identity,c,request,None)
                original.write_event(events,{'kind':'REQUEST','role':c.role,'payload':body},token)
                try:
                    raw=_exchange(factory(c),c,request,token,time.monotonic,lambda:False)
                    original.write_event(events,{'kind':'RESPONSE_IDENTITY','role':c.role,
                        'response_sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},token)
                    d,u,p,co,reasoning=parse_envelope(raw,c)
                    ledger.settle(identity,c,original.redact(u,token),p,co,hashlib.sha256(raw).hexdigest(),
                        original.redact({'model':d.get('model'),'request_id':d.get('id')},token))
                    summary={'kind':'RESPONSE','role':c.role,'model':d.get('model'),'id':d.get('id'),
                             'usage':u,'response_sha256':hashlib.sha256(raw).hexdigest()}
                    choices=d.get('choices')
                    if type(choices) is list and len(choices)==1 and type(choices[0]) is dict:
                        msg=choices[0].get('message',{})
                        summary.update(finish_reason=choices[0].get('finish_reason'),content=msg.get('content') if type(msg) is dict else None)
                    original.write_event(events,summary,token)
                    if token and canonical(original.redact(d,token))!=canonical(d):raise ContractError('Credential echo')
                    if not reviewed_descriptor(c.role,d.get('model'),c):raise ContractError('Unexpected model family')
                    reviewed=c if d['model'] in c.accepted_models else replace(c,accepted_models=c.accepted_models+(d['model'],))
                    result=accepted_result(d,u,p,co,reasoning,raw,reviewed)
                    parsed=parsed_content(c.role,result.content)
                    if c.role=='generator':answer=parsed
                    observed[c.role]=d['model'];completed.append(c.role)
                    original.write_event(events,{'kind':'IDENTITY_REVIEW','role':c.role,'exact_observed_model':d['model'],
                        'review_basis':'fixed_metadata_family_and_bounded_deployment_version_descriptor',
                        'exact_weights_verified':False},token)
                except Exception:
                    if ledger.entries[identity.key]['state']=='RESERVED' and not ledger.persistence_failed:
                        ledger.uncertain(identity,'CONTINUATION_UNRESOLVED')
                    ledger.halted=True;raise
        terminal={'status':'FIVE_ROLE_COMPATIBILITY_COMPLETE','completed_roles':completed,
                  'prior_calls':1,'new_calls':4,'total_calls':5,'repeated_roles':[],
                  'total_reference_cost_nanodollars':review['prior_reference_cost_nanodollars']+ledger.exposure,
                  'observed_model_names':observed,'actual_billing_certified':False,'study_authorized':False}
    except Exception as e:
        terminal={'status':'STOPPED_NO_RETRY','failure_type':type(e).__name__,'completed_roles':completed,
                  'prior_calls':1,'new_calls_reserved':len(ledger.entries),'repeated_roles':[],
                  'total_reference_exposure_nanodollars':review['prior_reference_cost_nanodollars']+ledger.exposure,
                  'study_authorized':False}
    finally:ledger.close()
    with (out/'terminal.pending').open('xb') as f:f.write(canonical(terminal));f.flush();os.fsync(f.fileno())
    os.rename(out/'terminal.pending',out/'terminal.json')
    return terminal


def main(argv=None):
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--continue-unused-roles',action='store_true');args=p.parse_args(argv)
    if not args.continue_unused_roles:print('HELD: approved continuation record required');return 2
    approval=json.loads((PACKAGE/'CONTINUATION_AUTHORIZATION.json').read_bytes())
    source=(PACKAGE/'source_manifest.json').read_bytes()
    if (approval.get('status')!='APPROVED_BY_USER' or approval.get('scope')!='FOUR_UNUSED_ROLES_NO_ROUTER_RETRY'
            or approval.get('source_manifest_sha256')!=hashlib.sha256(source).hexdigest()
            or approval.get('cap_nanodollars')!=10**9 or approval.get('maximum_new_calls')!=4
            or not approval.get('human_message')):raise DispatchHeld('Continuation authorization mismatch')
    manifest=json.loads(source)
    required={str((ROOT/p).resolve()) for p in REQUIRED_SOURCES}
    paths=[str(Path(r['path']).resolve()) for r in manifest['files']]
    if len(paths)!=len(required) or set(paths)!=required:raise DispatchHeld('Source membership mismatch')
    for row in manifest['files']:
        f=Path(row['path'])
        if f.stat().st_size!=row['size_bytes'] or hashlib.sha256(f.read_bytes()).hexdigest()!=row['sha256']:
            raise DispatchHeld('Frozen continuation source changed')
    validate_prior_evidence(approval.get('prior_evidence'))
    prior_router(PRIOR)
    spec=importlib.util.spec_from_file_location('continuation_key_reader',ROOT/'scripts/matched_baseline/inspect_databricks_metadata.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.no_alias(PACKAGE/'attempt')
    if (PACKAGE/'attempt').exists():raise DispatchHeld('Continuation already used; no retry')
    token=m.load_token(ROOT/'.env.terra-databricks.local')
    try:
        import ssl
        from http.client import HTTPSConnection
        terminal=execute_remaining(lambda c:HTTPSConnection(original.HOST,timeout=c.timeout_seconds,context=ssl.create_default_context()),
                                   token,PACKAGE/'attempt',PRIOR)
    finally:token=None
    print('Continuation outcome:',terminal['status']);print('Evidence:',PACKAGE/'attempt')
    return 0 if terminal['status']=='FIVE_ROLE_COMPATIBILITY_COMPLETE' else 1


if __name__=='__main__':
    try:code=main()
    except Exception as e:print('Continuation held/stopped:',type(e).__name__);code=2
    raise SystemExit(code)
