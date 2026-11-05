"""Resource lifecycle fixtures only; no native/model/store calls."""
import unittest
from scripts.matched_baseline.offline_cohort_assembly import (
    CohortAssembly, OwnedDependency, main)
from tests import test_offline_cohort_loader_synthetic as loader_fixtures


class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = loader_fixtures.LoaderTests(); self.fixture.setUp()
        self.released = []
        self.deps = dict(self.fixture.deps)
        for name in ('embedding','reader','roles'):
            original = self.deps[name]
            def factory(*args, _name=name, _original=original, **kwargs):
                value = _original(*args, **kwargs)
                return OwnedDependency(value, lambda:self.released.append(_name))
            self.deps[name] = factory

    def assembly(self, **kwargs):
        f=self.fixture
        return CohortAssembly(plan=f.plan, reviewed_plan=f.plan,
                              dependencies=self.deps, **kwargs)

    def load(self, assembly):
        f=self.fixture
        return assembly.load(spec=f.spec, query_pairs=f.pairs, receipt=f.receipt)

    def test_success_releases_reverse_order_after_use(self):
        with self.assembly() as assembly:
            result=self.load(assembly)
            self.assertIs(result['reader'],self.fixture.reader)
            self.assertEqual(self.released,[])
        self.assertEqual(self.released,['roles','reader','embedding'])
        assembly.close()
        self.assertEqual(len(self.released),3)

    def test_cache_failure_releases_embedding(self):
        self.fixture.embedding.verify_pinned_cache.side_effect=ValueError('fixture')
        with self.assertRaises(ValueError): self.load(self.assembly())
        self.assertEqual(self.released,['embedding'])

    def test_schema_failure_releases_reader_then_embedding(self):
        self.fixture.reader.validate_store_schema.side_effect=ValueError('fixture')
        with self.assertRaises(ValueError): self.load(self.assembly())
        self.assertEqual(self.released,['reader','embedding'])

    def test_role_validation_failure_releases_all(self):
        self.fixture.deps['roles'].side_effect=None
        self.fixture.deps['roles'].return_value={}
        with self.assertRaises(ValueError): self.load(self.assembly())
        self.assertEqual(self.released,['roles','reader','embedding'])

    def test_computation_failure_retained(self):
        error=ValueError('fixture')
        with self.assertRaises(ValueError) as caught:
            with self.assembly() as assembly:
                self.load(assembly)
                raise error
        self.assertIs(caught.exception,error)
        self.assertEqual(self.released,['roles','reader','embedding'])

    def test_cleanup_failures_do_not_skip_other_releases(self):
        error=ValueError('original')
        original=self.deps['reader']
        def reader(**kwargs):
            owned=original(**kwargs)
            def release():
                owned.release()
                raise OSError('cleanup fixture')
            return OwnedDependency(owned.value,release)
        self.deps['reader']=reader
        with self.assertRaises(BaseExceptionGroup) as caught:
            with self.assembly() as assembly:
                self.load(assembly)
                raise error
        self.assertIs(caught.exception.exceptions[0],error)
        self.assertIsInstance(caught.exception.exceptions[1],OSError)
        self.assertEqual(self.released,['roles','reader','embedding'])

    def test_reuse_and_close_before_load_rejected(self):
        assembly=self.assembly();assembly.close()
        with self.assertRaises(RuntimeError): self.load(assembly)
        with self.assembly() as assembly:
            self.load(assembly)
            with self.assertRaises(RuntimeError): self.load(assembly)

    def test_unowned_factory_result_stops(self):
        self.deps['reader']=lambda **kwargs:self.fixture.reader
        with self.assertRaises(ValueError): self.load(self.assembly())
        self.assertEqual(self.released,['embedding'])

    def test_authentic_entry_and_cli_held(self):
        with self.assertRaises(RuntimeError): self.assembly(is_synthetic=False)
        self.assertEqual(main(),2)
        self.assertEqual(self.fixture.events,[])

    def test_callback_required(self):
        with self.assertRaises(ValueError): OwnedDependency(object(),None)


if __name__ == '__main__': unittest.main()
