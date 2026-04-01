from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Mapping

from .capability_pricing import CapabilityPricing


@dataclass(frozen=True)
class Capability:
    capability_id: str
    name: str
    description: str
    category: str
    default_enabled: bool = False
    monetizable: bool = True
    usage_metered: bool = False
    metadata: Mapping[str, str] = MappingProxyType({})
    price: Decimal = Decimal("0")
    usage_based: bool = False
    included_in_plans: tuple[str, ...] = ()
    included_in_add_ons: tuple[str, ...] = ()

    @property
    def pricing(self) -> CapabilityPricing:
        return CapabilityPricing(
            capability_id=self.capability_id,
            price=self.price,
            usage_based=self.usage_based,
        )
