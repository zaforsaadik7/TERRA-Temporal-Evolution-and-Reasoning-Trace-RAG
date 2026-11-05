"""
hybrid_retriever.py
-------------------
Implements Reciprocal Rank Fusion (RRF) combining dense and BM25 retrieval lists.
Uses standard constant k=60 and deterministic tie-breaking by doc_id ascending.
"""

from typing import Dict, List, Optional, Tuple
from .bm25_engine import RobertsonOkapiBM25


def reciprocal_rank_fusion(
    ranked_lists: List[List[str]],
    k: int = 60,
    top_n: int = 10,
) -> List[Tuple[str, float]]:
    """
    Combine multiple ranked lists of doc_ids using Reciprocal Rank Fusion (RRF).
    
    Formula:
      RRF_score(d) = sum_{list_idx} 1.0 / (k + rank(d))
      where rank(d) is 1-based (1, 2, 3...).
      
    Ties broken deterministically by doc_id ascending.
    """
    scores: Dict[str, float] = {}

    for ranked in ranked_lists:
        for rank_idx, doc_id in enumerate(ranked, start=1):
            contrib = 1.0 / float(k + rank_idx)
            scores[doc_id] = scores.get(doc_id, 0.0) + contrib

    # Deterministic sort: score descending, then doc_id ascending
    sorted_candidates = sorted(scores.items(), key=lambda item: (-item[1], str(item[0])))
    return sorted_candidates[:top_n]


class HybridRetriever:
    """
    Hybrid retriever combining dense vector search and Robertson BM25.
    """

    def __init__(self, bm25_engine: RobertsonOkapiBM25, rrf_k: int = 60):
        self.bm25_engine = bm25_engine
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        dense_ranked_ids: List[str],
        top_k_bm25: int = 30,
        final_top_n: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Execute BM25 search and fuse with provided dense ranking.
        """
        bm25_results = self.bm25_engine.search(query, top_k=top_k_bm25)
        bm25_ranked_ids = [doc_id for doc_id, _ in bm25_results]

        ranked_lists = [dense_ranked_ids, bm25_ranked_ids]
        return reciprocal_rank_fusion(ranked_lists, k=self.rrf_k, top_n=final_top_n)
