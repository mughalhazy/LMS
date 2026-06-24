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
        # B01-013: publish to shared platform bus so downstream consumers receive events
        try:
            from backend.services.shared.events.bus import get_default_bus
            from backend.services.shared.events.envelope import build_event
            bus = get_default_bus()
            shared_envelope = build_event(
                event_type=event_type,
                payload=payload,
                tenant_id=tenant_id,
                correlation_id=envelope.correlation_id,
                producer_service="program-service",
            )
            bus.publish(shared_envelope)
        except Exception:
            pass  # best-effort — shared bus unavailable must not block service writes
        return envelope

    def list_events(self) -> list[EventEnvelope]:
        return list(self._events)
