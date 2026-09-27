"""
scripts/build_temporal_subgraphs_and_views.py - Phase 2: Time-Scoped Subgraph Construction & Provenance-Safe Views
===================================================================================================================
Constructs time-scoped Event Evolution Graphs (G_<=T) and provenance-safe ChromaDB vector collections
for all 5 pre-registered historical cutoff horizons:
  - T1 = 1890
  - T2 = 1930
  - T3 = 1950
  - T4 = 1970
  - T5 = 1980

Core Invariants:
1. Universal Node Invariant: node v is in G_<=T iff decision_year(v) <= T.
2. Universal Edge Invariant: edge (u, v) is in G_<=T iff decision_year(u) <= T and decision_year(v) <= T.
3. OVERRULES Edge Invariant: abrogation year (decision_year(source)) <= T. Prunes all future overrulings.
4. Non-Mutation Invariant: Canonical dataset_20k_cap/terra_eeg_index_20k.json and vector_db_20k are 100% unmutated.
5. Vector Parity Invariant: Embeddings and documents are preserved without re-embedding artifacts.
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
import chromadb

ROOT_DIR = Path(__file__).resolve().parent.parent
CANONICAL_GRAPH_PATH = ROOT_DIR / "dataset_20k_cap" / "terra_eeg_index_20k.json"
CANONICAL_VECTOR_PATH = ROOT_DIR / "dataset_20k_cap" / "vector_db_20k"
CANONICAL_SHA256 = "7aa6db466100ae384873a40dd2da2043a2f85a1ef4adb5859e2b338a057e98ad"

OUTPUT_SUBGRAPHS_DIR = ROOT_DIR / "dataset_20k_cap" / "temporal_subgraphs"
OUTPUT_TEMPORAL_VDB_DIR = ROOT_DIR / "dataset_20k_cap" / "temporal_vector_db"

CUTOFF_YEARS = [1890, 1930, 1950, 1970, 1980]


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def extract_year(date_str: str) -> int:
    if not date_str:
        return 9999
    try:
        return int(str(date_str)[:4])
    except (ValueError, TypeError):
        return 9999


def build_temporal_subgraphs():
    print("=" * 80)
    print("PHASE 2: TIME-SCOPED SUBGRAPH CONSTRUCTION & PROVENANCE-SAFE VIEWS")
    print("=" * 80)

    # 1. Verify Canonical Graph Integrity
    print(f"\n[1/4] Verifying canonical graph checksum: {CANONICAL_GRAPH_PATH}...")
    actual_hash = compute_sha256(CANONICAL_GRAPH_PATH)
    if actual_hash != CANONICAL_SHA256:
        raise ValueError(
            f"CANONICAL GRAPH INTEGRITY FAILURE!\n"
            f"Expected: {CANONICAL_SHA256}\n"
            f"Actual:   {actual_hash}"
        )
    print(f"  -> Integrity Verified: SHA256 matches {actual_hash[:16]}... (PASS)")

    with open(CANONICAL_GRAPH_PATH, "r", encoding="utf-8") as f:
        canonical_data = json.load(f)

    nodes = canonical_data["nodes"]
    edges = canonical_data["edges"]
    print(f"  -> Loaded canonical graph: {len(nodes):,} nodes, {len(edges):,} edges.")

    OUTPUT_SUBGRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    subgraph_manifest = {}

    # 2. Construct G_<=T Subgraphs for each Cutoff
    print("\n[2/4] Constructing time-scoped subgraphs G_<=T...")
    for T in CUTOFF_YEARS:
        t0 = time.time()
        # Node filtering: decision_year <= T
        sub_nodes = {
            nid: ninfo for nid, ninfo in nodes.items()
            if extract_year(ninfo.get("decision_date", "")) <= T
        }

        # Edge filtering: both u and v in sub_nodes, and OVERRULES abrogation <= T
        sub_edges = []
        cites_count = 0
        overrules_count = 0
        pruned_overrules_count = 0

        for e in edges:
            src = e["source"]
            tgt = e["target"]
            if src in sub_nodes and tgt in sub_nodes:
                rel = e.get("relation", "CITES")
                if rel == "OVERRULES":
                    src_year = extract_year(nodes[src].get("decision_date", ""))
                    if src_year <= T:
                        sub_edges.append(e)
                        overrules_count += 1
                    else:
                        pruned_overrules_count += 1
                else:
                    sub_edges.append(e)
                    cites_count += 1

        subgraph_data = {
            "cutoff_year": T,
            "total_nodes": len(sub_nodes),
            "total_edges": len(sub_edges),
            "cites_edges": cites_count,
            "overrules_edges": overrules_count,
            "pruned_overrules": pruned_overrules_count,
            "nodes": sub_nodes,
            "edges": sub_edges,
            "build_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "source_canonical_hash": actual_hash
        }

        out_path = OUTPUT_SUBGRAPHS_DIR / f"eeg_subgraph_T{T}.json"
        with open(out_path, "w", encoding="utf-8") as out_f:
            json.dump(subgraph_data, out_f, indent=2)

        file_size_mb = out_path.stat().st_size / (1024 * 1024)
        elapsed = time.time() - t0

        subgraph_manifest[T] = {
            "path": str(out_path),
            "nodes": len(sub_nodes),
            "edges": len(sub_edges),
            "cites": cites_count,
            "overrules": overrules_count,
            "file_size_mb": round(file_size_mb, 2)
        }

        print(
            f"  -> Cutoff T={T}: {len(sub_nodes):,} nodes ({len(sub_nodes)/len(nodes)*100:.1f}%), "
            f"{len(sub_edges):,} edges ({cites_count:,} CITES, {overrules_count} OVERRULES, "
            f"{pruned_overrules_count} future overrules pruned) | {file_size_mb:.2f} MB ({elapsed:.2f}s)"
        )

    # 3. Build Provenance-Safe ChromaDB Collections
    print(f"\n[3/4] Building provenance-safe ChromaDB collections in: {OUTPUT_TEMPORAL_VDB_DIR}...")
    OUTPUT_TEMPORAL_VDB_DIR.mkdir(parents=True, exist_ok=True)

    src_client = chromadb.PersistentClient(path=str(CANONICAL_VECTOR_PATH))
    src_col = src_client.get_collection("thinking_traces")
    total_src_docs = src_col.count()
    print(f"  -> Source ChromaDB count: {total_src_docs:,} thinking traces.")

    dest_client = chromadb.PersistentClient(path=str(OUTPUT_TEMPORAL_VDB_DIR))

    # Fetch all records with embeddings from canonical vector db in batches
    print("  -> Fetching all records and precomputed embeddings from canonical ChromaDB...")
    fetch_batch_size = 2000
    all_records = []
    t_fetch = time.time()
    for offset in range(0, total_src_docs, fetch_batch_size):
        batch = src_col.get(
            limit=fetch_batch_size,
            offset=offset,
            include=["embeddings", "metadatas", "documents"]
        )
        for i in range(len(batch["ids"])):
            all_records.append({
                "id": batch["ids"][i],
                "embedding": batch["embeddings"][i],
                "metadata": batch["metadatas"][i],
                "document": batch["documents"][i],
                "year": extract_year(batch["metadatas"][i].get("date", ""))
            })
    print(f"  -> Fetched {len(all_records):,} records with embeddings in {time.time() - t_fetch:.2f}s.")

    # Populate each time-scoped collection
    insert_batch_size = 1000
    vector_manifest = {}

    for T in CUTOFF_YEARS:
        t_v = time.time()
        col_name = f"thinking_traces_T{T}"
        try:
            dest_client.delete_collection(name=col_name)
        except Exception:
            pass
        t_col = dest_client.create_collection(name=col_name)

        filtered = [r for r in all_records if r["year"] <= T]
        print(f"  -> Populating collection '{col_name}' ({len(filtered):,} docs)...")

        for b_idx in range(0, len(filtered), insert_batch_size):
            chunk = filtered[b_idx:b_idx + insert_batch_size]
            t_col.add(
                ids=[r["id"] for r in chunk],
                embeddings=[r["embedding"] for r in chunk],
                metadatas=[r["metadata"] for r in chunk],
                documents=[r["document"] for r in chunk]
            )

        v_count = t_col.count()
        assert v_count == len(filtered), f"Count mismatch in {col_name}: expected {len(filtered)}, got {v_count}"
        vector_manifest[T] = {
            "collection_name": col_name,
            "document_count": v_count,
            "build_time_s": round(time.time() - t_v, 2)
        }
        print(f"     [OK] Collection '{col_name}' verified with {v_count:,} documents ({time.time() - t_v:.2f}s).")

    # 4. Save Subgraph & Vector Manifest
    manifest_path = OUTPUT_SUBGRAPHS_DIR / "temporal_subgraphs_manifest.json"
    full_manifest = {
        "build_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "canonical_graph_sha256": actual_hash,
        "canonical_node_count": len(nodes),
        "canonical_edge_count": len(edges),
        "subgraphs": subgraph_manifest,
        "vector_views": vector_manifest
    }
    with open(manifest_path, "w", encoding="utf-8") as m_f:
        json.dump(full_manifest, m_f, indent=2)

    print(f"\n[4/4] Phase 2 Subgraph & Vector Manifest written to: {manifest_path}")
    print("=" * 80)
    print("PHASE 2 TIME-SCOPED SUBGRAPHS & VIEWS SUCCESSFULLY CONSTRUCTED")
    print("=" * 80)
    return full_manifest


if __name__ == "__main__":
    build_temporal_subgraphs()
