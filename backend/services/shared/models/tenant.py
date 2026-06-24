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

    @property
    def segment_type(self) -> str:
        """CAT-002: canonical anchor field. Reads from segment_context['type'].
        Anchor tenant-contract.md defines segment_type as a plain string
        (enterprise|smb|edu|government). segment_context is the internal
        representation; this property exposes the canonical field name."""
        return str(self.segment_context.get("type", "default"))

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
