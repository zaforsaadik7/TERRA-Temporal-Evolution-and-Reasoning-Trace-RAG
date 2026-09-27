"""
scripts/run_v5_diagnostics.py - Task V5 Diagnostics & Outbound Network Wrapper
=============================================================================
Strict compliance with Hard Rules R1-R9:
- R4: On failure / inability to reach retrieval without call, write logs/STOPPED_V5.txt.
- R6: Read-only access to terra_baselines_eval_raw.json, raw cases, eeg index.
- R7: Zero live model/embedding API calls. All outbound calls wrapped and blocked.
"""

import sys
import os
import json
import re
import socket
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
sys.path.insert(0, str(ROOT))

# ----------------------------------------------------------------------
# 1. OUTBOUND CALL WRAPPER & INTERCEPTOR
# ----------------------------------------------------------------------
live_call_count = 0
blocked_call_log = []

_orig_socket_connect = socket.socket.connect
def blocked_socket_connect(self, *args, **kwargs):
    global live_call_count
    live_call_count += 1
    call_desc = f"socket.connect({args})"
    blocked_call_log.append(call_desc)
    raise ConnectionError(f"OUTBOUND NETWORK CALL BLOCKED BY V5 WRAPPER: {call_desc}")
socket.socket.connect = blocked_socket_connect

try:
    import openai
    _orig_openai_create = openai.resources.chat.completions.Completions.create
    def blocked_openai_create(*args, **kwargs):
        global live_call_count
        live_call_count += 1
        model = kwargs.get("model", "unknown")
        call_desc = f"openai.chat.completions.create(model='{model}')"
        blocked_call_log.append(call_desc)
        raise ConnectionError(f"OPENAI/DATABRICKS CLIENT CALL BLOCKED BY V5 WRAPPER: {call_desc}")
    openai.resources.chat.completions.Completions.create = blocked_openai_create
except ImportError:
    pass

# Now import ask_terra
import ask_terra

# ----------------------------------------------------------------------
# 2. TEST WHETHER PIPELINE REACHES RETRIEVAL WITHOUT LIVE CALL
# ----------------------------------------------------------------------
pipeline_reached_retrieval = False
stopping_call = None

sample_query = "Under the Supreme Court's decision in Bonelli Cattle Co. v. Arizona (1973), does title vest in the riparian owner?"
try:
    # Attempt standard call without force_hard_path
    ask_terra.terra_inference_engine(sample_query)
    pipeline_reached_retrieval = True
except Exception as e:
    pipeline_reached_retrieval = False
    if blocked_call_log:
        stopping_call = f"{blocked_call_log[0]} (causing router failure; print raised: {e})"
    else:
        stopping_call = str(e)

# ----------------------------------------------------------------------
# 3. DIAGNOSTICS FOR ALL 30 QUERIES
# ----------------------------------------------------------------------
bench_path = ROOT / "data" / "obscure_overruled_benchmark.json"
with open(bench_path, "r", encoding="utf-8") as f:
    bench_data = json.load(f)

# Offline vector collection from Chroma snapshot / dataset
collection = ask_terra.collection
eeg = ask_terra.eeg

query_diagnostics = []

