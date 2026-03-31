from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class KnowledgeNodeType(str, Enum):
    USER = "user"
    SKILL = "skill"
    COURSE = "course"
    LESSON = "lesson"


class KnowledgeEdgeType(str, Enum):
    ENROLLED_IN = "enrolled_in"
    LEARNED = "learned"
    REQUIRES = "requires"
    IMPROVES = "improves"


@dataclass(frozen=True)
class KnowledgeNode:
    node_id: str
    node_type: KnowledgeNodeType
    tenant_id: str
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeEdge:
    source_id: str
    target_id: str
    edge_type: KnowledgeEdgeType
    tenant_id: str
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeGraph:
    """Tenant-aware graph with user/skill/course/lesson nodes and required edge semantics."""

    def __init__(self) -> None:
        self._nodes: dict[tuple[str, str], KnowledgeNode] = {}
        self._edges: dict[tuple[str, str, str, str], KnowledgeEdge] = {}

    def upsert_node(self, node: KnowledgeNode) -> None:
        self._nodes[(node.tenant_id, node.node_id)] = node

    def upsert_edge(self, edge: KnowledgeEdge) -> None:
        key = (edge.tenant_id, edge.source_id, edge.target_id, edge.edge_type.value)
        existing = self._edges.get(key)
        if existing:
            existing.weight = edge.weight
            existing.metadata = {**existing.metadata, **edge.metadata}
            existing.updated_at = datetime.now(timezone.utc)
            return
        self._edges[key] = edge

    def get_edges(self, tenant_id: str, edge_type: KnowledgeEdgeType | None = None) -> list[KnowledgeEdge]:
        edges = [edge for edge in self._edges.values() if edge.tenant_id == tenant_id]
        if edge_type:
            return [edge for edge in edges if edge.edge_type == edge_type]
        return edges

    def get_nodes(self, tenant_id: str, node_type: KnowledgeNodeType | None = None) -> list[KnowledgeNode]:
        nodes = [node for (node_tenant, _), node in self._nodes.items() if node_tenant == tenant_id]
        if node_type:
            return [node for node in nodes if node.node_type == node_type]
        return nodes

    def as_dict(self, tenant_id: str) -> dict[str, Any]:
        return {
            "nodes": [asdict(node) for node in self.get_nodes(tenant_id)],
            "edges": [
                {
                    **asdict(edge),
                    "edge_type": edge.edge_type.value,
                    "updated_at": edge.updated_at.isoformat(),
                }
                for edge in self.get_edges(tenant_id)
            ],
        }
