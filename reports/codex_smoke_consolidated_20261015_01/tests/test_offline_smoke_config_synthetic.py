"""Pure in-memory configuration checks; no real benchmark or approval read."""
from dataclasses import replace
from hashlib import sha256
import unittest
from scripts.matched_baseline.offline_smoke_config import SmokeLaunchConfig, SmokeConfigurationError


class ConfigTests(unittest.TestCase):
    def setUp(self):
        pins = {name: 'a' * 64 for name in ('interpreter','driver','benchmark','graph',
                'snapshot_manifest','store_inventory','cache_inventory','tokenizer_manifests')}
        self.config = SmokeLaunchConfig(command=('F:\\fake\\python.exe','F:\\fake\\child.py'),
            query_id='synthetic-query', query_text_sha256=sha256(b'synthetic text').hexdigest(),
            authorization_id='synthetic-approval', authorization_sha256='b'*64,
            offline_condition='TEMPORARY_INTERPRETER_FIREWALL', rule_name='TERRA_Smoke_fake_001',
            lock_path='F:\\fake\\smoke.lock', evidence_directory='F:\\fake\\record',
            timeout_seconds=60, memory_bytes=1000, output_limit_bytes=100,
            pins=tuple(pins.items()))
        self.context = dict(reviewed_command=self.config.command, reviewed_pins=pins,
            reviewed_authorization=('synthetic-approval','b'*64), reviewed_query_id='synthetic-query',
            query_text='synthetic text', reviewed_paths=(self.config.lock_path,self.config.evidence_directory),
            reviewed_limits=(60,1000,100), reviewed_rule_name='TERRA_Smoke_fake_001')

    def test_matching_context_validates_without_io(self):
        self.assertIsNone(self.config.validate(**self.context))

    def test_mismatches_rejected(self):
        cases = dict(scope='FULL_PREFLIGHT', hypothetical_routes=('EASY',),
            command=('F:\\fake\\other.exe',), query_id='other', query_text_sha256='c'*64,
            authorization_sha256='d'*64, offline_condition='unknown', rule_name='foreign',
            output_limit_bytes=True, memory_bytes=2000, lock_path='relative.lock')
        for field, value in cases.items():
            with self.subTest(field=field):
                with self.assertRaises(SmokeConfigurationError):
                    replace(self.config, **{field:value}).validate(**self.context)

    def test_duplicate_pins_rejected(self):
        bad = replace(self.config, pins=self.config.pins + (self.config.pins[0],))
        with self.assertRaisesRegex(SmokeConfigurationError, 'pin set'):
            bad.validate(**self.context)

    def test_missing_asset_family_rejected_even_if_context_matches(self):
        pins = dict(self.context['reviewed_pins'])
        del pins['cache_inventory']
        context = {**self.context, 'reviewed_pins': pins}
        with self.assertRaisesRegex(SmokeConfigurationError, 'asset family'):
            replace(self.config, pins=tuple(pins.items())).validate(**context)
