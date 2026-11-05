"""Static transport tests; recorded failure fixture is historical provider data.

No real tokenizers, models, credentials, accounts, sockets or native Jobs.
"""
import copy,json,hashlib,tempfile,unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from tests import test_paired_study_runtime_synthetic as runtime_fixtures
from scripts.matched_baseline.paired_output_format import ENDPOINTS,output_format,output_contract
from scripts.matched_baseline.paired_dependency_bridge import measure_request
from scripts.matched_baseline.provider_accounting import CallIdentity,ContractError,canonical,BudgetJournal
from scripts.matched_baseline.paired_prompt_workflow import parsed_content
from scripts.matched_baseline.paired_study_runtime import validate_composed_result,StudyQuery

class StructuredOutputTests(unittest.TestCase):
    def fixture(self):
        f=runtime_fixtures.RuntimeTests('runTest');f.setUp();self.addCleanup(f.doCleanups)
        f.f.configs={role:replace(cfg,endpoint=ENDPOINTS[role]) for role,cfg in f.f.configs.items()}
        old=f.f.tokenizers['judge2'].apply_chat_template
        # Mock-only model-specific parameter support; no authentic template load.
        def mocked_harmony(*args,reasoning_effort=None,**kwargs):
            if reasoning_effort!='low':raise AssertionError('Missing reviewed reasoning policy')
            return old(*args,**kwargs)
        f.f.tokenizers['judge2'].apply_chat_template=mocked_harmony
        return f

    def test_recorded_failure_stays_invalid_without_repair(self):
        p=Path(__file__).parent/'fixtures/paired_verifier_invalid_json_20261024.json'
        fixture=json.loads(p.read_bytes())
        self.assertEqual(hashlib.sha256(fixture['content'].encode()).hexdigest(),fixture['content_sha256'])
        self.assertTrue(fixture['content'].endswith('.""}'))
        with self.assertRaisesRegex(ContractError,'Invalid JSON'):
            parsed_content('verifier',fixture['content'])

    def test_all_roles_actual_http_bytes_and_shared_arm_policy(self):
        f=self.fixture();f.run_study()
        by_stage={}
        for stage,connection in zip(f.factories,f.connections):
            body=json.loads(connection.requests[0][2])
            self.assertEqual(body.get('response_format'),output_format(stage,ENDPOINTS[stage]))
            by_stage.setdefault(stage,[]).append(body.get('response_format'))
        for stage in ('verifier','judge1','judge2'):
            self.assertEqual(len(by_stage[stage]),2)
            self.assertEqual(by_stage[stage][0],by_stage[stage][1])
        self.assertTrue(all(v is None for v in by_stage['generator']))
        self.assertEqual(len(f.connections),9)

    def test_schema_not_falsely_forwarded_to_local_template(self):
        f=self.fixture();observed=[];tok=f.f.tokenizers['judge2']
        original=tok.apply_chat_template
        def render(*a,**kw):observed.append(kw);return original(*a,**kw)
        with patch.object(tok,'apply_chat_template',side_effect=render):
            req=measure_request(CallIdentity('Q001','H','judge2'),f.f.configs['judge2'],tok,'alpha','evidence','answer')
        self.assertNotIn('response_format',observed[0])
        self.assertEqual(observed[0]['reasoning_effort'],'low')
        self.assertIn('response_format',json.loads(req.request))

    def test_persisted_schema_tamper_even_with_recomputed_hashes_rejected(self):
        f=self.fixture();f.run_study();root=f.root
        original=[json.loads(line) for line in (root/'events.jsonl').read_bytes().splitlines()]
        result=json.loads((root/'Q001.json').read_bytes());ledger=BudgetJournal.inspect(root/'calls.jsonl')
        for mutation in ('omit','alter','extra'):
            with self.subTest(mutation=mutation):
                rows=copy.deepcopy(original);entries={}
                for e in ledger['events']:
                    if e['kind']=='RESERVE':entries[e['key']]=dict(e,state='SETTLED')
                request=next(e for e in rows if e['kind']=='HTTP_REQUEST' and e['call']=='Q001:H:verifier')
                body=json.loads(request['raw'])
                if mutation=='omit':body.pop('response_format')
                elif mutation=='alter':body['response_format']['json_schema']['strict']=False
                else:body['unreviewed_flag']=True
                request['raw']=canonical(body).decode();digest=hashlib.sha256(request['raw'].encode()).hexdigest()
                request['request_sha256']=digest;entries[request['call']]['request_sha256']=digest
                next(e for e in rows if e['kind']=='MEASURED_REQUEST' and e['call']==request['call'])['request_sha256']=digest
                with self.assertRaisesRegex(ContractError,'Persisted .*role policy'):
                    validate_composed_result(StudyQuery('Q001','alpha','B_Evolutionary'),result,rows,
                        SimpleNamespace(path=root/'calls.jsonl',entries=entries))

    def test_schema_fresh_copies_null_vocab_and_numeric_bounds(self):
        a=output_format('verifier',ENDPOINTS['verifier']);a['json_schema']['strict']=False
        self.assertTrue(output_format('verifier',ENDPOINTS['verifier'])['json_schema']['strict'])
        c=output_contract();c['endpoints'].clear();self.assertEqual(len(output_contract()['endpoints']),5)
        self.assertIsNone(parsed_content('judge1','{"faithfulness":null,"outcome":"EXPLICIT_ABSTENTION","rationale":"unknown"}')['faithfulness'])
        with self.assertRaises(ContractError):parsed_content('judge1','{"faithfulness":1.1,"outcome":"SUBSTANTIVE_ANSWER","rationale":"x"}')
        with self.assertRaises(ContractError):parsed_content('verifier','{"sufficient":true,"reason":"x","extra":1}')

    def test_recorded_bad_content_settles_and_stops_without_retry(self):
        from scripts.matched_baseline.provider_run_control import StaticConnection,HttpFixture
        f=self.fixture();calls=[];original=f.connection
        fixture=json.loads((Path(__file__).parent/'fixtures/paired_verifier_invalid_json_20261024.json').read_bytes())
        def factory(config):
            calls.append(config.role)
            if config.role!='verifier':return original(config)
            body=canonical({'id':'recorded-content-static-envelope','model':'fixture-model',
                'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':fixture['content']}}],
                'usage':{'prompt_tokens':10,'completion_tokens':10,'total_tokens':20}})
            return StaticConnection(HttpFixture(body=body))
        with self.assertRaisesRegex(ContractError,'Invalid JSON'):f.run_study(connection_factory=factory)
        ledger=BudgetJournal.inspect(f.root/'calls.jsonl')
        self.assertEqual(calls,['router','verifier'])
        self.assertEqual(list(ledger['states'].values()),['SETTLE','SETTLE'])
        self.assertEqual(json.loads((f.root/'terminal.json').read_bytes())['completed_count'],0)

if __name__=='__main__':unittest.main()
