"""Deterministic Windows termination race models. No native functions invoked."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from scripts.matched_baseline.paired_native_job import backend_class
from tests.test_offline_smoke_windows_job_synthetic import FakeKernel
from tests.test_paired_quota_pacing_synthetic import Clock


class TerminationRaceTests(unittest.TestCase):
    def backend(self,kernel):
        clock=Clock()
        return backend_class()(kernel,cwd=Path.cwd(),capture_path=Path.cwd()/'SYNTHETIC_NOT_CREATED.log',
            clock=clock.now,pause=clock.pause)

    def test_kill_error_does_not_hide_observed_empty_tree(self):
        class RaceKernel(FakeKernel):
            def TerminateProcess(self,*args):
                self.alive=False
                return False  # Job kill won the race before explicit root kill.
        k=RaceKernel();b=self.backend(k)
        b.terminate(10,SimpleNamespace(process=20))
        self.assertTrue(b.termination_notes[0]['tree_empty_after_error'])
        self.assertEqual(b.termination_notes[0]['job_active_processes'],0)
        self.assertIn('TerminateProcess',b.termination_notes[0]['operation_message'])

    def test_unknown_tree_remains_error_and_is_not_certified(self):
        class StuckKernel(FakeKernel):
            def TerminateJobObject(self,*args):return False
            def TerminateProcess(self,*args):return False
        k=StuckKernel();b=self.backend(k)
        with self.assertRaises(RuntimeError):b.terminate(10,SimpleNamespace(process=20))
        self.assertFalse(b.termination_notes[0]['tree_empty_after_error'])


if __name__=='__main__':unittest.main()
