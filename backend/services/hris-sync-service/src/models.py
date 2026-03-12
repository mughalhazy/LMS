from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Role:
    tenant_id: str
    external_hris_code: str
    name: str
    category: str
    permission_set: Dict[str, bool]
    is_active: bool = True
    role_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class Department:
    tenant_id: str
    external_hris_code: str
    name: str
    cost_center: Optional[str]
    parent_external_hris_code: Optional[str] = None
    parent_department_id: Optional[str] = None
    is_active: bool = True
    department_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class User:
    tenant_id: str
    external_hris_id: str
    first_name: str
    last_name: str
    email: str
    status: str
    title: str
    role_id: Optional[str]
    department_id: Optional[str]
    manager_user_id: Optional[str]
    hire_date: Optional[datetime]
    deactivated_at: Optional[datetime]
    user_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class SyncJob:
    tenant_id: str
    job_name: str
    interval_minutes: int
    enabled: bool = True
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    job_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
