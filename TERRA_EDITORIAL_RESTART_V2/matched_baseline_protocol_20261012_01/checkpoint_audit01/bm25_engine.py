"""
bm25_engine.py
--------------
Pure-Python, zero-dependency implementation of Robertson/Lucene Okapi BM25.
Configured with standard IR parameters (k1=1.5, b=0.75), smoothed non-negative IDF,
and strict deterministic tie-breaking by doc_id ascending.
"""

import math
import re
from typing import Dict, List, Tuple


def tokenize(text: str) -> List[str]:
    """Extract lowercase alphanumeric tokens."""
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())


class RobertsonOkapiBM25:
    """
    Self-contained Robertson/Lucene Okapi BM25 implementation.
    
    Formula:
      score(D, Q) = sum_{q in Q} IDF(q) * [ f(q, D) * (k1 + 1) ] / [ f(q, D) + k1 * (1 - b + b * (|D| / avgdl)) ]
      
      where IDF(q) = ln(1 + (N - n(q) + 0.5) / (n(q) + 0.5))
      which guarantees non-negative weights for all document frequencies n(q) <= N.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = float(k1)
        self.b = float(b)
        self.doc_count: int = 0
        self.avg_doc_len: float = 0.0
        self.doc_lengths: Dict[str, int] = {}
        self.doc_freqs: Dict[str, int] = {}
        self.term_freqs: Dict[str, Dict[str, int]] = {}  # doc_id -> {term: count}

    def index_corpus(self, corpus: Dict[str, str]) -> None:
        """
        Index a dictionary of {doc_id: text}.
        """
        self.doc_count = len(corpus)
        if self.doc_count == 0:
            self.avg_doc_len = 0.0
            self.doc_lengths.clear()
            self.doc_freqs.clear()
            self.term_freqs.clear()
            return

        total_length = 0
        self.doc_lengths.clear()
        self.doc_freqs.clear()
        self.term_freqs.clear()

        # Deterministic indexing order
        for doc_id in sorted(corpus.keys()):
            tokens = tokenize(corpus[doc_id])
            doc_len = len(tokens)
            self.doc_lengths[doc_id] = doc_len
            total_length += doc_len

            tf: Dict[str, int] = {}
            seen_terms = set()
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
                if token not in seen_terms:
                    self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
                    seen_terms.add(token)
            self.term_freqs[doc_id] = tf

        self.avg_doc_len = total_length / float(self.doc_count)

    def idf(self, term: str) -> float:
        """
        Calculate smoothed non-negative IDF for a term.
        """
        n_q = self.doc_freqs.get(term, 0)
        if self.doc_count == 0:
            return 0.0
        return math.log(1.0 + (float(self.doc_count) - float(n_q) + 0.5) / (float(n_q) + 0.5))

    def score_document(self, query_tokens: List[str], doc_id: str) -> float:
        """
        Compute BM25 score for a single document against query tokens.
        """
        if doc_id not in self.term_freqs:
            return 0.0

        doc_len = self.doc_lengths[doc_id]
        if self.avg_doc_len == 0.0:
            len_norm = 1.0
        else:
            len_norm = 1.0 - self.b + self.b * (float(doc_len) / self.avg_doc_len)

        score = 0.0
        tf_dict = self.term_freqs[doc_id]
        for q in query_tokens:
            f = tf_dict.get(q, 0)
            if f > 0:
                idf_q = self.idf(q)
                numerator = float(f) * (self.k1 + 1.0)
                denominator = float(f) + self.k1 * len_norm
                score += idf_q * (numerator / denominator)
        return score

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Retrieve top_k documents for a query.
        Ties are broken deterministically by doc_id in ascending alphanumeric order.
        Returns list of (doc_id, score).
        """
        if self.doc_count == 0 or top_k <= 0:
            return []

        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        # Find documents containing at least one query token to avoid scanning whole corpus
        candidate_doc_ids = set()
        for q in q_tokens:
            if q in self.doc_freqs:
                for doc_id, tf_map in self.term_freqs.items():
                    if q in tf_map:
                        candidate_doc_ids.add(doc_id)

        scores: List[Tuple[str, float]] = []
        for doc_id in candidate_doc_ids:
            s = self.score_document(q_tokens, doc_id)
            if s > 0.0:
                scores.append((doc_id, s))

        # Sort: score descending, doc_id ascending
        scores.sort(key=lambda item: (-item[1], str(item[0])))
        return scores[:top_k]
