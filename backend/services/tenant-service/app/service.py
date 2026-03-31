from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

from app.audit import AuditLogger
from app.errors import TenantServiceError
from app.events import EventPublisher, build_lifecycle_event
from app.models import IsolationMode, LifecycleEvent, LifecycleState, Tenant, TenantConfiguration, TenantNamespace
from app.observability import MetricsRegistry
from app.schemas import IsolationContext, IsolationDecision
from app.store import TenantStore
from backend.services.shared.utils.entitlements import resolve_capabilities

SUPPORTED_COUNTRIES = {"US", "GB", "DE", "IN", "SG"}
DEFAULT_EFFECTIVE_SETTINGS = {
    "security.require_mfa": True,
    "security.session_ttl_minutes": 60,
    "feature.analytics": True,
}


class TenantService:
    def __init__(self, store: TenantStore, publisher: EventPublisher, metrics: MetricsRegistry):
        self.store = store
        self.publisher = publisher
        self.metrics = metrics
        self.audit_logger = AuditLogger("tenant.audit")

    def validate_creation(
        self,
        name: str,
        country_code: str,
        segment_type: str,
        plan_type: str,
        addon_flags: list[str] | None = None,
    ) -> list[dict[str, str]]:
        errors: list[dict[str, str]] = []
        if self.store.by_code(name.lower()):
            errors.append({"field": "name", "code": "duplicate", "message": "name already exists"})
        if country_code.upper() not in SUPPORTED_COUNTRIES:
            errors.append({"field": "country_code", "code": "unsupported", "message": "country_code is not supported"})
        if not segment_type.strip():
            errors.append({"field": "segment_type", "code": "invalid", "message": "segment_type cannot be empty"})
        if not plan_type.strip():
            errors.append({"field": "plan_type", "code": "invalid", "message": "plan_type cannot be empty"})
        normalized_addons = addon_flags or []
        if any(not addon.strip() for addon in normalized_addons):
            errors.append({"field": "addon_flags", "code": "invalid", "message": "addon_flags cannot contain empty values"})
        return errors

    def _select_isolation_mode(self, plan_type: str) -> IsolationMode:
        plan = plan_type.lower()
        if plan in {"enterprise", "regulated"}:
            return IsolationMode.DATABASE_PER_TENANT
        return IsolationMode.SCHEMA_PER_TENANT

    def _initialize_namespace(self, tenant_id: str, isolation_mode: IsolationMode) -> TenantNamespace:
        locator = f"db://lms_{tenant_id}" if isolation_mode == IsolationMode.DATABASE_PER_TENANT else f"schema://tenant_{tenant_id}"
        return TenantNamespace(resource_locator=locator)

    def create_tenant(self, **kwargs) -> tuple[Tenant, TenantNamespace]:
        with self.metrics.timer("tenant.create"):
            errors = self.validate_creation(
                kwargs["name"],
                kwargs["country_code"],
                kwargs["segment_type"],
                kwargs["plan_type"],
                kwargs.get("addon_flags", []),
            )
            if errors:
                self.metrics.inc("tenant.create.conflict")
                raise TenantServiceError("tenant creation conflict", status_code=409, detail=errors)

            tenant_id = f"tnt_{uuid4().hex[:12]}"
            isolation_mode = self._select_isolation_mode(kwargs["plan_type"])
            addon_flags = sorted(set(kwargs.get("addon_flags", [])))
            tenant = Tenant(
                tenant_id=tenant_id,
                isolation_mode=isolation_mode,
                lifecycle_state=LifecycleState.ACTIVE,
                name=kwargs["name"],
                country_code=kwargs["country_code"].upper(),
                segment_type=kwargs["segment_type"],
                plan_type=kwargs["plan_type"],
                addon_flags=addon_flags,
            )
            tenant.state_history.append(
                LifecycleEvent(
                    state=LifecycleState.ACTIVE,
                    reason="tenant_created",
                    actor_id=kwargs["admin_user"],
                    effective_at=datetime.now(timezone.utc),
                )
            )
            namespace = self._initialize_namespace(tenant.tenant_id, isolation_mode)
            self.store.add(tenant, namespace)
            self.metrics.inc("tenant.create.success")
            self.audit_logger.log(event_type="admin.tenant.created", tenant_id=tenant.tenant_id, actor_id=kwargs["admin_user"], details={"name": tenant.name})
            self.publisher.publish(build_lifecycle_event("tenant.lifecycle.created", tenant.tenant_id, "tenant.create", {"state": "active"}))
            return tenant, namespace

    def get_tenant(self, tenant_id: str) -> Tenant:
        tenant = self.store.get(tenant_id)
        if not tenant:
            raise TenantServiceError("tenant not found", status_code=404)
        return tenant

    def get_tenant_capabilities(self, tenant_id: str) -> set[str]:
        tenant = self.get_tenant(tenant_id)
        return resolve_capabilities(tenant.contract()).capabilities

    def initialize_configuration(self, tenant_id: str, configuration: TenantConfiguration, actor_id: str) -> TenantConfiguration:
        tenant = self.get_tenant(tenant_id)
        configuration.version = 1
        tenant.configuration = configuration
        tenant.updated_at = datetime.now(timezone.utc)
        self.store.update(tenant)
        self.audit_logger.log(event_type="admin.tenant.configuration.initialized", tenant_id=tenant_id, actor_id=actor_id)
        return tenant.configuration

    def patch_configuration(self, tenant_id: str, config_patch: dict, actor_id: str, reason: str) -> TenantConfiguration:
        tenant = self.get_tenant(tenant_id)
        updated = asdict(tenant.configuration)
        for key, value in config_patch.items():
            if key in updated:
                updated[key] = value
        updated["version"] = tenant.configuration.version + 1
        tenant.configuration = TenantConfiguration(**updated)
        tenant.updated_at = datetime.now(timezone.utc)
        tenant.state_history.append(
            LifecycleEvent(
                state=tenant.lifecycle_state,
                reason=f"config_update:{reason}",
                actor_id=actor_id,
                effective_at=datetime.now(timezone.utc),
            )
        )
        self.store.update(tenant)
        self.audit_logger.log(event_type="admin.tenant.configuration.updated", tenant_id=tenant.tenant_id, actor_id=actor_id, details={"reason": reason, "version": tenant.configuration.version})
        return tenant.configuration

    def manage_feature_flags(self, tenant_id: str, feature_flag_changes: dict[str, bool], actor_id: str) -> TenantConfiguration:
        tenant = self.get_tenant(tenant_id)
        tenant.configuration.feature_flags.update(feature_flag_changes)
        tenant.configuration.version += 1
        tenant.updated_at = datetime.now(timezone.utc)
        tenant.state_history.append(
            LifecycleEvent(
                state=tenant.lifecycle_state,
                reason="feature_flags_updated",
                actor_id=actor_id,
                effective_at=datetime.now(timezone.utc),
            )
        )
        self.store.update(tenant)
        return tenant.configuration

    def enforce_isolation(self, context: IsolationContext) -> IsolationDecision:
        if context.tenant_id != context.actor_tenant_id:
            self.metrics.inc("tenant.isolation.denied")
            return IsolationDecision(allowed=False, reason="cross-tenant access denied")
        tenant = self.get_tenant(context.tenant_id)
        if tenant.lifecycle_state in {LifecycleState.ARCHIVED, LifecycleState.DECOMMISSIONED}:
            self.metrics.inc("tenant.isolation.denied")
            return IsolationDecision(allowed=False, reason="tenant is immutable due to lifecycle state")
        if tenant.lifecycle_state == LifecycleState.SUSPENDED and context.action in {"write", "session_create"}:
            self.metrics.inc("tenant.isolation.denied")
            return IsolationDecision(allowed=False, reason="tenant is suspended; write/session actions blocked")
        self.metrics.inc("tenant.isolation.allowed")
        return IsolationDecision(allowed=True, reason="tenant isolation check passed")

    def transition_lifecycle(self, tenant_id: str, next_state: LifecycleState, reason: str, actor_id: str, effective_at: datetime) -> Tenant:
        tenant = self.get_tenant(tenant_id)
        tenant.lifecycle_state = next_state
        tenant.updated_at = datetime.now(timezone.utc)
        tenant.state_history.append(LifecycleEvent(state=next_state, reason=reason, actor_id=actor_id, effective_at=effective_at))
        self.store.update(tenant)
        self.audit_logger.log(event_type="admin.tenant.lifecycle.changed", tenant_id=tenant.tenant_id, actor_id=actor_id, details={"next_state": next_state.value, "reason": reason})
        self.publisher.publish(build_lifecycle_event("tenant.lifecycle.changed", tenant.tenant_id, "tenant.lifecycle", {"state": next_state.value, "reason": reason}))
        return tenant

    def effective_settings(self, tenant: Tenant, include_defaults: bool) -> dict:
        cfg = asdict(tenant.configuration)
        if include_defaults:
            merged = DEFAULT_EFFECTIVE_SETTINGS.copy()
            merged.update(cfg.get("security_baseline", {}))
            merged.update({f"feature.{k}": v for k, v in cfg.get("feature_flags", {}).items()})
            return merged
        return cfg
