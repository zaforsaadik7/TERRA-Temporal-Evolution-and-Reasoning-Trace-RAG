"""Filesystem adapters: streaming identity observation, full memberships, counters.

No DB connection or model initialization. Native factory held. Tests call private
cores only on generated temporary trees. Observations are not an OS write lock.
"""
from hashlib import sha256
import os
from pathlib import Path
import stat
from scripts.matched_baseline.offline_cohort_input import FilePin,_key
from scripts.matched_baseline.offline_cohort_parent import RootMembers
from scripts.matched_baseline.offline_cohort_evidence import guard

COHORT_FILESYSTEM_ADMITTED = False


def _regular(path):
    guard(path);info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink<1:
        raise ValueError('Ordinary inventory member required')
    return info


def _identity(path):
    path=Path(path);before=_regular(path);size=0;digest=sha256()
    with path.open('rb') as stream:
        opened=os.fstat(stream.fileno())
        if (opened.st_dev,opened.st_ino,opened.st_size,opened.st_mtime_ns)!=(
                before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns):
            raise ValueError('Inventory file changed before open')
        for block in iter(lambda:stream.read(1024**2),b''):
            size+=len(block);digest.update(block)
        after=os.fstat(stream.fileno())
    final=_regular(path)
    attrs=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
    if (any(getattr(opened,k)!=getattr(after,k) for k in attrs)
            or any(getattr(before,k)!=getattr(final,k) for k in attrs) or size!=before.st_size):
        raise ValueError('Inventory identity/content changed during observation')
    return FilePin(str(path),size,digest.hexdigest())


def _members(root,*,max_entries=100000,excluded=()):
    root=guard(Path(root));result=[];seen=0;stack=[root]
    while stack:
        directory=stack.pop()
        for path in directory.iterdir():
            seen+=1
            if seen>max_entries:raise ValueError('Inventory traversal entry ceiling')
            guard(path);info=path.lstat()
            if path.parent==root and path.name in excluded:
                continue
            if stat.S_ISDIR(info.st_mode):stack.append(path)
            elif stat.S_ISREG(info.st_mode):
                if _regular(path).st_nlink!=1:
                    raise ValueError('Hardlink in full protected-root membership')
                result.append(path.relative_to(root).as_posix())
            else:raise ValueError('Unexpected inventory member kind')
    return tuple(sorted(result))


def _observe_review(review):
    review.validate()
    pins=tuple(_identity(pin.path) for pin in review.pins)
    roots=tuple(RootMembers(root.root,_members(root.root)) for root in review.roots)
    if pins!=review.pins or roots!=review.roots:
        raise ValueError('Fresh selected pins/full-root memberships differ from frozen review')
    return pins,roots


def _storage(*,evidence_root,disposable_root):
    def size(root):
        root=Path(root)
        if not root.exists():
            guard(root.parent);return 0
        return sum(_regular(root/name).st_size for name in _members(root))
    return dict(evidence_bytes=size(evidence_root),disposable_bytes=size(disposable_root))


def _manifest(review,root):
    from scripts.matched_baseline.offline_preflight import ManifestEntry
    root=Path(root);values={}
    for pin in review.pins:
        try:name=Path(pin.path).relative_to(root).as_posix()
        except ValueError:continue
        values[name]=ManifestEntry(name,pin.size_bytes,pin.sha256)
    return values


def construct_observer(review):
    if not COHORT_FILESYSTEM_ADMITTED:raise RuntimeError('Authentic filesystem observation held')
    return lambda:_observe_review(review)


def _verify_namespaces(command):
    """Complete project namespace and stdlib, with explicit trust-root exclusions.

    Global base site-packages is outside the selected venv, never silently swept
    or admitted. Both venv configurations must explicitly forbid global sites.
    """
    review=command.launch.parent;roles=dict(command.launch.artifacts)
    for role in ('controller_image','child_image'):
        cfg=Path(roles[role].path).parent.parent/'pyvenv.cfg'
        pin=next((p for p in review.pins if _key(p.path)==_key(str(cfg))),None)
        if pin is None or _identity(cfg)!=pin:raise ValueError('Pinned venv configuration required')
        if cfg.stat().st_size>65536:raise ValueError('Venv configuration ceiling')
        text=cfg.read_text(encoding='utf-8')
        values={line.split('=',1)[0].strip().lower():line.split('=',1)[1].strip().lower()
                for line in text.splitlines() if '=' in line}
        if values.get('include-system-site-packages')!='false':
            raise ValueError('Global site-packages must be explicitly disabled')
    project=Path(review.plan.workspace)/'scripts'/'matched_baseline'
    base=Path(roles['firewall_image'].path).parent;stdlib=base/'Lib'
    for root,external,excluded in ((project,('offline_cohort_anchor.py','launch_offline_cohort_user.ps1'),()),
                                   (stdlib,(),('site-packages',))):
        expected=set(external)
        for pin in review.pins:
            try:name=Path(pin.path).relative_to(root).as_posix()
            except ValueError:continue
            if excluded and name.split('/')[0] in excluded:
                raise ValueError('Excluded global site-packages accidentally pinned as stdlib')
            expected.add(name)
        if set(_members(root,excluded=excluded))!=expected:
            raise ValueError('Dependency namespace membership changed')
    expected={Path(p.path).name for p in review.pins if Path(p.path).parent==base}
    actual=set()
    for path in guard(base).iterdir():
        guard(path)
        if path.is_file():_regular(path);actual.add(path.name)
    if actual!=expected:raise ValueError('Base runtime root file membership changed')
