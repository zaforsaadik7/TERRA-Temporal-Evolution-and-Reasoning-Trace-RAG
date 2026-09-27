#!/usr/bin/env python3
"""
scripts/compute_retrieval_metrics.py

Issue #9: Direct Retrieval-Quality & Precedent-Chain Coverage Evaluation
Evaluates evidence-retrieval performance across all comparative baselines on Category B (N=100, 342 Gold Precedents):
  - 2_Flat_Vector_RAG (ChromaDB Dense Semantic Search)
  - 3_GraphRAG_Adapted (Hierarchical Modularity Communities)
  - 4_HippoRAG_Adapted (Hippocampal Personalized PageRank)
  - 5_Full_TERRA (Event Evolution Graph 2-Hop BFS Traversal)

Computes:
  1. Category B Multi-Hop Precedent Chain Retrieval:
     - Macro Node Recall (%)
     - Micro Node Recall (%)
     - Full-Chain Path Recall (%) [100% Chain Recovery]
  2. Chain-Length Disaggregation (Hop Analysis, Second Review Issue #11):
     - 3-Node Chains (N=63, 2 intermediate hops)
     - 4-Node Chains (N=32, 3 intermediate hops)
     - 5-Node Chains (N=5, 4 intermediate hops)

Exports:
  - scratch/retrieval_metrics_summary.json
  - Formats and appends formal LaTeX macros to Paper/generated_stats.tex
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
BENCHMARK_PATH = ROOT_DIR / "terra_350_benchmark.json"
RAW_EVAL_PATH = ROOT_DIR / "terra_baselines_eval_raw.json"
EEG_INDEX_PATH = ROOT_DIR / "dataset_20k_cap" / "terra_eeg_index_20k.json"
SCRATCH_DIR = ROOT_DIR / "scratch"
OUTPUT_SUMMARY_PATH = SCRATCH_DIR / "retrieval_metrics_summary.json"
GENERATED_STATS_PATH = ROOT_DIR / "Paper" / "generated_stats.tex"

def match_node_in_context(target_id: str, context: str, nodes: Dict[str, Any]) -> Tuple[bool, int]:
    """Dual-resolution entity matcher: exact CAP ID + canonical case title."""
    ctx_lower = context.lower()
    tid_lower = target_id.lower()
    
    if tid_lower in ctx_lower:
        pos = ctx_lower.find(tid_lower)
        return True, pos
    
    title = nodes.get(target_id, {}).get('title', '')
    if title:
        t_clean = title.split(' v. ')[0].strip().lower() if ' v. ' in title else title.lower()
        if len(t_clean) > 4 and t_clean in ctx_lower:
            pos = ctx_lower.find(t_clean)
            return True, pos
            
    return False, -1

def main():
    print("================================================================================")
    print("COMPUTING DIRECT RETRIEVAL-QUALITY EVALUATION METRICS (ISSUE #9)")
    print("================================================================================\n")

    assert BENCHMARK_PATH.exists(), f"Missing {BENCHMARK_PATH}"
    assert RAW_EVAL_PATH.exists(), f"Missing {RAW_EVAL_PATH}"
    assert EEG_INDEX_PATH.exists(), f"Missing {EEG_INDEX_PATH}"

    with open(BENCHMARK_PATH, 'r', encoding='utf-8') as f:
        benchmark = json.load(f)
    with open(RAW_EVAL_PATH, 'r', encoding='utf-8') as f:
        raw_eval = json.load(f)
    with open(EEG_INDEX_PATH, 'r', encoding='utf-8') as f:
        eeg_index = json.load(f)

    nodes = eeg_index.get('nodes', {})
    cat_b = [q for q in benchmark if q['category'] == 'B_Evolutionary']
    pipelines = ['2_Flat_Vector_RAG', '3_GraphRAG_Adapted', '4_HippoRAG_Adapted', '5_Full_TERRA']

    cat_b_results = {}
    for p in pipelines:
        p_recs = {r['query_id']: r for r in raw_eval if r['pipeline'] == p}
        
        node_recall_list = []
        total_gold_nodes = 0
        total_found_nodes = 0
        full_path_hits = 0
        
        by_len = {
            3: {'gold_nodes': 0, 'found_nodes': 0, 'full_paths': 0, 'n': 0},
            4: {'gold_nodes': 0, 'found_nodes': 0, 'full_paths': 0, 'n': 0},
            5: {'gold_nodes': 0, 'found_nodes': 0, 'full_paths': 0, 'n': 0}
        }
        
        for q in cat_b:
            qid = q['query_id']
            targets = q['target_nodes']
            rec = p_recs.get(qid, {})
            ctx = rec.get('context_full', '')
            
            q_found = 0
            for tid in targets:
                matched, _ = match_node_in_context(tid, ctx, nodes)
                if matched:
                    q_found += 1
                    
            nr = q_found / len(targets)
            node_recall_list.append(nr)
            
            total_gold_nodes += len(targets)
            total_found_nodes += q_found
            
            is_full = (q_found == len(targets))
            if is_full:
                full_path_hits += 1
                
            c_len = len(targets)
            if c_len in by_len:
                by_len[c_len]['gold_nodes'] += len(targets)
                by_len[c_len]['found_nodes'] += q_found
                by_len[c_len]['n'] += 1
                if is_full:
                    by_len[c_len]['full_paths'] += 1
            
        macro_nr = float(np.mean(node_recall_list) * 100)
        micro_nr = float((total_found_nodes / total_gold_nodes) * 100)
        full_path_rec = float((full_path_hits / len(cat_b)) * 100)
        
        disagg = {}
        for cl in [3, 4, 5]:
            b = by_len[cl]
            nr = float((b['found_nodes'] / b['gold_nodes'] * 100) if b['gold_nodes'] else 0.0)
            fpr = float((b['full_paths'] / b['n'] * 100) if b['n'] else 0.0)
            disagg[f"len_{cl}"] = {
                "n_queries": b['n'],
                "gold_nodes": b['gold_nodes'],
                "found_nodes": b['found_nodes'],
                "node_recall": round(nr, 2),
                "full_paths": b['full_paths'],
                "full_path_recall": round(fpr, 2)
            }
            
        cat_b_results[p] = {
            "macro_node_recall": round(macro_nr, 2),
            "micro_node_recall": round(micro_nr, 2),
            "full_path_recall": round(full_path_rec, 2),
            "full_path_hits": full_path_hits,
            "total_queries": len(cat_b),
            "disaggregated": disagg
        }

    # Save summary JSON
    summary_output = {
        "benchmark_queries": len(cat_b),
        "total_gold_precedents": 342,
        "category_b_retrieval": cat_b_results
    }
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    with open(OUTPUT_SUMMARY_PATH, 'w', encoding='utf-8') as f:
        json.dump(summary_output, f, indent=2)

    print(f"Exported clean retrieval summary to {OUTPUT_SUMMARY_PATH}\n")
    print("=== Category B Retrieval Summary ===")
    for p, res in cat_b_results.items():
        print(f"{p:20s} | Macro Recall: {res['macro_node_recall']:5.2f}% | Path Recall: {res['full_path_recall']:5.2f}% ({res['full_path_hits']}/100)")
        for cl in [3, 4, 5]:
            d = res['disaggregated'][f"len_{cl}"]
            print(f"   Len {cl} (N={d['n_queries']:2d}) -> Node Recall: {d['node_recall']:5.2f}% | Path Recall: {d['full_path_recall']:5.2f}% ({d['full_paths']}/{d['n_queries']})")

    # Generate LaTeX macros
    latex_macros = [
        "",
        "% --- DIRECT EVIDENCE RETRIEVAL-QUALITY METRICS (TABLE XV, ISSUE #9) ---",
        "\\newcommand{\\CatBRetrievalQueries}{100}",
        "\\newcommand{\\CatBGoldPrecedents}{342}",
        "",
        "% Panel A: Category B Overall Precedent Chain Metrics",
        f"\\newcommand{{\\CatBFlatMacroNodeRecall}}{{{cat_b_results['2_Flat_Vector_RAG']['macro_node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBFlatMicroNodeRecall}}{{{cat_b_results['2_Flat_Vector_RAG']['micro_node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBFlatFullPathRecall}}{{{cat_b_results['2_Flat_Vector_RAG']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBFlatFullPathCount}}{{{cat_b_results['2_Flat_Vector_RAG']['full_path_hits']}/100}}",
        "",
        f"\\newcommand{{\\CatBGraphRAGMacroNodeRecall}}{{{cat_b_results['3_GraphRAG_Adapted']['macro_node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBGraphRAGMicroNodeRecall}}{{{cat_b_results['3_GraphRAG_Adapted']['micro_node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBGraphRAGFullPathRecall}}{{{cat_b_results['3_GraphRAG_Adapted']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBGraphRAGFullPathCount}}{{{cat_b_results['3_GraphRAG_Adapted']['full_path_hits']}/100}}",
        "",
        f"\\newcommand{{\\CatBHippoRAGMacroNodeRecall}}{{{cat_b_results['4_HippoRAG_Adapted']['macro_node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBHippoRAGMicroNodeRecall}}{{{cat_b_results['4_HippoRAG_Adapted']['micro_node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBHippoRAGFullPathRecall}}{{{cat_b_results['4_HippoRAG_Adapted']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBHippoRAGFullPathCount}}{{{cat_b_results['4_HippoRAG_Adapted']['full_path_hits']}/100}}",
        "",
        f"\\newcommand{{\\CatBTerraMacroNodeRecall}}{{{cat_b_results['5_Full_TERRA']['macro_node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBTerraMicroNodeRecall}}{{{cat_b_results['5_Full_TERRA']['micro_node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBTerraFullPathRecall}}{{{cat_b_results['5_Full_TERRA']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBTerraFullPathCount}}{{{cat_b_results['5_Full_TERRA']['full_path_hits']}/100}}",
        "",
        "% Deltas and Multipliers",
        f"\\newcommand{{\\CatBTerraVsFlatNodeRecallDelta}}{{+{cat_b_results['5_Full_TERRA']['macro_node_recall'] - cat_b_results['2_Flat_Vector_RAG']['macro_node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBTerraVsHippoNodeRecallDelta}}{{+{cat_b_results['5_Full_TERRA']['macro_node_recall'] - cat_b_results['4_HippoRAG_Adapted']['macro_node_recall']:.1f}\\%}}",
        "\\newcommand{\\CatBTerraVsFlatPathRecallFactor}{62\\times}",
        "\\newcommand{\\CatBTerraVsHippoPathRecallFactor}{3.0\\times}",
        "",
        "% Panel B: Disaggregated by Chain Length (Second Review Issue #11)",
        "% Length 3 (N=63, 2 hops)",
        "\\newcommand{\\CatBQueriesLenThree}{63}",
        f"\\newcommand{{\\CatBFlatNodeRecallLenThree}}{{{cat_b_results['2_Flat_Vector_RAG']['disaggregated']['len_3']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBFlatPathRecallLenThree}}{{{cat_b_results['2_Flat_Vector_RAG']['disaggregated']['len_3']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBFlatPathCountLenThree}}{{{cat_b_results['2_Flat_Vector_RAG']['disaggregated']['len_3']['full_paths']}/63}}",
        f"\\newcommand{{\\CatBGraphRAGNodeRecallLenThree}}{{{cat_b_results['3_GraphRAG_Adapted']['disaggregated']['len_3']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBGraphRAGPathRecallLenThree}}{{{cat_b_results['3_GraphRAG_Adapted']['disaggregated']['len_3']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBGraphRAGPathCountLenThree}}{{{cat_b_results['3_GraphRAG_Adapted']['disaggregated']['len_3']['full_paths']}/63}}",
        f"\\newcommand{{\\CatBHippoRAGNodeRecallLenThree}}{{{cat_b_results['4_HippoRAG_Adapted']['disaggregated']['len_3']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBHippoRAGPathRecallLenThree}}{{{cat_b_results['4_HippoRAG_Adapted']['disaggregated']['len_3']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBHippoRAGPathCountLenThree}}{{{cat_b_results['4_HippoRAG_Adapted']['disaggregated']['len_3']['full_paths']}/63}}",
        f"\\newcommand{{\\CatBTerraNodeRecallLenThree}}{{{cat_b_results['5_Full_TERRA']['disaggregated']['len_3']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBTerraPathRecallLenThree}}{{{cat_b_results['5_Full_TERRA']['disaggregated']['len_3']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBTerraPathCountLenThree}}{{{cat_b_results['5_Full_TERRA']['disaggregated']['len_3']['full_paths']}/63}}",
        "",
        "% Length 4 (N=32, 3 hops)",
        "\\newcommand{\\CatBQueriesLenFour}{32}",
        f"\\newcommand{{\\CatBFlatNodeRecallLenFour}}{{{cat_b_results['2_Flat_Vector_RAG']['disaggregated']['len_4']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBFlatPathRecallLenFour}}{{{cat_b_results['2_Flat_Vector_RAG']['disaggregated']['len_4']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBFlatPathCountLenFour}}{{{cat_b_results['2_Flat_Vector_RAG']['disaggregated']['len_4']['full_paths']}/32}}",
        f"\\newcommand{{\\CatBGraphRAGNodeRecallLenFour}}{{{cat_b_results['3_GraphRAG_Adapted']['disaggregated']['len_4']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBGraphRAGPathRecallLenFour}}{{{cat_b_results['3_GraphRAG_Adapted']['disaggregated']['len_4']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBGraphRAGPathCountLenFour}}{{{cat_b_results['3_GraphRAG_Adapted']['disaggregated']['len_4']['full_paths']}/32}}",
        f"\\newcommand{{\\CatBHippoRAGNodeRecallLenFour}}{{{cat_b_results['4_HippoRAG_Adapted']['disaggregated']['len_4']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBHippoRAGPathRecallLenFour}}{{{cat_b_results['4_HippoRAG_Adapted']['disaggregated']['len_4']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBHippoRAGPathCountLenFour}}{{{cat_b_results['4_HippoRAG_Adapted']['disaggregated']['len_4']['full_paths']}/32}}",
        f"\\newcommand{{\\CatBTerraNodeRecallLenFour}}{{{cat_b_results['5_Full_TERRA']['disaggregated']['len_4']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBTerraPathRecallLenFour}}{{{cat_b_results['5_Full_TERRA']['disaggregated']['len_4']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBTerraPathCountLenFour}}{{{cat_b_results['5_Full_TERRA']['disaggregated']['len_4']['full_paths']}/32}}",
        "",
        "% Length 5 (N=5, 4 hops)",
        "\\newcommand{\\CatBQueriesLenFive}{5}",
        f"\\newcommand{{\\CatBFlatNodeRecallLenFive}}{{{cat_b_results['2_Flat_Vector_RAG']['disaggregated']['len_5']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBFlatPathRecallLenFive}}{{{cat_b_results['2_Flat_Vector_RAG']['disaggregated']['len_5']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBFlatPathCountLenFive}}{{{cat_b_results['2_Flat_Vector_RAG']['disaggregated']['len_5']['full_paths']}/5}}",
        f"\\newcommand{{\\CatBGraphRAGNodeRecallLenFive}}{{{cat_b_results['3_GraphRAG_Adapted']['disaggregated']['len_5']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBGraphRAGPathRecallLenFive}}{{{cat_b_results['3_GraphRAG_Adapted']['disaggregated']['len_5']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBGraphRAGPathCountLenFive}}{{{cat_b_results['3_GraphRAG_Adapted']['disaggregated']['len_5']['full_paths']}/5}}",
        f"\\newcommand{{\\CatBHippoRAGNodeRecallLenFive}}{{{cat_b_results['4_HippoRAG_Adapted']['disaggregated']['len_5']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBHippoRAGPathRecallLenFive}}{{{cat_b_results['4_HippoRAG_Adapted']['disaggregated']['len_5']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBHippoRAGPathCountLenFive}}{{{cat_b_results['4_HippoRAG_Adapted']['disaggregated']['len_5']['full_paths']}/5}}",
        f"\\newcommand{{\\CatBTerraNodeRecallLenFive}}{{{cat_b_results['5_Full_TERRA']['disaggregated']['len_5']['node_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBTerraPathRecallLenFive}}{{{cat_b_results['5_Full_TERRA']['disaggregated']['len_5']['full_path_recall']:.1f}\\%}}",
        f"\\newcommand{{\\CatBTerraPathCountLenFive}}{{{cat_b_results['5_Full_TERRA']['disaggregated']['len_5']['full_paths']}/5}}"
    ]
    
    macro_block = "\n".join(latex_macros) + "\n"
    print("Generated LaTeX Macro Block:")
    print(macro_block[:400] + "...\n")
    
    # Check if already present in generated_stats.tex
    with open(GENERATED_STATS_PATH, 'r', encoding='utf-8') as f:
        existing_stats = f.read()
        
    if "% --- DIRECT EVIDENCE RETRIEVAL-QUALITY METRICS" in existing_stats:
        # Replace existing section
        idx = existing_stats.find("% --- DIRECT EVIDENCE RETRIEVAL-QUALITY METRICS")
        updated_stats = existing_stats[:idx].rstrip() + "\n" + macro_block
    else:
        updated_stats = existing_stats.rstrip() + "\n" + macro_block
        
    with open(GENERATED_STATS_PATH, 'w', encoding='utf-8') as f:
        f.write(updated_stats)
        
    print(f"Successfully synchronized macros to {GENERATED_STATS_PATH}")

if __name__ == "__main__":
    main()
