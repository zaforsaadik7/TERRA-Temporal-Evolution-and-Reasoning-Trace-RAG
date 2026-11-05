"""In-memory JSON request tests only; no child or filesystem operations."""
import json
from hashlib import sha256
import unittest
from scripts.matched_baseline.offline_smoke_request import SmokeChildRequest


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.payload = dict(scope='ONE_QUERY_OFFLINE_SMOKE',query_id='synthetic',query_text='fixture',
            query_text_sha256=sha256(b'fixture').hexdigest(),authorization_id='fake-approval',
            authorization_sha256='a'*64,protected_pins={key:'b'*64 for key in (
                'interpreter','driver','benchmark','graph','snapshot_manifest',
                'store_inventory','cache_inventory','tokenizer_manifests')},seed_k=2,expected_documents=1,
            limits={'timeout_seconds':1,'memory_bytes':100,'output_limit_bytes':100},
            isolation_receipt=dict(receipt_id='fake',source_dir='fake-source',snapshot_dir='fake-snapshot',
                disposable_dir='fake-disposable',manifest_sha256='c'*64,file_count=1,created_utc='fake'))

    def test_roundtrip(self):
        request = SmokeChildRequest.from_bytes(json.dumps(self.payload).encode())
        self.assertEqual(request.to_payload(),self.payload)

    def test_unknown_fields_rejected(self):
        for field in ('category','gold','api_key','python_code'):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError,'Unexpected'):
                    SmokeChildRequest.from_bytes(json.dumps({**self.payload,field:'forbidden'}).encode())

    def test_duplicate_json_fields_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            SmokeChildRequest.from_bytes(b'{"scope":"a","scope":"b"}')

    def test_hash_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            SmokeChildRequest.from_bytes(json.dumps({**self.payload,'query_text':'changed'}).encode())
