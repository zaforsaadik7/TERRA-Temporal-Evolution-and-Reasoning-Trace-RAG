#!/usr/bin/env python3
"""
scripts/process_author_assessments.py (v3 - Fully Hardened)
===========================================================
Merges and analyzes the two returned, completed author assessment workbooks:
  - ASSESSMENT_AUTHOR_1.xlsx / .tsv
  - ASSESSMENT_AUTHOR_2.xlsx / .tsv
Using the confidential mapping:
  - PRIVATE_KEY_MAPPING.json

Implements CODE_AUDIT_01 and CODE_AUDIT_02 repairs:
  1. Strict Completion & Semantic Cross-Field Validation:
     - Validates exact allowed enum domains.
     - Enforces semantic consistency: rationale required for all items,
       substantive answers cannot have correctness N/A, supported/contradicted
       require pinpoint sources/excerpts, refusals require justification evaluation.
     - Incomplete workbooks halt processing with WORKBOOK_COMPLETION_REPORT.json
       and WorkbookIncompleteError without emitting finalized metrics.
  2. Immutable Content & Tampering Detection:
     - Verifies loaded query and response texts against cryptographic SHA-256
       digests stored in PRIVATE_KEY_MAPPING.json.
     - Raises ItemTamperingError immediately if immutable content was altered.
  3. Lossless Long-Text Reassembly:
     - Reconstructs multi-chunk texts from Full_Text_Continuations tab with
       strict sequence contiguity validation and exact whitespace preservation.
  4. Inter-Assessor Reliability (Shared Overlap Items):
     - Evaluates observed agreement (%) and unweighted Cohen's kappa.
     - Constant-category zero-variance returns UNDEFINED.
  5. Aligned Denominators & Dynamic FNR / FOR:
     - Missing automated baseline labels are tracked separately as unavailable,
       not converted to negatives.
     - Human uncertain and N/A ratings are excluded from evaluable comparator pairs.
     - Reconstructs true confusion matrix (TP, FN, TN, FP) on identical evaluables.
     - FNR = FN / (TP + FN); FOR = FN / (TN + FN); undefined when denominators are zero.
  6. Cutoff-Stratified Cluster Bootstrap & Sensitivity Scenarios:
     - B=2,000 cluster bootstrap stratified across the 5 cutoff horizons.
     - Provides empirical 95% bootstrap intervals for both FOR and FNR.
     - Evaluates Secondary Assessor Sensitivity Scenario side-by-side.
  7. Mixed Answer Accounting in Canonical Useful-Answering:
     - Breaks down pure substantive, mixed refusal/substantive, pure refusal, and unusable.
     - Evaluates coverage and contradiction error rates across pure and total substantive.
  8. Full Lifecycle Integrity:
     - Enforces fresh exclusive output directory (FileExistsError).
     - Verifies input file hashes pre-read and post-execution.
     - Writes EXECUTION_INTEGRITY_MANIFEST.json with python interpreter, hashes, and status.
"""

import os
import sys
import json
import csv
import math
import random
import shutil
import hashlib
import datetime
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class WorkbookIncompleteError(Exception):
    """Raised when an author workbook is incomplete or contains invalid/missing fields."""
    pass


class ItemTamperingError(Exception):
    """Raised when immutable query or response text has been altered after preparation."""
    pass


class HashVerificationError(Exception):
    """Raised when input files fail cryptographic integrity hash verification."""
    pass


# Exact Allowed Enums
ALLOWED_ENUMS = {
    "response_status": {
        "substantive answer",
        "refusal",
        "mixed refusal/substantive answer",
        "missing/unusable"
    },
    "source_grounded_correctness": {
        "supported",
        "contradicted",
        "uncertain",
        "not applicable"
    },
    "temporal_leakage": {
        "yes",
        "no",
        "uncertain",
        "not applicable"
    },
    "responsiveness_usefulness": {
        "addresses requested issue",
        "partly addresses",
        "does not address",
        "uncertain"
    },
    "citation_check": {
        "authentic and supports proposition",
        "authentic but misapplied",
        "cannot locate",
        "no citation/not applicable"
    },
    "refusal_assessment": {
        "justified",
        "potentially unnecessary",
        "uncertain",
        "not applicable"
    }
}


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def unescape_formula(val: Any) -> str:
    """
    Unescapes leading spreadsheet formula prefix without stripping whitespace.
    Preserves all leading/trailing indentation and newlines.
    """
    if val is None:
        return ""
    s = str(val)
    if s.startswith("'") and len(s) > 1 and s[1] in ("'", "=", "+", "-", "@", "\t", "\r", "\n"):
        return s[1:]
    return s


