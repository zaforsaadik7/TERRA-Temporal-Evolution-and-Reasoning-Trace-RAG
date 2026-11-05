"""Named synthetic/installed-source contract tests only; no discovery or run entry."""
import contextlib
import io
import json
from pathlib import Path
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
modules = (ROOT/'reports/compact_manifest_repair_20261023_01/regression_modules.txt').read_text().splitlines()
modules += [
    'tests.test_offline_smoke_bindings_synthetic',
    'tests.test_offline_smoke_user_launcher_synthetic',
    'tests.test_offline_smoke_semantic_mapping_synthetic',
    'tests.test_offline_smoke_diagnostics_synthetic',
    'tests.test_offline_smoke_profile_environment_synthetic',
    'tests.test_offline_smoke_explicit_embeddings_synthetic',
    'tests.test_offline_preflight_cohort_synthetic',
    'tests.test_offline_cohort_core_synthetic',
]
assert len(modules) == len(set(modules)) == 33
log = io.StringIO()
started = time.monotonic()
with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
record = {'status': 'PASS' if result.wasSuccessful() else 'FAIL',
    'tests': result.testsRun, 'failures': len(result.failures),
    'errors': len(result.errors), 'skipped': len(result.skipped),
    'elapsed_seconds': time.monotonic()-started, 'modules': modules,
    'scope': 'Synthetic tests plus pinned installed Chroma function bodies with synthetic collaborators; no full Chroma import or client/model execution'}
with (OUT/'named_tests.log').open('x') as f:
    f.write(log.getvalue())
with (OUT/'TEST_RESULT.json').open('x') as f:
    json.dump(record, f, indent=2)
print(json.dumps(record))
raise SystemExit(0 if result.wasSuccessful() else 1)
