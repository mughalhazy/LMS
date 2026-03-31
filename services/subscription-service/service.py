from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.capability_pricing import CapabilityPricing


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


class SubscriptionService:
    """Source of truth for tenant subscription packaging (plan and add-ons)."""

    def __init__(self) -> None:
        self._tenant_subscriptions: dict[str, TenantSubscription] = {}
        self._tenant_add_on_purchases: dict[str, set[str]] = {}
        self._tenant_usage_ledger: dict[str, dict[str, int]] = {}

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
        plan_capabilities = {
            "free": {
                "assessment.attempt",
                "recommendation.basic",
                "commerce.catalog.basic",
                "learning.analytics.basic",
            },
            "pro": {
                "assessment.attempt",
                "assessment.author",
                "course.write",
                "recommendation.basic",
                "commerce.catalog.basic",
                "learning.analytics.basic",
            },
            "enterprise": {
                "assessment.attempt",
                "assessment.author",
                "course.write",
                "recommendation.basic",
                "commerce.catalog.basic",
                "learning.analytics.basic",
                "learning.analytics.advanced",
                "platform.support.priority",
            },
        }
        return set(plan_capabilities.get(plan_type.strip().lower(), set()))

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
        add_on_capabilities = {
            "analytics_advanced": {"learning.analytics.advanced"},
            "ai_tutor_pack": {"ai.tutor"},
            "dedicated_isolation": {"platform.isolation.dedicated"},
            "priority_support": {"platform.support.priority"},
        }
        return set(add_on_capabilities.get(add_on.strip().lower(), set()))
