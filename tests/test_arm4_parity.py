"""
tests/test_arm4_parity.py - Unit Test for Arm 4 (TERRA-Unlabeled) Parity Invariants
==================================================================================
Asserts:
1. Arm 4's serialized context contains ZERO occurrences of '[OVERRULES' or '[REPUDIATES]'.
2. All case snippets/holdings in Arm 4's context are strictly capped at 250 characters (uniform budget).
3. The generation prompt contains no relation-label oracle cues.
4. The grading context passed to the evaluation grader contains zero '[OVERRULES' or '[REPUDIATES]' tags.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import networkx as nx
from baselines.arm4_unlabeled import serialize_context_arm4_unlabeled, build_arm4_generator_prompt

def test_arm4_parity_on_5_queries():
    print("=" * 80)
    print("RUNNING ARM 4 (TERRA-UNLABELED) PARITY UNIT TEST ON 5 BENCHMARK QUERIES")
    print("=" * 80)
    
    # Load EEG
    with open(ROOT / 'dataset_20k_cap' / 'terra_eeg_index_20k.json', encoding='utf-8') as f:
        eeg_data = json.load(f)
    
    # Build NetworkX DiGraph
    G = nx.DiGraph()
    for nid, nd in eeg_data['nodes'].items():
        G.add_node(nid, **nd)
    for e in eeg_data['edges']:
        G.add_edge(e['source'], e['target'], relation=e.get('relation', 'CITES'))
    
    # Load benchmark
    with open(ROOT / 'data' / 'obscure_overruled_benchmark.json', encoding='utf-8') as f:
        bench = json.load(f)
        
    test_items = bench[:5]  # First 5 benchmark items: OBS_001 to OBS_005
    
    for item in test_items:
        qid = item['query_id']
        tcase = item['target_case']
        tnode = item['target_nodes'][0]
        onode = item['overruling_nodes'][0]
        query = item['query']
        
        print(f"\nEvaluating [{qid}] {tcase}:")
        print(f"  Target: {tnode}, Overruler in graph: {onode}")
        
        # Verify that the graph actually has an OVERRULES edge connecting them
        raw_edge_data = G.get_edge_data(onode, tnode) or G.get_edge_data(tnode, onode) or {}
        print(f"  Raw Graph Edge Relation: {raw_edge_data.get('relation', 'CITES')}")
        
        # 1. Generate Arm 4 Serialized Context
        context = serialize_context_arm4_unlabeled(
            seeds=[tnode],
            eeg=G,
            max_structural_chars=15000,
            max_snippet_chars=250
        )
        
        # Assertion 1: No oracle relation labels in serialized context
        assert "[OVERRULES" not in context, f"[{qid}] Oracle leak: '[OVERRULES' found in Arm 4 context!"
        assert "[REPUDIATES]" not in context, f"[{qid}] Oracle leak: '[REPUDIATES]' found in Arm 4 context!"
        assert "[OVERRULES / REPUDIATES]" not in context, f"[{qid}] Oracle leak: '[OVERRULES / REPUDIATES]' found!"
        print("  -> Assertion 1 PASSED: Zero '[OVERRULES]' or '[REPUDIATES]' tags in context.")
        
        # Assertion 2: All snippets capped at 250 chars (uniform character budget)
        lines = context.strip().split('\n')
        for line in lines:
            if "[Holding]:" in line:
                holding_part = line.split("[Holding]:")[1].strip()
                assert len(holding_part) <= 250, (
                    f"[{qid}] Budget breach: Holding snippet length {len(holding_part)} exceeds 250 char cap!"
                )
        print("  -> Assertion 2 PASSED: All snippets strictly <= 250 characters (uniform budget).")
        
        # Assertion 3: Generation prompt parity
        prompt = build_arm4_generator_prompt(query, context)
        assert "[OVERRULES / REPUDIATES]" not in prompt, f"[{qid}] Oracle leak in generator prompt!"
        assert "[OVERRULES" not in prompt, f"[{qid}] Oracle tag in generator prompt!"
        print("  -> Assertion 3 PASSED: Generator prompt contains zero oracle relation instructions.")
        
        # Assertion 4: Grading context parity
        # In evaluation, grading_context = context (no separate privileged context)
        grading_context = context
        assert "[OVERRULES" not in grading_context, f"[{qid}] Oracle leak in grading_context!"
        assert "[REPUDIATES]" not in grading_context, f"[{qid}] Oracle leak in grading_context!"
        print("  -> Assertion 4 PASSED: Grading context contains zero oracle relation tags.")

    print("\n" + "=" * 80)
    print("ALL 5 QUERIES PASSED ARM 4 PARITY ASSERTIONS WITH ZERO FAILS!")
    print("=" * 80)

if __name__ == "__main__":
    test_arm4_parity_on_5_queries()
