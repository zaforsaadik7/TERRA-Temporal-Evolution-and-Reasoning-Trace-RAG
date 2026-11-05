import json
from pathlib import Path
import tempfile
import unittest
from scripts.matched_baseline.provider_accounting import canonical,DispatchHeld
from scripts.matched_baseline.provider_run_control import StaticConnection,HttpFixture
from scripts.matched_baseline.provider_smoke_final_role import execute_final,prior_state,main


class FinalRoleSynthetic(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.p1=self.root/'p1';self.p2=self.root/'p2';self.p1.mkdir();self.p2.mkdir()
        (self.p1/'terminal.json').write_bytes(canonical({'status':'STOPPED_NO_RETRY','calls_reserved':1}))
        rows=[{'kind':'HEADER'},{'kind':'RESERVE','key':'COMPATIBILITY_001:shared:router'},
              {'kind':'SETTLE','cost':212869,'envelope_violation':False,'response_sha256':'r'}]
        (self.p1/'calls.jsonl').write_bytes(b''.join(canonical(x) for x in rows))
        (self.p1/'events.jsonl').write_bytes(canonical({'kind':'RESPONSE','role':'router','model':'gemma-3-12b-it-060225',
            'finish_reason':'stop','content':'{"route":"EASY"}','response_sha256':'r'}))
        rows=[{'kind':'HEADER','sequence':0}];events=[]
        for i,role in enumerate(('verifier','generator','judge1')):
            key='COMPATIBILITY_001:H:'+role
            rows.extend([{'kind':'RESERVE','key':key,'sequence':2*i+1},
                         {'kind':'SETTLE','key':key,'sequence':2*i+2,'cost':100,'envelope_violation':False,'response_sha256':role}])
            content=({'sufficient':True,'reason':'fixture'} if role=='verifier' else 'Prior fictional answer1900' if role=='generator' else
                     {'faithfulness':1,'outcome':'SUBSTANTIVE_ANSWER','rationale':'fixture'})
            if type(content) is dict:content=canonical(content).decode()
            events.append({'kind':'RESPONSE','role':role,'model':'qwen3-next-instruct-091725' if role=='judge1' else 'meta-llama-3.3-70b-instruct-121024',
                           'finish_reason':'stop','content':content,'response_sha256':role})
        (self.p2/'calls.jsonl').write_bytes(b''.join(canonical(x) for x in rows))
        (self.p2/'events.jsonl').write_bytes(b''.join(canonical(x) for x in events))

    def connection(self,c):
        content={'faithfulness':1,'outcome':'SUBSTANTIVE_ANSWER','rationale':'Supported'}
        return StaticConnection(HttpFixture(body=canonical({'id':'fixture','model':'gpt-oss-120b-080525',
            'usage':{'prompt_tokens':100,'completion_tokens':20,'total_tokens':120},
            'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':canonical(content).decode()}}]})))

    def test_only_one_unused_gpt_call_and_cumulative_cap(self):
        calls=[]
        def factory(c):calls.append(c.role);return self.connection(c)
        t=execute_final(factory,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.p1,self.p2)
        self.assertEqual(t['status'],'FIVE_ROLE_COMPATIBILITY_COMPLETE')
        self.assertEqual(calls,['judge2']);self.assertEqual(t['total_calls'],5);self.assertEqual(t['repeated_calls'],0)
        self.assertLess(t['total_reference_cost_nanodollars'],10**9)

    def test_prior_answer_sent_without_repeating_generation(self):
        conns=[]
        def factory(c):r=self.connection(c);conns.append(r);return r
        execute_final(factory,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.p1,self.p2)
        payload=json.loads(conns[0].requests[0][2]);user=json.loads(payload['messages'][1]['content'])
        self.assertEqual(user['candidate_answer'],'Prior fictional answer1900')

    def test_prior_wrong_qwen_identity_blocks_before_call(self):
        rows=[json.loads(x) for x in (self.p2/'events.jsonl').read_text().splitlines()];rows[-1]['model']='wrong-model'
        (self.p2/'events.jsonl').write_bytes(b''.join(canonical(x) for x in rows))
        with self.assertRaises(DispatchHeld):prior_state(self.p1,self.p2)

    def test_http_failure_no_retry(self):
        calls=[]
        def factory(c):calls.append(c.role);return StaticConnection(HttpFixture(status=429))
        t=execute_final(factory,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.p1,self.p2)
        self.assertEqual(t['status'],'STOPPED_NO_RETRY');self.assertEqual(calls,['judge2'])

    def test_attempt_collision_no_new_call(self):
        execute_final(self.connection,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.p1,self.p2)
        with self.assertRaises(FileExistsError):execute_final(self.connection,'SYNTHETIC_NOT_REAL',self.root/'attempt',self.p1,self.p2)

    def test_default_held(self):self.assertEqual(main([]),2)


if __name__=='__main__':unittest.main()
