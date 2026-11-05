"""Read-only check of the temporal records supplied in Antigravity-0001."""
import hashlib
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parents[2]
path = root / 'data/temporal_leakage_dual_judged.json'
with path.open('rb') as handle:
    digest = hashlib.file_digest(handle, 'sha256').hexdigest()
records = json.loads(path.read_text(encoding='utf-8'))
valid = [r for r in records if all(
    isinstance(r.get(k), dict) and not r[k].get('error')
    and r[k].get('severity_level') in range(3)
    and r[k].get('temporal_grounding_score') in range(1, 6)
    for k in ('judge1_evaluation', 'judge2_evaluation'))]

def qwk(field, levels):
    a = [r['judge1_evaluation'][field] for r in valid]
    b = [r['judge2_evaluation'][field] for r in valid]
    n = len(a)
    ca, cb = Counter(a), Counter(b)
    observed = sum((x-y)**2 for x, y in zip(a,b))/n
    expected = sum(ca[x]*cb[y]*(x-y)**2 for x in levels for y in levels)/(n*n)
    return 1-observed/expected if expected else None

print(json.dumps({
    'input': str(path), 'sha256': digest, 'records': len(records),
    'valid_pairs': len(valid), 'qwk_severity': qwk('severity_level', range(3)),
    'severity_raw_concordance': sum(r['judge1_evaluation']['severity_level'] ==
        r['judge2_evaluation']['severity_level'] for r in valid)/len(valid),
    'qwk_tgs': qwk('temporal_grounding_score', range(1,6)),
    'judge_models': {k: dict(Counter(str(r.get(k, {}).get('judge_model', '<missing>'))
        for r in records)) for k in ('judge1_evaluation','judge2_evaluation')},
    'nonempty_fields': {k: sum(bool(r.get(k)) for r in records) for k in
        ('answer_full','context_full','prompt_sha256','created_at')},
    'warning': 'Matches verify saved records only, not preregistration, historical execution or prompt authenticity.'
}, indent=2))
