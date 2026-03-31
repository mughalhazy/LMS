from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models import LifecycleState


class ValidateTenantCreationRequest(BaseModel):
    name: str = Field(min_length=2)
    country_code: str = Field(min_length=2, max_length=2)
    segment_type: str = Field(min_length=2)
    plan_type: str = Field(min_length=2)


class ValidationResponse(BaseModel):
    validation_passed: bool
    errors: list[dict[str, str]] = Field(default_factory=list)


class CreateTenantRequest(BaseModel):
    name: str = Field(min_length=2)
    country_code: str = Field(min_length=2, max_length=2)
    segment_type: str = Field(min_length=2)
    plan_type: str = Field(min_length=2)
    addon_flags: list[str] = Field(default_factory=list)
    admin_user: str = Field(min_length=2)


class CreateTenantResponse(BaseModel):
    tenant_id: str
    bootstrap_status: str
    isolation_mode: str
    namespace_resource: str


class InitializeTenantConfigurationRequest(BaseModel):
    default_locale: str = "en-US"
    timezone: str = "UTC"
    branding: dict[str, Any] = Field(default_factory=dict)
    enabled_modules: list[str] = Field(default_factory=list)
    security_baseline: dict[str, Any] = Field(default_factory=dict)


class UpdateTenantConfigurationRequest(BaseModel):
    config_patch: dict[str, Any]
    actor_id: str
    change_reason: str


class ManageFeatureFlagsRequest(BaseModel):
    feature_flag_changes: dict[str, bool]
    actor_id: str = "system"


class SuspendTenantRequest(BaseModel):
    suspension_reason: str
    suspended_by: str


class ReactivateTenantRequest(BaseModel):
    reactivation_reason: str
    approved_by: str


class ArchiveTenantRequest(BaseModel):
    archive_policy: str
    retention_period: str
    requested_by: str


class DecommissionTenantRequest(BaseModel):
    legal_hold_status: bool
    purge_after_date: datetime
    approved_by: str


class TenantConfigurationResponse(BaseModel):
    tenant_id: str
    configuration: dict[str, Any]
    effective_settings: dict[str, Any]


class LifecycleEventResponse(BaseModel):
    state: LifecycleState
    reason: str
    actor_id: str
    effective_at: datetime
    recorded_at: datetime


class LifecycleStatusResponse(BaseModel):
    tenant_id: str
    lifecycle_state: LifecycleState
    state_history: list[LifecycleEventResponse]
    pending_transitions: list[str]
    policy_constraints: list[str]
    next_allowed_actions: list[str]


class IsolationContext(BaseModel):
    tenant_id: str
    actor_tenant_id: str
    actor_id: str
    action: str


class IsolationDecision(BaseModel):
    allowed: bool
    reason: str
