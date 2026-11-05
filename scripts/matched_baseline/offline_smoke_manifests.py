"""Bounded manifest expansion; no runtime imports, clients or asset execution.

Manifests are data, not receipts that waive constituent identity checks.
The caller supplies independently pinned top-level manifest identities.
"""
import hashlib
import json
from pathlib import Path
import re
from scripts.matched_baseline.offline_preflight import IntegrityLifecycleManager as Manager

MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_MANIFESTS = 64
MAX_MEMBERS = 50000
MAX_TOTAL_MEMBERS = 100000


def canonical(value):
    if type(value) is not str or not value or '\0' in value:
        raise ValueError('Invalid manifest path')
    path = Path(value)
    if not path.is_absolute() or '..' in path.parts or any(':' in part for part in path.parts[1:]):
        raise ValueError('Absolute non-traversing manifest path required')
    Manager.check_symlink_and_reparse_containment(path)
    return path.resolve()


def validate_specs(specs, names):
    if type(specs) is not dict or len(specs) > MAX_MANIFESTS or not set(specs).issubset(names):
        raise ValueError('Invalid manifest bindings')
    total = 0
    for spec in specs.values():
        if type(spec) is not dict or set(spec) != {'roots','count','complete_roots'}:
            raise ValueError('Invalid manifest scope schema')
        if type(spec['count']) is not int or not 0 < spec['count'] <= MAX_MEMBERS:
            raise ValueError('Invalid manifest member count')
        total += spec['count']
        roots = spec['roots']
        if type(roots) is not list or not 0 < len(roots) <= 32 or any(
                type(root) is not str or not root or '\0' in root or not Path(root).is_absolute() or
                '..' in Path(root).parts or Path(root) == Path(Path(root).anchor) for root in roots):
            raise ValueError('Invalid manifest roots')
        complete = spec['complete_roots']
        if type(complete) is not list or len(set(complete)) != len(complete) or not set(complete).issubset(roots):
            raise ValueError('Invalid complete-root coverage')
    if total > MAX_TOTAL_MEMBERS:
        raise ValueError('Total manifest member limit exceeded')


def load_members(*, paths, pins, sizes, specs):
    validate_specs(specs, paths)
    members, counts = {}, {}
    def unique(pairs):
        result = {}
        for key,value in pairs:
            if key in result:
                raise ValueError('Duplicate manifest JSON field')
            result[key] = value
        return result
    for name,spec in specs.items():
        if sizes[name] > MAX_MANIFEST_BYTES:
            raise ValueError('Manifest byte bound exceeded')
        path = canonical(str(paths[name]))
        before = path.stat()
        with path.open('rb') as stream:
            raw = stream.read(MAX_MANIFEST_BYTES+1)
        after = path.stat()
        if ((before.st_size,before.st_mtime_ns) != (after.st_size,after.st_mtime_ns) or
                len(raw) != sizes[name] or hashlib.sha256(raw).hexdigest() != pins[name]):
            raise ValueError('Manifest identity changed')
        rows = json.loads(raw.decode('utf-8'),object_pairs_hook=unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite manifest value')))
        if type(rows) is not list or len(rows) != spec['count']:
            raise ValueError('Manifest count/schema mismatch')
        roots = [canonical(root) for root in spec['roots']]
        if len(set(roots)) != len(roots) or any(not root.is_dir() for root in roots):
            raise ValueError('Manifest roots must be distinct directories')
        seen = set()
        for row in rows:
            if (type(row) is not dict or not {'path','sha256','size_bytes'}.issubset(row) or
                    not set(row).issubset({'path','sha256','size_bytes','mtime_ns'}) or
                    type(row['sha256']) is not str or not re.fullmatch('[0-9a-f]{64}',row['sha256']) or
                    type(row['size_bytes']) is not int or row['size_bytes'] < 0 or
                    ('mtime_ns' in row and (type(row['mtime_ns']) is not str or not re.fullmatch('[0-9]+',row['mtime_ns'])))):
                raise ValueError('Invalid manifest member schema')
            member = canonical(row['path'])
            if not any(root in member.parents for root in roots):
                raise ValueError('Manifest member outside reviewed roots')
            if member in seen:
                raise ValueError('Duplicate manifest member')
            seen.add(member)
            identity = (row['sha256'],row['size_bytes'])
            if member in members and members[member] != identity:
                raise ValueError('Conflicting manifest member identity')
            members[member] = identity
        # Use only for roots whose manifest is a complete tree snapshot, not a
        # selected code/artifact list. Additional executable/startup files fail.
        for complete in spec['complete_roots']:
            root = canonical(complete)
            actual = set()
            for candidate in root.rglob('*'):
                candidate = canonical(str(candidate))
                if candidate.is_file():
                    actual.add(candidate)
            expected = {member for member in seen if root in member.parents}
            if actual != expected:
                raise ValueError('Complete manifest tree membership changed')
        counts[name] = len(rows)
    return members,counts
