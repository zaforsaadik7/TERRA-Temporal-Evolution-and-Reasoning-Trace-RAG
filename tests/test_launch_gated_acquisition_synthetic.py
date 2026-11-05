"""
Synthetic unit test wrapper for PowerShell gated acquisition launcher.
Executes tests/test_launch_gated_acquisition.ps1 in an isolated subprocess
and asserts complete pass of all synthetic fail-closed and lifecycle checks.
"""

import os
import subprocess
import unittest

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEST_PS1_SCRIPT = os.path.join(WORKSPACE_ROOT, "tests", "test_launch_gated_acquisition.ps1")
LAUNCHER_PS1_SCRIPT = os.path.join(WORKSPACE_ROOT, "scripts", "matched_baseline", "launch_gated_acquisition.ps1")


class TestLaunchGatedAcquisitionSynthetic(unittest.TestCase):
    def test_launcher_synthetic_suite_passes(self):
        self.assertTrue(os.path.isfile(LAUNCHER_PS1_SCRIPT), f"Missing launcher script: {LAUNCHER_PS1_SCRIPT}")
        self.assertTrue(os.path.isfile(TEST_PS1_SCRIPT), f"Missing test script: {TEST_PS1_SCRIPT}")

        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            TEST_PS1_SCRIPT,
        ]

        proc = subprocess.run(
            cmd,
            cwd=WORKSPACE_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
        )

        output = f"{proc.stdout}\n{proc.stderr}"

        # Assert exit code 0
        self.assertEqual(
            proc.returncode,
            0,
            f"PowerShell test runner exited with {proc.returncode}.\nOutput:\n{output}",
        )

        # Assert all 17 synthetic tests passed
        self.assertIn("SYNTHETIC TEST RESULTS: 17 / 17 PASSED (0 FAILED, 0 SKIPPED)", output)
        self.assertNotIn("[FAIL]", output)


if __name__ == "__main__":
    unittest.main()
