"""Child entry-point boundary, production still blocked before request-file I/O.

Only byte/context verification and a fake loader dispatch are currently tested.
No real CLI launch command is admitted by this source checkpoint.
"""
import hashlib
import json
import os
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


if __name__ == '__main__':
    raise SystemExit(main())
