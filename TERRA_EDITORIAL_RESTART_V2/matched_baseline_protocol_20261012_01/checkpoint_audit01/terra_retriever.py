"""
terra_retriever.py
------------------
Implements dense-seeded EEG graph traversal for Arm T.
Operates strictly query-seeded with zero access to benchmark metadata,
ground truth, or category labels.
"""

from typing import Dict, List, Optional, Set, Tuple


class TerraRetriever:
    """
    Retrieves evidence by expanding dense seed nodes along EEG graph relationships.
    Deterministic traversal and deterministic tie-breaking.
    """

    def __init__(
        self,
        graph_adj: Dict[str, List[Tuple[str, str]]],  # source -> [(target, relation_type)]
        max_hops: int = 2,
        max_nodes: int = 10,
    ):
        """
        graph_adj: Adjacency list mapping node_id to list of (neighbor_id, relation_type).
        """
        self.graph_adj = graph_adj
        self.max_hops = max_hops
        self.max_nodes = max_nodes

    def retrieve(
        self,
        seed_node_ids: List[str],
        top_n: Optional[int] = None,
    ) -> List[str]:
        """
        Traverse the graph starting from seed nodes up to max_hops.
        Returns ordered list of visited node IDs.
        Ties and visitation order are strictly deterministic.
        """
        limit = top_n if top_n is not None else self.max_nodes
        if not seed_node_ids or limit <= 0:
            return []

        visited: Set[str] = set()
        result: List[str] = []

        # Current frontier initialized with seeds
        frontier: List[str] = []
        for s in seed_node_ids:
            if s not in visited:
                visited.add(s)
                result.append(s)
                frontier.append(s)
                if len(result) >= limit:
                    return result

        # BFS expansion
        for _ in range(self.max_hops):
            next_frontier: List[str] = []
            for node in frontier:
                neighbors = self.graph_adj.get(node, [])
                # Deterministic traversal order: sort neighbors by node_id ascending
                sorted_neighbors = sorted(neighbors, key=lambda x: str(x[0]))
                for nbr_id, _ in sorted_neighbors:
                    if nbr_id not in visited:
                        visited.add(nbr_id)
                        result.append(nbr_id)
                        next_frontier.append(nbr_id)
                        if len(result) >= limit:
                            return result
            frontier = next_frontier
            if not frontier:
                break

        return result
