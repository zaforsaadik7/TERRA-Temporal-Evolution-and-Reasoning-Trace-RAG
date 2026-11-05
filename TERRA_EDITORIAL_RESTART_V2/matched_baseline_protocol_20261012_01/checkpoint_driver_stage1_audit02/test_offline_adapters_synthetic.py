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

import json
import lzma
import math
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from typing import Optional
import unittest

from scripts.matched_baseline.common_serializer import ConfigurationError
from scripts.matched_baseline.offline_preflight import (
    BoundedMemoryGraphLoader,
    BudgetExceededError,
    ChromaDisposableReader,
    ConfigurationBlockedError,
    ContainmentViolationError,
    CorpusParityError,
    DestinationCollisionError,
    DirectoryOverlapError,
    GraphSchemaAuditor,
    GraphSchemaError,
    IntegrityCheckError,
    IntegrityLifecycleManager,
    IsolationReceipt,
    ManifestVerificationError,
    ReadOnlyViolationError,
    StreamingGraphLoader,
    SymlinkContainmentError,
)


class TestOfflineAdaptersSynthetic(unittest.TestCase):
    """Synthetic unit tests for Stage 1 offline preflight adapters."""

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


if __name__ == "__main__":
    unittest.main()
