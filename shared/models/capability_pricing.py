from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CapabilityPricing:
    capability_id: str
    price: Decimal
    usage_based: bool = False

    def normalized(self) -> "CapabilityPricing":
        return CapabilityPricing(
            capability_id=self.capability_id.strip(),
            price=self.price,
            usage_based=bool(self.usage_based),
        )
