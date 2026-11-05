"""Generated corpus/query data and temporary evidence folders, never real assets."""
import itertools
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from scripts.matched_baseline.offline_cohort_contracts import ProposedResources
from scripts.matched_baseline.offline_cohort_controls import StageTelemetry,ByteBudget
from scripts.matched_baseline.offline_cohort_evidence import CohortEvidenceWriter
from scripts.matched_baseline.offline_cohort_worker import PreparedCohortWorker,run_synthetic_to_evidence
from scripts.matched_baseline.offline_preflight import OfflinePreflightDriver,MockBpeTokenizer
from tests import test_offline_cohort_core_synthetic as fixtures


class EvidenceSinkTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)/'evidence'

    def test_exclusive_directory_and_no_overwrite(self):
        writer=CohortEvidenceWriter(self.directory,budget_bytes=100)
        self.addCleanup(writer.close)
        writer.write_bytes('record.json',b'original',max_bytes=100)
        with self.assertRaises(FileExistsError):CohortEvidenceWriter(self.directory,budget_bytes=100)
        with self.assertRaises(FileExistsError):writer.new_stream('record.json',max_bytes=100)
        self.assertEqual((self.directory/'record.json').read_bytes(),b'original')

    def test_shared_reservation_and_single_telemetry_charge(self):
        writer=CohortEvidenceWriter(self.directory,budget_bytes=4096);self.addCleanup(writer.close)
        stream=writer.new_stream('telemetry.jsonl',max_bytes=4096)
        ticks=iter([1.0,2.0])
        telemetry=StageTelemetry(clock=lambda:next(ticks),budget=writer.budget,sink=stream._write_reserved)
        with telemetry.measure('DENSE_BATCH',index=0):pass
        self.assertEqual(writer.budget.charged,(self.directory/'telemetry.jsonl').stat().st_size)
        self.assertEqual(json.loads((self.directory/'telemetry.jsonl').read_bytes())['elapsed_seconds'],1)

    def test_file_or_aggregate_limit_preserves_partial_bytes(self):
        writer=CohortEvidenceWriter(self.directory,budget_bytes=10);self.addCleanup(writer.close)
        stream=writer.new_stream('partial.log',max_bytes=3);stream.write(b'ab')
        with self.assertRaises(ValueError):stream.write(b'cd')
        self.assertEqual((self.directory/'partial.log').read_bytes(),b'ab')
        other=writer.new_stream('other.log',max_bytes=10)
        with self.assertRaises(ValueError):other.write(b'x'*10)
        self.assertEqual((self.directory/'other.log').stat().st_size,0)

    def test_invalid_names_and_count_fail_before_open(self):
        writer=CohortEvidenceWriter(self.directory,budget_bytes=100,max_streams=1)
        self.addCleanup(writer.close)
        for name in ('../escape','a/b','C:stream','CON.txt','NUL','trailing.'):
            with self.assertRaises(ValueError):writer.new_stream(name,max_bytes=100)
        writer.new_stream('one.json',max_bytes=100)
        with self.assertRaises(ValueError):writer.new_stream('two.json',max_bytes=100)

    def test_closed_writer_and_stream_cannot_write(self):
        writer=CohortEvidenceWriter(self.directory,budget_bytes=100)
        stream=writer.new_stream('one.log',max_bytes=100);writer.close()
        with self.assertRaises(ValueError):stream.write(b'x')
        with self.assertRaises(ValueError):writer.new_stream('new.log',max_bytes=100)


