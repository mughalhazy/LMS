from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class PricingMode(str, Enum):
    INCLUDED = "included"
    ADDON = "addon"
    USAGE_BASED = "usage_based"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class PricingOverride:
    base_price: Decimal | None = None
    usage_unit_price: Decimal | None = None
    currency: str | None = None

    def normalized(self) -> "PricingOverride":
        return PricingOverride(
            base_price=Decimal(self.base_price) if self.base_price is not None else None,
            usage_unit_price=Decimal(self.usage_unit_price) if self.usage_unit_price is not None else None,
            currency=self.currency.strip().upper() if self.currency else None,
        )


@dataclass(frozen=True)
class CapabilityPricing:
    capability_id: str
    pricing_mode: PricingMode
    base_price: Decimal
    usage_unit_price: Decimal
    currency: str
    country_overrides: dict[str, PricingOverride] = field(default_factory=dict)
    plan_overrides: dict[str, PricingOverride] = field(default_factory=dict)

    def __init__(
        self,
        *,
        capability_id: str,
        pricing_mode: PricingMode | str | None = None,
        base_price: Decimal | int | str = Decimal("0"),
        usage_unit_price: Decimal | int | str = Decimal("0"),
        currency: str = "USD",
        country_overrides: dict[str, PricingOverride] | None = None,
        plan_overrides: dict[str, PricingOverride] | None = None,
        # backwards-compatible aliases
        price: Decimal | int | str | None = None,
        usage_based: bool | None = None,
    ) -> None:
        resolved_mode: PricingMode
        if pricing_mode is not None:
            resolved_mode = PricingMode(pricing_mode)
        elif usage_based is True:
            resolved_mode = PricingMode.USAGE_BASED
        else:
            resolved_mode = PricingMode.ADDON

        resolved_base = Decimal(price if price is not None else base_price)
        resolved_usage = Decimal(usage_unit_price)
        if resolved_mode == PricingMode.USAGE_BASED and usage_unit_price == Decimal("0") and price is not None:
            resolved_usage = Decimal(price)
            resolved_base = Decimal("0")

        object.__setattr__(self, "capability_id", capability_id.strip())
        object.__setattr__(self, "pricing_mode", resolved_mode)
        object.__setattr__(self, "base_price", resolved_base)
        object.__setattr__(self, "usage_unit_price", resolved_usage)
        object.__setattr__(self, "currency", currency.strip().upper())
        object.__setattr__(
            self,
            "country_overrides",
            {country.strip().upper(): override.normalized() for country, override in (country_overrides or {}).items()},
        )
        object.__setattr__(
            self,
            "plan_overrides",
            {plan.strip().lower(): override.normalized() for plan, override in (plan_overrides or {}).items()},
        )

    def normalized(self) -> "CapabilityPricing":
        return CapabilityPricing(
            capability_id=self.capability_id,
            pricing_mode=self.pricing_mode,
            base_price=self.base_price,
            usage_unit_price=self.usage_unit_price,
            currency=self.currency,
            country_overrides=self.country_overrides,
            plan_overrides=self.plan_overrides,
        )

    @property
    def price(self) -> Decimal:
        return self.usage_unit_price if self.pricing_mode == PricingMode.USAGE_BASED else self.base_price

    @property
    def usage_based(self) -> bool:
        return self.pricing_mode in {PricingMode.USAGE_BASED, PricingMode.HYBRID}

    def resolve(self, *, country_code: str = "", plan_id: str = "") -> "CapabilityPricing":
        resolved = self
        plan_override = self.plan_overrides.get(plan_id.strip().lower()) if plan_id else None
        if plan_override is not None:
            resolved = resolved._apply_override(plan_override)
        country_override = self.country_overrides.get(country_code.strip().upper()) if country_code else None
        if country_override is not None:
            resolved = resolved._apply_override(country_override)
        return resolved

    def _apply_override(self, override: PricingOverride) -> "CapabilityPricing":
        return CapabilityPricing(
            capability_id=self.capability_id,
            pricing_mode=self.pricing_mode,
            base_price=override.base_price if override.base_price is not None else self.base_price,
            usage_unit_price=override.usage_unit_price if override.usage_unit_price is not None else self.usage_unit_price,
            currency=override.currency or self.currency,
            country_overrides=self.country_overrides,
            plan_overrides=self.plan_overrides,
        )

    def has_valid_pricing_path(self) -> bool:
        if self.pricing_mode == PricingMode.INCLUDED:
            return True
        if self.pricing_mode == PricingMode.ADDON:
            return self.base_price > Decimal("0")
        if self.pricing_mode == PricingMode.USAGE_BASED:
            return self.usage_unit_price > Decimal("0")
        return self.base_price > Decimal("0") or self.usage_unit_price > Decimal("0")
