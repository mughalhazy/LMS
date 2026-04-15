from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.services.shared.context.correlation import ensure_correlation_id


@dataclass
class EventEnvelope:
    event_id: str
    event_type: str
    timestamp: datetime
    tenant_id: str
    correlation_id: str
    payload: dict[str, Any]
    metadata: dict[str, Any]


class EventPublisher:
    def __init__(self) -> None:
        self._events: list[EventEnvelope] = []

    def publish(
        self,
        *,
        event_type: str,
        tenant_id: str,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> EventEnvelope:
        envelope = EventEnvelope(
            event_id=str(uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            tenant_id=tenant_id,
            correlation_id=ensure_correlation_id(correlation_id),
            payload=payload,
            metadata={"producer": "program-service"},
        )
        self._events.append(envelope)
        return envelope

    def list_events(self) -> list[EventEnvelope]:
        return list(self._events)
