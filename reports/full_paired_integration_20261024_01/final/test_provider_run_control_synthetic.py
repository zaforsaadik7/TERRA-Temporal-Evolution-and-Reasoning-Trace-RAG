"""Static HTTP objects and temporary run directories, never real sockets/assets."""
from dataclasses import replace
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.matched_baseline.provider_accounting import (
    BudgetJournal, CallIdentity, ContractError, DispatchHeld, Price, RoleConfig, canonical,
)
from scripts.matched_baseline.provider_run_control import (
    EndpointLimiter, EndpointQuota, RateWait, HttpFixture, StaticConnection,
    SyntheticRunStore, StaticCallSession, _exchange, create_live_connection, run_live_study,
)


class ProviderRunControlSynthetic(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.cfg=RoleConfig('generator','https://synthetic.invalid','shared-fixture',('model-fixture',),
            10000,1000,100,20000,20000,30,Price('SYNTHETIC_ONLY',10**9,2*10**9,True))
        self.identity=CallIdentity('Q001','H','generator')
        self.quota=EndpointQuota(10000,1000,100)
        self.messages=(('user','synthetic question'),)
        self.clock=lambda:100.0
        self.journal=BudgetJournal(self.root/'ledger.jsonl',10**9,10)
        self.addCleanup(self.journal.close)
        self.store=SyntheticRunStore(self.root/'run',('Q001',))
        self.addCleanup(lambda:self.store.fail('TEST_FINALIZER'))
        self.limiter=EndpointLimiter()
        self.session=StaticCallSession(self.journal,self.store,self.limiter,self.clock)

    def body(self, **updates):
        d={'id':'fixture-response','model':'model-fixture',
           'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'fixture answer'}}],
           'usage':{'prompt_tokens':50,'completion_tokens':10,'total_tokens':60}}
        d.update(updates)
        return canonical(d)

    def conn(self, **kw): return StaticConnection(HttpFixture(body=self.body(),**kw))

    def invoke(self, conn=None, **kwargs):
        c=conn or self.conn()
        return self.session.invoke(self.identity,self.cfg,self.messages,40,self.quota,c,**kwargs)

    def events(self):
        return [json.loads(x) for x in (self.store.root/'events.jsonl').read_text().splitlines()]

    def pair_result(self):
        from dataclasses import asdict
        from scripts.matched_baseline.common_serializer import CommonSerializer, MockBpeTokenizer
        from scripts.matched_baseline.paired_prompt_workflow import FixtureQuery, RouteEvidence, run_fixture_pair
        from scripts.matched_baseline.provider_accounting import SyntheticResponse
        q=FixtureQuery('Q001','synthetic question','A_Factual')
        p=CommonSerializer(MockBpeTokenizer()).pack_and_serialize('fixture',q.query_text,[])
        roles=('router','generator','verifier','judge1','judge2')
        configs=tuple(replace(self.cfg,role=r) for r in roles)
        responses={}
        for arm,stage in [('shared','router')]+[(a,s) for a in ('H','T') for s in ('verifier','generator','judge1','judge2')]:
            content=({'route':'HARD'} if stage=='router' else
                     {'sufficient':True,'reason':'synthetic'} if stage=='verifier' else
                     'fixture answer' if stage=='generator' else
                     {'faithfulness':1,'outcome':'SUBSTANTIVE_ANSWER','rationale':'synthetic'})
            body=json.loads(self.body())
            body['choices'][0]['message']['content']=canonical(content).decode().strip() if type(content) is dict else content
            responses['Q001:'+arm+':'+stage]=SyntheticResponse(200,canonical(body))
        self.session.study_quotas={r:self.quota for r in roles}
        result=run_fixture_pair(q,RouteEvidence(p,p,p,p),configs,responses,self.journal,
            self.store.root/'Q001.trace.jsonl',http_session=self.session,aggregate_limit_bytes=128*1024**2)
        return asdict(result)

    def remaining_pair_calls(self):
        identities=[CallIdentity('Q001','shared','router')]
        identities += [CallIdentity('Q001',arm,stage) for arm in ('H','T')
                       for stage in ('verifier','generator','judge1','judge2')]
        for identity in identities:
            if identity.key not in self.journal.entries:
                cfg=replace(self.cfg,role=identity.stage)
                self.session.invoke(identity,cfg,self.messages,40,self.quota,self.conn())

    def test_single_post_exact_path_and_usage_settled(self):
        c=self.conn(); result=self.invoke(c)
        self.assertEqual(len(c.requests),1)
        self.assertEqual(c.requests[0][0:2],('POST','/serving-endpoints/shared-fixture/invocations'))
        self.assertTrue(c.closed)
        self.assertEqual(result.prompt_tokens,50)
        self.assertEqual(self.journal.exposure,70000)
        response=next(e for e in self.events() if e['kind']=='RESPONSE')
        self.assertEqual(base64.b64decode(response['body_base64']),self.body())

    def test_auth_header_not_persisted(self):
        self.invoke()
        for p in (self.store.root/'events.jsonl',self.journal.path):
            raw=p.read_text()
            self.assertNotIn('Authorization',raw)
            self.assertNotIn('SYNTHETIC_NOT_A_CREDENTIAL',raw)

    def test_redirect_not_followed(self):
        c=self.conn(status=302)
        with self.assertRaises(DispatchHeld): self.invoke(c)
        self.assertEqual(len(c.requests),1)
        self.assertEqual(self.journal.entries[self.identity.key]['state'],'UNCERTAIN')
        self.assertTrue(c.closed)

    def test_429_no_retry_uncertain_charge(self):
        c=self.conn(status=429)
        with self.assertRaises(DispatchHeld): self.invoke(c)
        self.assertEqual(len(c.requests),1)
        self.assertGreater(self.journal.exposure,0)
        self.assertEqual(json.loads((self.store.root/'terminal.json').read_text())['status'],'FAIL')

    def test_timeouts_request_headers_and_body(self):
        for phase in ('request','headers','read'):
            # Fresh independent fixture run/session per possible accepted attempt.
            root=self.root/phase
            j=BudgetJournal(self.root/(phase+'.jsonl'),10**9,10)
            store=SyntheticRunStore(root,('Q001',))
            self.addCleanup(j.close); self.addCleanup(lambda s=store:s.fail('TEST'))
            session=StaticCallSession(j,store,EndpointLimiter(),self.clock)
            c=self.conn(fail_at=phase)
            with self.subTest(phase=phase),self.assertRaises(TimeoutError):
                session.invoke(self.identity,self.cfg,self.messages,40,self.quota,c)
            self.assertEqual(j.entries[self.identity.key]['state'],'UNCERTAIN')
            self.assertTrue(c.closed)

    def test_cancelled_before_post_still_closes_owned_connection(self):
        c=self.conn()
        with self.assertRaises(TimeoutError): self.invoke(c,cancelled=lambda:True)
        self.assertEqual(c.requests,[])
        self.assertTrue(c.closed)
        self.assertTrue(self.journal.halted)

    def test_observed_deadline_stops_after_request(self):
        ticks=iter((0,0,31))
        c=self.conn()
        with self.assertRaises(TimeoutError):
            _exchange(c,self.cfg,b'{}','synthetic',lambda:next(ticks),lambda:False)
        self.assertEqual(len(c.requests),1)
        self.assertTrue(c.closed)

    def test_unknown_content_type_is_uncertain(self):
        with self.assertRaises(ContractError): self.invoke(self.conn(content_type='text/html'))
        self.assertEqual(self.journal.entries[self.identity.key]['state'],'UNCERTAIN')

    def test_oversize_header_stops_before_read(self):
        c=self.conn(content_length='20001')
        with self.assertRaises(ContractError): self.invoke(c)
        self.assertEqual(c.offset,0)

    def test_body_size_without_header_bound(self):
        c=StaticConnection(HttpFixture(body=b'x'*20001))
        with self.assertRaises(ContractError): self.invoke(c)
        self.assertEqual(c.offset,20001)  # one extra byte proves overflow, not unlimited buffering

    def test_length_mismatch_stops(self):
        with self.assertRaises(ContractError): self.invoke(self.conn(content_length='1'))

    def test_invalid_json_preserved_with_uncertain_reservation(self):
        raw=b'not json\xff'
        with self.assertRaises(ContractError): self.invoke(StaticConnection(HttpFixture(body=raw)))
        response=next(e for e in self.events() if e['kind']=='RESPONSE')
        self.assertEqual(base64.b64decode(response['body_base64']),raw)
        self.assertEqual(self.journal.entries[self.identity.key]['state'],'UNCERTAIN')

    def test_unknown_model_usage_settled_before_failure(self):
        c=StaticConnection(HttpFixture(body=self.body(model='different')))
        with self.assertRaises(ContractError): self.invoke(c)
        self.assertEqual(self.journal.exposure,70000)
        self.assertEqual(self.journal.entries[self.identity.key]['state'],'SETTLED')
        self.assertTrue(self.store.terminal)

    def test_no_more_calls_after_failure(self):
        with self.assertRaises(DispatchHeld): self.invoke(self.conn(status=500))
        c=self.conn()
        with self.assertRaises(DispatchHeld): self.invoke(c)
        self.assertEqual(c.requests,[])

    def test_shared_endpoint_combines_generator_verifier_rate(self):
        quota=EndpointQuota(1000,100,100)
        self.limiter.reserve(self.cfg,quota,0)
        verifier=replace(self.cfg,role='verifier')
        with self.assertRaises(RateWait) as wait: self.limiter.reserve(verifier,quota,1)
        self.assertEqual(wait.exception.seconds,59)
        self.limiter.reserve(verifier,quota,60)

    def test_hourly_rate_is_separate_from_tokens(self):
        q=EndpointQuota(100000,100000,1)
        self.limiter.reserve(self.cfg,q,0)
        with self.assertRaises(RateWait) as wait: self.limiter.reserve(self.cfg,q,60)
        self.assertEqual(wait.exception.seconds,3540)
        self.limiter.reserve(self.cfg,q,3600)

    def test_endpoint_conflicting_quotas_and_clock_regression_rejected(self):
        self.limiter.reserve(self.cfg,self.quota,5)
        with self.assertRaises(ContractError): self.limiter.reserve(self.cfg,EndpointQuota(20000,1000,100),6)
        with self.assertRaises(ContractError): self.limiter.reserve(self.cfg,self.quota,4)

    def test_local_rate_wait_no_money_reserved_or_post(self):
        q=EndpointQuota(1000,100,100)
        self.limiter.reserve(self.cfg,q,100)
        c=self.conn()
        with self.assertRaises(RateWait): self.session.invoke(self.identity,self.cfg,self.messages,40,q,c)
        self.assertEqual(self.journal.entries,{})
        self.assertEqual(c.requests,[])
        self.assertFalse(self.store.terminal)

    def test_duplicate_run_directory_rejected_and_lock_retained(self):
        self.store.fail('TEST')
        with self.assertRaises(FileExistsError): SyntheticRunStore(self.store.root,('Q001',))
        self.assertTrue((self.store.root/'single_attempt.lock').is_file())

    def test_pair_result_out_of_order_or_duplicate_rejected(self):
        with self.assertRaises(ContractError): self.store.complete_pair('OTHER',{'query_id':'OTHER'})
        result=self.pair_result()
        self.store.complete_pair('Q001',result)
        with self.assertRaises(ContractError): self.store.complete_pair('Q001',result)

    def test_run_finish_requires_complete_queries_and_settled_attempts(self):
        with self.assertRaises(DispatchHeld): self.store.finish(self.journal)
        result=self.pair_result()
        self.store.complete_pair('Q001',result)
        self.store.finish(self.journal)
        terminal=json.loads((self.store.root/'terminal.json').read_text())
        self.assertEqual(terminal['status'],'SYNTHETIC_COMPLETE')
        self.assertIs(terminal['provider_certified'],False)
        with self.assertRaises(DispatchHeld): self.store.event({'kind':'late'})

    def test_unresolved_attempt_cannot_complete_run(self):
        result=self.pair_result()
        self.store.complete_pair('Q001',result)
        self.journal.reserve(CallIdentity('Q002','H','generator'),self.cfg,b'{}',40)
        with self.assertRaises(DispatchHeld): self.store.finish(self.journal)

    def test_terminal_space_reserved_when_event_budget_exhausted(self):
        store=SyntheticRunStore(self.root/'small',('Q001',),byte_cap=8192)
        with self.assertRaises(ContractError): store.event({'large':'x'*5000})
        store.fail('EVIDENCE_LIMIT')
        self.assertTrue((store.root/'terminal.json').is_file())

    def test_persistence_error_before_post_prevents_request(self):
        c=self.conn()
        real_event=self.store.event
        def event(value):
            if value['kind']=='REQUEST': raise OSError('fixture only')
            return real_event(value)
        with patch.object(self.store,'event',side_effect=event):
            with self.assertRaises(OSError): self.invoke(c)
        self.assertEqual(c.requests,[])
        self.assertTrue(self.journal.halted)

    def test_real_factory_runner_and_nonstatic_connections_held(self):
        with self.assertRaises(DispatchHeld): create_live_connection(self.cfg)
        with self.assertRaises(DispatchHeld): run_live_study()
        with self.assertRaises(DispatchHeld): self.invoke(object())
        self.assertEqual(self.journal.entries,{})

    def test_missing_calls_cannot_be_hidden_by_complete_query_file(self):
        with self.assertRaises(ContractError):
            self.store.complete_pair('Q001',{'query_id':'Q001','arm_h':{'verifier_passed':True},'arm_t':{'verifier_passed':True}})

    def test_missing_explicit_arm_outcomes_rejected(self):
        with self.assertRaises(ContractError): self.store.complete_pair('Q001',{'query_id':'Q001'})

    def test_host_case_does_not_split_endpoint_quota(self):
        q=EndpointQuota(1000,100,100)
        self.limiter.reserve(self.cfg,q,0)
        other=replace(self.cfg,workspace_origin='https://SYNTHETIC.INVALID/')
        with self.assertRaises(RateWait): self.limiter.reserve(other,q,1)

    def test_spend_rejection_never_posts(self):
        tiny=BudgetJournal(self.root/'tiny.jsonl',1,10)
        self.addCleanup(tiny.close)
        session=StaticCallSession(tiny,self.store,self.limiter,self.clock)
        c=self.conn()
        with self.assertRaises(DispatchHeld): session.invoke(self.identity,self.cfg,self.messages,40,self.quota,c)
        self.assertEqual(c.requests,[])
        self.assertTrue(c.closed)

    def test_remaining_timeout_updated_before_each_read(self):
        ticks=iter((0,0,1,2,3,4,5,6))
        c=self.conn()
        raw=_exchange(c,self.cfg,b'{}','synthetic',lambda:next(ticks),lambda:False)
        self.assertEqual(raw,self.body())
        self.assertEqual(c.timeout,24)


if __name__=='__main__': unittest.main()
