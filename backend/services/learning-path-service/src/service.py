from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from .models import (
    CompletionRules,
    LearningPath,
    LearningPathProgress,
    NodeProgress,
    PathEdge,
    PathNode,
    utc_now,
)


class LearningPathServiceError(Exception):
    pass


class ValidationError(LearningPathServiceError):
    pass


class NotFoundError(LearningPathServiceError):
    pass


class CourseCatalog:
    """Simple interface for cross-service publishability checks."""

    def is_reference_active(self, ref_id: str) -> bool:
        raise NotImplementedError


class InMemoryCourseCatalog(CourseCatalog):
    def __init__(self, active_refs: Optional[Iterable[str]] = None) -> None:
        self.active_refs = set(active_refs or [])

    def is_reference_active(self, ref_id: str) -> bool:
        return ref_id in self.active_refs


class LearningPathService:
    def __init__(self, course_catalog: Optional[CourseCatalog] = None) -> None:
        self._paths: Dict[str, LearningPath] = {}
        self._nodes: Dict[str, List[PathNode]] = defaultdict(list)
        self._edges: Dict[str, List[PathEdge]] = defaultdict(list)
        self._audit_log: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        self._course_catalog = course_catalog or InMemoryCourseCatalog()

    def create_learning_path(
        self,
        *,
        tenant_id: str,
        title: str,
        owner_id: str,
        description: Optional[str] = None,
        audience: Optional[Dict[str, str]] = None,
        completion_rules: Optional[CompletionRules] = None,
        actor_id: Optional[str] = None,
    ) -> LearningPath:
        if not tenant_id or not title or not owner_id:
            raise ValidationError("tenant_id, title, and owner_id are required")

        rules = completion_rules or CompletionRules()
        self._validate_completion_rules(rules)

        path = LearningPath(
            tenant_id=tenant_id,
            title=title,
            owner_id=owner_id,
            description=description,
            audience=audience or {},
            completion_rules=rules,
        )
        self._paths[path.path_id] = path
        self._record_audit(path, actor_id or owner_id, "learning.path.created", "initial draft")
        return path

    def configure_completion_rules(
        self,
        *,
        tenant_id: str,
        path_id: str,
        rules: CompletionRules,
        actor_id: str,
        change_reason: str,
    ) -> LearningPath:
        path = self._get_tenant_path(tenant_id, path_id)
        self._validate_completion_rules(rules)
        path.completion_rules = rules
        path.updated_at = utc_now()
        self._record_audit(path, actor_id, "learning.path.completion_rules.updated", change_reason)
        return path

    def replace_nodes(self, *, tenant_id: str, path_id: str, nodes: List[PathNode], actor_id: str) -> List[PathNode]:
        path = self._get_tenant_path(tenant_id, path_id)
        if path.status != "draft":
            raise ValidationError("nodes can only be edited on draft paths")

        node_ids = {node.node_id for node in nodes}
        if len(node_ids) != len(nodes):
            raise ValidationError("duplicate node_id in payload")

        for node in nodes:
            if node.path_id != path_id:
                raise ValidationError("all nodes must belong to target path")

        self._nodes[path_id] = list(nodes)
        path.updated_at = utc_now()
        self._record_audit(path, actor_id, "learning.path.nodes.replaced", "sequencing update")
        return self._nodes[path_id]

    def replace_edges(self, *, tenant_id: str, path_id: str, edges: List[PathEdge], actor_id: str) -> List[PathEdge]:
        path = self._get_tenant_path(tenant_id, path_id)
        if path.status != "draft":
            raise ValidationError("edges can only be edited on draft paths")

        nodes_by_id = {node.node_id: node for node in self._nodes[path_id]}
        for edge in edges:
            if edge.path_id != path_id:
                raise ValidationError("all edges must belong to target path")
            if edge.from_node_id not in nodes_by_id or edge.to_node_id not in nodes_by_id:
                raise ValidationError("edge references unknown node")
            if edge.from_node_id == edge.to_node_id:
                raise ValidationError("self-loop edges are not allowed")

        self._validate_acyclic(nodes_by_id.keys(), edges)
        self._validate_required_node_upstream(nodes_by_id, edges)
        self._validate_explicit_merge_points(edges)

        self._edges[path_id] = list(edges)
        path.updated_at = utc_now()
        self._record_audit(path, actor_id, "learning.path.edges.replaced", "sequencing update")
        return self._edges[path_id]

    def publish_learning_path(self, *, tenant_id: str, path_id: str, actor_id: str, change_reason: str) -> LearningPath:
        path = self._get_tenant_path(tenant_id, path_id)
        nodes = self._nodes[path_id]
        edges = self._edges[path_id]
        if path.status == "archived":
            raise ValidationError("archived paths cannot be published")

        if not any(node.is_required for node in nodes):
            raise ValidationError("publish requires at least one required node")

        inactive_refs = [node.ref_id for node in nodes if not self._course_catalog.is_reference_active(node.ref_id)]
        if inactive_refs:
            raise ValidationError(f"non-publishable references found: {sorted(inactive_refs)}")

        self._validate_completion_rules(path.completion_rules)
        self._validate_acyclic((node.node_id for node in nodes), edges)

        path.status = "published"
        path.version += 1
        path.published_at = utc_now()
        path.published_by = actor_id
        path.updated_at = utc_now()
        self._record_audit(path, actor_id, "learning.path.published", change_reason)
        return path

    def evaluate_completion(
        self,
        *,
        tenant_id: str,
        path_id: str,
        progress_by_node_id: Dict[str, NodeProgress],
        completed_at: Optional[datetime] = None,
    ) -> LearningPathProgress:
        path = self._get_tenant_path(tenant_id, path_id)
        nodes = self._nodes[path_id]
        rules = path.completion_rules
        completed_at = completed_at or utc_now()

        required_nodes = [n for n in nodes if n.is_required]
        completed_required = [n for n in required_nodes if self._is_node_complete(n, progress_by_node_id.get(n.node_id))]

        elective_nodes = [n for n in nodes if not n.is_required]
        completed_electives = [n for n in elective_nodes if self._is_node_complete(n, progress_by_node_id.get(n.node_id))]

        if rules.mode == "all_required_complete":
            is_complete = len(completed_required) == len(required_nodes)
        elif rules.mode == "required_plus_n_electives":
            needed = rules.required_plus_n_electives or 0
            is_complete = len(completed_required) == len(required_nodes) and len(completed_electives) >= needed
        elif rules.mode == "milestone_based":
            milestones = [n for n in required_nodes if n.node_type == "milestone"]
            is_complete = all(self._is_node_complete(node, progress_by_node_id.get(node.node_id)) for node in milestones)
        else:  # score_threshold
            scored = [n for n in required_nodes if n.min_score is not None]
            is_complete = len(completed_required) == len(required_nodes) and all(
                (progress_by_node_id.get(n.node_id) and (progress_by_node_id[n.node_id].score or 0.0) >= (n.min_score or 0.0))
                for n in scored
            )

        overdue = bool(rules.due_date and completed_at > rules.due_date)
        if overdue and rules.strict_due_date:
            is_complete = False

        if not is_complete:
            return LearningPathProgress.in_progress(path_id, overdue=overdue)

        return LearningPathProgress.complete(path_id, completed_at, overdue=overdue).with_recertification(rules)

    def _is_node_complete(self, node: PathNode, progress: Optional[NodeProgress]) -> bool:
        if not progress or not progress.completed:
            return False
        if node.min_score is None:
            return True
        return (progress.score or 0.0) >= node.min_score

    def _get_tenant_path(self, tenant_id: str, path_id: str) -> LearningPath:
        path = self._paths.get(path_id)
        if not path:
            raise NotFoundError(f"path '{path_id}' not found")
        if path.tenant_id != tenant_id:
            raise NotFoundError("path not found in tenant")
        return path

    def _validate_completion_rules(self, rules: CompletionRules) -> None:
        valid_modes = {
            "all_required_complete",
            "required_plus_n_electives",
            "milestone_based",
            "score_threshold",
        }
        if rules.mode not in valid_modes:
            raise ValidationError("unsupported completion mode")
        if rules.mode == "required_plus_n_electives" and (rules.required_plus_n_electives is None or rules.required_plus_n_electives < 1):
            raise ValidationError("required_plus_n_electives mode requires a positive required_plus_n_electives value")
        if rules.recertification_interval_days is not None and rules.recertification_interval_days < 1:
            raise ValidationError("recertification_interval_days must be > 0")
        if rules.grace_window_days < 0:
            raise ValidationError("grace_window_days cannot be negative")

    def _validate_acyclic(self, node_ids: Iterable[str], edges: List[PathEdge]) -> None:
        ids = list(node_ids)
        adjacency: Dict[str, List[str]] = {node_id: [] for node_id in ids}
        indegree: Dict[str, int] = {node_id: 0 for node_id in ids}

        for edge in edges:
            adjacency[edge.from_node_id].append(edge.to_node_id)
            indegree[edge.to_node_id] += 1

        queue = deque([node_id for node_id, degree in indegree.items() if degree == 0])
        seen = 0
        while queue:
            current = queue.popleft()
            seen += 1
            for target in adjacency[current]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)

        if seen != len(ids):
            raise ValidationError("sequence graph must be acyclic")

    def _validate_required_node_upstream(self, nodes_by_id: Dict[str, PathNode], edges: List[PathEdge]) -> None:
        inbound: Dict[str, int] = defaultdict(int)
        for edge in edges:
            inbound[edge.to_node_id] += 1

        for node_id, node in nodes_by_id.items():
            if not node.is_required:
                continue
            if inbound[node_id] == 0:
                continue  # entry node
            if inbound[node_id] < 1:
                raise ValidationError(f"required node '{node_id}' missing upstream dependency")

    def _validate_explicit_merge_points(self, edges: List[PathEdge]) -> None:
        inbound_relations: Dict[str, List[str]] = defaultdict(list)
        for edge in edges:
            inbound_relations[edge.to_node_id].append(edge.relation)

        for node_id, relations in inbound_relations.items():
            if len(relations) <= 1:
                continue
            if "branch_merge" not in relations:
                raise ValidationError(f"branch merge point '{node_id}' must include explicit branch_merge relation")

    def _record_audit(self, path: LearningPath, actor_id: str, action: str, change_reason: str) -> None:
        self._audit_log[path.path_id].append(
            {
                "tenant_id": path.tenant_id,
                "path_version": str(path.version),
                "actor_id": actor_id,
                "action": action,
                "change_reason": change_reason,
                "timestamp": utc_now().isoformat(),
            }
        )
