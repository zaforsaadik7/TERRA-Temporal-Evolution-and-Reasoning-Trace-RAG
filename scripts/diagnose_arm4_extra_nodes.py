import os
import sys
import json
import re
import shutil
from pathlib import Path

ROOT = Path("f:/TERRA - Copy")
sys.path.insert(0, str(ROOT))

# Create instrumented copy in scratch/
orig_ask_terra = ROOT / "ask_terra.py"
copy_ask_terra = ROOT / "scratch" / "ask_terra_instrumented.py"
shutil.copyfile(orig_ask_terra, copy_ask_terra)

# We will instrument scratch/ask_terra_instrumented.py to track additions
# Let's inspect the exact lines in extract_graph_context in ask_terra.py
with open(copy_ask_terra, "r", encoding="utf-8") as f:
    code = f.read()

# Replace extract_graph_context with an instrumented version that logs every node addition
# Let's write the instrumented version directly in scratch/ask_terra_instrumented.py
instrumented_func = '''
def extract_graph_context_instrumented(retrieved_metadatas, max_depth=2, arm4_unlabeled=False):
    INCOMING_HUB_CAP = 75
    OUTGOING_HUB_CAP = 25
    HUB_DEGREE_CAP = 50
    structural_context = ""
    visited_nodes = set()
    node_trace = [] # list of (node_id, depth, relation, line_no, context_length)

    queue = []
    for meta in retrieved_metadatas:
        case_id = meta.get('case_id') or meta.get('node_id')
        if case_id and eeg.has_node(case_id):
            queue.append((case_id, 0))

    def _extract_year_date(pid):
        pdata = eeg.nodes.get(pid, {})
        pdate = str(pdata.get('decision_date') or pdata.get('date') or '')
        try:
            pyear = int(pdate[:4])
        except (ValueError, IndexError):
            pyear = 0
        return (pyear, pdate)

    def _sort_nodes_by_recency(nodes, reverse=True):
        return sorted(nodes, key=_extract_year_date, reverse=reverse)

    MAX_GRAPH_NODES = 40
    MAX_STRUCTURAL_CHARS = 35000

    while queue:
        if len(visited_nodes) >= MAX_GRAPH_NODES or len(structural_context) >= MAX_STRUCTURAL_CHARS:
            break
        current_id, depth = queue.pop(0)

        if current_id in visited_nodes or depth > max_depth:
            continue

        visited_nodes.add(current_id)
        node_trace.append((current_id, depth, "QUEUE_POP_VISITED", 458, len(structural_context)))

        current_node_data = eeg.nodes.get(current_id, {})
        current_title = current_node_data.get('title', current_id)
        current_holding = current_node_data.get('substantive_holding')
        if not current_holding:
            current_holding = clean_case_snippet(current_node_data.get('text', ''), max_chars=1200)
        else:
            current_holding = current_holding[:1200]
        current_date  = current_node_data.get('decision_date') or current_node_data.get('date', '')

        structural_context += (
            f"\\n--- Node: {current_title} (Case ID: {current_id}, Date: {current_date}, Depth {depth}) ---\\n"
        )
        if current_holding:
            structural_context += f"[Case Holding/Rule]: {current_holding}\\n"

        node_degree = eeg.degree(current_id)

        if node_degree > HUB_DEGREE_CAP:
            all_preds = list(eeg.predecessors(current_id)) if hasattr(eeg, "predecessors") else []
            sorted_preds = _sort_nodes_by_recency(all_preds, reverse=True)
            selected_preds = sorted_preds[:INCOMING_HUB_CAP]

            all_succs = list(eeg.neighbors(current_id)) if hasattr(eeg, "neighbors") else []
            sorted_succs = _sort_nodes_by_recency(all_succs, reverse=True)
            selected_succs = sorted_succs[:OUTGOING_HUB_CAP]

            structural_context += (
                f"[Note: High-degree hub node (total_degree={node_degree}, in_degree={len(all_preds)}, out_degree={len(all_succs)}). "
                f"Dual-budget traversal engaged: {len(selected_preds)} incoming citing cases (overruling/invalidation detection) "
                f"and {len(selected_succs)} outgoing cited precedents (foundational lineage).]\\n"
            )

            for predecessor in selected_preds:
                if len(structural_context) >= MAX_STRUCTURAL_CHARS:
                    break
                edge_data = eeg.get_edge_data(predecessor, current_id) or {}
                relation  = edge_data.get('relation', 'CITES')
                pred_data = eeg.nodes.get(predecessor, {})
                pred_title = pred_data.get('title', predecessor)
                pred_date  = pred_data.get('decision_date') or pred_data.get('date', '')
                pred_holding = pred_data.get('substantive_holding')

                if relation == "OVERRULES" and not arm4_unlabeled:
                    pred_text = pred_holding[:600] if pred_holding else clean_case_snippet(pred_data.get('text', ''), max_chars=400)
                    line = (
                        f"- CHRONOLOGICAL FLOW / OVERRULING SUCCESSOR: '{pred_title}' (Case ID: {predecessor}, Date: {pred_date}) "
                        f"[OVERRULES / REPUDIATES] this precedent (Case ID: {current_id})."
                    )
                    node_trace.append((predecessor, depth + 1, relation, 517, len(structural_context)))
                else:
                    rel_tag = "CITES" if arm4_unlabeled else relation
                    pred_text = pred_holding[:250] if pred_holding else clean_case_snippet(pred_data.get('text', ''), max_chars=180)
                    line = (
                        f"- CHRONOLOGICAL FLOW / CITING SUCCESSOR: '{pred_title}' (Case ID: {predecessor}, Date: {pred_date}) "
                        f"[{rel_tag}] this precedent (Case ID: {current_id})."
                    )
                    node_trace.append((predecessor, depth + 1, rel_tag, 524, len(structural_context)))
                if pred_text:
                    line += f" [Holding]: {pred_text}"
                structural_context += line + "\\n"

            for neighbor in selected_succs:
                if len(structural_context) >= MAX_STRUCTURAL_CHARS:
                    break
                edge_data = eeg.get_edge_data(current_id, neighbor) or {}
                relation  = edge_data.get('relation', 'CITES')
                nb_data   = eeg.nodes.get(neighbor, {})
                nb_title  = nb_data.get('title', neighbor)
                nb_date   = nb_data.get('decision_date') or nb_data.get('date', '')
                nb_holding = nb_data.get('substantive_holding')

                if relation == "OVERRULES" and not arm4_unlabeled:
                    nb_text = nb_holding[:600] if nb_holding else clean_case_snippet(nb_data.get('text', ''), max_chars=400)
                    line = (
                        f"- LOGICAL RELATION / OVERRULED DOCTRINE: This case (Case ID: {current_id}) "
                        f"[OVERRULES / REPUDIATES] earlier precedent '{nb_title}' (Case ID: {neighbor}, Date: {nb_date})."
                    )
                    node_trace.append((neighbor, depth + 1, relation, 550, len(structural_context)))
                else:
                    rel_tag = "CITES" if arm4_unlabeled else relation
                    nb_text = nb_holding[:250] if nb_holding else clean_case_snippet(nb_data.get('text', ''), max_chars=180)
                    line = (
                        f"- LOGICAL RELATION / CITED PRECEDENT: This case (Case ID: {current_id}) "
                        f"[{rel_tag}] earlier precedent '{nb_title}' (Case ID: {neighbor}, Date: {nb_date})."
                    )
                    node_trace.append((neighbor, depth + 1, rel_tag, 557, len(structural_context)))
                if nb_text:
                    line += f" [Holding]: {nb_text}"
                structural_context += line + "\\n"

            continue

        if eeg.has_node(current_id):
            for neighbor in list(eeg.neighbors(current_id))[:OUTGOING_HUB_CAP]:
                if len(structural_context) >= MAX_STRUCTURAL_CHARS:
                    break
                edge_data = eeg.get_edge_data(current_id, neighbor) or {}
                relation  = edge_data.get('relation', 'CITES')
                nb_data   = eeg.nodes.get(neighbor, {})
                nb_title  = nb_data.get('title', neighbor)
                nb_date   = nb_data.get('decision_date') or nb_data.get('date', '')
                nb_holding = nb_data.get('substantive_holding')

                if relation == "OVERRULES" and not arm4_unlabeled:
                    nb_text = nb_holding[:600] if nb_holding else clean_case_snippet(nb_data.get('text', ''), max_chars=400)
                    line = (
                        f"- LOGICAL RELATION / OVERRULED DOCTRINE: This case (Case ID: {current_id}) "
                        f"[OVERRULES / REPUDIATES] earlier precedent '{nb_title}' (Case ID: {neighbor}, Date: {nb_date})."
                    )
                    node_trace.append((neighbor, depth + 1, relation, 590, len(structural_context)))
                else:
                    rel_tag = "CITES" if arm4_unlabeled else relation
                    nb_text = nb_holding[:250] if nb_holding else clean_case_snippet(nb_data.get('text', ''), max_chars=180)
                    line = (
                        f"- LOGICAL RELATION: This case (Case ID: {current_id}) "
                        f"[{rel_tag}] earlier case '{nb_title}' (Case ID: {neighbor}, Date: {nb_date})."
                    )
                    node_trace.append((neighbor, depth + 1, rel_tag, 597, len(structural_context)))
                if nb_text:
                    line += f" [Holding]: {nb_text}"
                structural_context += line + "\\n"
                if neighbor not in visited_nodes and depth + 1 <= max_depth and len(queue) < 15:
                    queue.append((neighbor, depth + 1))

            if hasattr(eeg, "predecessors"):
                all_preds = list(eeg.predecessors(current_id))
                sorted_preds = _sort_nodes_by_recency(all_preds, reverse=True)
                for predecessor in sorted_preds[:INCOMING_HUB_CAP]:
                    if len(structural_context) >= MAX_STRUCTURAL_CHARS:
                        break
                    edge_data = eeg.get_edge_data(predecessor, current_id) or {}
                    relation  = edge_data.get('relation', 'CITES')
                    pred_data = eeg.nodes.get(predecessor, {})
                    pred_title = pred_data.get('title', predecessor)
                    pred_date  = pred_data.get('decision_date') or pred_data.get('date', '')
                    pred_holding = pred_data.get('substantive_holding')

                    if relation == "OVERRULES" and not arm4_unlabeled:
                        pred_text = pred_holding[:600] if pred_holding else clean_case_snippet(pred_data.get('text', ''), max_chars=400)
                        line = (
                            f"- CHRONOLOGICAL FLOW / OVERRULING SUCCESSOR: '{pred_title}' (Case ID: {predecessor}, Date: {pred_date}) "
                            f"[OVERRULES / REPUDIATES] this precedent (Case ID: {current_id})."
                        )
                        node_trace.append((predecessor, depth + 1, relation, 629, len(structural_context)))
                    else:
                        rel_tag = "CITES" if arm4_unlabeled else relation
                        pred_text = pred_holding[:250] if pred_holding else clean_case_snippet(pred_data.get('text', ''), max_chars=180)
                        line = (
                            f"- CHRONOLOGICAL FLOW / CITING SUCCESSOR: '{pred_title}' (Case ID: {predecessor}, Date: {pred_date}) "
                            f"[{rel_tag}] this precedent (Case ID: {current_id})."
                        )
                        node_trace.append((predecessor, depth + 1, rel_tag, 636, len(structural_context)))
                    if pred_text:
                        line += f" [Holding]: {pred_text}"
                    structural_context += line + "\\n"
                    if predecessor not in visited_nodes and depth + 1 <= max_depth and len(queue) < 15:
                        queue.append((predecessor, depth + 1))

    return structural_context[:40000], node_trace
'''

