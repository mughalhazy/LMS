from __future__ import annotations

from media_service.models import EventRecord


class EventPublisher:
    def publish(self, event_name: str, tenant_id: str, media_asset_id: str, payload: dict[str, str]) -> EventRecord:
        return EventRecord(event_name=event_name, tenant_id=tenant_id, media_asset_id=media_asset_id, payload=payload)
