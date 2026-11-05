"""Integrate real evidence writer and fake boundary/job; temporary files only."""
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from scripts.matched_baseline.offline_smoke_windows_assembly import assemble_windows_dispatch
from tests.test_offline_smoke_windows_job_synthetic import FakeKernel
from tests.test_offline_smoke_windows_capture_synthetic import FakeCaptureKernel

from scripts.matched_baseline.offline_smoke_boundary import OwnedSmokeBoundary, BoundaryReceipt
from scripts.matched_baseline.offline_smoke_evidence import SmokeEvidenceWriter
from scripts.matched_baseline.offline_smoke_lifecycle import SmokeLifecycle
from scripts.matched_baseline.offline_smoke_process import SmokeProcessSupervisor
from tests.test_offline_smoke_boundary_synthetic import FakeBackend
from tests.test_offline_smoke_process_synthetic import FakeJob


class ComponentIntegrationTests(unittest.TestCase):
    def assembly(self, folder):
        class Kernel(FakeKernel,FakeCaptureKernel):
            def __init__(self):
                FakeKernel.__init__(self)
                FakeCaptureKernel.__init__(self)
        kernel = Kernel()
        config = SimpleNamespace(evidence_directory=folder,timeout_seconds=10,
            memory_bytes=1000,output_limit_bytes=2000)
        dispatcher = assemble_windows_dispatch(kernel=kernel,cwd=folder,
            capture_path=Path(folder)/'child_output.log',config=config,
            clock=lambda:0,pause=lambda _:None)
        return kernel,config,dispatcher

    def test_windows_assembly_is_lazy_and_binds_resource_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            kernel,config,dispatcher = self.assembly(folder)
            self.assertEqual(kernel.events,[])
            self.assertEqual(kernel.files,[])
            self.assertEqual(dispatcher.supervisor.memory,1000)
            self.assertEqual(dispatcher.supervisor.timeout,10)
            self.assertEqual(dispatcher.supervisor.output_limit_bytes,2000)

    def test_windows_capture_failure_prevents_process_creation_and_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            kernel,config,dispatcher = self.assembly(folder)
            kernel.fail_output = True
            backend = dispatcher.supervisor.backend
            with self.assertRaisesRegex(RuntimeError,'output'):
                backend.create_suspended(['fake.exe'],{})
            self.assertNotIn('suspended',kernel.events)
            with self.assertRaisesRegex(RuntimeError,'retry'):
                backend.create_suspended(['fake.exe'],{})

    def test_windows_assembly_connects_capture_to_suspended_child(self):
        with tempfile.TemporaryDirectory() as folder:
            kernel,config,dispatcher = self.assembly(folder)
            kernel.GetLastError = lambda:122
            backend = dispatcher.supervisor.backend
            child = backend.create_suspended(['fake.exe'],{'SAFE':'value'})
            try:
                self.assertEqual(child.process_id,42)
                self.assertEqual(kernel.startup_output,101)
                self.assertEqual(kernel.allowlist,[102,101])
                self.assertTrue(kernel.creation_flags & 4)
                self.assertTrue(kernel.creation_flags & 0x80000)
                self.assertNotIn('resume',kernel.events)
            finally:
                backend.close(None,child)
            self.assertTrue(backend.output_capture.closed)

    def test_windows_assembly_rejects_foreign_capture_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            kernel,config,dispatcher = self.assembly(folder)
            config.evidence_directory = str(Path(folder)/'other')
            with self.assertRaisesRegex(ValueError,'directory mismatch'):
                assemble_windows_dispatch(kernel=kernel,cwd=folder,
                    capture_path=Path(folder)/'child_output.log',config=config,
                    clock=lambda:0,pause=lambda _:None)
            self.assertEqual(kernel.events,[])

    def test_windows_assembly_production_hold_precedes_path_access(self):
        with patch('pathlib.Path.resolve',side_effect=AssertionError('No filesystem')):
            with self.assertRaisesRegex(RuntimeError,'not admitted'):
                assemble_windows_dispatch(kernel=None,cwd=None,capture_path=None,
                    config=None,clock=None,pause=None,is_synthetic=False)

    def exercise(self, *, timeout=False, confirm=True, bad_preflight=False):
        with tempfile.TemporaryDirectory() as root:
            writer = SmokeEvidenceWriter(Path(root) / "record")
            backend = FakeBackend()
            if bad_preflight:
                backend.state['administrator'] = False
            receipt = BoundaryReceipt('TERRA_Smoke_integrated_001', 'fake-python', 'owner-001')
            boundary = OwnedSmokeBoundary(backend, receipt)
            job = FakeJob()
            job.confirm = confirm
            if timeout:
                job.states = [{'active_processes': 1, 'peak_memory_bytes': 12}]
            ticks = iter(range(100))
            supervisor = SmokeProcessSupervisor(job, clock=lambda: next(ticks),
                pause=lambda n: None, timeout_seconds=2, memory_bytes=100)
            events = []
            lifecycle = SmokeLifecycle(
                start_record=lambda: writer.start_record({'scope': 'synthetic'}),
                preflight=boundary.preflight, create_boundary=boundary.create,
                verify_boundary=boundary.verify, acquire_lock=lambda: events.append('lock'),
                run_child=lambda: supervisor.run(['fake-child'], {}),
                remove_boundary=boundary.remove, verify_absence=boundary.verify_absence,
                postcheck=lambda: events.append('hash'), close_transcript=writer.close_transcript,
                terminal_record=writer.terminal_record)
            outcome = lifecycle.run()
            saved = json.loads((writer.directory / 'terminal.json').read_text())
            return outcome, saved, backend, job, events

    def test_success_is_simulated_and_recorded_after_close(self):
        outcome, saved, backend, job, events = self.exercise()
        self.assertEqual(outcome.status, 'SIMULATED_SUCCESS')
        self.assertTrue(saved['transcript_closed'])
        self.assertIsNone(backend.rule)
        self.assertEqual(events, ['lock', 'hash'])

    def test_timeout_with_confirmed_termination_records_failure_and_cleans(self):
        outcome, saved, backend, job, events = self.exercise(timeout=True)
        self.assertEqual(saved['status'], 'FAIL')
        self.assertIn('timeout', ' '.join(saved['failures']))
        self.assertIsNone(backend.rule)
        self.assertIn('hash', events)

    def test_timeout_without_confirmation_retains_boundary_and_skips_hash(self):
        outcome, saved, backend, job, events = self.exercise(timeout=True, confirm=False)
        self.assertEqual(outcome.status, 'FAIL')
        self.assertIsNotNone(backend.rule)
        self.assertNotIn('hash', events)
        self.assertIn('BOUNDARY_RETAINED', ' '.join(saved['failures']))

    def test_gate_failure_leaves_lock_and_child_unused(self):
        outcome, saved, backend, job, events = self.exercise(bad_preflight=True)
        self.assertEqual(outcome.status, 'FAIL')
        self.assertNotIn('lock', events)
        self.assertEqual(job.events, [])
        self.assertEqual(backend.operations, [])
