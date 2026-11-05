import unittest,copy
from analyze_audited_results import analyze

def record(q,h,t):
    def arm(v):return {'judges':[{'faithfulness':v},{'faithfulness':v}],
        'composite':v,'verifier':{'sufficient':True}}
    return {'query_id':q,'route':'HARD','arms':{'H':arm(h),'T':arm(t)}}

class AnalysisTests(unittest.TestCase):
    def test_null_is_excluded_not_zero_and_bounds_use_all_assigned(self):
        rows=[record('B001',.25,.75),record('B002',None,.75)]
        ids=[{'query_id':r['query_id'],'category':'B_Evolutionary'} for r in rows]
        result=analyze(rows,ids)['summaries']['B']
        self.assertEqual(result['assigned'],2);self.assertEqual(result['eligible_pairs'],1)
        self.assertEqual(result['paired_mean_difference'],.5)
        self.assertEqual(result['assigned_cohort_worst_case_bounds'],[-.25,.75])
    def test_manifest_order_or_omission_rejected(self):
        with self.assertRaises(ValueError):analyze([record('B002',1,1)],[{'query_id':'B001','category':'B_Evolutionary'}])
    def test_all_null_primary_has_no_invented_estimate(self):
        result=analyze([record('B001',None,None)],[{'query_id':'B001','category':'B_Evolutionary'}])['summaries']['B']
        self.assertIsNone(result['paired_mean_difference']);self.assertIsNone(result['paired_bootstrap_95'])
        self.assertEqual(result['assigned_cohort_worst_case_bounds'],[-1,1])
    def test_composite_mismatch_rejected(self):
        r=record('B001',.5,.5);r['arms']['T']['composite']=1
        with self.assertRaises(ValueError):analyze([r],[{'query_id':'B001','category':'B_Evolutionary'}])

if __name__=='__main__':unittest.main()
