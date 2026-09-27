import os
import sys
import json
import time
import networkx as nx
from collections import Counter, defaultdict

print("=== DEEP FORENSIC AUDIT OF 20,000-CASE EEG GRAPH ===")
GRAPH_PATH = "dataset_20k_cap/terra_eeg_index_20k.json"

if not os.path.exists(GRAPH_PATH):
    print(f"Error: {GRAPH_PATH} not found!")
    sys.exit(1)

with open(GRAPH_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

nodes = data.get("nodes", {})
edges = data.get("edges", [])

print(f"\n[1] BASIC COUNTS:")
print(f"  - Total Nodes in Index: {len(nodes):,}")
print(f"  - Total Edges in Index: {len(edges):,}")

# [2] TEMPORAL DIRECTIONALITY AUDIT
print(f"\n[2] TEMPORAL DIRECTIONALITY CHECK (t_citing >= t_cited):")
strict_forward = 0
same_day = 0
backward_violations = 0
missing_date_edges = 0
violation_examples = []

for e in edges:
    src, tgt = e["source"], e["target"]
    d_src = nodes.get(src, {}).get("decision_date", "")
    d_tgt = nodes.get(tgt, {}).get("decision_date", "")

    if not d_src or not d_tgt:
        missing_date_edges += 1
        continue

    if d_src > d_tgt:
        strict_forward += 1
    elif d_src == d_tgt:
        same_day += 1
    else:
        backward_violations += 1
        violation_examples.append((src, d_src, tgt, d_tgt))

print(f"  - Strict Forward Edges (t_src > t_tgt): {strict_forward:,} ({strict_forward/len(edges)*100:.2f}%)")
print(f"  - Same-Day Decisions   (t_src == t_tgt): {same_day:,} ({same_day/len(edges)*100:.2f}%)")
print(f"  - Missing Date Edges                   : {missing_date_edges:,}")
print(f"  - Backward Violations  (t_src < t_tgt) : {backward_violations:,}")

if backward_violations > 0:
    print("  [ALERT] Backward Violations Found:")
    for src, d_src, tgt, d_tgt in violation_examples[:5]:
        print(f"    Edge: {src} ({d_src}) -> {tgt} ({d_tgt})")

# [3] NETWORKX GRAPH RECONSTRUCTION & TOPOLOGY
print(f"\n[3] NETWORKX TOPOLOGY & CONNECTIVITY:")
G = nx.DiGraph()
for nid in nodes:
    G.add_node(nid)
for e in edges:
    G.add_edge(e["source"], e["target"])

total_n = G.number_of_nodes()
total_e = G.number_of_edges()
density = nx.density(G)
avg_in_out = total_e / total_n

print(f"  - Verified DiGraph Nodes: {total_n:,}")
print(f"  - Verified DiGraph Edges: {total_e:,}")
print(f"  - Graph Density: {density:.6f}")
print(f"  - Average In/Out Degree: {avg_in_out:.4f}")

# Undirected projection
G_undir = G.to_undirected()
degrees = dict(G_undir.degree())
mean_degree = sum(degrees.values()) / total_n
max_node = max(degrees, key=degrees.get)
max_deg = degrees[max_node]
max_case_title = nodes.get(max_node, {}).get("title", "")

print(f"  - Mean Undirected Degree: {mean_degree:.2f}")
print(f"  - Max Degree Hub Node: {max_deg} ({max_case_title}, ID: {max_node})")

# [4] STRONGLY CONNECTED COMPONENTS (SCC)
print(f"\n[4] STRONGLY CONNECTED COMPONENTS (SCC):")
sccs = list(nx.strongly_connected_components(G))
scc_sizes = sorted([len(c) for c in sccs], reverse=True)
scc_counts = Counter(scc_sizes)

print(f"  - Total SCCs: {len(sccs):,}")
print(f"  - Largest SCC Size: {scc_sizes[0]}")
print(f"  - SCC Size Distribution: {dict(scc_counts.most_common(10))}")

multi_sccs = [c for c in sccs if len(c) > 1]
print(f"  - Number of Non-Trivial SCCs (size > 1): {len(multi_sccs)}")
for idx, c in enumerate(multi_sccs[:5], 1):
    c_nodes = list(c)
    print(f"    Cycle {idx} (size {len(c)}):")
    for nid in c_nodes:
        print(f"      {nid}: {nodes.get(nid, {}).get('title')} ({nodes.get(nid, {}).get('decision_date')})")

# [5] WEAKLY CONNECTED COMPONENTS (WCC)
print(f"\n[5] WEAKLY CONNECTED COMPONENTS (WCC):")
wccs = list(nx.weakly_connected_components(G))
wcc_sizes = sorted([len(c) for c in wccs], reverse=True)
largest_wcc = wcc_sizes[0]
largest_wcc_pct = (largest_wcc / total_n) * 100.0

print(f"  - Total WCCs: {len(wccs):,}")
print(f"  - Largest WCC Size: {largest_wcc:,} ({largest_wcc_pct:.2f}% of graph)")
print(f"  - Top 5 WCC Sizes: {wcc_sizes[:5]}")
singleton_wcc = sum(1 for s in wcc_sizes if s == 1)
print(f"  - Singleton (Isolated) Nodes: {singleton_wcc:,} ({singleton_wcc/total_n*100:.2f}%)")

# [6] DOCTRINAL CATEGORY BREAKDOWN & ISOLATION
print(f"\n[6] NODE CATEGORY & ISOLATION AUDIT:")
cat_counts = Counter(n.get("category", "unknown") for n in nodes.values())
for cat, cnt in cat_counts.most_common():
    cat_nodes = [nid for nid, n in nodes.items() if n.get("category") == cat]
    cat_degrees = [degrees[nid] for nid in cat_nodes]
    avg_cat_deg = sum(cat_degrees) / len(cat_degrees) if cat_degrees else 0
    zero_deg = sum(1 for d in cat_degrees if d == 0)
    print(f"  - {cat:20s}: {cnt:6,d} | Avg Degree: {avg_cat_deg:5.2f} | Zero-Degree (Isolated): {zero_deg:5,d} ({zero_deg/cnt*100:5.1f}%)")
