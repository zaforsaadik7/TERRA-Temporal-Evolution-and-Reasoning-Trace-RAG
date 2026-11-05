"""
terra_retriever.py
------------------
Reviewed TERRA dual-directional EEG graph traversal for Arm T.
Enforces:
- Separation of enqueued vs. expanded nodes.
- Full multi-hop expansion without arbitrary 15-queue truncation (queue bounded by max_graph_nodes).
- Hub degree behavior matching ask_terra.py: hubs extract 75 incoming / 25 outgoing into context,
  with no deeper expansion through high-degree hubs.
- Normal-degree nodes expand deeper hops up to max_depth.
- Full date tuple parsing (year, month, day) for chronological recency with deterministic tie-breaking.
- Accurate character accounting bounded by max_structural_chars=35000 and max_graph_nodes=40.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from .common_serializer import EvidenceItem, format_evidence_item
except ImportError:
    from scripts.matched_baseline.common_serializer import EvidenceItem, format_evidence_item



def _extract_date_tuple(date_str: str) -> Tuple[int, int, int]:
    """
    Extract (year, month, day) tuple from date string for complete chronological ordering.
    Fallback to (0, 0, 0) if unparseable.
    """
    if not date_str:
        return (0, 0, 0)
    s = str(date_str).strip()
    # Check for YYYY-MM-DD
    m = re.search(r"\b(1[789]\d{2}|20\d{2})(?:-(\d{1,2}))?(?:-(\d{1,2}))?\b", s)
    if m:
        yr = int(m.group(1))
        mo = int(m.group(2)) if m.group(2) else 0
        day = int(m.group(3)) if m.group(3) else 0
        return (yr, mo, day)
    return (0, 0, 0)


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
        Sort nodes by (year, month, day) descending, then node_id ascending for deterministic tie-breaking.
        """
        def sort_key(nid: str):
            nd = self.nodes_data.get(nid, {})
            d_str = nd.get("decision_date", nd.get("date", ""))
            dt = _extract_date_tuple(d_str)
            return (-dt[0], -dt[1], -dt[2], str(nid))

        return sorted(node_ids, key=sort_key)

    def _create_evidence_item(self, nid: str) -> EvidenceItem:
        """Build strictly validated EvidenceItem representation of node."""
        nd = self.nodes_data.get(nid, {})
        title = str(nd.get("title", f"Case {nid}")).strip() or f"Case {nid}"
        date = str(nd.get("decision_date", nd.get("date", "Unknown Date"))).strip() or "Unknown Date"
        holding = str(nd.get("substantive_holding", nd.get("holding", ""))).strip()
        trace = str(nd.get("thinking_trace", "")).strip()
        snippet = str(nd.get("text", nd.get("snippet", "")))[:600].strip()
        rel = str(nd.get("relation_context", "")).strip() or None
        return EvidenceItem(
            case_id=str(nid).strip(),
            title=title,
            decision_date=date,
            holding=holding,
            thinking_trace=trace,
            snippet=snippet,
            relation_context=rel,
        )

    def _compute_node_chars(self, nid: str, index: int = 1) -> int:
        """Compute exact character count of formatted node evidence matching format_evidence_item."""
        item = self._create_evidence_item(nid)
        return len(format_evidence_item(item, index))

    def retrieve(
        self,
        seed_node_ids: List[str],
        top_n: Optional[int] = None,
        max_depth_override: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute multi-hop dual-directional traversal starting from seed nodes.
        Enforces strict depth boundary (distance <= max_depth), deterministic recency ordering,
        hub no-deeper-expansion logic, and pre-admission structural character bounds.
        """
        limit_nodes = top_n if top_n is not None else self.max_graph_nodes
        effective_max_depth = max_depth_override if max_depth_override is not None else self.max_depth
        if not seed_node_ids or limit_nodes <= 0 or effective_max_depth < 0:
            return []

        enqueued_nodes: Set[str] = set()
        expanded_nodes: Set[str] = set()
        ordered_visited: List[str] = []
        accumulated_chars = 0
        queue: List[Tuple[str, int]] = []

        # Initialize queue with valid seed nodes in seed order
        for seed in seed_node_ids:
            s_id = str(seed).strip()
            if s_id in self.nodes_data and s_id not in enqueued_nodes:
                enqueued_nodes.add(s_id)
                queue.append((s_id, 0))

        while queue:
            if len(ordered_visited) >= limit_nodes or accumulated_chars >= self.max_structural_chars:
                break

            current_id, depth = queue.pop(0)

            if current_id in expanded_nodes or depth > effective_max_depth:
                continue

            expanded_nodes.add(current_id)
            if current_id not in ordered_visited:
                cand_idx = len(ordered_visited) + 1
                n_chars = self._compute_node_chars(current_id, cand_idx)
                sep_chars = 7 if ordered_visited else 0
                if accumulated_chars + sep_chars + n_chars > self.max_structural_chars:
                    break
                ordered_visited.append(current_id)
                accumulated_chars += sep_chars + n_chars

            # If current node is already at effective_max_depth, its neighbors would exceed max_depth (depth + 1 > max_depth)
            if depth >= effective_max_depth:
                continue

            deg = self._node_degree(current_id)
            preds = [src for src, _ in self.incoming_adj.get(current_id, [])]
            succs = [dst for dst, _ in self.outgoing_adj.get(current_id, [])]

            if deg > self.hub_degree_cap:
                # High-degree hub node (ask_terra.py lines 575-648):
                # Dual-budget extraction engaged: 75 incoming / 25 outgoing into context,
                # but no deeper queue expansion through high-degree hubs.
                sorted_preds = self._sort_by_recency(preds)[: self.incoming_hub_cap]
                sorted_succs = self._sort_by_recency(succs)[: self.outgoing_hub_cap]

                for nbr in sorted_preds + sorted_succs:
                    if len(ordered_visited) >= limit_nodes or accumulated_chars >= self.max_structural_chars:
                        break
                    if nbr not in ordered_visited:
                        cand_idx = len(ordered_visited) + 1
                        nb_chars = self._compute_node_chars(nbr, cand_idx)
                        sep_chars = 7 if ordered_visited else 0
                        if accumulated_chars + sep_chars + nb_chars > self.max_structural_chars:
                            break
                        ordered_visited.append(nbr)
                        accumulated_chars += sep_chars + nb_chars
                # Hub nodes do not enqueue neighbors for deeper hops
                continue

            # Normal-degree node (ask_terra.py lines 650-690):
            # Expand successors and predecessors up to hub caps, and queue for deeper hops if depth + 1 <= effective_max_depth
            sorted_succs = self._sort_by_recency(succs)[: self.outgoing_hub_cap]
            sorted_preds = self._sort_by_recency(preds)[: self.incoming_hub_cap]

            for nbr in sorted_succs + sorted_preds:
                if len(ordered_visited) >= limit_nodes or accumulated_chars >= self.max_structural_chars:
                    break
                if nbr not in ordered_visited:
                    cand_idx = len(ordered_visited) + 1
                    nb_chars = self._compute_node_chars(nbr, cand_idx)
                    sep_chars = 7 if ordered_visited else 0
                    if accumulated_chars + sep_chars + nb_chars > self.max_structural_chars:
                        break
                    ordered_visited.append(nbr)
                    accumulated_chars += sep_chars + nb_chars

                if depth + 1 <= effective_max_depth and nbr not in enqueued_nodes and len(queue) < self.max_graph_nodes:
                    enqueued_nodes.add(nbr)
                    queue.append((nbr, depth + 1))

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
