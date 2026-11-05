"""Temporary request/report plus fake job; never launches real processes."""
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from scripts.matched_baseline.offline_smoke_dispatch import SmokeChildDispatcher
from scripts.matched_baseline.offline_smoke_process import SmokeProcessSupervisor
from scripts.matched_baseline.offline_smoke_lifecycle import ChildExecutionFailure
from scripts.matched_baseline.offline_smoke_child_entry import execute_synthetic_request
from tests import test_offline_smoke_child_entry_synthetic as entry_fixture
from tests.test_offline_smoke_process_synthetic import FakeJob


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        fixture = entry_fixture.EntryTests(); fixture.setUp()
        self.payload = fixture.payload
        (self.root/'child_request.json').write_bytes(fixture.raw)
        self.report = execute_synthetic_request(fixture.raw,**fixture.kwargs)
        (self.root/'child_report.json').write_text(json.dumps(self.report))
        from scripts.matched_baseline.offline_preflight import IsolationReceipt
        self.receipt = IsolationReceipt(**self.payload['isolation_receipt'])
        limits = self.payload['limits']
        self.config = SimpleNamespace(command=('fake-python','--request',str(self.root/'child_request.json')),
            query_id=self.payload['query_id'],query_text_sha256=self.payload['query_text_sha256'],
            authorization_id=self.payload['authorization_id'],authorization_sha256=self.payload['authorization_sha256'],
            pins=tuple(self.payload['protected_pins'].items()),scope=self.payload['scope'],
            expected_documents=self.payload['expected_documents'],**limits)
        self.backend = FakeJob()
        self.backend.states[0]['output_bytes'] = 0
        supervisor = SmokeProcessSupervisor(self.backend,clock=lambda:0,pause=lambda s:None,
            timeout_seconds=limits['timeout_seconds'],memory_bytes=limits['memory_bytes'])
        supervisor.output_limit_bytes = limits['output_limit_bytes']
        self.dispatch = SmokeChildDispatcher(supervisor)

    def test_valid_report_after_confirmed_exit(self):
        result = self.dispatch(self.receipt,self.root/'output.log',self.config,{})
        self.assertTrue(result.termination_confirmed)
        self.assertEqual(result.exit_code,0)

    def test_exit_zero_without_report_is_failure_with_confirmed_cleanup(self):
        (self.root/'child_report.json').unlink()
        with self.assertRaisesRegex(ChildExecutionFailure,'report rejected') as ctx:
            self.dispatch(self.receipt,self.root/'output.log',self.config,{})
        self.assertTrue(ctx.exception.result.termination_confirmed)

    def test_request_mismatch_prevents_job_creation(self):
        self.config.query_id = 'wrong'
        with self.assertRaisesRegex(ValueError,'context mismatch'):
            self.dispatch(self.receipt,self.root/'output.log',self.config,{})
        self.assertEqual(self.backend.events,[])

    def test_wrong_population_report_rejected_after_exit_zero(self):
        self.report['documents'] = 2
        (self.root/'child_report.json').write_text(json.dumps(self.report))
        with self.assertRaisesRegex(ChildExecutionFailure,'frozen document population'):
            self.dispatch(self.receipt,self.root/'output.log',self.config,{})

    def test_request_limits_mismatch_prevents_job_creation(self):
        self.payload['limits']['memory_bytes'] += 1
        (self.root/'child_request.json').write_text(json.dumps(self.payload))
        with self.assertRaisesRegex(ValueError,'context mismatch'):
            self.dispatch(self.receipt,self.root/'output.log',self.config,{})
        self.assertEqual(self.backend.events,[])
