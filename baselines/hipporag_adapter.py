"""
baselines/hipporag_adapter.py - HippoRAG-Adapted Implementation
Implements hippocampal memory indexing and Personalized PageRank (PPR) spreading activation
directly over the 20,000-opinion legal precedent network, achieving associative multi-hop retrieval.
"""

import os
import sys
import json
import time
import numpy as np
import scipy.sparse as sp
import chromadb

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baselines.common import (
    load_verified_corpus,
    format_neutral_prompt,
    PayloadParityInterceptor,
    CORPUS_PATH
)

VECTOR_DB_PATH = os.environ.get("TERRA_VECTOR_DB_PATH", "./dataset_20k_cap/vector_db_20k")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")


class HippoRAGAdaptedEngine:
    def __init__(
        self,
        corpus_path: str = CORPUS_PATH,
        vector_db_path: str = VECTOR_DB_PATH,
        alpha: float = 0.85,
        max_iter: int = 50,
        tol: float = 1e-6
    ):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.alpha = alpha
        self.max_iter = max_iter
        self.tol = tol

        # 1. Load verified corpus
        self.corpus_data = load_verified_corpus(corpus_path)
        self.nodes = self.corpus_data.get("nodes", {})
        self.edges = self.corpus_data.get("edges", [])

        # 2. Build index mappings
        self.node_ids = sorted(list(self.nodes.keys()))
        self.id_to_idx = {nid: i for i, nid in enumerate(self.node_ids)}
        self.idx_to_id = {i: nid for i, nid in enumerate(self.node_ids)}
        self.N = len(self.node_ids)

        # 3. Build sparse transition matrix for PPR
        self.transition_matrix = self._build_sparse_transition_matrix()

        # 4. Connect to ChromaDB for seed mapping
        self.chroma_client = chromadb.PersistentClient(path=vector_db_path)
        self.collection = self.chroma_client.get_collection(name="thinking_traces")
        self.interceptor = PayloadParityInterceptor()

    def _build_sparse_transition_matrix(self) -> sp.csc_matrix:
        print("[HippoRAG-Adapted] Building sparse transition matrix over 145,363 citation edges...")
        t0 = time.time()
        rows, cols = [], []

        for e in self.edges:
            src = e.get("source")
            tgt = e.get("target")
            if src in self.id_to_idx and tgt in self.id_to_idx:
                u = self.id_to_idx[src]
                v = self.id_to_idx[tgt]
                # HippoRAG associative spreading allows bidirectional walk across citation links
                rows.extend([v, u])
                cols.extend([u, v])

        data = np.ones(len(rows), dtype=np.float32)
        adj = sp.csr_matrix((data, (rows, cols)), shape=(self.N, self.N))

        # Degree normalization: M = A D^{-1} (column-stochastic transition matrix)
        out_degrees = np.array(adj.sum(axis=0)).flatten()
        out_degrees[out_degrees == 0] = 1.0  # Handle dangling nodes
        inv_deg = 1.0 / out_degrees

        inv_deg_mat = sp.diags(inv_deg)
        trans_mat = adj.dot(inv_deg_mat).tocsc()
        print(f"[HippoRAG-Adapted] Transition matrix constructed in {time.time()-t0:.2f}s (Shape: {trans_mat.shape}, Nonzeros: {trans_mat.nnz}).")
        return trans_mat

    def run_ppr(self, seed_node_ids: list[str]) -> tuple[np.ndarray, int, float]:
        """
        Executes Personalized PageRank power iteration:
        p_{t+1} = alpha * M * p_t + (1 - alpha) * s
        """
        seed_indices = [self.id_to_idx[nid] for nid in seed_node_ids if nid in self.id_to_idx]
        if not seed_indices:
            # Uniform fallback if no valid seeds
            s = np.ones(self.N, dtype=np.float32) / self.N
        else:
            s = np.zeros(self.N, dtype=np.float32)
            s[seed_indices] = 1.0 / len(seed_indices)

        p = s.copy()
        residual = 1.0
        converged_iter = 0

        for it in range(self.max_iter):
            p_next = self.alpha * self.transition_matrix.dot(p) + (1.0 - self.alpha) * s
            residual = float(np.linalg.norm(p_next - p, 1))
            p = p_next
            converged_iter = it + 1
            if residual < self.tol:
                break

        return p, converged_iter, residual

    def retrieve_associative_context(self, query: str, top_k: int = 5) -> tuple[str, dict]:
        # 1. Identify seed precedent nodes (Entity Linking: Direct Case Mentions + Vector Fallback)
        query_lower = query.lower()
        direct_seed_ids = [
            nid for nid, n in self.nodes.items()
            if len(n.get("title", "")) > 6 and n.get("title", "").lower() in query_lower
        ]
        
        if direct_seed_ids:
            seed_ids = direct_seed_ids[:3]
        else:
            res = self.collection.query(query_texts=[query], n_results=3)
            seed_ids = res.get("ids", [[]])[0]

        # 2. Execute Personalized PageRank spreading activation
        p_dist, num_iters, residual = self.run_ppr(seed_ids)

        # 3. Extract top-k nodes by stationary probability
        top_indices = np.argsort(p_dist)[::-1][:top_k]

        passages = []
        retrieved_ids = []
        for rank, idx in enumerate(top_indices, 1):
            nid = self.idx_to_id[idx]
            retrieved_ids.append(nid)
            node_info = self.nodes.get(nid, {})
            case_name = node_info.get("title", f"Case_{nid}")
            date = node_info.get("decision_date", "Unknown")[:4] if node_info.get("decision_date") else "Unknown"
            dom = node_info.get("primary_domain", "Legal Precedent")
            text_snippet = node_info.get("text", "")[:400].replace("\n", " ").strip()
            score = p_dist[idx]

            passages.append(
                f"{rank}. Precedent: {case_name} ({date}) [{dom}]\n"
                f"   HippoRAG Activation Mass: {score:.6f}\n"
                f"   Syllabus / Holdings: {text_snippet}..."
            )

        context = (
            "[HIPPOCAMPAL ASSOCIATIVE RETRIEVAL: PERSONALIZED PAGERANK ACTIVATION]\n"
            + f"Personalization Seeds: {', '.join(seed_ids)} (PPR Iters: {num_iters}, Residual: {residual:.2e})\n\n"
            + "\n\n".join(passages)
        )

        metadata = {
            "seed_ids": seed_ids,
            "retrieved_ids": retrieved_ids,
            "ppr_iters": num_iters,
            "ppr_residual": residual
        }
        return context, metadata

    def infer(self, query: str, query_id: str = "N/A", return_timing: bool = True) -> tuple:
        t0 = time.time()
        context, meta = self.retrieve_associative_context(query, top_k=5)
        retrieval_ms = round((time.time() - t0) * 1000, 2)

        prompt = format_neutral_prompt(query, context)
        t1 = time.time()
        resp = self.interceptor.generate(
            prompt=prompt,
            query_id=query_id,
            pipeline_name="4_HippoRAG_Adapted"
        )
        gen_ms = round((time.time() - t1) * 1000, 2)
        total_ms = round((time.time() - t0) * 1000, 2)

        timing = {
            "routing_ms": 0,
            "retrieval_ms": retrieval_ms,
            "grading_ms": 0,
            "generation_ms": gen_ms,
            "total_ms": total_ms,
            "_generation_model_used": resp.model_used,
            "_retry_sleep_ms": resp.retry_sleep_ms,
            "_model_degraded": False,
            "ppr_iters": meta["ppr_iters"],
            "ppr_residual": meta["ppr_residual"]
        }

        if return_timing:
            return resp.text, context, timing
        return resp.text, context


def hipporag_inference_engine(query: str, query_id: str = "N/A", return_timing: bool = True) -> tuple:
    global _GLOBAL_HIPPORAG_ENGINE
    if "_GLOBAL_HIPPORAG_ENGINE" not in globals() or _GLOBAL_HIPPORAG_ENGINE is None:
        _GLOBAL_HIPPORAG_ENGINE = HippoRAGAdaptedEngine()
    return _GLOBAL_HIPPORAG_ENGINE.infer(query, query_id=query_id, return_timing=return_timing)
