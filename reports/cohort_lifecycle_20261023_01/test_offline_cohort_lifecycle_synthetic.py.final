"""Temporary disjoint writers and injected actor/time; no native process."""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from scripts.matched_baseline.offline_cohort_lifecycle import (
    EvidenceAllocation,FixtureEvidenceLease,OuterLifecycleWatchdog,main)
from scripts.matched_baseline.offline_cohort_contracts import ProposedResources
from scripts.matched_baseline.offline_cohort_execution import _run_bound


class AllocationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.p=ProposedResources()
        self.allocation=EvidenceAllocation(str(self.root/'evidence'),32*1024**2,96*1024**2)

    def lease(self):
        return FixtureEvidenceLease(self.allocation,reviewed=self.allocation,
                                   resources=self.p,fixture_root=self.root)

    def test_disjoint_directories_and_total_reserved_once(self):
        lease=self.lease();parent=lease.open_writer('parent');child=lease.open_writer('child')
        self.addCleanup(parent.close);self.addCleanup(child.close)
        parent.write_bytes('parent.json',b'parent',max_bytes=100)
        child.write_bytes('child.json',b'child',max_bytes=100)
        self.assertEqual(parent.budget.limit+child.budget.limit,self.p.evidence_bytes)
        self.assertNotEqual(parent.directory,child.directory)
        self.assertEqual(parent.budget.charged+child.budget.charged,11)
        with self.assertRaises(RuntimeError):lease.open_writer('parent')
        with self.assertRaises(FileExistsError):self.lease()

    def test_bad_split_and_unreviewed_change_fail_before_creation(self):
        for allocation in (replace(self.allocation,parent_bytes=True),
                           replace(self.allocation,child_bytes=self.p.evidence_bytes),
                           replace(self.allocation,parent_bytes=1)):
            with self.assertRaises(ValueError):allocation.validate(reviewed=allocation,resources=self.p)
        with self.assertRaises(ValueError):replace(self.allocation,parent_bytes=self.allocation.parent_bytes+1).validate(
            reviewed=self.allocation,resources=self.p)
        self.assertFalse(Path(self.allocation.root).exists())

    def test_wrong_owner_and_genuine_lease_held(self):
        lease=self.lease()
        with self.assertRaises(ValueError):lease.open_writer('other')
        with self.assertRaises(RuntimeError):FixtureEvidenceLease(None,reviewed=None,
            resources=None,fixture_root=None,is_synthetic=False)

    def test_child_cap_prevents_consuming_parent_reserve(self):
        lease=self.lease();child=lease.open_writer('child');self.addCleanup(child.close)
        stream=child.new_stream('partial.log',max_bytes=5)
        stream.write(b'12345')
        with self.assertRaises(ValueError):stream.write(b'6')
        self.assertEqual((child.directory/'partial.log').read_bytes(),b'12345')
        self.assertEqual(child.budget.limit,self.allocation.child_bytes)

    def test_worker_telemetry_stream_accepts_partitioned_child_budget(self):
        # Fail at mock network-guard entry, AFTER real stream creation. This
        # proves telemetry uses child allocation, not global128MiB artifact cap.
        lease=self.lease();child=lease.open_writer('child')
        guard=Mock(side_effect=RuntimeError('fixture stop before loading'))
        with self.assertRaises(RuntimeError):_run_bound(binding=None,spec=None,plan=None,
            reviewed_plan=None,receipt=None,resources=self.p,runtime={},writer=child,
            clock=None,guard=guard,worker_factory=None)
        self.assertTrue(child.closed)
        self.assertEqual(child.streams[0].limit,self.allocation.child_bytes)
        self.assertTrue((child.directory/'failure.json').exists())


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.p=replace(ProposedResources(),outer_seconds=10,finalization_reserve_seconds=3,
                       child_seconds=5,termination_wait_seconds=2)
        self.now=0.
        self.observer=Mock()
        self.observer.wait_stopped.return_value=True

    def watchdog(self,**kwargs):
        return OuterLifecycleWatchdog(self.p,clock=lambda:self.now,
            pause=lambda delta:setattr(self,'now',self.now+delta),**kwargs)

    def state(self,phase='SETUP',stopped=False,exit_code=None):
        return dict(phase=phase,stopped=stopped,exit_code=exit_code)

    def test_independent_actor_observed_from_setup_through_cleanup(self):
        self.observer.state.side_effect=[self.state('SETUP'),self.state('COPY'),
            self.state('HASH'),self.state('CHILD'),self.state('CLEANUP'),self.state('CLEANUP',True,0)]
        watchdog=self.watchdog();result=watchdog.run(self.observer,outer_started=0.)
        self.assertEqual(result['status'],'ACTOR_SUCCESS_REQUIRES_CHILD_AND_INTEGRITY_AUDIT')
        self.observer.request_shutdown.assert_not_called()
        self.observer.close_observer.assert_called_once()
        with self.assertRaises(RuntimeError):watchdog.run(self.observer,outer_started=0.)

    def test_setup_timeout_requests_stop_with_bounded_wait(self):
        self.now=7.
        result=self.watchdog().run(self.observer,outer_started=0.)
        self.assertEqual(result['status'],'FAIL');self.assertEqual(result['failure_type'],'TimeoutError')
        self.observer.state.assert_not_called()
        self.observer.wait_stopped.assert_called_once_with(timeout_seconds=2)
        self.observer.request_shutdown.assert_called_once_with(reason='TimeoutError')

    def test_late_blocking_observation_cannot_report_success(self):
        def state():self.now=8.;return self.state('CLEANUP',True,0)
        self.observer.state.side_effect=state
        result=self.watchdog().run(self.observer,outer_started=0.)
        self.assertEqual(result['status'],'FAIL')
        self.observer.wait_stopped.assert_called_once_with(timeout_seconds=2)

    def test_confirmed_cleanup_can_use_reserved_outer_time(self):
        count=[]
        def state():
            count.append(1)
            if len(count)==1:self.now=6.;return self.state('CLEANUP')
            self.now=8.;return self.state('CLEANUP',True,0)
        self.observer.state.side_effect=state
        result=self.watchdog().run(self.observer,outer_started=0.)
        self.assertEqual(result['status'],'ACTOR_SUCCESS_REQUIRES_CHILD_AND_INTEGRITY_AUDIT')

    def test_unconfirmed_stop_retains_recovery_not_firewall_delete(self):
        self.now=10.;self.observer.wait_stopped.return_value=False
        result=self.watchdog().run(self.observer,outer_started=0.)
        self.assertEqual(result['status'],'RECOVERY_REQUIRED')
        self.observer.wait_stopped.assert_called_once_with(timeout_seconds=0)
        self.observer.retain_recovery_record.assert_called_once()
        self.observer.remove_owned_rule.assert_not_called()
        self.observer.terminate.assert_not_called()

    def test_invalid_clock_requests_shutdown_and_no_inferred_wait_budget(self):
        self.now=float('nan')
        result=self.watchdog().run(self.observer,outer_started=0.)
        self.assertEqual(result['status'],'FAIL')
        self.observer.wait_stopped.assert_called_once_with(timeout_seconds=0)
        self.assertIsNone(result['elapsed_outer_seconds'])

    def test_phase_regression_and_incomplete_early_exit_fail(self):
        self.observer.state.side_effect=[self.state('HASH'),self.state('COPY')]
        self.assertEqual(self.watchdog().run(self.observer,outer_started=0.)['status'],'FAIL')
        self.observer.state.side_effect=None
        self.observer.state.return_value=self.state('SETUP',True,0)
        self.assertEqual(self.watchdog().run(self.observer,outer_started=0.)['status'],'FAIL')

    def test_shutdown_failure_does_not_skip_wait_or_observer_close(self):
        self.now=7.;self.observer.request_shutdown.side_effect=OSError('not exported')
        result=self.watchdog().run(self.observer,outer_started=0.)
        self.assertEqual(result['status'],'FAIL')
        self.assertEqual(result['cleanup_errors'],['shutdown:OSError'])
        self.observer.wait_stopped.assert_called_once();self.observer.close_observer.assert_called_once()

    def test_genuine_watchdog_and_cli_held(self):
        with self.assertRaises(RuntimeError):self.watchdog(is_synthetic=False)
        self.assertEqual(main(),2)


if __name__=='__main__':unittest.main()