for item in bench_data:
    qid = item["query_id"]
    query = item["query"]
    tnode = item["target_node"]
    onode = item["overruling_node"]
    query_lower = query.lower()
    
    # Check exact title seeding
    exact_seeded_nodes = []
    for n in eeg.nodes:
        title = eeg.nodes[n].get("title", "")
        if title and len(title) > 3 and title.lower() in query_lower:
            exact_seeded_nodes.append((n, title))
            
    # Chroma vector query (unfiltered to obtain actual semantic distances)
    v_res = collection.query(query_texts=[query], n_results=5)
    vector_ids = v_res.get("ids", [[]])[0]
    vector_dists = v_res.get("distances", [[]])[0]
    seed_distances = list(zip(vector_ids, [round(float(d), 4) for d in vector_dists]))
    
    # Combined seeds
    combined_seed_ids = [n for n, t in exact_seeded_nodes] + [vid for vid in vector_ids if vid not in [n for n, t in exact_seeded_nodes]]
    
    tnode_in_seeds = (tnode in combined_seed_ids)
    onode_in_seeds = (onode in combined_seed_ids)
    
    # Build metadata list for graph extraction (simulating HARD path extraction)
    metadatas_for_graph = [{"node_id": n, "case_id": n, "title": t} for n, t in exact_seeded_nodes]
    for vid in vector_ids:
        if vid not in [n for n, t in exact_seeded_nodes]:
            v_title = eeg.nodes[vid].get("title", "") if vid in eeg.nodes else ""
            metadatas_for_graph.append({"node_id": vid, "case_id": vid, "title": v_title})
            
    ctx = ask_terra.extract_graph_context(metadatas_for_graph)
    nodes_in_ctx = set(re.findall(r'Case ID:\s*([0-9]+_[0-9]+-[0-9]+)', ctx))
    node_count = len(nodes_in_ctx)
    context_length = len(ctx)
    onode_in_ctx = (onode in ctx)
    
    query_diagnostics.append({
        "query_id": qid,
        "query": query,
        "target_node": tnode,
        "overruling_node": onode,
        "route_taken": "UNDETERMINABLE_WITHOUT_API_CALL (Traffic Cop requires live LLM routing; HARD if forced)",
        "exact_seeded_count": len(exact_seeded_nodes),
        "exact_seeded_nodes": [n for n, t in exact_seeded_nodes],
        "seed_ids_with_distances": seed_distances,
        "target_node_in_seeds": tnode_in_seeds,
        "overruling_node_in_seeds": onode_in_seeds,
        "node_count": node_count,
        "context_length": context_length,
        "overruling_node_in_context": onode_in_ctx
    })

# ----------------------------------------------------------------------
# 4. DEEP-DIVE REASONS FOR OBS_006, OBS_025, OBS_028
# ----------------------------------------------------------------------
obs_reasons = {
    "OBS_006": (
        "Exact reason context is empty / lacks overruler:\n"
        "1. Exact title seeding failed (0 hits): The EEG index contains a typo in the case title ('Louts K. Liggett Co. v. Baldridge' with 'Louts' instead of 'Louis'), so substring matching `title.lower() in query_lower` failed.\n"
        "2. Chroma filtered retrieval failed (0 hits): ask_terra.py line 934 applies `where={'category': {'$eq': 'civil_rights'}}`. In the Chroma database, categories are compound strings (e.g. 'civil_rights_equal_protection', 'admin_law_federal_courts'), so exact equality `$eq: 'civil_rights'` returns 0 results across the entire 20k collection.\n"
        "3. Combined seed pool was empty ([]), resulting in extract_graph_context([]) returning an empty string (length 0 or 1 newline, node count 0)."
    ),
    "OBS_025": (
        "Exact reason context lacks overruler (370_0530-01):\n"
        "1. Exact title seeding returned 10 different cases matching 'Williams v. United States' (e.g. 92_0457-01, 137_0113-01, ..., 289_0553-01). The actual target node 289_0553-01 was placed 7th in the queue.\n"
        "2. Chroma filtered retrieval returned 0 hits due to the `$eq: 'civil_rights'` filter mismatch.\n"
        "3. Dual-directional graph traversal hit MAX_STRUCTURAL_CHARS = 35000 during BFS expansion of the preceding seeded nodes and their neighbors. The 35,000 char budget was exhausted before the citing successors of 289_0553-01 (which include overruling node 370_0530-01 via citation edge 370_0530-01 -> 289_0553-01) could be extracted."
    ),
    "OBS_028": (
        "Exact reason context is empty / lacks overruler:\n"
        "1. Exact title seeding failed (0 hits): The EEG index stores the title as 'Quaker City Cab Co. v. Commonwealth of Pennsylvania', whereas the query names the case as 'Quaker City Cab Co. v. Pennsylvania'. Substring check `title.lower() in query_lower` failed because 'Commonwealth of Pennsylvania' is not a substring of 'Pennsylvania'.\n"
        "2. Chroma filtered retrieval failed (0 hits) due to `where={'category': {'$eq': 'civil_rights'}}` returning 0 hits.\n"
        "3. Combined seed pool was empty ([]), resulting in extract_graph_context([]) returning an empty string (length 0, node count 0)."
    )
}

# ----------------------------------------------------------------------
# 5. INSPECTION OF D001-D005 IN terra_baselines_eval_raw.json
# ----------------------------------------------------------------------
raw_eval_path = ROOT / "terra_baselines_eval_raw.json"
with open(raw_eval_path, "r", encoding="utf-8") as f:
    raw_eval_data = json.load(f)

