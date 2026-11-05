"""One final UNUSED GPT-OSS call, following four preserved settled role calls."""
import hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from scripts.matched_baseline import provider_compatibility_smoke as original
from scripts.matched_baseline import provider_smoke_continuation as continuation
from scripts.matched_baseline.provider_accounting import BudgetJournal,CallIdentity,canonical,parse_envelope,accepted_result,ContractError,DispatchHeld
from scripts.matched_baseline.provider_run_control import _exchange,_no_reparse
from scripts.matched_baseline.paired_prompt_workflow import messages,parsed_content

PACKAGE=ROOT/'reports/provider_smoke_final_role_20261024_01'
PRIOR1=original.PACKAGE/'attempt'
PRIOR2=continuation.PACKAGE/'attempt'
REQUIRED_SOURCES=continuation.REQUIRED_SOURCES+('scripts/matched_baseline/provider_smoke_final_role.py',)


def prior_state(prior1,prior2):
    router=continuation.prior_router(prior1)
    ledger=[json.loads(x) for x in (prior2/'calls.jsonl').read_bytes().splitlines()]
    events=[json.loads(x) for x in (prior2/'events.jsonl').read_bytes().splitlines()]
    reserves=[x for x in ledger if x['kind']=='RESERVE'];settles=[x for x in ledger if x['kind']=='SETTLE']
    expected={'COMPATIBILITY_001:H:'+s for s in ('verifier','generator','judge1')}
    if (len(reserves)!=3 or len(settles)!=3 or {x['key'] for x in reserves}!=expected
            or {x['key'] for x in settles}!=expected or any(x['envelope_violation'] for x in settles)
            or [x['sequence'] for x in ledger]!=list(range(len(ledger)))):
        raise DispatchHeld('Exactly three additional settled roles required')
    responses={e['role']:e for e in events if e['kind']=='RESPONSE'}
    if set(responses)!={'verifier','generator','judge1'}:raise DispatchHeld('Prior response roles mismatch')
    for role,reply in responses.items():
        entry=next(x for x in settles if x['key'].endswith(':'+role))
        if reply['response_sha256']!=entry['response_sha256'] or reply['finish_reason']!='stop':
            raise DispatchHeld('Prior response identity mismatch')
        parsed_content(role,reply['content'])
    if responses['judge1']['model']!='qwen3-next-instruct-091725':raise DispatchHeld('Qwen descriptor review differs')
    # Exact abbreviated Qwen deployment descriptor is linked to the previously
    # authenticated fixed endpoint metadata; no parameter/weight equivalence claim.
    models={'router':router['model'],**{s:r['model'] for s,r in responses.items()}}
    cost=router['prior_reference_cost_nanodollars']+sum(x['cost'] for x in settles)
    if type(cost) is not int or not 0<=cost<10**9:raise DispatchHeld('Prior costs exceed cap')
    return cost,responses['generator']['content'],models


