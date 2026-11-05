"""Pure budget proposal tests. No files, model assets or provider requests."""
import unittest
from scripts.matched_baseline.paired_study_candidate import candidate


class CandidateTests(unittest.TestCase):
    def test_no_execution_authority_or_verified_balance_claim(self):
        c=candidate()
        self.assertFalse(c['execution_authorized'])
        self.assertFalse(c['balance_independently_verified'])
        self.assertFalse(c['effective_account_rate_confirmed'])

    def test_within_user_ceiling_and_client_proposal(self):
        c=candidate()
        self.assertLess(c['proposed_client_cap_usd'],400)
        self.assertTrue(c['budget']['within_proposed_cap'])
        self.assertEqual(c['budget']['maximum_attempts'],3150)
        self.assertEqual(c['budget']['automatic_retries'],0)
        self.assertLess(c['budget']['maximum_nanodollars'],300*10**9)

    def test_exact_observed_ids_no_discovery_aliases(self):
        c=candidate()
        self.assertTrue(all(len(r['accepted_models'])==1 for r in c['roles']))
        self.assertEqual(c['roles'][-1]['accepted_models'],('gpt-oss-120b-080525',))


if __name__=='__main__':unittest.main()
