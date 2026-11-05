"""Filesystem-only evidence generation. No application/dependency imports."""
import ast
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path(r'F:\TERRA -Copy')
OUT = Path(__file__).parent / 'inventory'
BASE = Path(r'C:\Users\zafor\AppData\Local\Python\pythoncore-3.14-64')


def safe(path):
    for item in (path, *path.parents):
        info = item.lstat()
        if item.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise RuntimeError('Reparse/symlink boundary: ' + str(item))


def digest(path):
    safe(path)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise RuntimeError('Non-ordinary inventory file')
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError('Changed during hash: ' + str(path))
    return {'path': str(path), 'size_bytes': after.st_size,
            'mtime_ns': str(after.st_mtime_ns), 'sha256': value.hexdigest()}


def files(root, exclude=()):
    safe(root)
    result = []
    for path in sorted(root.rglob('*')):
        if any(part in exclude for part in path.relative_to(root).parts):
            continue
        safe(path)
        if path.is_file():
            result.append(path)
    return result


def write(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write((json.dumps(value, indent=2) + '\n').encode('utf-8'))


def main():
    OUT.mkdir(exist_ok=False)
    groups = {}
    def add(kind, paths):
        groups[kind] = [digest(path) for path in sorted(set(paths))]
        print(kind, len(groups[kind]), 'files', flush=True)

    previous = json.loads((ROOT / 'reports/codex_task3_static_audit_20261022_01/repository_import_closure.json').read_bytes())
    # Refresh the known AST closure and detect newly referenced local modules.
    pending = [Path(item['path']) for item in previous['files']]
    pending.append(ROOT / 'scripts/matched_baseline/offline_smoke_parent.py')
    closure = set()
    external = set()
    while pending:
        path = pending.pop()
        if path in closure:
            continue
        safe(path)
        closure.add(path)
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            names = ([item.name for item in node.names] if isinstance(node, ast.Import)
                     else [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            if isinstance(node, ast.ImportFrom) and node.level:
                stem = path.parent
                for _ in range(node.level-1):
                    stem = stem.parent
                if node.module:
                    stem = stem.joinpath(*node.module.split('.'))
                candidate = stem.with_suffix('.py')
                if candidate.is_file():
                    pending.append(candidate)
                for alias in node.names:
                    candidate = stem / (alias.name+'.py')
                    if candidate.is_file():
                        pending.append(candidate)
                continue
            for name in names:
                if name.startswith('scripts.matched_baseline'):
                    stem = ROOT.joinpath(*name.split('.'))
                    candidate = stem.with_suffix('.py')
                    if not candidate.is_file():
                        candidate = stem / '__init__.py'
                    if candidate.is_file():
                        pending.append(candidate)
                    if isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            child = stem / (alias.name + '.py')
                            if child.is_file():
                                pending.append(child)
                else:
                    external.add(name.split('.')[0])
    anchor = ROOT / 'scripts/matched_baseline/offline_smoke_entry_anchor.py'
    closure.discard(anchor)
    for init in (ROOT / 'scripts/__init__.py', ROOT / 'scripts/matched_baseline/__init__.py'):
        if init.is_file():
            closure.add(init)
    add('repository_code', closure)
    add('repository_auxiliary', [path for path in files(ROOT / 'scripts/matched_baseline')
        if path not in closure and path != anchor and path.suffix in {'.py','.pyc','.ps1','.pth'}])
    add('out_of_band_anchor', [anchor])
    add('boundary_script', [ROOT / 'scripts/matched_baseline/offline_smoke_windows_boundary.ps1'])
    prior_assets = json.loads((ROOT / 'reports/task3_authorized_inventory_20261022_01/assets_and_runtimes.json').read_bytes())
    add('assets_and_runtime_targets', [Path(item['path']) for item in prior_assets])
    for row in prior_assets:
        if digest(Path(row['path']))['sha256'] != row['sha256']:
            raise RuntimeError('Asset/runtime drift since authorized inventory: ' + row['path'])
    prior_store = json.loads((ROOT / 'reports/task3_authorized_inventory_20261022_01/source_cache_before_exact.json').read_bytes())['first']
    for kind in ('store', 'cache'):
        root = Path(prior_store[kind]['root'])
        add(kind, files(root))
        expected = {str(root / item['relative_path']): item for item in prior_store[kind]['files']}
        if set(expected) != {item['path'] for item in groups[kind]}:
            raise RuntimeError('Protected file-set drift')
        for item in groups[kind]:
            old = expected[item['path']]
            if kind == 'store' and Path(item['path']).name == 'chroma.sqlite3':
                old = {'size_bytes': 362885120, 'sha256': '6a582ce87816aba771db2a54b91853ecf8ec818981120d67682c39730588189c'}
            if (item['size_bytes'], item['sha256']) != (old['size_bytes'], old['sha256']):
                raise RuntimeError('Protected bytes changed')
    add('venv_configuration', [ROOT / 'venv/pyvenv.cfg'])
    add('venv_installed_environment', files(ROOT / 'venv/Lib/site-packages'))
    add('base_runtime_root', [path for path in BASE.iterdir() if path.is_file()])
    add('base_runtime_dlls', files(BASE / 'DLLs'))
    add('base_standard_library', files(BASE / 'Lib', exclude=('site-packages',)))
    # Second complete tree enumeration catches additions/removals as well as drift.
    for kind, root, exclude in (
        ('store', Path(prior_store['store']['root']), ()),
        ('cache', Path(prior_store['cache']['root']), ()),
        ('venv_installed_environment', ROOT / 'venv/Lib/site-packages', ()),
        ('base_runtime_dlls', BASE / 'DLLs', ()),
        ('base_standard_library', BASE / 'Lib', ('site-packages',))):
        if {str(path) for path in files(root, exclude)} != {item['path'] for item in groups[kind]}:
            raise RuntimeError('Tree membership changed: ' + kind)
    for kind, rows in groups.items():
        for row in rows:
            if digest(Path(row['path'])) != row:
                raise RuntimeError('Second-pass identity change: ' + row['path'])
        write(kind + '.json', rows)
    drift = {}
    old_root = ROOT / 'reports/task3_candidate_packet_20261022_01/inventory'
    for kind,rows in groups.items():
        prior = old_root / (kind+'.json')
        old = {row['path']:row for row in json.loads(prior.read_bytes())} if prior.exists() else {}
        new = {row['path']:row for row in rows}
        drift[kind] = {'added':[new[path] for path in sorted(set(new)-set(old))],
            'removed':[old[path] for path in sorted(set(old)-set(new))],
            'changed':[{'before':old[path],'after':new[path]} for path in sorted(set(old)&set(new))
                if (old[path]['sha256'],old[path]['size_bytes']) != (new[path]['sha256'],new[path]['size_bytes'])],
            'metadata_only_count':sum(old[path].get('mtime_ns') != new[path].get('mtime_ns')
                for path in set(old)&set(new)
                if (old[path]['sha256'],old[path]['size_bytes']) == (new[path]['sha256'],new[path]['size_bytes']))}
    approved = json.loads((ROOT / 'reports/compact_manifest_repair_20261023_01/manifest.json').read_bytes())
    expected_code = {row['path']:row for row in approved['files'] if '/scripts/' in row['path'].replace('\\','/')}
    for row in groups['repository_code']:
        old_rows = {item['path']:item for item in json.loads((old_root/'repository_code.json').read_bytes())}
        if row['path'] not in old_rows or row['sha256'] != old_rows[row['path']]['sha256']:
            if row['path'] not in expected_code or row['sha256'] != expected_code[row['path']]['sha256']:
                raise RuntimeError('Unapproved source identity change: '+row['path'])
    write('drift_from_20261022.json', drift)
    write('summary.json', {'scope': 'FILESYSTEM_ONLY_TWO_PASS_NO_IMPORT_OR_MODEL_LOAD',
        'external_import_roots': sorted(external),
        'groups': {kind: {'files': len(rows), 'bytes': sum(row['size_bytes'] for row in rows)} for kind, rows in groups.items()},
        'limits': ['Observed trees are stable, not locked.',
                   'Installed environment inventory is conservative, not proof of complete OS dynamic-load closure.',
                   'Entry anchor is inventoried separately, not a constituent of its own packet.']})
    print('INVENTORY_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
