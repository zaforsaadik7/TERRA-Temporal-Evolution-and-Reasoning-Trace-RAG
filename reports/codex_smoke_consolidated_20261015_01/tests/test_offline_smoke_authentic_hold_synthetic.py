"""Verify holds before any paths/imports/model/database operations."""
import unittest
from unittest.mock import patch
from scripts.matched_baseline.offline_smoke_authentic import (
    construct_authentic_worker, LocalMiniLM)


class AuthenticHoldTests(unittest.TestCase):
    def test_construct_hold_precedes_path_or_hash_access(self):
        with patch('scripts.matched_baseline.offline_smoke_authentic.ProtectedInventoryAuditor.hash_file_sha256',
                   side_effect=AssertionError('No filesystem access')):
            with self.assertRaisesRegex(RuntimeError,'not admitted'):
                construct_authentic_worker(None,None,None)

    def test_tokenizer_hold_precedes_cache_access(self):
        instance = object.__new__(LocalMiniLM)
        with self.assertRaisesRegex(RuntimeError,'not admitted'):
            instance._get_tokenizer()

    def test_session_hold_precedes_cache_access(self):
        instance = object.__new__(LocalMiniLM)
        with self.assertRaisesRegex(RuntimeError,'not admitted'):
            instance._get_session()

    def test_secondary_worker_hold_precedes_io_even_if_flag_changes(self):
        with patch('scripts.matched_baseline.offline_smoke_authentic.PRODUCTION_ADMITTED', True), \
             patch('scripts.matched_baseline.offline_smoke_authentic.ProtectedInventoryAuditor.hash_file_sha256',
                   side_effect=AssertionError('No filesystem access')):
            with self.assertRaisesRegex(RuntimeError,'frozen role prompts'):
                construct_authentic_worker(None,None,None)
