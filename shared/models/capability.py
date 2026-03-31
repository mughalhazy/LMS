from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .capability_pricing import CapabilityPricing


@dataclass(frozen=True)
class Capability:
    capability_id: str
    name: str
    description: str
    category: str
    default_enabled: bool = False
    price: Decimal = Decimal("0")
    usage_based: bool = False

    @property
    def pricing(self) -> CapabilityPricing:
        return CapabilityPricing(
            capability_id=self.capability_id,
            price=self.price,
            usage_based=self.usage_based,
        )
