"""Synthetic approval records only; no actual permission created or inferred."""
from dataclasses import replace
import hashlib
import json
import unittest
from scripts.matched_baseline.offline_smoke_approval import verify_approval_bytes
from tests import test_offline_smoke_config_synthetic as config_fixture


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        fixture = config_fixture.ConfigTests(); fixture.setUp()
        self.config = fixture.config
        self.record = dict(approval_id=self.config.authorization_id,approval_date='2026-10-15',
            scope=self.config.scope,command=list(self.config.command),query_id=self.config.query_id,
            query_text_sha256=self.config.query_text_sha256,offline_condition=self.config.offline_condition,
            rule_name=self.config.rule_name,allow_create_remove_rule=True,max_attempts=1,
            allow_api_calls=False,allow_manuscript_changes=False,
            limits=dict(timeout_seconds=60,memory_bytes=1000,output_limit_bytes=100))

    def verify(self, record=None, reviewed=None):
        record = self.record if record is None else record
        raw = json.dumps(record).encode()
        digest = hashlib.sha256(raw).hexdigest()
        return verify_approval_bytes(raw,expected_sha256=digest,
            reviewed_record=record if reviewed is None else reviewed,
            config=replace(self.config,authorization_sha256=digest))

    def test_matching_synthetic_record(self):
        self.assertEqual(self.verify(),self.record)

    def test_reviewed_record_mismatch(self):
        with self.assertRaisesRegex(ValueError,'separately reviewed'):
            self.verify(reviewed={**self.record,'approval_id':'different'})

    def test_no_broader_scope_even_if_record_echoed(self):
        for field,value in (('max_attempts',2),('max_attempts',True),('allow_api_calls',True),
                            ('allow_manuscript_changes',True),('allow_create_remove_rule',False)):
            with self.subTest(field=field,value=value):
                with self.assertRaisesRegex(ValueError,'one attempt'):
                    self.verify({**self.record,field:value})

    def test_wrong_query_rejected(self):
        with self.assertRaisesRegex(ValueError,'scope/config'):
            self.verify({**self.record,'query_id':'different'})

    def test_invalid_date_rejected(self):
        with self.assertRaisesRegex(ValueError,'dated approval'):
            self.verify({**self.record,'approval_date':'not a date'})
