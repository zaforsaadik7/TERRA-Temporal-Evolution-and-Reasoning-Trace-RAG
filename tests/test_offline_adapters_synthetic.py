"""
test_offline_adapters_synthetic.py
----------------------------------
Synthetic unit test suite for Stage 1 preflight adapters:
1. IsolationReceipt issuance, 3-way lifecycle parity, and containment validation.
2. Authentic Chroma SQLite schema validation, Layer 1 corpus extraction, and native L2 retrieval.
3. Multi-collection isolation and strict read-only enforcement.
4. Dense candidate retrieval validation: rejecting missing distances, fabricated zeros,
   boolean distances, non-finite values, and candidate overflows.
5. BoundedMemoryGraphLoader (StreamingGraphLoader): memory ceiling, XZ extension enforcement,
   duplicate JSON key rejection, and graph schema auditing.

All tests operate strictly on synthetic in-memory/temp fixtures.
Zero connection to real databases, models, or network endpoints.
"""

import hashlib
import json
import lzma
import math
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from typing import Any, Dict, List, Optional
import unittest
from unittest import mock
import numpy as np

from scripts.matched_baseline.common_serializer import ConfigurationError, SecurityViolationError
from scripts.matched_baseline.offline_preflight import (
    BoundedMemoryGraphLoader,
    BudgetExceededError,
    CacheVerificationReceipt,
    ChromaDisposableReader,
    CleanChildEnvironmentBuilder,
    ConfigurationBlockedError,
    ContainmentViolationError,
    CorpusParityError,
    DestinationCollisionError,
    DirectoryOverlapError,
    ExecutionAuthorizationError,
    ExecutionAuthorizationReceipt,
    GraphSchemaAuditor,
    GraphSchemaError,
    InProcessNetworkBlocker,
    IntegrityCheckError,
    IntegrityLifecycleManager,
    IsolationReceipt,
    LaunchGateSequencer,
    LockCollisionError,
    ManifestVerificationError,
    NetworkAccessBlockedError,
    OfflineChromaClientFactory,
    OfflineExecutionScope,
    OfflineMiniLMEmbeddingFunction,
    OfflinePreflightSupervisor,
    OfflineSmokeGateConfig,
    ReadOnlyViolationError,
    SingleUseExecutionLock,
    StreamingGraphLoader,
    SupervisorExecutionError,
    SymlinkContainmentError,
    WindowsFirewallManager,
)


