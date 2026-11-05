"""
generate_master_launch_ledger.py
--------------------------------
Generates an authoritative, machine-readable launch inventory ledger (JSON and CSV)
with strict fail-closed safeguards:

1. Validates saved inventory evidence:
   - Verifies SHA-256 digest of inventory.json.
   - Verifies exit_code.txt == "0".
   - Verifies outcome == "STABLE_FILESYSTEM_INVENTORY" and errors == [].
   - Verifies before == after 100% stability.
2. Validates tokenizer assets against declared manifests:
   - Parses tokenizer_manifest.sha256 and gated_tokenizer_manifest.v1.sha256.
   - Compares measured file SHA-256 against expected manifest SHA-256.
   - Raises ManifestPinMismatchError on any discrepancy.
3. Validates canonical benchmark and graph data against reviewed pin constants:
   - Compares terra_350_benchmark.json, graph archive, provenance, and manifest.
   - Raises CanonicalPinMismatchError on any discrepancy.
4. Accurately labels codebase module measurements:
   - offline_preflight.py verified against Codex-0159 checkpoint.
   - Other active modules labeled MEASURED_ACTIVE_MODULE (local active measurement).
5. Enforces destination collision protection:
   - Rejects existing non-empty output directories.
   - Writes all export files in exclusive creation mode ("x").
   - Never overwrites or modifies existing ledger artifacts.
6. Guarantees 100% consistency between JSON and CSV rows.
7. Exits with non-zero code on any failure.
"""

from dataclasses import asdict, dataclass
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# =============================================================================
# Custom Exception Hierarchy
# =============================================================================

class LedgerGenerationError(Exception):
    """Base exception for launch ledger generation failures."""
    pass


class DestinationCollisionError(LedgerGenerationError):
    """Raised when output directory or export file already exists."""
    pass


class InventoryVerificationError(LedgerGenerationError):
    """Raised when saved inventory evidence is corrupt, missing, or unstable."""
    pass


class ManifestPinMismatchError(LedgerGenerationError):
    """Raised when a measured file SHA-256 does not match the expected manifest pin."""
    pass


class CanonicalPinMismatchError(LedgerGenerationError):
    """Raised when a measured file SHA-256 does not match canonical reviewed constants."""
    pass


# =============================================================================
# Master Generator Class
# =============================================================================

