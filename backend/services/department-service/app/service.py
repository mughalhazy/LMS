"""Department management service — tenant-scoped department CRUD, hierarchy, and membership.

CGAP-074: replaces NotImplementedError stub. Delegates domain operations to src.DepartmentService
and adds deactivation with cascade safety, tenant-scoped list, and audit trail for reparenting
per org_hierarchy_spec.md.

Spec refs: docs/specs/org_hierarchy_spec.md
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from models import Department, DepartmentMembership  # noqa: E402
from service import DepartmentService, NotFoundError, ValidationError  # noqa: E402


class DepartmentManagementService:
    """Tenant-scoped facade over DepartmentService per org_hierarchy_spec.md.

    Enforces:
    - Tenant isolation on every read/write
    - Unique name/code within organisation scope
    - No orphan departments (parent must exist in same org + tenant)
    - Cascade-safe deactivation: a department cannot be deactivated while it has
      active child departments (spec rule: deactivating parent requires children
      deactivated first or cascading policy applied)
    - Audit trail for reparenting operations (before/after parent IDs + actor)
    - Cycle detection on reparent (delegated to src layer)
    """

    def __init__(self) -> None:
        self._svc = DepartmentService()
        self._audit_log: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Departments                                                          #
    # ------------------------------------------------------------------ #

    def create_department(
        self,
        *,
        tenant_id: str,
        organization_id: str,
        name: str,
        code: str,
        parent_department_id: str | None = None,
        department_head_user_id: str | None = None,
        cost_center: str | None = None,
    ) -> Department:
        return self._svc.create_department(
            tenant_id=tenant_id,
            organization_id=organization_id,
            name=name,
            code=code,
            parent_department_id=parent_department_id,
            department_head_user_id=department_head_user_id,
            cost_center=cost_center,
        )

    def get_department(self, *, tenant_id: str, department_id: str) -> Department:
        dept = self._svc.get_department(department_id)
        if dept.tenant_id != tenant_id:
            raise NotFoundError(f"department '{department_id}' not found")
        return dept

    def update_department(
        self,
        *,
        tenant_id: str,
        department_id: str,
        name: str | None = None,
        code: str | None = None,
        department_head_user_id: str | None = None,
        cost_center: str | None = None,
    ) -> Department:
        dept = self.get_department(tenant_id=tenant_id, department_id=department_id)
        if name is not None:
            name = name.strip()
            if not name:
                raise ValidationError("Department name cannot be empty")
            # Uniqueness within org (excluding self)
            for other in self._svc._departments.values():  # noqa: SLF001
                if (
                    other.department_id != department_id
                    and other.organization_id == dept.organization_id
                    and other.name.strip().lower() == name.lower()
                ):
                    raise ValidationError(f"Department name '{name}' already exists in organization")
            dept.name = name
        if code is not None:
            code = code.strip()
            if not code:
                raise ValidationError("Department code cannot be empty")
            for other in self._svc._departments.values():  # noqa: SLF001
                if (
                    other.department_id != department_id
                    and other.organization_id == dept.organization_id
                    and other.code.strip().lower() == code.lower()
                ):
                    raise ValidationError(f"Department code '{code}' already exists in organization")
            dept.code = code
        if department_head_user_id is not None:
            dept.department_head_user_id = department_head_user_id
        if cost_center is not None:
            dept.cost_center = cost_center
        dept.updated_at = datetime.now(timezone.utc)
        return dept

    def deactivate_department(
        self,
        *,
        tenant_id: str,
        department_id: str,
        actor_id: str,
        cascade: bool = False,
    ) -> Department:
        """Deactivate a department.

        If cascade=False (default): raises ValidationError if active child departments exist.
        If cascade=True: recursively deactivates all active children first per spec cascade policy.
        """
        dept = self.get_department(tenant_id=tenant_id, department_id=department_id)
        if dept.status == "inactive":
            return dept

        active_children = [
            d for d in self._svc._departments.values()  # noqa: SLF001
            if d.parent_department_id == department_id and d.status == "active"
        ]
        if active_children and not cascade:
            raise ValidationError(
                f"Cannot deactivate department '{department_id}': "
                f"{len(active_children)} active child department(s) must be deactivated first. "
                "Pass cascade=True to apply cascading deactivation policy."
            )
        if cascade:
            for child in active_children:
                self.deactivate_department(
                    tenant_id=tenant_id,
                    department_id=child.department_id,
                    actor_id=actor_id,
                    cascade=True,
                )

        dept.status = "inactive"
        dept.updated_at = datetime.now(timezone.utc)
        self._audit(
            "department.deactivated",
            tenant_id=tenant_id,
            department_id=department_id,
            actor_id=actor_id,
            cascade=cascade,
        )
        return dept

    def reactivate_department(self, *, tenant_id: str, department_id: str, actor_id: str) -> Department:
        dept = self.get_department(tenant_id=tenant_id, department_id=department_id)
        if dept.status == "active":
            return dept
        # Parent must be active if one exists (no orphan reactivation)
        if dept.parent_department_id:
            parent = self._svc._departments.get(dept.parent_department_id)  # noqa: SLF001
            if parent and parent.status != "active":
                raise ValidationError("Cannot reactivate a department whose parent is inactive")
        dept.status = "active"
        dept.updated_at = datetime.now(timezone.utc)
        self._audit("department.reactivated", tenant_id=tenant_id, department_id=department_id, actor_id=actor_id)
        return dept

    def reparent_department(
        self,
        *,
        tenant_id: str,
        department_id: str,
        new_parent_department_id: str | None,
        actor_id: str,
    ) -> Department:
        """Reparent department with audit trail (spec: before/after parent IDs + actor metadata)."""
        dept = self.get_department(tenant_id=tenant_id, department_id=department_id)
        before_parent = dept.parent_department_id

        result = self._svc.reparent_department(
            department_id=department_id,
            new_parent_department_id=new_parent_department_id,
        )
        # Audit log per org_hierarchy_spec: "Re-parenting must be audit logged with before/after parent IDs and actor metadata"
        self._audit(
            "department.reparented",
            tenant_id=tenant_id,
            department_id=department_id,
            actor_id=actor_id,
            before_parent_id=before_parent,
            after_parent_id=new_parent_department_id,
        )
        return result

    def list_departments(
        self,
        *,
        tenant_id: str,
        organization_id: str | None = None,
        status: str | None = None,
    ) -> list[Department]:
        results = [
            d for d in self._svc._departments.values()  # noqa: SLF001
            if d.tenant_id == tenant_id
        ]
        if organization_id:
            results = [d for d in results if d.organization_id == organization_id]
        if status:
            results = [d for d in results if d.status == status]
        return results

    def list_children(self, *, tenant_id: str, parent_department_id: str) -> list[Department]:
        self.get_department(tenant_id=tenant_id, department_id=parent_department_id)
        return self._svc.list_children(parent_department_id)

    # ------------------------------------------------------------------ #
    # Membership                                                           #
    # ------------------------------------------------------------------ #

    def map_membership(
        self,
        *,
        tenant_id: str,
        organization_id: str,
        department_id: str,
        user_id: str,
        role: str,
    ) -> DepartmentMembership:
        return self._svc.map_membership(
            tenant_id=tenant_id,
            organization_id=organization_id,
            department_id=department_id,
            user_id=user_id,
            role=role,
        )

    def list_memberships(self, *, tenant_id: str, department_id: str) -> list[DepartmentMembership]:
        self.get_department(tenant_id=tenant_id, department_id=department_id)
        return self._svc.list_memberships(department_id)

    # ------------------------------------------------------------------ #
    # Audit                                                                #
    # ------------------------------------------------------------------ #

    def get_audit_log(self, *, tenant_id: str) -> list[dict[str, Any]]:
        return [entry for entry in self._audit_log if entry.get("tenant_id") == tenant_id]

    def _audit(self, event: str, **kwargs: Any) -> None:
        self._audit_log.append({
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        })
