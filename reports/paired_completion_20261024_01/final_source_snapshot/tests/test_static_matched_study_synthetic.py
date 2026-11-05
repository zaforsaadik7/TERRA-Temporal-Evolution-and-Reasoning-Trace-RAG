"""Complete synthetic cohort through prompts, HTTP core, accounting and persistence."""
from collections import Counter
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.matched_baseline.common_serializer import CommonSerializer, MockBpeTokenizer
from scripts.matched_baseline.paired_prompt_workflow import FixtureQuery, RouteEvidence, run_fixture_pair
from scripts.matched_baseline.provider_accounting import (
    BudgetJournal, ContractError, DispatchHeld, Price, RoleConfig, SyntheticResponse, canonical,
)
from scripts.matched_baseline.provider_run_control import (
    EndpointQuota, SyntheticRunStore, StaticCallSession, EndpointLimiter, StaticConnection, HttpFixture,
)
from scripts.matched_baseline.static_matched_study import run_static_study, check_aggregate, run_authentic_study


class StaticMatchedStudySynthetic(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.roles=('router','verifier','generator','judge1','judge2')
        self.configs=tuple(RoleConfig(r,'https://synthetic.invalid',
            'fixture-shared' if r in ('generator','verifier') else 'fixture-'+r,
            ('fixture-model',),20000,5000,100,20000,20000,30,
            Price('SYNTHETIC_NOT_APPROVED',10**9,2*10**9,True)) for r in self.roles)
        self.quotas={r:EndpointQuota(100000000,10000000,10000) for r in self.roles}

    def fixture(self, count):
        qs=[]; ev={}; responses={}
        for n in range(count):
            category=('A_Factual' if n<100 else 'B_Evolutionary' if n<200 else
                      'C_OutOfContext' if n<275 else 'D_Adversarial')
            q=FixtureQuery('Q'+str(n).zfill(3),'Synthetic question '+str(n),category); qs.append(q)
            p=CommonSerializer(MockBpeTokenizer()).pack_and_serialize('fixture',q.query_text,[])
            ev[q.query_id]=RouteEvidence(p,p,p,p)
            for arm,stage in [('shared','router')]+[(a,s) for a in ('H','T') for s in ('verifier','generator','judge1','judge2')]:
                content=({'route':'HARD'} if stage=='router' else
                         {'sufficient':True,'reason':'Synthetic support'} if stage=='verifier' else
                         'Synthetic answer' if stage=='generator' else
                         {'faithfulness':1 if arm=='T' else .5,'outcome':'SUBSTANTIVE_ANSWER','rationale':'Synthetic'})
                if type(content) is dict: content=canonical(content).decode().strip()
                responses[q.query_id+':'+arm+':'+stage]=SyntheticResponse(200,canonical({
                    'id':'fixture-'+q.query_id+'-'+arm+'-'+stage,'model':'fixture-model',
                    'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':content}}],
                    'usage':{'prompt_tokens':100,'completion_tokens':20,'total_tokens':120}}))
        return tuple(qs),ev,responses

    def run_study(self,count=1,**kwargs):
        q,e,r=self.fixture(count)
        return run_static_study(self.root/'run',q,e,self.configs,r,self.quotas,
                                spend_cap_nanodollars=10**12,**kwargs)

    def test_full_350_query_3150_call_end_to_end(self):
        # Stress logical composition without thousands of physical disk barriers.
        # Separate small-cohort and injected-fsync tests exercise real barriers/failure.
        with patch('os.fsync') as barrier:
            results=self.run_study(350)
        self.assertGreater(barrier.call_count,3150)
        self.assertEqual(len(results),350)
        self.assertEqual(Counter(r.category for r in results),{'A':100,'B':100,'C':75,'D':75})
        root=self.root/'run'
        terminal=json.loads((root/'terminal.json').read_text())
        manifest=json.loads((root/'artifact_manifest.json').read_text())
        self.assertEqual(terminal['status'],'SYNTHETIC_COMPLETE')
        self.assertEqual(terminal['completed_query_count'],350)
        self.assertEqual(manifest['logical_calls'],3150)
        self.assertFalse(manifest['provider_certified'])
        self.assertTrue(all(r.faithfulness_diff==.5 for r in results))
        inspect=BudgetJournal.inspect(root/'calls.jsonl')
        self.assertEqual(len(inspect['states']),3150)
        self.assertTrue(all(x=='SETTLE' for x in inspect['states'].values()))

    def test_second_query_failure_preserves_first_and_uncertain_bill(self):
        q,e,r=self.fixture(2); r['Q001:shared:router']=SyntheticResponse(429,b'{}')
        with self.assertRaises(DispatchHeld):
            run_static_study(self.root/'run',q,e,self.configs,r,self.quotas,spend_cap_nanodollars=10**12)
        root=self.root/'run'
        self.assertTrue((root/'Q000.json').is_file())
        self.assertFalse((root/'Q001.json').exists())
        self.assertEqual(json.loads((root/'terminal.json').read_text())['status'],'FAIL')
        self.assertFalse((root/'artifact_manifest.json').exists())
        self.assertEqual(BudgetJournal.inspect(root/'calls.jsonl')['states']['Q001:shared:router'],'UNCERTAIN')

    def test_no_resume_or_reexecution_of_existing_root(self):
        self.run_study()
        before=(self.root/'run'/'calls.jsonl').read_bytes()
        with self.assertRaises(FileExistsError): self.run_study()
        self.assertEqual((self.root/'run'/'calls.jsonl').read_bytes(),before)

    def test_aggregate_shortage_stops_before_http(self):
        with self.assertRaises(ContractError): self.run_study(aggregate_limit_bytes=100000)
        events=(self.root/'run'/'events.jsonl').read_text()
        self.assertNotIn('"kind":"REQUEST"',events)
        self.assertEqual(json.loads((self.root/'run'/'terminal.json').read_text())['status'],'FAIL')

    def test_manifest_failure_cannot_leave_success_terminal(self):
        real_open=Path.open
        def opening(path,*args,**kwargs):
            if path.name=='artifact_manifest.json': raise OSError('fixture')
            return real_open(path,*args,**kwargs)
        with patch.object(Path,'open',opening):
            with self.assertRaises(OSError): self.run_study()
        self.assertEqual(json.loads((self.root/'run'/'terminal.json').read_text())['status'],'FAIL')

    def test_exact_evidence_query_manifest_required(self):
        q,e,r=self.fixture(1)
        with self.assertRaises(ContractError):
            run_static_study(self.root/'run',q,{},self.configs,r,self.quotas,spend_cap_nanodollars=10**12)
        self.assertFalse((self.root/'run').exists())

    def test_terminal_summary_bounded_for_350_long_ids(self):
        ids=tuple('Q'+str(i).zfill(3)+'x'*124 for i in range(350))
        store=SyntheticRunStore(self.root/'long',ids,byte_cap=100000)
        store.completed=list(ids)
        store.fail('SYNTHETIC_FAILURE')
        raw=(store.root/'terminal.json').read_bytes()
        self.assertLess(len(raw),4096)
        self.assertEqual(json.loads(raw)['completed_query_count'],350)

    def test_session_settlement_fsync_failure_does_not_append_duplicate_sequence(self):
        store=SyntheticRunStore(self.root/'fsync',('Q000',))
        j=BudgetJournal(store.root/'calls.jsonl',10**12,9)
        self.addCleanup(j.close); self.addCleanup(lambda:store.fail('TEST'))
        session=StaticCallSession(j,store,EndpointLimiter(),lambda:100)
        cfg=next(c for c in self.configs if c.role=='generator')
        q,e,r=self.fixture(1)
        from scripts.matched_baseline.provider_accounting import CallIdentity
        c=StaticConnection(HttpFixture(body=r['Q000:H:generator'].body))
        original=os.fsync; calls=[0]
        def syncing(fd):
            if fd==j.file.fileno():
                calls[0]+=1
                if calls[0]>=2: raise OSError('settlement sync fixture')
            return original(fd)
        with patch('os.fsync',side_effect=syncing):
            with self.assertRaises((OSError,DispatchHeld)):
                session.invoke(CallIdentity('Q000','H','generator'),cfg,(('user','synthetic'),),10,
                               self.quotas['generator'],c)
        self.assertTrue(j.persistence_failed)
        events=[json.loads(x) for x in j.path.read_bytes().splitlines()]
        self.assertEqual([x['sequence'] for x in events],list(range(len(events))))
        self.assertFalse(any(x['kind']=='UNCERTAIN' for x in events))

    def test_same_length_retained_content_change_cannot_reuse_old_prompt_hash(self):
        from scripts.matched_baseline.common_serializer import EvidenceItem
        q,e,r=self.fixture(1)
        packed=CommonSerializer(MockBpeTokenizer()).pack_and_serialize('fixture',q[0].query_text,
            [EvidenceItem('case','Title','1900','original')])
        changed=replace(packed,retained_items=(replace(packed.retained_items[0],holding='modified'),))
        # Original and modified each have one lexical token; token equality alone is insufficient.
        e['Q000']=RouteEvidence(changed,changed,changed,changed)
        with self.assertRaises(ContractError):
            run_static_study(self.root/'run',q,e,self.configs,r,self.quotas,spend_cap_nanodollars=10**12)

    def test_fabricated_pair_dict_cannot_complete_against_saved_responses(self):
        self.run_study()
        root=self.root/'run'
        result=json.loads((root/'Q000.json').read_text()); result['arm_h']['output_text']='fabricated answer'
        from scripts.matched_baseline.paired_result_validation import validate_pair_artifact
        with self.assertRaises(ContractError): validate_pair_artifact(root,'Q000',result)

    def test_authentic_entry_remains_unconditionally_held(self):
        with self.assertRaises(DispatchHeld): run_authentic_study()

    def test_terminal_fsync_failure_leaves_no_committed_success(self):
        original=os.fsync
        real_open=Path.open
        target_fds=set()
        def opening(path,*args,**kwargs):
            f=real_open(path,*args,**kwargs)
            if path.name=='terminal.success.pending': target_fds.add(f.fileno())
            return f
        def syncing(fd):
            if fd in target_fds:
                target_fds.remove(fd)
                raise OSError('terminal sync fixture')
            return original(fd)
        with patch.object(Path,'open',opening),patch('os.fsync',side_effect=syncing):
            with self.assertRaises(OSError): self.run_study()
        root=self.root/'run'
        self.assertTrue((root/'terminal.success.pending').exists())
        self.assertEqual(json.loads((root/'terminal.json').read_text())['status'],'FAIL')

    def test_reserved_and_case_alias_ids_rejected_before_namespace_creation(self):
        for index,ids in enumerate((('terminal',),('artifact_manifest',),('CON',),('Lpt1',),('Q000','q000'))):
            path=self.root/('bad'+str(index))
            with self.subTest(ids=ids),self.assertRaises(ContractError): SyntheticRunStore(path,ids)
            self.assertFalse(path.exists())

    def test_consistent_result_and_final_trace_mutations_still_rejected(self):
        self.run_study()
        root=self.root/'run'; trace=root/'Q000.trace.jsonl'
        original=trace.read_bytes()
        result=json.loads((root/'Q000.json').read_text())
        from scripts.matched_baseline.paired_result_validation import validate_pair_artifact
        mutations=[('category','B'),('execution_order',list(reversed(result['execution_order']))),
                   ('prompt_tokens',123),('evidence_tokens',123),('evidence_sha256','f'*64),
                   ('retained_ids',['fabricated']),('composite_faithfulness',True)]
        for key,value in mutations:
            changed=json.loads(json.dumps(result))
            if key in ('category','execution_order'): changed[key]=value
            else:
                changed['arm_h'][key]=value
                if key=='retained_ids': changed['arm_h']['retrieved_ids']=['fabricated']
            events=[json.loads(x) for x in original.splitlines()]
            events[-1]['result']=changed
            trace.write_bytes(b''.join(canonical(x) for x in events))
            with self.subTest(key=key),self.assertRaises(ContractError):
                validate_pair_artifact(root,'Q000',changed)
        trace.write_bytes(original)

    def test_coordinated_trace_token_change_does_not_override_http_request(self):
        self.run_study()
        root=self.root/'run'; trace=root/'Q000.trace.jsonl'
        events=[json.loads(x) for x in trace.read_bytes().splitlines()]
        result=json.loads((root/'Q000.json').read_text())
        request=next(x for x in events if x['kind']=='REQUEST' and x['call']=='Q000:H:generator')
        request['local_tokens']+=1
        result['arm_h']['prompt_tokens']=request['local_tokens']
        events[-1]['result']=result
        trace.write_bytes(b''.join(canonical(x) for x in events))
        from scripts.matched_baseline.paired_result_validation import validate_pair_artifact
        with self.assertRaises(ContractError): validate_pair_artifact(root,'Q000',result)


if __name__=='__main__': unittest.main()