def load_author_file(filepath: Path) -> List[Dict[str, str]]:
    """
    Loads an author workbook (.xlsx or .tsv) with header normalization
    and strict continuation reassembly.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Author file not found: {filepath}")

    raw_records = []
    if filepath.suffix.lower() == ".tsv":
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                raw_records.append({k.strip(): unescape_formula(v) for k, v in row.items() if k})
    elif filepath.suffix.lower() == ".xlsx":
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl is required to load .xlsx workbooks")
        wb = openpyxl.load_workbook(filepath, data_only=True)
        if "Assessments" not in wb.sheetnames:
            raise ValueError(f"Workbook {filepath} missing 'Assessments' sheet!")
        ws = wb["Assessments"]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h).strip() if h is not None else "" for h in rows[0]]
        for row in rows[1:]:
            rec = {}
            for h, cell_val in zip(headers, row):
                if h:
                    rec[h] = unescape_formula(cell_val)
            if any(rec.values()):
                raw_records.append(rec)

        # Check for Full_Text_Continuations sheet to reconstruct long text fields (>30,000 chars)
        if "Full_Text_Continuations" in wb.sheetnames:
            ws_cont = wb["Full_Text_Continuations"]
            cont_rows = list(ws_cont.iter_rows(values_only=True))
            if cont_rows and len(cont_rows) > 1:
                # Group chunks by (assessment_id, field_name)
                continuations: Dict[Tuple[str, str], Dict[str, Any]] = {}
                for r_idx, c_row in enumerate(cont_rows[1:], start=2):
                    if c_row and len(c_row) >= 5 and c_row[0] is not None:
                        aid_c = str(c_row[0]).strip()
                        field_c = str(c_row[1]).strip()
                        try:
                            idx_c = int(c_row[2])
                            tot_c = int(c_row[3])
                        except (ValueError, TypeError):
                            raise ValueError(f"Invalid chunk metadata on Full_Text_Continuations row {r_idx}")
                        chunk_text = unescape_formula(c_row[4])
                        k_pair = (aid_c, field_c)
                        if k_pair not in continuations:
                            continuations[k_pair] = {"total": tot_c, "chunks": {}}
                        if idx_c in continuations[k_pair]["chunks"]:
                            raise ValueError(f"Duplicate chunk index {idx_c} for {k_pair} on Full_Text_Continuations")
                        continuations[k_pair]["chunks"][idx_c] = chunk_text

                # Reconstruct full texts with strict sequence validation
                full_texts: Dict[Tuple[str, str], str] = {}
                for k_pair, c_info in continuations.items():
                    tot = c_info["total"]
                    chunks_dict = c_info["chunks"]
                    expected_indices = list(range(1, tot + 1))
                    actual_indices = sorted(list(chunks_dict.keys()))
                    if actual_indices != expected_indices:
                        raise ValueError(
                            f"Continuation chunks for {k_pair} are non-contiguous or incomplete: "
                            f"expected {expected_indices}, found {actual_indices}"
                        )
                    full_texts[k_pair] = "".join(chunks_dict[i] for i in expected_indices)

                # Patch raw_records
                for rec in raw_records:
                    aid_val = None
                    for k, v in rec.items():
                        if "assessment id" in k.lower():
                            aid_val = str(v).strip()
                            break
                    if aid_val:
                        for k in list(rec.keys()):
                            k_lower = k.lower()
                            for (c_aid, c_field), full_s in full_texts.items():
                                if c_aid == aid_val:
                                    c_lower = c_field.lower()
                                    if ("response" in c_lower and "response" in k_lower) or \
                                       ("query" in c_lower and "query" in k_lower) or \
                                       (c_lower == k_lower):
                                        rec[k] = full_s

    else:
        raise ValueError(f"Unsupported file extension: {filepath.suffix}")

    # Normalize header names
    normalized_records = []
    for r in raw_records:
        norm = {}
        for k, v in r.items():
            k_clean = k.lower().strip()
            if "assessment id" in k_clean or k_clean == "assessment_id":
                norm["assessment_id"] = v
            elif "cluster" in k_clean:
                norm["cluster_id"] = v
            elif "task" in k_clean:
                norm["task_type"] = v
            elif "cutoff" in k_clean or "as-of" in k_clean or "as_of" in k_clean:
                norm["as_of_cutoff_year"] = v
            elif "response status" in k_clean:
                norm["response_status"] = v.lower()
            elif "source correctness" in k_clean:
                norm["source_grounded_correctness"] = v.lower()
            elif "temporal leakage" in k_clean:
                norm["temporal_leakage"] = v.lower()
            elif "responsiveness" in k_clean:
                norm["responsiveness_usefulness"] = v.lower()
            elif "citation authenticity" in k_clean:
                norm["citation_check"] = v.lower()
            elif "refusal justification" in k_clean:
                norm["refusal_assessment"] = v.lower()
            elif "primary legal source" in k_clean or "citation / url" in k_clean:
                norm["source_citation_or_url"] = v
            elif "supporting source excerpt" in k_clean:
                norm["supporting_excerpt"] = v
            elif "assessment rationale" in k_clean or "rationale" in k_clean:
                norm["assessment_rationale"] = v
            elif "assessor name" in k_clean:
                norm["assessor_identity"] = v
            elif "timestamp" in k_clean:
                norm["timestamp"] = v
            elif "query" in k_clean:
                norm["query_text"] = v
            elif "response" in k_clean:
                norm["response_text"] = v
            else:
                norm[k] = v
        normalized_records.append(norm)

    return normalized_records


def validate_author_records_against_mapping(
    records: List[Dict[str, str]],
    mapping_assessments: Dict[str, Any]
) -> None:
    """
    Validates that the returned author workbook has not had any of its immutable
    fields (assessment_id, cluster_id, task_type, as_of_cutoff_year, query_text,
    response_text) altered, and cryptographically verifies the composite item_digest.
    Fails closed if mandatory hashes or metadata fields are absent from the mapping.
    """
    if not records:
        raise ItemTamperingError("Author record list is empty; cannot validate integrity.")

    for rec in records:
        aid = rec.get("assessment_id", "")
        if not aid:
            raise ItemTamperingError("Record is missing mandatory assessment_id.")
        if aid not in mapping_assessments:
            raise ItemTamperingError(f"Unknown assessment_id '{aid}' not found in private mapping.")

        meta = mapping_assessments[aid]
        expected_q_hash = meta.get("query_text_sha256")
        expected_r_hash = meta.get("response_text_sha256")
        expected_digest = meta.get("item_digest")
        expected_cid = meta.get("cluster_id")
        expected_cutoff = meta.get("as_of_cutoff_year")
        expected_task = meta.get("task_type", "Legal Evaluation Task")

        if not expected_q_hash or not expected_r_hash or not expected_digest:
            raise ValueError(
                f"Mapping schema violation for {aid}: mandatory cryptographic hashes "
                f"(query_text_sha256, response_text_sha256, item_digest) are missing from private mapping."
            )

        # 1. Validate Cluster ID
        actual_cid = str(rec.get("cluster_id", ""))
        if actual_cid != str(expected_cid):
            raise ItemTamperingError(
                f"Tampering detected for {aid}! Cluster ID has been modified.\n"
                f"Expected: {expected_cid}\n"
                f"Actual:   {actual_cid}"
            )

        # 2. Validate Cutoff Year
        actual_cutoff = str(rec.get("as_of_cutoff_year", ""))
        if actual_cutoff != str(expected_cutoff):
            raise ItemTamperingError(
                f"Tampering detected for {aid}! As-of cutoff year has been modified.\n"
                f"Expected: {expected_cutoff}\n"
                f"Actual:   {actual_cutoff}"
            )

        # 3. Validate Task Type
        actual_task = str(rec.get("task_type", ""))
        if actual_task != str(expected_task):
            raise ItemTamperingError(
                f"Tampering detected for {aid}! Task type has been modified.\n"
                f"Expected: {expected_task}\n"
                f"Actual:   {actual_task}"
            )

        # 4. Validate Query Text SHA-256
        actual_q = rec.get("query_text", "")
        actual_q_hash = hashlib.sha256(actual_q.encode("utf-8")).hexdigest()
        if actual_q_hash != expected_q_hash:
            raise ItemTamperingError(
                f"Tampering detected for {aid}! Query text has been modified.\n"
                f"Expected hash: {expected_q_hash}\n"
                f"Actual hash:   {actual_q_hash}"
            )

        # 5. Validate Response Text SHA-256
        actual_r = rec.get("response_text", "")
        actual_r_hash = hashlib.sha256(actual_r.encode("utf-8")).hexdigest()
        if actual_r_hash != expected_r_hash:
            raise ItemTamperingError(
                f"Tampering detected for {aid}! Response text has been modified.\n"
                f"Expected hash: {expected_r_hash}\n"
                f"Actual hash:   {actual_r_hash}"
            )

        # 6. Cryptographically verify composite item digest
        reconstructed_digest = hashlib.sha256(
            f"{aid}|{meta['query_id']}|{meta['condition']}|{meta['pipeline']}|{meta['as_of_cutoff_year']}|{actual_q_hash}|{actual_r_hash}".encode("utf-8")
        ).hexdigest()
        if reconstructed_digest != expected_digest:
            raise ItemTamperingError(
                f"Tampering detected for {aid}! Composite item digest verification failed.\n"
                f"Expected digest: {expected_digest}\n"
                f"Actual digest:   {reconstructed_digest}"
            )


def validate_workbook_completion(
    records: List[Dict[str, str]],
    author_tag: str,
    expected_ids: Set[str],
    raise_on_error: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates completeness, ID alignment, exact enum adherence, and semantic cross-field consistency.
    Returns (is_complete, completion_report).
    """
    seen_ids = set()
    missing_fields_by_item = {}
    invalid_enums_by_item = {}
    semantic_violations_by_item = {}

    for r in records:
        aid = r.get("assessment_id", "")
        if not aid:
            continue
        if aid in seen_ids:
            raise ValueError(f"Duplicate assessment_id found in {author_tag} workbook: {aid}")
        seen_ids.add(aid)

        item_missing = []
        item_invalid = []
        item_semantic = []

        # Validate required enum fields
        for field, allowed in ALLOWED_ENUMS.items():
            val = r.get(field, "")
            if not val:
                item_missing.append(field)
            elif val not in allowed:
                item_invalid.append(f"{field}='{val}' (allowed: {sorted(list(allowed))})")

        # Semantic cross-field consistency rules (Finding 10)
        status = r.get("response_status", "")
        corr = r.get("source_grounded_correctness", "")
        temp = r.get("temporal_leakage", "")
        refusal_just = r.get("refusal_assessment", "")
        rationale = r.get("assessment_rationale", "")
        cite = r.get("source_citation_or_url", "")
        excerpt = r.get("supporting_excerpt", "")

        # Rule 1: Rationale is required for EVERY item (at least 5 characters)
        if not rationale or len(rationale.strip()) < 5:
            item_missing.append("assessment_rationale (minimum 5 characters explanation required)")

        # Rule 2: Substantive answers cannot have correctness marked not applicable
        if status == "substantive answer":
            if corr == "not applicable":
                item_semantic.append("Substantive answer cannot have source correctness marked 'not applicable'")

        # Rule 3: Supported or Contradicted judgments require pinpoint legal source and excerpt
        if corr in ("supported", "contradicted"):
            if not cite or len(cite.strip()) < 3:
                item_missing.append("source_citation_or_url (required when supported or contradicted)")
            if not excerpt or len(excerpt.strip()) < 3:
                item_missing.append("supporting_excerpt (required verbatim holding when supported or contradicted)")

        # Rule 4: Refusals must have refusal justification evaluated
        if status == "refusal":
            if refusal_just == "not applicable":
                item_semantic.append("Refusal output must evaluate refusal justification (cannot be 'not applicable')")

        # Rule 5: Mixed refusal/substantive answer must evaluate both justification and correctness
        if status == "mixed refusal/substantive answer":
            if refusal_just == "not applicable":
                item_semantic.append("Mixed response must evaluate refusal justification")
            if corr == "not applicable":
                item_semantic.append("Mixed response contains substantive legal propositions; cannot be 'not applicable'")

        # Rule 6: Temporal leakage 'yes' requires substantive explanation and primary source authority
        if temp == "yes":
            if len(rationale.strip()) < 10:
                item_semantic.append("Temporal leakage 'yes' requires explicit rationale (minimum 10 characters)")
            has_cite_or_excerpt = (cite and len(cite.strip()) >= 3) or (excerpt and len(excerpt.strip()) >= 3)
            explains_unavailability = any(kw in rationale.lower() for kw in ("unavailable", "unretrieved", "cannot locate", "not found", "inconclusive"))
            if not has_cite_or_excerpt and not explains_unavailability:
                item_semantic.append("Temporal leakage 'yes' requires post-cutoff primary source citation / excerpt, or explicit explanation in rationale")

        if not r.get("assessor_identity"):
            item_missing.append("assessor_identity")
        if not r.get("timestamp"):
            item_missing.append("timestamp")

        if item_missing:
            missing_fields_by_item[aid] = item_missing
        if item_invalid:
            invalid_enums_by_item[aid] = item_invalid
        if item_semantic:
            semantic_violations_by_item[aid] = item_semantic

    missing_ids = expected_ids - seen_ids
    extra_ids = seen_ids - expected_ids

    is_complete = (
        len(missing_ids) == 0 and
        len(extra_ids) == 0 and
        len(missing_fields_by_item) == 0 and
        len(invalid_enums_by_item) == 0 and
        len(semantic_violations_by_item) == 0
    )

    report = {
        "author": author_tag,
        "total_records_submitted": len(records),
        "expected_id_count": len(expected_ids),
        "missing_ids": sorted(list(missing_ids)),
        "extra_unknown_ids": sorted(list(extra_ids)),
        "unpopulated_items_count": len(missing_fields_by_item),
        "unpopulated_items_detail": missing_fields_by_item,
        "invalid_enums_count": len(invalid_enums_by_item),
        "invalid_enums_detail": invalid_enums_by_item,
        "semantic_violations_count": len(semantic_violations_by_item),
        "semantic_violations_detail": semantic_violations_by_item,
        "is_complete": is_complete
    }

    if raise_on_error and not is_complete:
        raise WorkbookIncompleteError(
            f"Workbook validation failed for {author_tag}:\n"
            f"  Unpopulated items: {len(missing_fields_by_item)}\n"
            f"  Invalid enum entries: {len(invalid_enums_by_item)}\n"
            f"  Semantic violations: {len(semantic_violations_by_item)}\n"
            f"  Missing IDs: {len(missing_ids)}\n"
            f"  Extra IDs: {len(extra_ids)}"
        )

    return is_complete, report


