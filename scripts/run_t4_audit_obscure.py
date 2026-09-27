import os
import sys
import json
import re
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_LOG = (ROOT / "logs" / "arm4_context_audit.txt").resolve()
STOP_LOG = (ROOT / "logs" / "STOPPED_U4.txt").resolve()
SELFTEST_LOG = (ROOT / "logs" / "selftest_arm4_audit.txt").resolve()
BENCH_PATH = (ROOT / "data" / "obscure_overruled_benchmark.json").resolve()

# Offline config
os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "mock_key_for_offline_import")
os.environ["TERRA_GRAPH_PATH"] = "dataset_20k_cap/terra_eeg_index_20k.json"
os.environ["TERRA_VECTOR_DB_PATH"] = "./dataset_20k_cap/vector_db_20k"

sys.path.insert(0, str(ROOT))
import ask_terra

def extract_node_ids(text: str) -> set:
    return set(re.findall(r'Case ID:\s*([0-9]+_[0-9]+-[0-9]+)', text))

def get_max_relation_holding_len(text: str) -> int:
    """Restricts excerpt-length metric to relation lines only (not seeded-case lines)."""
    max_len = 0
    for line in text.splitlines():
        line_s = line.strip()
        if (line_s.startswith("- CHRONOLOGICAL FLOW") or line_s.startswith("- LOGICAL RELATION")) and "[Holding]:" in line_s:
            snip = line_s.split("[Holding]:")[1].strip()
            max_len = max(max_len, len(snip))
    return max_len

