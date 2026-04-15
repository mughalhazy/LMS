"""Group management service — tenant-scoped group CRUD, membership, and learning assignment.

CGAP-073: replaces NotImplementedError stub. Delegates domain operations to src.GroupService
and adds tenant-scoped list operations, group update, and deactivation per org_hierarchy_spec.md.

Spec refs: docs/specs/org_hierarchy_spec.md
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure src/ layer is importable
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from group_service import GroupService, NotFoundError, ValidationError  # noqa: E402
from models import (  # noqa: E402
    AssignmentTarget,
    AssignmentType,
    Group,
    GroupMembership,
    GroupStatus,
    LearningAssignment,
)


class GroupManagementService:
    """Tenant-scoped facade over GroupService per org_hierarchy_spec.md.

    Enforces:
    - Tenant isolation on every read/write
    - Unique name/code within organisation scope
    - Status transition rules (DRAFT → ACTIVE → INACTIVE/ARCHIVED)
    - Cascade-safe deactivation (no active members before archiving)
    - Re-parenting audit trail (reparent_group not applicable at group level;
      group → organisation relationship is set at creation time)
    """

    def __init__(self) -> None:
        self._svc = GroupService()
        self._audit_log: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Groups                                                               #
    # ------------------------------------------------------------------ #

    def create_group(
        self,
        *,
        tenant_id: str,
        organization_id: str,
        name: str,
        code: str,
        created_by: str,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Group:
        return self._svc.create_group(
            tenant_id=tenant_id,
            organization_id=organization_id,
            name=name,
            code=code,
            created_by=created_by,
            description=description,
            metadata=metadata,
        )

    def get_group(self, *, tenant_id: str, group_id: str) -> Group:
        group = self._svc.groups.get(group_id)
        if not group or group.tenant_id != tenant_id:
            raise NotFoundError("Group not found")
        return group

    def update_group(
        self,
        *,
        tenant_id: str,
        group_id: str,
        name: str | None = None,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Group:
        group = self.get_group(tenant_id=tenant_id, group_id=group_id)
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError("Group name cannot be empty")
            # Uniqueness within org
            for other in self._svc.groups.values():
                if (
                    other.group_id != group_id
                    and other.tenant_id == tenant_id
                    and other.organization_id == group.organization_id
                    and other.name.lower() == name.lower()
                ):
                    raise ValidationError("Group name must be unique within organization")
            group.name = name
        if description is not None:
            group.description = description
        if metadata is not None:
            group.metadata = metadata
        group.updated_at = datetime.now(tz=timezone.utc)
        return group

    def activate_group(self, *, tenant_id: str, group_id: str) -> Group:
        self.get_group(tenant_id=tenant_id, group_id=group_id)
        return self._svc.transition_group_status(group_id, GroupStatus.ACTIVE)

    def deactivate_group(self, *, tenant_id: str, group_id: str) -> Group:
        """Transition to INACTIVE. Active members are preserved — group is suspended not archived."""
        self.get_group(tenant_id=tenant_id, group_id=group_id)
        return self._svc.transition_group_status(group_id, GroupStatus.INACTIVE)

    def archive_group(self, *, tenant_id: str, group_id: str) -> Group:
        """Archive group — blocked if active memberships exist (org_hierarchy_spec cascade rule)."""
        self.get_group(tenant_id=tenant_id, group_id=group_id)
        # Cascade check enforced inside transition_group_status
        result = self._svc.transition_group_status(group_id, GroupStatus.ARCHIVED)
        self._audit("group.archived", tenant_id=tenant_id, group_id=group_id)
        return result

    def list_groups(
        self,
        *,
        tenant_id: str,
        organization_id: str | None = None,
        status: GroupStatus | None = None,
    ) -> list[Group]:
        results = [g for g in self._svc.groups.values() if g.tenant_id == tenant_id]
        if organization_id:
            results = [g for g in results if g.organization_id == organization_id]
        if status:
            results = [g for g in results if g.status == status]
        return results

    # ------------------------------------------------------------------ #
    # Membership                                                           #
    # ------------------------------------------------------------------ #

    def add_member(
        self,
        *,
        tenant_id: str,
        group_id: str,
        user_id: str,
        role: str,
        added_by: str,
    ) -> GroupMembership:
        return self._svc.add_member(
            tenant_id=tenant_id,
            group_id=group_id,
            user_id=user_id,
            role=role,
            added_by=added_by,
        )

    def remove_member(self, *, tenant_id: str, group_id: str, user_id: str) -> GroupMembership:
        return self._svc.remove_member(tenant_id=tenant_id, group_id=group_id, user_id=user_id)

    def list_members(self, *, tenant_id: str, group_id: str) -> list[GroupMembership]:
        self.get_group(tenant_id=tenant_id, group_id=group_id)
        return self._svc.list_group_members(tenant_id=tenant_id, group_id=group_id)

    # ------------------------------------------------------------------ #
    # Learning assignment                                                  #
    # ------------------------------------------------------------------ #

    def assign_learning(
        self,
        *,
        tenant_id: str,
        group_id: str,
        assignment_type: str,
        learning_object_id: str,
        target: str,
        assigned_by: str,
        due_at: datetime | None = None,
        metadata: dict[str, str] | None = None,
    ) -> LearningAssignment:
        return self._svc.assign_learning(
            tenant_id=tenant_id,
            group_id=group_id,
            assignment_type=AssignmentType(assignment_type),
            learning_object_id=learning_object_id,
            target=AssignmentTarget(target),
            assigned_by=assigned_by,
            due_at=due_at,
            metadata=metadata,
        )

    def list_assignments(self, *, tenant_id: str, group_id: str) -> list[LearningAssignment]:
        self.get_group(tenant_id=tenant_id, group_id=group_id)
        return self._svc.list_assignments(tenant_id=tenant_id, group_id=group_id)

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _audit(self, event: str, **kwargs: Any) -> None:
        self._audit_log.append({
            "event": event,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            **kwargs,
        })
