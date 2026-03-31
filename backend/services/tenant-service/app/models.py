from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from backend.services.shared.models.tenant import TenantContract


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
    country_behavior_profiles: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass
class Tenant:
    tenant_id: str
    name: str
    country_code: str
    segment_type: str
    plan_type: str
    addon_flags: list[str]
    isolation_mode: IsolationMode
    lifecycle_state: LifecycleState = LifecycleState.PROVISIONING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    configuration: TenantConfiguration = field(default_factory=TenantConfiguration)
    state_history: list[LifecycleEvent] = field(default_factory=list)

    def contract(self) -> TenantContract:
        return TenantContract(
            tenant_id=self.tenant_id,
            name=self.name,
            country_code=self.country_code,
            segment_type=self.segment_type,
            plan_type=self.plan_type,
            addon_flags=self.addon_flags,
        ).normalized()


@dataclass
class TenantNamespace:
    resource_locator: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
