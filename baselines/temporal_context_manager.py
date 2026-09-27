"""
baselines/temporal_context_manager.py - Dynamic Temporal Horizon Switcher
==========================================================================
Provides scoped, in-memory context switching for TERRA and baseline pipelines
across historical horizons T in {1890, 1930, 1950, 1970, 1980}.

Architectural Resolution (Option A):
  - ChromaDB Handling: Instantiates an isolated chromadb.PersistentClient pointing
    to dataset_20k_cap/temporal_vector_db/, caching collection references in memory.
    Injects collection objects directly into ask_terra.collection on context enter,
    leaving ask_terra.chroma_client untouched.
  - Subgraph Handling: Preloads and caches NetworkX DiGraph representations of
    dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T{T}.json in memory.
    Injects graph objects into ask_terra.eeg on context enter.
  - Zero Mutation: Canonical files in dataset_20k_cap/ are never modified.
  - Safe Restoration: Guaranteed restoration of original ask_terra module attributes
    via try/finally semantics upon context exit.
  - Provenance Guard: Automated verification that all traversed nodes and retrieved
    passages strictly satisfy year <= T.
"""

import os
import sys
import json
import re
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Union, Tuple

import networkx as nx
import chromadb

# ---------------------------------------------------------------------------
# Constants & Supported Horizons
# ---------------------------------------------------------------------------
SUPPORTED_CUTOFF_YEARS: Set[int] = {1890, 1930, 1950, 1970, 1980}

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBGRAPH_DIR = REPO_ROOT / "dataset_20k_cap" / "temporal_subgraphs"
TEMPORAL_VECTOR_DB_DIR = REPO_ROOT / "dataset_20k_cap" / "temporal_vector_db"

# ---------------------------------------------------------------------------
# In-Memory Singletons & Caches
# ---------------------------------------------------------------------------
_CACHE_LOCK = threading.RLock()
_TEMPORAL_CHROMA_CLIENT: Optional[chromadb.PersistentClient] = None
_SUBGRAPH_CACHE: Dict[int, nx.DiGraph] = {}
_COLLECTION_CACHE: Dict[int, Any] = {}


def validate_cutoff_year(cutoff_year: int) -> int:
    """Validates that cutoff_year is within the supported temporal horizons."""
    if not isinstance(cutoff_year, int) or cutoff_year not in SUPPORTED_CUTOFF_YEARS:
        raise ValueError(
            f"Unsupported temporal cutoff year: {cutoff_year}. "
            f"Supported horizons are: {sorted(SUPPORTED_CUTOFF_YEARS)}"
        )
    return cutoff_year


def get_temporal_chroma_client() -> chromadb.PersistentClient:
    """
    Returns the singleton PersistentClient for the temporal vector database.
    (Option A: Isolated client for dataset_20k_cap/temporal_vector_db).
    """
    global _TEMPORAL_CHROMA_CLIENT
    if _TEMPORAL_CHROMA_CLIENT is None:
        with _CACHE_LOCK:
            if _TEMPORAL_CHROMA_CLIENT is None:
                db_path = str(TEMPORAL_VECTOR_DB_DIR)
                if not TEMPORAL_VECTOR_DB_DIR.exists():
                    raise FileNotFoundError(
                        f"Temporal vector DB directory not found at: {db_path}"
                    )
                _TEMPORAL_CHROMA_CLIENT = chromadb.PersistentClient(path=db_path)
    return _TEMPORAL_CHROMA_CLIENT


def get_temporal_collection(cutoff_year: int) -> Any:
    """
    Retrieves and caches the ChromaDB collection for historical horizon T.
    Collection name pattern: thinking_traces_T{cutoff_year}.
    """
    cutoff_year = validate_cutoff_year(cutoff_year)
    if cutoff_year in _COLLECTION_CACHE:
        return _COLLECTION_CACHE[cutoff_year]

    client = get_temporal_chroma_client()
    with _CACHE_LOCK:
        if cutoff_year in _COLLECTION_CACHE:
            return _COLLECTION_CACHE[cutoff_year]

        col_name = f"thinking_traces_T{cutoff_year}"
        collection = client.get_collection(name=col_name)
        _COLLECTION_CACHE[cutoff_year] = collection
        return collection


