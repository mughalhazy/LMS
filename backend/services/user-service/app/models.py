from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserStatus(str, Enum):
    # Spec: user-service-spec §1 — full lifecycle states
    PENDING_ACTIVATION = "pending_activation"  # awaiting first login / activation
    PROVISIONED = "provisioned"                # legacy alias — maps to pending_activation
    ACTIVE = "active"
    LOCKED = "locked"                          # temporary administrative hold; reversible
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
    TERMINATED = "terminated"


class UserLifecycleEventType(str, Enum):
    CREATED = "lms.user.created"
    PROFILE_UPDATED = "lms.user.profile.updated"
    STATUS_CHANGED = "lms.user.status.changed"
    ROLE_LINKED = "lms.user.role.linked"
    ROLE_UNLINKED = "lms.user.role.unlinked"
    IDENTITY_LINKED = "lms.user.identity.linked"
    IDENTITY_UNLINKED = "lms.user.identity.unlinked"
    PREFERENCES_UPDATED = "lms.user.preferences.updated"
    LIFECYCLE_TERMINATED = "user.lifecycle.terminated"
    LIFECYCLE_REINSTATED = "user.lifecycle.reinstated"
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
    role_display_name: str | None = None   # denormalised from rbac-service RoleDefinition.display_name
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


class IdentityLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    provider: str
    external_subject_id: str
    linked_at: datetime = Field(default_factory=utc_now)
    linked_by: str


class UserPreferences(BaseModel):
    model_config = ConfigDict(extra="allow")

    notification_preferences: dict[str, object] = Field(default_factory=dict)
    accessibility_preferences: dict[str, object] = Field(default_factory=dict)
    language_preference: str | None = None
    updated_at: datetime = Field(default_factory=utc_now)
    updated_by: str = "system"


class UserAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    user_id: str
    status: UserStatus = UserStatus.PROVISIONED
    identity: IdentityAttributes
    profile: UserProfile
    role_links: list[RoleLink] = Field(default_factory=list)
    identity_links: list[IdentityLink] = Field(default_factory=list)
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    version: int = 1
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    deleted_at: datetime | None = None
