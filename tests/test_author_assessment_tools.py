#!/usr/bin/env python3
"""
tests/test_author_assessment_tools.py (v3 - CODE_AUDIT_02 Compliant)
=====================================================================
Comprehensive synthetic test suite auditing CODE_AUDIT_02 repairs:
  1. Multi-pipeline 1,750-record canonical fixture (350 identical query IDs per pipeline)
     and 400-record temporal grid.
  2. Canonical cross-pipeline universe validation & field type error detection.
  3. Stage B SRS drawn FIRST from ALL 350 records with exact inclusion prob 40/350.
  4. Dynamic metadata accounting for sparse diagnostics (no hardcoded counts).
  5. Shuffled presentation order and blinding invariance.
  6. Companion HTML and TXT reading views generation and multiline/formula fidelity.
  7. Fresh output destination collision enforcement (FileExistsError).
  8. Tampering detection negative control (ItemTamperingError on altered text/digest).
  9. Semantic completion validation (cross-field consistency, rationale, citation).
 10. Missing automated label handling (not treated as negative) and exact FNR/FOR arithmetic.
 11. Mixed refusal/substantive answer accounting in Stage B metrics.
 12. Cohen's Kappa zero-variance undefined handling.
 13. End-to-end CLI execution of both prepare and process scripts with integrity manifest verification.
"""

import os
import sys
import json
import shutil
import hashlib
import tempfile
import subprocess
import unittest
import unittest.mock
from pathlib import Path
from typing import Tuple, List, Dict, Set, Any, Optional

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import scripts.prepare_author_assessment_workbooks as prep_module
import scripts.process_author_assessments as proc_module

import openpyxl

from scripts.prepare_author_assessment_workbooks import (
    load_and_verify_inputs,
    validate_cohorts_and_schemas,
    draw_samples_and_allocate,
    build_private_key_mapping,
    verify_blinding_invariance,
    export_xlsx_workbook,
    export_tsv_workbook,
    export_html_reading_view,
    export_txt_reading_view,
    escape_formula,
    run_pipeline,
    BlindingSecurityError,
    TEMPORAL_CUTOFFS,
    TEMPORAL_CONDITIONS,
    TEMPORAL_PIPELINES,
    CANONICAL_TARGET_PIPELINE,
    CANONICAL_ALL_PIPELINES,
    CANONICAL_CATEGORIES
)

from scripts.process_author_assessments import (
    load_author_file,
    validate_workbook_completion,
    validate_author_records_against_mapping,
    compute_cohens_kappa,
    clopper_pearson_interval,
    evaluate_inter_assessor_agreement,
    compute_population_metrics,
    process_author_assessments,
    ItemTamperingError,
    WorkbookIncompleteError,
    HashVerificationError,
    unescape_formula
)


def create_synthetic_datasets(base_dir: Path, sparse_diagnostics: bool = False) -> Tuple[Path, Path]:
    """
    Generates synthetic datasets strictly adhering to authentic schemas:
      - 400 temporal grid records (50 queries, 5 cutoffs, 2 conditions, 4 pipelines).
      - 1,750 canonical records across 5 pipelines (exact identical 350 queries per pipeline).
    """
    temp_records = []
    for cutoff in TEMPORAL_CUTOFFS:
        for q_idx in range(1, 11):
            qid = f"SYN-TLP-{cutoff}-{q_idx:02d}"
            for cond in TEMPORAL_CONDITIONS:
                for pipe in TEMPORAL_PIPELINES:
                    is_leak = (pipe in ("1_Direct_LLM", "TERRA_ungated") and q_idx in (1, 2))
                    temp_records.append({
                        "query_id": qid,
                        "cutoff_year": cutoff,
                        "condition": cond,
                        "pipeline": pipe,
                        "stratum": f"stratum_{cutoff}",
                        "query": f"Synthetic legal query for {qid} as of {cutoff} under {cond}?",
                        "reference": f"Synthetic reference legal answer for {qid}.",
                        "answer_full": f"Synthetic response from {pipe} on {qid} under {cond}.",
                        "is_safe_refusal": False,
                        "sptlr_level2": is_leak,
                        "target_case_name": f"Landmark Case {q_idx}",
                        "target_case_year": cutoff + 5 if is_leak else cutoff - 5,
                        "adjudication": {
                            "consensus_severity_level": 2 if is_leak else 0,
                            "agreement_severity": True
                        },
                        "judge1_evaluation": {"severity_level": 2 if is_leak else 0, "error": False},
                        "judge2_evaluation": {"severity_level": 2 if is_leak else 0, "error": False}
                    })

    if not sparse_diagnostics:
        # Distribute diagnostic conditions across queries 09 and 10 in each cutoff
        for r in temp_records:
            qid = r["query_id"]
            if qid.endswith("-09") or qid.endswith("-10"):
                if r["pipeline"] == "TERRA_gated":
                    r["nli_gate_refusal"] = True
                if r["pipeline"] == "1_Direct_LLM":
                    r["adjudication"]["agreement_severity"] = False
                    r["judge1_evaluation"]["severity_level"] = 2
                    r["judge2_evaluation"]["severity_level"] = 0
                if r["pipeline"] == "TERRA_ungated":
                    r["judge2_evaluation"]["error"] = True
    else:
        # Only 2 diagnostic conditions total in entire dataset
        for r in temp_records:
            if r["query_id"] == "SYN-TLP-1950-01" and r["pipeline"] == "TERRA_gated":
                r["nli_gate_refusal"] = True
            if r["query_id"] == "SYN-TLP-1950-02" and r["pipeline"] == "1_Direct_LLM":
                r["adjudication"]["agreement_severity"] = False
                r["judge1_evaluation"]["severity_level"] = 2
                r["judge2_evaluation"]["severity_level"] = 0

    # Canonical dataset: 1,750 records across 5 pipelines (350 per pipeline)
    can_records = []
    for pipe in CANONICAL_ALL_PIPELINES:
        for i in range(1, 101):
            qid = f"A{i:03d}"
            can_records.append({
                "query_id": qid,
                "category": "A_Factual",
                "pipeline": pipe,
                "query": f"Canonical query {qid}?",
                "reference": f"Reference answer {qid}.",
                "answer_full": f"Response text from {pipe} for {qid}.",
                "faithfulness": 0.85,
                "safety_rejected": False
            })
        for i in range(1, 101):
            qid = f"B{i:03d}"
            can_records.append({
                "query_id": qid,
                "category": "B_Evolutionary",
                "pipeline": pipe,
                "query": f"Canonical query {qid}?",
                "reference": f"Reference answer {qid}.",
                "answer_full": f"Response text from {pipe} for {qid}.",
                "faithfulness": 0.75,
                "safety_rejected": False
            })
        for i in range(1, 76):
            qid = f"C{i:03d}"
            can_records.append({
                "query_id": qid,
                "category": "C_OutOfContext",
                "pipeline": pipe,
                "query": f"Canonical query {qid}?",
                "reference": f"Reference answer {qid}.",
                "answer_full": f"Response text from {pipe} for {qid}.",
                "faithfulness": 0.0,
                "safety_rejected": True
            })
        for i in range(1, 76):
            qid = f"D{i:03d}"
            faith = 0.25 if qid in ("D033", "D034") else (0.45 if qid in ("D010", "D020") else 0.80)
            can_records.append({
                "query_id": qid,
                "category": "D_Adversarial",
                "pipeline": pipe,
                "query": f"Canonical query {qid}?",
                "reference": f"Reference answer {qid}.",
                "answer_full": f"Response text from {pipe} for {qid}.",
                "faithfulness": faith,
                "safety_rejected": False if qid in ("D033", "D034", "D010", "D020") else True
            })

    temp_path = base_dir / "synthetic_temporal.json"
    can_path = base_dir / "synthetic_canonical.json"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(temp_records, f, indent=2)
    with open(can_path, "w", encoding="utf-8") as f:
        json.dump(can_records, f, indent=2)

    return temp_path, can_path


