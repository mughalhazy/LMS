from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TenantContract:
    tenant_id: str
    name: str
    country_code: str
    plan_type: str
    segment_context: dict[str, Any] = field(default_factory=lambda: {"type": "default", "attributes": {}})
    addon_flags: list[str] = field(default_factory=list)

    def normalized(self) -> "TenantContract":
        unique_flags = sorted(set(self.addon_flags))
        return TenantContract(
            tenant_id=self.tenant_id,
            name=self.name,
            country_code=self.country_code.upper(),
            segment_context={
                "type": str(self.segment_context.get("type", "default")),
                "attributes": dict(self.segment_context.get("attributes", {})),
            },
            plan_type=self.plan_type,
            addon_flags=unique_flags,
        )
