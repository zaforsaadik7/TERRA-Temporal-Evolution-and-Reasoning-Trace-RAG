"""Bounded failure-location metadata, never exception text/locals/source/env.

Uses the existing captured stdout channel; no files, assets or OS APIs opened.
Stages are telemetry, not permission and not an error-recovery mechanism.
"""
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
import json
from pathlib import PureWindowsPath
import re

MAX_RECORD_BYTES = 16384
MAX_CHAIN = 4
MAX_FRAMES = 16
STAGES = frozenset({
    'PACKET_LOAD','CHILD_EXECUTION','INPUT_VERIFICATION','CONTEXT_READ',
    'CONTEXT_EXECUTION','REQUEST_RECEIPT','RUNTIME_IMAGE','WORKER_CONSTRUCTION',
    'NETWORK_GUARD','WORKER_ASSEMBLY','LOCAL_COMPUTATION','REPORT_VALIDATION',
    'PATH_VALIDATION','GRAPH_HASH','RECEIPT_VALIDATION','CACHE_VERIFICATION',
    'DISPOSABLE_READER','STORE_SCHEMA','GRAPH_LOAD','ROLE_TOKENIZERS',
    'MINILM_EMBEDDING','MINILM_TOKENIZER','MINILM_SESSION','UNKNOWN'})
_active = ContextVar('terra_failure_diagnostics', default=None)


class FailureScope:
    def __init__(self):
        self.failed_stage = None


@contextmanager
def failure_scope():
    state = FailureScope()
    token = _active.set(state)
    try:
        yield state
    finally:
        _active.reset(token)


@contextmanager
def diagnostic_stage(name):
    if name not in STAGES:
        raise ValueError('Unsupported diagnostic stage')
    try:
        yield
    except Exception:
        state = _active.get()
        # Preserve the deepest failed stage, not the outer wrapper's label.
        if state is not None and state.failed_stage is None:
            state.failed_stage = name
        raise


def _label(value, limit=120):
    return re.sub(r'[^A-Za-z0-9_.<>-]', '_', value[:limit])


def failure_record(exc, *, stage):
    """No str(exc), traceback formatting, source reads or local-variable capture."""
    record = {'schema_version':1,'status':'CHILD_FAILURE',
              'stage':stage if stage in STAGES else 'UNKNOWN',
              'exception_type':_label(type(exc).__name__),
              'message_omitted':True,'locals_omitted':True,'source_text_omitted':True,
              'traceback_chain':[],'truncated':False}
    seen = set()
    while exc is not None and id(exc) not in seen and len(record['traceback_chain']) < MAX_CHAIN:
        seen.add(id(exc))
        frames = deque(maxlen=MAX_FRAMES)
        tb = exc.__traceback__
        count = 0
        while tb is not None:
            code = tb.tb_frame.f_code
            frames.append({'file':_label(PureWindowsPath(code.co_filename).name),
                           'function':_label(code.co_name),'line':tb.tb_lineno})
            count += 1
            tb = tb.tb_next
        record['traceback_chain'].append({'exception_type':_label(type(exc).__name__),
            'frames':list(frames),'frames_truncated':count > MAX_FRAMES})
        record['truncated'] |= count > MAX_FRAMES
        exc = exc.__cause__ if exc.__cause__ is not None else (
            None if exc.__suppress_context__ else exc.__context__)
    record['truncated'] |= exc is not None
    return record


def emit_child_failure(exc, *, stage):
    """Best-effort telemetry cannot turn failure into success or mask exit 1."""
    try:
        record = failure_record(exc, stage=stage)
        encoded = json.dumps(record, sort_keys=True, ensure_ascii=True)
        while len(encoded.encode('utf-8')) > MAX_RECORD_BYTES:
            record['truncated'] = True
            if len(record['traceback_chain']) > 1:
                record['traceback_chain'].pop()
            elif record['traceback_chain'] and record['traceback_chain'][0]['frames']:
                record['traceback_chain'][0]['frames'].pop(0)
            else:
                break
            encoded = json.dumps(record, sort_keys=True, ensure_ascii=True)
        print('CHILD FAILURE: '+record['exception_type'], flush=True)
        print('CHILD FAILURE DETAIL: '+encoded, flush=True)
        return True
    except Exception:
        # No recursive exception formatting or alternate artifact overwrite.
        return False
