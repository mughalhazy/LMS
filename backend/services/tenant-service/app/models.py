from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class IsolationMode(str, Enum):
    SCHEMA_PER_TENANT = "schema_per_tenant"
    DATABASE_PER_TENANT = "database_per_tenant"


class LifecycleState(str, Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    DECOMMISSIONED = "decommissioned"


@dataclass
class PlanLink:
    plan_id: str
    plan_name: str


@dataclass
class LifecycleEvent:
    state: LifecycleState
    reason: str
    actor_id: str
    effective_at: datetime
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TenantConfiguration:
    version: int = 1
    default_locale: str = "en-US"
    timezone: str = "UTC"
    branding: dict[str, Any] = field(default_factory=dict)
    enabled_modules: list[str] = field(default_factory=list)
    security_baseline: dict[str, Any] = field(default_factory=dict)
    feature_flags: dict[str, bool] = field(default_factory=dict)


@dataclass
class Tenant:
    tenant_id: str
    tenant_name: str
    tenant_code: str
    primary_domain: str
    admin_user: str
    data_residency_region: str
    plan_link: PlanLink
    isolation_mode: IsolationMode
    lifecycle_state: LifecycleState = LifecycleState.PROVISIONING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    configuration: TenantConfiguration = field(default_factory=TenantConfiguration)
    state_history: list[LifecycleEvent] = field(default_factory=list)


@dataclass
class TenantNamespace:
    resource_locator: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