class TestAuthorAssessmentTools(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="terra_test_v3_"))
        self.temp_path, self.can_path = create_synthetic_datasets(self.test_dir)
        self.output_dir = self.test_dir / "output_test"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_schema_and_grid_validation(self):
        """Verifies full 400 temporal grid and 1750 canonical record validation."""
        temp_data, can_data, _ = load_and_verify_inputs(
            self.temp_path, self.can_path, expected_temp_hash=None, expected_can_hash=None
        )
        self.assertEqual(len(temp_data), 400)
        self.assertEqual(len(can_data), 1750)

        cohort_info = validate_cohorts_and_schemas(temp_data, can_data)
        self.assertEqual(len(cohort_info["temp_records_by_key"]), 400)
        self.assertEqual(len(cohort_info["terra_canonical_records"]), 350)

        # Duplicate composite key rejection in temporal records
        corrupted_temp = list(temp_data) + [temp_data[0]]
        with self.assertRaises(ValueError):
            validate_cohorts_and_schemas(corrupted_temp, can_data)

        # Universe mismatch across canonical pipelines rejection
        corrupted_can = [dict(r) for r in can_data]
        # Modify query_id of one record in 1_Direct_LLM to simulate mismatched query universe
        for r in corrupted_can:
            if r["pipeline"] == "1_Direct_LLM" and r["query_id"] == "A001":
                r["query_id"] = "MISMATCH_999"
                break
        with self.assertRaises(ValueError):
            validate_cohorts_and_schemas(temp_data, corrupted_can)

        # Canonical field type validation: non-boolean safety_rejected
        bad_type_can = [dict(r) for r in can_data]
        bad_type_can[0]["safety_rejected"] = "not_a_boolean"
        with self.assertRaises(ValueError):
            validate_cohorts_and_schemas(temp_data, bad_type_can)

    def test_02_stage_b_srs_drawn_first_and_allocation(self):
        """Verifies Stage B SRS drawn FIRST from ALL 350 records with exact p=40/350 and item digests."""
        temp_data, can_data, _ = load_and_verify_inputs(
            self.temp_path, self.can_path, expected_temp_hash=None, expected_can_hash=None
        )
        cohort_info = validate_cohorts_and_schemas(temp_data, can_data)
        auth1_items, auth2_items, meta = draw_samples_and_allocate(cohort_info, seed=20261008)

        # Workload sizing
        self.assertEqual(len(auth1_items), 76)
        self.assertEqual(len(auth2_items), 76)

        # Build mapping
        mapping = build_private_key_mapping(auth1_items, auth2_items)
        assessments = mapping["assessments"]

        # Verify Stage B properties
        srs_items = [v for v in assessments.values() if v["sample_stratum"] == "canonical_stage_b"]
        unique_srs_qids = set(v["query_id"] for v in srs_items)
        self.assertEqual(len(unique_srs_qids), 40)
        for it in srs_items:
            self.assertAlmostEqual(it["inclusion_prob"], 40.0 / 350.0, places=4)

        # Verify Stage A properties (20 clusters * 4 pipelines = 80 responses)
        stage_a_items = [v for v in assessments.values() if v["sample_stratum"] == "temporal_stage_a"]
        unique_stage_a_keys = set((v["query_id"], v["condition"], v["pipeline"]) for v in stage_a_items)
        self.assertEqual(len(unique_stage_a_keys), 80)

        # Verify item digest and SHA-256 presence for tampering prevention
        for aid, item in assessments.items():
            self.assertIn("query_text_sha256", item)
            self.assertIn("response_text_sha256", item)
            self.assertIn("item_digest", item)
            self.assertEqual(len(item["query_text_sha256"]), 64)
            self.assertEqual(len(item["response_text_sha256"]), 64)
            self.assertEqual(len(item["item_digest"]), 64)

    def test_03_sparse_diagnostics_handling(self):
        """Verifies that sparse diagnostic availability produces dynamic metadata and records shortfall."""
        s_temp_path, s_can_path = create_synthetic_datasets(self.test_dir, sparse_diagnostics=True)
        temp_data, can_data, _ = load_and_verify_inputs(
            s_temp_path, s_can_path, expected_temp_hash=None, expected_can_hash=None
        )
        cohort_info = validate_cohorts_and_schemas(temp_data, can_data)
        auth1_items, auth2_items, meta = draw_samples_and_allocate(cohort_info, seed=20261008)

        mapping = build_private_key_mapping(auth1_items, auth2_items)
        meta_dict = mapping["metadata"]

        self.assertIn("diagnostic_target_count", meta_dict)
        self.assertIn("diagnostic_selected_count", meta_dict)
        self.assertIn("diagnostic_shortfall", meta_dict)
        self.assertEqual(meta_dict["diagnostic_target_count"], 12)
        # With sparse diagnostics, selected count should be less than 12 and shortfall > 0
        self.assertLess(meta_dict["diagnostic_selected_count"], 12)
        self.assertGreater(meta_dict["diagnostic_shortfall"], 0)
        self.assertEqual(meta_dict["diagnostic_selected_count"] + meta_dict["diagnostic_shortfall"], 12)

    def test_04_pipeline_presentation_randomization(self):
        """Verifies that pipeline presentation positions are shuffled within temporal clusters."""
        temp_data, can_data, _ = load_and_verify_inputs(
            self.temp_path, self.can_path, expected_temp_hash=None, expected_can_hash=None
        )
        cohort_info = validate_cohorts_and_schemas(temp_data, can_data)
        auth1_items, auth2_items, _ = draw_samples_and_allocate(cohort_info, seed=20261008)

        temporal_items = [it for it in auth1_items if it["sample_stratum"] == "temporal_stage_a"]
        clusters = {}
        for it in temporal_items:
            clusters.setdefault(it["cluster_id"], []).append(it)

        first_positions = [cluster[0]["pipeline"] for cluster in clusters.values()]
        # First positions should not all be identical ("1_Direct_LLM")
        self.assertGreater(len(set(first_positions)), 1)

    def test_05_shuffled_presentation_and_blinding_invariance(self):
        """Verifies that items are shuffled in author sheets and blinding passes."""
        temp_data, can_data, _ = load_and_verify_inputs(
            self.temp_path, self.can_path, expected_temp_hash=None, expected_can_hash=None
        )
        cohort_info = validate_cohorts_and_schemas(temp_data, can_data)
        auth1_items, auth2_items, _ = draw_samples_and_allocate(cohort_info, seed=20261008)

        verify_blinding_invariance(auth1_items)
        verify_blinding_invariance(auth2_items)

        overlap_indices = [idx for idx, it in enumerate(auth1_items) if it["is_overlap"]]
        self.assertLess(min(overlap_indices), 66)

        # Artificially inject forbidden system name into query and assert BlindingSecurityError
        corrupted = [dict(auth1_items[0])]
        corrupted[0]["query_text"] = "Leaked term 5_Full_TERRA in query!"
        with self.assertRaises(BlindingSecurityError):
            verify_blinding_invariance(corrupted)

    def test_06_companion_reading_views_and_multiline_fidelity(self):
        """Verifies companion HTML/TXT generation, boundary whitespace, newlines, and reversible formula escaping."""
        # 1. Formula escaping and symmetric reversible contract for all triggers (Finding 1)
        prefixes = ["=", "+", "-", "@", "\t", "\r", "\n", "'"]
        for p in prefixes:
            raw = f"{p}Legal test content with prefix {repr(p)}"
            escaped = escape_formula(raw)
            unescaped = unescape_formula(escaped)
            self.assertEqual(unescaped, raw, f"Reversible round-trip failed for prefix {repr(p)}")

        # Test naturally occurring leading apostrophe text
        quoted_title = "'Marbury v. Madison', 5 U.S. 137 (1803)"
        esc_quoted = escape_formula(quoted_title)
        self.assertTrue(esc_quoted.startswith("''"))
        self.assertEqual(unescape_formula(esc_quoted), quoted_title)

        # Unescape formula whitespace preservation check
        self.assertEqual(unescape_formula("'=FORMULA"), "=FORMULA")
        self.assertEqual(unescape_formula("  whitespace preserved  "), "  whitespace preserved  ")
        self.assertEqual(unescape_formula("'\nleading newline"), "\nleading newline")

        # Test round-trip across XLSX and TSV exports with raw in-memory storage
        para1 = "=Heading: First Line\nSecond line with indentation   and details.\n"
        para2 = "+Additional observations:\n- Item 1\n- Item 2\n@cited reference\n'quoted precedent'\n"
        long_text = para1 * 50 + para2 * 50

        items = [{
            "assessment_id": "TEST-001",
            "cluster_id": "CLUST-01",
            "task_type": "Legal Evaluation Task",
            "as_of_cutoff_year": "As-of Year: 1950",
            "query_text": "=Query with leading formula and\nmultiple lines?",
            "response_text": long_text
        }]

        wb_path = self.test_dir / "multiline_test.xlsx"
        tsv_path = self.test_dir / "multiline_test.tsv"
        html_path = self.test_dir / "multiline_test.html"
        txt_path = self.test_dir / "multiline_test.txt"

        export_xlsx_workbook(wb_path, items, "Test Author")
        export_tsv_workbook(tsv_path, items)
        export_html_reading_view(html_path, items, "Test Author")
        export_txt_reading_view(txt_path, items, "Test Author")

        # Verify companion HTML exists and contains raw unescaped text
        self.assertTrue(html_path.exists())
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        self.assertIn("<!DOCTYPE html>", html_content)
        self.assertIn("TEST-001", html_content)
        self.assertIn("=Query with leading formula", html_content)

        # Verify companion TXT exists and contains raw text
        self.assertTrue(txt_path.exists())
        with open(txt_path, "r", encoding="utf-8") as f:
            txt_content = f.read()
        self.assertIn("TEST-001", txt_content)
        self.assertIn("=Query with leading formula", txt_content)

        # Verify load_author_file reconstructs the exact unbroken text from XLSX and TSV
        for pth in (wb_path, tsv_path):
            reloaded = load_author_file(pth)
            self.assertEqual(len(reloaded), 1)
            resp_key = [k for k in reloaded[0].keys() if "response" in k.lower()][0]
            q_key = [k for k in reloaded[0].keys() if "query" in k.lower()][0]
            self.assertEqual(reloaded[0][resp_key], long_text)
            self.assertEqual(reloaded[0][q_key], "=Query with leading formula and\nmultiple lines?")

    def test_07_destination_collision_enforcement(self):
        """Verifies run_pipeline raises FileExistsError if output directory already exists."""
        self.output_dir.mkdir(parents=True, exist_ok=False)
        with self.assertRaises(FileExistsError):
            run_pipeline(
                self.temp_path, self.can_path, self.output_dir, seed=20261008,
                test_fixture_mode=True
            )

    def test_08_tampering_detection_negative_control(self):
        """Verifies validate_author_records_against_mapping raises ItemTamperingError if immutable fields are altered."""
        run_pipeline(
            self.temp_path, self.can_path, self.output_dir, seed=20261008,
            test_fixture_mode=True
        )

        mapping_path = self.output_dir / "PRIVATE_KEY_MAPPING.json"
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        map_assessments = mapping["assessments"]

        auth1_tsv = self.output_dir / "ASSESSMENT_AUTHOR_1.tsv"
        records = load_author_file(auth1_tsv)

        # Without alterations, validation passes
        validate_author_records_against_mapping(records, map_assessments)

        # 1. Corrupt response text of the first record
        corrupted_resp = [dict(r) for r in records]
        resp_key = [k for k in corrupted_resp[0].keys() if "response" in k.lower()][0]
        corrupted_resp[0][resp_key] = corrupted_resp[0][resp_key] + " [TAMPERED_INJECTION]"
        with self.assertRaises(ItemTamperingError):
            validate_author_records_against_mapping(corrupted_resp, map_assessments)

        # 2. Corrupt cutoff year of the first record (Finding 2)
        corrupted_cutoff = [dict(r) for r in records]
        cutoff_key = [k for k in corrupted_cutoff[0].keys() if "cutoff" in k.lower()][0]
        corrupted_cutoff[0][cutoff_key] = "As-of Year: 2026"
        with self.assertRaises(ItemTamperingError):
            validate_author_records_against_mapping(corrupted_cutoff, map_assessments)

        # 3. Corrupt cluster ID of the first record (Finding 2)
        corrupted_clust = [dict(r) for r in records]
        clust_key = [k for k in corrupted_clust[0].keys() if "cluster" in k.lower()][0]
        corrupted_clust[0][clust_key] = "TAMPERED_CLUSTER_999"
        with self.assertRaises(ItemTamperingError):
            validate_author_records_against_mapping(corrupted_clust, map_assessments)

        # 4. Corrupt query text of the first record
        corrupted_q = [dict(r) for r in records]
        q_key = [k for k in corrupted_q[0].keys() if "query" in k.lower()][0]
        corrupted_q[0][q_key] = corrupted_q[0][q_key] + " [ALTERED_QUERY]"
        with self.assertRaises(ItemTamperingError):
            validate_author_records_against_mapping(corrupted_q, map_assessments)

        # 5. Missing mandatory cryptographic hash from mapping schema fails closed (Finding 2)
        bad_mapping = json.loads(json.dumps(map_assessments))
        first_aid = records[0]["assessment_id"]
        del bad_mapping[first_aid]["query_text_sha256"]
        with self.assertRaises(ValueError):
            validate_author_records_against_mapping(records, bad_mapping)

    def test_09_semantic_completion_validation(self):
        """Verifies semantic cross-field validation rules and rejection of contradictory judgments."""
        run_pipeline(
            self.temp_path, self.can_path, self.output_dir, seed=20261008,
            test_fixture_mode=True
        )

        mapping_path = self.output_dir / "PRIVATE_KEY_MAPPING.json"
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        map_assessments = mapping["assessments"]

        auth1_tsv = self.output_dir / "ASSESSMENT_AUTHOR_1.tsv"
        records = load_author_file(auth1_tsv)
        expected_ids = {aid for aid, m in map_assessments.items() if m["assigned_author"] == "author_1"}

        # 1. Blank records fail completion
        is_comp, rep = validate_workbook_completion(records, "author_1", expected_ids)
        self.assertFalse(is_comp)
        self.assertEqual(rep["unpopulated_items_count"], len(records))

        # 2. Populate records validly
        valid_records = []
        for r in records:
            vr = dict(r)
            vr["response_status"] = "substantive answer"
            vr["source_grounded_correctness"] = "supported"
            vr["temporal_leakage"] = "no"
            vr["responsiveness_usefulness"] = "addresses requested issue"
            vr["citation_check"] = "authentic and supports proposition"
            vr["refusal_assessment"] = "not applicable"
            vr["source_citation_or_url"] = "123 U.S. 456"
            vr["supporting_excerpt"] = "Direct quote from opinion."
            vr["assessment_rationale"] = "Valid legal analysis rationale."
            vr["assessor_identity"] = "Author 1"
            vr["timestamp"] = "2026-10-08T22:00:00Z"
            valid_records.append(vr)

        is_comp, rep = validate_workbook_completion(valid_records, "author_1", expected_ids)
        self.assertTrue(is_comp)
        self.assertEqual(rep["invalid_enums_count"], 0)
        self.assertEqual(rep["semantic_violations_count"], 0)

        # 3. Contradictory judgment: Substantive answer marked correctness 'not applicable'
        bad_records_1 = [dict(r) for r in valid_records]
        bad_records_1[0]["source_grounded_correctness"] = "not applicable"
        with self.assertRaises(WorkbookIncompleteError):
            validate_workbook_completion(bad_records_1, "author_1", expected_ids, raise_on_error=True)

        # 4. Contradictory judgment: Supported claim without supporting excerpt
        bad_records_2 = [dict(r) for r in valid_records]
        bad_records_2[0]["supporting_excerpt"] = ""
        with self.assertRaises(WorkbookIncompleteError):
            validate_workbook_completion(bad_records_2, "author_1", expected_ids, raise_on_error=True)

        # 5. Missing rationale: Empty rationale rejected
        bad_records_3 = [dict(r) for r in valid_records]
        bad_records_3[0]["assessment_rationale"] = ""
        with self.assertRaises(WorkbookIncompleteError):
            validate_workbook_completion(bad_records_3, "author_1", expected_ids, raise_on_error=True)

    def test_10_missing_labels_and_exact_confusion_matrix(self):
        """Verifies that missing automated baselines are not treated as negatives and tests exact FNR/FOR arithmetic."""
        run_pipeline(
            self.temp_path, self.can_path, self.output_dir, seed=20261008,
            test_fixture_mode=True
        )

        mapping_path = self.output_dir / "PRIVATE_KEY_MAPPING.json"
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        auth1_tsv = self.output_dir / "ASSESSMENT_AUTHOR_1.tsv"
        auth2_tsv = self.output_dir / "ASSESSMENT_AUTHOR_2.tsv"
        a1_recs = load_author_file(auth1_tsv)
        a2_recs = load_author_file(auth2_tsv)

        # Artificially set one automated baseline to None (missing/unlabeled)
        sample_aid = list(mapping["assessments"].keys())[0]
        mapping["assessments"][sample_aid]["automated_baseline"]["sptlr_level2"] = None

        # Build evaluations
        for r in a1_recs:
            r["response_status"] = "substantive answer"
            r["source_grounded_correctness"] = "supported"
            r["temporal_leakage"] = "no"
            r["responsiveness_usefulness"] = "addresses requested issue"
            r["citation_check"] = "authentic and supports proposition"
            r["refusal_assessment"] = "not applicable"
            r["source_citation_or_url"] = "123 U.S. 456"
            r["supporting_excerpt"] = "Holding"
            r["assessment_rationale"] = "Valid rationale"
            r["assessor_identity"] = "Author 1"
            r["timestamp"] = "2026-10-08T22:00:00Z"

        for r in a2_recs:
            r["response_status"] = "substantive answer"
            r["source_grounded_correctness"] = "supported"
            r["temporal_leakage"] = "no"
            r["responsiveness_usefulness"] = "addresses requested issue"
            r["citation_check"] = "authentic and supports proposition"
            r["refusal_assessment"] = "not applicable"
            r["source_citation_or_url"] = "123 U.S. 456"
            r["supporting_excerpt"] = "Holding"
            r["assessment_rationale"] = "Valid rationale"
            r["assessor_identity"] = "Author 2"
            r["timestamp"] = "2026-10-08T22:00:00Z"

        dict_a1 = {r["assessment_id"]: r for r in a1_recs}
        dict_a2 = {r["assessment_id"]: r for r in a2_recs}

        unique_items_dict = {}
        for aid, meta in mapping["assessments"].items():
            key = (meta["query_id"], meta["condition"], meta["pipeline"])
            if key not in unique_items_dict:
                unique_items_dict[key] = {
                    "unique_key": key,
                    "meta": meta,
                    "author_1_eval": None,
                    "author_2_eval": None
                }
            if meta["assigned_author"] == "author_1":
                unique_items_dict[key]["author_1_eval"] = dict_a1.get(aid)
            elif meta["assigned_author"] == "author_2":
                unique_items_dict[key]["author_2_eval"] = dict_a2.get(aid)

        metrics = compute_population_metrics(list(unique_items_dict.values()))
        temp_stats = metrics["temporal_probability_sample"]

        # Missing automated record is correctly counted in missing_or_unlabeled_automated_count
        if mapping["assessments"][sample_aid]["sample_stratum"] == "temporal_stage_a":
            self.assertGreaterEqual(temp_stats["missing_or_unlabeled_automated_count"], 1)

        # When human leakage is all "no", TP=0, FN=0 -> reference positives = 0 -> FNR is explicitly UNDEFINED
        self.assertEqual(temp_stats["confusion_matrix"]["false_negative_fn_missed"], 0)
        self.assertIn("UNDEFINED", temp_stats["false_negative_rate_fnr"])

    def test_11_mixed_refusal_accounting_in_canonical_metrics(self):
        """Verifies that mixed refusal/substantive answers enter strict and broad yields (Finding 5)."""
        run_pipeline(
            self.temp_path, self.can_path, self.output_dir, seed=20261008,
            test_fixture_mode=True
        )

        mapping_path = self.output_dir / "PRIVATE_KEY_MAPPING.json"
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        auth1_tsv = self.output_dir / "ASSESSMENT_AUTHOR_1.tsv"
        auth2_tsv = self.output_dir / "ASSESSMENT_AUTHOR_2.tsv"
        a1_recs = load_author_file(auth1_tsv)
        a2_recs = load_author_file(auth2_tsv)

        # For canonical items (40 SRS items), configure:
        # - 20 items: substantive answer, supported, addresses requested issue (pure strict supported responsive)
        # - 5 items: mixed refusal/substantive answer, supported, addresses requested issue (mixed strict supported responsive)
        # - 5 items: mixed refusal/substantive answer, contradicted, partly addresses (mixed contradicted)
        # - 8 items: refusal, not applicable, not applicable (pure refusal)
        # - 2 items: unusable / corrupted output
        can_unique_keys = sorted(list(set(
            (m["query_id"], m["condition"], m["pipeline"])
            for m in mapping["assessments"].values()
            if m["sample_stratum"] == "canonical_stage_b"
        )))
        self.assertEqual(len(can_unique_keys), 40)

        can_key_to_status = {}
        for idx, k in enumerate(can_unique_keys):
            if idx < 20:
                can_key_to_status[k] = ("substantive answer", "supported", "addresses requested issue", "not applicable")
            elif idx < 25:
                can_key_to_status[k] = ("mixed refusal/substantive answer", "supported", "addresses requested issue", "unjustified refusal")
            elif idx < 30:
                can_key_to_status[k] = ("mixed refusal/substantive answer", "contradicted", "partly addresses", "unjustified refusal")
            elif idx < 38:
                can_key_to_status[k] = ("refusal", "not applicable", "not applicable", "justified refusal")
            else:
                can_key_to_status[k] = ("unusable / corrupted output", "not applicable", "not applicable", "not applicable")

        all_recs = a1_recs + a2_recs
        for r in all_recs:
            aid = r.get("assessment_id")
            meta = mapping["assessments"][aid]
            key = (meta["query_id"], meta["condition"], meta["pipeline"])
            if key in can_key_to_status:
                stat, corr, usef, ref_just = can_key_to_status[key]
                r["response_status"] = stat
                r["source_grounded_correctness"] = corr
                r["responsiveness_usefulness"] = usef
                r["refusal_assessment"] = ref_just
            else:
                r["response_status"] = "substantive answer"
                r["source_grounded_correctness"] = "supported"
                r["responsiveness_usefulness"] = "addresses requested issue"
                r["refusal_assessment"] = "not applicable"

            r["temporal_leakage"] = "no"
            r["citation_check"] = "authentic and supports proposition"
            r["source_citation_or_url"] = "123 U.S. 456"
            r["supporting_excerpt"] = "Excerpt text"
            r["assessment_rationale"] = "Valid rationale for test"
            r["assessor_identity"] = "Assessor"
            r["timestamp"] = "2026-10-08T22:00:00Z"

        dict_a1 = {r["assessment_id"]: r for r in a1_recs}
        dict_a2 = {r["assessment_id"]: r for r in a2_recs}

        unique_items_dict = {}
        for aid, meta in mapping["assessments"].items():
            key = (meta["query_id"], meta["condition"], meta["pipeline"])
            if key not in unique_items_dict:
                unique_items_dict[key] = {
                    "unique_key": key,
                    "meta": meta,
                    "author_1_eval": None,
                    "author_2_eval": None
                }
            if meta["assigned_author"] == "author_1":
                unique_items_dict[key]["author_1_eval"] = dict_a1.get(aid)
            elif meta["assigned_author"] == "author_2":
                unique_items_dict[key]["author_2_eval"] = dict_a2.get(aid)

        metrics = compute_population_metrics(list(unique_items_dict.values()))
        can_stats = metrics["canonical_usefulness_sample"]

        # Assert breakdown
        self.assertEqual(can_stats["pure_substantive_count"], 20)
        self.assertEqual(can_stats["mixed_refusal_substantive_count"], 10)
        self.assertEqual(can_stats["total_substantive_coverage_count"], 30)
        self.assertEqual(can_stats["pure_refusal_count"], 8)
        self.assertEqual(can_stats["unusable_output_count"], 2)

        # Proportions
        self.assertEqual(can_stats["pure_substantive_proportion"], 0.5)
        self.assertEqual(can_stats["mixed_refusal_substantive_proportion"], 0.25)
        self.assertEqual(can_stats["total_substantive_coverage_proportion"], 0.75)

        # Strict supported and responsive yields (Finding 5)
        self.assertEqual(can_stats["strict_supported_and_responsive_pure_count"], 20)
        self.assertEqual(can_stats["strict_supported_and_responsive_yield_pure"], 0.5)
        self.assertEqual(can_stats["strict_supported_and_responsive_all_substantive_count"], 25)
        self.assertEqual(can_stats["strict_supported_and_responsive_yield_all_substantive"], 0.625)

        # Broad supported and responsive
        self.assertEqual(can_stats["broad_supported_and_responsive_yield_all"], 0.625)

        # Contradicted error rates
        self.assertEqual(can_stats["contradicted_among_pure_substantive"], 0.0)
        self.assertAlmostEqual(can_stats["contradicted_among_all_substantive"], 0.1667, places=3)

        # Legal disclaimer present
        self.assertIn("legal_status_caveat", can_stats)

    def test_12_cohens_kappa_zero_variance(self):
        """Verifies compute_cohens_kappa returns UNDEFINED on constant ratings and float when varying."""
        r1 = ["supported"] * 20
        r2 = ["supported"] * 20
        kappa = compute_cohens_kappa(r1, r2)
        self.assertIn("UNDEFINED", str(kappa))

        r1_var = ["supported"] * 10 + ["contradicted"] * 10
        r2_var = ["supported"] * 12 + ["contradicted"] * 8
        kappa_var = compute_cohens_kappa(r1_var, r2_var)
        self.assertIsInstance(kappa_var, float)
        self.assertGreater(kappa_var, 0.5)

    def test_13_cli_execution_and_integrity_manifest(self):
        """End-to-end CLI test: runs prepare CLI with test-fixture-mode, populates workbooks, runs process CLI, verifies manifest and preserved originals."""
        # 1. Run prepare_author_assessment_workbooks.py CLI in test-fixture-mode
        prep_script = ROOT_DIR / "scripts" / "prepare_author_assessment_workbooks.py"
        prep_cmd = [
            sys.executable,
            str(prep_script),
            "--temporal-input", str(self.temp_path),
            "--canonical-input", str(self.can_path),
            "--output-dir", str(self.output_dir),
            "--seed", "20261008",
            "--test-fixture-mode"
        ]
        prep_res = subprocess.run(prep_cmd, capture_output=True, text=True)
        self.assertEqual(prep_res.returncode, 0, f"Prepare CLI failed:\n{prep_res.stderr}\n{prep_res.stdout}")

        # Check prepare manifest
        prep_manifest_path = self.output_dir / "EXTRACTION_MANIFEST.json"
        self.assertTrue(prep_manifest_path.exists())
        with open(prep_manifest_path, "r", encoding="utf-8") as f:
            prep_manifest = json.load(f)
        self.assertEqual(prep_manifest["execution_mode"], "SYNTHETIC_TEST_FIXTURE_NON_PRODUCTION")
        self.assertFalse(prep_manifest["certified_for_production"])

        # Negative test: Running prepare CLI WITHOUT --test-fixture-mode on synthetic non-pinned data fails immediately (Finding 4)
        unpinned_dir = self.test_dir / "unpinned_output_should_fail"
        fail_cmd = [
            sys.executable,
            str(prep_script),
            "--temporal-input", str(self.temp_path),
            "--canonical-input", str(self.can_path),
            "--output-dir", str(unpinned_dir)
        ]
        fail_res = subprocess.run(fail_cmd, capture_output=True, text=True)
        self.assertNotEqual(fail_res.returncode, 0, "Prepare CLI must reject synthetic unpinned input without --test-fixture-mode")

        # Verify companion HTML and TXT exist
        self.assertTrue((self.output_dir / "READING_VIEW_AUTHOR_1.html").exists())
        self.assertTrue((self.output_dir / "READING_VIEW_AUTHOR_2.html").exists())
        self.assertTrue((self.output_dir / "READING_VIEW_AUTHOR_1.txt").exists())
        self.assertTrue((self.output_dir / "READING_VIEW_AUTHOR_2.txt").exists())

        # 2. Populate the workbooks
        mapping_path = self.output_dir / "PRIVATE_KEY_MAPPING.json"
        auth1_xlsx = self.output_dir / "ASSESSMENT_AUTHOR_1.xlsx"
        auth2_xlsx = self.output_dir / "ASSESSMENT_AUTHOR_2.xlsx"

        for pth, author_tag in [(auth1_xlsx, "Author 1"), (auth2_xlsx, "Author 2")]:
            wb = openpyxl.load_workbook(pth)
            ws = wb["Assessments"]
            for row in range(2, ws.max_row + 1):
                ws.cell(row, 7, value="substantive answer")
                ws.cell(row, 8, value="supported")
                ws.cell(row, 9, value="no")
                ws.cell(row, 10, value="addresses requested issue")
                ws.cell(row, 11, value="authentic and supports proposition")
                ws.cell(row, 12, value="not applicable")
                ws.cell(row, 13, value="123 U.S. 456 (1887)")
                ws.cell(row, 14, value="Court held that doctrine applies.")
                ws.cell(row, 15, value=f"Valid assessment rationale by {author_tag}.")
                ws.cell(row, 16, value=author_tag)
                ws.cell(row, 17, value="2026-10-08T22:00:00Z")
            wb.save(pth)

        # 3. Run process_author_assessments.py CLI
        proc_script = ROOT_DIR / "scripts" / "process_author_assessments.py"
        final_dir = self.test_dir / "final_processed_output"

        proc_cmd = [
            sys.executable,
            str(proc_script),
            "--author1-input", str(auth1_xlsx),
            "--author2-input", str(auth2_xlsx),
            "--mapping", str(mapping_path),
            "--output-dir", str(final_dir)
        ]
        proc_res = subprocess.run(proc_cmd, capture_output=True, text=True)
        self.assertEqual(proc_res.returncode, 0, f"Process CLI failed:\n{proc_res.stderr}\n{proc_res.stdout}")

        # 4. Verify integrity manifest, preserved originals, and output files
        manifest_path = final_dir / "EXECUTION_INTEGRITY_MANIFEST.json"
        self.assertTrue(manifest_path.exists())
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        self.assertEqual(manifest_data["status"], "COMPLETED_AND_VERIFIED")
        self.assertTrue(manifest_data["certified_for_production"])
        self.assertIn("author1_workbook", manifest_data["input_files"])
        self.assertIn("author2_workbook", manifest_data["input_files"])
        self.assertIn("private_mapping", manifest_data["input_files"])

        # Preserved originals check (Finding 2 - role-separated)
        pres_dir = final_dir / "preserved_originals"
        self.assertTrue(pres_dir.exists())
        self.assertTrue((pres_dir / "author_1" / auth1_xlsx.name).exists())
        self.assertTrue((pres_dir / "author_2" / auth2_xlsx.name).exists())
        self.assertTrue((pres_dir / "mapping" / mapping_path.name).exists())
        self.assertIn("author_1", manifest_data["preserved_originals"])
        self.assertIn("author_2", manifest_data["preserved_originals"])
        self.assertIn("mapping", manifest_data["preserved_originals"])
        self.assertEqual(manifest_data["preserved_originals"]["author_1"]["filename"], auth1_xlsx.name)

        # Check output artifacts
        self.assertTrue((final_dir / "merged_author_assessments.json").exists())
        self.assertTrue((final_dir / "assessment_statistical_summary.json").exists())
        self.assertTrue((final_dir / "WORKBOOK_COMPLETION_REPORT.json").exists())

    def test_14_exact_boolean_schema_validation(self):
        """Verifies exact boolean type validation (Finding 6) rejects numeric 0/1 and string booleans."""
        # 1. compute_population_metrics rejects numeric 0 or 1 in automated_baseline
        sample_item = {
            "meta": {
                "sample_stratum": "temporal_stage_a",
                "cluster_id": "test_cid",
                "as_of_cutoff_year": 1950,
                "query_id": "q1",
                "is_overlap": False,
                "primary_author": "author_1",
                "automated_baseline": {"sptlr_level2": 0}  # Numeric 0 instead of exact bool
            },
            "author_1_eval": {"temporal_leakage": "no"},
            "author_2_eval": None
        }
        with self.assertRaises(ValueError):
            compute_population_metrics([sample_item] * 80)

        # 2. String boolean "True" rejected
        sample_item["meta"]["automated_baseline"]["sptlr_level2"] = "True"
        with self.assertRaises(ValueError):
            compute_population_metrics([sample_item] * 80)

        # 3. validate_cohorts_and_schemas rejects numeric 0/1 in temporal records
        with open(self.temp_path, "r", encoding="utf-8") as f:
            temp_records = json.load(f)
        with open(self.can_path, "r", encoding="utf-8") as f:
            can_records = json.load(f)

        corrupt_temp = json.loads(json.dumps(temp_records))
        corrupt_temp[0]["sptlr_level2"] = 1  # Numeric 1 instead of True
        with self.assertRaises(ValueError):
            validate_cohorts_and_schemas(corrupt_temp, can_records)

        # 4. validate_cohorts_and_schemas rejects numeric 0 in canonical safety_rejected
        corrupt_can = json.loads(json.dumps(can_records))
        corrupt_can[0]["safety_rejected"] = 0  # Numeric 0 instead of False
        with self.assertRaises(ValueError):
            validate_cohorts_and_schemas(temp_records, corrupt_can)

    def test_15_processor_lifecycle_failure_paths(self):
        """Verifies processor unconditional lifecycle: failure and incomplete states write manifests without provisional metrics (Finding 3)."""
        run_pipeline(
            self.temp_path, self.can_path, self.output_dir, seed=20261008,
            test_fixture_mode=True
        )

        mapping_path = self.output_dir / "PRIVATE_KEY_MAPPING.json"
        auth1_xlsx = self.output_dir / "ASSESSMENT_AUTHOR_1.xlsx"
        auth2_xlsx = self.output_dir / "ASSESSMENT_AUTHOR_2.xlsx"
        proc_script = ROOT_DIR / "scripts" / "process_author_assessments.py"

        # Failure Path A: Incomplete / unpopulated workbooks
        inc_dir = self.test_dir / "incomplete_test_output"
        cmd_inc = [
            sys.executable,
            str(proc_script),
            "--author1-input", str(auth1_xlsx),
            "--author2-input", str(auth2_xlsx),
            "--mapping", str(mapping_path),
            "--output-dir", str(inc_dir)
        ]
        res_inc = subprocess.run(cmd_inc, capture_output=True, text=True)
        self.assertEqual(res_inc.returncode, 2, "Incomplete workbook must exit with code 2")

        # Manifest must exist and record INCOMPLETE
        inc_manifest_path = inc_dir / "EXECUTION_INTEGRITY_MANIFEST.json"
        self.assertTrue(inc_manifest_path.exists())
        with open(inc_manifest_path, "r", encoding="utf-8") as f:
            inc_manifest = json.load(f)
        self.assertEqual(inc_manifest["status"], "INCOMPLETE")
        self.assertFalse(inc_manifest["certified_for_production"])

        # Preserved originals must be present in role directory
        self.assertTrue((inc_dir / "preserved_originals" / "author_1" / auth1_xlsx.name).exists())

        # Substantive metrics files must NOT exist
        self.assertFalse((inc_dir / "merged_author_assessments.json").exists())
        self.assertFalse((inc_dir / "assessment_statistical_summary.json").exists())

        # Failure Path B: Tampered workbook (altered cutoff year)
        tampered_auth1 = self.test_dir / "tampered_author_1.xlsx"
        shutil.copy2(auth1_xlsx, tampered_auth1)
        wb = openpyxl.load_workbook(tampered_auth1)
        ws = wb["Assessments"]
        cutoff_col = None
        for col in range(1, ws.max_column + 1):
            if "cutoff" in str(ws.cell(1, col).value).lower():
                cutoff_col = col
                break
        self.assertIsNotNone(cutoff_col)
        ws.cell(2, cutoff_col, value="As-of Year: 9999")
        wb.save(tampered_auth1)

        tamp_dir = self.test_dir / "tampered_test_output"
        cmd_tamp = [
            sys.executable,
            str(proc_script),
            "--author1-input", str(tampered_auth1),
            "--author2-input", str(auth2_xlsx),
            "--mapping", str(mapping_path),
            "--output-dir", str(tamp_dir)
        ]
        res_tamp = subprocess.run(cmd_tamp, capture_output=True, text=True)
        self.assertEqual(res_tamp.returncode, 3, "Tampered workbook must exit with code 3")

        tamp_manifest_path = tamp_dir / "EXECUTION_INTEGRITY_MANIFEST.json"
        self.assertTrue(tamp_manifest_path.exists())
        with open(tamp_manifest_path, "r", encoding="utf-8") as f:
            tamp_manifest = json.load(f)
        self.assertEqual(tamp_manifest["status"], "FAILED")
        self.assertFalse(tamp_manifest["certified_for_production"])
        self.assertIn("Tampering detected", tamp_manifest["error_info"])

        # Metrics files must NOT exist
        self.assertFalse((tamp_dir / "merged_author_assessments.json").exists())
        self.assertFalse((tamp_dir / "assessment_statistical_summary.json").exists())

    def _populate_workbooks(self, auth1_xlsx: Path, auth2_xlsx: Path):
        """Helper to populate valid rubric judgments across all item rows."""
        for pth, author_tag in [(auth1_xlsx, "Author 1"), (auth2_xlsx, "Author 2")]:
            wb = openpyxl.load_workbook(pth)
            ws = wb["Assessments"]
            for row in range(2, ws.max_row + 1):
                ws.cell(row, 7, value="substantive answer")
                ws.cell(row, 8, value="supported")
                ws.cell(row, 9, value="no")
                ws.cell(row, 10, value="addresses requested issue")
                ws.cell(row, 11, value="authentic and supports proposition")
                ws.cell(row, 12, value="not applicable")
                ws.cell(row, 13, value="123 U.S. 456 (1887)")
                ws.cell(row, 14, value="Court held that doctrine applies.")
                ws.cell(row, 15, value=f"Valid assessment rationale by {author_tag}.")
                ws.cell(row, 16, value=author_tag)
                ws.cell(row, 17, value="2026-10-08T22:00:00Z")
            wb.save(pth)

    def test_16_terminal_hash_governs_terminal_status(self):
        """Verifies terminal hashes govern terminal status and force failure/nonzero exit (Finding 1)."""
        # 1. Prepare tool: Terminal hash mutation forces FAILED_INPUT_MUTATION and raises
        out_prep_drift = self.test_dir / "prep_terminal_drift_out"
        real_prep_sha = prep_module.compute_sha256

        prep_drift_calls = {"count": 0}
        def drifting_prep_sha(p):
            res = real_prep_sha(p)
            if str(p) == str(self.temp_path.resolve()) or str(p) == str(self.temp_path):
                prep_drift_calls["count"] += 1
                if prep_drift_calls["count"] >= 3:
                    return "mutated_prep_terminal_hash"
            return res

        with unittest.mock.patch.object(prep_module, "compute_sha256", side_effect=drifting_prep_sha):
            with self.assertRaises(prep_module.HashVerificationError):
                run_pipeline(self.temp_path, self.can_path, out_prep_drift, test_fixture_mode=True)

        manifest_file = out_prep_drift / "EXTRACTION_MANIFEST.json"
        self.assertTrue(manifest_file.exists())
        with open(manifest_file, "r", encoding="utf-8") as f:
            m = json.load(f)
        self.assertEqual(m["status"], "FAILED_INPUT_MUTATION")
        self.assertFalse(m["certified_for_production"])
        self.assertEqual(m["inputs"]["terminal_temporal_sha256"], "mutated_prep_terminal_hash")
        self.assertIn("Terminal hash drift detected", m["error_info"])

        # CLI test for prepare terminal drift (must return non-zero)
        cli_prep_drift_code = (
            "import sys\n"
            "from pathlib import Path\n"
            "import scripts.prepare_author_assessment_workbooks as m\n"
            "orig = m.compute_sha256\n"
            "cnt = [0]\n"
            "def drifted(p):\n"
            "    r = orig(p)\n"
            "    if 'temporal' in str(p):\n"
            "        cnt[0] += 1\n"
            "        if cnt[0] >= 3: return 'drifted_sha'\n"
            "    return r\n"
            "m.compute_sha256 = drifted\n"
            "sys.argv = ['prep', '--temporal-input', sys.argv[1], '--canonical-input', sys.argv[2], '--output-dir', sys.argv[3], '--test-fixture-mode']\n"
            "m.main()\n"
        )
        prep_cli_drift_dir = self.test_dir / "prep_cli_drift_out"
        res_prep_cli = subprocess.run([
            sys.executable, "-c", cli_prep_drift_code,
            str(self.temp_path), str(self.can_path), str(prep_cli_drift_dir)
        ], capture_output=True, text=True)
        self.assertNotEqual(res_prep_cli.returncode, 0, "Prepare CLI must exit non-zero on terminal drift")
        with open(prep_cli_drift_dir / "EXTRACTION_MANIFEST.json", "r", encoding="utf-8") as f:
            m_cli = json.load(f)
        self.assertEqual(m_cli["status"], "FAILED_INPUT_MUTATION")
        self.assertFalse(m_cli["certified_for_production"])

        # 2. Prepare tool: Final hash read raises exception (status FAILED, certified False)
        out_prep_exc = self.test_dir / "prep_terminal_exc_out"
        prep_exc_calls = {"count": 0}
        def raising_prep_sha(p):
            if str(p) == str(self.temp_path.resolve()) or str(p) == str(self.temp_path):
                prep_exc_calls["count"] += 1
                if prep_exc_calls["count"] >= 3:
                    raise PermissionError("Simulated locked file on terminal read")
            return real_prep_sha(p)

        with unittest.mock.patch.object(prep_module, "compute_sha256", side_effect=raising_prep_sha):
            with self.assertRaises(RuntimeError):
                run_pipeline(self.temp_path, self.can_path, out_prep_exc, test_fixture_mode=True)

        with open(out_prep_exc / "EXTRACTION_MANIFEST.json", "r", encoding="utf-8") as f:
            m_exc = json.load(f)
        self.assertEqual(m_exc["status"], "FAILED")
        self.assertFalse(m_exc["certified_for_production"])
        self.assertEqual(m_exc["inputs"]["terminal_temporal_sha256"], "UNAVAILABLE")
        self.assertIn("PermissionError", m_exc["error_info"])

        # 3. Process tool setup: Generate and populate valid workbooks
        prep_out = self.test_dir / "prep_for_proc_terminal_tests"
        run_pipeline(self.temp_path, self.can_path, prep_out, test_fixture_mode=True)
        auth1_file = prep_out / "ASSESSMENT_AUTHOR_1.xlsx"
        auth2_file = prep_out / "ASSESSMENT_AUTHOR_2.xlsx"
        mapping_file = prep_out / "PRIVATE_KEY_MAPPING.json"
        self._populate_workbooks(auth1_file, auth2_file)

        # 4. Process tool: Terminal hash mutation forces FAILED_INPUT_MUTATION and raises
        out_proc_drift = self.test_dir / "proc_terminal_drift_out"
        real_proc_sha = proc_module.compute_sha256

        proc_drift_calls = {"count": 0}
        def drifting_proc_sha(p):
            res = real_proc_sha(p)
            if str(p) == str(auth1_file.resolve()) or str(p) == str(auth1_file):
                proc_drift_calls["count"] += 1
                if proc_drift_calls["count"] >= 4:
                    return "mutated_proc_terminal_hash"
            return res

        with unittest.mock.patch.object(proc_module, "compute_sha256", side_effect=drifting_proc_sha):
            with self.assertRaises(proc_module.HashVerificationError):
                process_author_assessments(auth1_file, auth2_file, mapping_file, out_proc_drift)

        with open(out_proc_drift / "EXECUTION_INTEGRITY_MANIFEST.json", "r", encoding="utf-8") as f:
            pm = json.load(f)
        self.assertEqual(pm["status"], "FAILED_INPUT_MUTATION")
        self.assertFalse(pm["certified_for_production"])
        self.assertEqual(pm["input_files"]["author1_workbook"]["terminal_sha256"], "mutated_proc_terminal_hash")
        self.assertTrue(pm["input_files"]["author1_workbook"]["mutated"])

        # CLI test for process terminal drift (must return code 4)
        proc_cli_drift_code = (
            "import sys\n"
            "from pathlib import Path\n"
            "import scripts.process_author_assessments as m\n"
            "orig = m.compute_sha256\n"
            "cnt = [0]\n"
            "def drifted(p):\n"
            "    r = orig(p)\n"
            "    if 'AUTHOR_1' in str(p) or 'author_1' in str(p):\n"
            "        cnt[0] += 1\n"
            "        if cnt[0] >= 4: return 'drifted_proc_sha'\n"
            "    return r\n"
            "m.compute_sha256 = drifted\n"
            "sys.argv = ['proc', '--author1-input', sys.argv[1], '--author2-input', sys.argv[2], '--mapping', sys.argv[3], '--output-dir', sys.argv[4]]\n"
            "m.main()\n"
        )
        proc_cli_drift_dir = self.test_dir / "proc_cli_drift_out"
        res_proc_cli = subprocess.run([
            sys.executable, "-c", proc_cli_drift_code,
            str(auth1_file), str(auth2_file), str(mapping_file), str(proc_cli_drift_dir)
        ], capture_output=True, text=True)
        self.assertEqual(res_proc_cli.returncode, 4, "Process CLI must exit code 4 on terminal drift")
        with open(proc_cli_drift_dir / "EXECUTION_INTEGRITY_MANIFEST.json", "r", encoding="utf-8") as f:
            pm_cli = json.load(f)
        self.assertEqual(pm_cli["status"], "FAILED_INPUT_MUTATION")
        self.assertFalse(pm_cli["certified_for_production"])

        # 5. Process tool: Final hash read raises exception (status FAILED, certified False)
        out_proc_exc = self.test_dir / "proc_terminal_exc_out"
        proc_exc_calls = {"count": 0}
        def raising_proc_sha(p):
            if str(p) == str(auth1_file.resolve()) or str(p) == str(auth1_file):
                proc_exc_calls["count"] += 1
                if proc_exc_calls["count"] >= 4:
                    raise OSError("Simulated terminal file read I/O error")
            return real_proc_sha(p)

        with unittest.mock.patch.object(proc_module, "compute_sha256", side_effect=raising_proc_sha):
            with self.assertRaises(RuntimeError):
                process_author_assessments(auth1_file, auth2_file, mapping_file, out_proc_exc)

        with open(out_proc_exc / "EXECUTION_INTEGRITY_MANIFEST.json", "r", encoding="utf-8") as f:
            pm_exc = json.load(f)
        self.assertEqual(pm_exc["status"], "FAILED")
        self.assertFalse(pm_exc["certified_for_production"])
        self.assertEqual(pm_exc["input_files"]["author1_workbook"]["terminal_sha256"], "UNAVAILABLE")
        self.assertIn("Simulated terminal file read I/O error", pm_exc["error_info"])

    def test_17_role_separated_preservation_and_same_basename(self):
        """Verifies role-separated guarded preservation, identical basename survival, and corruption prevention (Finding 2)."""
        prep_out = self.test_dir / "prep_for_preservation_tests"
        run_pipeline(self.temp_path, self.can_path, prep_out, test_fixture_mode=True)
        auth1_file = prep_out / "ASSESSMENT_AUTHOR_1.xlsx"
        auth2_file = prep_out / "ASSESSMENT_AUTHOR_2.xlsx"
        mapping_file = prep_out / "PRIVATE_KEY_MAPPING.json"
        self._populate_workbooks(auth1_file, auth2_file)

        # 1. Both authors return files with IDENTICAL basenames from different folders
        folder1 = self.test_dir / "user_returned_folder"
        folder2 = self.test_dir / "coauthor_returned_folder"
        folder1.mkdir()
        folder2.mkdir()
        same_name1 = folder1 / "assessment.xlsx"
        same_name2 = folder2 / "assessment.xlsx"
        shutil.copy2(auth1_file, same_name1)
        shutil.copy2(auth2_file, same_name2)

        out_same_name = self.test_dir / "same_name_processed_output"
        process_author_assessments(same_name1, same_name2, mapping_file, out_same_name)

        # Verify role-separated preservation preserved BOTH files without overwriting
        pres_dir = out_same_name / "preserved_originals"
        pres_a1 = pres_dir / "author_1" / "assessment.xlsx"
        pres_a2 = pres_dir / "author_2" / "assessment.xlsx"
        pres_map = pres_dir / "mapping" / mapping_file.name

        self.assertTrue(pres_a1.exists())
        self.assertTrue(pres_a2.exists())
        self.assertTrue(pres_map.exists())

        # Check hashes match their distinct source files
        h_a1 = proc_module.compute_sha256(same_name1)
        h_a2 = proc_module.compute_sha256(same_name2)
        self.assertEqual(proc_module.compute_sha256(pres_a1), h_a1)
        self.assertEqual(proc_module.compute_sha256(pres_a2), h_a2)
        self.assertNotEqual(h_a1, h_a2, "Author 1 and Author 2 files have distinct content and hashes")

        # Verify manifest dictionary has separate role entries without collapsing
        with open(out_same_name / "EXECUTION_INTEGRITY_MANIFEST.json", "r", encoding="utf-8") as f:
            m_same = json.load(f)
        self.assertEqual(m_same["status"], "COMPLETED_AND_VERIFIED")
        self.assertTrue(m_same["certified_for_production"])
        self.assertIn("author_1", m_same["preserved_originals"])
        self.assertIn("author_2", m_same["preserved_originals"])
        self.assertIn("mapping", m_same["preserved_originals"])
        self.assertEqual(m_same["preserved_originals"]["author_1"]["sha256"], h_a1)
        self.assertEqual(m_same["preserved_originals"]["author_2"]["sha256"], h_a2)

        # 2. Preservation copy failure: terminal failure record written in output directory
        out_pres_fail = self.test_dir / "preservation_copy_fail_output"
        def failing_copy(src, dst):
            if "author_2" in str(dst):
                raise IOError("Simulated permission denied or disk error during copy")
            return shutil.copyfile(src, dst)

        with unittest.mock.patch("shutil.copy2", side_effect=failing_copy):
            with self.assertRaises(IOError):
                process_author_assessments(same_name1, same_name2, mapping_file, out_pres_fail)

        self.assertTrue((out_pres_fail / "EXECUTION_INTEGRITY_MANIFEST.json").exists())
        with open(out_pres_fail / "EXECUTION_INTEGRITY_MANIFEST.json", "r", encoding="utf-8") as f:
            m_fail = json.load(f)
        self.assertEqual(m_fail["status"], "FAILED")
        self.assertFalse(m_fail["certified_for_production"])
        self.assertIn("Simulated permission denied", m_fail["error_info"])
        # No metrics files generated
        self.assertFalse((out_pres_fail / "merged_author_assessments.json").exists())
        self.assertFalse((out_pres_fail / "assessment_statistical_summary.json").exists())

        # 3. Corrupted preserved copy halts processing immediately before analysis
        out_corrupt_copy = self.test_dir / "corrupted_copy_output"
        def corrupting_copy(src, dst):
            shutil.copyfile(src, dst)
            if "author_1" in str(dst):
                with open(dst, "ab") as f:
                    f.write(b"CORRUPTED_BYTES_IN_COPY")

        with unittest.mock.patch("shutil.copy2", side_effect=corrupting_copy):
            with self.assertRaises(proc_module.HashVerificationError):
                process_author_assessments(same_name1, same_name2, mapping_file, out_corrupt_copy)

        self.assertTrue((out_corrupt_copy / "EXECUTION_INTEGRITY_MANIFEST.json").exists())
        with open(out_corrupt_copy / "EXECUTION_INTEGRITY_MANIFEST.json", "r", encoding="utf-8") as f:
            m_corr = json.load(f)
        self.assertEqual(m_corr["status"], "FAILED_INPUT_MUTATION")
        self.assertFalse(m_corr["certified_for_production"])
        self.assertIn("Preserved copy corrupted", m_corr["error_info"])
        # No metrics files generated
        self.assertFalse((out_corrupt_copy / "merged_author_assessments.json").exists())
        self.assertFalse((out_corrupt_copy / "assessment_statistical_summary.json").exists())

    def test_18_manifest_write_failure_and_sentinel_protection(self):
        """Verifies manifest write failure forces failure/nonzero exit, exclusive creation, and unchanged sentinel bytes (CODE_AUDIT_05)."""
        # 1. Prepare tool: Write failure forces RuntimeError and CLI nonzero exit with no [OK]
        out_prep_fail = self.test_dir / "prep_manifest_write_fail_out"
        orig_open = open
        def failing_prep_open(file, *args, **kwargs):
            if "EXTRACTION_MANIFEST.json" in str(file):
                raise IOError("Simulated disk I/O error writing extraction manifest")
            return orig_open(file, *args, **kwargs)

        with unittest.mock.patch("builtins.open", side_effect=failing_prep_open):
            with self.assertRaises(RuntimeError) as ctx:
                run_pipeline(self.temp_path, self.can_path, out_prep_fail, test_fixture_mode=True)
            self.assertIn("Failed to save final audit manifest", str(ctx.exception))

        # CLI test for prepare tool manifest write failure: assert nonzero exit and no [OK]
        cli_prep_code = (
            "import sys, unittest.mock\n"
            "from pathlib import Path\n"
            "import scripts.prepare_author_assessment_workbooks as m\n"
            "orig_open = open\n"
            "def failing_open(file, *args, **kwargs):\n"
            "    if 'EXTRACTION_MANIFEST.json' in str(file):\n"
            "        raise IOError('Simulated disk I/O error writing extraction manifest')\n"
            "    return orig_open(file, *args, **kwargs)\n"
            "sys.argv = ['prep', '--temporal-input', sys.argv[1], '--canonical-input', sys.argv[2], '--output-dir', sys.argv[3], '--test-fixture-mode']\n"
            "with unittest.mock.patch('builtins.open', side_effect=failing_open):\n"
            "    m.main()\n"
        )
        prep_cli_fail_dir = self.test_dir / "prep_cli_manifest_fail_out"
        res_prep = subprocess.run([
            sys.executable, "-c", cli_prep_code,
            str(self.temp_path), str(self.can_path), str(prep_cli_fail_dir)
        ], capture_output=True, text=True)
        self.assertNotEqual(res_prep.returncode, 0, "Prepare CLI must exit nonzero when manifest write fails")
        self.assertNotIn("[OK]", res_prep.stdout, "Success message must never be printed when manifest write fails")
        self.assertIn("Failed to save final audit manifest", res_prep.stderr)

        # 2. Prepare tool: Sentinel precreation during mocked lifecycle forces FileExistsError/RuntimeError and preserves sentinel bytes
        out_prep_sentinel = self.test_dir / "prep_sentinel_out"
        SENTINEL_PREP_BYTES = b"ORIGINAL_EXTRACTION_MANIFEST_SENTINEL_BYTES_PRESERVED_123"

        orig_export_txt = prep_module.export_txt_reading_view
        def hooked_export_txt(*args, **kwargs):
            # Lifecycle hook: precreate sentinel file right before finalization
            s_file = out_prep_sentinel / "EXTRACTION_MANIFEST.json"
            s_file.write_bytes(SENTINEL_PREP_BYTES)
            return orig_export_txt(*args, **kwargs)

        with unittest.mock.patch.object(prep_module, "export_txt_reading_view", side_effect=hooked_export_txt):
            with self.assertRaises(RuntimeError) as ctx:
                run_pipeline(self.temp_path, self.can_path, out_prep_sentinel, test_fixture_mode=True)
            self.assertIn("Failed to save final audit manifest", str(ctx.exception))

        sentinel_prep_file = out_prep_sentinel / "EXTRACTION_MANIFEST.json"
        self.assertTrue(sentinel_prep_file.exists())
        self.assertEqual(
            sentinel_prep_file.read_bytes(), SENTINEL_PREP_BYTES,
            "Exclusive creation must leave pre-existing sentinel manifest bytes 100% unchanged"
        )

        # 3. Process tool setup: Generate and populate valid workbooks
        prep_out = self.test_dir / "prep_for_proc_manifest_tests"
        run_pipeline(self.temp_path, self.can_path, prep_out, test_fixture_mode=True)
        auth1_file = prep_out / "ASSESSMENT_AUTHOR_1.xlsx"
        auth2_file = prep_out / "ASSESSMENT_AUTHOR_2.xlsx"
        mapping_file = prep_out / "PRIVATE_KEY_MAPPING.json"
        self._populate_workbooks(auth1_file, auth2_file)

        # 4. Process tool: Write failure forces RuntimeError and CLI nonzero exit with no [OK]
        out_proc_fail = self.test_dir / "proc_manifest_write_fail_out"
        def failing_proc_open(file, *args, **kwargs):
            if "EXECUTION_INTEGRITY_MANIFEST.json" in str(file):
                raise IOError("Simulated disk I/O error writing integrity manifest")
            return orig_open(file, *args, **kwargs)

        with unittest.mock.patch("builtins.open", side_effect=failing_proc_open):
            with self.assertRaises(RuntimeError) as ctx:
                process_author_assessments(auth1_file, auth2_file, mapping_file, out_proc_fail)
            self.assertIn("Failed to save final audit manifest", str(ctx.exception))

        cli_proc_code = (
            "import sys, unittest.mock\n"
            "from pathlib import Path\n"
            "import scripts.process_author_assessments as m\n"
            "orig_open = open\n"
            "def failing_open(file, *args, **kwargs):\n"
            "    if 'EXECUTION_INTEGRITY_MANIFEST.json' in str(file):\n"
            "        raise IOError('Simulated disk I/O error writing integrity manifest')\n"
            "    return orig_open(file, *args, **kwargs)\n"
            "sys.argv = ['proc', '--author1-input', sys.argv[1], '--author2-input', sys.argv[2], '--mapping', sys.argv[3], '--output-dir', sys.argv[4]]\n"
            "with unittest.mock.patch('builtins.open', side_effect=failing_open):\n"
            "    m.main()\n"
        )
        proc_cli_fail_dir = self.test_dir / "proc_cli_manifest_fail_out"
        res_proc = subprocess.run([
            sys.executable, "-c", cli_proc_code,
            str(auth1_file), str(auth2_file), str(mapping_file), str(proc_cli_fail_dir)
        ], capture_output=True, text=True)
        self.assertNotEqual(res_proc.returncode, 0, "Process CLI must exit nonzero when manifest write fails")
        self.assertNotIn("[OK]", res_proc.stdout, "Success message must never be printed when manifest write fails")
        self.assertIn("Failed to save final audit manifest", res_proc.stderr)

        # 5. Process tool: Sentinel precreation during mocked lifecycle forces FileExistsError/RuntimeError and preserves sentinel bytes
        out_proc_sentinel = self.test_dir / "proc_sentinel_out"
        SENTINEL_PROC_BYTES = b"ORIGINAL_INTEGRITY_MANIFEST_SENTINEL_BYTES_PRESERVED_456"

        orig_compute_pop = proc_module.compute_population_metrics
        def hooked_compute_pop(*args, **kwargs):
            # Lifecycle hook: precreate sentinel file right before finalization
            s_file = out_proc_sentinel / "EXECUTION_INTEGRITY_MANIFEST.json"
            s_file.write_bytes(SENTINEL_PROC_BYTES)
            return orig_compute_pop(*args, **kwargs)

        with unittest.mock.patch.object(proc_module, "compute_population_metrics", side_effect=hooked_compute_pop):
            with self.assertRaises(RuntimeError) as ctx:
                process_author_assessments(auth1_file, auth2_file, mapping_file, out_proc_sentinel)
            self.assertIn("Failed to save final audit manifest", str(ctx.exception))

        sentinel_proc_file = out_proc_sentinel / "EXECUTION_INTEGRITY_MANIFEST.json"
        self.assertTrue(sentinel_proc_file.exists())
        self.assertEqual(
            sentinel_proc_file.read_bytes(), SENTINEL_PROC_BYTES,
            "Exclusive creation must leave pre-existing sentinel manifest bytes 100% unchanged"
        )

        # 6. Preserve original exceptions when one already exists during manifest write failure
        unpopulated_prep = self.test_dir / "prep_unpopulated_for_prior_exc"
        run_pipeline(self.temp_path, self.can_path, unpopulated_prep, test_fixture_mode=True)
        unpop_auth1 = unpopulated_prep / "ASSESSMENT_AUTHOR_1.xlsx"
        unpop_auth2 = unpopulated_prep / "ASSESSMENT_AUTHOR_2.xlsx"
        unpop_map = unpopulated_prep / "PRIVATE_KEY_MAPPING.json"

        cli_inc_fail_code = (
            "import sys, unittest.mock\n"
            "import scripts.process_author_assessments as m\n"
            "orig_open = open\n"
            "def failing_open(file, *args, **kwargs):\n"
            "    if 'EXECUTION_INTEGRITY_MANIFEST.json' in str(file):\n"
            "        raise IOError('Simulated failure during secondary manifest write')\n"
            "    return orig_open(file, *args, **kwargs)\n"
            "sys.argv = ['proc', '--author1-input', sys.argv[1], '--author2-input', sys.argv[2], '--mapping', sys.argv[3], '--output-dir', sys.argv[4]]\n"
            "with unittest.mock.patch('builtins.open', side_effect=failing_open):\n"
            "    m.main()\n"
        )
        proc_cli_inc_dir = self.test_dir / "proc_cli_inc_manifest_fail_out"
        res_inc = subprocess.run([
            sys.executable, "-c", cli_inc_fail_code,
            str(unpop_auth1), str(unpop_auth2), str(unpop_map), str(proc_cli_inc_dir)
        ], capture_output=True, text=True)
        self.assertEqual(
            res_inc.returncode, 2,
            "Original WorkbookIncompleteError exit code (2) must be preserved when secondary manifest write fails"
        )


if __name__ == "__main__":
    unittest.main()