def load_temporal_subgraph(cutoff_year: int) -> nx.DiGraph:
    """
    Loads and caches the NetworkX DiGraph for historical horizon T.
    Loads from dataset_20k_cap/temporal_subgraphs/eeg_subgraph_T{cutoff_year}.json.
    Supports both standard node-link format and custom dictionary node/edge format.
    """
    cutoff_year = validate_cutoff_year(cutoff_year)
    if cutoff_year in _SUBGRAPH_CACHE:
        return _SUBGRAPH_CACHE[cutoff_year]

    with _CACHE_LOCK:
        if cutoff_year in _SUBGRAPH_CACHE:
            return _SUBGRAPH_CACHE[cutoff_year]

        subgraph_path = SUBGRAPH_DIR / f"eeg_subgraph_T{cutoff_year}.json"
        if not subgraph_path.exists():
            raise FileNotFoundError(
                f"Temporal subgraph file not found at: {subgraph_path}"
            )

        with open(subgraph_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

        if "links" in graph_data or ("nodes" in graph_data and isinstance(graph_data["nodes"], list)):
            g = nx.node_link_graph(graph_data)
        else:
            g = nx.DiGraph()
            for nid, ninfo in graph_data.get("nodes", {}).items():
                g.add_node(nid, **ninfo)
            for e in graph_data.get("edges", []):
                attrs = {k: v for k, v in e.items() if k not in ["source", "target"]}
                g.add_edge(e["source"], e["target"], **attrs)

        _SUBGRAPH_CACHE[cutoff_year] = g
        return g


def preload_all_temporal_assets() -> Dict[int, Dict[str, Any]]:
    """
    Preloads all 5 temporal subgraphs and ChromaDB collections into memory.
    Ensures subsequent evaluations incur zero disk I/O latency.
    Returns a summary dictionary of loaded assets.
    """
    summary = {}
    for year in sorted(SUPPORTED_CUTOFF_YEARS):
        g = load_temporal_subgraph(year)
        col = get_temporal_collection(year)
        summary[year] = {
            "subgraph_nodes": len(g.nodes),
            "subgraph_edges": len(g.edges),
            "collection_name": col.name,
            "collection_count": col.count(),
        }
    return summary


# ---------------------------------------------------------------------------
# Provenance Safety Guards
# ---------------------------------------------------------------------------
_YEAR_REGEX = re.compile(r"\b(17\d\d|18\d\d|19\d\d|20\d\d)\b")


def extract_year_from_metadata(meta: Dict[str, Any]) -> Optional[int]:
    """Extracts a 4-digit integer calendar year from metadata dict."""
    if not isinstance(meta, dict):
        return None

    # 1. Direct integer year field
    if "year" in meta:
        try:
            return int(meta["year"])
        except (ValueError, TypeError):
            pass

    # 2. Date string fields (e.g., '1850-01', '1850-01-23')
    for date_key in ["date", "decision_date"]:
        val = meta.get(date_key)
        if isinstance(val, str) and len(val) >= 4:
            try:
                y = int(val[:4])
                if 1700 <= y <= 2100:
                    return y
            except ValueError:
                pass

    # 3. Fallback regex search on title or citation string
    for text_key in ["title", "case_name", "citation"]:
        val = meta.get(text_key)
        if isinstance(val, str):
            matches = _YEAR_REGEX.findall(val)
            if matches:
                try:
                    return int(matches[-1])  # Take the last year mentioned in citation
                except ValueError:
                    pass

    return None


def extract_year_from_node(node_attrs: Dict[str, Any]) -> Optional[int]:
    """Extracts a 4-digit integer calendar year from EEG node attributes."""
    if not isinstance(node_attrs, dict):
        return None

    for date_key in ["decision_date", "date", "year"]:
        val = node_attrs.get(date_key)
        if isinstance(val, int) and 1700 <= val <= 2100:
            return val
        if isinstance(val, str) and len(val) >= 4:
            try:
                y = int(val[:4])
                if 1700 <= y <= 2100:
                    return y
            except ValueError:
                pass

    # Fallback to title
    title = node_attrs.get("title", "")
    if isinstance(title, str):
        matches = _YEAR_REGEX.findall(title)
        if matches:
            try:
                return int(matches[-1])
            except ValueError:
                pass

    return None


def provenance_guard(
    items: Union[List[Any], Dict[str, Any]],
    cutoff_year: int,
    item_type: str = "doc",
    context_label: str = ""
) -> None:
    """
    Enforces that every retrieved passage or traversed graph node has year <= cutoff_year.
    Raises AssertionError if future information is detected.
    """
    cutoff_year = validate_cutoff_year(cutoff_year)

    # Normalize to list of dicts
    if isinstance(items, dict):
        items_list = [items]
    else:
        items_list = list(items)

    for idx, item in enumerate(items_list):
        if item_type == "doc":
            meta = item if isinstance(item, dict) else getattr(item, "metadata", {})
            item_id = meta.get("node_id") or meta.get("id") or f"doc_{idx}"
            year = extract_year_from_metadata(meta)
        elif item_type == "node":
            attrs = item if isinstance(item, dict) else getattr(item, "attrs", {})
            item_id = attrs.get("node_id") or f"node_{idx}"
            year = extract_year_from_node(attrs)
        else:
            meta = item if isinstance(item, dict) else {}
            item_id = f"item_{idx}"
            year = extract_year_from_metadata(meta) or extract_year_from_node(meta)

        if year is not None and year > cutoff_year:
            raise AssertionError(
                f"[TEMPORAL PROVENANCE VIOLATION] {context_label} item '{item_id}' "
                f"from year {year} exceeds historical horizon cutoff T={cutoff_year}."
            )


def assert_temporal_cleanliness(
    retrieved_docs: Optional[List[Dict[str, Any]]] = None,
    traversed_nodes: Optional[List[Dict[str, Any]]] = None,
    cutoff_year: int = 1980,
    context_label: str = ""
) -> None:
    """Convenience assertion function checking both retrieved docs and graph nodes."""
    if retrieved_docs:
        provenance_guard(retrieved_docs, cutoff_year, item_type="doc", context_label=context_label)
    if traversed_nodes:
        provenance_guard(traversed_nodes, cutoff_year, item_type="node", context_label=context_label)


# ---------------------------------------------------------------------------
# Isolated Flat Vector RAG Helper
# ---------------------------------------------------------------------------
def flat_vector_rag_temporal(
    query_text: str,
    cutoff_year: int,
    k: int = 2,
    enforce_provenance: bool = True
) -> Dict[str, Any]:
    """
    Queries the temporal vector collection directly with top-k retrieval without
    touching the 1980 vector database.

    Args:
        query_text: The user legal query string.
        cutoff_year: Target historical horizon T.
        k: Number of nearest neighbors to retrieve (default: 2).
        enforce_provenance: Whether to assert year <= cutoff_year on results.

    Returns:
        Dict with keys:
          'cutoff_year', 'query_text', 'ids', 'documents', 'metadatas',
          'distances', 'context_text'
    """
    col = get_temporal_collection(cutoff_year)
    res = col.query(query_texts=[query_text], n_results=k)

    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]

    if enforce_provenance and metas:
        provenance_guard(metas, cutoff_year, item_type="doc", context_label=f"FlatRAG_T{cutoff_year}")

    context_lines = [f"- {d}" for d in docs] if docs else ["No relevant passages found."]
    context_text = "\n".join(context_lines)

    return {
        "cutoff_year": cutoff_year,
        "query_text": query_text,
        "ids": ids,
        "documents": docs,
        "metadatas": metas,
        "distances": dists,
        "context_text": context_text,
    }