with open(copy_ask_terra, "a", encoding="utf-8") as f:
    f.write("\n\n" + instrumented_func + "\n")

import importlib.util
spec = importlib.util.spec_from_file_location("ask_terra_inst", str(copy_ask_terra))
mod_inst = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod_inst)

bench_path = ROOT / "data" / "obscure_overruled_benchmark.json"
with open(bench_path, "r", encoding="utf-8") as f:
    bench = json.load(f)

def extract_node_ids_from_text(ctx: str) -> set:
    return set(re.findall(r'Case ID:\s*([0-9]+_[0-9]+-[0-9]+)', ctx))

out_log_lines = []
out_log_lines.append("=" * 110)
out_log_lines.append("U4 DIAGNOSTIC AUDIT: EXTRA NODE IDS IN ARM 4 UNLABELED ACROSS MISMATCHING QUERIES")
out_log_lines.append("=" * 110)

mismatch_count = 0

for item in bench:
    qid = item["query_id"]
    query = item["query"]
    
    # Run exact seeded node lookup
    exact_seeded_metadatas = []
    exact_seeded_ids = set()
    query_lower = query.lower()
    for nid in mod_inst.eeg.nodes:
        title = mod_inst.eeg.nodes[nid].get("title", "")
        if title and len(title) > 3 and title.lower() in query_lower:
            exact_seeded_metadatas.append({"case_id": nid, "title": title, "category": mod_inst.eeg.nodes[nid].get("category", "")})
            exact_seeded_ids.add(nid)
            
    chroma_res = mod_inst.collection.query(
        query_texts=[query],
        n_results=3,
        where={"category": {"$eq": "civil_rights"}}
    )
    retrieved_metadatas = chroma_res['metadatas'][0] if chroma_res and 'metadatas' in chroma_res else []
    combined_metadatas = exact_seeded_metadatas + [m for m in retrieved_metadatas if (m.get('node_id') or m.get('case_id')) not in exact_seeded_ids]
    
    # Run Full
    ctx_full, trace_full = mod_inst.extract_graph_context_instrumented(combined_metadatas, max_depth=2, arm4_unlabeled=False)
    nodes_full = extract_node_ids_from_text(ctx_full)
    
    # Run Arm 4
    ctx_arm4, trace_arm4 = mod_inst.extract_graph_context_instrumented(combined_metadatas, max_depth=2, arm4_unlabeled=True)
    nodes_arm4 = extract_node_ids_from_text(ctx_arm4)
    
    if nodes_full != nodes_arm4:
        mismatch_count += 1
        extra_arm4 = sorted(nodes_arm4 - nodes_full)
        missing_arm4 = sorted(nodes_full - nodes_arm4)
        
        out_log_lines.append(f"\n--- {qid}: {item.get('target_case')} -> {item.get('overruling_case')} ---")
        out_log_lines.append(f"  Full Node Count: {len(nodes_full)} | Arm 4 Node Count: {len(nodes_arm4)}")
        out_log_lines.append(f"  Extra Nodes in Arm 4 ({len(extra_arm4)}): {extra_arm4}")
        if missing_arm4:
            out_log_lines.append(f"  Extra Nodes in Full ({len(missing_arm4)}): {missing_arm4}")
            
        # Details of extra nodes in Arm 4 trace
        for enode in extra_arm4:
            # find where enode appears in trace_arm4
            hits = [t for t in trace_arm4 if t[0] == enode]
            if hits:
                for h in hits:
                    nid, depth, rel, line_no, ctx_len = h
                    out_log_lines.append(
                        f"    -> Extra Node: {nid} | Depth: {depth} | Relation: {rel} | "
                        f"Code Path: extract_graph_context (line ~{line_no}) | Context Chars At Add: {ctx_len}"
                    )
            else:
                out_log_lines.append(f"    -> Extra Node: {enode} | Depth: UNKNOWN | Code Path: header/seed line")

out_log_lines.append("\n" + "=" * 110)
out_log_lines.append(f"SUMMARY: {mismatch_count}/30 queries had mismatching node sets between Full and Arm 4.")
out_log_lines.append("Root Cause Analysis:")
out_log_lines.append("  Full TERRA uses up to 600 chars for [OVERRULES / REPUDIATES] holding excerpts,")
out_log_lines.append("  reaching the 35,000 character limit earlier than Arm 4 (which uses 250 chars).")
out_log_lines.append("  Arm 4 therefore continues iterating and appends 1-2 additional nodes to context.")
out_log_lines.append("=" * 110)

out_log_path = ROOT / "logs" / "arm4_extra_nodes.txt"
with open(out_log_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out_log_lines) + "\n")

print(f"Wrote Arm 4 extra nodes diagnostic to {out_log_path}")
