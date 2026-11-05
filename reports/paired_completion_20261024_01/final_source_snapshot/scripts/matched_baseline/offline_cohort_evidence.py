"""Exclusive single-owner evidence sinks; no store/model/process operations.

Containment checks reduce path risk, not a race-proof OS sandbox. The reviewed
parent must allocate disjoint child/parent budgets before cross-process use.
"""
import os
from pathlib import Path
import re
import stat

from scripts.matched_baseline.offline_cohort_controls import ByteBudget


def guard(path):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Absolute non-traversing evidence path required')
    for item in (path,*path.parents):
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
            raise ValueError('Evidence reparse/symlink rejected')
    return path


class BudgetedStream:
    def __init__(self, owner, path, limit):
        self.owner,self.path,self.limit = owner,path,limit
        self.charged,self.closed = 0,False
        self.file = path.open('xb')

    def write(self, raw):
        self.owner.budget.write(raw,self._write_reserved)
        return len(raw)

    def _write_reserved(self, raw):
        """Private sink for the shared ByteBudget's already-charged write.
        Callers must route through that budget (including StageTelemetry).
        This object API is not an OS security boundary against arbitrary code.
        """
        if self.closed or type(raw) is not bytes or self.charged+len(raw)>self.limit:
            raise ValueError('Closed stream or artifact byte limit')
        guard(self.owner.directory);guard(self.path)
        disk = self.path.stat();handle = os.fstat(self.file.fileno())
        if (disk.st_dev,disk.st_ino)!=(handle.st_dev,handle.st_ino) or disk.st_nlink!=1:
            raise ValueError('Evidence file identity/hardlink changed')
        self.charged += len(raw)
        count=self.file.write(raw)
        self.file.flush()
        return count

    def close(self):
        if not self.closed:
            try:
                self.file.flush();os.fsync(self.file.fileno())
            finally:
                self.file.close();self.closed=True


class CohortEvidenceWriter:
    def __init__(self, directory, *, budget_bytes, max_streams=32):
        directory=Path(directory)
        guard(directory.parent)
        if type(max_streams) is not int or not 1<=max_streams<=32:
            raise ValueError('Bounded artifact count required')
        self.budget=ByteBudget(budget_bytes)
        directory.mkdir(exist_ok=False)
        self.directory=guard(directory)
        self.streams=[];self.max_streams=max_streams;self.closed=False

    def new_stream(self, name, *, max_bytes):
        if self.closed or len(self.streams)>=self.max_streams:
            raise ValueError('Evidence writer closed or artifact count exceeded')
        if (type(name) is not str or not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,79}',name)
                or name in ('.','..') or name.endswith('.')
                or name.split('.')[0].upper() in {'CON','PRN','AUX','NUL',
                    *[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}):
            raise ValueError('Invalid direct evidence filename')
        if type(max_bytes) is not int or not 0<max_bytes<=self.budget.limit:
            raise ValueError('Artifact ceiling outside allocated evidence budget')
        guard(self.directory)
        stream=BudgetedStream(self,self.directory/name,max_bytes)
        self.streams.append(stream)
        return stream

    def write_bytes(self,name,raw,*,max_bytes):
        stream=self.new_stream(name,max_bytes=max_bytes)
        try:stream.write(raw)
        finally:stream.close()

    def close(self):
        errors=[]
        for stream in self.streams:
            try:stream.close()
            except Exception as exc:errors.append(type(exc).__name__)
        self.closed=True
        if errors:raise IOError('Evidence closure failed')
