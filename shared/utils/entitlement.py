from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TenantEntitlementContext:
    tenant_id: str
    plan_type: str
    add_ons: tuple[str, ...] = field(default_factory=tuple)
    country_code: str = "global"
    segment_id: str = "default"

    def normalized(self) -> "TenantEntitlementContext":
        normalized_add_ons = tuple(sorted({addon.strip().lower() for addon in self.add_ons if addon.strip()}))
        return TenantEntitlementContext(
            tenant_id=self.tenant_id.strip(),
            plan_type=self.plan_type.strip().lower(),
            add_ons=normalized_add_ons,
            country_code=self.country_code.strip() or "global",
            segment_id=self.segment_id.strip() or "default",
        )


@dataclass(frozen=True)
class EntitlementDecision:
    tenant_id: str
    capability: str
    is_enabled: bool
    plan_type: str
    add_ons: tuple[str, ...]
    sources: tuple[str, ...] = field(default_factory=tuple)
