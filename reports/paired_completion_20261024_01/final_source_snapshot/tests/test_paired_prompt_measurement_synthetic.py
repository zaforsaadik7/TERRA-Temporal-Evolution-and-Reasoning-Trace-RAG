"""Tiny synthetic retrieval/tokenizer fixtures; no actual data, models or network."""
from dataclasses import replace
import unittest
from scripts.matched_baseline.paired_prompt_measurement import (
    RecordedRankingReader,parse_recorded_rankings,measure_queries,
)
from scripts.matched_baseline.paired_study_runtime import StudyQuery
from scripts.matched_baseline.paired_dependency_bridge import RetrievalComposition,digest
from scripts.matched_baseline.provider_accounting import canonical,ContractError
from tests import test_paired_dependency_bridge_synthetic as fixtures


class MeasurementTests(unittest.TestCase):
    def setup_case(self):
        f=fixtures.BridgeTests('runTest');f.setUp()
        queries=(StudyQuery('SYNTHETIC1','same query','A_Factual'),StudyQuery('SYNTHETIC2','same query','A_Factual'))
        ids=[str(i) for i in range(100)]
        records=[dict(query_id=q.query_id,query_text_sha256=digest(q.text.encode()),
            mode='AUTHENTIC_OFFLINE_FEASIBILITY',documents=20000,
            dense_candidate_ids=ids if n==0 else list(reversed(ids))) for n,q in enumerate(queries)]
        reader=RecordedRankingReader(records,queries)
        nodes={i:dict(f.nodes['1'],title='Synthetic '+i) for i in ids}
        retrieval=RetrievalComposition(reader,{i:'synthetic text' for i in ids},nodes,[])
        return f,queries,records,reader,retrieval

    def test_identical_query_texts_keep_distinct_recorded_id_bindings(self):
        _,queries,_,reader,_=self.setup_case()
        reader.activate(queries[0]);self.assertEqual(reader.query_dense_candidates(['same query'],top_k=100)[0][0],'0')
        reader.activate(queries[1]);self.assertEqual(reader.query_dense_candidates(['same query'],top_k=100)[0][0],'99')

    def test_full_measurement_hypothetical_routes_and_placeholder_truthful(self):
        f,queries,_,reader,retrieval=self.setup_case();events=[]
        summary=measure_queries(queries=queries,ranking_reader=reader,retrieval=retrieval,
            configs=f.configs,tokenizers=f.tokenizers,record=events.append,checkpoint=lambda:None)
        self.assertEqual(summary['status'],'LOCAL_PROMPT_MEASUREMENTS_PASS')
        self.assertEqual(summary['query_count'],2);self.assertEqual(summary['arm_route_records'],8)
        self.assertFalse(summary['actual_answers_measured']);self.assertEqual(summary['provider_calls'],0)
        self.assertEqual(summary['roles']['router']['count'],2)
        self.assertEqual(summary['roles']['judge2']['count'],8)

    def test_invalid_rank_query_hash_rejected(self):
        _,queries,records,_,_=self.setup_case();records[0]['query_text_sha256']='0'*64
        with self.assertRaises(ContractError):RecordedRankingReader(records,queries)

    def test_malformed_ledger_partial_json_and_duplicate_fields_rejected(self):
        for raw in (b'{}',b'{"x":1,"x":2}\n'):
            with self.assertRaises(ContractError):parse_recorded_rankings(raw)

    def test_judge_overflow_is_reported_not_hidden(self):
        f,queries,_,reader,retrieval=self.setup_case()
        f.tokenizers['judge2']=fixtures.ScaledTokenizer(100)
        summary=measure_queries(queries=queries,ranking_reader=reader,retrieval=retrieval,
            configs=f.configs,tokenizers=f.tokenizers,record=lambda _:None,checkpoint=lambda:None)
        self.assertEqual(summary['status'],'LOCAL_PROMPT_MEASUREMENTS_OVERFLOW')
        self.assertTrue(summary['overflows'])


if __name__=='__main__':unittest.main()
