import json,hashlib
from pathlib import Path
import tempfile
import unittest
from scripts.matched_baseline.provider_accounting import canonical,DispatchHeld
from scripts.matched_baseline.provider_run_control import StaticConnection,HttpFixture
from scripts.matched_baseline.provider_smoke_continuation import execute_remaining,prior_router,reviewed_descriptor,validate_prior_evidence,main
from scripts.matched_baseline.provider_compatibility_smoke import configs


class ContinuationSynthetic(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.prior=self.root/'prior';self.prior.mkdir()
        terminal={'status':'STOPPED_NO_RETRY','calls_reserved':1}
        rows=[{'kind':'HEADER'},{'kind':'RESERVE','key':'COMPATIBILITY_001:shared:router'},
              {'kind':'SETTLE','cost':212869,'envelope_violation':False,'response_sha256':'fixture'}]
        events=[{'kind':'RESPONSE','role':'router','model':'gemma-3-12b-it-060225','finish_reason':'stop',
                 'content':'{"route":"EASY"}','response_sha256':'fixture'}]
        (self.prior/'terminal.json').write_bytes(canonical(terminal))
        (self.prior/'calls.jsonl').write_bytes(b''.join(canonical(x) for x in rows))
        (self.prior/'events.jsonl').write_bytes(b''.join(canonical(x) for x in events))
        self.calls=[]

    def factory(self,c):
        self.calls.append(c.role)
        names={'verifier':'meta-llama-3.3-70b-instruct-110124','generator':'meta-llama-3.3-70b-instruct-110124',
               'judge1':'qwen3-next-80b-a3b-instruct-2509','judge2':'gpt-oss-120b-080525'}
        content=({'sufficient':True,'reason':'Fictional evidence'} if c.role=='verifier' else
                 'The fictional note states 1900.' if c.role=='generator' else
                 {'faithfulness':1,'outcome':'SUBSTANTIVE_ANSWER','rationale':'Fictional note supports it'})
        if type(content) is dict:content=canonical(content).decode()
        return StaticConnection(HttpFixture(body=canonical({'id':'fixture-'+c.role,'model':names[c.role],
            'usage':{'prompt_tokens':100,'completion_tokens':20,'total_tokens':120},
            'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':content}}]})))

    def test_four_new_calls_no_router_retry_and_total_cap(self):
        t=execute_remaining(self.factory,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.prior)
        self.assertEqual(t['status'],'FIVE_ROLE_COMPATIBILITY_COMPLETE')
        self.assertEqual(self.calls,['verifier','generator','judge1','judge2'])
        self.assertEqual(t['total_calls'],5);self.assertEqual(t['repeated_roles'],[])
        self.assertLess(t['total_reference_cost_nanodollars'],10**9)

    def test_prior_router_not_replayed(self):
        before=(self.prior/'calls.jsonl').read_bytes()
        execute_remaining(self.factory,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.prior)
        self.assertEqual((self.prior/'calls.jsonl').read_bytes(),before)
        self.assertNotIn('router',self.calls)

    def test_invalid_prior_receipt_stops_before_call(self):
        (self.prior/'terminal.json').write_bytes(canonical({'status':'OTHER','calls_reserved':2}))
        with self.assertRaises(DispatchHeld):execute_remaining(self.factory,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.prior)
        self.assertEqual(self.calls,[])

    def test_descriptor_rule_rejects_other_family_and_arbitrary_suffix(self):
        c=configs()[1]
        self.assertTrue(reviewed_descriptor('verifier','meta-llama-3.3-70b-instruct-110124',c))
        for name in ('llama-3.1-70b-instruct','llama-3.3-8b-instruct','meta-llama-3.3-70b-instruct-evil'):
            self.assertFalse(reviewed_descriptor('verifier',name,c))

    def test_http_failure_no_retry_or_next_role(self):
        def failing(c):self.calls.append(c.role);return StaticConnection(HttpFixture(status=429))
        t=execute_remaining(failing,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.prior)
        self.assertEqual(t['status'],'STOPPED_NO_RETRY');self.assertEqual(self.calls,['verifier'])
        self.assertEqual(t['new_calls_reserved'],1)

    def test_fresh_continuation_cannot_be_reused(self):
        execute_remaining(self.factory,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.prior)
        with self.assertRaises(FileExistsError):execute_remaining(self.factory,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.prior)
        self.assertEqual(len(self.calls),4)

    def test_dummy_secret_not_in_any_artifact(self):
        secret='SYNTHETIC_NOT_REAL'
        execute_remaining(self.factory,secret,self.root/'attempt',self.prior)
        for f in (self.root/'attempt').iterdir():self.assertNotIn(secret.encode(),f.read_bytes())

    def test_no_execute_flag_does_not_run(self):self.assertEqual(main([]),2)

    def test_exact_prior_receipt_membership_and_hashes_required(self):
        pins=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in
              (self.prior/'terminal.json',self.prior/'calls.jsonl',self.prior/'events.jsonl')]
        validate_prior_evidence(pins,self.prior)
        for bad in ([],pins[:-1],[pins[0]]*3,[dict(pins[0],path=str(self.root/'unrelated'))]+pins[1:]):
            with self.assertRaises(DispatchHeld):validate_prior_evidence(bad,self.prior)
        (self.prior/'terminal.json').write_text('{}')
        with self.assertRaises(DispatchHeld):validate_prior_evidence(pins,self.prior)


if __name__=='__main__':unittest.main()