class TestOfflineAdaptersSynthetic(unittest.TestCase):
    """Synthetic unit tests for Stage 1 offline preflight adapters."""

    def _native_metric_reader(self, *, space='l2',enabled=True,key='#embedding',legacy='{}'):
        self._create_synthetic_sqlite_db(self.source_dir/'chroma.sqlite3',metric=None,raw_config_json=legacy)
        schema = {'defaults':{'float_list':{'vector_index':{'enabled':False,'config':{'space':'l2'}}}},
            'keys':{key:{'float_list':{'vector_index':{'enabled':enabled,'config':{'space':space}}}}}}
        connection = sqlite3.connect(self.source_dir/'chroma.sqlite3')
        try:
            connection.execute('ALTER TABLE collections ADD COLUMN schema_str TEXT')
            connection.execute('UPDATE collections SET schema_str=? WHERE name=?',
                (json.dumps(schema),'thinking_traces'))
            connection.commit()
        finally:
            connection.close()
        _,receipt = self._create_synthetic_lifecycle_copies()
        return ChromaDisposableReader(receipt,self.disposable_dir,self.source_dir)

    def test_native_schema_metric_when_config_json_is_empty(self):
        reader = self._native_metric_reader()
        self.assertEqual(reader.validate_store_schema()['metric'],'l2')

    def test_native_schema_cosine_is_rejected(self):
        reader = self._native_metric_reader(space='cosine')
        with self.assertRaises(IntegrityCheckError): reader.validate_store_schema()

    def test_native_schema_inactive_vector_is_rejected(self):
        reader = self._native_metric_reader(enabled=False)
        with self.assertRaises(IntegrityCheckError): reader.validate_store_schema()

    def test_native_schema_unrelated_default_space_is_not_evidence(self):
        reader = self._native_metric_reader(key='unrelated')
        with self.assertRaises(IntegrityCheckError): reader.validate_store_schema()

    def test_native_and_legacy_metric_conflict_is_rejected(self):
        reader = self._native_metric_reader(space='cosine',legacy=json.dumps({'hnsw:space':'l2'}))
        with self.assertRaisesRegex(IntegrityCheckError,'Conflicting'): reader.validate_store_schema()

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_adapters_synthetic_"))
        self.source_dir = self.temp_dir / "mock_source"
        self.snapshot_dir = self.temp_dir / "mock_snapshot"
        self.disposable_dir = self.temp_dir / "mock_disposable"

        self.source_dir.mkdir(parents=True)
        # Create synthetic store files
        hnsw_dir = self.source_dir / "hnsw_index_sub"
        hnsw_dir.mkdir()
        (hnsw_dir / "data_level0.bin").write_bytes(b"\x00\x01\x02\x03")
        self._create_synthetic_sqlite_db(self.source_dir / "chroma.sqlite3")

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_synthetic_lifecycle_copies(self):
        """Helper to create snapshot and disposable copy and return IsolationReceipt with 3-way parity."""
        IntegrityLifecycleManager.create_preserved_snapshot(self.source_dir, self.snapshot_dir)
        disp_manifest = IntegrityLifecycleManager.create_disposable_copy(
            self.snapshot_dir, self.disposable_dir
        )
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            source_dir=self.source_dir,
            snapshot_dir=self.snapshot_dir,
            disposable_dir=self.disposable_dir,
            disposable_manifest=disp_manifest,
        )
        return disp_manifest, receipt

    def _setup_custom_lifecycle(
        self,
        collection_name: str = "thinking_traces",
        dimension: int = 384,
        metric: Optional[str] = "l2",
        documents: Optional[dict] = None,
        include_secondary: bool = True,
        raw_config_json: Optional[str] = None,
        inject_duplicate_id: bool = False,
    ):
        """Helper to create custom database in source_dir and propagate with 3-way lifecycle parity."""
        if self.snapshot_dir.exists():
            shutil.rmtree(self.snapshot_dir)
        if self.disposable_dir.exists():
            shutil.rmtree(self.disposable_dir)
        self._create_synthetic_sqlite_db(
            self.source_dir / "chroma.sqlite3",
            collection_name=collection_name,
            dimension=dimension,
            metric=metric,
            documents=documents,
            include_secondary_collection=include_secondary,
            raw_config_json=raw_config_json,
            inject_duplicate_id=inject_duplicate_id,
        )
        return self._create_synthetic_lifecycle_copies()

    def _create_synthetic_sqlite_db(
        self,
        db_path: Path,
        collection_name: str = "thinking_traces",
        dimension: int = 384,
        metric: Optional[str] = "l2",
        documents: Optional[dict] = None,
        include_secondary_collection: bool = True,
        raw_config_json: Optional[str] = None,
        inject_duplicate_id: bool = False,
    ):
        """Helper to create authentic Chroma SQLite schema with multiple collections."""
        if db_path.exists():
            db_path.unlink()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 1. collections table
        cursor.execute("""
            CREATE TABLE collections (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE,
                topic TEXT,
                dimension INTEGER,
                config_json_str TEXT
            )
        """)

        # 2. collection_metadata table
        cursor.execute("""
            CREATE TABLE collection_metadata (
                collection_id TEXT,
                key TEXT,
                str_value TEXT,
                int_value INTEGER,
                float_value REAL,
                bool_value INTEGER,
                PRIMARY KEY (collection_id, key)
            )
        """)

        # 3. segments table
        cursor.execute("""
            CREATE TABLE segments (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                scope TEXT NOT NULL,
                collection TEXT REFERENCES collections(id)
            )
        """)

        # 4. segment_metadata table
        cursor.execute("""
            CREATE TABLE segment_metadata (
                segment_id TEXT,
                key TEXT,
                str_value TEXT,
                int_value INTEGER,
                float_value REAL,
                bool_value INTEGER,
                PRIMARY KEY (segment_id, key)
            )
        """)

        # 5. embeddings table (integer internal ID, distinct external embedding_id)
        cursor.execute("""
            CREATE TABLE embeddings (
                id INTEGER PRIMARY KEY,
                segment_id TEXT NOT NULL,
                embedding_id TEXT NOT NULL,
                seq_id BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (segment_id, embedding_id)
            )
        """)

        # 6. embedding_metadata table
        cursor.execute("""
            CREATE TABLE embedding_metadata (
                id INTEGER,
                key TEXT NOT NULL,
                string_value TEXT,
                int_value INTEGER,
                float_value REAL,
                bool_value INTEGER,
                PRIMARY KEY (id, key)
            )
        """)

        # Populate target collection
        coll_id = "coll_uuid_001"
        seg_id = "seg_uuid_001"
        cfg_str = raw_config_json if raw_config_json is not None else (json.dumps({"hnsw:space": metric}) if metric else None)

        cursor.execute(
            "INSERT INTO collections VALUES (?, ?, ?, ?, ?)",
            (coll_id, collection_name, "test_topic", dimension, cfg_str),
        )
        if metric:
            cursor.execute(
                "INSERT INTO collection_metadata VALUES (?, ?, ?, ?, ?, ?)",
                (coll_id, "hnsw:space", metric, None, None, None),
            )

        cursor.execute(
            "INSERT INTO segments VALUES (?, ?, ?, ?)",
            (seg_id, "urn:chroma:segment/vector/hnsw", "VECTOR", coll_id),
        )
        if metric:
            cursor.execute(
                "INSERT INTO segment_metadata VALUES (?, ?, ?, ?, ?, ?)",
                (seg_id, "hnsw:space", metric, None, None, None),
            )

        docs = documents if documents is not None else {
            "case_001": "Full holding text for case 001",
            "case_002": "Full holding text for case 002",
            "case_003": "Full holding text for case 003",
        }
        for int_id, (ext_id, doc_text) in enumerate(docs.items(), start=1):
            cursor.execute(
                "INSERT INTO embeddings (id, segment_id, embedding_id, seq_id) VALUES (?, ?, ?, ?)",
                (int_id, seg_id, ext_id, b"\x00"),
            )
            cursor.execute(
                "INSERT INTO embedding_metadata (id, key, string_value) VALUES (?, ?, ?)",
                (int_id, "chroma:document", doc_text),
            )

        if inject_duplicate_id:
            dup_seg_id = "seg_uuid_dup_metadata"
            cursor.execute(
                "INSERT INTO segments VALUES (?, ?, ?, ?)",
                (dup_seg_id, "urn:chroma:segment/metadata", "METADATA", coll_id),
            )
            cursor.execute(
                "INSERT INTO embeddings (id, segment_id, embedding_id, seq_id) VALUES (?, ?, ?, ?)",
                (888, dup_seg_id, "case_001", b"\x00"),
            )
            cursor.execute(
                "INSERT INTO embedding_metadata (id, key, string_value) VALUES (?, ?, ?)",
                (888, "chroma:document", "Duplicate holding text for case_001"),
            )

        # Secondary collection to verify multi-collection isolation
        if include_secondary_collection:
            other_coll_id = "coll_uuid_other"
            other_seg_id = "seg_uuid_other"
            cursor.execute(
                "INSERT INTO collections VALUES (?, ?, ?, ?, ?)",
                (other_coll_id, "statutes_corpus", "other_topic", 384, json.dumps({"hnsw:space": "l2"})),
            )
            cursor.execute(
                "INSERT INTO collection_metadata VALUES (?, ?, ?, ?, ?, ?)",
                (other_coll_id, "hnsw:space", "l2", None, None, None),
            )
            cursor.execute(
                "INSERT INTO segments VALUES (?, ?, ?, ?)",
                (other_seg_id, "urn:chroma:segment/vector/hnsw", "VECTOR", other_coll_id),
            )
            cursor.execute(
                "INSERT INTO segment_metadata VALUES (?, ?, ?, ?, ?, ?)",
                (other_seg_id, "hnsw:space", "l2", None, None, None),
            )
            cursor.execute(
                "INSERT INTO embeddings (id, segment_id, embedding_id, seq_id) VALUES (?, ?, ?, ?)",
                (999, other_seg_id, "statute_sec_999", b"\x00"),
            )
            cursor.execute(
                "INSERT INTO embedding_metadata (id, key, string_value) VALUES (?, ?, ?)",
                (999, "chroma:document", "Unrelated statute text that must not bleed into thinking_traces"),
            )

        conn.commit()
        conn.close()

    # =========================================================================
    # 1. IsolationReceipt & Containment Validation Tests
    # =========================================================================

    def test_isolation_receipt_issue_and_fields(self):
        """Verify IsolationReceipt creation, aggregate hashing, and fields."""
        disp_manifest, receipt = self._create_synthetic_lifecycle_copies()
        self.assertIsInstance(receipt, IsolationReceipt)
        self.assertTrue(receipt.receipt_id.startswith("iso_rcpt_"))
        self.assertEqual(receipt.source_dir, str(self.source_dir.resolve()))
        self.assertEqual(receipt.snapshot_dir, str(self.snapshot_dir.resolve()))
        self.assertEqual(receipt.disposable_dir, str(self.disposable_dir.resolve()))
        self.assertEqual(receipt.file_count, 2)
        self.assertEqual(len(receipt.manifest_sha256), 64)

    def test_isolation_receipt_3way_parity_enforced_at_issuance(self):
        """Assert 3-way lifecycle parity: disparity between source, snapshot, and disposable raises IntegrityCheckError."""
        IntegrityLifecycleManager.create_preserved_snapshot(self.source_dir, self.snapshot_dir)
        IntegrityLifecycleManager.create_disposable_copy(self.snapshot_dir, self.disposable_dir)

        # Alter file in snapshot so snapshot differs from source
        (self.snapshot_dir / "chroma.sqlite3").write_bytes(b"altered_snapshot_bytes")

        with self.assertRaises(IntegrityCheckError):
            IntegrityLifecycleManager.issue_isolation_receipt(
                source_dir=self.source_dir,
                snapshot_dir=self.snapshot_dir,
                disposable_dir=self.disposable_dir,
            )

    def test_containment_validation_success(self):
        """Verify valid containment check succeeds and returns resolved disposable path."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        res = IntegrityLifecycleManager.validate_disposable_containment(
            receipt=receipt,
            candidate_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        self.assertEqual(res, self.disposable_dir.resolve())

    def test_containment_validation_candidate_mismatch(self):
        """Reject candidate directory that does not match receipt disposable path."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        wrong_dir = self.temp_dir / "wrong_disposable"
        wrong_dir.mkdir()
        with self.assertRaises(ContainmentViolationError):
            IntegrityLifecycleManager.validate_disposable_containment(
                receipt=receipt,
                candidate_dir=wrong_dir,
                expected_source_dir=self.source_dir,
            )

    def test_containment_validation_source_mismatch(self):
        """Reject expected source directory that does not match receipt source path."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        wrong_source = self.temp_dir / "wrong_source"
        wrong_source.mkdir()
        with self.assertRaises(ContainmentViolationError):
            IntegrityLifecycleManager.validate_disposable_containment(
                receipt=receipt,
                candidate_dir=self.disposable_dir,
                expected_source_dir=wrong_source,
            )

    def test_containment_validation_source_aliasing(self):
        """Reject candidate directory if it aliases the source store."""
        fake_receipt = IsolationReceipt(
            receipt_id="iso_fake",
            source_dir=str(self.source_dir.resolve()),
            snapshot_dir=str(self.snapshot_dir.resolve()),
            disposable_dir=str(self.source_dir.resolve()),
            manifest_sha256="abc",
            file_count=1,
            created_utc="2026-10-14T00:00:00Z",
        )
        with self.assertRaises(ContainmentViolationError):
            IntegrityLifecycleManager.validate_disposable_containment(
                receipt=fake_receipt,
                candidate_dir=self.source_dir,
                expected_source_dir=self.source_dir,
            )

    def test_containment_validation_snapshot_aliasing(self):
        """Reject candidate directory if it aliases the snapshot directory."""
        IntegrityLifecycleManager.create_preserved_snapshot(self.source_dir, self.snapshot_dir)
        fake_receipt = IsolationReceipt(
            receipt_id="iso_fake",
            source_dir=str(self.source_dir.resolve()),
            snapshot_dir=str(self.snapshot_dir.resolve()),
            disposable_dir=str(self.snapshot_dir.resolve()),
            manifest_sha256="abc",
            file_count=1,
            created_utc="2026-10-14T00:00:00Z",
        )
        with self.assertRaises(ContainmentViolationError):
            IntegrityLifecycleManager.validate_disposable_containment(
                receipt=fake_receipt,
                candidate_dir=self.snapshot_dir,
                expected_source_dir=self.source_dir,
            )

    def test_containment_validation_hierarchical_overlap(self):
        """Reject disposable copy if it is nested inside source or snapshot."""
        nested_disp = self.source_dir / "nested_disposable"
        nested_disp.mkdir()
        fake_receipt = IsolationReceipt(
            receipt_id="iso_fake",
            source_dir=str(self.source_dir.resolve()),
            snapshot_dir=str(self.snapshot_dir.resolve()),
            disposable_dir=str(nested_disp.resolve()),
            manifest_sha256="abc",
            file_count=1,
            created_utc="2026-10-14T00:00:00Z",
        )
        with self.assertRaises(DirectoryOverlapError):
            IntegrityLifecycleManager.validate_disposable_containment(
                receipt=fake_receipt,
                candidate_dir=nested_disp,
                expected_source_dir=self.source_dir,
            )

    def test_containment_validation_manifest_tampering_before_binding(self):
        """Before client binding, any file addition (including .wal/.shm) or alteration raises ManifestVerificationError."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        # Inject unexpected WAL file before client binding
        (self.disposable_dir / "chroma.sqlite3-wal").write_bytes(b"injected_wal_data")

        with self.assertRaises(ManifestVerificationError):
            IntegrityLifecycleManager.validate_disposable_containment(
                receipt=receipt,
                candidate_dir=self.disposable_dir,
                expected_source_dir=self.source_dir,
                pre_binding=True,
            )

    def test_containment_validation_spoofed_disposable_name(self):
        """Reject directory named 'disposable' if passed without an authentic matching receipt."""
        spoofed = self.temp_dir / "my_disposable_store"
        spoofed.mkdir()
        fake_receipt = IsolationReceipt(
            receipt_id="iso_fake",
            source_dir=str(self.source_dir.resolve()),
            snapshot_dir=str(self.snapshot_dir.resolve()),
            disposable_dir=str(self.disposable_dir.resolve()),
            manifest_sha256="abc",
            file_count=1,
            created_utc="2026-10-14T00:00:00Z",
        )
        with self.assertRaises(ContainmentViolationError):
            IntegrityLifecycleManager.validate_disposable_containment(
                receipt=fake_receipt,
                candidate_dir=spoofed,
                expected_source_dir=self.source_dir,
            )

    # =========================================================================
    # 2. ChromaDisposableReader Schema & Corpus Tests (Authentic Chroma)
    # =========================================================================

    def test_chroma_disposable_reader_schema_validation_success(self):
        """Verify reader validates authentic schema: thinking_traces, 384-dim, and l2 space."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        info = reader.validate_store_schema()
        self.assertTrue(info["schema_valid"])
        self.assertEqual(info["name"], "thinking_traces")
        self.assertEqual(info["dimension"], 384)
        self.assertEqual(info["metric"], "l2")

    def test_chroma_disposable_reader_missing_collection(self):
        """Fail closed when collection thinking_traces is absent."""
        _, receipt = self._setup_custom_lifecycle(collection_name="other_name")

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        with self.assertRaises(IntegrityCheckError):
            reader.validate_store_schema()

    def test_chroma_disposable_reader_dimension_mismatch(self):
        """Fail closed when dimension does not equal 384."""
        _, receipt = self._setup_custom_lifecycle(dimension=768)

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        with self.assertRaises(IntegrityCheckError):
            reader.validate_store_schema()

    def test_chroma_disposable_reader_metric_mismatch(self):
        """Fail closed when distance metric is not l2 (e.g. cosine)."""
        _, receipt = self._setup_custom_lifecycle(metric="cosine")

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        with self.assertRaises(IntegrityCheckError):
            reader.validate_store_schema()

    def test_chroma_disposable_reader_metric_fail_closed_on_absent_or_malformed(self):
        """Fail closed when hnsw:space is absent or malformed JSON (never defaults to l2)."""
        # Absent metric
        _, receipt_absent = self._setup_custom_lifecycle(metric=None)
        reader_absent = ChromaDisposableReader(
            receipt=receipt_absent,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        with self.assertRaises(IntegrityCheckError):
            reader_absent.validate_store_schema()

        # Malformed JSON in collection configuration
        _, receipt_malformed = self._setup_custom_lifecycle(
            metric=None, raw_config_json="INVALID_JSON{{{"
        )
        reader_malformed = ChromaDisposableReader(
            receipt=receipt_malformed,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        with self.assertRaises(IntegrityCheckError):
            reader_malformed.validate_store_schema()

    def test_chroma_disposable_reader_extract_layer1_corpus_authentic_join(self):
        """Extract Layer 1 document texts using authentic Chroma join and enforce expected count."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        docs = reader.extract_layer1_corpus(expected_count=3)
        self.assertEqual(len(docs), 3)
        self.assertEqual(docs["case_001"], "Full holding text for case 001")
        self.assertIn("case_002", docs)
        self.assertIn("case_003", docs)

        # Cardinality mismatch raises CorpusParityError
        with self.assertRaises(CorpusParityError):
            reader.extract_layer1_corpus(expected_count=100)

    def test_chroma_disposable_reader_extract_layer1_multi_collection_isolation(self):
        """Verify extraction filters strictly by collection segment and never mixes foreign collections."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        docs = reader.extract_layer1_corpus()
        # Verify statute_sec_999 from secondary collection was not extracted
        self.assertNotIn("statute_sec_999", docs)
        self.assertEqual(len(docs), 3)

    def test_chroma_disposable_reader_extract_rejects_empty_or_duplicate_documents(self):
        """Reject empty or duplicate documents during corpus extraction."""
        # 1. Test empty document text raises IntegrityCheckError
        empty_docs = {"case_001": "Doc 1", "case_empty": "   "}
        _, receipt_empty = self._setup_custom_lifecycle(documents=empty_docs, include_secondary=False)
        reader_empty = ChromaDisposableReader(
            receipt=receipt_empty,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        with self.assertRaises(IntegrityCheckError):
            reader_empty.extract_layer1_corpus()

        # 2. Test cross-segment duplicate embedding_id within the collection raises IntegrityCheckError
        _, receipt_dup = self._setup_custom_lifecycle(inject_duplicate_id=True, include_secondary=False)
        reader_dup = ChromaDisposableReader(
            receipt=receipt_dup,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        with self.assertRaises(IntegrityCheckError):
            reader_dup.extract_layer1_corpus()

    def test_chroma_disposable_reader_get_client_blocked_without_factory(self):
        """Calling get_client() without explicit client_factory raises ConfigurationBlockedError."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=None,
        )
        with self.assertRaises(ConfigurationBlockedError):
            reader.get_client()

    # =========================================================================
    # 3. Dense Query Interface, Validation & Tie-Breaking Tests
    # =========================================================================

    def test_chroma_disposable_reader_query_dense_candidates_success(self):
        """Verify query_dense_candidates returns ordered IDs from mock client."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        class MockCollection:
            def query(self, query_texts, n_results, include):
                return {
                    "ids": [["doc_c", "doc_a", "doc_b"]],
                    "distances": [[0.85, 0.12, 0.45]],
                }

        class MockClient:
            def get_collection(self, name):
                return MockCollection()

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: MockClient(),
        )

        results = reader.query_dense_candidates(["Synthetic Query"], top_k=100)
        self.assertEqual(len(results), 1)
        # Primary sorted by distance ascending: 0.12 -> doc_a, 0.45 -> doc_b, 0.85 -> doc_c
        self.assertEqual(results[0], ["doc_a", "doc_b", "doc_c"])

    def test_chroma_disposable_reader_deterministic_tie_breaking(self):
        """Deterministic tie-breaking: identical distances sort ascending by document_id."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        class MockCollection:
            def query(self, query_texts, n_results, include):
                return {
                    "ids": [["doc_z", "doc_a", "doc_m"]],
                    "distances": [[0.35, 0.35, 0.10]],
                }

        class MockClient:
            def get_collection(self, name):
                return MockCollection()

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: MockClient(),
        )

        results = reader.query_dense_candidates(["Query with tie"], top_k=100)
        # doc_m is lowest (0.10); doc_a and doc_z tie at 0.35 -> doc_a sorts before doc_z
        self.assertEqual(results[0], ["doc_m", "doc_a", "doc_z"])

    def test_chroma_disposable_reader_rejects_top_k_not_100(self):
        """Reject query request when top_k != 100."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: None,
        )
        with self.assertRaises(ConfigurationError):
            reader.query_dense_candidates(["Query"], top_k=50)

    def test_chroma_disposable_reader_rejects_missing_query_distances(self):
        """Reject retrieval results where distances is missing or None (never fabricates 0.0)."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        class MockCollectionNoDistances:
            def query(self, query_texts, n_results, include):
                return {"ids": [["doc_z", "doc_a"]]}

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: type("C", (), {"get_collection": lambda s, *a, **k: MockCollectionNoDistances()})(),
        )
        with self.assertRaises(IntegrityCheckError):
            reader.query_dense_candidates(["Test Query"], top_k=100)

    def test_chroma_disposable_reader_rejects_boolean_distance(self):
        """Reject boolean distances (e.g. True)."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        class MockCollectionBoolDist:
            def query(self, query_texts, n_results, include):
                return {"ids": [["doc_a"]], "distances": [[True]]}

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: type("C", (), {"get_collection": lambda s, *a, **k: MockCollectionBoolDist()})(),
        )
        with self.assertRaises(IntegrityCheckError):
            reader.query_dense_candidates(["Q"], top_k=100)

    def test_chroma_disposable_reader_rejects_nan_and_inf_distances(self):
        """Reject non-finite distances (NaN, Inf)."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        class MockCollectionNan:
            def query(self, query_texts, n_results, include):
                return {"ids": [["doc_a"]], "distances": [[float("nan")]]}

        reader_nan = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: type("C", (), {"get_collection": lambda s, *a, **k: MockCollectionNan()})(),
        )
        with self.assertRaises(IntegrityCheckError):
            reader_nan.query_dense_candidates(["Q"], top_k=100)

        class MockCollectionInf:
            def query(self, query_texts, n_results, include):
                return {"ids": [["doc_a"]], "distances": [[float("inf")]]}

        reader_inf = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: type("C", (), {"get_collection": lambda s, *a, **k: MockCollectionInf()})(),
        )
        with self.assertRaises(IntegrityCheckError):
            reader_inf.query_dense_candidates(["Q"], top_k=100)

    def test_chroma_disposable_reader_negative_distance_tolerance(self):
        """Reject negative distances exceeding floating tolerance, but accept small numerical noise >= -1e-6."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        class MockCollectionNegative:
            def query(self, query_texts, n_results, include):
                return {"ids": [["doc_a"]], "distances": [[-0.05]]}

        reader_neg = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: type("C", (), {"get_collection": lambda s, *a, **k: MockCollectionNegative()})(),
        )
        with self.assertRaises(IntegrityCheckError):
            reader_neg.query_dense_candidates(["Q"], top_k=100)

        class MockCollectionTolerance:
            def query(self, query_texts, n_results, include):
                return {"ids": [["doc_a"]], "distances": [[-1e-7]]}

        reader_tol = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: type("C", (), {"get_collection": lambda s, *a, **k: MockCollectionTolerance()})(),
        )
        res = reader_tol.query_dense_candidates(["Q"], top_k=100)
        self.assertEqual(res, [["doc_a"]])

    def test_chroma_disposable_reader_rejects_candidate_overflow(self):
        """Reject retrieval results returning more candidates than top_k."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        class MockCollectionOverflow:
            def query(self, query_texts, n_results, include):
                # Return 101 candidates for top_k=100
                ids = [f"doc_{i}" for i in range(101)]
                dists = [0.1 * i for i in range(101)]
                return {"ids": [ids], "distances": [dists]}

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: type("C", (), {"get_collection": lambda s, *a, **k: MockCollectionOverflow()})(),
        )
        with self.assertRaises(IntegrityCheckError):
            reader.query_dense_candidates(["Q"], top_k=100)

    def test_chroma_disposable_reader_rejects_duplicate_or_empty_ids(self):
        """Reject retrieval results with duplicate or empty IDs."""
        _, receipt = self._create_synthetic_lifecycle_copies()

        class MockCollectionDup:
            def query(self, query_texts, n_results, include):
                return {"ids": [["doc_a", "doc_a"]], "distances": [[0.1, 0.2]]}

        reader_dup = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: type("C", (), {"get_collection": lambda s, *a, **k: MockCollectionDup()})(),
        )
        with self.assertRaises(IntegrityCheckError):
            reader_dup.query_dense_candidates(["Q"], top_k=100)

        class MockCollectionEmpty:
            def query(self, query_texts, n_results, include):
                return {"ids": [["   "]], "distances": [[0.1]]}

        reader_empty = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: type("C", (), {"get_collection": lambda s, *a, **k: MockCollectionEmpty()})(),
        )
        with self.assertRaises(IntegrityCheckError):
            reader_empty.query_dense_candidates(["Q"], top_k=100)

    def test_chroma_disposable_reader_rejects_malformed_query_texts(self):
        """Reject empty or whitespace query texts."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: None,
        )
        with self.assertRaises(IntegrityCheckError):
            reader.query_dense_candidates(["   "], top_k=100)

    def test_chroma_disposable_reader_mutating_calls_prohibited(self):
        """Calling add, update, upsert, or delete raises ReadOnlyViolationError."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
            client_factory=lambda p: None,
        )
        with self.assertRaises(ReadOnlyViolationError):
            reader.add(["doc_id"])
        with self.assertRaises(ReadOnlyViolationError):
            reader.update(["doc_id"])
        with self.assertRaises(ReadOnlyViolationError):
            reader.upsert(["doc_id"])
        with self.assertRaises(ReadOnlyViolationError):
            reader.delete(["doc_id"])

    # =========================================================================
    # 4. BoundedMemoryGraphLoader (StreamingGraphLoader) Tests
    # =========================================================================

    def test_bounded_graph_loader_success_compressed_xz(self):
        """Verify BoundedMemoryGraphLoader decompresses .json.xz directly without uncompressed disk writes."""
        graph_dict = {
            "nodes": {
                "node_1": {
                    "node_id": "node_1",
                    "title": "Case 1",
                    "decision_date": "1990-01-01",
                    "substantive_holding": "Holding 1",
                    "thinking_trace": "Trace 1",
                    "snippet": "Snippet 1",
                },
                "node_2": {
                    "node_id": "node_2",
                    "title": "Case 2",
                    "decision_date": "1995-05-05",
                    "substantive_holding": "Holding 2",
                    "thinking_trace": "Trace 2",
                    "snippet": "Snippet 2",
                },
            },
            "edges": [
                {"source": "node_2", "target": "node_1", "relation": "CITES"},
            ],
            "total_nodes": 2,
            "total_edges": 1,
        }
        json_bytes = json.dumps(graph_dict).encode("utf-8")
        xz_bytes = lzma.compress(json_bytes)
        archive_path = self.temp_dir / "synthetic_graph.json.xz"
        archive_path.write_bytes(xz_bytes)

        import hashlib
        expected_sha = hashlib.sha256(xz_bytes).hexdigest()

        nodes, edges, audit = BoundedMemoryGraphLoader.load_graph_archive(
            archive_path=archive_path,
            expected_sha256=expected_sha,
            expected_node_count=2,
        )
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(edges), 1)
        self.assertTrue(audit["schema_valid"])
        self.assertEqual(edges[0]["relation"], "CITES")

    def test_bounded_graph_loader_rejects_plain_json_in_production(self):
        """Reject plain .json archives in production without explicit allow_uncompressed_test_mode."""
        graph_dict = {"nodes": {}, "edges": []}
        archive_path = self.temp_dir / "plain_graph.json"
        archive_path.write_text(json.dumps(graph_dict), encoding="utf-8")

        with self.assertRaises(ConfigurationError):
            BoundedMemoryGraphLoader.load_graph_archive(archive_path)

        # Explicit test mode flag allows .json
        with self.assertRaises(GraphSchemaError):  # Empty nodes collection fails schema audit
            BoundedMemoryGraphLoader.load_graph_archive(
                archive_path, allow_uncompressed_test_mode=True
            )

    def test_bounded_graph_loader_rejects_oversize_decompressed_bytes(self):
        """Raise BudgetExceededError when decompressed bytes exceed ceiling."""
        graph_dict = {
            "nodes": {"node_1": {"node_id": "node_1", "decision_date": "1990-01-01"}},
            "edges": [],
        }
        json_bytes = json.dumps(graph_dict).encode("utf-8")
        xz_bytes = lzma.compress(json_bytes)
        archive_path = self.temp_dir / "oversize_graph.json.xz"
        archive_path.write_bytes(xz_bytes)

        # Set artificially small max_decompressed_bytes (e.g. 10 bytes)
        with self.assertRaises(BudgetExceededError):
            BoundedMemoryGraphLoader.load_graph_archive(
                archive_path=archive_path,
                max_decompressed_bytes=10,
            )

    def test_bounded_graph_loader_rejects_duplicate_json_keys(self):
        """Raise GraphSchemaError when graph JSON contains duplicate keys."""
        # Manually create JSON with duplicate keys
        duplicate_json = (
            '{"nodes": {"n1": {"node_id": "n1", "decision_date": "1990-01-01"}, '
            '"n1": {"node_id": "n1", "decision_date": "1995-01-01"}}, "edges": []}'
        )
        xz_bytes = lzma.compress(duplicate_json.encode("utf-8"))
        archive_path = self.temp_dir / "duplicate_keys.json.xz"
        archive_path.write_bytes(xz_bytes)

        with self.assertRaises(GraphSchemaError):
            BoundedMemoryGraphLoader.load_graph_archive(archive_path)

    def test_bounded_graph_loader_rejects_corrupted_xz(self):
        """Raise IntegrityCheckError on corrupted XZ archive."""
        archive_path = self.temp_dir / "corrupted.json.xz"
        archive_path.write_bytes(b"\xfd7zXZ\x00corrupted_bytes_here")

        with self.assertRaises(IntegrityCheckError):
            BoundedMemoryGraphLoader.load_graph_archive(archive_path)

    def test_bounded_graph_loader_missing_file(self):
        """Raise IntegrityCheckError on non-existent archive path."""
        non_existent = self.temp_dir / "does_not_exist.json.xz"
        with self.assertRaises(IntegrityCheckError):
            BoundedMemoryGraphLoader.load_graph_archive(non_existent)

    def test_bounded_graph_loader_sha256_mismatch(self):
        """Raise IntegrityCheckError on SHA-256 mismatch."""
        json_bytes = json.dumps({"nodes": {}, "edges": []}).encode("utf-8")
        archive_path = self.temp_dir / "wrong_hash.json.xz"
        archive_path.write_bytes(lzma.compress(json_bytes))

        with self.assertRaises(IntegrityCheckError):
            BoundedMemoryGraphLoader.load_graph_archive(
                archive_path=archive_path,
                expected_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            )

    def test_bounded_graph_loader_schema_dangling_edge(self):
        """Raise GraphSchemaError when graph data contains dangling edge endpoints."""
        graph_dict = {
            "nodes": {
                "node_1": {"node_id": "node_1", "decision_date": "1990-01-01"},
            },
            "edges": [
                {"source": "node_1", "target": "missing_node", "relation": "CITES"},
            ],
        }
        archive_path = self.temp_dir / "dangling_edge.json.xz"
        archive_path.write_bytes(lzma.compress(json.dumps(graph_dict).encode("utf-8")))

        with self.assertRaises(GraphSchemaError):
            BoundedMemoryGraphLoader.load_graph_archive(archive_path)

    def test_bounded_graph_loader_schema_unsupported_relation(self):
        """Raise GraphSchemaError when graph data contains unauthorized relation type."""
        graph_dict = {
            "nodes": {
                "node_1": {"node_id": "node_1"},
                "node_2": {"node_id": "node_2"},
            },
            "edges": [
                {"source": "node_1", "target": "node_2", "relation": "BOGUS_RELATION"},
            ],
        }
        archive_path = self.temp_dir / "unsupported_rel.json.xz"
        archive_path.write_bytes(lzma.compress(json.dumps(graph_dict).encode("utf-8")))

        with self.assertRaises(GraphSchemaError):
            BoundedMemoryGraphLoader.load_graph_archive(archive_path)

    def test_bounded_graph_loader_invalid_node_shape(self):
        """Raise GraphSchemaError when node value is not a dictionary."""
        graph_dict = {
            "nodes": {
                "node_1": "not_a_dictionary",
            },
            "edges": [],
        }
        archive_path = self.temp_dir / "invalid_node_shape.json.xz"
        archive_path.write_bytes(lzma.compress(json.dumps(graph_dict).encode("utf-8")))

        with self.assertRaises(GraphSchemaError):
            BoundedMemoryGraphLoader.load_graph_archive(archive_path)

    def test_bounded_graph_loader_rejects_truncated_xz_with_valid_json(self):
        """Raise IntegrityCheckError when compressed XZ footer is truncated even if JSON is complete."""
        graph_dict = {
            "nodes": {
                "node_1": {
                    "node_id": "node_1",
                    "title": "Case 1",
                    "decision_date": "1990-01-01",
                    "substantive_holding": "Holding 1",
                    "thinking_trace": "Trace 1",
                    "snippet": "Snippet 1",
                },
            },
            "edges": [],
            "total_nodes": 1,
            "total_edges": 0,
        }
        json_bytes = json.dumps(graph_dict).encode("utf-8")
        xz_bytes = lzma.compress(json_bytes)
        # Truncate the final 12 bytes (XZ stream footer)
        truncated_bytes = xz_bytes[:-12]
        archive_path = self.temp_dir / "truncated_footer.json.xz"
        archive_path.write_bytes(truncated_bytes)

        with self.assertRaises(IntegrityCheckError) as ctx:
            BoundedMemoryGraphLoader.load_graph_archive(archive_path)
        self.assertIn("truncated", str(ctx.exception).lower())

    def test_bounded_graph_loader_rejects_trailing_data(self):
        """Raise IntegrityCheckError when unexpected trailing data follows compressed stream."""
        graph_dict = {
            "nodes": {
                "node_1": {
                    "node_id": "node_1",
                    "title": "Case 1",
                    "decision_date": "1990-01-01",
                    "substantive_holding": "Holding 1",
                    "thinking_trace": "Trace 1",
                    "snippet": "Snippet 1",
                },
            },
            "edges": [],
            "total_nodes": 1,
            "total_edges": 0,
        }
        json_bytes = json.dumps(graph_dict).encode("utf-8")
        xz_bytes = lzma.compress(json_bytes)
        # Append unauthorized trailing data
        trailing_archive = self.temp_dir / "trailing_junk.json.xz"
        trailing_archive.write_bytes(xz_bytes + b"\x00\x00UNAUTHORIZED_TRAILING_STREAM")

        with self.assertRaises(IntegrityCheckError) as ctx:
            BoundedMemoryGraphLoader.load_graph_archive(trailing_archive)
        self.assertIn("trailing data", str(ctx.exception).lower())

    def test_bounded_graph_loader_enforces_max_length_on_decompressor(self):
        """Verify that BoundedMemoryGraphLoader passes bounded max_length to decompressor on every call."""
        graph_dict = {
            "nodes": {
                "node_1": {
                    "node_id": "node_1",
                    "title": "Case 1",
                    "decision_date": "1990-01-01",
                    "substantive_holding": "Holding 1",
                    "thinking_trace": "Trace 1",
                    "snippet": "Snippet 1",
                },
            },
            "edges": [],
            "total_nodes": 1,
            "total_edges": 0,
        }
        json_bytes = json.dumps(graph_dict).encode("utf-8")
        xz_bytes = lzma.compress(json_bytes)
        archive_path = self.temp_dir / "recording_graph.json.xz"
        archive_path.write_bytes(xz_bytes)

        recorded_max_lengths = []

        class RecordingDecompressor:
            def __init__(self, memlimit=None):
                self._real = lzma.LZMADecompressor(memlimit=memlimit)

            def decompress(self, data, max_length=-1):
                recorded_max_lengths.append(max_length)
                return self._real.decompress(data, max_length=max_length)

            @property
            def eof(self):
                return self._real.eof

            @property
            def unused_data(self):
                return self._real.unused_data

            @property
            def needs_input(self):
                return self._real.needs_input

        nodes, edges, audit = BoundedMemoryGraphLoader.load_graph_archive(
            archive_path=archive_path,
            decompressor_factory=lambda: RecordingDecompressor(),
        )
        self.assertEqual(len(nodes), 1)
        self.assertGreater(len(recorded_max_lengths), 0)
        # Every decompress call must supply a positive bounded max_length
        for ml in recorded_max_lengths:
            self.assertIsInstance(ml, int)
            self.assertGreater(ml, 0)
            self.assertLessEqual(ml, 65536)

    def test_bounded_graph_loader_rejects_highly_compressible_bomb_expansion(self):
        """Raise BudgetExceededError on highly compressible expansion without unbounded memory allocation."""
        # Highly repetitive payload: >500 KB uncompressed, compresses to ~2 KB
        repeated_text = "Holding text with extensive repetition " * 15000
        graph_dict = {
            "nodes": {
                "node_1": {
                    "node_id": "node_1",
                    "decision_date": "1990-01-01",
                    "substantive_holding": repeated_text,
                }
            },
            "edges": [],
        }
        raw_bytes = json.dumps(graph_dict).encode("utf-8")
        self.assertGreater(len(raw_bytes), 500000)
        xz_bytes = lzma.compress(raw_bytes)
        self.assertLess(len(xz_bytes), 10000)

        archive_path = self.temp_dir / "expansion_bomb.json.xz"
        archive_path.write_bytes(xz_bytes)

        # Ceiling of 20 KB: must halt before inflating all 500 KB into RAM
        with self.assertRaises(BudgetExceededError):
            BoundedMemoryGraphLoader.load_graph_archive(
                archive_path=archive_path,
                max_decompressed_bytes=20000,
            )

    def test_bounded_graph_loader_rejects_invalid_limits(self):
        """Raise ConfigurationError when max_decompressed_bytes or decoder_memlimit are non-positive or non-integer."""
        archive_path = self.temp_dir / "valid_dummy.json.xz"
        archive_path.write_bytes(lzma.compress(b'{"nodes": {}, "edges": []}'))

        for invalid_limit in (0, -1, "250MB", 12.5, None):
            with self.assertRaises(ConfigurationError):
                BoundedMemoryGraphLoader.load_graph_archive(
                    archive_path=archive_path,
                    max_decompressed_bytes=invalid_limit,
                )

        for invalid_mem in (0, -500, "128MB", 64.0):
            with self.assertRaises(ConfigurationError):
                BoundedMemoryGraphLoader.load_graph_archive(
                    archive_path=archive_path,
                    decoder_memlimit=invalid_mem,
                )


