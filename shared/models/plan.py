from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class Plan:
    plan_id: str
    name: str
    billing_cycle: str
    included_capability_ids: tuple[str, ...] = ()
    addon_eligible_capability_ids: tuple[str, ...] = ()
    usage_limits: Mapping[str, int] = field(default_factory=dict)
    country_defaults: Mapping[str, str] = field(default_factory=dict)
    segment_defaults: Mapping[str, str] = field(default_factory=dict)

    def normalized(self) -> "Plan":
        return Plan(
            plan_id=self.plan_id.strip().lower(),
            name=self.name.strip(),
            billing_cycle=self.billing_cycle.strip().lower(),
            included_capability_ids=tuple(sorted({item.strip() for item in self.included_capability_ids if item.strip()})),
            addon_eligible_capability_ids=tuple(
                sorted({item.strip() for item in self.addon_eligible_capability_ids if item.strip()})
            ),
            usage_limits={str(key).strip(): int(value) for key, value in self.usage_limits.items() if str(key).strip()},
            country_defaults={str(key).strip().upper(): str(value).strip() for key, value in self.country_defaults.items() if str(key).strip()},
            segment_defaults={str(key).strip().lower(): str(value).strip() for key, value in self.segment_defaults.items() if str(key).strip()},
        )
