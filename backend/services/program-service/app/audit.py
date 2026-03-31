from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class AuditEvent:
    event_id: str
    event_type: str
    tenant_id: str
    correlation_id: str
    actor_id: str
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    def __init__(self, logger_name: str) -> None:
        self._logger = logging.getLogger(logger_name)
        self._events: list[AuditEvent] = []

    def log(
        self,
        *,
        event_type: str,
        tenant_id: str,
        correlation_id: str,
        actor_id: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            actor_id=actor_id,
            timestamp=datetime.now(timezone.utc),
            details=details or {},
        )
        self._events.append(event)
        self._logger.info(json.dumps(asdict(event), default=str))
        return event

    def list_events(self) -> list[AuditEvent]:
        return list(self._events)
