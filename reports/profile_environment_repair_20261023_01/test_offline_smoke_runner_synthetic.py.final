"""Whole runner on small temp files, fake boundary and fake child callback."""
from dataclasses import replace, asdict
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch
from scripts.matched_baseline.offline_smoke_parent import assemble_parent_runner, main as parent_main
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
from scripts.matched_baseline import offline_smoke_production as production
from types import SimpleNamespace
from unittest.mock import Mock


class ProductionIntegrationTests(unittest.TestCase):
    def test_authentic_terminal_status_requires_verified_capture(self):
        from scripts.matched_baseline.offline_smoke_lifecycle import SmokeOutcome
        with tempfile.TemporaryDirectory() as folder:
            writer = SmokeEvidenceWriter(Path(folder)/'record',success_status=production.STATUS)
            writer.start_record({'mode':production.MODE})
            writer.close_transcript()
            with self.assertRaisesRegex(RuntimeError,'verified capture'):
                writer.terminal_record(SmokeOutcome(production.STATUS,0,()))
            capture = writer.directory/'child_output.log'
            capture.write_bytes(b'fake capture')
            writer.record_child_capture(capture,termination_confirmed=True,max_bytes=100)
            writer.terminal_record(SmokeOutcome(production.STATUS,0,()))
            self.assertEqual(json.loads((writer.directory/'terminal.json').read_bytes())['status'],production.STATUS)

    def test_context_write_failure_confirms_no_child_launch(self):
        from tests.test_offline_smoke_request_synthetic import RequestTests
        from scripts.matched_baseline.offline_smoke_lifecycle import ChildExecutionFailure
        fixture = RequestTests(); fixture.setUp()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'child_request.json').write_bytes(json.dumps(fixture.payload).encode())
            receipt,config = object(),object()
            writer = SimpleNamespace(directory=root,_write_bytes=Mock(side_effect=OSError('fake write failure')))
            with patch.object(production,'_request_matches',return_value=receipt), \
                 patch('scripts.matched_baseline.offline_smoke_windows_assembly.assemble_windows_dispatch') as assemble:
                with self.assertRaises(ChildExecutionFailure) as caught:
                    production._dispatch({},config,object(),object(),writer)(receipt,root/'output',config,{})
                self.assertTrue(caught.exception.result.termination_confirmed)
                assemble.assert_not_called()

    def test_genuine_parent_composition_reaches_runner_without_real_dependencies(self):
        from scripts.matched_baseline.offline_smoke_lifecycle import SmokeOutcome
        with tempfile.TemporaryDirectory() as folder:
            packet,raw,digest = self.packet_fixture(Path(folder))
            packet,config,plan = production.decode_packet(raw,digest)
            runner = Mock(); runner.run.return_value = SmokeOutcome(production.STATUS,0,())
            with patch.object(production,'ENTRY_ADMITTED',True), \
                 patch.object(production,'verify_packet_inputs',return_value=(Mock(),b'fake approval')), \
                 patch('scripts.matched_baseline.offline_smoke_integrity.SmokeProtectedLifecycle'), \
                 patch('scripts.matched_baseline.offline_smoke_windows_assembly.load_authentic_windows_library') as dll, \
                 patch('scripts.matched_baseline.offline_smoke_executor.construct_boundary_backend',return_value=FakeBackend()), \
                 patch('scripts.matched_baseline.offline_smoke_runner.SmokeRunner',return_value=runner) as factory:
                self.assertEqual(production.run_parent(packet,config,plan).status,production.STATUS)
                self.assertEqual(factory.call_args.kwargs['report_mode'],production.MODE)
                self.assertEqual(factory.call_args.kwargs['writer'].success_status,production.STATUS)
                self.assertEqual(factory.call_args.kwargs['boundary'].receipt.program,config.firewall_program)
                self.assertNotEqual(config.firewall_program,config.command[0])
                import os
                self.assertEqual(factory.call_args.kwargs['boundary'].controller_pid,os.getpid())
                dll.assert_called_once()

    def test_parent_setup_failure_preserves_failure_and_runs_both_postchecks(self):
        with tempfile.TemporaryDirectory() as folder:
            packet,raw,digest = self.packet_fixture(Path(folder))
            packet,config,plan = production.decode_packet(raw,digest)
            verifier = Mock()
            with patch.object(production,'ENTRY_ADMITTED',True), \
                 patch.object(production,'verify_packet_inputs',return_value=(verifier,b'fake approval')), \
                 patch('scripts.matched_baseline.offline_smoke_integrity.SmokeProtectedLifecycle') as integrity, \
                 patch('scripts.matched_baseline.offline_smoke_windows_assembly.load_authentic_windows_library',side_effect=OSError('fake dll failure')):
                with self.assertRaisesRegex(OSError,'fake dll failure'):
                    production.run_parent(packet,config,plan)
                integrity.return_value.final_check.assert_called_once()
                verifier.verify.assert_called_once()
            saved = json.loads((Path(config.evidence_directory)/'parent_setup_failure.json').read_bytes())
            self.assertEqual(saved['status'],'FAIL')
            self.assertFalse(saved['child_launched'])

    def packet_fixture(self,root):
        fixture = config_fixture.ConfigTests(); fixture.setUp()
        evidence = str(root/'evidence')
        command = (str(root/'python.exe'),'-B','-m','scripts.matched_baseline.offline_smoke_child_entry',
                   '--request',str(root/'evidence'/'child_request.json'))
        config = replace(fixture.config,command=command,evidence_directory=evidence,lock_path=str(root/'lock'),
                         firewall_program=str(root/'runtime.exe'))
        context = {**fixture.context,'reviewed_command':command,'reviewed_paths':(config.lock_path,evidence),
                   'reviewed_firewall_program':config.firewall_program}
        paths = {key:str(root/key) for key in ('source','cache','snapshot','disposable')}
        packet = dict(schema_version=1,controller_interpreter=sys.executable,config=asdict(config),reviewed_context=context,
            load_plan=dict(workspace=str(root),cache_directory=paths['cache'],graph_archive=str(root/'graph.xz'),
                tokenizer_directory=str(root/'tokens'),expected_graph_sha256='a'*64,expected_documents=20000,seed_k=2),
            integrity={**paths,'source_manifest':{},'cache_manifest':{}},declared_files={},
            approval_path=str(root/'approval.json'),reviewed_approval={},owner_tag='fixture-owner',
            windows=dict(system_directory=str(root/'System32'),kernel32_sha256='d'*64,
                powershell_path=str(root/'powershell.exe'),script_path=str(root/'boundary.ps1')),
            runtime_environment={'SYSTEMROOT':'fixture','USERPROFILE':str(root/'profile')})
        raw = json.dumps(packet).encode()
        return packet,raw,hashlib.sha256(raw).hexdigest()

    def test_frozen_packet_roundtrip_and_fixed_command(self):
        with tempfile.TemporaryDirectory() as folder:
            packet,raw,digest = self.packet_fixture(Path(folder))
            decoded,config,plan = production.decode_packet(raw,digest)
            self.assertEqual(plan.expected_documents,20000)
            self.assertEqual(config.command[-2],'--request')
            self.assertEqual(config.command[3],'scripts.matched_baseline.offline_smoke_child_entry')

    def test_packet_digest_duplicate_and_command_override_reject(self):
        with tempfile.TemporaryDirectory() as folder:
            packet,raw,digest = self.packet_fixture(Path(folder))
            with self.assertRaisesRegex(ValueError,'digest'):
                production.decode_packet(raw+b' ',digest)
            raw = b'{"schema_version":1,"schema_version":1}'
            with self.assertRaisesRegex(ValueError,'Duplicate'):
                production.decode_packet(raw,hashlib.sha256(raw).hexdigest())
            packet['config']['command'] = [packet['config']['command'][0],'arbitrary.py']
            packet['reviewed_context']['reviewed_command'] = packet['config']['command']
            raw = json.dumps(packet).encode()
            with self.assertRaisesRegex(ValueError,'fixed entry'):
                production.decode_packet(raw,hashlib.sha256(raw).hexdigest())

    def test_entry_holds_before_packet_or_environment_access(self):
        with patch.object(production,'load_frozen_packet',side_effect=AssertionError('No packet access')),patch('builtins.print'):
            self.assertEqual(production.parent_main([]),2)
            self.assertEqual(production.child_main([]),2)

    def test_production_packet_cannot_infer_runtime_from_launcher(self):
        with tempfile.TemporaryDirectory() as folder:
            packet,raw,digest = self.packet_fixture(Path(folder))
            packet['config'].pop('firewall_program')
            packet['reviewed_context'].pop('reviewed_firewall_program')
            raw = json.dumps(packet).encode()
            with self.assertRaisesRegex(ValueError,'Explicit reviewed runtime'):
                production.decode_packet(raw,hashlib.sha256(raw).hexdigest())

    def test_packet_rejects_credential_and_python_override_environment_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            packet,raw,digest = self.packet_fixture(Path(folder))
            for key in ('HF_TOKEN','DATABRICKS_TOKEN','PYTHONPATH','PYTHONHOME'):
                with self.subTest(key=key):
                    packet['runtime_environment'] = {key:'synthetic-not-a-secret'}
                    raw = json.dumps(packet).encode()
                    with self.assertRaisesRegex(ValueError,'environment keys'):
                        production.decode_packet(raw,hashlib.sha256(raw).hexdigest())

    def test_component_flags_restore_on_exception(self):
        from scripts.matched_baseline import offline_smoke_authentic as authentic
        from scripts.matched_baseline import offline_smoke_windows_assembly as windows
        from scripts.matched_baseline import offline_smoke_executor as executor
        before = authentic.PRODUCTION_ADMITTED,windows.NATIVE_EXECUTION_ADMITTED,executor.EXECUTION_ADMITTED
        with patch.object(production,'ENTRY_ADMITTED',True):
            with self.assertRaisesRegex(ValueError,'fixture'):
                with production._components():
                    self.assertTrue(authentic.PRODUCTION_ADMITTED)
                    self.assertTrue(windows.NATIVE_EXECUTION_ADMITTED)
                    self.assertTrue(executor.EXECUTION_ADMITTED)
                    raise ValueError('fixture')
        self.assertEqual((authentic.PRODUCTION_ADMITTED,windows.NATIVE_EXECUTION_ADMITTED,executor.EXECUTION_ADMITTED),before)

    def test_parent_dispatch_crosses_context_file_and_environment_to_child(self):
        from tests.test_offline_smoke_child_entry_synthetic import EntryTests
        from tests.test_offline_smoke_process_synthetic import FakeJob
        from scripts.matched_baseline.offline_smoke_process import SmokeProcessSupervisor
        from scripts.matched_baseline.offline_smoke_dispatch import SmokeChildDispatcher
        from scripts.matched_baseline.offline_preflight import IsolationReceipt
        from scripts.matched_baseline.offline_smoke_child_entry import execute_synthetic_request
        fixture = EntryTests(); fixture.setUp()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            payload = fixture.payload
            for field in ('source','snapshot','disposable'):
                payload['isolation_receipt'][field+'_dir'] = str(root/field)
            raw = json.dumps(payload).encode()
            (root/'child_request.json').write_bytes(raw)
            receipt = IsolationReceipt(**payload['isolation_receipt'])
            config = SimpleNamespace(command=('fake.exe','--request',str(root/'child_request.json')),
                query_id=payload['query_id'],query_text_sha256=payload['query_text_sha256'],
                authorization_id=payload['authorization_id'],authorization_sha256=payload['authorization_sha256'],
                pins=tuple(payload['protected_pins'].items()),scope=payload['scope'],expected_documents=1,
                evidence_directory=str(root),**payload['limits'])
            packet = {'reviewed_context':{'query_text':payload['query_text']},
                'integrity':{field:str(root/field) for field in ('source','snapshot','disposable')}}
            plan = SimpleNamespace(seed_k=2,workspace=str(root))
            report = execute_synthetic_request(raw,**{**fixture.kwargs,
                'expected_request_sha256':hashlib.sha256(raw).hexdigest()})
            report['mode'] = production.MODE
            report['execution_facts'] = {'retrieval':'LOCAL_DISPOSABLE_STORE','embedding':'LOCAL_PINNED_ONNX',
                'tokenization':'LOCAL_PINNED_TOKENIZERS','routes':'HYPOTHETICAL_EASY_AND_HARD',
                'judge_answer':'SYNTHETIC_PLACEHOLDER','provider_certified':False,'live_api_calls':0}
            worker = Mock(); worker.run.return_value = report
            backend = FakeJob(); backend.states[0]['output_bytes'] = 0
            original_create = backend.create_suspended
            def create(command,environment):
                backend.environment = environment
                return original_create(command,environment)
            backend.create_suspended = create
            original_resume = backend.resume
            def resume(child):
                production.run_child(list(config.command[1:]),packet,config,plan,backend.environment)
                return original_resume(child)
            backend.resume = resume
            supervisor = SmokeProcessSupervisor(backend,clock=lambda:0,pause=lambda _:None,
                timeout_seconds=config.timeout_seconds,memory_bytes=config.memory_bytes)
            supervisor.output_limit_bytes = config.output_limit_bytes
            dispatcher = SmokeChildDispatcher(supervisor)
            writer = SimpleNamespace(directory=root)
            def write(name,data):
                with (root/name).open('xb') as output: output.write(data)
            writer._write_bytes = write
            with patch.object(production,'ENTRY_ADMITTED',True), \
                 patch.object(production,'verify_packet_inputs'), \
                 patch.object(Manager,'validate_disposable_containment'), \
                 patch.object(production,'_verify_child_runtime_image') as image_check, \
                 patch('scripts.matched_baseline.offline_smoke_authentic.construct_authentic_worker',return_value=worker), \
                 patch('scripts.matched_baseline.offline_smoke_windows_assembly.assemble_windows_dispatch',return_value=dispatcher):
                result = production._dispatch(packet,config,plan,object(),writer)(receipt,root/'child_output.log',config,{})
            self.assertEqual(result.exit_code,0)
            self.assertEqual(json.loads((root/'child_report.json').read_bytes())['mode'],production.MODE)
            context = (root/'child_context.json').read_bytes()
            self.assertEqual(backend.environment['TERRA_SMOKE_CONTEXT_SHA256'],hashlib.sha256(context).hexdigest())
            self.assertEqual(backend.events[:4],['create_job','create_suspended','assign','resume'])

    def test_child_missing_digest_prevents_worker_loading(self):
        with patch.object(production,'ENTRY_ADMITTED',True),patch.object(production,'verify_packet_inputs'), \
             patch('scripts.matched_baseline.offline_smoke_authentic.construct_authentic_worker') as worker:
            with self.assertRaisesRegex(ValueError,'independent parent'):
                production.run_child([],{},object(),object(),{})
            worker.assert_not_called()

    def test_child_image_failure_prevents_dependency_loading(self):
        def execute(argv,**kwargs):
            return kwargs['worker_loader'](object())
        with patch.object(production,'ENTRY_ADMITTED',True), \
             patch.object(production,'verify_packet_inputs'), \
             patch.object(production,'_read',return_value=b'fake context'), \
             patch.object(production,'_request_matches',return_value=object()), \
             patch.object(production,'_verify_child_runtime_image',side_effect=RuntimeError('image mismatch')), \
             patch('scripts.matched_baseline.offline_smoke_child_entry.execute_context_cli',side_effect=execute), \
             patch('scripts.matched_baseline.offline_smoke_authentic.construct_authentic_worker') as worker:
            with self.assertRaisesRegex(RuntimeError,'image mismatch'):
                production.run_child([],{},SimpleNamespace(evidence_directory=str(Path.cwd())),None,
                                     {'TERRA_SMOKE_CONTEXT_SHA256':'a'*64})
            worker.assert_not_called()

    def test_child_runtime_attestation_uses_only_environment_read(self):
        with tempfile.TemporaryDirectory() as folder:
            packet,raw,digest = self.packet_fixture(Path(folder))
            packet,config,plan = production.decode_packet(raw,digest)
            with patch('scripts.matched_baseline.offline_smoke_executor.construct_boundary_backend') as factory:
                production._verify_child_runtime_image(packet,config)
                factory.return_value.environment.assert_called_once_with(config.firewall_program)
                factory.return_value.create.assert_not_called()
                factory.return_value.remove.assert_not_called()
                self.assertEqual(factory.call_args.kwargs['receipt'].program,config.firewall_program)

    def test_missing_runtime_target_rejected_without_pin_or_store_access(self):
        with patch.object(production,'ENTRY_ADMITTED',True),patch.object(production,'verify_packet_inputs') as verify:
            with self.assertRaisesRegex(ValueError,'runtime firewall image'):
                production.run_parent({'controller_interpreter':sys.executable},
                    SimpleNamespace(command=(sys.executable,),firewall_program=None),None)
            verify.assert_not_called()