def compute_cohens_kappa(rater1: List[str], rater2: List[str]) -> Any:
    """
    Computes unweighted Cohen's kappa for two raters.
    Returns UNDEFINED if variance is zero or raters are degenerate.
    """
    assert len(rater1) == len(rater2)
    valid_pairs = [(r1, r2) for r1, r2 in zip(rater1, rater2) if r1 and r2]
    n = len(valid_pairs)
    if n == 0:
        return "UNDEFINED (zero valid pairs)"

    categories = sorted(list(set(r1 for r1, _ in valid_pairs).union(set(r2 for _, r2 in valid_pairs))))
    if len(categories) <= 1:
        return "UNDEFINED (zero rater variance across categories)"

    cat_to_idx = {c: i for i, c in enumerate(categories)}
    num_cats = len(categories)

    cm = [[0 for _ in range(num_cats)] for _ in range(num_cats)]
    for r1, r2 in valid_pairs:
        cm[cat_to_idx[r1]][cat_to_idx[r2]] += 1

    po = sum(cm[i][i] for i in range(num_cats)) / n
    pe = sum(
        (sum(cm[i][j] for j in range(num_cats)) * sum(cm[j][i] for j in range(num_cats)))
        for i in range(num_cats)
    ) / (n * n)

    if pe >= 1.0 or (1.0 - pe) == 0.0:
        return "UNDEFINED (marginal agreement equals 1.0)"

    kappa = (po - pe) / (1.0 - pe)
    return round(kappa, 4)


