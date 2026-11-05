import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.matched_baseline.provider_accounting import canonical,DispatchHeld
from scripts.matched_baseline.provider_run_control import StaticConnection,HttpFixture
from scripts.matched_baseline.provider_compatibility_smoke import (
    plan,configs,validate_approval,execute,main,ROLES,verify_manifest_membership,REQUIRED_SOURCES,ROOT,
)


class CompatibilitySmokeSynthetic(unittest.TestCase):
    def response(self,c):
        content=({'route':'EASY'} if c.role=='router' else
                 {'sufficient':True,'reason':'Fictional note states year'} if c.role=='verifier' else
                 'The fictional note states 1900.' if c.role=='generator' else
                 {'faithfulness':1,'outcome':'SUBSTANTIVE_ANSWER','rationale':'Supported by fictional note'})
        if type(content) is dict:content=canonical(content).decode()
        body=canonical({'id':'fixture-'+c.role,'model':c.endpoint,'usage':{
            'prompt_tokens':100,'completion_tokens':20,'total_tokens':120},
            'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':content}}]})
        return StaticConnection(HttpFixture(body=body))

    def test_five_roles_priced_below_proposed_dollar(self):
        p=plan();self.assertEqual(len(p['roles']),5);self.assertEqual(p['automatic_retries'],0)
        self.assertLess(p['maximum_reserved_nanodollars'],10**9)
        self.assertFalse(p['actual_account_rate_confirmed']);self.assertFalse(p['benchmark_queries_used'])

    def test_no_execution_default(self):self.assertEqual(main([]),2)

    def test_approval_missing_or_wrong_binding_rejected(self):
        for a in ({},{'status':'APPROVED_BY_USER'}):
            with self.assertRaises(DispatchHeld):validate_approval(a,'fixture')

    def test_explicit_fixture_approval_fields(self):
        a={'status':'APPROVED_BY_USER','scope':'FIVE_ROLE_COMPATIBILITY_SMOKE',
           'plan_sha256':hashlib.sha256(canonical(plan())).hexdigest(),'source_manifest_sha256':'fixture',
           'max_spend_nanodollars':10**9,'accept_public_rate_ceiling_assumption':True,
           'accept_cooperative_timeout_exception':True,
           'human_message':'SYNTHETIC FIXTURE NOT HUMAN AUTHORITY'}
        validate_approval(a,'fixture')
        a['accept_public_rate_ceiling_assumption']=False
        with self.assertRaises(DispatchHeld):validate_approval(a,'fixture')

    def test_complete_five_static_posts_and_no_secret_logging(self):
        cs=[]
        def factory(c):r=self.response(c);cs.append(r);return r
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'attempt';t=execute(factory,'SYNTHETIC_CREDENTIAL_NOT_REAL',root)
            self.assertEqual(t['status'],'COMPATIBILITY_SMOKE_COMPLETE')
            self.assertEqual(t['completed_roles'],list(ROLES))
            self.assertEqual(len(cs),5);self.assertTrue(all(len(c.requests)==1 and c.closed for c in cs))
            self.assertNotIn('SYNTHETIC_CREDENTIAL_NOT_REAL',(root/'events.jsonl').read_text())
            gpt=json.loads(cs[-1].requests[0][2]);self.assertEqual(gpt['reasoning_effort'],'low')

    def test_failure_stops_without_remaining_roles_or_retry(self):
        cs=[]
        def factory(c):
            r=StaticConnection(HttpFixture(status=429));cs.append(r);return r
        with tempfile.TemporaryDirectory() as d:
            t=execute(factory,'SYNTHETIC_CREDENTIAL_NOT_REAL',Path(d)/'attempt')
            self.assertEqual(t['status'],'STOPPED_NO_RETRY');self.assertEqual(len(cs),1)
            self.assertEqual(t['calls_reserved'],1)

    def test_no_reuse_attempt_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'attempt';execute(self.response,'SYNTHETIC_NOT_REAL',root)
            with self.assertRaises(FileExistsError):execute(self.response,'SYNTHETIC_NOT_REAL',root)

    def test_generated_answer_is_sent_to_both_judges(self):
        cs=[]
        def factory(c):r=self.response(c);cs.append(r);return r
        with tempfile.TemporaryDirectory() as d:execute(factory,'SYNTHETIC_NOT_REAL',Path(d)/'attempt')
        for c in cs[-2:]:
            payload=json.loads(c.requests[0][2]);user=json.loads(payload['messages'][1]['content'])
            self.assertEqual(user['candidate_answer'],'The fictional note states 1900.')

    def test_credential_echo_scrubbed_from_ledger_and_events_then_stops(self):
        secret='SYNTHETIC/CREDENTIAL_NOT_REAL'
        calls=[]
        def factory(c):
            response=self.response(c);d=json.loads(response.fixture.body)
            d['id']=secret;d['usage']['unexpected_echo']=secret
            # Encode slash characters explicitly on the wire to test decoded redaction.
            raw=json.dumps(d).replace('/',r'\u002f').encode()
            result=StaticConnection(HttpFixture(body=raw));calls.append(result);return result
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'attempt';t=execute(factory,secret,root)
            self.assertEqual(t['status'],'STOPPED_NO_RETRY');self.assertEqual(len(calls),1)
            for path in root.iterdir():
                data=path.read_bytes();self.assertNotIn(secret.encode(),data)
                self.assertNotIn(b'SYNTHETIC\\u002fCREDENTIAL_NOT_REAL',data)

    def test_local_bytes_not_claimed_as_measured_tokens(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'attempt';execute(self.response,'SYNTHETIC_NOT_REAL',root)
            rows=[json.loads(x) for x in (root/'calls.jsonl').read_text().splitlines()]
            reserves=[x for x in rows if x['kind']=='RESERVE']
            self.assertTrue(all(x['local_prompt_tokens'] is None and x['input_measurement']=='NOT_MEASURED' for x in reserves))
            self.assertTrue(all(x['request_bytes']>0 for x in reserves))

    def test_manifest_requires_complete_source_membership(self):
        with self.assertRaises(DispatchHeld):verify_manifest_membership({'files':[]})
        manifest={'files':[{'path':str(ROOT/p)} for p in REQUIRED_SOURCES]}
        verify_manifest_membership(manifest)
        manifest['files']=manifest['files'][:-1]
        with self.assertRaises(DispatchHeld):verify_manifest_membership(manifest)
        manifest={'files':[{'path':str(ROOT/p)} for p in REQUIRED_SOURCES]+[{'path':str(ROOT/'.env.terra-databricks.local')}]}
        with self.assertRaises(DispatchHeld):verify_manifest_membership(manifest)

    def test_malformed_usage_keeps_reservation_and_stops(self):
        def factory(c):return StaticConnection(HttpFixture(body=b'{"usage":null}'))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'attempt';t=execute(factory,'SYNTHETIC_NOT_REAL',root)
            self.assertEqual(t['status'],'STOPPED_NO_RETRY');self.assertEqual(t['calls_reserved'],1)
            self.assertGreater(t['reference_priced_exposure_nanodollars'],0)

    def test_excessive_usage_recorded_then_stops(self):
        def factory(c):
            response=self.response(c);data=json.loads(response.fixture.body)
            data['usage']={'prompt_tokens':9000,'completion_tokens':20,'total_tokens':9020}
            return StaticConnection(HttpFixture(body=canonical(data)))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'attempt';t=execute(factory,'SYNTHETIC_NOT_REAL',root)
            self.assertEqual(t['status'],'STOPPED_NO_RETRY');self.assertEqual(t['calls_reserved'],1)

    def test_each_approval_binding_and_timeout_optin_required(self):
        valid={'status':'APPROVED_BY_USER','scope':'FIVE_ROLE_COMPATIBILITY_SMOKE',
           'plan_sha256':hashlib.sha256(canonical(plan())).hexdigest(),'source_manifest_sha256':'fixture',
           'max_spend_nanodollars':10**9,'accept_public_rate_ceiling_assumption':True,
           'accept_cooperative_timeout_exception':True,'human_message':'SYNTHETIC NOT HUMAN AUTHORITY'}
        for key,value in (('plan_sha256','wrong'),('source_manifest_sha256','wrong'),
                          ('accept_cooperative_timeout_exception',False),('max_spend_nanodollars',True)):
            changed=dict(valid);changed[key]=value
            with self.subTest(key=key),self.assertRaises(DispatchHeld):validate_approval(changed,'fixture')

    def test_request_event_failure_prevents_any_post(self):
        called=[]
        def factory(c):called.append(c);return self.response(c)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'attempt'
            with patch('scripts.matched_baseline.provider_compatibility_smoke.write_event',side_effect=OSError('fixture')):
                t=execute(factory,'SYNTHETIC_NOT_REAL',root)
            self.assertEqual(called,[]);self.assertEqual(t['status'],'STOPPED_NO_RETRY')
            self.assertEqual(t['calls_reserved'],1)

    def test_settlement_fsync_failure_stops_and_preserves_ambiguous_tail(self):
        from scripts.matched_baseline.provider_accounting import BudgetJournal
        original=BudgetJournal._append;calls=[]
        def appending(j,event):
            if event['kind']=='SETTLE':
                with patch('os.fsync',side_effect=OSError('fixture')):return original(j,event)
            return original(j,event)
        def factory(c):calls.append(c);return self.response(c)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'attempt'
            with patch.object(BudgetJournal,'_append',appending):t=execute(factory,'SYNTHETIC_NOT_REAL',root)
            self.assertEqual(t['status'],'STOPPED_NO_RETRY');self.assertEqual(len(calls),1)
            rows=[json.loads(x) for x in (root/'calls.jsonl').read_text().splitlines()]
            self.assertEqual([x['sequence'] for x in rows],list(range(len(rows))))


if __name__=='__main__':unittest.main()