class MasterLaunchLedgerGenerator:
    """
    Validates, cross-checks, and exports the master launch ledger.
    """

    # Canonical inventory constants
    EXPECTED_SAVED_INVENTORY_SHA256 = "1d56f91cb1a18da9446d3e33f38011c75c31765c9c572a122fa40d4212ffca12"

    # Audited canonical constants from ProtectedInventoryAuditor
    EXPECTED_BENCHMARK_350_SHA256 = "8144fa81cf98899d8f48b49f98f147d19b4714c9c23895ed45b523093450b6b3"
    EXPECTED_CANONICAL_GRAPH_SHA256 = "330ab8c58468011de380f0d2a82f4cfda28e628ac001c314572a751540da5c63"
    EXPECTED_GRAPH_PROVENANCE_SHA256 = "f185c50995825b280e81a1b7a4e3912340090e00dcb5608c1b7568fdea707677"
    EXPECTED_GRAPH_MANIFEST_SHA256 = "be670d3fb62c547b057fe29bc1367a1198e7f3bdde02f6a5e4149df67ae51bb1"
    EXPECTED_PUBLIC_TOKENIZER_MANIFEST_SHA256 = "41902553acffa03065b3bc6049047d0d573fb4659aea9f428df6d3f809f84a44"
    EXPECTED_GATED_TOKENIZER_MANIFEST_SHA256 = "588f9614af4a5ae3cb43cf93014b5af386e9986db1d527763967d72a3f37da66"
    EXPECTED_OFFLINE_PREFLIGHT_SHA256 = "6b6cb11a95b34efe0457c3828be387b9d6e55357c42477182181a92fb53a4183"

    # Prospective store checkpoint evidence (Codex-0173 & Codex-0174)
    EXPECTED_PROSPECTIVE_DECISION_SHA256 = "553c9cbc2a8c610304659e0e49058b918179fa3d941ace1dd928c6b099756fba"
    EXPECTED_PROSPECTIVE_INVENTORY_SHA256 = "a44618af9cc95ffcce32f8ed70d3f7b7867dd3c72544cc52737c0f3d7365b4f6"
    EXPECTED_ACCEPTED_SQLITE_SHA256 = "c7fc28f24403303b384f73f3eac349629661a430aeee3c05e899c8d5e27b475d"

    def __init__(
        self,
        workspace_root: Path,
        saved_inventory_path: Path,
        output_dir: Path,
        expected_inventory_sha256: Optional[str] = EXPECTED_SAVED_INVENTORY_SHA256,
        expected_driver_sha256: Optional[str] = None,
        prospective_decision_path: Optional[Path] = None,
        expected_prospective_decision_sha256: Optional[str] = EXPECTED_PROSPECTIVE_DECISION_SHA256,
        enforce_exclusive_destination: bool = True,
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.saved_inventory_path = Path(saved_inventory_path).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.expected_inventory_sha256 = expected_inventory_sha256
        self.expected_driver_sha256 = expected_driver_sha256 or self.EXPECTED_OFFLINE_PREFLIGHT_SHA256
        self.prospective_decision_path = Path(prospective_decision_path).resolve() if prospective_decision_path else None
        self.expected_prospective_decision_sha256 = expected_prospective_decision_sha256
        self.enforce_exclusive_destination = enforce_exclusive_destination

    @staticmethod
    def hash_file(path: Path) -> str:
        """Compute lowercase hexadecimal SHA-256 digest of a file in 64 KB binary chunks."""
        h = hashlib.sha256()
        with open(path, "rb") as fp:
            while chunk := fp.read(65536):
                h.update(chunk)
        return h.hexdigest().lower()

    @staticmethod
    def parse_sha256_manifest(manifest_path: Path) -> Dict[str, str]:
        """
        Parse standard sha256 manifest file (<hash>  <relpath>).
        Normalizes paths to forward slashes and returns dict mapping path -> expected hash.
        """
        pins: Dict[str, str] = {}
        with open(manifest_path, "r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue
                sha, rel = parts[0].strip().lower(), parts[1].strip().replace("\\", "/")
                pins[rel] = sha
                pins[Path(rel).name] = sha
        return pins

    def verify_saved_inventory_evidence(self) -> Dict[str, Any]:
        """
        Verifies the integrity, stability, and exit status of the saved inventory evidence.
        Fails closed on hash mismatch, non-zero exit code, unhandled errors, or before/after drift.
        """
        if not self.saved_inventory_path.exists():
            raise InventoryVerificationError(f"Saved inventory file not found: {self.saved_inventory_path}")

        if self.expected_inventory_sha256:
            actual_inv_sha = self.hash_file(self.saved_inventory_path)
            if actual_inv_sha != self.expected_inventory_sha256.lower():
                raise InventoryVerificationError(
                    f"Saved inventory SHA-256 mismatch: expected {self.expected_inventory_sha256}, got {actual_inv_sha}"
                )

        exit_code_path = self.saved_inventory_path.parent / "exit_code.txt"
        if not exit_code_path.exists():
            raise InventoryVerificationError(f"Saved inventory exit_code.txt not found at: {exit_code_path}")
        exit_code_content = exit_code_path.read_text(encoding="utf-8").strip()
        if exit_code_content != "0":
            raise InventoryVerificationError(f"Saved inventory exit code is non-zero: '{exit_code_content}'")

        try:
            with open(self.saved_inventory_path, "r", encoding="utf-8") as fp:
                inv_data = json.load(fp)
        except Exception as e:
            raise InventoryVerificationError(f"Failed to parse saved inventory JSON: {e}")

        if inv_data.get("exit_code") != 0:
            raise InventoryVerificationError(f"Saved inventory records failure exit code: {inv_data.get('exit_code')}")
        if inv_data.get("outcome") != "STABLE_FILESYSTEM_INVENTORY":
            raise InventoryVerificationError(f"Saved inventory outcome not stable: '{inv_data.get('outcome')}'")
        if inv_data.get("errors"):
            raise InventoryVerificationError(f"Saved inventory contains errors: {inv_data.get('errors')}")

        # Assert before == after for both store and cache
        before = inv_data.get("before", {})
        after = inv_data.get("after", {})
        if not before or not after:
            raise InventoryVerificationError("Saved inventory missing 'before' or 'after' sections.")

        for label in ("store", "cache"):
            b_sec = before.get(label)
            a_sec = after.get(label)
            if not b_sec or not a_sec:
                raise InventoryVerificationError(f"Saved inventory missing section '{label}'.")
            b_json = json.dumps(b_sec, sort_keys=True)
            a_json = json.dumps(a_sec, sort_keys=True)
            if b_json != a_json:
                raise InventoryVerificationError(f"Saved inventory drift detected between before and after for '{label}'.")

        # Validate prospective decision record if configured
        if self.prospective_decision_path:
            if not self.prospective_decision_path.exists():
                raise InventoryVerificationError(
                    f"Prospective decision record not found: {self.prospective_decision_path}"
                )
            actual_dec_sha = self.hash_file(self.prospective_decision_path)
            if self.expected_prospective_decision_sha256 and actual_dec_sha != self.expected_prospective_decision_sha256.lower():
                raise InventoryVerificationError(
                    f"Prospective decision SHA-256 mismatch: expected {self.expected_prospective_decision_sha256}, got {actual_dec_sha}"
                )
            try:
                with open(self.prospective_decision_path, "r", encoding="utf-8") as fp:
                    dec_data = json.load(fp)
            except Exception as e:
                raise InventoryVerificationError(f"Failed to parse prospective decision JSON: {e}") from e

            if dec_data.get("status") != "ACCEPTED_PROSPECTIVE_INPUT_CHECKPOINT":
                raise InventoryVerificationError(
                    f"Invalid prospective decision status: '{dec_data.get('status')}'"
                )
            accepted_sql = dec_data.get("accepted_sqlite_sha256", "").lower()
            if accepted_sql != self.EXPECTED_ACCEPTED_SQLITE_SHA256.lower():
                raise InventoryVerificationError(
                    f"Prospective decision SQLite hash mismatch: expected {self.EXPECTED_ACCEPTED_SQLITE_SHA256}, got {accepted_sql}"
                )

            # Verify that saved inventory actually contains the accepted SQLite hash
            store_files = inv_data.get("before", {}).get("store", {}).get("files", [])
            sql_entry = next((f for f in store_files if f.get("relative_path") == "chroma.sqlite3"), None)
            if not sql_entry:
                raise InventoryVerificationError("Saved inventory store files missing 'chroma.sqlite3' entry")
            if sql_entry.get("sha256", "").lower() != accepted_sql:
                raise InventoryVerificationError(
                    f"Saved inventory chroma.sqlite3 SHA mismatch: expected {accepted_sql}, got {sql_entry.get('sha256')}"
                )

        return inv_data

    def generate(self) -> Dict[str, Any]:
        """
        Executes complete ledger generation, expected-vs-measured comparisons,
        and exclusive export.
        """
        # 1. Collision protection: check destination
        if self.enforce_exclusive_destination:
            if self.output_dir.exists():
                existing_items = list(self.output_dir.iterdir())
                if existing_items:
                    raise DestinationCollisionError(
                        f"Destination directory already exists and contains {len(existing_items)} items: {self.output_dir}. "
                        "Overwriting preserved ledger artifacts is strictly forbidden."
                    )

        # 2. Verify saved inventory evidence
        inv_data = self.verify_saved_inventory_evidence()

        entries: List[Dict[str, Any]] = []

        # 3. Source Chroma Store (Extracted from verified saved record)
        store_files = inv_data["before"]["store"]["files"]
        for f in store_files:
            rel = f["relative_path"]
            abs_p = f["absolute_path"]
            size = f["size_bytes"]
            sha = f["sha256"].lower()
            role = "store_sqlite" if rel == "chroma.sqlite3" else "store_index_data"
            entries.append({
                "category": "source_chroma_store",
                "role": role,
                "relative_path": f"dataset_20k_cap/vector_db_20k/{rel}",
                "absolute_path": abs_p,
                "size_bytes": size,
                "sha256": sha,
                "evidence_type": "FROZEN_SAVED_INVENTORY",
                "evidence_source": "reports/read_only_inventory_dd3ef843b37248b8953ec0ca9f88558b/inventory.json",
                "verification_status": "VERIFIED_SAVED_RECORD",
            })

        # 4. Local ONNX Model Cache (Extracted from verified saved record)
        cache_files = inv_data["before"]["cache"]["files"]
        for f in cache_files:
            rel = f["relative_path"]
            abs_p = f["absolute_path"]
            size = f["size_bytes"]
            sha = f["sha256"].lower()
            role = "model_archive" if rel == "onnx.tar.gz" else ("model_weights_onnx" if rel.endswith(".onnx") else "model_support_asset")
            entries.append({
                "category": "onnx_model_cache",
                "role": role,
                "relative_path": rel,
                "absolute_path": abs_p,
                "size_bytes": size,
                "sha256": sha,
                "evidence_type": "FROZEN_SAVED_INVENTORY",
                "evidence_source": "reports/read_only_inventory_dd3ef843b37248b8953ec0ca9f88558b/inventory.json",
                "verification_status": "VERIFIED_SAVED_RECORD",
            })

        # 5. Tokenizer Manifests (Verify manifest hash against canonical constants)
        pub_man_path = self.workspace_root / "assets" / "tokenizers" / "tokenizer_manifest.sha256"
        gated_man_path = self.workspace_root / "assets" / "tokenizers" / "gated_tokenizer_manifest.v1.sha256"

        for man_path, exp_man_sha, role in [
            (pub_man_path, self.EXPECTED_PUBLIC_TOKENIZER_MANIFEST_SHA256, "public_manifest"),
            (gated_man_path, self.EXPECTED_GATED_TOKENIZER_MANIFEST_SHA256, "gated_manifest"),
        ]:
            if not man_path.exists():
                raise FileNotFoundError(f"Missing tokenizer manifest: {man_path}")
            act_man_sha = self.hash_file(man_path)
            if act_man_sha != exp_man_sha.lower():
                raise ManifestPinMismatchError(
                    f"Tokenizer manifest pin mismatch for {man_path.name}: expected {exp_man_sha}, got {act_man_sha}"
                )
            rel_p = str(man_path.relative_to(self.workspace_root)).replace("\\", "/")
            entries.append({
                "category": "tokenizer_manifest",
                "role": role,
                "relative_path": rel_p,
                "absolute_path": str(man_path),
                "size_bytes": man_path.stat().st_size,
                "sha256": act_man_sha,
                "evidence_type": "VALIDATED_MANIFEST_RECORD",
                "evidence_source": rel_p,
                "verification_status": "VERIFIED_MANIFEST_MATCH",
            })

        # Parse manifests for individual file pin verification
        pub_pins = self.parse_sha256_manifest(pub_man_path)
        gated_pins = self.parse_sha256_manifest(gated_man_path)
        manifest_pins = {**pub_pins, **gated_pins}

        # 6. Admitted Tokenizer Assets (Compare measured hash against parsed manifest pins)
        tok_files = [
            # Generator
            ("assets/tokenizers/generator/tokenizer.json", "generator_tokenizer"),
            ("assets/tokenizers/generator/tokenizer_config.json", "generator_config"),
            ("assets/tokenizers/generator/special_tokens_map.json", "generator_tokens_map"),
            # Router
            ("assets/tokenizers/router/tokenizer.json", "router_tokenizer"),
            ("assets/tokenizers/router/tokenizer_config.json", "router_config"),
            ("assets/tokenizers/router/special_tokens_map.json", "router_tokens_map"),
            ("assets/tokenizers/router/chat_template.json", "router_chat_template"),
            # Judge 1
            ("assets/tokenizers/judge1/tokenizer.json", "judge1_tokenizer"),
            ("assets/tokenizers/judge1/tokenizer_config.json", "judge1_config"),
            ("assets/tokenizers/judge1/vocab.json", "judge1_vocab"),
            ("assets/tokenizers/judge1/merges.txt", "judge1_merges"),
            # Judge 2
            ("assets/tokenizers/judge2/tokenizer.json", "judge2_tokenizer"),
            ("assets/tokenizers/judge2/tokenizer_config.json", "judge2_config"),
            ("assets/tokenizers/judge2/special_tokens_map.json", "judge2_tokens_map"),
            ("assets/tokenizers/judge2/chat_template.jinja", "judge2_chat_template"),
        ]

        for rel, role in tok_files:
            p = self.workspace_root / rel
            if not p.exists():
                raise FileNotFoundError(f"Missing tokenizer file: {p}")
            act_sha = self.hash_file(p)
            exp_sha = manifest_pins.get(rel) or manifest_pins.get(p.name)
            if not exp_sha:
                raise ManifestPinMismatchError(f"No expected manifest pin found for tokenizer asset: {rel}")
            if act_sha != exp_sha.lower():
                raise ManifestPinMismatchError(
                    f"Tokenizer pin mismatch on '{rel}': expected {exp_sha}, got {act_sha}"
                )
            ev_source = "assets/tokenizers/tokenizer_manifest.sha256" if "judge" in rel else "assets/tokenizers/gated_tokenizer_manifest.v1.sha256"
            entries.append({
                "category": "tokenizer_asset",
                "role": role,
                "relative_path": rel,
                "absolute_path": str(p),
                "size_bytes": p.stat().st_size,
                "sha256": act_sha,
                "evidence_type": "VALIDATED_MANIFEST_RECORD",
                "evidence_source": ev_source,
                "verification_status": "VERIFIED_MANIFEST_MATCH",
            })

        # 7. Benchmark Cohort & Canonical Graph Data (Compare against canonical pin constants)
        data_files = [
            ("benchmark_data", "terra_350_benchmark.json", "evaluation_cohort_350", self.EXPECTED_BENCHMARK_350_SHA256, "ProtectedInventoryAuditor.EXPECTED_BENCHMARK_350_SHA256"),
            ("canonical_graph", "TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.json.xz", "graph_index_xz", self.EXPECTED_CANONICAL_GRAPH_SHA256, "ProtectedInventoryAuditor.EXPECTED_CANONICAL_GRAPH_SHA256"),
            ("graph_provenance", "TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/terra_eeg_index_20k_r30corr_v1.provenance.json", "graph_provenance_json", self.EXPECTED_GRAPH_PROVENANCE_SHA256, "ProtectedInventoryAuditor.EXPECTED_GRAPH_PROVENANCE_SHA256"),
            ("graph_manifest", "TERRA_EDITORIAL_RESTART_V2/derived_graphs/r30corr_v1/manifest.sha256", "graph_manifest_sha256", self.EXPECTED_GRAPH_MANIFEST_SHA256, "ProtectedInventoryAuditor.EXPECTED_GRAPH_MANIFEST_SHA256"),
        ]

        for cat, rel, role, exp_sha, ev_source in data_files:
            p = self.workspace_root / rel
            if not p.exists():
                raise FileNotFoundError(f"Missing canonical data file: {p}")
            act_sha = self.hash_file(p)
            if act_sha != exp_sha.lower():
                raise CanonicalPinMismatchError(
                    f"Canonical data pin mismatch on '{rel}': expected {exp_sha}, got {act_sha}"
                )
            entries.append({
                "category": cat,
                "role": role,
                "relative_path": rel,
                "absolute_path": str(p),
                "size_bytes": p.stat().st_size,
                "sha256": act_sha,
                "evidence_type": "CANONICAL_PIN_RECORD",
                "evidence_source": ev_source,
                "verification_status": "VERIFIED_CANONICAL_PIN_MATCH",
            })

        # 8. Codebase Modules & Pinned Interpreter
        code_files = [
            ("codebase_module", "scripts/matched_baseline/fast_tokenizer_adapter.py", "tokenizer_adapter", "MEASURED_CODEBASE_IDENTITY", "Local_measurement_Codex-0160_observation"),
            ("codebase_module", "scripts/matched_baseline/offline_preflight.py", "preflight_driver", "MEASURED_CODEBASE_IDENTITY", "Codex-0159_pass_checkpoint"),
            ("codebase_module", "scripts/matched_baseline/common_serializer.py", "serializer_engine", "MEASURED_CODEBASE_IDENTITY", "Local_measurement"),
            ("codebase_module", "scripts/matched_baseline/bm25_engine.py", "bm25_engine", "MEASURED_CODEBASE_IDENTITY", "Local_measurement"),
            ("codebase_module", "scripts/matched_baseline/hybrid_retriever.py", "hybrid_retriever", "MEASURED_CODEBASE_IDENTITY", "Local_measurement"),
            ("codebase_module", "scripts/matched_baseline/terra_retriever.py", "terra_retriever", "MEASURED_CODEBASE_IDENTITY", "Local_measurement"),
            ("python_runtime", "venv/Scripts/python.exe", "python_interpreter_binary", "MEASURED_CODEBASE_IDENTITY", "Python_3.14_venv_measurement"),
        ]

        for cat, rel, role, ev_type, ev_source in code_files:
            p = self.workspace_root / rel
            if not p.exists():
                raise FileNotFoundError(f"Missing codebase file: {p}")
            act_sha = self.hash_file(p)
            v_status = "MEASURED_ACTIVE_MODULE" if cat == "codebase_module" else "MEASURED_ACTIVE_RUNTIME"
            if rel == "scripts/matched_baseline/offline_preflight.py":
                if act_sha == self.expected_driver_sha256.lower():
                    v_status = "VERIFIED_CHECKPOINT_MATCH"
                else:
                    raise CanonicalPinMismatchError(
                        f"offline_preflight.py checksum mismatch: expected {self.expected_driver_sha256}, got {act_sha}"
                    )
            entries.append({
                "category": cat,
                "role": role,
                "relative_path": rel,
                "absolute_path": str(p),
                "size_bytes": p.stat().st_size,
                "sha256": act_sha,
                "evidence_type": ev_type,
                "evidence_source": ev_source,
                "verification_status": v_status,
            })

        # 9. Compute Category Summary & Master Totals
        cat_summary: Dict[str, Dict[str, int]] = {}
        for e in entries:
            c = e["category"]
            if c not in cat_summary:
                cat_summary[c] = {"file_count": 0, "total_bytes": 0}
            cat_summary[c]["file_count"] += 1
            cat_summary[c]["total_bytes"] += e["size_bytes"]

        overall_total_bytes = sum(e["size_bytes"] for e in entries)
        overall_file_count = len(entries)

        master_payload = {
            "schema_version": "1.1",
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_files": overall_file_count,
            "total_bytes": overall_total_bytes,
            "category_summary": cat_summary,
            "entries": entries,
        }

        # 10. Exclusive File Writes
        self.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = self.output_dir / "launch_inventory.json"
        csv_path = self.output_dir / "launch_inventory.csv"
        man_path = self.output_dir / "manifest.sha256"

        try:
            with open(json_path, "x", encoding="utf-8") as fp:
                json.dump(master_payload, fp, indent=2)
        except FileExistsError:
            raise DestinationCollisionError(f"Target JSON file already exists: {json_path}")

        fieldnames = [
            "category",
            "role",
            "relative_path",
            "absolute_path",
            "size_bytes",
            "sha256",
            "evidence_type",
            "evidence_source",
            "verification_status",
        ]
        try:
            with open(csv_path, "x", newline="", encoding="utf-8") as fp:
                writer = csv.DictWriter(fp, fieldnames=fieldnames)
                writer.writeheader()
                for e in entries:
                    writer.writerow(e)
        except FileExistsError:
            raise DestinationCollisionError(f"Target CSV file already exists: {csv_path}")

        h_json = self.hash_file(json_path)
        h_csv = self.hash_file(csv_path)
        try:
            with open(man_path, "x", encoding="utf-8") as fp:
                fp.write(f"{h_json}  launch_inventory.json\n")
                fp.write(f"{h_csv}  launch_inventory.csv\n")
        except FileExistsError:
            raise DestinationCollisionError(f"Target manifest file already exists: {man_path}")

        return {
            "total_files": overall_file_count,
            "total_bytes": overall_total_bytes,
            "category_summary": cat_summary,
            "json_path": str(json_path),
            "csv_path": str(csv_path),
            "manifest_path": str(man_path),
            "json_sha256": h_json,
            "csv_sha256": h_csv,
        }


# =============================================================================
# CLI Entrypoint with Non-Zero Exit Codes
# =============================================================================

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="TERRA Master Launch Ledger Generator")
    parser.add_argument("--workspace-root", type=str, default=str(WORKSPACE_ROOT), help="Workspace root directory")
    parser.add_argument(
        "--saved-inventory",
        type=str,
        default=str(WORKSPACE_ROOT / "reports" / "read_only_inventory_dd3ef843b37248b8953ec0ca9f88558b" / "inventory.json"),
        help="Path to saved inventory JSON evidence",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(WORKSPACE_ROOT / "reports" / "master_launch_ledger_v2"),
        help="Target output directory (must not overwrite existing files)",
    )
    parser.add_argument(
        "--expected-inventory-sha",
        type=str,
        default=MasterLaunchLedgerGenerator.EXPECTED_SAVED_INVENTORY_SHA256,
        help="Expected SHA-256 digest of saved inventory JSON",
    )
    parser.add_argument(
        "--expected-driver-sha",
        type=str,
        default=None,
        help="Expected SHA-256 digest of offline_preflight.py driver",
    )
    parser.add_argument(
        "--prospective-decision",
        type=str,
        default=None,
        help="Path to accepted prospective store decision JSON (e.g. ACCEPTED_PROSPECTIVE_CHECKPOINT.json)",
    )
    parser.add_argument(
        "--expected-decision-sha",
        type=str,
        default=MasterLaunchLedgerGenerator.EXPECTED_PROSPECTIVE_DECISION_SHA256,
        help="Expected SHA-256 digest of prospective decision JSON",
    )
    args = parser.parse_args()

    try:
        generator = MasterLaunchLedgerGenerator(
            workspace_root=Path(args.workspace_root),
            saved_inventory_path=Path(args.saved_inventory),
            output_dir=Path(args.output_dir),
            expected_inventory_sha256=args.expected_inventory_sha,
            expected_driver_sha256=args.expected_driver_sha,
            prospective_decision_path=Path(args.prospective_decision) if args.prospective_decision else None,
            expected_prospective_decision_sha256=args.expected_decision_sha,
            enforce_exclusive_destination=True,
        )
        res = generator.generate()
        print(f"Master Launch Ledger successfully generated in: {args.output_dir}")
        print(f"Total Files: {res['total_files']}, Total Bytes: {res['total_bytes']}")
        print(f"JSON SHA-256: {res['json_sha256']}")
        print(f"CSV  SHA-256: {res['csv_sha256']}")
        return 0
    except DestinationCollisionError as dce:
        sys.stderr.write(f"[COLLISION ERROR] {dce}\n")
        return 1
    except InventoryVerificationError as ive:
        sys.stderr.write(f"[INVENTORY ERROR] {ive}\n")
        return 1
    except ManifestPinMismatchError as mpme:
        sys.stderr.write(f"[MANIFEST PIN MISMATCH] {mpme}\n")
        return 1
    except CanonicalPinMismatchError as cpme:
        sys.stderr.write(f"[CANONICAL PIN MISMATCH] {cpme}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"[UNEXPECTED ERROR] {type(e).__name__}: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