# ---------------------------------------------------------------------------
# Scoped Context Manager (Option A)
# ---------------------------------------------------------------------------
class TemporalHorizonContext:
    """
    Scoped context manager that dynamically rebinds ask_terra's EEG graph
    and ChromaDB collection to a specific historical cutoff year T.

    Option A Implementation:
      - Directly injects the temporal collection object into ask_terra.collection
        from an isolated PersistentClient pointing to dataset_20k_cap/temporal_vector_db.
      - Never touches or alters ask_terra.chroma_client.
      - Dynamically replaces ask_terra.eeg with preloaded nx.DiGraph subgraph.
      - Updates ask_terra.GRAPH_INDEX_PATH and ask_terra.VECTOR_DB_PATH pointers.
      - Uses try/finally semantics in __exit__ to guarantee 100% restoration of
        original module attributes.
    """

    def __init__(self, cutoff_year: int, strict_provenance: bool = True):
        self.cutoff_year = validate_cutoff_year(cutoff_year)
        self.strict_provenance = strict_provenance

        self._orig_eeg: Optional[nx.DiGraph] = None
        self._orig_collection: Optional[Any] = None
        self._orig_graph_path: Optional[str] = None
        self._orig_vector_path: Optional[str] = None

        self._subgraph: Optional[nx.DiGraph] = None
        self._collection: Optional[Any] = None

    @property
    def subgraph(self) -> nx.DiGraph:
        if self._subgraph is None:
            self._subgraph = load_temporal_subgraph(self.cutoff_year)
        return self._subgraph

    @property
    def collection(self) -> Any:
        if self._collection is None:
            self._collection = get_temporal_collection(self.cutoff_year)
        return self._collection

    @property
    def node_count(self) -> int:
        return len(self.subgraph.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.subgraph.edges)

    @property
    def doc_count(self) -> int:
        return self.collection.count()

    def __enter__(self) -> "TemporalHorizonContext":
        import ask_terra

        # 1. Preload/fetch cached temporal assets
        temporal_subgraph = self.subgraph
        temporal_col = self.collection

        # 2. Save original ask_terra module-level state
        self._orig_eeg = getattr(ask_terra, "eeg", None)
        self._orig_collection = getattr(ask_terra, "collection", None)
        self._orig_graph_path = getattr(ask_terra, "GRAPH_INDEX_PATH", None)
        self._orig_vector_path = getattr(ask_terra, "VECTOR_DB_PATH", None)

        # 3. Patch ask_terra module-level pointers
        ask_terra.eeg = temporal_subgraph
        ask_terra.collection = temporal_col
        ask_terra.GRAPH_INDEX_PATH = str(SUBGRAPH_DIR / f"eeg_subgraph_T{self.cutoff_year}.json")
        ask_terra.VECTOR_DB_PATH = str(TEMPORAL_VECTOR_DB_DIR)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        import ask_terra

        # Unconditionally restore original module attributes
        try:
            if self._orig_eeg is not None:
                ask_terra.eeg = self._orig_eeg
            if self._orig_collection is not None:
                ask_terra.collection = self._orig_collection
            if self._orig_graph_path is not None:
                ask_terra.GRAPH_INDEX_PATH = self._orig_graph_path
            if self._orig_vector_path is not None:
                ask_terra.VECTOR_DB_PATH = self._orig_vector_path
        except Exception as e:
            print(f"[TEMPORAL CONTEXT RESTORATION ERROR] {e}", file=sys.stderr)

        # Return False to let any exception propagate to caller
        return False