def clopper_pearson_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Computes exact Clopper-Pearson binomial confidence interval."""
    if n == 0:
        return (0.0, 0.0)
    alpha = 1.0 - confidence
    try:
        from scipy.stats import beta
        lower = 0.0 if k == 0 else float(beta.ppf(alpha / 2.0, k, n - k + 1))
        upper = 1.0 if k == n else float(beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
        return (round(lower, 4), round(upper, 4))
    except ImportError:
        # Wilson score interval fallback if scipy is unavailable
        z = 1.95996
        p = k / n
        denom = 1.0 + (z**2) / n
        center = (p + (z**2) / (2 * n)) / denom
        half = (z * math.sqrt((p * (1 - p) / n) + (z**2) / (4 * n**2))) / denom
        return (round(max(0.0, center - half), 4), round(min(1.0, center + half), 4))


def evaluate_inter_assessor_agreement(overlap_items: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Evaluates observed agreement and Cohen's kappa across the 20 shared overlap items.
    """
    fields_to_compare = [
        "response_status",
        "source_grounded_correctness",
        "temporal_leakage",
        "responsiveness_usefulness",
        "citation_check",
        "refusal_assessment"
    ]

    agreement_summary: Dict[str, Any] = {}
    for fld in fields_to_compare:
        r1_list = []
        r2_list = []
        for it in overlap_items:
            e1 = it["author_1_eval"] or {}
            e2 = it["author_2_eval"] or {}
            r1_list.append(e1.get(fld, ""))
            r2_list.append(e2.get(fld, ""))

        agree_count = sum(1 for v1, v2 in zip(r1_list, r2_list) if v1 == v2 and v1 != "")
        total_valid = sum(1 for v1, v2 in zip(r1_list, r2_list) if v1 != "" and v2 != "")
        agree_pct = round(agree_count / total_valid * 100.0, 2) if total_valid > 0 else 0.0
        kappa = compute_cohens_kappa(r1_list, r2_list)

        agreement_summary[fld] = {
            "valid_pair_count": total_valid,
            "raw_agreement_count": agree_count,
            "observed_agreement_pct": agree_pct,
            "cohens_kappa": kappa
        }

    disagreement_ledger = []
    for it in overlap_items:
        e1 = it["author_1_eval"] or {}
        e2 = it["author_2_eval"] or {}
        item_disagreements = {}
        for fld in fields_to_compare:
            v1 = e1.get(fld, "")
            v2 = e2.get(fld, "")
            if v1 != v2:
                item_disagreements[fld] = {"author_1": v1, "author_2": v2}
        if item_disagreements:
            disagreement_ledger.append({
                "query_id": it["meta"]["query_id"],
                "condition": it["meta"]["condition"],
                "pipeline": it["meta"]["pipeline"],
                "sample_stratum": it["meta"]["sample_stratum"],
                "disagreements": item_disagreements
            })

    return agreement_summary, disagreement_ledger


def run_temporal_cluster_bootstrap(
    cluster_records: Dict[str, List[Dict[str, Any]]],
    cluster_to_cutoff: Dict[str, int],
    num_bootstrap: int = 2000,
    seed: int = 20261008
) -> Dict[str, Any]:
    """
    Computes cluster-level bootstrap confidence intervals for temporal rates.
    Resamples query clusters within cutoff strata with replacement.
    Evaluates both False Omission Rate (FOR) and False Negative Rate (FNR)
    strictly over identical evaluable comparison pairs.
    """
    rng = random.Random(seed)
    cutoffs = sorted(list(set(cluster_to_cutoff.values())))
    clusters_by_cutoff: Dict[int, List[str]] = {c: [] for c in cutoffs}
    for cid, c_yr in cluster_to_cutoff.items():
        clusters_by_cutoff[c_yr].append(cid)

    boot_for = []
    boot_fnr = []

    for _ in range(num_bootstrap):
        sampled_cids = []
        for c_yr in cutoffs:
            stratum_cids = clusters_by_cutoff[c_yr]
            n_stratum = len(stratum_cids)
            if n_stratum > 0:
                sampled_cids.extend([rng.choice(stratum_cids) for _ in range(n_stratum)])

        sample_items = []
        for cid in sampled_cids:
            sample_items.extend(cluster_records[cid])

        # Filter strictly to evaluable comparison pairs (Finding 6: exact bool check)
        evaluable_items = [
            it for it in sample_items
            if type(it["automated_baseline"].get("sptlr_level2")) is bool
            and (it["eval"].get("temporal_leakage") or "").lower() in ("yes", "no")
        ]

        b_tp = sum(1 for it in evaluable_items if it["automated_baseline"]["sptlr_level2"] is True and it["eval"]["temporal_leakage"].lower() == "yes")
        b_fn = sum(1 for it in evaluable_items if it["automated_baseline"]["sptlr_level2"] is False and it["eval"]["temporal_leakage"].lower() == "yes")
        b_tn = sum(1 for it in evaluable_items if it["automated_baseline"]["sptlr_level2"] is False and it["eval"]["temporal_leakage"].lower() == "no")
        b_fp = sum(1 for it in evaluable_items if it["automated_baseline"]["sptlr_level2"] is True and it["eval"]["temporal_leakage"].lower() == "no")

        # FOR = FN / (TN + FN)
        if (b_tn + b_fn) > 0:
            boot_for.append(b_fn / (b_tn + b_fn))

        # FNR = FN / (TP + FN)
        if (b_tp + b_fn) > 0:
            boot_fnr.append(b_fn / (b_tp + b_fn))

    def calc_ci(data: List[float]) -> Any:
        if not data:
            return "UNDEFINED (zero evaluable replicates)"
        data.sort()
        l_idx = int(0.025 * len(data))
        u_idx = int(0.975 * len(data))
        return (round(data[l_idx], 4), round(data[u_idx], 4))

    return {
        "for_bootstrap_95": calc_ci(boot_for),
        "fnr_bootstrap_95": calc_ci(boot_fnr)
    }


