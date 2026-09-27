import os
import sys
import json
import time
import argparse
import logging
import warnings
import concurrent.futures
from pathlib import Path
from unittest.mock import MagicMock

# Suppress eyecite and library warnings
warnings.filterwarnings("ignore")
logging.getLogger("eyecite").setLevel(logging.CRITICAL)

# Mock fast_diff_match_patch to prevent ImportError on Windows
sys.modules['fast_diff_match_patch'] = MagicMock()
import eyecite

import chromadb
import networkx as nx

print("=== TERRA 20,000-CASE EEG GRAPH BUILDER & VECTOR DB INGESTOR ===\n")

manifest_path = Path("dataset_20k_cap/manifests/selection_manifest_20k.json")
raw_dir = Path("dataset_20k_cap/raw_cases")
source_10k_index = Path("dataset_10k_cap/terra_eeg_index_10k.json")
output_index_path = Path("dataset_20k_cap/terra_eeg_index_20k.json")
vector_db_path = Path("dataset_20k_cap/vector_db_20k")

def build_structured_trace(title, date, category):
    d_str = date[:4] if date and len(date) >= 4 else "Historical"
    cat_label = category.replace("_", " ").title()
    return (
        f"Thinking Trace — {title} ({d_str}): "
        f"Step 1: Identify operative legal and constitutional question under {cat_label} jurisprudence. "
        f"Step 2: Scrutinize governing Supreme Court precedent, historical canons, and statutory text. "
        f"Step 3: Evaluate factual record under binding standards of appellate review. "
        f"Step 4: Harmonize conflicting doctrines, distinguish non-controlling authority, and resolve claims. "
        f"Step 5: Pronounce holding, enter judgment, and transmit mandate."
    )

def parse_case_citations(node_id, full_text, cite_to_node, node_date):
    extracted_edges = []
    if not full_text:
        return extracted_edges
    try:
        cites = eyecite.get_citations(full_text)
        for c in cites:
            matched = (c.corrected_citation() if hasattr(c, 'corrected_citation') else c.matched_text()).strip()
            if matched in cite_to_node:
                target_id = cite_to_node[matched]
                if target_id != node_id:
                    extracted_edges.append((node_id, target_id))
    except Exception:
        pass
    return extracted_edges

