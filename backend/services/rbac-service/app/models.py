from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ScopeType(str, Enum):
    PLATFORM = "platform"
    TENANT = "tenant"
    ORG_UNIT = "org_unit"
    COURSE = "course"
    SELF = "self"


class SubjectType(str, Enum):
    USER = "user"
    GROUP = "group"
    SERVICE_ACCOUNT = "service_account"


class Role(BaseModel):
    role_id: str
    role_name: str
    description: str


class Permission(BaseModel):
    permission_id: str
    action: str
    resource_type: str


class RolePermission(BaseModel):
    role_id: str
    permission_id: str


class Assignment(BaseModel):
    assignment_id: str
    subject_type: SubjectType
    subject_id: str
    role_id: str
    scope_type: ScopeType
    scope_id: str
    starts_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ends_at: datetime | None = None
    assigned_by: str
    assignment_model: Literal["direct", "group-derived", "just-in-time"] = "direct"


class AssignmentCreate(BaseModel):
    subject_type: SubjectType
    subject_id: str
    role_id: str
    scope_type: ScopeType
    scope_id: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    assigned_by: str
    assignment_model: Literal["direct", "group-derived", "just-in-time"] = "direct"


class AuthorizeRequest(BaseModel):
    principal_id: str
    principal_type: SubjectType = SubjectType.USER
    permission: str
    scope_type: ScopeType
    scope_id: str
    tenant_id: str | None = None


class AuthorizeDecision(BaseModel):
    decision: Literal["ALLOW", "DENY"]
    reason: str
    effective_permissions: list[str]


class AuthorizationAuditEvent(BaseModel):
    event_id: str
    timestamp: datetime
    principal: str
    action: str
    resource: str
    scope: str
    decision: Literal["ALLOW", "DENY"]
    reason: str
    correlation_id: str | None = None