def compute_population_metrics(
    unique_items: List[Dict[str, Any]],
    use_secondary_for_overlap: bool = False
) -> Dict[str, Any]:
    """
    Computes design-appropriate statistical estimates without double-counting.
    If use_secondary_for_overlap is True, evaluates sensitivity to second-author ratings.
    """
    # -------------------------------------------------------------------------
    # 1. Temporal Probability Sample (Stage A: 80 responses, 20 clusters)
    # -------------------------------------------------------------------------
    temporal_items = [it for it in unique_items if it["meta"]["sample_stratum"] == "temporal_stage_a"]
    assert len(temporal_items) == 80, f"Expected 80 temporal items; found {len(temporal_items)}"

    cluster_dict: Dict[str, List[Dict[str, Any]]] = {}
    cluster_to_cutoff: Dict[str, int] = {}

    # Strict Evaluables Tracking
    tp = 0
    fn = 0
    tn = 0
    fp = 0
    human_uncertain = 0
    human_na = 0
    missing_automated_count = 0

    for it in temporal_items:
        meta = it["meta"]
        if use_secondary_for_overlap and meta["is_overlap"]:
            eval_dict = it["author_2_eval"] if meta["primary_author"] == "author_1" else it["author_1_eval"]
        else:
            eval_dict = it["author_1_eval"] if meta["primary_author"] == "author_1" else it["author_2_eval"]

        cid = meta["cluster_id"]
        cutoff_raw = str(meta.get("as_of_cutoff_year", "0")).replace("As-of Year:", "").strip()
        cutoff_yr = int(cutoff_raw) if cutoff_raw.isdigit() else 0
        cluster_to_cutoff[cid] = cutoff_yr
        cluster_dict.setdefault(cid, []).append({
            "eval": eval_dict,
            "automated_baseline": meta["automated_baseline"]
        })

        sptlr_val = meta["automated_baseline"].get("sptlr_level2")
        human_leak_label = (eval_dict.get("temporal_leakage") or "").lower()

        # Check for missing/unlabeled automated baseline (Finding 6: exact bool check)
        if sptlr_val is None:
            missing_automated_count += 1
            continue
        if type(sptlr_val) is not bool:
            raise ValueError(
                f"Automated baseline sptlr_level2 must be an exact bool or None; "
                f"got {type(sptlr_val).__name__} ({sptlr_val}) for query {meta.get('query_id')}"
            )

        # Check human rating
        if human_leak_label not in ("yes", "no"):
            if human_leak_label == "uncertain":
                human_uncertain += 1
            else:
                human_na += 1
            continue

        # Both ratings are definitive: evaluable pair
        if human_leak_label == "yes":
            if sptlr_val is True:
                tp += 1
            else:
                fn += 1
        else:
            if sptlr_val is True:
                fp += 1
            else:
                tn += 1

    evaluable_auto_negatives = tn + fn
    evaluable_auto_positives = tp + fp
    evaluable_human_positives = tp + fn
    evaluable_human_negatives = tn + fp
    total_evaluable_pairs = tp + fn + tn + fp

    # False Omission Proportion: FN / (TN + FN) on evaluable automated-negatives
    if evaluable_auto_negatives == 0:
        fop = "UNDEFINED (zero automated-negative cases in evaluable set)"
    else:
        fop = round(fn / evaluable_auto_negatives, 4)

    # False Negative Rate: FN / (TP + FN) on evaluable human reference positives
    if evaluable_human_positives == 0:
        fnr = "UNDEFINED (zero reference-positive cases identified by human assessors)"
    else:
        fnr = round(fn / evaluable_human_positives, 4)

    # Cutoff-Stratified Cluster Bootstrap Uncertainty
    boot_intervals = run_temporal_cluster_bootstrap(cluster_dict, cluster_to_cutoff)

    temporal_stats = {
        "sample_size": len(temporal_items),
        "query_cluster_count": len(cluster_dict),
        "total_evaluable_comparison_pairs": total_evaluable_pairs,
        "missing_or_unlabeled_automated_count": missing_automated_count,
        "confusion_matrix": {
            "true_positive_tp": tp,
            "false_negative_fn_missed": fn,
            "true_negative_tn": tn,
            "false_positive_fp": fp,
            "human_uncertain_excluded": human_uncertain,
            "human_not_applicable_excluded": human_na
        },
        "evaluable_automated_negative_denominator": evaluable_auto_negatives,
        "false_omission_proportion": fop,
        "false_omission_cluster_bootstrap_95": boot_intervals.get("for_bootstrap_95"),
        "evaluable_human_reference_positive_denominator": evaluable_human_positives,
        "false_negative_rate_fnr": fnr,
        "false_negative_rate_cluster_bootstrap_95": boot_intervals.get("fnr_bootstrap_95")
    }

    # -------------------------------------------------------------------------
    # 2. Canonical Usefulness Probability Sample (Stage B: 40 SRS responses)
    # -------------------------------------------------------------------------
    canonical_items = [it for it in unique_items if it["meta"]["sample_stratum"] == "canonical_stage_b"]
    assert len(canonical_items) == 40, f"Expected 40 canonical items; found {len(canonical_items)}"

    pure_substantive_count = 0
    mixed_substantive_count = 0
    pure_refusal_count = 0
    unusable_count = 0

    pure_strict_supported_responsive = 0
    mixed_strict_supported_responsive = 0
    all_broad_supported_responsive = 0
    pure_contradicted = 0
    mixed_contradicted = 0
    correctness_uncertain_count = 0
    responsiveness_uncertain_count = 0

    for it in canonical_items:
        meta = it["meta"]
        if use_secondary_for_overlap and meta["is_overlap"]:
            eval_dict = it["author_2_eval"] if meta["primary_author"] == "author_1" else it["author_1_eval"]
        else:
            eval_dict = it["author_1_eval"] if meta["primary_author"] == "author_1" else it["author_2_eval"]

        r_stat = (eval_dict.get("response_status") or "").lower()
        s_corr = (eval_dict.get("source_grounded_correctness") or "").lower()
        r_use = (eval_dict.get("responsiveness_usefulness") or "").lower()

        if s_corr == "uncertain":
            correctness_uncertain_count += 1
        if r_use == "uncertain":
            responsiveness_uncertain_count += 1

        if r_stat == "substantive answer":
            pure_substantive_count += 1
            if s_corr == "supported" and r_use == "addresses requested issue":
                pure_strict_supported_responsive += 1
            if s_corr == "supported" and r_use in ("addresses requested issue", "partly addresses"):
                all_broad_supported_responsive += 1
            if s_corr == "contradicted":
                pure_contradicted += 1
        elif r_stat == "mixed refusal/substantive answer":
            mixed_substantive_count += 1
            if s_corr == "supported" and r_use == "addresses requested issue":
                mixed_strict_supported_responsive += 1
            if s_corr == "supported" and r_use in ("addresses requested issue", "partly addresses"):
                all_broad_supported_responsive += 1
            if s_corr == "contradicted":
                mixed_contradicted += 1
        elif r_stat == "refusal":
            pure_refusal_count += 1
        else:
            unusable_count += 1

    total_substantive_count = pure_substantive_count + mixed_substantive_count
    strict_all_substantive_count = pure_strict_supported_responsive + mixed_strict_supported_responsive

    canonical_stats = {
        "sample_size": 40,
        "pure_substantive_count": pure_substantive_count,
        "pure_substantive_proportion": round(pure_substantive_count / 40.0, 4),
        "mixed_refusal_substantive_count": mixed_substantive_count,
        "mixed_refusal_substantive_proportion": round(mixed_substantive_count / 40.0, 4),
        "total_substantive_coverage_count": total_substantive_count,
        "total_substantive_coverage_proportion": round(total_substantive_count / 40.0, 4),
        "pure_refusal_count": pure_refusal_count,
        "pure_refusal_proportion": round(pure_refusal_count / 40.0, 4),
        "unusable_output_count": unusable_count,
        "unusable_output_proportion": round(unusable_count / 40.0, 4),
        "strict_supported_and_responsive_pure_count": pure_strict_supported_responsive,
        "strict_supported_and_responsive_yield_pure": round(pure_strict_supported_responsive / 40.0, 4),
        "strict_supported_and_responsive_all_substantive_count": strict_all_substantive_count,
        "strict_supported_and_responsive_yield_all_substantive": round(strict_all_substantive_count / 40.0, 4),
        "broad_supported_and_responsive_count": all_broad_supported_responsive,
        "broad_supported_and_responsive_yield_all": round(all_broad_supported_responsive / 40.0, 4),
        "correctness_uncertain_count": correctness_uncertain_count,
        "correctness_uncertain_proportion": round(correctness_uncertain_count / 40.0, 4),
        "responsiveness_uncertain_count": responsiveness_uncertain_count,
        "responsiveness_uncertain_proportion": round(responsiveness_uncertain_count / 40.0, 4),
        "contradicted_among_pure_substantive": (
            round(pure_contradicted / pure_substantive_count, 4)
            if pure_substantive_count > 0 else "UNDEFINED (zero pure substantive answers)"
        ),
        "contradicted_among_all_substantive": (
            round((pure_contradicted + mixed_contradicted) / total_substantive_count, 4)
            if total_substantive_count > 0 else "UNDEFINED (zero substantive answers)"
        ),
        "legal_status_caveat": (
            "Empirical source-grounded judgments evaluate factual agreement with controlling historical authorities "
            "and do not constitute formal legal advice or licensed legal certification."
        )
    }

    # -------------------------------------------------------------------------
    # 3. Diagnostic Appendix Cases (Strictly Segregated)
    # -------------------------------------------------------------------------
    diagnostic_items = [it for it in unique_items if it["meta"]["sample_stratum"] == "diagnostic_appendix"]
    diag_summary = []
    for it in diagnostic_items:
        meta = it["meta"]
        if use_secondary_for_overlap and meta["is_overlap"]:
            eval_dict = it["author_2_eval"] if meta["primary_author"] == "author_1" else it["author_1_eval"]
        else:
            eval_dict = it["author_1_eval"] if meta["primary_author"] == "author_1" else it["author_2_eval"]

        diag_summary.append({
            "query_id": meta["query_id"],
            "pipeline": meta["pipeline"],
            "stratum_rule": meta.get("stratum", meta.get("sample_stratum", "diagnostic_appendix")),
            "human_response_status": eval_dict.get("response_status"),
            "human_correctness": eval_dict.get("source_grounded_correctness"),
            "human_leakage": eval_dict.get("temporal_leakage"),
            "primary_author": meta["primary_author"]
        })

    return {
        "temporal_probability_sample": temporal_stats,
        "canonical_usefulness_sample": canonical_stats,
        "diagnostic_appendix_cases": {
            "count": len(diagnostic_items),
            "records": diag_summary
        }
    }