class CohortWorkerTests(unittest.TestCase):
    def setUp(self):
        self.spec=fixtures.fixture_spec();self.resources=ProposedResources()
        self.pairs=[(row.query_id,f'text {row.query_id[0]}{int(row.query_id[1:])}') for row in self.spec.queries]
        self.corpus={f'doc-{i:05d}':'fixture legal text' for i in range(20000)}
        self.nodes={key:{'title':key,'decision_date':'2020','holding':'fixture holding',
            'snippet':'fixture text','thinking_trace':'fixture scaffold'} for key in self.corpus}
        self.ids=list(self.corpus)[:100]
        self.reader=SimpleNamespace(extract_layer1_corpus=Mock(return_value=self.corpus),
            query_dense_candidates=Mock(side_effect=lambda texts,top_k:[list(self.ids) for _ in texts]))
        self.roles=object.__new__(OfflinePreflightDriver)._build_default_mock_role_configs(tok=MockBpeTokenizer())
        self.ticks=itertools.count(step=0.01)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)

    def test_complete_generated_cohort_writes_350_700_and_all_batch_timings(self):
        writer=CohortEvidenceWriter(Path(self.temp.name)/'complete',budget_bytes=self.resources.evidence_bytes)
        report=run_synthetic_to_evidence(spec=self.spec,query_pairs=self.pairs,reader=self.reader,
            nodes=self.nodes,edges=[],role_configs=self.roles,resources=self.resources,
            writer=writer,clock=lambda:next(self.ticks))
        parsed=json.loads(report)
        self.assertTrue(parsed['complete']);self.assertEqual(parsed['query_count'],350)
        self.assertEqual(parsed['route_record_count'],700)
        self.assertEqual(parsed['mode'],'SIMULATED')
        folder=writer.directory
        rows=(folder/'query_records.jsonl').read_text().splitlines()
        self.assertEqual(len(rows),350)
        telemetry=[json.loads(row) for row in (folder/'telemetry.jsonl').read_text().splitlines()]
        batches=[r for r in telemetry if r['stage']=='DENSE_BATCH']
        self.assertEqual([r['index'] for r in batches],list(range(11)))
        self.assertEqual(sum(r['stage']=='ROUTE_ENVELOPE' for r in telemetry),700)
        self.assertEqual(writer.budget.charged,sum(p.stat().st_size for p in folder.iterdir()))
        self.assertTrue(writer.closed)
        self.reader.extract_layer1_corpus.assert_called_once_with(expected_count=20000)

    def test_bad_query_identity_fails_before_corpus_or_dense_calls(self):
        telemetry=StageTelemetry(clock=lambda:next(self.ticks),budget=ByteBudget(10000),sink=lambda raw:len(raw))
        worker=PreparedCohortWorker(reader=self.reader,nodes=self.nodes,edges=[],role_configs=self.roles,
            resources=self.resources,telemetry=telemetry)
        bad=list(self.pairs);bad[0]=(bad[0][0],'altered')
        with self.assertRaises(ValueError):worker.run(self.spec,bad,on_record=lambda raw:None)
        self.reader.extract_layer1_corpus.assert_not_called()
        with self.assertRaisesRegex(RuntimeError,'retry'):worker.run(self.spec,self.pairs,on_record=lambda raw:None)

    def test_dense_failure_preserves_incomplete_evidence_and_does_not_retry(self):
        self.reader.query_dense_candidates.side_effect=RuntimeError('fixture failure')
        writer=CohortEvidenceWriter(Path(self.temp.name)/'failed',budget_bytes=self.resources.evidence_bytes)
        with self.assertRaises(RuntimeError):run_synthetic_to_evidence(spec=self.spec,query_pairs=self.pairs,
            reader=self.reader,nodes=self.nodes,edges=[],role_configs=self.roles,resources=self.resources,
            writer=writer,clock=lambda:next(self.ticks))
        self.reader.query_dense_candidates.assert_called_once()
        self.assertFalse((writer.directory/'cohort_report.json').exists())
        self.assertEqual(json.loads((writer.directory/'failure.json').read_bytes())['status'],'FAILED_INCOMPLETE')
        telemetry=[json.loads(row) for row in (writer.directory/'telemetry.jsonl').read_text().splitlines()]
        self.assertFalse(telemetry[-1]['computation_completed']);self.assertTrue(writer.closed)

    def test_graph_population_failure_precedes_corpus_and_dense(self):
        telemetry=StageTelemetry(clock=lambda:next(self.ticks),budget=ByteBudget(10000),sink=lambda raw:len(raw))
        worker=PreparedCohortWorker(reader=self.reader,nodes={},edges=[],role_configs=self.roles,
            resources=self.resources,telemetry=telemetry)
        with self.assertRaises(ValueError):worker.run(self.spec,self.pairs,on_record=lambda raw:None)
        self.reader.extract_layer1_corpus.assert_not_called()

    def test_authentic_dependency_entry_rejected(self):
        with self.assertRaises(RuntimeError):PreparedCohortWorker(reader=self.reader,nodes=self.nodes,
            edges=[],role_configs=self.roles,resources=self.resources,telemetry=None,is_synthetic=False)
        self.reader.extract_layer1_corpus.assert_not_called()


if __name__=='__main__':unittest.main()
