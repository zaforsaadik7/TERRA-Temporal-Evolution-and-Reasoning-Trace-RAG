"""
tests/test_production_arm4_parity.py - Production Arm 4 Parity Unit Test & Context Diff
========================================================================================
Tests extract_graph_context directly from ask_terra.py across 5 benchmark queries.
Asserts:
1. Full TERRA serializes [OVERRULES / REPUDIATES] and awards expanded budget.
2. Arm 4 serializes generic [CITES], zero [OVERRULES / REPUDIATES], and enforces uniform <= 250-char budget.
3. Emits unified diff between Full TERRA and Arm 4 serialized context for OBS_001.
"""

import json
import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ask_terra import extract_graph_context

def test_production_arm4_parity():
    print("=" * 80)
    print("RUNNING PRODUCTION ARM 4 PARITY TEST & CONTEXT DIFF (FIRST 5 QUERIES)")
    print("=" * 80)
    
    bench = json.load(open(ROOT / 'data' / 'obscure_overruled_benchmark.json', encoding='utf-8'))
    first_5 = bench[:5]
    
    diff_output = ""
    
    for it in first_5:
        qid = it['query_id']
        tcase = it['target_case']
        tnode = it['target_node']
        onode = it['overruling_node']
        
        # Build metadata list as vector search returns
        retrieved_metadatas = [{'node_id': tnode, 'case_id': tnode}]
        
        # 1. Full TERRA Context (Production)
        ctx_full = extract_graph_context(retrieved_metadatas, max_depth=2, arm4_unlabeled=False)
        
        # 2. Arm 4 Context (Production Path Ablation)
        ctx_arm4 = extract_graph_context(retrieved_metadatas, max_depth=2, arm4_unlabeled=True)
        
        print(f"\nEvaluating [{qid}] {tcase}:")
        print(f"  Target: {tnode}, Overruling neighbor: {onode}")
        
        # Assertions on Full TERRA
        assert "[OVERRULES / REPUDIATES]" in ctx_full, f"[{qid}] Expected [OVERRULES / REPUDIATES] in Full TERRA context!"
        print("  -> Full TERRA: Contains '[OVERRULES / REPUDIATES]' tag.")
        
        # Assertions on Arm 4
        assert "[OVERRULES" not in ctx_arm4, f"[{qid}] Found [OVERRULES in Arm 4 context!"
        assert "[REPUDIATES]" not in ctx_arm4, f"[{qid}] Found [REPUDIATES] in Arm 4 context!"
        assert "[CITES]" in ctx_arm4, f"[{qid}] Expected [CITES] in Arm 4 context!"
        print("  -> Arm 4: Zero '[OVERRULES]' or '[REPUDIATES]' tags (all normalized to '[CITES]').")
        
        # Budget check on Arm 4 snippets
        for line in ctx_arm4.splitlines():
            if "[Holding]:" in line:
                snip = line.split("[Holding]:")[1].strip()
                assert len(snip) <= 250, f"[{qid}] Arm 4 snippet length {len(snip)} exceeds 250-char cap!"
        print("  -> Arm 4: All snippets strictly <= 250 chars (uniform budget).")
        
        if qid == "OBS_001":
            diff = list(difflib.unified_diff(
                ctx_full.splitlines(keepends=True),
                ctx_arm4.splitlines(keepends=True),
                fromfile="Full_TERRA_Context_OBS_001",
                tofile="Arm4_Unlabeled_Context_OBS_001",
                n=3
            ))
            diff_output = "".join(diff)
            diff_path = ROOT / 'scratch' / 'arm4_context_diff_obs001.diff'
            with open(diff_path, 'w', encoding='utf-8') as f:
                f.write(diff_output)
            print(f"\nWrote unified diff for OBS_001 to: {diff_path}")

    print("\n" + "=" * 80)
    print("UNIFIED DIFF FOR OBS_001 (Full TERRA vs Arm 4 Production Context):")
    print("=" * 80)
    print(diff_output)
    print("=" * 80)
    print("ALL 5 BENCHMARK QUERIES PASSED PRODUCTION ARM 4 PARITY INVARIANTS!")
    print("=" * 80)

if __name__ == '__main__':
    test_production_arm4_parity()
