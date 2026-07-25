import os
import json
import networkx as nx

def run_graph_audit():
    index_file = "terra_eeg_index.json"
    if not os.path.exists(index_file):
        print(f"[ERROR] Graph index file '{index_file}' does not exist. Please run ingestion first.")
        return

    print(f"Loading Graph Index from '{index_file}'...")
    with open(index_file, "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    # Load into NetworkX
    eeg = nx.node_link_graph(graph_data, edges="edges" if "edges" in graph_data else "links")

    num_nodes = eeg.number_of_nodes()
    num_edges = eeg.number_of_edges()

    print("\n==========================================")
    print("=== GRAPH CONNECTIVITY AUDIT REPORT ===")
    print("==========================================")
    print(f"Total Nodes (Legal Cases):    {num_nodes}")
    print(f"Total Edges (Citation Links): {num_edges}")

    if num_nodes == 0:
        print("[WARNING] The graph has 0 nodes. Ingestion contains no data.")
        return

    # Calculate Degrees
    degrees = [deg for node, deg in eeg.degree()]
    in_degrees = [deg for node, deg in eeg.in_degree()]
    out_degrees = [deg for node, deg in eeg.out_degree()]

    avg_degree = sum(degrees) / num_nodes
    avg_in_degree = sum(in_degrees) / num_nodes
    avg_out_degree = sum(out_degrees) / num_nodes

    # Calculate Network Density
    density = nx.density(eeg)

    print(f"Average Degree (Total):       {avg_degree:.2f}")
    print(f"Average In-Degree:            {avg_in_degree:.2f}")
    print(f"Average Out-Degree:           {avg_out_degree:.2f}")
    print(f"Graph Density:                {density:.4f}")
    print("------------------------------------------")

    print("\nNode-by-Node Connectivity Details:")
    for node_id in eeg.nodes:
        node_data = eeg.nodes[node_id]
        title = node_data.get("title", f"Node {node_id}")
        in_deg = eeg.in_degree(node_id)
        out_deg = eeg.out_degree(node_id)
        print(f"- [{node_id}] {title:<30} | In-Degree: {in_deg} | Out-Degree: {out_deg} | Total Connections: {in_deg + out_deg}")

    print("\nAudit Evaluation:")
    if avg_degree < 1.0:
        print("[STATUS: SPARSE] Average connectivity is extremely low. Most nodes are isolated. Consider lowering min_citations threshold or expanding topic keyword filter.")
    elif avg_degree < 2.0:
        print("[STATUS: MODERATE] Nodes are connected but sparse. This is typical for small test runs with 3-5 nodes.")
    else:
        print("[STATUS: DENSE] Nodes are highly connected and cohesive. Graph is ready for complex multihop reasoning and citation paths.")
    print("==========================================\n")

if __name__ == "__main__":
    run_graph_audit()