class FakeTokenEncoding:
    def __init__(self, ids: List[int], attention_mask: List[int]):
        self.ids = ids
        self.attention_mask = attention_mask


class FakeTokenizer:
    def __init__(self, max_length: int = 256):
        self.max_length = max_length
        self.truncation_enabled = False
        self.padding_enabled = False
        self.truncation_calls = []
        self.padding_calls = []

    def enable_truncation(self, max_length: int = 256):
        self.truncation_enabled = True
        self.max_length = max_length
        self.truncation_calls.append({"max_length": max_length})

    def enable_padding(self, pad_id: int = 0, pad_token: str = "[PAD]", length: int = 256):
        self.padding_enabled = True
        self.max_length = length
        self.padding_calls.append({"pad_id": pad_id, "pad_token": pad_token, "length": length})

    def encode(self, text: str) -> FakeTokenEncoding:
        words = text.split()
        raw_ids = [(abs(hash(w)) % 10000) + 1 for w in words]
        if self.truncation_enabled and len(raw_ids) > self.max_length:
            raw_ids = raw_ids[:self.max_length]

        mask = [1] * len(raw_ids)
        if self.padding_enabled and len(raw_ids) < self.max_length:
            pad_len = self.max_length - len(raw_ids)
            raw_ids.extend([0] * pad_len)
            mask.extend([0] * pad_len)
        return FakeTokenEncoding(raw_ids, mask)


class FakeOnnxSession:
    def __init__(self, output_dim: int = 384, custom_output: Optional[np.ndarray] = None):
        self.output_dim = output_dim
        self.custom_output = custom_output
        self.last_inputs: Optional[Dict[str, Any]] = None

    def run(self, output_names, input_feed):
        self.last_inputs = input_feed
        if self.custom_output is not None:
            return [self.custom_output]
        batch_size, seq_len = input_feed["input_ids"].shape
        out = np.ones((batch_size, seq_len, self.output_dim), dtype=np.float32)
        return [out]


