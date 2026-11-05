"""Policy hashes and fake launch jobs; fixture extensions are not real binaries."""
from dataclasses import asdict,replace
from hashlib import sha256
import json
from pathlib import Path
import unittest
from unittest.mock import Mock,patch
from scripts.matched_baseline import offline_cohort_launch as launch
from scripts.matched_baseline.offline_cohort_input import FilePin
from scripts.matched_baseline.offline_cohort_lifecycle import EvidenceAllocation
from tests import test_offline_cohort_parent_synthetic as fixtures


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.ParentTests();self.f.setUp();self.addCleanup(self.f.temp.cleanup)
        artifacts=[];pins=list(self.f.review.pins)
        directory=self.f.root/'launch_inputs';directory.mkdir()
        for role,suffix in sorted(launch.ROLE_SUFFIXES.items()):
            path=directory/(role+suffix);raw=('synthetic '+role).encode();path.write_bytes(raw)
            pin=FilePin(str(path),len(raw),sha256(raw).hexdigest())
            artifacts.append((role,pin));pins.append(pin)
        self.review=replace(self.f.review,pins=tuple(pins))
        self.f.review=self.review
        run='cohort_20261024_fixture01'
        allocation=EvidenceAllocation(str(self.f.root/'reports'/run/'evidence'),32*1024**2,96*1024**2)
        self.launch=launch.CohortLaunchBinding(self.review,allocation,run,tuple(artifacts),
            'TERRA_Cohort_FIXTURE_LAUNCH','TERRA_COHORT_FIXTURE_LAUNCH')

    def admission(self):
        return launch.BoundLaunchAdmission(candidate=self.launch,reviewed=self.launch)

    def authorize(self,admission,**changes):
        record=dict(approval_id='SYNTHETIC_LAUNCH_ONLY',approval_date='2026-10-24',
            scope=self.review.spec.scope,request_sha256=sha256(self.review.spec.request_bytes()).hexdigest(),
            resources=asdict(self.review.resources),launch_binding_sha256=self.launch.digest(),
            rule_name=self.launch.rule_name,owner_tag=self.launch.owner_tag,max_attempts=1,
            allow_api_calls=False,allow_manuscript_changes=False)
        record.update(changes);raw=json.dumps(record).encode()
        admission.authorize_fixture(raw,expected_sha256=sha256(raw).hexdigest(),reviewed_record=record)

    def prepare(self,admission):
        return admission.prepare(observe_inventory=self.f.observer,read_benchmark=self.f.reader)

    def test_payload_binds_policy_without_plaintext_or_authority_cycle(self):
        with patch.object(Path,'open',side_effect=AssertionError('policy hash must be pure')):
            payload=self.launch.payload();digest=self.launch.digest()
        self.assertEqual(len(digest),64)
        raw=json.dumps(payload)
        self.assertNotIn('excluded target',raw);self.assertNotIn('text A0',raw)
        self.assertNotIn('approval_id',raw)
        self.assertFalse(payload['watchdog']['hard_interrupt_certified'])
        self.assertFalse(payload['boundary']['actor_stop_proves_child_exit'])
        self.assertEqual(payload['command_contract'],'UNRENDERED_PENDING_NATIVE_CONTROLLER_CLI_REVIEW')
        self.assertFalse(self.launch.attempt_root.exists())

    def test_changed_allocation_poll_rule_or_pin_changes_digest(self):
        baseline=self.launch.digest()
        changed=replace(self.launch.allocation,parent_bytes=48*1024**2,child_bytes=80*1024**2)
        for candidate in (replace(self.launch,allocation=changed),replace(self.launch,poll_seconds=.5),
                          replace(self.launch,rule_name='TERRA_Cohort_CHANGED_FIXTURE')):
            self.assertNotEqual(candidate.digest(),baseline)
        role,pin=self.launch.artifacts[0];changed_pin=replace(pin,sha256='b'*64)
        pins=tuple(changed_pin if row==pin else row for row in self.review.pins)
        artifacts=((role,changed_pin),)+self.launch.artifacts[1:]
        self.assertNotEqual(replace(self.launch,parent=replace(self.review,pins=pins),
                                    artifacts=artifacts).digest(),baseline)

    def test_unreviewed_config_rejected_before_any_observer(self):
        with self.assertRaises(ValueError):launch.BoundLaunchAdmission(
            candidate=replace(self.launch,poll_seconds=.5),reviewed=self.launch)
        self.f.observer.assert_not_called()

    def test_bad_layout_or_process_exemption_rejected(self):
        for candidate in (replace(self.launch,run_id='authentic_smoke_old'),
                replace(self.launch,allocation=replace(self.launch.allocation,root=str(self.f.root/'cache'))),
                replace(self.launch,process_policy='ALLOW_CONTROLLER_NETWORK')):
            with self.assertRaises(ValueError):candidate.validate()

    def test_all_artifacts_must_be_pinned_and_correct_kind(self):
        for artifacts in (self.launch.artifacts[:-1],
                ((self.launch.artifacts[0][0],replace(self.launch.artifacts[0][1],sha256='0'*64)),)+self.launch.artifacts[1:],
                tuple((role,next(p for p in self.review.pins if p.path==self.review.benchmark_path))
                    if role=='boundary_script' else (role,pin) for role,pin in self.launch.artifacts)):
            with self.assertRaises(ValueError):replace(self.launch,artifacts=artifacts).validate()

    def test_fixture_approval_must_bind_actual_launch_digest(self):
        admission=self.admission()
        with self.assertRaises(ValueError):self.authorize(admission,launch_binding_sha256='a'*64)
        with self.assertRaises(RuntimeError):self.authorize(admission)
        with self.assertRaises(ValueError):self.prepare(admission)
        self.f.observer.assert_not_called()

    def test_wrong_rule_cannot_leave_authorized_parent(self):
        admission=self.admission()
        with self.assertRaises(ValueError):self.authorize(admission,rule_name='TERRA_Cohort_OTHER_FIXTURE')
        self.assertIsNone(admission.parent.authorization_sha256)
        with self.assertRaises(RuntimeError):self.authorize(admission)
        with self.assertRaises(ValueError):self.prepare(admission)

    def test_bound_job_single_dispatch_and_watchdog_policy(self):
        admission=self.admission();self.authorize(admission);job=self.prepare(admission)
        dispatch=Mock(return_value='SIMULATED')
        self.assertEqual(admission.dispatch(job,reviewed_job_sha256=job.digest(),dispatcher=dispatch),'SIMULATED')
        dispatch.assert_called_once_with(job)
        with self.assertRaises(RuntimeError):admission.dispatch(job,reviewed_job_sha256=job.digest(),dispatcher=dispatch)
        watchdog=job.fixture_watchdog(clock=lambda:0.,pause=Mock())
        self.assertEqual(watchdog.resources,self.review.resources)
        self.assertEqual(watchdog.poll_seconds,self.launch.poll_seconds)

    def test_rejected_bound_job_consumes_dispatch(self):
        admission=self.admission();self.authorize(admission);job=self.prepare(admission);dispatch=Mock()
        with self.assertRaises(ValueError):admission.dispatch(job,reviewed_job_sha256='0'*64,dispatcher=dispatch)
        with self.assertRaises(RuntimeError):admission.dispatch(job,reviewed_job_sha256=job.digest(),dispatcher=dispatch)
        dispatch.assert_not_called()

    def test_corrupt_job_validation_also_consumes_dispatch(self):
        admission=self.admission();self.authorize(admission);job=self.prepare(admission)
        corrupted=replace(job,handoff=replace(job.handoff,binding=replace(job.handoff.binding,size_bytes=0)))
        with self.assertRaises(ValueError):admission.dispatch(corrupted,reviewed_job_sha256='0'*64,dispatcher=Mock())
        with self.assertRaises(RuntimeError):admission.dispatch(job,reviewed_job_sha256=job.digest(),dispatcher=Mock())

    def test_genuine_admission_watchdog_and_cli_held(self):
        with self.assertRaises(RuntimeError):launch.BoundLaunchAdmission(candidate=None,reviewed=None,is_synthetic=False)
        admission=self.admission();self.authorize(admission);job=self.prepare(admission)
        with self.assertRaises(RuntimeError):job.fixture_watchdog(clock=None,pause=None,is_synthetic=False)
        self.assertEqual(launch.main(),2)


if __name__=='__main__':unittest.main()
