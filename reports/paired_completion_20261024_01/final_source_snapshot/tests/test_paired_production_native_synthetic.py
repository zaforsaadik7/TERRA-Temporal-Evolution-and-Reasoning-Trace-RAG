"""Paid entry and control contracts only. No credentials, native APIs or network."""
from pathlib import Path
import copy
import tempfile
import unittest
from unittest.mock import patch
from tests import test_paired_worker_contract_synthetic as fixtures
from scripts.matched_baseline import paired_production_native as native
from scripts.matched_baseline.paired_preparation_native import encode,sha


class ProductionNativeTests(unittest.TestCase):
    def controls(self):
        fixture=fixtures.WorkerContractTests('runTest');fixture.setUp()
        inputs=[{'path':r'F:\TERRA -Copy\SYNTHETIC_native.py','size_bytes':0,'sha256':'a'*64}]
        fixture.value['reviewed_input_manifest_sha256']=sha(encode(inputs))
        root=r'F:\TERRA -Copy\reports\SYNTHETIC_NATIVE_ATTEMPT'
        fixture.value['output_root']=str(Path(root)/'results')
        context=fixture.context();context_raw=context.raw
        plan={'inputs':inputs,'source_plan':fixture.value['plan'],'attempt_dir':root,
            'context_pin':{'path':r'F:\TERRA -Copy\SYNTHETIC_context.json',
                'size_bytes':len(context_raw),'sha256':sha(context_raw)},
            'approval_pin':{'path':'SYNTHETIC_APPROVAL_NOT_USER','size_bytes':0,'sha256':'b'*64},
            'resources':{'child_seconds':100,'outer_seconds':200}}
        approval={'worker_approval':fixture.approval(context),'launch_binding_sha256':native.launch_binding(plan)}
        return plan,context_raw,encode(approval)

    def test_context_and_native_resource_binding(self):
        plan,context,approval=self.controls()
        decoded=native.validate_controls(plan,context,approval)
        self.assertEqual(decoded.scope,'PAIRED_350_LIVE_COMPARISON')
        plan['resources']['child_seconds']+=1
        with self.assertRaises(ValueError):native.validate_controls(plan,context,approval)

    def test_asset_manifest_change_rejected(self):
        plan,context,approval=self.controls();plan['inputs'][0]['sha256']='c'*64
        with self.assertRaises(ValueError):native.validate_controls(plan,context,approval)

    def test_missing_human_record_cannot_become_authority(self):
        plan,context,_=self.controls()
        approval=encode({'worker_approval':None,'launch_binding_sha256':native.launch_binding(plan)})
        with self.assertRaises(ValueError):native.validate_controls(plan,context,approval)

    def test_approval_pin_is_outside_its_own_launch_digest(self):
        plan,_,_=self.controls();before=native.launch_binding(plan)
        plan['approval_pin']['sha256']='d'*64
        self.assertEqual(before,native.launch_binding(plan))
        # The enclosing plan SHA, pinned in the external anchor, DOES change.
        before_plan=sha(encode(plan));plan['approval_pin']['sha256']='e'*64
        self.assertNotEqual(before_plan,sha(encode(plan)))

    def test_paid_main_held_before_open_or_argument_processing(self):
        with patch.object(Path,'open',side_effect=AssertionError('must not open')):
            self.assertEqual(native.main(['--role','worker','--arbitrary']),2)

    def test_even_temporary_gate_needs_external_anchor(self):
        with patch.object(native,'LIVE_ADMITTED',True),patch.object(Path,'open',side_effect=AssertionError('must not open')):
            with self.assertRaises(ValueError):
                native.main(['--plan',r'F:\SYNTHETIC.json','--sha','f'*64,'--role','outer'])

    def test_each_child_role_can_only_be_claimed_once(self):
        with tempfile.TemporaryDirectory() as directory:
            plan={'attempt_dir':directory}
            native.claim_role(plan,'a'*64,'worker')
            before=(Path(directory)/'worker_attempt.lock').read_bytes()
            with self.assertRaises(FileExistsError):native.claim_role(plan,'a'*64,'worker')
            self.assertEqual(before,(Path(directory)/'worker_attempt.lock').read_bytes())

    def test_finalized_attempt_cannot_claim_an_unsent_role(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'controller_terminal.json').write_bytes(b'{}')
            with self.assertRaises(ValueError):native.claim_role({'attempt_dir':directory},'a'*64,'worker')
            self.assertFalse((Path(directory)/'worker_attempt.lock').exists())


if __name__=='__main__':unittest.main()
