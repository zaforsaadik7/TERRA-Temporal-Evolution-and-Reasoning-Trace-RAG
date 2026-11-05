"""Named synthetic regression; exclusive checkpoint outputs, no real entry."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
modules=json.loads((ROOT/'reports/cohort_loader_20261023_01/regression_r02/TEST_RESULT.json').read_text())['modules']
modules=modules+['tests.test_offline_cohort_assembly_synthetic']
assert len(modules)==len(set(modules))==36
log=io.StringIO();start=time.monotonic()
with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromNames(modules))
record=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
    skipped=len(result.skipped),elapsed_seconds=time.monotonic()-start,
    status='PASS' if result.wasSuccessful() else 'FAIL',modules=modules,
    scope='Named synthetic tests and installed-source fixtures; no genuine factories executed')
with (OUT/'named_tests.log').open('x') as f:f.write(log.getvalue())
with (OUT/'TEST_RESULT.json').open('x') as f:json.dump(record,f,indent=2)
sources=[]
for rel in ('scripts/matched_baseline/offline_cohort_assembly.py',
            'tests/test_offline_cohort_assembly_synthetic.py'):
    path=ROOT/rel;raw=path.read_bytes()
    with (OUT/(path.name+'.final')).open('xb') as f:f.write(raw)
    sources.append(dict(path=str(path),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
files=[]
for path in sorted(OUT.iterdir()):
    if path.is_file():
        raw=path.read_bytes();files.append(dict(path=str(path),size_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
with (OUT/'manifest.json').open('x') as f:json.dump(dict(sources=sources,files=files),f,indent=2)
print(json.dumps(record))
raise SystemExit(0 if result.wasSuccessful() else 1)
