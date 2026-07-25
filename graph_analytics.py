"""
graph_analytics.py — TERRA Graph Network Analysis Module
=========================================================
Computes publication-grade network metrics on the Event Evolution Graph (EEG)
for inclusion in the methodology section of the research paper.

Metrics computed:
  - Node/edge counts and density
  - Degree statistics (in/out/total, mean/max/min)
  - Clustering coefficient (on undirected projection)
  - Diameter and average shortest path (largest weakly connected component)
  - Strongly connected component analysis
  - Betweenness centrality (top-10 hub nodes)
  - Curated vs synthetic node breakdown

Output: terra_graph_metrics.json (embeddable in paper)
"""
import os
import json
import networkx as nx


def run_graph_analytics(index_file="terra_eeg_index.json", output_file="terra_graph_metrics.json"):
    if not os.path.exists(index_file):
        print(f"[ERROR] '{index_file}' not found. Run ingest_and_build.py first.")
        return

    print(f"\nLoading graph from '{index_file}'...")
    with open(index_file, "r", encoding="utf-8") as f:
        graph_data = json.load(f)
    eeg = nx.node_link_graph(graph_data, edges="edges" if "edges" in graph_data else "links")

    n_nodes = eeg.number_of_nodes()
    n_edges = eeg.number_of_edges()

    print(f"\n{'='*60}")
    print("  TERRA — Graph Network Analysis Report")
    print(f"{'='*60}")

    if n_nodes == 0:
        print("[WARNING] Graph has 0 nodes. Run ingestion first.")
        return

    # --- 1. Basic Stats ---
    density = nx.density(eeg)
    curated_nodes = [n for n in eeg.nodes if not eeg.nodes[n].get("is_synthetic", False)]
    synthetic_nodes = [n for n in eeg.nodes if eeg.nodes[n].get("is_synthetic", False)]

    print(f"\n[1] Basic Statistics")
    print(f"  Total Nodes (Cases):         {n_nodes}")
    print(f"  - Curated (Real) Cases:      {len(curated_nodes)}")
    print(f"  - Synthetic Supplement:      {len(synthetic_nodes)}")
    print(f"  Total Edges (Citations):     {n_edges}")
    print(f"  Graph Density:               {density:.6f}")

    # --- 2. Degree Distribution ---
    degrees     = dict(eeg.degree())
    in_degrees  = dict(eeg.in_degree())
    out_degrees = dict(eeg.out_degree())

    deg_vals = list(degrees.values())
    in_vals  = list(in_degrees.values())
    out_vals = list(out_degrees.values())

    print(f"\n[2] Degree Distribution")
    print(f"  Total Degree — Mean: {sum(deg_vals)/n_nodes:.2f} | Max: {max(deg_vals)} | Min: {min(deg_vals)}")
    print(f"  In-Degree    — Mean: {sum(in_vals)/n_nodes:.2f}  | Max: {max(in_vals)}  | Min: {min(in_vals)}")
    print(f"  Out-Degree   — Mean: {sum(out_vals)/n_nodes:.2f} | Max: {max(out_vals)} | Min: {min(out_vals)}")

    # Top-10 nodes by total degree (hub analysis)
    top_hubs = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n  Top-10 Hub Nodes by Total Degree:")
    for node_id, deg in top_hubs:
        title = eeg.nodes[node_id].get("title", node_id)
        synthetic_flag = " [SYNTHETIC]" if eeg.nodes[node_id].get("is_synthetic") else " [CURATED]"
        print(f"    {deg:3d} | {title}{synthetic_flag}")

    # --- 3. Clustering Coefficient ---
    undirected = eeg.to_undirected()
    try:
        avg_clustering = nx.average_clustering(undirected)
    except Exception:
        avg_clustering = None

    print(f"\n[3] Clustering Coefficient")
    if avg_clustering is not None:
        print(f"  Average Clustering Coefficient: {avg_clustering:.4f}")
    else:
        print(f"  Average Clustering Coefficient: N/A (computation failed)")

    # --- 4. Connected Components ---
    wcc_sizes = sorted([len(c) for c in nx.weakly_connected_components(eeg)], reverse=True)
    scc_sizes = sorted([len(c) for c in nx.strongly_connected_components(eeg)], reverse=True)

    print(f"\n[4] Connected Components")
    print(f"  Weakly Connected Components:   {len(wcc_sizes)}")
    print(f"    - Largest WCC size:          {wcc_sizes[0]}")
    print(f"    - Coverage (% of nodes):     {wcc_sizes[0]/n_nodes*100:.1f}%")
    print(f"  Strongly Connected Components: {len(scc_sizes)}")
    print(f"    - Largest SCC size:          {scc_sizes[0]}")

    # --- 5. Diameter & Avg Shortest Path (on largest WCC) ---
    largest_wcc_nodes = max(nx.weakly_connected_components(eeg), key=len)
    largest_wcc_subgraph = eeg.subgraph(largest_wcc_nodes).to_undirected()

    diameter = None
    avg_spl = None
    try:
        if nx.is_connected(largest_wcc_subgraph):
            diameter = nx.diameter(largest_wcc_subgraph)
            avg_spl = nx.average_shortest_path_length(largest_wcc_subgraph)
        else:
            print("  [NOTE] Largest WCC is not connected as undirected — skipping diameter.")
    except Exception as e:
        print(f"  [NOTE] Diameter computation skipped: {e}")

    print(f"\n[5] Path Length Analysis (Largest WCC, n={len(largest_wcc_nodes)})")
    print(f"  Diameter:                   {diameter if diameter else 'N/A (graph too large or disconnected)'}")
    print(f"  Avg Shortest Path Length:   {f'{avg_spl:.3f}' if avg_spl else 'N/A'}")

    # --- 6. Betweenness Centrality (Top-10) ---
    print(f"\n[6] Betweenness Centrality (Top-10 — Bridge Cases in Citation Network)")
    try:
        bc = nx.betweenness_centrality(eeg, normalized=True)
        top_bc = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:10]
        for node_id, score in top_bc:
            title = eeg.nodes[node_id].get("title", node_id)
            synthetic_flag = " [SYNTHETIC]" if eeg.nodes[node_id].get("is_synthetic") else " [CURATED]"
            print(f"    {score:.4f} | {title}{synthetic_flag}")
    except Exception as e:
        top_bc = []
        print(f"  [ERROR] Betweenness centrality failed: {e}")

    # --- 7. Edge Type Distribution ---
    relation_counts = {}
    for u, v, data in eeg.edges(data=True):
        rel = data.get("relation", "UNKNOWN")
        relation_counts[rel] = relation_counts.get(rel, 0) + 1

    print(f"\n[7] Edge Relation Distribution")
    for rel, count in sorted(relation_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / n_edges * 100 if n_edges > 0 else 0
        print(f"  {rel:12s}: {count:5d} edges ({pct:.1f}%)")

    # --- Save to JSON ---
    metrics = {
        "basic_stats": {
            "total_nodes": n_nodes,
            "curated_nodes": len(curated_nodes),
            "synthetic_nodes": len(synthetic_nodes),
            "total_edges": n_edges,
            "density": round(density, 6)
        },
        "degree_distribution": {
            "mean_degree": round(sum(deg_vals) / n_nodes, 3),
            "max_degree": max(deg_vals),
            "min_degree": min(deg_vals),
            "mean_in_degree": round(sum(in_vals) / n_nodes, 3),
            "max_in_degree": max(in_vals),
            "mean_out_degree": round(sum(out_vals) / n_nodes, 3),
            "max_out_degree": max(out_vals),
        },
        "top_hubs": [
            {
                "case_id": node_id,
                "title": eeg.nodes[node_id].get("title", node_id),
                "total_degree": deg,
                "is_curated": not eeg.nodes[node_id].get("is_synthetic", False)
            }
            for node_id, deg in top_hubs
        ],
        "clustering": {
            "avg_clustering_coefficient": round(avg_clustering, 4) if avg_clustering is not None else None
        },
        "connected_components": {
            "num_weakly_connected": len(wcc_sizes),
            "largest_wcc_size": wcc_sizes[0],
            "largest_wcc_coverage_pct": round(wcc_sizes[0] / n_nodes * 100, 1),
            "num_strongly_connected": len(scc_sizes),
            "largest_scc_size": scc_sizes[0],
        },
        "path_analysis": {
            "diameter": diameter,
            "avg_shortest_path_length": round(avg_spl, 3) if avg_spl else None
        },
        "betweenness_centrality_top10": [
            {
                "case_id": node_id,
                "title": eeg.nodes[node_id].get("title", node_id),
                "betweenness": round(score, 4),
                "is_curated": not eeg.nodes[node_id].get("is_synthetic", False)
            }
            for node_id, score in top_bc
        ],
        "edge_relation_distribution": relation_counts
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Graph metrics saved to '{output_file}'")
    print(f"{'='*60}\n")

    return metrics


if __name__ == "__main__":
    run_graph_analytics()
