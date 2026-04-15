from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserStatus(str, Enum):
    PROVISIONED = "provisioned"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
    TERMINATED = "terminated"


class UserLifecycleEventType(str, Enum):
    CREATED = "lms.user.created"
    PROFILE_UPDATED = "lms.user.profile.updated"
    STATUS_CHANGED = "lms.user.status.changed"
    ROLE_LINKED = "lms.user.role.linked"
    ROLE_UNLINKED = "lms.user.role.unlinked"
    DELETED = "lms.user.deleted"


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str
    last_name: str
    display_name: str | None = None
    locale: str | None = None
    timezone: str | None = None
    title: str | None = None
    department: str | None = None
    phone_number: str | None = None
    avatar_url: str | None = None


class IdentityAttributes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    username: str
    external_subject_id: str | None = None


class RoleLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: str
    linked_at: datetime = Field(default_factory=utc_now)
    linked_by: str


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_id: str
    tenant_id: str
    user_id: str
    action: str
    actor_id: str
    at: datetime = Field(default_factory=utc_now)
    changes: dict[str, Any] = Field(default_factory=dict)


class UserLifecycleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    event_type: UserLifecycleEventType
    timestamp: datetime = Field(default_factory=utc_now)
    tenant_id: str
    correlation_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    user_id: str
    status: UserStatus = UserStatus.PROVISIONED
    identity: IdentityAttributes
    profile: UserProfile
    role_links: list[RoleLink] = Field(default_factory=list)
    version: int = 1
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    deleted_at: datetime | None = None
