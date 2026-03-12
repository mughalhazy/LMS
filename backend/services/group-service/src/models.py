from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class GroupStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class MembershipStatus(str, Enum):
    ACTIVE = "active"
    REMOVED = "removed"


class AssignmentType(str, Enum):
    COURSE = "course"
    LEARNING_PATH = "learning_path"


class AssignmentTarget(str, Enum):
    CURRENT_MEMBERS = "current_members"
    CURRENT_AND_FUTURE_MEMBERS = "current_and_future_members"


@dataclass(slots=True)
class Group:
    group_id: str
    tenant_id: str
    organization_id: str
    name: str
    code: str
    description: Optional[str]
    status: GroupStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class GroupMembership:
    membership_id: str
    tenant_id: str
    group_id: str
    user_id: str
    role: str
    status: MembershipStatus
    added_by: str
    added_at: datetime
    removed_at: Optional[datetime] = None


@dataclass(slots=True)
class LearningAssignment:
    assignment_id: str
    tenant_id: str
    group_id: str
    assignment_type: AssignmentType
    learning_object_id: str
    target: AssignmentTarget
    assigned_by: str
    assigned_at: datetime
    due_at: Optional[datetime]
    metadata: Dict[str, str] = field(default_factory=dict)
