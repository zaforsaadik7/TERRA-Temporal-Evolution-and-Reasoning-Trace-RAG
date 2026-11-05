"""Integrate real evidence writer and fake boundary/job; temporary files only."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.matched_baseline.offline_smoke_boundary import OwnedSmokeBoundary, BoundaryReceipt
from scripts.matched_baseline.offline_smoke_evidence import SmokeEvidenceWriter
from scripts.matched_baseline.offline_smoke_lifecycle import SmokeLifecycle
from scripts.matched_baseline.offline_smoke_process import SmokeProcessSupervisor
from tests.test_offline_smoke_boundary_synthetic import FakeBackend
from tests.test_offline_smoke_process_synthetic import FakeJob


class ComponentIntegrationTests(unittest.TestCase):
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
