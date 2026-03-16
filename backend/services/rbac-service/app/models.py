from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class SubjectType(str, Enum):
    USER = "user"
    GROUP = "group"
    SERVICE_ACCOUNT = "service_account"


class ScopeType(str, Enum):
    TENANT = "tenant"
    ORG_UNIT = "org_unit"
    COURSE = "course"
    PROGRAM = "program"
    COHORT = "cohort"


class RoleStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"


class RuleType(str, Enum):
    SOD_CONFLICT = "sod_conflict"
    EXPLICIT_DENY = "explicit_deny"
    STEP_UP_REQUIRED = "step_up_required"
    TIME_WINDOW = "time_window"
    NETWORK_BOUNDARY = "network_boundary"


class RoleDefinition(BaseModel):
    role_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    role_key: str
    display_name: str
    description: str
    is_system: bool = False
    status: RoleStatus = RoleStatus.ACTIVE
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PermissionDefinition(BaseModel):
    permission_id: str = Field(default_factory=lambda: str(uuid4()))
    permission_key: str
    resource_type: str
    action: str
    risk_tier: Literal["low", "moderate", "high", "critical"] = "low"
    is_assignable: bool = True


class RolePermissionBinding(BaseModel):
    role_id: str
    permission_id: str
    effect: Literal["allow", "deny"] = "allow"
    conditions: dict[str, str] = Field(default_factory=dict)


class SubjectRoleAssignment(BaseModel):
    assignment_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    subject_type: SubjectType
    subject_id: str
    role_id: str
    scope_type: ScopeType
    scope_id: str
    starts_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ends_at: datetime | None = None
    source: Literal["direct", "group_derived", "jit"] = "direct"
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: datetime | None = None


class PolicyRule(BaseModel):
    policy_rule_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    rule_type: RuleType
    expression: dict[str, str]
    priority: int = 100
    enabled: bool = True


class AuthorizationDecisionLog(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    principal_subject: str
    permission_key: str
    resource_type: str
    resource_id: str
    decision: Literal["allow", "deny"]
    reason_codes: list[str]
    policy_trace: list[str]
    correlation_id: str | None = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
