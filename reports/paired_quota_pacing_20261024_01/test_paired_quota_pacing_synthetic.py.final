"""Fake-clock pacing and temporary study integration; no actual sleeping/network."""
from dataclasses import replace
import unittest
from unittest.mock import Mock

from scripts.matched_baseline.paired_quota_pacing import (
    PacingPolicy, validate_shared_quotas, reserve_with_pacing,
)
from scripts.matched_baseline.provider_run_control import EndpointLimiter, EndpointQuota, RateWait
from scripts.matched_baseline.provider_accounting import ContractError, DispatchHeld
from tests import test_paired_dependency_bridge_synthetic as fixtures


class Clock:
    def __init__(self):self.value=0;self.sleeps=[]
    def now(self):return self.value
    def pause(self,seconds):self.sleeps.append(seconds);self.value+=seconds


class PacingTests(unittest.TestCase):
    def setUp(self):
        f=fixtures.BridgeTests('runTest');f.setUp()
        self.configs=f.configs
        self.cfg=f.configs['generator']
        self.quota=EndpointQuota(7000,10000,1000)
        self.limiter=EndpointLimiter();self.clock=Clock();self.events=[]

    def reserve(self,**updates):
        options=dict(limiter=self.limiter,config=self.cfg,quota=self.quota,
            policy=PacingPolicy(60,1.0,61),now=self.clock.now,pause=self.clock.pause,
            cancelled=lambda:False,record=self.events.append,call_key='Q001:H:generator')
        options.update(updates)
        return reserve_with_pacing(**options)

    def test_available_no_sleep(self):
        self.reserve();self.assertEqual(self.clock.sleeps,[])

    def test_input_window_paces_only_unsent_call(self):
        self.reserve();self.reserve()
        self.assertEqual(self.clock.value,60)
        self.assertEqual(len(self.clock.sleeps),60)
        self.assertTrue(all(e['request_sent'] is False for e in self.events))
        history=next(iter(self.limiter.histories.values()))
        self.assertEqual(len(history),2)

    def test_fail_fast_default_preserves_ratewait(self):
        self.reserve()
        with self.assertRaises(RateWait):self.reserve(policy=PacingPolicy())
        self.assertEqual(self.clock.sleeps,[])

    def test_wait_deadline_no_admission(self):
        self.reserve()
        with self.assertRaises(RateWait):self.reserve(policy=PacingPolicy(2,1,3))
        self.assertEqual(self.clock.value,2)
        self.assertEqual(len(next(iter(self.limiter.histories.values()))),1)

    def test_cancel_before_admission(self):
        with self.assertRaises(DispatchHeld):self.reserve(cancelled=lambda:True)
        self.assertEqual(self.limiter.histories,{})

    def test_cancel_during_wait(self):
        self.reserve()
        with self.assertRaises(DispatchHeld):self.reserve(cancelled=lambda:self.clock.value>=1)
        self.assertEqual(self.clock.sleeps,[1])

    def test_wait_evidence_failure_before_pause(self):
        self.reserve()
        record=Mock(side_effect=OSError('fixture'))
        with self.assertRaises(OSError):self.reserve(record=record)
        self.assertEqual(self.clock.sleeps,[])

    def test_frozen_clock_check_limit_terminates(self):
        self.reserve()
        with self.assertRaises(DispatchHeld):
            self.reserve(policy=PacingPolicy(60,1,3),pause=lambda _:None)

    def test_clock_regression_rejected(self):
        self.reserve()
        values=iter([2,1])
        with self.assertRaises(ContractError):self.reserve(now=lambda:next(values))

    def test_one_call_larger_than_quota_rejected_not_waited(self):
        with self.assertRaises(ContractError):self.reserve(quota=EndpointQuota(10,10000,1000))
        self.assertEqual(self.clock.sleeps,[])

    def test_queries_per_hour_wait_is_bounded(self):
        self.quota=EndpointQuota(1000000,1000000,1)
        self.reserve()
        with self.assertRaises(RateWait):self.reserve(policy=PacingPolicy(2,1,3))
        self.assertEqual(self.clock.value,2)

    def test_output_window_paced_even_if_input_available(self):
        self.quota=EndpointQuota(1000000,self.cfg.max_output_tokens,1000)
        self.reserve();self.reserve()
        self.assertEqual(self.clock.value,60)

    def test_shared_endpoint_conflict_prevalidated(self):
        self.configs['verifier']=replace(self.configs['verifier'],endpoint=self.cfg.endpoint)
        quotas={r:EndpointQuota(1000000,1000000,1000) for r in self.configs}
        quotas['verifier']=EndpointQuota(999999,1000000,1000)
        with self.assertRaises(ContractError):validate_shared_quotas(self.configs,quotas)

    def test_invalid_policy_values(self):
        for args in ((True,1,1),(-1,1,1),(1,0,1),(1,float('nan'),1),(1,2,1),(1,1,False)):
            with self.subTest(args=args),self.assertRaises(ContractError):PacingPolicy(*args)


if __name__=='__main__':unittest.main()
