from dataclasses import replace
import unittest
from scripts.matched_baseline.provider_accounting import ContractError, Price, RoleConfig
from scripts.matched_baseline.matched_budget_preview import preview_budget


class MatchedBudgetPreviewSynthetic(unittest.TestCase):
    def setUp(self):
        self.configs=tuple(RoleConfig(r,'https://synthetic.invalid','fixture',('fixture',),
            10000,1000,100,20000,20000,30,Price('SYNTHETIC',10**9,2*10**9,True))
            for r in ('router','verifier','generator','judge1','judge2'))

    def test_3150_calls_and_no_authority(self):
        d=preview_budget(self.configs,spend_cap_nanodollars=10**12)
        self.assertEqual(d['maximum_attempts'],3150)
        self.assertEqual(d['maximum_nanodollars'],3150*1200000)
        self.assertFalse(d['live_admitted'])

    def test_smoke_allocated_separately(self):
        d=preview_budget(self.configs,study_queries=350,smoke_queries=2,spend_cap_nanodollars=10**12)
        self.assertEqual(d['maximum_attempts'],3168)
        self.assertEqual(sum(x['smoke_calls'] for x in d['roles'].values()),18)

    def test_low_cap_is_not_approved_automatically(self):
        d=preview_budget(self.configs,spend_cap_nanodollars=1)
        self.assertFalse(d['within_proposed_cap'])

    def test_fixed_charges_not_forgotten(self):
        d=preview_budget(self.configs,spend_cap_nanodollars=10**12,fixed_charges_nanodollars=99)
        self.assertEqual(d['maximum_nanodollars'],d['token_cost_nanodollars']+99)

    def test_duplicate_roles_and_bool_caps_rejected(self):
        with self.assertRaises(ContractError): preview_budget((self.configs[0],)*5,spend_cap_nanodollars=1)
        with self.assertRaises(ContractError): preview_budget(self.configs,spend_cap_nanodollars=True)

    def test_price_change_recalculates_without_altering_prior(self):
        a=preview_budget(self.configs,spend_cap_nanodollars=10**12)
        configs=tuple(replace(c,price=Price('SYNTHETIC_NEW',2*10**9,4*10**9,True)) for c in self.configs)
        b=preview_budget(configs,spend_cap_nanodollars=10**12)
        self.assertEqual(b['maximum_nanodollars'],2*a['maximum_nanodollars'])


if __name__=='__main__': unittest.main()
