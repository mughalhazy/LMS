from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AuditEvent:
    event_type: str
    actor_id: str
    tenant_id: str
    target_id: str
    details: dict[str, Any] = field(default_factory=dict)
    destination: str = "loki"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLogger:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def log(self, event: AuditEvent) -> None:
        self._events.append(event)

    def list_events(self) -> list[AuditEvent]:
        return list(self._events)
