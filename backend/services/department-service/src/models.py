from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Department:
    tenant_id: str
    organization_id: str
    name: str
    code: str
    parent_department_id: Optional[str] = None
    department_head_user_id: Optional[str] = None
    cost_center: Optional[str] = None
    status: str = "active"
    department_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)


@dataclass
class DepartmentMembership:
    tenant_id: str
    organization_id: str
    department_id: str
    user_id: str
    role: str
    membership_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=_utc_now)
