"""Whole runner on small temp files, fake boundary and fake child callback."""
from dataclasses import replace
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from scripts.matched_baseline.offline_smoke_runner import SmokeRunner
from scripts.matched_baseline.offline_smoke_boundary import OwnedSmokeBoundary, BoundaryReceipt
from scripts.matched_baseline.offline_smoke_evidence import SmokeEvidenceWriter
from scripts.matched_baseline.offline_smoke_file_pins import FrozenFilePinVerifier
from scripts.matched_baseline.offline_smoke_integrity import SmokeProtectedLifecycle
from scripts.matched_baseline.offline_smoke_lifecycle import ChildProcessResult
from scripts.matched_baseline.offline_preflight import IntegrityLifecycleManager as Manager, SingleUseExecutionLock
from tests.test_offline_smoke_boundary_synthetic import FakeBackend
from tests import test_offline_smoke_config_synthetic as config_fixture
from tests import test_offline_smoke_approval_synthetic as approval_fixture


class RunnerTests(unittest.TestCase):
    def exercise(self, oversized=False, bad_config=False, lock_collision=False, missing_approval=False,
                 boundary_evidence_failure=False, tamper_pin=False):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, cache = root/'source', root/'cache'
            source.mkdir(); cache.mkdir()
            (source/'chroma.sqlite3').write_bytes(b'fake')
            (cache/'model').write_bytes(b'fake')
            integrity = SmokeProtectedLifecycle(source=source,cache=cache,snapshot=root/'snapshot',
                disposable=root/'disposable',source_manifest=Manager.compute_manifest(source),
                cache_manifest=Manager.compute_manifest(cache))
            writer = SmokeEvidenceWriter(root/'evidence')
            if boundary_evidence_failure:
                original_write = writer._write_json
                def fail_boundary_record(name, value):
                    if name == 'boundary_verified.json':
                        raise OSError('Synthetic boundary evidence failure')
                    return original_write(name,value)
                writer._write_json = fail_boundary_record
            fixture = config_fixture.ConfigTests(); fixture.setUp()
            pin_folder = root/'pin-fixtures'; pin_folder.mkdir()
            paths, pins, sizes = {}, {}, {}
            for name,_ in fixture.config.pins:
                paths[name] = pin_folder/name
                data = ('synthetic file '+name).encode()
                paths[name].write_bytes(data)
                pins[name] = hashlib.sha256(data).hexdigest(); sizes[name] = len(data)
            file_verifier = FrozenFilePinVerifier(file_paths=paths,expected_pins=pins,expected_sizes=sizes)
            config = replace(fixture.config, evidence_directory=str(writer.directory),
                             lock_path=str(root/'smoke.lock'),pins=tuple(pins.items()))
            approval = approval_fixture.ApprovalTests(); approval.setUp()
            approval_bytes = json.dumps(approval.record).encode()
            digest = hashlib.sha256(approval_bytes).hexdigest()
            config = replace(config,authorization_sha256=digest)
            context = {**fixture.context, 'reviewed_paths': (config.lock_path,config.evidence_directory)}
            context['reviewed_authorization'] = (config.authorization_id,digest)
            context['reviewed_pins'] = pins
            if bad_config:
                config = replace(config, query_id='wrong')
            if lock_collision:
                Path(config.lock_path).write_bytes(b'prior attempt')
            backend = FakeBackend()
            boundary = OwnedSmokeBoundary(backend, BoundaryReceipt(config.rule_name, config.command[0], 'owner'))
            events = []
            def fake_child(receipt, capture, config, environment):
                events.append('child')
                self.assertEqual(Path(receipt.disposable_dir), integrity.disposable)
                self.assertEqual(environment['HF_HUB_OFFLINE'],'1')
                self.assertNotIn('FAKE_API_KEY',environment)
                self.assertNotIn('PYTHONPATH',environment)
                self.assertNotIn('PYTHONHOME',environment)
                capture.write_bytes(b'x' * (101 if oversized else 5))
                if tamper_pin:
                    paths['driver'].write_bytes(b'tampered synthetic driver')
                return ChildProcessResult(True, 0)
            runner = SmokeRunner(config=config,reviewed_context=context,integrity=integrity,
                boundary=boundary,writer=writer,execution_lock=SingleUseExecutionLock(config.lock_path),
                execute_child=fake_child,approval_bytes=None if missing_approval else approval_bytes,
                reviewed_approval=approval.record,runtime_environment={
                    'SYSTEMROOT':'synthetic-system','FAKE_API_KEY':'synthetic-not-secret',
                    'PYTHONPATH':'untrusted-fixture','PYTHONHOME':'untrusted-fixture'},file_verifier=file_verifier)
            outcome = runner.run()
            terminal = json.loads((writer.directory/'terminal.json').read_text())
            if not bad_config and not lock_collision and not missing_approval and not boundary_evidence_failure:
                self.assertTrue(Path(config.lock_path).exists())
                self.assertTrue((writer.directory/'protected_inventories.json').exists())
                self.assertTrue((writer.directory/'boundary_recovery.json').exists())
                self.assertEqual((writer.directory/'execution_approval.original.json').read_bytes(),approval_bytes)
                observed = json.loads((writer.directory/'boundary_verified.json').read_text())
                self.assertEqual(observed['observed']['owner_tag'],'owner')
                env_record = json.loads((writer.directory/'boundary_environment_preparation.json').read_text())
                self.assertEqual(env_record['unreadable_process_count'],3)
            if bad_config or missing_approval or boundary_evidence_failure:
                self.assertFalse(Path(config.lock_path).exists())
                if not boundary_evidence_failure:
                    self.assertFalse(integrity.snapshot.exists())
            if lock_collision:
                self.assertEqual(Path(config.lock_path).read_bytes(), b'prior attempt')
            return outcome, terminal, events, backend.operations

    def test_integrated_success_has_verified_capture(self):
        outcome, terminal, events, operations = self.exercise()
        self.assertEqual(outcome.status,'SIMULATED_SUCCESS')
        self.assertEqual(terminal['child_capture']['status'],'VERIFIED')
        self.assertTrue(terminal['transcript_closed'])
        self.assertEqual(events,['child'])
        self.assertEqual(operations,['create','remove'])

    def test_oversized_capture_forces_terminal_failure(self):
        outcome, terminal, events, operations = self.exercise(oversized=True)
        self.assertEqual(outcome.status,'FAIL')
        self.assertEqual(terminal['child_capture']['status'],'FAIL')
        self.assertTrue(terminal['transcript_closed'])

    def test_config_failure_prevents_copy_boundary_lock_child(self):
        outcome, terminal, events, operations = self.exercise(bad_config=True)
        self.assertEqual(outcome.status,'FAIL')
        self.assertEqual(events,[])
        self.assertEqual(operations,[])

    def test_existing_lock_stops_before_copy_boundary_child(self):
        outcome, terminal, events, operations = self.exercise(lock_collision=True)
        self.assertEqual(outcome.status,'FAIL')
        self.assertEqual(events,[])
        self.assertEqual(operations,[])

    def test_missing_approval_prevents_copy_boundary_lock_child(self):
        outcome, terminal, events, operations = self.exercise(missing_approval=True)
        self.assertEqual(outcome.status,'FAIL')
        self.assertEqual(events,[])
        self.assertEqual(operations,[])

    def test_boundary_evidence_failure_cleans_without_spending_lock(self):
        outcome, terminal, events, operations = self.exercise(boundary_evidence_failure=True)
        self.assertEqual(outcome.status,'FAIL')
        self.assertEqual(events,[])
        self.assertEqual(operations,['create','remove'])
        self.assertIn('boundary evidence failure',' '.join(terminal['failures']))

    def test_postrun_declared_pin_change_forces_failure(self):
        outcome, terminal, events, operations = self.exercise(tamper_pin=True)
        self.assertEqual(outcome.status,'FAIL')
        self.assertIn('driver:',' '.join(terminal['failures']))
        self.assertEqual(operations,['create','remove'])
