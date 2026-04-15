from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from .models import (
    AssignmentTarget,
    AssignmentType,
    Group,
    GroupMembership,
    GroupStatus,
    LearningAssignment,
    MembershipStatus,
)


class GroupServiceError(Exception):
    """Domain-specific exception."""


class NotFoundError(GroupServiceError):
    """Domain-specific exception."""


class ValidationError(GroupServiceError):
    """Domain-specific exception."""


class GroupService:
    def __init__(self) -> None:
        self.groups: Dict[str, Group] = {}
        self.memberships: Dict[str, GroupMembership] = {}
        self.assignments: Dict[str, LearningAssignment] = {}
        self.group_member_index: Dict[str, Dict[str, str]] = defaultdict(dict)

    def _now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def create_group(
        self,
        tenant_id: str,
        organization_id: str,
        name: str,
        code: str,
        created_by: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Group:
        if not name.strip() or not code.strip():
            raise ValidationError("Group name and code are required")

        for group in self.groups.values():
            if group.tenant_id == tenant_id and group.organization_id == organization_id:
                if group.name.lower() == name.lower():
                    raise ValidationError("Group name must be unique within organization")
                if group.code.lower() == code.lower():
                    raise ValidationError("Group code must be unique within organization")

        now = self._now()
        group = Group(
            group_id=str(uuid4()),
            tenant_id=tenant_id,
            organization_id=organization_id,
            name=name,
            code=code,
            description=description,
            status=GroupStatus.DRAFT,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self.groups[group.group_id] = group
        return group

    def transition_group_status(self, group_id: str, new_status: GroupStatus) -> Group:
        group = self.groups.get(group_id)
        if not group:
            raise NotFoundError("Group not found")

        valid_transitions = {
            GroupStatus.DRAFT: {GroupStatus.ACTIVE, GroupStatus.ARCHIVED},
            GroupStatus.ACTIVE: {GroupStatus.INACTIVE, GroupStatus.ARCHIVED},
            GroupStatus.INACTIVE: {GroupStatus.ACTIVE, GroupStatus.ARCHIVED},
            GroupStatus.ARCHIVED: set(),
        }

        if new_status == group.status:
            return group

        if new_status not in valid_transitions[group.status]:
            raise ValidationError(
                f"Invalid status transition: {group.status.value} -> {new_status.value}"
            )

        if new_status == GroupStatus.ARCHIVED:
            active_members = [
                member
                for member in self.memberships.values()
                if member.group_id == group.group_id and member.status == MembershipStatus.ACTIVE
            ]
            if active_members:
                raise ValidationError("Cannot archive a group with active memberships")

        group.status = new_status
        group.updated_at = self._now()
        return group

    def add_member(self, tenant_id: str, group_id: str, user_id: str, role: str, added_by: str) -> GroupMembership:
        group = self.groups.get(group_id)
        if not group or group.tenant_id != tenant_id:
            raise NotFoundError("Group not found")
        if group.status not in {GroupStatus.ACTIVE, GroupStatus.DRAFT}:
            raise ValidationError("Members can only be added to draft or active groups")

        existing_membership_id = self.group_member_index[group_id].get(user_id)
        if existing_membership_id:
            existing = self.memberships[existing_membership_id]
            if existing.status == MembershipStatus.ACTIVE:
                raise ValidationError("User already has active group membership")

        membership = GroupMembership(
            membership_id=str(uuid4()),
            tenant_id=tenant_id,
            group_id=group_id,
            user_id=user_id,
            role=role,
            status=MembershipStatus.ACTIVE,
            added_by=added_by,
            added_at=self._now(),
        )
        self.memberships[membership.membership_id] = membership
        self.group_member_index[group_id][user_id] = membership.membership_id
        return membership

    def remove_member(self, tenant_id: str, group_id: str, user_id: str) -> GroupMembership:
        membership_id = self.group_member_index[group_id].get(user_id)
        if not membership_id:
            raise NotFoundError("Membership not found")

        membership = self.memberships[membership_id]
        if membership.tenant_id != tenant_id:
            raise NotFoundError("Membership not found")

        membership.status = MembershipStatus.REMOVED
        membership.removed_at = self._now()
        del self.group_member_index[group_id][user_id]
        return membership

    def list_group_members(self, tenant_id: str, group_id: str) -> List[GroupMembership]:
        return [
            membership
            for membership in self.memberships.values()
            if membership.tenant_id == tenant_id
            and membership.group_id == group_id
            and membership.status == MembershipStatus.ACTIVE
        ]

    def assign_learning(
        self,
        tenant_id: str,
        group_id: str,
        assignment_type: AssignmentType,
        learning_object_id: str,
        target: AssignmentTarget,
        assigned_by: str,
        due_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> LearningAssignment:
        group = self.groups.get(group_id)
        if not group or group.tenant_id != tenant_id:
            raise NotFoundError("Group not found")

        if group.status != GroupStatus.ACTIVE:
            raise ValidationError("Learning can only be assigned to active groups")

        duplicate_assignment = any(
            assignment.tenant_id == tenant_id
            and assignment.group_id == group_id
            and assignment.assignment_type == assignment_type
            and assignment.learning_object_id == learning_object_id
            for assignment in self.assignments.values()
        )
        if duplicate_assignment:
            raise ValidationError("This learning object has already been assigned to the group")

        assignment = LearningAssignment(
            assignment_id=str(uuid4()),
            tenant_id=tenant_id,
            group_id=group_id,
            assignment_type=assignment_type,
            learning_object_id=learning_object_id,
            target=target,
            assigned_by=assigned_by,
            assigned_at=self._now(),
            due_at=due_at,
            metadata=metadata or {},
        )
        self.assignments[assignment.assignment_id] = assignment
        return assignment

    def list_assignments(self, tenant_id: str, group_id: str) -> List[LearningAssignment]:
        return [
            assignment
            for assignment in self.assignments.values()
            if assignment.tenant_id == tenant_id and assignment.group_id == group_id
        ]