class TestOfflineMiniLMEmbeddingFunctionSynthetic(unittest.TestCase):
    """Synthetic unit tests for OfflineMiniLMEmbeddingFunction and client/collection binding."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_minilm_synthetic_"))
        self.cache_dir = self.temp_dir / "onnx_cache"
        self.cache_dir.mkdir(parents=True)

        # Create synthetic valid ONNX cache files matching EXPECTED_PINS
        self.expected_pins: Dict[str, str] = {}
        for fname in OfflineMiniLMEmbeddingFunction.EXPECTED_PINS.keys():
            content = f"synthetic_onnx_asset_{fname}".encode("utf-8")
            f_p = self.cache_dir / fname
            f_p.write_bytes(content)
            h = hashlib.sha256(content).hexdigest()
            self.expected_pins[fname] = h

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_minilm_explicit_tokenizer_configuration_calls(self):
        """Verify adapter explicitly configures owned tokenizer with enable_truncation and enable_padding."""
        fake_tok = FakeTokenizer(max_length=256)
        fake_sess = FakeOnnxSession(output_dim=384)

        # Initially unconfigured
        self.assertFalse(fake_tok.truncation_enabled)
        self.assertFalse(fake_tok.padding_enabled)

        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=fake_sess,
            is_synthetic=True,
        )

        # Verified configured by adapter
        self.assertTrue(fake_tok.truncation_enabled)
        self.assertTrue(fake_tok.padding_enabled)
        self.assertEqual(len(fake_tok.truncation_calls), 1)
        self.assertEqual(fake_tok.truncation_calls[0], {"max_length": 256})
        self.assertEqual(len(fake_tok.padding_calls), 1)
        self.assertEqual(fake_tok.padding_calls[0], {"pad_id": 0, "pad_token": "[PAD]", "length": 256})

    def test_minilm_fixed_width_256_feeds_across_variable_batches(self):
        """Verify ONNX feeds are strictly fixed-width (batch_size, 256) across variable document lengths."""
        fake_tok = FakeTokenizer(max_length=256)
        fake_sess = FakeOnnxSession(output_dim=384)

        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=fake_sess,
            is_synthetic=True,
        )

        # 1-word doc and 40-word doc
        res = emb_fn(["hello", " ".join([f"word_{i}" for i in range(40)])])
        self.assertEqual(len(res), 2)

        # Input feeds must be strictly fixed-width 256
        self.assertEqual(fake_sess.last_inputs["input_ids"].shape, (2, 256))
        self.assertEqual(fake_sess.last_inputs["attention_mask"].shape, (2, 256))
        self.assertEqual(fake_sess.last_inputs["token_type_ids"].shape, (2, 256))

        # First doc: 1 active token, 255 padded tokens
        self.assertEqual(list(fake_sess.last_inputs["attention_mask"][0][:1]), [1])
        self.assertEqual(list(fake_sess.last_inputs["attention_mask"][0][1:]), [0] * 255)

        # Second doc: 40 active tokens, 216 padded tokens
        self.assertEqual(list(fake_sess.last_inputs["attention_mask"][1][:40]), [1] * 40)
        self.assertEqual(list(fake_sess.last_inputs["attention_mask"][1][40:]), [0] * 216)

    def test_minilm_truncation_of_large_inputs(self):
        """Verify inputs exceeding 256 tokens are truncated to exactly 256."""
        fake_tok = FakeTokenizer(max_length=256)
        fake_sess = FakeOnnxSession(output_dim=384)

        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=fake_sess,
            is_synthetic=True,
        )

        long_text = " ".join([f"token_{i}" for i in range(350)])
        res = emb_fn(long_text)
        self.assertEqual(len(res), 1)
        self.assertEqual(fake_sess.last_inputs["input_ids"].shape, (1, 256))
        self.assertEqual(fake_sess.last_inputs["attention_mask"].shape, (1, 256))
        self.assertEqual(list(fake_sess.last_inputs["attention_mask"][0]), [1] * 256)

    def test_minilm_attention_masking_mean_pooling_math(self):
        """
        Verify mean pooling math with attention weighting:
        Padded tokens with mask=0 must NOT contribute to the pooled mean.
        """
        custom_hidden = np.full((1, 4, 384), 999.0, dtype=np.float32)
        custom_hidden[0, 0, :] = 2.0
        custom_hidden[0, 1, :] = 4.0

        mask = np.array([[1, 1, 0, 0]], dtype=np.int64)

        emb_fn = OfflineMiniLMEmbeddingFunction(is_synthetic=True)
        pooled = emb_fn._mean_pooling(custom_hidden, mask)

        self.assertEqual(pooled.shape, (1, 384))
        np.testing.assert_allclose(pooled[0], np.full(384, 3.0, dtype=np.float32), rtol=1e-5)

    def test_minilm_l2_normalization_math(self):
        """Verify output vectors have Euclidean norm == 1.0, with division by zero protection."""
        emb_fn = OfflineMiniLMEmbeddingFunction(is_synthetic=True)

        # 1. Normal vector
        v = np.random.randn(5, 384).astype(np.float32)
        norm_v = emb_fn._normalize(v)
        norms = np.linalg.norm(norm_v, axis=1)
        np.testing.assert_allclose(norms, np.ones(5, dtype=np.float32), rtol=1e-5)

        # 2. All-zero vector
        v_zeros = np.zeros((2, 384), dtype=np.float32)
        norm_zeros = emb_fn._normalize(v_zeros)
        self.assertFalse(np.isnan(norm_zeros).any())
        self.assertFalse(np.isinf(norm_zeros).any())
        np.testing.assert_allclose(norm_zeros, np.zeros((2, 384), dtype=np.float32))

    def test_minilm_output_dimension_verification(self):
        """Verify function strictly enforces 384-dimension output and rejects invalid dimensions."""
        fake_tok = FakeTokenizer(max_length=256)
        fake_sess_512 = FakeOnnxSession(output_dim=512)

        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=fake_sess_512,
            is_synthetic=True,
        )
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn("Sample text")
        self.assertIn("malformed onnx output shape", str(ctx.exception).lower())

    def test_minilm_cache_verification_success_and_tampered_rejection(self):
        """Verify cache verification checks pins, rejects tampered hashes, and rejects missing files."""
        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            is_synthetic=True,
        )
        receipt = emb_fn.verify_pinned_cache()
        self.assertIsInstance(receipt, CacheVerificationReceipt)
        self.assertEqual(len(receipt.verified_sha256), 6)

        # 2. Missing file raises IntegrityCheckError
        (self.cache_dir / "vocab.txt").unlink()
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn.verify_pinned_cache()
        self.assertIn("missing", str(ctx.exception).lower())

        # 3. Restore vocab and test tampered hash on model.onnx raises IntegrityCheckError
        (self.cache_dir / "vocab.txt").write_bytes(b"synthetic_onnx_asset_vocab.txt")
        (self.cache_dir / "model.onnx").write_bytes(b"tampered_weights")
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn.verify_pinned_cache()
        self.assertIn("digest mismatch", str(ctx.exception).lower())

    def test_minilm_cache_containment_rejects_symlink_before_resolution(self):
        """Verify cache constructor rejects symlinks and reparse points before resolution."""
        with mock.patch("os.path.islink", return_value=True):
            with self.assertRaises(SymlinkContainmentError) as ctx:
                OfflineMiniLMEmbeddingFunction(cache_dir=self.cache_dir, is_synthetic=True)
            self.assertIn("symlink rejected", str(ctx.exception).lower())

    def test_minilm_expected_pins_immutable_in_authentic_mode(self):
        """In authentic mode, caller cannot override expected_pins with partial or altered maps."""
        with self.assertRaises(ConfigurationError) as ctx:
            OfflineMiniLMEmbeddingFunction(
                is_synthetic=False,
                expected_pins={"model.onnx": "foo"},
            )
        self.assertIn("cannot be overridden with partial or custom pins", str(ctx.exception).lower())

    def test_minilm_synthetic_pins_must_have_all_six_assets(self):
        """In synthetic mode, expected_pins must specify all 6 canonical assets."""
        with self.assertRaises(ConfigurationError) as ctx:
            OfflineMiniLMEmbeddingFunction(
                is_synthetic=True,
                expected_pins={"model.onnx": "foo"},
            )
        self.assertIn("must specify all 6 canonical assets", str(ctx.exception).lower())

    def test_minilm_verification_receipt_binding(self):
        """Verify CacheVerificationReceipt is bound to instance upon verification."""
        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            is_synthetic=True,
        )
        self.assertIsNone(emb_fn.verification_receipt)
        receipt = emb_fn.verify_pinned_cache()
        self.assertIsInstance(receipt, CacheVerificationReceipt)
        self.assertIs(emb_fn.verification_receipt, receipt)
        self.assertEqual(receipt.file_count, 6)

    def test_minilm_call_invokes_verification_and_rejects_tampering(self):
        """Verify __call__ validates cache and rejects tampered files before returning embeddings."""
        fake_tok = FakeTokenizer(max_length=256)
        fake_sess = FakeOnnxSession(output_dim=384)
        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=fake_sess,
            is_synthetic=True,
        )
        # Tamper asset on disk before invocation
        (self.cache_dir / "model.onnx").write_bytes(b"tampered_model_bytes")
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn("Sample input")
        self.assertIn("digest mismatch", str(ctx.exception).lower())

    def test_minilm_batch_size_validation(self):
        """Verify batch_size must be a positive non-boolean integer."""
        for bad_size in [True, False, 0, -1, -50, "32", 4.5]:
            with self.subTest(batch_size=bad_size):
                with self.assertRaises(ConfigurationError) as ctx:
                    OfflineMiniLMEmbeddingFunction(batch_size=bad_size, is_synthetic=True)
                self.assertIn("positive non-boolean integer", str(ctx.exception).lower())

    def test_minilm_malformed_onnx_outputs_raise_integrity_error(self):
        """Verify malformed ONNX output ranks, shapes, and sequence lengths raise IntegrityCheckError."""
        fake_tok = FakeTokenizer(max_length=256)

        # 1. Rank 2 output instead of rank 3
        sess_rank2 = FakeOnnxSession(custom_output=np.ones((1, 384), dtype=np.float32))
        emb_fn1 = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=sess_rank2,
            is_synthetic=True,
        )
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn1("Doc")
        self.assertIn("rank-3", str(ctx.exception).lower())

        # 2. Wrong sequence length (128 instead of 256)
        sess_seq128 = FakeOnnxSession(custom_output=np.ones((1, 128, 384), dtype=np.float32))
        emb_fn2 = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=sess_seq128,
            is_synthetic=True,
        )
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn2("Doc")
        self.assertIn("malformed onnx output shape", str(ctx.exception).lower())

    def test_minilm_non_finite_onnx_outputs_raise_integrity_error(self):
        """Verify NaN or Inf in ONNX outputs raises IntegrityCheckError and yields no embeddings."""
        fake_tok = FakeTokenizer(max_length=256)

        # 1. NaN in last_hidden_state
        nan_out = np.ones((1, 256, 384), dtype=np.float32)
        nan_out[0, 10, 20] = np.nan
        sess_nan = FakeOnnxSession(custom_output=nan_out)
        emb_fn_nan = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=sess_nan,
            is_synthetic=True,
        )
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn_nan("Doc")
        self.assertIn("non-finite values (nan/inf)", str(ctx.exception).lower())

        # 2. Inf in last_hidden_state
        inf_out = np.ones((1, 256, 384), dtype=np.float32)
        inf_out[0, 10, 20] = np.inf
        sess_inf = FakeOnnxSession(custom_output=inf_out)
        emb_fn_inf = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=sess_inf,
            is_synthetic=True,
        )
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn_inf("Doc")
        self.assertIn("non-finite values (nan/inf)", str(ctx.exception).lower())

    def test_minilm_call_with_missing_cache_dir_fails_closed(self):
        """Verify __call__ fails closed when cache directory does not exist on disk."""
        missing_dir = self.temp_dir / "nonexistent_cache"
        fake_tok = FakeTokenizer(max_length=256)
        fake_sess = FakeOnnxSession(output_dim=384)
        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=missing_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=fake_sess,
            is_synthetic=True,
        )
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn("Sample text")
        self.assertIn("local onnx cache directory not found", str(ctx.exception).lower())

    def test_minilm_call_success_then_post_verification_tamper_fails_closed(self):
        """
        Verify that after an initial successful call with a bound receipt,
        subsequent tampering, removal, or replacement of assets on disk fails closed
        WITHOUT clearing or resetting the verification receipt.
        """
        fake_tok = FakeTokenizer(max_length=256)
        fake_sess = FakeOnnxSession(output_dim=384)
        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=fake_tok,
            session_instance=fake_sess,
            is_synthetic=True,
        )

        # 1. First call succeeds and establishes receipt
        res1 = emb_fn(["First call"])
        self.assertEqual(len(res1), 1)
        self.assertIsNotNone(emb_fn.verification_receipt)
        initial_receipt = emb_fn.verification_receipt

        # 2. Tamper asset on disk (Case A: Remove file) WITHOUT clearing receipt
        (self.cache_dir / "model.onnx").unlink()
        self.assertIs(emb_fn.verification_receipt, initial_receipt)
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn(["Second call post-removal"])
        self.assertIn("missing on disk", str(ctx.exception).lower())

        # 3. Tamper asset on disk (Case B: Replace file with altered digest) WITHOUT clearing receipt
        (self.cache_dir / "model.onnx").write_bytes(b"tampered_corrupted_model_weights")
        self.assertIs(emb_fn.verification_receipt, initial_receipt)
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn(["Third call post-tamper"])
        self.assertIn("digest mismatch", str(ctx.exception).lower())

        # 4. Tamper asset on disk (Case C: Remove entire cache directory) WITHOUT clearing receipt
        shutil.rmtree(self.cache_dir)
        self.assertIs(emb_fn.verification_receipt, initial_receipt)
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn(["Fourth call post-cache-removal"])
        self.assertIn("not found", str(ctx.exception).lower())

    def test_minilm_tokenizer_lacking_enable_truncation_fails_closed(self):
        """Verify adapter fails closed if tokenizer lacks required enable_truncation method."""
        class TokenizerNoTrunc:
            def enable_padding(self, **kwargs): pass
            def encode(self, text): pass

        with self.assertRaises(IntegrityCheckError) as ctx:
            OfflineMiniLMEmbeddingFunction(
                cache_dir=self.cache_dir,
                expected_pins=self.expected_pins,
                tokenizer_instance=TokenizerNoTrunc(),
                is_synthetic=True,
            )
        self.assertIn("enable_truncation", str(ctx.exception).lower())

    def test_minilm_tokenizer_lacking_enable_padding_fails_closed(self):
        """Verify adapter fails closed if tokenizer lacks required enable_padding method."""
        class TokenizerNoPad:
            def enable_truncation(self, **kwargs): pass
            def encode(self, text): pass

        with self.assertRaises(IntegrityCheckError) as ctx:
            OfflineMiniLMEmbeddingFunction(
                cache_dir=self.cache_dir,
                expected_pins=self.expected_pins,
                tokenizer_instance=TokenizerNoPad(),
                is_synthetic=True,
            )
        self.assertIn("enable_padding", str(ctx.exception).lower())

    def test_minilm_tokenizer_overlength_encoding_rejected_without_slicing(self):
        """Verify tokenizer returning overlength encoding (>256) is rejected and NOT repaired by slicing."""
        class OverlengthTokenizer:
            def enable_truncation(self, **kwargs): pass
            def enable_padding(self, **kwargs): pass
            def encode(self, text):
                return FakeTokenEncoding(ids=[1] * 300, attention_mask=[1] * 300)

        fake_sess = FakeOnnxSession(output_dim=384)
        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=OverlengthTokenizer(),
            session_instance=fake_sess,
            is_synthetic=True,
        )
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn("Sample text")
        self.assertIn("overlength encoding", str(ctx.exception).lower())
        self.assertIn("manual slicing is strictly forbidden", str(ctx.exception).lower())

    def test_minilm_tokenizer_underlength_encoding_rejected_without_padding(self):
        """Verify tokenizer returning underlength encoding (<256) is rejected and NOT repaired by padding."""
        class UnderlengthTokenizer:
            def enable_truncation(self, **kwargs): pass
            def enable_padding(self, **kwargs): pass
            def encode(self, text):
                return FakeTokenEncoding(ids=[1] * 50, attention_mask=[1] * 50)

        fake_sess = FakeOnnxSession(output_dim=384)
        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=UnderlengthTokenizer(),
            session_instance=fake_sess,
            is_synthetic=True,
        )
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn("Sample text")
        self.assertIn("underlength encoding", str(ctx.exception).lower())
        self.assertIn("manual padding is strictly forbidden", str(ctx.exception).lower())

    def test_minilm_tokenizer_mismatched_ids_and_mask_lengths_rejected(self):
        """Verify tokenizer returning mismatched IDs and attention_mask lengths is rejected."""
        class MismatchedTokenizer:
            def enable_truncation(self, **kwargs): pass
            def enable_padding(self, **kwargs): pass
            def encode(self, text):
                return FakeTokenEncoding(ids=[1] * 256, attention_mask=[1] * 200)

        fake_sess = FakeOnnxSession(output_dim=384)
        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=MismatchedTokenizer(),
            session_instance=fake_sess,
            is_synthetic=True,
        )
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn("Sample text")
        self.assertIn("encoding length mismatch", str(ctx.exception).lower())

    def test_minilm_tokenizer_missing_ids_or_mask_attributes_rejected(self):
        """Verify tokenizer output missing 'ids' or 'attention_mask' attributes is rejected."""
        class BadOutputTokenizer:
            def enable_truncation(self, **kwargs): pass
            def enable_padding(self, **kwargs): pass
            def encode(self, text):
                return object()

        fake_sess = FakeOnnxSession(output_dim=384)
        emb_fn = OfflineMiniLMEmbeddingFunction(
            cache_dir=self.cache_dir,
            expected_pins=self.expected_pins,
            tokenizer_instance=BadOutputTokenizer(),
            session_instance=fake_sess,
            is_synthetic=True,
        )
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn("Sample text")
        self.assertIn("lacks required 'ids' attribute", str(ctx.exception).lower())

    def test_minilm_no_download_fallback_enforcement(self):
        """Verify network download is unconditionally forbidden."""
        emb_fn = OfflineMiniLMEmbeddingFunction(is_synthetic=True)
        with self.assertRaises(IntegrityCheckError) as ctx:
            emb_fn._download_model_if_not_exists()
        self.assertIn("network download fallback is unconditionally disabled", str(ctx.exception).lower())

    def test_minilm_authentic_mode_blocks_fakes_and_real_exec(self):
        """In authentic mode (is_synthetic=False), injected fakes and unreviewed calls are strictly blocked."""
        fake_tok = FakeTokenizer()
        with self.assertRaises(ConfigurationError) as ctx:
            OfflineMiniLMEmbeddingFunction(is_synthetic=False, tokenizer_instance=fake_tok)
        self.assertIn("cannot inject synthetic fakes", str(ctx.exception).lower())

        emb_fn = OfflineMiniLMEmbeddingFunction(is_synthetic=False)
        with self.assertRaises(ConfigurationBlockedError) as ctx:
            emb_fn._get_tokenizer()
        self.assertIn("unconditionally blocked", str(ctx.exception).lower())

        with self.assertRaises(ConfigurationBlockedError) as ctx:
            emb_fn._get_session()
        self.assertIn("unconditionally blocked", str(ctx.exception).lower())

    def test_chroma_disposable_reader_binds_offline_embedding_function(self):
        """Verify ChromaDisposableReader stores and binds offline embedding function to get_collection."""
        src_dir = self.temp_dir / "src_bind"
        snap_dir = self.temp_dir / "snap_bind"
        disp_dir = self.temp_dir / "disp_bind"
        src_dir.mkdir(parents=True)
        (src_dir / "chroma.sqlite3").write_bytes(b"dummy_db")

        IntegrityLifecycleManager.create_preserved_snapshot(src_dir, snap_dir)
        disp_man = IntegrityLifecycleManager.create_disposable_copy(snap_dir, disp_dir)
        fake_receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            source_dir=src_dir,
            snapshot_dir=snap_dir,
            disposable_dir=disp_dir,
            disposable_manifest=disp_man,
        )

        captured_bind = {}

        class MockBoundClient:
            def get_collection(self, name, embedding_function=None):
                captured_bind["name"] = name
                captured_bind["embedding_function"] = embedding_function
                return "bound_collection_instance"

        fake_emb_fn = OfflineMiniLMEmbeddingFunction(is_synthetic=True)

        reader = ChromaDisposableReader(
            receipt=fake_receipt,
            disposable_dir=disp_dir,
            expected_source_dir=src_dir,
            client_factory=lambda p: MockBoundClient(),
            embedding_function=fake_emb_fn,
        )
        reader._schema_validated = True

        coll = reader.get_collection()
        self.assertEqual(coll, "bound_collection_instance")
        self.assertEqual(captured_bind["name"], "thinking_traces")
        self.assertIs(captured_bind["embedding_function"], fake_emb_fn)

    def test_offline_chroma_client_factory_governance(self):
        """Verify OfflineChromaClientFactory blocks authentic execution and delegates in synthetic mode."""
        src_dir = self.temp_dir / "gov_src"
        snap_dir = self.temp_dir / "gov_snap"
        disp_dir = self.temp_dir / "gov_disp"
        src_dir.mkdir(parents=True)
        (src_dir / "data.bin").write_bytes(b"content")

        IntegrityLifecycleManager.create_preserved_snapshot(src_dir, snap_dir)
        disp_manifest = IntegrityLifecycleManager.create_disposable_copy(snap_dir, disp_dir)
        iso_receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            source_dir=src_dir,
            snapshot_dir=snap_dir,
            disposable_dir=disp_dir,
            disposable_manifest=disp_manifest,
        )

        factory_auth = OfflineChromaClientFactory(
            expected_source_dir=src_dir,
            expected_snapshot_dir=snap_dir,
            is_synthetic=False,
        )
        with self.assertRaises(ConfigurationBlockedError) as ctx:
            factory_auth(disp_dir, isolation_receipt=iso_receipt)
        self.assertIn("unconditionally blocked", str(ctx.exception).lower())

        fake_emb = OfflineMiniLMEmbeddingFunction(is_synthetic=True)
        factory_synth = OfflineChromaClientFactory(
            embedding_function=fake_emb,
            expected_source_dir=src_dir,
            expected_snapshot_dir=snap_dir,
            is_synthetic=True,
            synthetic_client_factory=lambda path, emb: {"path": path, "emb": emb},
        )
        res = factory_synth(disp_dir, isolation_receipt=iso_receipt)
        self.assertEqual(res["path"], disp_dir.resolve())
        self.assertIs(res["emb"], fake_emb)

    def test_query_dense_candidates_routes_query_texts_only(self):
        """Verify query_dense_candidates routes query_texts exclusively and rejects bypassing."""
        src_dir = self.temp_dir / "src_q"
        snap_dir = self.temp_dir / "snap_q"
        disp_dir = self.temp_dir / "disp_q"
        src_dir.mkdir(parents=True)
        (src_dir / "chroma.sqlite3").write_bytes(b"dummy_db")

        IntegrityLifecycleManager.create_preserved_snapshot(src_dir, snap_dir)
        disp_man_q = IntegrityLifecycleManager.create_disposable_copy(snap_dir, disp_dir)
        fake_receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            source_dir=src_dir,
            snapshot_dir=snap_dir,
            disposable_dir=disp_dir,
            disposable_manifest=disp_man_q,
        )

        captured_queries = []

        class MockQueryCollection:
            def query(self, **kwargs):
                captured_queries.append(kwargs)
                return {
                    "ids": [["doc_1", "doc_2"]],
                    "distances": [[0.1, 0.2]],
                }

        class MockClient:
            def get_collection(self, name, embedding_function=None):
                return MockQueryCollection()

        reader = ChromaDisposableReader(
            receipt=fake_receipt,
            disposable_dir=disp_dir,
            expected_source_dir=src_dir,
            client_factory=lambda p: MockClient(),
        )
        reader._schema_validated = True

        res = reader.query_dense_candidates(query_texts=["hello world"])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], ["doc_1", "doc_2"])
        self.assertIn("query_texts", captured_queries[-1])
        self.assertNotIn("query_embeddings", captured_queries[-1])
        self.assertEqual(captured_queries[-1]["query_texts"], ["hello world"])


class TestGuardedActivationAndLauncherSynthetic(unittest.TestCase):
    """Synthetic unit tests for guarded activation and launcher interfaces."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_guarded_launcher_"))
        self.valid_receipt_kwargs = {
            "scope": "OFFLINE_SMOKE_SINGLE_QUERY",
            "approval_id": "USER_CODEX_AUTH_20261015",
            "command": "python -B scripts/matched_baseline/offline_preflight.py --smoke-gate",
            "query_id": "smoke_q0",
            "query_text_sha256": "9541720173299f71739564a4c3446cddeab6318dcc1824164a066c966dc6bed9",
            "driver_sha256": "1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
            "store_sqlite_sha256": "c7fc28f24403303b384f73f3eac349629661a430aeee3c05e899c8d5e27b475d",
            "cache_manifest_sha256": "3333222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
            "firewall_rule_id": "TERRA_OFFLINE_BLOCK_smoke_q0",
            "issued_utc": "2026-10-15T00:00:00Z",
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_authorization_receipt_validation_success(self):
        """Verify valid ExecutionAuthorizationReceipt passes validation cleanly."""
        receipt = ExecutionAuthorizationReceipt(**self.valid_receipt_kwargs)
        receipt.validate()
        self.assertEqual(receipt.scope, "OFFLINE_SMOKE_SINGLE_QUERY")

    def test_authorization_receipt_missing_or_empty_field(self):
        """Verify ExecutionAuthorizationReceipt fails closed on missing or empty field."""
        for field in self.valid_receipt_kwargs.keys():
            bad_kwargs = dict(self.valid_receipt_kwargs)
            bad_kwargs[field] = ""
            receipt = ExecutionAuthorizationReceipt(**bad_kwargs)
            with self.assertRaises(ExecutionAuthorizationError) as ctx:
                receipt.validate()
            self.assertIn(f"missing or empty required field: '{field}'", str(ctx.exception))

    def test_authorization_receipt_malformed_hash_format(self):
        """Verify ExecutionAuthorizationReceipt rejects invalid hash strings."""
        for hash_field in ("query_text_sha256", "driver_sha256", "store_sqlite_sha256"):
            bad_kwargs = dict(self.valid_receipt_kwargs)
            bad_kwargs[hash_field] = "not_a_valid_64_char_hash"
            receipt = ExecutionAuthorizationReceipt(**bad_kwargs)
            with self.assertRaises(ExecutionAuthorizationError) as ctx:
                receipt.validate()
            self.assertIn("format", str(ctx.exception).lower())

    def test_single_use_execution_lock_lifecycle(self):
        """Verify SingleUseExecutionLock acquires cleanly and creates lock file."""
        lock_path = self.temp_dir / "locks" / "smoke_q0.lock"
        lock = SingleUseExecutionLock(lock_path)
        self.assertFalse(lock.is_locked())
        lock.acquire(metadata={"query": "smoke_q0"})
        self.assertTrue(lock.is_locked())

        with open(lock_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        self.assertEqual(data["metadata"]["query"], "smoke_q0")
        self.assertEqual(data["pid"], os.getpid())

    def test_single_use_execution_lock_collision_fails_closed(self):
        """Verify SingleUseExecutionLock rejects double acquire or preexisting lock."""
        lock_path = self.temp_dir / "locks" / "collision.lock"
        lock1 = SingleUseExecutionLock(lock_path)
        lock1.acquire()

        # In-memory double acquire
        with self.assertRaises(LockCollisionError) as ctx:
            lock1.acquire()
        self.assertIn("already acquired", str(ctx.exception).lower())

        # Second lock instance on preexisting path fails closed
        lock2 = SingleUseExecutionLock(lock_path)
        with self.assertRaises(LockCollisionError) as ctx:
            lock2.acquire()
        self.assertIn("already exists", str(ctx.exception).lower())

    def test_single_use_execution_lock_release_retains_disk_artifact(self):
        """Verify lock release marks inactive in memory without deleting on disk (replay prevention)."""
        lock_path = self.temp_dir / "locks" / "noreplay.lock"
        lock = SingleUseExecutionLock(lock_path)
        lock.acquire()
        lock.release()
        self.assertTrue(lock_path.exists())
        # Re-acquiring still fails because disk artifact persists
        with self.assertRaises(LockCollisionError):
            lock.acquire()

    def test_offline_embedding_function_auth_receipt_guard(self):
        """Verify OfflineMiniLMEmbeddingFunction validates receipt and blocks without it."""
        # Malformed receipt fails at init
        bad_receipt = ExecutionAuthorizationReceipt(**{**self.valid_receipt_kwargs, "scope": ""})
        with self.assertRaises(ExecutionAuthorizationError):
            OfflineMiniLMEmbeddingFunction(is_synthetic=False, auth_receipt=bad_receipt)

        # Without receipt in authentic mode, init succeeds but real loading is blocked
        emb_fn = OfflineMiniLMEmbeddingFunction(is_synthetic=False, auth_receipt=None)
        with self.assertRaises(ConfigurationBlockedError) as ctx:
            emb_fn._get_tokenizer()
        self.assertIn("unconditionally blocked", str(ctx.exception).lower())

        with self.assertRaises(ConfigurationBlockedError) as ctx:
            emb_fn._get_session()
        self.assertIn("unconditionally blocked", str(ctx.exception).lower())

    def test_offline_chroma_client_factory_auth_receipt_guard(self):
        """Verify OfflineChromaClientFactory validates receipt and blocks without it."""
        bad_receipt = ExecutionAuthorizationReceipt(**{**self.valid_receipt_kwargs, "approval_id": ""})
        with self.assertRaises(ExecutionAuthorizationError):
            OfflineChromaClientFactory(is_synthetic=False, auth_receipt=bad_receipt)

        # Missing boundaries raises ConfigurationError
        factory_no_bounds = OfflineChromaClientFactory(is_synthetic=False, auth_receipt=None)
        with self.assertRaises(ConfigurationError):
            factory_no_bounds(self.temp_dir)

        # Missing isolation receipt raises ContainmentViolationError
        factory_with_bounds = OfflineChromaClientFactory(
            expected_source_dir=self.temp_dir / "src",
            expected_snapshot_dir=self.temp_dir / "snap",
            is_synthetic=False,
            auth_receipt=None,
        )
        with self.assertRaises(ContainmentViolationError):
            factory_with_bounds(self.temp_dir)

    def test_offline_smoke_gate_config_invariants(self):
        """Verify OfflineSmokeGateConfig invariants and query text SHA-256."""
        self.assertEqual(OfflineSmokeGateConfig.GATE_NAME, "Stage3D Offline Smoke Gate")
        self.assertEqual(OfflineSmokeGateConfig.QUERY_ID, "smoke_q0")
        actual_sha = hashlib.sha256(OfflineSmokeGateConfig.QUERY_TEXT.encode("utf-8")).hexdigest()
        self.assertEqual(actual_sha, OfflineSmokeGateConfig.QUERY_TEXT_SHA256)
        self.assertEqual(actual_sha, "9541720173299f71739564a4c3446cddeab6318dcc1824164a066c966dc6bed9")

    def test_clean_child_environment_builder(self):
        """Verify CleanChildEnvironmentBuilder applies strict allowlist and offline flags."""
        base_env = {
            "PATH": "/usr/bin;C:\\Windows",
            "SYSTEMROOT": "C:\\Windows",
            "OPENAI_API_KEY": "sk-secret123",
            "DATABRICKS_TOKEN": "dapi-token456",
            "HF_TOKEN": "hf_secret789",
            "AWS_SECRET_ACCESS_KEY": "aws-secret",
            "API_KEY_CUSTOM": "custom-key",
            "USER_PROJECT_ID": "terra_restart_v2",
        }
        cleaned = CleanChildEnvironmentBuilder.build(base_env=base_env)
        self.assertEqual(cleaned["PATH"], "/usr/bin;C:\\Windows")
        self.assertEqual(cleaned["SYSTEMROOT"], "C:\\Windows")
        self.assertEqual(cleaned["HF_HUB_OFFLINE"], "1")
        self.assertEqual(cleaned["TRANSFORMERS_OFFLINE"], "1")
        self.assertEqual(cleaned["NO_PROXY"], "*")

        # Confirm non-allowlisted credentials and arbitrary user vars were stripped
        self.assertNotIn("OPENAI_API_KEY", cleaned)
        self.assertNotIn("DATABRICKS_TOKEN", cleaned)
        self.assertNotIn("HF_TOKEN", cleaned)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", cleaned)
        self.assertNotIn("API_KEY_CUSTOM", cleaned)
        self.assertNotIn("USER_PROJECT_ID", cleaned)

        # Confirm parent env was not mutated
        self.assertIn("OPENAI_API_KEY", base_env)

    def test_in_process_network_blocker(self):
        """Verify InProcessNetworkBlocker intercepts socket and DNS calls, then restores handlers."""
        import socket
        orig_connect = socket.socket.connect
        orig_connect_ex = socket.socket.connect_ex
        orig_sendto = socket.socket.sendto
        orig_getaddrinfo = socket.getaddrinfo
        orig_gethostbyname = socket.gethostbyname
        orig_gethostbyname_ex = socket.gethostbyname_ex

        with InProcessNetworkBlocker():
            s = socket.socket()
            try:
                with self.assertRaises(NetworkAccessBlockedError) as ctx:
                    s.connect(("127.0.0.1", 8080))
                self.assertIn("blocked", str(ctx.exception).lower())

                with self.assertRaises(NetworkAccessBlockedError) as ctx:
                    s.connect_ex(("127.0.0.1", 8080))
                self.assertIn("blocked", str(ctx.exception).lower())

                with self.assertRaises(NetworkAccessBlockedError) as ctx:
                    s.sendto(b"ping", ("127.0.0.1", 8080))
                self.assertIn("blocked", str(ctx.exception).lower())

                with self.assertRaises(NetworkAccessBlockedError) as ctx:
                    socket.getaddrinfo("localhost", 8080)
                self.assertIn("blocked", str(ctx.exception).lower())

                with self.assertRaises(NetworkAccessBlockedError) as ctx:
                    socket.gethostbyname("localhost")
                self.assertIn("blocked", str(ctx.exception).lower())

                with self.assertRaises(NetworkAccessBlockedError) as ctx:
                    socket.gethostbyname_ex("localhost")
                self.assertIn("blocked", str(ctx.exception).lower())
            finally:
                s.close()

        # Confirm restoration of all 6 methods
        self.assertIs(socket.socket.connect, orig_connect)
        self.assertIs(socket.socket.connect_ex, orig_connect_ex)
        self.assertIs(socket.socket.sendto, orig_sendto)
        self.assertIs(socket.getaddrinfo, orig_getaddrinfo)
        self.assertIs(socket.gethostbyname, orig_gethostbyname)
        self.assertIs(socket.gethostbyname_ex, orig_gethostbyname_ex)

    def test_windows_firewall_manager_mock_lifecycle(self):
        """Verify WindowsFirewallManager mock lifecycle and safety constraints."""
        fwm = WindowsFirewallManager(rule_id="TEST_RULE_01", is_synthetic=True)
        self.assertIsNone(fwm.verify_rule())
        props = fwm.create_rule(program_path=Path("venv/Scripts/python.exe"))
        self.assertIsNotNone(props)
        self.assertEqual(props["rule_name"], "TEST_RULE_01")
        self.assertEqual(props["direction"], "outbound")
        self.assertEqual(props["action"], "block")
        self.assertEqual(props["owner_pid"], os.getpid())
        self.assertIsNotNone(fwm.verify_rule())

        # Collision detection: cannot recreate active rule
        with self.assertRaises(IntegrityCheckError):
            fwm.create_rule(program_path=Path("venv/Scripts/python.exe"))

        cmd = fwm.get_manual_recovery_command()
        self.assertEqual(cmd, 'netsh advfirewall firewall delete rule name="TEST_RULE_01"')

        # Non-owner PID cannot remove rule
        fwm._owner_pid = 999999
        with self.assertRaises(SecurityViolationError):
            fwm.remove_rule()

        # Owner PID removes cleanly
        fwm._owner_pid = os.getpid()
        fwm.remove_rule()
        self.assertIsNone(fwm.verify_rule())

        # Authentic mode strictly blocked
        fwm_auth = WindowsFirewallManager(rule_id="AUTH_RULE_01", is_synthetic=False)
        with self.assertRaises(NotImplementedError):
            fwm_auth.create_rule(program_path=Path("venv/Scripts/python.exe"))
        with self.assertRaises(NotImplementedError):
            fwm_auth.verify_rule()
        with self.assertRaises(NotImplementedError):
            fwm_auth.remove_rule()

    def test_authorization_receipt_compute_sha256(self):
        """Verify compute_receipt_sha256 produces deterministic canonical hash."""
        receipt = ExecutionAuthorizationReceipt(**self.valid_receipt_kwargs)
        h1 = receipt.compute_receipt_sha256()
        self.assertEqual(len(h1), 64)
        self.assertEqual(h1, receipt.compute_receipt_sha256())
        # Changing any field changes the hash
        receipt2 = ExecutionAuthorizationReceipt(**{**self.valid_receipt_kwargs, "query_id": "other_q"})
        self.assertNotEqual(h1, receipt2.compute_receipt_sha256())

    def test_authorization_receipt_validate_against_context_success(self):
        """Verify validate_against_context passes when all launch parameters match."""
        receipt = ExecutionAuthorizationReceipt(**self.valid_receipt_kwargs)
        receipt.validate_against_context(
            expected_scope=self.valid_receipt_kwargs["scope"],
            expected_command=self.valid_receipt_kwargs["command"],
            expected_query_id=self.valid_receipt_kwargs["query_id"],
            expected_query_text_sha256=self.valid_receipt_kwargs["query_text_sha256"],
            expected_driver_sha256=self.valid_receipt_kwargs["driver_sha256"],
            expected_store_sqlite_sha256=self.valid_receipt_kwargs["store_sqlite_sha256"],
            expected_cache_manifest_sha256=self.valid_receipt_kwargs["cache_manifest_sha256"],
            expected_firewall_rule_id=self.valid_receipt_kwargs["firewall_rule_id"],
        )

    def test_authorization_receipt_validate_against_context_mismatches(self):
        """Verify validate_against_context fails closed on any parameter mismatch."""
        receipt = ExecutionAuthorizationReceipt(**self.valid_receipt_kwargs)
        test_cases = [
            ("expected_scope", "WRONG_SCOPE"),
            ("expected_command", "WRONG_COMMAND"),
            ("expected_query_id", "WRONG_QID"),
            ("expected_query_text_sha256", "0" * 64),
            ("expected_driver_sha256", "0" * 64),
            ("expected_store_sqlite_sha256", "0" * 64),
            ("expected_cache_manifest_sha256", "0" * 64),
            ("expected_firewall_rule_id", "WRONG_RULE"),
        ]
        for field, bad_val in test_cases:
            kwargs = {
                "expected_scope": self.valid_receipt_kwargs["scope"],
                "expected_command": self.valid_receipt_kwargs["command"],
                "expected_query_id": self.valid_receipt_kwargs["query_id"],
                "expected_query_text_sha256": self.valid_receipt_kwargs["query_text_sha256"],
                "expected_driver_sha256": self.valid_receipt_kwargs["driver_sha256"],
                "expected_store_sqlite_sha256": self.valid_receipt_kwargs["store_sqlite_sha256"],
                "expected_cache_manifest_sha256": self.valid_receipt_kwargs["cache_manifest_sha256"],
                "expected_firewall_rule_id": self.valid_receipt_kwargs["firewall_rule_id"],
            }
            kwargs[field] = bad_val
            with self.assertRaises(ExecutionAuthorizationError) as ctx:
                receipt.validate_against_context(**kwargs)
            self.assertIn("mismatch", str(ctx.exception).lower())

    def _create_synthetic_lifecycle_fixture(self, name: str, with_sqlite: bool = False):
        """Helper creating 3-way lifecycle fixture with valid IsolationReceipt."""
        src = self.temp_dir / f"src_{name}"
        snap = self.temp_dir / f"snap_{name}"
        disp = self.temp_dir / f"disp_{name}"
        src.mkdir(parents=True)
        (src / "f.txt").write_bytes(b"content_data")
        if with_sqlite:
            db_path = src / "chroma.sqlite3"
            conn = sqlite3.connect(str(db_path))
            try:
                cur = conn.cursor()
                cur.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT, dimension INTEGER)")
                cur.execute("INSERT INTO collections VALUES ('coll_1', 'thinking_traces', 384)")
                cur.execute("CREATE TABLE collection_metadata (collection_id TEXT, key TEXT, str_value TEXT)")
                cur.execute("INSERT INTO collection_metadata VALUES ('coll_1', 'hnsw:space', 'l2')")
                conn.commit()
            finally:
                conn.close()
        IntegrityLifecycleManager.create_preserved_snapshot(src, snap)
        disp_manifest = IntegrityLifecycleManager.create_disposable_copy(snap, disp)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            source_dir=src,
            snapshot_dir=snap,
            disposable_dir=disp,
            disposable_manifest=disp_manifest,
        )
        return src, snap, disp, receipt

    def test_offline_chroma_client_factory_disjointness_checks(self):
        """Verify OfflineChromaClientFactory enforces disjointness from source and snapshot dirs."""
        src, snap, disp, receipt = self._create_synthetic_lifecycle_fixture("disjoint")

        factory = OfflineChromaClientFactory(
            expected_source_dir=src,
            expected_snapshot_dir=snap,
            is_synthetic=True,
            synthetic_client_factory=lambda p, ef: "mock_client",
        )

        # Passing source_dir as disposable_dir fails disjointness
        with self.assertRaises(DirectoryOverlapError):
            factory(src, isolation_receipt=receipt)

        # Passing subfolder of source_dir fails
        sub_src = src / "sub"
        sub_src.mkdir()
        with self.assertRaises(DirectoryOverlapError):
            factory(sub_src, isolation_receipt=receipt)

        # Passing snapshot_dir fails
        with self.assertRaises(DirectoryOverlapError):
            factory(snap, isolation_receipt=receipt)

        # Clean disjoint disposable_dir succeeds
        res = factory(disp, isolation_receipt=receipt)
        self.assertEqual(res, "mock_client")

    def test_offline_chroma_client_factory_isolation_receipt_validation(self):
        """Verify OfflineChromaClientFactory verifies IsolationReceipt fields."""
        src, snap, disp, receipt = self._create_synthetic_lifecycle_fixture("iso_val")
        other_disp = self.temp_dir / "disp_other_iso"
        other_disp.mkdir()

        factory = OfflineChromaClientFactory(
            expected_source_dir=src,
            expected_snapshot_dir=snap,
            is_synthetic=True,
            synthetic_client_factory=lambda p, ef: "mock_client",
        )

        # Missing isolation receipt fails closed
        with self.assertRaises(ContainmentViolationError):
            factory(disp, isolation_receipt=None)

        # Missing expected boundaries fails closed
        factory_no_src = OfflineChromaClientFactory(
            expected_source_dir=None,
            expected_snapshot_dir=snap,
            is_synthetic=True,
            synthetic_client_factory=lambda p, ef: "mock_client",
        )
        with self.assertRaises(ConfigurationError):
            factory_no_src(disp, isolation_receipt=receipt)

        # Mismatched disposable dir raises ContainmentViolationError
        with self.assertRaises(ContainmentViolationError):
            factory(other_disp, isolation_receipt=receipt)

        # Valid match succeeds
        res = factory(disp, isolation_receipt=receipt)
        self.assertEqual(res, "mock_client")

        # Authentic mode unconditionally blocks even with valid receipts
        auth_receipt = ExecutionAuthorizationReceipt(**self.valid_receipt_kwargs)
        factory_auth = OfflineChromaClientFactory(
            expected_source_dir=src,
            expected_snapshot_dir=snap,
            auth_receipt=auth_receipt,
            is_synthetic=False,
        )
        with self.assertRaises(ConfigurationBlockedError):
            factory_auth(disp, isolation_receipt=receipt)

    def test_offline_chroma_client_factory_inventory_tamper_fails_closed(self):
        """Verify full disposable inventory revalidation rejects modified, extra, or missing files."""
        src, snap, disp, receipt = self._create_synthetic_lifecycle_fixture("inv_tamper")
        factory = OfflineChromaClientFactory(
            expected_source_dir=src,
            expected_snapshot_dir=snap,
            is_synthetic=True,
            synthetic_client_factory=lambda p, ef: "mock_client",
        )

        # 1. Corrupt file content -> digest mismatch fails
        (disp / "f.txt").write_bytes(b"tampered_content")
        with self.assertRaises(ContainmentViolationError) as ctx:
            factory(disp, isolation_receipt=receipt)
        self.assertIn("digest mismatch", str(ctx.exception).lower())
        (disp / "f.txt").write_bytes(b"content_data")  # restore

        # 2. Extra file added -> count mismatch fails
        (disp / "extra.txt").write_bytes(b"extra")
        with self.assertRaises(ContainmentViolationError) as ctx:
            factory(disp, isolation_receipt=receipt)
        self.assertIn("file count", str(ctx.exception).lower())
        (disp / "extra.txt").unlink()  # restore

        # 3. File removed -> count mismatch fails
        (disp / "f.txt").unlink()
        with self.assertRaises(ContainmentViolationError) as ctx:
            factory(disp, isolation_receipt=receipt)
        self.assertIn("file count", str(ctx.exception).lower())

    def test_chroma_disposable_reader_end_to_end_offline_factory_binding(self):
        """
        Verify end-to-end binding: ChromaDisposableReader passes IsolationReceipt
        to OfflineChromaClientFactory, which constructs a synthetic client,
        fails closed on tampered files before fake construction, and authentic mode
        blocks unconditionally with zero genuine client instantiation.
        """
        src = self.temp_dir / "src_reader_e2e"
        snap = self.temp_dir / "snap_reader_e2e"
        disp = self.temp_dir / "disp_reader_e2e"
        src.mkdir(parents=True)
        (src / "f.txt").write_bytes(b"content_data")

        # Create valid SQLite schema in src before snapshotting
        db_path = src / "chroma.sqlite3"
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.cursor()
            cur.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT, dimension INTEGER)")
            cur.execute("INSERT INTO collections VALUES ('coll_1', 'thinking_traces', 384)")
            cur.execute("CREATE TABLE collection_metadata (collection_id TEXT, key TEXT, str_value TEXT)")
            cur.execute("INSERT INTO collection_metadata VALUES ('coll_1', 'hnsw:space', 'l2')")
            conn.commit()
        finally:
            conn.close()

        IntegrityLifecycleManager.create_preserved_snapshot(src, snap)
        disp_manifest = IntegrityLifecycleManager.create_disposable_copy(snap, disp)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            source_dir=src,
            snapshot_dir=snap,
            disposable_dir=disp,
            disposable_manifest=disp_manifest,
        )

        class MockE2EClient:
            def get_collection(self, name, embedding_function=None):
                return "e2e_collection"

        fake_calls = []
        def fake_builder(p, ef):
            fake_calls.append((p, ef))
            return MockE2EClient()

        factory_synth = OfflineChromaClientFactory(
            expected_source_dir=src,
            expected_snapshot_dir=snap,
            is_synthetic=True,
            synthetic_client_factory=fake_builder,
        )

        # 1. Successful end-to-end receipt delivery and client binding
        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=factory_synth,
        )
        client = reader.get_client()
        self.assertIsInstance(client, MockE2EClient)
        self.assertEqual(len(fake_calls), 1)

        # 2. Tampering rejected before fake construction:
        # Pre-construct reader while directory is intact
        reader_pre = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=factory_synth,
        )
        (disp / "f.txt").write_bytes(b"tampered_data_bytes")

        # Factory-level inventory check rejects before fake_builder is called
        with mock.patch.object(reader_pre, "_revalidate_containment"):
            with self.assertRaises(ContainmentViolationError) as ctx:
                reader_pre.get_client()
            self.assertIn("digest mismatch", str(ctx.exception).lower())
        # Assert fake_builder was NOT called for tampered client request
        self.assertEqual(len(fake_calls), 1)
        (disp / "f.txt").write_bytes(b"content_data")  # restore

        # 3. Authentic mode unconditionally blocks with zero genuine client instantiation
        factory_auth = OfflineChromaClientFactory(
            expected_source_dir=src,
            expected_snapshot_dir=snap,
            is_synthetic=False,
        )
        reader_auth = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=factory_auth,
        )
        with self.assertRaises(ConfigurationBlockedError) as ctx:
            reader_auth.get_client()
        self.assertIn("unconditionally blocked", str(ctx.exception).lower())

    def test_chroma_disposable_reader_factory_internal_error_called_exactly_once(self):
        """
        Verify that internal factory errors (TypeError, ValueError) are not retried,
        the factory is invoked exactly once, the binding flag remains False,
        original errors are preserved, and no fallback receipt-free call occurs.
        """
        src = self.temp_dir / "src_retry_test"
        snap = self.temp_dir / "snap_retry_test"
        disp = self.temp_dir / "disp_retry_test"
        src.mkdir(parents=True)
        (src / "f.txt").write_bytes(b"content_data")

        db_path = src / "chroma.sqlite3"
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.cursor()
            cur.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT, dimension INTEGER)")
            cur.execute("INSERT INTO collections VALUES ('coll_1', 'thinking_traces', 384)")
            cur.execute("CREATE TABLE collection_metadata (collection_id TEXT, key TEXT, str_value TEXT)")
            cur.execute("INSERT INTO collection_metadata VALUES ('coll_1', 'hnsw:space', 'l2')")
            conn.commit()
        finally:
            conn.close()

        IntegrityLifecycleManager.create_preserved_snapshot(src, snap)
        disp_manifest = IntegrityLifecycleManager.create_disposable_copy(snap, disp)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            source_dir=src,
            snapshot_dir=snap,
            disposable_dir=disp,
            disposable_manifest=disp_manifest,
        )

        # 1. Factory raising internal TypeError
        type_call_count = 0
        def failing_type_factory(path, isolation_receipt=None):
            nonlocal type_call_count
            type_call_count += 1
            raise TypeError("Simulated internal factory TypeError")

        reader_type = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=failing_type_factory,
        )
        self.assertFalse(reader_type._bound)
        with self.assertRaises(TypeError) as ctx:
            reader_type.get_client()
        self.assertIn("Simulated internal factory TypeError", str(ctx.exception))
        self.assertEqual(type_call_count, 1)
        self.assertFalse(reader_type._bound)

        # 2. Factory raising internal ValueError
        val_call_count = 0
        def failing_val_factory(path, isolation_receipt=None):
            nonlocal val_call_count
            val_call_count += 1
            raise ValueError("Simulated internal factory ValueError")

        reader_val = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=failing_val_factory,
        )
        self.assertFalse(reader_val._bound)
        with self.assertRaises(ValueError) as ctx:
            reader_val.get_client()
        self.assertIn("Simulated internal factory ValueError", str(ctx.exception))
        self.assertEqual(val_call_count, 1)
        self.assertFalse(reader_val._bound)

        # 3. Uninspectable signature fails closed with ConfigurationError (no execution)
        with mock.patch("inspect.signature", side_effect=TypeError("Signature uninspectable")):
            uninspectable_called = 0
            def uninspectable_factory(path, isolation_receipt=None):
                nonlocal uninspectable_called
                uninspectable_called += 1
                return "never_reached"

            reader_uninspectable = ChromaDisposableReader(
                receipt=receipt,
                disposable_dir=disp,
                expected_source_dir=src,
                client_factory=uninspectable_factory,
            )
            with self.assertRaises(ConfigurationError) as ctx:
                reader_uninspectable.get_client()
            self.assertIn("Unable to inspect signature", str(ctx.exception))
            self.assertEqual(uninspectable_called, 0)
            self.assertFalse(reader_uninspectable._bound)

        # 4. Successful single-argument legacy fake compatibility
        legacy_called = 0
        def legacy_factory(path):
            nonlocal legacy_called
            legacy_called += 1
            return "legacy_client"

        reader_legacy = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=legacy_factory,
        )
        res = reader_legacy.get_client()
        self.assertEqual(res, "legacy_client")
        self.assertEqual(legacy_called, 1)
        self.assertTrue(reader_legacy._bound)

    def test_chroma_disposable_reader_get_collection_internal_errors_called_once_and_unset(self):
        """
        Verify that internal TypeError and ValueError during client.get_collection
        each propagate with exactly one invocation, leave reader._collection unset,
        and never trigger an unbound collection fallback.
        """
        src = self.temp_dir / "src_coll_err_test"
        snap = self.temp_dir / "snap_coll_err_test"
        disp = self.temp_dir / "disp_coll_err_test"
        src.mkdir(parents=True)
        (src / "f.txt").write_bytes(b"content_data")

        db_path = src / "chroma.sqlite3"
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.cursor()
            cur.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT, dimension INTEGER)")
            cur.execute("INSERT INTO collections VALUES ('coll_1', 'thinking_traces', 384)")
            cur.execute("CREATE TABLE collection_metadata (collection_id TEXT, key TEXT, str_value TEXT)")
            cur.execute("INSERT INTO collection_metadata VALUES ('coll_1', 'hnsw:space', 'l2')")
            conn.commit()
        finally:
            conn.close()

        IntegrityLifecycleManager.create_preserved_snapshot(src, snap)
        disp_manifest = IntegrityLifecycleManager.create_disposable_copy(snap, disp)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            source_dir=src,
            snapshot_dir=snap,
            disposable_dir=disp,
            disposable_manifest=disp_manifest,
        )
        fake_emb = OfflineMiniLMEmbeddingFunction(is_synthetic=True)

        # 1. Internal TypeError propagation
        type_call_count = 0
        class FailingTypeClient:
            def get_collection(self, name, embedding_function=None):
                nonlocal type_call_count
                type_call_count += 1
                raise TypeError("Simulated collection internal TypeError")

        reader_type = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=lambda p: FailingTypeClient(),
            embedding_function=fake_emb,
        )
        self.assertIsNone(reader_type._collection)
        with self.assertRaises(TypeError) as ctx:
            reader_type.get_collection()
        self.assertIn("Simulated collection internal TypeError", str(ctx.exception))
        self.assertEqual(type_call_count, 1)
        self.assertIsNone(reader_type._collection)

        # 2. Internal ValueError propagation
        val_call_count = 0
        class FailingValClient:
            def get_collection(self, name, embedding_function=None):
                nonlocal val_call_count
                val_call_count += 1
                raise ValueError("Simulated collection internal ValueError")

        reader_val = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=lambda p: FailingValClient(),
            embedding_function=fake_emb,
        )
        self.assertIsNone(reader_val._collection)
        with self.assertRaises(ValueError) as ctx:
            reader_val.get_collection()
        self.assertIn("Simulated collection internal ValueError", str(ctx.exception))
        self.assertEqual(val_call_count, 1)
        self.assertIsNone(reader_val._collection)

    def test_chroma_disposable_reader_get_collection_incompatible_signature_fails_before_invocation(self):
        """
        Verify that an incompatible get_collection signature (lacking embedding_function)
        fails closed with ConfigurationError BEFORE invocation, leaving collection unset
        with zero invocations and zero fallback.
        """
        src = self.temp_dir / "src_coll_incompat_test"
        snap = self.temp_dir / "snap_coll_incompat_test"
        disp = self.temp_dir / "disp_coll_incompat_test"
        src.mkdir(parents=True)
        (src / "f.txt").write_bytes(b"content_data")

        db_path = src / "chroma.sqlite3"
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.cursor()
            cur.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT, dimension INTEGER)")
            cur.execute("INSERT INTO collections VALUES ('coll_1', 'thinking_traces', 384)")
            cur.execute("CREATE TABLE collection_metadata (collection_id TEXT, key TEXT, str_value TEXT)")
            cur.execute("INSERT INTO collection_metadata VALUES ('coll_1', 'hnsw:space', 'l2')")
            conn.commit()
        finally:
            conn.close()

        IntegrityLifecycleManager.create_preserved_snapshot(src, snap)
        disp_manifest = IntegrityLifecycleManager.create_disposable_copy(snap, disp)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            source_dir=src,
            snapshot_dir=snap,
            disposable_dir=disp,
            disposable_manifest=disp_manifest,
        )
        fake_emb = OfflineMiniLMEmbeddingFunction(is_synthetic=True)

        invocations = 0
        class IncompatibleClient:
            def get_collection(self, name):  # Only accepts 'name', cannot receive embedding_function
                nonlocal invocations
                invocations += 1
                return "incompatible_mock_collection"

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=lambda p: IncompatibleClient(),
            embedding_function=fake_emb,
        )
        self.assertIsNone(reader._collection)
        with self.assertRaises(ConfigurationError) as ctx:
            reader.get_collection()
        self.assertIn("does not accept mandatory 'embedding_function'", str(ctx.exception))
        # STRICT GUARANTEE: method was NEVER invoked!
        self.assertEqual(invocations, 0)
        self.assertIsNone(reader._collection)

    def test_chroma_disposable_reader_get_collection_receives_identical_verified_embedding_function(self):
        """
        Verify successful get_collection receives the identical verified embedding function object
        and returns the bound collection without error.
        """
        src = self.temp_dir / "src_coll_success_test"
        snap = self.temp_dir / "snap_coll_success_test"
        disp = self.temp_dir / "disp_coll_success_test"
        src.mkdir(parents=True)
        (src / "f.txt").write_bytes(b"content_data")

        db_path = src / "chroma.sqlite3"
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.cursor()
            cur.execute("CREATE TABLE collections (id TEXT PRIMARY KEY, name TEXT, dimension INTEGER)")
            cur.execute("INSERT INTO collections VALUES ('coll_1', 'thinking_traces', 384)")
            cur.execute("CREATE TABLE collection_metadata (collection_id TEXT, key TEXT, str_value TEXT)")
            cur.execute("INSERT INTO collection_metadata VALUES ('coll_1', 'hnsw:space', 'l2')")
            conn.commit()
        finally:
            conn.close()

        IntegrityLifecycleManager.create_preserved_snapshot(src, snap)
        disp_manifest = IntegrityLifecycleManager.create_disposable_copy(snap, disp)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            source_dir=src,
            snapshot_dir=snap,
            disposable_dir=disp,
            disposable_manifest=disp_manifest,
        )
        fake_emb = OfflineMiniLMEmbeddingFunction(is_synthetic=True)

        captured_calls = []
        class BoundClient:
            def get_collection(self, name, embedding_function=None):
                captured_calls.append({"name": name, "embedding_function": embedding_function})
                return "bound_collection_mock"

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=lambda p: BoundClient(),
            embedding_function=fake_emb,
        )
        coll = reader.get_collection()
        self.assertEqual(coll, "bound_collection_mock")
        self.assertEqual(len(captured_calls), 1)
        self.assertEqual(captured_calls[0]["name"], "thinking_traces")
        self.assertIs(captured_calls[0]["embedding_function"], fake_emb)
        self.assertIs(reader._collection, coll)

    def test_chroma_disposable_reader_get_collection_unrelated_second_parameter_fails_before_invocation(self):
        """
        Verify that a client.get_collection method with an unrelated second parameter
        (e.g., get_collection(name, unrelated_option=None)) fails closed with ConfigurationError
        BEFORE invocation, leaving collection unset with zero invocations and zero fallback.
        """
        src, snap, disp, receipt = self._create_synthetic_lifecycle_fixture("unrelated_param", with_sqlite=True)
        fake_emb = OfflineMiniLMEmbeddingFunction(is_synthetic=True)

        invocations = 0
        class UnrelatedOptionClient:
            def get_collection(self, name, unrelated_option=None):
                nonlocal invocations
                invocations += 1
                return "unrelated_mock_collection"

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=lambda p: UnrelatedOptionClient(),
            embedding_function=fake_emb,
        )
        self.assertIsNone(reader._collection)
        with self.assertRaises(ConfigurationError) as ctx:
            reader.get_collection()
        self.assertIn("does not accept mandatory 'embedding_function'", str(ctx.exception))
        self.assertEqual(invocations, 0)
        self.assertIsNone(reader._collection)

    def test_chroma_disposable_reader_get_collection_positional_only_embedding_function_fails_before_invocation(self):
        """
        Verify that a client.get_collection method with positional-only embedding_function
        (e.g., get_collection(name, embedding_function, /)) fails closed with ConfigurationError
        BEFORE invocation, leaving collection unset with zero invocations and zero fallback.
        """
        src, snap, disp, receipt = self._create_synthetic_lifecycle_fixture("pos_only_ef", with_sqlite=True)
        fake_emb = OfflineMiniLMEmbeddingFunction(is_synthetic=True)

        invocations = 0
        class PositionalOnlyClient:
            def get_collection(self, name, embedding_function, /):
                nonlocal invocations
                invocations += 1
                return "positional_only_mock_collection"

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=lambda p: PositionalOnlyClient(),
            embedding_function=fake_emb,
        )
        self.assertIsNone(reader._collection)
        with self.assertRaises(ConfigurationError) as ctx:
            reader.get_collection()
        self.assertIn("does not accept mandatory 'embedding_function'", str(ctx.exception))
        self.assertEqual(invocations, 0)
        self.assertIsNone(reader._collection)

    def test_chroma_disposable_reader_get_collection_incompatible_name_parameter_fails_before_invocation(self):
        """
        Verify that a client.get_collection method with an incompatible parameter name
        or positional-only name parameter fails closed with ConfigurationError BEFORE invocation,
        leaving collection unset with zero invocations and zero fallback.
        """
        src, snap, disp, receipt = self._create_synthetic_lifecycle_fixture("incompat_name", with_sqlite=True)
        fake_emb = OfflineMiniLMEmbeddingFunction(is_synthetic=True)

        # 1. Incompatible parameter name ('collection_id' instead of 'name')
        invocations_diff_name = 0
        class IncompatibleNameClient:
            def get_collection(self, collection_id, embedding_function=None):
                nonlocal invocations_diff_name
                invocations_diff_name += 1
                return "incompatible_name_mock_collection"

        reader_diff_name = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=disp,
            expected_source_dir=src,
            client_factory=lambda p: IncompatibleNameClient(),
            embedding_function=fake_emb,
        )
        self.assertIsNone(reader_diff_name._collection)
        with self.assertRaises(ConfigurationError) as ctx:
            reader_diff_name.get_collection()
        self.assertIn("does not accept mandatory 'embedding_function'", str(ctx.exception))
        self.assertEqual(invocations_diff_name, 0)
        self.assertIsNone(reader_diff_name._collection)

        # 2. Positional-only name parameter ('name, /')
        src_pos, snap_pos, disp_pos, receipt_pos = self._create_synthetic_lifecycle_fixture("pos_name", with_sqlite=True)
        invocations_pos_name = 0
        class PositionalOnlyNameClient:
            def get_collection(self, name, /, embedding_function=None):
                nonlocal invocations_pos_name
                invocations_pos_name += 1
                return "positional_name_mock_collection"

        reader_pos_name = ChromaDisposableReader(
            receipt=receipt_pos,
            disposable_dir=disp_pos,
            expected_source_dir=src_pos,
            client_factory=lambda p: PositionalOnlyNameClient(),
            embedding_function=fake_emb,
        )
        self.assertIsNone(reader_pos_name._collection)
        with self.assertRaises(ConfigurationError) as ctx:
            reader_pos_name.get_collection()
        self.assertIn("does not accept mandatory 'embedding_function'", str(ctx.exception))
        self.assertEqual(invocations_pos_name, 0)
        self.assertIsNone(reader_pos_name._collection)

    def test_launch_gate_sequencer_lifecycle(self):
        """Verify LaunchGateSequencer validates receipt and acquires single-use lock."""
        lock_path = self.temp_dir / "seq_test.lock"
        lock = SingleUseExecutionLock(lock_path)
        receipt = ExecutionAuthorizationReceipt(**self.valid_receipt_kwargs)
        sequencer = LaunchGateSequencer(
            receipt=receipt,
            lock=lock,
            expected_driver_sha256=self.valid_receipt_kwargs["driver_sha256"],
            expected_store_sqlite_sha256=self.valid_receipt_kwargs["store_sqlite_sha256"],
            expected_cache_manifest_sha256=self.valid_receipt_kwargs["cache_manifest_sha256"],
            expected_firewall_rule_id=self.valid_receipt_kwargs["firewall_rule_id"],
            expected_command=self.valid_receipt_kwargs["command"],
            expected_scope=self.valid_receipt_kwargs["scope"],
            expected_query_id=self.valid_receipt_kwargs["query_id"],
            expected_query_text_sha256=self.valid_receipt_kwargs["query_text_sha256"],
        )
        sequencer.validate_and_lock()
        self.assertTrue(lock.is_locked())

        # Second call fails with LockCollisionError
        with self.assertRaises(LockCollisionError):
            sequencer.validate_and_lock()

    def test_launch_gate_sequencer_wrong_command_fails_closed_lock_not_acquired(self):
        """Verify LaunchGateSequencer rejects wrong expected command and does NOT acquire lock."""
        lock_path = self.temp_dir / "wrong_cmd.lock"
        lock = SingleUseExecutionLock(lock_path)
        receipt = ExecutionAuthorizationReceipt(**self.valid_receipt_kwargs)
        sequencer = LaunchGateSequencer(
            receipt=receipt,
            lock=lock,
            expected_driver_sha256=self.valid_receipt_kwargs["driver_sha256"],
            expected_store_sqlite_sha256=self.valid_receipt_kwargs["store_sqlite_sha256"],
            expected_cache_manifest_sha256=self.valid_receipt_kwargs["cache_manifest_sha256"],
            expected_firewall_rule_id=self.valid_receipt_kwargs["firewall_rule_id"],
            expected_command="python -B scripts/matched_baseline/offline_preflight.py --eval-suite",
            expected_scope=self.valid_receipt_kwargs["scope"],
            expected_query_id=self.valid_receipt_kwargs["query_id"],
            expected_query_text_sha256=self.valid_receipt_kwargs["query_text_sha256"],
        )
        with self.assertRaises(ExecutionAuthorizationError) as ctx:
            sequencer.validate_and_lock()
        self.assertIn("command mismatch", str(ctx.exception).lower())
        self.assertFalse(lock.is_locked())
        self.assertFalse(lock_path.exists())

    def test_launch_gate_sequencer_reserved_metadata_override_fails_closed_lock_not_acquired(self):
        """Verify LaunchGateSequencer rejects reserved metadata keys and does NOT acquire lock."""
        lock_path = self.temp_dir / "meta_override.lock"
        lock = SingleUseExecutionLock(lock_path)
        receipt = ExecutionAuthorizationReceipt(**self.valid_receipt_kwargs)
        sequencer = LaunchGateSequencer(
            receipt=receipt,
            lock=lock,
            expected_driver_sha256=self.valid_receipt_kwargs["driver_sha256"],
            expected_store_sqlite_sha256=self.valid_receipt_kwargs["store_sqlite_sha256"],
            expected_cache_manifest_sha256=self.valid_receipt_kwargs["cache_manifest_sha256"],
            expected_firewall_rule_id=self.valid_receipt_kwargs["firewall_rule_id"],
            expected_command=self.valid_receipt_kwargs["command"],
            expected_scope=self.valid_receipt_kwargs["scope"],
            expected_query_id=self.valid_receipt_kwargs["query_id"],
            expected_query_text_sha256=self.valid_receipt_kwargs["query_text_sha256"],
        )
        for reserved_key in ("receipt_sha256", "scope", "query_id"):
            with self.assertRaises(ConfigurationError) as ctx:
                sequencer.validate_and_lock(metadata={reserved_key: "forged_value"})
            self.assertIn("cannot override reserved lock fields", str(ctx.exception))
            self.assertFalse(lock.is_locked())
            self.assertFalse(lock_path.exists())

    def test_offline_preflight_supervisor_supervised_process_success(self):
        """Verify supervisor runs child process command and records audit JSON on success."""
        src_dir = self.temp_dir / "sup_src"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()

        class MockProc:
            def __init__(self):
                self.killed = False
                self.exit_code = 0
            def poll(self):
                return 0
            def kill(self):
                self.killed = True

        mock_proc = MockProc()
        audit_dir = self.temp_dir / "audit"

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            audit_output_dir=audit_dir,
            process_runner=lambda cmd, env: mock_proc,
            clock_fn=lambda: 100.0,
        )
        res = sup.run_supervised_process(command=["echo", "test"])
        self.assertEqual(res["status"], "SUPERVISED_EXECUTION_SUCCESS")
        self.assertTrue(res["source_store_intact"])
        self.assertTrue(res["termination_confirmed"])
        self.assertTrue((audit_dir / "supervisor_audit.json").exists())

    def test_offline_preflight_supervisor_fake_kill_wait_ordering(self):
        """Verify supervisor calls .kill() before .wait(), and reaps child before outer file hashing."""
        src_dir = self.temp_dir / "sup_ordering_src"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()

        action_log = []

        class OrderedProc:
            def poll(self):
                return None
            def kill(self):
                action_log.append("kill")
            def wait(self, timeout=None):
                action_log.append("wait")
                return -9

        proc = OrderedProc()
        time_states = [100.0, 170.0, 170.0]
        def advancing_clock():
            if time_states:
                return time_states.pop(0)
            return 170.0

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            timeout_seconds=60.0,
            process_runner=lambda cmd, env: proc,
            clock_fn=advancing_clock,
        )
        # Instrument verify_source_integrity to log hashing step
        orig_verify = sup.verify_source_integrity
        def logged_verify():
            action_log.append("hash_check")
            return orig_verify()
        sup.verify_source_integrity = logged_verify

        with self.assertRaises(SupervisorExecutionError) as ctx:
            sup.run_supervised_process(command=["sleep", "100"])

        self.assertIn("timed out", str(ctx.exception).lower())
        self.assertEqual(action_log, ["kill", "wait", "hash_check"])

    def test_offline_preflight_supervisor_timeout_breach(self):
        """Verify supervisor kills and reaps child process on timeout breach."""
        src_dir = self.temp_dir / "sup_timeout_src"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()

        class HangingProc:
            def __init__(self):
                self.killed = False
                self.waited = False
            def poll(self):
                return -9 if self.killed else None
            def wait(self, timeout=None):
                self.waited = True
                return -9
            def kill(self):
                self.killed = True

        proc = HangingProc()
        time_states = [100.0, 170.0, 170.0]
        def advancing_clock():
            if time_states:
                return time_states.pop(0)
            return 170.0

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            timeout_seconds=60.0,
            process_runner=lambda cmd, env: proc,
            clock_fn=advancing_clock,
        )
        with self.assertRaises(SupervisorExecutionError) as ctx:
            sup.run_supervised_process(command=["sleep", "100"])
        self.assertTrue(proc.killed)
        self.assertTrue(proc.waited)
        self.assertIn("timed out", str(ctx.exception).lower())

    def test_offline_preflight_supervisor_memory_ceiling_breach(self):
        """Verify supervisor kills and reaps child process on memory ceiling breach."""
        src_dir = self.temp_dir / "sup_mem_src"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()

        class LeakingProc:
            def __init__(self):
                self.killed = False
                self.waited = False
            def poll(self):
                return -9 if self.killed else None
            def wait(self, timeout=None):
                self.waited = True
                return -9
            def kill(self):
                self.killed = True

        proc = LeakingProc()
        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            memory_ceiling_bytes=1000,
            process_runner=lambda cmd, env: proc,
            clock_fn=lambda: 100.0,
            memory_sampler=lambda p: 2000,
        )
        with self.assertRaises(SupervisorExecutionError) as ctx:
            sup.run_supervised_process(command=["leak_mem"])
        self.assertTrue(proc.killed)
        self.assertTrue(proc.waited)
        self.assertIn("memory ceiling", str(ctx.exception).lower())

    def test_offline_preflight_supervisor_memory_or_poll_exception_reaps_child(self):
        """Verify supervisor reaps child when memory_sampler or poll raises an exception."""
        src_dir = self.temp_dir / "sup_exc_src"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()
        audit_dir = self.temp_dir / "audit_exc"

        class LiveProc:
            def __init__(self):
                self.killed = False
                self.waited = False
            def poll(self):
                return None
            def kill(self):
                self.killed = True
            def wait(self, timeout=None):
                self.waited = True
                return -9

        proc = LiveProc()
        def bad_sampler(p):
            raise RuntimeError("Memory sampling driver crashed")

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            audit_output_dir=audit_dir,
            process_runner=lambda cmd, env: proc,
            clock_fn=lambda: 100.0,
            memory_sampler=bad_sampler,
        )
        with self.assertRaises(RuntimeError) as ctx:
            sup.run_supervised_process(command=["bad_proc"])
        self.assertIn("Memory sampling driver crashed", str(ctx.exception))
        self.assertTrue(proc.killed)
        self.assertTrue(proc.waited)
        self.assertTrue((audit_dir / "supervisor_audit.json").exists())

    def test_offline_preflight_supervisor_final_hash_read_failure_persists_evidence(self):
        """Verify supervisor catches file read exceptions per-input and still persists audit JSON."""
        src_dir = self.temp_dir / "sup_read_fail_src"
        src_dir.mkdir()
        sql_file = src_dir / "chroma.sqlite3"
        sql_file.write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()
        audit_dir = self.temp_dir / "audit_read_fail"

        class OkProc:
            def poll(self):
                return 0

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            audit_output_dir=audit_dir,
            process_runner=lambda cmd, env: OkProc(),
            clock_fn=lambda: 100.0,
        )

        orig_open = open
        def custom_open(file, *args, **kwargs):
            if "chroma.sqlite3" in str(file):
                raise OSError("Simulated hardware sector read error")
            return orig_open(file, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=custom_open):
            with self.assertRaises(IntegrityCheckError) as ctx:
                sup.run_supervised_process(command=["echo", "1"])
            self.assertIn("Simulated hardware sector read error", str(ctx.exception))

        audit_path = audit_dir / "supervisor_audit.json"
        self.assertTrue(audit_path.exists())
        with open(audit_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        self.assertFalse(data["source_store_intact"])
        self.assertIn("Simulated hardware sector read error", str(data["source_hash_errors"]))

    def test_offline_preflight_supervisor_unconfirmed_termination_fails_closed(self):
        """Verify supervisor fails closed if child process termination cannot be confirmed."""
        src_dir = self.temp_dir / "sup_unconfirmed_src"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()

        class UnkillableProc:
            def poll(self):
                return None
            def kill(self):
                pass
            def wait(self, timeout=None):
                raise TimeoutError("Process refused to terminate")

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            process_runner=lambda cmd, env: UnkillableProc(),
            clock_fn=lambda: 100.0,
            timeout_seconds=0.01,
        )
        time_states = [100.0, 170.0, 170.0]
        sup.clock_fn = lambda: time_states.pop(0) if time_states else 170.0

        with self.assertRaises(SupervisorExecutionError) as ctx:
            sup.run_supervised_process(command=["stubborn_proc"])
        self.assertIn("termination could not be confirmed", str(ctx.exception).lower())

    def test_offline_preflight_supervisor_hash_auditor_never_called_when_termination_unconfirmed(self):
        """Verify supervisor never calls verify_source_integrity if child termination is unconfirmed."""
        src_dir = self.temp_dir / "sup_unconfirmed_no_audit"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()
        audit_dir = self.temp_dir / "audit_unconfirmed"

        class UnkillableProc:
            def poll(self):
                return None
            def kill(self):
                pass
            def wait(self, timeout=None):
                raise TimeoutError("Refused to die")

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            audit_output_dir=audit_dir,
            process_runner=lambda cmd, env: UnkillableProc(),
            clock_fn=lambda: 100.0,
            timeout_seconds=0.01,
        )
        time_states = [100.0, 170.0, 170.0]
        sup.clock_fn = lambda: time_states.pop(0) if time_states else 170.0

        with mock.patch.object(sup, "verify_source_integrity", wraps=sup.verify_source_integrity) as mock_verify:
            with self.assertRaises(SupervisorExecutionError) as ctx:
                sup.run_supervised_process(command=["stubborn_proc"])
            self.assertIn("termination could not be confirmed", str(ctx.exception).lower())
            # STRICT SECURITY GUARANTEE: verify_source_integrity MUST NOT be called!
            mock_verify.assert_not_called()

        audit_path = audit_dir / "supervisor_audit.json"
        self.assertTrue(audit_path.exists())
        with open(audit_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        self.assertFalse(data["termination_confirmed"])
        self.assertFalse(data["source_store_intact"])
        self.assertEqual(data["source_integrity_status"], "NOT_VERIFIED")
        self.assertIn("NOT_VERIFIED", str(data["source_hash_errors"]))

    def test_offline_preflight_supervisor_polling_iteration_ceiling_terminates(self):
        """Verify supervisor enforces max_poll_iterations bound and reaps child on ceiling breach."""
        src_dir = self.temp_dir / "sup_poll_ceiling"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()

        killed = []
        class HangingProc:
            def poll(self):
                return None
            def kill(self):
                killed.append(True)
            def wait(self, timeout=None):
                return -9

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            process_runner=lambda cmd, env: HangingProc(),
            clock_fn=lambda: 100.0,
            max_poll_iterations=15,
        )

        with self.assertRaises(SupervisorExecutionError) as ctx:
            sup.run_supervised_process(command=["hang_cmd"])
        self.assertIn("exceeded maximum supervisor polling iterations", str(ctx.exception).lower())
        self.assertTrue(len(killed) > 0)

    def test_offline_preflight_supervisor_production_memory_sampler_required(self):
        """Verify supervisor requires memory sampler in production/authentic mode if ceiling is set."""
        src_dir = self.temp_dir / "sup_sampler_req"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()

        with self.assertRaises(ConfigurationError) as ctx:
            OfflinePreflightSupervisor(
                source_dir=src_dir,
                expected_sqlite_sha256=exp_sha,
                memory_ceiling_bytes=1000,
                is_synthetic=False,
                memory_sampler=None,
            )
        self.assertIn("mandatory production memory sampler", str(ctx.exception).lower())

    def test_offline_preflight_supervisor_child_failure_exit_code(self):
        """Verify supervisor fails closed on child process non-zero exit code."""
        src_dir = self.temp_dir / "sup_fail_src"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()

        class FailProc:
            def poll(self):
                return 42

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            process_runner=lambda cmd, env: FailProc(),
            clock_fn=lambda: 100.0,
        )
        with self.assertRaises(SupervisorExecutionError) as ctx:
            sup.run_supervised_process(command=["fail_cmd"])
        self.assertIn("exit code: 42", str(ctx.exception))

    def test_offline_preflight_supervisor_audit_log_collision_rejection(self):
        """Verify supervisor fails closed if audit file already exists."""
        src_dir = self.temp_dir / "sup_coll_src"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        exp_sha = hashlib.sha256(b"content").hexdigest()
        audit_dir = self.temp_dir / "audit_coll"
        audit_dir.mkdir()
        (audit_dir / "supervisor_audit.json").write_text("preexisting")

        class OkProc:
            def poll(self):
                return 0

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sha,
            audit_output_dir=audit_dir,
            process_runner=lambda cmd, env: OkProc(),
            clock_fn=lambda: 100.0,
        )
        with self.assertRaises(DestinationCollisionError) as ctx:
            sup.run_supervised_process(command=["echo", "1"])
        self.assertIn("already exists", str(ctx.exception).lower())

    def test_offline_preflight_supervisor_multi_asset_tamper_detection(self):
        """Verify supervisor outer finalizer detects store and cache tampering."""
        src_dir = self.temp_dir / "sup_multi_src"
        src_dir.mkdir()
        (src_dir / "chroma.sqlite3").write_bytes(b"content")
        (src_dir / "f1.bin").write_bytes(b"f1")
        cache_dir = self.temp_dir / "sup_cache"
        cache_dir.mkdir()
        (cache_dir / "c1.bin").write_bytes(b"c1")

        exp_sqlite = hashlib.sha256(b"content").hexdigest()
        exp_inv = {"chroma.sqlite3": exp_sqlite, "f1.bin": hashlib.sha256(b"f1").hexdigest()}
        exp_cache = {"c1.bin": hashlib.sha256(b"c1").hexdigest()}

        sup = OfflinePreflightSupervisor(
            source_dir=src_dir,
            expected_sqlite_sha256=exp_sqlite,
            expected_store_inventory=exp_inv,
            expected_cache_dir=cache_dir,
            expected_cache_pins=exp_cache,
        )
        is_intact, _ = sup.verify_source_integrity()
        self.assertTrue(is_intact)

        # Tamper store file
        (src_dir / "f1.bin").write_bytes(b"tampered")
        is_intact, _ = sup.verify_source_integrity()
        self.assertFalse(is_intact)
        (src_dir / "f1.bin").write_bytes(b"f1")

        # Tamper cache file
        (cache_dir / "c1.bin").write_bytes(b"tampered")
        is_intact, _ = sup.verify_source_integrity()
        self.assertFalse(is_intact)

    def test_offline_preflight_supervisor_outer_finalizer_success(self):
        """Verify supervisor runs child function and outer finalizer validates intact source store."""
        src_dir = self.temp_dir / "src_sup"
        src_dir.mkdir(parents=True)
        sql_file = src_dir / "chroma.sqlite3"
        sql_file.write_bytes(b"initial_sqlite_content")
        expected_sha = hashlib.sha256(b"initial_sqlite_content").hexdigest()

        sup = OfflinePreflightSupervisor(source_dir=src_dir, expected_sqlite_sha256=expected_sha)
        res = sup.run_supervised(child_fn=lambda: "child_output_ok")
        self.assertEqual(res["status"], "SUPERVISED_EXECUTION_SUCCESS")
        self.assertEqual(res["result"], "child_output_ok")
        self.assertTrue(res["source_store_intact"])

    def test_offline_preflight_supervisor_outer_finalizer_detects_tamper(self):
        """Verify supervisor outer finalizer detects store modification and raises IntegrityCheckError."""
        src_dir = self.temp_dir / "src_tamper"
        src_dir.mkdir(parents=True)
        sql_file = src_dir / "chroma.sqlite3"
        sql_file.write_bytes(b"initial_sqlite_content")
        expected_sha = hashlib.sha256(b"initial_sqlite_content").hexdigest()

        def tampering_child():
            sql_file.write_bytes(b"tampered_bytes_in_source")
            return "tampered"

        sup = OfflinePreflightSupervisor(source_dir=src_dir, expected_sqlite_sha256=expected_sha)
        with self.assertRaises(IntegrityCheckError) as ctx:
            sup.run_supervised(child_fn=tampering_child)
        self.assertIn("SUPERVISOR OUTER FINALIZER ALERT", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()


