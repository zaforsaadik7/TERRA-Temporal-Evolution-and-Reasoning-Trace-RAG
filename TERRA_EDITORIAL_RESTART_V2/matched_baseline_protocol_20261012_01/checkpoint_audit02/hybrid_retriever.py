"""
hybrid_retriever.py
-------------------
Implements Reciprocal Rank Fusion (RRF) combining dense and BM25 retrieval lists.
Enforces deduplication within ranked lists, parameter validation (k > 0, top_n > 0),
100/100 candidate fusion feeding token-budget packing, and deterministic tie-breaking.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from .bm25_engine import RobertsonOkapiBM25


def reciprocal_rank_fusion(
    ranked_lists: List[List[str]],
    k: int = 60,
    top_n: int = 100,
) -> List[Tuple[str, float]]:
    """
    Combine multiple ranked lists of doc_ids using Reciprocal Rank Fusion (RRF).
    
    Formula:
      RRF_score(d) = sum_{list_idx} 1.0 / (k + rank(d))
      where rank(d) is 1-based (1, 2, 3...).
      
    Invariants:
    - Deduplicates IDs within each list (only first/best rank contributes).
    - Ties broken deterministically by doc_id ascending.
    """
    if k <= 0:
        raise ValueError(f"RRF constant k must be > 0, got {k}")
    if top_n <= 0:
        raise ValueError(f"top_n must be > 0, got {top_n}")

    scores: Dict[str, float] = {}

    for ranked in ranked_lists:
        seen_in_list: Set[str] = set()
        clean_rank = 1
        for doc_id in ranked:
            doc_id_str = str(doc_id).strip()
            if not doc_id_str or doc_id_str in seen_in_list:
                continue
            seen_in_list.add(doc_id_str)
            contrib = 1.0 / float(k + clean_rank)
            scores[doc_id_str] = scores.get(doc_id_str, 0.0) + contrib
            clean_rank += 1

    # Deterministic sort: score descending, then doc_id ascending
    sorted_candidates = sorted(scores.items(), key=lambda item: (-item[1], str(item[0])))
    return sorted_candidates[:top_n]


class HybridRetriever:
    """
    Hybrid retriever combining dense vector search and Robertson BM25.
    Fuses top-100 dense and top-100 BM25 candidates via RRF (k=60).
    """

    def __init__(
        self,
        bm25_engine: RobertsonOkapiBM25,
        corpus_nodes: Optional[Dict[str, Dict[str, Any]]] = None,
        rrf_k: int = 60,
        default_top_k: int = 100,
    ):
        self.bm25_engine = bm25_engine
        self.corpus_nodes = corpus_nodes or {}
        self.rrf_k = rrf_k
        self.default_top_k = default_top_k

    def retrieve(
        self,
        query: str,
        dense_ranked_ids: List[str],
        top_k_bm25: Optional[int] = None,
        final_top_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute BM25 search and fuse with provided dense ranking.
        Returns structured node dictionaries ready for token-budget evidence packaging.
        """
        k_bm25 = top_k_bm25 if top_k_bm25 is not None else self.default_top_k
        n_final = final_top_n if final_top_n is not None else self.default_top_k

        bm25_results = self.bm25_engine.search(query, top_k=k_bm25)
        bm25_ranked_ids = [doc_id for doc_id, _ in bm25_results]

        ranked_lists = [dense_ranked_ids, bm25_ranked_ids]
        fused = reciprocal_rank_fusion(ranked_lists, k=self.rrf_k, top_n=n_final)

        results: List[Dict[str, Any]] = []
        for doc_id, score in fused:
            node_data = self.corpus_nodes.get(doc_id, {})
            results.append({
                "case_id": doc_id,
                "title": node_data.get("title", f"Case {doc_id}"),
                "decision_date": node_data.get("decision_date", node_data.get("date", "Unknown Date")),
                "holding": node_data.get("substantive_holding", node_data.get("holding", "")),
                "thinking_trace": node_data.get("thinking_trace", ""),
                "snippet": node_data.get("text", node_data.get("snippet", ""))[:600],
                "relation_context": None,  # Arm H has no graph relation labels
                "rrf_score": score,
            })

        return results
