from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


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

    def upsert_tenant_subscription(self, subscription: TenantSubscription) -> None:
        normalized = subscription.normalized()
        self._tenant_subscriptions[normalized.tenant_id] = normalized

    def get_tenant_subscription(self, tenant_id: str) -> TenantSubscription | None:
        return self._tenant_subscriptions.get(tenant_id.strip())

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
        plan_type: str,
        add_ons: tuple[str, ...],
        capability: str,
        entitlement: Callable[[str], bool],
    ) -> bool:
        del plan_type, add_ons
        is_enabled = entitlement(capability.strip())
        return bool(is_enabled)

    def get_add_on_capabilities(self, add_on: str) -> set[str]:
        add_on_capabilities = {
            "analytics_advanced": {"learning.analytics.advanced"},
            "ai_tutor_pack": {"ai.tutor"},
            "dedicated_isolation": {"platform.isolation.dedicated"},
            "priority_support": {"platform.support.priority"},
        }
        return set(add_on_capabilities.get(add_on.strip().lower(), set()))
