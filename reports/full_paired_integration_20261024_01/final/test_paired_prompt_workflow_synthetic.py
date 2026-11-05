"""No real assets: synthetic packed evidence, tokens, responses, temporary files."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from scripts.matched_baseline.common_serializer import CommonSerializer, EvidenceItem, MockBpeTokenizer
from scripts.matched_baseline.provider_accounting import (
    BudgetJournal, ContractError, DispatchHeld, Price, RoleConfig, SyntheticResponse, canonical,
)
from scripts.matched_baseline.paired_prompt_workflow import (
    FixtureQuery, RouteEvidence, messages, parsed_content, prompt_contract_sha256,
    run_fixture_pair, run_live_pair,
)
from scripts.matched_baseline.scoring_analyzer import ScoringAnalyzer


class PairedPromptWorkflowSynthetic(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.journal = BudgetJournal(self.root/'ledger.jsonl', 10**12, 9)
        self.addCleanup(self.journal.close)
        self.price = Price('SYNTHETIC_ONLY', 10**9, 2*10**9, True)
        self.configs = tuple(RoleConfig(r,'https://synthetic.invalid',
            'fixture-shared' if r in ('generator','verifier') else 'fixture-'+r,
            ('fixture-model',),100000,50000,4096,1000000,1000000,30,self.price)
            for r in ('router','verifier','generator','judge1','judge2'))
        self.query = FixtureQuery('B001','How did the synthetic precedent develop?','B_Evolutionary')
        serializer = CommonSerializer(MockBpeTokenizer())
        self.packed = serializer.pack_and_serialize('fixture system', self.query.query_text,
            [EvidenceItem('fixture-case','Synthetic Case','1900','A synthetic holding',snippet='Synthetic facts')])
        self.evidence = RouteEvidence(self.packed,self.packed,self.packed,self.packed)
        self.trace = self.root/'pair.jsonl'

    def response(self, content):
        if type(content) is dict: content = canonical(content).decode().strip()
        return SyntheticResponse(200,canonical({'id':'fixture-response','model':'fixture-model',
            'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':content}}],
            'usage':{'prompt_tokens':300,'completion_tokens':30,'total_tokens':330}}))

    def responses(self, route='HARD'):
        rows = {'B001:shared:router':self.response({'route':route})}
        for arm in ('H','T'):
            rows['B001:'+arm+':verifier'] = self.response({'sufficient':True,'reason':'Synthetic support'})
            rows['B001:'+arm+':generator'] = self.response('Synthetic answer [fixture-case].')
            for judge in ('judge1','judge2'):
                rows['B001:'+arm+':'+judge] = self.response({'faithfulness':1 if arm=='T' else 0.5,
                    'outcome':'SUBSTANTIVE_ANSWER','rationale':'Synthetic score'})
        return rows

    def run_pair(self, responses=None, **kwargs):
        return run_fixture_pair(kwargs.pop('query', self.query),kwargs.pop('evidence', self.evidence),
            kwargs.pop('configs', self.configs),responses or self.responses(),self.journal,self.trace,**kwargs)

    def events(self): return [json.loads(x) for x in self.trace.read_text().splitlines()]

    def test_complete_pair_shared_router_nine_calls(self):
        pair = self.run_pair()
        self.assertEqual(len(self.journal.entries),9)
        self.assertEqual(sum(':shared:router' in x for x in self.journal.entries),1)
        self.assertEqual(pair.category,'B')
        self.assertEqual(pair.faithfulness_diff,0.5)
        self.assertEqual(pair.arm_h.router_route,pair.arm_t.router_route)
        self.assertGreater(pair.arm_h.prompt_tokens,0)
        self.assertEqual(self.events()[-1]['kind'],'PAIR_COMPLETE')

    def test_same_evidence_prompt_bytes_equal_across_arms(self):
        self.run_pair()
        reqs={e['call']:e['messages'] for e in self.events() if e['kind']=='REQUEST'}
        for stage in ('verifier','generator'):
            self.assertEqual(reqs['B001:H:'+stage],reqs['B001:T:'+stage])
        for call,msgs in reqs.items():
            raw=json.dumps(msgs)
            self.assertNotIn('B001',raw)
            self.assertNotIn('B_Evolutionary',raw)
            self.assertNotIn('ground_truth',raw)
            self.assertNotIn('Arm_H',raw)
            self.assertNotIn('Arm_T',raw)

    def test_router_receives_query_only(self):
        self.run_pair()
        request=next(e for e in self.events() if e['kind']=='REQUEST')
        payload=json.loads(request['messages'][1][1])
        self.assertEqual(payload,{'query':self.query.query_text})

    def test_verifier_refusal_skips_generator_but_both_judges_run(self):
        rs=self.responses()
        rs['B001:H:verifier']=self.response({'sufficient':False,'reason':'Missing source'})
        del rs['B001:H:generator']
        pair=self.run_pair(rs)
        self.assertEqual(len(self.journal.entries),8)
        self.assertTrue(pair.arm_h.is_refusal)
        self.assertEqual(pair.arm_h.prompt_tokens,0)
        self.assertEqual(pair.arm_h.composite_faithfulness,0.5)
        self.assertIsNotNone(pair.faithfulness_diff)

    def test_null_judge_score_retained_as_missing_pair(self):
        rs=self.responses(); rs['B001:T:judge1']=self.response({
            'faithfulness':None,'outcome':'MIXED_OR_UNCERTAIN','rationale':'Unassessable support'})
        pair=self.run_pair(rs)
        self.assertIsNone(pair.arm_t.composite_faithfulness)
        self.assertIsNone(pair.faithfulness_diff)
        self.assertFalse(pair.arm_t.api_error)
        analyzer=ScoringAnalyzer(bootstrap_resamples=10,randomization_flips=10)
        result=analyzer.analyze_results([pair],expected_manifest_ids={'B001'})
        self.assertEqual(result['status'],'UNAVAILABLE')
        self.assertEqual(result['valid_pairs'],0)
        self.assertEqual(result['missing_pairs'],1)
        self.assertEqual(result['total_cohort_denominator'],1)
        self.assertEqual(result['sensitivity_bounds_mean_diff'],(-0.5,0.5))

    def test_judge_outcome_disagreement_not_keyword_guessed(self):
        rs=self.responses(); rs['B001:T:judge1']=self.response({
            'faithfulness':1,'outcome':'PREMISE_REFUTATION','rationale':'Synthetic'})
        pair=self.run_pair(rs)
        self.assertEqual(pair.arm_t.outcome_type.value,'MIXED_OR_UNCERTAIN')

    def test_bad_router_charged_and_pair_failure_preserved(self):
        rs=self.responses(); rs['B001:shared:router']=self.response({'route':'CATEGORY_B'})
        with self.assertRaises(ContractError): self.run_pair(rs)
        self.assertEqual(len(self.journal.entries),1)
        self.assertEqual(self.journal.entries['B001:shared:router']['state'],'SETTLED')
        self.assertTrue(self.journal.halted)
        self.assertEqual(self.events()[-1]['kind'],'PAIR_FAILED')
        self.assertEqual(self.events()[-2]['kind'],'RESPONSE')

    def test_bad_judge_boolean_score_rejected_after_accounting(self):
        rs=self.responses()
        for arm in ('H','T'):
            rs['B001:'+arm+':judge1']=self.response({
                'faithfulness':True,'outcome':'SUBSTANTIVE_ANSWER','rationale':'bad'})
        with self.assertRaises(ContractError): self.run_pair(rs)
        self.assertTrue(self.journal.halted)
        self.assertGreater(self.journal.exposure,0)

    def test_timeout_is_failure_not_refusal(self):
        rs=self.responses(); rs['B001:shared:router']=SyntheticResponse(200,b'',True)
        with self.assertRaises(DispatchHeld): self.run_pair(rs)
        self.assertEqual(self.events()[-1]['kind'],'PAIR_FAILED')
        self.assertNotIn('result',self.events()[-1])

    def test_trace_collision_prevents_any_calls(self):
        self.trace.write_text('preserve')
        with self.assertRaises(FileExistsError): self.run_pair()
        self.assertEqual(self.journal.entries,{})
        self.assertEqual(self.trace.read_text(),'preserve')

    def test_wrong_query_category_rejected(self):
        with self.assertRaises(ContractError): FixtureQuery('B001','q','B')

    def test_duplicate_role_configuration_rejected(self):
        with self.assertRaises(ContractError): self.run_pair(configs=(self.configs[0],)*5)
        self.assertEqual(self.journal.entries,{})

    def test_verifier_generator_serving_parity(self):
        configs=tuple(replace(c,endpoint='other') if c.role=='verifier' else c for c in self.configs)
        with self.assertRaises(ContractError): self.run_pair(configs=configs)
        self.assertFalse(self.trace.exists())

    def test_missing_fixture_stops_without_inventing_response(self):
        rs=self.responses(); del rs['B001:shared:router']
        with self.assertRaises(ContractError): self.run_pair(rs)
        self.assertEqual(self.journal.entries,{})
        self.assertEqual(self.events()[-1]['kind'],'PAIR_FAILED')

    def test_mutated_packed_hash_rejected(self):
        p=replace(self.packed,content_sha256='0'*64)
        with self.assertRaises(ContractError): self.run_pair(evidence=RouteEvidence(p,p,p,p))
        self.assertEqual(len(self.journal.entries),1)  # router accounted before evidence selection

    def test_route_selects_only_prespecified_fixture(self):
        pair=self.run_pair(self.responses('EASY'))
        self.assertEqual(pair.arm_h.router_route,'EASY')
        self.assertEqual(pair.arm_t.router_route,'EASY')

    def test_same_case_different_information_rejected_before_router(self):
        changed=replace(self.packed.retained_items[0],holding='Changed holding for one arm')
        p=replace(self.packed,retained_items=(changed,))
        with self.assertRaises(ContractError):
            self.run_pair(evidence=RouteEvidence(self.packed,p,self.packed,p))
        self.assertEqual(self.journal.entries,{})
        self.assertFalse(self.trace.exists())

    def test_empty_evidence_is_valid_and_not_auto_credited(self):
        empty=CommonSerializer(MockBpeTokenizer()).pack_and_serialize('fixture',self.query.query_text,[])
        pair=self.run_pair(evidence=RouteEvidence(empty,empty,empty,empty))
        self.assertEqual(pair.arm_h.retained_ids,[])
        self.assertEqual(pair.arm_h.composite_faithfulness,0.5)  # provider fixture score, not inferred 1

    def test_overlong_router_rejected_before_spend(self):
        query=replace(self.query,query_text='word '*2000)
        with self.assertRaises(ContractError): self.run_pair(query=query)
        self.assertEqual(self.journal.entries,{})

    def test_partial_pair_preserved_after_later_stage_failure(self):
        rs=self.responses()
        # Deterministically corrupt the second arm's verifier.
        import hashlib
        first='H' if hashlib.sha256(canonical([42,'B001'])).digest()[0]%2==0 else 'T'
        second='T' if first=='H' else 'H'
        rs['B001:'+second+':verifier']=self.response({'sufficient':'true','reason':'bad type'})
        with self.assertRaises(ContractError): self.run_pair(rs)
        self.assertEqual(len(self.journal.entries),6)  # router + first four stages + second verifier
        self.assertEqual(self.events()[-1]['failed_call'],'B001:'+second+':verifier')
        self.assertTrue(any(e['kind']=='RESPONSE' and e['call']=='B001:'+first+':judge2'
                            for e in self.events()))

    def test_invalid_json_and_unexpected_fields_rejected(self):
        for text in ('{"route":"EASY","route":"HARD"}',
                     '{"route":"EASY","extra":1}', 'not-json'):
            with self.subTest(text=text), self.assertRaises(ContractError): parsed_content('router',text)
        with self.assertRaises(ContractError): parsed_content('unknown','{}')

    def test_judge_does_not_receive_reference_or_other_answer(self):
        a=messages('judge1','synthetic query','synthetic evidence','candidate')
        payload=json.loads(a[1][1])
        self.assertEqual(set(payload),{'query','evidence','candidate_answer'})
        self.assertEqual(a,messages('judge2','synthetic query','synthetic evidence','candidate'))

    def test_prompt_version_digest_and_live_hold(self):
        self.assertEqual(len(prompt_contract_sha256()),64)
        with self.assertRaises(DispatchHeld): run_live_pair()

    def test_primary_adapter_keeps_pair_and_omitted_denominator(self):
        pair=self.run_pair()
        analyzer=ScoringAnalyzer(bootstrap_resamples=10,randomization_flips=10)
        result=analyzer.analyze_results([pair],expected_manifest_ids={'B001','B002'})
        self.assertEqual(result['valid_pairs'],1)
        self.assertEqual(result['omitted_queries'],1)
        self.assertEqual(result['total_cohort_denominator'],2)
        self.assertEqual(result['observed_mean_diff'],0.5)

    def test_execution_order_is_repeatable_from_frozen_seed(self):
        pair=self.run_pair(seed=918)
        journal2=BudgetJournal(self.root/'ledger2.jsonl',10**12,9)
        self.addCleanup(journal2.close)
        other=run_fixture_pair(self.query,self.evidence,self.configs,self.responses(),journal2,
                               self.root/'pair2.jsonl',seed=918)
        self.assertEqual(pair.execution_order,other.execution_order)


if __name__=='__main__': unittest.main()
