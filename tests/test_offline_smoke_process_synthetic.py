"""Fake jobs and clocks only; no child processes launched."""
import unittest
from scripts.matched_baseline.offline_smoke_process import SmokeProcessSupervisor, SupervisionFailure


class FakeJob:
    def __init__(self):
        self.events = []
        self.states = [{'active_processes': 0, 'peak_memory_bytes': 12}]
        self.failure = None
        self.confirm = True

    def event(self, name):
        self.events.append(name)
        if self.failure == name:
            raise RuntimeError(name)

    def create_job(self, **kwargs):
        self.event('create_job'); return 'job'
    def create_suspended(self, command, env):
        self.event('create_suspended'); return 'child'
    def pid(self, child): return 42
    def assign(self, job, child): self.event('assign')
    def resume(self, child): self.event('resume')
    def state(self, job, child):
        self.event('state')
        return self.states.pop(0) if len(self.states) > 1 else self.states[0]
    def exit_code(self, child): return 0
    def terminate(self, job, child): self.event('terminate')
    def wait_empty(self, job, child, **kwargs):
        self.event('wait_empty'); return self.confirm
    def close(self, job, child): self.event('close')


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeJob()
        self.tick = 0
        def clock():
            self.tick += 1
            return self.tick
        self.supervisor = SmokeProcessSupervisor(self.backend, clock=clock, pause=lambda n: None,
                                                  timeout_seconds=3, memory_bytes=100)

    def test_assign_before_resume(self):
        result = self.supervisor.run(['fake'], {})
        self.assertTrue(result.termination_confirmed)
        self.assertEqual(self.backend.events[:4], ['create_job','create_suspended','assign','resume'])

    def test_timeout_terminates_tree(self):
        self.backend.states = [{'active_processes': 1, 'peak_memory_bytes': 12}]
        with self.assertRaisesRegex(SupervisionFailure, 'timeout') as ctx:
            self.supervisor.run(['fake'], {})
        self.assertTrue(ctx.exception.result.termination_confirmed)
        self.assertIn('terminate', self.backend.events)
        self.assertIn('wait_empty', self.backend.events)

    def test_assignment_failure_kills_suspended_child(self):
        self.backend.failure = 'assign'
        with self.assertRaisesRegex(SupervisionFailure, 'assign'):
            self.supervisor.run(['fake'], {})
        self.assertNotIn('resume', self.backend.events)
        self.assertIn('terminate', self.backend.events)

    def test_unconfirmed_kill_never_certifies(self):
        self.backend.failure = 'state'
        self.backend.confirm = False
        with self.assertRaises(SupervisionFailure) as ctx:
            self.supervisor.run(['fake'], {})
        self.assertFalse(ctx.exception.result.termination_confirmed)

    def test_memory_event_fails(self):
        self.backend.states = [{'active_processes': 0, 'peak_memory_bytes': 12, 'memory_limit_hit': True}]
        with self.assertRaisesRegex(SupervisionFailure, 'memory'):
            self.supervisor.run(['fake'], {})

    def test_waits_for_descendants(self):
        self.backend.states = [{'active_processes': 1, 'peak_memory_bytes': 12},
                               {'active_processes': 0, 'peak_memory_bytes': 14}]
        result = self.supervisor.run(['fake'], {})
        self.assertEqual(self.backend.events.count('state'), 2)
        self.assertEqual(result.peak_memory_bytes, 14)

    def test_oversized_output_fails_before_success(self):
        self.supervisor.output_limit_bytes = 10
        self.backend.states = [{'active_processes': 0, 'peak_memory_bytes': 12, 'output_bytes': 11}]
        with self.assertRaisesRegex(SupervisionFailure, 'output size limit'):
            self.supervisor.run(['fake'], {})
        self.assertIn('terminate', self.backend.events)

    def test_missing_output_accounting_fails_closed(self):
        self.supervisor.output_limit_bytes = 10
        with self.assertRaisesRegex(SupervisionFailure, 'Missing output'):
            self.supervisor.run(['fake'], {})
