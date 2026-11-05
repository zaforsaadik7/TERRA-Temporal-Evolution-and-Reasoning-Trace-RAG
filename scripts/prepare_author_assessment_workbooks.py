#!/usr/bin/env python3
"""
scripts/prepare_author_assessment_workbooks.py (v2 - Hardened)
=============================================================
Prepares two self-contained, blinded assessment workbooks for prospective
non-expert source-grounded review of temporal leakage and answer usefulness:
  - ASSESSMENT_AUTHOR_1.xlsx / .tsv (User / Lead Author)
  - ASSESSMENT_AUTHOR_2.xlsx / .tsv (Co-author)
  - PRIVATE_KEY_MAPPING.json (Kept strictly outside author workbooks)
  - EXTRACTION_MANIFEST.json (Audit trail with input/output SHA-256 hashes)

Implements PROTOCOL_DRAFT_01, TWO_ASSESSOR_ADDENDUM_01, and CODE_AUDIT_01 repairs:
  1. Full 400-grid temporal validation (50 queries, 5 cutoffs, 2 conditions, 4 pipelines)
     and 1,750-record canonical multi-pipeline validation with composite-key duplicate detection.
  2. Stage B Simple Random Sampling (SRS) drawn FIRST from ALL 350 5_Full_TERRA records
     with exact inclusion probability p = 40/350. Adverse cases (e.g. D033/D034) are
     not removed if sampled, and are flagged privately as diagnostic case studies.
  3. Diagnostic Appendix drawn from remaining records (up to 12 targeted failure modes).
  4. Stratified, randomized primary author allocation across categories/cutoffs to eliminate
     assessor/category confounding.
  5. Randomized pipeline presentation order within each temporal cluster so row position
     cannot reveal pipeline identity.
  6. Shuffled workbook presentation order so overlap and diagnostic records are not grouped
     in identifiable blocks. Blinded presentation removes diagnostic labeling.
  7. Escape spreadsheet formulas ('=', '+', '-', '@') to prevent formula injection.
  8. Comfortable reading layout with dynamic row heights, wrapped text, and a dedicated
     Detailed_Reading_View tab for full query/response reading without clipping.
  9. Comprehensive semantic rubric and two-pass workflow instructions.
 10. Private key mapping retains original automated labels (sptlr_level2, consensus severity,
     refusal flags) for subsequent valid FNR and false omission calculation.
 11. Strictly requires a fresh, non-existent output directory.
 12. Input SHA-256 hashes verified before and after the complete lifecycle.
"""

import os
import sys
import json
import csv
import random
import hashlib
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class BlindingSecurityError(Exception):
    """Raised when blinded fields or identifying tags leak into author files."""
    pass


class HashVerificationError(Exception):
    """Raised when input file hashes drift or fail verification."""
    pass


# Production Pinned SHA-256 Hashes
PINNED_HASHES = {
    "temporal": "ae6726d970d10237cccd0b508031297f09c836987dc515973595e0754d842a22",
    "canonical": "95e775e29c3a0d95f3cb35aa9d50a5f030d04b51d3f2175848db2f2b57aad507"
}

# Cohort constants
TEMPORAL_CUTOFFS = [1890, 1930, 1950, 1970, 1980]
TEMPORAL_CONDITIONS = ["Condition_A", "Condition_B"]
TEMPORAL_PIPELINES = ["1_Direct_LLM", "2_Flat_Vector_RAG", "TERRA_ungated", "TERRA_gated"]
CANONICAL_TARGET_PIPELINE = "5_Full_TERRA"
CANONICAL_ALL_PIPELINES = [
    "1_Direct_LLM", "2_Flat_Vector_RAG", "3_GraphRAG_Adapted",
    "4_HippoRAG_Adapted", "5_Full_TERRA"
]
CANONICAL_CATEGORIES = {
    "A_Factual": 100,
    "B_Evolutionary": 100,
    "C_OutOfContext": 75,
    "D_Adversarial": 75
}

# Standardized Rubric Definitions & Semantic Guidelines
RUBRIC_DEFINITIONS = {
    "response_status": [
        "substantive answer",
        "refusal",
        "mixed refusal/substantive answer",
        "missing/unusable"
    ],
    "source_grounded_correctness": [
        "supported",
        "contradicted",
        "uncertain",
        "not applicable"
    ],
    "temporal_leakage": [
        "yes",
        "no",
        "uncertain",
        "not applicable"
    ],
    "responsiveness_usefulness": [
        "addresses requested issue",
        "partly addresses",
        "does not address",
        "uncertain"
    ],
    "citation_check": [
        "authentic and supports proposition",
        "authentic but misapplied",
        "cannot locate",
        "no citation/not applicable"
    ],
    "refusal_assessment": [
        "justified",
        "potentially unnecessary",
        "uncertain",
        "not applicable"
    ]
}

# Assessment sheet columns
ASSESSMENT_COLUMNS = [
    ("assessment_id", "Assessment ID", 20, True),
    ("cluster_id", "Cluster Group", 16, True),
    ("task_type", "Task Classification", 24, True),
    ("as_of_cutoff_year", "As-Of Cutoff Year", 18, True),
    ("query_text", "Query / Legal Question", 50, True),
    ("response_text", "System Response (Full Text)", 75, True),
    ("response_status", "Response Status [Select]", 22, False),
    ("source_grounded_correctness", "Source Correctness [Select]", 24, False),
    ("temporal_leakage", "Temporal Leakage [Select]", 22, False),
    ("responsiveness_usefulness", "Responsiveness / Usefulness [Select]", 26, False),
    ("citation_check", "Citation Authenticity [Select]", 26, False),
    ("refusal_assessment", "Refusal Justification [Select]", 24, False),
    ("source_citation_or_url", "Primary Legal Source (Citation / URL / Reporter)", 35, False),
    ("supporting_excerpt", "Supporting Source Excerpt (Verbatim Quote)", 40, False),
    ("assessment_rationale", "Assessment Rationale & Explanation", 40, False),
    ("assessor_identity", "Assessor Name / Role", 20, False),
    ("timestamp", "Timestamp Completed", 22, False)
]


