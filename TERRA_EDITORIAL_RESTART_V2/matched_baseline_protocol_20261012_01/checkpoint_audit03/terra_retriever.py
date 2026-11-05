"""
terra_retriever.py
------------------
Reviewed TERRA dual-directional EEG graph traversal for Arm T.
Enforces:
- Separation of enqueued vs. expanded nodes (proper multi-hop expansion).
- Depth tracking up to max_depth (e.g., s -> a -> b with max_depth=2 visits all 3).
- Cycle safety (e.g., s -> a -> s handled cleanly).
- Fixed hub degree capping (HUB_DEGREE_CAP=50, INCOMING=75, OUTGOING=25).
- Recency sorting by decision year descending with secondary deterministic tie-breaking.
- Hard limits: max_graph_nodes=40, max_structural_chars=35000.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple


def _extract_year(date_str: str) -> int:
    """Extract 4-digit year from date string; fallback to 0 if unparseable."""
    if not date_str:
        return 0
    m = re.search(r"\b(1[789]\d{2}|20\d{2})\b", str(date_str))
    return int(m.group(1)) if m else 0


class TerraRetriever:
    """
    Reviewed TERRA dual-directional graph traversal matching ask_terra.py.
    """

    def __init__(
        self,
        nodes_data: Dict[str, Dict[str, Any]],
        edges_data: List[Dict[str, Any]],
        hub_degree_cap: int = 50,
        incoming_hub_cap: int = 75,
        outgoing_hub_cap: int = 25,
        max_graph_nodes: int = 40,
        max_structural_chars: int = 35000,
        max_depth: int = 2,
    ):
        self.nodes_data = nodes_data
        self.hub_degree_cap = hub_degree_cap
        self.incoming_hub_cap = incoming_hub_cap
        self.outgoing_hub_cap = outgoing_hub_cap
        self.max_graph_nodes = max_graph_nodes
        self.max_structural_chars = max_structural_chars
        self.max_depth = max_depth

        # Build adjacency structures (ignoring edges referencing non-existent nodes)
        self.outgoing_adj: Dict[str, List[Tuple[str, str]]] = {}  # src -> [(dst, rel)]
        self.incoming_adj: Dict[str, List[Tuple[str, str]]] = {}  # dst -> [(src, rel)]

        for e in edges_data:
            src = str(e.get("source", "")).strip()
            dst = str(e.get("target", "")).strip()
            rel = str(e.get("relation", "CITES")).strip()
            if src and dst and src in self.nodes_data and dst in self.nodes_data:
                self.outgoing_adj.setdefault(src, []).append((dst, rel))
                self.incoming_adj.setdefault(dst, []).append((src, rel))

    def _node_degree(self, node_id: str) -> int:
        out_deg = len(self.outgoing_adj.get(node_id, []))
        in_deg = len(self.incoming_adj.get(node_id, []))
        return out_deg + in_deg

    def _sort_by_recency(self, node_ids: List[str]) -> List[str]:
        """
        Sort nodes by decision year descending, then node_id ascending for deterministic tie-breaking.
        """
        def sort_key(nid: str):
            nd = self.nodes_data.get(nid, {})
            d_str = nd.get("decision_date", nd.get("date", ""))
            yr = _extract_year(d_str)
            return (-yr, str(nid))

        return sorted(node_ids, key=sort_key)

    def retrieve(
        self,
        seed_node_ids: List[str],
        top_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute multi-hop dual-directional traversal starting from seed nodes.
        Returns list of structured node dictionaries formatted for evidence packaging.
        """
        limit_nodes = top_n if top_n is not None else self.max_graph_nodes
        if not seed_node_ids or limit_nodes <= 0:
            return []

        enqueued_nodes: Set[str] = set()
        expanded_nodes: Set[str] = set()
        ordered_visited: List[str] = []
        accumulated_chars = 0
        queue: List[Tuple[str, int]] = []

        # Initialize queue with valid seed nodes
        for seed in seed_node_ids:
            s_id = str(seed).strip()
            if s_id in self.nodes_data and s_id not in enqueued_nodes:
                enqueued_nodes.add(s_id)
                queue.append((s_id, 0))

        while queue:
            if len(ordered_visited) >= limit_nodes or accumulated_chars >= self.max_structural_chars:
                break

            current_id, depth = queue.pop(0)

            # Skip if already expanded or exceeding max depth
            if current_id in expanded_nodes or depth > self.max_depth:
                continue

            expanded_nodes.add(current_id)
            if current_id not in ordered_visited:
                ordered_visited.append(current_id)
                c_data = self.nodes_data.get(current_id, {})
                holding = str(c_data.get("substantive_holding", c_data.get("holding", "")))
                snippet = str(c_data.get("text", c_data.get("snippet", "")))[:1200]
                accumulated_chars += len(holding) + len(snippet)

            # Stop expansion if at max_depth
            if depth >= self.max_depth:
                continue

            deg = self._node_degree(current_id)
            preds = [src for src, _ in self.incoming_adj.get(current_id, [])]
            succs = [dst for dst, _ in self.outgoing_adj.get(current_id, [])]

            if deg > self.hub_degree_cap:
                # High-degree hub node: engage dual-budget controls (fixed 75 incoming / 25 outgoing caps)
                sorted_preds = self._sort_by_recency(preds)[: self.incoming_hub_cap]
                sorted_succs = self._sort_by_recency(succs)[: self.outgoing_hub_cap]
            else:
                # Normal-degree node: expand successors and predecessors within hub caps
                sorted_preds = self._sort_by_recency(preds)[: self.incoming_hub_cap]
                sorted_succs = self._sort_by_recency(succs)[: self.outgoing_hub_cap]

            # Enqueue candidates for deeper expansion
            for nbr in sorted_preds + sorted_succs:
                if len(ordered_visited) >= limit_nodes or accumulated_chars >= self.max_structural_chars:
                    break
                if nbr not in enqueued_nodes:
                    enqueued_nodes.add(nbr)
                    if len(queue) < 15:
                        queue.append((nbr, depth + 1))
                    # Also include in visited order
                    if nbr not in ordered_visited:
                        ordered_visited.append(nbr)
                        nb_data = self.nodes_data.get(nbr, {})
                        holding = str(nb_data.get("substantive_holding", nb_data.get("holding", "")))[:600]
                        accumulated_chars += len(holding)

        # Build output dictionaries from shared node data
        results: List[Dict[str, Any]] = []
        for nid in ordered_visited[:limit_nodes]:
            nd = self.nodes_data.get(nid, {})
            results.append({
                "case_id": nid,
                "title": nd.get("title", f"Case {nid}"),
                "decision_date": nd.get("decision_date", nd.get("date", "Unknown Date")),
                "holding": nd.get("substantive_holding", nd.get("holding", "")),
                "thinking_trace": nd.get("thinking_trace", ""),
                "snippet": nd.get("text", nd.get("snippet", ""))[:600],
                "relation_context": nd.get("relation_context"),
            })

        return results
