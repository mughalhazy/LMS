from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class EventEnvelope:
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    correlation_id: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


def build_event(
    *,
    event_type: str,
    tenant_id: str,
    correlation_id: str,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        event_id=str(uuid4()),
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        payload=payload,
        metadata=metadata or {},
    )
