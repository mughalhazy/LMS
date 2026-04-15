from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class UsageRecord:
    usage_id: str
    tenant_id: str
    capability_id: str
    unit_type: str
    quantity: int
    source_service: str
    timestamp: datetime
    reference_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized(self) -> "UsageRecord":
        normalized_metadata = {
            str(key).strip(): value
            for key, value in self.metadata.items()
            if str(key).strip()
        }
        normalized_quantity = int(self.quantity)
        if normalized_quantity < 0:
            raise ValueError("quantity must be >= 0")
        normalized_reference = self.reference_id.strip()
        if not normalized_reference:
            raise ValueError("reference_id is required")
        return UsageRecord(
            usage_id=self.usage_id.strip() or str(uuid4()),
            tenant_id=self.tenant_id.strip(),
            capability_id=self.capability_id.strip(),
            unit_type=self.unit_type.strip() or "count",
            quantity=normalized_quantity,
            source_service=self.source_service.strip(),
            timestamp=self.timestamp if self.timestamp.tzinfo else self.timestamp.replace(tzinfo=timezone.utc),
            reference_id=normalized_reference,
            metadata=normalized_metadata,
        )
