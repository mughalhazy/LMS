from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .models import ScopeType, SubjectType


class RoleCreateRequest(BaseModel):
    role_key: str = Field(min_length=3)
    display_name: str
    description: str


class RoleUpdateRequest(BaseModel):
    display_name: str | None = None
    description: str | None = None
    status: str | None = None


class ReplaceRolePermissionsRequest(BaseModel):
    permissions: list[str]


class AssignmentCreateRequest(BaseModel):
    subject_type: SubjectType
    subject_id: str
    role_id: str
    scope_type: ScopeType
    scope_id: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    source: str = "direct"
    created_by: str


class AssignmentUpdateRequest(BaseModel):
    ends_at: datetime | None = None
    scope_type: ScopeType | None = None
    scope_id: str | None = None


class SubjectRef(BaseModel):
    type: SubjectType
    id: str


class ResourceRef(BaseModel):
    type: str
    id: str


class AuthorizeRequest(BaseModel):
    subject: SubjectRef
    permission_key: str
    resource: ResourceRef
    scope_type: ScopeType
    scope_id: str
    context: dict[str, str] = Field(default_factory=dict)


class AuthorizeBatchRequest(BaseModel):
    checks: list[AuthorizeRequest]


class AuthorizeResponse(BaseModel):
    decision: str
    reason_codes: list[str]
    policy_trace: list[str]


class PolicyRuleCreateRequest(BaseModel):
    rule_type: str
    expression: dict[str, str]
    priority: int = 100


class PolicyRuleUpdateRequest(BaseModel):
    expression: dict[str, str] | None = None
    priority: int | None = None
    enabled: bool | None = None