def escape_formula(value: Any) -> str:
    """
    Reversibly escapes leading spreadsheet formula / command trigger characters.
    If string starts with an apostrophe, doubles it (' -> '').
    If string starts with formula triggers (=, +, -, @, \t, \r, \n), prefixes with '.
    """
    if value is None:
        return ""
    s = str(value)
    if s.startswith(("'", "=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + s
    return s


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def verify_file_hash(filepath: Path, expected_hash: Optional[str] = None) -> str:
    """Verifies file exists and computes hash, checking against expected if provided."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required input file does not exist: {filepath}")
    actual_hash = compute_sha256(filepath)
    if expected_hash and actual_hash.lower() != expected_hash.lower():
        raise ValueError(
            f"Hash drift detected for {filepath}!\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}"
        )
    return actual_hash


def load_and_verify_inputs(
    temporal_path: Path,
    canonical_path: Path,
    expected_temp_hash: Optional[str] = PINNED_HASHES["temporal"],
    expected_can_hash: Optional[str] = PINNED_HASHES["canonical"]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, str]]:
    """Loads input JSON files with pre-read SHA-256 verification."""
    pre_hash_temp = verify_file_hash(temporal_path, expected_temp_hash)
    pre_hash_can = verify_file_hash(canonical_path, expected_can_hash)

    with open(temporal_path, "r", encoding="utf-8") as f:
        temporal_data = json.load(f)
    with open(canonical_path, "r", encoding="utf-8") as f:
        canonical_data = json.load(f)

    hashes = {
        "temporal_path": str(temporal_path.resolve()),
        "temporal_sha256": pre_hash_temp,
        "canonical_path": str(canonical_path.resolve()),
        "canonical_sha256": pre_hash_can
    }
    return temporal_data, canonical_data, hashes


def validate_cohorts_and_schemas(
    temporal_data: List[Dict[str, Any]],
    canonical_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Rigorously validates the full 400 temporal grid and 1,750 canonical multi-pipeline records.
    Detects duplicate composite keys, invalid pipelines, missing fields, or cohort drift.
    """
    # 1. Temporal Validation (Full 400 Grid)
    if len(temporal_data) != 400:
        raise ValueError(f"Temporal dataset contains {len(temporal_data)} records; expected exactly 400!")

    temp_records_by_key: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    temp_queries_by_cutoff: Dict[int, Set[str]] = {c: set() for c in TEMPORAL_CUTOFFS}
    temp_query_to_cutoff: Dict[str, int] = {}

    for idx, r in enumerate(temporal_data):
        qid = r.get("query_id")
        cutoff = r.get("cutoff_year")
        cond = r.get("condition")
        pipe = r.get("pipeline")

        if not qid or not isinstance(qid, str):
            raise ValueError(f"Temporal record {idx} has invalid query_id: {qid}")
        if cutoff not in TEMPORAL_CUTOFFS:
            raise ValueError(f"Temporal record {idx} ({qid}) has unexpected cutoff {cutoff}")
        if cond not in TEMPORAL_CONDITIONS:
            raise ValueError(f"Temporal record {idx} ({qid}) has unexpected condition {cond}")
        if pipe not in TEMPORAL_PIPELINES:
            raise ValueError(f"Temporal record {idx} ({qid}) has unexpected pipeline {pipe}")

        # Verify stable query -> cutoff relationship
        if qid in temp_query_to_cutoff and temp_query_to_cutoff[qid] != cutoff:
            raise ValueError(
                f"Query {qid} has conflicting cutoffs: {temp_query_to_cutoff[qid]} vs {cutoff}"
            )
        temp_query_to_cutoff[qid] = cutoff
        temp_queries_by_cutoff[cutoff].add(qid)

        # Composite key duplicate detection
        composite_key = (qid, cond, pipe)
        if composite_key in temp_records_by_key:
            raise ValueError(f"Duplicate composite key detected in temporal dataset: {composite_key}")

        # Validate text fields
        q_text = r.get("query")
        ans_text = r.get("answer_full")
        if not q_text or not isinstance(q_text, str):
            raise ValueError(f"Temporal record {composite_key} missing valid query text")
        if ans_text is None:
            raise ValueError(f"Temporal record {composite_key} has null answer_full")

        # Exact boolean validation on baseline fields (Finding 6)
        sptlr_val = r.get("sptlr_level2")
        if sptlr_val is not None and type(sptlr_val) is not bool:
            raise ValueError(
                f"Temporal record {composite_key} has non-boolean sptlr_level2: "
                f"must be exact bool or null, got {type(sptlr_val).__name__} ({sptlr_val})"
            )
        safe_ref = r.get("is_safe_refusal")
        if safe_ref is not None and type(safe_ref) is not bool:
            raise ValueError(
                f"Temporal record {composite_key} has non-boolean is_safe_refusal: "
                f"must be exact bool or null, got {type(safe_ref).__name__} ({safe_ref})"
            )

        temp_records_by_key[composite_key] = r

    # Check exactly 10 queries per cutoff (50 unique queries total)
    for c, qids in temp_queries_by_cutoff.items():
        if len(qids) != 10:
            raise ValueError(f"Cutoff {c} has {len(qids)} queries; expected exactly 10!")

    if len(temp_query_to_cutoff) != 50:
        raise ValueError(f"Temporal dataset has {len(temp_query_to_cutoff)} queries; expected exactly 50!")

    if len(temp_records_by_key) != 400:
        raise ValueError(f"Temporal grid has {len(temp_records_by_key)} records; expected exactly 400!")

    # 2. Canonical Validation (Multi-pipeline 1,750 records)
    if len(canonical_data) != 1750:
        raise ValueError(f"Canonical dataset has {len(canonical_data)} records; expected exactly 1750!")

    can_records_by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    terra_canonical_records: List[Dict[str, Any]] = []
    category_counts = {cat: 0 for cat in CANONICAL_CATEGORIES}
    pipe_to_qids: Dict[str, Set[str]] = {p: set() for p in CANONICAL_ALL_PIPELINES}

    for idx, r in enumerate(canonical_data):
        qid = r.get("query_id")
        pipe = r.get("pipeline")
        cat = r.get("category")
        q_text = r.get("query")
        ans_text = r.get("answer_full")
        faith = r.get("faithfulness")
        safety_rej = r.get("safety_rejected")

        if not qid or not isinstance(qid, str):
            raise ValueError(f"Canonical record {idx} has invalid query_id: {qid}")
        if pipe not in CANONICAL_ALL_PIPELINES:
            raise ValueError(f"Canonical record {idx} ({qid}) has unexpected pipeline {pipe}")
        if cat not in CANONICAL_CATEGORIES:
            raise ValueError(f"Canonical record {idx} ({qid}) has unexpected category {cat}")
        if not isinstance(q_text, str) or not q_text.strip():
            raise ValueError(f"Canonical record {idx} ({qid}) missing valid query text")
        if ans_text is None or not isinstance(ans_text, str):
            raise ValueError(f"Canonical record {idx} ({qid}) has invalid answer_full")
        if not isinstance(faith, (int, float)):
            raise ValueError(f"Canonical record {idx} ({qid}) has non-numeric faithfulness: {faith}")
        if type(safety_rej) is not bool:
            raise ValueError(f"Canonical record {idx} ({qid}) has non-boolean safety_rejected: {safety_rej}")

        composite_key = (qid, pipe)
        if composite_key in can_records_by_key:
            raise ValueError(f"Duplicate canonical composite key detected: {composite_key}")
        can_records_by_key[composite_key] = r
        pipe_to_qids[pipe].add(qid)

        if pipe == CANONICAL_TARGET_PIPELINE:
            category_counts[cat] += 1
            terra_canonical_records.append(r)

    # Validate target pipeline counts
    if len(terra_canonical_records) != 350:
        raise ValueError(
            f"Found {len(terra_canonical_records)} {CANONICAL_TARGET_PIPELINE} records; expected 350!"
        )
    for cat, exp_count in CANONICAL_CATEGORIES.items():
        if category_counts[cat] != exp_count:
            raise ValueError(
                f"Category {cat} has {category_counts[cat]} records; expected {exp_count}!"
            )

    # Validate that every pipeline evaluates the exact identical universe of 350 query IDs
    target_universe = pipe_to_qids[CANONICAL_TARGET_PIPELINE]
    if len(target_universe) != 350:
        raise ValueError(f"Target pipeline query universe has {len(target_universe)} queries; expected 350!")
    for pipe, qids in pipe_to_qids.items():
        if len(qids) != 350:
            raise ValueError(f"Pipeline {pipe} has {len(qids)} unique queries; expected 350!")
        if qids != target_universe:
            diff = qids.symmetric_difference(target_universe)
            raise ValueError(f"Pipeline {pipe} query universe mismatch with target pipeline! Discrepancy: {diff}")

    return {
        "temp_records_by_key": temp_records_by_key,
        "temp_queries_by_cutoff": {c: sorted(list(q)) for c, q in temp_queries_by_cutoff.items()},
        "temp_query_to_cutoff": temp_query_to_cutoff,
        "terra_canonical_records": terra_canonical_records
    }


def draw_samples_and_allocate(
    cohort_info: Dict[str, Any],
    seed: int = 20261008
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Executes true random sampling and allocation adhering strictly to CODE_AUDIT_01:
      1. Stage B SRS (40 records) drawn FIRST from ALL 350 5_Full_TERRA records.
      2. Stage A Temporal Stratified Cluster Sample (20 clusters, 80 responses).
      3. Diagnostic Appendix drawn from remaining records (up to 12 records).
      4. Balanced primary author allocation across categories and cutoffs.
      5. Randomized pipeline order within each temporal cluster.
      6. Shuffled presentation order in author workbooks.
    """
    rng = random.Random(seed)

    # =========================================================================
    # 1. STAGE B: Canonical Simple Random Sample (SRS of 40 from ALL 350)
    # =========================================================================
    all_can_records = cohort_info["terra_canonical_records"]
    # Sort deterministically before pseudo-random draw
    sorted_all_can = sorted(all_can_records, key=lambda r: r["query_id"])
    sampled_can_srs_records = rng.sample(sorted_all_can, 40)
    sampled_can_srs_qids = set(r["query_id"] for r in sampled_can_srs_records)

    # Stratified balance across categories for Primary Author allocation
    # Group sampled records by category
    srs_by_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in CANONICAL_CATEGORIES}
    for r in sampled_can_srs_records:
        srs_by_cat[r["category"]].append(r)

    auth1_can_primary_raw: List[Dict[str, Any]] = []
    auth2_can_primary_raw: List[Dict[str, Any]] = []
    can_overlap_qids: Set[str] = set()

    for cat in sorted(CANONICAL_CATEGORIES.keys()):
        cat_recs = sorted(srs_by_cat[cat], key=lambda r: r["query_id"])
        rng.shuffle(cat_recs)
        # Split half to Auth 1, half to Auth 2
        split_idx = len(cat_recs) // 2
        a1_recs = cat_recs[:split_idx]
        a2_recs = cat_recs[split_idx:]
        auth1_can_primary_raw.extend(a1_recs)
        auth2_can_primary_raw.extend(a2_recs)

        # Distribute 8 total overlap items across categories (e.g. 2 per category)
        if a1_recs:
            can_overlap_qids.add(a1_recs[0]["query_id"])
        if a2_recs:
            can_overlap_qids.add(a2_recs[0]["query_id"])

    # Ensure exactly 20 primary per author for Stage B
    # If integer division left uneven counts, balance them
    while len(auth1_can_primary_raw) > 20:
        auth2_can_primary_raw.append(auth1_can_primary_raw.pop())
    while len(auth2_can_primary_raw) > 20:
        auth1_can_primary_raw.append(auth2_can_primary_raw.pop())

    # Ensure exactly 8 canonical overlap items
    all_srs_qids_ordered = [r["query_id"] for r in auth1_can_primary_raw + auth2_can_primary_raw]
    while len(can_overlap_qids) < 8:
        for qid in all_srs_qids_ordered:
            if qid not in can_overlap_qids:
                can_overlap_qids.add(qid)
                break
    while len(can_overlap_qids) > 8:
        can_overlap_qids.pop()

    # =========================================================================
    # 2. STAGE A: Temporal Stratified Cluster Sample (20 clusters, 80 responses)
    # =========================================================================
    temp_lookup = cohort_info["temp_records_by_key"]
    sampled_temporal_clusters: List[Dict[str, Any]] = []
    cluster_idx = 1

    auth1_clusters: List[Dict[str, Any]] = []
    auth2_clusters: List[Dict[str, Any]] = []
    temporal_overlap_cluster_ids: Set[str] = set()

    for cutoff in sorted(TEMPORAL_CUTOFFS):
        qids = sorted(cohort_info["temp_queries_by_cutoff"][cutoff])
        # Sample 4 of 10 without replacement
        sampled_qids = sorted(rng.sample(qids, 4))
        rng.shuffle(sampled_qids)

        # Assign 2 to Condition A, 2 to Condition B (balanced)
        cutoff_cluster_dicts = []
        for i, qid in enumerate(sampled_qids):
            cond = "Condition_A" if (i % 2 == 0) else "Condition_B"
            cid = f"CLUST-T{cluster_idx:02d}"
            cluster_idx += 1
            c_dict = {
                "cluster_id": cid,
                "cutoff_year": cutoff,
                "query_id": qid,
                "condition": cond,
                "inclusion_prob": 4.0 / 10.0
            }
            sampled_temporal_clusters.append(c_dict)
            cutoff_cluster_dicts.append(c_dict)

        # Allocate 2 clusters to Auth 1, 2 clusters to Auth 2
        auth1_clusters.extend(cutoff_cluster_dicts[:2])
        auth2_clusters.extend(cutoff_cluster_dicts[2:])

    # Select 2 overlap temporal clusters from different cutoffs (1 from Auth 1, 1 from Auth 2)
    temporal_overlap_cluster_ids.add(auth1_clusters[0]["cluster_id"])
    temporal_overlap_cluster_ids.add(auth2_clusters[2]["cluster_id"])

    # Expand temporal clusters into responses with randomized pipeline presentation order
    def expand_temporal_cluster(cluster_dict: Dict[str, Any], primary_author: str) -> List[Dict[str, Any]]:
        items = []
        qid = cluster_dict["query_id"]
        cond = cluster_dict["condition"]

        # Randomize presentation order of the 4 pipelines within this cluster
        pipes_shuffled = list(TEMPORAL_PIPELINES)
        rng.shuffle(pipes_shuffled)

        for presentation_pos, pipe in enumerate(pipes_shuffled, start=1):
            raw_rec = temp_lookup[(qid, cond, pipe)]
            is_overlap = cluster_dict["cluster_id"] in temporal_overlap_cluster_ids
            items.append({
                "source_dataset": "data/temporal_leakage_dual_judged.json",
                "cluster_id": cluster_dict["cluster_id"],
                "task_type": "Legal Evaluation Task",
                "query_id": qid,
                "condition": cond,
                "pipeline": pipe,
                "pipeline_cluster_pos": presentation_pos,
                "stratum": f"cutoff_{cluster_dict['cutoff_year']}",
                "as_of_cutoff_year": f"As-of Year: {cluster_dict['cutoff_year']}",
                "query_text": str(raw_rec.get("query", "")),
                "response_text": str(raw_rec.get("answer_full") or "[MISSING / EMPTY RESPONSE]"),
                "primary_author": primary_author,
                "is_overlap": is_overlap,
                "sample_stratum": "temporal_stage_a",
                "inclusion_prob": cluster_dict["inclusion_prob"],
                "_automated_baseline": {
                    "sptlr_level2": raw_rec.get("sptlr_level2"),
                    "consensus_severity": (raw_rec.get("adjudication") or {}).get("consensus_severity_level"),
                    "is_safe_refusal": raw_rec.get("is_safe_refusal"),
                    "target_case_name": raw_rec.get("target_case_name"),
                    "target_case_year": raw_rec.get("target_case_year")
                }
            })
        return items

    auth1_temporal_primary = []
    for c in auth1_clusters:
        auth1_temporal_primary.extend(expand_temporal_cluster(c, "author_1"))

    auth2_temporal_primary = []
    for c in auth2_clusters:
        auth2_temporal_primary.extend(expand_temporal_cluster(c, "author_2"))

    auth1_temporal_overlap_for_auth2 = [dict(it) for it in auth1_temporal_primary if it["is_overlap"]]
    auth2_temporal_overlap_for_auth1 = [dict(it) for it in auth2_temporal_primary if it["is_overlap"]]

    # =========================================================================
    # 3. DIAGNOSTIC APPENDIX: Targeted Failure Modes (At Most 12 Records)
    # =========================================================================
    # Candidate pools must exclude Stage A (qid, cond) pairs and Stage B qids
    stage_a_keys = set((c["query_id"], c["condition"]) for c in sampled_temporal_clusters)
    temp_all = list(cohort_info["temp_records_by_key"].values())
    temp_eligible = [r for r in temp_all if (r["query_id"], r["condition"]) not in stage_a_keys]

    can_eligible = [r for r in all_can_records if r["query_id"] not in sampled_can_srs_qids]

    # Rule 1: Known fatal errors D033, D034 (if not already sampled in Stage B)
    diag_fatal = [r for r in can_eligible if r["query_id"] in ["D033", "D034"]]

    # Rule 2: Borderline Category D cases (lowest non-zero faithfulness, not in Stage B)
    borderline_d = [
        r for r in can_eligible
        if r.get("category") == "D_Adversarial"
        and r["query_id"] not in ["D033", "D034"]
        and 0.1 <= float(r.get("faithfulness", 0) or 0) <= 0.6
    ]
    borderline_d.sort(key=lambda r: (r.get("faithfulness", 0), r["query_id"]))
    diag_borderline = borderline_d[:2]

    # Rule 3: Temporal judge severity disagreements
    disagreements = [
        r for r in temp_eligible
        if (r.get("adjudication") or {}).get("agreement_severity") is False
        and not (r.get("judge2_evaluation") or {}).get("error")
    ]
    disagreements.sort(key=lambda r: (r["query_id"], r["condition"], r["pipeline"]))
    diag_disagree = rng.sample(disagreements, min(4, len(disagreements)))

    # Rule 4: Temporal gate interceptions
    intercepted = [
        r for r in temp_eligible
        if r.get("pipeline") == "TERRA_gated"
        and r.get("nli_gate_refusal") is True
    ]
    intercepted.sort(key=lambda r: (r["query_id"], r["condition"]))
    diag_intercepted = rng.sample(intercepted, min(2, len(intercepted)))

    # Rule 5: Provider error / timeout records (handling both boolean and string errors)
    def has_judge2_error(r: Dict[str, Any]) -> bool:
        err = (r.get("judge2_evaluation") or {}).get("error")
        return bool(err)

    prov_errors = [r for r in temp_eligible if has_judge2_error(r)]
    prov_errors.sort(key=lambda r: (r["query_id"], r["condition"], r["pipeline"]))
    diag_errors = rng.sample(prov_errors, min(2, len(prov_errors)))

    # Assemble and strictly deduplicate diagnostic candidates
    diag_candidate_records: List[Tuple[Dict[str, Any], str]] = []
    seen_diag_keys: Set[Tuple[str, str, str]] = set()

    for r in (diag_fatal + diag_borderline + diag_disagree + diag_intercepted + diag_errors):
        key = (r["query_id"], r.get("condition", "canonical_eval"), r.get("pipeline", CANONICAL_TARGET_PIPELINE))
        if key not in seen_diag_keys:
            seen_diag_keys.add(key)
            rule = "canonical_diagnostic" if "category" in r else "temporal_diagnostic"
            diag_candidate_records.append((r, rule))

    # Cap at at most 12
    diag_selected_records = diag_candidate_records[:12]

    # Split primary 50/50 between Author 1 and Author 2
    auth1_diag_raw = diag_selected_records[:len(diag_selected_records) // 2]
    auth2_diag_raw = diag_selected_records[len(diag_selected_records) // 2:]

    # Select 4 overlap diagnostic items (2 from each author)
    diag_overlap_keys: Set[Tuple[str, str, str]] = set()
    for r_tup in auth1_diag_raw[:2]:
        diag_overlap_keys.add((
            r_tup[0]["query_id"],
            r_tup[0].get("condition", "canonical_eval"),
            r_tup[0].get("pipeline", CANONICAL_TARGET_PIPELINE)
        ))
    for r_tup in auth2_diag_raw[:2]:
        diag_overlap_keys.add((
            r_tup[0]["query_id"],
            r_tup[0].get("condition", "canonical_eval"),
            r_tup[0].get("pipeline", CANONICAL_TARGET_PIPELINE)
        ))

    def convert_diagnostic(record_tuple: Tuple[Dict[str, Any], str], primary_author: str) -> Dict[str, Any]:
        raw_rec, rule = record_tuple
        is_temp = "cutoff_year" in raw_rec
        qid = raw_rec["query_id"]
        cond = raw_rec.get("condition", "canonical_eval")
        pipe = raw_rec.get("pipeline", CANONICAL_TARGET_PIPELINE)
        cutoff = raw_rec.get("cutoff_year")
        cutoff_str = f"As-of Year: {cutoff}" if cutoff else "N/A"
        key = (qid, cond, pipe)
        return {
            "source_dataset": "data/temporal_leakage_dual_judged.json" if is_temp else "data/terra_canonical_v2_eval.json",
            "cluster_id": "IND",
            "task_type": "Legal Evaluation Task",
            "query_id": qid,
            "condition": cond,
            "pipeline": pipe,
            "pipeline_cluster_pos": 1,
            "stratum": rule,
            "as_of_cutoff_year": cutoff_str,
            "query_text": str(raw_rec.get("query", "")),
            "response_text": str(raw_rec.get("answer_full") or "[MISSING / EMPTY RESPONSE]"),
            "primary_author": primary_author,
            "is_overlap": key in diag_overlap_keys,
            "sample_stratum": "diagnostic_appendix",
            "inclusion_prob": "targeted_non_probability",
            "_automated_baseline": {
                "sptlr_level2": raw_rec.get("sptlr_level2"),
                "consensus_severity": (raw_rec.get("adjudication") or {}).get("consensus_severity_level"),
                "is_safe_refusal": raw_rec.get("is_safe_refusal") if is_temp else raw_rec.get("safety_rejected"),
                "faithfulness": raw_rec.get("faithfulness")
            }
        }

    auth1_diag_primary = [convert_diagnostic(r, "author_1") for r in auth1_diag_raw]
    auth2_diag_primary = [convert_diagnostic(r, "author_2") for r in auth2_diag_raw]

    auth1_diag_overlap_for_auth2 = [dict(it) for it in auth1_diag_primary if it["is_overlap"]]
    auth2_diag_overlap_for_auth1 = [dict(it) for it in auth2_diag_primary if it["is_overlap"]]

    # Convert Stage B Canonical Records
    def convert_canonical(raw_rec: Dict[str, Any], primary_author: str) -> Dict[str, Any]:
        qid = raw_rec["query_id"]
        return {
            "source_dataset": "data/terra_canonical_v2_eval.json",
            "cluster_id": "IND",
            "task_type": "Legal Evaluation Task",
            "query_id": qid,
            "condition": "canonical_eval",
            "pipeline": CANONICAL_TARGET_PIPELINE,
            "pipeline_cluster_pos": 1,
            "stratum": raw_rec.get("category", "unknown"),
            "as_of_cutoff_year": "N/A",
            "query_text": str(raw_rec.get("query", "")),
            "response_text": str(raw_rec.get("answer_full") or "[MISSING / EMPTY RESPONSE]"),
            "primary_author": primary_author,
            "is_overlap": qid in can_overlap_qids,
            "sample_stratum": "canonical_stage_b",
            "inclusion_prob": 40.0 / 350.0,
            "_automated_baseline": {
                "faithfulness": raw_rec.get("faithfulness"),
                "safety_rejected": raw_rec.get("safety_rejected"),
                "category": raw_rec.get("category")
            }
        }

    auth1_can_primary = [convert_canonical(r, "author_1") for r in auth1_can_primary_raw]
    auth2_can_primary = [convert_canonical(r, "author_2") for r in auth2_can_primary_raw]

    auth1_can_overlap_for_auth2 = [dict(it) for it in auth1_can_primary if it["is_overlap"]]
    auth2_can_overlap_for_auth1 = [dict(it) for it in auth2_can_primary if it["is_overlap"]]

    # =========================================================================
    # 4. WORKLOAD COMPILATION & PRESENTATION SHUFFLING
    # =========================================================================
    # Compile author pools
    author_1_items = (
        auth1_temporal_primary +
        auth1_can_primary +
        auth1_diag_primary +
        auth2_temporal_overlap_for_auth1 +
        auth2_can_overlap_for_auth1 +
        auth2_diag_overlap_for_auth1
    )

    author_2_items = (
        auth2_temporal_primary +
        auth2_can_primary +
        auth2_diag_primary +
        auth1_temporal_overlap_for_auth2 +
        auth1_can_overlap_for_auth2 +
        auth1_diag_overlap_for_auth2
    )

    # Deep copy dictionaries to ensure zero reference mutation
    author_1_items = [dict(it) for it in author_1_items]
    author_2_items = [dict(it) for it in author_2_items]

    # Shuffle presentation order within each workbook to avoid block grouping of overlap/diagnostics
    # BUT keep temporal clusters contiguous so an assessor evaluates a cluster together
    def shuffle_workbook_items(items: List[Dict[str, Any]], author_tag: str) -> List[Dict[str, Any]]:
        # Group items by cluster_id if cluster_id starts with "CLUST-", else individual
        cluster_groups: Dict[str, List[Dict[str, Any]]] = {}
        individual_items: List[Dict[str, Any]] = []

        for it in items:
            cid = it["cluster_id"]
            if cid.startswith("CLUST-"):
                cluster_groups.setdefault(cid, []).append(it)
            else:
                individual_items.append(it)

        # Form units of presentation
        units: List[List[Dict[str, Any]]] = list(cluster_groups.values()) + [[it] for it in individual_items]
        rng.shuffle(units)

        ordered_items: List[Dict[str, Any]] = []
        for unit in units:
            ordered_items.extend(unit)

        # Assign opaque assessment IDs
        for idx, it in enumerate(ordered_items, start=1):
            it["assessment_id"] = f"{author_tag}-ITEM-{idx:03d}"
            it["assigned_author"] = "author_1" if author_tag == "AUTH1" else "author_2"
            it["workbook_display_row"] = idx + 1

        return ordered_items

    shuffled_auth1 = shuffle_workbook_items(author_1_items, "AUTH1")
    shuffled_auth2 = shuffle_workbook_items(author_2_items, "AUTH2")

    return shuffled_auth1, shuffled_auth2, {
        "sampled_temporal_clusters": sampled_temporal_clusters,
        "sampled_can_srs_qids": sorted(list(sampled_can_srs_qids)),
        "diag_count": len(diag_selected_records),
        "total_unique_items": len(auth1_temporal_primary) + len(auth2_temporal_primary) +
                              len(auth1_can_primary) + len(auth2_can_primary) +
                              len(auth1_diag_primary) + len(auth2_diag_primary)
    }


def build_private_key_mapping(
    author_1_items: List[Dict[str, Any]],
    author_2_items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Builds the master confidential mapping file linking opaque IDs to ground truth keys
    and original automated baseline labels (for later FNR and false omission computation).
    """
    all_items = author_1_items + author_2_items
    unique_resp_keys = set((v["query_id"], v["condition"], v["pipeline"]) for v in all_items)
    overlap_keys = set((v["query_id"], v["condition"], v["pipeline"]) for v in all_items if v.get("is_overlap"))
    diag_keys = set((v["query_id"], v["condition"], v["pipeline"]) for v in all_items if v.get("sample_stratum") == "diagnostic_appendix")

    mapping: Dict[str, Any] = {
        "metadata": {
            "author_1_item_count": len(author_1_items),
            "author_2_item_count": len(author_2_items),
            "overlap_count": len(overlap_keys),
            "unique_response_count": len(unique_resp_keys),
            "diagnostic_target_count": 12,
            "diagnostic_selected_count": len(diag_keys),
            "diagnostic_shortfall": max(0, 12 - len(diag_keys))
        },
        "assessments": {}
    }

    for item in all_items:
        aid = item["assessment_id"]
        q_text = str(item.get("query_text", ""))
        r_text = str(item.get("response_text", ""))
        q_sha = hashlib.sha256(q_text.encode("utf-8")).hexdigest()
        r_sha = hashlib.sha256(r_text.encode("utf-8")).hexdigest()
        item_digest = hashlib.sha256(
            f"{aid}|{item['query_id']}|{item['condition']}|{item['pipeline']}|{item['as_of_cutoff_year']}|{q_sha}|{r_sha}".encode("utf-8")
        ).hexdigest()

        mapping["assessments"][aid] = {
            "assessment_id": aid,
            "assigned_author": item["assigned_author"],
            "primary_author": item["primary_author"],
            "is_overlap": item["is_overlap"],
            "source_dataset": item["source_dataset"],
            "query_id": item["query_id"],
            "condition": item["condition"],
            "pipeline": item["pipeline"],
            "pipeline_cluster_pos": item["pipeline_cluster_pos"],
            "stratum": item.get("stratum", item.get("sample_stratum", "")),
            "sample_stratum": item["sample_stratum"],
            "cluster_id": item["cluster_id"],
            "as_of_cutoff_year": item["as_of_cutoff_year"],
            "inclusion_prob": item["inclusion_prob"],
            "workbook_display_row": item["workbook_display_row"],
            "query_text_sha256": q_sha,
            "response_text_sha256": r_sha,
            "item_digest": item_digest,
            "automated_baseline": item.get("_automated_baseline", {})
        }
    return mapping


def verify_blinding_invariance(item_rows: List[Dict[str, Any]]) -> None:
    """
    Rigorous negative control: verifies zero occurrences of forbidden pipeline names,
    judge names, automated score keys, or gold references in text visible to assessors.
    """
    forbidden_terms = [
        "1_Direct_LLM", "2_Flat_Vector_RAG", "3_GraphRAG_Adapted",
        "4_HippoRAG_Adapted", "5_Full_TERRA", "TERRA_gated", "TERRA_ungated",
        "qwen3-next-80b", "gpt-oss-120b", "sptlr_level2", "consensus_severity",
        "faithfulness_qwen", "faithfulness_gpt", "adjudication_rule",
        "diagnostic_appendix", "canonical_stage_b", "temporal_stage_a"
    ]

    for item in item_rows:
        fields_to_check = [
            str(item.get("query_text", "")),
            str(item.get("as_of_cutoff_year", "")),
            str(item.get("cluster_id", "")),
            str(item.get("task_type", "")),
            str(item.get("assessment_id", ""))
        ]
        for val in fields_to_check:
            for term in forbidden_terms:
                if term in val:
                    raise BlindingSecurityError(
                        f"Blinding violation! Term '{term}' found in visible field value: {val[:100]}"
                    )


def export_tsv_workbook(filepath: Path, items: List[Dict[str, Any]]) -> None:
    """Exports items to a clean TSV workbook fallback."""
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        # Header row
        writer.writerow([col[1] for col in ASSESSMENT_COLUMNS])
        for it in items:
            row = []
            for col_key, _, _, _ in ASSESSMENT_COLUMNS:
                val = str(it.get(col_key, ""))
                if col_key in ("query_text", "response_text"):
                    val = escape_formula(val)
                row.append(val)
            writer.writerow(row)


def export_html_reading_view(filepath: Path, items: List[Dict[str, Any]], author_name: str, author_tag: str = "") -> None:
    """
    Generates a lossless, comfortably readable HTML companion file displaying
    the complete unclipped legal query and system response for each item,
    with modern responsive card layout, zero text limits, and anchor navigation.
    """
    import html
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='utf-8'>",
        "  <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        f"  <title>TERRA Reading Companion — {author_name}</title>",
        "  <style>",
        "    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f6f8fa; color: #24292f; margin: 0; padding: 24px; line-height: 1.5; }",
        "    .container { max-width: 1100px; margin: 0 auto; }",
        "    .header-box { background: #ffffff; border: 1px solid #d0d7de; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }",
        "    .header-box h1 { margin: 0 0 8px 0; font-size: 24px; color: #1f497d; }",
        "    .header-box p { margin: 4px 0; color: #57606a; font-size: 14px; }",
        "    .alert-banner { background: #fff8c5; border: 1px solid #d4a72c; border-radius: 6px; padding: 12px 16px; margin: 16px 0; font-size: 13px; color: #4d2d00; }",
        "    .nav-box { background: #ffffff; border: 1px solid #d0d7de; border-radius: 8px; padding: 16px; margin-bottom: 24px; }",
        "    .nav-box h2 { font-size: 16px; margin: 0 0 12px 0; color: #244061; }",
        "    .nav-links { display: flex; flex-wrap: wrap; gap: 8px; font-size: 12px; }",
        "    .nav-links a { background: #f1f3f5; border: 1px solid #d0d7de; padding: 4px 8px; border-radius: 4px; text-decoration: none; color: #0969da; }",
        "    .nav-links a:hover { background: #0969da; color: #ffffff; }",
        "    .item-card { background: #ffffff; border: 1px solid #d0d7de; border-radius: 8px; padding: 24px; margin-bottom: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }",
        "    .item-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #244061; padding-bottom: 12px; margin-bottom: 16px; }",
        "    .item-id { font-size: 18px; font-weight: bold; color: #1f497d; }",
        "    .item-meta { font-size: 13px; color: #57606a; }",
        "    .section-title { font-size: 13px; font-weight: bold; text-transform: uppercase; color: #57606a; margin: 16px 0 6px 0; letter-spacing: 0.5px; }",
        "    .query-box { background: #f0f6fc; border: 1px solid #c8e1ff; border-radius: 6px; padding: 16px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; color: #1f2328; }",
        "    .response-box { background: #ffffff; border: 1px solid #d0d7de; border-radius: 6px; padding: 18px; font-size: 14px; line-height: 1.65; white-space: pre-wrap; word-break: break-word; color: #24292f; margin-top: 6px; }",
        "    .rubric-reminder { background: #f6f8fa; border: 1px dashed #d0d7de; border-radius: 6px; padding: 12px 16px; margin-top: 16px; font-size: 12px; color: #57606a; }",
        "    .top-link { display: inline-block; margin-top: 12px; font-size: 12px; color: #0969da; text-decoration: none; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <div class='container' id='top'>",
        "    <div class='header-box'>",
        f"      <h1>TERRA Assessment Companion — Reading View</h1>",
        f"      <p><strong>Assigned Assessor:</strong> {author_name} ({author_tag})</p>",
        "      <p><strong>Protocol:</strong> Source-Grounded Human Review Guidelines (Draft 01 / Addendum 01)</p>",
        "      <div class='alert-banner'>",
        "        <strong>STRICTLY CONFIDENTIAL INDEPENDENT REVIEW:</strong> All evaluations must be performed independently without discussing items with co-authors until Pass 1 is locked. This companion file displays full, unclipped query and system response texts without character limits.",
        "      </div>",
        "    </div>",
        "    <div class='nav-box'>",
        "      <h2>Jump to Assessment Item:</h2>",
        "      <div class='nav-links'>"
    ]

    for it in items:
        aid = it["assessment_id"]
        html_lines.append(f"        <a href='#{aid}'>{aid}</a>")

    html_lines.extend([
        "      </div>",
        "    </div>"
    ])

    for it in items:
        aid = it["assessment_id"]
        cid = it["cluster_id"]
        cutoff = it.get("as_of_cutoff_year", "N/A")
        q_raw = str(it.get("query_text", ""))
        r_raw = str(it.get("response_text", ""))
        q_esc = html.escape(q_raw)
        r_esc = html.escape(r_raw)

        html_lines.extend([
            f"    <div class='item-card' id='{aid}'>",
            "      <div class='item-header'>",
            f"        <div class='item-id'>{aid}</div>",
            f"        <div class='item-meta'>Group / Cluster: <strong>{cid}</strong> &nbsp;|&nbsp; <strong>{cutoff}</strong></div>",
            "      </div>",
            "      <div class='section-title'>Legal Query / Question</div>",
            f"      <div class='query-box'>{q_esc}</div>",
            "      <div class='section-title'>System Response (Full Unclipped Text)</div>",
            f"      <div class='response-box'>{r_esc}</div>",
            "      <div class='rubric-reminder'>",
            "        <strong>Evaluation Fields Reference:</strong> Response Status &bull; Source Correctness &bull; Temporal Leakage &bull; Responsiveness / Usefulness &bull; Citation Authenticity &bull; Refusal Justification &bull; Primary Legal Source &bull; Supporting Excerpt &bull; Assessment Rationale",
            "      </div>",
            "      <a class='top-link' href='#top'>&uarr; Back to top</a>",
            "    </div>"
        ])

    html_lines.extend([
        "  </div>",
        "</body>",
        "</html>"
    ])

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))