def process_author_assessments(
    author1_input: Path,
    author2_input: Path,
    mapping_path: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Processes, validates, and analyzes author assessment workbooks with strict
    unconditional lifecycle integrity management.
    """
    if output_dir.exists():
        raise FileExistsError(
            f"Output directory already exists: {output_dir}\n"
            f"A fresh, exclusive directory is required to guarantee integrity."
        )

    output_dir.mkdir(parents=True, exist_ok=False)

    manifest_status = "INITIALIZING"
    error_info = None
    output_file_hashes: Dict[str, str] = {}
    preserved_hashes: Dict[str, Any] = {}
    pre_a1_hash = "UNAVAILABLE"
    pre_a2_hash = "UNAVAILABLE"
    pre_map_hash = "UNAVAILABLE"
    completion_report_path = output_dir / "WORKBOOK_COMPLETION_REPORT.json"

    try:
        # 1. Pre-execution input hash snapshot inside guarded lifecycle
        pre_a1_hash = compute_sha256(author1_input)
        pre_a2_hash = compute_sha256(author2_input)
        pre_map_hash = compute_sha256(mapping_path)

        # 2. Role-separated exclusive directory creation and immediate byte-for-byte preservation
        preserved_dir = output_dir / "preserved_originals"
        preserved_dir.mkdir(parents=True, exist_ok=False)

        a1_pres_dir = preserved_dir / "author_1"
        a1_pres_dir.mkdir(parents=True, exist_ok=False)
        a2_pres_dir = preserved_dir / "author_2"
        a2_pres_dir.mkdir(parents=True, exist_ok=False)
        map_pres_dir = preserved_dir / "mapping"
        map_pres_dir.mkdir(parents=True, exist_ok=False)

        target_a1 = a1_pres_dir / author1_input.name
        target_a2 = a2_pres_dir / author2_input.name
        target_map = map_pres_dir / mapping_path.name

        shutil.copy2(author1_input, target_a1)
        shutil.copy2(author2_input, target_a2)
        shutil.copy2(mapping_path, target_map)

        # Verify preserved copies against pre-read original hashes immediately
        copied_a1 = compute_sha256(target_a1)
        if copied_a1 != pre_a1_hash:
            raise HashVerificationError(
                f"Preserved copy corrupted for Author 1: {copied_a1} != {pre_a1_hash}"
            )
        copied_a2 = compute_sha256(target_a2)
        if copied_a2 != pre_a2_hash:
            raise HashVerificationError(
                f"Preserved copy corrupted for Author 2: {copied_a2} != {pre_a2_hash}"
            )
        copied_map = compute_sha256(target_map)
        if copied_map != pre_map_hash:
            raise HashVerificationError(
                f"Preserved copy corrupted for Mapping: {copied_map} != {pre_map_hash}"
            )

        preserved_hashes = {
            "author_1": {
                "filename": author1_input.name,
                "relative_path": str(target_a1.relative_to(output_dir)).replace("\\", "/"),
                "sha256": copied_a1,
                "verified": True
            },
            "author_2": {
                "filename": author2_input.name,
                "relative_path": str(target_a2.relative_to(output_dir)).replace("\\", "/"),
                "sha256": copied_a2,
                "verified": True
            },
            "mapping": {
                "filename": mapping_path.name,
                "relative_path": str(target_map.relative_to(output_dir)).replace("\\", "/"),
                "sha256": copied_map,
                "verified": True
            }
        }

        print(f"[*] Ingesting mapping from {mapping_path}...")
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping_data = json.load(f)

        map_assessments = mapping_data.get("assessments", {})
        if not map_assessments:
            raise ValueError(f"Mapping file {mapping_path} contains no 'assessments' block.")

        expected_a1_ids = {aid for aid, meta in map_assessments.items() if meta.get("assigned_author") == "author_1"}
        expected_a2_ids = {aid for aid, meta in map_assessments.items() if meta.get("assigned_author") == "author_2"}

        print(f"[*] Ingesting Author 1 workbook from {author1_input}...")
        auth1_records = load_author_file(author1_input)
        validate_author_records_against_mapping(auth1_records, map_assessments)
        a1_complete, a1_report = validate_workbook_completion(auth1_records, "author_1", expected_a1_ids)

        print(f"[*] Ingesting Author 2 workbook from {author2_input}...")
        auth2_records = load_author_file(author2_input)
        validate_author_records_against_mapping(auth2_records, map_assessments)
        a2_complete, a2_report = validate_workbook_completion(auth2_records, "author_2", expected_a2_ids)

        # Write completion report
        with open(completion_report_path, "w", encoding="utf-8") as f:
            json.dump({"author_1": a1_report, "author_2": a2_report}, f, indent=2)
        output_file_hashes["WORKBOOK_COMPLETION_REPORT.json"] = compute_sha256(completion_report_path)

        if not a1_complete or not a2_complete:
            manifest_status = "INCOMPLETE"
            raise WorkbookIncompleteError(
                "Workbooks are incomplete or contain enum/semantic validation errors. "
                "See WORKBOOK_COMPLETION_REPORT.json for detailed diagnostics."
            )

        # Pre-metric input verification: verify inputs have not drifted during read
        mid_a1_hash = compute_sha256(author1_input)
        mid_a2_hash = compute_sha256(author2_input)
        mid_map_hash = compute_sha256(mapping_path)
        if mid_a1_hash != pre_a1_hash:
            manifest_status = "FAILED_INPUT_MUTATION"
            raise HashVerificationError(f"Input drift detected on {author1_input} during ingestion!")
        if mid_a2_hash != pre_a2_hash:
            manifest_status = "FAILED_INPUT_MUTATION"
            raise HashVerificationError(f"Input drift detected on {author2_input} during ingestion!")
        if mid_map_hash != pre_map_hash:
            manifest_status = "FAILED_INPUT_MUTATION"
            raise HashVerificationError(f"Input drift detected on {mapping_path} during ingestion!")

        # Assemble unique items
        dict_a1 = {r["assessment_id"]: r for r in auth1_records}
        dict_a2 = {r["assessment_id"]: r for r in auth2_records}

        unique_items_dict: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        for aid, meta in map_assessments.items():
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

        unique_items_list = list(unique_items_dict.values())
        overlap_items = [it for it in unique_items_list if it["meta"]["is_overlap"]]

        print(f"[*] Evaluating inter-assessor reliability on {len(overlap_items)} shared items...")
        agreement_summary, disagreement_ledger = evaluate_inter_assessor_agreement(overlap_items)

        print(f"[*] Computing primary non-double-counting population metrics...")
        primary_metrics = compute_population_metrics(unique_items_list, use_secondary_for_overlap=False)

        print(f"[*] Computing Secondary Assessor Sensitivity Scenario...")
        sensitivity_metrics = compute_population_metrics(unique_items_list, use_secondary_for_overlap=True)

        merged_ledger = []
        for it in unique_items_list:
            meta = it["meta"]
            merged_ledger.append({
                "query_id": meta["query_id"],
                "condition": meta["condition"],
                "pipeline": meta["pipeline"],
                "sample_stratum": meta["sample_stratum"],
                "is_overlap": meta["is_overlap"],
                "primary_author": meta["primary_author"],
                "primary_evaluation": it["author_1_eval"] if meta["primary_author"] == "author_1" else it["author_2_eval"],
                "secondary_evaluation": it["author_2_eval"] if meta["primary_author"] == "author_1" else it["author_1_eval"] if meta["is_overlap"] else None
            })

        # Pre-emission input verification: verify inputs have not drifted before writing metrics
        post_a1_hash = compute_sha256(author1_input)
        post_a2_hash = compute_sha256(author2_input)
        post_map_hash = compute_sha256(mapping_path)
        if post_a1_hash != pre_a1_hash or post_a2_hash != pre_a2_hash or post_map_hash != pre_map_hash:
            manifest_status = "FAILED_INPUT_MUTATION"
            raise HashVerificationError("Concurrent drift detected on input files before writing metrics!")

        # Save output artifacts
        merged_path = output_dir / "merged_author_assessments.json"
        summary_path = output_dir / "assessment_statistical_summary.json"

        with open(merged_path, "w", encoding="utf-8") as f:
            json.dump({
                "inter_assessor_agreement": agreement_summary,
                "disagreement_count": len(disagreement_ledger),
                "disagreements": disagreement_ledger,
                "merged_records": merged_ledger
            }, f, indent=2)
        output_file_hashes["merged_author_assessments.json"] = compute_sha256(merged_path)

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({
                "primary_point_estimates": primary_metrics,
                "secondary_assessor_sensitivity_scenario": sensitivity_metrics
            }, f, indent=2)
        output_file_hashes["assessment_statistical_summary.json"] = compute_sha256(summary_path)

        manifest_status = "COMPLETED_AND_VERIFIED"

    except WorkbookIncompleteError as e:
        manifest_status = "INCOMPLETE"
        error_info = str(e)
        raise
    except ItemTamperingError as e:
        manifest_status = "FAILED"
        error_info = str(e)
        raise
    except HashVerificationError as e:
        manifest_status = "FAILED_INPUT_MUTATION"
        error_info = str(e)
        raise
    except Exception as e:
        manifest_status = "FAILED"
        error_info = str(e)
        raise
    finally:
        terminal_a1_hash = "UNAVAILABLE"
        terminal_a2_hash = "UNAVAILABLE"
        terminal_map_hash = "UNAVAILABLE"
        hash_read_failed = False

        try:
            terminal_a1_hash = compute_sha256(author1_input)
        except Exception as e_a1:
            hash_read_failed = True
            if error_info is None:
                error_info = f"Failed to compute terminal hash for author 1 input: {type(e_a1).__name__}: {e_a1}"

        try:
            terminal_a2_hash = compute_sha256(author2_input)
        except Exception as e_a2:
            hash_read_failed = True
            if error_info is None:
                error_info = f"Failed to compute terminal hash for author 2 input: {type(e_a2).__name__}: {e_a2}"

        try:
            terminal_map_hash = compute_sha256(mapping_path)
        except Exception as e_map:
            hash_read_failed = True
            if error_info is None:
                error_info = f"Failed to compute terminal hash for mapping: {type(e_map).__name__}: {e_map}"

        mutated_a1 = (terminal_a1_hash != pre_a1_hash)
        mutated_a2 = (terminal_a2_hash != pre_a2_hash)
        mutated_map = (terminal_map_hash != pre_map_hash)
        terminal_drift = mutated_a1 or mutated_a2 or mutated_map

        if hash_read_failed:
            manifest_status = "FAILED"
        elif terminal_drift:
            manifest_status = "FAILED_INPUT_MUTATION"
            if error_info is None:
                error_info = (
                    f"Terminal input hash mutation detected: "
                    f"author_1_mutated={mutated_a1}, "
                    f"author_2_mutated={mutated_a2}, "
                    f"mapping_mutated={mutated_map}"
                )

        certified_for_production = (manifest_status == "COMPLETED_AND_VERIFIED")

        manifest = {
            "execution_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "python_version": sys.version,
            "processor_script": "scripts/process_author_assessments.py",
            "processor_version": "v5_hardened",
            "processor_sha256": compute_sha256(Path(__file__).resolve()),
            "status": manifest_status,
            "certified_for_production": certified_for_production,
            "error_info": error_info,
            "input_files": {
                "author1_workbook": {
                    "path": str(author1_input.resolve()),
                    "pre_read_sha256": pre_a1_hash,
                    "terminal_sha256": terminal_a1_hash,
                    "mutated": mutated_a1
                },
                "author2_workbook": {
                    "path": str(author2_input.resolve()),
                    "pre_read_sha256": pre_a2_hash,
                    "terminal_sha256": terminal_a2_hash,
                    "mutated": mutated_a2
                },
                "private_mapping": {
                    "path": str(mapping_path.resolve()),
                    "pre_read_sha256": pre_map_hash,
                    "terminal_sha256": terminal_map_hash,
                    "mutated": mutated_map
                }
            },
            "preserved_originals": preserved_hashes,
            "output_files": output_file_hashes
        }

        prior_exc = sys.exc_info()[1]
        manifest_write_error = None
        integrity_path = output_dir / "EXECUTION_INTEGRITY_MANIFEST.json"

        try:
            manifest_json_str = json.dumps(manifest, indent=2)
            # Exclusive creation mode ("x") prevents overwriting or truncating any existing report
            with open(integrity_path, "x", encoding="utf-8") as f:
                f.write(manifest_json_str)

            # Read back and validate the written manifest before returning success
            with open(integrity_path, "r", encoding="utf-8") as rf:
                readback = json.load(rf)
            if readback.get("status") != manifest["status"]:
                raise RuntimeError(
                    f"Execution integrity manifest readback status mismatch: {readback.get('status')} != {manifest['status']}"
                )
        except Exception as manifest_err:
            manifest_write_error = manifest_err
            print(f"[FATAL] Failed to write EXECUTION_INTEGRITY_MANIFEST.json: {manifest_err}", file=sys.stderr)

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

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Process and merge author assessment workbooks (v4).")
    parser.add_argument("--author1-input", type=Path, required=True, help="Path to Author 1 workbook (.xlsx or .tsv)")
    parser.add_argument("--author2-input", type=Path, required=True, help="Path to Author 2 workbook (.xlsx or .tsv)")
    parser.add_argument("--mapping", type=Path, required=True, help="Path to PRIVATE_KEY_MAPPING.json")
    parser.add_argument("--output-dir", type=Path, required=True, help="Fresh non-existent output directory")

    args = parser.parse_args()

    try:
        manifest = process_author_assessments(
            args.author1_input,
            args.author2_input,
            args.mapping,
            args.output_dir
        )
        print(f"[OK] Processing complete! Manifest written to: {args.output_dir / 'EXECUTION_INTEGRITY_MANIFEST.json'}")
    except WorkbookIncompleteError as e:
        print(f"[!] Workbooks are incomplete: {e}", file=sys.stderr)
        sys.exit(2)
    except ItemTamperingError as e:
        print(f"[!] Item tampering detected: {e}", file=sys.stderr)
        sys.exit(3)
    except HashVerificationError as e:
        print(f"[!] Hash verification error: {e}", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"[!] Processing failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
