"""Fake-kernel ownership tests: no WinDLL/Job/process/firewall is executed."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from scripts.matched_baseline.offline_cohort_contracts import ProposedResources
from scripts.matched_baseline import offline_cohort_native as native
from scripts.matched_baseline.offline_smoke_windows_job import WindowsJobBackend
from scripts.matched_baseline.offline_smoke_boundary import BoundaryReceipt
from scripts.matched_baseline.offline_cohort_lifecycle import OuterLifecycleWatchdog
from tests import test_offline_smoke_windows_job_synthetic as fixtures


class NativeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.time=0.;self.clock=lambda:self.time
        self.kernel=fixtures.FakeKernel()
        self.kernel.GetExitCodeProcess=lambda process,ptr:(setattr(ptr._obj,'value',0) or True)
        self.backend=WindowsJobBackend(self.kernel,cwd=Path.cwd(),clock=self.clock,pause=self.pause)
        original_state=self.backend.state
        self.backend.state=lambda job,child:dict(original_state(job,child),output_bytes=0)
        self.storage=Mock(return_value=dict(evidence_bytes=1,disposable_bytes=10))
        self.resources=replace(ProposedResources(),termination_wait_seconds=1)
        self.owner=native.CohortJobOwner(self.backend,resources=self.resources,storage_observer=self.storage)

    def pause(self,n):self.time+=n
    def launch(self):self.owner.start(('C:\\fixture\\python.exe','-B'),{'SAFE':'fixture'})
    def stopped(self):self.kernel.alive=False;self.kernel.active=0

    def test_launch_is_suspended_assigned_then_resumed_and_single_use(self):
        self.launch()
        self.assertEqual(self.kernel.events[:4],['job','suspended','assign','resume'])
        with self.assertRaises(RuntimeError):self.launch()

    def test_exact_native_state_and_normal_close(self):
        self.launch();state=self.owner.state()
        self.assertFalse(state['root_exited']);self.assertIsNone(state['exit_code'])
        self.assertEqual(state['active_processes'],1)
        self.stopped();state=self.owner.state()
        self.assertTrue(self.owner.confirmed);self.assertEqual(state['exit_code'],0)
        self.owner.close();self.assertTrue(self.owner.closed)

    def test_root_exit_does_not_prove_descendant_exit(self):
        self.launch();self.kernel.alive=False
        self.assertTrue(self.owner.state()['root_exited']);self.assertFalse(self.owner.confirmed)
        with self.assertRaises(RuntimeError):self.owner.close()
        self.assertFalse(any(isinstance(e,tuple) and e[0]=='close' for e in self.kernel.events))

    def test_failed_assignment_cleanup_terminates_unassigned_root(self):
        self.kernel.failed_assignment=True
        with self.assertRaises(RuntimeError):self.launch()
        self.owner.terminate();self.assertTrue(self.owner.wait_empty(timeout_seconds=1))
        self.owner.close()
        self.assertIn('terminate_root',self.kernel.events)

    def test_unknown_wait_and_invalid_counters_fail_closed(self):
        self.launch();self.kernel.WaitForSingleObject=lambda *args:0xffffffff
        with self.assertRaises(RuntimeError):self.owner.state()
        self.kernel.WaitForSingleObject=lambda *args:258
        self.storage.return_value={'evidence_bytes':True,'disposable_bytes':10}
        with self.assertRaises(ValueError):self.owner.state()

    def test_zero_wait_checks_already_empty_job(self):
        self.launch();self.stopped()
        self.assertTrue(self.owner.wait_empty(timeout_seconds=0))
        self.owner.close()

    def test_outer_observer_does_not_close_unknown_job(self):
        self.launch();recovery=Mock()
        observer=native.ControllerActorObserver(self.owner,read_phase=lambda:'SETUP',
            retain_recovery=recovery,baseline_bytes=10)
        self.owner.wait_empty=Mock(return_value=False)
        self.owner.terminate=Mock()
        resources=replace(self.resources,outer_seconds=3,finalization_reserve_seconds=1)
        result=OuterLifecycleWatchdog(resources,clock=self.clock,pause=self.pause).run(observer,outer_started=0)
        self.assertEqual(result['status'],'RECOVERY_REQUIRED')
        self.assertFalse(self.owner.closed);recovery.assert_called_once()

    def test_outer_success_still_requires_child_and_integrity_audit(self):
        self.launch();self.stopped()
        observer=native.ControllerActorObserver(self.owner,read_phase=lambda:'CLEANUP',
            retain_recovery=Mock(),baseline_bytes=10)
        result=OuterLifecycleWatchdog(self.resources,clock=self.clock,pause=self.pause).run(observer,outer_started=0)
        self.assertEqual(result['status'],'ACTOR_SUCCESS_REQUIRES_CHILD_AND_INTEGRITY_AUDIT')
        self.assertTrue(self.owner.closed)

    def test_cohort_boundary_namespace_and_real_factory_held(self):
        receipt=BoundaryReceipt('TERRA_Cohort_FIXTURE_NATIVE','C:\\fixture\\python.exe','TERRA_COHORT_FIXTURE_NATIVE')
        value=native.OwnedCohortBoundary(Mock(),receipt,controller_pid=42)
        self.assertFalse(value.owned)
        for bad in (replace(receipt,name='TERRA_Smoke_FIXTURE_NATIVE'),replace(receipt,owner_tag='other')):
            with self.assertRaises(ValueError):native.OwnedCohortBoundary(Mock(),bad,controller_pid=42)
        with self.assertRaises(RuntimeError):native.CohortJobOwner(None,resources=None,
            storage_observer=None,is_synthetic=False)
        self.assertEqual(native.main(),2)


if __name__=='__main__':unittest.main()
