"""Fake backend only; no firewall queries or mutation."""
from dataclasses import asdict
import unittest
from scripts.matched_baseline.offline_smoke_boundary import (
    BoundaryFailure, BoundaryReceipt, OwnedSmokeBoundary)


class FakeBackend:
    def __init__(self):
        self.rule = None
        self.operations = []
        self.state = {"administrator": True, "service": "Running",
                      "profiles": {k: True for k in ("Domain", "Private", "Public")},
                      "known_other_pids": [], "unreadable_process_count": 3}
        self.fail_after_create = False
        self.fail_remove = False

    def environment(self, program):
        return self.state

    def query(self, name):
        return self.rule

    def create(self, receipt):
        self.operations.append("create")
        self.rule = {**asdict(receipt), "direction": "Outbound", "action": "Block",
                     "profile": "Any", "enabled": True}
        if self.fail_after_create:
            raise RuntimeError("lost creation response")

    def remove(self, name):
        self.operations.append("remove")
        if not self.fail_remove:
            self.rule = None


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeBackend()
        self.receipt = BoundaryReceipt("TERRA_Smoke_fake_run_001", "synthetic-python", "owner-001")
        self.boundary = OwnedSmokeBoundary(self.backend, self.receipt)

    def test_owned_create_remove(self):
        receipt = self.boundary.create()
        self.boundary.verify(receipt)
        self.boundary.remove(receipt)
        self.assertEqual(self.backend.operations, ["create", "remove"])
        self.assertFalse(self.boundary.owned)

    def test_prechecks_stop_creation(self):
        for key, value, reason in (
            ("administrator", False, "Administrator"),
            ("service", "Stopped", "service"),
            ("profiles", {}, "Incomplete"),
            ("profiles", {"Domain": True, "Private": False, "Public": True}, "Disabled"),
            ("known_other_pids", [123], "competing")):
            with self.subTest(key=key, value=value):
                self.setUp()
                self.backend.state[key] = value
                with self.assertRaisesRegex(BoundaryFailure, reason):
                    self.boundary.create()
                self.assertEqual(self.backend.operations, [])

    def test_collision_preserved(self):
        self.backend.rule = {"owner_tag": "foreign"}
        with self.assertRaisesRegex(BoundaryFailure, "collision"):
            self.boundary.create()
        self.assertEqual(self.backend.operations, [])

    def test_ambiguous_creation_recovers_owned_rule(self):
        self.backend.fail_after_create = True
        with self.assertRaisesRegex(BoundaryFailure, "Creation failed"):
            self.boundary.create()
        self.assertEqual(self.backend.operations, ["create", "remove"])
        self.assertIsNone(self.backend.rule)
        with self.assertRaisesRegex(BoundaryFailure, "retried"):
            self.boundary.create()

    def test_failed_removal_retains_owned_state(self):
        self.boundary.create()
        self.backend.fail_remove = True
        with self.assertRaisesRegex(BoundaryFailure, "not verified"):
            self.boundary.remove(self.receipt)
        self.assertTrue(self.boundary.owned)

    def test_changed_rule_not_deleted(self):
        self.boundary.create()
        self.backend.rule["owner_tag"] = "foreign"
        with self.assertRaisesRegex(BoundaryFailure, "verification"):
            self.boundary.remove(self.receipt)
        self.assertEqual(self.backend.operations, ["create"])

    def test_native_backend_stays_blocked(self):
        with self.assertRaisesRegex(BoundaryFailure, "not admitted"):
            OwnedSmokeBoundary(self.backend, self.receipt, is_synthetic=False)

    def owned_controller(self):
        self.backend.state.update(known_other_pids=[123],adapter_parent_pid=123,
            verified_controller={'pid':123,'program':self.receipt.program,'start_ticks':'639000000000000001'})
        return OwnedSmokeBoundary(self.backend,self.receipt,controller_pid=123)

    def test_only_verified_owned_controller_can_remain(self):
        boundary = self.owned_controller()
        state = boundary.preflight()
        self.assertEqual(state['known_other_pids'],[123])  # evidence is not filtered
        boundary.create()
        boundary.remove(self.receipt)
        self.assertEqual(self.backend.operations,['create','remove'])

    def test_extra_matching_process_stops_before_creation(self):
        boundary = self.owned_controller()
        self.backend.state['known_other_pids'].append(456)
        with self.assertRaisesRegex(BoundaryFailure,'competing'):
            boundary.create()
        self.assertEqual(self.backend.operations,[])

    def test_unverified_parent_or_reused_pid_fails(self):
        for key,value in [('adapter_parent_pid',456),('verified_controller',None),('known_other_pids',[])]:
            with self.subTest(key=key):
                boundary = self.owned_controller()
                self.backend.state[key] = value
                with self.assertRaisesRegex(BoundaryFailure,'identity not verified'):
                    boundary.create()
                self.assertEqual(self.backend.operations,[])
        boundary = self.owned_controller()
        boundary.preflight()
        self.backend.state['verified_controller']['start_ticks'] = '639000000000000002'
        with self.assertRaisesRegex(BoundaryFailure,'identity changed'):
            boundary.create()

    def test_pid_image_and_inventory_types_fail_closed(self):
        for identity in ({'pid':True,'program':self.receipt.program,'start_ticks':'1'},
                         {'pid':123,'program':'foreign','start_ticks':'1'},
                         {'pid':123,'program':self.receipt.program,'start_ticks':1}):
            boundary = self.owned_controller()
            self.backend.state['verified_controller'] = identity
            with self.assertRaisesRegex(BoundaryFailure,'identity not verified'):
                boundary.preflight()
        boundary = self.owned_controller()
        self.backend.state['known_other_pids'] = [123,123]
        with self.assertRaisesRegex(BoundaryFailure,'Invalid known-process'):
            boundary.preflight()
