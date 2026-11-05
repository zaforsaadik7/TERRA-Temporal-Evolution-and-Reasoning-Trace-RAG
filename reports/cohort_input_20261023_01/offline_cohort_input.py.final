"""Bounded file observation and pure inventory binding; canonical entry held.

Metadata comparisons reduce replacement risk, not an OS lock or race-free
sandbox. Pure inventory equality is not a fresh recursive membership audit.
"""
from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import re
import stat
from scripts.matched_baseline.offline_cohort_evidence import guard
from scripts.matched_baseline.offline_cohort_execution import (
    MAX_BENCHMARK_BYTES, bind_benchmark_bytes)

COHORT_INPUT_ADMITTED = False


def _key(value):
    if type(value) is not str:
        raise ValueError('Explicit file path string required')
    path=Path(value)
    if (not path.is_absolute() or '..' in path.parts
            or any(':' in part for part in path.parts[1:])):
        raise ValueError('Absolute non-traversing non-ADS path required')
    return str(path).casefold()


@dataclass(frozen=True)
class FilePin:
    path: str
    size_bytes: int
    sha256: str

    def validate(self):
        _key(self.path)
        if (type(self.size_bytes) is not int or not 0 <= self.size_bytes < 2**63
                or type(self.sha256) is not str
                or re.fullmatch('[0-9a-f]{64}',self.sha256) is None):
            raise ValueError('Exact file size and lowercase digest required')
        return self


@dataclass(frozen=True)
class FileReadReceipt:
    pin: FilePin
    metadata: tuple
    synthetic_fixture: bool


def _metadata(info):
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
            or getattr(info,'st_file_attributes',0)&0x400):
        raise ValueError('Regular single-link non-reparse input required')
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)


def _read_once(path, *, reviewed_pin, synthetic_fixture):
    reviewed_pin.validate()
    if _key(str(path)) != _key(reviewed_pin.path):
        raise ValueError('Input path differs from reviewed pin')
    if reviewed_pin.size_bytes > MAX_BENCHMARK_BYTES:
        raise ValueError('Input exceeds bounded benchmark size')
    path=guard(Path(path))
    before=_metadata(path.lstat())
    if before[2] != reviewed_pin.size_bytes:
        raise ValueError('Input size differs from reviewed pin')
    # Read exactly one bounded stream; hash and parser consume the same bytes.
    with path.open('rb') as stream:
        opened=_metadata(os.fstat(stream.fileno()))
        # Windows path and handle APIs can expose different ctime semantics.
        # Compare identity/size/mtime across APIs, but compare the complete
        # metadata (including ctime) before/after within each same API.
        if opened[:4] != before[:4]:
            raise ValueError('Input changed before open')
        raw=stream.read(reviewed_pin.size_bytes+1)
        after=_metadata(os.fstat(stream.fileno()))
    guard(path)
    if (after != opened or _metadata(path.lstat()) != before
            or len(raw) != reviewed_pin.size_bytes
            or sha256(raw).hexdigest() != reviewed_pin.sha256):
        raise ValueError('Input identity/content changed during observation')
    return raw, FileReadReceipt(reviewed_pin,before,synthetic_fixture)


def read_fixture_benchmark(*, path, fixture_root, reviewed_pin, spec, is_synthetic=True):
    if is_synthetic is not True:
        raise RuntimeError('Fixture reader cannot admit canonical inputs')
    spec.validate()
    # Tests supply only temporary fixtures. This is a trusted test seam, not
    # permission to inspect arbitrary real assets under a fixture label.
    root=guard(Path(fixture_root));candidate=guard(Path(path))
    candidate.resolve(strict=True).relative_to(root.resolve(strict=True))
    if _key(str(candidate)) == _key(spec.benchmark_path):
        raise ValueError('Canonical benchmark cannot be a synthetic fixture')
    raw,receipt=_read_once(candidate,reviewed_pin=reviewed_pin,synthetic_fixture=True)
    return receipt,bind_benchmark_bytes(raw,spec=spec,
        reviewed_sha256=reviewed_pin.sha256,is_synthetic=True)


def read_canonical_benchmark(*, spec, reviewed_pin):
    if not COHORT_INPUT_ADMITTED:
        raise RuntimeError('Canonical cohort input reading remains blocked')
    spec.validate();reviewed_pin.validate()
    if (_key(reviewed_pin.path) != _key(spec.benchmark_path)
            or reviewed_pin.sha256 != spec.benchmark_sha256):
        raise ValueError('Canonical benchmark pin required')
    raw,receipt=_read_once(Path(spec.benchmark_path),reviewed_pin=reviewed_pin,
                           synthetic_fixture=False)
    return receipt,bind_benchmark_bytes(raw,spec=spec,
        reviewed_sha256=spec.benchmark_sha256,is_synthetic=False)


def bind_inventory(*, observed_pins, reviewed_pins, required_paths, benchmark_receipt):
    """Pure exact selected-file binding, not a scan, signature or authority.

    Observed pin rows must originate in a separately trusted inventory lifecycle.
    This rejects missing/extra/aliased entries and ensures the benchmark receipt
    refers to the same pinned bytes. It cannot prove how arbitrary rows arose.
    """
    def index(rows):
        if type(rows) is not tuple or not rows:
            raise ValueError('Immutable nonempty inventory required')
        result={}
        for pin in rows:
            if type(pin) is not FilePin:
                raise ValueError('Typed inventory file pins required')
            pin.validate();key=_key(pin.path)
            if key in result:
                raise ValueError('Duplicate or aliased inventory path')
            result[key]=pin
        return result
    if type(required_paths) is not tuple or not required_paths:
        raise ValueError('Independent required file set needed')
    keys=[_key(path) for path in required_paths]
    if len(set(keys)) != len(keys):
        raise ValueError('Aliased required paths')
    observed,reviewed=index(observed_pins),index(reviewed_pins)
    if set(observed)!=set(keys) or set(reviewed)!=set(keys) or observed!=reviewed:
        raise ValueError('Inventory differs from complete reviewed selected-file set')
    if type(benchmark_receipt) is not FileReadReceipt:
        raise ValueError('Benchmark read receipt required')
    pin=benchmark_receipt.pin
    if type(pin) is not FilePin or observed.get(_key(pin.path))!=pin:
        raise ValueError('Benchmark receipt does not match selected inventory')
    if (type(benchmark_receipt.synthetic_fixture) is not bool
            or type(benchmark_receipt.metadata) is not tuple
            or len(benchmark_receipt.metadata)!=5
            or any(type(v) is not int or v < 0 for v in benchmark_receipt.metadata)
            or benchmark_receipt.metadata[2]!=pin.size_bytes):
        raise ValueError('Malformed benchmark observation metadata')
    return tuple(observed[key] for key in sorted(observed))


def main():
    print('BLOCKED: canonical file inventory and parent admission pending')
    return 2


if __name__=='__main__':raise SystemExit(main())