def run_arm4_audit(bench_data, inject_selftest_tag=False):
    log_lines = []
    log_lines.append("=" * 120)
    log_lines.append("U4 AUDIT: FULL TERRA VS ARM 4 UNLABELED ACROSS BENCHMARK QUERIES (WITH NODE RESTRICTION)" + (" [SELFTEST CANARY]" if inject_selftest_tag else ""))
    log_lines.append(f"Repository Root: {ROOT.resolve()}")
    log_lines.append(f"Benchmark File:  {BENCH_PATH.resolve()}")
    log_lines.append("=" * 120)

    node_parity_matches = 0
    tag_clean_arm4_count = 0
    tag_leak_arm4_count = 0
    rel_holding_capped_count = 0
    overruler_present_both_count = 0
    missing_overruler_records = []
    parity_failed = False
    tag_leak_records = []

    for idx, item in enumerate(bench_data):
        qid = item["query_id"]
        query = item["query"]
        tnode = item["target_node"]
        onode = item["overruling_node"]
        
        # 1. Exact seeded nodes logic matching ask_terra.py
        exact_seeded_metadatas = []
        exact_seeded_ids = set()
        query_lower = query.lower()
        for nid in ask_terra.eeg.nodes:
            title = ask_terra.eeg.nodes[nid].get("title", "")
            if title and len(title) > 3 and title.lower() in query_lower:
                exact_seeded_metadatas.append({"case_id": nid, "title": title, "category": ask_terra.eeg.nodes[nid].get("category", "")})
                exact_seeded_ids.add(nid)
                
        chroma_res = ask_terra.collection.query(
            query_texts=[query],
            n_results=3,
            where={"category": {"$eq": "civil_rights"}}
        )
        retrieved_traces = chroma_res['documents'][0] if chroma_res and 'documents' in chroma_res else []
        retrieved_metadatas = chroma_res['metadatas'][0] if chroma_res and 'metadatas' in chroma_res else []
        
        combined_metadatas = exact_seeded_metadatas + [m for m in retrieved_metadatas if (m.get('node_id') or m.get('case_id')) not in exact_seeded_ids]
        
        # --- 1. RUN FULL TERRA FIRST ---
        struct_full = ask_terra.extract_graph_context(combined_metadatas, max_depth=2, arm4_unlabeled=False, restrict_to_nodes=None)
        nodes_full = extract_node_ids(struct_full)
        
        conn_full = []
        for _src in exact_seeded_ids:
            for _dst in exact_seeded_ids:
                if _src != _dst:
                    _edge = ask_terra.eeg.get_edge_data(_src, _dst)
                    if _edge is not None:
                        _src_title = ask_terra.eeg.nodes.get(_src, {}).get('title', _src)
                        _dst_title = ask_terra.eeg.nodes.get(_dst, {}).get('title', _dst)
                        _rel = _edge.get('relation', 'CITES') if isinstance(_edge, dict) else 'CITES'
                        conn_full.append(f"- [{_rel}] '{_src_title}' directly relates to/cites '{_dst_title}' in the legal citation graph.")
        conn_block_full = ("[STRUCTURAL CONNECTIONS]\n" + "\n".join(conn_full) + "\n\n") if conn_full else ""
        
        succ_lines_full = [
            line.strip() for line in struct_full.splitlines() 
            if ("CHRONOLOGICAL FLOW / CITING SUCCESSOR" in line or "LOGICAL RELATION" in line)
        ]
        graph_evo_full = (f"[PRECEDENT EVOLUTION & CITING SUCCESSORS (GRAPH TRAVERSAL)]\n" + "\n".join(succ_lines_full[:100]) + "\n\n") if succ_lines_full else ""
        
        seed_summaries_full = []
        for _nid in exact_seeded_ids:
            _ndata = ask_terra.eeg.nodes.get(_nid, {})
            _title = _ndata.get('title', _nid)
            _holding = _ndata.get('substantive_holding') or ask_terra.clean_case_snippet(_ndata.get('text', ''), max_chars=1200)
            _holding = _holding[:1200]
            try:
                _c = ask_terra.collection.get(ids=[_nid])
                _trace = _c['documents'][0] if (_c and _c.get('documents')) else ""
            except Exception:
                _trace = ""
            _summary = f"{_trace}\n[Holding]: {_holding}".strip() if (_trace or _holding) else ""
            if _title or _summary:
                seed_summaries_full.append(f"[SEEDED CASE] {_title}:\n{_summary}")
        seed_header_full = "\n\n".join(seed_summaries_full) if seed_summaries_full else ""
        traces_excerpt = "\n".join([f"- {t}" for t in retrieved_traces[:5]])
        traces_context = "\n".join([f"- {t}" for t in retrieved_traces])
        
        if seed_header_full:
            compiled_ctx_full = f"{seed_header_full}\n\n[GRAPH EXPANSION CONTEXT]\n{struct_full}\n{traces_context}"
        else:
            compiled_ctx_full = f"{struct_full}\n{traces_context}"
        compiled_ctx_full = compiled_ctx_full[:60000]

        # --- 2. RUN ARM 4 PASSING FULL'S NODE SET ---
        struct_arm4 = ask_terra.extract_graph_context(combined_metadatas, max_depth=2, arm4_unlabeled=True, restrict_to_nodes=nodes_full)
        
        # CANARY INJECTION (mutates only the first context in selftest mode)
        if inject_selftest_tag and idx == 0:
            struct_arm4 = "- CHRONOLOGICAL FLOW / OVERRULING SUCCESSOR: [OVERRULES / REPUDIATES]\n" + struct_arm4
            
        nodes_arm4 = extract_node_ids(struct_arm4)
        
        conn_arm4 = []
        for _src in exact_seeded_ids:
            for _dst in exact_seeded_ids:
                if _src != _dst:
                    _edge = ask_terra.eeg.get_edge_data(_src, _dst)
                    if _edge is not None:
                        _src_title = ask_terra.eeg.nodes.get(_src, {}).get('title', _src)
                        _dst_title = ask_terra.eeg.nodes.get(_dst, {}).get('title', _dst)
                        conn_arm4.append(f"- [CITES] '{_src_title}' directly relates to/cites '{_dst_title}' in the legal citation graph.")
        conn_block_arm4 = ("[STRUCTURAL CONNECTIONS]\n" + "\n".join(conn_arm4) + "\n\n") if conn_arm4 else ""
        
        if seed_header_full:
            compiled_ctx_arm4 = f"{seed_header_full}\n\n[GRAPH EXPANSION CONTEXT]\n{struct_arm4}\n{traces_context}"
        else:
            compiled_ctx_arm4 = f"{struct_arm4}\n{traces_context}"
        compiled_ctx_arm4 = compiled_ctx_arm4[:60000]

        # Checks
        nodes_identical = (nodes_full == nodes_arm4)
        if nodes_identical:
            node_parity_matches += 1
        else:
            parity_failed = True
            
        onode_in_full = onode in compiled_ctx_full
        onode_in_arm4 = onode in compiled_ctx_arm4
        if onode_in_full and onode_in_arm4:
            overruler_present_both_count += 1
        else:
            if not onode_in_full:
                missing_overruler_records.append((qid, "Full TERRA", onode, item.get("overruling_case")))
            if not onode_in_arm4:
                missing_overruler_records.append((qid, "Arm 4 Unlabeled", onode, item.get("overruling_case")))

        max_rel_h_full = get_max_relation_holding_len(compiled_ctx_full)
        max_rel_h_arm4 = get_max_relation_holding_len(compiled_ctx_arm4)
        if max_rel_h_arm4 <= 250:
            rel_holding_capped_count += 1

        # Tag presence in context
        full_tags_ctx = {
            "[OVERRULES": "[OVERRULES" in compiled_ctx_full,
            "REPUDIATES": "REPUDIATES" in compiled_ctx_full,
            "OVERRULING SUCCESSOR": "OVERRULING SUCCESSOR" in compiled_ctx_full
        }
        arm4_tags_ctx = {
            "[OVERRULES": "[OVERRULES" in compiled_ctx_arm4,
            "REPUDIATES": "REPUDIATES" in compiled_ctx_arm4,
            "OVERRULING SUCCESSOR": "OVERRULING SUCCESSOR" in compiled_ctx_arm4
        }
        
        has_arm4_leak = any(arm4_tags_ctx.values())
        if has_arm4_leak:
            tag_leak_arm4_count += 1
            tag_leak_records.append((qid, arm4_tags_ctx))
        else:
            tag_clean_arm4_count += 1

        log_lines.append(f"\n--- {qid}: {item.get('target_case')} -> {item.get('overruling_case')} ---")
        log_lines.append(f"  Target Node: {tnode} | Overruling Node: {onode}")
        log_lines.append(f"  NODE PARITY: set(Arm4) == set(Full): {nodes_identical} (Nodes: {len(nodes_full)})")
        log_lines.append(f"  OVERRULER IN CONTEXT: Full={onode_in_full}, Arm4={onode_in_arm4}")
        log_lines.append(f"  MAX RELATION HOLDING LENGTH: Full={max_rel_h_full} chars, Arm4={max_rel_h_arm4} chars (Cap <= 250: {max_rel_h_arm4 <= 250})")
        log_lines.append(f"  FULL TAGS: [OVERRULES]={full_tags_ctx['[OVERRULES']}, REPUDIATES={full_tags_ctx['REPUDIATES']}, OVERRULING SUCCESSOR={full_tags_ctx['OVERRULING SUCCESSOR']}")
        log_lines.append(f"  ARM4 TAGS: [OVERRULES]={arm4_tags_ctx['[OVERRULES']}, REPUDIATES={arm4_tags_ctx['REPUDIATES']}, OVERRULING SUCCESSOR={arm4_tags_ctx['OVERRULING SUCCESSOR']}")

    log_lines.append("\n" + "=" * 120)
    log_lines.append("SUMMARY COUNTERS:")
    log_lines.append(f"  TOTAL QUERIES EVALUATED:          {len(bench_data)}")
    log_lines.append(f"  EXACT NODE PARITY MATCHES:        {node_parity_matches}/{len(bench_data)}")
    log_lines.append(f"  ARM 4 TAG-CLEAN QUERIES:          {tag_clean_arm4_count}/{len(bench_data)}")
    log_lines.append(f"  ARM 4 TAG LEAKS DETECTED:         {tag_leak_arm4_count}")
    log_lines.append(f"  OVERRULER PRESENT IN BOTH ARMS:   {overruler_present_both_count}/{len(bench_data)}")
    log_lines.append(f"  RELATION HOLDING CAPPED (<=250):  {rel_holding_capped_count}/{len(bench_data)}")
    log_lines.append("=" * 120)
    
    if missing_overruler_records:
        log_lines.append("\nMISSING OVERRULING NODE AUDIT:")
        for qid, arm, onode, ocase in missing_overruler_records:
            log_lines.append(f"  MISSING OVERRULER: {qid} in {arm} | Overruling Node: {onode} ({ocase})")
        log_lines.append(f"Total instances lacking overruling node: {len(missing_overruler_records)}")
    else:
        log_lines.append("\n  Overruling node present in ALL 60 contexts.")

    audit_success = (node_parity_matches == len(bench_data)) and (tag_leak_arm4_count == 0) and (rel_holding_capped_count == len(bench_data))
    return audit_success, "\n".join(log_lines), tag_leak_records, parity_failed


