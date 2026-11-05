import hashlib,json,unittest
from audit_core import *
class Tests(unittest.TestCase):
 def test_duplicate_same_cohort_fails(self):
  with self.assertRaises(ValueError):unique([{'c':'a','q':'1'},{'c':'a','q':'1'}],['c','q'])
 def test_cross_cohort_id_is_not_duplicate(self):self.assertEqual(len(unique([{'c':'a','q':'1'},{'c':'b','q':'1'}],['c','q'])),2)
 def test_pipeline_pairing_distinct(self):self.assertEqual(len(unique([{'q':'1','a':'H'},{'q':'1','a':'T'}],['q','a'])),2)
 def test_zero_denominator(self):self.assertIsNone(fraction(0,0)['fraction'])
 def test_bad_fraction(self):
  with self.assertRaises(ValueError):fraction(3,2)
 def test_abstention_is_not_substantive(self):self.assertEqual(judge_proxy_bounds(['EXPLICIT_ABSTENTION']*2),(0,0))
 def test_judge_disagreement_unknown(self):self.assertEqual(consensus_status(['EXPLICIT_ABSTENTION','SUBSTANTIVE_ANSWER']),'unclassifiable')
 def test_mixed_not_full(self):self.assertEqual(consensus_status(['MIXED_OR_UNCERTAIN']*2),'partial_or_mixed')
 def test_refutation_separate(self):self.assertEqual(consensus_status(['PREMISE_REFUTATION']*2),'premise_refutation')
 def test_invalid_outcome(self):
  with self.assertRaises(ValueError):consensus_status(['NEW','NEW'])
 def test_sampling_exact(self):self.assertEqual(str(positive_weight(10,75)[0]),'2/15')
 def test_sampling_not_uniform(self):self.assertNotEqual(positive_weight(10,75)[0],positive_weight(10,100)[0])
 def test_targeted_cases_no_fake_probability(self):
  with self.assertRaises(ValueError):positive_weight(0,350)
 def test_self_reference_excluded(self):
  x=verifier_rates([{'input_verified':True,'reference':'sufficient','passed':False,'reference_basis':'verifier_self'}]);self.assertEqual(x['eligible'],0);self.assertIsNone(x['confusion_matrix'])
 def test_high_refusal_score_not_gold(self):self.assertEqual(verifier_rates([{'input_verified':True,'reference':'sufficient','passed':False,'reference_basis':'judge_abstention_score'}])['eligible'],0)
 def test_missing_input_excluded(self):self.assertEqual(verifier_rates([{'input_verified':False,'reference':'sufficient','passed':True,'reference_basis':'independent_reference'}])['eligible'],0)
 def test_unreviewed_reference_name_excluded(self):self.assertEqual(verifier_rates([{'input_verified':True,'reference':'sufficient','passed':True,'reference_basis':'same_model_rationale_renamed'}])['eligible'],0)
 def test_rates_have_correct_denominators(self):
  x=verifier_rates([{'input_verified':True,'reference':r,'passed':p,'reference_basis':'independent_reference'} for r,p in [('sufficient',True),('sufficient',False),('insufficient',True)]])
  self.assertEqual(x['false_rejection_rate']['denominator'],2);self.assertEqual(x['false_acceptance_rate']['denominator'],1)
 def test_request_hash_not_reserialized(self):
  s=json.dumps({'messages':[{'role':'user','content':json.dumps({'query':'q','evidence':'é'})}]},ensure_ascii=False);self.assertEqual(verify_request(s,hashlib.sha256(s.encode()).hexdigest())['query'],'q')
  with self.assertRaises(ValueError):verify_request(s+' ',hashlib.sha256(s.encode()).hexdigest())
 def test_missing_request_not_rationale(self):
  s=json.dumps({'reason':'trust me'})
  with self.assertRaises(ValueError):verify_request(s,hashlib.sha256(s.encode()).hexdigest())
 def test_author_mixed_preserved(self):
  x=author_counts([{'response_status':'mixed refusal/substantive answer','source_correctness':'supported'},{'response_status':'substantive answer','source_correctness':'uncertain'}]);self.assertEqual(x['non_refusal']['numerator'],2);self.assertEqual(x['supported_answer_proxy']['numerator'],1)
if __name__=='__main__':unittest.main()
