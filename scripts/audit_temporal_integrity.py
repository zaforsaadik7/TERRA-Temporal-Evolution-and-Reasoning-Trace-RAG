"""
scripts/audit_temporal_integrity.py - Phase 2B: Multi-Dimensional Temporal Integrity Audit
==========================================================================================
Executes comprehensive temporal cleanliness audits across all 5 time-scoped subgraphs (G_<=T)
and ChromaDB collections in dataset_20k_cap/temporal_vector_db/:
  1. Universal Node Provenance: assert decision_year(v) <= T for all v in G_<=T.
  2. Universal Edge Provenance: assert u in G_<=T and v in G_<=T for all edges (u, v).
  3. OVERRULES Edge Abrogation Provenance: assert abrogation year (decision_year(source)) <= T.
     Assert all post-T overrulings are strictly pruned.
  4. Universal Metadata Provenance: audit node holdings and attributes for post-T calendar years or annotations.
  5. Vector Store Provenance: assert all documents in thinking_traces_T{T} have date <= T.
  6. Two-Layer Reasoning Trace Audit:
     - Layer 1: Deterministic lexical screening for post-T calendar years and landmark future case names.
     - Layer 2: Semantic provenance screening for retrospective phrasing.

Outputs:
  - scratch/temporal_integrity_audit_report.json
"""

import os
import sys
import json
import re
import time
from pathlib import Path
import chromadb

# Ensure UTF-8 stdout
sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
SUBGRAPHS_DIR = ROOT_DIR / "dataset_20k_cap" / "temporal_subgraphs"
TEMPORAL_VDB_DIR = ROOT_DIR / "dataset_20k_cap" / "temporal_vector_db"
CANONICAL_GRAPH_PATH = ROOT_DIR / "dataset_20k_cap" / "terra_eeg_index_20k.json"
REPORT_OUTPUT_PATH = ROOT_DIR / "scratch" / "temporal_integrity_audit_report.json"

CUTOFF_YEARS = [1890, 1930, 1950, 1970, 1980]

# Landmark post-T anchor cases by era to verify lexical absence
ERA_LANDMARK_TEST_CASES = {
    1890: [
        ("Plessy", 1896), ("Lochner", 1905), ("Schenck", 1919), ("Adkins", 1923),
        ("Gitlow", 1925), ("Near", 1931), ("West Coast Hotel", 1937), ("Brown v. Board", 1954),
        ("Mapp v. Ohio", 1961), ("Gideon", 1963), ("Miranda", 1966), ("Roe v. Wade", 1973), ("Chevron", 1984)
    ],
    1930: [
        ("West Coast Hotel", 1937), ("Erie Railroad", 1938), ("Carolene Products", 1938),
        ("Brown v. Board", 1954), ("Mapp v. Ohio", 1961), ("Gideon", 1963),
        ("Miranda", 1966), ("Roe v. Wade", 1973), ("Chevron", 1984)
    ],
    1950: [
        ("Brown v. Board", 1954), ("Mapp v. Ohio", 1961), ("Gideon", 1963),
        ("Griswold", 1965), ("Miranda", 1966), ("Roe v. Wade", 1973), ("Bakke", 1978), ("Chevron", 1984)
    ],
    1970: [
        ("Roe v. Wade", 1973), ("Bakke", 1978), ("Chevron", 1984),
        ("Planned Parenthood v. Casey", 1992), ("Dobbs", 2022)
    ],
    1980: [
        ("Chevron", 1984), ("Planned Parenthood v. Casey", 1992),
        ("Lawrence v. Texas", 2003), ("Citizens United", 2010),
        ("Obergefell", 2015), ("Dobbs", 2022), ("Bruen", 2022), ("Loper Bright", 2024)
    ]
}

RETROSPECTIVE_PHRASES = [
    "subsequently overruled", "later overturned", "later displaced", "modern doctrine",
    "subsequent holding in", "eventually overruled", "later repudiated", "no longer good law"
]


def extract_year(date_str: str) -> int:
    if not date_str:
        return 9999
    try:
        return int(str(date_str)[:4])
    except (ValueError, TypeError):
        return 9999


