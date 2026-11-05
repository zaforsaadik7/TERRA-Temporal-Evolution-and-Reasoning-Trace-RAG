"""Held dependency assembly with explicit resource ownership; no real factories.

Injected collaborators are trusted. A factory owns its partial allocations until
it returns OwnedDependency. Native termination remains the parent controller's
responsibility; running a release callback is not proof of process-tree exit.
"""
from dataclasses import dataclass
from scripts.matched_baseline.offline_cohort_loader import CohortDependencyLoader

COHORT_ASSEMBLY_ADMITTED = False


@dataclass(frozen=True)
class OwnedDependency:
    value: object
    release: object

    def __post_init__(self):
        if not callable(self.release):
            raise ValueError('Explicit release callback required')


class CohortAssembly:
    """Synthetic single-use context with reverse-order, best-effort cleanup.

    No reflection-based close(), private Chroma shutdown or guessed ONNX API.
    Real factories/release adapters and authentic admission are not implemented.
    """
    OWNED = frozenset({'embedding', 'reader', 'roles'})

    def __init__(self, *, plan, reviewed_plan, dependencies, is_synthetic=True):
        if is_synthetic is not True:
            raise RuntimeError('Authentic cohort assembly remains blocked')
        if (type(dependencies) is not dict
                or set(dependencies) != CohortDependencyLoader.REQUIRED
                or any(not callable(v) for v in dependencies.values())):
            raise ValueError('Explicit assembly collaborators required')
        self._releases = []
        self._started = False
        self._closed = False
        wrapped = dict(dependencies)
        for name in self.OWNED:
            factory = dependencies[name]
            def acquire(*args, _factory=factory, **kwargs):
                owned = _factory(*args, **kwargs)
                if type(owned) is not OwnedDependency:
                    raise ValueError('Factory must return an explicitly owned dependency')
                self._releases.append(owned.release)
                return owned.value
            wrapped[name] = acquire
        self._loader = CohortDependencyLoader(plan=plan, reviewed_plan=reviewed_plan,
                                               dependencies=wrapped, is_synthetic=True)

    def load(self, **request):
        if self._started or self._closed:
            raise RuntimeError('Assembly reuse forbidden')
        self._started = True
        try:
            return self._loader.load(**request)
        except BaseException as original:
            self._finalize(original)
            raise

    def _finalize(self, original=None):
        if self._closed:
            return
        self._closed = True
        failures = []
        while self._releases:
            release = self._releases.pop()
            try:
                release()
            except BaseException as exc:
                failures.append(exc)
        if failures:
            # Preserve both original failure and every cleanup failure, without
            # echoing exception strings into an evidence stream or console.
            raise BaseExceptionGroup('Cohort assembly cleanup failed',
                                     ([original] if original is not None else []) + failures)

    def close(self):
        self._finalize()

    def __enter__(self):
        if self._closed or self._started:
            raise RuntimeError('Fresh assembly context required')
        return self

    def __exit__(self, kind, error, traceback):
        self._finalize(error)
        return False


def main():
    print('BLOCKED: genuine factories and cohort assembly admission pending')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
