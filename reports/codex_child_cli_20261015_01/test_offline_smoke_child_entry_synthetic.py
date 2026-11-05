"""Bytes and fake worker only; main is called in-process, no child launched."""
import hashlib
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from scripts.matched_baseline.offline_smoke_child_entry import execute_synthetic_request, execute_request_files, execute_injected_cli, main
from tests import test_offline_smoke_request_synthetic as request_fixture


class EntryTests(unittest.TestCase):
    def test_cli_to_file_to_worker_report(self):
        with tempfile.TemporaryDirectory() as folder:
            request = Path(folder)/'child_request.json'
            request.write_bytes(self.raw)
            receipt = execute_injected_cli(['--request',str(request)],
                expected_request_path=str(request),**self.kwargs)
            self.assertEqual(json.loads(Path(receipt['report_path']).read_bytes())['mode'],'SIMULATED')
            self.assertEqual(len(self.calls),2)

    def test_cli_rejects_policy_overrides_and_duplicates_before_io(self):
        for argv in (['--req','x'],['--request','x','--request','y'],
                     ['--request','x','--mode','AUTHENTIC_OFFLINE_FEASIBILITY'],[],
                     ['--request','x','--allow-others']):
            with self.subTest(argv=argv),patch('pathlib.Path.open',side_effect=AssertionError('No I/O')):
                with self.assertRaisesRegex(ValueError,'exact --request'):
                    execute_injected_cli(argv,expected_request_path='unused',**self.kwargs)
        self.assertEqual(self.calls,[])

    def test_cli_wrong_frozen_path_stops_before_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            request = Path(folder)/'child_request.json'
            with self.assertRaisesRegex(ValueError,'frozen path'):
                execute_injected_cli(['--request',str(request)],
                    expected_request_path=str(Path(folder)/'other.json'),**self.kwargs)
            self.assertEqual(self.calls,[])

    def test_cli_production_hold_precedes_argument_access(self):
        with self.assertRaisesRegex(RuntimeError,'not admitted'):
            execute_injected_cli(None,expected_request_path=None,**self.kwargs,is_synthetic=False)

    def authentic_report_fixture(self):
        from scripts.matched_baseline.offline_smoke_request import SmokeChildRequest
        report = execute_synthetic_request(self.raw,**self.kwargs)
        report['mode'] = 'AUTHENTIC_OFFLINE_FEASIBILITY'
        report['execution_facts'] = {
            'retrieval':'LOCAL_DISPOSABLE_STORE','embedding':'LOCAL_PINNED_ONNX',
            'tokenization':'LOCAL_PINNED_TOKENIZERS','routes':'HYPOTHETICAL_EASY_AND_HARD',
            'judge_answer':'SYNTHETIC_PLACEHOLDER','provider_certified':False,'live_api_calls':0}
        return report,SmokeChildRequest.from_bytes(self.raw)

    def test_authentic_label_cannot_self_select_parent_mode(self):
        from scripts.matched_baseline.offline_smoke_report import validate_smoke_report
        report,request = self.authentic_report_fixture()
        with self.assertRaisesRegex(ValueError,'identity/mode'):
            validate_smoke_report(report,request)

    def test_explicit_authentic_contract_retains_hypothetical_disclosure(self):
        from scripts.matched_baseline.offline_smoke_report import validate_smoke_report
        report,request = self.authentic_report_fixture()
        self.assertIs(validate_smoke_report(report,request,
            expected_mode='AUTHENTIC_OFFLINE_FEASIBILITY'),report)
        for key,value in (('judge_answer','REAL_MODEL_ANSWER'),('provider_certified',True),
                          ('live_api_calls',False),('live_api_calls',1)):
            with self.subTest(key=key,value=value):
                modified = {**report,'execution_facts':{**report['execution_facts'],key:value}}
                with self.assertRaisesRegex(ValueError,'disclosure'):
                    validate_smoke_report(modified,request,
                        expected_mode='AUTHENTIC_OFFLINE_FEASIBILITY')

    def test_authentic_contract_requires_all_disclosure_fields(self):
        from scripts.matched_baseline.offline_smoke_report import validate_smoke_report
        report,request = self.authentic_report_fixture()
        del report['execution_facts']['tokenization']
        with self.assertRaisesRegex(ValueError,'disclosure'):
            validate_smoke_report(report,request,expected_mode='AUTHENTIC_OFFLINE_FEASIBILITY')

    def test_file_entry_writes_valid_report_and_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            request = Path(folder)/'child_request.json'
            request.write_bytes(self.raw)
            receipt = execute_request_files(request,**self.kwargs)
            raw = Path(receipt['report_path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),receipt['sha256'])
            self.assertEqual(len(raw),receipt['size_bytes'])
            self.assertEqual(json.loads(raw)['documents'],1)

    def test_file_entry_collision_preserves_report_before_loading(self):
        with tempfile.TemporaryDirectory() as folder:
            request = Path(folder)/'child_request.json'
            request.write_bytes(self.raw)
            report = request.with_name('child_report.json')
            report.write_bytes(b'sentinel')
            with self.assertRaises(FileExistsError):
                execute_request_files(request,**self.kwargs)
            self.assertEqual(report.read_bytes(),b'sentinel')
            self.assertEqual(self.calls,[])

    def test_file_entry_wrong_hash_preserves_failed_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            request = Path(folder)/'child_request.json'
            request.write_bytes(self.raw+b' ')
            with self.assertRaisesRegex(ValueError,'request hash'):
                execute_request_files(request,**self.kwargs)
            self.assertEqual(self.calls,[])
            self.assertEqual(request.with_name('child_report.json').read_bytes(),b'')

    def test_file_entry_production_hold_before_io(self):
        with patch('pathlib.Path.open',side_effect=AssertionError('No I/O')):
            with self.assertRaisesRegex(RuntimeError,'not admitted'):
                execute_request_files(None,**self.kwargs,is_synthetic=False)

    def setUp(self):
        fixture = request_fixture.RequestTests(); fixture.setUp()
        self.payload = fixture.payload
        self.raw = json.dumps(self.payload).encode()
        self.calls = []
        parent = self
        class FakeWorker:
            def run(self, **query):
                parent.calls.append(query)
                result = dict(mode='SIMULATED',scope=parent.payload['scope'],documents=1,
                    dense_candidate_ids=['a'],graph_seed_ids=['a'],graph_audit={'schema_valid':True},
                    query_id=query['query_id'],query_text_sha256=query['expected_query_sha256'])
                result['hypothetical_route_metrics'] = {}
                for route in ('EASY','HARD'):
                    metrics = dict(query_id=query['query_id'],route_name=route,router_fits=True,
                        all_roles_passed=True,router_prompt_tokens=1,arm_t_structural_chars=1)
                    for arm in ('h','t'):
                        for field in ('gen_fits','verifier_fits','judge1_fits','judge2_fits'):
                            metrics[f'arm_{arm}_{field}'] = True
                        for field in ('admitted_count','evidence_tokens','prompt_tokens','verifier_tokens','judge1_tokens','judge2_tokens'):
                            metrics[f'arm_{arm}_{field}'] = 1
                    result['hypothetical_route_metrics'][route] = metrics
                return result
        def loader(request):
            self.calls.append('load')
            return FakeWorker()
        self.kwargs = dict(expected_request_sha256=hashlib.sha256(self.raw).hexdigest(),
                           reviewed_context=self.payload,worker_loader=loader)

    def test_valid_context_dispatches_once(self):
        result = execute_synthetic_request(self.raw,**self.kwargs)
        self.assertEqual(result['mode'],'SIMULATED')
        self.assertEqual(len(self.calls),2)

    def test_wrong_hash_prevents_loading(self):
        with self.assertRaisesRegex(ValueError,'request hash'):
            execute_synthetic_request(self.raw,**{**self.kwargs,'expected_request_sha256':'a'*64})
        self.assertEqual(self.calls,[])

    def test_context_mismatch_prevents_loading(self):
        context = {**self.payload,'authorization_id':'different'}
        with self.assertRaisesRegex(ValueError,'reviewed scope'):
            execute_synthetic_request(self.raw,**{**self.kwargs,'reviewed_context':context})
        self.assertEqual(self.calls,[])

    def test_cli_hold_precedes_file_access(self):
        with patch('builtins.open',side_effect=AssertionError('No file access')),patch('builtins.print'):
            self.assertEqual(main(['--request','nonexistent']),2)

    def test_authentic_dispatch_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'not admitted'):
            execute_synthetic_request(self.raw,**self.kwargs,is_synthetic=False)
        self.assertEqual(self.calls,[])

    def test_incomplete_identity_only_result_rejected(self):
        class IncompleteWorker:
            def run(worker, **query):
                return dict(mode='SIMULATED',scope=self.payload['scope'],query_id=query['query_id'],
                    query_text_sha256=query['expected_query_sha256'])
        with self.assertRaisesRegex(ValueError,'population'):
            execute_synthetic_request(self.raw,**{**self.kwargs,'worker_loader':lambda r:IncompleteWorker()})
