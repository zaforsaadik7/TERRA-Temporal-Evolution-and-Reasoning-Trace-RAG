"""Child entry-point boundary, production still blocked before request-file I/O.

Only byte/context verification and a fake loader dispatch are currently tested.
No real CLI launch command is admitted by this source checkpoint.
"""
import hashlib
import argparse
import json
import os
import re
from pathlib import Path
from scripts.matched_baseline.offline_preflight import IntegrityLifecycleManager
from scripts.matched_baseline.offline_smoke_request import SmokeChildRequest
from scripts.matched_baseline.offline_smoke_report import validate_smoke_report


def execute_synthetic_request(raw, *, expected_request_sha256, reviewed_context,
                              worker_loader, is_synthetic=True):
    if is_synthetic is not True:
        raise RuntimeError('Authentic child entry execution not admitted')
    if type(raw) is not bytes or len(raw) > 1024*1024:
        raise ValueError('Child request byte bound exceeded')
    if hashlib.sha256(raw).hexdigest() != expected_request_sha256:
        raise ValueError('Saved child request hash mismatch')
    request = SmokeChildRequest.from_bytes(raw)
    payload = request.to_payload()
    # Context is independently supplied by the outer reviewed gate. Echoing a
    # request into this argument is not human authorization or current pin proof.
    if type(reviewed_context) is not dict or set(reviewed_context) != set(payload):
        raise ValueError('Missing independent child request context')
    if payload != reviewed_context:
        raise ValueError('Child request differs from reviewed scope/context')
    worker = worker_loader(request)
    result = worker.run(query_id=request.query_id,query_text=request.query_text,
        expected_query_id=request.query_id,expected_query_sha256=request.query_text_sha256)
    return validate_smoke_report(result, request)


def main(argv=None):
    # Holds ahead of argparse, filesystem access and model/database imports.
    # Removing this rejection is a code change requiring complete source review
    # and a separately approved frozen execution packet, not a CLI switch.
    print('BLOCKED: authentic child entry admission/context still pending')
    return 2


def execute_request_files(request_path, *, expected_request_sha256,
                          reviewed_context, worker_loader, is_synthetic=True):
    """Connect saved parent request to child result using temporary fixtures.

    Production CLI admission remains separate. Never overwrite a prior report;
    an exclusive partial file on failure is preserved as failed-run evidence.
    """
    if is_synthetic is not True:
        raise RuntimeError('Authentic file entry execution not admitted')
    request_path = Path(request_path)
    if not request_path.is_absolute() or request_path.name != 'child_request.json':
        raise ValueError('Absolute canonical child request path required')
    IntegrityLifecycleManager.check_symlink_and_reparse_containment(request_path)
    if not request_path.is_file():
        raise ValueError('Ordinary child request required')
    report_path = request_path.with_name('child_report.json')
    # Reserve before loading any dependencies; collisions must stop before work.
    with report_path.open('xb') as output:
        with request_path.open('rb') as stream:
            raw = stream.read(1024*1024+1)
        result = execute_synthetic_request(raw,
            expected_request_sha256=expected_request_sha256,
            reviewed_context=reviewed_context,worker_loader=worker_loader)
        encoded = json.dumps(result,allow_nan=False,sort_keys=True).encode('utf-8')
        if len(encoded) > 16*1024*1024:
            raise ValueError('Child report byte bound exceeded')
        output.write(encoded)
        output.flush()
        os.fsync(output.fileno())
    return {'report_path':str(report_path),'size_bytes':len(encoded),
            'sha256':hashlib.sha256(encoded).hexdigest()}


def execute_injected_cli(argv, *, expected_request_path, expected_request_sha256,
                         reviewed_context, worker_loader, is_synthetic=True):
    """In-process CLI integration for fake workers, not the production main.

    Frozen context and digest are supplied independently, never read from the
    request or accepted as command-line overrides. No environment is consulted.
    """
    if is_synthetic is not True:
        raise RuntimeError('Authentic CLI execution not admitted')
    if type(argv) is not list or any(type(arg) is not str for arg in argv):
        raise ValueError('Explicit argument vector required')
    # Exact shape rejects duplicates, abbreviations and extra policy switches.
    if len(argv) != 2 or argv[0] != '--request':
        raise ValueError('Only one exact --request argument permitted')
    parser = argparse.ArgumentParser(allow_abbrev=False,add_help=False)
    parser.add_argument('--request',required=True)
    arguments = parser.parse_args(argv)
    candidate,expected = Path(arguments.request),Path(expected_request_path)
    if not candidate.is_absolute() or not expected.is_absolute() or str(candidate) != str(expected):
        raise ValueError('CLI request differs from frozen path')
    return execute_request_files(candidate,expected_request_sha256=expected_request_sha256,
        reviewed_context=reviewed_context,worker_loader=worker_loader,is_synthetic=True)


def encode_child_context(*, request_path, request_sha256, reviewed_context):
    """Serialize parent context; the returned digest needs independent transport."""
    payload = {'request_path':str(request_path),'request_sha256':request_sha256,
               'reviewed_context':reviewed_context}
    raw = json.dumps(payload,sort_keys=True,allow_nan=False).encode('utf-8')
    if len(raw) > 2*1024*1024:
        raise ValueError('Child context byte bound exceeded')
    return raw,hashlib.sha256(raw).hexdigest()


def execute_context_cli(argv, *, context_bytes, expected_context_sha256,
                        worker_loader, is_synthetic=True):
    """Validate transported bytes before file access or fake worker loading.

    A digest stored beside its own untrusted context is not authentication.
    Genuine parent transport and admission remain separate unfinished work.
    """
    if is_synthetic is not True:
        raise RuntimeError('Authentic context transport not admitted')
    if type(context_bytes) is not bytes or len(context_bytes) > 2*1024*1024:
        raise ValueError('Child context byte bound exceeded')
    if hashlib.sha256(context_bytes).hexdigest() != expected_context_sha256:
        raise ValueError('Transported context digest mismatch')
    def unique(pairs):
        value = {}
        for key,item in pairs:
            if key in value:
                raise ValueError('Duplicate context field')
            value[key] = item
        return value
    context = json.loads(context_bytes.decode('utf-8'),object_pairs_hook=unique,
        parse_constant=lambda item: (_ for _ in ()).throw(ValueError('Nonfinite context')))
    if type(context) is not dict or set(context) != {'request_path','request_sha256','reviewed_context'}:
        raise ValueError('Unexpected child context fields')
    if type(context['request_path']) is not str or type(context['request_sha256']) is not str:
        raise ValueError('Invalid context identity types')
    if not re.fullmatch('[0-9a-f]{64}',context['request_sha256']):
        raise ValueError('Invalid context request digest')
    # Reuse the strict request parser to validate the whole reviewed payload.
    SmokeChildRequest.from_bytes(json.dumps(context['reviewed_context'],allow_nan=False).encode())
    return execute_injected_cli(argv,expected_request_path=context['request_path'],
        expected_request_sha256=context['request_sha256'],
        reviewed_context=context['reviewed_context'],worker_loader=worker_loader)


if __name__ == '__main__':
    raise SystemExit(main())
