"""Only explicitly named fixture suites. No discover, assets or providers."""
import json,hashlib,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=Path(__file__).parent
prior=json.loads((ROOT/'reports/paired_completion_20261024_01/FINAL_TEST_RESULT.json').read_bytes())
command=prior['command']+['tests.test_paired_output_format_synthetic']
paths=list((ROOT/'scripts/matched_baseline').glob('*.py'))+[ROOT/(name.replace('.','/')+'.py') for name in command if name.startswith('tests.')]
paths.append(ROOT/'tests/fixtures/paired_verifier_invalid_json_20261024.json')
def pins():return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before=pins();start=time.monotonic()
result=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
after=pins();assert before==after
with (P/'TEST_OUTPUT.txt').open('xb') as f:f.write(result.stdout)
out=dict(command=command,exit_code=result.returncode,wall_seconds=time.monotonic()-start,
    source_test_pins=before,pins_unchanged=True,output_sha256=hashlib.sha256(result.stdout).hexdigest())
with (P/'TEST_RESULT.json').open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
print(result.stdout.decode(errors='replace')[-4000:]);raise SystemExit(result.returncode)
