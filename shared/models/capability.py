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
    # CGAP-038: Monthly usage quota. None = unlimited.
    usage_quota: int | None = None
    # MS-CAP-01 (MS§2.2): required fields for capability definition completeness
    domain: str = ""                          # owner domain (e.g. "commerce", "learning", "ai")
    required_adapters: tuple[str, ...] = ()   # adapter keys required; empty tuple = no external deps
    # BC-LANG-01 / MO-031: business impact description in operator-facing language.
    # Required (non-empty) for monetizable capabilities — enforced in MS-CAP-01 validation.
    # Example: "Recover up to 30% of unpaid fees automatically via WhatsApp reminders"
    business_impact_description: str = ""

    @property
    def pricing(self) -> CapabilityPricing:
        return CapabilityPricing(
            capability_id=self.capability_id,
            price=self.price,
            usage_based=self.usage_based,
        )
