"""Synthetic failure injection only; no real packet/model/store/native work."""
from contextlib import nullcontext, redirect_stdout
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts.matched_baseline import offline_smoke_diagnostics as d
from scripts.matched_baseline import offline_smoke_production as production
from scripts.matched_baseline import offline_smoke_authentic as authentic


class DiagnosticsTests(unittest.TestCase):
    def capture_child(self, callback):
        output=io.StringIO()
        with redirect_stdout(output):
            result=callback()
        lines=output.getvalue().splitlines()
        detail=[line.split('CHILD FAILURE DETAIL: ',1)[1] for line in lines
                if line.startswith('CHILD FAILURE DETAIL: ')]
        return result,lines,json.loads(detail[0]) if detail else None

    def test_nested_stage_preserves_primary_exception_and_deepest_location(self):
        error=RuntimeError('private input')
        with d.failure_scope() as scope:
            try:
                with d.diagnostic_stage('CHILD_EXECUTION'):
                    with d.diagnostic_stage('STORE_SCHEMA'):
                        raise error
            except RuntimeError as caught:
                self.assertIs(caught,error)
        self.assertEqual(scope.failed_stage,'STORE_SCHEMA')

    def test_scopes_reset_after_error_and_do_not_bleed(self):
        with d.failure_scope() as first:
            try:
                with d.diagnostic_stage('GRAPH_LOAD'):raise RuntimeError()
            except RuntimeError:pass
        with d.failure_scope() as second:
            self.assertIsNone(second.failed_stage)
        self.assertEqual(first.failed_stage,'GRAPH_LOAD')
        self.assertIsNone(d._active.get())

    def test_raw_messages_locals_and_exception_str_never_serialized(self):
        class HostileError(RuntimeError):
            def __str__(self):raise AssertionError('Never format exception strings')
        secret='hf_PRIVATE_TOKEN_EXAMPLE'
        try:raise HostileError(secret,{'Authorization':'Bearer PRIVATE','query':'private query'})
        except HostileError as exc:
            payload=d.failure_record(exc,stage='STORE_SCHEMA')
        encoded=json.dumps(payload)
        for value in (secret,'Authorization','Bearer PRIVATE','private query','Never format'):
            self.assertNotIn(value,encoded)
        self.assertTrue(payload['message_omitted'])
        frame=payload['traceback_chain'][0]['frames'][-1]
        self.assertEqual(frame['file'],Path(__file__).name)
        self.assertEqual(frame['function'],self._testMethodName)
        self.assertGreater(frame['line'],0)
        self.assertEqual(set(frame),{'file','function','line'})

    def test_exception_chain_and_deep_frames_are_bounded(self):
        def recurse(n):
            if n:recurse(n-1)
            else:raise RuntimeError('not exported')
        try:
            try:recurse(70)
            except RuntimeError as inner:raise ValueError('not exported either') from inner
        except ValueError as exc:
            record=d.failure_record(exc,stage='LOCAL_COMPUTATION')
        self.assertEqual([v['exception_type'] for v in record['traceback_chain']],['ValueError','RuntimeError'])
        self.assertTrue(record['truncated'])
        self.assertLessEqual(max(len(v['frames']) for v in record['traceback_chain']),d.MAX_FRAMES)

    def test_chain_cycle_and_suppression_do_not_leak_or_loop(self):
        a=RuntimeError('a');b=RuntimeError('b');a.__cause__=b;b.__cause__=a
        self.assertEqual(len(d.failure_record(a,stage='UNKNOWN')['traceback_chain']),2)
        a.__cause__=None;a.__context__=b;a.__suppress_context__=True
        self.assertEqual(len(d.failure_record(a,stage='UNKNOWN')['traceback_chain']),1)

    def test_record_cap_and_unknown_stage(self):
        error=RuntimeError('x'*100000)
        current=error
        for _ in range(20):
            nxt=RuntimeError('private');current.__cause__=nxt;current=nxt
        output=io.StringIO()
        with redirect_stdout(output):self.assertTrue(d.emit_child_failure(error,stage='private unknown stage'))
        encoded=output.getvalue().split('CHILD FAILURE DETAIL: ')[1].strip()
        record=json.loads(encoded)
        self.assertLessEqual(len(encoded.encode()),d.MAX_RECORD_BYTES)
        self.assertEqual(record['stage'],'UNKNOWN')
        self.assertLessEqual(len(record['traceback_chain']),d.MAX_CHAIN)
        self.assertTrue(record['truncated'])

    def test_closed_entry_does_not_load_packet_or_emit_details(self):
        with patch.object(production,'ENTRY_ADMITTED',False), \
             patch.object(production,'load_frozen_packet',side_effect=AssertionError('No packet')):
            status,lines,record=self.capture_child(lambda:production.child_main([]))
        self.assertEqual(status,2);self.assertIsNone(record)
        self.assertTrue(lines[0].startswith('BLOCKED:'))

    def test_packet_load_failure_logs_stage_and_exit_one(self):
        with patch.object(production,'ENTRY_ADMITTED',True), \
             patch.object(production,'load_frozen_packet',side_effect=RuntimeError('private packet')):
            status,lines,record=self.capture_child(lambda:production.child_main([]))
        self.assertEqual(status,1);self.assertEqual(record['stage'],'PACKET_LOAD')
        self.assertIn('CHILD FAILURE: RuntimeError',lines)
        self.assertNotIn('private packet','\n'.join(lines))

    def test_child_runtime_image_failure_reports_real_loader_stage(self):
        config=SimpleNamespace(evidence_directory='C:/synthetic/evidence')
        def context(argv,**kwargs):return kwargs['worker_loader'](object())
        with patch.object(production,'ENTRY_ADMITTED',True), \
             patch.object(production,'load_frozen_packet',return_value=({},config,object())), \
             patch.object(production,'verify_packet_inputs'), \
             patch.object(production,'_read',return_value=b'fake context'), \
             patch.object(production,'_request_matches',return_value=object()), \
             patch.object(production,'_verify_child_runtime_image',side_effect=RuntimeError('private')), \
             patch.dict(production.os.environ,{'TERRA_SMOKE_CONTEXT_SHA256':'a'*64}), \
             patch('scripts.matched_baseline.offline_smoke_child_entry.execute_context_cli',side_effect=context), \
             patch.object(authentic,'construct_authentic_worker') as worker:
            status,_,record=self.capture_child(lambda:production.child_main([]))
            worker.assert_not_called()
        self.assertEqual(status,1);self.assertEqual(record['stage'],'RUNTIME_IMAGE')
        self.assertFalse(authentic.PRODUCTION_ADMITTED)

    def test_failed_telemetry_does_not_change_exit_one(self):
        with patch.object(production,'ENTRY_ADMITTED',True), \
             patch.object(production,'load_frozen_packet',side_effect=RuntimeError('private')), \
             patch('builtins.print',side_effect=OSError('fake broken pipe')):
            self.assertEqual(production.child_main([]),1)

    def test_synthetic_success_not_relabelled_or_changed(self):
        with patch.object(production,'ENTRY_ADMITTED',True), \
             patch.object(production,'load_frozen_packet',return_value=({},object(),object())), \
             patch.object(production,'run_child',return_value={'fake':'result'}) as run:
            status,lines,record=self.capture_child(lambda:production.child_main([]))
        run.assert_called_once();self.assertEqual(status,0);self.assertIsNone(record)
        self.assertEqual(lines,['CHILD OUTCOME: '+production.MODE])

    def test_worker_failure_stage_with_only_fake_dependencies(self):
        plan=authentic.AuthenticLoadPlan(workspace='C:/fixture',cache_directory='C:/fixture/cache',
            graph_archive='C:/fixture/graph.xz',tokenizer_directory='C:/fixture/tokenizers',
            expected_graph_sha256='a'*64)
        receipt=SimpleNamespace(disposable_dir='C:/fixture/disposable',source_dir='C:/fixture/source')
        for failing_key,expected in [('embedding','CACHE_VERIFICATION'),('reader','DISPOSABLE_READER'),
                                     ('graph','GRAPH_LOAD'),('roles','ROLE_TOKENIZERS')]:
            embedding=Mock();reader=Mock()
            deps={'check_path':Mock(),'hash_graph':Mock(return_value='a'*64),'validate_receipt':Mock(),
                  'embedding':Mock(return_value=embedding),'reader':Mock(return_value=reader),
                  'graph':Mock(return_value=({},[],{'schema_valid':True})),'roles':Mock()}
            deps[failing_key].side_effect=RuntimeError('fake only')
            with self.subTest(stage=expected),d.failure_scope() as state:
                with self.assertRaisesRegex(RuntimeError,'fake only'):
                    authentic.assemble_worker_with_dependencies(plan,receipt,dependencies=deps)
                self.assertEqual(state.failed_stage,expected)

    def test_authentic_run_error_preserves_worker_exception_and_stage(self):
        worker=authentic.AuthenticOfflineWorker(object(),object())
        error=RuntimeError('fake calculation')
        with patch.object(authentic,'PRODUCTION_ADMITTED',True), \
             patch.object(authentic,'InProcessNetworkBlocker',return_value=nullcontext()), \
             patch.object(authentic,'_genuine_dependencies',return_value={}), \
             patch.object(authentic,'assemble_worker_with_dependencies',return_value=SimpleNamespace(
                 run=Mock(side_effect=error))), d.failure_scope() as state:
            with self.assertRaises(RuntimeError) as caught:worker.run(fake='query')
            self.assertIs(caught.exception,error)
            self.assertEqual(state.failed_stage,'LOCAL_COMPUTATION')
        self.assertTrue(worker.used)


if __name__=='__main__':unittest.main()