def main():
    parser = argparse.ArgumentParser(description="Arm 4 Parity & Tag Audit")
    parser.add_argument("--selftest", action="store_true", help="Run canary test by injecting tag into Arm 4 context")
    args = parser.parse_args()
    
    with open(BENCH_PATH, "r", encoding="utf-8") as f:
        bench = json.load(f)
        
    if args.selftest:
        print("[CANARY] Running --selftest by injecting [OVERRULES into Arm 4 context ...")
        passed, log_text, tag_leaks, parity_failed = run_arm4_audit(bench, inject_selftest_tag=True)
        
        canary_lines = []
        canary_lines.append("CANARY TEST: run_t4_audit_obscure.py --selftest")
        canary_lines.append("Mutation injected: Injected '[OVERRULES / REPUDIATES]' into OBS_001 Arm 4 context")
        canary_lines.append("Expected behavior: Tag leak detected in Arm 4; audit_success=False")
        canary_lines.append(f"Actual audit_success: {passed}")
        canary_lines.append(f"Tag leaks caught: {len(tag_leaks)}")
        for qid, leaks in tag_leaks:
            canary_lines.append(f"  - {qid}: {leaks}")
            
        canary_passed = (not passed) and (len(tag_leaks) > 0)
        canary_lines.append(f"CANARY SELFTEST RESULT: {'PASSED (Canary caught intentional tag injection)' if canary_passed else 'FAILED (Canary defect went undetected)'}")
        
        with open(SELFTEST_LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(canary_lines) + "\n\n" + log_text + "\n")
            
        print(f"Wrote canary test results to {SELFTEST_LOG}")
        if not canary_passed:
            sys.exit(1)
    else:
        passed, log_text, tag_leaks, parity_failed = run_arm4_audit(bench, inject_selftest_tag=False)
        with open(OUT_LOG, "w", encoding="utf-8") as f:
            f.write(log_text + "\n")
            
        if parity_failed:
            with open(STOP_LOG, "w", encoding="utf-8") as f:
                f.write("STOPPED_U4: set(Arm4) != set(Full) detected in benchmark queries.\n")
            print(f"STOPPED_U4: Node parity check failed. Logged to {STOP_LOG}")
            sys.exit(1)
            
        print(f"Wrote Arm 4 audit results to {OUT_LOG}")
        if not passed:
            sys.exit(1)

if __name__ == '__main__':
    main()
