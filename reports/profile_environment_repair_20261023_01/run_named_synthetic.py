"""Approved named synthetic suites only, no discovery or authentic entry."""
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
R=Path('F:/TERRA -Copy');O=Path(__file__).resolve().parent
sys.path.insert(0,str(R))
modules=(R/'reports/compact_manifest_repair_20261023_01/regression_modules.txt').read_text().split()
modules+=['tests.test_offline_smoke_bindings_synthetic',
          'tests.test_offline_smoke_user_launcher_synthetic',
          'tests.test_offline_smoke_semantic_mapping_synthetic',
          'tests.test_offline_smoke_diagnostics_synthetic',
          'tests.test_offline_smoke_profile_environment_synthetic']
assert len(modules)==30 and len(set(modules))==30
output=io.StringIO()
with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
    suite=unittest.TestLoader().loadTestsFromNames(modules)
    result=unittest.TextTestRunner(stream=output,verbosity=1).run(suite)
raw=output.getvalue()
with (O/'synthetic_console.log').open('x',encoding='utf-8') as f:f.write(raw)
summary={'status':'PASS' if result.wasSuccessful() else 'FAIL','modules':modules,
         'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
         'skipped':len(result.skipped),'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
         'scope':'Synthetic fixtures only; no B001/native/model/store execution'}
with (O/'TEST_RESULT.json').open('x') as f:json.dump(summary,f,indent=2)
print(raw[-1800:]);print(json.dumps(summary))
raise SystemExit(0 if result.wasSuccessful() else 1)


