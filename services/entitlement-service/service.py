from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.config import ConfigResolutionContext
from shared.utils.entitlement import EntitlementDecision, TenantEntitlementContext

_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_SubscriptionModule = _load_module("subscription_service_module", "services/subscription-service/service.py")
_ConfigModule = _load_module("config_service_module", "services/config-service/service.py")
_CapabilityModule = _load_module("capability_registry_module", "services/capability-registry/service.py")

SubscriptionService = _SubscriptionModule.SubscriptionService
TenantSubscription = _SubscriptionModule.TenantSubscription
ConfigService = _ConfigModule.ConfigService
CapabilityRegistryService = _CapabilityModule.CapabilityRegistryService


class EntitlementService:
    """Runtime entitlement decision engine and only source of truth for capability access."""

    def __init__(
        self,
        *,
        subscription_service: SubscriptionService | None = None,
        config_service: ConfigService | None = None,
        capability_registry_service: CapabilityRegistryService | None = None,
    ) -> None:
        self._subscription_service = subscription_service or SubscriptionService()
        self._config_service = config_service or ConfigService()
        self._capability_registry = capability_registry_service or CapabilityRegistryService()

    def upsert_tenant_context(self, context: TenantEntitlementContext) -> None:
        normalized = context.normalized()
        self._subscription_service.upsert_tenant_subscription(
            TenantSubscription(
                tenant_id=normalized.tenant_id,
                plan_type=normalized.plan_type,
                add_ons=normalized.add_ons,
            )
        )

    def decide(self, tenant: TenantEntitlementContext, capability: str) -> EntitlementDecision:
        normalized_tenant = tenant.normalized()
        normalized_capability = capability.strip()

        capability_meta = self._capability_registry.get_capability(normalized_capability)
        if capability_meta is None:
            return EntitlementDecision(
                tenant_id=normalized_tenant.tenant_id,
                capability=normalized_capability,
                is_enabled=False,
                plan_type=normalized_tenant.plan_type,
                add_ons=normalized_tenant.add_ons,
                sources=("unknown_capability",),
            )

        subscription = self._subscription_service.get_tenant_subscription(normalized_tenant.tenant_id)
        if subscription is None:
            subscription = TenantSubscription(
                tenant_id=normalized_tenant.tenant_id,
                plan_type=normalized_tenant.plan_type,
                add_ons=normalized_tenant.add_ons,
            ).normalized()
            self._subscription_service.upsert_tenant_subscription(subscription)

        candidate_enabled = capability_meta.default_enabled
        sources: list[str] = ["registry_default"] if capability_meta.default_enabled else []

        if normalized_capability in self._subscription_service.get_plan_capabilities(subscription.plan_type):
            candidate_enabled = True
            sources.append(f"plan:{subscription.plan_type}")

        for add_on in subscription.add_ons:
            if normalized_capability in self._subscription_service.get_add_on_capabilities(add_on):
                candidate_enabled = True
                sources.append(f"addon:{add_on}")
        if normalized_capability in self._subscription_service.get_active_add_on_capability_ids(normalized_tenant.tenant_id):
            candidate_enabled = True
            sources.append("addon_purchase")

        effective_config = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=normalized_tenant.tenant_id,
                country_code=normalized_tenant.country_code,
                segment_id=normalized_tenant.segment_id,
            )
        )
        if normalized_capability in effective_config.capability_enabled:
            candidate_enabled = effective_config.capability_enabled[normalized_capability]
            sources.append("config_override")

        return EntitlementDecision(
            tenant_id=normalized_tenant.tenant_id,
            capability=normalized_capability,
            is_enabled=bool(candidate_enabled),
            plan_type=subscription.plan_type,
            add_ons=subscription.add_ons,
            sources=tuple(sources),
        )


    def resolve_enabled_capabilities(self, tenant: TenantEntitlementContext) -> set[str]:
        normalized_tenant = tenant.normalized()
        subscription = self._subscription_service.get_tenant_subscription(normalized_tenant.tenant_id)
        if subscription is None:
            subscription = TenantSubscription(
                tenant_id=normalized_tenant.tenant_id,
                plan_type=normalized_tenant.plan_type,
                add_ons=normalized_tenant.add_ons,
            ).normalized()

        candidates = {
            capability.capability_id
            for capability in self._capability_registry.list_capabilities()
            if capability.default_enabled
        }
        candidates.update(self._subscription_service.get_plan_capabilities(subscription.plan_type))

        for add_on in subscription.add_ons:
            candidates.update(self._subscription_service.get_add_on_capabilities(add_on))
        candidates.update(self._subscription_service.get_active_add_on_capability_ids(normalized_tenant.tenant_id))

        effective_config = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=normalized_tenant.tenant_id,
                country_code=normalized_tenant.country_code,
                segment_id=normalized_tenant.segment_id,
            )
        )
        for capability_id, enabled in effective_config.capability_enabled.items():
            if enabled:
                candidates.add(capability_id)
            else:
                candidates.discard(capability_id)

        return {capability_id for capability_id in candidates if self.is_enabled(normalized_tenant, capability_id)}

    def is_enabled(self, tenant: TenantEntitlementContext, capability: str) -> bool:
        return self.decide(tenant=tenant, capability=capability).is_enabled

    def has_bypass_paths(self) -> bool:
        required_methods = (
            hasattr(self, "decide"),
            hasattr(self, "is_enabled"),
        )
        return not all(required_methods)