def export_txt_reading_view(filepath: Path, items: List[Dict[str, Any]], author_name: str) -> None:
    """Generates a plain-text companion file displaying full unclipped text."""
    lines = [
        "================================================================================",
        f"TERRA ASSESSMENT COMPANION — READING VIEW ({author_name})",
        "================================================================================",
        "CONFIDENTIAL INDEPENDENT REVIEW PROTOCOL",
        "Complete all evaluations independently prior to locking Pass 1.",
        "================================================================================\n"
    ]
    for it in items:
        aid = it.get("assessment_id", "")
        cid = it.get("cluster_id", "")
        cutoff = it.get("as_of_cutoff_year", "")
        q_text = str(it.get("query_text", ""))
        r_text = str(it.get("response_text", ""))

        lines.extend([
            f"ITEM: {aid}  |  Cluster: {cid}  |  {cutoff}",
            "--------------------------------------------------------------------------------",
            "[LEGAL QUERY]",
            q_text,
            "",
            "[SYSTEM RESPONSE (FULL TEXT)]",
            r_text,
            "================================================================================\n"
        ])

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def export_xlsx_workbook(filepath: Path, items: List[Dict[str, Any]], author_name: str) -> None:
    """
    Generates a professional, self-contained openpyxl workbook with:
      - Instructions & Semantic Rubric sheet
      - Assessments sheet with generous dynamic row heights
      - Detailed_Reading_View sheet formatting full query and response for comfortable reading
    """
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is required to generate Excel workbooks.")

    wb = openpyxl.Workbook()

    # Styling definitions
    title_font = Font(name="Segoe UI", size=14, bold=True, color="1F497D")
    header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    section_font = Font(name="Segoe UI", size=11, bold=True, color="244061")
    bold_font = Font(name="Segoe UI", size=9, bold=True)
    body_font = Font(name="Segoe UI", size=9)
    card_title_font = Font(name="Segoe UI", size=11, bold=True, color="002060")
    mono_font = Font(name="Consolas", size=9)

    header_fill_readonly = PatternFill(start_color="244061", end_color="244061", fill_type="solid")
    header_fill_fillable = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    card_header_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
    query_box_fill = PatternFill(start_color="F2F5F8", end_color="F2F5F8", fill_type="solid")

    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # -------------------------------------------------------------
    # Sheet 1: Instructions & Semantic Rubric
    # -------------------------------------------------------------
    ws_inst = wb.active
    ws_inst.title = "Instructions_and_Rubric"
    ws_inst.views.sheetView[0].showGridLines = True

    ws_inst["A1"] = f"TERRA Prospective Assessment Protocol — Two-Author Independent Review ({author_name})"
    ws_inst["A1"].font = title_font
    ws_inst["A2"] = "Source-Grounded Human Review Guidelines (Draft 01 / Addendum 01)"
    ws_inst["A2"].font = section_font

    inst_lines = [
        "",
        "OVERVIEW & TWO-AUTHOR INDEPENDENT BLINDING PROTOCOL:",
        "1. This workbook contains blinded model responses evaluated independently by two authors (Lead Author and Co-Author).",
        "2. All system pipeline tags, automated judge scores, internal metrics, and gold references have been withheld from this sheet.",
        "   (Note: Verbatim system responses are preserved authentically and may occasionally contain organic self-identification.)",
        "3. Both authors must assess each response independently based on authentic legal sources and controlling historical opinions.",
        "4. Do NOT discuss individual assessments with your co-author until both independent workbooks are locked and returned.",
        "5. AUTHORITATIVE READING ROUTE: For comfortable, 100% unclipped reading of queries and multi-paragraph responses without spreadsheet cell limits,",
        "   the companion HTML view ('READING_VIEW_AUTHOR_X.html') in this directory is the AUTHORITATIVE reading interface.",
        "   (Excel cells cap single values at 32,767 characters and row height at 409 pt; responses exceeding 1,200 chars are chunked across card rows or continuations).",
        "",
        "TWO-PASS ASSESSMENT WORKFLOW:",
        "Pass 1 (Source Verification & Independent Assessment):",
        "  - Read the query, historical cutoff horizon (if applicable), and system response (in the authoritative companion HTML view or workbook).",
        "  - Retrieve and consult controlling primary legal authorities (opinions, statutes, reporters) independently.",
        "  - Populate all fillable judgment fields (columns G through Q on the 'Assessments' tab).",
        "  - Mark UNCERTAIN freely whenever evidence is ambiguous or primary sources cannot resolve the issue.",
        "  - LOCK initial assessment upon completion and return the file.",
        "Pass 2 (Context Entailment & Discrepancy Analysis):",
        "  - Only after Pass 1 is locked will retrieval context and automated labels be revealed to evaluate entailment.",
        "",
        "STANDARDIZED FIELD DEFINITIONS & SEMANTIC GUIDELINES:",
        "• Response Status:",
        "  - substantive answer: The response directly attempts to answer the legal issue.",
        "  - refusal: The response explicitly declines to answer (e.g., stating inability or ethical/temporal limitation).",
        "  - mixed refusal/substantive answer: The response contains refusal language but proceeds to give substantive legal analysis.",
        "  - missing/unusable: The output is blank, truncated, or unparseable.",
        "",
        "• Source-Grounded Correctness (Doctrinal & Citation Status):",
        "  - supported: Material doctrinal and factual propositions are confirmed by controlling primary legal sources as of cutoff.",
        "  - contradicted: Response misstates the holding, rule, or doctrine of controlling historical authority, or relies on an authority already overruled prior to cutoff.",
        "  - uncertain: Available primary sources are inconclusive, or doctrine remains unsettled as of the query cutoff.",
        "  - not applicable: Applicable to pure refusals where no substantive legal propositions are asserted.",
        "",
        "• Temporal Leakage (Severe Operative Level-2 Standard — Directly Aligned with Benchmark sptlr_level2):",
        "  - yes: Severe operative temporal leakage: controlling judicial doctrine, statutory amendments, or case holdings originating strictly AFTER the stated as-of cutoff year are asserted as governing legal rules to answer the query.",
        "         (Directly corresponds to automated sptlr_level2 severity level 2).",
        "         (Note: Reliance on an authority that was already overruled BEFORE the cutoff year is an historical correctness error classified under source_grounded_correctness: contradicted, NOT temporal leakage.",
        "          Pre-cutoff doctrine that was subsequently overruled after cutoff remains valid historical doctrine as of cutoff).",
        "  - no: No operative post-cutoff leakage (analysis relies strictly on governing pre-cutoff authorities as of cutoff horizon).",
        "  - uncertain: Ambiguous cutoff applicability or controlling primary authorities inconclusive as of cutoff horizon.",
        "  - not applicable: Applicable to pure refusals or canonical non-temporal benchmark queries.",
        "",
        "• Responsiveness / Usefulness:",
        "  - addresses requested issue: Accurately and directly answers the specific legal issue posed.",
        "  - partly addresses: Discusses relevant legal principles but misses the core holding or requested application.",
        "  - does not address: Provides irrelevant historical discourse, answers a different question, or hallucinates.",
        "  - uncertain: Ambiguity in the question makes responsiveness borderline.",
        "",
        "• Citation Authenticity:",
        "  - authentic and supports proposition: Cited case/statute exists and genuine text supports the asserted rule.",
        "  - authentic but misapplied: Cited case exists, but does NOT stand for the proposition claimed by the response.",
        "  - cannot locate: Case name or reporter citation appears fabricated or cannot be located in legal databases.",
        "  - no citation/not applicable: No citations offered, or pure refusal.",
        "",
        "• Refusal Assessment:",
        "  - justified: Refusal was warranted because the requested analysis required overruled or unavailable authority.",
        "  - potentially unnecessary: Query was answerable under sound historical doctrine without violating constraints.",
        "  - uncertain: Borderline justification.",
        "  - not applicable: Response answered substantively."
    ]

    for row_idx, line in enumerate(inst_lines, start=3):
        ws_inst.cell(row=row_idx, column=1, value=line).font = bold_font if line.endswith(":") else body_font

    ws_inst.column_dimensions["A"].width = 120

    # -------------------------------------------------------------
    # Sheet 2: Assessments (Tabular Entry)
    # -------------------------------------------------------------
    ws_assess = wb.create_sheet(title="Assessments")
    ws_assess.views.sheetView[0].showGridLines = True

    # Header Row
    for col_idx, (col_key, col_title, width, is_readonly) in enumerate(ASSESSMENT_COLUMNS, start=1):
        cell = ws_assess.cell(row=1, column=col_idx, value=col_title)
        cell.font = header_font
        cell.fill = header_fill_readonly if is_readonly else header_fill_fillable
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        col_letter = get_column_letter(col_idx)
        ws_assess.column_dimensions[col_letter].width = width

    ws_assess.row_dimensions[1].height = 28

    # Populate Assessment Data
    for row_idx, it in enumerate(items, start=2):
        ans_text = str(it.get("response_text", ""))
        # Compute dynamic row height based on text length
        text_len = len(ans_text)
        if text_len > 2000:
            row_height = 140
        elif text_len > 800:
            row_height = 95
        elif text_len > 300:
            row_height = 65
        else:
            row_height = 45

        ws_assess.row_dimensions[row_idx].height = row_height

        for col_idx, (col_key, _, _, is_readonly) in enumerate(ASSESSMENT_COLUMNS, start=1):
            val = it.get(col_key, "")
            val_str = str(val) if val is not None else ""
            if len(val_str) > 30000:
                val_str = val_str[:30000] + "\n\n[NOTICE: Text exceeds 30,000 characters; see Full_Text_Continuations tab for complete text]"
            if col_key in ("query_text", "response_text"):
                val_str = escape_formula(val_str)
            cell = ws_assess.cell(row=row_idx, column=col_idx, value=val_str)
            cell.data_type = 's'
            cell.border = thin_border
            cell.font = body_font
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    ws_assess.freeze_panes = "G2"

    # -------------------------------------------------------------
    # Sheet 3: Detailed_Reading_View (Expansive per-item cards)
    # -------------------------------------------------------------
    ws_read = wb.create_sheet(title="Detailed_Reading_View")
    ws_read.views.sheetView[0].showGridLines = True

    ws_read.column_dimensions["A"].width = 25
    ws_read.column_dimensions["B"].width = 110

    curr_r = 1
    for it in items:
        aid = it.get("assessment_id", "")
        cid = it.get("cluster_id", "")
        cutoff = it.get("as_of_cutoff_year", "")

        # Card Header
        header_cell = ws_read.cell(row=curr_r, column=1, value=f"ITEM: {aid}")
        header_cell.font = card_title_font
        header_cell.fill = card_header_fill

        info_cell = ws_read.cell(row=curr_r, column=2, value=f"Cluster: {cid}  |  {cutoff}")
        info_cell.font = bold_font
        info_cell.fill = card_header_fill
        ws_read.row_dimensions[curr_r].height = 24
        curr_r += 1

        # Query Block
        q_label = ws_read.cell(row=curr_r, column=1, value="Legal Query:")
        q_label.font = bold_font
        q_label.alignment = Alignment(vertical="top")

        q_val_str = str(it.get("query_text", ""))
        if len(q_val_str) > 30000:
            q_val_str = q_val_str[:30000] + "\n\n[NOTICE: Text exceeds 30,000 characters; see Full_Text_Continuations tab for complete text]"
        q_val = ws_read.cell(row=curr_r, column=2, value=q_val_str)
        q_val.font = body_font
        q_val.fill = query_box_fill
        q_val.alignment = Alignment(vertical="top", wrap_text=True)
        ws_read.row_dimensions[curr_r].height = 45
        curr_r += 1

        # Response Blocks (split into multiple comfortable rows if multiline or exceeding 1,200 chars)
        resp_str = str(it.get("response_text", ""))
        r_paragraphs = [p for p in resp_str.split("\n\n") if p.strip()] or [resp_str]
        r_label_placed = False
        for p_idx, para in enumerate(r_paragraphs):
            p_chunks = [para[i:i + 1200] for i in range(0, len(para), 1200)] or [para]
            for ch in p_chunks:
                r_label = ws_read.cell(row=curr_r, column=1, value="System Response:" if not r_label_placed else "")
                r_label.font = bold_font
                r_label.alignment = Alignment(vertical="top")
                r_label_placed = True

                r_val = ws_read.cell(row=curr_r, column=2, value=escape_formula(ch))
                r_val.font = body_font
                r_val.alignment = Alignment(vertical="top", wrap_text=True)

                approx_lines = max(1, len(ch) // 70 + ch.count("\n"))
                ws_read.row_dimensions[curr_r].height = min(350, max(28, approx_lines * 18))
                curr_r += 1

        # Separator row
        curr_r += 1

    # -------------------------------------------------------------
    # Sheet 4: Full_Text_Continuations (Handling texts exceeding Excel's 32,767 cell ceiling)
    # -------------------------------------------------------------
    long_items = []
    for it in items:
        for field_k in ("query_text", "response_text"):
            raw_v = str(it.get(field_k, ""))
            if len(raw_v) > 30000:
                long_items.append((it.get("assessment_id", ""), field_k, raw_v))

    if long_items:
        ws_cont = wb.create_sheet(title="Full_Text_Continuations")
        ws_cont.views.sheetView[0].showGridLines = True
        cont_headers = ["Assessment ID", "Field Name", "Chunk Index", "Total Chunks", "Unbroken Text Chunk"]
        for c_idx, h in enumerate(cont_headers, start=1):
            cell = ws_cont.cell(row=1, column=c_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill_readonly
        ws_cont.column_dimensions["A"].width = 22
        ws_cont.column_dimensions["B"].width = 20
        ws_cont.column_dimensions["C"].width = 14
        ws_cont.column_dimensions["D"].width = 14
        ws_cont.column_dimensions["E"].width = 100

        cont_r = 2
        chunk_size = 25000
        for aid, field_k, raw_text in long_items:
            chunks = [raw_text[i:i + chunk_size] for i in range(0, len(raw_text), chunk_size)]
            tot = len(chunks)
            for c_i, ch in enumerate(chunks, start=1):
                ws_cont.cell(row=cont_r, column=1, value=aid).font = body_font
                ws_cont.cell(row=cont_r, column=2, value=field_k).font = body_font
                ws_cont.cell(row=cont_r, column=3, value=c_i).font = body_font
                ws_cont.cell(row=cont_r, column=4, value=tot).font = body_font
                ch_cell = ws_cont.cell(row=cont_r, column=5, value=escape_formula(ch))
                ch_cell.data_type = 's'
                ch_cell.font = mono_font
                ch_cell.alignment = Alignment(vertical="top", wrap_text=True)
                ws_cont.row_dimensions[cont_r].height = 60
                cont_r += 1

    wb.save(filepath)


def run_pipeline(
    temporal_path: Path,
    canonical_path: Path,
    output_dir: Path,
    seed: int = 20261008,
    test_fixture_mode: bool = False
) -> Dict[str, Any]:
    """Executes the complete hardened workbook preparation pipeline."""
    # Enforce strictly fresh, non-existent destination directory
    if output_dir.exists():
        raise FileExistsError(
            f"Output directory already exists: {output_dir}\n"
            f"A strictly fresh, non-existent directory is required to guarantee exclusive output."
        )

    output_dir.mkdir(parents=True, exist_ok=False)

    expected_temp_hash = None if test_fixture_mode else PINNED_HASHES["temporal"]
    expected_can_hash = None if test_fixture_mode else PINNED_HASHES["canonical"]

    manifest_status = "INITIALIZING"
    error_info = None
    hashes: Dict[str, str] = {}
    output_file_hashes: Dict[str, str] = {}
    auth1_items: List[Dict[str, Any]] = []
    auth2_items: List[Dict[str, Any]] = []
    sampling_meta: Dict[str, Any] = {}
    private_mapping: Dict[str, Any] = {"metadata": {}}

    try:
        print(f"[*] Step 1: Pre-read hash verification and loading of input datasets...")
        temporal_data, canonical_data, hashes = load_and_verify_inputs(
            temporal_path, canonical_path,
            expected_temp_hash=expected_temp_hash,
            expected_can_hash=expected_can_hash
        )

        print(f"[*] Step 2: Validating 400 temporal grid and 1750 canonical multi-pipeline records...")
        cohort_info = validate_cohorts_and_schemas(temporal_data, canonical_data)

        print(f"[*] Step 3: Drawing Stage B SRS, Stage A Temporal clusters, and Diagnostic failure modes (seed={seed})...")
        auth1_items, auth2_items, sampling_meta = draw_samples_and_allocate(cohort_info, seed=seed)

        print(f"[*] Step 4: Executing blinding invariance negative control...")
        verify_blinding_invariance(auth1_items)
        verify_blinding_invariance(auth2_items)

        print(f"[*] Step 5: Building private key mapping (retaining baseline labels for FNR evaluation)...")
        private_mapping = build_private_key_mapping(auth1_items, auth2_items)

        # Save private mapping
        mapping_path = output_dir / "PRIVATE_KEY_MAPPING.json"
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(private_mapping, f, indent=2)
        output_file_hashes["PRIVATE_KEY_MAPPING.json"] = compute_sha256(mapping_path)

        # Export Author 1 files
        auth1_xlsx = output_dir / "ASSESSMENT_AUTHOR_1.xlsx"
        auth1_tsv = output_dir / "ASSESSMENT_AUTHOR_1.tsv"
        auth1_html = output_dir / "READING_VIEW_AUTHOR_1.html"
        auth1_txt = output_dir / "READING_VIEW_AUTHOR_1.txt"
        print(f"[*] Step 6: Exporting Author 1 workbooks & reading companion ({len(auth1_items)} items)...")
        export_xlsx_workbook(auth1_xlsx, auth1_items, "Author 1 (Lead Author)")
        export_tsv_workbook(auth1_tsv, auth1_items)
        export_html_reading_view(auth1_html, auth1_items, "Author 1 (Lead Author)", "AUTHOR_1")
        export_txt_reading_view(auth1_txt, auth1_items, "Author 1 (Lead Author)")
        output_file_hashes["ASSESSMENT_AUTHOR_1.xlsx"] = compute_sha256(auth1_xlsx)
        output_file_hashes["ASSESSMENT_AUTHOR_1.tsv"] = compute_sha256(auth1_tsv)
        output_file_hashes["READING_VIEW_AUTHOR_1.html"] = compute_sha256(auth1_html)
        output_file_hashes["READING_VIEW_AUTHOR_1.txt"] = compute_sha256(auth1_txt)

        # Export Author 2 files
        auth2_xlsx = output_dir / "ASSESSMENT_AUTHOR_2.xlsx"
        auth2_tsv = output_dir / "ASSESSMENT_AUTHOR_2.tsv"
        auth2_html = output_dir / "READING_VIEW_AUTHOR_2.html"
        auth2_txt = output_dir / "READING_VIEW_AUTHOR_2.txt"
        print(f"[*] Step 7: Exporting Author 2 workbooks & reading companion ({len(auth2_items)} items)...")
        export_xlsx_workbook(auth2_xlsx, auth2_items, "Author 2 (Co-Author)")
        export_tsv_workbook(auth2_tsv, auth2_items)
        export_html_reading_view(auth2_html, auth2_items, "Author 2 (Co-Author)", "AUTHOR_2")
        export_txt_reading_view(auth2_txt, auth2_items, "Author 2 (Co-Author)")
        output_file_hashes["ASSESSMENT_AUTHOR_2.xlsx"] = compute_sha256(auth2_xlsx)
        output_file_hashes["ASSESSMENT_AUTHOR_2.tsv"] = compute_sha256(auth2_tsv)
        output_file_hashes["READING_VIEW_AUTHOR_2.html"] = compute_sha256(auth2_html)
        output_file_hashes["READING_VIEW_AUTHOR_2.txt"] = compute_sha256(auth2_txt)

        # Step 8: Post-lifecycle hash verification on input files to confirm zero mutation
        post_hash_temp = compute_sha256(temporal_path)
        post_hash_can = compute_sha256(canonical_path)
        if post_hash_temp != hashes.get("temporal_sha256"):
            raise HashVerificationError(f"Concurrent drift detected on {temporal_path} after generation!")
        if post_hash_can != hashes.get("canonical_sha256"):
            raise HashVerificationError(f"Concurrent drift detected on {canonical_path} after generation!")

        manifest_status = "COMPLETED_AND_VERIFIED" if not test_fixture_mode else "SYNTHETIC_TEST_ONLY_NOT_CERTIFIED"
    except Exception as e:
        manifest_status = "FAILED"
        error_info = str(e)
        raise
    finally:
        terminal_post_temp = "UNAVAILABLE"
        terminal_post_can = "UNAVAILABLE"
        hash_read_failed = False
        try:
            terminal_post_temp = compute_sha256(temporal_path)
        except Exception as e_hash:
            hash_read_failed = True
            if error_info is None:
                error_info = f"Failed to compute terminal hash for temporal input {temporal_path}: {type(e_hash).__name__}: {e_hash}"

        try:
            terminal_post_can = compute_sha256(canonical_path)
        except Exception as e_hash:
            hash_read_failed = True
            if error_info is None:
                error_info = f"Failed to compute terminal hash for canonical input {canonical_path}: {type(e_hash).__name__}: {e_hash}"

        # Terminal hashes govern terminal status
        init_temp = hashes.get("temporal_sha256")
        init_can = hashes.get("canonical_sha256")
        terminal_drift = (terminal_post_temp != init_temp or terminal_post_can != init_can)

        if hash_read_failed:
            manifest_status = "FAILED"
        elif terminal_drift:
            manifest_status = "FAILED_INPUT_MUTATION"
            if error_info is None:
                error_info = (
                    f"Terminal hash drift detected on inputs: "
                    f"temporal ({terminal_post_temp} != {init_temp}) or "
                    f"canonical ({terminal_post_can} != {init_can})"
                )

        certified_for_production = (manifest_status == "COMPLETED_AND_VERIFIED")

        manifest = {
            "generator_script": "scripts/prepare_author_assessment_workbooks.py",
            "generator_version": "v5_hardened",
            "execution_mode": "PRODUCTION" if not test_fixture_mode else "SYNTHETIC_TEST_FIXTURE_NON_PRODUCTION",
            "certified_for_production": certified_for_production,
            "status": manifest_status,
            "error_info": error_info,
            "warning": (
                "THIS ARTIFACT WAS GENERATED IN TEST FIXTURE MODE AND CANNOT BE USED FOR PRODUCTION ASSESSMENT."
                if test_fixture_mode else None
            ),
            "random_seed": seed,
            "inputs": {
                "temporal_path": str(temporal_path.resolve()),
                "canonical_path": str(canonical_path.resolve()),
                "pre_read_temporal_sha256": hashes.get("temporal_sha256", "N/A"),
                "terminal_temporal_sha256": terminal_post_temp,
                "pre_read_canonical_sha256": hashes.get("canonical_sha256", "N/A"),
                "terminal_canonical_sha256": terminal_post_can
            },
            "sampling_meta": sampling_meta,
            "allocation_summary": {
                "author_1_items": len(auth1_items),
                "author_2_items": len(auth2_items),
                "overlap_items": private_mapping.get("metadata", {}).get("overlap_count", 0),
                "unique_responses": private_mapping.get("metadata", {}).get("unique_response_count", 0),
                "diagnostic_target": private_mapping.get("metadata", {}).get("diagnostic_target_count", 0),
                "diagnostic_selected": private_mapping.get("metadata", {}).get("diagnostic_selected_count", 0),
                "diagnostic_shortfall": private_mapping.get("metadata", {}).get("diagnostic_shortfall", 0)
            },
            "output_files": output_file_hashes
        }

        prior_exc = sys.exc_info()[1]
        manifest_write_error = None
        manifest_path = output_dir / "EXTRACTION_MANIFEST.json"

        try:
            manifest_json_str = json.dumps(manifest, indent=2)
            # Exclusive creation mode ("x") prevents overwriting or truncating any existing report
            with open(manifest_path, "x", encoding="utf-8") as f:
                f.write(manifest_json_str)

            # Read back and validate the written manifest before returning success
            with open(manifest_path, "r", encoding="utf-8") as rf:
                readback = json.load(rf)
            if readback.get("status") != manifest["status"]:
                raise RuntimeError(
                    f"Extraction manifest readback status mismatch: {readback.get('status')} != {manifest['status']}"
                )
        except Exception as manifest_err:
            manifest_write_error = manifest_err
            print(f"[FATAL] Failed to write EXTRACTION_MANIFEST.json: {manifest_err}", file=sys.stderr)

        # 1. If an exception was already in-flight from try block, preserve it unconditionally
        if prior_exc is not None:
            pass
        # 2. If terminal hashes indicated failure, raise now
        elif manifest_status in ("FAILED", "FAILED_INPUT_MUTATION"):
            if manifest_status == "FAILED_INPUT_MUTATION":
                raise HashVerificationError(error_info or "Terminal hash drift detected on input files.")
            else:
                raise RuntimeError(error_info or "Terminal hash verification failed.")
        # 3. If manifest write failed on an otherwise successful run, fail closed with nonzero/no [OK]
        elif manifest_write_error is not None:
            raise RuntimeError(f"Failed to save final audit manifest: {manifest_write_error}") from manifest_write_error

    print(f"[OK] Pipeline complete! All artifacts generated in: {output_dir}")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Prepare author assessment workbooks (v4).")
    parser.add_argument(
        "--temporal-input",
        type=Path,
        default=Path("data/temporal_leakage_dual_judged.json"),
        help="Path to temporal evaluated records"
    )
    parser.add_argument(
        "--canonical-input",
        type=Path,
        default=Path("data/terra_canonical_v2_eval.json"),
        help="Path to canonical benchmark evaluated records"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Fresh non-existent output directory"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20261008,
        help="Deterministic pseudo-random seed"
    )
    parser.add_argument(
        "--test-fixture-mode",
        action="store_true",
        help="Explicit flag for synthetic test execution only. Bypasses production hash pins and marks manifest as non-production."
    )

    args = parser.parse_args()

    try:
        run_pipeline(
            temporal_path=args.temporal_input,
            canonical_path=args.canonical_input,
            output_dir=args.output_dir,
            seed=args.seed,
            test_fixture_mode=args.test_fixture_mode
        )
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
