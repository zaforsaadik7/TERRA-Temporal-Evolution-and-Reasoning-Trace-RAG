"""Mock Job backend only: no DLLs, native processes, firewall or real clock waits."""
import unittest
from dataclasses import replace
from unittest.mock import Mock
from scripts.matched_baseline.paired_study_supervision import (
    SupervisionPlan, SupervisedStudyDispatch, launch_authentic_study,
)
from scripts.matched_baseline.provider_accounting import ContractError, DispatchHeld


class SupervisionTests(unittest.TestCase):
    def setUp(self):
        self.plan=SupervisionPlan(('fixture-python','fixture-child'),(('MODE','fixture'),),60,1024**3,4096,100)
        self.backend=Mock()
        self.backend.state.return_value=dict(active_processes=0,peak_memory_bytes=100,output_bytes=20)
        self.backend.pid.return_value=123
        self.backend.exit_code.return_value=0

    def dispatcher(self,**updates):
        args=dict(plan=self.plan,reviewed_plan=self.plan,backend=self.backend,
                  clock=lambda:0,pause=lambda _:None)
        args.update(updates)
        return SupervisedStudyDispatch(**args)

    def test_suspended_assignment_order_and_exact_environment(self):
        self.assertTrue(self.dispatcher().run().termination_confirmed)
        names=[c[0] for c in self.backend.mock_calls]
        self.assertLess(names.index('create_suspended'),names.index('assign'))
        self.assertLess(names.index('assign'),names.index('resume'))
        self.backend.create_suspended.assert_called_once_with(list(self.plan.command),dict(self.plan.environment))

    def test_retry_blocked(self):
        d=self.dispatcher();d.run()
        with self.assertRaises(DispatchHeld):d.run()
        self.backend.create_suspended.assert_called_once()

    def test_resource_or_environment_change_rejected_before_launch(self):
        with self.assertRaises(ContractError):
            self.dispatcher(plan=replace(self.plan,timeout_seconds=61))
        self.backend.create_job.assert_not_called()

    def test_nonzero_exit_rejected(self):
        self.backend.exit_code.return_value=1
        with self.assertRaises(DispatchHeld):self.dispatcher().run()

    def test_credentials_not_allowed_in_environment(self):
        with self.assertRaises(ContractError):
            replace(self.plan,environment=(('DATABRICKS_TOKEN','fixture'),))

    def test_live_entry_held_before_backend(self):
        with self.assertRaises(DispatchHeld):launch_authentic_study(backend=self.backend)
        with self.assertRaises(DispatchHeld):self.dispatcher(is_synthetic=False)
        self.backend.create_job.assert_not_called()


if __name__=='__main__':unittest.main()