def execute_final(factory,token,out,prior1,prior2):
    previous,answer,models=prior_state(prior1,prior2)
    out=Path(out);out.mkdir()
    with (out/'single_final_role.lock').open('xb') as f:f.write(b'ONE_UNUSED_GPT_ROLE_ONLY\n');f.flush();os.fsync(f.fileno())
    c=original.configs()[4];identity=CallIdentity('COMPATIBILITY_001','H','judge2')
    ledger=BudgetJournal(out/'calls.jsonl',10**9-previous,1)
    try:
        with (out/'events.jsonl').open('xb') as events:
            msgs=messages('judge2',original.QUERY,original.EVIDENCE,answer)
            body={'messages':[{'role':r,'content':v} for r,v in msgs],
                  'temperature':0,'max_tokens':4096,'stream':False,'reasoning_effort':'low'}
            request=canonical(body)
            if len(request)>8192:raise ContractError('Request bound')
            ledger.reserve(identity,c,request,None)
            original.write_event(events,{'kind':'REQUEST','role':'judge2','payload':body},token)
            raw=_exchange(factory(c),c,request,token,time.monotonic,lambda:False)
            original.write_event(events,{'kind':'RESPONSE_IDENTITY','role':'judge2','response_sha256':hashlib.sha256(raw).hexdigest()},token)
            d,u,p,co,re=parse_envelope(raw,c)
            ledger.settle(identity,c,original.redact(u,token),p,co,hashlib.sha256(raw).hexdigest(),
                          original.redact({'model':d.get('model'),'id':d.get('id')},token))
            choice=d.get('choices',[{}])
            message=choice[0].get('message',{}) if type(choice) is list and len(choice)==1 and type(choice[0]) is dict else {}
            original.write_event(events,{'kind':'RESPONSE','role':'judge2','model':d.get('model'),
                'content':message.get('content') if type(message) is dict else None,
                'finish_reason':choice[0].get('finish_reason') if type(choice) is list and len(choice)==1 and type(choice[0]) is dict else None,
                'usage':u,'response_sha256':hashlib.sha256(raw).hexdigest()},token)
            if canonical(original.redact(d,token))!=canonical(d):raise ContractError('Credential echo')
            if not continuation.reviewed_descriptor('judge2',d.get('model'),c):raise ContractError('Unexpected model family')
            from dataclasses import replace
            cfg=c if d['model'] in c.accepted_models else replace(c,accepted_models=c.accepted_models+(d['model'],))
            result=accepted_result(d,u,p,co,re,raw,cfg);parsed_content('judge2',result.content)
            models['judge2']=d['model']
        terminal={'status':'FIVE_ROLE_COMPATIBILITY_COMPLETE','total_calls':5,'repeated_calls':0,
            'completed_roles':list(original.ROLES),'observed_model_names':models,
            'total_reference_cost_nanodollars':previous+ledger.exposure,'actual_billing_certified':False,
            'study_authorized':False}
    except Exception as e:
        if identity.key in ledger.entries and ledger.entries[identity.key]['state']=='RESERVED' and not ledger.persistence_failed:
            ledger.uncertain(identity,'FINAL_ROLE_UNRESOLVED')
        terminal={'status':'STOPPED_NO_RETRY','failure_type':type(e).__name__,
                  'prior_calls':4,'new_calls_reserved':len(ledger.entries),'study_authorized':False}
    finally:ledger.close()
    with (out/'terminal.pending').open('xb') as f:f.write(canonical(terminal));f.flush();os.fsync(f.fileno())
    os.rename(out/'terminal.pending',out/'terminal.json')
    return terminal


def main(argv=None):
    import argparse,importlib.util
    p=argparse.ArgumentParser();p.add_argument('--complete-unused-judge',action='store_true');a=p.parse_args(argv)
    if not a.complete_unused_judge:print('HELD: one unused role only');return 2
    raw=(PACKAGE/'source_manifest.json').read_bytes();manifest=json.loads(raw)
    auth=json.loads((PACKAGE/'AUTHORIZATION.json').read_bytes())
    if (auth.get('scope')!='ONE_UNUSED_JUDGE2_NO_REPEAT' or auth.get('status')!='APPROVED_BY_USER'
            or auth.get('source_manifest_sha256')!=hashlib.sha256(raw).hexdigest()
            or auth.get('max_new_calls')!=1 or auth.get('cumulative_cap_nanodollars')!=10**9):
        raise DispatchHeld('Final role authority mismatch')
    paths=[str(Path(r['path']).resolve()) for r in manifest['files']]
    expected={str((ROOT/n).resolve()) for n in REQUIRED_SOURCES}
    if len(paths)!=len(expected) or set(paths)!=expected:raise DispatchHeld('Source membership mismatch')
    for row in manifest['files']:
        path=Path(row['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise DispatchHeld('Source changed')
    expected_prior={str((base/n).resolve()) for base in (PRIOR1,PRIOR2) for n in ('terminal.json','calls.jsonl','events.jsonl')}
    records=auth.get('prior_evidence',[]);actual=[str(Path(r['path']).resolve()) for r in records]
    if len(actual)!=6 or set(actual)!=expected_prior:raise DispatchHeld('Prior receipt membership mismatch')
    for row in records:
        path=Path(row['path']);_no_reparse(path)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise DispatchHeld('Prior receipt changed')
    prior_state(PRIOR1,PRIOR2)
    spec=importlib.util.spec_from_file_location('final_key_reader',ROOT/'scripts/matched_baseline/inspect_databricks_metadata.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.no_alias(PACKAGE/'attempt')
    if (PACKAGE/'attempt').exists():raise DispatchHeld('Final call already used')
    token=m.load_token(ROOT/'.env.terra-databricks.local')
    try:
        import ssl
        from http.client import HTTPSConnection
        terminal=execute_final(lambda c:HTTPSConnection(original.HOST,timeout=120,context=ssl.create_default_context()),
                               token,PACKAGE/'attempt',PRIOR1,PRIOR2)
    finally:token=None
    print('Final smoke outcome:',terminal['status']);print('Evidence:',PACKAGE/'attempt')
    return 0 if terminal['status']=='FIVE_ROLE_COMPATIBILITY_COMPLETE' else 1


if __name__=='__main__':
    try:code=main()
    except Exception as e:print('Final role held/stopped:',type(e).__name__);code=2
    raise SystemExit(code)
