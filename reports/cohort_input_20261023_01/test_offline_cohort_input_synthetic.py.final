"""Temporary file reads and generated inventory pins; no real inputs."""
from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.matched_baseline import offline_cohort_input as inputs
from tests import test_offline_cohort_execution_synthetic as fixtures


class InputTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.BindingTests();self.f.setUp()
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.path=self.root/'benchmark.json';self.path.write_bytes(self.f.raw)
        self.pin=inputs.FilePin(str(self.path),len(self.f.raw),sha256(self.f.raw).hexdigest())

    def read(self, **kwargs):
        return inputs.read_fixture_benchmark(path=self.path,fixture_root=self.root,
            reviewed_pin=kwargs.pop('reviewed_pin',self.pin),spec=self.f.spec,**kwargs)

    def test_exact_handle_read_and_query_only_binding(self):
        receipt,binding=self.read()
        self.assertEqual(receipt.pin,self.pin)
        self.assertTrue(receipt.synthetic_fixture)
        self.assertEqual(binding.content_sha256,receipt.pin.sha256)
        self.assertEqual(binding.query_pairs,tuple(self.f.f.f.pairs))
        self.assertNotIn('excluded target',repr(binding))
        self.assertEqual(self.path.read_bytes(),self.f.raw)

    def test_wrong_size_hash_or_path_rejected(self):
        for pin in (replace(self.pin,size_bytes=self.pin.size_bytes+1),
                    replace(self.pin,sha256='0'*64),
                    replace(self.pin,path=str(self.root/'other.json'))):
            with self.assertRaises(ValueError):self.read(reviewed_pin=pin)

    def test_limit_rejected_before_open(self):
        with patch.object(Path,'open',side_effect=AssertionError('must not open')):
            with self.assertRaises(ValueError):self.read(reviewed_pin=replace(
                self.pin,size_bytes=inputs.MAX_BENCHMARK_BYTES+1))

    def test_postread_identity_drift_rejected(self):
        original=inputs._metadata
        calls=[]
        def metadata(info):
            value=original(info);calls.append(value)
            return value[:-1]+(value[-1]+1,) if len(calls)==3 else value
        with patch.object(inputs,'_metadata',side_effect=metadata):
            with self.assertRaises(ValueError):self.read()

    def test_cross_api_ctime_difference_does_not_change_identity(self):
        original=inputs._metadata
        calls=[]
        def metadata(info):
            value=original(info);calls.append(value)
            # Model observed Windows path-vs-handle ctime distinction, stable
            # within both interfaces. Hash and all other metadata still match.
            return value[:-1]+(987654321,) if len(calls) in (2,3) else value
        with patch.object(inputs,'_metadata',side_effect=metadata):
            receipt,binding=self.read()
        self.assertEqual(binding.content_sha256,receipt.pin.sha256)

    def test_hardlinked_input_rejected(self):
        alias=self.root/'alias.json'
        os.link(self.path,alias)
        with self.assertRaises(ValueError):self.read()

    def test_outside_fixture_root_rejected(self):
        sub=self.root/'sub';sub.mkdir()
        with self.assertRaises(ValueError):
            inputs.read_fixture_benchmark(path=self.path,fixture_root=sub,
                reviewed_pin=self.pin,spec=self.f.spec)

    def test_invalid_pin_data(self):
        for pin in (replace(self.pin,size_bytes=True),replace(self.pin,sha256='BAD'),
                    replace(self.pin,path='relative.json'),
                    replace(self.pin,path=str(self.root/'x'/'..'/'benchmark.json')),
                    replace(self.pin,path=str(self.root/'benchmark.json:stream'))):
            with self.assertRaises(ValueError):pin.validate()

    def test_canonical_and_nonfixture_entries_held_before_filesystem(self):
        with patch.object(inputs,'guard',side_effect=AssertionError('no filesystem')):
            with self.assertRaises(RuntimeError):inputs.read_canonical_benchmark(spec=None,reviewed_pin=None)
            with self.assertRaises(RuntimeError):self.read(is_synthetic=False)
        self.assertEqual(inputs.main(),2)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.f=InputTests();self.f.setUp()
        self.addCleanup(self.f.temp.cleanup)
        self.receipt,_=self.f.read()
        self.other=inputs.FilePin(str(self.f.root/'graph.xz'),7,'a'*64)
        self.rows=(self.f.pin,self.other)
        self.paths=tuple(pin.path for pin in self.rows)

    def bind(self, **kwargs):
        args=dict(observed_pins=self.rows,reviewed_pins=self.rows,
                  required_paths=self.paths,benchmark_receipt=self.receipt)
        args.update(kwargs);return inputs.bind_inventory(**args)

    def test_exact_selected_set_binds_without_reading_assets(self):
        with patch.object(Path,'open',side_effect=AssertionError('pure binding')):
            bound=self.bind()
        self.assertEqual(set(bound),set(self.rows))
        self.assertFalse(Path(self.other.path).exists()) # Data equality is not fresh existence proof.

    def test_missing_extra_changed_pin_rejected(self):
        for rows in ((self.f.pin,), self.rows+(replace(self.other,path=str(self.f.root/'extra')),),
                     (self.f.pin,replace(self.other,sha256='b'*64))):
            with self.assertRaises(ValueError):self.bind(observed_pins=rows)

    def test_case_alias_duplicates_rejected(self):
        with self.assertRaises(ValueError):self.bind(observed_pins=(
            self.f.pin,replace(self.f.pin,path=self.f.pin.path.upper())))
        with self.assertRaises(ValueError):self.bind(required_paths=(self.f.pin.path,self.f.pin.path.upper()))

    def test_receipt_pin_and_metadata_must_match(self):
        for receipt in (replace(self.receipt,pin=replace(self.f.pin,sha256='c'*64)),
                        replace(self.receipt,synthetic_fixture=1),
                        replace(self.receipt,metadata=(True,1,self.f.pin.size_bytes,1,1)),
                        replace(self.receipt,metadata=(1,1,0,1,1))):
            with self.assertRaises(ValueError):self.bind(benchmark_receipt=receipt)


if __name__=='__main__':unittest.main()
