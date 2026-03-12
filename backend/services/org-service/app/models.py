from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Organization:
    tenant_id: str
    name: str
    code: str
    primary_admin_user_id: Optional[str] = None
    timezone: str = "UTC"
    locale: str = "en-US"
    parent_organization_id: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)
    status: Status = Status.ACTIVE
    organization_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class Department:
    organization_id: str
    name: str
    code: str
    department_head_user_id: Optional[str] = None
    cost_center: Optional[str] = None
    parent_department_id: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)
    status: Status = Status.ACTIVE
    department_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class Team:
    department_id: str
    name: str
    code: str
    team_lead_user_id: Optional[str] = None
    capacity: Optional[int] = None
    metadata: dict[str, str] = field(default_factory=dict)
    status: Status = Status.ACTIVE
    team_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class ReparentAuditLog:
    actor_user_id: str
    entity_type: str
    entity_id: str
    old_parent_id: Optional[str]
    new_parent_id: Optional[str]
    changed_at: datetime = field(default_factory=utc_now)
