"""Full declared-file pin verification; no model/database initialization.

Production admission and a reviewed file map are still required. Tests provide
only temporary files. Aggregate-family files must themselves enumerate every
constituent; checking their digest is not a substitute for constituent checks.
"""
import hashlib
from pathlib import Path
import re
from copy import deepcopy
from scripts.matched_baseline.offline_preflight import IntegrityLifecycleManager


class FrozenFilePinVerifier:
    def __init__(self, *, file_paths, expected_pins, expected_sizes, is_synthetic=True,
                 manifest_specs=None):
        if is_synthetic is not True:
            raise RuntimeError('Authentic file inventory admission not implemented')
        if not file_paths or set(file_paths) != set(expected_pins) or set(file_paths) != set(expected_sizes):
            raise ValueError('Incomplete declared file inventory')
        if any(type(pin) is not str or not re.fullmatch('[0-9a-f]{64}',pin) for pin in expected_pins.values()):
            raise ValueError('Invalid file digest')
        if any(type(size) is not int or size < 0 for size in expected_sizes.values()):
            raise ValueError('Invalid file byte count')
        self.paths = {key:Path(value) for key,value in file_paths.items()}
        if any(not path.is_absolute() for path in self.paths.values()):
            raise ValueError('Absolute pinned file paths required')
        self.pins, self.sizes = dict(expected_pins), dict(expected_sizes)
        from scripts.matched_baseline.offline_smoke_manifests import validate_specs, MAX_MANIFEST_BYTES
        self.manifest_specs = {} if manifest_specs is None else deepcopy(manifest_specs)
        validate_specs(self.manifest_specs, self.paths)
        if any(self.sizes[name] > MAX_MANIFEST_BYTES for name in self.manifest_specs):
            raise ValueError('Manifest byte bound exceeded')
        if '__manifest_verification__' in self.paths:
            raise ValueError('Reserved file identity name')
        self.verified_paths = frozenset()

    def verify(self):
        self.verified_paths = frozenset()
        observations, failures = {}, []
        for name, path in self.paths.items():
            try:
                IntegrityLifecycleManager.check_symlink_and_reparse_containment(path)
                if not path.is_file():
                    raise ValueError('Missing ordinary pinned file')
                before = path.stat()
                digest, size = hashlib.sha256(), 0
                with path.open('rb') as stream:
                    for block in iter(lambda:stream.read(65536),b''):
                        size += len(block); digest.update(block)
                after = path.stat()
                if (before.st_size,before.st_mtime_ns) != (after.st_size,after.st_mtime_ns) or size != after.st_size:
                    raise ValueError('Pinned file changed during hashing')
                if size != self.sizes[name] or digest.hexdigest() != self.pins[name]:
                    raise ValueError('Pinned file size/hash mismatch')
                observations[name] = {'path':str(path),'size_bytes':size,'sha256':digest.hexdigest()}
            except Exception as exc:
                failures.append(f'{name}: {exc}')
        if failures:
            raise RuntimeError('; '.join(failures))
        if self.manifest_specs:
            from scripts.matched_baseline.offline_smoke_manifests import load_members
            members,counts = load_members(paths=self.paths,pins=self.pins,sizes=self.sizes,specs=self.manifest_specs)
            direct = {path.resolve():(self.pins[name],self.sizes[name]) for name,path in self.paths.items()}
            for path,identity in members.items():
                if path in direct and direct[path] != identity:
                    raise ValueError('Direct/manifest identity conflict')
            member_verifier = FrozenFilePinVerifier(
                file_paths={str(i):path for i,path in enumerate(members)},
                expected_pins={str(i):identity[0] for i,identity in enumerate(members.values())},
                expected_sizes={str(i):identity[1] for i,identity in enumerate(members.values())})
            member_verifier.verify()  # Full byte checks in parent AND child; no receipt shortcut.
            observations['__manifest_verification__'] = {'verified_unique_members':len(members),
                                                        'manifest_counts':counts}
            self.verified_paths = frozenset(members) | frozenset(path.resolve() for path in self.paths.values())
        else:
            self.verified_paths = frozenset(path.resolve() for path in self.paths.values())
        return observations
