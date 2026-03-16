from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import AuditLogEntry, UserAggregate, UserLifecycleEvent, UserStatus


class TenantScopedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    actor_id: str


class CreateUserRequest(TenantScopedRequest):
    user_id: str = Field(description="Canonical User id from Rails User model")
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    display_name: str | None = None
    locale: str | None = None
    timezone: str | None = None
    title: str | None = None
    department: str | None = None
    external_subject_id: str | None = None


class UpdateUserRequest(TenantScopedRequest):
    email: EmailStr | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    locale: str | None = None
    timezone: str | None = None
    title: str | None = None
    department: str | None = None
    phone_number: str | None = None
    avatar_url: str | None = None


class UpdateStatusRequest(TenantScopedRequest):
    status: UserStatus
    reason: str


class RoleLinkRequest(TenantScopedRequest):
    role_id: str


class RoleUnlinkRequest(TenantScopedRequest):
    role_id: str


class UserResponse(BaseModel):
    user: UserAggregate


class UserListResponse(BaseModel):
    users: list[UserAggregate]


class AuditLogResponse(BaseModel):
    entries: list[AuditLogEntry]


class EventEnvelope(BaseModel):
    event: UserLifecycleEvent


class EventsResponse(BaseModel):
    events: list[UserLifecycleEvent]


class HealthResponse(BaseModel):
    status: str
    service: str


class MetricsResponse(BaseModel):
    service: str
    counters: dict[str, int]
    attributes: dict[str, Any] = Field(default_factory=dict)
