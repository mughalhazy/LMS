"""Learning path management service — creation, sequencing, completion rules, assignment, and evaluation.

CGAP-064: replaces NotImplementedError stub. Delegates domain operations to src.LearningPathService
and adds tenant-scoped list/get/archive, assignment scope management, and audit log access
per learning_path_spec.md.

Spec refs: docs/specs/learning_path_spec.md
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from models import (  # noqa: E402
    CompletionRules,
    LearningPath,
    LearningPathProgress,
    PathEdge,
    PathNode,
)
from service import LearningPathService, NotFoundError, ValidationError  # noqa: E402


class LearningPathManagementService:
    """Tenant-scoped facade over LearningPathService per learning_path_spec.md.

    Covers:
    - path_creation: draft/publish lifecycle, completion rules, validation
    - course_sequencing: node graph with acyclic enforcement, prerequisite/branch edges
    - completion_rules: all_required_complete, required_plus_n_electives, milestone_based, score_threshold
    - path_assignment_scope: role/department/location/manual scopes with effective date windows
    - auditability: all structure + rule changes versioned with actor, timestamp, change_reason
    """

    def __init__(self) -> None:
        self._svc = LearningPathService()
        # Assignment scopes: path_id → list of scope dicts
        self._assignment_scopes: dict[str, list[dict[str, Any]]] = {}

    # ------------------------------------------------------------------ #
    # Path lifecycle                                                       #
    # ------------------------------------------------------------------ #

    def create_learning_path(
        self,
        *,
        tenant_id: str,
        title: str,
        owner_id: str,
        description: str | None = None,
        audience: dict[str, str] | None = None,
        completion_rules: CompletionRules | None = None,
    ) -> LearningPath:
        return self._svc.create_learning_path(
            tenant_id=tenant_id,
            title=title,
            owner_id=owner_id,
            description=description,
            audience=audience,
            completion_rules=completion_rules,
            actor_id=owner_id,
        )

    def get_learning_path(self, *, tenant_id: str, path_id: str) -> LearningPath:
        return self._svc._get_tenant_path(tenant_id, path_id)  # noqa: SLF001

    def list_learning_paths(
        self,
        *,
        tenant_id: str,
        status: str | None = None,
        owner_id: str | None = None,
    ) -> list[LearningPath]:
        results = [p for p in self._svc._paths.values() if p.tenant_id == tenant_id]  # noqa: SLF001
        if status:
            results = [p for p in results if p.status == status]
        if owner_id:
            results = [p for p in results if p.owner_id == owner_id]
        return results

    def publish_learning_path(
        self,
        *,
        tenant_id: str,
        path_id: str,
        actor_id: str,
        change_reason: str,
    ) -> LearningPath:
        return self._svc.publish_learning_path(
            tenant_id=tenant_id,
            path_id=path_id,
            actor_id=actor_id,
            change_reason=change_reason,
        )

    def archive_learning_path(self, *, tenant_id: str, path_id: str, actor_id: str) -> LearningPath:
        path = self._svc._get_tenant_path(tenant_id, path_id)  # noqa: SLF001
        if path.status == "archived":
            return path
        path.status = "archived"
        from models import utc_now  # noqa: PLC0415
        path.updated_at = utc_now()
        self._svc._record_audit(path, actor_id, "learning.path.archived", "archived by actor")  # noqa: SLF001
        return path

    # ------------------------------------------------------------------ #
    # Completion rules                                                     #
    # ------------------------------------------------------------------ #

    def configure_completion_rules(
        self,
        *,
        tenant_id: str,
        path_id: str,
        rules: CompletionRules,
        actor_id: str,
        change_reason: str,
    ) -> LearningPath:
        return self._svc.configure_completion_rules(
            tenant_id=tenant_id,
            path_id=path_id,
            rules=rules,
            actor_id=actor_id,
            change_reason=change_reason,
        )

    # ------------------------------------------------------------------ #
    # Node and edge sequencing                                             #
    # ------------------------------------------------------------------ #

    def set_nodes(
        self,
        *,
        tenant_id: str,
        path_id: str,
        nodes: list[PathNode],
        actor_id: str,
    ) -> list[PathNode]:
        return self._svc.replace_nodes(tenant_id=tenant_id, path_id=path_id, nodes=nodes, actor_id=actor_id)

    def set_edges(
        self,
        *,
        tenant_id: str,
        path_id: str,
        edges: list[PathEdge],
        actor_id: str,
    ) -> list[PathEdge]:
        return self._svc.replace_edges(tenant_id=tenant_id, path_id=path_id, edges=edges, actor_id=actor_id)

    def get_nodes(self, *, tenant_id: str, path_id: str) -> list[PathNode]:
        self._svc._get_tenant_path(tenant_id, path_id)  # noqa: SLF001
        return list(self._svc._nodes[path_id])  # noqa: SLF001

    def get_edges(self, *, tenant_id: str, path_id: str) -> list[PathEdge]:
        self._svc._get_tenant_path(tenant_id, path_id)  # noqa: SLF001
        return list(self._svc._edges[path_id])  # noqa: SLF001

    # ------------------------------------------------------------------ #
    # Assignment scope (path_assignment_scope per spec)                   #
    # ------------------------------------------------------------------ #

    def assign_path(
        self,
        *,
        tenant_id: str,
        path_id: str,
        assignment_type: str,
        target_ref: str,
        effective_from: datetime,
        effective_to: datetime | None = None,
        assigned_by: str,
    ) -> dict[str, Any]:
        """Assign a published learning path to a role/department/location/manual target.

        learning_path_spec: path_assignment_scope — scope_id, path_id, assignment_type,
        target_ref, effective_from, effective_to.
        """
        path = self._svc._get_tenant_path(tenant_id, path_id)  # noqa: SLF001
        if path.status != "published":
            raise ValidationError("Only published paths can be assigned")

        valid_types = {"role", "department", "location", "manual"}
        if assignment_type not in valid_types:
            raise ValidationError(f"assignment_type must be one of {valid_types}")

        import uuid  # noqa: PLC0415
        scope = {
            "scope_id": str(uuid.uuid4()),
            "path_id": path_id,
            "tenant_id": tenant_id,
            "assignment_type": assignment_type,
            "target_ref": target_ref,
            "effective_from": effective_from.isoformat(),
            "effective_to": effective_to.isoformat() if effective_to else None,
            "assigned_by": assigned_by,
        }
        self._assignment_scopes.setdefault(path_id, []).append(scope)
        return scope

    def list_assignments(self, *, tenant_id: str, path_id: str) -> list[dict[str, Any]]:
        self._svc._get_tenant_path(tenant_id, path_id)  # noqa: SLF001
        return [s for s in self._assignment_scopes.get(path_id, []) if s["tenant_id"] == tenant_id]

    # ------------------------------------------------------------------ #
    # Completion evaluation                                                #
    # ------------------------------------------------------------------ #

    def evaluate_completion(
        self,
        *,
        tenant_id: str,
        path_id: str,
        progress_by_node_id: dict[str, Any],
        completed_at: datetime | None = None,
    ) -> LearningPathProgress:
        from models import NodeProgress  # noqa: PLC0415
        typed_progress = {
            node_id: NodeProgress(
                node_id=node_id,
                completed=bool(p.get("completed")),
                score=p.get("score"),
            )
            for node_id, p in progress_by_node_id.items()
        }
        return self._svc.evaluate_completion(
            tenant_id=tenant_id,
            path_id=path_id,
            progress_by_node_id=typed_progress,
            completed_at=completed_at,
        )

    # ------------------------------------------------------------------ #
    # Audit                                                                #
    # ------------------------------------------------------------------ #

    def get_audit_log(self, *, tenant_id: str, path_id: str) -> list[dict[str, str]]:
        self._svc._get_tenant_path(tenant_id, path_id)  # noqa: SLF001
        return list(self._svc._audit_log[path_id])  # noqa: SLF001