class RunnerTests(unittest.TestCase):
    def exercise(self, oversized=False, bad_config=False, lock_collision=False, missing_approval=False,
                 boundary_evidence_failure=False, tamper_pin=False, assembled_parent=False):
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
            arguments = dict(config=config,reviewed_context=context,integrity=integrity,
                boundary=boundary,writer=writer,execution_lock=SingleUseExecutionLock(config.lock_path),
                approval_bytes=None if missing_approval else approval_bytes,
                reviewed_approval=approval.record,runtime_environment={
                    'SYSTEMROOT':'synthetic-system','FAKE_API_KEY':'synthetic-not-secret',
                    'PYTHONPATH':'untrusted-fixture','PYTHONHOME':'untrusted-fixture'},file_verifier=file_verifier)
            if assembled_parent:
                with patch('scripts.matched_baseline.offline_smoke_parent.assemble_windows_dispatch') as assemble:
                    assemble.return_value = fake_child
                    runner = assemble_parent_runner(kernel=object(),cwd=root,
                        clock=lambda:0,pause=lambda _:None,runner_arguments=arguments)
                    assemble.assert_not_called()
                    outcome = runner.run()
                    if missing_approval:
                        assemble.assert_not_called()
                    else:
                        assemble.assert_called_once()
                        self.assertIs(assemble.call_args.kwargs['config'],config)
                        self.assertEqual(assemble.call_args.kwargs['capture_path'],writer.directory/'child_output.log')
            else:
                runner = SmokeRunner(**arguments,execute_child=fake_child)
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

    def test_parent_composition_defers_assembly_until_admitted_child_stage(self):
        outcome,terminal,events,operations = self.exercise(assembled_parent=True)
        self.assertEqual(outcome.status,'SIMULATED_SUCCESS')
        self.assertEqual(events,['child'])
        self.assertEqual(operations,['create','remove'])

    def test_parent_approval_failure_never_assembles_windows_dispatch(self):
        outcome,terminal,events,operations = self.exercise(assembled_parent=True,missing_approval=True)
        self.assertEqual(outcome.status,'FAIL')
        self.assertEqual(events,[])
        self.assertEqual(operations,[])

    def test_parent_production_entry_and_factory_remain_held(self):
        with patch('builtins.print'),patch('pathlib.Path.open',side_effect=AssertionError('No I/O')):
            self.assertEqual(parent_main(['--run']),2)
            with self.assertRaisesRegex(RuntimeError,'not admitted'):
                assemble_parent_runner(kernel=None,cwd=None,clock=None,pause=None,
                    runner_arguments=None,is_synthetic=False)

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
