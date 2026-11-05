"""Explicit synthetic regression and exclusive input-reader checkpoint."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
modules=json.loads((ROOT/'reports/cohort_execution_20261023_01/TEST_RESULT.json').read_text())['modules']
modules=modules+['tests.test_offline_cohort_input_synthetic']
assert len(modules)==len(set(modules))==39
log=io.StringIO();started=time.monotonic()
with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
record=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
    skipped=len(result.skipped),elapsed_seconds=time.monotonic()-started,
    status='PASS' if result.wasSuccessful() else 'FAIL',modules=modules,
    scope='Generated temporary benchmark/hardlink fixtures and prior synthetic suites; canonical input gate never opened')
with (OUT/'named_tests.log').open('x') as f:f.write(log.getvalue())
with (OUT/'TEST_RESULT.json').open('x') as f:json.dump(record,f,indent=2)
def identity(path):
    raw=path.read_bytes()
    return dict(path=str(path),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
sources=[]
for rel in ('scripts/matched_baseline/offline_cohort_input.py',
            'tests/test_offline_cohort_input_synthetic.py'):
    path=ROOT/rel;sources.append(identity(path))
    with (OUT/(path.name+'.final')).open('xb') as f:f.write(path.read_bytes())
with (OUT/'manifest.json').open('x') as f:
    json.dump(dict(sources=sources,files=[identity(p) for p in sorted(OUT.iterdir())
        if p.is_file() and p.name!='manifest.json']),f,indent=2)
print(json.dumps(record))
raise SystemExit(0 if result.wasSuccessful() else 1)
