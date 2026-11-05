"""Parent admission using generated temporary trees and mock dispatch only."""
from dataclasses import asdict,replace
from hashlib import sha256
from pathlib import Path
import tempfile
import json
import unittest
from unittest.mock import Mock,patch
from scripts.matched_baseline import offline_cohort_parent as parent
from scripts.matched_baseline.offline_cohort_contracts import ProposedResources
from scripts.matched_baseline.offline_cohort_loader import CohortLoadPlan
from scripts.matched_baseline.offline_cohort_input import FilePin,read_fixture_benchmark
from tests import test_offline_cohort_execution_synthetic as fixtures


class ParentTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.BindingTests();self.f.setUp()
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        files={'benchmark.json':self.f.raw,'graph.xz':b'synthetic graph placeholder',
            'source/chroma.sqlite3':b'synthetic store placeholder',
            'cache/model.onnx':b'synthetic cache placeholder',
            'tokens/tokenizer.json':b'synthetic tokenizer placeholder'}
        for relative,raw in files.items():
            path=self.root/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        self.pins=tuple(FilePin(str(self.root/relative),len(raw),sha256(raw).hexdigest())
                        for relative,raw in sorted(files.items()))
        self.roots=tuple(parent.RootMembers(str(self.root/name),tuple(sorted(
            path.relative_to(self.root/name).as_posix() for path in (self.root/name).rglob('*')
            if path.is_file()))) for name in ('source','cache','tokens'))
        graph=next(pin for pin in self.pins if pin.path==str(self.root/'graph.xz'))
        self.plan=CohortLoadPlan(str(self.root),str(self.root/'source'),str(self.root/'cache'),
            graph.path,str(self.root/'tokens'),graph.sha256)
        self.review=parent.ParentReview(self.f.spec,self.plan,ProposedResources(),
            self.pins,self.roots,str(self.root/'benchmark.json'),True)
        self.observer=Mock(side_effect=self.observe)
        self.reader=Mock(side_effect=self.read)

    def observe(self,review):
        # Real observation of generated fixture files, never genuine assets.
        pins=tuple(FilePin(pin.path,Path(pin.path).stat().st_size,
                          sha256(Path(pin.path).read_bytes()).hexdigest()) for pin in review.pins)
        roots=tuple(parent.RootMembers(root.root,tuple(sorted(
            p.relative_to(Path(root.root)).as_posix() for p in Path(root.root).rglob('*')
            if p.is_file()))) for root in review.roots)
        return pins,roots

    def read(self,review):
        pin=next(p for p in review.pins if p.path==review.benchmark_path)
        return read_fixture_benchmark(path=review.benchmark_path,fixture_root=self.root,
                                      reviewed_pin=pin,spec=review.spec)

    def admission(self):
        return parent.ParentReceiptAdmission(candidate=self.review,reviewed=self.review)

    def prepare(self,admission):
        if not admission.authority_attempted:self.authorize(admission)
        return admission.prepare(observe_inventory=self.observer,read_benchmark=self.reader)

    def authorize(self,admission,**changes):
        # Generated test record, not an assertion of actual human approval.
        record=dict(approval_id='SYNTHETIC_FIXTURE_ONLY',approval_date='2026-10-23',
            scope=self.review.spec.scope,request_sha256=sha256(self.review.spec.request_bytes()).hexdigest(),
            resources=asdict(self.review.resources),launch_binding_sha256='a'*64,
            rule_name='TERRA_Cohort_FIXTURE_ONLY',owner_tag='TERRA_COHORT_FIXTURE_ONLY',
            max_attempts=1,allow_api_calls=False,allow_manuscript_changes=False)
        record.update(changes);raw=json.dumps(record).encode()
        admission.authorize_fixture(raw,expected_sha256=sha256(raw).hexdigest(),
            reviewed_record=record,reviewed_launch_binding_sha256='a'*64)

    def test_observation_to_receipt_to_single_worker_dispatch(self):
        admission=self.admission();handoff=self.prepare(admission)
        dispatcher=Mock(return_value='synthetic dispatched')
        digest=handoff.digest()
        self.assertEqual(admission.dispatch(handoff,reviewed_handoff_sha256=digest,
                         dispatcher=dispatcher),'synthetic dispatched')
        dispatcher.assert_called_once_with(handoff)
        with self.assertRaises(RuntimeError):admission.dispatch(handoff,
            reviewed_handoff_sha256=digest,dispatcher=dispatcher)
        self.assertEqual(handoff.binding.query_pairs,tuple(self.f.f.f.pairs))
        self.assertNotIn('excluded target',repr(handoff))

    def test_changed_file_stops_before_benchmark_reader(self):
        (self.root/'graph.xz').write_bytes(b'changed fixture')
        admission=self.admission()
        with self.assertRaises(ValueError):self.prepare(admission)
        self.reader.assert_not_called()
        with self.assertRaises(RuntimeError):self.prepare(admission)

    def test_extra_full_root_file_stops_before_benchmark_reader(self):
        (self.root/'cache'/'extra').write_bytes(b'new fixture')
        with self.assertRaises(ValueError):self.prepare(self.admission())
        self.reader.assert_not_called()

    def test_missing_full_root_member_stops(self):
        pins,roots=self.observe(self.review)
        self.observer.side_effect=None
        self.observer.return_value=(pins,(replace(roots[0],members=()),)+roots[1:])
        with self.assertRaises(ValueError):self.prepare(self.admission())
        self.reader.assert_not_called()

    def test_missing_required_roots_and_overlap_rejected(self):
        for roots in (self.roots[:-1],self.roots+(parent.RootMembers(str(self.root),()),)):
            with self.assertRaises(ValueError):replace(self.review,roots=roots).validate()

    def test_relative_member_aliases_and_traversal_rejected(self):
        for members in (('../x',),('x\\y',),('x','X'),('b','a'),('x:stream',)):
            with self.assertRaises(ValueError):parent.RootMembers(str(self.root),members).validate()

    def test_context_change_rejected_before_observation(self):
        changed=replace(self.review,resources=replace(self.review.resources,child_seconds=1))
        with self.assertRaises(ValueError):parent.ParentReceiptAdmission(candidate=changed,reviewed=self.review)
        self.observer.assert_not_called()

    def test_binding_must_match_observed_receipt(self):
        receipt,binding=self.read(self.review)
        self.reader.side_effect=None
        self.reader.return_value=(receipt,replace(binding,content_sha256='0'*64))
        with self.assertRaises(ValueError):self.prepare(self.admission())

    def test_wrong_fixture_mode_rejected(self):
        receipt,binding=self.read(self.review)
        for value in (parent.WorkerHandoff(self.review,replace(receipt,synthetic_fixture=False),binding),
                      parent.WorkerHandoff(self.review,receipt,replace(binding,synthetic_fixture=False))):
            with self.assertRaises(ValueError):value.validate()

    def test_replaced_handoff_or_unreviewed_digest_stops_dispatch(self):
        admission=self.admission();handoff=self.prepare(admission)
        dispatch=Mock()
        with self.assertRaises(ValueError):admission.dispatch(handoff,
            reviewed_handoff_sha256='0'*64,dispatcher=dispatch)
        dispatch.assert_not_called()
        altered=replace(handoff,binding=replace(handoff.binding,query_pairs=tuple(reversed(handoff.binding.query_pairs))))
        with self.assertRaises(ValueError):altered.digest()

    def test_fixed_worker_bridge_passes_query_binding_not_raw_benchmark(self):
        handoff=self.prepare(self.admission());writer=object()
        with patch.object(parent,'_run_bound',return_value=b'SIMULATED') as run:
            result=parent.synthetic_worker_handoff(handoff,reviewed_handoff_sha256=handoff.digest(),
                isolation_receipt=object(),runtime={},writer=writer,clock=None,guard=None)
        self.assertEqual(result,b'SIMULATED')
        self.assertIs(run.call_args.kwargs['binding'],handoff.binding)
        self.assertNotIn('raw',run.call_args.kwargs)
        self.assertIs(run.call_args.kwargs['worker_factory'],parent.PreparedCohortWorker)

    def test_authentic_admission_and_bridge_rejected_before_callbacks(self):
        with self.assertRaises(RuntimeError):parent.ParentReceiptAdmission(
            candidate=None,reviewed=None,is_synthetic=False)
        with self.assertRaises(RuntimeError):parent.synthetic_worker_handoff(None,
            reviewed_handoff_sha256=None,isolation_receipt=None,runtime=None,
            writer=None,clock=None,guard=None,is_synthetic=False)
        self.assertEqual(parent.main(),2)
        self.observer.assert_not_called();self.reader.assert_not_called()

    def test_no_observation_before_authority_data_validation(self):
        admission=self.admission()
        with self.assertRaises(ValueError):admission.prepare(
            observe_inventory=self.observer,read_benchmark=self.reader)
        self.observer.assert_not_called();self.reader.assert_not_called()

    def test_bad_authority_scope_or_launch_pin_cannot_retry(self):
        for changes in (dict(allow_api_calls=True),dict(launch_binding_sha256='b'*64)):
            admission=self.admission()
            with self.assertRaises(ValueError):self.authorize(admission,**changes)
            with self.assertRaises(RuntimeError):self.authorize(admission)
            with self.assertRaises(ValueError):admission.prepare(
                observe_inventory=self.observer,read_benchmark=self.reader)
        self.observer.assert_not_called()


if __name__=='__main__':unittest.main()
