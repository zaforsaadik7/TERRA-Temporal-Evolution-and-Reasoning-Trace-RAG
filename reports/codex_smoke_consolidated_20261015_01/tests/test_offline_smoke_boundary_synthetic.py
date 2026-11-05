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
