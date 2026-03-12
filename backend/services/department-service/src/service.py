from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import Department, DepartmentMembership


class DepartmentServiceError(Exception):
    """Base error for department service operations."""


class ValidationError(DepartmentServiceError):
    """Raised when an operation violates hierarchy or uniqueness rules."""


class NotFoundError(DepartmentServiceError):
    """Raised when a requested department or membership does not exist."""


class DepartmentService:
    """In-memory implementation of department creation, hierarchy, and membership mappings."""

    def __init__(self) -> None:
        self._departments: Dict[str, Department] = {}
        self._memberships_by_department: Dict[str, List[DepartmentMembership]] = defaultdict(list)

    def create_department(
        self,
        *,
        tenant_id: str,
        organization_id: str,
        name: str,
        code: str,
        parent_department_id: Optional[str] = None,
        department_head_user_id: Optional[str] = None,
        cost_center: Optional[str] = None,
    ) -> Department:
        self._validate_unique_within_organization(organization_id=organization_id, name=name, code=code)

        if parent_department_id:
            parent = self._departments.get(parent_department_id)
            if not parent:
                raise NotFoundError(f"parent department '{parent_department_id}' was not found")
            if parent.organization_id != organization_id:
                raise ValidationError("parent department must belong to the same organization")
            if parent.tenant_id != tenant_id:
                raise ValidationError("cross-tenant hierarchy is not permitted")

        department = Department(
            tenant_id=tenant_id,
            organization_id=organization_id,
            name=name,
            code=code,
            parent_department_id=parent_department_id,
            department_head_user_id=department_head_user_id,
            cost_center=cost_center,
        )
        self._departments[department.department_id] = department
        return department

    def get_department(self, department_id: str) -> Department:
        department = self._departments.get(department_id)
        if not department:
            raise NotFoundError(f"department '{department_id}' was not found")
        return department

    def list_children(self, parent_department_id: str) -> List[Department]:
        return [d for d in self._departments.values() if d.parent_department_id == parent_department_id]

    def reparent_department(self, *, department_id: str, new_parent_department_id: Optional[str]) -> Department:
        department = self.get_department(department_id)

        if new_parent_department_id is None:
            department.parent_department_id = None
            department.updated_at = self._now()
            return department

        if new_parent_department_id == department_id:
            raise ValidationError("a department cannot be its own parent")

        new_parent = self.get_department(new_parent_department_id)

        if new_parent.organization_id != department.organization_id:
            raise ValidationError("cross-organization re-parenting is not allowed")
        if new_parent.tenant_id != department.tenant_id:
            raise ValidationError("cross-tenant re-parenting is not allowed")

        self._ensure_no_cycle(department_id=department_id, candidate_parent_id=new_parent_department_id)

        department.parent_department_id = new_parent_department_id
        department.updated_at = self._now()
        return department

    def map_membership(
        self,
        *,
        tenant_id: str,
        organization_id: str,
        department_id: str,
        user_id: str,
        role: str,
    ) -> DepartmentMembership:
        department = self.get_department(department_id)

        if department.tenant_id != tenant_id:
            raise ValidationError("membership tenant_id does not match department tenant_id")
        if department.organization_id != organization_id:
            raise ValidationError("membership organization_id does not match department organization_id")

        existing = self._memberships_by_department[department_id]
        if any(m.user_id == user_id and m.role == role for m in existing):
            raise ValidationError("duplicate department membership mapping")

        membership = DepartmentMembership(
            tenant_id=tenant_id,
            organization_id=organization_id,
            department_id=department_id,
            user_id=user_id,
            role=role,
        )
        existing.append(membership)
        return membership

    def list_memberships(self, department_id: str) -> List[DepartmentMembership]:
        self.get_department(department_id)
        return list(self._memberships_by_department[department_id])

    def _validate_unique_within_organization(self, *, organization_id: str, name: str, code: str) -> None:
        normalized_name = name.strip().lower()
        normalized_code = code.strip().lower()

        for department in self._departments.values():
            if department.organization_id != organization_id:
                continue
            if department.name.strip().lower() == normalized_name:
                raise ValidationError(f"department name '{name}' already exists in organization '{organization_id}'")
            if department.code.strip().lower() == normalized_code:
                raise ValidationError(f"department code '{code}' already exists in organization '{organization_id}'")

    def _ensure_no_cycle(self, *, department_id: str, candidate_parent_id: str) -> None:
        cursor = candidate_parent_id
        while cursor:
            if cursor == department_id:
                raise ValidationError("re-parenting would create a cycle in department hierarchy")
            cursor = self._departments[cursor].parent_department_id

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)
