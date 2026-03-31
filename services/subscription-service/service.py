from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import importlib.util
from typing import Callable

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.capability_pricing import CapabilityPricing

_ROOT = Path(__file__).resolve().parents[2]


def _load_registry_service():
    module_path = _ROOT / "services/capability-registry/service.py"
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location("capability_registry_for_subscription", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load capability registry service")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.CapabilityRegistryService


@dataclass(frozen=True)
class TenantSubscription:
    tenant_id: str
    plan_type: str
    add_ons: tuple[str, ...] = field(default_factory=tuple)

    def normalized(self) -> "TenantSubscription":
        return TenantSubscription(
            tenant_id=self.tenant_id.strip(),
            plan_type=self.plan_type.strip().lower(),
            add_ons=tuple(sorted({addon.strip().lower() for addon in self.add_ons if addon.strip()})),
        )


@dataclass(frozen=True)
class CommerceSubscription:
    subscription_id: str
    tenant_id: str
    plan_type: str
    source_order_id: str
    status: str = "active"
    renewals: int = 0


class SubscriptionService:
    """Source of truth for tenant subscription packaging (plan and add-ons)."""

    def __init__(self) -> None:
        self._tenant_subscriptions: dict[str, TenantSubscription] = {}
        self._tenant_add_on_purchases: dict[str, set[str]] = {}
        self._tenant_usage_ledger: dict[str, dict[str, int]] = {}
        self._commerce_subscriptions: dict[str, CommerceSubscription] = {}
        self._capability_registry = _load_registry_service()()

    def upsert_tenant_subscription(self, subscription: TenantSubscription) -> None:
        normalized = subscription.normalized()
        self._tenant_subscriptions[normalized.tenant_id] = normalized

    def get_tenant_subscription(self, tenant_id: str) -> TenantSubscription | None:
        return self._tenant_subscriptions.get(tenant_id.strip())

    def purchase_capability_add_on(self, tenant_id: str, capability_id: str) -> None:
        normalized_tenant_id = tenant_id.strip()
        normalized_capability_id = capability_id.strip()
        purchased = self._tenant_add_on_purchases.setdefault(normalized_tenant_id, set())
        purchased.add(normalized_capability_id)

    def get_purchased_capability_add_ons(self, tenant_id: str) -> set[str]:
        return set(self._tenant_add_on_purchases.get(tenant_id.strip(), set()))

    def record_capability_usage(self, *, tenant_id: str, capability_id: str, units: int = 1) -> None:
        normalized_tenant_id = tenant_id.strip()
        normalized_capability_id = capability_id.strip()
        ledger = self._tenant_usage_ledger.setdefault(normalized_tenant_id, {})
        ledger[normalized_capability_id] = ledger.get(normalized_capability_id, 0) + max(units, 0)

    def get_usage_for_tenant(self, tenant_id: str) -> dict[str, int]:
        return dict(self._tenant_usage_ledger.get(tenant_id.strip(), {}))

    def calculate_capability_charge(
        self,
        *,
        tenant_id: str,
        pricing: CapabilityPricing,
    ) -> Decimal:
        normalized_pricing = pricing.normalized()
        if normalized_pricing.usage_based:
            units = self._tenant_usage_ledger.get(tenant_id.strip(), {}).get(normalized_pricing.capability_id, 0)
            return normalized_pricing.price * Decimal(units)
        return normalized_pricing.price

    def get_plan_capabilities(self, plan_type: str) -> set[str]:
        normalized_plan = plan_type.strip().lower()
        return {
            capability.capability_id
            for capability in self._capability_registry.list_capabilities()
            if normalized_plan in capability.included_in_plans
        }

    def is_enabled_for_subscription(
        self,
        *,
        tenant_id: str = "",
        plan_type: str,
        add_ons: tuple[str, ...],
        capability: str,
        entitlement: Callable[[str], bool],
    ) -> bool:
        normalized_capability = capability.strip()
        if entitlement(normalized_capability):
            return True
        purchased = normalized_capability in self.get_purchased_capability_add_ons(tenant_id)
        if purchased:
            return True
        for add_on in add_ons:
            if normalized_capability in self.get_add_on_capabilities(add_on):
                return True
        return False

    def get_add_on_capabilities(self, add_on: str) -> set[str]:
        normalized_add_on = add_on.strip().lower()
        return {
            capability.capability_id
            for capability in self._capability_registry.list_capabilities()
            if normalized_add_on in capability.included_in_add_ons
        }

    def create_or_activate_subscription(
        self,
        *,
        tenant_id: str,
        subscription_id: str,
        plan_type: str,
        source_order_id: str,
    ) -> CommerceSubscription:
        normalized = CommerceSubscription(
            subscription_id=subscription_id.strip(),
            tenant_id=tenant_id.strip(),
            plan_type=plan_type.strip().lower(),
            source_order_id=source_order_id.strip(),
            status="active",
            renewals=0,
        )
        self._commerce_subscriptions[normalized.subscription_id] = normalized
        return normalized

    def renew_subscription(self, subscription_id: str) -> CommerceSubscription:
        current = self._commerce_subscriptions[subscription_id.strip()]
        renewed = CommerceSubscription(
            subscription_id=current.subscription_id,
            tenant_id=current.tenant_id,
            plan_type=current.plan_type,
            source_order_id=current.source_order_id,
            status="active",
            renewals=current.renewals + 1,
        )
        self._commerce_subscriptions[renewed.subscription_id] = renewed
        return renewed

    def cancel_subscription(self, subscription_id: str) -> CommerceSubscription:
        current = self._commerce_subscriptions[subscription_id.strip()]
        canceled = CommerceSubscription(
            subscription_id=current.subscription_id,
            tenant_id=current.tenant_id,
            plan_type=current.plan_type,
            source_order_id=current.source_order_id,
            status="canceled",
            renewals=current.renewals,
        )
        self._commerce_subscriptions[canceled.subscription_id] = canceled
        return canceled

    def get_subscription_contract(self, subscription_id: str) -> CommerceSubscription | None:
        return self._commerce_subscriptions.get(subscription_id.strip())