def main():
    t0 = time.time()
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"Loaded {len(manifest):,} manifest entries.")

    # 1. Build Citation Resolution Map
    print("Building citation-to-node lookup table across all 20,000 cases...")
    cite_to_node = {}
    node_date_map = {}
    for entry in manifest:
        vol = entry["volume"]
        fname = entry["file_name"]
        node_id = f"{vol}_{fname}"
        node_date_map[node_id] = entry.get("decision_date") or ""
        for c in entry.get("citations", []):
            if isinstance(c, dict) and c.get("cite"):
                cite_to_node[c["cite"].strip()] = node_id
            elif isinstance(c, str):
                cite_to_node[c.strip()] = node_id

    print(f"Indexed {len(cite_to_node):,} official citations.")

    # 2. Load Existing 10k Nodes
    nodes = {}
    existing_10k_nodes = {}
    if source_10k_index.exists():
        with open(source_10k_index, "r", encoding="utf-8") as f:
            data_10k = json.load(f)
            existing_10k_nodes = data_10k.get("nodes", {})
        print(f"Loaded {len(existing_10k_nodes):,} base nodes from existing 10k index.")

    # 3. Process all 20,000 cases to populate nodes
    print("\nProcessing node metadata and text...")
    new_cases_count = 0
    inherited_count = 0
    missing_raw = 0

    cases_to_extract_cites = []

    for idx, entry in enumerate(manifest, 1):
        vol = entry["volume"]
        fname = entry["file_name"]
        node_id = f"{vol}_{fname}"
        category = entry.get("category", "other_subject")
        char_count = entry.get("char_count", 0)
        citations = [c.get("cite") for c in entry.get("citations", []) if isinstance(c, dict)]

        # Check if already present in 10k
        if node_id in existing_10k_nodes:
            base_info = dict(existing_10k_nodes[node_id])
            # Ensure text is present
            if not base_info.get("text"):
                raw_path = raw_dir / f"{node_id}.json"
                if raw_path.exists():
                    try:
                        with open(raw_path, "r", encoding="utf-8") as rf:
                            cdata = json.load(rf)
                        opinions = cdata.get("casebody", {}).get("opinions", [])
                        txt = "\n\n".join([op.get("text", "") for op in opinions if op.get("text")]).strip()
                        base_info["text"] = txt[:3000] if txt else base_info.get("title", "")
                    except Exception:
                        base_info["text"] = base_info.get("title", "")
                else:
                    base_info["text"] = base_info.get("title", "")
            nodes[node_id] = base_info
            inherited_count += 1
        else:
            raw_path = raw_dir / f"{node_id}.json"
            if not raw_path.exists():
                missing_raw += 1
                continue

            try:
                with open(raw_path, "r", encoding="utf-8") as rf:
                    cdata = json.load(rf)
            except Exception:
                missing_raw += 1
                continue

            title = cdata.get("name_abbreviation") or cdata.get("name") or entry.get("name_abbreviation") or entry.get("name") or "Unknown Case"
            date = cdata.get("decision_date") or entry.get("decision_date") or ""
            court = cdata.get("court", {}).get("name", "U.S. Supreme Court")

            cbody = cdata.get("casebody", {})
            opinions = cbody.get("opinions", []) if isinstance(cbody, dict) and isinstance(cbody.get("opinions"), list) else []
            full_text = "\n\n".join([op.get("text", "") for op in opinions if op.get("text")]).strip()

            trace_text = build_structured_trace(title, date, category)

            node_info = {
                "node_id": node_id,
                "title": title,
                "decision_date": date,
                "court": court,
                "category": category,
                "char_count": char_count,
                "thinking_trace": trace_text,
                "citations": citations,
                "edges_count": 0,
                "text": full_text[:3000] if full_text else title
            }
            nodes[node_id] = node_info
            new_cases_count += 1

            if full_text:
                cases_to_extract_cites.append((node_id, full_text, date))

    print(f"Nodes compiled: Total = {len(nodes):,} (Inherited = {inherited_count:,}, New = {new_cases_count:,}, Missing Raw = {missing_raw})")

    # 4. Extract Citation Edges
    print(f"\nExtracting citation edges across {len(cases_to_extract_cites):,} new full-text cases (20 workers)...")
    raw_edges = []

    # First, import existing edges from 10k index
    if source_10k_index.exists():
        with open(source_10k_index, "r", encoding="utf-8") as f:
            data_10k = json.load(f)
            for e in data_10k.get("edges", []):
                src, tgt = e.get("source"), e.get("target")
                if src in nodes and tgt in nodes and src != tgt:
                    raw_edges.append((src, tgt))
        print(f"Imported {len(raw_edges):,} valid edges from 10k baseline graph.")

    # Second, parallel eyecite extraction for new cases
    def worker(item):
        nid, txt, dt = item
        return parse_case_citations(nid, txt, cite_to_node, dt)

    t_cite = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        for idx, edges_list in enumerate(executor.map(worker, cases_to_extract_cites), 1):
            raw_edges.extend(edges_list)
            if idx % 2000 == 0 or idx == len(cases_to_extract_cites):
                print(f"  Processed {idx:5d}/{len(cases_to_extract_cites)} cases | Current total raw edges: {len(raw_edges):,}")

    print(f"Citation parsing completed in {time.time() - t_cite:.1f}s.")

    # 5. Deduplicate and Filter Edges (Preserving Temporal Directionality)
    print("\nFiltering and enforcing temporal directionality...")
    unique_edges = set()
    temporal_reversals = 0

    for src, tgt in raw_edges:
        if src not in nodes or tgt not in nodes or src == tgt:
            continue
        
        d_src = node_date_map.get(src, "")
        d_tgt = node_date_map.get(tgt, "")
        
        # Enforce t(citing) >= t(cited)
        if d_src and d_tgt and len(d_src) >= 4 and len(d_tgt) >= 4:
            y_src = int(d_src[:4])
            y_tgt = int(d_tgt[:4])
            if y_src < y_tgt:
                temporal_reversals += 1
                continue
                
        unique_edges.add((src, tgt))

    print(f"Final valid unique directed edges: {len(unique_edges):,} (Filtered {temporal_reversals:,} temporal reversals/errata)")

    formatted_edges = [{"source": s, "target": t, "relation": "CITES"} for s, t in sorted(unique_edges)]

    # Update edge counts on nodes
    edge_counts = {}
    for s, t in unique_edges:
        edge_counts[s] = edge_counts.get(s, 0) + 1
        edge_counts[t] = edge_counts.get(t, 0) + 1
    for nid, ninfo in nodes.items():
        ninfo["edges_count"] = edge_counts.get(nid, 0)

    # 6. Graph Topology Metrics
    print("\nComputing Graph Topology Metrics (NetworkX)...")
    G = nx.DiGraph()
    for nid in nodes:
        G.add_node(nid)
    for s, t in unique_edges:
        G.add_edge(s, t)

    total_opinions = G.number_of_nodes()
    total_edges = G.number_of_edges()
    density = nx.density(G)
    avg_degree = total_edges / total_opinions if total_opinions else 0.0

    wcc = list(nx.weakly_connected_components(G))
    largest_wcc = max(len(c) for c in wcc) if wcc else 0
    largest_wcc_pct = (largest_wcc / total_opinions * 100.0) if total_opinions else 0.0

    scc = list(nx.strongly_connected_components(G))
    largest_scc = max(len(c) for c in scc) if scc else 0

    print(f"Topology Summary:")
    print(f"  - Total Nodes (Opinions): {total_opinions:,}")
    print(f"  - Total Edges (Precedent): {total_edges:,}")
    print(f"  - Density: {density:.6f}")
    print(f"  - Average In/Out Degree: {avg_degree:.4f}")
    print(f"  - Weakly Connected Components: {len(wcc):,}")
    print(f"  - Largest WCC: {largest_wcc:,} ({largest_wcc_pct:.2f}%)")
    print(f"  - Strongly Connected Components: {len(scc):,}")
    print(f"  - Largest SCC: {largest_scc:,}")

    # 7. Write out EEG Index
    output_index_path.parent.mkdir(parents=True, exist_ok=True)
    index_data = {
        "nodes": nodes,
        "edges": formatted_edges,
        "total_nodes": len(nodes),
        "total_edges": len(formatted_edges),
        "graph_density": density,
        "average_degree": avg_degree,
        "largest_wcc_size": largest_wcc,
        "largest_wcc_pct": round(largest_wcc_pct, 2),
        "largest_scc_size": largest_scc,
        "build_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }

    with open(output_index_path, "w", encoding="utf-8") as out:
        json.dump(index_data, out, indent=2)

    print(f"\nEEG Index successfully written to: {output_index_path}")
    print(f"File size: {output_index_path.stat().st_size / (1024*1024):.2f} MB")

    # 8. Build ChromaDB Vector Store
    print(f"\nConnecting to ChromaDB at: {vector_db_path}...")
    chroma_client = chromadb.PersistentClient(path=str(vector_db_path))
    try:
        chroma_client.delete_collection(name="thinking_traces")
        print("Reset existing collection for clean rebuild.")
    except Exception:
        pass
    collection = chroma_client.create_collection(name="thinking_traces")

    print(f"Populating ChromaDB with {len(nodes):,} thinking traces...")
    batch_size = 500
    all_node_items = list(nodes.items())

    for b_idx in range(0, len(all_node_items), batch_size):
        batch = all_node_items[b_idx:b_idx + batch_size]
        docs, metas, ids = [], [], []

        for nid, ninfo in batch:
            title = ninfo.get("title", "Case")
            date = ninfo.get("decision_date", "")
            d_str = date[:4] if date else "Historical"
            trace = ninfo.get("thinking_trace", "")
            text_snip = ninfo.get("text", "")[:1000]

            doc_text = f"{title} ({d_str})\nThinking Trace: {trace}\nOpinion Snippet: {text_snip}"
            docs.append(doc_text)
            metas.append({
                "node_id": nid,
                "title": title,
                "date": date,
                "category": ninfo.get("category", "other_subject"),
                "char_count": ninfo.get("char_count", 0)
            })
            ids.append(nid)

        collection.upsert(documents=docs, metadatas=metas, ids=ids)
        if (b_idx + len(batch)) % 2500 == 0 or (b_idx + len(batch)) == len(all_node_items):
            print(f"  ChromaDB Upserted: {b_idx + len(batch):5d}/{len(all_node_items):5d} documents")

    print(f"\nChromaDB build complete. Collection count: {collection.count():,}")
    print(f"=== WORKSTREAM 1.5 INGESTION COMPLETED IN {time.time() - t0:.1f}s ===")

if __name__ == "__main__":
    main()
