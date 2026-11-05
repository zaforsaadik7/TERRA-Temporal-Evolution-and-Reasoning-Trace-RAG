"""Strict one-query child request; parsing is not execution authorization."""
from dataclasses import asdict, dataclass
import hashlib
import json
import re


@dataclass(frozen=True)
class SmokeChildRequest:
    scope: str
    query_id: str
    query_text: str
    query_text_sha256: str
    authorization_id: str
    authorization_sha256: str
    isolation_receipt: dict
    protected_pins: dict
    seed_k: int
    expected_documents: int
    limits: dict

    def validate(self):
        if self.scope != 'ONE_QUERY_OFFLINE_SMOKE':
            raise ValueError('Wrong child request scope')
        if type(self.query_id) is not str or not self.query_id or type(self.query_text) is not str or not self.query_text:
            raise ValueError('Missing query identity')
        if hashlib.sha256(self.query_text.encode('utf-8')).hexdigest() != self.query_text_sha256:
            raise ValueError('Query hash mismatch')
        if not self.authorization_id or type(self.authorization_sha256) is not str or not re.fullmatch('[0-9a-f]{64}',self.authorization_sha256):
            raise ValueError('Invalid approval reference')
        if type(self.isolation_receipt) is not dict or set(self.isolation_receipt) != {
                'receipt_id','source_dir','snapshot_dir','disposable_dir','manifest_sha256','file_count','created_utc'}:
            raise ValueError('Invalid isolation receipt fields')
        if type(self.protected_pins) is not dict or not self.protected_pins or any(
                type(key) is not str or not key or type(value) is not str or
                not re.fullmatch('[0-9a-f]{64}',value) for key,value in self.protected_pins.items()):
            raise ValueError('Invalid protected pins')
        required = {'interpreter','driver','benchmark','graph','snapshot_manifest',
                    'store_inventory','cache_inventory','tokenizer_manifests'}
        if not required.issubset(self.protected_pins):
            raise ValueError('Missing protected input family')
        receipt = self.isolation_receipt
        if (type(receipt['file_count']) is not int or receipt['file_count'] <= 0 or
                type(receipt['manifest_sha256']) is not str or
                not re.fullmatch('[0-9a-f]{64}',receipt['manifest_sha256']) or any(
                type(receipt[key]) is not str or not receipt[key] for key in (
                    'receipt_id','source_dir','snapshot_dir','disposable_dir','created_utc'))):
            raise ValueError('Invalid isolation receipt values')
        if type(self.seed_k) is not int or self.seed_k != 2:
            raise ValueError('Unreviewed graph seed count')
        if type(self.expected_documents) is not int or self.expected_documents <= 0:
            raise ValueError('Expected document population required')
        if type(self.limits) is not dict or set(self.limits) != {'timeout_seconds','memory_bytes','output_limit_bytes'} or any(
                type(value) is not int or value <= 0 for value in self.limits.values()):
            raise ValueError('Invalid resource policies')

    def to_payload(self):
        self.validate()
        return asdict(self)

    @classmethod
    def from_bytes(cls, raw):
        if type(raw) is not bytes or len(raw) > 1024*1024:
            raise ValueError('Child request size/type rejected')
        def unique(pairs):
            result = {}
            for key,value in pairs:
                if key in result:
                    raise ValueError('Duplicate child request JSON field')
                result[key] = value
            return result
        payload = json.loads(raw.decode('utf-8'),object_pairs_hook=unique,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON rejected')))
        if type(payload) is not dict or set(payload) != set(cls.__dataclass_fields__):
            raise ValueError('Unexpected or missing child request fields')
        request = cls(**payload)
        request.validate()
        return request
