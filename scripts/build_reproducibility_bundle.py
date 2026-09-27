#!/usr/bin/env python3
"""
scripts/build_reproducibility_bundle.py
=======================================
Builds a curated, standalone, clean reproducibility bundle for the TERRA paper.

Enforces User Annotation 1 (Requirement 5):
  "For the final paper, maintain a clean reproducibility bundle containing only
   approved source files, scripts, data manifests, and logs."

Filters out all legacy un-tracked scratch artifacts (25,000+ files), packaging
only verified and approved research assets into:
  - TERRA_Reproducibility_Bundle.zip
  - logs/reproducibility_bundle_manifest.json
"""

import os
import sys
import json
import zipfile
import hashlib
from datetime import datetime, timezone

ROOT_DIR = os.path.abspath(".")
BUNDLE_ZIP = os.path.join(ROOT_DIR, "TERRA_Reproducibility_Bundle.zip")
BUNDLE_MANIFEST = os.path.join(ROOT_DIR, "logs", "reproducibility_bundle_manifest.json")

# Approved File Patterns & Explicit Targets
APPROVED_EXPLICIT_FILES = [
    # Core Architecture
    "ask_terra.py",
    "README.md",
    "TERRA_43_ISSUES_MASTER_CHECKLIST_new ones added.md",

    # Benchmarks & Subgraphs
    "terra_350_benchmark.json",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1890.json",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1930.json",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1950.json",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1970.json",
    "dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T1980.json",

    # Core Execution & Governance Scripts
    "scripts/build_repo_baseline_manifest.py",
    "scripts/task_manifest_guard.py",
    "scripts/build_reproducibility_bundle.py",
    "scripts/run_temporal_expansion_eval.py",
    "scripts/verify_issue19_deliverables.py",
    "scripts/bundle_paper_for_compilation.py",
    "scripts/test_paper_macros.py",
    "scripts/check_paper_v2_consistency.py",

    # Governance & Audit Artifacts: Issue 19
    "logs/baseline_manifest_post_issue19.json",
    "logs/baseline_manifest_post_issue19.txt",
    "logs/issue19_preflight_manifest.json",
    "logs/issue19_preflight_manifest.txt",
    "logs/issue19_manifest_audit.json",
    "logs/issue19_manifest_audit.txt",
    "logs/issue19_closeout.txt",
    "logs/issue19_phase1_prereg.txt",
    "logs/issue19_phase2_execution.txt",
    "logs/issue19_phase3_validation.txt",
    "data/issue19_temporal_update_queries.json",
    "scratch/issue19_metrics_summary.json",
    "scratch/issue19_prereg.json",
    "scratch/issue19_query_stratification.json",

    # Governance & Audit Artifacts: Issue 20
    "scripts/audit_corpus_length_filtering.py",
    "scripts/generate_issue20_macros.py",
    "scripts/verify_issue20_landmark_exclusions.py",
    "data/landmark_scotus_catalog.json",
    "data/issue20_length_filtering_audit.json",
    "logs/issue20_length_filtering_audit.txt",
    "logs/issue20_closeout_correction.txt",

    # Governance & Audit Artifacts: Issue 21
    "scripts/audit_citation_edge_precision.py",
    "scripts/generate_issue21_macros.py",
    "data/issue21_preflight.json",
    "logs/issue21_preflight.txt",
    "data/issue21_citation_precision_audit.json",
    "data/issue21_same_year_edges.json",
    "logs/issue21_citation_edge_audit.txt",
    "logs/issue21_closeout.txt",
    "logs/issue21_reproducibility_correction.txt",

    # Governance & Audit Artifacts: Issue 22
    "scripts/verify_issue22_preflight.py",
    "scripts/audit_doctrinal_taxonomy.py",
    "scripts/generate_issue22_macros.py",
    "data/issue22_preflight.json",
    "logs/issue22_preflight.txt",
    "data/issue22_taxonomy_audit.json",
    "logs/issue22_taxonomy_audit.txt",
    "data/cache/issue22_judge_cache.json",
    "data/cache/issue22_adjudicator_cache.json",
    "logs/issue22_closeout.txt",

    # Governance & Audit Artifacts: Issue 23
    "scripts/verify_issue23_preflight.py",
    "scripts/verify_baseline_parameters.py",
    "data/issue23_preflight.json",
    "logs/issue23_preflight.txt",
    "logs/issue23_closeout.txt",
    "Paper/tables/table_baseline_specifications.tex",
]

APPROVED_DIRS = [
    ("Paper", [".tex", ".bib", ".sty", ".cls", ".pdf"]),
]

def hash_file(abs_path):
    h = hashlib.sha256()
    with open(abs_path, "rb") as f:
        while chunk := f.read(1048576):
            h.update(chunk)
    return h.hexdigest()

def collect_approved_files():
    file_list = []

    # 1. Add explicit files
    for rel_p in APPROVED_EXPLICIT_FILES:
        abs_p = os.path.join(ROOT_DIR, rel_p.replace("/", os.sep))
        if os.path.isfile(abs_p):
            file_list.append(rel_p)
        else:
            print(f"Notice: explicit approved file not present: {rel_p}")

    # 2. Add approved directories
    for dir_rel, extensions in APPROVED_DIRS:
        dir_abs = os.path.join(ROOT_DIR, dir_rel)
        if not os.path.isdir(dir_abs):
            continue
        for root, dirs, files in os.walk(dir_abs):
            # Skip hidden or build dirs
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in extensions:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, ROOT_DIR).replace("\\", "/")
                    if rel_p not in file_list:
                        file_list.append(rel_p)

    file_list.sort()
    return file_list

def main():
    print("=" * 80)
    print("BUILDING CLEAN TERRA REPRODUCIBILITY BUNDLE")
    print("=" * 80)

    files_to_bundle = collect_approved_files()
    print(f"Total approved files to package: {len(files_to_bundle)}")

    total_bytes = 0
    records = {}

    print(f"Archiving files into {BUNDLE_ZIP} ...")
    with zipfile.ZipFile(BUNDLE_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_p in files_to_bundle:
            abs_p = os.path.join(ROOT_DIR, rel_p.replace("/", os.sep))
            sz = os.path.getsize(abs_p)
            sha = hash_file(abs_p)
            total_bytes += sz
            records[rel_p] = {
                "size_bytes": sz,
                "sha256": sha
            }
            zf.write(abs_p, arcname=rel_p)
            print(f"  + [{sz:8d} B] {rel_p}")

    bundle_sha = hash_file(BUNDLE_ZIP)
    bundle_size = os.path.getsize(BUNDLE_ZIP)

    # Write Bundle Manifest
    manifest_payload = {
        "bundle_metadata": {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "bundle_zip_filename": os.path.basename(BUNDLE_ZIP),
            "bundle_zip_size_bytes": bundle_size,
            "bundle_zip_sha256": bundle_sha,
            "total_files_packaged": len(records),
            "uncompressed_total_bytes": total_bytes
        },
        "packaged_files": records
    }

    os.makedirs(os.path.dirname(BUNDLE_MANIFEST), exist_ok=True)
    with open(BUNDLE_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)

    print("=" * 80)
    print(f"[SUCCESS] Clean Reproducibility Bundle Created:")
    print(f"  Archive:  {BUNDLE_ZIP} ({bundle_size:,} bytes)")
    print(f"  SHA256:   {bundle_sha}")
    print(f"  Manifest: {BUNDLE_MANIFEST}")
    print(f"  Files:    {len(records)} approved files packaged")
    print("=" * 80)

if __name__ == "__main__":
    main()
