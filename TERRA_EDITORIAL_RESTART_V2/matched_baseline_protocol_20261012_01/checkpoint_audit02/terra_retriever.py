"""
terra_retriever.py
------------------
Implements reviewed TERRA dual-directional EEG graph traversal for Arm T.
Incorporates:
- Dual-budget hub degree capping (HUB_DEGREE_CAP=50, INCOMING=75, OUTGOING=25)
- Directional predecessor (incoming citing/overruling) and successor (outgoing precedent) expansion
- Recency sorting by decision year descending with deterministic secondary tie-breaking
- Hard bounds: MAX_GRAPH_NODES=40, MAX_STRUCTURAL_CHARS=35000, max_depth=2
- Strict query-only seeded operation with zero benchmark metadata access
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

        # Build adjacency structures
        self.outgoing_adj: Dict[str, List[Tuple[str, str]]] = {}  # src -> [(dst, rel)]
        self.incoming_adj: Dict[str, List[Tuple[str, str]]] = {}  # dst -> [(src, rel)]

        for e in edges_data:
            src = str(e.get("source", ""))
            dst = str(e.get("target", ""))
            rel = str(e.get("relation", "CITES"))
            if src and dst:
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
        Execute reviewed TERRA dual-directional traversal starting from seed nodes.
        Returns list of structured node dictionaries formatted for evidence packaging.
        """
        limit_nodes = top_n if top_n is not None else self.max_graph_nodes
        if not seed_node_ids or limit_nodes <= 0:
            return []

        visited_nodes: Set[str] = set()
        ordered_visited: List[str] = []
        accumulated_chars = 0
        queue: List[Tuple[str, int]] = []

        for seed in seed_node_ids:
            if seed not in visited_nodes:
                queue.append((seed, 0))

        while queue:
            if len(visited_nodes) >= limit_nodes or accumulated_chars >= self.max_structural_chars:
                break

            current_id, depth = queue.pop(0)
            if current_id in visited_nodes or depth > self.max_depth:
                continue

            visited_nodes.add(current_id)
            ordered_visited.append(current_id)

            c_data = self.nodes_data.get(current_id, {})
            holding = str(c_data.get("substantive_holding", c_data.get("holding", "")))
            snippet = str(c_data.get("text", c_data.get("snippet", "")))[:1200]
            accumulated_chars += len(holding) + len(snippet)

            deg = self._node_degree(current_id)
            preds = [src for src, _ in self.incoming_adj.get(current_id, [])]
            succs = [dst for dst, _ in self.outgoing_adj.get(current_id, [])]

            if deg > self.hub_degree_cap:
                # High-degree hub node: dual-budget controls (apportioned by 75:25 ratio when limit_nodes < 100)
                cap_p = min(self.incoming_hub_cap, max(1, int(limit_nodes * 0.75)))
                cap_s = min(self.outgoing_hub_cap, max(1, int(limit_nodes * 0.25)))
                sorted_preds = self._sort_by_recency(preds)[:cap_p]
                sorted_succs = self._sort_by_recency(succs)[:cap_s]

                for p in sorted_preds:
                    if len(ordered_visited) >= limit_nodes or accumulated_chars >= self.max_structural_chars:
                        break
                    if p not in visited_nodes:
                        visited_nodes.add(p)
                        ordered_visited.append(p)
                        p_data = self.nodes_data.get(p, {})
                        accumulated_chars += len(str(p_data.get("substantive_holding", ""))[:250])

                for s in sorted_succs:
                    if len(ordered_visited) >= limit_nodes or accumulated_chars >= self.max_structural_chars:
                        break
                    if s not in visited_nodes:
                        visited_nodes.add(s)
                        ordered_visited.append(s)
                        s_data = self.nodes_data.get(s, {})
                        accumulated_chars += len(str(s_data.get("substantive_holding", ""))[:250])
            else:
                # Normal-degree node: expand successors and predecessors
                sorted_succs = self._sort_by_recency(succs)[: self.outgoing_hub_cap]
                sorted_preds = self._sort_by_recency(preds)[: self.incoming_hub_cap]

                for s in sorted_succs:
                    if len(ordered_visited) >= limit_nodes or accumulated_chars >= self.max_structural_chars:
                        break
                    if s not in visited_nodes:
                        visited_nodes.add(s)
                        ordered_visited.append(s)
                        s_data = self.nodes_data.get(s, {})
                        accumulated_chars += len(str(s_data.get("substantive_holding", ""))[:250])
                        if depth + 1 <= self.max_depth and len(queue) < 15:
                            queue.append((s, depth + 1))

                for p in sorted_preds:
                    if len(ordered_visited) >= limit_nodes or accumulated_chars >= self.max_structural_chars:
                        break
                    if p not in visited_nodes:
                        visited_nodes.add(p)
                        ordered_visited.append(p)
                        p_data = self.nodes_data.get(p, {})
                        accumulated_chars += len(str(p_data.get("substantive_holding", ""))[:250])
                        if depth + 1 <= self.max_depth and len(queue) < 15:
                            queue.append((p, depth + 1))

        # Format output items for serializer
        results: List[Dict[str, Any]] = []
        for nid in ordered_visited:
            nd = self.nodes_data.get(nid, {})
            # Detect relation context if present relative to seeds
            rel_context = None
            for s in seed_node_ids:
                # Check if nid overrules s or vice versa
                for dst, rel in self.outgoing_adj.get(nid, []):
                    if dst == s and rel in ("OVERRULES", "REPUDIATES"):
                        rel_context = f"[OVERRULES / REPUDIATES] seed case {s}"
                for dst, rel in self.outgoing_adj.get(s, []):
                    if dst == nid and rel in ("OVERRULES", "REPUDIATES"):
                        rel_context = f"Seed case {s} [OVERRULES / REPUDIATES] this precedent"

            results.append({
                "case_id": nid,
                "title": nd.get("title", f"Case {nid}"),
                "decision_date": nd.get("decision_date", nd.get("date", "Unknown Date")),
                "holding": nd.get("substantive_holding", nd.get("holding", "")),
                "thinking_trace": nd.get("thinking_trace", ""),
                "snippet": nd.get("text", nd.get("snippet", ""))[:600],
                "relation_context": rel_context,
            })

        return results
