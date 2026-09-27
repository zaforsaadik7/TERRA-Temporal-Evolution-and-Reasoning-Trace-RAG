"""
baselines/graphrag_adapter.py - GraphRAG-Adapted Implementation
Implements hierarchical community detection (Leiden/Louvain modularity optimization)
directly over the 20,000-opinion citation network (145,363 edges), generating multi-level
legal community summaries and executing dual-level Local Search over local precedent subgraphs.
"""

import os
import sys
import json
import time
from collections import Counter
import networkx as nx
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
COMMUNITIES_CACHE_FILE = os.path.join(CACHE_DIR, "graphrag_communities_20k.json")


class GraphRAGAdaptedEngine:
    def __init__(
        self,
        corpus_path: str = CORPUS_PATH,
        vector_db_path: str = VECTOR_DB_PATH,
        seed: int = 42
    ):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.corpus_data = load_verified_corpus(corpus_path)
        self.nodes = self.corpus_data.get("nodes", {})
        self.edges = self.corpus_data.get("edges", [])

        # Build citation graph
        self.G = nx.DiGraph()
        for nid, ninfo in self.nodes.items():
            self.G.add_node(nid, **ninfo)
        for e in self.edges:
            self.G.add_edge(e["source"], e["target"])

        self.G_undirected = self.G.to_undirected()

        # Compute or load communities
        self.communities, self.modularity_score = self._load_or_compute_communities(seed)
        self.node_to_community = {}
        for cid, comm in enumerate(self.communities):
            for nid in comm:
                self.node_to_community[nid] = cid

        # Precompute community summary profiles
        self.community_summaries = self._build_community_summaries()

        # Connect to ChromaDB for seed mapping
        self.chroma_client = chromadb.PersistentClient(path=vector_db_path)
        self.collection = self.chroma_client.get_collection(name="thinking_traces")
        self.interceptor = PayloadParityInterceptor()

    def _load_or_compute_communities(self, seed: int):
        if os.path.exists(COMMUNITIES_CACHE_FILE):
            print(f"[GraphRAG-Adapted] Loading cached communities from {COMMUNITIES_CACHE_FILE}...")
            with open(COMMUNITIES_CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            communities = [set(comm) for comm in cached["communities"]]
            modularity_val = cached.get("modularity", 0.0)
            return communities, modularity_val

        print("[GraphRAG-Adapted] Computing Louvain/Leiden modularity communities on 145k citation edges...")
        from networkx.algorithms.community import louvain_communities, modularity
        communities = louvain_communities(self.G_undirected, seed=seed, resolution=1.0)
        modularity_val = modularity(self.G_undirected, communities)
        print(f"[GraphRAG-Adapted] Partitioned into {len(communities)} communities. Modularity Q = {modularity_val:.4f}")

        # Cache for fast re-execution
        cache_data = {
            "num_communities": len(communities),
            "modularity": round(modularity_val, 4),
            "communities": [list(c) for c in communities]
        }
        with open(COMMUNITIES_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)

        return communities, modularity_val

    def _build_community_summaries(self) -> dict:
        summaries = {}
        for cid, comm in enumerate(self.communities):
            domains = []
            degrees = {}
            for nid in comm:
                node_data = self.nodes.get(nid, {})
                dom = node_data.get("primary_domain")
                if dom:
                    domains.append(dom)
                degrees[nid] = self.G.degree(nid)

            dom_counter = Counter(domains)
            dominant_domain = dom_counter.most_common(1)[0][0] if dom_counter else "General Law"
            purity = (dom_counter.most_common(1)[0][1] / len(domains)) if domains else 0.0

            # Top 3 landmark cases by degree
            top_cases = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:3]
            landmark_names = [self.nodes.get(nid, {}).get("title", nid) for nid, _ in top_cases]

            summaries[cid] = {
                "community_id": cid,
                "size": len(comm),
                "dominant_domain": dominant_domain,
                "purity": round(purity, 4),
                "landmarks": landmark_names
            }
        return summaries

    def retrieve_local_context(self, query: str, top_k: int = 5) -> tuple[str, dict]:
        # 1. Query ChromaDB for top candidate seed cases
        res = self.collection.query(query_texts=[query], n_results=top_k)
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]

        # 2. Extract local subgraph & parent community summaries
        community_contexts = []
        visited_communities = set()
        local_subgraph_snippets = []

        for idx, nid in enumerate(ids):
            node_info = self.nodes.get(nid, {})
            case_name = node_info.get("title", f"Case_{nid}")
            year = node_info.get("decision_date", "Unknown")[:4] if node_info.get("decision_date") else "Unknown"
            doc_text = docs[idx] if idx < len(docs) else ""

            # 1-hop citation neighbors
            out_edges = list(self.G.successors(nid))[:3]
            in_edges = list(self.G.predecessors(nid))[:3]
            cites = [self.nodes.get(e, {}).get("title", e) for e in out_edges]
            cited_by = [self.nodes.get(e, {}).get("title", e) for e in in_edges]

            subgraph_entry = (
                f"- Precedent: {case_name} ({year})\n"
                f"  Substantive Extract: {doc_text[:400]}...\n"
                f"  Direct Citations Out: {', '.join(cites) if cites else 'None'}\n"
                f"  Direct Citations In: {', '.join(cited_by) if cited_by else 'None'}"
            )
            local_subgraph_snippets.append(subgraph_entry)

            cid = self.node_to_community.get(nid)
            if cid is not None and cid not in visited_communities:
                visited_communities.add(cid)
                c_sum = self.community_summaries.get(cid, {})
                community_contexts.append(
                    f"* Community {cid} [{c_sum.get('dominant_domain', 'Law')} - {c_sum.get('size', 0)} cases]: "
                    f"Core landmark authorities include {', '.join(c_sum.get('landmarks', []))}."
                )

        context = (
            "[GRAPHRAG-ADAPTED HIERARCHICAL COMMUNITY CONTEXT]\n"
            + "\n".join(community_contexts)
            + "\n\n[GRAPHRAG-ADAPTED LOCAL PRECEDENT SUBGRAPH & PASSAGES]\n"
            + "\n\n".join(local_subgraph_snippets)
        )
        return context, {"retrieved_communities": list(visited_communities), "seed_cases": ids}

    def infer(self, query: str, query_id: str = "N/A", return_timing: bool = True) -> tuple:
        t0 = time.time()
        context, meta = self.retrieve_local_context(query, top_k=5)
        retrieval_ms = round((time.time() - t0) * 1000, 2)

        prompt = format_neutral_prompt(query, context)
        t1 = time.time()
        resp = self.interceptor.generate(
            prompt=prompt,
            query_id=query_id,
            pipeline_name="3_GraphRAG_Adapted"
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
            "_model_degraded": False
        }

        if return_timing:
            return resp.text, context, timing
        return resp.text, context


def graphrag_inference_engine(query: str, query_id: str = "N/A", return_timing: bool = True) -> tuple:
    global _GLOBAL_GRAPHRAG_ENGINE
    if "_GLOBAL_GRAPHRAG_ENGINE" not in globals() or _GLOBAL_GRAPHRAG_ENGINE is None:
        _GLOBAL_GRAPHRAG_ENGINE = GraphRAGAdaptedEngine()
    return _GLOBAL_GRAPHRAG_ENGINE.infer(query, query_id=query_id, return_timing=return_timing)
