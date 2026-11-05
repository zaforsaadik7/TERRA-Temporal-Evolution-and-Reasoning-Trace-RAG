"""Receiving contract with generated tiny files and trusted mock callbacks only."""
from dataclasses import asdict
from hashlib import sha256
import contextlib
import io
import json
import unittest
from unittest.mock import Mock,patch
from scripts.matched_baseline import offline_cohort_controller as controller
from tests import test_offline_cohort_command_synthetic as fixtures


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.CommandTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.command=self.f.command;self.launch=self.command.launch
        self.raw=controller.context_bytes(self.command)
        self.record=dict(approval_id='SYNTHETIC_CONTROLLER_ONLY',approval_date='2026-10-24',
            scope=self.launch.parent.spec.scope,
            request_sha256=sha256(self.launch.parent.spec.request_bytes()).hexdigest(),
            resources=asdict(self.launch.parent.resources),launch_binding_sha256=self.command.digest(),
            rule_name=self.launch.rule_name,owner_tag=self.launch.owner_tag,max_attempts=1,
            allow_api_calls=False,allow_manuscript_changes=False)
        self.argv=tuple(self.command.payload()['argv'][4:])
        self.context_reader=Mock(return_value=self.raw)
        self.approval_reader=Mock();self.dispatch=Mock(return_value='SIMULATED_DISPATCH')
        self.observer=self.f.f.f.observer;self.reader=self.f.f.f.reader

    def run_controller(self,instance,*,raw=None,record=None,argv=None):
        raw=self.raw if raw is None else raw
        record=self.record if record is None else record
        self.context_reader.return_value=raw
        approval=json.dumps(record).encode();self.approval_reader.return_value=approval
        return instance.run(self.argv if argv is None else argv,
            context_sha256=sha256(raw).hexdigest(),approval_sha256=sha256(approval).hexdigest(),
            approval_record=record,read_context=self.context_reader,read_approval=self.approval_reader,
            observe_inventory=self.observer,read_benchmark=self.reader,dispatcher=self.dispatch)

    def test_receiving_to_observed_handoff_and_single_dispatch(self):
        instance=controller.FixtureController(self.command)
        self.assertEqual(self.run_controller(instance),'SIMULATED_DISPATCH')
        item=self.dispatch.call_args.args[0]
        self.assertEqual(item.command,self.command);self.assertEqual(len(item.digest()),64)
        self.assertNotEqual(item.digest(),item.job.digest())
        with self.assertRaises(RuntimeError):self.run_controller(instance)
        self.dispatch.assert_called_once()

    def test_old_policy_only_approval_rejected_before_inventory(self):
        record=dict(self.record,launch_binding_sha256=self.launch.digest())
        with self.assertRaises(ValueError):self.run_controller(
            controller.FixtureController(self.command),record=record)
        self.observer.assert_not_called();self.reader.assert_not_called()

    def test_wrong_rule_rejected_before_inventory(self):
        with self.assertRaises(ValueError):self.run_controller(controller.FixtureController(self.command),
            record=dict(self.record,rule_name='TERRA_Cohort_OTHER_FIXTURE'))
        self.observer.assert_not_called()

    def test_context_extra_numeric_bool_and_duplicate_rejected(self):
        value=json.loads(self.raw)
        variants=[dict(value,extra='unexpected'),dict(value,shell=0)]
        raws=[json.dumps(v).encode() for v in variants]+[b'{"shell":false,"shell":false}']
        for raw in raws:
            with self.assertRaises(ValueError):self.run_controller(
                controller.FixtureController(self.command),raw=raw)
        self.approval_reader.assert_not_called();self.observer.assert_not_called()

    def test_hash_size_encoding_and_nonfinite_rejected(self):
        for raw,expected in ((self.raw,'0'*64),(b'\xff',sha256(b'\xff').hexdigest()),
                (b'NaN',sha256(b'NaN').hexdigest()),(b'x'*(controller.CONTEXT_LIMIT+1),'0'*64)):
            with self.assertRaises(ValueError):controller.decode_context(raw,
                expected_sha256=expected,reviewed=self.command)

    def test_cli_wrong_paths_repeats_abbreviations_no_reads_and_consumes(self):
        variants=[self.argv+('--approval',self.argv[-1]),
            ('--launch-context','C:\\wrong.json','--approval',self.argv[-1]),
            ('--launch',self.argv[1],'--approval',self.argv[-1])]
        for argv in variants:
            instance=controller.FixtureController(self.command)
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises((ValueError,SystemExit)):self.run_controller(instance,argv=argv)
            with self.assertRaises(RuntimeError):self.run_controller(instance)
        self.context_reader.assert_not_called()

    def test_dispatch_exception_consumes_and_preserves_error(self):
        self.dispatch.side_effect=OSError('synthetic dispatch failure')
        instance=controller.FixtureController(self.command)
        with self.assertRaises(OSError):self.run_controller(instance)
        with self.assertRaises(RuntimeError):self.run_controller(instance)
        self.dispatch.assert_called_once()

    def test_genuine_main_held_before_parse_and_reads(self):
        with self.assertRaises(RuntimeError):controller.FixtureController(None,is_synthetic=False)
        with patch.object(controller,'parse_fixture_cli',side_effect=AssertionError('must not parse')):
            self.assertEqual(controller.main(['--anything']),2)
        self.assertFalse(controller.COHORT_CONTROLLER_ADMITTED)


if __name__=='__main__':unittest.main()
