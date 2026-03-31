from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass(frozen=True)
class Plan:
    plan_type: str
    price: Decimal
    billing_cycle: BillingCycle
    included_features: tuple[str, ...]

    def normalized(self) -> "Plan":
        return Plan(
            plan_type=self.plan_type.strip().lower(),
            price=self.price,
            billing_cycle=self.billing_cycle,
            included_features=tuple(sorted({feature.strip() for feature in self.included_features if feature.strip()})),
        )
