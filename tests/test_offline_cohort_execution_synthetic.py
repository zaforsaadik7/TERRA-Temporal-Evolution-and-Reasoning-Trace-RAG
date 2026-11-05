"""Generated benchmark bytes, mock runtime and orchestration fixtures only."""
from contextlib import contextmanager
from hashlib import sha256
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.matched_baseline import offline_cohort_execution as execution
from scripts.matched_baseline.offline_cohort_contracts import ProposedResources
from scripts.matched_baseline.offline_cohort_evidence import CohortEvidenceWriter
from tests import test_offline_cohort_adapters_synthetic as fixtures


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.AdapterTests();self.f.setUp()
        self.spec=self.f.f.spec
        self.rows=[dict(query_id=i.query_id,query=text,category=i.category,
                        answer='excluded target') for i,(_,text) in zip(self.spec.queries,self.f.f.pairs)]
        self.raw=json.dumps(self.rows).encode()

    def bind(self, raw=None, **kwargs):
        raw=self.raw if raw is None else raw
        return execution.bind_benchmark_bytes(raw,spec=self.spec,
            reviewed_sha256=sha256(raw).hexdigest(),**kwargs)

    def test_binding_returns_only_ordered_query_pairs(self):
        bound=self.bind()
        self.assertTrue(bound.synthetic_fixture)
        self.assertEqual(bound.query_pairs,tuple(self.f.f.pairs))
        self.assertEqual(bound.content_sha256,sha256(self.raw).hexdigest())
        self.assertNotIn('excluded target',repr(bound))

    def test_changed_bytes_fail_independent_digest(self):
        with self.assertRaises(ValueError):
            execution.bind_benchmark_bytes(self.raw+b' ',spec=self.spec,
                                          reviewed_sha256=sha256(self.raw).hexdigest())

    def test_duplicate_json_key_rejected(self):
        raw=self.raw.replace(b'"answer": "excluded target"',
            b'"answer": "a", "answer": "b"',1)
        with self.assertRaises(ValueError):self.bind(raw)

    def test_order_category_and_text_mismatch(self):
        for field,value in (('query_id','wrong'),('category','wrong'),('query','wrong')):
            rows=[dict(r) for r in self.rows];rows[0][field]=value
            with self.assertRaises(ValueError):self.bind(json.dumps(rows).encode())

    def test_fixture_cannot_use_canonical_mode(self):
        with self.assertRaises(ValueError):self.bind(is_synthetic=False)

    def test_population_and_bounded_bytes(self):
        for raw in (b'',b'x'*(execution.MAX_BENCHMARK_BYTES+1),b'[]'):
            with self.assertRaises(ValueError):self.bind(raw)


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.fixture=BindingTests();self.fixture.setUp()
        self.f=self.fixture.f.f
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.resources=ProposedResources();self.ticks=itertools.count(step=.01)
        self.active=False;self.guarded_calls=[];self.handles=[]
        @contextmanager
        def guard():
            self.assertFalse(self.active);self.active=True
            try:yield
            finally:self.active=False
        self.guard=guard
        self.writer=CohortEvidenceWriter(Path(self.temp.name)/'evidence',
                                        budget_bytes=self.resources.evidence_bytes)

    def run_pipeline(self,raw=None):
        raw=self.fixture.raw if raw is None else raw
        return execution.run_synthetic_bound_cohort(raw=raw,spec=self.f.spec,
            reviewed_sha256=sha256(self.fixture.raw).hexdigest(),plan=self.f.plan,
            reviewed_plan=self.f.plan,receipt=self.f.receipt,resources=self.resources,
            runtime=self.fixture.f.runtime,writer=self.writer,
            clock=lambda:next(self.ticks),guard=self.guard)

    def fake_worker(self, **dependencies):
        self.assertTrue(self.active)
        self.handles.append(dependencies['reader'])
        outer=self
        class Worker:
            def run(self,spec,pairs,*,on_record):
                outer.assertTrue(outer.active)
                outer.assertEqual(len(pairs),350)
                on_record(b'{"fixture_row":true}\n')
                return b'{"mode":"SIMULATED","orchestration_fixture":true}\n'
        return Worker()

    def test_guard_spans_loading_computation_and_release(self):
        original=self.f.deps['reader'].side_effect
        def reader(*args,**kwargs):
            self.assertTrue(self.active)
            return original(*args,**kwargs)
        self.f.deps['reader'].side_effect=reader
        with patch.object(execution,'PreparedCohortWorker',side_effect=self.fake_worker):
            result=self.run_pipeline()
        self.assertEqual(json.loads(result)['mode'],'SIMULATED')
        self.assertFalse(self.active);self.assertTrue(self.writer.closed)
        with self.assertRaises(RuntimeError):self.handles[0].validate_store_schema()

    def test_bad_binding_closes_writer_before_loader(self):
        with self.assertRaises(ValueError):self.run_pipeline(b'[]')
        self.assertEqual(self.f.events,[])
        self.assertEqual(list(self.writer.directory.iterdir()),[])
        self.assertTrue(self.writer.closed)

    def test_worker_failure_preserves_marker_and_releases(self):
        with patch.object(execution,'PreparedCohortWorker',side_effect=ValueError('not exported')):
            with self.assertRaises(ValueError):self.run_pipeline()
        self.assertFalse(self.active);self.assertTrue(self.writer.closed)
        self.assertFalse((self.writer.directory/'cohort_report.json').exists())
        marker=(self.writer.directory/'failure.json').read_bytes()
        self.assertNotIn(b'not exported',marker)
        self.assertEqual(json.loads(marker)['status'],'FAILED_INCOMPLETE')

    def test_guard_exit_failure_does_not_return_success(self):
        guard=self.guard
        @contextmanager
        def failing():
            with guard():yield
            raise RuntimeError('guard exit fixture')
        self.guard=failing
        with patch.object(execution,'PreparedCohortWorker',side_effect=self.fake_worker):
            with self.assertRaises(RuntimeError):self.run_pipeline()
        # Computational report may exist; failure marker prevents treating it as terminal PASS.
        self.assertTrue((self.writer.directory/'failure.json').exists())
        self.assertTrue(self.writer.closed)

    def test_writer_cleanup_failure_preserves_binding_failure(self):
        with patch.object(self.writer,'close',side_effect=OSError('cleanup fixture')):
            with self.assertRaises(BaseExceptionGroup) as caught:self.run_pipeline(b'[]')
        self.assertIsInstance(caught.exception.exceptions[0],ValueError)
        self.assertIsInstance(caught.exception.exceptions[1],OSError)
        self.writer.close()

    def test_writer_cleanup_failure_preserves_worker_failure(self):
        with patch.object(self.writer,'close',side_effect=OSError('cleanup fixture')):
            with patch.object(execution,'PreparedCohortWorker',side_effect=ValueError('worker fixture')):
                with self.assertRaises(BaseExceptionGroup) as caught:self.run_pipeline()
        self.assertIsInstance(caught.exception.exceptions[0],ValueError)
        self.assertIsInstance(caught.exception.exceptions[1],OSError)
        self.writer.close()

    def test_authentic_entries_block_before_dependency_access(self):
        with patch('builtins.__import__',side_effect=AssertionError('unexpected import')):
            with self.assertRaises(RuntimeError):execution.AuthenticCohortComputation()
            with self.assertRaises(RuntimeError):execution.run_authentic_bound_cohort(
                raw=b'',spec=None,plan=None,reviewed_plan=None,receipt=None,
                resources=None,writer=None,clock=None)
        self.assertEqual(execution.main(),2)
        self.writer.close()


if __name__=='__main__':unittest.main()
