"""
test_master_launch_ledger_synthetic.py
---------------------------------------
Synthetic unit test suite for MasterLaunchLedgerGenerator safeguards:
- Rejects tampered manifest pins.
- Rejects tampered canonical data pins.
- Rejects failed/altered saved inventory (exit_code != 0, errors present, before/after drift).
- Rejects output destination collision (exclusive directory and file creation).
- Verifies exact JSON and CSV consistency on successful generation in isolated fixtures.
"""

import csv
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from reports.generate_master_launch_ledger import (
    CanonicalPinMismatchError,
    DestinationCollisionError,
    InventoryVerificationError,
    ManifestPinMismatchError,
    MasterLaunchLedgerGenerator,
)


class TestMasterLaunchLedgerGeneratorSynthetic(unittest.TestCase):
    """Synthetic unit tests for MasterLaunchLedgerGenerator."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="ledger_test_")
        self.ws_dir = Path(self.temp_dir) / "workspace"
        self.ws_dir.mkdir(parents=True, exist_ok=True)

        self.reports_dir = self.ws_dir / "reports"
        self.inv_dir = self.reports_dir / "read_only_inventory_fake"
        self.inv_dir.mkdir(parents=True, exist_ok=True)
        self.inv_json = self.inv_dir / "inventory.json"
        self.exit_code_txt = self.inv_dir / "exit_code.txt"
        self.output_dir = self.reports_dir / "test_output_ledger"

        # Create minimal synthetic valid inventory.json and exit_code.txt
        self.exit_code_txt.write_text("0", encoding="utf-8")
        self.fake_inventory = {
            "exit_code": 0,
            "outcome": "STABLE_FILESYSTEM_INVENTORY",
            "errors": [],
            "before": {
                "store": {
                    "root": str(self.ws_dir / "dataset_20k_cap" / "vector_db_20k"),
                    "files": [
                        {
                            "relative_path": "chroma.sqlite3",
                            "absolute_path": str(self.ws_dir / "dataset_20k_cap" / "vector_db_20k" / "chroma.sqlite3"),
                            "size_bytes": 1024,
                            "sha256": "aaaa1111222233334444555566667777888899990000aaaabbbbccccddddeeee",
                        }
                    ]
                },
                "cache": {
                    "root": str(self.ws_dir / "cache_models"),
                    "files": [
                        {
                            "relative_path": "onnx/model.onnx",
                            "absolute_path": str(self.ws_dir / "cache_models" / "onnx" / "model.onnx"),
                            "size_bytes": 2048,
                            "sha256": "bbbb1111222233334444555566667777888899990000aaaabbbbccccddddeeee",
                        }
                    ]
                }
            },
            "after": {}
        }
        self.fake_inventory["after"] = json.loads(json.dumps(self.fake_inventory["before"]))
        with open(self.inv_json, "w", encoding="utf-8") as fp:
            json.dump(self.fake_inventory, fp, indent=2)

        # Build mock tokenizer assets & manifests
        tok_dir = self.ws_dir / "assets" / "tokenizers"
        tok_dir.mkdir(parents=True, exist_ok=True)

        pub_man = tok_dir / "tokenizer_manifest.sha256"
        gated_man = tok_dir / "gated_tokenizer_manifest.v1.sha256"

        self.tok_files = {
            "assets/tokenizers/generator/tokenizer.json": "content_generator_tok",
            "assets/tokenizers/generator/tokenizer_config.json": "content_generator_cfg",
            "assets/tokenizers/generator/special_tokens_map.json": "content_generator_tokens",
            "assets/tokenizers/router/tokenizer.json": "content_router_tok",
            "assets/tokenizers/router/tokenizer_config.json": "content_router_cfg",
            "assets/tokenizers/router/special_tokens_map.json": "content_router_tokens",
            "assets/tokenizers/router/chat_template.json": "content_router_chat",
            "assets/tokenizers/judge1/tokenizer.json": "content_judge1_tok",
            "assets/tokenizers/judge1/tokenizer_config.json": "content_judge1_cfg",
            "assets/tokenizers/judge1/vocab.json": "content_judge1_vocab",
            "assets/tokenizers/judge1/merges.txt": "content_judge1_merges",
            "assets/tokenizers/judge2/tokenizer.json": "content_judge2_tok",
            "assets/tokenizers/judge2/tokenizer_config.json": "content_judge2_cfg",
            "assets/tokenizers/judge2/special_tokens_map.json": "content_judge2_tokens",
            "assets/tokenizers/judge2/chat_template.jinja": "content_judge2_jinja",
        }

        self.hashes = {}
        for rel_p, content in self.tok_files.items():
            f_p = self.ws_dir / rel_p
            f_p.parent.mkdir(parents=True, exist_ok=True)
            f_p.write_text(content, encoding="utf-8")
            h = hashlib.sha256(content.encode("utf-8")).hexdigest()
            self.hashes[rel_p] = h

        # Write manifest entries
        pub_lines = []
        gated_lines = []
        for rel_p, h in self.hashes.items():
            if "judge" in rel_p:
                pub_lines.append(f"{h}  {rel_p}")
            else:
                gated_lines.append(f"{h}  {rel_p}")

        pub_man.write_text("\n".join(pub_lines) + "\n", encoding="utf-8")
        gated_man.write_text("\n".join(gated_lines) + "\n", encoding="utf-8")

        # Canonical data files
        self.data_files = {
            "terra_350_benchmark.json": "benchmark_cohort_350_synthetic",
            "TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz": "graph_xz_content",
            "TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.provenance.json": "graph_prov_content",
            "TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/manifest.sha256": "graph_man_content",
        }
        for rel_p, content in self.data_files.items():
            p = self.ws_dir / rel_p
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            h = hashlib.sha256(content.encode("utf-8")).hexdigest()
            self.hashes[rel_p] = h

        # Codebase modules
        self.code_files = [
            "scripts/matched_baseline/fast_tokenizer_adapter.py",
            "scripts/matched_baseline/offline_preflight.py",
            "scripts/matched_baseline/common_serializer.py",
            "scripts/matched_baseline/bm25_engine.py",
            "scripts/matched_baseline/hybrid_retriever.py",
            "scripts/matched_baseline/terra_retriever.py",
            "venv/Scripts/python.exe",
        ]
        for rel_p in self.code_files:
            p = self.ws_dir / rel_p
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("code_module_placeholder", encoding="utf-8")
            h = hashlib.sha256(b"code_module_placeholder").hexdigest()
            self.hashes[rel_p] = h

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_generator(self, **kwargs):
        output_dir = kwargs.get("output_dir", self.output_dir)
        driver_sha = kwargs.get("expected_driver_sha256", self.hashes.get("scripts/matched_baseline/offline_preflight.py"))
        gen = MasterLaunchLedgerGenerator(
            workspace_root=self.ws_dir,
            saved_inventory_path=self.inv_json,
            output_dir=output_dir,
            expected_inventory_sha256=kwargs.get("expected_inv_sha", None),
            expected_driver_sha256=driver_sha,
            prospective_decision_path=kwargs.get("prospective_decision_path", None),
            expected_prospective_decision_sha256=kwargs.get("expected_prospective_decision_sha256", None),
            enforce_exclusive_destination=kwargs.get("enforce_exclusive", True),
        )
        # Patch generator expected constants to match synthetic hashes
        gen.EXPECTED_PUBLIC_TOKENIZER_MANIFEST_SHA256 = MasterLaunchLedgerGenerator.hash_file(
            self.ws_dir / "assets" / "tokenizers" / "tokenizer_manifest.sha256"
        )
        gen.EXPECTED_GATED_TOKENIZER_MANIFEST_SHA256 = MasterLaunchLedgerGenerator.hash_file(
            self.ws_dir / "assets" / "tokenizers" / "gated_tokenizer_manifest.v1.sha256"
        )
        gen.EXPECTED_BENCHMARK_350_SHA256 = self.hashes["terra_350_benchmark.json"]
        gen.EXPECTED_CANONICAL_GRAPH_SHA256 = self.hashes["TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz"]
        gen.EXPECTED_GRAPH_PROVENANCE_SHA256 = self.hashes["TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.provenance.json"]
        gen.EXPECTED_GRAPH_MANIFEST_SHA256 = self.hashes["TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/manifest.sha256"]
        gen.EXPECTED_OFFLINE_PREFLIGHT_SHA256 = self.hashes["scripts/matched_baseline/offline_preflight.py"]
        return gen

    def test_generator_succeeds_and_creates_consistent_json_csv(self):
        """Verify generator succeeds and outputs 100% consistent JSON and CSV records."""
        gen = self._create_generator()
        res = gen.generate()

        self.assertTrue((self.output_dir / "launch_inventory.json").exists())
        self.assertTrue((self.output_dir / "launch_inventory.csv").exists())
        self.assertTrue((self.output_dir / "manifest.sha256").exists())

        # Load and verify JSON
        with open(self.output_dir / "launch_inventory.json", "r", encoding="utf-8") as fp:
            j_data = json.load(fp)

        # Load and verify CSV
        with open(self.output_dir / "launch_inventory.csv", "r", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            c_rows = list(reader)

        self.assertEqual(len(j_data["entries"]), len(c_rows))
        self.assertEqual(res["total_files"], len(c_rows))

        # Check field-by-field consistency
        for j_entry, c_entry in zip(j_data["entries"], c_rows):
            self.assertEqual(j_entry["category"], c_entry["category"])
            self.assertEqual(j_entry["role"], c_entry["role"])
            self.assertEqual(j_entry["relative_path"], c_entry["relative_path"])
            self.assertEqual(j_entry["absolute_path"], c_entry["absolute_path"])
            self.assertEqual(str(j_entry["size_bytes"]), c_entry["size_bytes"])
            self.assertEqual(j_entry["sha256"], c_entry["sha256"])
            self.assertEqual(j_entry["evidence_type"], c_entry["evidence_type"])
            self.assertEqual(j_entry["evidence_source"], c_entry["evidence_source"])
            self.assertEqual(j_entry["verification_status"], c_entry["verification_status"])

    def test_generator_rejects_existing_output_collision(self):
        """Verify generator refuses to overwrite existing destination files."""
        gen = self._create_generator()
        gen.generate()

        # Attempt to run second generator targeting same output dir
        gen2 = self._create_generator()
        with self.assertRaises(DestinationCollisionError) as ctx:
            gen2.generate()
        self.assertIn("already exists and contains", str(ctx.exception))

    def test_generator_rejects_tampered_saved_inventory_exit_code(self):
        """Verify generator fails closed if saved inventory exit_code is non-zero."""
        self.exit_code_txt.write_text("1", encoding="utf-8")
        gen = self._create_generator()
        with self.assertRaises(InventoryVerificationError) as ctx:
            gen.generate()
        self.assertIn("non-zero", str(ctx.exception).lower())

    def test_generator_rejects_saved_inventory_drift(self):
        """Verify generator fails closed if saved inventory before != after."""
        with open(self.inv_json, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        data["after"]["store"]["files"][0]["sha256"] = "different_drift_hash"
        with open(self.inv_json, "w", encoding="utf-8") as fp:
            json.dump(data, fp)

        gen = self._create_generator()
        with self.assertRaises(InventoryVerificationError) as ctx:
            gen.generate()
        self.assertIn("drift detected", str(ctx.exception).lower())

    def test_generator_rejects_saved_inventory_checksum_mismatch(self):
        """Verify generator fails closed if saved inventory file itself was modified."""
        gen = self._create_generator(expected_inv_sha="0000000000000000000000000000000000000000000000000000000000000000")
        with self.assertRaises(InventoryVerificationError) as ctx:
            gen.generate()
        self.assertIn("sha-256 mismatch", str(ctx.exception).lower())

    def test_generator_rejects_tampered_tokenizer_manifest_pin(self):
        """Verify generator detects tampered tokenizer file not matching manifest."""
        # Tamper router tokenizer.json
        router_p = self.ws_dir / "assets" / "tokenizers" / "router" / "tokenizer.json"
        router_p.write_text("tampered_content_injection", encoding="utf-8")

        gen = self._create_generator()
        with self.assertRaises(ManifestPinMismatchError) as ctx:
            gen.generate()
        self.assertIn("tokenizer pin mismatch", str(ctx.exception).lower())

    def test_generator_rejects_tampered_canonical_data_pin(self):
        """Verify generator detects tampered canonical benchmark data."""
        bench_p = self.ws_dir / "terra_350_benchmark.json"
        bench_p.write_text("tampered_benchmark_content", encoding="utf-8")

        gen = self._create_generator()
        with self.assertRaises(CanonicalPinMismatchError) as ctx:
            gen.generate()
        self.assertIn("canonical data pin mismatch", str(ctx.exception).lower())

    def test_generator_rejects_file_level_write_collision(self):
        """Verify generator fails closed if individual output file exists when checking directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "launch_inventory.json").write_text("preexisting", encoding="utf-8")

        gen = self._create_generator()
        with self.assertRaises(DestinationCollisionError) as ctx:
            gen.generate()
        self.assertIn("already exists and contains", str(ctx.exception))

    def test_cli_main_success_and_collision_failure(self):
        """Verify main() CLI entrypoint exits 0 on success and 1 on collision."""
        import sys
        from unittest.mock import patch
        from reports.generate_master_launch_ledger import main, MasterLaunchLedgerGenerator

        inv_sha = MasterLaunchLedgerGenerator.hash_file(self.inv_json)
        out_cli = self.reports_dir / "cli_test_out"
        test_args = [
            "generate_master_launch_ledger.py",
            "--workspace-root", str(self.ws_dir),
            "--saved-inventory", str(self.inv_json),
            "--output-dir", str(out_cli),
            "--expected-inventory-sha", inv_sha,
        ]

        # Patch class-level expected constants to match synthetic fixtures
        with patch.object(MasterLaunchLedgerGenerator, "EXPECTED_PUBLIC_TOKENIZER_MANIFEST_SHA256", MasterLaunchLedgerGenerator.hash_file(self.ws_dir / "assets" / "tokenizers" / "tokenizer_manifest.sha256")), \
             patch.object(MasterLaunchLedgerGenerator, "EXPECTED_GATED_TOKENIZER_MANIFEST_SHA256", MasterLaunchLedgerGenerator.hash_file(self.ws_dir / "assets" / "tokenizers" / "gated_tokenizer_manifest.v1.sha256")), \
             patch.object(MasterLaunchLedgerGenerator, "EXPECTED_BENCHMARK_350_SHA256", self.hashes["terra_350_benchmark.json"]), \
             patch.object(MasterLaunchLedgerGenerator, "EXPECTED_CANONICAL_GRAPH_SHA256", self.hashes["TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz"]), \
             patch.object(MasterLaunchLedgerGenerator, "EXPECTED_GRAPH_PROVENANCE_SHA256", self.hashes["TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.provenance.json"]), \
             patch.object(MasterLaunchLedgerGenerator, "EXPECTED_GRAPH_MANIFEST_SHA256", self.hashes["TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/manifest.sha256"]), \
             patch.object(MasterLaunchLedgerGenerator, "EXPECTED_OFFLINE_PREFLIGHT_SHA256", self.hashes["scripts/matched_baseline/offline_preflight.py"]), \
             patch.object(sys, "argv", test_args):

            exit_code = main()
            self.assertEqual(exit_code, 0)
            self.assertTrue((out_cli / "launch_inventory.json").exists())
            self.assertTrue((out_cli / "launch_inventory.csv").exists())

            # Calling again without changing output dir must return 1 due to collision
            exit_code_coll = main()
            self.assertEqual(exit_code_coll, 1)

    def test_prospective_mode_validation_success(self):
        """Verify generator validates prospective decision record and inventory SQLite hash."""
        from unittest.mock import patch

        sql_sha = "aaaa1111222233334444555566667777888899990000aaaabbbbccccddddeeee"
        decision_doc = {
            "checkpoint_id": "TEST_PROSPECTIVE_20261015",
            "status": "ACCEPTED_PROSPECTIVE_INPUT_CHECKPOINT",
            "accepted_sqlite_sha256": sql_sha,
            "accepted_sqlite_size_bytes": 1024,
        }
        dec_path = self.reports_dir / "test_prospective_decision.json"
        with open(dec_path, "w", encoding="utf-8") as fp:
            json.dump(decision_doc, fp, indent=2)

        dec_sha = MasterLaunchLedgerGenerator.hash_file(dec_path)

        with patch.object(MasterLaunchLedgerGenerator, "EXPECTED_ACCEPTED_SQLITE_SHA256", sql_sha), \
             patch.object(MasterLaunchLedgerGenerator, "EXPECTED_PROSPECTIVE_DECISION_SHA256", dec_sha):
            gen = self._create_generator(
                prospective_decision_path=dec_path,
                expected_prospective_decision_sha256=dec_sha,
            )
            res = gen.generate()
            self.assertEqual(res["total_files"], 30)

    def test_prospective_mode_rejects_tampered_decision_hash(self):
        """Verify generator rejects prospective decision record with mismatched sha256."""
        dec_path = self.reports_dir / "test_prospective_tampered.json"
        dec_path.write_text("{\"status\": \"ACCEPTED_PROSPECTIVE_INPUT_CHECKPOINT\"}", encoding="utf-8")

        gen = self._create_generator(
            prospective_decision_path=dec_path,
            expected_prospective_decision_sha256="0000000000000000000000000000000000000000000000000000000000000000",
        )
        with self.assertRaises(InventoryVerificationError) as ctx:
            gen.generate()
        self.assertIn("prospective decision sha-256 mismatch", str(ctx.exception).lower())

    def test_prospective_mode_rejects_invalid_decision_status(self):
        """Verify generator rejects prospective decision record with wrong status."""
        from unittest.mock import patch

        sql_sha = "aaaa1111222233334444555566667777888899990000aaaabbbbccccddddeeee"
        decision_doc = {
            "status": "REJECTED_OR_UNKNOWN",
            "accepted_sqlite_sha256": sql_sha,
        }
        dec_path = self.reports_dir / "test_prospective_bad_status.json"
        with open(dec_path, "w", encoding="utf-8") as fp:
            json.dump(decision_doc, fp, indent=2)

        dec_sha = MasterLaunchLedgerGenerator.hash_file(dec_path)
        with patch.object(MasterLaunchLedgerGenerator, "EXPECTED_PROSPECTIVE_DECISION_SHA256", dec_sha):
            gen = self._create_generator(
                prospective_decision_path=dec_path,
                expected_prospective_decision_sha256=dec_sha,
            )
            with self.assertRaises(InventoryVerificationError) as ctx:
                gen.generate()
            self.assertIn("invalid prospective decision status", str(ctx.exception).lower())

    def test_prospective_mode_rejects_sqlite_hash_mismatch(self):
        """Verify generator rejects inventory if chroma.sqlite3 hash does not match accepted sqlite hash."""
        from unittest.mock import patch

        decision_doc = {
            "status": "ACCEPTED_PROSPECTIVE_INPUT_CHECKPOINT",
            "accepted_sqlite_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        }
        dec_path = self.reports_dir / "test_prospective_mismatch_sql.json"
        with open(dec_path, "w", encoding="utf-8") as fp:
            json.dump(decision_doc, fp, indent=2)

        dec_sha = MasterLaunchLedgerGenerator.hash_file(dec_path)
        with patch.object(MasterLaunchLedgerGenerator, "EXPECTED_ACCEPTED_SQLITE_SHA256", "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"), \
             patch.object(MasterLaunchLedgerGenerator, "EXPECTED_PROSPECTIVE_DECISION_SHA256", dec_sha):
            gen = self._create_generator(
                prospective_decision_path=dec_path,
                expected_prospective_decision_sha256=dec_sha,
            )
            with self.assertRaises(InventoryVerificationError) as ctx:
                gen.generate()
            self.assertIn("saved inventory chroma.sqlite3 sha mismatch", str(ctx.exception).lower())

    def test_configurable_driver_pin_override(self):
        """Verify generator respects expected_driver_sha256 override parameter."""
        # When driver pin matches actual driver file
        actual_driver_sha = self.hashes["scripts/matched_baseline/offline_preflight.py"]
        gen_good = self._create_generator(expected_driver_sha256=actual_driver_sha)
        res = gen_good.generate()
        self.assertEqual(res["total_files"], 30)

        # When driver pin does not match actual driver file
        gen_bad = self._create_generator(
            output_dir=self.reports_dir / "bad_driver_out",
            expected_driver_sha256="deadbeef" * 8,
        )
        with self.assertRaises(CanonicalPinMismatchError) as ctx:
            gen_bad.generate()
        self.assertIn("offline_preflight.py checksum mismatch", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()