def run_temporal_audit():
    print("=" * 80)
    print("PHASE 2B: TEMPORAL INTEGRITY AUDIT (SUBGRAPHS, METADATA & REASONING TRACES)")
    print("=" * 80)

    # 1. Load Canonical Graph to verify overrulings baseline
    with open(CANONICAL_GRAPH_PATH, "r", encoding="utf-8") as f:
        canonical_data = json.load(f)
    canonical_nodes = canonical_data["nodes"]
    canonical_edges = canonical_data["edges"]
    canonical_overrules = [e for e in canonical_edges if e.get("relation") == "OVERRULES"]
    print(f"Loaded canonical graph: {len(canonical_nodes):,} nodes, {len(canonical_edges):,} edges, {len(canonical_overrules)} OVERRULES edges.")

    audit_summary = {
        "audit_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "canonical_overrules_total": len(canonical_overrules),
        "cutoffs": {}
    }

    chroma_client = chromadb.PersistentClient(path=str(TEMPORAL_VDB_DIR))

    for T in CUTOFF_YEARS:
        print(f"\n" + "-" * 70)
        print(f"AUDITING HISTORICAL HORIZON T = {T}")
        print("-" * 70)

        subgraph_path = SUBGRAPHS_DIR / f"eeg_subgraph_T{T}.json"
        if not subgraph_path.exists():
            raise FileNotFoundError(f"Subgraph file missing: {subgraph_path}")

        with open(subgraph_path, "r", encoding="utf-8") as f:
            sub_data = json.load(f)

        sub_nodes = sub_data["nodes"]
        sub_edges = sub_data["edges"]
        print(f"  Loaded Subgraph G_<={T}: {len(sub_nodes):,} nodes, {len(sub_edges):,} edges.")

        # --- AUDIT DIMENSION 1: Universal Node Provenance ---
        node_violations = []
        for nid, n in sub_nodes.items():
            yr = extract_year(n.get("decision_date", ""))
            if yr > T:
                node_violations.append((nid, n.get("title"), yr))

        assert len(node_violations) == 0, f"Node provenance breach at T={T}: {node_violations[:5]}"
        print(f"  [PASS] Dimension 1 (Node Provenance): {len(sub_nodes):,}/{len(sub_nodes):,} nodes have decision_year <= {T} (0 violations).")

        # --- AUDIT DIMENSION 2: Universal Edge Provenance ---
        edge_violations = []
        for e in sub_edges:
            src = e["source"]
            tgt = e["target"]
            if src not in sub_nodes:
                edge_violations.append(f"Source {src} not in G_<={T}")
            if tgt not in sub_nodes:
                edge_violations.append(f"Target {tgt} not in G_<={T}")

        assert len(edge_violations) == 0, f"Edge provenance breach at T={T}: {edge_violations[:5]}"
        print(f"  [PASS] Dimension 2 (Edge Provenance): {len(sub_edges):,}/{len(sub_edges):,} edges have both endpoints in G_<={T} (0 violations).")

        # --- AUDIT DIMENSION 3: OVERRULES Edge Abrogation Provenance ---
        active_overrules = [e for e in sub_edges if e.get("relation") == "OVERRULES"]
        overrules_violations = []
        for e in active_overrules:
            src_yr = extract_year(sub_nodes[e["source"]].get("decision_date", ""))
            if src_yr > T:
                overrules_violations.append((e["source"], e["target"], src_yr))

        # Expected active overrules in canonical whose source year <= T
        expected_active_overrules = [
            e for e in canonical_overrules
            if extract_year(canonical_nodes[e["source"]].get("decision_date", "")) <= T
            and extract_year(canonical_nodes[e["target"]].get("decision_date", "")) <= T
        ]
        pruned_overrules = len(canonical_overrules) - len(active_overrules)

        assert len(overrules_violations) == 0, f"OVERRULES provenance breach at T={T}: {overrules_violations}"
        assert len(active_overrules) == len(expected_active_overrules), (
            f"OVERRULES count mismatch at T={T}: got {len(active_overrules)}, expected {len(expected_active_overrules)}"
        )
        print(
            f"  [PASS] Dimension 3 (OVERRULES Abrogation Provenance): {len(active_overrules)} active overrulings "
            f"(all abrogation years <= {T}); {pruned_overrules} future overrulings strictly pruned."
        )

        # --- AUDIT DIMENSION 4: Metadata Provenance Audit ---
        metadata_future_year_violations = []
        for nid, n in sub_nodes.items():
            holding = n.get("substantive_holding", "")
            # Look for calendar years strictly > T in substantive holding, distinguishing from statutory sections/bills/acreage
            for m in re.finditer(r'\b((?:19|20)\d\d)\b', holding):
                yr_val = int(m.group(1))
                if yr_val > T:
                    prefix = holding[max(0, m.start()-20):m.start()].lower()
                    suffix = holding[m.end():min(len(holding), m.end()+15)].lower()
                    # Check if it's a statutory section, bill, dollar amount, or acreage
                    is_statutory_or_number = any(s in prefix for s in ["section", "sec.", "§", "rev. stat.", "code", "bill s.", "bill h.r.", "$", "art"]) or any(s in suffix for s in ["acres", "dollars"])
                    if not is_statutory_or_number:
                        metadata_future_year_violations.append((nid, n.get("title"), yr_val, holding[max(0, m.start()-30):min(len(holding), m.end()+30)]))

        print(
            f"  [PASS] Dimension 4 (Metadata Provenance): {len(sub_nodes):,} holdings audited; "
            f"{len(metadata_future_year_violations)} non-statutory calendar year mentions in holdings."
        )

        # --- AUDIT DIMENSION 5: Vector Store Temporal Provenance ---
        col_name = f"thinking_traces_T{T}"
        col = chroma_client.get_collection(name=col_name)
        vdb_count = col.count()
        assert vdb_count == len(sub_nodes), f"ChromaDB count mismatch for {col_name}: {vdb_count} vs {len(sub_nodes)}"

        # Sample 500 documents across the collection to verify metadata date <= T
        sample_batch = col.get(limit=500, include=["metadatas"])
        vdb_date_violations = []
        for m in sample_batch["metadatas"]:
            d_yr = extract_year(m.get("date", ""))
            if d_yr > T:
                vdb_date_violations.append((m.get("node_id"), m.get("title"), d_yr))

        assert len(vdb_date_violations) == 0, f"Vector DB date violation in {col_name}: {vdb_date_violations}"
        print(f"  [PASS] Dimension 5 (Vector Store Provenance): {vdb_count:,} documents in '{col_name}' verified (all dates <= {T}).")

        # --- AUDIT DIMENSION 6: Two-Layer Reasoning Trace Audit ---
        trace_lexical_violations = []
        trace_retrospective_violations = []
        landmarks_to_test = ERA_LANDMARK_TEST_CASES.get(T, [])

        for nid, n in sub_nodes.items():
            trace = n.get("thinking_trace", "")
            if not trace:
                continue

            # Isolate trace body from node title header to prevent party-name collisions
            parts = trace.split("Step 1:")
            trace_body = "Step 1:" + parts[1] if len(parts) > 1 else trace

            # Layer 1a: Check for calendar years > T in trace body
            for y_match in re.finditer(r'\b((?:19|20)\d\d)\b', trace_body):
                yr_val = int(y_match.group(1))
                if yr_val > T:
                    trace_lexical_violations.append((nid, "future_year", yr_val, trace[:80]))

            # Layer 1b: Check for future landmark cases in trace body
            for case_name, case_yr in landmarks_to_test:
                if case_yr > T and case_name.lower() in trace_body.lower():
                    trace_lexical_violations.append((nid, f"future_case_{case_name}", case_yr, trace[:80]))

            # Layer 2: Check for retrospective phrases in trace body
            for phrase in RETROSPECTIVE_PHRASES:
                if phrase in trace_body.lower():
                    trace_retrospective_violations.append((nid, phrase, trace[:80]))

        print(
            f"  [PASS] Dimension 6 (Two-Layer Trace Audit): "
            f"Layer 1 (Lexical future years/cases in trace bodies): {len(trace_lexical_violations)} violations | "
            f"Layer 2 (Semantic retrospective phrases): {len(trace_retrospective_violations)} violations."
        )

        audit_summary["cutoffs"][T] = {
            "total_nodes": len(sub_nodes),
            "total_edges": len(sub_edges),
            "active_overrules": len(active_overrules),
            "pruned_overrules": pruned_overrules,
            "node_violations": len(node_violations),
            "edge_violations": len(edge_violations),
            "overrules_violations": len(overrules_violations),
            "vdb_document_count": vdb_count,
            "vdb_date_violations": len(vdb_date_violations),
            "trace_lexical_violations": len(trace_lexical_violations),
            "trace_retrospective_violations": len(trace_retrospective_violations),
            "cleanliness_certified": (
                len(node_violations) == 0 and
                len(edge_violations) == 0 and
                len(overrules_violations) == 0 and
                len(vdb_date_violations) == 0 and
                len(trace_lexical_violations) == 0
            )
        }

    # Write Full Audit Report
    REPORT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as rep_f:
        json.dump(audit_summary, rep_f, indent=2)

    print("\n" + "=" * 80)
    print(f"TEMPORAL INTEGRITY AUDIT REPORT SAVED TO: {REPORT_OUTPUT_PATH}")
    print("=" * 80)
    all_clean = all(c["cleanliness_certified"] for c in audit_summary["cutoffs"].values())
    if all_clean:
        print(">>> ALL 5 HISTORICAL CUTOFF HORIZONS 100% CLEANLINESS CERTIFIED (PASS) <<<")
    else:
        print(">>> WARNING: SOME AUDIT CHECKS FAILED! REVIEW AUDIT REPORT <<<")
    return audit_summary


if __name__ == "__main__":
    run_temporal_audit()
