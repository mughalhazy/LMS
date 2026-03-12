from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Sequence, Set

from .models import (
    DependencyType,
    LearningPathEdge,
    LearningPathNode,
    LearningPathProgressionResult,
    NodeProgress,
)


class LearningPathProgressionValidator:
    """Validates learning path progression requirements and unlock state."""

    @staticmethod
    def _is_complete(status: str) -> bool:
        return status.lower() == "completed"

    @classmethod
    def _validate_acyclic(
        cls,
        nodes: Sequence[LearningPathNode],
        edges: Sequence[LearningPathEdge],
    ) -> List[str]:
        indegree: Dict[str, int] = {node.node_id: 0 for node in nodes}
        adjacency: Dict[str, List[str]] = defaultdict(list)
        for edge in edges:
            adjacency[edge.from_node_id].append(edge.to_node_id)
            indegree[edge.to_node_id] = indegree.get(edge.to_node_id, 0) + 1
            indegree.setdefault(edge.from_node_id, 0)

        queue = deque(node_id for node_id, degree in indegree.items() if degree == 0)
        visited = 0

        while queue:
            current = queue.popleft()
            visited += 1
            for nxt in adjacency.get(current, []):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        if visited != len(indegree):
            return ["path_cycle_detected"]
        return []

    @classmethod
    def validate_progression_requirements(
        cls,
        nodes: Sequence[LearningPathNode],
        edges: Sequence[LearningPathEdge],
        progress: Sequence[NodeProgress],
    ) -> LearningPathProgressionResult:
        violations = cls._validate_acyclic(nodes, edges)

        node_index: Dict[str, LearningPathNode] = {node.node_id: node for node in nodes}
        progress_map: Dict[str, NodeProgress] = {entry.node_id: entry for entry in progress}
        incoming: Dict[str, List[LearningPathEdge]] = defaultdict(list)

        for edge in edges:
            incoming[edge.to_node_id].append(edge)

        unlocked_nodes: Set[str] = set()
        locked_nodes: Set[str] = set()
        warnings: List[str] = []

        for node in nodes:
            prereqs = incoming.get(node.node_id, [])
            if not prereqs:
                unlocked_nodes.add(node.node_id)
                continue

            strict_block = False
            for edge in prereqs:
                upstream_progress = progress_map.get(edge.from_node_id)
                upstream_complete = upstream_progress is not None and cls._is_complete(upstream_progress.completion_status)

                if edge.dependency_type == DependencyType.STRICT:
                    if not upstream_complete:
                        strict_block = True
                        break

                    upstream_node = node_index.get(edge.from_node_id)
                    if upstream_node and upstream_node.minimum_score is not None:
                        if upstream_progress is None or upstream_progress.score is None:
                            strict_block = True
                            break
                        if upstream_progress.score < upstream_node.minimum_score:
                            strict_block = True
                            break
                else:
                    if not upstream_complete:
                        warnings.append(
                            f"advisory_dependency_unmet:{edge.from_node_id}->{node.node_id}"
                        )

            if strict_block:
                locked_nodes.add(node.node_id)
            else:
                unlocked_nodes.add(node.node_id)

        return LearningPathProgressionResult(
            unlocked_nodes=sorted(unlocked_nodes),
            locked_nodes=sorted(locked_nodes),
            advisory_warnings=sorted(set(warnings)),
            violations=violations,
        )
