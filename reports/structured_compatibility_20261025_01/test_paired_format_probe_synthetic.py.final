import json,tempfile,time,unittest
from pathlib import Path
from tests import test_paired_output_format_synthetic as fixtures
from scripts.matched_baseline.paired_format_probe import execute,main
from scripts.matched_baseline.provider_accounting import BudgetJournal

class ProbeTests(unittest.TestCase):
    def test_held_entry(self):self.assertEqual(main([]),2)
    def test_five_calls_same_schema_path_and_actual_generator_answer(self):
        owner=fixtures.StructuredOutputTests('runTest');f=owner.fixture();self.addCleanup(owner.doCleanups)
        out=Path(f.tmp.name)/'probe'
        result=execute(out=out,configs=f.f.configs,tokenizers=f.f.tokenizers,factory=f.connection,
            bearer=lambda:'SYNTHETIC',deadline=100,now=lambda:0)
        self.assertEqual(result['status'],'FIVE_ROLE_COMPATIBILITY_PASS')
        self.assertEqual(len(f.connections),5)
        self.assertEqual(len(BudgetJournal.inspect(out/'calls.jsonl')['states']),5)
        for c in f.connections[-2:]:
            payload=json.loads(json.loads(c.requests[0][2])['messages'][1]['content'])
            self.assertEqual(payload['candidate_answer'],'synthetic generated answer')
    def test_first_invalid_stops_no_retry_and_settles(self):
        owner=fixtures.StructuredOutputTests('runTest');f=owner.fixture();self.addCleanup(owner.doCleanups)
        f.bad_stage='router';out=Path(f.tmp.name)/'probe'
        result=execute(out=out,configs=f.f.configs,tokenizers=f.f.tokenizers,factory=f.connection,
            bearer=lambda:'SYNTHETIC',deadline=100,now=lambda:0)
        self.assertEqual(result['status'],'STOPPED_NO_RETRY');self.assertEqual(len(f.connections),1)
        self.assertEqual(list(BudgetJournal.inspect(out/'calls.jsonl')['states'].values()),['SETTLE'])

    def test_advancing_clock_completes_five_mock_requests(self):
        owner=fixtures.StructuredOutputTests('runTest');f=owner.fixture();self.addCleanup(owner.doCleanups)
        import itertools
        clock=itertools.count(0,0.000001)
        result=execute(out=Path(f.tmp.name)/'advancing',configs=f.f.configs,tokenizers=f.f.tokenizers,
            factory=f.connection,bearer=lambda:'SYNTHETIC',deadline=100,now=lambda:next(clock))
        self.assertEqual(result['status'],'FIVE_ROLE_COMPATIBILITY_PASS')
        self.assertEqual(len(f.connections),5)

if __name__=='__main__':unittest.main()
