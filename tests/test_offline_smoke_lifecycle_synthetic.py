"""Pure mock lifecycle tests; no protected assets or real OS operations."""
import unittest
from scripts.matched_baseline.offline_smoke_lifecycle import (
    SmokeLifecycle, ChildProcessResult, ChildExecutionFailure)


class SmokeLifecycleTests(unittest.TestCase):
    def build(self, fail=None, result=None):
        self.events = []
        self.records = []
        def hook(name, value=None):
            def call(*args):
                self.events.append(name)
                if fail == name:
                    raise RuntimeError(name)
                if name == "terminal_record":
                    self.records.append(args[0])
                return value
            return call
        keys = ["preflight", "acquire_lock", "verify_boundary", "remove_boundary",
                "verify_absence", "postcheck", "start_record", "close_transcript",
                "terminal_record"]
        kwargs = {key: hook(key) for key in keys}
        kwargs["create_boundary"] = hook("create_boundary", "owned-receipt")
        kwargs["run_child"] = hook("run_child", result if result is not None else
                                   ChildProcessResult(True, 0))
        return SmokeLifecycle(**kwargs)

    def test_success_order_and_label(self):
        outcome = self.build().run()
        self.assertEqual(outcome.status, "SIMULATED_SUCCESS")
        self.assertEqual(self.events, ["start_record", "preflight", "create_boundary",
            "verify_boundary", "acquire_lock", "run_child", "remove_boundary",
            "verify_absence", "postcheck", "close_transcript", "terminal_record"])

    def test_prelaunch_failures_no_child_or_spent_lock(self):
        for failure in ("start_record", "preflight", "create_boundary", "verify_boundary"):
            with self.subTest(failure=failure):
                outcome = self.build(fail=failure).run()
                self.assertEqual(outcome.status, "FAIL")
                self.assertNotIn("run_child", self.events)
                self.assertNotIn("acquire_lock", self.events)
                self.assertIn(failure, outcome.failures[0])

    def test_finalization_failures_never_success(self):
        for failure in ("remove_boundary", "verify_absence", "postcheck", "close_transcript"):
            with self.subTest(failure=failure):
                outcome = self.build(fail=failure).run()
                self.assertEqual(outcome.status, "FAIL")
                self.assertIn(failure, " ".join(outcome.failures))
                self.assertEqual(self.records[0].status, "FAIL")

    def test_unknown_termination_skips_hashes(self):
        outcome = self.build(fail="run_child").run()
        self.assertNotIn("postcheck", self.events)
        self.assertNotIn("remove_boundary", self.events)
        self.assertIn("BOUNDARY_RETAINED", " ".join(outcome.failures))
        self.assertIn("NOT_VERIFIED", " ".join(outcome.failures))

    def test_nonzero_child(self):
        outcome = self.build(result=ChildProcessResult(True, 7)).run()
        self.assertEqual(outcome.child_exit, 7)
        self.assertEqual(outcome.status, "FAIL")
        self.assertIn("postcheck", self.events)

    def test_terminal_write_failure_propagates(self):
        with self.assertRaisesRegex(RuntimeError, "terminal_record"):
            self.build(fail="terminal_record").run()

    def test_invalid_result_leaves_termination_unknown(self):
        for result in ({"termination_confirmed": True, "exit_code": 0},
                       ChildProcessResult(1, 0)):
            with self.subTest(result=result):
                outcome = self.build(result=result).run()
                self.assertEqual(outcome.status, "FAIL")
                self.assertNotIn("postcheck", self.events)
                self.assertIn("NOT_VERIFIED", " ".join(outcome.failures))

    def test_prelaunch_failure_still_checks_integrity(self):
        outcome = self.build(fail="preflight").run()
        self.assertEqual(outcome.status, "FAIL")
        self.assertIn("postcheck", self.events)
        self.assertNotIn("run_child", self.events)

    def test_production_block(self):
        with self.assertRaisesRegex(RuntimeError, "real execution blocked"):
            SmokeLifecycle(is_synthetic=False, **{k: lambda *a: None for k in (
                "preflight", "acquire_lock", "create_boundary", "verify_boundary",
                "run_child", "remove_boundary", "verify_absence", "postcheck",
                "start_record", "close_transcript", "terminal_record")})

    def test_typed_failure_confirmed_allows_cleanup_without_success(self):
        lifecycle = self.build()
        def failed_child():
            raise ChildExecutionFailure("timeout", ChildProcessResult(True, 0))
        lifecycle.run_child = failed_child
        outcome = lifecycle.run()
        self.assertEqual(outcome.status, "FAIL")
        self.assertIn("timeout", " ".join(outcome.failures))
        self.assertIn("remove_boundary", self.events)
        self.assertIn("postcheck", self.events)

    def test_typed_failure_unconfirmed_retains_boundary(self):
        lifecycle = self.build()
        def failed_child():
            raise ChildExecutionFailure("kill failed", ChildProcessResult(False, None))
        lifecycle.run_child = failed_child
        outcome = lifecycle.run()
        self.assertEqual(outcome.status, "FAIL")
        self.assertNotIn("remove_boundary", self.events)
        self.assertNotIn("postcheck", self.events)

    def test_invalid_failure_result_cannot_release_boundary(self):
        lifecycle = self.build()
        def failed_child():
            raise ChildExecutionFailure("invalid", {"termination_confirmed": True})
        lifecycle.run_child = failed_child
        outcome = lifecycle.run()
        self.assertEqual(outcome.status, "FAIL")
        self.assertNotIn("remove_boundary", self.events)