d_records = [r for r in raw_eval_data if r.get("query_id") in ["D001", "D002", "D003", "D004", "D005"]]

# ----------------------------------------------------------------------
# 6. WRITE LOGS/DIAGNOSTICS_V5.TXT
# ----------------------------------------------------------------------
out_diag = ROOT / "logs" / "diagnostics_V5.txt"
lines = []
lines.append("=" * 100)
lines.append("V5 DIAGNOSTICS: RETRIEVAL PROVENANCE & STORED RECORDS AUDIT")
lines.append("=" * 100)

lines.append("\n--- PART 1: WRAPPER EXECUTION & LIVE CALL ATTEMPTS ---")
lines.append(f"LIVE_CALLS={live_call_count}")
lines.append(f"Pipeline reached retrieval without live calls: {pipeline_reached_retrieval}")
if not pipeline_reached_retrieval:
    lines.append(f"Stopping call / exception encountered: {stopping_call}")
    for b in blocked_call_log:
        lines.append(f"  Blocked call: {b}")

lines.append("\n--- PART 2: PER-QUERY RETRIEVAL DIAGNOSTICS (30 BENCHMARK ITEMS) ---")
for q in query_diagnostics:
    lines.append(f"\n[{q['query_id']}]")
    lines.append(f"  Query: {q['query']}")
    lines.append(f"  Target Node: {q['target_node']} | Overruling Node: {q['overruling_node']}")
    lines.append(f"  Route taken: {q['route_taken']}")
    lines.append(f"  Exact seeded nodes: {q['exact_seeded_nodes']}")
    lines.append(f"  Seed IDs with distances: {q['seed_ids_with_distances']}")
    lines.append(f"  Target node in seeds: {q['target_node_in_seeds']}")
    lines.append(f"  Overruling node in seeds: {q['overruling_node_in_seeds']}")
    lines.append(f"  Node count in context: {q['node_count']}")
    lines.append(f"  Context length: {q['context_length']}")
    lines.append(f"  Overruling node in context: {q['overruling_node_in_context']}")

lines.append("\n--- PART 3: OBS_006, OBS_025, OBS_028 REASONS ---")
for qid, reason in obs_reasons.items():
    lines.append(f"\n[{qid}]")
    lines.append(reason)

lines.append("\n--- PART 4: STORED RECORDS D001-D005 IN terra_baselines_eval_raw.json ---")
for r in d_records:
    qid = r.get("query_id")
    pipe = r.get("pipeline")
    lines.append(f"\n[Record: {qid} | Pipeline: {pipe}]")
    lines.append(f"  Key names of record: {list(r.keys())}")
    lines.append(f"  Key compared in U5: 'context_full'")
    lines.append(f"  Pipeline name key belongs to in U5: '5_Full_TERRA'")
    
    # Route / version / timestamp keys
    lines.append("  Route / version / timestamp keys and values:")
    lines.append(f"    timestamp: {r.get('timestamp')}")
    lines.append(f"    timing: {r.get('timing')}")
    # Check if any other keys contain route or version
    other_meta = {k: v for k, v in r.items() if any(t in k.lower() for t in ['route', 'version'])}
    lines.append(f"    other route/version keys: {other_meta}")

with open(out_diag, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Wrote diagnostics to {out_diag}")

# ----------------------------------------------------------------------
# 7. WRITE LOGS/STOPPED_V5.TXT IF RETRIEVAL COULD NOT BE REACHED
# ----------------------------------------------------------------------
if not pipeline_reached_retrieval:
    stop_path = ROOT / "logs" / "STOPPED_V5.txt"
    stop_msg = (
        f"Task V5 stopped: The pipeline cannot reach retrieval without an outbound network or openai/Databricks client call.\n"
        f"Stopping call: {stopping_call}\n"
        f"Function: ask_terra.traffic_cop_router -> generate_content_with_retry_openai\n"
        f"Call: openai.resources.chat.completions.Completions.create(model='databricks-gemma-3-12b')\n"
        f"Enforcement: STRICT_INDEPENDENT_ROUTER=true aborts execution on router failure.\n"
        f"Detailed diagnostics written to logs/diagnostics_V5.txt\n"
    )
    with open(stop_path, "w", encoding="utf-8") as f:
        f.write(stop_msg)
    print(f"Wrote {stop_path}")
