from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from media_service.models import EventRecord


class EventPublisher:
    def publish(self, event_name: str, tenant_id: str, media_asset_id: str, payload: dict[str, str]) -> EventRecord:
        return EventRecord(
            event_id=str(uuid4()),
            event_type=event_name,
            timestamp=datetime.now(timezone.utc),
            tenant_id=tenant_id,
            correlation_id=str(uuid4()),
            payload=payload,
            metadata={"media_asset_id": media_asset_id, "producer": "media-service"},
        )
