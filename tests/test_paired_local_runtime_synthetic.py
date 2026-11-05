"""Local assembly seam over tiny in-memory fake objects; no real loaders."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts.matched_baseline.paired_local_runtime import _assemble_local, load_authentic_local, _run_loaded_study, PairedLocalBundle
from scripts.matched_baseline.provider_accounting import ContractError, DispatchHeld
from tests import test_paired_dependency_bridge_synthetic as fixtures


class LocalRuntimeTests(unittest.TestCase):
    def setup_bundle(self):
        f = fixtures.BridgeTests('runTest'); f.setUp()
        f.tokenizers['verifier'] = f.tokenizers['generator']
        reader = Mock()
        reader.extract_layer1_corpus.return_value = f.corpus
        values = dict(reader=reader, nodes=f.nodes, edges=f.edges,
            role_configs={r: SimpleNamespace(tokenizer=t) for r,t in f.tokenizers.items()})
        assembly = Mock()
        assembly.load.return_value = values
        return f, reader, assembly, values

    def test_shared_tokenizers_and_full_corpus_use(self):
        f,reader,assembly,_ = self.setup_bundle()
        bundle = _assemble_local(assembly=assembly,spec='fixture',query_pairs=[],receipt='fixture',expected_count=3)
        reader.extract_layer1_corpus.assert_called_once_with(expected_count=3)
        self.assertIs(bundle.tokenizers['generator'], bundle.tokenizers['verifier'])
        assembly.close.assert_not_called()
        bundle.close(); assembly.close.assert_called_once()

    def test_loading_failure_closes_ownership(self):
        _,_,assembly,_ = self.setup_bundle()
        assembly.load.side_effect = ValueError('fixture')
        with self.assertRaises(ValueError):
            _assemble_local(assembly=assembly,spec=None,query_pairs=[],receipt=None,expected_count=3)
        assembly.close.assert_called_once()

    def test_tokenizer_mismatch_rejected_and_closed(self):
        _,_,assembly,values = self.setup_bundle()
        values['role_configs']['verifier'] = SimpleNamespace(tokenizer=object())
        with self.assertRaises(ContractError):
            _assemble_local(assembly=assembly,spec=None,query_pairs=[],receipt=None,expected_count=3)
        assembly.close.assert_called_once()

    def test_population_mismatch_rejected(self):
        _,_,assembly,_ = self.setup_bundle()
        with self.assertRaises(ContractError):
            _assemble_local(assembly=assembly,spec=None,query_pairs=[],receipt=None,expected_count=20000)
        assembly.close.assert_called_once()

    def test_cleanup_error_preserves_original(self):
        _,_,assembly,_ = self.setup_bundle()
        assembly.load.side_effect=ValueError('fixture')
        assembly.close.side_effect=OSError('fixture')
        with self.assertRaises(BaseExceptionGroup) as caught:
            _assemble_local(assembly=assembly,spec=None,query_pairs=[],receipt=None,expected_count=3)
        self.assertEqual(len(caught.exception.exceptions),2)

    def test_genuine_entry_held_before_any_callback(self):
        assembly=Mock()
        with self.assertRaises(DispatchHeld):load_authentic_local(assembly=assembly)
        assembly.load.assert_not_called()

    def test_loaded_bundle_handoff_and_success_release(self):
        bundle=PairedLocalBundle(object(),{},Mock())
        with patch('scripts.matched_baseline.paired_study_runtime._run_bound_study',return_value={'fixture':'ok'}) as run:
            result=_run_loaded_study(bundle=bundle,queries=(),configs={},quotas={},root='fixture',
                cap_nanodollars=1,byte_cap=8192,connection_factory=Mock(),bearer=Mock(),
                mode='SYNTHETIC_DEPENDENCY_COMPOSITION')
        self.assertEqual(result,{'fixture':'ok'})
        self.assertIs(run.call_args.kwargs['retrieval'],bundle.retrieval)
        bundle.close.assert_called_once()

    def test_loaded_bundle_failure_and_release_errors_preserved(self):
        bundle=PairedLocalBundle(object(),{},Mock(side_effect=OSError('fixture')))
        with patch('scripts.matched_baseline.paired_study_runtime._run_bound_study',side_effect=ValueError('fixture')):
            with self.assertRaises(BaseExceptionGroup) as caught:
                _run_loaded_study(bundle=bundle,queries=(),configs={},quotas={},root='fixture',
                    cap_nanodollars=1,byte_cap=8192,connection_factory=Mock(),bearer=Mock(),mode='SYNTHETIC_DEPENDENCY_COMPOSITION')
        self.assertEqual(len(caught.exception.exceptions),2)
        bundle.close.assert_called_once()


if __name__ == '__main__':unittest.main()
