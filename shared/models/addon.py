from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Mapping


@dataclass(frozen=True)
class AddOn:
    addon_id: str
    capability_id: str
    price: Decimal
    billing_mode: str
    eligibility_rules: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    country_scope: tuple[str, ...] = ()
    status: str = "active"

    def normalized(self) -> "AddOn":
        normalized_rules: dict[str, tuple[str, ...]] = {}
        for key, values in self.eligibility_rules.items():
            normalized_key = str(key).strip().lower()
            if not normalized_key:
                continue
            normalized_values = tuple(
                sorted(
                    {
                        str(value).strip().lower()
                        for value in values
                        if str(value).strip()
                    }
                )
            )
            if normalized_values:
                normalized_rules[normalized_key] = normalized_values

        billing_mode = self.billing_mode.strip().lower()
        if billing_mode not in {"one_time", "recurring", "usage_based"}:
            raise ValueError("billing_mode must be one_time | recurring | usage_based")

        normalized_status = self.status.strip().lower() or "active"
        return AddOn(
            addon_id=self.addon_id.strip().lower(),
            capability_id=self.capability_id.strip(),
            price=Decimal(self.price),
            billing_mode=billing_mode,
            eligibility_rules=normalized_rules,
            country_scope=tuple(sorted({item.strip().upper() for item in self.country_scope if item.strip()})),
            status=normalized_status,
        )
