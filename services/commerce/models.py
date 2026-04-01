from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass(frozen=True)
class SubscriptionPlan:
    plan_id: str
    billing_cycle: BillingCycle
    price: Decimal
    capability_ids: tuple[str, ...] = field(default_factory=tuple)

    def normalized(self) -> "SubscriptionPlan":
        return SubscriptionPlan(
            plan_id=self.plan_id.strip().lower(),
            billing_cycle=BillingCycle(self.billing_cycle),
            price=Decimal(self.price),
            capability_ids=tuple(
                sorted({capability_id.strip() for capability_id in self.capability_ids if capability_id.strip()})
            ),
        )
