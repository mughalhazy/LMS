from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TenantContract:
    tenant_id: str
    name: str
    country_code: str
    segment_type: str
    plan_type: str
    addon_flags: list[str] = field(default_factory=list)

    def normalized(self) -> "TenantContract":
        unique_flags = sorted(set(self.addon_flags))
        return TenantContract(
            tenant_id=self.tenant_id,
            name=self.name,
            country_code=self.country_code.upper(),
            segment_type=self.segment_type,
            plan_type=self.plan_type,
            addon_flags=unique_flags,
        )
