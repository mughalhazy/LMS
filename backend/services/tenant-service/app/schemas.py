from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.models import LifecycleEvent, LifecycleState, TenantConfiguration


@dataclass
class ValidateTenantCreationRequest:
    tenant_code: str
    primary_domain: str
    admin_email: str
    requested_region: str


@dataclass
class ValidationResponse:
    validation_passed: bool
    errors: list[dict[str, str]] = field(default_factory=list)


@dataclass
class CreateTenantRequest:
    tenant_name: str
    tenant_code: str
    primary_domain: str
    admin_user: str
    data_residency_region: str
    subscription_plan: str


@dataclass
class CreateTenantResponse:
    tenant_id: str
    bootstrap_status: str
    isolation_mode: str
    namespace_resource: str


@dataclass
class InitializeTenantConfigurationRequest:
    default_locale: str = "en-US"
    timezone: str = "UTC"
    branding: dict[str, Any] = field(default_factory=dict)
    enabled_modules: list[str] = field(default_factory=list)
    security_baseline: dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateTenantConfigurationRequest:
    config_patch: dict[str, Any]
    actor_id: str
    change_reason: str


@dataclass
class ManageFeatureFlagsRequest:
    feature_flag_changes: dict[str, bool]
    rollout_strategy: str = "immediate"
    actor_id: str = "system"


@dataclass
class SuspendTenantRequest:
    suspension_reason: str
    suspended_by: str
    effective_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ReactivateTenantRequest:
    reactivation_reason: str
    approved_by: str
    effective_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ArchiveTenantRequest:
    archive_policy: str
    retention_period: str
    requested_by: str


@dataclass
class DecommissionTenantRequest:
    legal_hold_status: bool
    purge_after_date: datetime
    approved_by: str


@dataclass
class TenantConfigurationResponse:
    tenant_id: str
    configuration: TenantConfiguration
    effective_settings: dict[str, Any]


@dataclass
class LifecycleStatusResponse:
    tenant_id: str
    lifecycle_state: LifecycleState
    state_history: list[LifecycleEvent]
    pending_transitions: list[str]
    policy_constraints: list[str]
    next_allowed_actions: list[str]


@dataclass
class IsolationContext:
    tenant_id: str
    actor_tenant_id: str
    actor_id: str
    action: str


@dataclass
class IsolationDecision:
    allowed: bool
    reason: str
