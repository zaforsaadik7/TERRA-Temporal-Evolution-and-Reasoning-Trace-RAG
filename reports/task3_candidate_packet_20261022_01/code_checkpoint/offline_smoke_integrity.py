"""Protected inventory/copy integration; temporary synthetic fixtures only.

Two matching inventories and absent journals are stability observations, not an
OS write lock. Production admission/quiescence policy remains unimplemented.
"""
from pathlib import Path
from scripts.matched_baseline.offline_preflight import IntegrityLifecycleManager as Manager


class SmokeProtectedLifecycle:
    def __init__(self, *, source, cache, snapshot, disposable, source_manifest,
                 cache_manifest, is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Production protected lifecycle not admitted')
        self.source, self.cache = Path(source), Path(cache)
        self.snapshot, self.disposable = Path(snapshot), Path(disposable)
        if not source_manifest or not cache_manifest:
            raise ValueError('Complete reviewed inventories required')
        self.source_manifest = dict(source_manifest)
        self.cache_manifest = dict(cache_manifest)
        self.attempted = False
        self.receipt = None

    def _verify(self, path, expected, label):
        Manager.check_symlink_and_reparse_containment(path)
        actual = Manager.compute_manifest(path)
        Manager.assert_manifest_parity(expected, actual, label)
        return actual

    def preflight(self):
        Manager.validate_directory_separation([
            ('source', self.source), ('cache', self.cache),
            ('snapshot', self.snapshot), ('disposable', self.disposable)])
        if self.snapshot.exists() or self.disposable.exists():
            raise RuntimeError('Preserved copy destination collision')
        Manager.verify_source_quiescence(self.source)
        first = self._verify(self.source, self.source_manifest, 'Source pins')
        self._verify(self.cache, self.cache_manifest, 'Cache pins')
        Manager.assert_manifest_parity(first, self._verify(self.source, self.source_manifest,
            'Source repeat pins'), 'Two-pass source stability')
        self._verify(self.cache, self.cache_manifest, 'Cache repeat pins')
        Manager.verify_source_quiescence(self.source)

    def prepare(self):
        if self.attempted:
            raise RuntimeError('Protected preparation retry forbidden')
        self.preflight()
        self.attempted = True
        Manager.create_preserved_snapshot(self.source, self.snapshot)
        self._verify(self.snapshot, self.source_manifest, 'Snapshot pins')
        Manager.create_disposable_copy(self.snapshot, self.disposable)
        self._verify(self.disposable, self.source_manifest, 'Disposable pins')
        self._verify(self.source, self.source_manifest, 'Source after copy pins')
        self.receipt = Manager.issue_isolation_receipt(self.source, self.snapshot, self.disposable)
        return self.receipt

    def final_check(self):
        failures = []
        targets = [('source', self.source, self.source_manifest),
                   ('cache', self.cache, self.cache_manifest)]
        if self.attempted:
            targets.append(('snapshot', self.snapshot, self.source_manifest))
        for label, path, expected in targets:
            try:
                self._verify(path, expected, f'Final {label} pins')
            except Exception as exc:
                failures.append(f'{label}: {exc}')
        # Disposable mutations are allowed inside the working copy; inventory
        # recording is separate from protected source/snapshot equality.
        if failures:
            raise RuntimeError('; '.join(failures))
