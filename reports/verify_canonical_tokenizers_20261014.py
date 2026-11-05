"""Single approved canonical tokenizer integration check; no network/model inference."""
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path('F:/TERRA -Copy')
sys.path.insert(0, str(ROOT))
from scripts.matched_baseline.fast_tokenizer_adapter import LocalFastTokenizer

evidence = ROOT / 'reports' / ('canonical_tokenizer_check_' + uuid.uuid4().hex)
evidence.mkdir(exist_ok=False)
pins = {
    'scripts/matched_baseline/fast_tokenizer_adapter.py': '976ffaa1c4e702f3352683fa15373877d03391bb0debd4ddf9e3623e94631b3c',
    'venv/Scripts/python.exe': '896ccf899b9d45c1c119ba35d6cce6e16cc10dd6a7f502f88fb50429a6e5cf4c',
    'assets/tokenizers/tokenizer_manifest.sha256': '41902553acffa03065b3bc6049047d0d573fb4659aea9f428df6d3f809f84a44',
    'assets/tokenizers/gated_tokenizer_manifest.v1.sha256': '588f9614af4a5ae3cb43cf93014b5af386e9986db1d527763967d72a3f37da66',
}
report = {'outcome': 'FAILED', 'errors': [], 'roles': {}, 'before': {}, 'after': {},
          'caveats': 'Local integration only; upstream receipt and serving-provider parity caveats remain.'}
def digest(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()

code = 1
try:
    for rel, expected in list(pins.items()):
        if digest(rel) != expected:
            raise ValueError('Pin mismatch: ' + rel)
    for manifest in ('assets/tokenizers/tokenizer_manifest.sha256', 'assets/tokenizers/gated_tokenizer_manifest.v1.sha256'):
        for row in (ROOT / manifest).read_text().splitlines():
            expected, rel = row.split('  ', 1)
            if rel in pins:
                raise ValueError('Duplicate protected path: ' + rel)
            pins[rel] = expected
    if len(pins) != 19:
        raise ValueError('Unexpected protected inventory')
    report['before'] = {rel: digest(rel) for rel in pins}
    if report['before'] != pins:
        raise ValueError('Asset pre-hash mismatch')
    for role in ('generator', 'router', 'judge1', 'judge2'):
        manifest = ('gated_tokenizer_manifest.v1.sha256' if role in ('generator', 'router') else 'tokenizer_manifest.sha256')
        adapter = LocalFastTokenizer(role=role, role_dir=ROOT/'assets/tokenizers'/role,
                                    manifest_path=ROOT/'assets/tokenizers'/manifest, base_dir=ROOT, mode='authentic')
        if adapter.is_synthetic:
            raise ValueError('Synthetic adapter in authentic check')
        if role in ('generator', 'router') and adapter.vocab_size != {'generator': 128256, 'router': 262145}[role]:
            raise ValueError('Vocabulary mismatch: ' + role)
        messages = [{'role': 'system', 'content': 'You are a research assistant.'},
                    {'role': 'user', 'content': 'Summarize this synthetic example: section 4 and 特許法.'}]
        rendered = adapter.apply_chat_template(messages, add_generation_prompt=True)
        if not rendered or rendered != adapter.apply_chat_template(messages, add_generation_prompt=True):
            raise ValueError('Empty or nondeterministic rendering: ' + role)
        ids = adapter._tokenizer.encode(rendered, add_special_tokens=False).ids
        if not ids or ids != adapter._tokenizer.encode(rendered, add_special_tokens=False).ids:
            raise ValueError('Empty or nondeterministic encoding: ' + role)
        report['roles'][role] = {'vocab_size': adapter.vocab_size, 'manifest': manifest,
            'rendered_sha256': hashlib.sha256(rendered.encode()).hexdigest(),
            'token_count': len(ids), 'is_synthetic': False, 'outcome': 'PASS'}
    report['outcome'] = 'SUCCESS'
    code = 0
except Exception as exc:
    report['errors'].append(str(exc))
finally:
    for rel in pins:
        try:
            report['after'][rel] = digest(rel)
            if report['after'][rel] != pins[rel]:
                raise ValueError('Post-hash mismatch: ' + rel)
        except Exception as exc:
            report['errors'].append(str(exc))
            report['outcome'] = 'FAILED'
            code = 1
    try:
        with (evidence/'verification_report.json').open('x', encoding='utf-8') as out:
            json.dump(report, out, indent=2)
    except Exception as exc:
        print('Evidence write failure:', exc, file=sys.stderr)
        code = 1
print('EVIDENCE', evidence)
print('OUTCOME', report['outcome'], 'EXIT', code)
print('ERRORS', report['errors'])
print('ROLES', report['roles'])
sys.exit(code)
