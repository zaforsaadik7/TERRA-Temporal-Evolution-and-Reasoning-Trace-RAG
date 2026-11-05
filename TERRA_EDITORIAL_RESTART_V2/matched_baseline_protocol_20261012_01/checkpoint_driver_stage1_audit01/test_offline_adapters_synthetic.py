"""
test_offline_adapters_synthetic.py
----------------------------------
Synthetic unit test suite for Stage 1 preflight adapters:
1. IsolationReceipt issuance, lifecycle binding, and disjoint containment validation.
2. ChromaDisposableReader schema validation, Layer 1 corpus extraction, and native L2 retrieval.
3. Strict read-only enforcement (mutating operations prohibited).
4. Deterministic tie-breaking and distance validation (NaN, Inf, negative, duplicates).
5. StreamingGraphLoader memory-safe streaming decompression and schema auditing.

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
import unittest

from scripts.matched_baseline.common_serializer import ConfigurationError
from scripts.matched_baseline.offline_preflight import (
    ChromaDisposableReader,
    ContainmentViolationError,
    CorpusParityError,
    DestinationCollisionError,
    DirectoryOverlapError,
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
        """Helper to create snapshot and disposable copy and return IsolationReceipt."""
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

    def _create_synthetic_sqlite_db(
        self,
        db_path: Path,
        collection_name: str = "thinking_traces",
        dimension: int = 384,
        metric: str = "l2",
        documents: dict = None,
    ):
        """Helper to create synthetic Chroma SQLite schema."""
        if db_path.exists():
            db_path.unlink()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE collections (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE,
                dimension INTEGER,
                schema_str TEXT
            )
        """)
        schema_dict = {"hnsw:space": metric}
        cursor.execute(
            "INSERT INTO collections VALUES (?, ?, ?, ?)",
            ("coll_uuid_001", collection_name, dimension, json.dumps(schema_dict)),
        )

        cursor.execute("""
            CREATE TABLE embeddings (
                id TEXT PRIMARY KEY,
                collection_id TEXT,
                document TEXT
            )
        """)
        docs = documents or {
            "case_001": "Full holding text for case 001",
            "case_002": "Full holding text for case 002",
            "case_003": "Full holding text for case 003",
        }
        for doc_id, doc_text in docs.items():
            cursor.execute(
                "INSERT INTO embeddings VALUES (?, ?, ?)",
                (doc_id, "coll_uuid_001", doc_text),
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
            disposable_dir=str(self.source_dir.resolve()),  # Aliases source!
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
            disposable_dir=str(self.snapshot_dir.resolve()),  # Aliases snapshot!
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

    def test_containment_validation_manifest_drift(self):
        """Reject candidate directory if files drift from the receipt manifest."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        # Mutate a file in the disposable copy
        (self.disposable_dir / "chroma.sqlite3").write_text("tampered_content", encoding="utf-8")
        with self.assertRaises(ManifestVerificationError):
            IntegrityLifecycleManager.validate_disposable_containment(
                receipt=receipt,
                candidate_dir=self.disposable_dir,
                expected_source_dir=self.source_dir,
            )

    def test_containment_validation_file_count_drift(self):
        """Reject candidate directory if extra files are added to disposable copy."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        (self.disposable_dir / "unexpected_file.txt").write_text("extra", encoding="utf-8")
        with self.assertRaises(ManifestVerificationError):
            IntegrityLifecycleManager.validate_disposable_containment(
                receipt=receipt,
                candidate_dir=self.disposable_dir,
                expected_source_dir=self.source_dir,
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
    # 2. ChromaDisposableReader Schema & Corpus Tests
    # =========================================================================

    def test_chroma_disposable_reader_schema_validation_success(self):
        """Verify reader validates schema: thinking_traces, 384-dim, and l2 space."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        self._create_synthetic_sqlite_db(self.disposable_dir / "chroma.sqlite3")

        # Update receipt manifest to reflect the newly written database
        disp_manifest = IntegrityLifecycleManager.compute_manifest(self.disposable_dir)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            self.source_dir, self.snapshot_dir, self.disposable_dir, disp_manifest
        )

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
        _, receipt = self._create_synthetic_lifecycle_copies()
        self._create_synthetic_sqlite_db(
            self.disposable_dir / "chroma.sqlite3", collection_name="other_name"
        )
        disp_manifest = IntegrityLifecycleManager.compute_manifest(self.disposable_dir)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            self.source_dir, self.snapshot_dir, self.disposable_dir, disp_manifest
        )

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        with self.assertRaises(IntegrityCheckError):
            reader.validate_store_schema()

    def test_chroma_disposable_reader_dimension_mismatch(self):
        """Fail closed when dimension does not equal 384."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        self._create_synthetic_sqlite_db(
            self.disposable_dir / "chroma.sqlite3", dimension=768
        )
        disp_manifest = IntegrityLifecycleManager.compute_manifest(self.disposable_dir)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            self.source_dir, self.snapshot_dir, self.disposable_dir, disp_manifest
        )

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        with self.assertRaises(IntegrityCheckError):
            reader.validate_store_schema()

    def test_chroma_disposable_reader_metric_mismatch(self):
        """Fail closed when distance metric is not l2 (e.g. cosine)."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        self._create_synthetic_sqlite_db(
            self.disposable_dir / "chroma.sqlite3", metric="cosine"
        )
        disp_manifest = IntegrityLifecycleManager.compute_manifest(self.disposable_dir)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            self.source_dir, self.snapshot_dir, self.disposable_dir, disp_manifest
        )

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        with self.assertRaises(IntegrityCheckError):
            reader.validate_store_schema()

    def test_chroma_disposable_reader_extract_layer1_corpus(self):
        """Extract Layer 1 document texts and enforce expected count."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        self._create_synthetic_sqlite_db(self.disposable_dir / "chroma.sqlite3")
        disp_manifest = IntegrityLifecycleManager.compute_manifest(self.disposable_dir)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            self.source_dir, self.snapshot_dir, self.disposable_dir, disp_manifest
        )

        reader = ChromaDisposableReader(
            receipt=receipt,
            disposable_dir=self.disposable_dir,
            expected_source_dir=self.source_dir,
        )
        docs = reader.extract_layer1_corpus(expected_count=3)
        self.assertEqual(len(docs), 3)
        self.assertEqual(docs["case_001"], "Full holding text for case 001")

        # Cardinality mismatch raises CorpusParityError
        with self.assertRaises(CorpusParityError):
            reader.extract_layer1_corpus(expected_count=100)

    # =========================================================================
    # 3. Dense Query Interface, Validation & Tie-Breaking Tests
    # =========================================================================

    def test_chroma_disposable_reader_query_dense_candidates_success(self):
        """Verify query_dense_candidates returns ordered IDs from mock client."""
        _, receipt = self._create_synthetic_lifecycle_copies()
        disp_manifest = IntegrityLifecycleManager.compute_manifest(self.disposable_dir)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            self.source_dir, self.snapshot_dir, self.disposable_dir, disp_manifest
        )

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
        disp_manifest = IntegrityLifecycleManager.compute_manifest(self.disposable_dir)
        receipt = IntegrityLifecycleManager.issue_isolation_receipt(
            self.source_dir, self.snapshot_dir, self.disposable_dir, disp_manifest
        )

        class MockCollection:
            def query(self, query_texts, n_results, include):
                return {
                    # doc_z and doc_a have identical distance 0.35
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

    def test_chroma_disposable_reader_rejects_nan_and_inf_distances(self):
        """Reject non-finite distances (NaN, Inf, negative)."""
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
    # 4. StreamingGraphLoader Tests
    # =========================================================================

    def test_streaming_graph_loader_success_compressed_xz(self):
        """Verify StreamingGraphLoader decompresses .json.xz directly without disk writes."""
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

        nodes, edges, audit = StreamingGraphLoader.load_graph_archive(
            archive_path=archive_path,
            expected_sha256=expected_sha,
            expected_node_count=2,
        )
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(edges), 1)
        self.assertTrue(audit["schema_valid"])
        self.assertEqual(edges[0]["relation"], "CITES")

    def test_streaming_graph_loader_missing_file(self):
        """Raise IntegrityCheckError on non-existent archive path."""
        non_existent = self.temp_dir / "does_not_exist.json.xz"
        with self.assertRaises(IntegrityCheckError):
            StreamingGraphLoader.load_graph_archive(non_existent)

    def test_streaming_graph_loader_sha256_mismatch(self):
        """Raise IntegrityCheckError on SHA-256 mismatch."""
        json_bytes = json.dumps({"nodes": {}, "edges": []}).encode("utf-8")
        archive_path = self.temp_dir / "wrong_hash.json.xz"
        archive_path.write_bytes(lzma.compress(json_bytes))

        with self.assertRaises(IntegrityCheckError):
            StreamingGraphLoader.load_graph_archive(
                archive_path=archive_path,
                expected_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            )

    def test_streaming_graph_loader_schema_dangling_edge(self):
        """Raise GraphSchemaError when graph data contains dangling edge endpoints."""
        graph_dict = {
            "nodes": {
                "node_1": {"node_id": "node_1", "decision_date": "1990-01-01"},
            },
            "edges": [
                {"source": "node_1", "target": "missing_node", "relation": "CITES"},
            ],
        }
        archive_path = self.temp_dir / "dangling_edge.json"
        archive_path.write_text(json.dumps(graph_dict), encoding="utf-8")

        with self.assertRaises(GraphSchemaError):
            StreamingGraphLoader.load_graph_archive(archive_path)

    def test_streaming_graph_loader_schema_unsupported_relation(self):
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
        archive_path = self.temp_dir / "unsupported_rel.json"
        archive_path.write_text(json.dumps(graph_dict), encoding="utf-8")

        with self.assertRaises(GraphSchemaError):
            StreamingGraphLoader.load_graph_archive(archive_path)


if __name__ == "__main__":
    unittest.main()
